# Fonte : contexte et consignes pour Claude Code

Carnet de musculation open source (AGPL-3.0-or-later), dépôt public `Piyaim/Fonte`.
Appli Android autonome (coque WebView Java qui sert `server/static`, données dans IndexedDB) + version serveur facultative (Flask + SQLite dans `server/`).

Ce fichier est la **référence** du projet pour Claude Code. Le lire en entier au début de chaque session. Le tenir à jour (voir « Tenir ce fichier à jour »).

---

## 1. Avec qui on travaille et comment

- Georgio, francophone, **non-développeur**. Répondre **toujours en français**, en langage simple : dire ce que fait chaque commande en une phrase.
- Il travaille sur son PC Bazzite (Linux), dans `/home/PM/Fonte`, et juge le résultat **sur captures d'écran** et sur son téléphone Android.
- Il veut de la **qualité, pas de la quantité**. Les éléments phares de l'appli sont la **collection des Esprits** et les **démonstrations d'exercice en 2D** (section 8) : ils doivent être soignés et donner envie de progresser.
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
- **Demander d'abord** (une question courte, choix proposés) : tout ce qui touche au rendu visuel validé par lui, à la direction artistique des Esprits, à un changement de règle du jeu, à une dépense de poids notable dans l'APK.
- **Toujours demander avant** : publier une release, supprimer des fichiers ou des données, réécrire l'historique Git, `git push --force`, toucher à la signature ou aux secrets GitHub, modifier `.github/workflows/build.yml`.
- **Décider seul** : les détails d'implémentation, le nommage, la structure interne, tant que les règles ci-dessous sont respectées. Le dire dans le résumé.
- Il aime **voir des propositions avant que tu ne t'engages** sur du design. Avant toute nouvelle direction visuelle, lui demander **2 ou 3 références visuelles** (jeux, personnages, illustrations) qu'il aime et ce qui lui déplaisait, et poser les questions de cadrage **une par une**.

---

## 2. Structure du projet

- `server/static/` : toute l'interface (HTML/JS/CSS sans framework, **sans étape de build**).
  - `index.html` : appli entière (vues, état `EX`, `WO`, `SESS`, `BW`, `go()`, `R()`), exposée au reste par la passerelle `window.APPX`.
  - `local-backend.js` : remplace `fetch('/api/...')` par IndexedDB en mode local (`/?local=1`, ou toujours dans l'appli Android).
  - `figure.js` + `figure-data.js` : moteur d'animation 2D des exercices (squelette, IK, `limbTube`), 50 animations. `figure-data.js` est **généré** et fait foi (les sources `d0..d4.js` + `merge.py` n'ont pas été conservées).
  - `creatures.js` : dessin actuel des 27 esprits en SVG (6 silhouettes × 3 stades, auras par rareté), à remplacer par les sprites pixel art (section 8). `jeu.js` : règles du jeu (jetons, tirages, quêtes, boutique, garde-robe par variables CSS `--f3 --f4 --f5 --fxc`).
  - `profil.js` : questionnaire de départ et programme généré (section 8 bis).
  - `sw.js` : service worker du mode serveur (cache à l'exécution, rien à lister).
- `android/` : coque Java (`MainActivity.java`), icônes alternatives par couleur, `gradle.properties` (`VERSION_CODE`, `VERSION_NAME`).
- `tests/` : voir section 5.
- `notes-de-version/vX.Y.Z.md` : texte de chaque release, en français.
- `fastlane/metadata/android/` : fiches de store (en-US, fr-FR). Visée probable F-Droid : voir les contraintes de licence en section 7.
- `design/avatar/` : prototypes SVG d'avatar **refusés** (conservés pour mémoire ; l'avatar humain est abandonné, voir section 8).
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
- État dans `localStorage`, clé `muscu-jeu`. 27 esprits dans le code (45 prévus par le bestiaire v3), 25 objets (tenue, cheveux, muscle). L'onglet « Esprits » peut être masqué dans les options.
- Un esprit **ne régresse jamais** si l'utilisateur fait une pause : une zone oubliée reste visible pour inviter à la travailler, sans punir.

---

## 5. Tests

Fichiers dans `tests/`, à lancer avec `python3 tests/nom.py` (Playwright et Flask requis). Chacun doit finir **sans « ÉCHEC »**.
- `figures.py` : moteur d'animation. `ui_local.py` : interface en mode local. `jeu.py` : règles du jeu (environ 40 contrôles). `simulation_android.py` : simulation de la coque. `differentiel.py` : le mode serveur et le mode local doivent répondre à l'identique (99 comparaisons, réglages par séance compris ; les clés `jeu` et `profil` sont dans `DROP`). `icone_app.py` : icônes.
- `profil.py` : questionnaire de départ et programme généré (IMC, exemple du cahier des charges, blessures, santé, IMC caché, « Garder mes programmes », catalogue inchangé par le générateur, export/import).
- `migration.py` : sort le code du commit 805eba3 de Git, lui fait créer de vraies données (SQLite, IndexedDB, photos, profil, jeu), puis vérifie que le code actuel les rouvre sans perte. À garder tant que l'historique Git contient ce commit.
- `reglages_seance.py` : même exercice réglé différemment dans deux programmes (écrans Programmes et Séance, conseil de charge, minuteur, retour aux valeurs de l'exercice), modes local et serveur.
- `import_profil.py` : un import réussi fait sauter le questionnaire (depuis « Bienvenue » et depuis Données, modes local et serveur) ; import en échec ou annulé : rien ne change.
- **Polices sur Bazzite** : le Chromium de Playwright ne lit pas la configuration de polices du système (aucun texte rendu, `inner_text` vide, tests en échec). Toujours lancer les tests ainsi, depuis `/home/PM/Fonte` :
  `FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/profil.py` (même chose pour chaque fichier de test ; chemin complet obligatoire, un chemin relatif ne marche pas).
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
- **Budget de poids** : les Esprits et les démonstrations d'exercice doivent tenir en **quelques Mo au total** dans l'APK ; annoncer le poids de chaque lot d'images avant de l'intégrer, privilégier WebP et les calques réutilisables.

---

## 8. Cap du projet (décisions de Georgio, 15/10/2026 et 20/10/2026)

### Avatar humain : abandonné (15/10/2026)
- On **abandonne l'avatar humain personnalisable et évolutif** (homme/femme, corpulence, Blender, three.js, vêtements séparés). Ne plus y travailler sans nouvelle décision de Georgio.
- **Aucun fichier n'est supprimé** : tout reste conservé hors dépôt (`/home/PM/fonte-blender`, `/home/PM/fonte-travail`, journal `/home/PM/fonte-blender/JOURNAL.md`) et dans le dépôt (`design/avatar/`).
- Les deux éléments phares sont désormais : **la collection des Esprits** et **les démonstrations d'exercice en 2D**.

### Élément phare : la collection des Esprits (bestiaire v3, 45 esprits)
- **Bestiaire v3** (`/home/PM/fonte-travail/esprits/bestiaire.html` et `.md`) : 15 zones × 3 = **45 esprits** (Commune 15, Peu commune 12, Rare 9, Épique 6, Légendaire 3). Les 27 identifiants actuels sont gardés avec leur rareté et leur zone (aucune migration de l'état du jeu) ; 18 nouveaux, dont 12 pour les nouvelles zones. Ordre de livraison : esprit de référence, 27 existants, 6 nouveaux des zones existantes, 12 des nouvelles zones.
- Dans le code actuel (`creatures.js`, `jeu.js`), il y a toujours **27 esprits dessinés par SVG** (6 silhouettes) : rien de la nouvelle direction n'est encore intégré à l'appli.
- **Direction artistique : PIXEL ART** (décision du 20/10/2026). Le rendu 3D Blender (velours, WebP 3D) est **abandonné** ; les fichiers 3D de Pomo restent conservés hors dépôt. Choix fait après l'essai de 3 directions 2D sur Pomo et Gloumi (A vectoriel peint, B pixel art, C ombres franches) : **B retenue**, A et C écartées.
- Règles du style : sprite natif dans une case de **64 × 64**, affiché seulement en multiple entier (×1 à ×4, `image-rendering: pixelated`) ; **12 à 16 couleurs par espèce** ; ombres qui changent de teinte, jamais vers le noir ; contour sélectif coloré ; pixels placés avec intention ; **halo en calque séparé** (80 × 80 centré sur la case), de forme et de matière propres à l'espèce, intensité selon la rareté (barème commun des 5 raretés), toujours une lueur claire sur fond sombre. Un contour continu propre à l'espèce, jamais un empilement de cercles et d'ellipses.
- **Pomo validé aux 3 stades** (20/10/2026) : il sert de référence de style. Gloumi : première passe faite, en attente d'avis.
- **Caractère selon le stade** (règle durable, tous les esprits) : stade 1 mignon ; stade 2 plus affirmé ; stade 3 **un peu plus menaçant**, mais attachant et reconnaissable (sourcils froncés, regard dur, une ou deux petites crocs, pointes modérées). Jamais d'arme, de sang, ni rien d'effrayant pour un enfant.
- **On garde** : les 3 stades, la diversité des espèces, et les règles de silhouette : écart de forme ≥ 20 % entre deux stades (viser 30 %), ≥ 25 % entre deux espèces au même stade, mesuré à 64 px avec cas témoins ; place occupée 65 / 80 / 95 % de la case ; un fil rouge visible aux 3 stades ; stade 2 = deux changements parmi proportions, posture, pièce attachée ; membres rattachés visiblement au corps (séparés tolérés pour Pomo seul).
- **Méthode** : les **cartes de pixels** (`<espèce>_s1.txt` à `_s3.txt`, 64 lignes de 64 caractères, une lettre par couleur) sont la source de vérité ; outils communs dans `/home/PM/fonte-travail/esprits/da2d/outils/` (carte → PNG et retour, halo, planche, mesures, page de test téléphone). Détails et historique : `JOURNAL.md`.
- **Un esprit ne régresse jamais** : si l'utilisateur fait une pause ou si un exercice change de zone, le stade affiché reste le plus haut stade atteint (`s.stg` le mémorise déjà dans `jeu.js`, mais **l'affichage ne s'en sert pas encore** : à brancher à l'intégration des nouveaux sprites).
- Contraintes : lisibles en vignette (64 px) sur fond sombre et clair, hors ligne, budget de poids de la section 7 (Pomo : 7,6 Ko les 3 stades avec halos, en PNG), garde-fous du jeu (section 4) inchangés, export et import de l'état du jeu toujours compatibles.

### Démonstrations d'exercice : moteur 2D `figure.js`
- Les démonstrations s'inspirent de la **présentation d'exercice de l'appli LEVELING: Fitness**, en **améliorant le moteur 2D `figure.js`**, pas en passant à des vidéos ni à de la 3D.
- **Inspiration seulement** : on ne copie ni personnage, ni monstre, ni interface, ni nom, ni logo, ni slogan de cette appli.
- Ne pas casser les 50 animations existantes (`tests/figures.py`). La garde-robe (tenue, cheveux, couleur des muscles) s'applique au personnage de `figure.js`.

---

## 8 bis. Questionnaire et programme généré

### Lot 1 (20/10/2026, commit local 805eba3, validé sur le téléphone de Georgio)
- Fichier `server/static/profil.js` (chargé par `<script>`, passe par `window.APPX`). Cahier des charges : PDF « Appli fitness questionnaire et génération de programme » (11 pages).
- Profil dans `localStorage`, clé `muscu-profil` (`version: 1`) ; réponses en cours dans `muscu-profil-brouillon`, enregistrées à chaque saisie. Le profil suit l'export local (clé `profil`, comme `jeu`) ; un export sans cette clé reste accepté. En mode serveur, il n'est pas dans `/api/export`.
- **Un import réussi fait sauter le questionnaire** (20/10/2026) : profil de l'export s'il y en a un ; sinon profil actuel gardé ; sinon profil `imported: true` (« importé, questionnaire non rempli », `answers: {}`), programmes importés gardés tels quels, questionnaire proposé dans « Mon profil » (« Remplir le questionnaire »), jamais imposé. Brouillon du questionnaire effacé. Import annulé ou refusé : rien ne change.
- Questionnaire de 17 écrans (16 du PDF + « Veux-tu voir le détail santé ? », réponse par défaut « Non »), imposé une fois tant que le profil n'existe pas ; n'efface jamais de données. Avec « Non », aucun écran n'affiche « IMC », une tranche ou « kcal ».
- Règles, dans l'ordre : sécurité (santé « Oui » → programme allégé, 2 séries, ni intervalles ni course ; moins de 18 ans → 8 répétitions au minimum ; IMC ≥ 30 → cardio à faible impact ; blessure → remplaçant, sinon autre exercice de la même famille de schéma moteur, sinon retrait expliqué, jamais un exercice déconseillé), niveau et phase (phase 1 sans isolation, 5 exercices au plus ; Avancé = paramètres de phase 2), fréquence (A/B, Haut/Bas, Poussée/Tirage/Jambes/Haut/Bas), durée (4 à 7 exercices, cardio d'après le tableau des durées), objectif.
- Blessures (décision de Georgio) : si l'exercice et son remplaçant sont déconseillés, prendre un autre exercice du même type (interprétation de Claude : même **famille** de schéma moteur, poussée horizontale ou verticale, tirage horizontal ou vertical), de préférence absent de l'autre séance ; sinon le retirer avec « … : aucun exercice de ce type ne convient à ta blessure … Demande conseil à un professionnel de santé. » « Aucune » est exclusive.
- Choix techniques validés : phase 1 sans isolation ; durée du cardio d'après le tableau des durées ; intervalles en fin de 1re séance seulement (endurance ou athlétique, phase 2).
- Programmes remplacés seulement après confirmation (création des nouveaux programmes, puis suppression des anciens ; historique intact, chaque séance passée garde son nom ; séance en cours non enregistrée rattachée à « séance libre »). « Garder mes programmes » enregistre le profil sans rien toucher ; « Mon profil » permet de générer plus tard.
- La table des 50 exercices (`LIB` dans `profil.js`) est **à relire par un professionnel** : contre-indications, impacts, types et une partie des niveaux et remplaçants sont des propositions de Claude. Elle n'est pas validée médicalement.

### Lot 2A : réglages propres à chaque séance (20/10/2026, fait, en attente de validation sur téléphone)
- Un même exercice peut avoir des séries, une cible (min, max) et un repos **différents selon le programme** (par exemple 4 × 5 en séance force, 3 × 12 en séance volume). Prépare la phase 3 (lot 2B).
- Réglages **facultatifs** sur `workout_item` (séries, cible min, cible max, repos) : vide = valeurs de l'exercice, comme avant. Mêmes règles dans `app.py` et `local-backend.js`, comparées par `tests/differentiel.py`.
- Migration sans perte d'une base SQLite et de données IndexedDB créées par le code de 805eba3 ; un ancien export s'importe toujours, un nouvel export restitue les réglages.
- L'écran Séance affiche les réglages de la séance et le conseil de charge les utilise ; l'écran Programmes permet de les voir, de les modifier et de revenir aux valeurs de l'exercice.
- Le générateur écrit ses séries, répétitions et repos **dans les réglages de séance** et **ne modifie plus le catalogue d'exercices**. La confirmation montre les réglages de chaque nouvelle séance (plus de section « Exercices modifiés »). « Garder mes programmes » et « Annuler » ne changent rien.
- Format (choix de Claude) : chaque programme de `/api/state` et de l'export porte `settings` = `{"id d'exercice": {sets, target_min, target_max, rest}}`, seulement pour les exercices réglés ; un champ vide (`null`) prend la valeur de l'exercice. `PUT /api/workouts/<id>` : avec `settings`, les réglages sont remplacés (`null` = tout effacer) ; sans `settings` (ancienne interface), ceux des exercices restés sont gardés. Mêmes bornes que l'exercice (séries 1-10, cible 1-1000, repos 0-600), cible min et max inversées si besoin, une seule cible = les deux. Archiver ou supprimer un exercice retire aussi son réglage.
- Migration : SQLite, colonnes ajoutées par `ALTER TABLE` au démarrage (`migrate` dans `app.py`) ; IndexedDB, champs `null` ajoutés au chargement puis enregistrés (`migrate` dans `local-backend.js`).
- **Version de l'export inchangée (`version: 1`)** : le changement est un ajout facultatif ; aucun des deux importeurs ne lit ce numéro ; un ancien export s'importe sans changement ; un nouvel export importé dans une ancienne version de l'appli perd seulement les réglages, ce qu'un nouveau numéro n'empêcherait pas (l'ancien code ne le lit pas). Même pratique que pour les clés `jeu` et `profil`.

### Lot 2B (à venir, rien de commencé)
- Phases 1, 2 et 3 (changement de phase **proposé puis confirmé** par l'utilisateur, jamais imposé), séances ondulatoires de phase 3 (force, volume et endurance, puissance et cardio) grâce aux réglages par séance ; semaine allégée ; reprise en douceur à 80 % après plus de 3 semaines sans séance ; placement des séances sur les jours choisis ; conseil de charge combiné (double progression, régression, ressenti, semaine allégée, reprise) ; repos plus longs si IMC de 30 ou plus.
- Plus tard : bouton « J'ai mal », circuit d'endurance.

---

## 9. À faire ensuite
- Questionnaire : lot 2A (réglages par séance), puis lot 2B (section 8 bis).
- Esprits : avis de Georgio sur Gloumi (première passe pixel art), puis les autres espèces du bestiaire v3 une par une, puis intégration dans l'appli (sprites PNG, halo, stade jamais en recul). Puis démonstrations d'exercice (`figure.js`).
- Zones et exercices manquants : avant-bras, trapèzes, obliques, adducteurs (les formes musculaires sont dessinées mais absentes de `ZONES` et `EXZ`).
- Non vérifié sur téléphone réel : changement d'icône du lanceur, fluidité des animations dans la WebView, empreinte de la signature, animations/sons/vibrations du tirage.
- Mettre à jour le wiki (voir section 10), en une seule écriture, après confirmation de Georgio.

---

## 10. Tenir ce fichier et le wiki à jour

- Après toute décision durable (choix technique, règle du jeu, version publiée, incident résolu), mettre à jour **ce fichier** (sections 4, 8, 9 en priorité) dans le même commit que le changement.
- Georgio tient un wiki BookStack (projet Raspberry Pi, hors Fonte) avec une page « Suivi muscu » (id 71) : résumé fonctionnel du projet (dépôt local-first, alias d'icônes, moteur d'animation, jeu des Esprits ; l'avatar humain est abandonné). Si le connecteur BookStack est disponible dans cette session, la mettre à jour **en une seule écriture** (BookStack n'a pas de mise à jour partielle : chaque écriture renvoie la page entière), après sa confirmation. Sinon, préparer le texte et le lui remettre pour qu'il le fasse passer par sa conversation Claude habituelle.
- **Ne pas dupliquer** : la procédure de publication et les règles de code vivent dans ce fichier ; le wiki n'en garde qu'un résumé et y renvoie.
