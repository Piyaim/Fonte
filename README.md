# Fonte

Carnet de musculation **auto-hébergé** : tu notes tes séances sur ton téléphone, les données restent sur **ton** serveur.

*English summary at the bottom.*

Le projet a deux parties :

| Dossier | Contenu |
|---|---|
| `server/` | Le serveur (Flask + SQLite, un seul conteneur Docker). Il sert aussi l'appli web, installable comme PWA. |
| `android/` | Une petite coque Android (une WebView) qui ouvre ton serveur. Aucune bibliothèque tierce, aucun traceur, une seule permission : le réseau. |

## Ce que fait l'appli

- Un catalogue de 50 exercices que tu modifies librement (ajout, changement, archivage), avec schéma animé, consignes d'exécution et erreurs courantes.
- Programmes, séances libres ou parallèles, séances composées par zones musculaires, mode focus.
- Une jauge de difficulté ressentie (1 à 5) qui influence le conseil de charge de la séance suivante.
- Un minuteur de repos dont l'affichage reste juste quand l'écran se verrouille.
- Records (1RM estimé), courbes de progression, poids de corps, photos de progression, import et export JSON.
- Cinq couleurs au choix. L'interface est **en français uniquement** pour l'instant.

## ⚠️ À lire avant d'utiliser

- **Aucune authentification.** Quiconque atteint le serveur voit et modifie tout. Ne le mets jamais sur Internet tel quel : garde-le sur ton réseau local, derrière un VPN, ou derrière un proxy inverse qui demande un mot de passe.
- **Ce n'est ni un coach ni un avis médical.** Les textes d'exécution des exercices, les erreurs courantes, les animations et la règle de conseil de charge ont été rédigés **sans source externe ni relecture par un professionnel**. Certaines animations sont des approximations. En cas de douleur ou de doute, demande l'avis d'un coach ou d'un médecin.
- **Pas d'écriture hors ligne.** L'appli s'ouvre sans réseau avec le dernier état connu, mais rien n'est enregistré tant que le serveur n'est pas joignable.
- **Les photos de progression** sont stockées sur le serveur, sans EXIF ni GPS. L'export JSON ne les contient pas : sauvegarde le volume Docker.
- Projet indépendant, sans lien avec une salle de sport ni une marque.

## Installer le serveur

Il faut Docker avec Docker Compose. Depuis le dossier `server/` :

```bash
docker compose up -d --build
```

L'appli écoute alors sur `http://127.0.0.1:8080`, donc **uniquement sur la machine elle-même**. Pour l'ouvrir sur ton réseau local, modifie la ligne `ports` de `server/docker-compose.yml` en remplaçant `127.0.0.1` par l'adresse IP de la machine (par exemple `"192.168.1.20:8080:8000"`), puis relance la commande ci-dessus.

Les données (base `suivi.db` et dossier `photos/`) vivent dans le volume Docker nommé `fonte_data`.

**HTTPS.** Le service worker et l'installation en PWA exigent HTTPS (sauf sur `localhost`). Mets un proxy inverse devant (Caddy, nginx, Traefik…) avec un certificat valide. La coque Android accepte aussi `http://` pour un serveur sur réseau de confiance, mais pas un certificat auto-signé.

**Sauvegarde du volume**, avec Docker (crée `fonte-data.tar.gz` dans le dossier courant) :

```bash
docker run --rm -v fonte_data:/data -v "$PWD":/b alpine tar czf /b/fonte-data.tar.gz -C /data .
```

## Installer l'appli Android

1. Télécharge le fichier `.apk` de la dernière version dans la page **Releases** du dépôt.
2. Ouvre-le sur le téléphone et autorise l'installation depuis cette source si Android le demande.
3. Au premier lancement, saisis l'adresse de ton serveur (par exemple `https://fonte.exemple.org`). Tu pourras la changer plus tard dans le menu ☰ de l'appli, bouton **Changer le serveur**.

Pour recevoir les mises à jour, tu peux suivre le dépôt avec une appli comme Obtainium. Fonte n'est pas (encore) sur F-Droid.

L'export JSON de l'onglet Données s'ouvre dans le navigateur du téléphone. L'import passe par le sélecteur de fichiers d'Android.

> Sur iPhone, il n'y a pas d'appli : ouvre le serveur dans Safari et utilise « Sur l'écran d'accueil ». Cette piste n'a pas été testée.

## Développer

Lancer le serveur sans Docker, avec Python 3.12 :

```bash
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
DB_PATH=/tmp/fonte.db .venv/bin/python -c "import app; app.init_db(); app.app.run(port=8080)"
```

L'appli web tient dans un seul fichier, `server/static/index.html` (JavaScript sans framework). Le catalogue de départ est `server/seed.py` : il n'est lu qu'une seule fois, à la création de la base.

## Construire l'APK

Le dépôt contient un workflow GitHub Actions (`.github/workflows/build.yml`) qui construit l'APK sur les serveurs de GitHub.

1. **Crée la clé de signature, une seule fois**, sur une machine avec Docker : `sh tools/creer-cle-signature.sh`. Elle crée le dossier `~/fonte-signature`. **Sauvegarde-le ailleurs** : sans cette clé, plus aucune mise à jour ne pourra s'installer par-dessus les anciennes versions.
2. Dans GitHub, **Settings > Secrets and variables > Actions**, crée quatre secrets : `KEYSTORE_BASE64`, `KEYSTORE_PASSWORD`, `KEY_PASSWORD` et `KEY_ALIAS`. Le script affiche quel fichier correspond à chacun.
3. Choisis ton identifiant d'appli dans `android/gradle.properties` (`APP_ID`) **avant la première version publiée**, puis augmente `VERSION_CODE` et `VERSION_NAME` à chaque version.
4. Crée une version : dans GitHub, **Releases > Draft a new release**, avec un nouveau tag `v` suivi du numéro (par exemple `v0.1.0`, identique à `VERSION_NAME`). Le workflow construit l'APK et l'attache à la version.

Sans les secrets, le workflow construit quand même un APK, signé avec la clé de debug : il s'installe, mais une version signée plus tard avec ta vraie clé ne pourra pas le mettre à jour (il faudra le désinstaller d'abord).

Pour construire en local, il faut le SDK Android et un JDK 17, puis `cd android && ./gradlew assembleRelease`.

## Contribuer

Les idées et les corrections sont bienvenues, en particulier : la vérification des textes d'exercices par des personnes compétentes, les traductions, l'écriture hors ligne avec synchronisation, une authentification optionnelle.

## Licence

Fonte est un logiciel libre sous licence **GNU Affero General Public License v3.0 ou ultérieure** (AGPL-3.0-or-later). Le texte complet est dans le fichier `LICENSE`. En clair : tu peux l'utiliser, l'étudier, le modifier et le partager ; si tu proposes une version modifiée à d'autres via un réseau, tu dois leur donner son code source sous la même licence.

---

## English summary

**Fonte** is a self-hosted weight-training log: a small Flask + SQLite server (`server/`, one Docker container) that also serves an installable web app, plus a minimal Android shell (`android/`, a WebView with no third-party libraries, no trackers and a single network permission) that opens your own server. The interface is in French only.

- **No authentication**: keep it on your LAN, behind a VPN or behind an authenticating reverse proxy.
- **Not a coach, not medical advice**: exercise texts, animations and the load-advice rule were written without external sources or professional review.
- No offline writes. Android app: download the `.apk` from Releases, enter your server address on first launch. iPhone: use the web app from Safari (untested).
- Server: `docker compose up -d --build` in `server/` (listens on `127.0.0.1:8080` by default). APK: built by the GitHub Actions workflow with your own signing key (see "Construire l'APK").
- License: AGPL-3.0-or-later.
