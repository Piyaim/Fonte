# SPDX-License-Identifier: AGPL-3.0-or-later
# Corrections du 20/10/2026 :
# 1. création d'un exercice : le groupe se choisit dans une liste qui propose tous les groupes (avant : seul « Jambes » apparaissait
#    sur Android, car le champ libre ne suggérait que les groupes qui commencent par le texte déjà écrit) ;
# 2. séance par zones : option « Poids du corps uniquement ».
import os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5121
env = dict(os.environ, DB_PATH="/tmp/exz.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/exz.db", "/tmp/exz.db-wal", "/tmp/exz.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
def profil(lieu):
    return "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'%s}}))" % (", lieu: '%s'" % lieu if lieu else "")
TOUTES = "ZSEL = new Set(ZONES.map(([k]) => k)); ZN = 8; ZADV = true;"
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(profil(None))
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector(".tabbar button"); time.sleep(.4)

        # ---- 1. groupe d'un nouvel exercice
        pg.evaluate("go('exercices'); editEx = {}; R()"); time.sleep(.3)
        opts = pg.evaluate("[...document.querySelectorAll('#e-grps option')].map(o => o.textContent)") if pg.locator("#e-grps").count() else []
        attendus = ["Jambes", "Pectoraux", "Dos", "Épaules", "Bras", "Abdos et gainage", "Cardio", "Autre groupe…"]
        ok(all(g in opts for g in attendus), f"le choix du groupe propose tous les groupes : {opts}")
        if opts:
            pg.fill("#e-name", "Essai dos"); pg.select_option("#e-grps", "Dos"); pg.evaluate("saveEx()"); time.sleep(.6)
            g = pg.evaluate("(Object.values(EX).find(e => e.name === 'Essai dos') || {}).grp")
            ok(g == "Dos", f"exercice créé dans le groupe choisi ({g})")
            pg.evaluate("editEx = {}; R()"); time.sleep(.2)
            pg.fill("#e-name", "Essai mobilité"); pg.select_option("#e-grps", ""); pg.evaluate("grpPick()")
            ok(pg.is_visible("#e-grp"), "« Autre groupe… » ouvre le champ du nouveau groupe")
            pg.evaluate("saveEx()"); time.sleep(.3)
            ok(not pg.evaluate("Object.values(EX).some(e => e.name === 'Essai mobilité')"), "nouveau groupe vide : l'exercice n'est pas créé")
            pg.fill("#e-grp", "Mobilité"); pg.evaluate("saveEx()"); time.sleep(.6)
            g = pg.evaluate("(Object.values(EX).find(e => e.name === 'Essai mobilité') || {}).grp")
            ok(g == "Mobilité", f"exercice créé dans un nouveau groupe ({g})")
            pg.evaluate("editEx = Object.values(EX).find(e => e.name === 'Essai mobilité'); R()"); time.sleep(.2)
            ok(pg.evaluate("document.getElementById('e-grps').value") == "Mobilité", "à la modification, le groupe personnalisé est présélectionné")
            pg.evaluate("editEx = null; R()")

        # ---- 2. poids du corps uniquement
        pdc_cat = pg.evaluate("Object.values(EX).filter(e => PROFIL.pdc(e.slug) === true).map(e => e.slug)")
        ok(len(pdc_cat) >= 5 and "pompes" in pdc_cat and "pc" not in pdc_cat, f"exercices du catalogue au poids du corps : {pdc_cat}")
        pg.evaluate("api('POST', '/api/exercises', {name: 'Rowing inversé maison', grp: 'Dos', kind: 'reps', sets: 3, target_min: 8, target_max: 12, rest: 90}).then(load)"); time.sleep(.6)
        def tirage(pdc, n=15):
            return pg.evaluate("""(pdc) => { ZPDC = pdc; %s const out = new Set(); for (let i = 0; i < %d; i++) buildZones().forEach(id => out.add(id)); return [...out].map(id => ({slug: EX[id].slug, name: EX[id].name, pdc: isPdc(EX[id])})); }""" % (TOUTES, n), pdc)
        avec = tirage(True)
        ok(avec and all(x["pdc"] for x in avec), f"option cochée : seulement des exercices au poids du corps ({len(avec)} différents)")
        ok(any(x["name"] == "Rowing inversé maison" for x in avec), "un exercice créé, saisi en répétitions, est retenu au poids du corps")
        ok(not any(x["name"] == "Essai dos" for x in avec), "un exercice créé, saisi avec une charge, est écarté")
        sans = tirage(False)
        ok(any(not x["pdc"] for x in sans), "option décochée : les machines reviennent")
        pg.evaluate("ZPDC = true; ZCARD = true; " + TOUTES); ids = pg.evaluate("buildZones().map(id => EX[id].slug)")
        ok(not any(s in ("tapis-incline", "velo", "rameur", "elliptique", "stairmaster") for s in ids), f"cardio doux sur machine écarté : {ids}")
        pg.evaluate("ZCARD = false; ZPDC = false; localStorage.removeItem('muscu-zpdc')")
        pg.evaluate("ZPDC = true; go('zones')"); time.sleep(.3)
        ok("Poids du corps uniquement" in pg.inner_text("#app"), "case visible dans la séance par zones")
        n_dos = pg.evaluate("zCount('dos')"); pg.evaluate("ZPDC = false"); n_dos2 = pg.evaluate("zCount('dos')")
        ok(n_dos < n_dos2, f"le petit chiffre des zones suit l'option (dos : {n_dos} au poids du corps, {n_dos2} en tout)")
        ok(not errs, f"aucune erreur JavaScript : {errs}")
        pg.screenshot(path="/tmp/exz-zones.png", full_page=True)

        # ---- 3. par défaut, la case suit la réponse « Poids du corps seulement » du questionnaire
        for lieu, attendu in (("pdc", True), ("complete", False)):
            c = b.new_context(viewport={"width": 390, "height": 844}); c.add_init_script(profil(lieu)); q = c.new_page()
            q.goto(f"http://127.0.0.1:{PORT}/?local=1"); q.wait_for_selector(".tabbar button"); time.sleep(.3)
            ok(q.evaluate("zPdc()") is attendu, f"profil « {lieu} » : case {'cochée' if attendu else 'décochée'} par défaut")
            q.evaluate("ZPDC = !zPdc(); store('muscu-zpdc', ZPDC)"); q.reload(); q.wait_for_selector(".tabbar button")
            ok(q.evaluate("zPdc()") is (not attendu), "le choix de l'utilisateur est gardé et prime sur le profil")
            c.close()
        b.close()
finally:
    srv.terminate()
