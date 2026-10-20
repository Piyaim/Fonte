# SPDX-License-Identifier: AGPL-3.0-or-later
# Imite MainActivity.shouldInterceptRequest : la page est servie depuis server/static sous https://appassets.androidplatform.net/
# (sans aucun serveur, sans ?local=1) pour vérifier la détection du mode local, IndexedDB et le blocage du réseau.
import mimetypes, os, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATIC = os.path.join(ROOT, "server", "static")
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"   # profil déjà rempli : le questionnaire de départ ne s'impose pas
HOST = "appassets.androidplatform.net"; blocked = []; served = []
def handler(route):
    u = route.request.url; path = u.split(HOST, 1)[1].split("?")[0] if HOST in u else None
    if path is None:
        blocked.append(u); return route.fulfill(status=403, body="")
    p = "/index.html" if path in ("", "/") else path
    if p.startswith("/static/"): p = p[7:]
    p = p[1:]
    if ".." in p or not os.path.isfile(os.path.join(STATIC, p)): served.append((p, 404)); return route.fulfill(status=404, body="")
    served.append((p, 200)); route.fulfill(status=200, body=open(os.path.join(STATIC, p), "rb").read(), headers={"Content-Type": {".js": "text/javascript", ".html": "text/html", ".json": "application/json", ".webmanifest": "application/manifest+json", ".png": "image/png"}.get(os.path.splitext(p)[1], "application/octet-stream"), "Cache-Control": "no-cache"})
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}); errs = []; ctx.add_init_script(PROFIL_FAIT)
    ctx.route("**/*", lambda r: handler(r) if r.request.url.startswith("http") else r.continue_())
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"https://{HOST}/"); pg.wait_for_selector(".tabbar button", timeout=8000); time.sleep(.5)
    ok(pg.evaluate("window.FONTE_LOCAL") is True, "mode local détecté à partir du nom d'hôte de la coque")
    ok("Démarrer la séance" in pg.inner_text("#app"), "accueil affiché, 50 exercices chargés depuis seed.json")
    ok(pg.evaluate("'serviceWorker' in navigator && navigator.serviceWorker.controller === null"), "pas de service worker en mode local")
    pg.evaluate("api('POST','/api/bodyweight',{kg:82})"); time.sleep(.3); pg.reload(); pg.wait_for_selector(".tabbar button"); time.sleep(.5)
    bw = pg.evaluate("fetch('/api/state').then(r=>r.json()).then(s=>s.bodyweight.length)"); ok(bw == 1, f"les données survivent au rechargement ({bw} pesée)")
    ok(not blocked, f"aucune requête vers un autre domaine : {blocked}")
    ok(not any(c == 404 for _, c in served), f"tous les fichiers demandés existent : {[x for x in served if x[1] == 404]}")
    ok(not errs, f"erreurs JavaScript : {errs}")
    print("fichiers servis :", sorted({x[0] for x in served}))

    # aucune requête sortante, sur tous les écrans : onglets, sous-onglets des Esprits, fiche et démonstration d'un exercice,
    # puis le questionnaire de départ (appareil neuf, sans profil)
    for v in ["accueil", "seance", "zones", "progres", "historique", "exercices", "programmes", "jeu", "profil", "donnees"]:
        pg.evaluate(f"go('{v}')"); time.sleep(.3)
    for k in ["tirage", "collection", "garde", "boutique", "regles"]:
        pg.evaluate(f"go('jeu'); JEU.sub('{k}')"); time.sleep(.2)
    pg.evaluate("go('exercices'); openEx(Object.keys(EX)[0])"); time.sleep(1.5)
    ctx2 = b.new_context(viewport={"width": 390, "height": 844}); ctx2.route("**/*", lambda r: handler(r) if r.request.url.startswith("http") else r.continue_())
    pg2 = ctx2.new_page(); pg2.on("pageerror", lambda e: errs.append(str(e))); pg2.goto(f"https://{HOST}/"); pg2.wait_for_selector("button:has-text('Commencer')", timeout=8000)
    pg2.click("button:has-text('Commencer')"); time.sleep(.3)
    vus = len(served)
    ok(not blocked, f"aucune requête vers un autre domaine sur les 10 onglets, les 5 sous-onglets des Esprits, une fiche d'exercice et le questionnaire ({vus} fichiers servis) : {blocked}")
    pg2.evaluate("fetch('https://example.org/x').catch(() => 0)"); time.sleep(.5)
    ok(blocked == ["https://example.org/x"], f"(témoin : une requête sortante ajoutée exprès est bien détectée et bloquée) {blocked}")
    ok(not errs, f"erreurs JavaScript (tous les écrans) : {errs}")
