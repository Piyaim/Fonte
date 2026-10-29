# SPDX-License-Identifier: AGPL-3.0-or-later
# Refonte, lot 2 : Progrès, Historique et détail d'une séance passée.
# 1. Données de la 0.6.1 (code sorti de Git par le tag v0.6.1, ou dossier ANCIEN_DIR), en mode serveur (SQLite, photos) et en mode
#    local (IndexedDB) : séances (dont un exercice fait deux fois, deux séances le même jour, anciennes notes de ressenti 1 et 5,
#    une note avec des caractères HTML), pesées, photos ; puis leurs exports.
#    a) le code actuel rouvre ces données SANS migration (même base, même profil de navigateur) : Historique, détail de chaque
#       séance (toutes les séries), Progrès (tuiles, pesées, photos) s'affichent ; les séances sont identiques ;
#    b) les exports de la 0.6.1 s'importent dans une appli neuve (modes serveur et local) et s'affichent de même.
# 2. Écrans (données d'essai de la maquette, horloge du 4 novembre 2026) :
#    Progrès sans séance (une phrase à la place des tuiles), tuiles dès la première séance, « 2/3 » puis « 4 » et
#    « cette semaine · objectif atteint » (jamais « 4/3 ») ; plus belle progression ; calendrier (seuls les jours de séance sont des
#    boutons, flèches de 48 px, cases de 44 px au moins à 360 px, ligne qui ouvre le détail) ; 5 records récents avec leur gain,
#    sans 1RM ; courbe : légende « 1RM estimé (≈) », chaque graduation porte sa valeur (la première et la dernière aux bords, axe du
#    poids d'au moins 5 kg), textes de 13 px au moins affichés à 360 px, tracé coupé en mouvement réduit ; période « 90 j » à l'encre ;
#    phrase des photos selon le mode ; Historique (lignes de 64 px groupées par mois, durée seulement si elle existe) ; détail
#    (« ‹ » revient à l'écran d'origine, durée absente d'une séance saisie après coup, Modifier puis Annuler revient au détail,
#    Supprimer revient à la liste) ; aucune action orange ; ni « manqué » ni « semaines d'affilée » ; aucune requête sortante.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot2.py
import base64, io, json, os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "v0.6.1"; P1, P2 = 5184, 5185
TMP = tempfile.mkdtemp(prefix="fonte-lot2-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

if os.environ.get("ANCIEN_DIR"): OLD = os.environ["ANCIEN_DIR"]
else:
    OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
    subprocess.run(f"git -C '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}' archive {TAG} server | tar -x -C '{OLD}'", shell=True, check=True)
VIEUX = open(os.path.join(OLD, "server", "static", "index.html"), encoding="utf-8").read()
ok("start_ts" not in VIEUX and "openSess" not in VIEUX, f"(le code de départ est celui de la 0.6.1 : ni durée de séance ni détail de séance) {OLD}")

PROCS = []
def serveur(dossier, dbf, port):
    os.makedirs(os.path.dirname(dbf), exist_ok=True)
    pr = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={port})"], cwd=dossier,
                          env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(pr); time.sleep(2.5)
    if pr.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {port} déjà pris ?)")
    return pr
def arreter(pr): pr.terminate(); pr.wait()

from PIL import Image
def jpeg(size, seed):
    bb = io.BytesIO(); Image.effect_noise((size, size), 40 + seed).convert("RGB").save(bb, "JPEG", quality=80); return base64.b64encode(bb.getvalue()).decode()
IMG, THUMB = jpeg(320, 1), jpeg(96, 2)
DONNEES = "".join(l for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lot2_donnees.js"), encoding="utf-8") if not l.startswith("//"))
PROFIL = "localStorage.setItem('muscu-profil', JSON.stringify({version: 1, imported: true, answers: {}}))"   # questionnaire sauté
# scénario joué par la page de la 0.6.1 (mêmes appels que l'interface)
SCENARIO = """async ([img, thumb]) => {
  const mk = o => api('POST', '/api/exercises', Object.assign({sets: 3, rest: 90}, o));
  const sq = (await mk({name: 'Squat ancien', grp: 'Jambes', kind: 'weight', target_min: 6, target_max: 10})).id;
  const pl = (await mk({name: 'Planche ancienne', grp: 'Abdos et gainage', kind: 'time', target_min: 30, target_max: 60})).id;
  const po = (await mk({name: 'Pompes anciennes', grp: 'Pectoraux', kind: 'reps', target_min: 8, target_max: 15})).id;
  const ve = (await mk({name: 'Vélo ancien', grp: 'Cardio', kind: 'cardio', target_min: 15, target_max: 30})).id;
  await api('POST', '/api/sessions', {day: '2026-10-12', workout_name: 'Séance A', notes: '', entries: [{exercise_id: sq, sets: [[60, 8], [60, 8]], effort: 1}, {exercise_id: pl, sets: [[null, 40], [null, 40]], effort: 5}, {exercise_id: ve, sets: [[6, 20]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_name: 'Séance B', notes: 'Note <b>&</b> "test"', entries: [{exercise_id: sq, sets: [[62.5, 6]], effort: 3}, {exercise_id: po, sets: [[null, 12], [5, 8]], effort: 2}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_name: 'Séance du soir', notes: '', entries: [{exercise_id: sq, sets: [[50, 10]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-16', workout_name: 'Séance A', notes: '', entries: [{exercise_id: sq, sets: [[62.5, 8]], effort: 4}, {exercise_id: sq, sets: [[65, 3]]}]});
  await api('POST', '/api/bodyweight', {kg: 66.5, day: '2026-10-12'}); await api('POST', '/api/bodyweight', {kg: 66.1, day: '2026-10-16'});
  const bl = s => new Blob([Uint8Array.from(atob(s), ch => ch.charCodeAt(0))], {type: 'image/jpeg'});
  for (const [day, note] of [['2026-10-12', 'de face'], ['2026-10-16', 'de profil']]) {
    const fd = new FormData(); fd.append('img', bl(img), 'a.jpg'); fd.append('thumb', bl(thumb), 't.jpg'); fd.append('day', day); fd.append('note', note);
    const r = await fetch('/api/photos', {method: 'POST', body: fd}); if (!r.ok) throw new Error('photo ' + r.status);
  }
  await load(); R(); return await api('GET', '/api/export'); }"""
NS, NSETS = 4, 11   # séances et séries (toutes lignes) du scénario
def sessions_sans_duree(ex):
    return [{k: v for k, v in s.items() if k not in ("start_ts", "end_ts")} for s in ex["sessions"]]

# ce que les écrans du lot 2 montrent pour ces données
AFFICHE = r"""() => { go('historique'); const L = document.querySelector('#app .hi');
  const rows = [...document.querySelectorAll('#app .hlist .lrow')].length, mois = [...document.querySelectorAll('#app h2.mon')].map(x => x.textContent);
  const det = SESS.map(s => { openSess(s.id, 'historique'); const d = document.querySelector('#app .sd');
    return {n: d.querySelectorAll('.ex').length, li: d.querySelectorAll('li').length, tags: [...d.querySelectorAll('.tag.feel')].map(t => t.textContent), notes: (d.querySelector('.card:last-of-type p') || {}).textContent || '', txt: d.innerText}; });
  go('progres'); const p = document.querySelector('#app .pg');
  return {rows, mois, det, tot: (p.querySelector('.sum div b') || {}).textContent, bw: p.querySelectorAll('.chart .lb').length}; }"""
def verifier(pg, M, photos):
    a = pg.evaluate(AFFICHE); pg.wait_for_timeout(600); a["ph"] = pg.locator("#app .phgrid button").count()   # photos : chargées à part
    ok(a["rows"] == NS and a["mois"] == ["Octobre 2026 · 4 séances"], f"{M} : Historique, 4 lignes sous « Octobre 2026 · 4 séances » {a['rows']} {a['mois']}")
    ok([d["n"] for d in a["det"]] == [3, 2, 1, 1] and sum(d["li"] for d in a["det"]) == NSETS, f"{M} : détail de chaque séance, tous les exercices et les {NSETS} séries {[(d['n'], d['li']) for d in a['det']]}")
    ok(a["det"][0]["tags"] == ["facile", "dur"], f"{M} : anciennes notes 1 et 5 affichées « facile » et « dur » {a['det'][0]['tags']}")
    ok('Note <b>&</b> "test"' in a["det"][1]["txt"], f"{M} : la note s'affiche telle quelle (caractères HTML échappés)")
    ok("60 kg × 8" in a["det"][0]["txt"] and "40 s" in a["det"][0]["txt"] and "20 min · niveau 6" in a["det"][0]["txt"] and "5 kg × 8" in a["det"][1]["txt"],
       f"{M} : séries en kg × reps, secondes, reps lestées et cardio")
    # exercice saisi deux fois dans la séance : les deux modes de stockage le rendent en une seule ligne (toutes ses séries) ; un record, une étiquette
    ok("Record battu" in a["det"][3]["txt"] and a["det"][3]["txt"].count("record") == 1 and a["det"][3]["li"] == 2, f"{M} : exercice saisi deux fois (62,5 × 8 puis 65 × 3) : une ligne, un record, une étiquette")
    ok(a["tot"] == str(NS) and a["bw"] == 1, f"{M} : Progrès, « {NS} séances au total », courbe des 2 pesées {a['tot']} {a['bw']}")
    if photos: ok(a["ph"] == 2, f"{M} : Progrès, les 2 photos {a['ph']}")

try:
    with sync_playwright() as p:
        b = p.chromium.launch(); outs = []
        def nouvelle(ctx, U):
            ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(U) or not r.request.url.startswith("http") else (outs.append(r.request.url), r.abort()))
            pg = ctx.pages[0] if ctx.pages else ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time("2026-10-20T19:00:00"); return pg, errs
        def ouvrir(pg, url):
            pg.goto(url); pg.wait_for_selector("#app", timeout=8000); pg.wait_for_timeout(500); pg.evaluate(PROFIL); pg.reload(); pg.wait_for_selector(".tabbar button", timeout=8000); pg.wait_for_timeout(300)

        # ------------------------------------------------------------ 1. la 0.6.1 crée des données (serveur et local), puis ses exports
        U1 = f"http://127.0.0.1:{P1}/"; DB1 = os.path.join(TMP, "a", "suivi.db"); NAV = os.path.join(TMP, "navigateur")
        old = serveur(os.path.join(OLD, "server"), DB1, P1)
        ctx = b.new_context(viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U1); ouvrir(pg, U1)
        exS = pg.evaluate(SCENARIO, [IMG, THUMB]); ctx.close()
        ok(len(exS["sessions"]) == NS and not errs, f"0.6.1, mode serveur : données créées et exportées {len(exS['sessions'])} {errs[:1]}")
        ctx = p.chromium.launch_persistent_context(NAV, viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U1); ouvrir(pg, U1 + "?local=1")
        exL = pg.evaluate(SCENARIO, [IMG, THUMB]); ctx.close()
        ok(len(exL["sessions"]) == NS and not errs, f"0.6.1, mode local : données créées et exportées {len(exL['sessions'])} {errs[:1]}")
        arreter(old)

        # ------------------------------------------------------------ 1a. le code actuel rouvre ces données, sans migration
        new = serveur(os.path.join(ROOT, "server"), DB1, P1)
        ctx = b.new_context(viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U1); ouvrir(pg, U1)
        verifier(pg, "rouvert, mode serveur", True)
        ok(sessions_sans_duree(pg.evaluate("api('GET', '/api/export')")) == sessions_sans_duree(exS), "rouvert, mode serveur : séances identiques (début et fin mis à part)")
        ok(not errs, f"rouvert, mode serveur : aucune erreur JavaScript {errs[:2]}"); ctx.close()
        ctx = p.chromium.launch_persistent_context(NAV, viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U1)
        pg.goto(U1 + "?local=1"); pg.wait_for_selector(".tabbar button", timeout=8000); pg.wait_for_timeout(400)
        verifier(pg, "rouvert, mode local", True)
        ok(sessions_sans_duree(pg.evaluate("api('GET', '/api/export')")) == sessions_sans_duree(exL), "rouvert, mode local : séances identiques (début et fin mis à part)")
        ok(not errs, f"rouvert, mode local : aucune erreur JavaScript {errs[:2]}"); ctx.close()
        arreter(new)

        # ------------------------------------------------------------ 1b. exports de la 0.6.1 importés dans une appli neuve
        U2 = f"http://127.0.0.1:{P2}/"; new = serveur(os.path.join(ROOT, "server"), os.path.join(TMP, "b", "suivi.db"), P2)
        for mode, ex, url in (("serveur", exS, U2), ("local", exL, U2 + "?local=1")):
            ctx = b.new_context(viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U2); ouvrir(pg, url)
            pg.evaluate("go('donnees')"); pg.fill("#bk", json.dumps(ex)); pg.click("#app button:has-text('Importer')"); pg.wait_for_timeout(1500)
            verifier(pg, f"export 0.6.1 importé, mode {mode}", False)
            ok(not errs, f"export 0.6.1 importé, mode {mode} : aucune erreur JavaScript {errs[:2]}"); ctx.close()
        arreter(new)

        # ------------------------------------------------------------ 2. écrans, données d'essai de la maquette
        DB3 = os.path.join(TMP, "c", "suivi.db"); new = serveur(os.path.join(ROOT, "server"), DB3, P2)
        ctx = b.new_context(viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U2); pg.clock.set_fixed_time("2026-11-04T19:30:00"); ouvrir(pg, U2)
        txt = lambda: pg.inner_text("#app")
        pg.evaluate("go('progres')"); t = txt()
        ok("Ta première séance apparaîtra ici." in t and not pg.locator("#app .sum").count() and "0/3" not in t, "Progrès sans séance : la phrase, pas de tuiles à zéro")
        ok("Tes records apparaîtront ici" in t and "Après ta première séance, ta courbe démarre ici." in t and "Aucune séance ce mois-ci." in t, "Progrès sans séance : records, courbe et mois en une phrase")
        ok(pg.locator("#app details.opt summary:has-text('Suivre ton poids')").count() == 1 and not pg.locator("#app details.opt[open]").count(), "sans pesée : « Suivre ton poids · facultatif », fermé")
        ok("Gardées sur ton serveur Fonte, envoyées nulle part ailleurs." in t and "ce téléphone" not in t, "version serveur : les photos sont sur le serveur")
        pg.evaluate("go('historique')"); ok("Aucune séance enregistrée." in txt(), "Historique sans séance : une phrase")
        # une séance : les tuiles apparaissent
        pg.evaluate("""async () => { const e = await api('POST', '/api/exercises', {name: 'Essai', grp: 'Jambes', kind: 'weight', sets: 3, target_min: 8, target_max: 12, rest: 90});
          await api('POST', '/api/sessions', {day: '2026-11-03', workout_name: 'Séance A', entries: [{exercise_id: e.id, sets: [[40, 10]]}]}); await load(); go('progres'); }""")
        ok(pg.locator("#app .sum div").count() == 3 and "Ta première séance" not in txt() and "1/3" in txt(), "première séance : les 3 tuiles apparaissent (« 1/3 »)")
        ctx.close(); arreter(new); os.remove(DB3)
        new = serveur(os.path.join(ROOT, "server"), DB3, P2)
        ctx = b.new_context(viewport={"width": 390, "height": 844}, reduced_motion="no-preference"); pg, errs = nouvelle(ctx, U2); pg.clock.set_fixed_time("2026-11-04T19:30:00"); ouvrir(pg, U2)
        pg.evaluate(DONNEES, False)
        pg.evaluate("go('progres')"); pg.wait_for_timeout(300); t = txt()
        tiles = pg.eval_on_selector_all("#app .sum div", "l => l.map(d => d.innerText.replace(/\\n/g, ' '))")
        ok(tiles == ["16 séances au total", "2/3 cette semaine", "8 048 kg cette semaine"], f"tuiles : 16, 2/3, kg de la semaine {tiles}")
        ok("+10 s" in t and "Ta plus belle progression depuis le 21 septembre" in t, "plus belle progression : Planche +10 s (le plus grand pourcentage)")
        cal = pg.evaluate("""() => { const c = document.querySelector('#app .cal'); const r = el => el.getBoundingClientRect();
          return {btn: [...c.querySelectorAll('button')].map(x => x.textContent), span: [...c.querySelectorAll('span.cd')].length,
                  fl: [...document.querySelectorAll('#app .calh button')].map(x => [r(x).width, r(x).height]), sel: (document.querySelector('#app .daysel') || {}).innerText || ''}; }""")
        ok(cal["btn"] == ["2", "4"] and cal["span"] == 28, f"calendrier : seuls les jours de séance (2 et 4 novembre) sont des boutons {cal['btn']} {cal['span']}")
        ok(all(w >= 48 and h >= 48 for w, h in cal["fl"]), f"flèches du mois de 48 × 48 au moins {cal['fl']}")
        ok("Séance B · aujourd’hui" in cal["sel"] and "47 min · 15 séries · 4 080 kg" in cal["sel"] and "2 séances ce mois-ci" in t, f"jour choisi : aujourd'hui, une ligne {cal['sel']!r}")
        pg.click("#app .daysel .lrow"); pg.wait_for_timeout(200)
        ok(pg.locator("#app .sd").count() == 1 and pg.get_attribute("#tb-back", "aria-label") == "Retour à Progrès" and pg.is_hidden("#menu-btn"), "la ligne ouvre le détail ; « ‹ » à la place du menu")
        hd = [pg.inner_text("#ttl"), pg.inner_text(".tabbar button.on")]
        ok(hd == ["Progrès", "Progrès"], f"détail ouvert depuis Progrès : titre et onglet « Progrès » {hd}")
        pg.click("#app .sd button:has-text('Modifier')"); pg.wait_for_timeout(150); pg.evaluate("cancelEdit()"); pg.wait_for_timeout(150)
        ok(pg.locator("#app .sd").count() == 1 and pg.inner_text("#ttl") == "Progrès", "Modifier puis Annuler : retour au détail, toujours depuis Progrès")
        pg.click("#tb-back"); pg.wait_for_timeout(200); ok(pg.evaluate("view") == "progres" and pg.is_visible("#menu-btn"), "« ‹ » revient à Progrès")
        pg.evaluate("calMove(-1)"); pg.click("#app .cal button.cd >> nth=0"); pg.wait_for_timeout(150)
        ok("Séance B · ven. 2 oct." in pg.inner_text("#app .daysel"), f"autre jour choisi : la séance de ce jour {pg.inner_text('#app .daysel')!r}")
        pg.evaluate("CAL = null; R()")
        recs = pg.eval_on_selector_all("#app .recl", "l => l.map(r => r.innerText.replace(/\\n/g, ' | '))")
        ok(len(recs) == 5 and recs[0].startswith("Dead bug | 10 reps") and recs[0].endswith("+1 rep") and all("+" in r for r in recs), f"5 records récents, avec leur gain {recs}")
        rc = pg.inner_text("#app .pg section.card:has(.recl)")
        ok("1RM" not in rc, "aucun 1RM dans les records")
        ok("1RM estimé (≈)" in t and pg.locator("#app details.det:not([open]) summary:has-text('Détails')").count() == 1, "courbe : légende « 1RM estimé (≈) », explication dans « Détails » fermé")
        def axes():
            return pg.evaluate("""() => [...document.querySelectorAll('#app .chart')].map(c => { const L = [...c.querySelectorAll('line.gr')].map(l => +l.getAttribute('y1'));
              const T = [...c.querySelectorAll('text')].filter(x => x.getAttribute('text-anchor') === 'end' && !x.classList.contains('lv') && +x.getAttribute('x') < 60);
              return {lignes: L, valeurs: T.map(x => x.textContent), haut: Math.min(...L), bas: Math.max(...L), taille: c.querySelector('text').getBoundingClientRect().height,
                      px: parseFloat(getComputedStyle(c.querySelector('text')).fontSize) * c.getBoundingClientRect().width / 320}; })""")
        ax = axes()
        ok(len(ax) == 2 and all(len(a["lignes"]) == len(a["valeurs"]) and a["haut"] == 18 and a["bas"] == 144 for a in ax), f"chaque graduation porte sa valeur, la première et la dernière aux bords de la courbe {[(a['valeurs'], a['haut'], a['bas']) for a in ax]}")
        v = [float(x.replace(",", ".")) for x in ax[1]["valeurs"]]
        ok(v == [72, 74, 76, 78], f"poids de corps : axe 72-78, rien d'étiqueté au-dessus de 76 sans valeur {ax[1]['valeurs']}")
        db = pg.evaluate("Object.values(EX).find(e => e.name === 'Dead bug' && SESS.some(s => setsOf(s, e.id))).id")
        pg.evaluate(f"PGEX = {db}; R()"); vd = axes()[0]["valeurs"]
        ok(vd and all("," not in x for x in vd), f"reps : graduations entières, pas de demi-répétition {vd}")
        pg.evaluate("PGEX = null; R()")
        chips = pg.evaluate("""() => { const c = document.querySelector('#app .chip[aria-pressed="true"]'); return [c.textContent, getComputedStyle(c).backgroundColor, getComputedStyle(document.querySelector('#app .cal .cd.on i')).backgroundColor]; }""")
        ok(chips[0] == "90 j" and chips[1] != chips[2], f"période « 90 j » choisie, à l'encre et non à l'accent {chips}")
        pg.evaluate("go('progres')"); anim = pg.evaluate("getComputedStyle(document.querySelector('#app .chart .l1')).animationName")
        ok(anim == "trace", f"la courbe se trace (animation « trace ») {anim}")
        pg.emulate_media(reduced_motion="reduce"); pg.evaluate("ANIMK = null; R()")
        anim = pg.evaluate("getComputedStyle(document.querySelector('#app .chart .l1')).animationName"); pg.emulate_media(reduced_motion="no-preference")
        ok(anim == "none", f"mouvement réduit : pas de tracé animé {anim}")
        ok(pg.locator("#app .go:visible").count() == 0, "Progrès : aucune action orange")
        pg.set_viewport_size({"width": 360, "height": 780}); pg.evaluate("R()")
        ax = axes(); cell = pg.evaluate("Math.min(...[...document.querySelectorAll('#app .cal button.cd')].map(b => Math.min(b.getBoundingClientRect().width, b.getBoundingClientRect().height)))")
        ok(all(a["px"] >= 13 for a in ax), f"360 px : textes des courbes de 13 px au moins à l'écran {[round(a['px'], 1) for a in ax]}")
        ok(cell >= 44, f"360 px : jours de séance de 44 px au moins {cell}")
        ok(pg.evaluate("document.documentElement.scrollWidth") <= 360, "360 px : aucun défilement horizontal")
        note = pg.evaluate("(() => { const i = document.getElementById('ph-note'); return [i.getBoundingClientRect().width, i.closest('.card').getBoundingClientRect().width]; })()")
        ok(note[0] > note[1] - 40, f"360 px : champ « Note (facultatif) » sur toute sa ligne {note}")
        pg.set_viewport_size({"width": 390, "height": 844})
        # Historique
        pg.evaluate("go('historique')"); pg.wait_for_timeout(150)
        h = pg.evaluate("""() => ({mois: [...document.querySelectorAll('#app h2.mon')].map(x => x.textContent), haut: Math.min(...[...document.querySelectorAll('#app .hlist .lrow')].map(r => r.getBoundingClientRect().height)),
          l: [...document.querySelectorAll('#app .hlist .lrow')].map(r => r.innerText.replace(/\\n/g, ' | '))})""")
        ok(h["mois"] == ["Novembre 2026 · 2 séances", "Octobre 2026 · 9 séances", "Septembre 2026 · 5 séances"], f"Historique : groupé par mois {h['mois']}")
        ok(h["haut"] >= 64, f"lignes de 64 px au moins {h['haut']}")
        l9 = [x for x in h["l"] if x.startswith("9 | ")]
        ok(l9 and "min" not in l9[0] and "15 séries" in l9[0], f"séance saisie après coup : pas de durée, sans commentaire {l9}")
        ok(any("3 records" in x for x in h["l"]) and pg.locator("#app .go:visible").count() == 0, "étiquette « 3 records » ; aucune action orange")
        pg.evaluate("window.scrollTo(0, 400)"); pg.click("#app .hlist .lrow:has-text('23') >> nth=0"); pg.wait_for_timeout(150)
        d = pg.inner_text("#app")
        ok("Vendredi 23 octobre" in d and "3 records battus" in d and "Avant : 27,5 kg × 12" in d and "46 min" in d and "kg soulevés" in d, "détail : date, tuiles, records battus avec « Avant : … »")
        ok("+1 rep" in d and "juste bien" in d and "20 min · niveau 7" in d and "S1" in d and "Épaule un peu raide" in d, "détail : gain de reps en gris, ressenti, cardio, séries, notes")
        ok(pg.locator("#app .sd .tag.rec").count() == 3 and pg.locator("#app .go:visible").count() == 0, "détail : 3 étiquettes « record », aucune action orange")
        dang = pg.evaluate("(() => { const b = [...document.querySelectorAll('#app .sd button')].find(x => x.textContent === 'Supprimer la séance'); return b && b.classList.contains('danger') && getComputedStyle(b).backgroundColor; })()")
        dc = pg.evaluate("(() => { const b = [...document.querySelectorAll('#app .sd button')].find(x => x.textContent === 'Supprimer la séance'), t = document.createElement('i'); t.style.color = 'var(--danger)'; document.body.append(t); const c = getComputedStyle(t).color; t.remove(); return [getComputedStyle(b).color, c]; })()")
        ok(dang in ("rgba(0, 0, 0, 0)", "transparent") and dc[0] == dc[1], f"« Supprimer la séance » en lien rouge (--danger), sans fond {dang} {dc}")
        pg.click("#tb-back"); pg.wait_for_timeout(150)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)"); pg.click("#app .hlist .lrow >> nth=-1"); pg.wait_for_timeout(150)
        ok("Lundi 21 septembre" in pg.inner_text("#app"), "dernière ligne de la liste : séance du 21 septembre")
        pg.click("#tb-back"); pg.wait_for_timeout(150); y = pg.evaluate("[HSCROLL, window.scrollY]"); ok(pg.locator("#app .hlist").count() == 3 and y[1] > 0 and y[0] == y[1], f"« ‹ » revient à la liste, à la même place {y}")
        pg.click("#app .hlist .lrow:has-text('16') >> nth=0"); pg.wait_for_timeout(150)
        ok("durée" not in pg.inner_text("#app .sum") and pg.locator("#app .sd .sum div").count() == 2, "séance saisie après coup : pas de tuile durée")
        sid = pg.evaluate("HDET")
        pg.click("#app .sd button:has-text('Modifier')"); pg.wait_for_timeout(200)
        ok(pg.evaluate("view") == "seance" and pg.evaluate("F && F.mode") == "edit", "« Modifier » ouvre la modification")
        pg.evaluate("cancelEdit()"); pg.wait_for_timeout(150); ok(pg.evaluate("HDET") == sid and pg.locator("#app .sd").count() == 1, "Annuler revient au détail de la séance")
        pg.click("#app .sd button:has-text('Supprimer la séance')"); pg.wait_for_timeout(800)
        r = pg.evaluate("[SESS.length, document.querySelectorAll('#app .hlist').length, HDET]")
        ok(r == [15, 3, None] and pg.is_visible("#menu-btn"), f"Supprimer (après confirmation) revient à la liste {r}")
        # fiche d'exercice (écran Exercices, non refait) : sa courbe utilise la même fonction et reste dessinée
        pg.evaluate("go('exercices'); openEx(Object.values(EX).find(e => e.name === 'Presse à cuisses' && SESS.some(s => setsOf(s, e.id))).id)"); pg.wait_for_timeout(200)
        fc = pg.evaluate("[[...document.querySelectorAll('#app .chart polyline')].map(l => l.getAttribute('class')), document.getElementById('app').innerText.includes('undefined')]")
        ok(fc == [["l2", "l1"], False], f"fiche d'exercice : courbe et 1RM dessinés, aucun « undefined » {fc}")
        tout = "".join(pg.evaluate(f"go('{v}'), document.getElementById('app').innerText") for v in ("progres", "historique"))
        ok("manqu" not in tout.lower() and "affilée" not in tout, "ni « manqué » ni « semaines d'affilée »")
        # au-delà de l'objectif : « 4 », jamais « 4/3 »
        pg.evaluate("""async () => { const s = SESS[SESS.length - 1]; for (const day of ['2026-11-03', '2026-11-04']) await api('POST', '/api/sessions', {day, workout_name: s.workout_name, entries: s.entries}); await load(); go('progres'); }""")
        tiles = pg.eval_on_selector_all("#app .sum div", "l => l.map(d => d.innerText.replace(/\\n/g, ' '))")
        ok(tiles[1] == "4 cette semaine · objectif atteint" and "4/3" not in txt(), f"4 séances cette semaine : « 4 », « cette semaine · objectif atteint » {tiles}")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}"); ctx.close()
        # appli (mode local) : photos sur le téléphone
        ctx = b.new_context(viewport={"width": 390, "height": 844}); pg, errs = nouvelle(ctx, U2); ouvrir(pg, U2 + "?local=1"); pg.evaluate("go('progres')")
        ok("Gardées sur ce téléphone, envoyées nulle part." in txt() and "serveur" not in txt(), "appli (mode local) : les photos restent sur le téléphone")
        ok(not errs, f"mode local : aucune erreur JavaScript {errs[:2]}"); ctx.close()
        ok(not outs, f"aucune requête sortante {outs[:3]}")
        arreter(new)
        b.close()
finally:
    for pr in PROCS:
        if pr.poll() is None: pr.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
