# Fonte : contexte et consignes pour Claude Code

Carnet de musculation open source (AGPL-3.0-or-later), dépôt public `Piyaim/Fonte`.
Appli Android autonome (coque WebView Java qui sert `server/static`, données dans IndexedDB) + version serveur facultative (Flask + SQLite dans `server/`).

Ce fichier est la **référence** du projet pour Claude Code. Le lire en entier au début de chaque session. Le tenir à jour (voir « Tenir ce fichier à jour »).

---

## 1. Avec qui on travaille et comment

- Georgio, francophone, **non-développeur**. Répondre **toujours en français**, en langage simple : dire ce que fait chaque commande en une phrase.
- Il travaille sur son PC Bazzite (Linux), dans `/home/PM/Fonte`, et juge le résultat **sur captures d'écran** et sur son téléphone Android.
- Il veut de la **qualité, pas de la quantité**. L'avatar sera « l'élément phare » de l'appli : il doit être soigné et donner envie de progresser.
- Commandes à lui donner : **complètes, prêtes à copier-coller, avec les vraies valeurs**. Jamais de chevrons ni de placeholders (il les colle tels quels).
- Il ne colle **jamais** de secrets (clé de signature, mots de passe, jetons). Ne jamais lui en demander, ne jamais afficher un fichier de config entier : filtrer à la source (`grep -v`, `sed`).
- Réponses courtes : ce qui a été fait, le fichier ou la capture à regarder, la prochaine étape si elle est réelle. Pas de récit des étapes.

### Méthode de vérification (non négociable)
- Une chose « configurée » n'est pas une chose qui fonctionne : exiger une vérification réelle avant de conclure.
- Un test doit contenir un élément qui **diffère selon l'hypothèse**, sinon il ne prouve rien.
- Un contrôle doit mesurer ce qui compte, pas ce qui en est proche (« le fichier existe » n'est pas « l'appli marche »).
- Avant de proposer une solution qui suppose une fonctionnalité d'un outil tiers (Blender, three.js, WebView Android, API Android, GitHub Actions), **vérifier qu'elle existe** (documentation, essai réel, recherche web) plutôt que de l'assumer.
- **Signaler ce qui n'a pas été vérifié**. Si une affirmation passée se révèle fausse, le dire à voix haute et la corriger.

### Quand demander, quand décider
- **Demander d'abord** (une question courte, choix proposés) : tout ce qui touche au rendu visuel validé par lui, au choix technique de l'avatar, à un changement de règle du jeu, à une dépense de poids notable dans l'APK.
- **Toujours demander avant** : publier une release, supprimer des fichiers ou des données, réécrire l'historique Git, `git push --force`, toucher à la signature ou aux secrets GitHub, modifier `.github/workflows/build.yml`.
- **Décider seul** : les détails d'implémentation, le nommage, la structure interne, tant que les règles ci-dessous sont respectées. Le dire dans le résumé.
- Il aime **voir des propositions avant que tu ne t'engages** sur du design. Ses trois premières directions d'avatar ont été refusées sans détail : avant de repartir, lui demander **2 ou 3 références visuelles** (jeux, personnages, illustrations) qu'il aime et ce qui lui déplaisait.

---

## 2. Structure du projet

- `server/static/` : toute l'interface (HTML/JS/CSS sans framework, **sans étape de build**).
  - `index.html` : appli entière (vues, état `EX`, `WO`, `SESS`, `BW`, `go()`, `R()`), exposée au reste par la passerelle `window.APPX`.
  - `local-backend.js` : remplace `fetch('/api/...')` par IndexedDB en mode local (`/?local=1`, ou toujours dans l'appli Android).
  - `figure.js` + `figure-data.js` : moteur d'animation 2D des exercices (squelette, IK, `limbTube`), 50 animations. `figure-data.js` est **généré** et fait foi (les sources `d0..d4.js` + `merge.py` n'ont pas été conservées).
  - `creatures.js` : dessin des 27 esprits (6 silhouettes × 3 stades, auras par rareté). `jeu.js` : règles du jeu (jetons, tirages, quêtes, boutique, garde-robe par variables CSS `--f3 --f4 --f5 --fxc`).
  - `sw.js` : service worker du mode serveur (cache à l'exécution, rien à lister).
- `android/` : coque Java (`MainActivity.java`), icônes alternatives par couleur, `gradle.properties` (`VERSION_CODE`, `VERSION_NAME`).
- `tests/` : voir section 5.
- `notes-de-version/vX.Y.Z.md` : texte de chaque release, en français.
- `fastlane/metadata/android/` : fiches de store (en-US, fr-FR). Visée probable F-Droid : voir les contraintes de licence en section 7.
- `design/avatar/` : prototypes SVG d'avatar **refusés** (conservés pour mémoire, ne pas les reprendre tels quels).
- `.github/workflows/build.yml` : construit et signe l'APK quand une release est **publiée** (ou en lancement manuel). Secrets déjà créés : `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_PASSWORD`, `KEY_ALIAS`.

---

## 3. Règles de code

- En-tête `SPDX-License-Identifier: AGPL-3.0-or-later` sur tout nouveau fichier de code.
- **Aucune requête réseau sortante** : la coque Android les bloque, et c'est une promesse faite aux utilisateurs. Pas de CDN, pas de police distante, pas de statistiques. Toute bibliothèque (three.js par exemple) est **copiée dans le dépôt**, avec sa licence.
- Pas d'étape de build côté interface : du JS/CSS lisible, chargé par `<script>`. Ne pas introduire de bundler sans l'avoir demandé.
- Les `let/const` d'`index.html` ne sont pas sur `window` : passer par `window.APPX`.
- Interface en **français**, casse de phrase, mêmes mots pour la même action partout. Cibles tactiles d'au moins 44 px, contrastes lisibles, `aria-label` sur les boutons-icônes, `prefers-reduced-motion` respecté pour les animations non demandées par l'utilisateur.
- Lisibilité d'abord sur écran de téléphone : contrôler à 360 px et 390 px de large.
- **Données de l'utilisateur** (IndexedDB, `localStorage`, export/import) : ne jamais casser l'existant. Toute évolution de schéma passe par une migration testée. L'export contient la clé `jeu` quand elle est non nulle ; l'import la restaure via `JEU.importState`. Garder export et import compatibles avec les anciennes versions.
- Performance : l'appli doit rester fluide sur un téléphone modeste dans une WebView. Mesurer avant d'affirmer que c'est fluide.

---

## 4. Le jeu des Esprits (garde-fous non négociables)

Aucun argent réel, aucune série à perdre, jetons gagnés **seulement par effort réel**, plafond quotidien, taux de tirage affichés. Ne pas assouplir ces règles sans accord explicite de Georgio.

Valeurs actuelles (v0.3.1) :
- Taux : Commun 58, Peu commun 26, Rare 11, Épique 4, Légendaire 1. Compassion (pity) : Épique à 30, Légendaire à 90 tirages.
- Tirage : 1 jeton, ×5 possible. Plafond : 4 jetons par jour.
- Éclats par doublon : C 4, U 10, R 30, E 80, L 200. Prix boutique : 40, 100, 300, 800, 2000.
- Niveau d'une zone = 1 + partie entière de la racine carrée du nombre de séries dans la zone ; stade 2 au niveau 6, stade 3 au niveau 14.
- Jetons : 3 séries ou plus +1, 10 séries ou plus +1, record battu +1, effort moyen entre 3 et 4,5 +1 (tout cela exige au moins 3 séries ; « À fond » ne donne rien de plus). L'historique existant ne donne aucun jeton. Cadeau de bienvenue : 3 jetons + l'esprit Gloumi.
- Quêtes : objectif de séances `WGOAL` +2, 5 zones différentes +1, équipe complète +2.
- État dans `localStorage`, clé `muscu-jeu`. 27 esprits, 25 objets (tenue, cheveux, muscle). L'onglet « Esprits » peut être masqué dans les options.
- L'avatar **ne régresse jamais** si l'utilisateur fait une pause : une zone oubliée reste visible pour inviter à la travailler, sans punir.

---

## 5. Tests

Fichiers dans `tests/`, à lancer avec `python3 tests/nom.py` (Playwright et Flask requis). Chacun doit finir **sans « ÉCHEC »**.
- `figures.py` : moteur d'animation. `ui_local.py` : interface en mode local. `jeu.py` : règles du jeu (environ 40 contrôles). `simulation_android.py` : simulation de la coque. `differentiel.py` : le mode serveur et le mode local doivent répondre à l'identique (69 comparaisons ; la clé `jeu` est dans `DROP`). `icone_app.py` : icônes.
- **Tout lancer avant chaque commit qui touche au code** ; si un test est ajouté ou modifié, vérifier qu'il **échoue** quand l'hypothèse est fausse.
- Pour tout changement visuel : faire des **captures Playwright à 390×844** (et 360 de large), les regarder réellement, les enregistrer dans un dossier de travail hors dépôt et dire à Georgio où les ouvrir.
- Sur Bazzite (système immuable), si Python, Flask ou Playwright manquent : utiliser un environnement virtuel (`python3 -m venv .venv`, dossier ignoré par Git) ou une boîte `distrobox`. Ne pas installer de paquets système sans lui expliquer pourquoi. (À vérifier sur sa machine : je n'y ai pas accès.)

---

## 6. Git et publication

### Au quotidien
- Dépôt : `https://github.com/Piyaim/Fonte.git`, branche `main`. Identité Git du dépôt : `Piyaim` / `Piyaim@users.noreply.github.com` (adresse noreply, pour ne pas exposer son vrai mail dans un dépôt public).
- L'authentification du push passe par un jeton personnel GitHub (90 jours, limité à ce dépôt, permission « Contents : lecture et écriture »), mémorisé par KDE. À l'expiration, Georgio en crée un autre ; **ne jamais lui demander de le coller dans la conversation**.
- Commits **petits et fréquents**, messages en français qui disent le pourquoi. Avant chaque commit : `git status --short` et `git diff --cached --stat`, et relire la liste pour y chercher des secrets ou de gros fichiers.
- **Ne jamais ajouter `android/gradlew.bat` à un commit** : il apparaît toujours « modifié » à cause des fins de ligne (le contenu est identique ; vérifié avec `git diff --ignore-space-at-eol`). Ajouter les fichiers **par nom**, pas avec `git add -A`, tant que ce fichier traîne ; ou lancer `git restore android/gradlew.bat` avant.
- **Ne pas toucher à `.github/workflows/build.yml`** sans demander : la version de GitHub a été corrigée à la main et fonctionne. Y toucher exige aussi une permission supplémentaire du jeton.
- Jamais de `git push --force`, jamais de réécriture de l'historique.
- Un push sur `main` **ne publie pas** l'appli : seule une release GitHub déclenche la construction de l'APK.

### Fichiers lourds et secrets
- **Ne jamais commiter** : clé ou coffre de signature (`*.jks`, `*.keystore`), mots de passe, jetons, fichiers `.blend` et rendus bruts de Blender, environnement virtuel `.venv/`. Le dépôt est public et l'historique Git ne rétrécit pas : un gros fichier ou un secret commité y reste.
- Les **sources Blender** restent hors du dépôt, mais **sauvegardées** (copie sur son Nextcloud du Pi, par exemple). Seuls les **résultats finaux** utiles à l'appli (images, modèles légers) vont dans `server/static/`.
- Si un secret part par erreur sur GitHub : le dire tout de suite et faire révoquer le secret, ne pas se contenter de le supprimer du dépôt.

### Publier une version (procédure qui a déjà échoué une fois : la suivre à la lettre)
1. Dans `android/gradle.properties`, passer `VERSION_CODE` (+1) et `VERSION_NAME` (exemple : de `0.3.1` à `0.3.2`) ; écrire `notes-de-version/v0.3.2.md` (en français, pour l'utilisateur final).
2. Lancer **tous** les tests.
3. Commit, puis `git push`.
4. **Seulement ensuite**, créer la release GitHub dont le tag est `v` + `VERSION_NAME` (ici `v0.3.2`). Sinon le tag pointe vers un ancien commit et le workflow échoue avec « Le tag ... ne correspond pas à VERSION_NAME ».
5. Georgio installe l'APK de la release sur son téléphone ; ne **jamais** affirmer qu'un point fonctionne sur téléphone sans qu'il l'ait confirmé.
Version actuelle : voir `android/gradle.properties` (0.3.1, VERSION_CODE 6, au moment du passage de relais).

---

## 7. Licences, poids, hors ligne

- Projet **AGPL-3.0-or-later**. Tout élément tiers (modèle 3D, texture, police, bibliothèque, son) doit avoir une licence **compatible** et utilisable sans réseau ; préférer CC0, MIT, SIL OFL. Noter chaque élément tiers (nom, auteur, licence, origine) dans un fichier `CREDITS.md` à la racine. Ce qui est créé par Georgio ou par Claude pour le projet est sous la licence du projet.
- Le dossier `fastlane` laisse penser à une visée F-Droid (non confirmée) : donc pas de composant propriétaire, pas de pistage, pas de dépendance réseau.
- **Budget de poids** : l'avatar et ses variantes doivent tenir en **quelques Mo au total** dans l'APK ; annoncer le poids de chaque lot d'images avant de l'intégrer, privilégier WebP et les calques réutilisables.

---

## 8. Chantier en cours : l'avatar

Georgio veut un **avatar personnalisable, homme ou femme**, qui soit l'élément phare de l'appli, qui **évolue avec l'entraînement** (idéalement zone par zone, sans jamais régresser), personnalisable avec la garde-robe du jeu (tenue, cheveux, muscle), présent aussi dans les animations d'exercices.

Déjà fait : trois directions SVG dessinées à la main (A « Héros », B « Mascotte » chibi, C « Sticker »), **toutes refusées** (`design/avatar/`). Des maquettes d'écrans (accueil, tenues, évolution) existent dans un canvas de design Claude (`https://claude.ai/artifact/KNbGbY24Bkv64X7rKLGzsL`, privé), **non validées** : à n'utiliser que comme idées de composition, pas de style.

Outils : PC Bazzite (Ryzen 9800X3D, RX 9070) avec **Blender connecté** à Claude Code. Vérifier au tout début que Blender répond réellement (essai simple : créer un cube et en faire un rendu).

Démarche imposée, dans cet ordre :
1. Poser les questions de cadrage (références visuelles qu'il aime, ce qui lui déplaisait).
2. Trancher la piste technique **avec lui, sur essais réels** : (a) calques PNG/WebP rendus depuis Blender, empilés comme des sprites (léger, compatible WebView, personnalisation par superposition) ; (b) modèle glTF affiché avec three.js (rotation possible, plus lourd, plus risqué sur téléphones modestes). Mesurer poids et fluidité avant de choisir.
3. Produire **un seul personnage de référence**, le lui montrer en capture, **attendre sa validation**. Aucune variante avant.
4. Seulement ensuite : version homme et femme, paliers d'évolution par zone, coiffures, tenues, accessoires.
5. Intégration dans la garde-robe (la boutique et les aperçus existent déjà) et dans les animations d'exercices (`figure.js`), sans casser les 50 animations existantes.
Contraintes : tout fonctionne hors ligne dans l'APK, reste lisible en vignette, s'accorde avec les 27 esprits, respecte les budgets de la section 7.

---

## 9. À faire ensuite
- Avatar (section 8).
- Zones et exercices manquants : avant-bras, trapèzes, obliques, adducteurs (les formes musculaires sont dessinées mais absentes de `ZONES` et `EXZ`).
- Non vérifié sur téléphone réel : changement d'icône du lanceur, fluidité des animations dans la WebView, empreinte de la signature, animations/sons/vibrations du tirage.
- Mettre à jour le wiki (voir section 10), en une seule écriture, après confirmation de Georgio.

---

## 10. Tenir ce fichier et le wiki à jour

- Après toute décision durable (choix technique, règle du jeu, version publiée, incident résolu), mettre à jour **ce fichier** (sections 4, 8, 9 en priorité) dans le même commit que le changement.
- Georgio tient un wiki BookStack (projet Raspberry Pi, hors Fonte) avec une page « Suivi muscu » (id 71) : résumé fonctionnel du projet (dépôt local-first, alias d'icônes, moteur d'animation, jeu des Esprits, avatar). Si le connecteur BookStack est disponible dans cette session, la mettre à jour **en une seule écriture** (BookStack n'a pas de mise à jour partielle : chaque écriture renvoie la page entière), après sa confirmation. Sinon, préparer le texte et le lui remettre pour qu'il le fasse passer par sa conversation Claude habituelle.
- **Ne pas dupliquer** : la procédure de publication et les règles de code vivent dans ce fichier ; le wiki n'en garde qu'un résumé et y renvoie.
