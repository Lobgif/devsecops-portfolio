## [1.19.5](https://gitlab.com/personnel4344847/agoraci/compare/v1.19.4...v1.19.5) (2026-10-05)


### Bug Fixes

* **infra:** cap_drop sur traefik + rabbitmq (phase 3) ([c35c658](https://gitlab.com/personnel4344847/agoraci/commit/c35c6586e5ef102595ba299dd08544896871fc98))

## [1.19.4](https://gitlab.com/personnel4344847/agoraci/compare/v1.19.3...v1.19.4) (2026-10-05)


### Bug Fixes

* **infra:** durcit cap_drop/read_only (phase 2) ([26dc58c](https://gitlab.com/personnel4344847/agoraci/commit/26dc58c1b9eaecf439e99d88e9ad82c6a90c46c8))

## [1.19.3](https://gitlab.com/personnel4344847/agoraci/compare/v1.19.2...v1.19.3) (2026-10-05)


### Bug Fixes

* **infra:** durcit la securite des conteneurs Docker ([6010b0a](https://gitlab.com/personnel4344847/agoraci/commit/6010b0a64b46f483075cdf191ada3166e2b75589))

## [1.19.2](https://gitlab.com/personnel4344847/agoraci/compare/v1.19.1...v1.19.2) (2026-09-18)


### Bug Fixes

* **ci:** scan needs:optional + meme filtre changes que le build ([9edc9bf](https://gitlab.com/personnel4344847/agoraci/commit/9edc9bff8aa6f8a81998d7828bd691de0c778c97))

## [1.19.1](https://gitlab.com/personnel4344847/agoraci/compare/v1.19.0...v1.19.1) (2026-09-18)


### Bug Fixes

* **ui:** espace parasite du footer + icone de recherche + e-mail contact ([0adb778](https://gitlab.com/personnel4344847/agoraci/commit/0adb778e44ffa442725ce87a78cd80b38f3c2af1))

# [1.19.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.18.2...v1.19.0) (2026-09-18)


### Features

* **email:** template Jamakan soigne + version texte + job fix:sender ([b5fa88a](https://gitlab.com/personnel4344847/agoraci/commit/b5fa88abc5fe73f46fbbfb4693f96d8d2bff2f34))

## [1.18.2](https://gitlab.com/personnel4344847/agoraci/compare/v1.18.1...v1.18.2) (2026-09-17)


### Bug Fixes

* **email:** defaut BREVO_SENDER_EMAIL en no-reply@kaedys.com ([8d18e02](https://gitlab.com/personnel4344847/agoraci/commit/8d18e027a95ad479b547425dfb81538276f0926d))

## [1.18.1](https://gitlab.com/personnel4344847/agoraci/compare/v1.18.0...v1.18.1) (2026-09-17)


### Performance Improvements

* **ssr:** allege le payload de chaque page (textes legaux hors /settings) ([529cdc6](https://gitlab.com/personnel4344847/agoraci/commit/529cdc65cbdd10f7f0783b15dadd10210a909dae))

# [1.18.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.17.0...v1.18.0) (2026-09-17)


### Bug Fixes

* **ci:** corrige le job backup:up (echo avec ': ' cassait le YAML script) ([9fae72b](https://gitlab.com/personnel4344847/agoraci/commit/9fae72b8fbaa09ec6d4bf2a359d93f930e216506))


### Features

* **ci:** backup:up ecrit aussi BACKUP_PASSPHRASE dans le .env (chiffrement) ([7e4902e](https://gitlab.com/personnel4344847/agoraci/commit/7e4902ea5cb700d9e3acbc280c21f5a66c627b29))
* **infra:** sauvegardes PostgreSQL automatiques vers S3/R2 (hors VM) ([3dc5f84](https://gitlab.com/personnel4344847/agoraci/commit/3dc5f8473f7ce03c35af6e9a4c8fdf3c4b8cdb13))

# [1.17.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.16.2...v1.17.0) (2026-09-17)


### Features

* **pwa:** rend Jamakan installable (manifest + icone + enregistrement SW) ([a4df054](https://gitlab.com/personnel4344847/agoraci/commit/a4df054f8ee30a50548d6a89e3553a93dc8391f6))

## [1.16.2](https://gitlab.com/personnel4344847/agoraci/compare/v1.16.1...v1.16.2) (2026-09-16)


### Bug Fixes

* **brand:** remplace les logos AgoraCI restants (footer + sidebar admin) ([3c68ae1](https://gitlab.com/personnel4344847/agoraci/commit/3c68ae136ed071e3e5661f3d703eca59dd9c93cf))

## [1.16.1](https://gitlab.com/personnel4344847/agoraci/compare/v1.16.0...v1.16.1) (2026-09-16)


### Bug Fixes

* **ci:** serialise les operations VM (resource_group) pour eviter les conflits ([3c13e68](https://gitlab.com/personnel4344847/agoraci/commit/3c13e68cd7d5a7de710fdc76cfe4b429645aa395))

# [1.16.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.15.0...v1.16.0) (2026-09-16)


### Features

* **brand:** rebrand AgoraCI → Jamakan (nom visible partout) ([ec62a26](https://gitlab.com/personnel4344847/agoraci/commit/ec62a2606c50d0b21ee946b637fd28f4806b1054))
* **infra:** redirection 301 de l'ancienne URL vers jamakan.kaedys.com ([8b6921d](https://gitlab.com/personnel4344847/agoraci/commit/8b6921d32a8d617102dfcd4b5ebdaf42552f59c9))

# [1.15.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.14.1...v1.15.0) (2026-09-16)


### Features

* **groups:** bouton Partager + CTA d'inscription (visiteurs déconnectés) ([dfe1f84](https://gitlab.com/personnel4344847/agoraci/commit/dfe1f8489293d35ba9c2da2a2f48d705994bf8a9))

## [1.14.1](https://gitlab.com/personnel4344847/agoraci/compare/v1.14.0...v1.14.1) (2026-09-15)


### Bug Fixes

* **analytics:** retire les env NUXT_PUBLIC_UMAMI/SENTRY vides du compose ([45b2e90](https://gitlab.com/personnel4344847/agoraci/commit/45b2e906355ee3af4d85e5720a9b2fa909410333))

# [1.14.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.13.2...v1.14.0) (2026-09-15)


### Features

* **analytics:** active le tracking Umami (Website ID + domaine autorise dans la CSP) ([4f8e6a2](https://gitlab.com/personnel4344847/agoraci/commit/4f8e6a2ab7cacf59853258caa567821e8ccfa6d6))

## [1.13.2](https://gitlab.com/personnel4344847/agoraci/compare/v1.13.1...v1.13.2) (2026-09-15)


### Bug Fixes

* **chat:** redis_listener resilient (reconnexion auto au lieu de mourir sur timeout) ([025661e](https://gitlab.com/personnel4344847/agoraci/commit/025661e634001b7e35b9650b4783889691d91ed3))

## [1.13.1](https://gitlab.com/personnel4344847/agoraci/compare/v1.13.0...v1.13.1) (2026-09-15)


### Bug Fixes

* **sentry:** ajoute sentry-sdk a uv.lock + init defensif + reactive les DSN ([f5cfd40](https://gitlab.com/personnel4344847/agoraci/commit/f5cfd405cb0d0bbe098b95dffa163a712b692d0f))

# [1.13.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.12.0...v1.13.0) (2026-09-14)


### Features

* **monitoring:** suivi d'erreurs Sentry (front + back), inerte sans DSN ([39418ea](https://gitlab.com/personnel4344847/agoraci/commit/39418ea8db5e0bba0ad914a1ec32cc8d2e5e7004))

# [1.12.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.11.0...v1.12.0) (2026-09-14)


### Features

* **analytics:** Umami auto-heberge (profil compose 'analytics') + tracking front conditionnel ([8191791](https://gitlab.com/personnel4344847/agoraci/commit/81917914958980821f9dd83fd17cdae2f6f4ee94))

# [1.11.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.10.0...v1.11.0) (2026-09-14)


### Features

* **nanan:** cap quotidien par utilisateur (reglable admin) + compteur de conso du jour ([8713c3f](https://gitlab.com/personnel4344847/agoraci/commit/8713c3fe90ed036ff5e69c72473e49b25e0f53a2))

# [1.10.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.9.0...v1.10.0) (2026-08-30)


### Features

* **design:** cartes contact alignees au formulaire + refonte page creation de groupe ([f06e2d8](https://gitlab.com/personnel4344847/agoraci/commit/f06e2d8cc582ccb8dafee038c6327112d37fbd19))

# [1.9.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.8.0...v1.9.0) (2026-08-30)


### Features

* **design:** reseaux sociaux cliquables via admin (login/register/contact/footer) + Instagram ([10c94ea](https://gitlab.com/personnel4344847/agoraci/commit/10c94eaf09cfe7721d7a1395b48d807b01ddd017))

# [1.8.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.7.0...v1.8.0) (2026-08-30)


### Bug Fixes

* **backend:** imports manquants (uuid, ROLE_MEMBER/ROLE_ADMIN) + tri imports ([11038be](https://gitlab.com/personnel4344847/agoraci/commit/11038be38858bbfcec520d97f2ccc640a7b35445))


### Features

* **design:** auth split-panel, sections accueil, page contact, a propos, footer sombre ([7639d84](https://gitlab.com/personnel4344847/agoraci/commit/7639d841a86e2134427be242a5f5b5369344133e))

# [1.7.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.6.0...v1.7.0) (2026-08-30)


### Features

* **design:** refonte layout fidele aux maquettes (3 colonnes + dashboard) ([71dcbc1](https://gitlab.com/personnel4344847/agoraci/commit/71dcbc160e853afec1224212344328183385facd))
* **design:** refonte pages discussion (vote vertical + meilleure reponse) et groupe (hero) ([7648f14](https://gitlab.com/personnel4344847/agoraci/commit/7648f14c8f40947e31a9cc17c0c4fd2a099b4b01))
* **design:** refonte profil public (u/[id]) + parametres dans la coquille ([3d94c08](https://gitlab.com/personnel4344847/agoraci/commit/3d94c08cf5b6afdf4bbb880e393df4066984c484))

# [1.6.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.5.0...v1.6.0) (2026-08-30)


### Bug Fixes

* **ia:** Nanan devient un assistant general (plus seulement juridique) ([cb326b6](https://gitlab.com/personnel4344847/agoraci/commit/cb326b622abad63f2c80f51f8bd53f16a87271fa))


### Features

* **badges:** seuils ABSOLUS configurables + un seul badge par groupe ([49cd5a8](https://gitlab.com/personnel4344847/agoraci/commit/49cd5a8b8fa495a102b18a1aa03fdced1a602b1d))
* **gouvernance:** Phase 1 - creation de groupe par proposition + seuil de soutiens ([855ab4d](https://gitlab.com/personnel4344847/agoraci/commit/855ab4d2e610cd3a3bfe2e9c5205ebe8650f6f3e))
* **gouvernance:** Phase 2 - vote pondere (plafonne) + retrait democratique de membre ([cdc4e6f](https://gitlab.com/personnel4344847/agoraci/commit/cdc4e6ff0f1bf3ebe4956426d7a5a1a50b131af2))
* **gouvernance:** Phase 2 front - page gouvernance du groupe (propositions + vote + retrait) ([90dba67](https://gitlab.com/personnel4344847/agoraci/commit/90dba6738dc3ec353f1e4488fdaaf0862b319453))
* **gouvernance:** Phase 3 - vote d'admission (groupes prives) + election des moderateurs ([8395f35](https://gitlab.com/personnel4344847/agoraci/commit/8395f35ad96e78965be7ef8477c98363d2066d9d))
* **gouvernance:** Phase 4 - suppression de groupe avec preavis (super-admin) ([dc27d61](https://gitlab.com/personnel4344847/agoraci/commit/dc27d615f56cec0c11803aa738f7d4c06c3689f5))

# [1.5.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.4.0...v1.5.0) (2026-08-30)


### Features

* **content:** generalise les textes au-dela du droit + contact configurable ([90e6946](https://gitlab.com/personnel4344847/agoraci/commit/90e69468861734681a18aac049625a1ab3274c71))

# [1.4.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.3.0...v1.4.0) (2026-08-29)


### Features

* **admin:** tableau de bord Metriques AARRR + info-bulles (definition + calcul) ([205831f](https://gitlab.com/personnel4344847/agoraci/commit/205831f6a65855b0fc7095911dd86ab4afaf96d5))

# [1.3.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.2.0...v1.3.0) (2026-08-29)


### Features

* **categories:** elargit les categories au-dela du droit + groupes de demarrage ([a01a69f](https://gitlab.com/personnel4344847/agoraci/commit/a01a69fcae2f3f84d060a3aa64f5e5ec9b2122d0))
* **ia:** boucle brouillon Nanan (propose -> valide par la communaute) ([6a373c9](https://gitlab.com/personnel4344847/agoraci/commit/6a373c907813d6b6a1d3c5f1a9dcbba2fefa3dc7))
* **ia:** fraicheur du RAG + paliers de badges plus rigoureux ([70de6f6](https://gitlab.com/personnel4344847/agoraci/commit/70de6f60a660db5cb62c8b00640e72a9dc093f71))

# [1.2.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.1.0...v1.2.0) (2026-08-29)


### Features

* **experts:** profession + candidature expert validee par l'admin + badges ([5b38edc](https://gitlab.com/personnel4344847/agoraci/commit/5b38edccb12b953c18f6d75455991d773b6f181c))
* **experts:** UI inscription profession + candidature expert + validation admin + badges ([d567f59](https://gitlab.com/personnel4344847/agoraci/commit/d567f59f1357edaeb22a7f67f09cd44b8e742846))

# [1.1.0](https://gitlab.com/personnel4344847/agoraci/compare/v1.0.0...v1.1.0) (2026-08-29)


### Features

* **ia:** Nanan route par categorie + apprentissage communautaire base sur la qualite ([5abcea6](https://gitlab.com/personnel4344847/agoraci/commit/5abcea644519a20b5ad0c19b49f69dd3ff5b25d1))

# 1.0.0 (2026-08-29)


### Bug Fixes

* **auth:** le super-admin reconcilie aussi le mot de passe depuis SUPERADMIN_PASSWORD ([1d08036](https://gitlab.com/personnel4344847/agoraci/commit/1d08036415234fdd29094c199da5282b0aac47f9))
* **ci:** corrige semantic-release (conflit de version conventional-changelog) ([f4b97a8](https://gitlab.com/personnel4344847/agoraci/commit/f4b97a8f9d7deca5e55c9ecd806f76fd8a32df7e))
* **ci:** preset semantic-release par defaut (evite le module conventionalcommits instable) ([45e6c82](https://gitlab.com/personnel4344847/agoraci/commit/45e6c82067eec34a39a3e7332834136314a9e4cb))
* **security:** applique le chemin admin secret au build (arg), pas au runtime ([547cb8d](https://gitlab.com/personnel4344847/agoraci/commit/547cb8d19e69ea0559c52cb58c4fccce8ce57d35))


### Features

* **home:** elargit le positionnement au-dela du droit (tous sujets du quotidien ivoirien) ([eb9f783](https://gitlab.com/personnel4344847/agoraci/commit/eb9f783a4ce6b31a87199104a60293ab74436624))
