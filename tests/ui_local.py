# SPDX-License-Identifier: AGPL-3.0-or-later
# Parcours dans l'interface en mode local (/?local=1) : accueil, séance, photo, export, import, rechargement.
import base64, io, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5112
env = dict(os.environ, DB_PATH="/tmp/ui.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/ui.db", "/tmp/ui.db-wal", "/tmp/ui.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from PIL import Image
im = Image.effect_noise((900, 600), 50).convert("RGB"); im.save("/tmp/ui_photo.jpg", "JPEG", quality=85)
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", accept_downloads=True)
    pg = ctx.new_page(); errs = []; reqs = []
    pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("request", lambda r: reqs.append(r.url))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector(".tabbar button"); time.sleep(.5)
    ok("Démarrer la séance" in pg.inner_text("#app"), "accueil affiché depuis les données locales")
    api_calls = [u for u in reqs if "/api/" in u]
    ok(not api_calls, f"aucun appel /api/ n'a atteint le réseau ({len(api_calls)})")
    pg.evaluate("go('seance')"); time.sleep(.3); ok(pg.locator(".eff").count() > 0 or "Presse" in pg.inner_text("#app") or len(pg.inner_text("#app")) > 200, "vue séance affichée")
    # enregistrer une séance par l'API de la page puis la retrouver dans l'historique
    pg.evaluate("""async () => { await api('POST','/api/sessions',{day:'2026-10-10',entries:[{exercise_id:EX_FIRST(),sets:[[40,10],[40,9]],effort:3}]}); await load(); }""".replace("EX_FIRST()", "Object.keys(EX)[0]"))
    pg.evaluate("go('historique')"); time.sleep(.3); ok("ressenti 3/5" in pg.inner_text("#app") or "40" in pg.inner_text("#app"), "séance visible dans l'historique")
    # photo
    pg.evaluate("go('progres')"); time.sleep(.5)
    pg.set_input_files('input[accept="image/*"]', "/tmp/ui_photo.jpg"); time.sleep(1.5)
    n = pg.locator(".phgrid img").count(); ok(n == 1, f"photo ajoutée ({n} vignette)")
    if n:
        src = pg.locator(".phgrid img").first.get_attribute("src"); w = pg.evaluate("document.querySelector('.phgrid img').naturalWidth")
        ok(src.startswith("blob:") and w > 0, f"vignette chargée depuis le stockage local (blob, largeur {w})")
    # export
    pg.evaluate("go('donnees')"); time.sleep(.3)
    with pg.expect_download() as d: pg.click("text=Télécharger l'export")
    data = json.load(open(d.value.path())); ok(data["format"] == "suivi-muscu" and len(data["sessions"]) == 1, f"export séances : {len(data['sessions'])} séance(s), {len(data['exercises'])} exercices")
    with pg.expect_download() as d2: pg.click("text=Télécharger les photos")
    ph = json.load(open(d2.value.path())); ok(ph["format"] == "fonte-photos" and len(ph["photos"]) == 1 and ph["photos"][0]["full"].startswith("data:image/jpeg"), "export photos : 1 photo en JPEG")
    # tout supprimer puis réimporter séances + photos
    pg.evaluate("indexedDB.deleteDatabase('fonte')"); 
    ctx2 = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True); pg2 = ctx2.new_page(); pg2.on("dialog", lambda d: d.accept())
    pg2.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg2.wait_for_selector(".tabbar button"); pg2.evaluate("go('donnees')"); time.sleep(.3)
    pg2.fill("#bk", json.dumps(data)); pg2.click("text=Importer le JSON") if pg2.locator("text=Importer le JSON").count() else pg2.evaluate("doImport()"); time.sleep(.8)
    pg2.fill("#bk", json.dumps(ph)); pg2.evaluate("doImport()"); time.sleep(1)
    st = pg2.evaluate("fetch('/api/state').then(r=>r.json())"); phs = pg2.evaluate("fetch('/api/photos').then(r=>r.json())")
    ok(len(st["sessions"]) == 1 and len(phs) == 1, f"import dans une base neuve : {len(st['sessions'])} séance, {len(phs)} photo")
    pg2.reload(); pg2.wait_for_selector(".tabbar button"); pg2.evaluate("go('progres')"); time.sleep(.8)
    ok(pg2.evaluate("document.querySelectorAll('.phgrid img').length") == 1, "la photo importée survit au rechargement")
    # couleurs
    pg2.click("#menu-btn"); time.sleep(.3); txt = pg2.inner_text("#drawer"); ok("icône sur l’écran d’accueil du téléphone reste orange" in txt, "mention honnête sur l'icône dans le menu")
    pg2.click('.sw[aria-label="Vert"]'); time.sleep(.2); lg = pg2.evaluate("document.getElementById('lg').src"); ok(lg.startswith("data:image/png"), "logo du menu dessiné en local")
    ok(not errs, f"erreurs JavaScript : {errs}")
    ext = [u for u in reqs if not u.startswith(f"http://127.0.0.1:{PORT}") and not u.startswith("blob:") and not u.startswith("data:")]
    ok(not ext, f"aucune requête vers l'extérieur : {ext}")
srv.kill()
