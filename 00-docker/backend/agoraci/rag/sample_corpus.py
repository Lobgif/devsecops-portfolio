"""Corpus juridique de DÉMONSTRATION pour amorcer le RAG.

⚠️ Contenu illustratif (non officiel). Remplacer par les textes officiels
ivoiriens via l'endpoint POST /api/rag/ingest-document ou le pipeline d'ingestion.
Les numéros et formulations sont génériques et servent uniquement à tester la chaîne.
"""

SAMPLE_DOCUMENTS = [
    {
        "title": "Code de la famille — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Code de la famille (démo)",
        "content": """
Article 1 : Le mariage est l'union légale d'un homme et d'une femme célébrée
devant l'officier de l'état civil. Le consentement libre des deux époux est requis.

Article 2 : Chacun des époux contribue aux charges du ménage à proportion de ses
facultés. Les biens acquis pendant le mariage relèvent du régime matrimonial choisi.

Article 3 : Le divorce peut être prononcé par consentement mutuel ou pour faute.
Le juge statue sur la résidence des enfants en tenant compte de leur intérêt supérieur.

Article 4 : En cas de divorce, le partage des biens communs s'effectue selon le
régime matrimonial. Une pension alimentaire peut être fixée au profit des enfants.

Article 5 : La filiation établit les droits et devoirs entre parents et enfants,
y compris l'obligation d'entretien et le droit à l'héritage.
""",
    },
    {
        "title": "Code des successions — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Successions (démo)",
        "content": """
Article 10 : La succession s'ouvre au décès. Les héritiers sont appelés selon
l'ordre légal : descendants, puis ascendants et collatéraux.

Article 11 : Tout héritier peut accepter ou renoncer à la succession. L'acceptation
peut être pure et simple ou à concurrence de l'actif net.

Article 12 : Le défunt peut disposer d'une quotité de ses biens par testament,
dans le respect de la réserve héréditaire des héritiers réservataires.

Article 13 : Le partage met fin à l'indivision successorale. Tout héritier écarté
ou lésé peut saisir le tribunal compétent pour faire valoir ses droits.
""",
    },
    {
        "title": "Code du travail — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Code du travail (démo)",
        "content": """
Article 20 : Le contrat de travail peut être à durée déterminée ou indéterminée.
Toute rupture doit respecter les procédures et les délais de préavis prévus.

Article 21 : Le licenciement doit reposer sur un motif légitime. À défaut, le
salarié peut prétendre à des dommages et intérêts.

Article 22 : Le salarié a droit à un congé payé annuel ainsi qu'au repos
hebdomadaire. La durée légale du travail est fixée par la réglementation.

Article 23 : En cas de litige, le salarié peut saisir l'inspection du travail
puis, le cas échéant, le tribunal du travail compétent.
""",
    },
    {
        "title": "Création d'entreprise (OHADA) — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Acte uniforme OHADA (démo)",
        "content": """
Article 30 : Toute personne peut entreprendre une activité commerciale en créant
une entreprise individuelle ou une société (SARL, SAS, SA), immatriculée au
Registre du Commerce et du Crédit Mobilier (RCCM).

Article 31 : La société à responsabilité limitée (SARL) peut être constituée par
une ou plusieurs personnes. Le capital social est librement fixé par les statuts.

Article 32 : L'immatriculation au RCCM confère la personnalité juridique à la
société. Les formalités s'effectuent au guichet unique (CEPICI en Côte d'Ivoire).

Article 33 : L'entreprenant est un statut simplifié permettant d'exercer une petite
activité avec des obligations comptables allégées.
""",
    },
    {
        "title": "Fiscalité des entreprises — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Code général des impôts (démo)",
        "content": """
Article 40 : Les entreprises sont soumises à l'impôt sur les bénéfices selon leur
régime d'imposition (réel normal, réel simplifié, ou microentreprise).

Article 41 : La taxe sur la valeur ajoutée (TVA) s'applique aux livraisons de biens
et prestations de services, sauf exonérations prévues par la loi.

Article 42 : Toute entreprise doit déclarer ses revenus et s'acquitter de ses
impôts dans les délais légaux, sous peine de pénalités.
""",
    },
    {
        "title": "Droit foncier — extraits de démonstration",
        "source_type": "demo",
        "code_source": "Code foncier rural (démo)",
        "content": """
Article 50 : La propriété foncière est établie par un titre foncier ou un certificat
foncier délivré par l'administration compétente.

Article 51 : Toute transaction sur un terrain (vente, donation) doit être constatée
par un acte et faire l'objet d'une publicité foncière pour être opposable aux tiers.

Article 52 : En cas de litige foncier, les parties peuvent recourir à la médiation
puis, à défaut d'accord, saisir le tribunal compétent.
""",
    },
    {
        "title": "Politique & démocratie — repères",
        "source_type": "reference",
        "code_source": "Repères politiques",
        "content": """
La séparation des pouvoirs (législatif, exécutif, judiciaire) est théorisée par Montesquieu
dans « De l'esprit des lois » comme garantie contre l'arbitraire.

Le contrat social de Jean-Jacques Rousseau fonde la légitimité du pouvoir sur la volonté générale
et la souveraineté du peuple.

Alexis de Tocqueville, dans « De la démocratie en Amérique », analyse les forces et les risques de
la démocratie, dont la « tyrannie de la majorité ».

L'État de droit suppose des élections libres, le pluralisme, la liberté d'expression et le respect
des droits fondamentaux.
""",
    },
    {
        "title": "Entrepreneuriat & développement personnel — repères",
        "source_type": "reference",
        "code_source": "Repères entrepreneuriat",
        "content": """
« Père riche, père pauvre » de Robert Kiyosaki popularise l'éducation financière et la distinction
actif/passif.

« Les 7 habitudes des gens efficaces » de Stephen Covey propose des principes d'efficacité personnelle
(proactivité, priorités, synergie).

« Lean Startup » d'Eric Ries promeut l'expérimentation, le produit minimum viable (MVP) et l'itération.

« Réfléchissez et devenez riche » de Napoleon Hill insiste sur la vision, la persévérance et l'objectif clair.
""",
    },
    {
        "title": "Religions & spiritualité — repères",
        "source_type": "reference",
        "code_source": "Repères religieux",
        "content": """
Les grandes traditions s'appuient sur des textes de référence : le Coran (islam), la Bible
(christianisme), la Torah (judaïsme), ainsi que des traditions orales et spirituelles africaines.

Sur les débats religieux, Jamakan encourage le respect mutuel, la liberté de conscience et la
présentation de plusieurs perspectives sans prosélytisme ni jugement.
""",
    },
]
