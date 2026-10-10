# Jamakan — Gouvernance des groupes (« démocratie encadrée »)

Document de référence **avant de coder**. Principe directeur : **aucune décision unilatérale**,
**tous les seuils réglables depuis l'admin** (jamais en dur), et **réutilisation du moteur de vote
existant** (`ModerationProposal` + `ModerationVote`).

Statuts : ✅ existe · ⏳ à construire

---

## 1. Principes fondateurs
1. **Anti-chaos** : on ne crée pas un groupe « comme ça » — il faut une demande prouvée.
2. **Anti-dictature** : personne (ni fondateur, ni modérateur) n'expulse seul ; tout passe par un vote.
3. **Neutralité du super-admin** : il n'agit que sur les violations **globales** (illégal, harcèlement, spam), jamais sur les opinions.
4. **Tout est paramétrable** en admin (seuils, délais, poids) pour ajuster pendant test / lancement / production.

## 2. Paramètres configurables (Admin → Paramètres)
| Clé | Défaut proposé | Rôle |
|---|---|---|
| `group_creation_threshold` | **30** | Nb de soutiens pour créer un groupe |
| `group_direct_creation_min_rep` | (option) | Réputation min. pour créer **sans** passer par le vote (0 = désactivé) |
| `admission_deliberation_min` | 15–30 | Délai avant révélation/intégration après un vote d'admission |
| `election_cycle_days` | 365 | Cycle d'élection des modérateurs |
| `election_effectif_variation_pct` | 50 | Déclenche une élection si l'effectif varie de X% |
| `removal_supermajority_pct` | 66 | Super-majorité pour retirer un membre |
| `removal_cooldown_hours` | 48 | Délai avant application d'un retrait (appel possible) |
| `jury_size` | 12 | Taille du jury tiré au sort (si mode jury) |
| `vote_weight_cap` | 2.0 | Poids **max** d'un vote (équilibre — « pas trop d'écart ») |
| `superadmin_group_delete_notice_h` | 72 | Préavis avant suppression d'un groupe |
| `superadmin_group_delete_grace_h` | 48 | Délai après préavis avant suppression effective |

## 3. Création d'un groupe — « démocratie par la demande »
1. Un membre **propose** (nom, catégorie, description, motivation).
2. Les autres **soutiennent** (« je veux rejoindre »).
3. À **`group_creation_threshold` soutiens (30)** → le groupe est **créé automatiquement**.
4. Le proposeur devient **fondateur**, les soutiens = **membres fondateurs**.
- Option : création **directe** pour comptes très fiables (réputation ≥ `group_direct_creation_min_rep` ou expert vérifié).
- Garde-fou anti-spam : seuls les **comptes vérifiés** peuvent proposer.

## 4. Adhésion (rejoindre)
- **Voir** un groupe **public** + son contenu = **ouvert à tous, même non-inscrits** (découverte / SEO).
- **Participer** (proposer, soutenir, voter, rejoindre, poster) = **inscription obligatoire** (email/mot de passe **ou Google** — mêmes droits).
- **Groupe public** : adhésion libre.
- **Groupe privé / sensible** : demande → **vote d'admission** de tous les membres.
  - **1 vote unique** par membre, **délai ferme** (pas de changement après).
  - **Résultats anonymisés**, **délibération automatique** après `admission_deliberation_min` (15–30 min) → intégration.
  - **Votes groupés** (oui/non) possibles à **dates fixes** (sessions de vote) pour éviter le vote permanent.
- **Identité** : chacun choisit **pseudo ou vrai nom** (`display_pref` existe déjà). Les comptes **vérifiés / à vrai nom** portent un **marqueur de confiance** et **pèsent plus** (voir §6).

## 5. Modérateurs — élus, jamais auto-désignés
- Au-delà d'une certaine taille, les membres **élisent** les modérateurs.
- Déclenchement : par **cycle** (`election_cycle_days`) **ou** quand l'effectif varie de `election_effectif_variation_pct`.
- Le fondateur n'a **pas** de pouvoir spécial permanent : il est membre comme les autres (peut être élu).

## 6. Vote pondéré (équilibré)
Le poids d'un vote dépend du **palier de contribution** — mais **plafonné** (`vote_weight_cap`, ex. 2.0) pour rester équilibré :
| Palier | Poids indicatif |
|---|---|
| Membre (base) | 1.0 |
| Membre actif (≥75) | 1.2 |
| Contributeur (≥100) | 1.4 |
| Contributeur confirmé (≥200 & 70%) | 1.6 |
| Référence (≥500 & >90%) | 1.8 |
| **Expert vérifié** (dans son domaine) | + bonus (plafonné à `vote_weight_cap`) |
> Objectif : les membres sérieux pèsent **un peu** plus, sans écraser les autres. Tous les poids sont **configurables**.

## 7. Retrait d'un membre — 3 mécanismes **combinables** (non redondants)
Aucune expulsion unilatérale. Selon la situation, un ou plusieurs mécanismes :
- **(a) Vote pondéré à super-majorité** (`removal_supermajority_pct`, ex. 66%) — décision de la communauté.
- **(b) Jury tiré au sort** (`jury_size` membres aléatoires) — évite les clans / règlements de comptes.
- **(c) Période de refroidissement** (`removal_cooldown_hours`) — délai avant application + **droit d'appel**.
- Les membres peuvent **déclencher** eux-mêmes un vote de retrait.
- **(d) Modération plateforme** : uniquement pour **violation claire** (contenu signalé + confirmé).

## 8. Super-admin (toi) — portée limitée + préavis
- N'intervient que sur les **violations globales** (illégal, harcèlement, spam). **Jamais** sur les opinions/débats.
- **Suppression d'un groupe** : **préavis `72h`** (notification aux membres) → suppression effective **`48h` après** (soft-delete + délai de grâce, **annulable**).
- **Bannir / bloquer** une personne : selon gravité (immédiat pour illégal/harcèlement).

## 9. Rôles & permissions (cible)
| Action | Qui |
|---|---|
| Voir groupe public + contenu | Tous (même non-inscrits) |
| Proposer / soutenir / rejoindre / voter | Membres inscrits |
| Créer un groupe | Via proposition + 30 soutiens (ou compte très fiable) |
| Élire / être modérateur | Membres du groupe |
| Retirer un membre | Vote (pondéré + jury + refroidissement) |
| Supprimer un groupe | Super-admin, avec préavis 72h/48h |

## 10. Existant vs à construire
| Élément | État |
|---|---|
| Moteur de vote au seuil (`ModerationProposal`/`ModerationVote`, vote unique) | ✅ existe |
| Rôles membre/admin/créateur · groupes privés · paramètres site configurables | ✅ existe |
| Création par **proposition + seuil de soutiens** (+ création directe gated) | ✅ (Phase 1) |
| **Vote d'admission** (groupe privé : rejoindre = demande soumise au vote des membres) | ✅ (Phase 3) |
| **Élection des modérateurs** (membre proposé → vote → rôle admin) | ✅ (Phase 3) |
| Anonymisation des votes + délai de délibération + sessions groupées + cycles auto d'élection | ⏳ (raffinements Phase 3) |
| **Vote pondéré plafonné** par réputation | ✅ (Phase 2) |
| **Retrait** démocratique d'un membre (vote pondéré) | ✅ (Phase 2) |
| **Suppression super-admin avec préavis** (soft-delete programmé + balayage) | ✅ (Phase 4) |
| Jury tiré au sort + refroidissement + appel (raffinements du retrait) | ⏳ |

## 11. Plan de construction (phasé)
1. ✅ **Phase 1** — Création par proposition + seuil de soutiens (+ paramètres admin)
2. ✅ **Phase 2** — Vote pondéré plafonné + retrait démocratique d'un membre
3. ✅ **Phase 3 (cœur)** — Vote d'admission (groupes privés) + élection des modérateurs par vote
   · ⏳ raffinements : anonymisation, délai de délibération, sessions groupées, cycles auto, jury tiré au sort
4. ✅ **Phase 4** — Suppression super-admin avec préavis (soft-delete programmé + balayage horaire)

---

_Document vivant : on l'ajuste au fil des décisions et des retours du MVP._
