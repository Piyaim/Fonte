# SPDX-License-Identifier: AGPL-3.0-or-later
# Un import réussi fait sauter le questionnaire de départ.
# - Ancien export sans « profil » (0.3.1, serveur) : profil « importé, questionnaire non rempli », programmes gardés tels quels.
# - Export avec « profil » : ce profil est restauré.
# - Import en échec ou annulé : rien ne change, le questionnaire est toujours là.
# - Brouillon du questionnaire effacé après un import réussi.
# Chaque cas est joué depuis l'écran « Bienvenue » (bouton « J'ai une sauvegarde ») et depuis l'écran Données.
#   python3 tests/import_profil.py
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5117
env = dict(os.environ, DB_PATH="/tmp/import_profil.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/import_profil.db", "/tmp/import_profil.db-wal", "/tmp/import_profil.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REPONSES = {"prenom": "Témoin", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
            "passe": ["aucun"], "seances": 2, "duree": 45, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["mar", "jeu"], "detail": "non"}
PROFIL = {"version": 1, "created": "2026-09-01T08:00:00Z", "updated": "2026-09-01T08:00:00Z", "answers": REPONSES, "bmi": 22.8, "program": None}
PROGS = "fetch('/api/state').then(r => r.json()).then(s => s.workouts.map(w => ({id: w.id, name: w.name, items: w.items, settings: w.settings})))"
QUESTIONNAIRE = lambda t: "Bienvenue dans Fonte" in t or "Question " in t

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        def page(local=True, dismiss=False):
            ctx = b.new_context(viewport={"width": 390, "height": 844})
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.on("dialog", lambda d: d.dismiss() if dismiss and d.type == "confirm" else d.accept())
            pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if local else "")); pg.wait_for_selector("#app .card", timeout=8000); time.sleep(.4)
            return ctx, pg, errs

        # ------------------------------------------------------------ deux sauvegardes, faites à partir de l'état de départ
        ctx, pg, errs = page()
        base = pg.evaluate("fetch('/api/export').then(r => r.json())"); ctx.close()
        ancien = json.loads(json.dumps(base)); ancien.pop("profil", None); ancien.pop("jeu", None)
        for i, w in enumerate(ancien["workouts"]):      # programmes personnels, différents de ceux d'une appli neuve
            w["name"] = f"Mon programme {i + 1}"; w["items"] = list(reversed(w["items"]))[:4]
            w.pop("settings", None)                     # export d'avant le lot 2A (0.3.1) : pas de « settings »
        ancien["sessions"] = [{"id": 1, "day": "2026-09-15", "ts": 1757930000000, "workout_id": ancien["workouts"][0]["id"], "workout_name": "Mon programme 1", "notes": "",
                               "entries": [{"exercise_id": ancien["workouts"][0]["items"][0], "sets": [[40, 10], [40, 9]], "effort": 3}]}]
        attendu = [{"id": w["id"], "name": w["name"], "items": w["items"], "settings": {}} for w in ancien["workouts"]]
        avec = json.loads(json.dumps(ancien)); avec["profil"] = PROFIL

        def commencer(pg):     # questionnaire commencé (brouillon avec un prénom), puis retour à l'écran Bienvenue
            pg.click("button:has-text('Commencer')"); time.sleep(.2); pg.fill("#qin", "Brouillon"); pg.click("button:has-text('Suivant')"); time.sleep(.2)
            pg.click("button:has-text('Retour')"); time.sleep(.2); pg.click("button:has-text('Retour')"); time.sleep(.2)
        def ouvrir_import(pg, entree):
            if entree == "Bienvenue": pg.click("button:has-text('J’ai une sauvegarde')")
            else: pg.evaluate("go('donnees')")
            time.sleep(.3)
        def importer(pg, texte):
            pg.fill("#bk", texte); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1500)   # wait_for_timeout laisse passer la boîte « Import terminé » (time.sleep la bloque)
        def recharger(pg):
            pg.reload(); pg.wait_for_selector("#app .card", timeout=8000); time.sleep(.4); return pg.inner_text("#app")
        prof = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil') || 'null')")
        brouillon = lambda pg: pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil-brouillon') || 'null')")

        for local in (True, False):
            for entree in (("Bienvenue", "Données") if local else ("Bienvenue",)):
                M = f"[{entree}, mode {'local' if local else 'serveur'}]"
                # -------------------------------------------- A. ancien export sans profil
                ctx, pg, errs = page(local)
                commencer(pg)
                ok(QUESTIONNAIRE(recharger(pg)) and brouillon(pg)["answers"]["prenom"] == "Brouillon" and prof(pg) is None,
                   f"{M} témoin : avant l'import, le questionnaire s'impose au rechargement, brouillon présent")
                ok(pg.evaluate(PROGS) != attendu, f"{M} témoin : les programmes de départ diffèrent de ceux de la sauvegarde")
                ouvrir_import(pg, entree); importer(pg, json.dumps(ancien))
                t0 = pg.inner_text("#app"); ok("Démarrer la séance" in t0 and pg.locator(".tabbar").is_visible(), f"{M} ancien export : accueil affiché juste après l'import ({t0[:80]!r})")
                t = recharger(pg)
                ok(not QUESTIONNAIRE(t) and pg.locator(".tabbar").is_visible(), f"{M} ancien export : après rechargement, pas de questionnaire")
                ok(pg.evaluate(PROGS) == attendu, f"{M} ancien export : programmes identiques à ceux de la sauvegarde")
                pr = prof(pg)
                ok(pr and pr.get("imported") is True and pr["answers"] == {} and pr["program"] is None, f"{M} profil « importé, questionnaire non rempli »")
                ok(brouillon(pg) is None, f"{M} brouillon du questionnaire effacé")
                pg.evaluate("go('profil')"); time.sleep(.3); t = pg.inner_text("#app")
                ok("Remplir le questionnaire" in t and "IMC" not in t, f"{M} « Mon profil » propose « Remplir le questionnaire »")
                if local and entree == "Bienvenue":
                    pg.click("button:has-text('Remplir le questionnaire')"); time.sleep(.3)
                    ok("Question 1 sur 17" in pg.inner_text("#app") and pg.input_value("#qin") == "", "« Remplir le questionnaire » : question 1, réponses vides")
                    pg.click("button:has-text('Quitter')"); time.sleep(.3)
                    ok("Reprendre le questionnaire" in pg.inner_text("#app") and not QUESTIONNAIRE(recharger(pg)), "quitter : questionnaire à reprendre dans « Mon profil », jamais imposé")
                    ok(pg.evaluate(PROGS) == attendu, "questionnaire ouvert puis quitté : programmes inchangés")
                ok(not errs, f"{M} aucune erreur JavaScript (A) {errs[:2]}"); ctx.close()

                # -------------------------------------------- B. export avec profil
                ctx, pg, errs = page(local)
                commencer(pg); ok(prof(pg) is None, f"{M} témoin : pas de profil avant l'import")
                ouvrir_import(pg, entree); importer(pg, json.dumps(avec)); t = recharger(pg)
                ok(prof(pg) == PROFIL and not QUESTIONNAIRE(t), f"{M} export avec profil : profil restauré à l'identique, pas de questionnaire")
                ok(brouillon(pg) is None and pg.evaluate(PROGS) == attendu, f"{M} export avec profil : brouillon effacé, programmes de la sauvegarde")
                ok(not errs, f"{M} aucune erreur JavaScript (B) {errs[:2]}"); ctx.close()

                # -------------------------------------------- C. import en échec, puis annulé
                for nom, texte, annule in (("fichier invalide", "ceci n'est pas une sauvegarde", False), ("format inconnu", json.dumps({"bonjour": 1}), False),
                                           ("export abîmé", json.dumps(dict(ancien, exercises=[{"id": 1}])), False), ("import annulé", json.dumps(ancien), True)):
                    ctx, pg, errs = page(local, dismiss=annule)
                    commencer(pg); progs0 = pg.evaluate(PROGS)
                    ouvrir_import(pg, entree); importer(pg, texte); t = recharger(pg)
                    ok(QUESTIONNAIRE(t) and prof(pg) is None and brouillon(pg)["answers"]["prenom"] == "Brouillon" and pg.evaluate(PROGS) == progs0,
                       f"{M} {nom} : questionnaire toujours là, brouillon et programmes inchangés")
                    ok(not errs, f"{M} aucune erreur JavaScript ({nom}) {errs[:2]}"); ctx.close()

        # ------------------------------------------------------------ témoin : sans la correction, le contrôle échoue bien
        ctx, pg, errs = page()
        pg.evaluate("PROFIL.afterImport = () => {}")    # comportement d'avant la correction
        commencer(pg); ouvrir_import(pg, "Bienvenue"); importer(pg, json.dumps(ancien))
        ok(QUESTIONNAIRE(recharger(pg)), "témoin : sans la correction, le questionnaire revient après l'import d'un ancien export (le bug est bien détecté)")
        ctx.close()

        # ------------------------------------------------------------ profil déjà rempli : un ancien export le garde, un export avec profil le remplace
        ctx, pg, errs = page()
        mien = dict(PROFIL, answers=dict(REPONSES, prenom="Déjà rempli"))
        pg.evaluate("p => localStorage.setItem('muscu-profil', JSON.stringify(p))", mien)
        pg.evaluate("localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: {prenom: 'En cours'}, mode: 'q', i: 1, redo: true}))")
        recharger(pg); pg.evaluate("go('donnees')"); time.sleep(.3); importer(pg, json.dumps(ancien))
        ok(prof(pg) == mien and brouillon(pg) is None, "profil déjà rempli + ancien export : profil gardé, questionnaire en cours effacé")
        pg.evaluate("go('donnees')"); time.sleep(.3); importer(pg, json.dumps(avec))
        ok(prof(pg) == PROFIL, "profil déjà rempli + export avec profil : profil de l'export")
        ok(not errs, f"aucune erreur JavaScript (profil déjà rempli) {errs[:2]}"); ctx.close()
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
