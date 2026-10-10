# Sondages Jamakan — Analyse et feuille de route

Statut : document d'analyse et de cadrage produit. Aucun code n'est encore
ecrit. Ce document consigne toutes les options discutees, pour decider avant de
construire.

Contexte : Jamakan (« la voix du peuple » en dioula) est une plateforme
citoyenne (forum, groupes, Q&A, assistant IA Nanan). La fonctionnalite Sondages
est une extension naturelle de cette mission.

---

## 1. Vision et concept

Une page dediee ou des createurs autorises posent une question a choix multiples
et ou les gens votent. Les sujets sont ouverts : societe, politique, referendums
informels, mais aussi etudes de marche pour des entreprises.

Trois sources de valeur :

- Civique : donner une voix mesurable aux citoyens.
- Commerciale : les entreprises et institutions paient pour de la donnee.
- Differenciant : peu d'acteurs offrent en Cote d'Ivoire des sondages fiables et
  cibles.

Principe directeur retenu : la sequence prime sur les fonctionnalites. On demarre
civique et simple, on prouve l'engagement, puis on monetise. Voir section 9.

---

## 2. Types de sondages et ciblage de l'audience

Portee (choisie par le createur) :

- Public : tout le monde via le lien. Exige au minimum la verification par
  telephone pour rester credible.
- Inscrits uniquement : reserve aux membres Jamakan.
- Prive : sur invitation, lien secret ou liste de participants.

Ciblage demographique (optionnel, pour les etudes de marche) :

- Region, tranche d'age, profession. Le champ profession existe deja sur les
  profils ; region et age seraient a ajouter (optionnels a l'inscription).

Formats de sondage possibles :

- Choix unique, choix multiple.
- Echelle (ex. de 1 a 5, tout a fait d'accord / pas du tout d'accord).
- Classement d'options.
- Question ouverte courte (a moderer, plus difficile a analyser).

---

## 3. Qui peut publier et monetisation

Publication reservee aux personnes badgees. C'est le levier de revenu evoque.
Modeles de revenu combinables :

- Badge « Sondeur verifie » payant (abonnement) donnant le droit de publier.
- Paiement au sondage (creer un sondage coute un montant fixe).
- Paliers de portee (payer pour atteindre jusqu'a N repondants).
- Ciblage payant (par region, age, profession).
- Rapport et analytics premium (export PDF ou CSV, graphiques, croisements
  demographiques). C'est ce que les entreprises paient reellement.
- Sondage sponsorise ou mis en avant sur la page.

Note importante : la monetisation la plus simple et la plus rentable au depart
est de vendre les resultats et analytics, pas de payer les repondants (voir
sections 5 et 9).

---

## 4. Fiabilite : le defi central « une personne, un vote »

C'est le point le plus difficile. Verite a assumer : le sondage en ligne
100 % infraudable n'existe pas, meme les Etats ont du mal. La bonne approche
n'est pas une solution unique mais des niveaux de fiabilite selon l'enjeu, avec
le niveau affiche publiquement sur chaque sondage.

### Niveaux de verification

| Niveau | Verification | Fiabilite | Friction / cout | Usage |
|---|---|---|---|---|
| 1 - Compte | Inscrit + email verifie (deja en place) | Moyenne (comptes multiples possibles) | Faible | Sondages legers, societe |
| 2 - Telephone | 1 vote par numero verifie par OTP SMS | Forte (un numero est rare et coute cher) | Moyenne + cout SMS | Referendums, decisions, sujets serieux |
| 3 - Identite (plus tard) | Piece d'identite / KYC leger | Tres forte | Elevee | Etudes officielles, clients premium |

Pourquoi le telephone est meilleur que l'email : un email est gratuit et
illimite, un numero de telephone est rare, coute de l'argent et est lie a une
SIM (en Cote d'Ivoire l'enregistrement SIM est encadre). C'est le meilleur
rempart pratique, sans etre parfait.

### Garde-fous transversaux (en plus du niveau choisi)

- Turnstile (deja en place) pour bloquer les robots.
- Empreinte d'appareil et adresse IP pour detecter les votes en rafale.
- Contrainte d'unicite en base (poll_id + identite hachee) rendant le double vote
  techniquement impossible.
- Detection d'anomalies (pic soudain, meme IP ou meme appareil) avec signalement
  ou annulation.
- Limites de debit (rate limiting), deja presentes cote backend.

### Recommandation

Le createur choisit le niveau de fiabilite ; ce niveau est affiche sur le
sondage (« verifie par telephone » = credible ; « ouvert » = indicatif). La
fiabilite devient un argument de vente et un label (« Sondage verifie Jamakan »).

---

## 5. Systeme de recompenses (points echangeables)

Idee : recompenser les repondants avec des points, echangeables a terme contre
des cartes cadeaux chez des enseignes partenaires, du credit telephonique ou du
Mobile Money. But : augmenter la participation, principal defi de tout sondage.

### Le paradoxe de la recompense

Des que repondre rapporte de l'argent, deux problemes apparaissent :

- La fraude explose : incitation forte a creer des comptes multiples et a
  multiplier les numeros pour farmer des points. L'anti-double-vote passe de
  important a vital.
- La qualite des donnees chute : on repond pour le point, pas sincerement
  (reponses au hasard, a toute vitesse), ce qui pollue la donnee vendue.

Consequence : toute recompense en argent impose la verification telephone
(niveau 2) et des controles qualite (ci-dessous).

### Qui finance les recompenses

Une recompense reelle coute de l'argent. Le seul modele durable :

- Sondages payants (entreprises et institutions) : une partie de ce que paie le
  client finance les recompenses des repondants (modele des panels
  professionnels : le client paie, le repondant touche une part, la plateforme
  prend sa marge).
- Sondages civiques et gratuits : pas de financement, donc pas de recompense en
  argent.

Deux categories a distinguer clairement :

| Type | Recompense | Financement |
|---|---|---|
| Sondage payant (entreprise) | Points convertibles (carte, credit, argent) | Le client |
| Sondage civique (societe, referendum) | Points de gamification (badges, classement, statut), sans valeur monetaire | Aucun |

Cette separation protege aussi le civique : personne ne farme un referendum
puisqu'il ne rapporte pas d'argent.

### Controles qualite indispensables (comme les panels professionnels)

- Verification telephone obligatoire pour tout sondage recompense.
- Questions-pieges d'attention (ex. « cochez la case 3 ») pour eliminer robots et
  reponses non serieuses.
- Temps minimum passe sur le sondage (repondre en 2 secondes = rejete).
- Plafonds : maximum de points par jour, anciennete de compte minimale.
- Seuil de retrait (ex. atteindre X points avant conversion) pour que le
  micro-farming ne vaille pas le coup.
- Verification a l'encaissement (KYC leger) avant de donner une recompense.
- Detection d'anomalies (meme appareil ou IP, pics) avec suspension.

### La recompense en Cote d'Ivoire : commencer simple

- Le plus rapide et universel : credit telephonique (airtime) et Mobile Money
  (Orange Money, MTN MoMo, Wave). Conversion instantanee, pas besoin d'un reseau
  de magasins.
- Les cartes cadeaux d'enseignes viennent apres, quand le volume permet de
  negocier des partenariats.

### Attention reglementaire

- Recompenser puis encaisser peut toucher au jeu ou a la loterie, au fiscal et,
  des qu'on manipule du Mobile Money, a la regulation financiere.
- Donnees personnelles (telephone) : cadre ARTCI (protection des donnees en Cote
  d'Ivoire) : consentement, conservation limitee, securite.
- A cadrer juridiquement avant de lancer les vrais paiements.

### Recompenses non monetaires (moins de fraude, moins cher)

- Statut et reputation (deja en place), deblocage de fonctions, visibilite (sa
  question ou son commentaire mis en avant).
- Sondage sponsorise : une marque finance une cagnotte (par ex. en credit
  telephonique) sur un sondage civique et recupere les resultats brandes. Cela
  finance les recompenses des le depart sans que la plateforme avance l'argent.

---

## 6. La page et le design

- Hub /sondages : sondages a la une, classes par thematique (comme les forums),
  tendances, « bientot clos », classements (les plus votes, les plus fiables).
- Page d'un sondage : question, options, vote, resultats en direct (barres ou
  camembert), total, temps restant, repartition demographique si collectee,
  badge de fiabilite.
- Creation (badges) : question, options, thematique, audience, niveau de
  fiabilite, duree, cible.
- Tableau de bord sondeur : ses sondages, statistiques, exports.

---

## 7. Reutilisation de l'existant (avantage majeur)

Environ 80 % des briques existent deja :

- Comptes utilisateurs verifies (email).
- Badges et reputation.
- Systeme de vote (propositions de groupes, moderation).
- Turnstile (anti-robot).
- Thematiques (categories des forums).
- Notifications.
- Profil avec champ profession.

Le sondage n'est donc pas un projet a partir de zero, mais une extension.

---

## 8. Risques a cadrer (contexte Cote d'Ivoire)

- Politique et referendums sensibles : sujets politiques, electoraux ou ethniques
  delicats. Necessite un disclaimer clair (« sondage informel, non officiel »),
  une moderation des sujets, de la transparence sur la methode, et probablement
  l'interdiction de certains sujets (haine, desinformation).
- Donnees personnelles (telephone) : cadre ARTCI (consentement, conservation,
  securite).
- Credibilite : un sondage manipulable donne un resultat sans valeur et devient
  un vecteur de desinformation. La fiabilite n'est pas qu'une option technique,
  c'est la credibilite du produit.

---

## 9. Analyse et recommandation

En une phrase : les sondages sont un excellent ajout, tres coherent avec la
marque, mais les recompenses en argent et les etudes de marche sont un autre
metier, bien plus dur. Les viser trop tot disperse alors que le coeur
(forum, Q&A, Nanan) est encore jeune.

Le vrai piege : l'oeuf et la poule.

- Les entreprises ne paient pour des etudes de marche que si l'audience est deja
  large, verifiee et representative.
- Mais on ne peut pas recompenser cette audience sans l'argent des entreprises.
- Attaquer les deux en meme temps mene a l'impasse. L'ordre est determinant.

Recommandation : commencer civique et gamifie, prouver l'engagement, puis
monetiser.

1. MVP : sondages civiques, creation badgee, points de statut (pas d'argent),
   reutilisation de l'existant. Objectif : volume et habitude de voter.
2. Ensuite : la credibilite devient l'actif, et seulement la on ouvre le payant.

Premier revenu le plus simple : vendre les resultats et analytics, pas payer les
repondants (pas de recompense a financer, pas de fraude-argent, rentable tout de
suite).

---

## 10. Idees complementaires

1. Utiliser la communaute existante : bouton « transformer un debat en sondage »
   depuis une discussion, sondage attache a un groupe ou a une discussion. Cela
   amorce la participation gratuitement.
2. Un sondage-phare recurrent, « Le Pouls de la Cote d'Ivoire » : chaque semaine
   ou mois, un barometre sur un grand sujet, tres mis en avant. But : etre cite
   par la presse (« selon Jamakan, X % des Ivoiriens... »), ce qui donne du
   marketing gratuit et de la credibilite, et attire ensuite les entreprises.
3. La credibilite comme fosse concurrentiel : afficher taille d'echantillon,
   niveau de verification, demographie, marge d'erreur. Etre le sondage serieux
   de reference (vs les sondages Facebook non fiables). Le label « Sondage
   verifie Jamakan » transforme la difficulte (anti-fraude) en argument.
4. Monetiser d'abord les resultats, pas les repondants : voter est gratuit, voir
   le detail (croisements region, age, profession) ou exporter est premium.
   Journalistes, chercheurs, ONG, entreprises paient pour l'insight. Simple et
   rentable immediatement.
5. Recompenses malignes sans cash au depart : statut, deblocage de fonctions,
   visibilite ; sondage sponsorise qui finance une cagnotte ; puis credit
   telephonique et Mobile Money avant les cartes cadeaux.
6. Cibler d'abord institutions, ONG et medias plutot que les entreprises privees.
   En Cote d'Ivoire ils ont des budgets d'etude et un besoin reel de donnees
   citoyennes ; clients plus faciles et alignes avec la mission.

---

## 11. Feuille de route en phases

Phase A - MVP (le plus simple, gratuit, sur)

- Sondages civiques, creation reservee aux badges.
- Verification niveau 1 (compte email deja en place).
- Points de gamification uniquement (badges, classement, statut), sans valeur
  monetaire.
- Thematiques, resultats en direct, page dediee.
- Monetisation possible des cette phase : vente des resultats et analytics
  (export, croisements).

Phase B - Fiabilite et recompenses reelles

- OTP telephone (sondages publics fiables) via un fournisseur SMS a choisir.
- Collecte demographique (region, age) et exports analytics avances.
- Points convertibles finances par les sondages payants ; controles qualite ;
  seuil de retrait ; recompenses en credit telephonique et Mobile Money d'abord.
- Cadrage reglementaire (jeu, fiscal, financier, donnees) avant lancement.

Phase C - Etudes de marche et entreprises

- Quotas, ciblage avance, facturation.
- Niveau identite (KYC leger) pour les etudes officielles.
- Cartes cadeaux avec enseignes partenaires.

---

## 12. Decisions ouvertes

1. Le MVP demarre-t-il en inscrits uniquement (sans SMS, gratuit, rapide) ou avec
   le telephone d'entree (plus credible mais cout et fournisseur SMS a choisir) ?
2. Modele de revenu prioritaire : badge payant, paiement au sondage, ou analytics
   premium ?
3. Politique editoriale : autoriser tous les sujets (y compris politiques) des le
   depart, ou restreindre au lancement pour limiter les risques ?
4. Recompenses au lancement : points de gamification seulement (simple, gratuit,
   sur), ou viser directement des recompenses en argent (plus vendeur mais
   fraude, financement et regulation a gerer d'entree) ?
5. Cible commerciale prioritaire : entreprises privees, ou institutions, ONG et
   medias ?

---

Prochaine etape possible : une fois ces decisions prises, produire
l'architecture detaillee (modele de donnees, ecrans, parcours anti-fraude et
parcours de recompense) avant tout developpement.
