# Fonte : contexte pour Claude Code

Carnet de musculation open source (AGPL-3.0-or-later), dépôt public `Piyaim/Fonte`.
Appli Android autonome (coque WebView Java qui sert `server/static`, données dans IndexedDB) + version serveur facultative (Flask + SQLite dans `server/`).

## Qui est l'utilisateur et comment travailler avec lui
- Georgio, francophone, **non-développeur** : répondre **toujours en français**.
- Donner des **commandes complètes, prêtes à copier-coller**, avec les vraies valeurs : jamais de chevrons ni de placeholders.
- Il ne colle **jamais** de secrets (clé de signature, mots de passe) : ne jamais lui en demander, ne jamais afficher un fichier de config entier.
- Avant de conclure, **vérifier pour de vrai** (test qui diffère selon l'hypothèse), signaler ce qui n'est pas vérifié, corriger à voix haute une erreur passée.
- Il aime la qualité plutôt que la quantité. Il juge sur capture d'écran de son téléphone Android.
- Son wiki BookStack (projet Raspberry Pi, hors Fonte) contient une page « Suivi muscu » (id 71) : la mettre à jour **en une seule écriture** après sa confirmation (dépôt local-first, alias d'icônes, moteur d'animation, jeu des Esprits, avatar).

## Structure
- `server/static/` : toute l'interface (HTML/JS/CSS sans framework, sans build).
  - `index.html` : appli entière (vues, état `EX`, `WO`, `SESS`, `BW`, `go()`, `R()`), exposée au reste par la passerelle `window.APPX`.
  - `local-backend.js` : remplace `fetch('/api/...')` par IndexedDB en mode local (`/?local=1`, ou toujours dans l'appli Android).
  - `figure.js` + `figure-data.js` : moteur d'animation 2D des exercices (squelette, IK, `limbTube`), 50 animations ; `figure-data.js` est **généré** (voir `design/avatar` pour l'idée, la source était `d0..d4.js` + `merge.py`, non conservés : le fichier généré fait foi).
  - `creatures.js` : dessin des 27 esprits (6 silhouettes × 3 stades). `jeu.js` : règles du jeu (jetons, tirages, quêtes, boutique, garde-robe via variables CSS `--f3 --f4 --f5 --fxc`).
- `android/` : coque Java, icônes alternatives par couleur, `gradle.properties` (VERSION_CODE, VERSION_NAME).
- `tests/` : `figures.py`, `ui_local.py`, `jeu.py`, `simulation_android.py`, `differentiel.py` (serveur et local doivent répondre à l'identique, 69 comparaisons), `icone_app.py`. Lancer chacun avec `python3 tests/<nom>.py` (Playwright + Flask requis ; chacun doit finir sans « ÉCHEC »).
- `notes-de-version/vX.Y.Z.md` : texte de la release, en français.
- `.github/workflows/build.yml` : construit et signe l'APK quand une release est **publiée** (ou en lancement manuel). Secrets déjà créés : KEYSTORE_BASE64, KEYSTORE_PASSWORD, KEY_PASSWORD, KEY_ALIAS.

## Règles de code
- En-tête `SPDX-License-Identifier: AGPL-3.0-or-later` sur les fichiers de code.
- Pas de requête réseau sortante : la coque Android les bloque et c'est une promesse faite aux utilisateurs.
- Les `let/const` d'`index.html` ne sont pas sur `window` : passer par `window.APPX`.
- Le service worker (`sw.js`, mode serveur) met en cache à l'exécution, rien à lister.
- Garde-fous du jeu non négociables : aucun argent, aucune série à perdre, jetons seulement par effort réel, plafond quotidien, taux affichés.

## Publier une version (procédure qui a déjà échoué une fois : la suivre à la lettre)
1. Passer `VERSION_CODE` (+1) et `VERSION_NAME` dans `android/gradle.properties`, écrire `notes-de-version/v<VERSION_NAME>.md`.
2. Lancer tous les tests.
3. `git add -A && git commit && git push`.
4. **Seulement ensuite**, créer la release GitHub dont le tag est `v` + `VERSION_NAME` (sinon le tag pointe vers un ancien commit et le workflow échoue avec « Le tag ne correspond pas à VERSION_NAME »).
Version actuelle : voir `android/gradle.properties` (0.3.1 au moment du passage de relais).

## Avatar : le chantier en cours (pas encore dans l'appli)
Georgio veut un **avatar personnalisable, homme ou femme**, qui soit **l'élément phare** de l'appli, très soigné, qui donne envie de progresser, personnalisable avec la garde-robe du jeu, qui **évolue avec l'entraînement** (idéalement zone par zone) et apparaisse aussi dans les animations d'exercices.
- Les trois directions dessinées à la main en SVG ont été **refusées** (`design/avatar/`).
- Il a installé Claude Code sur son PC Bazzite avec **Blender connecté** : l'idée est de modéliser/styliser l'avatar dans Blender.
- Piste technique à trancher avec lui avant de produire en masse : (a) calques PNG/WebP rendus depuis Blender (corps par niveau de muscle, coiffures, tenues, accessoires, empilés comme des sprites : léger, compatible WebView, personnalisation par superposition) ; (b) modèle glTF affiché avec three.js dans la WebView (rotation possible, plus lourd, plus risqué sur téléphones modestes). Poids total visé : quelques Mo, hors ligne.
- Contraintes : tout doit fonctionner hors ligne dans l'APK, rester lisible en petit (vignettes d'exercices), exister en version homme et femme, et s'accorder avec les 27 esprits.
- Ne pas produire des dizaines d'objets : d'abord **un** personnage de référence validé visuellement par Georgio (capture d'écran), puis les variantes.

## Reste à faire
- Avatar (ci-dessus). Zones et exercices manquants : avant-bras, trapèzes, obliques, adducteurs (les formes musculaires sont dessinées mais absentes de `ZONES` et `EXZ`).
- Non vérifié sur téléphone réel : changement d'icône du lanceur, fluidité des animations dans la WebView, empreinte de la signature.
