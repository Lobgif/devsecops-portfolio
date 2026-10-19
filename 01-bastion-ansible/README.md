# Projet 01 — Bastion sécurisé & automatisé

> **Tu écris tout le code toi-même.** Ce README est le cahier des charges et le guide
> pas à pas. Les dossiers sont vides exprès : à toi de les remplir.

## Objectif

Durcir une VM Linux vierge **uniquement via Ansible**, depuis ton PC — zéro
configuration manuelle en SSH. À la fin, la VM est conforme aux CIS Benchmarks et le
prouve avec un scan OpenSCAP.

## Pourquoi (le « pourquoi » à mettre dans ton pitch recruteur)

Un recruteur veut voir que tu ne configures **jamais** un serveur à la main : tout est
versionné, reproductible, idempotent. Si la VM brûle, un `ansible-playbook` la
reconstruit à l'identique.

## Prérequis

- Une VM vierge (Ubuntu Server 24.04 LTS recommandé) chez un hébergeur (Hetzner, OVH, Scaleway).
- Une paire de clés SSH (`ssh-keygen -t ed25519`).
- Ansible installé sur ton PC (via `pipx` ou `asdf`).
- Accès SSH initial à la VM (souvent `root` + mot de passe fourni par l'hébergeur).

## Ce que le playbook doit faire

1. **Utilisateur** : créer un utilisateur non-root avec `sudo`, y déposer ta clé SSH publique.
2. **SSH** : désactiver `PermitRootLogin`, désactiver `PasswordAuthentication`, changer le port.
3. **Pare-feu (UFW)** : tout bloquer par défaut, autoriser seulement le nouveau port SSH (+ 80/443 plus tard).
4. **Mises à jour** : activer les mises à jour de sécurité automatiques (`unattended-upgrades`).
5. **Docker** : installer Docker Engine + plugin Compose.
6. **Hardening CIS** : appliquer un rôle de durcissement (partitions, sysctl, auditd, modules noyau…).

## Structure attendue (à créer toi-même)

```
01-bastion-ansible/
├── ansible.cfg            # config : inventaire par défaut, user, clé
├── inventory/
│   └── hosts.ini          # l'IP de ta VM, le port SSH, l'utilisateur
├── group_vars/
│   └── all.yml            # variables : port SSH, nom d'utilisateur, etc.
├── playbooks/
│   └── site.yml           # playbook principal qui appelle les rôles
└── roles/
    ├── common/            # paquets de base, mises à jour auto
    ├── ssh-hardening/     # durcissement SSH
    ├── firewall/          # UFW
    ├── docker/            # installation Docker
    └── cis-hardening/     # durcissement CIS (ou rôle externe, voir ressources)
```

## Étapes conseillées

1. `ansible --version` et teste la connexion : `ansible all -i inventory/hosts.ini -m ping`.
2. Commence par le rôle `common`, puis `ssh-hardening` (⚠️ garde une session SSH ouverte
   pendant que tu testes, pour ne pas te verrouiller dehors).
3. Ajoute `firewall`, teste que le nouveau port répond **avant** de couper l'ancien.
4. Ajoute `docker`, vérifie avec `docker run hello-world`.
5. Termine par `cis-hardening`.
6. Lance deux fois le playbook : la 2ᵉ exécution doit afficher `changed=0` (**idempotence**).

## Critères de réussite

- [ ] `ssh root@vm` → refusé.
- [ ] `ssh -p <ancien_port>` → refusé ; `ssh -p <nouveau_port>` → OK par clé only.
- [ ] `ufw status` → `deny (incoming)` par défaut.
- [ ] Playbook idempotent (`changed=0` au 2ᵉ run).
- [ ] `ansible-lint` → zéro erreur.
- [ ] Scan OpenSCAP → score de conformité documenté (avant/après).

## Qualité du code (ce que le recruteur inspecte)

- Rôles **modulaires** et réutilisables, pas un seul gros playbook.
- Variables externalisées dans `group_vars/`, **jamais** de secret en clair
  (utiliser Ansible Vault).
- `ansible-lint` intégré, idéalement en CI.
- README du rôle expliquant ses variables.

## Ressources

- Ansible (docs officielles) — https://docs.ansible.com/ansible/latest/index.html
- Ansible-Lint — https://ansible.readthedocs.io/projects/lint/
- Ansible Vault — https://docs.ansible.com/ansible/latest/vault_guide/index.html
- OpenSCAP — https://www.open-scap.org/
- CIS Benchmarks — https://www.cisecurity.org/cis-benchmarks
- UFW (Ubuntu) — https://help.ubuntu.com/community/UFW
- Docker Engine sur Ubuntu — https://docs.docker.com/engine/install/ubuntu/
- unattended-upgrades (Debian/Ubuntu) — https://wiki.debian.org/UnattendedUpgrades
