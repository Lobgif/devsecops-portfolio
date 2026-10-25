# DevSecOps Portfolio

Parcours DevSecOps **de bout en bout**, construit brique par brique comme en
entreprise : d'une seule VM durcie à la main jusqu'à un cluster Kubernetes managé,
sécurisé en profondeur et entièrement observable.

> Pas de projet tutoriel jetable. Chaque projet est reproductible (`terraform apply`
> / `make deploy`), documenté, et réutilise ce que le précédent a construit.

---

## Principe

L'application n'est **pas** le sujet : tout le focus est sur **l'infrastructure, la
sécurité native (Shift Left), la gouvernance et l'observabilité**.

- **Phase 1** → application réelle [`agoraci`](https://github.com/Lobgif) (front + back) :
  montre la maîtrise d'un cas concret (Docker, CI/CD, hardening).
- **Phase 3** → application microservices de référence
  ([Google Online Boutique](https://github.com/GoogleCloudPlatform/microservices-demo)) :
  idéale pour le service mesh, le Zero Trust et l'observabilité distribuée.

---

## Le parcours en 10 projets

### Phase 1 — La VM unique (OS, conteneur, automatisation) · ~10-15 €/mois

| # | Projet | Stack principale | Statut |
|---|--------|------------------|--------|
| 01 | [Bastion sécurisé & automatisé](01-bastion-ansible/) | Ansible, UFW, OpenSCAP, CIS | 🚧 en cours |
| 02 | Pipeline CI/CD « Zero Vulnerability » | GitHub Actions / GitLab CI, Gitleaks, SonarQube, Trivy, Cosign | ⏳ à venir |
| 03 | Hardening à l'échelle + tests | Ansible roles, Molecule, OpenSCAP | ⏳ à venir |
| 04 | Kubernetes de poche + GitOps | K3s, Helm, Argo CD | ⏳ à venir |

### Phase 2 — Passage au Cloud (IaC, échelle) · Free tier + `terraform destroy`

| # | Projet | Stack principale | Statut |
|---|--------|------------------|--------|
| 05 | IaC d'un cluster d'entreprise | Terraform, AWS/GCP, Checkov/Tfsec | ⏳ à venir |
| 06 | Vrai K8s managé + migration GitOps | Terraform, EKS/GKE, Argo CD | ⏳ à venir |

### Phase 3 — SecOps avancé (sur le cluster cloud)

| # | Projet | Stack principale | Statut |
|---|--------|------------------|--------|
| 07 | Service Mesh / Zero Trust | Istio ou Linkerd, mTLS, NetworkPolicies | ⏳ à venir |
| 08 | Gestion des secrets d'entreprise | HashiCorp Vault, ESO | ⏳ à venir |
| 09 | Sécurité Runtime | Kyverno / OPA, Falco | ⏳ à venir |
| 10 | Observabilité totale | Prometheus, Grafana, Loki, OpenTelemetry, Jaeger | ⏳ à venir |

Détail complet de chaque projet : **[docs/ROADMAP.md](docs/ROADMAP.md)**.

---

## Architecture des dépôts

Un parcours lisible **et** conforme aux pratiques pro (le GitOps impose la séparation
entre le code et les manifestes de déploiement) :

```
devsecops-portfolio   ← ce dépôt : vitrine, roadmap, projets 01 → 03
devsecops-gitops      ← créé au projet 04 (Argo CD le surveille)
infra-terraform       ← créé en Phase 2
```

Détail et justification : **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

---

## Pourquoi cet ordre

- **Progression financière** : les projets 01→04 ne coûtent que le prix de la VM
  (~10-15 €/mois) le temps d'assimiler Linux, les conteneurs et le GitOps.
- **Zéro friction** : on apprend Kubernetes (04) dans un environnement simple avant
  d'y ajouter la complexité du Cloud (05).
- **Cohérence** : chaque outil arrive quand il résout un problème créé par le projet
  précédent.

---

## Ressources

Documentations officielles des outils du parcours (vérifiées le 2026-10-06).

- Ansible — https://docs.ansible.com/ansible/latest/index.html
- OpenSCAP — https://www.open-scap.org/
- CIS Benchmarks — https://www.cisecurity.org/cis-benchmarks
- Trivy — https://trivy.dev/
- Gitleaks — https://github.com/gitleaks/gitleaks
- SonarQube — https://docs.sonarsource.com/sonarqube-server/latest/
- Cosign (Sigstore) — https://docs.sigstore.dev/cosign/signing/overview/
- Distroless — https://github.com/GoogleContainerTools/distroless
- K3s — https://docs.k3s.io/
- Helm — https://helm.sh/docs/
- Argo CD — https://argo-cd.readthedocs.io/en/stable/
- Terraform — https://developer.hashicorp.com/terraform/docs
- Checkov — https://www.checkov.io/
- Tfsec — https://aquasecurity.github.io/tfsec/
- Istio — https://istio.io/latest/docs/
- Linkerd — https://linkerd.io/2/overview/
- HashiCorp Vault — https://developer.hashicorp.com/vault/docs
- Kyverno — https://kyverno.io/docs/
- Falco — https://falco.org/docs/
- Prometheus — https://prometheus.io/docs/
- Grafana Loki — https://grafana.com/docs/loki/latest/
- OpenTelemetry — https://opentelemetry.io/docs/
- Jaeger — https://www.jaegertracing.io/docs/
- Google Online Boutique — https://github.com/GoogleCloudPlatform/microservices-demo
