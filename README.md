# Fonte

Carnet de musculation qui **fonctionne seul sur ton téléphone** : pas de serveur, pas de compte, pas de réseau. Tes séances restent dans l'appli, sur ton appareil.

*English summary at the bottom.*

Il y a deux façons de l'utiliser, avec la même interface :

| | Contenu | Pour qui |
|---|---|---|
| **Appli Android autonome** (`android/`) | Une coque qui embarque l'appli web et stocke tout sur le téléphone. | Tout le monde. C'est la voie simple. |
| **Version serveur** (`server/`) | Le même carnet hébergé par toi (Flask + SQLite, un conteneur Docker), utilisable depuis plusieurs appareils et installable comme PWA. | Ceux qui veulent un seul carnet partagé entre plusieurs appareils et savent héberger un service. |

## Ce que fait l'appli

- Un catalogue de 50 exercices que tu modifies librement (ajout, changement, archivage), avec schéma animé, consignes d'exécution et erreurs courantes.
- Un questionnaire de départ (objectif, niveau, temps, jours, douleurs) qui propose un programme adapté, ou te laisse garder tes programmes. Le programme avance par phases, avec semaine légère et reprise en douceur proposées, jamais imposées ; l'accueil montre la séance du jour selon tes jours.
- Programmes, séances libres ou parallèles, séances composées par zones musculaires, mode focus. Un même exercice peut avoir des séries, répétitions et repos différents d'un programme à l'autre.
- Une jauge de difficulté ressentie (1 à 5) qui influence le conseil de charge de la séance suivante (une ligne par exercice, d'après ta dernière séance du même programme).
- Un minuteur de repos dont l'affichage reste juste quand l'écran se verrouille.
- Records (1RM estimé), courbes de progression, poids de corps, photos de progression, import et export.
- Des animations de personnage (homme ou femme, au choix dans le menu ☰) montrent chaque mouvement, avec les muscles travaillés qui s'allument. Les 50 exercices du catalogue de départ ont leur animation (musculation, gainage, cardio).
- Un mini-jeu facultatif, les « Esprits de fonte » : les séances rapportent des jetons selon l'effort réel (plafonnés par jour), pour tirer des créatures qui évoluent avec les séries faites sur leur zone du corps, et des objets qui changent l'apparence du personnage. Sans argent, sans série à perdre, taux affichés. Code : `server/static/jeu.js` (règles) et `creatures.js` (dessin), tests dans `tests/jeu.py`. L'état est stocké localement ; en mode serveur il reste sur l'appareil.
- Six couleurs au choix (dont noir et blanc), qui changent aussi l'icône de l'écran d'accueil dans l'appli Android (selon ton lanceur, ça peut prendre quelques secondes). L'interface est **en français uniquement** pour l'instant.

## ⚠️ À lire avant d'utiliser

- **Ce n'est ni un coach ni un avis médical.** Les textes d'exécution des exercices, les erreurs courantes, les animations, la règle de conseil de charge, le questionnaire et les programmes générés (contre-indications comprises) ont été rédigés **sans source externe ni relecture par un professionnel**. Certaines animations sont des approximations. En cas de douleur ou de doute, demande l'avis d'un coach ou d'un médecin.
- **Tes données ne sont que sur ton téléphone.** Si tu désinstalles l'appli ou effaces ses données, tout disparaît. **Exporte régulièrement** (Données > Télécharger l'export, puis Télécharger les photos) et garde les fichiers ailleurs. Il n'y a pas de synchronisation entre appareils dans la version autonome.
- **Les photos de progression** sont dans un fichier d'export séparé de celui des séances.
- L'appli demande la permission « réseau » par précaution technique (la WebView d'Android l'attend), mais elle **bloque elle-même toute requête vers l'extérieur** : rien ne quitte le téléphone.
- Projet indépendant, sans lien avec une salle de sport ni une marque.
- La version serveur n'a **aucune authentification** : voir plus bas.

## Installer l'appli Android

1. Télécharge le fichier `.apk` de la dernière version dans la page **Releases** du dépôt.
2. Ouvre-le sur le téléphone et autorise l'installation depuis cette source si Android le demande.
3. Lance Fonte : c'est tout. Pour recevoir les mises à jour, tu peux suivre le dépôt avec une appli comme Obtainium. Fonte n'est pas (encore) sur F-Droid.

**Sauvegarder et restaurer.** Onglet **Données** de l'appli : « Télécharger l'export (JSON) » et « Télécharger les photos (JSON) » ouvrent le sélecteur de fichiers d'Android pour choisir où ranger le fichier. Pour restaurer (ou changer de téléphone), ouvre ces fichiers dans la zone **Importer** du même onglet : l'export des séances remplace toute la base, l'export des photos ajoute les photos. Les exports d'une version serveur de Fonte et ceux de l'ancienne appli HTML sont aussi acceptés.

> L'appli autorise la sauvegarde automatique d'Android (`allowBackup`), ce qui permet en principe de la transférer avec le téléphone. Ce n'est pas vérifié : ne compte que sur tes exports.

> Sur iPhone, il n'y a pas d'appli. Ouvre une version serveur dans Safari et utilise « Sur l'écran d'accueil » : cette piste n'a pas été testée.

## Version serveur (facultative)

Il faut Docker avec Docker Compose. Depuis le dossier `server/` :

```bash
docker compose up -d --build
```

L'appli écoute alors sur `http://127.0.0.1:8080`, donc **uniquement sur la machine elle-même**. Pour l'ouvrir sur ton réseau local, modifie la ligne `ports` de `server/docker-compose.yml` en remplaçant `127.0.0.1` par l'adresse IP de la machine (par exemple `"192.168.1.20:8080:8000"`), puis relance la commande ci-dessus. Les données vivent dans le volume Docker nommé `fonte_data`.

- **Aucune authentification.** Quiconque atteint le serveur voit et modifie tout. Garde-le sur ton réseau local, derrière un VPN, ou derrière un proxy inverse qui demande un mot de passe.
- **HTTPS.** Le service worker et l'installation en PWA exigent HTTPS (sauf sur `localhost`) : mets un proxy inverse devant (Caddy, nginx, Traefik…) avec un certificat valide.
- **Pas d'écriture hors ligne** : l'appli s'ouvre sans réseau avec le dernier état connu, mais rien n'est enregistré tant que le serveur n'est pas joignable.
- **Sauvegarde du volume**, avec Docker (crée `fonte-data.tar.gz` dans le dossier courant) :

```bash
docker run --rm -v fonte_data:/data -v "$PWD":/b alpine tar czf /b/fonte-data.tar.gz -C /data .
```

Tu peux aussi essayer le mode sans serveur dans un navigateur : ajoute `?local=1` à l'adresse du serveur. Les données sont alors dans le navigateur, pas sur le serveur.

## Développer

Comment ça marche : l'appli web (`server/static/index.html`, JavaScript sans framework) parle à une API `/api/...`. Sur le serveur, c'est `server/app.py` (Flask + SQLite). Dans l'appli Android, c'est `server/static/local-backend.js`, qui reproduit cette API dans le navigateur avec IndexedDB. La coque Android embarque simplement le dossier `server/static` et le sert à une WebView.

**Si tu changes l'API, change les deux** (`app.py` et `local-backend.js`) puis lance les tests. Le catalogue de départ est `server/seed.py` ; après l'avoir modifié, régénère `server/static/seed.json` avec `python3 tools/export-seed.py`.

Tests (Python 3.12) :

```bash
pip install flask playwright pillow
playwright install chromium
python3 tests/differentiel.py       # même scénario sur Flask et sur le serveur local : les réponses doivent être identiques
python3 tests/ui_local.py           # parcours dans l'interface en mode local (photo, export, import)
python3 tests/simulation_android.py # imite la coque : page servie sous l'adresse interne de la WebView
python3 tests/figures.py            # animations de personnage : valeurs valides, mains sur la barre, pieds au sol
python3 tests/icone_app.py          # le choix d'une couleur appelle bien le changement d'icône de la coque
python3 tests/profil.py             # questionnaire de départ et programme généré (aussi : lot2b.py, lot2c.py, reglages_seance.py, import_profil.py)
python3 tests/migration_v031.py     # données créées par la dernière version publiée (0.3.1), rouvertes sans perte
```

Lancer le serveur sans Docker :

```bash
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DB_PATH=/tmp/fonte.db .venv/bin/python -c "import app; app.init_db(); app.app.run(port=8080)"
```

## Construire l'APK

Le dépôt contient un workflow GitHub Actions (`.github/workflows/build.yml`) qui construit l'APK sur les serveurs de GitHub.

1. **Crée la clé de signature, une seule fois**, sur une machine avec Docker : `sh tools/creer-cle-signature.sh`. Elle crée le dossier `~/fonte-signature`. **Sauvegarde-le ailleurs** : sans cette clé, plus aucune mise à jour ne pourra s'installer par-dessus les anciennes versions.
2. Dans GitHub, **Settings > Secrets and variables > Actions**, crée quatre secrets : `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_PASSWORD` et `KEY_ALIAS`. Le script affiche quel fichier correspond à chacun.
3. Choisis ton identifiant d'appli dans `android/gradle.properties` (`APP_ID`) **avant la première version publiée**, puis augmente `VERSION_CODE` et `VERSION_NAME` à chaque version.
4. Crée une version : dans GitHub, **Releases > Draft a new release**, avec un nouveau tag `v` suivi du numéro (par exemple `v0.1.0`, identique à `VERSION_NAME`). Le workflow construit l'APK et l'attache à la version.

Sans les secrets, le workflow construit quand même un APK, signé avec la clé de debug : il s'installe, mais une version signée plus tard avec ta vraie clé ne pourra pas le mettre à jour (il faudra le désinstaller d'abord, donc exporter tes données avant).

Pour construire en local, il faut le SDK Android et un JDK 17, puis `cd android && ./gradlew assembleRelease`.

## Contribuer

Les idées et les corrections sont bienvenues, en particulier : la vérification des textes d'exercices par des personnes compétentes, les traductions, la synchronisation entre appareils, l'export des photos dans un format plus léger.

## Licence

Fonte est un logiciel libre sous licence **GNU Affero General Public License v3.0 ou ultérieure** (AGPL-3.0-or-later). Le texte complet est dans le fichier `LICENSE`. En clair : tu peux l'utiliser, l'étudier, le modifier et le partager ; si tu proposes une version modifiée à d'autres, y compris via un réseau, tu dois leur donner son code source sous la même licence.

---

## English summary

**Fonte** is a weight-training log that **runs entirely on your phone**: no server, no account, no network. The Android app (`android/`) bundles the web app and stores everything on the device (IndexedDB). An optional self-hosted server version (`server/`, Flask + SQLite, Docker) is also provided for multi-device use. The interface is in French only.

- **Not a coach, not medical advice**: exercise texts, animations and the load-advice rule were written without external sources or professional review.
- **Your data lives only on the phone**: uninstalling the app or clearing its data erases it. Export regularly (Données tab; sessions and photos are separate files). No sync between devices in the standalone version.
- The app declares the network permission as a technical precaution but blocks every request to the outside.
- The server version has **no authentication**: keep it on your LAN, behind a VPN or an authenticating reverse proxy.
- APK: built by the GitHub Actions workflow with your own signing key (see "Construire l'APK"). License: AGPL-3.0-or-later.
