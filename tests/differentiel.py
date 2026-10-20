# SPDX-License-Identifier: AGPL-3.0-or-later
# Test différentiel : le même scénario d'appels API est joué contre le serveur Flask et contre le serveur local
# (static/local-backend.js, page ouverte avec ?local=1). Les réponses doivent être identiques.
#   python3 tests/differentiel.py     (nécessite : pip install flask playwright pillow)
import base64, io, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "server"); PORT = 5111; DBF = "/tmp/diff.db"
for f in (DBF, DBF + "-wal", DBF + "-shm"):
    if os.path.exists(f): os.remove(f)
env = dict(os.environ, DB_PATH=DBF, PYTHONDONTWRITEBYTECODE="1")
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(3)
from PIL import Image
def jpeg(color, size):
    b = io.BytesIO(); Image.effect_noise((size, size), 60).convert("RGB").save(b, "JPEG", quality=80); return base64.b64encode(b.getvalue()).decode()
IMG, THUMB = jpeg(0, 300), jpeg(0, 100)
BAD = base64.b64encode(b"not a jpeg" * 100).decode()
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"   # profil déjà rempli : le questionnaire de départ ne s'impose pas
DROP = {"ts", "updated_at", "exported_at", "jeu", "profil"}   # « jeu », « profil » : état du mini-jeu et questionnaire de départ, joints à l'export local seulement
def norm(x):
    # le champ diagram est un texte JSON : Python l'écrit avec des espaces, JavaScript sans ; on compare le contenu
    if isinstance(x, dict): return {k: (json.loads(v) if k == "diagram" and isinstance(v, str) else norm(v)) for k, v in x.items() if k not in DROP}
    if isinstance(x, list): return [norm(v) for v in x]
    return x
CALL = """async ([m,u,b,ph]) => { const o={method:m}; if (b!==null){o.headers={'Content-Type':'application/json'};o.body=JSON.stringify(b);}
  if (ph){ const fd=new FormData(); const bl=s=>{const a=Uint8Array.from(atob(s),c=>c.charCodeAt(0));return new Blob([a],{type:'image/jpeg'})};
    if(ph.img) fd.append('img',bl(ph.img),'a.jpg'); if(ph.thumb) fd.append('thumb',bl(ph.thumb),'t.jpg'); if(ph.day) fd.append('day',ph.day); if(ph.note!==undefined) fd.append('note',ph.note); o.body=fd; delete o.headers; }
  const r=await fetch(u,o); let j=null; try{j=await r.json()}catch(e){} return {status:r.status, body:j}; }"""
from playwright.sync_api import sync_playwright
fails = 0; total = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    cA, cB = b.new_context(), b.new_context(); cA.add_init_script(PROFIL_FAIT); cB.add_init_script(PROFIL_FAIT)
    A = cA.new_page(); B = cB.new_page()
    A.goto(f"http://127.0.0.1:{PORT}/"); B.goto(f"http://127.0.0.1:{PORT}/?local=1")
    A.wait_for_selector(".tabbar button"); B.wait_for_selector(".tabbar button")
    print("mode local actif :", B.evaluate("window.FONTE_LOCAL"), "| serveur :", A.evaluate("window.FONTE_LOCAL"))
    def both(label, m, u, body=None, ph=None, loose=False):
        global fails, total
        ra, rb = A.evaluate(CALL, [m, u, body, ph]), B.evaluate(CALL, [m, u, body, ph]); total += 1
        if loose:   # seul le code HTTP (et le début du message d'erreur) est comparé : le détail du texte vient de SQLite / Flask
            cut = (lambda r: r["status"]) if loose == "status" else (lambda r: (r["status"], ((r["body"] or {}).get("error") or "")[:28]))
            ra, rb = cut(ra), cut(rb)
            if ra != rb: fails += 1; print("DIFFÉRENCE", label, ra, rb)
            return ra
        if norm(ra) != norm(rb):
            fails += 1; print("DIFFÉRENCE", label, m, u, "\n  serveur:", json.dumps(norm(ra), ensure_ascii=False)[:600], "\n  local  :", json.dumps(norm(rb), ensure_ascii=False)[:600])
        return ra
    st = both("état initial", "GET", "/api/state")["body"]
    ids = [e["id"] for e in st["exercises"]]; e1, e2, e3 = ids[0], ids[1], ids[2]
    cardio = next(e["id"] for e in st["exercises"] if e["kind"] == "cardio")
    W = lambda **k: dict(name="Test", grp="Pecs", kind="weight", **k)
    # exercices
    both("ex ok", "POST", "/api/exercises", W(sets="4", target_min="12", target_max="8", rest=60, focus="x", tip="y", green=1, per_side=1, assisted=1))
    both("ex slug doublon", "POST", "/api/exercises", W())
    both("ex sans nom", "POST", "/api/exercises", dict(name=" ", grp="a", kind="reps"))
    both("ex sans groupe", "POST", "/api/exercises", dict(name="a", grp="", kind="reps"))
    both("ex type invalide", "POST", "/api/exercises", dict(name="a", grp="b", kind="zzz"))
    both("ex nombre invalide", "POST", "/api/exercises", W(sets="abc"))
    both("ex bornes", "POST", "/api/exercises", W(sets=99, rest=9999, target_min=0))
    both("ex accents slug", "POST", "/api/exercises", dict(name="Écarté à la poulie ÉÈ", grp="Dos", kind="reps"))
    both("ex corps invalide", "POST", "/api/exercises", [1, 2])
    new = both("état", "GET", "/api/state")["body"]["exercises"]; nid = max(e["id"] for e in new)
    both("ex maj", "PUT", f"/api/exercises/{nid}", dict(name="Renommé", grp="Dos", kind="time", sets=2, target_min=30, target_max=60))
    both("ex maj 404", "PUT", "/api/exercises/9999", W())
    both("ex archive 404", "POST", "/api/exercises/9999/archive", dict(archived=True))
    # programmes
    both("wo vide", "POST", "/api/workouts", dict(name=" "))
    wo = both("wo ok", "POST", "/api/workouts", dict(name="Mon programme"))["body"]["id"]
    both("wo maj", "PUT", f"/api/workouts/{wo}", dict(name="Prog 2", items=[e1, e2, e1, e3]))
    both("wo maj item inconnu", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[99999]))
    both("wo maj items pas liste", "PUT", f"/api/workouts/{wo}", dict(name="x", items="a"))
    both("wo maj 404", "PUT", "/api/workouts/9999", dict(name="x", items=[]))
    both("wo ordre", "POST", "/api/workouts/order", dict(ids=[wo, 1, 2]))
    # réglages propres à chaque séance (lot 2A) : séries, cible, repos d'un exercice dans un programme
    def check(label, cond):
        global fails, total
        total += 1
        if not cond: fails += 1; print("ÉCHEC", label)
    def reg(wid): return next(w for w in both(f"état (réglages {wid})", "GET", "/api/state")["body"]["workouts"] if w["id"] == wid)["settings"]
    both("wo réglages", "PUT", f"/api/workouts/{wo}", dict(name="Prog 2", items=[e1, e2, e3], settings={str(e1): dict(sets=4, target_min=5, target_max=5, rest=180), str(e2): dict(target_max="12", rest="45"), str(e3): dict(sets=None)}))
    r = reg(wo)
    check("réglages enregistrés", r == {str(e1): dict(sets=4, target_min=5, target_max=5, rest=180), str(e2): dict(sets=None, target_min=12, target_max=12, rest=45)})
    both("wo réglages bornes et inversion", "PUT", f"/api/workouts/{wo}", dict(name="Prog 2", items=[e1, e2, e3], settings={str(e1): dict(sets=99, target_min=15, target_max="8", rest=9999), str(e3): dict(target_min="0", sets=True), "99999": dict(sets=2)}))
    r = reg(wo)
    check("bornes, inversion, réglage hors programme ignoré", r == {str(e1): dict(sets=10, target_min=8, target_max=15, rest=600), str(e3): dict(sets=1, target_min=1, target_max=1, rest=None)})
    both("wo réglages pas objet", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[e1], settings=[1]))
    both("wo réglage pas objet", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[e1], settings={str(e1): 5}))
    both("wo réglage nombre invalide", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[e1], settings={str(e1): dict(sets="abc")}))
    both("wo réglage clé invalide", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[e1], settings={"abc": {}}))
    check("refus : programme et réglages inchangés", reg(wo) == r)
    both("wo sans settings (ancienne interface)", "PUT", f"/api/workouts/{wo}", dict(name="Prog 3", items=[e3, e1]))
    check("sans settings : réglages gardés pour les exercices restés", reg(wo) == {str(e1): r[str(e1)], str(e3): r[str(e3)]})
    both("wo settings null", "PUT", f"/api/workouts/{wo}", dict(name="Prog 3", items=[e3, e1], settings=None))
    check("settings null : retour aux valeurs des exercices", reg(wo) == {})
    both("wo réglages (suite)", "PUT", f"/api/workouts/{wo}", dict(name="Prog 2", items=[e1, e2, e3], settings={str(e1): dict(sets=4, target_min=5, rest=180), str(e2): dict(rest=30)}))
    w1 = st["workouts"][0]
    both("wo 1 réglages (pour l'export)", "PUT", f"/api/workouts/{w1['id']}", dict(name=w1["name"], items=w1["items"], settings={str(w1["items"][0]): dict(sets=5, target_min=3, target_max=5, rest=240)}))
    both("ex archive", "POST", f"/api/exercises/{e2}/archive", dict(archived=True))
    both("état après archive", "GET", "/api/state")
    check("archive : l'exercice et son réglage quittent le programme", str(e2) not in reg(wo) and str(e1) in reg(wo))
    both("wo maj archivé", "PUT", f"/api/workouts/{wo}", dict(name="x", items=[e2]))
    both("ex désarchive", "POST", f"/api/exercises/{e2}/archive", dict(archived=False))
    # séances
    S = lambda **k: dict(day="2026-10-01", workout_id=wo, entries=[dict(exercise_id=e1, sets=[[40, 10], ["42,5", "8"], [None, None], [50, 6]], effort=2), dict(exercise_id=cardio, sets=[[None, 20]])], **k)
    s1 = both("séance ok", "POST", "/api/sessions", S(notes="ok"))["body"]["id"]
    both("séance sans série", "POST", "/api/sessions", dict(day="2026-10-02", entries=[dict(exercise_id=e1, sets=[[None, None]])]))
    both("séance exo inconnu", "POST", "/api/sessions", dict(entries=[dict(exercise_id=99999, sets=[[1, 1]])]))
    both("séance jour invalide", "POST", "/api/sessions", dict(day="2026-02-30", entries=[dict(exercise_id=e1, sets=[[1, 1]])]))
    both("séance entries non liste", "POST", "/api/sessions", dict(entries="x"))
    both("séance nombre invalide", "POST", "/api/sessions", dict(entries=[dict(exercise_id=e1, sets=[["abc", 1]])]))
    both("séance hors limites", "POST", "/api/sessions", dict(entries=[dict(exercise_id=e1, sets=[[1e9, 1]])]))
    both("séance effort hors bornes", "POST", "/api/sessions", dict(day="2026-10-03", workout_id=99999, workout_name="Libre X", entries=[dict(exercise_id=e3, sets=[[10, 5]], effort=9)]))
    both("séance sans jour", "POST", "/api/sessions", dict(entries=[dict(exercise_id=e3, sets=[[1, 1]] * 25)]))
    both("séance maj", "PUT", f"/api/sessions/{s1}", dict(day="2026-10-04", workout_id=wo, workout_name="Renommée", notes="n", entries=[dict(exercise_id=e3, sets=[[30, 12]], effort=5)]))
    both("séance maj 404", "PUT", "/api/sessions/9999", S())
    both("séance maj vide", "PUT", f"/api/sessions/{s1}", dict(entries=[]))
    both("état après séances", "GET", "/api/state")
    both("ex suppr utilisé", "DELETE", f"/api/exercises/{e3}")
    both("ex suppr libre", "DELETE", f"/api/exercises/{nid}")
    # poids
    both("poids ok", "POST", "/api/bodyweight", dict(kg="81,5", day="2026-10-05"))
    both("poids trop bas", "POST", "/api/bodyweight", dict(kg=5))
    both("poids vide", "POST", "/api/bodyweight", dict())
    both("poids ok 2", "POST", "/api/bodyweight", dict(kg=80))
    both("poids suppr", "DELETE", "/api/bodyweight/1")
    # photos
    both("photo manquante", "POST", "/api/photos", None, dict(day="2026-10-05"))
    both("photo pas jpeg", "POST", "/api/photos", None, dict(img=BAD, thumb=BAD, day="2026-10-05"))
    both("photo jour invalide", "POST", "/api/photos", None, dict(img=IMG, thumb=THUMB, day="nope"))
    both("photo ok", "POST", "/api/photos", None, dict(img=IMG, thumb=THUMB, day="2026-10-05", note="de face"))
    both("photo ok 2", "POST", "/api/photos", None, dict(img=IMG, thumb=THUMB, day="2026-09-01", note="x" * 300))
    both("photos liste", "GET", "/api/photos")
    la = A.evaluate("fetch('/photos/1/full').then(r=>r.blob()).then(b=>b.size)")
    lb = B.evaluate("fetch(photoUrl(1,'full')).then(r=>r.blob()).then(b=>b.size)")
    total += 1
    if la != lb or la < 500: fails += 1; print("DIFFÉRENCE taille photo", la, lb)
    both("photo suppr", "DELETE", "/api/photos/1")
    both("programme suppr", "DELETE", f"/api/workouts/{wo}")
    both("état final 1", "GET", "/api/state")
    # export / import
    ex = both("export", "GET", "/api/export")["body"]
    attendu = {str(w1["items"][0]): dict(sets=5, target_min=3, target_max=5, rest=240)}
    check("l'export contient les réglages par séance", next(w for w in ex["workouts"] if w["id"] == w1["id"])["settings"] == attendu)
    vieux = json.loads(json.dumps(ex)); [w.pop("settings") for w in vieux["workouts"]]
    both("import ancien export (sans réglages)", "POST", "/api/import", vieux)
    check("ancien export importé : programmes là, sans réglages", all(w["settings"] == {} for w in both("état après ancien export", "GET", "/api/state")["body"]["workouts"]) and reg(w1["id"]) == {})
    both("import complet (aller-retour)", "POST", "/api/import", ex)
    both("état après import", "GET", "/api/state")
    check("nouvel export ré-importé : réglages restitués", reg(w1["id"]) == attendu)
    both("import complet incomplet", "POST", "/api/import", dict(format="suivi-muscu", exercises=[dict(id=1)]), loose=True)
    both("état après import refusé", "GET", "/api/state")
    both("import format inconnu", "POST", "/api/import", dict(zzz=1))
    both("import corps invalide", "POST", "/api/import", [1])
    seed = json.load(open(os.path.join(APP, "static", "seed.json")))
    cardio_key = next(iter(seed["legacy_cardio"]))
    leg = dict(L=[dict(ts=1760000000000, d="12/10/2026", s="A", x={"pc": [[40, 10], [40, 8]], "di": [[None, 12]]}, c=[25, cardio_key], n="vieille séance"), dict(ts=1760000100000, d="13/10/2026", s="B", x={})], W=[["12/10/2026", 80.5], ["13/10/2026", 80.0]])
    both("import ancienne appli", "POST", "/api/import", leg)
    both("import ancienne appli (doublons)", "POST", "/api/import", leg)
    both("import ancienne exo inconnu", "POST", "/api/import", dict(L=[dict(d="01/01/2026", x={"zzz": [[1, 1]]})]))
    both("import ancienne date illisible", "POST", "/api/import", dict(L=[dict(d="hier", x={})]))
    both("état après import ancienne appli", "GET", "/api/state")
    both("route inconnue", "GET", "/api/nimporte", loose="status")
    # persistance locale : rechargement de la page
    avant = B.evaluate(CALL, ["GET", "/api/state", None, None])
    B.reload(); B.wait_for_selector(".tabbar button")
    apres = B.evaluate(CALL, ["GET", "/api/state", None, None]); total += 1
    if norm(avant) != norm(apres): fails += 1; print("DIFFÉRENCE : les données locales ne survivent pas au rechargement")
    print(f"\n{total - fails}/{total} comparaisons identiques" + ("" if not fails else f" ; {fails} ÉCHEC(S)"))
srv.kill(); sys.exit(1 if fails else 0)
