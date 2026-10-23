# SPDX-License-Identifier: AGPL-3.0-or-later
# Refonte visuelle, lot 1 (direction B+, 22/10/2026) : polices locales, une seule action orange par écran, carte Esprits compacte,
# mode « un exercice à la fois » (série en cours visible à l'ouverture), démonstration de l'exercice suivant pendant le repos qui suit
# la dernière série d'un exercice (image fixe en mouvement réduit), écran de fin unique (records d'abord, puis les Esprits ; plus de
# fenêtres superposées), aucune requête hors de l'appli. Mode local (comme l'appli Android), 360 × 780, normal et mouvement réduit.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot1.py
import os, re, subprocess, sys, tempfile, shutil, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5177
TMP = tempfile.mkdtemp(prefix="fonte-lot1-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
STATIC = os.path.join(APP, "static")
src = open(os.path.join(STATIC, "index.html"), encoding="utf-8").read() + open(os.path.join(STATIC, "tokens.css"), encoding="utf-8").read()
ok(not re.search(r"https?://(fonts\.|cdn|unpkg)", src) and "url(polices/BricolageGrotesque.woff2)" in src and "url(polices/AtkinsonHyperlegibleNext.woff2)" in src,
   "polices déclarées en local (server/static/polices), aucun lien vers Google Fonts ni un CDN")
ok(all(os.path.exists(os.path.join(STATIC, "polices", f)) for f in ("BricolageGrotesque.woff2", "AtkinsonHyperlegibleNext.woff2", "OFL-BricolageGrotesque.txt", "OFL-AtkinsonHyperlegibleNext.txt"))
   and os.path.exists(os.path.join(ROOT, "CREDITS.md")), "polices, licences OFL et CREDITS.md présents")
ORANGE = """() => { const d = document.createElement('i'); d.style.color = getComputedStyle(document.documentElement).getPropertyValue('--a').trim(); document.body.appendChild(d);
  const c = getComputedStyle(d).color; d.remove(); const vis = b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(b).visibility !== 'hidden'; };
  return [...document.querySelectorAll('button')].filter(b => vis(b) && getComputedStyle(b).backgroundColor === c && b.getAttribute('aria-pressed') !== 'true').map(b => b.textContent.trim()); }"""
VISIBLE = """sel => { const a = document.querySelector(sel); if (!a) return null; const r = a.getBoundingClientRect();
  const bars = [...document.querySelectorAll('.bar, .fnavb')].filter(x => getComputedStyle(x).display !== 'none' && getComputedStyle(x).position === 'fixed').map(x => x.getBoundingClientRect().top);
  return r.top >= 0 && r.bottom <= Math.min(innerHeight, ...bars); }"""

from playwright.sync_api import sync_playwright
srv = None
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for reduit in (False, True):
            M = "mouvement réduit" if reduit else "normal"
            dbf = os.path.join(TMP, f"{int(reduit)}.db")
            srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"),
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(3)
            ctx = b.new_context(viewport={"width": 360, "height": 780}, reduced_motion="reduce" if reduit else "no-preference"); externes = []
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(f"http://127.0.0.1:{PORT}/") or not r.request.url.startswith("http") else (externes.append(r.request.url), r.abort()))
            pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time("2026-11-02T18:00:00")
            pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector("#app .card", timeout=8000)
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REP)
            pg.reload(); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
            pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            pg.evaluate("""async () => { for (const w of WO) await api('POST', '/api/sessions', {day: w === WO[0] ? '2026-10-30' : '2026-11-02', workout_id: w.id,
                entries: w.items.map(i => ({exercise_id: i, sets: [[40, 10], [40, 10], [40, 10]], effort: 3}))}); await load(); }""")
            pg.clock.set_fixed_time("2026-11-04T10:00:00"); pg.reload(); pg.wait_for_selector("#app .hero"); pg.evaluate("go('accueil')"); pg.wait_for_timeout(300)
            f = pg.evaluate("[...document.fonts].filter(x => x.status === 'loaded').map(x => x.family)")
            ok({"Bricolage Grotesque", "Atkinson Hyperlegible Next"} <= set(f), f"{M} · les deux polices sont chargées ({sorted(set(f))})")
            ok(pg.evaluate(ORANGE) == ["Démarrer la séance"], f"{M} · accueil : une seule action orange, « Démarrer la séance » ({pg.evaluate(ORANGE)})")
            sp = pg.evaluate("(() => { const c = document.querySelector('#app .card.spirits'); return c ? [!!c.querySelector('.team .lead svg'), c.querySelector('.team .lead').getBoundingClientRect().width, [...c.querySelectorAll('button')].map(b => b.textContent.trim())] : null; })()")
            ok(sp and sp[0] and sp[1] >= 56 and sp[2] in (["Tirer"], ["Équipe"]), f"{M} · carte Esprits compacte : esprit de tête de {sp and sp[1]} px, une action {sp and sp[2]}")
            # séance : série en cours entière à l'ouverture, au-dessus de la barre du bas, à 360 × 780
            pg.click("#app .hero button:has-text('Démarrer la séance')"); pg.wait_for_selector(".focus"); pg.evaluate("window.scrollTo(0, 0)"); pg.wait_for_timeout(300)
            ok(pg.evaluate(VISIBLE, ".focus .frow.act") is True, f"{M} · ouverture : série en cours visible sans défiler (360 × 780)")
            ok(pg.evaluate(ORANGE) == [], f"{M} · série en cours : aucune action orange ({pg.evaluate(ORANGE)})")
            for i in pg.locator(".focus .frow input").all(): i.fill("42,5")
            while pg.locator(".focus .frow.act .tick").count(): pg.locator(".focus .frow.act .tick").click(); pg.wait_for_timeout(200)
            dm = pg.evaluate("(() => { const s = document.querySelector('.bar .rb-demo svg.fig'); return s ? s.hasAttribute('data-fig') : null; })()")
            ok(dm is (not reduit), f"{M} · repos après la dernière série : exercice suivant en grand dans la barre de repos, {'image fixe' if reduit else 'animé'} ({dm})")
            ok(pg.locator(".focus button:has-text('Suivant ›')").is_visible(), f"{M} · pendant le repos : « Suivant › » accessible")
            pg.click(".bar button:has-text('Passer')"); pg.wait_for_timeout(300)
            ok(pg.evaluate("document.querySelector('.bar .rb-demo')") is None and pg.evaluate(ORANGE) == ["Suivant ›"], f"{M} · exercice fini : « Suivant › » devient l'action orange ({pg.evaluate(ORANGE)})")
            # fin : un seul écran, records puis Esprits, durée de 52 min, une seule action orange (« Terminer »)
            while True:
                for i in pg.locator(".focus .frow input").all():
                    if not i.input_value(): i.fill("45")
                if pg.locator(".focus button:has-text('Suivant ›')").count(): pg.click(".focus button:has-text('Suivant ›')"); pg.wait_for_timeout(120)
                else: pg.clock.set_fixed_time("2026-11-04T10:52:00"); pg.click(".focus button:has-text('Terminer et enregistrer')"); break
            pg.wait_for_selector(".fin"); pg.wait_for_timeout(600)
            fin = pg.evaluate("""(() => { const a = document.querySelector('.fin'), ss = [...a.querySelectorAll('section')];
              return {fenetres: document.querySelectorAll('.pr-overlay,.j-ov').length, tuiles: [...a.querySelectorAll('.sum div')].map(d => d.innerText.replace(/\\s+/g, ' ')),
                      ordre: ss.map(s => s.classList.contains('reward') ? 'esprits' : s.querySelector('.rec') ? 'records' : '?'), confettis: document.querySelectorAll('canvas').length,
                      tabbar: getComputedStyle(document.querySelector('.tabbar')).display}; })()""")
            ok(fin["fenetres"] == 0 and fin["ordre"] == ["records", "esprits"] and fin["tabbar"] == "none", f"{M} · fin : un seul écran, records puis Esprits, plus de fenêtres superposées {fin['ordre']}")
            ok(fin["tuiles"][0] == "52 min durée" and "séries" in fin["tuiles"][1], f"{M} · fin : durée de la séance, puis séries {fin['tuiles']}")
            ok(pg.evaluate(ORANGE) == ["Terminer"] and pg.locator(".fin .reward button:has-text('Tirer maintenant')").count() == 1, f"{M} · fin : « Terminer » seule action orange, « Tirer maintenant » en secondaire")
            ok(fin["confettis"] == (0 if reduit else 1), f"{M} · confettis du record : {'coupés' if reduit else 'lancés'} ({fin['confettis']})")
            pg.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)"); pg.wait_for_timeout(200)
            ok(pg.evaluate(VISIBLE, "#fin-hist") is True, f"{M} · fin : lien vers l'historique visible au bas de l'écran")
            pg.click("button:has-text('Terminer')"); pg.wait_for_timeout(300)
            ok(pg.evaluate("view") == "accueil", f"{M} · « Terminer » ramène à l'accueil")
            ok(not externes, f"{M} · aucune requête hors de l'appli {externes[:2]}")
            ok(not errs, f"{M} · aucune erreur JavaScript {errs[:2]}")
            ctx.close(); srv.terminate(); srv.wait(); srv = None
        b.close()
finally:
    if srv: srv.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
