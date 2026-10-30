# SPDX-License-Identifier: AGPL-3.0-or-later
# Refonte, lot 3 : questionnaire, Exercices, fiche, formulaire, Programmes, Zones (maquette validée le 29/10/2026).
# 1. Données de la 0.7.1 (code sorti de Git par le tag v0.7.1, ou dossier ANCIEN_DIR), modes serveur et local : exercice créé et
#    modifié, programme réglé (5 × 3-5, repos 180 s), séances, exercice archivé, jeu. Le code actuel les rouvre sans perte (export
#    identique, même après avoir parcouru tous les écrans du lot 3) et les affiche (liste, fiche, réglages du programme, archivés).
#    L'export de la 0.7.1 s'importe dans une appli neuve à l'identique.
# 2. Questionnaire parcouru à l'écran (390 et 360 px) : aucune réponse de santé cochée d'avance, « Suivant » grisé jusqu'à la
#    7e réponse ; espace insécable avant « ? », « ! », « ; » et aucun de ces signes en début de ligne, sur les 17 questions,
#    le résumé, la confirmation et « Programme prêt ».
# 3. Écrans du lot 3 × 6 couleurs du menu × clair et sombre × 390 et 360 px : une action orange au plus, cibles de 44 × 44 px,
#    texte 4,5:1 et 13 px au moins, aucun débordement ; « Retirer » et les autres liens « danger » : sans fond, avec une icône, à 20 au
#    moins (écart CIEDE2000) de --a et --at ; numéros de « Comment le faire » dans la couleur d'accent (--at), jamais en framboise.
# 4. Changements en attente (Programmes) : gardés en changeant de programme, d'onglet, après un rechargement de la page, et après
#    la fermeture complète du navigateur puis sa réouverture (même profil de navigateur) ;
#    point sur le programme modifié ; séance lancée depuis ce programme = version enregistrée, avec une ligne neutre ;
#    « Annuler » efface, « Enregistrer » applique. Aucun texte ne promet qu'ils survivent à la fermeture de l'appli.
# 5. Aucune erreur JavaScript, aucune requête sortante.
# Témoins : tests/lot3_temoins.py (une règle faussée à la fois dans une copie du code, FONTE_ROOT) : chaque contrôle doit échouer.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot3.py
import json, os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAG = "v0.7.1"; P1, P2 = 5191, 5192
PARTIES = os.environ.get("LOT3_PARTIES", "1234")   # témoins : seulement les parties utiles
ACC_T = os.environ.get("LOT3_ACC")
TMP = tempfile.mkdtemp(prefix="fonte-lot3-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

if os.environ.get("ANCIEN_DIR"): OLD = os.environ["ANCIEN_DIR"]
else:
    OLD = os.path.join(TMP, "ancien"); os.makedirs(OLD)
    subprocess.run(f"git -C '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}' archive {TAG} server | tar -x -C '{OLD}'", shell=True, check=True)
VIEUX = open(os.path.join(OLD, "server", "static", "index.html"), encoding="utf-8").read()
ok("muscu-prog-attente" not in VIEUX and "s.pend" in open(os.path.join(OLD, "server", "static", "jeu.js"), encoding="utf-8").read(), f"(le code de départ est celui de la 0.7.1, sans le lot 3) {OLD}")

PROCS = []
def serveur(dossier, dbf, port):
    os.makedirs(os.path.dirname(dbf), exist_ok=True)
    pr = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={port})"], cwd=dossier,
                          env=dict(os.environ, DB_PATH=dbf, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(pr); time.sleep(2.5)
    if pr.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {port} déjà pris ?)")
    return pr
def arreter(pr): pr.terminate(); pr.wait()

PROFIL = "localStorage.setItem('muscu-profil', JSON.stringify({version: 1, imported: true, answers: {}}))"   # questionnaire sauté
SCENARIO = """async () => {
  const mk = o => api('POST', '/api/exercises', Object.assign({sets: 3, rest: 90}, o));
  const ti = (await mk({name: 'Tirage perso', grp: 'Dos', kind: 'weight', sets: 4, target_min: 6, target_max: 8, rest: 120})).id;
  const vi = (await mk({name: 'Vieil exercice', grp: 'Jambes', kind: 'weight', target_min: 8, target_max: 12})).id;
  const st = await api('GET', '/api/state'), a = st.exercises.find(e => e.slug === 'developpe-couche') || st.exercises[0];
  await api('PUT', '/api/exercises/' + a.id, Object.assign({}, a, {tip: 'mon astuce'}));
  const w = await api('POST', '/api/workouts', {name: 'Mon programme'});
  await api('PUT', '/api/workouts/' + w.id, {name: 'Mon programme', items: [a.id, ti, vi], settings: {[ti]: {sets: 5, target_min: 3, target_max: 5, rest: 180}}});
  await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: w.id, notes: 'première', entries: [{exercise_id: ti, sets: [[30, 5], [30, 5]], effort: 3}, {exercise_id: vi, sets: [[50, 10]]}]});
  await api('POST', '/api/sessions', {day: '2026-10-14', workout_id: w.id, entries: [{exercise_id: ti, sets: [[32.5, 4], [32.5, 4]], effort: 4}]});
  await api('POST', '/api/exercises/' + vi + '/archive', {archived: true});
  await load(); const s = SESS[SESS.length - 1]; if (window.JEU) { JEU.award(s.id); }
}"""
RELEVE = """async () => { const ex = await (await fetch('/api/export')).json(); delete ex.exported_at;
  return {export: ex, jeu: localStorage.getItem('muscu-jeu'), profil: localStorage.getItem('muscu-profil')}; }"""
REPONSES = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
            "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non",
            "sante": {k: False for k in ("poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre")}}
BROUILLON = "([a, mode, i]) => { localStorage.removeItem('muscu-profil'); localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode, i, redo: false})); }"
OUVRIR = "document.querySelectorAll('#app details').forEach(d => d.open = true)"
ACC = ACC_T.split(",") if ACC_T else ["orange", "blue", "green", "violet", "red", "mono"]

# mesures sur l'écran affiché (#app, barre du haut) ; les replis sont ouverts avant
MESURE = r"""() => {
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126 * f(m[0]) + .7152 * f(m[1]) + .0722 * f(m[2]); };
  const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const mix = (fg, bg) => { const f = fg.match(/[\d.]+/g).map(Number), b = bg.match(/[\d.]+/g).map(Number), a = f[3] ?? 1; return `rgb(${[0, 1, 2].map(i => Math.round(f[i] * a + b[i] * (1 - a))).join(',')})`; };
  const opa = el => { let o = 1; for (let e = el; e && e.nodeType === 1; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor, m = c.match(/[\d.]+/g); if (m && (m[3] === undefined || +m[3] > .5)) return c; } return getComputedStyle(document.body).backgroundColor; };
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && opa(el) > .05 && !el.closest('details:not([open]) > :not(summary)'); };
  const lab = c => { const [r, g, b] = c.match(/[\d.]+/g).slice(0, 3).map(v => { v /= 255; return v <= .04045 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; });
    const t = v => v > .008856 ? Math.cbrt(v) : 7.787 * v + 16 / 116, X = t((r * .4124 + g * .3576 + b * .1805) / .95047), Y = t(r * .2126 + g * .7152 + b * .0722), Z = t((r * .0193 + g * .1192 + b * .9505) / 1.08883);
    return [116 * Y - 16, 500 * (X - Y), 200 * (Y - Z)]; };
  const de = (p, q) => {   // écart de couleur CIEDE2000
    const [L1, a1, b1] = lab(p), [L2, a2, b2] = lab(q), rad = Math.PI / 180, Cm = (Math.hypot(a1, b1) + Math.hypot(a2, b2)) / 2, G = .5 * (1 - Math.sqrt(Cm ** 7 / (Cm ** 7 + 25 ** 7)));
    const A1 = a1 * (1 + G), A2 = a2 * (1 + G), C1 = Math.hypot(A1, b1), C2 = Math.hypot(A2, b2), h1 = (Math.atan2(b1, A1) / rad + 360) % 360, h2 = (Math.atan2(b2, A2) / rad + 360) % 360;
    let dh = h2 - h1; if (Math.abs(dh) > 180) dh -= 360 * Math.sign(dh);
    const dH = 2 * Math.sqrt(C1 * C2) * Math.sin(dh / 2 * rad), Lm = (L1 + L2) / 2, Cp = (C1 + C2) / 2; let hm = (h1 + h2) / 2; if (Math.abs(h1 - h2) > 180) hm += 180;
    const T = 1 - .17 * Math.cos((hm - 30) * rad) + .24 * Math.cos(2 * hm * rad) + .32 * Math.cos((3 * hm + 6) * rad) - .2 * Math.cos((4 * hm - 63) * rad);
    const SL = 1 + .015 * (Lm - 50) ** 2 / Math.sqrt(20 + (Lm - 50) ** 2), SC = 1 + .045 * Cp, SH = 1 + .015 * Cp * T, RT = -2 * Math.sqrt(Cp ** 7 / (Cp ** 7 + 25 ** 7)) * Math.sin(60 * Math.exp(-(((hm - 275) / 25) ** 2)) * rad);
    const x = (L2 - L1) / SL, y = (C2 - C1) / SC, z = dH / SH; return Math.sqrt(x * x + y * y + z * z + RT * y * z); };
  const col = v => { const i = document.createElement('i'); i.style.color = v; document.body.appendChild(i); const c = getComputedStyle(i).color; i.remove(); return c; };
  const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
  const A = col(css('--a')), AT = col(css('--at')), DG = col(css('--danger'));
  const out = {txt: [], cible: [], orange: 0, deb: 0, danger: [], typo: [], steps: [], mots: []};
  const app = document.getElementById('app');
  out.deb = Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth);
  const wk = document.createTreeWalker(app, NodeFilter.SHOW_TEXT);
  for (let n; (n = wk.nextNode());) {
    const x = n.textContent; if (!x.trim()) continue; const el = n.parentElement; if (!vis(el) || el.closest('svg, style, script')) continue;
    if (!el.closest('button[disabled]')) {
      const s = getComputedStyle(el), bg = bgOf(el), o = opa(el), r = ratio(o < 1 ? mix(s.color.replace(/rgba?\(([^)]+)\)/, (m, v) => `rgba(${v.split(',').slice(0, 3).join(',')},${o})`), bg) : mix(s.color, bg), bg);
      if (r < 4.5) out.txt.push([x.trim().slice(0, 30), +r.toFixed(2)]);
      if (parseFloat(s.fontSize) < 12.95) out.txt.push([x.trim().slice(0, 30), 'taille ' + s.fontSize]);
    }
    if (!/[?!;]/.test(x)) continue;
    if (/[ \t\n][?!;]/.test(x)) out.typo.push('espace sécable : ' + x.trim().slice(-40));
    for (let i = 1; i < x.length; i++) {
      if (!'?!;'.includes(x[i])) continue; let j = i - 1; while (j > 0 && /\s/.test(x[j])) j--;
      const ra = document.createRange(); ra.setStart(n, i); ra.setEnd(n, i + 1); const rb = document.createRange(); rb.setStart(n, j); rb.setEnd(n, j + 1);
      const P = ra.getClientRects()[0], Q = rb.getClientRects()[0]; if (P && Q && P.top > Q.top + 2) out.typo.push('« ' + x[i] + ' » en début de ligne : ' + x.trim().slice(-40));
    }
  }
  for (const el of document.querySelectorAll('#app button, #app input, #app select, #app textarea, #app summary, #app a, .topbar button')) {
    if (!vis(el)) continue;
    const r = el.getBoundingClientRect(); if (r.width < 43.5 || r.height < 43.5) out.cible.push([(el.innerText || el.getAttribute('aria-label') || el.tagName).trim().slice(0, 30), Math.round(r.width), Math.round(r.height)]);
    if (el.tagName === 'BUTTON' && getComputedStyle(el).backgroundColor === A) out.orange++;
  }
  for (const el of app.querySelectorAll('.btn-d, .danger')) {
    if (!vis(el)) continue; const s = getComputedStyle(el), m = s.backgroundColor.match(/[\d.]+/g), nm = el.innerText.trim().slice(0, 24);
    if (m && (m[3] === undefined || +m[3] > 0)) out.danger.push(nm + ' : fond');
    if (!el.querySelector('svg')) out.danger.push(nm + ' : sans icône');
    const d = Math.min(de(s.color, A), de(s.color, AT)); if (d < 20) out.danger.push(nm + ' : écart ' + d.toFixed(1));
  }
  for (const li of app.querySelectorAll('.steps li')) { const c = getComputedStyle(li, '::before').color; if (c !== AT || de(c, DG) < 20) out.steps.push(c); }
  const t = app.innerText; if (/manqu[ée]/i.test(t)) out.mots.push('manqué'); if (/semaines? d.affilée/i.test(t)) out.mots.push("semaines d'affilée");
  out.n = {steps: app.querySelectorAll('.steps li').length, danger: [...app.querySelectorAll('.btn-d, .danger')].filter(vis).length};
  return out;
}"""

externes = []; errs = []   # errs : aussi quand seule une partie tourne (témoins)
HOTES = tuple(f"http://{h}:{p}/" for h in ("127.0.0.1", "localhost") for p in (P1, P2))
try:
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        def surveiller(ctx):
            ctx.route("**/*", lambda r: r.continue_() if not r.request.url.startswith("http") or r.request.url.startswith(HOTES) else (externes.append(r.request.url), r.abort()))
            ctx.on("dialog", lambda d: d.accept())

        # ============================================================ 1. données de la 0.7.1 rouvertes par le code actuel
        if "1" in PARTIES:
            dbf = os.path.join(TMP, "donnees", "fonte.db"); NAV = os.path.join(TMP, "navigateur")
            MODES = {"serveur": f"http://127.0.0.1:{P1}/", "local": f"http://localhost:{P1}/?local=1"}
            errs = []
            def nav_persist():
                ctx = pw.chromium.launch_persistent_context(NAV, viewport={"width": 390, "height": 844}, service_workers="block"); surveiller(ctx); return ctx
            def ouvrir(ctx, mode):
                pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(f"{mode}: {e}"))
                pg.goto(MODES[mode]); pg.wait_for_selector(".tabbar button", timeout=10000); pg.wait_for_timeout(500); return pg
            pr = serveur(os.path.join(OLD, "server"), dbf, P1); ctx = nav_persist(); avant = {}
            for mode in MODES:
                pg = ctx.new_page(); pg.add_init_script(PROFIL); pg.goto(MODES[mode]); pg.wait_for_selector(".tabbar button", timeout=10000)
                pg.evaluate(SCENARIO); avant[mode] = pg.evaluate(RELEVE); pg.close()
            ctx.close(); arreter(pr)
            ok(all(len(avant[m]["export"]["sessions"]) == 2 and any(e["archived"] for e in avant[m]["export"]["exercises"]) for m in MODES), "0.7.1 : 2 séances, programme réglé, exercice archivé (modes serveur et local)")
            pr = serveur(os.path.join(ROOT, "server"), dbf, P1); ctx = nav_persist()
            for mode in MODES:
                pg = ouvrir(ctx, mode)
                ok(pg.evaluate(RELEVE) == avant[mode], f"mode {mode} : données de la 0.7.1 rouvertes à l'identique (export, jeu, profil)")
                pg.evaluate("go('exercices')"); t = pg.inner_text("#app")
                ok("Tirage perso" in t and "Vieil exercice" not in t, f"mode {mode} : Exercices, exercice créé visible, exercice archivé caché")
                pg.click("button:has-text('Afficher les exercices archivés')"); ok("Vieil exercice" in pg.inner_text("#app") and "archivé" in pg.inner_text("#app"), f"mode {mode} : « Afficher les exercices archivés » le montre")
                pg.evaluate("catArch = false; openEx(Object.values(EX).find(e => e.name === 'Tirage perso').id)"); pg.evaluate(OUVRIR); t = pg.inner_text("#app")
                ok("4 × 6-8 · repos 120 s" in t and "Mon programme" in t and "5 × 3-5 · repos 180 s" in t and "2\nséances" in t, f"mode {mode} : fiche (prescription, programme et son réglage, 2 séances)")
                pg.evaluate("go('programmes'); selProg(WO.find(w => w.name === 'Mon programme').id)"); t = pg.inner_text("#app")
                ok("5 × 3-5 · repos 180 s" in t and "Tirage perso" in t, f"mode {mode} : Programmes, réglage propre au programme affiché")
                pg.evaluate("cfgProg(Object.values(EX).find(e => e.name === 'Tirage perso').id)"); t = pg.inner_text("#app")
                ok("Pas encore enregistré" not in t and pg.evaluate("localStorage.getItem('muscu-prog-attente')") in (None, "{}"), f"mode {mode} : ouvrir un réglage ne crée aucun changement en attente")
                pg.evaluate("go('zones')"); pg.evaluate("ZMODE = 'heat'; R()"); pg.evaluate("ZMODE = 'pick'; R()")
                pg.evaluate("go('profil')"); pg.evaluate("go('accueil')")
                ok(pg.evaluate(RELEVE) == avant[mode], f"mode {mode} : après le passage sur tous les écrans du lot 3, données inchangées")
                pg.close()
            ctx.close(); arreter(pr)
            ok(not errs, f"aucune erreur JavaScript (données de la 0.7.1) {errs[:2]}")
            # export de la 0.7.1 importé dans une appli neuve
            pr = serveur(os.path.join(ROOT, "server"), os.path.join(TMP, "neuf", "fonte.db"), P1)
            for mode in MODES:
                ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); surveiller(ctx); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(MODES[mode]); pg.wait_for_selector("#app .btn-t", timeout=10000)
                pg.click("button:has-text('J’ai une sauvegarde')"); pg.wait_for_timeout(300)
                pg.fill("#bk", json.dumps(dict(avant[mode]["export"], jeu=json.loads(avant[mode]["jeu"])) if mode == "local" else avant[mode]["export"])); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
                n = pg.evaluate(RELEVE)["export"]
                ok({k: n[k] for k in ("exercises", "workouts", "sessions")} == {k: avant[mode]["export"][k] for k in ("exercises", "workouts", "sessions")}, f"mode {mode} : export de la 0.7.1 importé à l'identique")
                ctx.close()
            arreter(pr)

        # ============================================================ 2. questionnaire parcouru à l'écran
        URL = f"http://127.0.0.1:{P2}/?local=1"
        if set("234") & set(PARTIES): pr = serveur(os.path.join(ROOT, "server"), os.path.join(TMP, "ecrans", "fonte.db"), P2)
        if "2" in PARTIES:
            for w, h in ((390, 844), (360, 780)):
                ctx = b.new_context(viewport={"width": w, "height": h}, service_workers="block"); surveiller(ctx); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
                pg.goto(URL); pg.wait_for_selector("#app .btn-p", timeout=10000); pg.wait_for_timeout(300)
                typo = []
                def mesure_typo(nom):
                    pg.evaluate(OUVRIR); typo.extend(f"{nom} : {x}" for x in pg.evaluate(MESURE)["typo"])
                mesure_typo("bienvenue"); pg.click("button:has-text('Commencer')"); pg.wait_for_timeout(150)
                plan = [("fill", "Léo"), ("fill", "35"), ("pick", [0]), ("fill", "178"), ("fill", "75"), ("pick", [4]), ("pick", [5]), ("pick", [1]), ("pick", [5]), ("pick", [1]), ("pick", [2]), ("pick", [0]), ("pick", [0]),
                        ("sante", None), ("pick", []), ("pick", [0, 2, 4]), ("pick", [0])]
                sante = []
                for i, (k, v) in enumerate(plan):
                    mesure_typo(f"question {i + 1}")
                    if k == "fill": pg.fill("#qin", v)
                    elif k == "pick":
                        for j in v: pg.click(f".qo >> nth={j}")
                    else:
                        if pg.locator('.sq button[aria-pressed="true"]').count(): sante.append("réponse cochée d'avance")
                        nq = pg.locator(".sq").count()
                        if nq != 7: sante.append(f"{nq} questions au lieu de 7")
                        for q in range(nq):   # le défaut est noté, puis les 7 réponses sont données quand même pour que la suite du parcours tourne
                            if pg.locator("#qnext").is_enabled() and not any("actif après" in m for m in sante): sante.append(f"« Suivant » actif après {q} réponse(s)")
                            pg.locator(".sq").nth(q).locator("button", has_text="Non").click(); pg.wait_for_timeout(50)
                        if not pg.locator("#qnext").is_enabled(): sante.append("« Suivant » inactif après 7 réponses")
                        mesure_typo("question 14 (7 réponses)")
                    pg.click("#qnext"); pg.wait_for_timeout(150)
                ok(not sante, f"{w} px : santé, aucune réponse cochée d'avance, « Suivant » grisé de 0 à 6 réponses, actif à 7 {sante}")
                mesure_typo("résumé"); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
                mesure_typo("confirmation"); pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000); pg.wait_for_timeout(200)
                mesure_typo("programme prêt")
                ok(not typo, f"{w} px : espace insécable avant « ? », « ! », « ; » et aucun de ces signes en début de ligne (17 questions, résumé, confirmation, programme prêt) {typo[:3]}")
                ctx.close()

        # ============================================================ 3. écrans × 6 couleurs × clair et sombre × 390 et 360 px
        if "3" in PARTIES:
            DC = "Object.values(EX).find(e => e.slug === 'developpe-couche').id"
            ECRANS = [
                ("bienvenue", "q", [REPONSES, "intro", 0]), ("question 1", "q", [REPONSES, "q", 0]), ("question 2", "q", [REPONSES, "q", 1]), ("question 6", "q", [REPONSES, "q", 5]),
                ("question 13", "q", [REPONSES, "q", 12]), ("question 14", "q", [REPONSES, "q", 13]), ("question 15", "q", [REPONSES, "q", 14]), ("question 16", "q", [REPONSES, "q", 15]),
                ("résumé", "q", [REPONSES, "resume", 16]), ("confirmation", "clic", "Générer mon programme"), ("programme prêt", "clic", "Remplacer"),
                ("exercices", "js", "go('exercices')"), ("fiche", "js", f"openEx({DC})"),
                ("fiche en séance", "js", f"pickWorkout(WO[0].id); F.t0 = Date.now(); store(draftKey(), F); go('exercices'); openEx({DC})"),
                ("formulaire", "js", f"F = null; store(draftKey(), undefined); editOpen({DC})"), ("nouvel exercice", "js", "editOpen(null)"),
                ("programmes", "js", "editEx = null; go('programmes'); selProg(WO[0].id)"), ("programme ouvert", "js", "cfgProg(WO[0].items[1])"),
                ("programme modifié", "js", "pSets(WO[0].items[1], 1)"), ("autre programme, changement en attente", "js", "selProg(WO[1].id)"),
                ("zones", "js", "selProg(WO[0].id); progCancel(); go('zones'); ZMODE = 'pick'; ZSEL.clear(); R()"), ("zones choisies", "js", "togZone('pectoraux'); togZone('dos')"),
                ("ma semaine", "js", "ZMODE = 'heat'; R()")]
            res = {}; vues = 0; vus = {"steps": 0, "danger": 0}
            for th in ("light", "dark"):
                for w, h in ((390, 844), (360, 780)):
                    ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=th, service_workers="block"); surveiller(ctx); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
                    for acc in ACC:
                        pg.goto(URL); pg.evaluate(f"localStorage.setItem('muscu-accent', JSON.stringify('{acc}'))")
                        for nom, k, v in ECRANS:
                            if k == "q": pg.evaluate(BROUILLON, v); pg.reload(); pg.wait_for_selector("#app .l3", timeout=10000)
                            elif k == "clic": pg.click(f"button:has-text('{v}')"); pg.wait_for_selector("#app .l3 h1", timeout=8000); pg.wait_for_timeout(250 if v == "Remplacer" else 100)
                            else: pg.evaluate(v)
                            if nom == "programme prêt": pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
                            pg.evaluate(OUVRIR); r = pg.evaluate(MESURE); vues += 1
                            for x in vus: vus[x] += r["n"][x]
                            d = []
                            if r["orange"] > 1: d.append(f"{r['orange']} actions orange")
                            if r["cible"]: d.append(f"cibles {r['cible'][:3]}")
                            if r["txt"]: d.append(f"texte {r['txt'][:3]}")
                            if r["deb"]: d.append(f"débordement {r['deb']} px")
                            if r["danger"]: d.append(f"danger {r['danger'][:3]}")
                            if r["steps"]: d.append(f"numéros des étapes {r['steps'][:1]}")
                            if r["mots"]: d.append(f"mots {r['mots']}")
                            for x in d: res.setdefault(x.split(" ")[0] if not x[0].isdigit() else "orange", []).append(f"{th} {w} {acc} {nom} : {x}")
                    ctx.close()
            for cle, lib in (("orange", "une action orange au plus"), ("cibles", "cibles de 44 × 44 px au moins"), ("texte", "texte 4,5:1 et 13 px au moins"), ("débordement", "aucun débordement horizontal"),
                             ("danger", "liens « danger » (Retirer, Supprimer) : sans fond, avec icône, à 20 au moins de --a et --at"), ("numéros", "numéros de « Comment le faire » en --at, pas en framboise"), ("mots", "ni « manqué » ni « semaines d'affilée »")):
                ok(not res.get(cle), f"{vues} vues : {lib} {res.get(cle, [])[:3]}")
            ok(vus["steps"] > 0 and vus["danger"] > 0, f"(les numéros d'étapes et les liens « danger » ont bien été mesurés : {vus})")

        # ============================================================ 4. changements en attente (Programmes)
        if "4" in PARTIES:
            NAV4 = os.path.join(TMP, "navigateur4")   # profil de navigateur gardé sur disque : on peut le fermer puis le rouvrir
            def nav4():
                c = pw.chromium.launch_persistent_context(NAV4, viewport={"width": 390, "height": 844}, service_workers="block"); surveiller(c)
                p_ = c.new_page(); p_.on("pageerror", lambda e: errs.append(str(e))); return c, p_
            ctx, pg = nav4()
            pg.goto(URL); pg.evaluate(BROUILLON, [REPONSES, "resume", 16]); pg.reload(); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(200)
            pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000); pg.evaluate("PROFIL.home(); go('accueil')")
            ok(pg.evaluate("localStorage.getItem('muscu-prog-attente')") is None and pg.evaluate("WO.length") >= 2, "(appli neuve, programme généré, rien en attente)")
            X = "WO[0].items[1]"; s0 = pg.evaluate(f"exIn(EX[{X}], WO[0]).sets")
            pg.evaluate(f"go('programmes'); selProg(WO[0].id); cfgProg({X})"); pg.click(f"button[aria-label='Une série de plus']")
            t = pg.inner_text("#app")
            ok("Pas encore enregistré" in t and pg.locator(".actbar button:has-text('Enregistrer')").count() == 1, "changement : « Pas encore enregistré » et « Enregistrer »")
            pg.click(".scroller .chip >> nth=1"); a = pg.locator(".scroller .chip >> nth=0")
            ok(a.locator(".dot").count() == 1 and "pas encore enregistré" in (a.get_attribute("aria-label") or "") and pg.locator(".actbar button:has-text('Voir')").count() == 1,
               "autre programme ouvert : point et « pas encore enregistré » sur le programme modifié, bouton « Voir »")
            pg.evaluate("go('accueil')"); pg.evaluate("go('programmes'); selProg(WO[0].id)")
            ok(pg.evaluate(f"exIn(EX[{X}], progDraft).sets") == s0 + 1 and "Pas encore enregistré" in pg.inner_text("#app"), "changement gardé après un passage par l'accueil")
            pg.reload(); pg.wait_for_selector(".tabbar button"); pg.evaluate("go('programmes'); selProg(WO[0].id)")
            ok(pg.evaluate(f"exIn(EX[{X}], progDraft).sets") == s0 + 1 and "Pas encore enregistré" in pg.inner_text("#app"), "changement gardé après un rechargement de la page (navigateur)")
            ok(not any(m in pg.inner_text("#app").lower() for m in ("fermes", "fermer l", "même si")), "aucun texte ne promet que les changements survivent à la fermeture de l'appli")
            ctx.close()   # navigateur fermé pour de bon (toutes ses pages), puis rouvert sur le même profil
            ctx, pg = nav4(); pg.goto(URL); pg.wait_for_selector(".tabbar button", timeout=8000); pg.evaluate("go('programmes'); selProg(WO[0].id)")
            ok(pg.evaluate(f"exIn(EX[{X}], progDraft).sets") == s0 + 1 and "Pas encore enregistré" in pg.inner_text("#app") and pg.evaluate(f"exIn(EX[{X}], WO[0]).sets") == s0,
               "changement gardé après la fermeture complète du navigateur puis sa réouverture, toujours pas enregistré")
            pg.evaluate("startFromHome(WO[0].id); exitFocus()")
            ok(pg.evaluate(f"rowsFor(exF({X})).length") == s0 and pg.evaluate(f"exF({X}).sets") == s0, f"séance lancée depuis le programme modifié : version enregistrée ({s0} séries, pas {s0 + 1})")
            t = pg.inner_text("#app")
            ok("modifié, pas enregistré : séance faite avec la version enregistrée." in t, "écran Séance : une ligne neutre le dit")
            pg.evaluate("FOC = 0; F.ap = false; R()")
            ok("modifié, pas enregistré : séance faite avec la version enregistrée." in pg.inner_text("#app"), "écran Séance, un exercice à la fois : la même ligne")
            pg.evaluate("F = null; store(draftKey(), undefined); go('programmes'); selProg(WO[0].id)"); pg.click(".actbar button:has-text('Annuler')")
            ok(pg.evaluate(f"exIn(EX[{X}], WO[0]).sets") == s0 and pg.evaluate("localStorage.getItem('muscu-prog-attente')") == "{}" and "Pas encore enregistré" not in pg.inner_text("#app"), "« Annuler » efface le changement en attente")
            pg.evaluate(f"cfgProg({X})"); pg.click("button[aria-label='Une série de plus']"); pg.click(".actbar button:has-text('Enregistrer')"); pg.wait_for_timeout(600)
            ok(pg.evaluate(f"exIn(EX[{X}], WO[0]).sets") == s0 + 1 and pg.evaluate("localStorage.getItem('muscu-prog-attente')") == "{}", "« Enregistrer » applique le changement et vide l'attente")
            pg.evaluate("startFromHome(WO[0].id); exitFocus()")
            ok("modifié, pas enregistré" not in pg.inner_text("#app") and pg.evaluate(f"exF({X}).sets") == s0 + 1, "après « Enregistrer » : la séance prend le nouveau réglage, plus de ligne")
            ctx.close(); arreter(pr)
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        ok(not externes, f"aucune requête sortante {externes[:3]}")
finally:
    for pr in PROCS:
        if pr.poll() is None: pr.terminate()
print("\n" + ("TOUT EST BON" if not fails else f"{len(fails)} ÉCHEC(S)"))
sys.exit(1 if fails else 0)
