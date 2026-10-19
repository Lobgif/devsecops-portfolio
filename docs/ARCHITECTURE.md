# Architecture & décisions

## Décision 1 — Application support : hybride

| Phase | Application | Pourquoi |
|-------|-------------|----------|
| 1 (01→04) | `agoraci` (front + back, réelle) | Récit de **ownership** : une vraie app qu'on maîtrise, idéale pour Docker, CI/CD et hardening |
| 3 (07→10) | [Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo) | Déjà éclatée en microservices : idéale pour service mesh, mTLS, NetworkPolicies, tracing distribué |

> L'application n'est jamais le livrable. Tout le travail porte sur l'infra et la sécurité.

---

## Décision 2 — Structure des dépôts : hub, puis split au GitOps

On commence par un dépôt **vitrine** lisible, puis on sépare **quand un outil l'exige**
(ce qui est exactement la pratique en entreprise).

```
devsecops-portfolio        ← CE dépôt (vitrine)
  ├── README.md               page d'accueil + parcours
  ├── docs/                   ROADMAP, ARCHITECTURE
  ├── 01-bastion-ansible/     Projet 01
  ├── 02-cicd-pipeline/       Projet 02 (à créer)
  ├── 03-hardening-molecule/  Projet 03 (à créer)
  └── 04-k3s-gitops/          Projet 04 : install K3s + Argo CD

devsecops-gitops           ← 2ᵉ dépôt, créé AU projet 04
  └── manifests/              c'est CE dépôt qu'Argo CD surveille

infra-terraform            ← 3ᵉ dépôt, créé en Phase 2
  └── modules/               VPC, EKS/GKE, etc.
```

### Pourquoi séparer `devsecops-gitops` ?

Le GitOps repose sur un principe : **l'état désiré du cluster vit dans un dépôt Git
dédié**, qu'Argo CD surveille en continu. Mélanger le code applicatif et les manifestes
de déploiement dans un même dépôt crée des boucles (un build déclenche un commit qui
déclenche un build…) et brouille la séparation des responsabilités.

Montrer qu'on comprend **pourquoi** cette séparation existe est un point bonus face à un
recruteur.

---

## Décision 3 — Progression des coûts

| Phase | Ressources | Coût |
|-------|-----------|------|
| 1 | 1 VM (4 vCPU / 8 Go) | ~10-15 €/mois |
| 2 | Free tier cloud + `terraform destroy` après chaque test | ~quelques centimes |
| 3 | Cluster managé allumé seulement pendant les sessions de travail | variable, maîtrisé |

Quand le parcours le justifiera (HA réelle, multi-nœuds permanents), passage à 3-5
serveurs assumé.

---

## Schéma d'architecture

> À produire avec Excalidraw ou draw.io, puis exporter en PNG/SVG dans `docs/img/`.
> Un schéma par phase, référencé depuis les READMEs.

- [ ] Schéma Phase 1 (VM unique : SSH, Docker, K3s, Argo CD)
- [ ] Schéma Phase 2 (VM de contrôle → Cloud via Terraform)
- [ ] Schéma Phase 3 (cluster + mesh + Vault + Falco + stack observabilité)

---

## Ressources

- GitOps (principes, OpenGitOps) — https://opengitops.dev/
- Argo CD — https://argo-cd.readthedocs.io/en/stable/
- Google Online Boutique — https://github.com/GoogleCloudPlatform/microservices-demo
- Excalidraw — https://excalidraw.com/
- diagrams.net (draw.io) — https://www.drawio.com/
