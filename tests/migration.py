# SPDX-License-Identifier: AGPL-3.0-or-later
# Migration vers les réglages par séance (lot 2A), sans perte.
# 1. Le code du commit 805eba3 (lot 1, sorti de Git) crée de vraies données : base SQLite (mode serveur) ET
#    IndexedDB + localStorage (mode local), avec programmes modifiés, séances, ressentis, pesées, photos, profil, jeu.
# 2. Le code actuel rouvre ces mêmes données (même fichier SQLite, même profil de navigateur, même adresse).
# 3. Tout doit être identique, avec en plus des réglages vides ; puis les réglages doivent fonctionner sur ces données.
#   python3 tests/migration.py
import base64, io, json, os, shutil, sqlite3, subprocess, sys, tempfile, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); PORT = 5115; ANCIEN = "805eba3"
TMP = tempfile.mkdtemp(prefix="fonte-migration-"); DBF = os.path.join(TMP, "data", "suivi.db"); PROFIL_NAV = os.path.join(TMP, "navigateur")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

# ------------------------------------------------------------ code de 805eba3, extrait de Git dans un dossier temporaire
OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
subprocess.run(f"git -C '{ROOT}' archive {ANCIEN} server | tar -x -C '{OLD}'", shell=True, check=True)
ok("ITEM_FIELDS" not in open(os.path.join(OLD, "server", "app.py"), encoding="utf-8").read(), f"(le code extrait est bien celui d'avant le lot 2A : {ANCIEN})")

PROCS = []
def serveur(dossier):
    env = dict(os.environ, DB_PATH=DBF, PYTHONDONTWRITEBYTECODE="1")
    p = subprocess.Popen([sys.executable, "-c", f"import app;app.app.run(port={PORT})"], cwd=dossier, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    PROCS.append(p); time.sleep(3)
    if p.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {PORT} déjà pris ?)")
    return p

from PIL import Image
def jpeg(size):
    b = io.BytesIO(); Image.effect_noise((size, size), 60).convert("RGB").save(b, "JPEG", quality=80); return base64.b64encode(b.getvalue()).decode()
IMG, THUMB = jpeg(300), jpeg(100)
PROFIL = {"version": 1, "created": "2026-10-18T09:00:00Z", "updated": "2026-10-18T09:05:00Z", "bmi": 22.8, "program": None,
          "answers": {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
                      "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]},
                      "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}}
# scénario joué par l'ANCIENNE page, en mode serveur puis en mode local (mêmes appels)
REMPLIR = """async ([img, thumb]) => {
  const st = await api('GET', '/api/state'), ids = Object.keys(EX).map(Number), [a, b, c, d] = ids;
  const ex = await api('POST', '/api/exercises', {name: 'Tirage perso', grp: 'Dos', kind: 'weight', sets: 4, target_min: 6, target_max: 8, rest: 120});
  const w = await api('POST', '/api/workouts', {name: 'Mon programme'});
  await api('PUT', '/api/workouts/' + w.id, {name: 'Mon programme', items: [a, ex.id, c]});
  await api('PUT', '/api/workouts/' + st.workouts[0].id, {name: st.workouts[0].name + ' modifiée', items: [...st.workouts[0].items].reverse()});
  await api('POST', '/api/sessions', {day: '2026-10-10', workout_id: st.workouts[0].id, notes: 'première', entries: [{exercise_id: a, sets: [[40, 10], [42.5, 8]], effort: 3}, {exercise_id: b, sets: [[null, 12]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: w.id, entries: [{exercise_id: ex.id, sets: [[30, 8], [30, 7], [30, 6], [27.5, 8]], effort: 4}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_id: st.workouts[1].id, entries: [{exercise_id: d, sets: [[20, 12]], effort: 2}]});
  await api('DELETE', '/api/workouts/' + st.workouts[1].id);
  await api('POST', '/api/exercises/' + b + '/archive', {archived: true});
  await api('POST', '/api/bodyweight', {kg: 81.5, day: '2026-10-10'}); await api('POST', '/api/bodyweight', {kg: 80.9, day: '2026-10-14'});
  const bl = s => new Blob([Uint8Array.from(atob(s), ch => ch.charCodeAt(0))], {type: 'image/jpeg'});
  for (const [day, note] of [['2026-10-10', 'de face'], ['2026-10-14', 'de profil']]) {
    const fd = new FormData(); fd.append('img', bl(img), 'a.jpg'); fd.append('thumb', bl(thumb), 't.jpg'); fd.append('day', day); fd.append('note', note);
    const r = await fetch('/api/photos', {method: 'POST', body: fd}); if (!r.ok) throw new Error('photo ' + r.status);
  }
  await load(); go('jeu');
}"""
# tout ce qui doit survivre (les photos sont comparées par taille et par octets du début)
RELEVE = """async () => {
  const j = async u => (await fetch(u)).json(), st = await j('/api/state'), ex = await j('/api/export'), ph = await j('/api/photos');
  delete ex.exported_at;
  const tailles = [];
  for (const p of ph) for (const k of ['full', 'thumb']) { const b = await (await fetch(photoUrl(p.id, k))).arrayBuffer(); tailles.push([p.id, k, b.byteLength, Array.from(new Uint8Array(b.slice(0, 64))).join(',')]); }
  return {state: st, export: ex, photos: ph, tailles, profil: localStorage.getItem('muscu-profil'), jeu: localStorage.getItem('muscu-jeu')};
}"""
BRUT_IDB = """() => new Promise((res, rej) => { const r = indexedDB.open('fonte', 1); r.onerror = () => rej(r.error);
  r.onsuccess = () => { const t = r.result.transaction('kv', 'readonly').objectStore('kv').get('db'); t.onsuccess = () => { res(t.result); r.result.close(); }; t.onerror = () => rej(t.error); }; })"""
def sans_settings(x):
    if isinstance(x, dict): return {k: sans_settings(v) for k, v in x.items() if k != "settings"}
    if isinstance(x, list): return [sans_settings(v) for v in x]
    return x
def sqlite_brut():
    c = sqlite3.connect(DBF); c.row_factory = sqlite3.Row
    out = {t: [dict(r) for r in c.execute(f"SELECT * FROM {t} ORDER BY rowid")] for t in ("exercise", "workout", "workout_item", "session", "entry", "effort", "bodyweight", "photo")}
    cols = [r[1] for r in c.execute("PRAGMA table_info(workout_item)")]; c.close(); return out, cols
MODES = {"serveur": "/", "local": "/?local=1"}

from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        def navigateur():
            ctx = p.chromium.launch_persistent_context(PROFIL_NAV, viewport={"width": 390, "height": 844}, service_workers="block")
            ctx.on("dialog", lambda d: d.accept()); return ctx
        def ouvrir(ctx, mode, errs):
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(f"{mode}: {e}"))
            pg.goto(f"http://127.0.0.1:{PORT}{MODES[mode]}"); pg.wait_for_selector(".tabbar button", timeout=10000); time.sleep(.5); return pg

        # ------------------------------------------------------------ 1. données créées par l'ancien code
        srv = serveur(os.path.join(OLD, "server")); ctx = navigateur(); errs = []
        pg = ctx.new_page(); pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.evaluate("p => localStorage.setItem('muscu-profil', JSON.stringify(p))", PROFIL); pg.close()
        avant = {}
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs); pg.evaluate(REMPLIR, [IMG, THUMB]); time.sleep(.5)
            avant[mode] = pg.evaluate(RELEVE); pg.close()
        idb0 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        ctx.close(); srv.terminate(); srv.wait()
        sql0, cols0 = sqlite_brut()
        for mode, a in avant.items():
            s = a["state"]
            ok(len(s["sessions"]) == 3 and len(s["bodyweight"]) == 2 and len(a["photos"]) == 2 and any(w["name"] == "Mon programme" for w in s["workouts"]),
               f"ancien code, mode {mode} : 3 séances, 2 pesées, 2 photos, programme ajouté")
            ok(all("settings" not in w for w in s["workouts"]), f"(témoin, mode {mode} : l'ancien code ne connaît pas les réglages par séance)")
        ok(avant["local"]["profil"] and avant["local"]["jeu"], "ancien code : profil et état du jeu présents dans localStorage")
        ok(cols0 == ["workout_id", "exercise_id", "position"] and not any("sets" in r for r in idb0["workout_item"]), "(témoin : base SQLite et IndexedDB à l'ancien format)")

        # ------------------------------------------------------------ 2. mêmes données ouvertes par le code actuel
        srv = serveur(os.path.join(ROOT, "server")); ctx = navigateur(); errs = []
        apres = {}
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs); apres[mode] = pg.evaluate(RELEVE); pg.close()
        idb1 = ouvrir(ctx, "local", errs).evaluate(BRUT_IDB)
        sql1, cols1 = sqlite_brut()
        for mode in MODES:
            a, b = avant[mode], apres[mode]
            ok(sans_settings(b["state"]) == a["state"], f"mode {mode} : état identique (exercices, programmes, séances, ressentis, pesées)")
            ok(all(w["settings"] == {} for w in b["state"]["workouts"]) and all(w["settings"] == {} for w in b["export"]["workouts"]), f"mode {mode} : réglages par séance vides partout")
            ok(sans_settings(b["export"]) == a["export"], f"mode {mode} : export identique (hors réglages vides)")
            ok(b["photos"] == a["photos"] and b["tailles"] == a["tailles"] and len(b["tailles"]) == 4, f"mode {mode} : 2 photos et vignettes intactes (tailles et octets)")
            ok(b["profil"] == a["profil"] and b["jeu"] == a["jeu"], f"mode {mode} : profil et état du jeu intacts")
        ok(cols1 == ["workout_id", "exercise_id", "position", "sets", "target_min", "target_max", "rest"], f"SQLite : colonnes de réglage ajoutées ({cols1})")
        ok({t: [{k: r[k] for k in r if k in (cols0 if t == "workout_item" else r)} for r in v] for t, v in sql1.items()} == sql0, "SQLite : toutes les lignes de toutes les tables inchangées")
        ok(all(r["sets"] is None and r["rest"] is None for r in sql1["workout_item"]), "SQLite : réglages vides (NULL) sur les lignes existantes")
        ok({k: v for k, v in idb1.items() if k != "workout_item"} == {k: v for k, v in idb0.items() if k != "workout_item"}, "IndexedDB : toutes les tables inchangées sauf workout_item")
        ok([{k: r[k] for k in ("workout_id", "exercise_id", "position")} for r in idb1["workout_item"]] == idb0["workout_item"]
           and all(r.get(k, "absent") is None for r in idb1["workout_item"] for k in ("sets", "target_min", "target_max", "rest")),
           "IndexedDB : programmes intacts, réglages vides ajoutés et enregistrés")

        # ------------------------------------------------------------ 3. les réglages fonctionnent sur les données migrées, et restent après redémarrage
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs)
            pg.evaluate("""async () => { const w = WO.find(x => x.name === 'Mon programme'); await api('PUT', '/api/workouts/' + w.id, {name: w.name, items: w.items, settings: {[w.items[1]]: {sets: 5, target_min: 3, target_max: 5, rest: 180}}}); }""")
            pg.close()
        ctx.close(); srv.terminate(); srv.wait()
        srv = serveur(os.path.join(ROOT, "server")); ctx = navigateur()
        for mode in MODES:
            pg = ouvrir(ctx, mode, errs)
            w = pg.evaluate("WO.find(x => x.name === 'Mon programme')")
            ok(w["settings"] == {str(w["items"][1]): {"sets": 5, "target_min": 3, "target_max": 5, "rest": 180}}, f"mode {mode} : réglage enregistré sur données migrées, présent après redémarrage")
            n = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => [s.sessions.length, s.bodyweight.length])")
            ok(n == [3, 2], f"mode {mode} : deuxième ouverture (migration déjà faite) sans perte ({n})")
            pg.close()
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        ctx.close(); srv.terminate()
finally:
    for pr in PROCS: pr.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
