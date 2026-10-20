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

# Chaque couleur proposée dans l'appli doit exister partout : sinon l'icône ne change pas (ou l'appli plante au build).
import re
lire = lambda *c: open(os.path.join(ROOT, *c), encoding="utf-8").read()
RES = os.path.join(ROOT, "android", "app", "src", "main", "res")
cles = re.findall(r"\['(\w+)','[^']+','", re.search(r"var ACC = \[(.*?)\];", lire("server", "static", "index.html")).group(1))
java = re.search(r"ICONS = \{(.*?)\}", lire("android", "app", "src", "main", "java", "app", "fonte", "MainActivity.java")).group(1)
man, coul, lb, srv = lire("android", "app", "src", "main", "AndroidManifest.xml"), lire("android", "app", "src", "main", "res", "values", "colors.xml"), lire("server", "static", "local-backend.js"), lire("server", "app.py")
ok("mono" in cles and len(cles) == 6, f"couleurs proposées : {cles}")
for k in cles:
    suf = "" if k == "orange" else "_" + k
    manque = [n for n, c in [
        ("MainActivity.ICONS", f'"{k}"' in java),
        ("alias du manifeste", f'android:name=".Icon{k.capitalize()}"' in man and f"@mipmap/ic_launcher{suf}\"" in man),
        ("couleur de fond", f'name="ic_bg{suf}"' in coul),
        ("icône adaptative", os.path.isfile(os.path.join(RES, "mipmap-anydpi-v26", f"ic_launcher{suf}.xml"))),
        ("icônes PNG (5 tailles)", all(os.path.isfile(os.path.join(RES, f"mipmap-{d}", f"ic_launcher{suf}.png")) for d in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"))),
        ("logo local (local-backend.js)", re.search(rf"\b{k}: '#", lb) is not None),
        ("icône PWA (app.py)", f'"{k}": ((' in srv),
    ] if not c]
    ok(not manque, f"couleur {k} présente partout" + (f" ; manque : {manque}" if manque else ""))

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
        pg.click('.sw[aria-label="Bleu"]'); pg.click('.sw[aria-label="Rouge"]'); pg.click('.sw[aria-label="Noir et blanc"]'); time.sleep(.2)
        got = pg.evaluate("window.__icons || null")
        if avec:
            ok(got == ["blue", "red", "mono"], f"pont présent : setIcon reçoit les couleurs choisies ({got})")
            ok("l’icône de l’écran d’accueil" in txt and "reste orange" not in txt, "texte du menu : l'icône suit la couleur")
        else:
            ok(got is None and "reste orange" in txt, "sans pont (ancienne coque) : texte d'origine, aucune erreur")
        ok(pg.evaluate("document.documentElement.dataset.accent") == "mono", "l'interface change bien de couleur (noir et blanc)")
        ok(not errs, f"erreurs JavaScript : {errs}")
        ctx.close()
