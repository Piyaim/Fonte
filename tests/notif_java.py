# SPDX-License-Identifier: AGPL-3.0-or-later
# Règles de la coque Android pour les notifications (NotifRules.java : heures calmes, plafond d'une par jour, une seule fois par
# événement, rien de périmé), compilées et lancées sur le PC dans le conteneur JDK qui construit l'APK (podman, sans Android).
import os, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.environ.get("NOTIF_RULES", "android/app/src/main/java/app/fonte/NotifRules.java")   # témoins : une copie faussée
cmd = ["podman", "run", "--rm", "--security-opt", "label=disable", "-v", f"{ROOT}:/src:ro", "-w", "/tmp", "docker.io/library/eclipse-temurin:17-jdk", "sh", "-c",
       f"mkdir -p out && javac -encoding UTF-8 -d out /src/{src} /src/tests/notif_java/NotifRulesTest.java && java -cp out app.fonte.NotifRulesTest"]
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout + r.stderr)
if r.returncode and "ÉCHEC" not in r.stdout: print("ÉCHEC  compilation ou lancement")
sys.exit(r.returncode)
