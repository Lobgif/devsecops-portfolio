# Jamakan — Plan d'amélioration continue

Document **vivant** : il liste ce qui est fait, en cours, et à faire. On le met à jour au fur et à
mesure. Priorité : **valider le produit (MVP) avec de vrais utilisateurs**, puis durcir/scaler.

Statuts : ✅ fait · 🔨 en cours · ⏳ à faire · 💡 idée à valider

---

## 0. Socle MVP (fait)
- ✅ Frontend Nuxt 3 (SSR) + backend FastAPI (monolithe modulaire), **services séparés**
- ✅ PostgreSQL + pgvector (RAG « Nanan », recherche hybride)
- ✅ Auth (JWT, Google OAuth, sessions, honeypot + Turnstile)
- ✅ Forums (groupes, discussions, réponses, votes, réputation, modération, signalements)
- ✅ Déploiement prod : VPS Oracle ARM gratuit, HTTPS auto (Traefik/Let's Encrypt)
- ✅ CI/CD GitLab (build + scan + **déploiement auto**), cache `mode=max`
- ✅ Releases auto (semantic-release : version + CHANGELOG + tag + Release GitLab)

## 1. Intelligence & communauté (le cœur différenciant)
- ✅ Nanan **à la demande** (pas automatique)
- ✅ Nanan **apprend des réponses communautaires** (flywheel) — auto-indexation au vote
- ✅ **Critères de qualité** (score net + non masquée + aucun signalement) au lieu des likes bruts
- ✅ Nanan **routé par catégorie** (droit → juridique, sinon général)
- ✅ **Badge expert vérifié** (candidature + validation admin) + badges de contribution évolutifs
      (paliers rigoureux : Membre actif ≥75, Contributeur ≥100, Confirmé ≥200 & 70%, Référence ≥500 & >90%)
- ✅ Réponses d'experts **pondérées plus fort** dans l'apprentissage
- ✅ **Boucle brouillon** : Nanan propose un brouillon « à valider » → validé par la communauté (badge de
      confiance) ; seules les réponses **humaines** nourrissent le RAG (anti-écho)
- ✅ **Fraîcheur** : recherche exclut l'abrogé + réponses communautaires trop anciennes (> 24 mois, config.)
- ✅ **Catégories élargies** : 12 catégories (Démarches admin, Santé, Emploi, Business, Finance, Tech,
      Immobilier, Politique, Vie pratique…) + groupes de démarrage semés au lancement
- 💡 Enrichir le corpus avec des **sources officielles publiques** par catégorie (lois, données publiques)
      — ⚠️ jamais le contenu **propriétaire** de concurrents (copyright)
- 💡 Types de badges par **métier** (avocat, médecin, agent, comptable…) + niveaux de confiance

### Gouvernance des groupes — « démocratie encadrée » (à construire)
- ⏳ **Création** par **proposition + seuil de soutiens** (ex. 10) au lieu de « n'importe qui »
      (+ garde-fou : compte vérifié / réputation minimale ; option création directe pour comptes très fiables)
- ⏳ **Retrait d'un membre** par **vote du groupe** (super-majorité), jamais unilatéral par le fondateur/admin
- ⏳ **Modérateurs élus** par les membres (pas auto-désignés)
- ⏳ **Vote d'admission** pour les groupes privés/sensibles
- Le super-admin plateforme n'intervient que sur les **violations globales** (illégal, harcèlement), jamais sur les opinions

## 2. Mesure & décision (Lean Startup / Ray Dalio)
- ⏳ **Tableau de bord « Métriques » admin** (AARRR, actionnable, pas illusoire) :
  activation, rétention D7/D30, engagement (questions/réponses), qualité (% réponses acceptées),
  IA (requêtes Nanan, % répondues vs échecs) — requêtes SQL dans l'admin
- ⏳ (après traction) **Prometheus + Grafana** pour l'observabilité technique (latence, erreurs,
  ressources), avec lien dans l'admin

## 3. Qualité & robustesse (avant de scaler)
- ⏳ **Tests automatisés** (backend pytest + frontend) — le vrai manque actuel
- ⏳ Journalisation structurée + alerting basique (erreurs, quotas IA)
- ⏳ Sauvegardes automatiques Postgres + stockage objet

## 4. Scale & infrastructure (quand le trafic le justifie)
- ⏳ Haute dispo : Docker Swarm mono-nœud (rolling updates + Docker secrets), puis multi-nœuds si besoin
- ⏳ Build ARM natif en CI (runners ARM) → déploiement par `pull` au lieu de rebuild
- ⏳ CDN / cache pour les pages publiques (SEO + charge)
- 💡 Séparer un worker dédié (jobs d'ingestion) si la charge IA grandit

## 5. Croissance & valeur
- ⏳ SEO (sitemap, données structurées) — partiellement en place
- ⏳ Modèle de confiance : mise en avant des experts, classement, gamification saine
- 💡 App mobile / PWA
- 💡 Partenariats (institutions, ordres professionnels) pour crédibiliser les catégories

---

_Dernière mise à jour : au fil des développements. Chaque item passe de ⏳ → 🔨 → ✅._
