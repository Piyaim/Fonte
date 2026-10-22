# SPDX-License-Identifier: AGPL-3.0-or-later
# Lot « Séance » (22/10/2026), modes local et serveur :
# - poids décimaux (47,3 kg ; 47,25 ; 47,333 ; 0,3) saisis avec une virgule ou un point : enregistrés tels quels, affichés sans arrondi
#   (historique, « Dernière », courbe de Progrès), gardés par l'export puis l'import, utilisés tels quels par le conseil de charge ;
# - lignes préremplies avec le conseil de charge (montée, baisse, ressenti « dur »), sinon la dernière séance, sinon vides ;
# - un exercice à la fois par défaut (« Démarrer la séance », « Reprendre la séance »), Aperçu en liste avec ✓ ;
# - boutons − et + (0,5 kg, 1 rep), appui long qui répète, jamais sous 0 ; ✓ : vibration de 15 ms et repos lancé ;
# - ressenti en 3 choix, affiché seulement après la dernière série validée : Facile = 2, Juste bien = 3, Dur = 4 (« dur » fait garder la charge) ;
# - minuteur : −15 s, +15 s, Passer, autre durée, série suivante annoncée, visible sur les autres onglets pendant un repos ;
# - écran allumé (coque simulée : FonteApp.keepScreenOn) en mode « un exercice à la fois » et pendant un repos, réglage du menu.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/seance.py
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5161
DB = "/tmp/seance_test.db"
for f in (DB, DB + "-wal", DB + "-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                       env=dict(os.environ, DB_PATH=DB, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

# profil « importé » : pas de questionnaire imposé, pas de phase ; vibrations et écran allumé notés
INIT = """localStorage.setItem('muscu-profil', JSON.stringify({version: 1, imported: true, created: '2026-10-01T10:00:00', updated: '2026-10-01T10:00:00', answers: {}, program: null}));
window.__vib = []; navigator.vibrate = p => { window.__vib.push(p); return true; };
window.__scr = []; window.FonteApp = {keepScreenOn: on => window.__scr.push(on)};"""
# programme « Test » : un exercice à charge (3 × 10-12, repos 90 s) et la planche (secondes)
PROG = """async () => { const x = Object.values(EX).find(e => e.slug === 'chest-press').id, p = Object.values(EX).find(e => e.slug === 'pl').id;
  const r = await api('POST', '/api/workouts', {name: 'Test'});
  await api('PUT', '/api/workouts/' + r.id, {name: 'Test', items: [x, p], settings: {[x]: {sets: 3, target_min: 10, target_max: 12, rest: 90}}});
  await load(); return [r.id, x, p]; }"""
SEANCES = "async l => { for (const s of l) await api('POST', '/api/sessions', s); await load(); R(); }"
EFFACER = "async () => { for (const s of [...SESS]) await api('DELETE', '/api/sessions/' + s.id); localStorage.removeItem('muscu-draft'); localStorage.removeItem('muscu-extras'); localStorage.removeItem('muscu-xcur'); F = null; await load(); R(); }"
TXT = "(el => { const c = el.cloneNode(true); c.querySelectorAll('details').forEach(d => d.remove()); return c.innerText; })"

try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for mode, url in (("local", f"http://127.0.0.1:{PORT}/?local=1"), ("serveur", f"http://127.0.0.1:{PORT}/")):
            M = mode
            ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(INIT)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time("2026-10-22T10:00:00")
            pg.goto(url); pg.wait_for_selector("#app .hero", timeout=8000)
            if mode == "serveur": pg.evaluate(EFFACER)
            wid, x, p_ = pg.evaluate(PROG)
            def demarrer():
                pg.evaluate(f"go('accueil'); startFromHome({wid})"); time.sleep(.3)
            def entrees(wid_=None):
                st = pg.evaluate("fetch('/api/state').then(r => r.json())")
                return st["sessions"][-1]["entries"]
            def serie(day, sets, effort=3):
                return {"day": day, "workout_id": wid, "workout_name": "Test", "entries": [{"exercise_id": x, "sets": sets, "effort": effort}]}

            # ======================================================= 1. un exercice à la fois par défaut, Aperçu en liste avec ✓
            demarrer()
            ok(pg.locator(".focus").count() == 1 and not pg.locator(".tabbar").is_visible(), f"{M} · « Démarrer la séance » ouvre un exercice à la fois (barre du bas masquée)")
            ok(pg.locator("#app input:not([type=date])").count() == 6 and pg.locator(".frow.act").count() == 1, f"{M} · un seul exercice affiché, une seule ligne avec − et +")
            pg.click("button:has-text('Aperçu')"); time.sleep(.2)
            n_tick = pg.locator(".card .tick").count()
            ok(pg.locator(".focus").count() == 0 and n_tick == 6 and pg.locator(".frow.act").count() == 0, f"{M} · Aperçu : séance en liste, ✓ sur les 6 séries, sans − ni + ({n_tick} ✓)")
            ok(pg.locator(".aph svg.fig").count() == 2 and pg.locator(".aph svg [data-fig], .aph svg[data-fig]").count() == 0, f"{M} · Aperçu : vignettes fixes, pas d'animation")
            pg.click("button:has-text('Un exercice à la fois')"); time.sleep(.2)
            ok(pg.locator(".focus").count() == 1, f"{M} · « Un exercice à la fois » revient au mode focus")
            pg.click("button:has-text('Aperçu')"); time.sleep(.2); pg.fill(f"#v{x}_0l", "41"); pg.evaluate("touched()")
            pg.evaluate("go('accueil')"); time.sleep(.2)
            ok("Reprendre la séance" in pg.inner_text("#app"), f"{M} · accueil : séance commencée")
            pg.click("button:has-text('Reprendre la séance')"); time.sleep(.3)
            ok(pg.locator(".focus").count() == 1 and pg.input_value(f"#v{x}_0l") == "41", f"{M} · « Reprendre la séance » : un exercice à la fois, valeur saisie gardée")
            pg.evaluate(EFFACER)
            pg.evaluate(f"go('accueil'); curW = {wid}; go('seance')"); time.sleep(.3)
            ok(pg.locator(".focus").count() == 1, f"{M} · onglet Séance ouvert directement : un exercice à la fois aussi")
            pg.evaluate(EFFACER)

            # ======================================================= 2. poids décimaux : saisis, enregistrés, affichés sans arrondi
            demarrer()
            for i, (l, v) in enumerate((("47,3", "10"), ("47.25", "10"), ("47,333", "12"))):
                pg.fill(f"#v{x}_{i}l", l); pg.fill(f"#v{x}_{i}v", v)
            pg.evaluate("touched()"); pg.evaluate("focMove(1)"); time.sleep(.2)
            pg.fill(f"#v{p_}_0l", "0,3"); pg.fill(f"#v{p_}_0v", "40"); pg.evaluate("touched()")
            pg.evaluate("saveSession()"); time.sleep(1); pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
            en = {e["exercise_id"]: e["sets"] for e in entrees()}
            ok(en.get(x) == [[47.3, 10], [47.25, 10], [47.333, 12]] and en.get(p_) == [[0.3, 40]], f"{M} · enregistré tel quel (virgule et point) : {en}")
            pg.evaluate("go('historique')"); time.sleep(.2); h = pg.inner_text("#app")
            ok("47,3 kg × 10" in h and "47,25 kg × 10" in h and "47,333 kg × 12" in h and "0,3 kg × 40 s" in h, f"{M} · historique : 47,3 · 47,25 · 47,333 · 0,3 kg, sans arrondi")
            demarrer(); t = pg.locator(".focus").evaluate(TXT)
            ok("Dernière : 47,3 kg × 10 · 47,25 kg × 10 · 47,333 kg × 12" in t, f"{M} · « Dernière » sans arrondi {[l for l in t.splitlines() if 'Dernière' in l]}")
            pg.evaluate("exitFocus()"); pg.evaluate("go('progres')"); pg.evaluate(f"PGEX = {x}; R()"); time.sleep(.2)
            lv = pg.locator(".chart .lv").first.text_content() if pg.locator(".chart .lv").count() else None
            pg.evaluate(SEANCES, [serie("2026-10-23", [[47.25, 10]])])
            pg.evaluate(f"PGEX = {x}; R()"); time.sleep(.2)
            lv2 = pg.locator(".chart .lv").first.text_content()
            ok(lv2 == "47,25", f"{M} · courbe de Progrès : dernière valeur 47,25 (pas 47,3) : {lv!r} puis {lv2!r}")
            # export puis import dans une appli neuve
            ex = pg.evaluate("fetch('/api/export').then(r => r.json())")
            raw = json.dumps(ex)
            ok("47.333" in raw and "47.25" in raw and "0.3" in raw, f"{M} · export : 47.333, 47.25 et 0.3 tels quels")
            ctx2 = b.new_context(viewport={"width": 390, "height": 844}); ctx2.add_init_script(INIT)
            pg2 = ctx2.new_page(); pg2.on("dialog", lambda d: d.accept())
            pg2.goto(url.replace("127.0.0.1", "localhost")); pg2.wait_for_selector("#app .hero", timeout=8000)
            pg2.evaluate("go('donnees')"); time.sleep(.2)
            pg2.fill("#bk", json.dumps(ex)); pg2.click("button:has-text('Importer')"); time.sleep(1.2)
            st2 = pg2.evaluate("fetch('/api/state').then(r => r.json())")
            got = sorted(json.dumps(e["sets"]) for s in st2["sessions"] for e in s["entries"])
            want = sorted(json.dumps(e["sets"]) for s in pg.evaluate("fetch('/api/state').then(r => r.json())")["sessions"] for e in s["entries"])
            ok(got == want and "[[47.3, 10], [47.25, 10], [47.333, 12]]" in got, f"{M} · import de l'export : séries identiques, décimales comprises")
            ctx2.close()
            pg.evaluate(EFFACER)

            # ======================================================= 3. conseil de charge avec une décimale, et lignes préremplies par le conseil
            pg.evaluate(SEANCES, [serie("2026-10-20", [[47.3, 12]] * 3)])
            demarrer(); t = pg.locator(".focus").evaluate(TXT)
            ok("Conseil : 48,3 kg × 10" in t, f"{M} · conseil après 3 × 12 à 47,3 kg : 48,3 kg × 10 (47,3 + 1, pas d'arrondi de la base)")
            v = [(pg.input_value(f"#v{x}_{i}l"), pg.input_value(f"#v{x}_{i}v")) for i in range(3)]
            ok(v == [("48,3", "10")] * 3, f"{M} · lignes préremplies avec le conseil (48,3 kg × 10), pas la dernière fois (47,3 × 12) : {v}")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
            pg.evaluate(SEANCES, [serie("2026-10-20", [[40, 11], [40, 12], [40, 12]])])
            demarrer(); v = [(pg.input_value(f"#v{x}_{i}l"), pg.input_value(f"#v{x}_{i}v")) for i in range(3)]
            ok(v == [("40", "12")] * 3, f"{M} · (témoin) une série sous le haut de la fourchette : on garde 40 kg, cible 12 : {v}")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
            pg.evaluate(SEANCES, [serie("2026-10-17", [[40, 8], [40, 8], [40, 10]]), serie("2026-10-20", [[40, 8], [40, 8], [40, 10]])])
            demarrer(); v = [(pg.input_value(f"#v{x}_{i}l"), pg.input_value(f"#v{x}_{i}v")) for i in range(3)]
            ok("35-37,5 kg × 10" in pg.inner_text(".focus") and v == [("37,5", "10")] * 3, f"{M} · baisse (35-37,5 kg × 10, pas de 2,5 kg) : lignes à 37,5 kg × 10 {v}")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
            pg.evaluate(SEANCES, [serie("2026-10-20", [[40, 12], [40, 12], [40, 11]], 4)])
            demarrer(); v = [(pg.input_value(f"#v{x}_{i}l"), pg.input_value(f"#v{x}_{i}v")) for i in range(3)]
            ok("garde 40 kg" in pg.inner_text(".focus") and v == [("40", "12"), ("40", "12"), ("40", "11")], f"{M} · ressenti « dur » : on garde 40 kg, répétitions de la dernière fois {v}")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
            demarrer(); v = [(pg.input_value(f"#v{x}_{i}l"), pg.input_value(f"#v{x}_{i}v")) for i in range(3)]
            ok(v == [("", "")] * 3, f"{M} · exercice jamais fait : lignes vides {v}")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)

            # ======================================================= 4. ressenti : 3 choix, après la dernière série ; « dur » fait garder
            pg.evaluate(SEANCES, [serie("2026-10-20", [[40, 12]] * 3)])
            demarrer()
            ok(pg.locator(".feel").count() == 0, f"{M} · ressenti absent avant la première série")
            pg.click(".frow.act .tick"); pg.click(".frow.act .tick"); time.sleep(.2)
            ok(pg.locator(".feel").count() == 0, f"{M} · ressenti absent après 2 séries sur 3")
            pg.click(".frow.act .tick"); time.sleep(.2)
            fb = [t.splitlines()[0] for t in pg.locator(".feelb button").all_inner_texts()]
            ok(fb == ["Facile", "Juste bien", "Dur"], f"{M} · après la dernière série : Facile, Juste bien, Dur {fb}")
            hb = min(pg.locator(".feelb button").evaluate_all("l => l.map(b => b.getBoundingClientRect().height)"))
            ok(hb >= 48, f"{M} · boutons du ressenti : {hb:.0f} px de haut (48 au moins)")
            pg.click(".feelb button:has-text('Dur')"); time.sleep(.2)
            ok(pg.locator(".feel").count() == 0 and "Dur" in pg.inner_text(".feel1"), f"{M} · après le choix : une seule ligne « Ressenti : Dur »")
            pg.evaluate("TMskip(); saveSession()"); time.sleep(1); pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
            eff = [e["effort"] for e in entrees() if e["exercise_id"] == x]
            ok(eff == [4], f"{M} · « Dur » enregistré comme 4 {eff}")
            demarrer(); t = pg.inner_text(".focus")
            ok("garde 42,5 kg" in t, f"{M} · séance suivante après « Dur » au haut de la fourchette : on garde 42,5 kg")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
            pg.evaluate(SEANCES, [serie("2026-10-20", [[40, 12]] * 3, 3)])
            demarrer(); ok("42,5 kg × 10" in pg.inner_text(".focus"), f"{M} · (témoin) « Juste bien » au haut de la fourchette : on monte (42,5 kg)")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)

            # ======================================================= 5. − et +, appui long, ✓ : vibration et repos
            demarrer(); pg.evaluate("window.__vib = []")
            plus, moins = f".frow.act .pm[data-in='v{x}_0l'][data-d='0.5']", f".frow.act .pm[data-in='v{x}_0l'][data-d='-0.5']"
            pg.fill(f"#v{x}_0l", "40"); pg.click(plus); a1 = pg.input_value(f"#v{x}_0l")
            pg.click(moins); pg.click(moins); a2 = pg.input_value(f"#v{x}_0l")
            pg.click(f".frow.act .pm[data-in='v{x}_0v'][data-d='1']"); r1 = pg.input_value(f"#v{x}_0v")
            ok(a1 == "40,5" and a2 == "39,5" and r1 == "1", f"{M} · + et − : 0,5 kg et 1 rep ({a1}, {a2}, reps {r1})")
            bb = pg.locator(plus).bounding_box(); pg.mouse.move(bb["x"] + 20, bb["y"] + 20); pg.mouse.down(); pg.wait_for_timeout(1200); pg.mouse.up()
            a3 = pg.evaluate(f"num($('v{x}_0l').value)"); pg.wait_for_timeout(400); a4 = pg.evaluate(f"num($('v{x}_0l').value)")
            ok(a3 >= 39.5 + 3 and a3 == a4, f"{M} · appui long de 1,2 s : la valeur monte toute seule puis s'arrête au relâchement ({a3}, puis {a4})")
            pg.fill(f"#v{x}_0l", "0,3"); pg.click(moins); pg.click(moins); a5 = pg.input_value(f"#v{x}_0l")
            ok(a5 == "0", f"{M} · − ne descend jamais sous 0 ({a5})")
            pg.fill(f"#v{x}_0l", "47,3"); pg.evaluate("touched()")
            hpm = min(pg.locator(".frow.act .pm").evaluate_all("l => l.map(b => Math.min(b.getBoundingClientRect().width, b.getBoundingClientRect().height))"))
            ok(hpm >= 48, f"{M} · boutons − et + de {hpm:.0f} px (48 au moins)")
            ok(pg.evaluate("window.__vib") == [], f"{M} · pas de vibration avant le ✓")
            pg.click(".frow.act .tick"); time.sleep(.3)
            ok(pg.evaluate("window.__vib") == [15], f"{M} · ✓ : vibration de 15 ms {pg.evaluate('window.__vib')}")
            ok(pg.inner_text("#tm") in ("1:30", "1:29"), f"{M} · ✓ : repos de 90 s lancé ({pg.inner_text('#tm')})")
            ok(pg.input_value(f"#v{x}_0l") == "47,3" and pg.locator(f".frow.act #v{x}_1l").count() == 1, f"{M} · ✓ : la série 2 devient la ligne active, 47,3 gardé")

            # ======================================================= 6. minuteur
            t0 = pg.inner_text("#tm"); pg.click("button:has-text('+15 s')"); t1 = pg.inner_text("#tm"); pg.click("button:has-text('−15 s')"); pg.click("button:has-text('−15 s')"); t2 = pg.inner_text("#tm")
            ok(t1 in ("1:45", "1:44") and t2 in ("1:15", "1:14"), f"{M} · +15 s puis −15 s ×2 : {t0} → {t1} → {t2}")
            ok("Ensuite : série 2 sur 3" in pg.inner_text(".bar"), f"{M} · série suivante annoncée : {pg.inner_text('.rb-next')!r}")
            fz = pg.evaluate("parseFloat(getComputedStyle($('tm')).fontSize)")
            ok(fz >= 40, f"{M} · compte à rebours en {fz:.0f} px")
            pg.evaluate("exitFocus(); go('progres')"); time.sleep(.2)
            ok(pg.locator(".bar").is_visible() and pg.locator("#tm").count() == 1, f"{M} · repos en cours : minuteur visible sur l'onglet Progrès")
            pg.click("button:has-text('Passer')"); time.sleep(.2)
            ok(not pg.locator(".bar").is_visible(), f"{M} · « Passer » : plus de minuteur sur Progrès")
            pg.evaluate("go('seance')"); time.sleep(.2)
            ok(pg.locator(".bar").is_visible() and "Lancer" in pg.inner_text(".bar") and pg.locator("#tm").count() == 0, f"{M} · onglet Séance, sans repos : « Lancer » et « Autre durée »")
            pg.click(".bar button:has-text('Autre durée')"); time.sleep(.1)
            ok(pg.locator(".rb-more button").all_inner_texts() == ["60 s", "90 s", "2 min"], f"{M} · « Autre durée » : 60 s, 90 s, 2 min")
            pg.click(".rb-more button:has-text('2 min')"); time.sleep(.2)
            ok(pg.inner_text("#tm") in ("2:00", "1:59"), f"{M} · 2 min lancé ({pg.inner_text('#tm')})")
            for _ in range(9):
                if pg.locator("button:has-text('−15 s')").count(): pg.click("button:has-text('−15 s')")
            time.sleep(.2)
            ok(pg.locator("#tm").count() == 0, f"{M} · −15 s jusqu'à zéro : le repos s'arrête")

            # ======================================================= 7. écran allumé (coque simulée)
            pg.evaluate("TMskip(); exitFocus(); go('accueil')"); time.sleep(.2); pg.evaluate("window.__scr = []")
            demarrer(); s1 = pg.evaluate("window.__scr.slice()")
            pg.evaluate("exitFocus()"); time.sleep(.1); s2 = pg.evaluate("window.__scr.slice()")
            pg.evaluate("TM(30)"); time.sleep(.1); s3 = pg.evaluate("window.__scr.slice()")
            pg.evaluate("TMskip()"); time.sleep(.1); s4 = pg.evaluate("window.__scr.slice()")
            ok(s1 == [True] and s2 == [True, False] and s3 == [True, False, True] and s4 == [True, False, True, False],
               f"{M} · écran allumé en mode « un exercice à la fois » et pendant un repos, puis rendu : {s4}")
            pg.evaluate("openMenu()"); time.sleep(.3)
            ok("Garder l’écran allumé" in pg.inner_text("#drawer") and pg.get_attribute("#dscreen .sw2", "aria-checked") == "true", f"{M} · menu : « Garder l’écran allumé », activé par défaut")
            pg.click("#dscreen .sw2"); pg.evaluate("closeMenu(); window.__scr = []"); demarrer(); pg.evaluate("TM(30)"); time.sleep(.1)
            ok(pg.evaluate("window.__scr") == [] and pg.evaluate("localStorage.getItem('muscu-ecran')") == "false", f"{M} · réglage coupé : l'écran n'est plus gardé allumé, réglage mémorisé")
            pg.evaluate("TMskip(); setScreen(true); exitFocus()")
            ok(not errs, f"{M} · aucune erreur JavaScript {errs[:2]}")
            ctx.close()

        # ======================================================= 8. 360 px : rien ne déborde dans la ligne active ni dans le minuteur
        ctx = b.new_context(viewport={"width": 360, "height": 780}); ctx.add_init_script(INIT); pg = ctx.new_page()
        pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector("#app .hero", timeout=8000)
        wid, x, p_ = pg.evaluate(PROG); pg.evaluate(f"startFromHome({wid})"); time.sleep(.3); pg.click(".frow.act .tick"); time.sleep(.3)
        lg = pg.evaluate("document.documentElement.scrollWidth")
        hs = pg.evaluate("[...document.querySelectorAll('.bar button, .frow.act button')].filter(b => b.getBoundingClientRect().height < 44).length")
        ok(lg <= 360 and hs == 0, f"360 px : pas de défilement horizontal ({lg}), boutons du minuteur et de la ligne active ≥ 44 px ({hs} trop petits)")
        ctx.close(); b.close()
finally:
    srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
