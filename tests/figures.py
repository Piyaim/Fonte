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
  const res = {flat: [], rules: []}, deg = 180 / Math.PI, B = FIG.BODY.m;
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
  const rule = (ok, msg) => { if (!ok) res.rules.push(msg); };
  const minOf = (slug, fn) => Math.min(...frames(slug).map(fn)), maxOf = (slug, fn) => Math.max(...frames(slug).map(fn));
  ['dips-assistes', 'dips-banc'].forEach(s => { const m = minOf(s, elbow); rule(m >= 85, s + ' : coude ' + m.toFixed(0) + '° en bas (au moins 85° attendu)'); });
  const rdl = frames('rdl'), lo = rdl.reduce((a, b) => (b.g.armN.end[1] > a.g.armN.end[1] ? b : a));
  rule(Math.abs(lo.g.armN.end[0] - (lo.p.leg.ik[0] + 3)) <= 4, 'rdl : haltères à ' + (lo.g.armN.end[0] - lo.p.leg.ik[0] - 3).toFixed(1) + " du milieu du pied en bas (4 au plus)");
  rule(minOf('rdl', knee) >= 150 && maxOf('rdl', knee) <= 172, 'rdl : genoux entre ' + minOf('rdl', knee).toFixed(0) + ' et ' + maxOf('rdl', knee).toFixed(0) + '° (150 à 172 attendus, souples et fixes)');
  ['developpe-couche', 'barre-front'].forEach(s => { const b = FIGDATA[s].scene.find(o => o.t === 'bench'), h = frames(s)[0].g.head; rule(h[0] >= b.x + 3, s + ' : tête à x=' + h[0].toFixed(1) + ', banc dès x=' + b.x + ' (tête posée sur le banc attendue)'); });
  rule(maxOf('preacher', elbow) <= 170, 'preacher : bras à ' + maxOf('preacher', elbow).toFixed(0) + '° en bas (170 au plus, sans verrouiller)');
  rule(minOf('pl', knee) >= 165, 'pl : genoux à ' + minOf('pl', knee).toFixed(0) + '° (165 au moins, corps aligné)');
  ['de', 'developpe-militaire'].forEach(s => { const m = maxOf(s, elbow); rule(m >= 140, s + ' : coude à ' + m.toFixed(0) + '° en haut (140 au moins, bras presque tendus)'); });
  // face pull : en fin de tirage, coude à hauteur d'épaule et sous les mains (avant-bras qui remonte vers le visage)
  const fp = frames('face-pull').reduce((a, b) => (b.g.armN.end[0] < a.g.armN.end[0] ? b : a)), fe = fp.g.armN.mid, fh = fp.g.armN.end;
  rule(fe[1] >= fh[1] + 6 && Math.abs(fe[1] - fp.g.S[1]) <= 5, 'face-pull : coude à y=' + fe[1].toFixed(1) + ', mains à y=' + fh[1].toFixed(1) + ', épaule à y=' + fp.g.S[1].toFixed(1) + " (coude sous les mains, à hauteur d'épaule)");
  return res;
}"""
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.set_content("<html><body></body></html>")
    pg.add_script_tag(path=os.path.join(STATIC, "figure.js")); pg.add_script_tag(path=os.path.join(STATIC, "figure-data.js"))
    r = pg.evaluate(JS)
    ok(not errs, f"aucune erreur JavaScript : {errs}")
    ok(r["n"] > 0 and not r["bad"], f"{r['n']} images calculées, aucune valeur invalide {r['bad'][:3]}")
    ok(min(r["paths"]) >= 15, f"chaque image contient un corps complet (min {min(r['paths'])} formes)")
    ok(not r["reach"], f"les mains restent sur la barre : {r['reach'][:4]}")
    ok(not r["floor"], f"les pieds restent au sol : {r['floor'][:4]}")
    q = pg.evaluate(POSTURE)
    ok(not q["flat"], f"les pieds posés au sol restent à plat : {q['flat'][:4]}")
    ok(not q["rules"], f"règles de posture de l'audit respectées : {q['rules']}")
