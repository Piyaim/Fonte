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

### Écrire l'interface : moins de texte, plus direct (décision du 20/10/2026, lot 2C)
- L'utilisateur doit comprendre chaque écran en 2 secondes. **Une idée par carte** : titre de 6 mots au plus, puis une seule phrase de 15 mots au plus.
- Tout le reste (explications, exemples, détails de réglages) va dans un repli **« Détails »** fermé par défaut (`<details class="det">`, fonction `det()` de `profil.js`). Bouton du repli : 44 px de haut au moins.
- Des chiffres plutôt que des phrases (« 3 × 10-12 · repos 90 s », « Conseil : 55 kg × 8 »). Pas de parenthèses explicatives. Pas de répétition d'une info déjà visible sur l'écran. Pas de jargon visible (« 1RM » seulement dans « Détails » ou Progrès).
- Mots fixés : « Semaine légère » (et non plus « semaine allégée »), « Conseil : … » (une seule ligne de conseil par exercice), « Dernière : … », « Détails ».
- **Toujours visibles, jamais dans un repli** : l'avertissement médical et « Arrête l'exercice en cas de douleur vive, de vertige ou de gêne à la poitrine » (au moins sur le résumé), l'alerte « Consulte un médecin » (santé « Oui »), les messages de blessure (« aucun exercice de ce type ne convient… »), le bouton « Démarrer la séance » en tête de l'accueil.
- Contrôlé par `tests/lot2c.py` (carte de proposition : 25 mots visibles au plus hors « Détails » et hors boutons ; une seule ligne de conseil par bloc d'exercice). Dans les tests, ouvrir les replis avant de chercher un texte qui doit exister (`OUVRIR`), et surtout avant de vérifier qu'un mot interdit (« IMC », « manquée ») est absent.

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
    Postures revues le 20/10/2026 (audit biomécanique, validé sur téléphone). Le pied posé au sol se mesure par rapport au sol (ftAbs, ftRel pour les exceptions) ; la vue de face accepte un raccourci de perspective (tk, hk, k, k1, k2). tests/figures.py contrôle les points corrigés.
    Remarques de Georgio (20/10/2026, seconde passe) : de profil, `fore` (avec `ik`) fixe la direction de l'avant-bras et dessine le bras en raccourci (coude écarté vers l'extérieur) ; développés épaules en vue de face, face pull en vue de dos. Bouton « Tourner » dans la fiche : `FIGDATA[slug].alt` donne une seconde vue (4 exercices aujourd'hui), choix non enregistré, vignettes toujours en vue principale (`tests/tourner.py`).
  - `creatures.js` : dessin actuel des 27 esprits en SVG (6 silhouettes × 3 stades, auras par rareté), à remplacer par les sprites pixel art (section 8). `jeu.js` : règles du jeu (jetons, tirages, quêtes, boutique, garde-robe par variables CSS `--f3 --f4 --f5 --fxc`).
  - `profil.js` : questionnaire de départ et programme généré (section 8 bis).
  - `sw.js` : service worker du mode serveur (cache à l'exécution, rien à lister).
  - `notif.js` : notifications (page Menu ☰ > Notifications, plan des 14 prochains jours confié à la coque ; section 8 ter).
- `android/` : coque Java (`MainActivity.java`, et pour les notifications `Notifs.java`, `NotifRules.java`, `AlarmReceiver.java`, `BootReceiver.java`), icônes alternatives par couleur, `gradle.properties` (`VERSION_CODE`, `VERSION_NAME`).
- **Entrées de lanceur** : une `activity-alias` par couleur ; le noir et blanc utilise `.IconNoirBlanc` depuis la 0.5.3 (sur le téléphone de Georgio, le lanceur gardait l'ancien dessin de `.IconMono` après la mise à jour). `.IconMono` reste déclarée mais n'est plus activée : `MainActivity.migrateIcon` et `setIcon` la désactivent. Si le dessin du logo change encore et qu'un lanceur garde l'ancien, même remède : une entrée au nom neuf. Cause exacte non prouvée (cache d'icônes du lanceur).
- **Logo** (« Élan », haltère incliné en fonte, choisi le 21/10/2026) : **tout est généré par `tools/logo.py`**, ne rien retoucher à la main. Il écrit l'avant-plan `drawable/ic_fg.xml` (dégradés, API 24+), la silhouette `ic_fg_mono.xml` (icône à thème), un fond `ic_bg_<couleur>.xml` par couleur, les icônes WebP des anciens Android, le logo du menu `server/static/icons/logo-<couleur>.svg`, les icônes de la version serveur `server/icons/` (hors APK) et `fastlane/…/icon.png`. Relancer `python3 tools/logo.py` après toute modification du dessin, puis `tests/logo.py`.
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

Valeurs actuelles (inchangées depuis v0.3.1, toujours valables en v0.4.0) :
- Taux : Commun 58, Peu commun 26, Rare 11, Épique 4, Légendaire 1. Compassion (pity) : Épique à 30, Légendaire à 90 tirages.
- Tirage : 1 jeton, ×5 possible. Plafond : 4 jetons par jour.
- Éclats par doublon : C 4, U 10, R 30, E 80, L 200. Prix boutique : 40, 100, 300, 800, 2000.
- Niveau d'une zone = 1 + partie entière de la racine carrée du nombre de séries dans la zone ; stade 2 au niveau 6, stade 3 au niveau 14.
- Jetons : 3 séries ou plus +1, 10 séries ou plus +1, record battu +1 (tout cela exige au moins 3 séries). **Le ressenti ne rapporte plus rien** (22/10/2026) : il sert seulement au conseil de charge. L'historique existant ne donne aucun jeton. Cadeau de bienvenue : 3 jetons + l'esprit Gloumi.
- Rencontres méritées par zone (rencontres.md) : idée en pause jusqu'à la refonte des esprits ; le tirage actuel reste en place d'ici là. Le ressenti ne rapporte plus de jeton.
- Quêtes : objectif de séances `WGOAL` +2, 5 zones différentes +1, équipe complète +2.
- **Masquer l'onglet Esprits** (22/10/2026) le retire seulement de la barre du bas (et masque la carte de l'accueil et l'écran de récompense, choix confirmé par Georgio) : « Esprits » reste dans le menu ☰, et l'interrupteur « Afficher l’onglet Esprits dans la barre du bas » du menu le remet.
- État dans `localStorage`, clé `muscu-jeu`. 27 esprits dans le code (45 prévus par le bestiaire v3), 25 objets (tenue, cheveux, muscle). L'onglet « Esprits » peut être masqué dans les options.
- Un esprit **ne régresse jamais** si l'utilisateur fait une pause : une zone oubliée reste visible pour inviter à la travailler, sans punir.
- **Aucun compteur de série** (lot 2C, 20/10/2026) : rien qui retombe à 0 après une pause ni qui récompense des jours ou des semaines consécutifs. L'ancien « N semaines d'affilée » (accueil et Progrès, avec son « record ») est remplacé par **« N séances au total »**, qui ne baisse jamais. Restent, car ce ne sont pas des séries (rien d'acquis n'est perdu) : l'objectif de la semaine (« n/3 », anneau et carte « Cette semaine » de l'accueil, barre de Progrès) et les quêtes de la semaine du jeu (règle du jeu : non touchée).
- **Aucune notification liée aux Esprits ni aux jetons** (décision du 20/10/2026, version 0.5.0) : `notif.js` ne lit pas l'état du jeu ; `tests/notifications.py` le contrôle.

---

## 5. Tests

Fichiers dans `tests/`, à lancer avec `python3 tests/nom.py` (Playwright et Flask requis). Chacun doit finir **sans « ÉCHEC »**.
- `figures.py` : moteur d'animation. `ui_local.py` : interface en mode local. `jeu.py` : règles du jeu (environ 40 contrôles). `simulation_android.py` : simulation de la coque. `differentiel.py` : le mode serveur et le mode local doivent répondre à l'identique (99 comparaisons, réglages par séance compris ; les clés `jeu` et `profil` sont dans `DROP`). `icone_app.py` : icônes. `logo.py` : les dessins Android relus par un traducteur indépendant donnent la même image que le logo du menu, et l'haltère reste dans la zone visible.
- `profil.py` : questionnaire de départ et programme généré (IMC, exemple du cahier des charges, blessures, santé, IMC caché, « Garder mes programmes », catalogue inchangé par le générateur, export/import).
- `migration.py` : sort le code du commit 805eba3 de Git, lui fait créer de vraies données (SQLite, IndexedDB, photos, profil, jeu), puis vérifie que le code actuel les rouvre sans perte. À garder tant que l'historique Git contient ce commit.
- `reglages_seance.py` : même exercice réglé différemment dans deux programmes (écrans Programmes et Séance, conseil de charge, minuteur, retour aux valeurs de l'exercice), modes local et serveur.
- `import_profil.py` : un import réussi fait sauter le questionnaire (depuis « Bienvenue » et depuis Données, modes local et serveur) ; import en échec ou annulé : rien ne change.
- `seance.py` (lot « Séance ») : modes local et serveur ; poids décimaux (virgule ou point, enregistrés, affichés, courbe, export et import, conseil sans arrondi), lignes préremplies par le conseil, un exercice à la fois par défaut et Aperçu, − et + (appui long, jamais sous 0), ✓ (vibration de 15 ms, repos), ressenti en 3 choix, minuteur (±15 s, Passer, Autre durée, visible sur les autres onglets), écran allumé (coque simulée), 360 px. 12 témoins par mutation (script de session `temoins.py`).
- `retours_seance.py` : onglet Esprits masqué puis remis depuis le menu, conseil toujours au pas du matériel (6 pas, 7 cas, assistance comprise), ligne active visible à l'ouverture (390 et 360 px), ✓ pâle, minuteur compact, conséquences du ressenti égales au conseil suivant, contrastes des 6 couleurs. Échoue 40 fois sur le code de l'APK de test d'avant ces corrections.
- `proposition_seance.py` : séance proposée par l'accueil avec un programme généré (questionnaire, Haut/Bas, séance enregistrée en mode focus et depuis l'Aperçu, lendemain, jours sans séance), modes local et serveur ; 25 échecs sur le code de la 0.6.0.
- `lot2c.py` : règles d'écriture (cartes courtes, un seul conseil par exercice, replis fermés et de 44 px, avertissements toujours visibles).
- `lot2b.py` : dates simulées (horloge de Playwright, `page.clock.set_fixed_time`) : phases, « Plus tard », semaine allégée, reprise, mot « manquée », placement (624 choix de jours), conseil combiné, IMC ≥ 30, bouton « Démarrer la séance » en tête, boutons de 44 px. `migration_lot2b.py` : données créées par le code de 64e77a8 (programme généré par l'interface) rouvertes par le code actuel, et nouvel export importé dans l'ancien code.
- `migration_v031.py` : le code de la **dernière version publiée** (tag `v0.3.1`, sorti par `git archive`, ou dossier `ANCIEN_DIR`) crée de vraies données en mode serveur et en mode local (deux origines : 127.0.0.1 et localhost), exports compris ; le code actuel les rouvre (tout identique, photos octet par octet, jeu), questionnaire affiché une fois, « Garder mes programmes » sans effet sur les données, exports 0.3.1 importés dans une appli neuve (questionnaire sauté), aucune requête sortante. **À chaque nouvelle version** : copier ce test en `migration_vX.py` avec le tag de la version publiée précédente (ou changer `TAG`).
- `migration_v042.py` (pour la 0.5.0) : même méthode depuis le tag `v0.4.2` (questionnaire rempli, programme généré et réglages par séance, photos, jeu) ; le code actuel rouvre tout à l'identique (profil et jeu compris), page Notifications, plan calculé avec une coque simulée, réglages des notifications absents de l'export ; exports 0.4.2 importés dans une appli neuve, export 0.5.0 importé dans la 0.4.2. Le tag `v0.4.2` a été créé sur GitHub : `git fetch origin tag v0.4.2 --no-tags` s'il manque en local. Remplacé pour la 0.6.0 par `migration_v053.py` (même méthode depuis le tag `v0.5.3`, plus le contrôle que l'ancien code n'a ni mode focus ni pas du matériel). Pour la 0.6.1 : `migration_v060.py` (même méthode depuis le tag `v0.6.0`, plus le contrôle que l'ancien code a le mode focus et le pas du matériel mais pas le correctif de la séance proposée). Prochaine version : copier `migration_v060.py` avec le tag `v0.6.1`.
- `notifications.py` : page Notifications (version serveur : explication seule ; appli : valeurs par défaut, autorisation refusée, « Alarmes et rappels » demandée seulement en activant la fin du repos, un bouton « Son et vibration » par canal, Android 7 sans canaux, notification d'essai), demande d'autorisation après le questionnaire, planification sur dates simulées (une par jour, heures calmes, étape reportée au jour libre suivant et une seule fois, bilan, « Bon retour » une seule fois puis rien, aucune notification d'Esprit), texte de fin du repos, aucune requête sortante. Fausse coque `FonteApp` injectée par `add_init_script`.
- `notif_java.py` : règles de la coque (`NotifRules.java` : heures calmes, plafond d'une par jour, événement envoyé une seule fois, rien de plus de 2 h en retard), compilées et lancées dans le conteneur `eclipse-temurin:17-jdk` (podman), sans Android. 12 témoins par mutation (JS et Java) : `/home/PM/fonte-travail/notifications/temoins.py`.
- **Typographie** : espace insécable (`\u00a0`) avant « % » et avant le « : » qui suit une valeur calculée ; contrôlé par `lot2c.py` (carte rétrécie de 360 à 100 px, aucun « % » précédé d'une espace sécable sur les écrans principaux). Les tests qui cherchent « Conseil : », « Dernière : » ou un pourcentage écrivent donc `\u00a0`.
- Réseau : `simulation_android.py` bloque et note toute requête hors de l'adresse de la coque, sur les 11 onglets (Notifications compris), les sous-onglets des Esprits, une fiche d'exercice et le questionnaire (témoin inclus).
- Témoins par mutation : script de session `temoins.py` (une règle faussée à la fois dans le code, test relancé, fichier remis à l'identique, empreinte vérifiée). Piège : dans un test Playwright synchrone, `time.sleep` bloque les boîtes `alert` ; attendre avec `pg.wait_for_timeout`.
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
### APK de test (identifiant `app.fonte.suivi.test`, construit sur le PC)
- Conteneur podman `eclipse-temurin:17-jdk`, SDK `/home/PM/Android/Sdk`, cache Gradle `/home/PM/.cache/fonte-gradle`, `sh ./gradlew --no-daemon --offline -q -PAPP_ID=app.fonte.suivi.test assembleRelease` (commande complète dans JOURNAL.md).
- **Toujours monter la clé de test fixe** : `-v /home/PM/fonte-travail/cle-test:/root/.android` (créée le 20/10/2026, hors dépôt, mot de passe public « android »). Sans elle, chaque construction crée une clé jetable : les APK de test du lot 1 et du lot 2A ont deux clés différentes, et aucun APK ne peut s'installer par-dessus eux.
Version actuelle : voir `android/gradle.properties` (0.6.1, VERSION_CODE 15, 22/10/2026 : correctif, l'accueil propose la séance qui suit la dernière faite, section 8 bis lot 2B). Précédente : 0.6.0 (VERSION_CODE 14, publiée le 22/10/2026 : lot « Séance », section 8 quater) ; 0.5.3 (VERSION_CODE 13, préversion du 21/10/2026 : icône noir et blanc qui gardait l'ancien dessin sur le lanceur) ; 0.5.2 (VERSION_CODE 12 : nouveau logo « Élan ») ; 0.5.1 (VERSION_CODE 11, préversion du 21/10/2026 : démonstrations corrigées après les remarques de Georgio, bouton « Tourner »). Version publiée précédente : 0.5.0 (VERSION_CODE 10 : notifications, section 8 ter) ; 0.4.2 (VERSION_CODE 9 : séance par zones « Poids du corps uniquement », choix du groupe d'un nouvel exercice en liste, dead bug corrigé) ; 0.4.1 : couleur « Noir et blanc ».
### Émulateur Android (essais de la coque sur le PC)
- AVD `Pixel_8` (Android 16, API 36, image `google_apis`, donc `adb root` possible) dans `/home/PM/Android/Sdk`. Lancer en lecture seule pour ne pas modifier l'AVD : `/home/PM/Android/Sdk/emulator/emulator -avd Pixel_8 -read-only -no-snapshot -no-window -no-audio -no-boot-anim -gpu host -camera-back none -camera-front none`. Avec `-gpu swiftshader_indirect` ou `-gpu guest`, l'émulateur plante (erreur de segmentation) sur cette machine.
- Pilotage par `adb` et l'arbre d'accessibilité (`uiautomator dump`), qui expose le texte de la WebView : outil `/home/PM/fonte-travail/notifications/emu.py` (lire l'écran, toucher un texte, capturer). Arrêt : `adb emu kill`. Ne pas tuer le processus par `pkill -f` (la commande se tue elle-même).
- Pas d'image Android 7 (minSdk 24) : rien n'a été essayé sur un vrai Android 7. Une couleur ajoutée doit exister partout (index.html `ACC`, `MainActivity.ICONS`, alias du manifeste, couleurs de `tools/logo.py` qui produit `ic_bg_*`, les icônes et les SVG, `local-backend.js`, `app.py`) : `tests/icone_app.py` le vérifie.

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
- Règles, dans l'ordre : sécurité (santé « Oui » → programme allégé, 2 séries, ni intervalles ni course ; moins de 18 ans → 8 répétitions au minimum, jamais d'intervalles (lot 2B) ; IMC ≥ 30 → cardio à faible impact ; blessure → remplaçant, sinon autre exercice de la même famille de schéma moteur, sinon retrait expliqué, jamais un exercice déconseillé), niveau et phase (phase 1 sans isolation, 5 exercices au plus ; Avancé = phase 3 d'emblée depuis le lot 2B), fréquence (A/B, Haut/Bas, Poussée/Tirage/Jambes/Haut/Bas), durée (4 à 7 exercices, cardio d'après le tableau des durées), objectif.
- Blessures (décision de Georgio) : si l'exercice et son remplaçant sont déconseillés, prendre un autre exercice du même type (interprétation de Claude : même **famille** de schéma moteur, poussée horizontale ou verticale, tirage horizontal ou vertical), de préférence absent de l'autre séance ; sinon le retirer avec « … : aucun exercice de ce type ne convient à ta blessure … Demande conseil à un professionnel de santé. » « Aucune » est exclusive.
- Choix techniques validés : phase 1 sans isolation ; durée du cardio d'après le tableau des durées ; intervalles en fin de 1re séance seulement (endurance ou athlétique, phase 2).
- Programmes remplacés seulement après confirmation (création des nouveaux programmes, puis suppression des anciens ; historique intact, chaque séance passée garde son nom ; séance en cours non enregistrée rattachée à « séance libre »). « Garder mes programmes » enregistre le profil sans rien toucher ; « Mon profil » permet de générer plus tard.
- La table des 50 exercices (`LIB` dans `profil.js`) est **à relire par un professionnel** : contre-indications, impacts, types et une partie des niveaux et remplaçants sont des propositions de Claude. Elle n'est pas validée médicalement.

### Lot 2A : réglages propres à chaque séance (20/10/2026, validé sur le téléphone de Georgio)
- Un même exercice peut avoir des séries, une cible (min, max) et un repos **différents selon le programme** (par exemple 4 × 5 en séance force, 3 × 12 en séance volume). Prépare la phase 3 (lot 2B).
- Réglages **facultatifs** sur `workout_item` (séries, cible min, cible max, repos) : vide = valeurs de l'exercice, comme avant. Mêmes règles dans `app.py` et `local-backend.js`, comparées par `tests/differentiel.py`.
- Migration sans perte d'une base SQLite et de données IndexedDB créées par le code de 805eba3 ; un ancien export s'importe toujours, un nouvel export restitue les réglages.
- L'écran Séance affiche les réglages de la séance et le conseil de charge les utilise ; l'écran Programmes permet de les voir, de les modifier et de revenir aux valeurs de l'exercice.
- Le générateur écrit ses séries, répétitions et repos **dans les réglages de séance** et **ne modifie plus le catalogue d'exercices**. La confirmation montre les réglages de chaque nouvelle séance (plus de section « Exercices modifiés »). « Garder mes programmes » et « Annuler » ne changent rien.
- Format (choix de Claude) : chaque programme de `/api/state` et de l'export porte `settings` = `{"id d'exercice": {sets, target_min, target_max, rest}}`, seulement pour les exercices réglés ; un champ vide (`null`) prend la valeur de l'exercice. `PUT /api/workouts/<id>` : avec `settings`, les réglages sont remplacés (`null` = tout effacer) ; sans `settings` (ancienne interface), ceux des exercices restés sont gardés. Mêmes bornes que l'exercice (séries 1-10, cible 1-1000, repos 0-600), cible min et max inversées si besoin, une seule cible = les deux. Archiver ou supprimer un exercice retire aussi son réglage.
- Migration : SQLite, colonnes ajoutées par `ALTER TABLE` au démarrage (`migrate` dans `app.py`) ; IndexedDB, champs `null` ajoutés au chargement puis enregistrés (`migrate` dans `local-backend.js`).
- **Version de l'export inchangée (`version: 1`)** : le changement est un ajout facultatif ; aucun des deux importeurs ne lit ce numéro ; un ancien export s'importe sans changement ; un nouvel export importé dans une ancienne version de l'appli perd seulement les réglages, ce qu'un nouveau numéro n'empêcherait pas (l'ancien code ne le lit pas). Même pratique que pour les clés `jeu` et `profil`.

### Lot 2B : progression (20/10/2026, validé par Georgio, tableau de la phase 3 compris, comme proposition non relue par un professionnel)
- **Principe non négociable** : à chaque ouverture, l'accueil propose la séance à faire, bouton « Démarrer la séance » en tête ; tout ce que le lot 2B ajoute (carte de proposition, semaine allégée ou reprise en cours, ligne de jour de repos) est **dessous**, jamais à la place.
- **Jamais de séance « manquée »** : le mot n'apparaît nulle part, aucun compteur de séances non faites, aucune couleur d'alerte. Seul l'écart depuis la dernière séance déclenche une proposition, toujours formulée positivement.
- Propositions (passage de phase, semaine allégée, reprise) : une carte sur l'accueil (une seule à la fois, ordre reprise, semaine allégée, phase), et toutes dans « Mon profil », avec « Accepter » et « Plus tard » (reproposée 7 jours après). Rien ne change sans « Accepter ».
- Phases : phase 1 de 4 semaines (2 pour Débutant), phase 2 jusqu'à la semaine 12 (8 semaines après son début réel si elle a été acceptée en retard), phase 3 ensuite ; Avancé : phase 3 d'emblée (un ancien profil Avancé en phase 2 se la voit proposer tout de suite). Un passage réécrit **seulement les réglages de séance** des programmes générés (exercices de la bibliothèque), jamais le catalogue, les exercices des programmes ni l'historique ; il n'ajoute donc pas l'isolation de la phase 2 (« Générer un programme à partir de ce profil » le fait, en gardant la phase atteinte).
- Phase 3 : le programme n° i prend le type force, volume et endurance, puissance et cardio (i modulo 3) ; avec 2 programmes, une séance C est ajoutée (lot 2C, ci-dessous). Table `PRM3` dans `profil.js` : proposition de Claude **validée par Georgio** (20/10/2026), non relue par un professionnel. Profils protégés (santé « Oui », IMC ≥ 30, moins de 18 ans) : cardio continu et facile, sans intervalles.
- Semaine allégée : proposée 5 semaines après le début du cycle (début du programme, de l'import, ou fin de la dernière semaine allégée ou reprise), ou après plus de 7 jours sans séance ; dure 7 jours, se termine seule ; charges proposées −20 %, mêmes séances. Reprise : après 22 jours ou plus sans séance (« au-delà de 3 semaines »), 7 jours à 80 % des charges.
- Conseil de charge (un seul, priorité : reprise, semaine allégée, baisse −5 à 10 % après 2 séances de suite sous la fourchette, ressenti 5 = garder, montée par double progression +1 à 2,5 kg (2,5 % borné) et retour au bas de la fourchette, ou ressenti 1-2 avec toutes les séries au minimum). Séance sous la fourchette = au moins la moitié des séries sous le minimum ; les séances de semaine allégée et de reprise ne comptent pas. Secondes et poids du corps : +5 à 10 s, ou 1 à 2 reps, ou une série. « Dernière fois », lignes préremplies et conseil : dernière séance du **même programme** si elle existe, sinon de l'exercice. Phase 1 : rappel « jamais jusqu'à l'échec ».
- Placement : séances sur les jours de la question 16 (sous-ensemble si plus de jours que de séances), le moins possible de jours de suite pour un même groupe musculaire (zones principales des exercices, sans tronc, lombaires ni cardio), 3 séances = A, B, A puis B, A, B (parité de la semaine depuis le début du programme). Accueil : séance prévue aujourd'hui, sinon la prochaine prévue (**correctif du 22/10/2026** : les jours viennent du calendrier, mais la séance est celle qui suit la dernière faite du programme ; un jour prévu passé sans séance ne fait pas avancer la rotation ; même règle pour les rappels ; « Cette semaine » de « Mon profil » garde la séance du calendrier pour les jours passés), avec « Jour de repos : la récupération fait partie du progrès. » les jours sans séance prévue. Sans questionnaire rempli ou sans programme généré : comportement d'avant (séance qui suit la dernière faite).
- Repos +30 s si IMC ≥ 30, 3 min au plus ; avec « Non » au détail santé, la raison n'est jamais écrite.
- **Données (choix de Claude)** : tout dans le profil `muscu-profil`, toujours `version: 1`, champs ajoutés : `program.ids` (programmes générés, dans l'ordre), `program.start`, `program.phase_start`, `program.history`, et `cycle` = {`light`: [{kind: allegee|reprise, start, end}], `later`: {phase|allegee|reprise: date}}. Pourquoi : l'état du programme dépend du questionnaire, il suit l'export et l'import local sans changer l'API ni `app.py` (différentiel inchangé) ; garder `version: 1` permet à l'ancien code (qui exige `version === 1`) d'accepter un nouvel export. Migration : `upgrade()` retrouve les programmes générés par leur nom au lancement (date de début = date de génération) ; si un nom manque, phases et placement restent inactifs. Limite connue : en mode serveur, cet état reste dans le navigateur (comme le profil), il n'est pas dans `/api/export`.
- Boutons ↑ ↓ ✕ de l'écran Programmes : 44 × 44 px.
- Plus tard : bouton « J'ai mal », circuit d'endurance.

### Lot 2C : séance C « puissance et cardio » (20/10/2026, validé sur le téléphone de Georgio ; version 0.4.0)
- Détails de la carte « Phase 3 prête » : liste de la séance C, une ligne « A : force · B : volume et endurance · C : puissance et cardio » (nom du programme sans « Séance »), « Ton historique reste le même. » Rien d'autre.
- Décision de Georgio : avec 2 programmes générés (A/B ou Haut/Bas : 2, 3 ou 4 séances), le passage en phase 3 propose d'**ajouter une 3e séance**. Carte « Phase 3 prête » / « Une 3e séance s'ajoute : puissance et cardio. », exercices de C dans « Détails ». « Accepter » crée C (nom « Séance C »), puis réécrit les réglages : A = force, B = volume, C = puissance et cardio. « Plus tard » ne change rien. Rien n'est supprimé, historique intact.
- Composition de C (`FB_C`, `planC`, `structOf` dans `profil.js`) : corps entier, exercices **polyarticulaires seulement** (ni isolation ni tronc ; remplaçants de blessure aussi polyarticulaires), nombre selon la durée (4 à 7), de préférence absents de A et B ; mêmes règles que le générateur (lieu, niveau, blessures, exercices à éviter, profils protégés) ; cardio à la fin, durée haute de `x.cardio` (donc durée basse pour l'objectif force et un IMC sous 18,5, comme ailleurs) ; intervalles seulement pour endurance et athlétique, jamais pour un profil protégé. Si aucun exercice de force n'est possible, pas de séance C.
- Rotation A, B, C, A… continue d'une semaine à l'autre, quel que soit le nombre de séances (`seqFor` : séance n° (semaine × séances + i) modulo programmes, comptée depuis `program.rot`, lundi de l'ajout de C ou de la génération ; sans `rot`, depuis `program.start`). Pour 2 programmes, c'est exactement l'alternance du lot 2B.
- Profil Avancé (phase 3 d'emblée) : le générateur crée directement A, B et C. 5 séances : rien ne change. Programmes importés ou gardés : jamais de séance C automatique (elle vient seulement de « Générer un programme à partir de ce profil »).
- Données (profil `muscu-profil`, toujours `version: 1`) : `program.ids` gagne l'id de C, `program.workouts` son nom, `program.extra` = id de C, `program.rot` = lundi de départ de la rotation. Si l'utilisateur supprime C, `managed()` la retire de la rotation (A, B) sans désactiver phases et placement.
- Tests : `tests/lot2c.py` (acceptation, « Plus tard », genoux sur 36 programmes, santé « Oui », moins de 18 ans, IMC 32, rotation sur 3 semaines avec 2, 3 et 4 séances, C supprimée, Avancé avec 2, 4 et 5 séances, « Garder mes programmes »), 7 témoins par mutation.

## 8 quater. Lot « Séance » (22/10/2026, décisions de Georgio après l'audit UX ; validé sur son téléphone, version 0.6.0)
- **Un exercice à la fois par défaut** : « Démarrer la séance » et « Reprendre la séance » ouvrent le mode focus ; bouton « Aperçu » = toute la séance en liste (vignettes fixes, ✓ sur chaque série, bouton « Faire cet exercice »). `F.ap` mémorise le choix de l'Aperçu dans le brouillon. Une séance passée se modifie toujours en liste, sans ✓.
- **Saisie** : champs texte (`inputmode="decimal"`), virgule ou point, **aucun arrondi** à l'enregistrement ni à l'affichage (`fmt` ne fait que nettoyer les restes de calcul, `toPrecision(12)`). La première série non validée a des boutons − et + de 48 px : 0,5 kg (charge, lest), 1 rep ; choix de Claude : 5 s pour les exercices en secondes, 1 niveau et 1 min pour le cardio. Appui long : répète après 0,4 s, toutes les 0,1 s. Jamais sous 0.
- **Lignes préremplies avec le conseil de charge** (`loadTip` renvoie aussi les valeurs proposées ; `tipSets`), sinon la dernière séance, sinon vides. Baisse « 36-38 kg » : choix de Claude, préremplie à la valeur haute (−5 %).
- **✓** : vibration de 15 ms, repos de l'exercice, la série suivante remonte au-dessus du minuteur.
- **Ressenti** : 3 boutons « Facile », « Juste bien », « Dur », une seule fois après la dernière série validée, puis une ligne avec « Changer ». Enregistré 2, 3, 4 (échelle 1-5 inchangée dans les données ; anciennes notes 1 et 5 lues Facile et Dur). Règle du conseil changée : **« dur » (4 ou 5) fait garder la charge** ; « facile » fait monter si toutes les séries ont atteint le bas de la fourchette ; « juste bien » laisse décider les répétitions (montée au haut de la fourchette).
- **Minuteur** : barre du bas, compte à rebours de 44 px, −15 s, +15 s, Passer, Autre durée (60 s, 90 s, 2 min), « Ensuite : … » ; visible sur tous les onglets pendant un repos (classe `rest-on`), sur l'onglet Séance seulement sinon. À zéro par −15 s, le repos s'arrête sans sonner.
- **Écran allumé** : en mode focus et pendant un repos, réglage « Garder l’écran allumé » dans le menu (clé `muscu-ecran`, activé par défaut). Coque : `FonteApp.keepScreenOn(bool)` pose ou retire `FLAG_KEEP_SCREEN_ON` ; navigateur : Screen Wake Lock s'il existe. Vérifié sur le téléphone de Georgio (22/10/2026).
- **Couleurs du thème clair** : texte des boutons orange `#1b1005` (5,2:1 sur `#e8590c`), gris `--m` `#56636e` (5,4:1 sur le fond). Conseil en texte foncé avec un trait orange à gauche (l'orange en texte fin fait 3,2 à 3,6:1). Tailles : conseil 18 px gras dans le focus, « Dernière » 15 px, étiquettes des courbes 12 unités (au moins 11 px à 360 px).
- **Retours sur l'APK de test (22/10/2026)** : écran allumé, appui long, vibration du ✓ et virgule confirmés sur téléphone.
  - **Pas du matériel** (décision de Georgio) : le conseil arrondit au pas déduit des charges des 10 dernières séances de référence (`kgStep` : 2,5 kg si toutes en sont multiples, sinon 2, 1,25, 1, 0,5 ; aucun → arrondi à 0,5 kg d'avant). Montée d'au moins un pas, baisse et semaine légère au moins un pas sous la charge. Exemple : 3 × 12 à 52,5 kg → 55 kg (54 avant). Les boutons − et + gardent leur pas de 0,5 kg.
  - Ouverture d'un exercice en focus : la ligne active défile juste au-dessus de la barre de repos (`focReveal`). ✓ pâle dans le rond d'une série non validée. Hors de l'onglet Séance, minuteur d'une ligne (temps, Passer) agrandi au toucher (`BARX`, bouton « Réduire »).
  - Ressenti : sous chaque bouton, le conseil de la prochaine séance du programme (`feelNext` : `loadTip` sur l'historique plus la séance en cours) ; rien pendant une semaine légère ou une reprise.
  - Contrastes ≥ 4,5:1 : `--at` = couleur d'accent réservée au texte (orange `#a83a0a` en clair), `--a` reste celle des boutons ; vert `#277c38` ; dégradé de l'accueil foncé côté clair pour chaque couleur.
- Progrès : la flamme est remplacée par un haltère (`IC_TOTAL`, `totalBar`). Style d'apparence : le style « Dynamique », seul restant, est fusionné (règles en `:root`, même priorité, 0 pixel de différence sur 24 captures) ; sélecteur et style « Cartes » supprimés.

## 8 ter. Notifications (version 0.5.0, décisions de Georgio du 20/10/2026)
- **Réservées à l'appli Android** : la version serveur (navigateur) affiche seulement « Disponibles seulement dans l'appli Android. ». Tout est local (AlarmManager, BroadcastReceiver, NotificationChannel), ni réseau ni Firebase.
- **Autorisation** : demande système POST_NOTIFICATIONS (Android 13 et plus ; permise d'office avant) une seule fois, juste après le questionnaire, ou à l'ouverture pour un profil déjà rempli. Après un refus, l'appli ne redemande pas d'elle-même ; le bouton « Activer les notifications » de la page réaffiche la demande tant qu'Android le permet, puis ouvre les réglages de notifications de l'appli (documentation Android : après deux refus, la demande ne s'affiche plus).
- **« Alarmes et rappels »** (SCHEDULE_EXACT_ALARM) : demandée seulement quand l'utilisateur active « Fin du repos » ; `canScheduleExactAlarms()` vérifié avant chaque alarme exacte (sans elle, `setExact` lève une SecurityException depuis Android 14). Sans l'autorisation, la fin du repos reste dans l'appli.
- **Types et canaux** : un canal par type, réglé par l'utilisateur dans Android via le bouton « Son et vibration » de chaque carte (ACTION_CHANNEL_NOTIFICATION_SETTINGS) ; l'appli ne choisit pas le son (un canal créé ne peut plus être modifié par l'appli). Canaux : « Rappels de séance » (`rappels`), « Fin du repos » (`repos`, importance haute, vibration), « Programme et bilan » (`programme` : étapes, bon retour, bilan). Android 7 (pas de canaux) : son et vibration par défaut réglés sur la notification, boutons « Son et vibration » masqués.
- **Valeurs par défaut** (validées) : tout activé sauf la fin du repos ; rappel à 18:00 les jours du questionnaire (sinon lundi et jeudi) ; heures calmes 21:00-08:00 ; « Bon retour » après 7 jours sans séance ; bilan du dimanche activé.
- **Textes** (validés) : « Séance B prête : 6 exercices » / « Touche pour commencer. » ; « Repos terminé » / « Prochaine série : Développé couché, série 3 sur 4. » ; « Phase 2 prête » / « Ouvre Fonte pour voir ce qui change. » ; « Phase 3 prête » / « Une 3e séance s'ajoute : puissance et cardio. » ; « Semaine légère prête » / « Charges à −20 % pendant 7 jours, si tu veux. » ; « Bon retour quand tu veux » / « Ta séance B est prête, à ton rythme. » ; « Ta semaine : 3 séances » / « 42 séries · 5 zones travaillées · 1 record » ; « Notification d'essai » / « Les notifications de Fonte fonctionnent. »
- **Règles de planification** : une notification par jour au plus (fin du repos à part), par priorité rappel, étape (sinon reportée au jour libre suivant), bon retour, bilan ; toutes à l'heure du rappel ; rien pendant les heures calmes (la fin du repos seule y est permise) ; pas de rappel le jour où la séance est faite ; après 7 jours sans séance (ou 7 jours après l'activation sans aucune séance), plus de rappel ni d'étape : un seul « Bon retour » (seulement s'il existe une séance), puis plus rien jusqu'à la prochaine séance ; pendant une pause, ni reprise ni semaine légère notifiées ; une seule fois par événement (clés `phase:<n>:<début du programme>`, `allegee:<début du cycle>`, `retour:<dernière séance>`) ; bilan seulement s'il y a eu une séance dans la semaine ; aucun mot de reproche.
- **Fonctionnement** (choix de Claude) : `notif.js` calcule le plan des 14 prochains jours (heure et texte) et le confie à la coque (`FonteApp.notifPlan`, une ligne d'en-tête `calme`, puis une ligne par notification séparée par des tabulations) après chaque `R()`. La coque le garde (SharedPreferences `notif`), programme la suivante par `setWindow` (fenêtre de 10 minutes), la reprogramme au démarrage, à la mise à jour et au changement d'heure (`BootReceiver`), et revérifie au moment d'envoyer heures calmes, plafond du jour, événement déjà envoyé et retard de plus de 2 h (`NotifRules`). Fin du repos : `setExactAndAllowWhileIdle`, notification seulement si l'appli n'est pas à l'écran, effacée au retour dans l'appli.
- **Données** : réglages dans `localStorage`, clé `muscu-notif` (`version: 1`), **hors de l'export** (ils restent sur le téléphone) ; export et import inchangés. Nouvelles autorisations du manifeste : POST_NOTIFICATIONS, SCHEDULE_EXACT_ALARM, RECEIVE_BOOT_COMPLETED, VIBRATE (aussi utile à la vibration du minuteur de la page, effet non vérifié sur téléphone).
- **Vérifié** : sur l'émulateur Android 16 (21/10/2026) : demande après le questionnaire, refus une puis deux fois, notification d'essai, alarme du rappel à 18:00 (fenêtre de 10 min), fin du repos écran éteint avec et sans « Alarmes et rappels », rappel reçu après un redémarrage sans rouvrir l'appli. Sur téléphone réel (21/10/2026, APK de test) : validé par Georgio sur le Pixel 8 (GrapheneOS) et sur le Honor Magic 7 Pro.
- **Non vérifié** : vrai Android 7 à 12 ; chemin exact des menus de batterie de MagicOS 9 (donné dans les notes comme précaution, d'après des guides d'anciennes versions) ; on ne sait pas si Georgio a dû changer un réglage de batterie sur son Honor.

## 9. À faire ensuite
- Version 0.5.0 (notifications) : préparée ; commit, push, puis release `v0.5.0` créée par Georgio lui-même après le push.
- Questionnaire : ensuite bouton « J'ai mal » et circuit d'endurance.
- Esprits : avis de Georgio sur Gloumi (première passe pixel art), puis les autres espèces du bestiaire v3 une par une, puis intégration dans l'appli (sprites PNG, halo, stade jamais en recul). Puis démonstrations d'exercice (`figure.js`).
- Zones et exercices manquants : avant-bras, trapèzes, obliques, adducteurs (les formes musculaires sont dessinées mais absentes de `ZONES` et `EXZ`).
- Notifications : essai sur un vrai Android 7 (image système à télécharger pour l'émulateur, environ 1 Go, si Georgio le veut).
- Non vérifié sur téléphone réel : changement d'icône du lanceur, fluidité des animations dans la WebView, empreinte de la signature, animations/sons/vibrations du tirage.
- Mettre à jour le wiki (voir section 10), en une seule écriture, après confirmation de Georgio.

---

## 10. Tenir ce fichier et le wiki à jour

- Après toute décision durable (choix technique, règle du jeu, version publiée, incident résolu), mettre à jour **ce fichier** (sections 4, 8, 9 en priorité) dans le même commit que le changement.
- Georgio tient un wiki BookStack (projet Raspberry Pi, hors Fonte) avec une page « Suivi muscu » (id 71) : résumé fonctionnel du projet (dépôt local-first, alias d'icônes, moteur d'animation, jeu des Esprits ; l'avatar humain est abandonné). Si le connecteur BookStack est disponible dans cette session, la mettre à jour **en une seule écriture** (BookStack n'a pas de mise à jour partielle : chaque écriture renvoie la page entière), après sa confirmation. Sinon, préparer le texte et le lui remettre pour qu'il le fasse passer par sa conversation Claude habituelle.
- **Ne pas dupliquer** : la procédure de publication et les règles de code vivent dans ce fichier ; le wiki n'en garde qu'un résumé et y renvoie.
