#!/bin/sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Crée UNE FOIS la clé qui signe l'APK (nécessite Docker). Les fichiers vont dans ~/fonte-signature.
# SAUVEGARDE ce dossier ailleurs : sans cette clé, tu ne pourras plus publier de mise à jour installable par-dessus les anciennes versions.
set -eu
DIR="$HOME/fonte-signature"
if [ -e "$DIR" ]; then echo "Le dossier $DIR existe déjà : rien n'a été fait."; exit 1; fi
mkdir -p "$DIR"; chmod 700 "$DIR"; cd "$DIR"
PASS=$(head -c 32 /dev/urandom | base64 | tr -d '/+=\n' | cut -c1-28)
docker run --rm --user "$(id -u):$(id -g)" -v "$DIR":/k -w /k eclipse-temurin:17-jdk \
  keytool -genkeypair -keystore fonte.jks -alias fonte -keyalg RSA -keysize 4096 -validity 10000 \
  -storepass "$PASS" -keypass "$PASS" -dname "CN=Fonte"
base64 -w0 fonte.jks > KEYSTORE_BASE64.txt
printf '%s' "$PASS" > MOT_DE_PASSE.txt
printf '%s' fonte > KEY_ALIAS.txt
chmod 600 ./*
echo "Terminé. Fichiers créés dans $DIR :"
ls -1 "$DIR"
echo "Dans GitHub (Settings > Secrets and variables > Actions), crée 4 secrets :"
echo "  KEYSTORE_BASE64 = contenu de KEYSTORE_BASE64.txt"
echo "  KEYSTORE_PASSWORD = contenu de MOT_DE_PASSE.txt"
echo "  KEY_PASSWORD = contenu de MOT_DE_PASSE.txt (la même valeur)"
echo "  KEY_ALIAS = contenu de KEY_ALIAS.txt (fonte)"
