# SPDX-License-Identifier: AGPL-3.0-or-later
# Durée de séance (décision du 22/10/2026) : début et fin enregistrés avec la séance, modes local et serveur.
#   début = « Démarrer la séance » de l'accueil, ou la première série validée si la séance est saisie depuis l'Aperçu ;
#   fin = enregistrement ; rien si la séance est saisie après coup (autre date) ; durée affichable seulement de 5 min à 3 h ;
#   modification depuis l'Historique (sans les champs) : début et fin gardés ; la durée ne change ni les jetons ni les quêtes ;
#   export et import : aller-retour exact, ancien export sans ces champs accepté ; un export actuel s'importe dans la 0.6.1
#   (mode serveur : API ; le mode local est contrôlé par migration_v061.py) ; mêmes réponses du serveur et du mode local.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/duree.py
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5175
TMP = tempfile.mkdtemp(prefix="fonte-duree-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
PROCS = []
def serveur(dossier, dbf, port=PORT):
    p = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={port})"], cwd=dossier,
                         env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(p); time.sleep(3); return p

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
SRC = open(os.path.join(APP, "static", "index.html"), encoding="utf-8").read(); JEU = open(os.path.join(APP, "static", "jeu.js"), encoding="utf-8").read()
ok("start_ts" not in JEU and "dureeMin" not in JEU and "end_ts" not in JEU, "jeu.js ne lit ni le début ni la fin : la durée ne rapporte ni jeton ni quête")
import re
ok(not re.search(r"(durée|séance)[^\"'`<]{0,30}trop (court|rapide)", SRC, re.I) and "Amplitude trop courte" in SRC,
   "aucun message de durée ou de séance « trop courte » (les conseils d'exercice « Amplitude trop courte » restent)")

T = lambda h: f"2026-11-04T{h}:00"   # un mercredi
CAS = [   # (début, fin) -> durée affichée attendue
    ("10:00", "10:04", None), ("10:00", "10:05", 5), ("10:00", "10:52", 52), ("10:00", "13:00", 180), ("10:00", "13:01", None), ("10:52", "10:00", None)]
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch(); reponses = {}
        for mode in ("local", "serveur"):
            dbf = os.path.join(TMP, mode + ".db"); srv = serveur(APP, dbf)
            ctx = b.new_context(viewport={"width": 390, "height": 844}); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            def heure(h): pg.clock.set_fixed_time(T(h))
            def clean(): pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
            def derniere(): return pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions.reduce((a, x) => x.id > a.id ? x : a))")
            heure("09:00"); pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if mode == "local" else "")); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REP)
            pg.reload(); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
            pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)

            # 1. « Démarrer la séance » à 10:00, saisie en mode focus, enregistrée à 10:52
            heure("10:00"); pg.evaluate("go('accueil')"); pg.click("#app .hero button:has-text('Démarrer la séance')"); pg.wait_for_timeout(300)
            heure("10:20"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000); pg.evaluate("go('seance')"); pg.wait_for_selector(".focus", timeout=8000)   # appli rouverte : le début survit (brouillon)
            pg.locator(".focus .tick").first.click(); pg.wait_for_timeout(100)
            while True:
                for i in pg.locator(".focus input[inputmode=decimal]").all(): i.fill("20")
                if pg.locator(".focus button:has-text('Suivant ›')").count(): pg.click(".focus button:has-text('Suivant ›')"); pg.wait_for_timeout(100)
                else: heure("10:52"); pg.click(".focus button:has-text('Terminer et enregistrer')"); break
            pg.wait_for_timeout(800); clean(); s1 = derniere()
            ok(s1["start_ts"] == pg.evaluate(f"Date.parse('{T('10:00')}')") and s1["end_ts"] == pg.evaluate(f"Date.parse('{T('10:52')}')"),
               f"{mode} · « Démarrer la séance » 10:00 → enregistrée 10:52 : début et fin enregistrés (première série validée à 10:20, rechargement entre-temps)")
            ok(pg.evaluate("s => APPX.dureeMin(s)", s1) == 52, f"{mode} · durée affichable : 52 min")

            # 2. Aperçu, sans « Démarrer » : ouverte à 11:00, première série validée à 11:05, enregistrée à 11:40 → 35 min (et pas 40)
            heure("11:00"); pg.evaluate("go('seance')"); pg.wait_for_timeout(300)
            if pg.locator("#tb-ap").is_visible(): pg.click("#tb-ap"); pg.wait_for_timeout(300)
            for i in pg.locator("#app input[inputmode=decimal]").all(): i.fill("22")
            heure("11:05"); pg.locator("#app .tick").first.click(); pg.wait_for_timeout(100)
            heure("11:40"); pg.click("#app button:has-text('Enregistrer la séance')"); pg.wait_for_timeout(800); clean(); s2 = derniere()
            ok(pg.evaluate("s => APPX.dureeMin(s)", s2) == 35 and s2["start_ts"] == pg.evaluate(f"Date.parse('{T('11:05')}')"),
               f"{mode} · Aperçu : le début est la première série validée (11:05 → 11:40 = 35 min)")

            # 3. saisie après coup : date changée pour la veille → ni début ni fin
            heure("12:00"); pg.evaluate("go('seance')"); pg.wait_for_timeout(300)
            if pg.locator("#tb-ap").is_visible(): pg.click("#tb-ap"); pg.wait_for_timeout(300)
            pg.fill("#f-day", "2026-11-03"); pg.dispatch_event("#f-day", "change")
            for i in pg.locator("#app input[inputmode=decimal]").all(): i.fill("24")
            pg.locator("#app .tick").first.click(); heure("12:30"); pg.click("#app button:has-text('Enregistrer la séance')"); pg.wait_for_timeout(800); clean(); s3 = derniere()
            ok(s3["day"] == "2026-11-03" and s3["start_ts"] is None and s3["end_ts"] is None and pg.evaluate("s => APPX.dureeMin(s)", s3) is None,
               f"{mode} · séance saisie après coup (veille) : ni début, ni fin, aucune durée ({s3['day']}, {s3['start_ts']})")

            # 4. bornes : 5 min à 3 h, sinon rien ; fin du jour d'avant ou fin avant le début : rien
            res = pg.evaluate("""cas => cas.map(([a, b]) => APPX.dureeMin({day: '2026-11-04', start_ts: Date.parse('2026-11-04T' + a + ':00'), end_ts: Date.parse('2026-11-04T' + b + ':00')}))""", [[a, c] for a, c, _ in CAS])
            ok(res == [d for _, _, d in CAS], f"{mode} · bornes : 4 min → rien, 5 → 5, 52 → 52, 180 → 180, 181 → rien, fin avant début → rien ({res})")
            ok(pg.evaluate("APPX.dureeMin({day: '2026-11-05', start_ts: Date.parse('2026-11-04T10:00:00'), end_ts: Date.parse('2026-11-04T10:52:00')})") is None,
               f"{mode} · séance datée d'un autre jour que sa fin : aucune durée")

            # 5. modification depuis l'Historique (corps sans début ni fin) : gardés ; avec null : effacés
            pg.evaluate("s => api('PUT', '/api/sessions/' + s.id, {workout_id: s.workout_id, day: s.day, notes: 'modifiée', entries: s.entries})", s1)
            m = pg.evaluate(f"fetch('/api/state').then(r => r.json()).then(s => s.sessions.find(x => x.id === {s1['id']}))")
            ok(m["notes"] == "modifiée" and m["start_ts"] == s1["start_ts"] and m["end_ts"] == s1["end_ts"], f"{mode} · modification sans les champs : début et fin gardés")
            pg.evaluate("s => api('PUT', '/api/sessions/' + s.id, {workout_id: s.workout_id, day: s.day, notes: '', entries: s.entries, start_ts: null, end_ts: null})", s2)
            m = pg.evaluate(f"fetch('/api/state').then(r => r.json()).then(s => s.sessions.find(x => x.id === {s2['id']}))")
            ok(m["start_ts"] is None and m["end_ts"] is None, f"{mode} · modification avec null : début et fin effacés")

            # 6. la durée ne change rien au jeu : même compte de jetons avec et sans début et fin
            sc = pg.evaluate("s => [JEU._.scoreSession(s), JEU._.scoreSession(Object.assign({}, s, {start_ts: null, end_ts: null})), JEU._.scoreSession(Object.assign({}, s, {start_ts: 1, end_ts: 9e12}))]", s1)
            ok(sc[0] == sc[1] == sc[2] and sc[0]["total"] >= 1, f"{mode} · jetons identiques avec ou sans durée ({sc[0]['lines']})")

            # 7. valeurs invalides : jamais d'erreur, rien d'enregistré (mêmes réponses en local et serveur, comparées plus bas)
            out = pg.evaluate("""async s => { const r = [];
              for (const v of ['abc', true, 123, -5, 1e14, '1761988800000', 1761988800000.7, null]) {
                const x = await api('POST', '/api/sessions', {day: '2026-11-02', workout_id: s.workout_id, entries: s.entries, start_ts: v, end_ts: v});
                const st = await (await fetch('/api/state')).json(), y = st.sessions.find(z => z.id === x.id); r.push([y.start_ts, y.end_ts]); }
              return r; }""", s1)
            reponses[mode] = out
            ok(out[:5] == [[None, None]] * 5 and out[5] == [1761988800000] * 2 and out[6] == [1761988800000] * 2 and out[7] == [None, None],
               f"{mode} · valeurs invalides (texte, booléen, trop petit, trop grand) : rien ; nombre en texte et décimal : arrondi ({out})")

            # 8. export, puis import : aller-retour exact ; ancien export (sans les champs) : séances sans début ni fin
            ex = pg.evaluate("fetch('/api/export').then(r => r.json())")
            ok(any(x.get("start_ts") for x in ex["sessions"]) and all("start_ts" in x and "end_ts" in x for x in ex["sessions"]), f"{mode} · l'export contient le début et la fin de chaque séance")
            st0 = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
            r = pg.evaluate("e => api('POST', '/api/import', e)", ex)
            st1 = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
            ok(st1 == st0, f"{mode} · export réimporté : séances identiques, début et fin compris")
            vieux = json.loads(json.dumps(ex))
            for x in vieux["sessions"]: x.pop("start_ts"); x.pop("end_ts")
            pg.evaluate("e => api('POST', '/api/import', e)", vieux)
            st2 = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
            ok(len(st2) == len(st0) and all(x["start_ts"] is None and x["end_ts"] is None for x in st2), f"{mode} · export sans ces champs (ancienne version) : importé, séances sans durée")
            reponses[mode + "-export"] = ex
            ok(not errs, f"{mode} · aucune erreur JavaScript {errs[:2]}")
            ctx.close(); srv.terminate(); srv.wait()
        ok(reponses["local"] == reponses["serveur"], "mêmes réponses du mode local et du serveur pour les valeurs invalides")
        b.close()

    # 9. un export actuel (avec durée) importé dans la 0.6.1, mode serveur : accepté, champs ignorés
    vieux = os.path.join(TMP, "v061"); os.makedirs(vieux)
    subprocess.run(f"git -C '{ROOT}' archive v0.6.1 server | tar -x -C '{vieux}'", shell=True, check=True)
    ok("start_ts" not in open(os.path.join(vieux, "server", "app.py"), encoding="utf-8").read(), "(le code de la 0.6.1 ne connaît pas start_ts)")
    srv = serveur(os.path.join(vieux, "server"), os.path.join(TMP, "v061.db"), PORT + 1)
    ex = reponses["serveur-export"]
    req = urllib.request.Request(f"http://127.0.0.1:{PORT + 1}/api/import", data=json.dumps(ex).encode(), headers={"Content-Type": "application/json"}, method="POST")
    code = urllib.request.urlopen(req).status
    st = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{PORT + 1}/api/state").read())
    sans = [{k: v for k, v in x.items() if k not in ("start_ts", "end_ts")} for x in ex["sessions"]]
    ok(code == 200 and st["sessions"] == sans, "0.6.1 (serveur) : export actuel importé, mêmes séances, début et fin ignorés sans erreur")
finally:
    for p in PROCS: p.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
