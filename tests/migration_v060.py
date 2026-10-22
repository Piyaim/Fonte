# SPDX-License-Identifier: AGPL-3.0-or-later
# Migration depuis la dernière version publiée (0.6.0, tag Git v0.6.0) vers la 0.6.1 (correctif : séance proposée par l'accueil), sans perte.
# 1. Le code de la 0.6.0 (sorti de Git par le tag, ou pris dans le dossier ANCIEN_DIR) crée de vraies données, en mode serveur
#    (SQLite + fichiers photo) ET en mode local (IndexedDB + localStorage) : questionnaire rempli et programme généré (réglages
#    par séance), exercice ajouté et modifié, programme ajouté, séances, pesées, photos, jeu des Esprits ; puis ses exports.
# 2. Le code actuel rouvre ces données (même SQLite, même profil de navigateur, mêmes adresses) : tout est identique (photos
#    octet par octet, profil, jeu), le questionnaire ne revient pas ; la page Notifications s'affiche ; avec une coque Android
#    simulée, le plan des notifications se calcule sur ces données ; l'export reste identique (les réglages des notifications
#    n'y entrent pas).
# 3. Les exports de la 0.6.0 s'importent dans une appli neuve (code actuel) : mêmes données, profil et jeu compris.
# 4. Un export fait par le code actuel s'importe dans la 0.6.0 : mêmes données.
# 5. Aucune requête ne sort vers un autre domaine que le serveur de test.
#   python3 tests/migration_v060.py          (ANCIEN_DIR=/chemin/vers/v060 pour prendre le code d'un worktree)
import base64, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 5123; TAG = "v0.6.0"
TMP = tempfile.mkdtemp(prefix="fonte-migration-v060-"); PROFIL_NAV = os.path.join(TMP, "navigateur")
DBF = os.path.join(TMP, "data", "suivi.db"); DBF_NEUF = os.path.join(TMP, "neuf", "suivi.db"); DBF_RETOUR = os.path.join(TMP, "retour", "suivi.db")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

# ------------------------------------------------------------ code de la 0.6.0
if os.environ.get("ANCIEN_DIR"): OLD = os.environ["ANCIEN_DIR"]
else:
    OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
    subprocess.run(f"git -C '{ROOT}' archive {TAG} server | tar -x -C '{OLD}'", shell=True, check=True)
VIEUX = open(os.path.join(OLD, "server", "static", "index.html"), encoding="utf-8").read()
VIEUX_PROFIL = open(os.path.join(OLD, "server", "static", "profil.js"), encoding="utf-8").read()
ok("const inFocus" in VIEUX and "function kgStep" in VIEUX and "rien n’est compté comme non fait" not in VIEUX_PROFIL,
   f"(le code de départ est bien celui de la 0.6.0 : mode « un exercice à la fois » et pas du matériel, mais pas le correctif de la séance proposée) {OLD}")

PROCS = []
def serveur(dossier, dbf):
    os.makedirs(os.path.dirname(dbf), exist_ok=True)
    subprocess.run([sys.executable, "-c", "import app;app.init_db()"], cwd=dossier, env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), check=True)
    p = subprocess.Popen([sys.executable, "-c", f"import app;app.app.run(port={PORT})"], cwd=dossier, env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    PROCS.append(p); time.sleep(3)
    if p.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {PORT} déjà pris ?)")
    return p
def arreter(p): p.terminate(); p.wait()

from PIL import Image
def jpeg(size, seed):
    b = io.BytesIO(); Image.effect_noise((size, size), 40 + seed).convert("RGB").save(b, "JPEG", quality=80); return base64.b64encode(b.getvalue()).decode()
IMG, THUMB = jpeg(320, 1), jpeg(96, 2)

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REPONSES = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
            "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
# scénario joué par la page de la 0.6.0 après le questionnaire (mêmes appels que l'interface)
REMPLIR = """async ([img, thumb]) => {
  const st = await api('GET', '/api/state'), w0 = st.workouts[0], [a, b] = w0.items, c = st.workouts[1].items[0];
  const e0 = EX[c]; await api('PUT', '/api/exercises/' + c, Object.assign({}, e0, {tip: 'mon conseil'}));
  const ex = await api('POST', '/api/exercises', {name: 'Tirage perso', grp: 'Dos', kind: 'weight', sets: 4, target_min: 6, target_max: 8, rest: 120});
  const w = await api('POST', '/api/workouts', {name: 'Mon programme'});
  await api('PUT', '/api/workouts/' + w.id, {name: 'Mon programme', items: [a, ex.id], settings: {[ex.id]: {sets: 5, target_min: 3, target_max: 5, rest: 180}}});
  await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: w0.id, notes: 'première', entries: [{exercise_id: a, sets: [[40, 10], [42.5, 8]], effort: 3}, {exercise_id: b, sets: [[20, 12]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_id: w.id, entries: [{exercise_id: ex.id, sets: [[30, 5], [30, 5], [30, 4], [27.5, 5], [27.5, 5]], effort: 4}]});
  await api('POST', '/api/exercises/' + b + '/archive', {archived: true});
  await api('POST', '/api/bodyweight', {kg: 66.5, day: '2026-10-12'}); await api('POST', '/api/bodyweight', {kg: 66.1, day: '2026-10-14'});
  const bl = s => new Blob([Uint8Array.from(atob(s), ch => ch.charCodeAt(0))], {type: 'image/jpeg'});
  for (const [day, note] of [['2026-10-12', 'de face'], ['2026-10-14', 'de profil']]) {
    const fd = new FormData(); fd.append('img', bl(img), 'a.jpg'); fd.append('thumb', bl(thumb), 't.jpg'); fd.append('day', day); fd.append('note', note);
    const r = await fetch('/api/photos', {method: 'POST', body: fd}); if (!r.ok) throw new Error('photo ' + r.status);
  }
  await load(); go('jeu');
  const s = await api('POST', '/api/sessions', {day: '2026-10-16', workout_id: w.id, entries: [{exercise_id: ex.id, sets: [[30, 5], [30, 5], [30, 5], [30, 5], [30, 5]], effort: 4}]});
  await load(); const rep = JEU.award(s.id); JEU._.pull(1); go('jeu');
  return rep;
}"""
RELEVE = """async () => {
  const j = async u => (await fetch(u)).json(), st = await j('/api/state'), ex = await j('/api/export'), ph = await j('/api/photos');
  delete ex.exported_at;
  const octets = [];
  for (const p of ph) for (const k of ['full', 'thumb']) { const b = new Uint8Array(await (await fetch(photoUrl(p.id, k))).arrayBuffer()); let h = 0; for (const x of b) h = (h * 31 + x) >>> 0; octets.push([p.day, p.note, k, b.length, h]); }
  return {state: st, export: ex, photos: ph, octets, jeu: localStorage.getItem('muscu-jeu'), profil: localStorage.getItem('muscu-profil')};
}"""
BRUT_IDB = """() => new Promise((res, rej) => { const r = indexedDB.open('fonte', 1); r.onerror = () => rej(r.error);
  r.onsuccess = () => { const t = r.result.transaction('kv', 'readonly').objectStore('kv').get('db'); t.onsuccess = () => { res(t.result); r.result.close(); }; t.onerror = () => rej(t.error); }; })"""
COQUE = """window.__N = {calls: []};
window.FonteApp = {notifStatus: () => JSON.stringify({sdk: 34, perm: 'granted', exact: false, exactNeeded: true, channels: true, sent: []}),
  notifAskOnce: () => __N.calls.push(['ask']), notifRequest: () => {}, notifPlan: t => __N.calls.push(['plan', t]), notifTest: () => {},
  restStart: () => false, restCancel: () => {}, openChannel: () => {}, exactRequest: () => {}, saveFile: (n, m, t) => __N.calls.push(['save', n, t]), setIcon: () => {}};"""
QUESTIONNAIRE = lambda t: "Bienvenue dans Fonte" in t or "Questionnaire" in t

def sqlite_brut(dbf):
    c = sqlite3.connect(dbf); c.row_factory = sqlite3.Row
    out = {t: [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in ("exercise", "workout", "workout_item", "session", "entry", "effort", "bodyweight", "photo")}
    c.close(); return out
def fichiers_photo(dbf):
    d = os.path.join(os.path.dirname(dbf), "photos")
    return {os.path.relpath(os.path.join(r, f), d): open(os.path.join(r, f), "rb").read() for r, _, fs in os.walk(d) for f in fs} if os.path.isdir(d) else {}
MODES = {"serveur": f"http://127.0.0.1:{PORT}/", "local": f"http://localhost:{PORT}/?local=1"}
HOTES = (f"http://127.0.0.1:{PORT}/", f"http://localhost:{PORT}/")
sans_date = lambda e: {k: v for k, v in e.items() if k != "exported_at"}

from playwright.sync_api import sync_playwright
import sans_duree   # séances relues sans start_ts ni end_ts (ajoutés vides par le code actuel), vérifiés à la fin
sans_duree.brancher(globals())
try:
    with sync_playwright() as p:
        externes = []
        def surveiller(ctx):
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
        def importer(pg, data):
            pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3)
            pg.fill("#bk", json.dumps(data)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)

        # ============================================================ 1. données créées par la 0.6.0
        srv = serveur(os.path.join(OLD, "server"), DBF); ctx = navigateur(); errs = []
        avant, exports, rep = {}, {}, {}
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs, "#app .card")
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REPONSES)
            pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); pg.click("button:has-text('Générer mon programme')"); time.sleep(.4)
            pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            rep[mode] = pg.evaluate(REMPLIR, [IMG, THUMB]); time.sleep(.5)
            avant[mode] = pg.evaluate(RELEVE)
            exports[mode] = telecharger(pg, "Télécharger l'export")
            if mode == "local": exports["photos"] = telecharger(pg, "Télécharger les photos")
            pg.close()
        idb0 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        ctx.close(); arreter(srv)
        sql0, ph0 = sqlite_brut(DBF), fichiers_photo(DBF)
        for mode, a in avant.items():
            s, j, pr = a["state"], json.loads(a["jeu"] or "null"), json.loads(a["profil"] or "null")
            ok(len(s["sessions"]) == 3 and len(s["bodyweight"]) == 2 and len(a["photos"]) == 2 and any(w["name"] == "Mon programme" and w["settings"] for w in s["workouts"])
               and any(e["archived"] for e in s["exercises"]), f"0.6.0, mode {mode} : 3 séances, 2 pesées, 2 photos, programme réglé, exercice archivé")
            ok(pr and pr["program"] and len(pr["program"]["ids"]) >= 2 and pr["answers"]["prenom"] == "Léa", f"0.6.0, mode {mode} : questionnaire rempli, programme généré")
            ok(j and j["init"] and j["pulls"] == 1, f"0.6.0, mode {mode} : jeu des Esprits joué")
        ok(exports["local"].get("jeu") and exports["local"].get("profil") and len(exports["photos"]["photos"]) == 2 and len(ph0) == 4,
           "0.6.0 : export local avec jeu et profil, export des 2 photos, 4 fichiers photo côté serveur")
        ok(not errs, f"(0.6.0 sans erreur JavaScript) {errs[:2]}")

        # ============================================================ 2. mêmes données ouvertes par le code actuel
        srv = serveur(os.path.join(ROOT, "server"), DBF); ctx = navigateur(); errs = []
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs); t = pg.inner_text("#app")
            ok(not QUESTIONNAIRE(t) and pg.locator(".tabbar").is_visible() and "Démarrer la séance" in t, f"mode {mode} : accueil, le questionnaire ne revient pas")
            b = pg.evaluate(RELEVE); a = avant[mode]
            ok(b["state"] == a["state"], f"mode {mode} : état identique (exercices, programmes et réglages, séances, ressentis, pesées)")
            ok(b["export"] == a["export"], f"mode {mode} : export identique (les réglages des notifications n'y entrent pas)")
            ok(b["photos"] == a["photos"] and b["octets"] == a["octets"] and len(b["octets"]) == 4, f"mode {mode} : 2 photos et 2 vignettes identiques octet par octet")
            ok(b["jeu"] == a["jeu"] and b["profil"] == a["profil"], f"mode {mode} : jeu des Esprits et profil identiques")
            pg.evaluate("go('notifications')"); time.sleep(.3)
            ok("Disponibles seulement dans l’appli Android." in pg.inner_text("#app"), f"mode {mode} : page Notifications (navigateur : explication)")
            ok(pg.evaluate("localStorage.getItem('muscu-notif')") is None, f"mode {mode} : rien n'est écrit pour les notifications hors de l'appli Android")
            pg.close()
        # coque Android simulée, mêmes données (mode local) : plan calculé, export inchangé
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(f"coque: {e}")); pg.add_init_script(COQUE)
        pg.clock.set_fixed_time("2026-10-19T10:00:00")   # un lundi, 3 jours après la dernière séance
        pg.goto(MODES["local"]); pg.wait_for_selector(".tabbar button", timeout=10000); time.sleep(1)
        plans = [c[1] for c in pg.evaluate("__N.calls") if c[0] == "plan"]
        lignes = plans[-1].split("\n") if plans else []
        ok(lignes[:1] == ["calme\t21:00\t08:00"] and len(lignes) >= 2 and all(len(l.split("\t")) == 5 for l in lignes[1:]), f"coque simulée : plan calculé sur les données de la 0.6.0 ({len(lignes) - 1} notification(s))")
        ok(any("\trappel:2026-10-19\t" in l for l in lignes), "coque simulée : rappel du lundi (jour du questionnaire) prévu")
        ok(pg.evaluate("[...JSON.parse(localStorage.getItem('muscu-notif')).rappel.days]") == [0, 2, 4], "réglages par défaut : jours du questionnaire (lundi, mercredi, vendredi)")
        b = pg.evaluate(RELEVE)
        ok(b["export"] == avant["local"]["export"] and b["profil"] == avant["local"]["profil"] and b["jeu"] == avant["local"]["jeu"], "coque simulée : export, profil et jeu inchangés")
        pg.evaluate("go('donnees')"); time.sleep(.3); pg.click("a:has-text(\"Télécharger l'export\")"); time.sleep(1)
        sv = [c for c in pg.evaluate("__N.calls") if c[0] == "save"]
        nouvel_export = sans_date(json.loads(sv[-1][2])) if sv else {}
        ok(bool(sv), "coque simulée : export confié à la coque (enregistrement du fichier)")
        ok("muscu-notif" not in json.dumps(nouvel_export) and "notif" not in nouvel_export, "nouvel export : sans réglages de notifications")
        pg.close()
        idb1 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        ok(idb1 == idb0, "IndexedDB : toutes les tables inchangées")
        ok(sqlite_brut(DBF) == sql0 and fichiers_photo(DBF) == ph0, "SQLite et fichiers photo du serveur inchangés")
        ok(not errs, f"aucune erreur JavaScript (données de la 0.6.0 rouvertes) {errs[:2]}")
        ctx.close(); arreter(srv)

        # ============================================================ 3. exports de la 0.6.0 importés dans une appli neuve
        srv = serveur(os.path.join(ROOT, "server"), DBF_NEUF)
        br = p.chromium.launch(); errs = []
        for mode in MODES:
            ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); ctx.on("dialog", lambda d: d.accept()); surveiller(ctx)
            pg = ouvrir(ctx, mode, errs, "#app .card")
            importer(pg, exports[mode])
            if mode == "local":
                pg.evaluate("go('donnees')"); time.sleep(.3); pg.fill("#bk", json.dumps(exports["photos"])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
            pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.6)
            ok(not QUESTIONNAIRE(pg.inner_text("#app")), f"import de l'export 0.6.0, mode {mode} : le questionnaire saute")
            n = pg.evaluate(RELEVE)
            ok({k: v for k, v in n["export"].items() if k not in ("jeu", "profil")} == {k: v for k, v in exports[mode].items() if k not in ("exported_at", "jeu", "profil")},
               f"mode {mode} : export de la 0.6.0 importé à l'identique (exercices, programmes et réglages, séances, pesées)")
            if mode == "local":
                ok(json.loads(n["jeu"]) == json.loads(avant["local"]["jeu"]) and json.loads(n["profil"]) == json.loads(avant["local"]["profil"]), "mode local : jeu et profil restaurés")
                ok([o[4] for o in n["octets"]] == [o[4] for o in avant["local"]["octets"]], "mode local : photos restaurées octet par octet")
            ctx.close()
        arreter(srv)

        # ============================================================ 4. export du code actuel importé dans la 0.6.0
        srv = serveur(os.path.join(OLD, "server"), DBF_RETOUR)
        ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); ctx.on("dialog", lambda d: d.accept()); surveiller(ctx)
        pg = ouvrir(ctx, "local", errs, "#app .card"); importer(pg, nouvel_export)
        pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.6)
        n = pg.evaluate(RELEVE)
        ok({k: v for k, v in n["export"].items() if k not in ("photos",)} == {k: v for k, v in nouvel_export.items() if k not in ("photos",)},
           "export 0.6.1 importé dans la 0.6.0 : mêmes données, jeu et profil compris")
        ctx.close(); br.close(); arreter(srv)
        ok(not errs, f"aucune erreur JavaScript (imports) {errs[:2]}")
        ok(not externes, f"aucune requête vers un autre domaine pendant tout le test {externes[:3]}")
finally:
    for pr in PROCS: pr.kill()
    shutil.rmtree(TMP, ignore_errors=True)
sans_duree.bilan(ok)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
