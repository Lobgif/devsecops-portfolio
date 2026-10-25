"""Import en masse d'un dossier de fichiers juridiques dans la base de connaissances.

Dépose tes fichiers (.pdf / .docx / .txt) dans le dossier monté, puis :

    docker compose --project-directory . -f infra/compose.yaml \\
        exec backend python -m agoraci.rag.import_folder /imports

Chaque fichier devient un document (titre = nom du fichier), découpé par article,
vectorisé et indexé. Idempotent : relancer n'ajoute pas de doublon (clé = titre).
"""
import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agoraci.common.db import get_engine

from .extract import extract_text
from .ingest import ingest_document

logging.basicConfig(level="INFO")
logger = logging.getLogger("rag.import_folder")

EXTS = {".pdf", ".docx", ".txt", ".md", ".text"}


async def main(folder: str, source_type: str = "loi") -> None:
    files = sorted(p for p in Path(folder).rglob("*") if p.suffix.lower() in EXTS)
    logger.info("%d fichier(s) trouvé(s) dans %s", len(files), folder)
    if not files:
        logger.warning("Aucun fichier .pdf/.docx/.txt. Place tes documents dans %s", folder)
        return

    maker = async_sessionmaker(get_engine(), expire_on_commit=False, class_=AsyncSession)
    ok = total = 0
    async with maker() as session:
        for p in files:
            try:
                text = extract_text(p.name, p.read_bytes())
                if not text.strip():
                    logger.warning("  ✗ %s : aucun texte extrait", p.name)
                    continue
                r = await ingest_document(
                    session, title=p.stem, content=text,
                    source_type=source_type, code_source=p.stem,
                )
                ok += 1
                total += r["chunks"]
                logger.info("  ✓ %s : %d article(s)%s", p.name, r["chunks"],
                            " (déjà présent)" if r["skipped"] else "")
            except Exception as exc:  # noqa: BLE001
                logger.error("  ✗ %s : %s", p.name, exc)
    logger.info("✅ Terminé : %d/%d fichiers, %d articles indexés.", ok, len(files), total)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "/imports"
    asyncio.run(main(target))
