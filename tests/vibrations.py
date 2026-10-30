# SPDX-License-Identifier: AGPL-3.0-or-later
# Réglage général des vibrations (décision du 22/10/2026) : un interrupteur « Vibrations » dans le menu ☰ commande toutes les
# vibrations de l'appli (✓ de série, record, fin du repos, tirage) ; il remplace opts.haptic de jeu.js (bouton retiré de
# Esprits > Règles, « Sons » y reste). Migration : tirage coupé (opts.haptic false) = vibrations coupées partout, une seule fois.
# Le réglage reste dans le menu quand l'onglet Esprits est masqué. Modes local et serveur.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/vibrations.py
import json, os, subprocess, sys, tempfile, shutil, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5176
TMP = tempfile.mkdtemp(prefix="fonte-vibrations-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
ESPION = "window.__vib = []; navigator.vibrate = p => { window.__vib.push(p); return true; };"
JEU_COUPE = {"v": 1, "init": False, "tokens": 0, "shards": 0, "pulls": 0, "pe": 0, "pl": 0, "owned": {}, "items": {}, "team": [], "equip": {}, "awarded": {},
             "days": {}, "wk": {}, "opts": {"sound": False, "haptic": False, "hide": False}, "log": []}

from playwright.sync_api import sync_playwright
srv = None
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for mode in ("local", "serveur"):
            dbf = os.path.join(TMP, mode + ".db")
            srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                                   env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(3)
            URL = f"http://127.0.0.1:{PORT}/" + ("?local=1" if mode == "local" else "")
            ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(ESPION); pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(URL); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
            ok(pg.evaluate("localStorage.getItem('muscu-vibration')") == "true", f"{mode} · appli neuve : vibrations activées par défaut")
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REP)
            pg.reload(); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
            pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            pg.evaluate("go('accueil')"); pg.click("#app .hero button:has-text('Démarrer la séance')"); pg.wait_for_selector(".focus")
            # les quatre sources de vibration : ✓ de série, record (celebrate), fin du repos (ring), tirage (buzz de jeu.js)
            QUATRE = """async () => { const n0 = __vib.length, out = {};
              document.querySelector('.focus .tick[aria-pressed="false"]').click(); out.serie = __vib.slice(n0);
              let n = __vib.length; const e = Object.values(EX).find(x => x.kind === 'weight');
              celebrate([{ex: e, set: [40, 10], score: 53, prev: 50}]); out.record = __vib.slice(n); document.querySelectorAll('.pr-overlay').forEach(o => o.remove());
              n = __vib.length; ring(); out.repos = __vib.slice(n);
              n = __vib.length; JEU.pull(1); await new Promise(r => setTimeout(r, 2500)); out.tirage = __vib.slice(n); document.querySelectorAll('.j-ov').forEach(o => o.remove());
              return out; }"""
            on = pg.evaluate(QUATRE)
            ok(on["serie"] == [15] and on["record"] == [[80, 60, 80]] and on["repos"] == [[300, 100, 300]] and len(on["tirage"]) >= 1,
               f"{mode} · activé : ✓ de série, record, fin du repos et tirage vibrent ({on})")
            # mouvement réduit : les confettis disparaissent, la vibration du record reste (seul l'interrupteur décide)
            pg.emulate_media(reduced_motion="reduce")
            rm = pg.evaluate("""() => { const n = __vib.length, c0 = document.querySelectorAll('canvas').length, e = Object.values(EX).find(x => x.kind === 'weight');
              celebrate([{ex: e, set: [40, 10], score: 53, prev: 50}]); const r = {vib: __vib.slice(n), confettis: document.querySelectorAll('canvas').length - c0};
              document.querySelectorAll('.pr-overlay').forEach(o => o.remove()); return r; }""")
            pg.emulate_media(reduced_motion="no-preference")
            ok(rm == {"vib": [[80, 60, 80]], "confettis": 0}, f"{mode} · mouvement réduit, vibrations activées : le record vibre, sans confettis ({rm})")
            # interrupteur du menu
            pg.click("#menu-btn"); pg.wait_for_timeout(300)
            sw = pg.locator("#dvib button[role=switch]")
            ok(sw.count() == 1 and sw.get_attribute("aria-checked") == "true" and "Vibrations" in pg.inner_text("#dvib"), f"{mode} · menu ☰ : interrupteur « Vibrations » activé")
            sw.click(); pg.wait_for_timeout(200)
            ok(sw.get_attribute("aria-checked") == "false" and pg.evaluate("localStorage.getItem('muscu-vibration')") == "false", f"{mode} · interrupteur coupé : réglage enregistré")
            pg.keyboard.press("Escape"); pg.evaluate("go('seance')"); pg.wait_for_selector(".focus")
            off = pg.evaluate(QUATRE)
            ok(off == {"serie": [], "record": [], "repos": [], "tirage": []}, f"{mode} · coupé : aucune vibration nulle part ({off})")
            pg.reload(); pg.wait_for_selector("#app .hero")
            ok(pg.evaluate("localStorage.getItem('muscu-vibration')") == "false", f"{mode} · coupé : le réglage survit au redémarrage")
            # Esprits masqué : le réglage reste dans le menu ; Règles : « Sons » reste, « Vibrations » n'y est plus
            pg.evaluate("go('jeu'); JEU.sub('regles')"); pg.wait_for_timeout(300); t = pg.inner_text("#app")
            ok("Sons" in t and "Vibrations" not in t, f"{mode} · Esprits > Règles : « Sons » reste, « Vibrations » est parti")
            pg.evaluate("JEU.setHidden(true); go('accueil')"); pg.wait_for_timeout(200); pg.click("#menu-btn"); pg.wait_for_timeout(300)
            ok(pg.locator("#dvib button[role=switch]").count() == 1 and pg.locator(".tabbar button:has-text('Esprits')").count() == 0,
               f"{mode} · onglet Esprits masqué : « Vibrations » toujours dans le menu")
            ok(not errs, f"{mode} · aucune erreur JavaScript {errs[:2]}")
            ctx.close()

            # migration : ancien réglage du tirage repris une seule fois
            for haptic, deja, attendu, quoi in ((False, None, False, "tirage coupé → coupées partout"), (True, None, True, "tirage activé → activées"),
                                                (None, None, True, "aucun état du jeu → activées"), (False, True, True, "réglage général déjà choisi : l'ancien n'est plus lu")):
                c2 = b.new_context(); c2.add_init_script(ESPION); p2 = c2.new_page()
                p2.goto(URL); p2.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
                j = dict(JEU_COUPE, opts={"sound": False, "haptic": haptic, "hide": False}) if haptic is not None else None
                p2.evaluate("([j, d]) => { localStorage.clear(); if (j) localStorage.setItem('muscu-jeu', JSON.stringify(j)); if (d !== null) localStorage.setItem('muscu-vibration', JSON.stringify(d)); }", [j, deja])
                p2.reload(); p2.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
                p2.evaluate("APPX.vib(15)")
                ok(p2.evaluate("localStorage.getItem('muscu-vibration')") == json.dumps(attendu) and (p2.evaluate("__vib") == [15]) == attendu,
                   f"{mode} · migration : {quoi}")
                c2.close()
            srv.terminate(); srv.wait(); srv = None
        b.close()
finally:
    if srv: srv.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
