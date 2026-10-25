"""Extraction de texte depuis fichiers (PDF, DOCX, TXT) et URL, avec OCR de secours.

Le texte extrait est ensuite ingéré par `ingest_document` (découpage par article,
vectorisation, indexation). On ne stocke jamais le binaire pour le RAG : seul le texte compte.
"""
import io
import logging
import re

logger = logging.getLogger("rag.extract")

# En dessous de ce nb de caractères, on considère le PDF comme « scanné » → OCR
_MIN_TEXT_LEN = 200

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0 Safari/537.36 Jamakan/1.0")
_RETRY_STATUS = {429, 500, 502, 503, 504}


def _http_get(url: str, timeout: int = 30, attempts: int = 3):
    """GET HTTP avec réessais + backoff sur erreurs transitoires (anti-throttling des sites)."""
    import time

    import httpx
    last: Exception | None = None
    for i in range(attempts):
        try:
            r = httpx.get(url, timeout=timeout, follow_redirects=True, headers={"User-Agent": _UA})
            if r.status_code in _RETRY_STATUS:
                last = httpx.HTTPStatusError(str(r.status_code), request=r.request, response=r)
                time.sleep(2 * (i + 1))  # backoff : 2s, 4s
                continue
            r.raise_for_status()
            return r
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            last = exc
            time.sleep(2 * (i + 1))
    raise last or RuntimeError(f"GET a échoué : {url}")


def _clean(text: str) -> str:
    # Recolle les coupures de mots en fin de ligne et normalise les espaces
    text = text.replace("\r\n", "\n")
    text = re.sub(r"-\n(\w)", r"\1", text)          # mot cou-\npé → coupé
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _from_txt(data: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


def _from_docx(data: bytes) -> str:
    from docx import Document  # python-docx
    doc = Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _ocr_pdf(data: bytes) -> str:
    """OCR de secours pour les PDF scannés (images)."""
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
    except Exception as exc:  # noqa: BLE001
        logger.warning("OCR indisponible: %s", exc)
        return ""
    pages = convert_from_bytes(data, dpi=200)
    out = []
    for img in pages:
        out.append(pytesseract.image_to_string(img, lang="fra"))
    return "\n".join(out)


def _from_pdf(data: bytes, ocr: bool = True) -> str:
    from pypdf import PdfReader
    reader = PdfReader(io.BytesIO(data))
    text = "\n".join((page.extract_text() or "") for page in reader.pages)
    if len(text.strip()) < _MIN_TEXT_LEN and ocr:
        logger.info("PDF peu de texte (%d car.) → tentative OCR", len(text.strip()))
        ocr_text = _ocr_pdf(data)
        if len(ocr_text.strip()) > len(text.strip()):
            text = ocr_text
    return text


def extract_text(filename: str, data: bytes, ocr: bool = True) -> str:
    """Extrait le texte d'un fichier selon son extension."""
    name = (filename or "").lower()
    if name.endswith(".pdf"):
        text = _from_pdf(data, ocr=ocr)
    elif name.endswith(".docx"):
        text = _from_docx(data)
    elif name.endswith((".txt", ".md", ".text")):
        text = _from_txt(data)
    else:
        raise ValueError(f"Format non supporté : {filename} (utilisez .pdf, .docx ou .txt)")
    return _clean(text)


_PAGINATION_RE = re.compile(r"([?&]page=\d+|/page/\d+|/p/\d+|[?&]paged=\d+)", re.I)


def _page_links(url: str, host: str) -> list[str]:
    """Tous les liens (même domaine) d'une page, dédoublonnés."""
    from urllib.parse import urljoin, urlparse

    from bs4 import BeautifulSoup

    resp = _http_get(url, timeout=30)
    soup = BeautifulSoup(resp.text, "html.parser")
    seen: set = set()
    out: list[str] = []
    for a in soup.find_all("a", href=True):
        href = urljoin(url, a["href"]).split("#")[0]
        if urlparse(href).netloc != host or href in seen:
            continue
        seen.add(href)
        out.append(href)
    return out


def extract_links(index_url: str, filter_substr: str | None = None, limit: int = 100) -> list[str]:
    """Liens d'une page index correspondant au filtre (un seul niveau)."""
    from urllib.parse import urlparse
    host = urlparse(index_url).netloc
    out = []
    for href in _page_links(index_url, host):
        if filter_substr and filter_substr not in href:
            continue
        if href.rstrip("/") == index_url.rstrip("/"):
            continue
        out.append(href)
        if len(out) >= limit:
            break
    return out


def crawl_collect(index_url: str, filter_substr: str | None = None,
                  max_depth: int = 1, max_pages: int = 60, max_visit: int = 60) -> list[str]:
    """Crawl borné, même domaine : suit la PAGINATION et descend en PROFONDEUR (sous-index).

    Renvoie la liste des URLs de contenu (correspondant au filtre) à ingérer, dédoublonnée et bornée.
    """
    from urllib.parse import urlparse
    host = urlparse(index_url).netloc
    visited: set = set()
    content: list[str] = []
    content_set: set = set()
    queue: list[tuple[str, int]] = [(index_url, 1)]

    while queue and len(content) < max_pages and len(visited) < max_visit:
        url, depth = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            links = _page_links(url, host)
        except Exception:  # noqa: BLE001
            continue
        for href in links:
            if href.rstrip("/") == index_url.rstrip("/"):
                continue
            if _PAGINATION_RE.search(href):
                # page de listing suivante → même niveau
                if href not in visited:
                    queue.append((href, depth))
            elif (not filter_substr) or (filter_substr in href):
                # contenu à ingérer
                if href not in content_set:
                    content_set.add(href)
                    content.append(href)
                    if len(content) >= max_pages:
                        break
            elif depth < max_depth and href not in visited:
                # sous-index → on descend
                queue.append((href, depth + 1))
    return content[:max_pages]


def extract_from_url(url: str) -> str:
    """Récupère une page web et en extrait le texte principal."""
    from bs4 import BeautifulSoup

    resp = _http_get(url, timeout=120)
    ctype = resp.headers.get("content-type", "")
    if "application/pdf" in ctype or url.lower().endswith(".pdf"):
        return _clean(_from_pdf(resp.content))
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer", "noscript", "aside", "form"]):
        tag.decompose()
    # Conteneurs de contenu courants (WordPress comme loidici/legici, puis génériques)
    main = None
    for sel in [".mw-parser-output", "#mw-content-text",  # Wikipédia / MediaWiki
                ".entry-content", ".post-content", "article .content", "article",
                "main", "#content", ".content"]:
        node = soup.select_one(sel)
        if node and len(node.get_text(strip=True)) > 200:
            main = node
            break
    main = main or soup.body or soup
    return _clean(main.get_text("\n"))
