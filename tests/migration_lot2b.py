# SPDX-License-Identifier: AGPL-3.0-or-later
# Migration vers le lot 2B (phases, semaine allégée, reprise, placement), sans perte. Même méthode que tests/migration.py :
# 1. Le code du commit 64e77a8 (lot 2A, sorti de Git) crée de vraies données : en mode local (IndexedDB + localStorage),
#    questionnaire rempli et programme GÉNÉRÉ par l'interface, séances, réglage modifié, pesée, jeu ; en mode serveur (SQLite),
#    programmes, séances et pesée.
# 2. Le code actuel rouvre ces mêmes données (même fichier SQLite, même profil de navigateur, même adresse).
# 3. Tout doit être identique ; le profil gagne seulement les champs du programme suivi (ids, start, phase_start, history),
#    retrouvés par le nom des programmes générés ; phases et placement fonctionnent.
# 4. Dans l'autre sens : un export du code actuel s'importe dans le code de 64e77a8 (profil accepté, données identiques).
#   python3 tests/migration_lot2b.py
import json, os, shutil, sqlite3, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 5119; ANCIEN = "64e77a8"
TMP = tempfile.mkdtemp(prefix="fonte-migration-2b-"); DBF = os.path.join(TMP, "data", "suivi.db"); PROFIL_NAV = os.path.join(TMP, "navigateur")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
subprocess.run(f"git -C '{ROOT}' archive {ANCIEN} server | tar -x -C '{OLD}'", shell=True, check=True)
ok("ITEM_FIELDS" in open(os.path.join(OLD, "server", "app.py"), encoding="utf-8").read() and "PRM3" not in open(os.path.join(OLD, "server", "static", "profil.js"), encoding="utf-8").read(),
   f"(le code extrait est bien celui du lot 2A, avant le lot 2B : {ANCIEN})")

PROCS = []
def serveur(dossier, dbf=DBF):
    env = dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.Popen([sys.executable, "-c", f"import app;app.app.run(port={PORT})"], cwd=dossier, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    PROCS.append(p); time.sleep(3)
    if p.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {PORT} déjà pris ?)")
    return p
def arreter(p): p.terminate(); p.wait()

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REPONSES = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
            "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
# mode local : programme généré par l'interface du lot 2A, puis données d'usage
GENERER = "a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))"
REMPLIR = """async () => {
  const [a, b] = WO, x = a.items[0], y = b.items[1];
  await api('PUT', '/api/workouts/' + a.id, {name: a.name, items: a.items, settings: Object.assign({}, a.settings, {[x]: {sets: 5, target_min: 3, target_max: 5, rest: 180}})});
  await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: a.id, notes: 'première', entries: [{exercise_id: x, sets: [[40, 10], [42.5, 8]], effort: 3}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_id: b.id, entries: [{exercise_id: y, sets: [[20, 12], [20, 11]], effort: 2}]});
  await api('POST', '/api/sessions', {day: '2026-10-16', entries: [{exercise_id: x, sets: [[45, 6]], effort: 5}]});
  await api('POST', '/api/bodyweight', {kg: 66.4, day: '2026-10-12'});
  await load(); go('jeu');
}"""
RELEVE = """async () => { const j = async u => (await fetch(u)).json(), st = await j('/api/state'), ex = await j('/api/export'); delete ex.exported_at;
  return {state: st, export: ex, profil: JSON.parse(localStorage.getItem('muscu-profil') || 'null'), jeu: localStorage.getItem('muscu-jeu')}; }"""
MODES = {"local": "/?local=1", "serveur": "/"}
NOUVEAUX = {"ids", "start", "phase_start", "history"}

from playwright.sync_api import sync_playwright
import sans_duree   # séances relues sans start_ts ni end_ts (ajoutés vides par le code actuel), vérifiés à la fin
sans_duree.brancher(globals())
try:
    with sync_playwright() as p:
        def navigateur(dossier=PROFIL_NAV):
            ctx = p.chromium.launch_persistent_context(dossier, viewport={"width": 390, "height": 844}, service_workers="block")
            ctx.on("dialog", lambda d: d.accept()); return ctx
        def ouvrir(ctx, mode, errs, attendre=".tabbar button"):
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(f"{mode}: {e}"))
            pg.goto(f"http://127.0.0.1:{PORT}{MODES[mode]}"); pg.wait_for_selector(attendre, timeout=10000); time.sleep(.5); return pg

        # ------------------------------------------------------------ 1. données créées par le code du lot 2A
        srv = serveur(os.path.join(OLD, "server")); ctx = navigateur(); errs = []
        pg = ouvrir(ctx, "local", errs, "#app button:has-text('Commencer')"); pg.evaluate(GENERER, REPONSES); pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')")
        pg.click("button:has-text('Générer mon programme')"); time.sleep(.3); pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
        jour = pg.evaluate("today()"); pg.evaluate(REMPLIR); time.sleep(.5); pg.close()
        pg = ouvrir(ctx, "serveur", errs)
        pg.evaluate("""async () => { const [a] = WO; await api('POST', '/api/sessions', {day: '2026-10-13', workout_id: a.id, entries: [{exercise_id: a.items[0], sets: [[30, 10]], effort: 3}]});
          await api('POST', '/api/bodyweight', {kg: 70, day: '2026-10-13'}); await load(); }"""); pg.close()
        avant = {m: (lambda pg: (pg.evaluate(RELEVE), pg.close())[0])(ouvrir(ctx, m, errs)) for m in MODES}
        ctx.close(); arreter(srv)
        a = avant["local"]
        ok(a["profil"]["program"] and set(a["profil"]["program"]) == {"generated", "phase", "level", "structure", "workouts"}, f"(lot 2A : programme généré, sans les champs du lot 2B : {sorted(a['profil']['program'])})")
        ok([w["name"] for w in a["state"]["workouts"]] == ["Séance A", "Séance B"] and len(a["state"]["sessions"]) == 3 and a["jeu"], "lot 2A, mode local : Séance A et B, 3 séances, état du jeu")
        ok(len(avant["serveur"]["state"]["sessions"]) == 1, "lot 2A, mode serveur : 1 séance")

        # ------------------------------------------------------------ 2. mêmes données ouvertes par le code actuel
        srv = serveur(os.path.join(ROOT, "server")); ctx = navigateur(); errs = []
        apres = {m: (lambda pg: (pg.evaluate(RELEVE), pg.close())[0])(ouvrir(ctx, m, errs)) for m in MODES}
        b = apres["local"]
        for m in MODES:
            ok(apres[m]["state"] == avant[m]["state"], f"mode {m} : état identique (exercices, programmes et réglages, séances, ressentis, pesées)")
            ea, eb = dict(avant[m]["export"]), dict(apres[m]["export"]); ea.pop("profil", None); eb.pop("profil", None)
            ok(ea == eb, f"mode {m} : export identique (hors profil)")
            ok(apres[m]["jeu"] == avant[m]["jeu"], f"mode {m} : état du jeu intact")
        pa, pb = a["profil"], b["profil"]
        ok({k: v for k, v in pb.items() if k != "program"} == {k: v for k, v in pa.items() if k != "program"}, "profil : réponses, dates et réglages intacts")
        ok({k: v for k, v in pb["program"].items() if k not in NOUVEAUX} == pa["program"], "profil : champs du programme du lot 2A intacts")
        ids = [w["id"] for w in b["state"]["workouts"]]
        ok(pb["program"]["ids"] == ids and pb["program"]["start"] == jour == pb["program"]["phase_start"] and pb["program"]["history"] == [{"phase": 1, "start": jour}],
           f"profil : programmes générés retrouvés par leur nom {pb['program']['ids']}, début le {pb['program']['start']}")
        ok(b["export"]["profil"] == pb, "l'export contient le profil complété")
        pg = ouvrir(ctx, "local", errs)
        ok(pg.evaluate("PROFIL.coach().phase") == 1 and pg.evaluate("PROFIL.schedule() !== null"), "phases et placement actifs sur les données migrées")
        pg.evaluate("go('profil')"); time.sleep(.3); t = pg.inner_text("#app")
        ok("Phase 1" in t and "Cette semaine" in t, "« Mon profil » : phase et semaine de séances affichées")
        pg.evaluate("go('accueil')"); time.sleep(.2)
        ok(pg.evaluate("document.querySelector('#app').firstElementChild.classList.contains('hero') && document.querySelector('#app button').textContent.trim()") == "Démarrer la séance",
           "accueil : « Démarrer la séance » en tête")
        nouvel_export = pg.evaluate("fetch('/api/export').then(r => r.json())"); pg.close()
        ctx.close(); arreter(srv)
        srv = serveur(os.path.join(ROOT, "server")); ctx = navigateur()
        pg = ouvrir(ctx, "local", errs); ok(pg.evaluate(RELEVE)["profil"] == pb and len(pg.evaluate("SESS")) == 3, "deuxième ouverture (migration déjà faite) : rien ne bouge"); pg.close()
        ctx.close(); arreter(srv)

        # ------------------------------------------------------------ 2 bis. export du lot 2A (profil sans les champs du lot 2B) importé dans le code actuel
        srv = serveur(os.path.join(ROOT, "server"), os.path.join(TMP, "data3", "suivi.db")); ctx = navigateur(os.path.join(TMP, "navigateur3"))
        pg = ouvrir(ctx, "local", errs, "#app button:has-text('Commencer')"); pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3)
        pg.fill("#bk", json.dumps(a["export"])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1500)
        ok(pg.evaluate("PROFIL.coach().phase") == 1 and pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil')).program.ids").__len__() == 2,
           "export du lot 2A importé dans le code actuel : programmes suivis retrouvés tout de suite, phase 1 active")
        ctx.close(); arreter(srv)

        # ------------------------------------------------------------ 3. export du code actuel -> code du lot 2A (navigateur et base neufs)
        srv = serveur(os.path.join(OLD, "server"), os.path.join(TMP, "data2", "suivi.db")); ctx = navigateur(os.path.join(TMP, "navigateur2")); errs2 = []
        pg = ouvrir(ctx, "local", errs2, "#app button:has-text('Commencer')")
        ok("Bienvenue dans Fonte" in pg.inner_text("#app"), "(code du lot 2A, appareil neuf : questionnaire affiché)")
        pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3); pg.fill("#bk", json.dumps(nouvel_export)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1500)
        pg.reload(); pg.wait_for_selector(".tabbar button", timeout=8000); time.sleep(.4)
        r = pg.evaluate(RELEVE)
        ok(r["profil"] == pb and "Bienvenue" not in pg.inner_text("#app"), "code du lot 2A : le nouvel export s'importe, profil accepté tel quel, pas de questionnaire")
        ok([(w["name"], w["items"], w["settings"]) for w in r["state"]["workouts"]] == [(w["name"], w["items"], w["settings"]) for w in b["state"]["workouts"]] and r["state"]["sessions"] == b["state"]["sessions"],
           "code du lot 2A : programmes, réglages et séances identiques")
        ok(not errs2, f"aucune erreur JavaScript dans le code du lot 2A {errs2[:2]}")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        ctx.close(); arreter(srv)
finally:
    for pr in PROCS: pr.kill()
    shutil.rmtree(TMP, ignore_errors=True)
sans_duree.bilan(ok)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
