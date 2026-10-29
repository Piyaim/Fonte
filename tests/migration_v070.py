# SPDX-License-Identifier: AGPL-3.0-or-later
# Migration depuis la dernière version publiée (0.7.0, tag Git v0.7.0) vers le code actuel (plafond des jetons quêtes comprises,
# jetons de quête en attente : champ « pend » de l'état du jeu), sans perte.
# 1. Le code de la 0.7.0 (sorti de Git par le tag, ou pris dans le dossier ANCIEN_DIR) crée de vraies données, en mode serveur
#    (SQLite + fichiers photo) ET en mode local (IndexedDB + localStorage) : questionnaire rempli et programme généré, exercice
#    ajouté et modifié, programme ajouté, séances, pesées, photos, jeu des Esprits (jetons crédités, tirage) ; puis ses exports.
# 2. Le code actuel rouvre ces données : tout est identique (état, export, IndexedDB, SQLite, photos octet par octet, profil,
#    jeu : solde ni recalculé ni retiré, rien en attente), le questionnaire ne revient pas ; plan des notifications calculé.
# 3. Les exports de la 0.7.0 (jeu sans « pend ») s'importent dans une appli neuve (code actuel) : mêmes données, profil et jeu.
# 4. Un export du code actuel, avec 2 jetons de quête en attente, s'importe dans la 0.7.0 sans erreur : mêmes données.
# 5. Aucune requête ne sort vers un autre domaine que le serveur de test.
#   python3 tests/migration_v070.py          (ANCIEN_DIR=/chemin/vers/v070 pour prendre le code d'un worktree)
import base64, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 5125; TAG = "v0.7.0"
TMP = tempfile.mkdtemp(prefix="fonte-migration-v070-"); PROFIL_NAV = os.path.join(TMP, "navigateur")
DBF = os.path.join(TMP, "data", "suivi.db"); DBF_NEUF = os.path.join(TMP, "neuf", "suivi.db"); DBF_RETOUR = os.path.join(TMP, "retour", "suivi.db")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

# ------------------------------------------------------------ code de la 0.7.0
if os.environ.get("ANCIEN_DIR"): OLD = os.environ["ANCIEN_DIR"]
else:
    OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
    subprocess.run(f"git -C '{ROOT}' archive {TAG} server | tar -x -C '{OLD}'", shell=True, check=True)
VIEUX = open(os.path.join(OLD, "server", "static", "index.html"), encoding="utf-8").read()
VIEUX_PROFIL = open(os.path.join(OLD, "server", "static", "profil.js"), encoding="utf-8").read()
VIEUX_APP = open(os.path.join(OLD, "server", "app.py"), encoding="utf-8").read()
VIEUX_JEU = open(os.path.join(OLD, "server", "static", "jeu.js"), encoding="utf-8").read()
ok("start_ts" in VIEUX_APP and "muscu-vibration" in VIEUX and "Ta première séance apparaîtra ici." in VIEUX and "s.pend" not in VIEUX_JEU,
   f"(le code de départ est bien celui de la 0.7.0 : durée de séance, vibrations, lot 2, mais pas de jetons de quête en attente) {OLD}")

def sans_attente(e):
    """Export sans le champ « pend » du jeu (ajouté à 0 par le code actuel) ; renvoie aussi sa valeur."""
    e = json.loads(json.dumps(e)); v = e["jeu"].pop("pend", None) if isinstance(e.get("jeu"), dict) else None
    return e, v
def sans_duree(o):
    """Depuis la 0.7.0, début et fin de séance existent déjà des deux côtés : rien à retirer (même forme que migration_v061.py)."""
    return o, []

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
# scénario joué par la page de la 0.7.0 après le questionnaire (mêmes appels que l'interface)
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

        # ============================================================ 1. données créées par la 0.7.0
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
               and any(e["archived"] for e in s["exercises"]), f"0.7.0, mode {mode} : 3 séances, 2 pesées, 2 photos, programme réglé, exercice archivé")
            ok(pr and pr["program"] and len(pr["program"]["ids"]) >= 2 and pr["answers"]["prenom"] == "Léa", f"0.7.0, mode {mode} : questionnaire rempli, programme généré")
            ok(j and j["init"] and j["pulls"] == 1, f"0.7.0, mode {mode} : jeu des Esprits joué")
        ok(exports["local"].get("jeu") and exports["local"].get("profil") and len(exports["photos"]["photos"]) == 2 and len(ph0) == 4,
           "0.7.0 : export local avec jeu et profil, export des 2 photos, 4 fichiers photo côté serveur")
        ok(not errs, f"(0.7.0 sans erreur JavaScript) {errs[:2]}")

        # ============================================================ 2. mêmes données ouvertes par le code actuel
        srv = serveur(os.path.join(ROOT, "server"), DBF); ctx = navigateur(); errs = []
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs); t = pg.inner_text("#app")
            ok(not QUESTIONNAIRE(t) and pg.locator(".tabbar").is_visible() and "Démarrer la séance" in t, f"mode {mode} : accueil, le questionnaire ne revient pas")
            b = pg.evaluate(RELEVE); a = avant[mode]
            (bs, vs), (be, ve) = sans_duree(b["state"]), sans_duree(b["export"])
            ok(bs == a["state"], f"mode {mode} : état identique (exercices, programmes et réglages, séances, ressentis, pesées)")
            be, pv = sans_attente(be)
            ok(be == sans_attente(a["export"])[0] and not pv, f"mode {mode} : export identique, jetons en attente à 0 (les réglages des notifications n'y entrent pas)")
            jb = json.loads(b["jeu"] or "null"); ja = json.loads(a["jeu"] or "null")
            ok(ja and jb and jb["tokens"] == ja["tokens"] and not jb.get("pend") and "pend" not in ja, f"mode {mode} : solde de jetons gardé tel quel ({jb and jb['tokens']}), rien en attente")
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
        ok(lignes[:1] == ["calme\t21:00\t08:00"] and len(lignes) >= 2 and all(len(l.split("\t")) == 5 for l in lignes[1:]), f"coque simulée : plan calculé sur les données de la 0.7.0 ({len(lignes) - 1} notification(s))")
        ok(any("\trappel:2026-10-19\t" in l for l in lignes), "coque simulée : rappel du lundi (jour du questionnaire) prévu")
        ok(pg.evaluate("[...JSON.parse(localStorage.getItem('muscu-notif')).rappel.days]") == [0, 2, 4], "réglages par défaut : jours du questionnaire (lundi, mercredi, vendredi)")
        b = pg.evaluate(RELEVE)
        ok(sans_attente(b["export"])[0] == sans_attente(avant["local"]["export"])[0] and b["profil"] == avant["local"]["profil"] and sans_attente({"jeu": json.loads(b["jeu"])})[0] == sans_attente({"jeu": json.loads(avant["local"]["jeu"])})[0] and not json.loads(b["jeu"]).get("pend"),
           "coque simulée : export, profil et jeu inchangés (jetons en attente à 0)")
        pg.evaluate("JEU.state().pend = 2")   # 2 jetons de quête en attente, pour l'export importé dans la 0.7.0 (étape 4)
        # une séance avec début et fin (52 min), comme l'enregistrerait l'interface, pour l'export importé dans la 0.7.0 (étape 4)
        pg.evaluate("""async () => { await api('POST', '/api/sessions', {day: '2026-10-19', workout_id: WO[0].id, start_ts: Date.parse('2026-10-19T09:00:00'),
          end_ts: Date.parse('2026-10-19T09:52:00'), entries: [{exercise_id: WO[0].items[0], sets: [[40, 10], [40, 10], [40, 9]]}]}); await load(); }""")
        ok(pg.evaluate("APPX.dureeMin(SESS.find(s => s.day === '2026-10-19'))") == 52, "coque simulée : séance de 52 min enregistrée")
        pg.evaluate("go('donnees')"); time.sleep(.3); pg.click("a:has-text(\"Télécharger l'export\")"); time.sleep(1)
        sv = [c for c in pg.evaluate("__N.calls") if c[0] == "save"]
        nouvel_export = sans_date(json.loads(sv[-1][2])) if sv else {}
        ok(bool(sv), "coque simulée : export confié à la coque (enregistrement du fichier)")
        ok("muscu-notif" not in json.dumps(nouvel_export) and "notif" not in nouvel_export, "nouvel export : sans réglages de notifications")
        ok("muscu-vibration" not in json.dumps(nouvel_export), "nouvel export : sans le réglage des vibrations (il reste sur le téléphone)")
        ok([(s["start_ts"], s["end_ts"]) for s in nouvel_export.get("sessions", []) if s["start_ts"]] == [(pg.evaluate("Date.parse('2026-10-19T09:00:00')"), pg.evaluate("Date.parse('2026-10-19T09:52:00')"))],
           "nouvel export : début et fin de la nouvelle séance (et rien pour les anciennes)")
        pg.close()
        idb1 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        i1, iv = sans_duree(idb1); i1["session"] = [x for x in i1["session"] if x["day"] != "2026-10-19"]; i1["entry"] = [x for x in i1["entry"] if x["session_id"] in {s["id"] for s in i1["session"]}]
        i1["_seq"] = idb0.get("_seq") if "_seq" in idb0 else i1.get("_seq")
        ok({k: v for k, v in i1.items() if k not in ("seq", "_seq")} == {k: v for k, v in idb0.items() if k not in ("seq", "_seq")},
           "IndexedDB : toutes les tables inchangées")
        sq, sv2 = sans_duree(sqlite_brut(DBF))
        ok(sq == sql0 and fichiers_photo(DBF) == ph0, "SQLite : rien ne change ; fichiers photo inchangés")
        ok(not errs, f"aucune erreur JavaScript (données de la 0.7.0 rouvertes) {errs[:2]}")
        ctx.close(); arreter(srv)

        # ============================================================ 3. exports de la 0.7.0 importés dans une appli neuve
        srv = serveur(os.path.join(ROOT, "server"), DBF_NEUF)
        br = p.chromium.launch(); errs = []
        for mode in MODES:
            ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); ctx.on("dialog", lambda d: d.accept()); surveiller(ctx)
            pg = ouvrir(ctx, mode, errs, "#app .card")
            importer(pg, exports[mode])
            if mode == "local":
                pg.evaluate("go('donnees')"); time.sleep(.3); pg.fill("#bk", json.dumps(exports["photos"])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
            pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.6)
            ok(not QUESTIONNAIRE(pg.inner_text("#app")), f"import de l'export 0.7.0, mode {mode} : le questionnaire saute")
            n = pg.evaluate(RELEVE)
            ok({k: v for k, v in sans_duree(n["export"])[0].items() if k not in ("jeu", "profil")} == {k: v for k, v in exports[mode].items() if k not in ("exported_at", "jeu", "profil")},
               f"mode {mode} : export de la 0.7.0 importé à l'identique (exercices, programmes et réglages, séances, pesées)")
            if mode == "local":
                jn = json.loads(n["jeu"]); ok(jn.pop("pend", 0) == 0 and jn == json.loads(avant["local"]["jeu"]) and json.loads(n["profil"]) == json.loads(avant["local"]["profil"]), "mode local : jeu et profil restaurés")
                ok([o[4] for o in n["octets"]] == [o[4] for o in avant["local"]["octets"]], "mode local : photos restaurées octet par octet")
            ctx.close()
        arreter(srv)

        # ============================================================ 4. export du code actuel importé dans la 0.7.0
        srv = serveur(os.path.join(OLD, "server"), DBF_RETOUR)
        ctx = br.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); ctx.on("dialog", lambda d: d.accept()); surveiller(ctx)
        pg = ouvrir(ctx, "local", errs, "#app .card"); importer(pg, nouvel_export)
        pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.6)
        n = pg.evaluate(RELEVE)
        ok({k: v for k, v in n["export"].items() if k not in ("photos",)} == {k: v for k, v in sans_duree(nouvel_export)[0].items() if k not in ("photos",)},
           "export du code actuel importé dans la 0.7.0 : mêmes données, jeu et profil compris")
        ok(nouvel_export.get("jeu", {}).get("pend") == 2 and len(n["state"]["sessions"]) == len(nouvel_export["sessions"]),
           "la 0.7.0 importe sans erreur un export avec 2 jetons de quête en attente")
        ctx.close(); br.close(); arreter(srv)
        ok(not errs, f"aucune erreur JavaScript (imports) {errs[:2]}")
        ok(not externes, f"aucune requête vers un autre domaine pendant tout le test {externes[:3]}")
finally:
    for pr in PROCS: pr.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
