# SPDX-License-Identifier: AGPL-3.0-or-later
# Bouton « Tourner » de la fiche d'exercice : passage de la vue principale à la seconde vue (de face, de dos, de côté) et retour.
# Usage : python3 tests/tourner.py [dossier pour les captures]
import os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5117
SHOTS = sys.argv[1] if len(sys.argv) > 1 else None
env = dict(os.environ, DB_PATH="/tmp/tourner.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/tourner.db", "/tmp/tourner.db-wal", "/tmp/tourner.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, scheme in ((390, "light"), (360, "dark")):
            ctx = b.new_context(viewport={"width": w, "height": 844}, color_scheme=scheme); ctx.add_init_script(PROFIL_FAIT)
            pg = ctx.new_page(); errs = []; reqs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("request", lambda r: reqs.append(r.url))
            pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector(".tabbar button"); time.sleep(.5)
            open_ex = lambda slug: pg.evaluate(f"go('exercices'); openEx(Object.values(EX).find(e => e.slug === '{slug}').id)") or time.sleep(.4)
            aria = lambda: pg.get_attribute(".exd .big svg.fig", "aria-label") or ""
            frame = lambda: pg.evaluate("document.querySelector('.exd .big svg.fig g').innerHTML")
            tag = f"{w} px, {scheme}"
            for slug, v1, v2 in (("de", "de face", "de côté"), ("face-pull", "de dos", "de côté"), ("dips-assistes", "de côté", "de face")):
                open_ex(slug)
                btn = pg.locator(".exd .figturn")
                ok(btn.count() == 1 and f"Voir {v2}" in btn.inner_text() and f"vue {v1}" in aria(), f"{slug} ({tag}) : vue {v1}, bouton « Voir {v2} »")
                bb = btn.bounding_box() if btn.count() else None
                ok(bb and bb["height"] >= 44 and bb["x"] >= 0 and bb["x"] + bb["width"] <= w, f"{slug} ({tag}) : bouton d'au moins 44 px, dans l'écran")
                if not btn.count(): continue
                btn.click(); time.sleep(.3)
                f1 = frame(); time.sleep(.6); f2 = frame()
                ok(f"vue {v2}" in aria() and pg.get_attribute(".exd .big svg.fig", "data-alt") == "1" and f1 != f2, f"{slug} ({tag}) : après « Tourner », vue {v2} animée")
                if SHOTS and slug == "de": pg.screenshot(path=os.path.join(SHOTS, f"tourner-{slug}-{w}-{scheme}.png"))
                pg.locator(".exd .figturn").click(); time.sleep(.3)
                ok(f"vue {v1}" in aria() and pg.get_attribute(".exd .big svg.fig", "data-alt") is None, f"{slug} ({tag}) : second appui, retour à la vue {v1}")
                if SHOTS and slug == "de": pg.screenshot(path=os.path.join(SHOTS, f"fiche-{slug}-{w}-{scheme}.png"))
            open_ex("developpe-couche")
            ok(pg.locator(".figturn").count() == 0, f"développé couché ({tag}) : une seule vue, pas de bouton")
            pg.evaluate("viewEx = null; go('exercices')"); time.sleep(.4)
            ok(pg.locator(".li .th svg").count() > 40 and pg.locator(".figturn").count() == 0, f"liste des exercices ({tag}) : vignettes sans bouton")
            ok(not errs, f"aucune erreur JavaScript ({tag}) : {errs[:2]}")
            ok(all(u.startswith(f"http://127.0.0.1:{PORT}/") or u.startswith("blob:") or u.startswith("data:") for u in reqs), f"aucune requête hors de l'appli ({tag})")
            ctx.close()
        b.close()
finally:
    srv.terminate()
