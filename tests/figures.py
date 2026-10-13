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
          if (p.arm && p.arm.ik === 'bar') { const d = norm(geo.armN.end, p.bar); if (d > 1.5) res.reach.push(slug + ' ' + g + ' t=' + t.toFixed(2) + ' écart ' + d.toFixed(1)); }
          if (p.leg && p.leg.ik && p.leg.ik[1] >= 86) { const d = norm(geo.legN.end, p.leg.ik); if (d > 1.0) res.floor.push(slug + ' ' + g + ' t=' + t.toFixed(2) + ' écart ' + d.toFixed(1)); }
        }
      }
    });
  });
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
