# SPDX-License-Identifier: AGPL-3.0-or-later
# Vérifie les animations de personnage : aucune valeur invalide, mains sur la barre, pieds au sol, les deux silhouettes (homme et femme).
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATIC = os.path.join(ROOT, "server", "static")
from playwright.sync_api import sync_playwright
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
JS = """() => {
  const res = {bad: [], reach: [], floor: [], n: 0, paths: []};
  const norm = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);
  Object.keys(FIGDATA).forEach(slug => {
    const spec = FIGDATA[slug]; FIG.prepare(spec);
    ['m', 'f'].forEach(g => {
      for (let i = 0; i <= 24; i++) {
        const t = spec._T * i / 24, svg = FIG.sideSvg(spec, t, {g});
        res.n++; res.paths.push((svg.match(/<path/g) || []).length);
        if (/NaN|Infinity|undefined/.test(svg)) res.bad.push(slug + ' ' + g + ' t=' + t.toFixed(2));
        if (spec.view !== 'front' && spec.view !== 'back') {
          const p = FIG.poseAt(spec, t), geo = FIG.solveSide(p, FIG.BODY[g], spec.f || 1);
          if (p.arm && p.arm.ik === "bar") { const d = norm(geo.armN.end, geo.bar); if (d > 1.5) res.reach.push(slug + ' ' + g + ' t=' + t.toFixed(2) + ' écart ' + d.toFixed(1)); }
          if (p.leg && p.leg.ik && p.leg.ik[1] >= 86) { const d = norm(geo.legN.end, p.leg.ik); if (d > 1.0) res.floor.push(slug + ' ' + g + ' t=' + t.toFixed(2) + ' écart ' + d.toFixed(1)); }
        }
      }
    });
  });
  return res;
}"""
# Postures : pieds à plat quand ils sont posés au sol, et règles techniques issues de l'audit des postures (20/10/2026).
# Chaque règle échoue sur l'ancienne version des animations : elle mesure la faute qui avait été dessinée.
POSTURE = """() => {
  const res = {flat: [], rules: [], under: []}, deg = 180 / Math.PI, B = FIG.BODY.m;
  const ang = (a, b, c) => { const u = [a[0] - b[0], a[1] - b[1]], v = [c[0] - b[0], c[1] - b[1]]; return Math.acos(Math.max(-1, Math.min(1, (u[0] * v[0] + u[1] * v[1]) / Math.hypot(...u) / Math.hypot(...v)))) * deg; };
  const frames = slug => { const s = FIGDATA[slug]; FIG.prepare(s); const out = []; for (let i = 0; i <= 40; i++) { const t = s._T * i / 40, p = FIG.poseAt(s, t); out.push({t, p, g: FIG.solveSide(p, B, s.f || 1), f: s.f || 1}); } return out; };
  const elbow = r => ang(r.g.armN.root, r.g.armN.mid, r.g.armN.end), knee = r => ang(r.g.legN.root, r.g.legN.mid, r.g.legN.end);
  Object.keys(FIGDATA).forEach(slug => {
    if (FIGDATA[slug].view) return;
    frames(slug).forEach(r => {
      [[r.p.leg, r.g.footN, r.p.ft], [r.p.leg2 || r.p.leg, r.g.footF, r.p.ft2 != null ? r.p.ft2 : r.p.ft]].forEach(([L, F, ft]) => {
        if (!L || !L.ik || L.ik === 'bar' || L.ik[1] < 86 || L.ftRel || ft) return;
        const a = Math.atan2(F.fd[1], F.fd[0] * r.f) * deg;
        if (Math.abs(a) > 5) res.flat.push(slug + ' t=' + r.t.toFixed(2) + ' pied à ' + a.toFixed(0) + '°');
      });
    });
  });
  // aucun bras ne passe sous le sol (dead bug du 20/10/2026 : le bras allait derrière la tête en traversant le sol)
  Object.keys(FIGDATA).forEach(slug => {
    if (FIGDATA[slug].view) return;
    const bad = frames(slug).find(r => [r.g.armN.mid, r.g.armN.end, r.g.armF.mid, r.g.armF.end].some(q => q[1] > FIG.FLOOR + 0.5));
    if (bad) res.under.push(slug + ' t=' + bad.t.toFixed(2));
  });
  const rule = (ok, msg) => { if (!ok) res.rules.push(msg); };
  const minOf = (slug, fn) => Math.min(...frames(slug).map(fn)), maxOf = (slug, fn) => Math.max(...frames(slug).map(fn));
  ['dips-assistes', 'dips-banc'].forEach(s => { const m = minOf(s, elbow); rule(m >= 85, s + ' : coude ' + m.toFixed(0) + '° en bas (au moins 85° attendu)'); });
  const rdl = frames('rdl'), lo = rdl.reduce((a, b) => (b.g.armN.end[1] > a.g.armN.end[1] ? b : a));
  rule(Math.abs(lo.g.armN.end[0] - (lo.p.leg.ik[0] + 3)) <= 4, 'rdl : haltères à ' + (lo.g.armN.end[0] - lo.p.leg.ik[0] - 3).toFixed(1) + " du milieu du pied en bas (4 au plus)");
  rule(minOf('rdl', knee) >= 150 && maxOf('rdl', knee) <= 172, 'rdl : genoux entre ' + minOf('rdl', knee).toFixed(0) + ' et ' + maxOf('rdl', knee).toFixed(0) + '° (150 à 172 attendus, souples et fixes)');
  ['developpe-couche', 'barre-front'].forEach(s => { const b = FIGDATA[s].scene.find(o => o.t === 'bench'), h = frames(s)[0].g.head; rule(h[0] >= b.x + 3, s + ' : tête à x=' + h[0].toFixed(1) + ', banc dès x=' + b.x + ' (tête posée sur le banc attendue)'); });
  rule(maxOf('preacher', elbow) <= 170, 'preacher : bras à ' + maxOf('preacher', elbow).toFixed(0) + '° en bas (170 au plus, sans verrouiller)');
  rule(minOf('pl', knee) >= 165, 'pl : genoux à ' + minOf('pl', knee).toFixed(0) + '° (165 au moins, corps aligné)');
  // Remarques de Georgio (20/10/2026) : coudes vers l'extérieur, avant-bras verticaux, charge qui monte et descend à la verticale.
  const L2 = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]), l1 = B.upper * B.sc;
  // avant-bras d'orientation fixe (fore) : le bras dessiné en raccourci ne peut pas dépasser sa vraie longueur
  Object.keys(FIGDATA).forEach(slug => { if (FIGDATA[slug].view) return; frames(slug).forEach(r => { if (!r.p.arm || r.p.arm.fore == null) return;
    const u = L2(r.g.armN.root, r.g.armN.mid); if (u > l1 + 0.3 || u < 1) rule(false, slug + ' t=' + r.t.toFixed(2) + ' : bras dessiné sur ' + u.toFixed(1) + ' (entre 1 et ' + l1.toFixed(1) + ' attendu)'); }); });
  ['developpe-couche', 'di'].forEach(s => { const fr = frames(s), xs = fr.map(r => r.g.armN.end[0]), lo = fr.reduce((a, b) => (b.g.armN.end[1] > a.g.armN.end[1] ? b : a));
    rule(Math.max(...xs) - Math.min(...xs) <= 1, s + ' : la charge se déplace de ' + (Math.max(...xs) - Math.min(...xs)).toFixed(1) + " à l'horizontale (1 au plus, trajet vertical)");
    rule(Math.abs(lo.g.armN.mid[0] - lo.g.armN.end[0]) <= 0.5 && L2(lo.g.armN.root, lo.g.armN.mid) <= 9, s + ' : en bas, avant-bras vertical et coude écarté (bras en raccourci) attendus'); });
  const dp = frames('dips-assistes'), dlo = dp.reduce((a, b) => (b.g.S[1] > a.g.S[1] ? b : a)), du = L2(dlo.g.armN.root, dlo.g.armN.mid);
  rule(dlo.p.tor >= 25, 'dips-assistes : buste penché de ' + dlo.p.tor.toFixed(0) + '° en bas (25 au moins)');
  rule(du >= 7 && du <= 11 && Math.abs(dlo.g.armN.mid[0] - dlo.g.armN.end[0]) <= 0.5, 'dips-assistes : bras dessiné sur ' + du.toFixed(1) + ' en bas (7 à 11 : coude écarté à environ 45°, avant-bras vertical)');
  const po = frames('pull-over').reduce((a, b) => (b.g.armN.end[1] > a.g.armN.end[1] ? b : a));
  rule(po.g.armN.end[0] - po.p.hip[0] <= 15, 'pull-over : mains à ' + (po.g.armN.end[0] - po.p.hip[0]).toFixed(1) + ' devant le bassin en fin de tirage (15 au plus)');
  // vues de face et de dos : coudes à l'extérieur des épaules, avant-bras verticaux
  const front = slug => { const s = FIGDATA[slug]; FIG.prepare(s); const Bf = Object.assign({}, FIG.FB.m, { sc: B.sc, torso: 24, upper: B.upper, fore: B.fore, thigh: B.thigh, shank: B.shank }), out = [];
    for (let i = 0; i <= 40; i++) { const t = s._T * i / 40, p = FIG.poseAt(s, t); out.push({t, p, g: FIG.solveFront(p, Bf, 1)}); } return out; };
  ['de', 'developpe-militaire'].forEach(s => {
    if (FIGDATA[s].view !== 'front') return rule(false, s + ' : vue de face attendue (coudes écartés sur les côtés)');
    const fr = front(s), lo = fr[0], hi = fr.reduce((a, b) => (b.g.armR.end[1] < a.g.armR.end[1] ? b : a)), A = lo.g.armR;
    rule(A.mid[0] - A.root[0] >= 10 && A.mid[1] >= A.root[1] - 1, s + ' : en bas, coude à ' + (A.mid[0] - A.root[0]).toFixed(1) + " à l'extérieur de l'épaule et pas au-dessus (10 au moins)");
    rule(fr.every(r => Math.abs(r.g.armR.mid[0] - r.g.armR.end[0]) <= 0.5), s + ' : avant-bras vertical sur tout le mouvement');
    const e = ang(hi.g.armR.root, hi.g.armR.mid, hi.g.armR.end); rule(e >= 140, s + ' : coude à ' + e.toFixed(0) + '° en haut (140 au moins, bras presque tendus)'); });
  if (FIGDATA['face-pull'].view !== 'back') rule(false, "face-pull : vue de dos attendue (coudes qui s'ouvrent sur les côtés)");
  else { const fr = front('face-pull'), end = fr.reduce((a, b) => (b.g.armR.mid[0] > a.g.armR.mid[0] ? b : a)), A = end.g.armR;
    rule(A.mid[0] - A.root[0] >= 10 && Math.abs(A.mid[1] - A.root[1]) <= 4 && A.mid[1] - A.end[1] >= 8, "face-pull : en fin de tirage, coude à hauteur d'épaule, sur le côté, mains au-dessus des coudes");
    rule(fr.every(r => r.g.armR.mid[1] >= r.g.armR.root[1] - 4), 'face-pull : les coudes ne montent jamais au-dessus des épaules'); }
  return res;
}"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.set_content("<html><body></body></html>")
    pg.add_script_tag(path=os.path.join(STATIC, "figure.js")); pg.add_script_tag(path=os.path.join(STATIC, "figure-data.js"))
    # secondes vues (bouton « Tourner ») : contrôlées comme des animations à part entière, sous le nom « slug~alt »
    alts = pg.evaluate("""() => Object.keys(FIGDATA).filter(s => FIGDATA[s].alt).map(s => { FIGDATA[s + '~alt'] = FIGDATA[s].alt;
      const v = x => x.view || 'side'; return [s, v(FIGDATA[s]), v(FIGDATA[s].alt)]; })""")
    ok(len(alts) >= 4 and all(a[1] != a[2] for a in alts), f"{len(alts)} exercices à deux vues, chaque seconde vue montre un autre côté : {alts}")
    r = pg.evaluate(JS)
    ok(not errs, f"aucune erreur JavaScript : {errs}")
    ok(r["n"] > 0 and not r["bad"], f"{r['n']} images calculées, aucune valeur invalide {r['bad'][:3]}")
    ok(min(r["paths"]) >= 15, f"chaque image contient un corps complet (min {min(r['paths'])} formes)")
    ok(not r["reach"], f"les mains restent sur la barre : {r['reach'][:4]}")
    ok(not r["floor"], f"les pieds restent au sol : {r['floor'][:4]}")
    q = pg.evaluate(POSTURE)
    ok(not q["flat"], f"les pieds posés au sol restent à plat : {q['flat'][:4]}")
    ok(not q["rules"], f"règles de posture de l'audit respectées : {q['rules']}")
    ok(not q["under"], f"aucun bras ne passe sous le sol : {q['under'][:4]}")
