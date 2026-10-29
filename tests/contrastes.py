# SPDX-License-Identifier: AGPL-3.0-or-later
# Contrastes des écrans de la refonte (lot 1), mesurés sur l'appli affichée, pour toutes les palettes : les 6 couleurs du menu
# (orange, bleu, vert, violet, rouge, noir et blanc), en clair et en sombre (12 palettes), à 390 × 844.
# Écrans : accueil (jour de séance, jour de repos avec une carte de proposition, séance commencée avec la barre de repos compacte),
# séance (ouverture, repos, repos avec démonstration et ressenti, exercice fini), écran de fin ; lot 2 : Progrès (sans aucune séance,
# poids replié puis ouvert ; avec séances et pesées, « Détails » ouvert ; jour choisi dans le calendrier), Historique, détail d'une séance.
# - texte : 4,5:1 au moins contre le fond réellement dessous (fonds composés, surlignage du conseil compris), et 13 px au moins ;
# - éléments non textuels (WCAG 1.4.11) : 3:1 au moins pour le bouton principal (fond ou bord contre ce qui l'entoure), les bâtons
#   de comptage, le cadre de la série en cours, la coche des ronds de validation, la barre de progression du repos, le point de
#   l'étiquette de zone, la marque de l'onglet actif, le trait des records, le choix du ressenti sélectionné ; lot 2 : pastilles des
#   jours de séance, courbes (charge, poids de corps) et leurs points, traits des records, bord des étiquettes « record », chevrons,
#   période choisie, bords du choix d'exercice et des champs.
# Les lignes de graduation et les bords des cartes sont décoratifs (valeurs écrites ; cartes distinguées par leur fond) : non comptés.
# Les boutons secondaires sans bord (V3) sont identifiés par leur texte (contrôlé comme du texte) ; les boutons désactivés sont exclus.
# Témoin : FONTE_ROOT=dossier du code du commit 08f52a0 : « Démarrer la séance » blanc sur papier en « Noir et blanc » doit échouer.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/contrastes.py
import os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "server"); PORT = 5182
TMP = tempfile.mkdtemp(prefix="fonte-contrastes-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}

MESURE = r"""() => {
  const parse = c => { const m = /rgba?\(([^)]+)\)/.exec(c || ''); if (!m) return null; const p = m[1].split(/[\s,\/]+/).filter(Boolean).map(Number); return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1]; };
  const L = c => { const f = v => (v /= 255) <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; return .2126 * f(c[0]) + .7152 * f(c[1]) + .0722 * f(c[2]); };
  const cr = (a, b) => { const x = L(a), y = L(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const over = (fg, bg, k = 1) => { const a = (fg[3] ?? 1) * k; return [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); };
  const vis = el => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return false; for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden') return false; } return true; };
  const opa = el => { let o = 1; for (let e = el; e; e = e.parentElement) o *= +getComputedStyle(e).opacity; return o; };
  // fonds possibles sous un élément : couleurs empilées jusqu'au premier fond opaque, plus les couleurs des dégradés (surlignage)
  function bgs(el) {
    const layers = []; let grads = [];
    for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e), c = parse(s.backgroundColor);
      if (s.backgroundImage && s.backgroundImage.includes('gradient')) grads.push(...(s.backgroundImage.match(/rgba?\([^)]+\)/g) || []).map(parse));
      if (c && c[3] > 0) { layers.push(c); if (c[3] >= 1) break; } }
    let base = [255, 255, 255]; for (let i = layers.length - 1; i >= 0; i--) base = over(layers[i], base);
    return [base, ...grads.filter(g => g[3] > 0).map(g => over(g, base))];
  }
  const bgOf = el => bgs(el)[0];
  const texte = [], petit = [], objets = [];
  const add = (el, fg, what) => { if (el.closest('button:disabled')) return; const k = opa(el);
    for (const b of bgs(el)) { const c = over(fg, b, k), v = cr(c, b); if (v < 4.5) texte.push(`${what} ${v.toFixed(2)}:1`); } };
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n; (n = w.nextNode());) { const t = n.textContent.trim(); if (!t) continue; const el = n.parentElement; if (!el || el.closest('script,style,svg') || !vis(el)) continue;
    const rg = document.createRange(); rg.selectNodeContents(n); const r = rg.getBoundingClientRect(); if (!r.width || !r.height) continue;
    if (el.closest('details:not([open])') && !el.closest('summary')) continue;
    const s = getComputedStyle(el); add(el, parse(s.color), `« ${t.slice(0, 28)} »`);
    if (parseFloat(s.fontSize) < 12.95) petit.push(`« ${t.slice(0, 28)} » ${s.fontSize}`); }
  document.querySelectorAll('input').forEach(i => { if (!vis(i)) return; const s = getComputedStyle(i, i.value ? null : '::placeholder');
    add(i, parse(s.color), `champ « ${i.value || i.placeholder} »`); });
  const obj = (sel, f, what) => document.querySelectorAll(sel).forEach(el => { if (!vis(el)) return; const v = f(el); if (v != null && v < 3) objets.push(`${what}${el.textContent.trim() ? ' « ' + el.textContent.trim().slice(0, 24) + ' »' : ''} ${v.toFixed(2)}:1`); });
  const bgc = el => parse(getComputedStyle(el).backgroundColor);
  obj('.go', el => { const s = getComputedStyle(el), b = bgOf(el.parentElement), f = over(bgc(el), b);
    return Math.max(cr(f, b), parseFloat(s.borderTopWidth) > 0 ? cr(over(parse(s.borderTopColor), b), b) : 0); }, 'bouton principal contre son entourage');
  obj('.tally i', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'bâton de comptage');
  obj('.frow.act', el => cr(over(parse(getComputedStyle(el).borderTopColor), bgOf(el)), bgOf(el)), 'cadre de la série en cours');
  obj('.tick svg', el => { const t = el.closest('.tick'); return cr(over(parse(getComputedStyle(t).color), bgOf(t)), bgOf(t)); }, 'coche du rond de validation');
  obj('.bar .pbar i', el => cr(over(bgc(el), bgOf(el.closest('.bar'))), bgOf(el.closest('.bar'))), 'barre de progression du repos');
  obj('.zchip i', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), "point de l'étiquette de zone");
  obj('.tabbar button.on', el => { const c = parse(getComputedStyle(el, '::before').backgroundColor); return c ? cr(over(c, bgOf(el)), bgOf(el)) : 0; }, "marque de l'onglet actif");
  obj('.fin .rec i', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'trait du record');
  obj('.feelb button.on', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'ressenti choisi');
  // lot 2
  const svgc = (el, prop) => parse(getComputedStyle(el)[prop]), card = el => bgOf(el.closest('.card,section,div'));
  obj('.cal .cd.on i', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'pastille du jour de séance');
  obj('.recl i', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'trait du record (lot 2)');
  obj('.chart .l1, .chart .lb', el => cr(over(svgc(el, 'stroke'), card(el)), card(el)), 'courbe');
  obj('.chart .p1, .chart .pb', el => cr(over(svgc(el, 'fill'), card(el)), card(el)), 'point de la courbe');
  obj('.tag.rec', el => cr(over(parse(getComputedStyle(el).borderTopColor), bgOf(el)), bgOf(el)), 'bord de l’étiquette « record »');
  obj('svg.chev', el => cr(over(svgc(el, 'stroke'), bgOf(el.parentElement)), bgOf(el.parentElement)), 'chevron');
  obj('.pg .chip[aria-pressed="true"]', el => cr(over(bgc(el), bgOf(el.parentElement)), bgOf(el.parentElement)), 'période choisie');
  obj('.pg select, .pg input', el => cr(over(parse(getComputedStyle(el).borderTopColor), bgOf(el.parentElement)), bgOf(el.parentElement)), 'bord du champ');
  const n = sel => [...document.querySelectorAll(sel)].filter(vis).length;
  return {texte: [...new Set(texte)], petit: [...new Set(petit)], objets: [...new Set(objets)],
          vus: {go: n('.go'), tally: n('.tally i'), act: n('.frow.act'), tick: n('.tick svg'), pbar: n('.bar .pbar i'), zchip: n('.zchip i'), onglet: n('.tabbar button.on'), rec: n('.fin .rec i'), feel: n('.feelb button.on'),
                pastille: n('.cal .cd.on i'), recl: n('.recl i'), courbe: n('.chart .l1'), poids: n('.chart .lb'), etiquette: n('.tag.rec'), chevron: n('svg.chev'), periode: n('.pg .chip[aria-pressed="true"]'), champ: n('.pg select, .pg input')}};
}"""

srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=dict(os.environ, DB_PATH=os.path.join(TMP, "s.db"), PYTHONDONTWRITEBYTECODE="1"),
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
U = f"http://127.0.0.1:{PORT}/"
TRAIN, REST = "2026-12-11T10:00:00", "2026-12-10T10:00:00"   # vendredi (séance prévue), jeudi (jour de repos)
vus = {}
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(U) or not r.request.url.startswith("http") else r.abort())
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.clock.set_fixed_time("2026-11-02T08:00:00")
        pg.goto(U); pg.wait_for_selector("#app .card", timeout=8000)
        pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", REP)
        pg.reload(); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
        pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
        pg.evaluate("JEU.view()")
        def mesure(nom, M):
            pg.wait_for_timeout(250); r = pg.evaluate(MESURE)
            for k, v in r["vus"].items(): vus[k] = vus.get(k, 0) + v
            ok(not r["texte"], f"{M} · {nom} : texte à 4,5:1 au moins {r['texte'][:4]}")
            ok(not r["objets"], f"{M} · {nom} : éléments non textuels à 3:1 au moins {r['objets'][:4]}")
            ok(not r["petit"], f"{M} · {nom} : aucun texte sous 13 px {r['petit'][:4]}")
        # lot 2 : Progrès et Historique sans aucune séance ni pesée (12 palettes)
        for scheme, tn in (("light", "clair"), ("dark", "sombre")):
            pg.emulate_media(color_scheme=scheme)
            for acc in ("orange", "blue", "green", "violet", "red", "mono"):
                M = f"{tn} · {acc}"; pg.evaluate(f"setAccent('{acc}')")
                pg.evaluate("go('progres')"); mesure("Progrès sans séance", M)
                pg.evaluate("document.querySelector('details.opt').open = true"); mesure("Progrès sans séance, pesée ouverte", M)
                pg.evaluate("go('historique')"); mesure("Historique sans séance", M)
        pg.evaluate("""async () => { for (const [day, kg] of [['2026-11-02', 75.4], ['2026-11-16', 75.1], ['2026-11-30', 74.9]]) await api('POST', '/api/bodyweight', {day, kg}); }""")
        pg.evaluate("""async () => { let d = new Date(2026, 10, 2), k = 0; const end = new Date(2026, 11, 9);
          while (d <= end) { if ([1, 3, 5].includes(d.getDay())) { const w = WO[k % WO.length], wk = Math.floor(k / 3), day = new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10);
            await api('POST', '/api/sessions', {day, workout_id: w.id, workout_name: w.name, entries: w.items.map(i => { const e = EX[i];
              const s = e.kind === 'weight' ? [40 + 2.5 * Math.floor(wk / 2), 10 + wk % 2] : e.kind === 'cardio' ? [null, 20] : e.kind === 'time' ? [null, 30 + 5 * wk] : [null, 8 + wk];
              return {exercise_id: i, sets: e.kind === 'cardio' ? [s] : [s, s, s], effort: 3}; })}); k++; }
            d.setDate(d.getDate() + 1); } await load(); }""")
        for scheme, tn in (("light", "clair"), ("dark", "sombre")):
            pg.emulate_media(color_scheme=scheme)
            for acc in ("orange", "blue", "green", "violet", "red", "mono"):
                M = f"{tn} · {acc}"
                pg.evaluate(f"setAccent('{acc}')"); pg.evaluate("store('muscu-draft'); store('muscu-xcur'); XS = []; F = null; FOC = null; TMskip()")
                pg.clock.set_fixed_time(REST); pg.evaluate("go('accueil')"); mesure("accueil, jour de repos", M)
                pg.clock.set_fixed_time(TRAIN); pg.evaluate("go('accueil')"); mesure("accueil", M)
                pg.click("#app .hero button:has-text('Démarrer la séance')"); pg.wait_for_selector(".focus"); pg.evaluate("window.scrollTo(0, 0)"); mesure("séance, ouverture", M)
                pg.locator(".focus .frow.act .tick").click(); mesure("séance, repos", M)
                pg.evaluate("go('accueil')"); mesure("accueil, séance commencée et repos", M)
                pg.evaluate("go('seance')"); pg.wait_for_selector(".focus")
                while pg.locator(".focus .frow.act .tick").count(): pg.locator(".focus .frow.act .tick").click(); pg.wait_for_timeout(120)
                mesure("séance, repos avec démonstration et ressenti", M)
                pg.click(".bar button:has-text('Passer')"); pg.locator(".focus .feelb button").nth(1).click(); mesure("séance, exercice fini", M)
                pg.evaluate("""() => { const ids = F.ids.filter(i => EX[i]); ids.forEach((id, k) => { const e = exF(id); F.vals[id] = rowsFor(e).map(() => e.kind === 'weight' ? ['60', '8'] : ['', '40']); F.dn = F.dn || {}; F.dn[id] = F.vals[id].map(() => true); }); store(draftKey(), F); }""")
                pg.evaluate("saveSession()"); pg.wait_for_selector(".fin"); pg.evaluate("window.scrollTo(0, 0)"); mesure("écran de fin", M)
                pg.evaluate("FIN = null; go('progres')"); pg.evaluate("document.querySelectorAll('#app details').forEach(d => d.open = true)"); mesure("Progrès", M)
                pg.evaluate("CAL = null; R()"); pg.click("#app .cal .cd.on >> nth=0"); mesure("Progrès, jour choisi", M)
                pg.evaluate("go('historique')"); mesure("Historique", M)
                pg.evaluate("openSess(SESS.find(s => (computePRs().bySession[s.id] || []).length).id, 'historique')"); mesure("détail d’une séance", M)
                pg.evaluate("go('accueil')")
        ok(all(vus.get(k, 0) > 0 for k in ("go", "tally", "act", "tick", "pbar", "zchip", "onglet", "rec", "pastille", "recl", "courbe", "poids", "etiquette", "chevron", "periode", "champ")), f"(témoin) chaque élément non textuel a bien été mesuré {vus}")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        b.close()
finally:
    srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
