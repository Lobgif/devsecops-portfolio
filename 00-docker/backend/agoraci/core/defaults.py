"""Valeurs par défaut : paramètres du site + corpus initial du glossaire."""

DEFAULT_SETTINGS = {
    "site_name": "Jamakan",
    "footer_tagline": "Plateforme citoyenne collaborative pour la Côte d'Ivoire. Entraide, information et savoir pour tous les sujets du quotidien.",
    "contact_email": "contact@kaedys.com",
    "contact_location": "Abidjan, Côte d'Ivoire",
    "contact_phone": "",  # affiché sur Contact/footer si renseigné (ex. +225 …)
    "footer_made_with": "Fait avec ❤️ pour la Côte d'Ivoire",
    "social_facebook": "",
    "social_x": "",
    "social_instagram": "",
    "social_linkedin": "",
    "about_show_team": "1",  # « 1 » = section « Notre équipe » visible ; « 0 » = masquée au public
    "nanan_daily_limit": "15",  # nb de questions Nanan / utilisateur / jour (0 = illimité) — anti-abus + coût
    # Seuils ABSOLUS des badges de groupe (automatiques) — réglables en admin
    "badge_alaune_posts_week": "1000",   # « à la une » : > N messages / semaine (top)
    "badge_populaire_posts_week": "375", # « populaire » : > 375 messages / semaine
    "badge_vedette_members": "100",      # « vedette » : > 100 membres
    "badge_reactif_posts_day": "50",     # « réactif » : > 50 réponses / jour
    "badge_actif_days": "7",             # « actif » : dernière activité <= N jours
    "badge_nouveau_days": "7",           # « nouveau » : créé il y a <= N jours
    "badge_max_per_group": "1",          # nb de badges affichés par groupe
    # Gouvernance des groupes — réglables en admin
    "group_creation_threshold": "30",       # nb de soutiens pour créer un groupe
    "group_direct_creation_min_rep": "0",   # réputation min. pour créer sans proposition (0 = désactivé)
    "vote_weight_cap": "2.0",               # poids max d'un vote (équilibre : 1.0 → 2.0)
    "superadmin_group_delete_notice_h": "72",  # préavis (h) avant suppression d'un groupe par le super-admin
    # Textes légaux (markdown) — éditables depuis l'admin, affichés sur les pages dédiées
    "legal_cgu": (
        "# Conditions générales d'utilisation\n\n"
        "Bienvenue sur Jamakan. En utilisant la plateforme, vous acceptez les présentes conditions.\n\n"
        "## 1. Objet\n"
        "Jamakan est une plateforme citoyenne d'entraide, d'information juridique et de discussion. "
        "Les réponses de l'assistant Nanan et de la communauté sont fournies **à titre informatif** et "
        "ne constituent pas un conseil juridique officiel.\n\n"
        "## 2. Compte\n"
        "Vous êtes responsable de l'exactitude de vos informations et de la confidentialité de votre mot de passe.\n\n"
        "## 3. Règles de la communauté\n"
        "Les propos haineux, injurieux, diffamatoires ou illégaux sont interdits et peuvent entraîner la "
        "suspension ou la suppression du compte.\n\n"
        "## 4. Contenu\n"
        "Vous restez responsable des contenus que vous publiez. La modération est assurée par la communauté "
        "(vote) et l'administration.\n\n"
        "## 5. Modification\n"
        "Ces conditions peuvent évoluer ; la version en vigueur est celle publiée sur cette page."
    ),
    "legal_privacy": (
        "# Politique de confidentialité\n\n"
        "Jamakan respecte votre vie privée et protège vos données personnelles.\n\n"
        "## Données collectées\n"
        "Email, nom d'utilisateur, et les contenus que vous publiez. Pour la connexion Google, les "
        "informations de profil fournies par Google.\n\n"
        "## Utilisation\n"
        "Vos données servent à faire fonctionner la plateforme (authentification, notifications, affichage "
        "de votre profil public) et ne sont pas vendues à des tiers.\n\n"
        "## Vos droits\n"
        "Vous pouvez consulter, modifier ou supprimer votre compte et vos données à tout moment depuis votre "
        "profil. Pour toute demande, contactez-nous.\n\n"
        "## Cookies\n"
        "Des cookies strictement nécessaires assurent votre session de connexion (cookies httpOnly sécurisés)."
    ),
    "legal_mentions": (
        "# Mentions légales\n\n"
        "**Jamakan** — Plateforme citoyenne collaborative.\n\n"
        "**Contact :** lahigic@gmail.com\n\n"
        "**Localisation :** Abidjan, Côte d'Ivoire\n\n"
        "**Hébergement :** voir le fournisseur d'hébergement en vigueur.\n\n"
        "Le contenu juridique est fourni à titre informatif et ne remplace pas la consultation d'un professionnel du droit."
    ),
}

GLOSSARY_TERMS = [
    ("Jurisprudence", "Général", "Ensemble des décisions de justice qui interprètent la loi et servent de référence."),
    ("Dot", "Famille", "Biens ou somme remis lors du mariage ; en droit ivoirien la dot coutumière est encadrée."),
    ("Garde des enfants", "Famille", "Attribution de la résidence et de la responsabilité des enfants, décidée selon leur intérêt supérieur."),
    ("Pension alimentaire", "Famille", "Somme versée pour subvenir aux besoins d'un enfant ou d'un ex-conjoint."),
    ("Régime matrimonial", "Famille", "Règles organisant les biens des époux (communauté, séparation de biens…)."),
    ("Succession", "Héritage", "Transmission du patrimoine d'une personne décédée à ses héritiers."),
    ("Réserve héréditaire", "Héritage", "Part minimale du patrimoine réservée par la loi à certains héritiers."),
    ("Testament", "Héritage", "Acte par lequel une personne organise la transmission de ses biens après sa mort."),
    ("Préavis", "Travail", "Délai à respecter avant la rupture d'un contrat de travail."),
    ("Licenciement abusif", "Travail", "Rupture du contrat sans motif légitime, ouvrant droit à réparation."),
    ("Contrat à durée déterminée (CDD)", "Travail", "Contrat de travail conclu pour une durée limitée précise."),
    ("Présomption d'innocence", "Pénal", "Principe selon lequel toute personne est innocente jusqu'à preuve de culpabilité."),
    ("Garde à vue", "Pénal", "Mesure privative de liberté de courte durée pour les besoins d'une enquête."),
    ("Plainte", "Pénal", "Acte par lequel une victime signale une infraction à la justice."),
    ("RCCM", "Entreprise", "Registre du Commerce et du Crédit Mobilier où s'immatriculent les entreprises."),
    ("OHADA", "Entreprise", "Organisation pour l'harmonisation en Afrique du droit des affaires."),
    ("Titre foncier", "Propriété", "Document officiel établissant la propriété d'un terrain."),
    ("Médiation", "Général", "Mode amiable de résolution des litiges avec l'aide d'un tiers neutre."),
]

# Actualités de démonstration (titre, résumé, contenu, catégorie, source, date ISO)
ARTICLES = [
    ("Nouvelle loi sur le foncier rural en Côte d'Ivoire",
     "La loi réforme en profondeur le régime foncier rural pour sécuriser les droits des paysans.",
     "La réforme renforce la délivrance des certificats fonciers et encadre les transactions sur les terres rurales, "
     "afin de réduire les conflits et de sécuriser les exploitants.",
     "Nouvelles lois", "Journal Officiel CI", "2024-03-15"),
    ("Droits des femmes : nouvelles dispositions du Code de la famille",
     "Des amendements renforcent la protection des femmes en matière de mariage, divorce et garde d'enfants.",
     "Les évolutions visent une plus grande égalité dans le ménage, la protection contre les violences conjugales "
     "et une meilleure prise en compte de l'intérêt de l'enfant.",
     "Droits citoyens", "Ministère de la Justice CI", "2024-02-20"),
    ("Réforme du Code pénal ivoirien",
     "Le nouveau Code pénal renforce les sanctions contre la corruption, la cybercriminalité et les violences de genre.",
     "Le texte modernise les infractions, alourdit certaines peines et introduit des dispositions sur les délits numériques.",
     "Justice", "Assemblée Nationale CI", "2024-01-10"),
    ("Code électoral : ce qui change pour les prochaines élections",
     "Les modifications prévoient de nouvelles règles pour l'inscription sur les listes électorales et la campagne.",
     "La révision encadre le financement, la période de campagne et les modalités d'inscription des électeurs.",
     "Élections", "CEI Côte d'Ivoire", "2024-04-01"),
    ("Protection sociale : extension de la CMU en zones rurales",
     "La Couverture Maladie Universelle étend sa couverture aux populations rurales.",
     "De nouveaux centres agréés permettent l'accès aux soins pour les populations éloignées des grandes villes.",
     "Social", "Ministère de la Santé CI", "2024-03-28"),
]
