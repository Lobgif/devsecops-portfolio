# Roadmap détaillée — 10 projets DevSecOps

> Ce document décrit **quoi construire et pourquoi**. Le code est écrit à la main,
> projet par projet. Chaque dossier `NN-*/` contient un README guide plus précis.

Légende statut : 🚧 en cours · ⏳ à venir · ✅ terminé

---

## Phase 1 — La VM unique

**Budget :** ~10-15 €/mois (ex. Hetzner CX22/CX32, OVH, Scaleway). Cette VM est aussi
ton **serveur de contrôle** pour la Phase 2.

### Projet 01 — Bastion sécurisé & automatisé 🚧

| | |
|---|---|
| **Objectif** | Gérer un système Linux sans jamais y toucher manuellement en SSH |
| **Stack** | Ansible, Ansible-Lint, UFW, OpenSCAP, CIS Benchmarks |
| **Livrables** | Playbooks qui : désactivent root et le SSH par mot de passe, changent le port SSH, configurent UFW, installent Docker, durcissent l'OS (CIS) |
| **Preuve** | Rapport de scan OpenSCAP avant/après (score de conformité qui monte) |
| **Ce que le recruteur regarde** | Code Ansible propre, modulaire, idempotent, linté |
| **Prérequis** | Clés SSH publique/privée, une VM vierge, Git |

### Projet 02 — Pipeline CI/CD « Zero Vulnerability » ⏳

| | |
|---|---|
| **Objectif** | Bloquer le code vulnérable ou les fuites de secrets **avant** tout déploiement |
| **Stack** | GitHub Actions / GitLab CI, Gitleaks, SonarQube, Trivy, Cosign, Dockerfile multi-stage |
| **Livrables** | À chaque push : scan secrets (Gitleaks) → SAST (SonarQube) → build image multi-stage → scan image (Trivy) → signature (Cosign) → push GHCR |
| **Preuve** | Badges verts, image distroless/non-root, image signée vérifiable |
| **Ce que le recruteur regarde** | Images légères et sécurisées, zéro root, chaîne de confiance (signature) |
| **Lien** | Le pipeline se connecte en SSH à la VM (projet 01) pour déployer via Compose |

### Projet 03 — Hardening à l'échelle + tests ⏳

| | |
|---|---|
| **Objectif** | Tester l'automatisation de façon industrielle avant la prod |
| **Stack** | Ansible roles, Molecule, OpenSCAP |
| **Livrables** | Rôles testés automatiquement dans des conteneurs via Molecule à chaque modif |
| **Preuve** | CI qui exécute `molecule test` et un scan OpenSCAP en continu |
| **Ce que le recruteur regarde** | Tests unitaires/intégration sur de l'infra — rare chez un junior |

### Projet 04 — Kubernetes de poche + GitOps ⏳

| | |
|---|---|
| **Objectif** | Apprendre l'orchestration et le GitOps sans payer un cluster managé |
| **Stack** | K3s, Helm, Argo CD |
| **Livrables** | App du projet 02 packagée en chart Helm, déployée par Argo CD qui surveille le dépôt `devsecops-gitops` |
| **Preuve** | Un commit dans Git = déploiement automatique, plus jamais de `kubectl apply` manuel |
| **Ce que le recruteur regarde** | YAML propres, Helm dynamique, séparation code/manifestes |
| **Note** | C'est ici qu'on crée le **2ᵉ dépôt** `devsecops-gitops` (voir ARCHITECTURE.md) |

---

## Phase 2 — Passage au Cloud

**Budget :** Free tiers AWS/Azure/GCP. On crée, on teste 1 h, puis `terraform destroy`
(coût proche de 0 €). La VM de Phase 1 sert de machine de contrôle.

### Projet 05 — IaC d'un cluster d'entreprise ⏳

| | |
|---|---|
| **Objectif** | Déployer une infra cloud complète, sécurisée, reproductible |
| **Stack** | Terraform, AWS/Azure/GCP, Checkov/Tfsec, backend S3 + verrou DynamoDB |
| **Livrables** | Modules réutilisables : VPC, sous-réseaux public/privé, NAT, firewall. Scan sécu du code Terraform en CI |
| **Preuve** | `terraform plan`/`apply` propre, blocage CI si disque non chiffré ou port ouvert |
| **Ce que le recruteur regarde** | State distant sécurisé, modularité des modules |

### Projet 06 — Vrai K8s managé + migration GitOps ⏳

| | |
|---|---|
| **Objectif** | Prouver que la logique GitOps (projet 04) passe à l'échelle cloud |
| **Stack** | Terraform, AWS EKS ou GCP GKE, Argo CD |
| **Livrables** | Terraform provisionne le cluster managé ; Argo CD du projet 04 s'y branche |
| **Preuve** | La même app tourne sur K3s **et** sur EKS/GKE sans changer la logique de déploiement |
| **Ce que le recruteur regarde** | Transition transparente K3s → EKS grâce au GitOps |

---

## Phase 3 — SecOps avancé (sur le cluster cloud)

À partir d'ici on bascule sur l'app microservices de référence (Online Boutique).

### Projet 07 — Service Mesh / Zero Trust ⏳

| | |
|---|---|
| **Objectif** | Sécuriser et chiffrer les flux **internes** au cluster |
| **Stack** | Istio ou Linkerd, mTLS, NetworkPolicies |
| **Livrables** | mTLS auto entre pods, routage canary (10 % vers la V2), le frontend ne peut pas joindre la DB directement |
| **Preuve** | Schéma des flux, démonstration qu'un flux interdit est bloqué |
| **Ce que le recruteur regarde** | Maîtrise fine des flux internes (Zero Trust) |

### Projet 08 — Gestion des secrets d'entreprise ⏳

| | |
|---|---|
| **Objectif** | Supprimer les mots de passe des codes et des configs |
| **Stack** | HashiCorp Vault, External Secrets Operator (ou Vault injector) |
| **Livrables** | L'app s'authentifie via son ServiceAccount K8s, récupère les creds DB en RAM, rien sur disque ni dans Git |
| **Preuve** | `grep` du dépôt et des manifestes : aucun secret en clair. Rotation démontrée |
| **Ce que le recruteur regarde** | Cycle de vie des secrets, rotation automatique |

### Projet 09 — Sécurité Runtime ⏳

| | |
|---|---|
| **Objectif** | Détecter et bloquer les intrusions en temps réel |
| **Stack** | Kyverno ou OPA Gatekeeper, Falco |
| **Livrables** | Politiques qui interdisent les pods root/sans limites. Falco détecte la lecture de `/etc/shadow` → alerte Slack/Discord ou kill |
| **Preuve** | Simulation d'attaque filmée/capturée + alerte déclenchée |
| **Ce que le recruteur regarde** | Réponse à incident en direct (Incident Response) |

### Projet 10 — Observabilité totale ⏳

| | |
|---|---|
| **Objectif** | La tour de contrôle : santé + sécurité de toute la plateforme |
| **Stack** | Prometheus, Grafana, Loki, OpenTelemetry, Jaeger |
| **Livrables** | Golden Signals (latence, trafic, erreurs, saturation), logs centralisés (Loki), tracing bout-en-bout (Jaeger), alertes Falco (projet 09) remontées |
| **Preuve** | Dashboard Grafana unique ; diagnostic d'une panne en corrélant log ↔ métrique ↔ trace |
| **Ce que le recruteur regarde** | Capacité à corréler les signaux pour diagnostiquer vite |

---

## Présentation aux recruteurs

Pour chaque projet, le README doit contenir :

1. **Schéma d'architecture** clair (Excalidraw ou diagrams.net / draw.io).
2. **Problématique & Solution** : pourquoi ces choix technologiques.
3. **Démarrage rapide** : cloner → `terraform apply` ou `make deploy` → l'infra se monte seule.

---

## Ressources

Documentations officielles (vérifiées le 2026-10-06) — voir la liste complète dans le
[README racine](../README.md#ressources).
