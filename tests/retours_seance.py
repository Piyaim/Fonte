# SPDX-License-Identifier: AGPL-3.0-or-later
# Retours de Georgio sur l'APK du lot « Séance » (22/10/2026), mode local :
# 1. masquer l'onglet Esprits le retire seulement de la barre du bas : « Esprits » reste dans le menu, et l'interrupteur
#    « Afficher l'onglet Esprits dans la barre du bas » du menu le remet ; il suit toujours l'état réel (même changé depuis le jeu) ;
# 2. le conseil de charge ne propose jamais un poids hors du pas du matériel, déduit des charges déjà faites
#    (2,5 kg, sinon 2, 1,25, 1, 0,5 kg) : presse à cuisses 3 × 12 à 52,5 kg → 55 kg (54 avant) ; sans pas reconnu (47,3 kg), arrondi d'avant ;
# 3. à l'ouverture d'un exercice (mode focus), la ligne active est entière au-dessus de la barre de repos, fermée ou ouverte, à 390 et 360 px ;
# 4. ✓ pâle dans le rond d'une série non validée ;
# 5. hors de l'onglet Séance, minuteur d'une ligne (temps restant, Passer), agrandi au toucher ; version complète sur l'onglet Séance ;
# 6. sous chaque bouton du ressenti, la conséquence pour la prochaine séance : c'est bien le conseil affiché la fois suivante ;
# 7. contrastes : texte en couleur d'accent, texte des boutons, texte blanc du dégradé de l'accueil, au moins 4,5:1 (6 couleurs, clair et sombre).
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/retours_seance.py
import os, re, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5163
DB = "/tmp/retours_seance_test.db"
for f in (DB, DB + "-wal", DB + "-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                       env=dict(os.environ, DB_PATH=DB, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

INIT = """localStorage.setItem('muscu-profil', JSON.stringify({version: 1, imported: true, created: '2026-10-01T10:00:00', updated: '2026-10-01T10:00:00', answers: {}, program: null}));
window.FonteApp = {keepScreenOn: on => 0};"""
# programme « Jambes » : presse à cuisses (3 × 10-12, repos 90 s) puis chest press
PROG = """async () => { const x = Object.values(EX).find(e => e.slug === 'pc').id, p = Object.values(EX).find(e => e.slug === 'chest-press').id;
  const r = await api('POST', '/api/workouts', {name: 'Jambes'});
  await api('PUT', '/api/workouts/' + r.id, {name: 'Jambes', items: [x, p], settings: {[x]: {sets: 3, target_min: 10, target_max: 12, rest: 90}}});
  await load(); return [r.id, x, p]; }"""
SEANCES = "async l => { for (const s of l) await api('POST', '/api/sessions', s); await load(); R(); }"
EFFACER = "async () => { TMskip(); for (const s of [...SESS]) await api('DELETE', '/api/sessions/' + s.id); localStorage.removeItem('muscu-draft'); localStorage.removeItem('muscu-extras'); localStorage.removeItem('muscu-xcur'); F = null; FOC = null; await load(); go('accueil'); }"
CONSEIL = "() => { const l = document.querySelector('.focus .sug'); return l ? l.textContent : ''; }"
MES = """() => { const r = document.querySelector('.focus .frow.act').getBoundingClientRect(),
  b = [...document.querySelectorAll('.bar, .fnavb')].filter(x => getComputedStyle(x).display !== 'none' && getComputedStyle(x).position === 'fixed').map(x => x.getBoundingClientRect()).sort((x, y) => x.top - y.top)[0],   // lot 1 : hors repos, barre « ‹ / Suivant › »
  t = document.querySelector('.topbar').getBoundingClientRect(); return {haut: r.top, bas: r.bottom, barre: b.top, barreH: b.height, titre: t.bottom}; }"""

def lum(rgb):
    c = [v / 255 for v in rgb]; c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]
def hexrgb(h):
    h = h.strip().lstrip('#'); h = ''.join(x * 2 for x in h) if len(h) == 3 else h
    return [int(h[i:i + 2], 16) for i in (0, 2, 4)]
def ctr(a, b):
    x, y = sorted([lum(hexrgb(a)), lum(hexrgb(b))], reverse=True); return (x + 0.05) / (y + 0.05)
def degrade(g1, g2, g3, n=60):   # pire contraste du blanc le long du dégradé de l'accueil (arrêts 0, 55 %, 100 %)
    a, b, c = hexrgb(g1), hexrgb(g2), hexrgb(g3); pire = 99
    for k in range(n + 1):
        t = k / n; p, q, u = (a, b, t / .55) if t <= .55 else (b, c, (t - .55) / .45)
        pire = min(pire, ctr('#fff', '#%02x%02x%02x' % tuple(round(p[i] + (q[i] - p[i]) * u) for i in range(3))))
    return pire

try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(INIT)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.clock.set_fixed_time("2026-10-22T10:00:00")
        pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector("#app .hero", timeout=8000)
        wid, x, p_ = pg.evaluate(PROG)
        def demarrer():
            pg.evaluate(f"go('accueil'); startFromHome({wid})"); time.sleep(.4)
        def serie(day, kg, reps=12, n=3, effort=3):
            return {"day": day, "workout_id": wid, "workout_name": "Jambes", "entries": [{"exercise_id": x, "sets": [[kg, reps]] * n, "effort": effort}]}

        # ======================================================= 1. onglet Esprits masqué : seulement dans la barre du bas
        barre = lambda: pg.inner_text(".tabbar"); menu = lambda: [t.strip() for t in pg.locator("#dnav button").all_text_contents()]
        inter = lambda: pg.get_attribute("#dtabs .sw2", "aria-checked") if pg.locator("#dtabs .sw2").count() else None
        ok("Esprits" in barre() and "Esprits" in menu(), "(témoin) au départ : Esprits dans la barre du bas et dans le menu")
        def clic(sel):   # ne bloque pas si l'élément manque (ancien code) : le contrôle suivant échoue
            if pg.locator(sel).count(): pg.click(sel, timeout=3000); time.sleep(.2)
        pg.evaluate("go('jeu'); JEU.sub('regles')"); time.sleep(.2)
        if pg.locator("button:has-text('Masquer de la barre du bas')").count(): clic("button:has-text('Masquer de la barre du bas')")
        else: pg.evaluate("JEU.opt('hide')"); time.sleep(.2)
        ok("Esprits" not in barre(), "masqué depuis les Réglages du jeu : plus d'onglet Esprits dans la barre du bas")
        ok("Esprits" in menu(), f"masqué : « Esprits » reste dans le menu de gauche {menu()}")
        pg.evaluate("openMenu()"); time.sleep(.3)
        ok(pg.locator("#dtabs").is_visible() and "Afficher l’onglet Esprits dans la barre du bas" in pg.inner_text("#dtabs") and inter() == "false",
           f"menu : interrupteur « Afficher l’onglet Esprits dans la barre du bas », sur « non » ({inter()})")
        hs = pg.locator("#dtabs .sw2").bounding_box() if pg.locator("#dtabs .sw2").count() else None
        ok(hs and hs["height"] >= 44 and hs["width"] >= 44, f"interrupteur de {hs and round(hs['width'])} × {hs and round(hs['height'])} px (44 au moins)")
        clic("#dnav button:has-text('Esprits')")
        ok(pg.evaluate("view") == "jeu" and pg.locator("#app .card").count() > 0, "menu > Esprits ouvre la collection même quand l'onglet est masqué")
        pg.evaluate("openMenu()"); time.sleep(.3); clic("#dtabs .sw2")
        ok("Esprits" in barre() and inter() == "true" and not pg.evaluate("JEU.hidden()"), f"interrupteur activé : l'onglet revient dans la barre du bas ({inter()})")
        if pg.evaluate("JEU.hidden()"): pg.evaluate("JEU.opt('hide')")   # ancien code : repartir de « visible » pour la suite
        clic("#dtabs .sw2")
        ok("Esprits" not in barre() and inter() == "false" and "Esprits" in menu(), "interrupteur coupé : onglet retiré de la barre, toujours dans le menu")
        pg.evaluate("closeMenu(); if (JEU.hidden()) JEU.opt('hide')"); time.sleep(.2); pg.evaluate("openMenu()"); time.sleep(.3)
        ok(inter() == "true" and "Esprits" in barre(), "l'interrupteur suit l'état changé depuis le jeu")
        pg.evaluate("closeMenu()")

        # ======================================================= 2. conseil de charge : toujours au pas du matériel
        pg.evaluate(SEANCES, [serie("2026-10-20", 52.5)])
        demarrer(); c = pg.evaluate(CONSEIL); v = [pg.input_value(f"#v{x}_{i}l") for i in range(3)]
        ok(c == "Conseil : 55 kg × 10" and v == ["55"] * 3, f"presse à cuisses, 3 × 12 à 52,5 kg : conseil 55 kg × 10 et lignes à 55 kg ({c!r}, {v})")
        pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
        pg.evaluate(SEANCES, [serie("2026-10-20", 47.3)])
        demarrer(); c = pg.evaluate(CONSEIL)
        ok(c == "Conseil : 48,3 kg × 10", f"(témoin) charges sans pas reconnu (47,3 kg) : arrondi d'avant le lot, 48,3 kg ({c!r})")
        pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
        # toutes les branches de loadTip, pour chaque pas : chaque charge proposée (texte et lignes préremplies) est un multiple du pas
        CAS = """([kgs, assisted]) => {
          const e = {id: 9999, kind: 'weight', assisted, sets: 3, target_min: 10, target_max: 12};
          const s = (day, sets, effort) => ({id: day, day, workout_id: 1, entries: [{exercise_id: 9999, sets, effort}]});
          const top = kgs.map(k => [k, 12]), low = kgs.map(k => [k, 8]), mid = kgs.map(k => [k, 10]), out = [];
          const go = (nom, ref, cs, ef) => { const r = loadTip(e, ref, cs, ef); out.push([nom, r[0], r[2].l]); };
          go('montée', [s('2026-10-20', top, 3)], {}, 3);
          go('facile', [s('2026-10-20', mid, 2)], {}, 2);
          go('dur', [s('2026-10-20', top, 4)], {}, 4);
          go('juste bien', [s('2026-10-20', mid, 3)], {}, 3);
          go('baisse', [s('2026-10-20', low, 3), s('2026-10-17', low, 3)], {}, 3);
          go('semaine légère', [s('2026-10-20', top, 3)], {light: {kind: 'allegee'}, periods: []}, 3);
          go('reprise', [s('2026-10-20', top, 3)], {light: {kind: 'reprise'}, periods: []}, 3);
          return out; }"""
        def multiples(txt, l, p):
            nb = [float(n.replace(',', '.')) for n in re.findall(r"(\d+(?:,\d+)?)(?=(?:-\d+(?:,\d+)?)? kg)", txt)] + ([l] if l is not None else [])
            return nb, all(abs(n / p - round(n / p)) < 1e-6 for n in nb)
        for kgs, p, nom in (([52.5, 52.5, 52.5], 2.5, "barre ou machine (52,5 kg)"), ([40, 40, 40], 2.5, "40 kg"), ([20, 22, 22], 2, "haltères (20 et 22 kg)"),
                            ([31.25, 31.25, 30], 1.25, "petits disques (31,25 kg)"), ([17, 18, 18], 1, "pas de 1 kg (17 et 18 kg)"), ([9, 9, 9.5], .5, "pas de 0,5 kg")):
            for assisted in (False, True):
                mauvais = []
                for cas, txt, l in pg.evaluate(CAS, [kgs, assisted]):
                    nb, bon = multiples(txt, l, p)
                    if not bon or not nb and cas not in ('juste bien', 'dur' if assisted else ''): mauvais.append((cas, txt, l))   # « même objectif » : aucune charge proposée
                ok(not mauvais, f"pas de {str(p).replace('.', ',')} kg · {nom}{' · assistance' if assisted else ''} : 7 conseils (montée, facile, dur, juste bien, baisse, semaine légère, reprise) au pas du matériel {mauvais}")
        r = pg.evaluate("loadTip({id: 9999, kind: 'weight', sets: 3, target_min: 10, target_max: 12}, [{id: 1, day: '2026-10-20', workout_id: 1, entries: [{exercise_id: 9999, sets: [[5, 8], [5, 8], [5, 8]]}]}, {id: 2, day: '2026-10-17', workout_id: 1, entries: [{exercise_id: 9999, sets: [[5, 8], [5, 8], [5, 8]]}]}], {}, 3)")
        ok(r[0] == "2,5 kg × 10", f"baisse depuis 5 kg (pas de 2,5) : un pas plus bas, 2,5 kg ({r[0]!r})")

        # ======================================================= 3. ouverture d'un exercice : ligne active entière au-dessus de la barre de repos
        for w, h in ((390, 844), (360, 780)):
            pg.set_viewport_size({"width": w, "height": h})
            pg.evaluate(EFFACER); pg.evaluate(SEANCES, [serie("2026-10-20", 52.5)])
            demarrer(); time.sleep(.3); m = pg.evaluate(MES)
            ok(m["bas"] <= m["barre"] - 4 and m["haut"] >= m["titre"], f"{w} px · ouverture, barre fermée ({m['barreH']:.0f} px) : ligne de {m['haut']:.0f} à {m['bas']:.0f}, barre à {m['barre']:.0f}")
            for _ in range(3): pg.click(".frow.act .tick"); time.sleep(.3)
            pg.evaluate("focMove(1)"); time.sleep(.4); m = pg.evaluate(MES)
            ok(pg.locator("#tm").count() == 1 and m["bas"] <= m["barre"] - 4 and m["haut"] >= m["titre"], f"{w} px · exercice suivant, repos en cours ({m['barreH']:.0f} px) : ligne de {m['haut']:.0f} à {m['bas']:.0f}, barre à {m['barre']:.0f}")
            pg.evaluate("exitFocus()")
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.evaluate(EFFACER); pg.evaluate(SEANCES, [serie("2026-10-20", 52.5)])

        # ======================================================= 4. ✓ pâle dans le rond d'une série non validée
        demarrer()
        # refonte, lot 1 (boutons V3) : coche grise dessinée, à 3:1 au moins contre le fond du rond (WCAG 1.4.11), au lieu du ✓ pâle
        ck = pg.evaluate("""() => { const t = document.querySelector('.frow.act .tick'), k = t && t.querySelector('svg.tk0'); if (!k) return null;
          const c = s => s.match(/[\\d.]+/g).slice(0, 3).map(Number); return [c(getComputedStyle(k).color), c(getComputedStyle(t).backgroundColor), parseFloat(getComputedStyle(k).opacity)]; }""")
        rk = (max(lum(ck[0]), lum(ck[1])) + .05) / (min(lum(ck[0]), lum(ck[1])) + .05) if ck else 0
        ok(ck is not None and rk >= 3 and ck[2] == 1, f"série non validée : coche grise dans le rond, {rk:.2f}:1 contre son fond")
        pg.click(".frow.act .tick"); time.sleep(.3)
        ok(pg.locator(".frow.ok .tick .tk0").count() == 0 and pg.locator(".frow.ok .tick svg").count() >= 1, "série validée : coche pleine, sans la coche grise")
        # pendant le repos qui suit, « Suivant › » reste accessible (dans la page, au-dessus de la barre de repos)
        sv = pg.locator(".focus button:has-text('Suivant ›')")
        ok(pg.locator(".bar #tm").count() == 1 and sv.count() == 1 and sv.is_visible() and sv.is_enabled(), "pendant un repos : « Suivant › » toujours accessible")

        # ======================================================= 5. minuteur compact hors de l'onglet Séance
        hS = pg.locator(".bar").bounding_box()["height"]
        ok(pg.locator(".bar button:has-text('−15 s')").count() == 1, f"onglet Séance : minuteur complet (−15 s, +15 s, Autre durée), {hS:.0f} px")
        pg.evaluate("exitFocus(); go('progres')"); time.sleep(.3)
        bb = pg.locator(".bar").bounding_box(); txt = pg.inner_text(".bar")
        ok(pg.locator(".bar").is_visible() and bb["height"] <= 70 and pg.locator("#tm").count() == 1 and "Passer" in txt and "−15 s" not in txt and "Ensuite" not in txt,
           f"Progrès : minuteur d'une ligne ({bb['height']:.0f} px) avec le temps restant ({pg.inner_text('#tm')}) et « Passer »")
        hb = min(pg.locator(".bar button").evaluate_all("l => l.map(b => b.getBoundingClientRect().height)"))
        ok(hb >= 44, f"minuteur compact : boutons de {hb:.0f} px (44 au moins)")
        clic(".rb-cx")
        ok(pg.locator(".bar button:has-text('−15 s')").count() == 1 and pg.locator(".bar").bounding_box()["height"] > 120, "toucher le minuteur compact l'agrandit (−15 s, +15 s…)")
        clic(".bar button:has-text('Réduire')")
        ok(pg.locator(".bar").bounding_box()["height"] <= 70, "« Réduire » le remet sur une ligne")
        pg.evaluate("go('historique')"); time.sleep(.2)
        ok(pg.locator(".bar").bounding_box()["height"] <= 70 and pg.locator("#tm").count() == 1, "Historique : minuteur compact aussi")
        pg.click(".bar button:has-text('Passer')"); time.sleep(.2)
        ok(not pg.locator(".bar").is_visible(), "« Passer » depuis le minuteur compact : repos arrêté")
        pg.evaluate("go('seance')"); time.sleep(.2); pg.evaluate("TM(60)"); time.sleep(.2)
        ok(pg.locator(".bar button:has-text('−15 s')").count() == 1, "(témoin) onglet Séance : version complète pendant un repos")
        pg.evaluate("TMskip()"); pg.evaluate(EFFACER)

        # ======================================================= 6. ressenti : la conséquence affichée est le conseil de la séance suivante
        for choix in ("Facile", "Juste bien", "Dur"):
            pg.evaluate(SEANCES, [serie("2026-10-20", 52.5, 12)])
            demarrer()
            for i in range(3): pg.fill(f"#v{x}_{i}l", "55"); pg.fill(f"#v{x}_{i}v", "10" if choix != "Juste bien" else "12" if i else "11")
            pg.evaluate("touched()")
            for _ in range(3): pg.click(".frow.act .tick"); time.sleep(.25)
            prevu = {t.splitlines()[0]: (t.splitlines()[1] if len(t.splitlines()) > 1 else "") for t in pg.locator(".feelb button").all_inner_texts()}
            pg.click(f".feelb button:has-text('{choix}')"); time.sleep(.2)
            pg.evaluate("TMskip(); saveSession()"); time.sleep(1); pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
            demarrer(); c = pg.evaluate(CONSEIL).replace("Conseil : ", "ensuite : ")   # lot 1 : « ensuite : … » sous chaque choix (avant : « → … »)
            ok(prevu.get(choix) == c, f"« {choix} » : annoncé {prevu.get(choix)!r}, conseil de la séance suivante {c!r} (tous : {prevu})")
            pg.evaluate("exitFocus()"); pg.evaluate(EFFACER)
        ok(len(set(prevu.values())) == 3, f"(témoin) les trois choix annoncent trois conséquences différentes {prevu}")

        # ======================================================= 7. contrastes (au moins 4,5:1)
        VARS = "() => { const s = getComputedStyle(document.documentElement), v = k => s.getPropertyValue(k).trim(); return ['--a', '--at', '--on', '--bg', '--c', '--g1', '--g2', '--g3'].map(v); }"
        pire = []
        for scheme in ("light", "dark"):
            pg.emulate_media(color_scheme=scheme)
            for acc in ("orange", "blue", "green", "violet", "red", "mono"):
                pg.evaluate(f"setAccent('{acc}')"); time.sleep(.05)
                a, at, on, bg, c, g1, g2, g3 = pg.evaluate(VARS)
                at = at or a   # avant ce lot, le texte en couleur d'accent utilisait --a
                mesures = {"texte d'accent sur le fond": ctr(at, bg), "texte d'accent sur une carte": ctr(at, c), "texte des boutons": ctr(on, a), "blanc sur le dégradé": degrade(g1, g2, g3)}
                bas = {k: round(v, 2) for k, v in mesures.items() if v < 4.5}
                ok(not bas, f"{scheme} · {acc} : contrastes ≥ 4,5:1 (minimum {min(mesures.values()):.2f}) {bas or ''}")
        pg.evaluate("setAccent('orange')")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        ctx.close(); b.close()
finally:
    srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
