# SPDX-License-Identifier: AGPL-3.0-or-later
# Vérifie le branchement du changement d'icône : un faux pont FonteApp.setIcon (comme celui de MainActivity) reçoit la couleur choisie.
# Sans ce pont (ancienne coque), le texte d'origine reste affiché.
import os, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATIC = os.path.join(ROOT, "server", "static")
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"   # profil déjà rempli : le questionnaire de départ ne s'impose pas
HOST = "appassets.androidplatform.net"
def handler(route):
    p = route.request.url.split(HOST, 1)[1].split("?")[0]; p = "index.html" if p in ("", "/") else p[1:]
    if p.startswith("static/"): p = p[7:]
    f = os.path.join(STATIC, p)
    if not os.path.isfile(f): return route.fulfill(status=404, body="")
    route.fulfill(status=200, body=open(f, "rb").read(), headers={"Content-Type": {".js": "text/javascript", ".html": "text/html", ".json": "application/json", ".png": "image/png"}.get(os.path.splitext(p)[1], "application/octet-stream")})
with sync_playwright() as p:
    b = p.chromium.launch()
    for avec in (True, False):
        ctx = b.new_context(viewport={"width": 390, "height": 844}); errs = []; ctx.add_init_script(PROFIL_FAIT)
        ctx.route(f"https://{HOST}/**", handler)
        if avec: ctx.add_init_script("window.__icons=[]; window.FonteApp={setIcon:function(k){window.__icons.push(k)}, saveFile:function(){}};")
        pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(f"https://{HOST}/"); pg.wait_for_selector(".tabbar button"); time.sleep(.4)
        pg.evaluate("openMenu()"); time.sleep(.3)
        txt = pg.inner_text("#daccent")
        pg.click('.sw[aria-label="Bleu"]'); pg.click('.sw[aria-label="Rouge"]'); time.sleep(.2)
        got = pg.evaluate("window.__icons || null")
        if avec:
            ok(got == ["blue", "red"], f"pont présent : setIcon reçoit les couleurs choisies ({got})")
            ok("l’icône de l’écran d’accueil" in txt and "reste orange" not in txt, "texte du menu : l'icône suit la couleur")
        else:
            ok(got is None and "reste orange" in txt, "sans pont (ancienne coque) : texte d'origine, aucune erreur")
        ok(pg.evaluate("document.documentElement.dataset.accent") == "red", "l'interface change bien de couleur")
        ok(not errs, f"erreurs JavaScript : {errs}")
        ctx.close()
