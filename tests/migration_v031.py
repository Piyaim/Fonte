# SPDX-License-Identifier: AGPL-3.0-or-later
# Migration depuis la dernière version publiée (0.3.1, tag Git v0.3.1), sans perte.
# 1. Le code de la 0.3.1 (sorti de Git par le tag, ou pris dans le dossier ANCIEN_DIR s'il est donné) crée de vraies données,
#    en mode serveur (SQLite + fichiers photo) ET en mode local (IndexedDB + localStorage) : exercice ajouté et exercice modifié,
#    programmes modifiés, séances avec séries et ressentis, pesées, photos, état du jeu des Esprits (bienvenue, jetons, tirage).
#    Il fait aussi ses exports, par le lien « Télécharger l'export » de l'écran Données (et celui des photos en mode local).
# 2. Le code actuel rouvre ces mêmes données (même fichier SQLite, même profil de navigateur, même adresse) :
#    tout est identique, photos comprises ; le questionnaire de départ s'affiche, sans rien effacer ;
#    « Garder mes programmes » laisse programmes et exercices intacts ; ensuite le questionnaire ne revient plus.
# 3. Les exports faits en 0.3.1 s'importent dans une appli neuve (code actuel) : mêmes données, jeu et photos compris,
#    et le questionnaire saute.
# 4. Aucune requête ne sort vers un autre domaine que le serveur de test.
#   python3 tests/migration_v031.py          (ANCIEN_DIR=/chemin/vers/v031 pour prendre le code d'un worktree)
import base64, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 5120; TAG = "v0.3.1"
TMP = tempfile.mkdtemp(prefix="fonte-migration-v031-"); PROFIL_NAV = os.path.join(TMP, "navigateur")
DBF = os.path.join(TMP, "data", "suivi.db"); DBF_NEUF = os.path.join(TMP, "neuf", "suivi.db")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

# ------------------------------------------------------------ code de la 0.3.1
if os.environ.get("ANCIEN_DIR"): OLD = os.environ["ANCIEN_DIR"]
else:
    OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
    subprocess.run(f"git -C '{ROOT}' archive {TAG} server | tar -x -C '{OLD}'", shell=True, check=True)
VIEUX = open(os.path.join(OLD, "server", "static", "index.html"), encoding="utf-8").read()
ok("profil.js" not in VIEUX and "settings" not in open(os.path.join(OLD, "server", "app.py"), encoding="utf-8").read(),
   f"(le code de départ est bien celui de la 0.3.1 : ni questionnaire ni réglages par séance) {OLD}")

PROCS = []
def serveur(dossier, dbf):
    env = dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.Popen([sys.executable, "-c", f"import app;app.app.run(port={PORT})"], cwd=dossier, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    PROCS.append(p); time.sleep(3)
    if p.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {PORT} déjà pris ?)")
    return p
def arreter(p): p.terminate(); p.wait()

from PIL import Image
def jpeg(size, seed):
    b = io.BytesIO(); Image.effect_noise((size, size), 40 + seed).convert("RGB").save(b, "JPEG", quality=80); return base64.b64encode(b.getvalue()).decode()
IMG, THUMB = jpeg(320, 1), jpeg(96, 2)

# scénario joué par la page de la 0.3.1, en mode serveur puis en mode local (mêmes appels que l'interface)
REMPLIR = """async ([img, thumb]) => {
  const st = await api('GET', '/api/state'), ids = Object.keys(EX).map(Number), [a, b, c, d] = ids;
  const e0 = EX[c]; await api('PUT', '/api/exercises/' + c, Object.assign({}, e0, {sets: 5, target_min: 4, target_max: 6, rest: 150, tip: 'mon conseil'}));
  const ex = await api('POST', '/api/exercises', {name: 'Tirage perso', grp: 'Dos', kind: 'weight', sets: 4, target_min: 6, target_max: 8, rest: 120});
  const w = await api('POST', '/api/workouts', {name: 'Mon programme'});
  await api('PUT', '/api/workouts/' + w.id, {name: 'Mon programme', items: [a, ex.id, c]});
  await api('PUT', '/api/workouts/' + st.workouts[0].id, {name: st.workouts[0].name + ' modifiée', items: [...st.workouts[0].items].reverse()});
  await api('POST', '/api/sessions', {day: '2026-10-01', workout_id: st.workouts[0].id, notes: 'première', entries: [{exercise_id: a, sets: [[40, 10], [42.5, 8]], effort: 3}, {exercise_id: b, sets: [[null, 12]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-03', workout_id: w.id, entries: [{exercise_id: ex.id, sets: [[30, 8], [30, 7], [30, 6], [27.5, 8]], effort: 4}]});
  await api('POST', '/api/sessions', {day: '2026-10-05', workout_id: st.workouts[1].id, entries: [{exercise_id: d, sets: [[20, 12]], effort: 2}]});
  await api('DELETE', '/api/workouts/' + st.workouts[1].id);
  await api('POST', '/api/exercises/' + b + '/archive', {archived: true});
  await api('POST', '/api/bodyweight', {kg: 81.5, day: '2026-10-01'}); await api('POST', '/api/bodyweight', {kg: 80.9, day: '2026-10-05'});
  const bl = s => new Blob([Uint8Array.from(atob(s), ch => ch.charCodeAt(0))], {type: 'image/jpeg'});
  for (const [day, note] of [['2026-10-01', 'de face'], ['2026-10-05', 'de profil']]) {
    const fd = new FormData(); fd.append('img', bl(img), 'a.jpg'); fd.append('thumb', bl(thumb), 't.jpg'); fd.append('day', day); fd.append('note', note);
    const r = await fetch('/api/photos', {method: 'POST', body: fd}); if (!r.ok) throw new Error('photo ' + r.status);
  }
  await load(); go('jeu');                                      // ouverture de l'onglet Esprits : cadeau de bienvenue (3 jetons, Gloumi)
  const s = await api('POST', '/api/sessions', {day: '2026-10-08', workout_id: w.id, entries: [{exercise_id: ex.id, sets: [[30, 8], [30, 8], [30, 8], [30, 8]], effort: 4}]});
  await load(); const rep = JEU.award(s.id); JEU._.pull(1); JEU._.pull(1); go('jeu');   // séance gagnée en jetons, puis deux tirages
  return rep;
}"""
# tout ce qui doit survivre (les photos sont comparées octet par octet, pleine taille et vignette)
RELEVE = """async () => {
  const j = async u => (await fetch(u)).json(), st = await j('/api/state'), ex = await j('/api/export'), ph = await j('/api/photos');
  delete ex.exported_at;
  const octets = [];
  for (const p of ph) for (const k of ['full', 'thumb']) { const b = new Uint8Array(await (await fetch(photoUrl(p.id, k))).arrayBuffer()); let h = 0; for (const x of b) h = (h * 31 + x) >>> 0; octets.push([p.day, p.note, k, b.length, h]); }
  return {state: st, export: ex, photos: ph, octets, jeu: localStorage.getItem('muscu-jeu')};
}"""
BRUT_IDB = """() => new Promise((res, rej) => { const r = indexedDB.open('fonte', 1); r.onerror = () => rej(r.error);
  r.onsuccess = () => { const t = r.result.transaction('kv', 'readonly').objectStore('kv').get('db'); t.onsuccess = () => { res(t.result); r.result.close(); }; t.onerror = () => rej(t.error); }; })"""
PROGS = "fetch('/api/state').then(r => r.json()).then(s => ({workouts: s.workouts, exercises: s.exercises, sessions: s.sessions}))"
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REPONSES = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
            "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
QUESTIONNAIRE = lambda t: "Bienvenue dans Fonte" in t

def sans_settings(x):
    if isinstance(x, dict): return {k: sans_settings(v) for k, v in x.items() if k != "settings"}
    if isinstance(x, list): return [sans_settings(v) for v in x]
    return x
def sqlite_brut(dbf):
    c = sqlite3.connect(dbf); c.row_factory = sqlite3.Row
    out = {t: [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in ("exercise", "workout", "workout_item", "session", "entry", "effort", "bodyweight", "photo")}
    c.close(); return out
def fichiers_photo(dbf):
    d = os.path.join(os.path.dirname(dbf), "photos")
    return {os.path.relpath(os.path.join(r, f), d): open(os.path.join(r, f), "rb").read() for r, _, fs in os.walk(d) for f in fs} if os.path.isdir(d) else {}
# deux adresses, donc deux origines : chaque mode a son propre localStorage (jeu, profil), comme sur un vrai appareil
MODES = {"serveur": f"http://127.0.0.1:{PORT}/", "local": f"http://localhost:{PORT}/?local=1"}
HOTES = (f"http://127.0.0.1:{PORT}/", f"http://localhost:{PORT}/")

from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        externes = []
        def surveiller(ctx):      # toute requête http(s) qui ne va pas vers le serveur de test est notée et bloquée
            ctx.route("**/*", lambda r: r.continue_() if not r.request.url.startswith("http") or r.request.url.startswith(HOTES) else (externes.append(r.request.url), r.abort()))
        def navigateur():
            ctx = p.chromium.launch_persistent_context(PROFIL_NAV, viewport={"width": 390, "height": 844}, service_workers="block", accept_downloads=True)
            ctx.on("dialog", lambda d: d.accept()); surveiller(ctx); return ctx
        def ouvrir(ctx, mode, errs, sel=".tabbar button, #app .card"):
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(f"{mode}: {e}"))
            pg.goto(MODES[mode]); pg.wait_for_selector(sel, timeout=10000); time.sleep(.5); return pg
        def telecharger(pg, lien):
            pg.evaluate("go('donnees')"); time.sleep(.3)
            with pg.expect_download() as dl: pg.click(f"a:has-text(\"{lien}\")")
            return json.loads(open(dl.value.path(), encoding="utf-8").read())

        # ============================================================ 1. données créées par la 0.3.1
        srv = serveur(os.path.join(OLD, "server"), DBF); ctx = navigateur(); errs = []
        avant, exports, rep = {}, {}, {}
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs)
            rep[mode] = pg.evaluate(REMPLIR, [IMG, THUMB]); time.sleep(.5)
            avant[mode] = pg.evaluate(RELEVE)
            exports[mode] = telecharger(pg, "Télécharger l'export")
            if mode == "local": exports["photos"] = telecharger(pg, "Télécharger les photos")
            pg.close()
        idb0 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        ctx.close(); arreter(srv)
        sql0, ph0 = sqlite_brut(DBF), fichiers_photo(DBF)
        for mode, a in avant.items():
            s, j = a["state"], json.loads(a["jeu"] or "null")
            ok(len(s["sessions"]) == 4 and len(s["bodyweight"]) == 2 and len(a["photos"]) == 2 and any(w["name"] == "Mon programme" for w in s["workouts"])
               and any(e["tip"] == "mon conseil" and e["sets"] == 5 for e in s["exercises"]) and any(e["archived"] for e in s["exercises"]),
               f"0.3.1, mode {mode} : 4 séances, 2 pesées, 2 photos, programme ajouté, exercice modifié, exercice archivé")
            ok(j and j["init"] and "gloumi" in j["owned"] and j["pulls"] == 2 and rep[mode] and rep[mode]["tokens"] >= 2,
               f"0.3.1, mode {mode} : jeu des Esprits joué (bienvenue, {rep[mode] and rep[mode]['tokens']} jetons gagnés, 2 tirages)")
            ok(all("settings" not in w for w in s["workouts"]), f"(témoin, mode {mode} : la 0.3.1 ne connaît pas les réglages par séance)")
        ok(exports["local"].get("jeu") == json.loads(avant["local"]["jeu"]) and len(exports["photos"]["photos"]) == 2 and len(ph0) == 4,
           "0.3.1 : export local avec l'état du jeu, export des 2 photos, 4 fichiers photo côté serveur")

        # ============================================================ 2. mêmes données ouvertes par le code actuel
        srv = serveur(os.path.join(ROOT, "server"), DBF); ctx = navigateur(); errs = []
        apres = {}
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs); t = pg.inner_text("#app")
            ok(QUESTIONNAIRE(t) and not pg.locator(".tabbar").is_visible(), f"mode {mode} : le questionnaire de départ s'affiche à la première ouverture")
            apres[mode] = pg.evaluate(RELEVE); pg.close()
        idb1 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        for mode in MODES:
            a, b = avant[mode], apres[mode]
            ok(sans_settings(b["state"]) == a["state"], f"mode {mode} : état identique (exercices, programmes, séances, ressentis, pesées)")
            ok(all(w["settings"] == {} for w in b["state"]["workouts"]), f"mode {mode} : réglages par séance vides")
            ok(sans_settings(b["export"]) == a["export"], f"mode {mode} : export identique (hors réglages vides)")
            ok(b["photos"] == a["photos"] and b["octets"] == a["octets"] and len(b["octets"]) == 4, f"mode {mode} : 2 photos et 2 vignettes identiques octet par octet")
            ok(b["jeu"] == a["jeu"], f"mode {mode} : état du jeu des Esprits identique")
        sql1 = sqlite_brut(DBF)
        ok({t: [{k: r[k] for k in r if k in sql0[t][0]} for r in v] for t, v in sql1.items() if v} == {t: v for t, v in sql0.items() if v}
           and all(len(sql1[t]) == len(sql0[t]) for t in sql0), "SQLite : toutes les lignes de toutes les tables inchangées")
        ok(fichiers_photo(DBF) == ph0, "fichiers photo du serveur inchangés (4 fichiers, octet par octet)")
        ok({k: v for k, v in idb1.items() if k != "workout_item"} == {k: v for k, v in idb0.items() if k != "workout_item"}
           and [{k: r[k] for k in ("workout_id", "exercise_id", "position")} for r in idb1["workout_item"]] == idb0["workout_item"],
           "IndexedDB : toutes les tables inchangées (programmes compris, réglages vides ajoutés)")

        # « Garder mes programmes », dans chaque mode
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs)
            pg.evaluate("a => { localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false})); }", REPONSES)
            pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); x0 = pg.evaluate(PROGS)
            pg.click("button:has-text('Générer mon programme')"); time.sleep(.4)
            ok("Garder mes programmes" in pg.inner_text("#app"), f"mode {mode} : la confirmation propose « Garder mes programmes »")
            pg.click("button:has-text('Garder mes programmes')"); time.sleep(.6)
            x1 = pg.evaluate(PROGS); pr = pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil'))")
            ok(x1 == x0 and sans_settings(x1["workouts"]) == avant[mode]["state"]["workouts"], f"mode {mode} : « Garder mes programmes » laisse programmes, exercices et séances intacts")
            ok(pr and pr["program"] is None and pr["answers"]["prenom"] == "Léa", f"mode {mode} : profil enregistré, sans programme généré")
            pg.reload(); pg.wait_for_selector(".tabbar button"); time.sleep(.4)
            ok(not QUESTIONNAIRE(pg.inner_text("#app")) and pg.locator(".tabbar").is_visible(), f"mode {mode} : le questionnaire ne revient plus")
            b = pg.evaluate(RELEVE)
            ok(sans_settings(b["state"]) == avant[mode]["state"] and b["octets"] == avant[mode]["octets"] and b["jeu"] == avant[mode]["jeu"], f"mode {mode} : après le questionnaire, toutes les données sont toujours là")
            pg.close()
        ok(not errs, f"aucune erreur JavaScript (données de la 0.3.1 rouvertes) {errs[:2]}")
        ctx.close(); arreter(srv)

        # ============================================================ 3. exports de la 0.3.1 importés dans une appli neuve
        os.makedirs(os.path.dirname(DBF_NEUF)); srv = serveur(os.path.join(ROOT, "server"), DBF_NEUF)
        subprocess.run([sys.executable, "-c", "import app;app.init_db()"], cwd=os.path.join(ROOT, "server"), env=dict(os.environ, DB_PATH=DBF_NEUF, PYTHONDONTWRITEBYTECODE="1"), check=True)
        b = p.chromium.launch(); errs = []
        for mode in MODES:
            ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); ctx.on("dialog", lambda d: d.accept()); surveiller(ctx)
            pg = ouvrir(ctx, mode, errs, "#app .card")
            ok(QUESTIONNAIRE(pg.inner_text("#app")), f"appli neuve, mode {mode} : questionnaire de départ")
            pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3)
            pg.fill("#bk", json.dumps(exports[mode])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
            if mode == "local":
                pg.evaluate("go('donnees')"); time.sleep(.3); pg.fill("#bk", json.dumps(exports["photos"])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
            pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.6)
            ok(not QUESTIONNAIRE(pg.inner_text("#app")) and pg.locator(".tabbar").is_visible(), f"import de l'export 0.3.1, mode {mode} : le questionnaire saute (accueil rouvert)")
            pr = pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil'))")
            ok(pr and pr.get("imported") is True and pr["program"] is None, f"mode {mode} : profil « importé, questionnaire non rempli »")
            n = pg.evaluate(RELEVE); a = avant[mode]
            ok({k: sans_settings(v) for k, v in n["export"].items() if k not in ("jeu", "profil")} == {k: v for k, v in exports[mode].items() if k not in ("exported_at", "jeu")},
               f"mode {mode} : export de la 0.3.1 importé à l'identique (exercices, programmes, séances, pesées)")
            ok(sans_settings(n["state"]["workouts"]) == a["state"]["workouts"] and n["state"]["sessions"] == a["state"]["sessions"], f"mode {mode} : programmes et historique identiques à ceux de la 0.3.1")
            if mode == "local":
                ok(json.loads(n["jeu"]) == json.loads(a["jeu"]), "mode local : état du jeu des Esprits restauré")
                ok([o[:4] for o in n["octets"]] == [o[:4] for o in a["octets"]] and [o[4] for o in n["octets"]] == [o[4] for o in a["octets"]], "mode local : 2 photos et vignettes restaurées octet par octet")
            ctx.close()
        ok(not errs, f"aucune erreur JavaScript (imports) {errs[:2]}")
        b.close(); arreter(srv)
        ok(not externes, f"aucune requête vers un autre domaine pendant tout le test {externes[:3]}")
finally:
    for pr in PROCS: pr.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
