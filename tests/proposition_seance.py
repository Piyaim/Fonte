# SPDX-License-Identifier: AGPL-3.0-or-later
# Séance proposée par l'accueil avec un programme généré (bug signalé sur l'APK de test de la 0.6.0 : « Haut du corps » proposée
# deux jours de suite). Règle : la séance qui suit la dernière faite du programme, sur les jours choisis, jamais une séance « manquée ».
# Modes local et serveur, séance enregistrée par l'interface en mode « un exercice à la fois » puis depuis l'Aperçu :
#   questionnaire (4 séances lun, mar, jeu, ven → « Haut du corps » et « Bas du corps », anciens programmes remplacés)
#   mercredi (jour libre) : Haut faite → Bas le jour même et jeudi ; jeudi : Bas faite → Haut vendredi (prévu Bas au calendrier) ;
#   vendredi : Haut faite → Bas lundi (prévu Haut) ; mercredi suivant, après lundi et mardi sans séance : toujours Bas, puis Haut.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/proposition_seance.py
import os, re, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5171
DB = "/tmp/proposition_seance.db"
srv = None
def serveur():
    global srv
    for f in (DB, DB + "-wal", DB + "-shm"):
        if os.path.exists(f): os.remove(f)
    srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                           env=dict(os.environ, DB_PATH=DB, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
       "passe": ["aucun"], "seances": 4, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [],
       "jours": ["lun", "mar", "jeu", "ven"], "detail": "non"}
MANQUE = re.compile(r"manqué", re.I)

try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for mode in ("local", "serveur"):
            for facon in ("un exercice à la fois", "Aperçu"):
                serveur()
                M = f"{mode} · {facon}"
                ctx = b.new_context(viewport={"width": 390, "height": 844}); pg = ctx.new_page(); errs = []
                pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
                def jour(j):
                    pg.clock.set_fixed_time(j + "T10:00:00"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000); time.sleep(.3)
                pg.clock.set_fixed_time("2026-11-04T10:00:00")   # un mercredi, jour libre
                pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if mode == "local" else "")); pg.wait_for_selector("#app .card", timeout=8000); time.sleep(.3)
                anciens = pg.evaluate("WO.map(w => w.id)")
                # questionnaire rempli, puis « Générer mon programme » et « Remplacer mes programmes »
                pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REP)
                pg.reload(); pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
                pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
                wo = pg.evaluate("WO.map(w => [w.id, w.name])"); ids = {n: i for i, n in wo}
                ok([n for _, n in wo] == ["Haut du corps", "Bas du corps"] and anciens and not set(anciens) & set(ids.values()),
                   f"{M} · programme de 2 séances, anciens programmes remplacés ({anciens} → {wo})")
                def accueil():
                    pg.evaluate("go('accueil')"); time.sleep(.2)
                    return pg.inner_text("#app .hero h2"), pg.inner_text("#app .hero .sub >> nth=0")
                def faire():   # « Démarrer la séance » de l'accueil, séries saisies, enregistrement par l'interface
                    nom = accueil()[0]
                    pg.click("#app .hero button:has-text('Démarrer la séance')"); time.sleep(.3)
                    if facon == "Aperçu":
                        pg.click(".focus button:has-text('Aperçu')"); time.sleep(.3)
                        for i in pg.locator("#app input[inputmode=decimal]").all(): i.fill("10")
                        pg.click("#app button:has-text('Enregistrer la séance')")
                    else:
                        while True:
                            for i in pg.locator(".focus input[inputmode=decimal]").all(): i.fill("10")
                            if pg.locator(".focus button:has-text('Suivant ›')").count(): pg.click(".focus button:has-text('Suivant ›')"); time.sleep(.2)
                            else: pg.click(".focus button:has-text('Terminer et enregistrer')"); break
                    time.sleep(1); pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
                    st = pg.evaluate("fetch('/api/state').then(r => r.json())")["sessions"][-1]
                    ok(st["workout_id"] == ids[nom] and st["workout_name"] == nom and len(st["entries"]) >= 4,
                       f"{M} · séance « {nom} » enregistrée avec l'identifiant de son programme ({st['workout_id']}, {st['workout_name']!r})")
                def attendu(nom, sous, quand):
                    h = accueil(); ok(h == (nom, sous), f"{M} · {quand} : l'accueil propose « {nom} » ({h[0]} · {h[1]})")
                attendu("Haut du corps", "6 exercices · prévue demain", "mercredi, rien de fait")
                faire()
                attendu("Bas du corps", "6 exercices · prévue demain", "mercredi, Haut faite")
                jour("2026-11-05"); attendu("Bas du corps", "6 exercices · prévue aujourd’hui", "jeudi, lendemain de Haut")
                faire()
                attendu("Haut du corps", "6 exercices · prévue demain", "jeudi, Bas faite")
                jour("2026-11-06"); attendu("Haut du corps", "6 exercices · prévue aujourd’hui", "vendredi, lendemain de Bas")
                faire()
                jour("2026-11-09"); attendu("Bas du corps", "6 exercices · prévue aujourd’hui", "lundi, 2 jours après Haut")
                jour("2026-11-11"); attendu("Bas du corps", "6 exercices · prévue demain", "mercredi, 4 jours sans séance (lundi et mardi passés)")
                pg.evaluate("document.querySelectorAll('#app details').forEach(d => d.open = true)")
                ok(not MANQUE.search(pg.inner_text("body")), f"{M} · « manquée » absent de l'accueil après plusieurs jours sans séance")
                faire()
                attendu("Haut du corps", "6 exercices · prévue demain", "mercredi, Bas faite après la pause")
                ok(not errs, f"{M} · aucune erreur JavaScript {errs[:2]}")
                ctx.close(); srv.terminate(); srv.wait()
        b.close()
finally:
    if srv: srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tous les contrôles sont passés."))
sys.exit(1 if fails else 0)
