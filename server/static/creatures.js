/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Fonte : les « esprits de fonte », dessinés par code (aucune image à télécharger).
 * CREA.svg(creature, stade, options) -> chaîne SVG (viewBox 0 0 120 120).
 * Six silhouettes (blob, golem, bête, oiseau, drake, esprit) × une palette × des attributs (oreilles, cornes, queue, motif, regard),
 * et trois stades d'évolution qui ajoutent des parties (crête, ailes, armure, auréole) et agrandissent la créature.
 */
(function () {
  'use strict';
  var PI = Math.PI, sin = Math.sin, cos = Math.cos, UID = 0;
  function n1(x) { return (Math.round(x * 10) / 10).toString(); }
  function P(p) { return n1(p[0]) + ',' + n1(p[1]); }
  function smoothQ(pts, closed) { return window.FIG.smoothQ(pts, closed !== false); }
  function path(d, fill, extra) { return '<path d="' + d + '" fill="' + fill + '"' + (extra || '') + '/>'; }
  function ell(cx, cy, rx, ry, fill, extra) { return '<ellipse cx="' + n1(cx) + '" cy="' + n1(cy) + '" rx="' + n1(rx) + '" ry="' + n1(ry) + '" fill="' + fill + '"' + (extra || '') + '/>'; }
  function circ(cx, cy, r, fill, extra) { return '<circle cx="' + n1(cx) + '" cy="' + n1(cy) + '" r="' + n1(r) + '" fill="' + fill + '"' + (extra || '') + '/>'; }
  function hsl(h, s, l, a) { return 'hsl(' + Math.round(((h % 360) + 360) % 360) + ',' + Math.round(s) + '%,' + Math.round(l) + '%' + (a == null ? '' : ',' + a) + ')'; }
  function scaleAbout(pts, c, k) { return pts.map(function (p) { return [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k]; }); }
  function mirror(pts) { return pts.map(function (p) { return [120 - p[0], p[1]]; }); }

  var RAR = {
    C: { n: 'Commune', col: '#8fa3b3', glow: 0.0, spark: 0 },
    U: { n: 'Peu commune', col: '#52c27a', glow: 0.25, spark: 2 },
    R: { n: 'Rare', col: '#4aa3ff', glow: 0.4, spark: 4 },
    E: { n: 'Épique', col: '#b06bff', glow: 0.6, spark: 6 },
    L: { n: 'Légendaire', col: '#ffc233', glow: 0.85, spark: 9 }
  };

  /* ---------- palette ---------- */
  function palette(c) {
    var h = c.hue, s = c.sat == null ? 62 : c.sat;
    return { base: hsl(h, s, 58), light: hsl(h, s - 8, 74), dark: hsl(h, s + 6, 38), deep: hsl(h, s + 8, 26), acc: hsl(h + (c.shift == null ? 38 : c.shift), 78, 60), accD: hsl(h + (c.shift == null ? 38 : c.shift), 70, 42), belly: hsl(h + 8, s - 24, 88) };
  }

  /* ---------- visage ---------- */
  function face(c, cx, cy, sc, pal, stage) {
    var o = '', dx = 11 * sc, er = 5.2 * sc, st = c.eyes || 'round';
    function eye(x, side) {
      if (st === 'happy') return '<path d="M' + P([x - er, cy + 1]) + 'Q' + P([x, cy - er * 1.5]) + ' ' + P([x + er, cy + 1]) + '" fill="none" stroke="#1d1b26" stroke-width="' + n1(2.6 * sc) + '" stroke-linecap="round"/>';
      if (st === 'sleepy') return '<path d="M' + P([x - er, cy - 1]) + 'Q' + P([x, cy + er]) + ' ' + P([x + er, cy - 1]) + '" fill="none" stroke="#1d1b26" stroke-width="' + n1(2.6 * sc) + '" stroke-linecap="round"/>';
      var e = ell(x, cy, er, er * 1.18, '#fff') + ell(x + side * 0.6, cy + 0.6, er * 0.68, er * 0.86, '#1d1b26') + circ(x + side * 0.6 - er * 0.22, cy - er * 0.25, er * 0.28, '#fff');
      if (st === 'fierce') e += '<path d="M' + P([x - side * er * 1.4, cy - er * 1.5 - side * 0]) + 'L' + P([x + side * er * 1.5, cy - er * 0.8 - side * 2.2 * sc]) + '" stroke="' + pal.deep + '" stroke-width="' + n1(2.4 * sc) + '" stroke-linecap="round"/>';
      if (st === 'spark') e = ell(x, cy, er * 1.1, er * 1.25, '#1d1b26') + circ(x - 1.2 * sc, cy - 1.6 * sc, er * 0.42, '#fff') + circ(x + 1.4 * sc, cy + 1.6 * sc, er * 0.2, '#fff');
      return e;
    }
    o += eye(cx - dx, -1) + eye(cx + dx, 1);
    if (c.cheeks !== false) o += ell(cx - dx * 1.5, cy + 6.5 * sc, 3.4 * sc, 2.2 * sc, hsl(c.hue + 330, 80, 70, 0.55)) + ell(cx + dx * 1.5, cy + 6.5 * sc, 3.4 * sc, 2.2 * sc, hsl(c.hue + 330, 80, 70, 0.55));
    var m = c.mouth || 'smile';
    if (m === 'smile') o += '<path d="M' + P([cx - 3.4 * sc, cy + 7 * sc]) + 'Q' + P([cx, cy + 10.5 * sc]) + ' ' + P([cx + 3.4 * sc, cy + 7 * sc]) + '" fill="none" stroke="#1d1b26" stroke-width="' + n1(1.8 * sc) + '" stroke-linecap="round"/>';
    else if (m === 'fang') o += '<path d="M' + P([cx - 4.5 * sc, cy + 7 * sc]) + 'Q' + P([cx, cy + 11 * sc]) + ' ' + P([cx + 4.5 * sc, cy + 7 * sc]) + '" fill="none" stroke="#1d1b26" stroke-width="' + n1(1.8 * sc) + '" stroke-linecap="round"/>' + path('M' + P([cx - 3 * sc, cy + 8.4 * sc]) + 'L' + P([cx - 1.6 * sc, cy + 11.4 * sc]) + 'L' + P([cx - 0.5 * sc, cy + 9.2 * sc]) + 'Z', '#fff') + path('M' + P([cx + 3 * sc, cy + 8.4 * sc]) + 'L' + P([cx + 1.6 * sc, cy + 11.4 * sc]) + 'L' + P([cx + 0.5 * sc, cy + 9.2 * sc]) + 'Z', '#fff');
    else if (m === 'open') o += ell(cx, cy + 9 * sc, 3.6 * sc, 3 * sc, '#3b1a2a') + ell(cx, cy + 10.4 * sc, 2.2 * sc, 1.3 * sc, '#ff7b8a');
    else if (m === 'flat') o += '<path d="M' + P([cx - 3 * sc, cy + 8.5 * sc]) + 'L' + P([cx + 3 * sc, cy + 8.5 * sc]) + '" stroke="#1d1b26" stroke-width="' + n1(1.8 * sc) + '" stroke-linecap="round"/>';
    return o;
  }

  /* ---------- motifs ---------- */
  function pattern(c, pal, cx, cy, w, h, cid) {
    var p = c.pat, o = '', i;
    if (p === 'stripes') for (i = -1; i <= 1; i++) o += path('M' + P([cx + i * w * 0.34 - 3.2, cy - h * 0.5]) + 'Q' + P([cx + i * w * 0.34, cy - h * 0.2]) + ' ' + P([cx + i * w * 0.34 + 3.2, cy - h * 0.5]) + 'Q' + P([cx + i * w * 0.34 + 1, cy - h * 0.1]) + ' ' + P([cx + i * w * 0.34 - 3.2, cy - h * 0.5]) + 'Z', pal.dark, ' opacity=".5"');
    if (p === 'dots') for (i = 0; i < 6; i++) o += circ(cx + ((i * 37) % 5 - 2) * w * 0.18, cy - h * 0.34 + (i % 3) * h * 0.16, 2.2 + (i % 2), pal.light, ' opacity=".7"');
    if (p === 'bolt') o += path('M' + P([cx + 2, cy - h * 0.42]) + 'L' + P([cx - 5, cy - h * 0.12]) + 'L' + P([cx, cy - h * 0.12]) + 'L' + P([cx - 3, cy + h * 0.12]) + 'L' + P([cx + 6, cy - h * 0.2]) + 'L' + P([cx + 1, cy - h * 0.2]) + 'Z', pal.acc, ' opacity=".9"');
    return o;
  }

  /* ---------- parties communes ---------- */
  function hornSet(c, pal, base, k, stage) {   // base : [x, y] côté droit ; k : taille
    var o = '', t = c.horn;
    if (!t || t === 'none') return '';
    function one(side) {
      var x = side > 0 ? base[0] : 120 - base[0], y = base[1], s = side;
      if (t === 'two' || t === 'big') { var L = (t === 'big' ? 20 : 13) * k; return path('M' + P([x - s * 4, y]) + 'Q' + P([x + s * 2, y - L * 0.6]) + ' ' + P([x + s * 5, y - L]) + 'Q' + P([x + s * 7, y - L * 0.4]) + ' ' + P([x + s * 5, y + 1]) + 'Z', pal.belly) + path('M' + P([x - s * 4, y]) + 'Q' + P([x + s * 2, y - L * 0.6]) + ' ' + P([x + s * 5, y - L]) + 'Q' + P([x + s * 2, y - L * 0.3]) + ' ' + P([x - s * 1, y + 1]) + 'Z', pal.light, ' opacity=".7"'); }
      if (t === 'nub') return path('M' + P([x - s * 3, y]) + 'Q' + P([x, y - 8 * k]) + ' ' + P([x + s * 3, y]) + 'Z', pal.belly);
      return '';
    }
    if (t === 'one') { var L1 = 17 * k; return path('M' + P([56, base[1] + 2]) + 'Q' + P([60, base[1] - L1 * 0.5]) + ' ' + P([60, base[1] - L1]) + 'Q' + P([62, base[1] - L1 * 0.4]) + ' ' + P([64, base[1] + 2]) + 'Z', pal.acc); }
    if (t === 'crest') { var j, s2 = ''; for (j = -2; j <= 2; j++) s2 += path('M' + P([60 + j * 6 - 3, base[1] + 1]) + 'Q' + P([60 + j * 6, base[1] - (12 - Math.abs(j) * 2.6) * k]) + ' ' + P([60 + j * 6 + 3, base[1] + 1]) + 'Z', j % 2 ? pal.acc : pal.accD); return s2; }
    return one(1) + one(-1);
  }
  function earSet(c, pal, base, k) {
    var t = c.ears, o = '';
    if (!t || t === 'none') return '';
    function one(side) {
      var x = side > 0 ? base[0] : 120 - base[0], y = base[1], s = side;
      if (t === 'cat') return path('M' + P([x - s * 9, y + 6]) + 'Q' + P([x - s * 5, y - 12 * k]) + ' ' + P([x + s * 2, y - 14 * k]) + 'Q' + P([x + s * 7, y - 6 * k]) + ' ' + P([x + s * 9, y + 8]) + 'Z', pal.base) + path('M' + P([x - s * 5, y + 4]) + 'Q' + P([x - s * 3, y - 7 * k]) + ' ' + P([x + s * 1, y - 9 * k]) + 'Q' + P([x + s * 4, y - 3 * k]) + ' ' + P([x + s * 5, y + 5]) + 'Z', hsl(c.hue + 340, 70, 78));
      if (t === 'long') return path('M' + P([x - s * 5, y + 4]) + 'Q' + P([x - s * 9, y - 22 * k]) + ' ' + P([x - s * 2, y - 26 * k]) + 'Q' + P([x + s * 6, y - 20 * k]) + ' ' + P([x + s * 4, y + 6]) + 'Z', pal.base) + path('M' + P([x - s * 2, y + 2]) + 'Q' + P([x - s * 4, y - 16 * k]) + ' ' + P([x - s * 1, y - 19 * k]) + 'Q' + P([x + s * 3, y - 14 * k]) + ' ' + P([x + s * 2, y + 3]) + 'Z', hsl(c.hue + 340, 70, 80));
      if (t === 'round') return circ(x, y - 3, 8 * k, pal.base) + circ(x, y - 3, 4.6 * k, hsl(c.hue + 340, 70, 80));
      if (t === 'fin') return path('M' + P([x - s * 3, y + 6]) + 'Q' + P([x + s * 4, y - 6]) + ' ' + P([x + s * 12, y - 12 * k]) + 'Q' + P([x + s * 10, y + 2]) + ' ' + P([x + s * 4, y + 9]) + 'Z', pal.acc);
      return '';
    }
    return one(1) + one(-1);
  }
  function wingPair(pal, c, ax, ay, k, col) {   // ailes de chauve-souris/plumes derrière le corps
    var R = [[ax, ay], [ax + 16 * k, ay - 18 * k], [ax + 36 * k, ay - 22 * k], [ax + 30 * k, ay - 8 * k], [ax + 40 * k, ay - 2 * k], [ax + 28 * k, ay + 6 * k], [ax + 32 * k, ay + 16 * k], [ax + 14 * k, ay + 10 * k], [ax + 4 * k, ay + 12 * k]];
    var Lw = mirror(R);
    return path(smoothQ(R), col || pal.accD, ' opacity=".95"') + path(smoothQ(Lw), col || pal.accD, ' opacity=".95"') + path(smoothQ(scaleAbout(R, [ax, ay], 0.7)), pal.acc, ' opacity=".55"') + path(smoothQ(scaleAbout(Lw, [120 - ax, ay], 0.7)), pal.acc, ' opacity=".55"');
  }
  function tailPath(c, pal, bx, by, k) {
    var t = c.tail, s = c.tailSide || 1;
    if (!t || t === 'none') return '';
    if (t === 'curl') return path('M' + P([bx, by]) + 'C' + P([bx + s * 18 * k, by + 2]) + ' ' + P([bx + s * 26 * k, by - 16 * k]) + ' ' + P([bx + s * 14 * k, by - 22 * k]) + 'C' + P([bx + s * 20 * k, by - 12 * k]) + ' ' + P([bx + s * 14 * k, by - 4]) + ' ' + P([bx, by - 7]) + 'Z', pal.base);
    if (t === 'spike') return path('M' + P([bx, by - 6]) + 'Q' + P([bx + s * 20 * k, by + 4]) + ' ' + P([bx + s * 30 * k, by - 6 * k]) + 'Q' + P([bx + s * 22 * k, by - 10]) + ' ' + P([bx + s * 22 * k, by - 14]) + 'Q' + P([bx + s * 14 * k, by - 12]) + ' ' + P([bx, by - 10]) + 'Z', pal.base) + path('M' + P([bx + s * 26 * k, by - 4 * k]) + 'L' + P([bx + s * 36 * k, by - 12 * k]) + 'L' + P([bx + s * 30 * k, by + 2]) + 'Z', pal.acc);
    if (t === 'flame') return path('M' + P([bx, by]) + 'Q' + P([bx + s * 14 * k, by - 4]) + ' ' + P([bx + s * 18 * k, by - 16 * k]) + 'Q' + P([bx + s * 22 * k, by - 4]) + ' ' + P([bx + s * 12 * k, by + 4]) + 'Q' + P([bx + s * 6, by + 8]) + ' ' + P([bx, by + 4]) + 'Z', '#ff8a3d') + path('M' + P([bx + s * 3, by]) + 'Q' + P([bx + s * 11 * k, by - 2]) + ' ' + P([bx + s * 14 * k, by - 10 * k]) + 'Q' + P([bx + s * 15 * k, by - 2]) + ' ' + P([bx + s * 9, by + 2]) + 'Z', '#ffd36a');
    return '';
  }
  function halo(pal, cx, cy, rx, col) {
    return '<ellipse cx="' + n1(cx) + '" cy="' + n1(cy) + '" rx="' + n1(rx) + '" ry="' + n1(rx * 0.26) + '" fill="none" stroke="' + (col || '#ffd45e') + '" stroke-width="3" opacity=".95"/><ellipse cx="' + n1(cx) + '" cy="' + n1(cy) + '" rx="' + n1(rx) + '" ry="' + n1(rx * 0.26) + '" fill="none" stroke="#fff" stroke-width="1" opacity=".6"/>';
  }
  function plates(pal, pts, col) { return pts.map(function (p) { return path(smoothQ([[p[0] - 5, p[1] - 3], [p[0], p[1] - 5], [p[0] + 5, p[1] - 3], [p[0] + 4, p[1] + 3], [p[0] - 4, p[1] + 3]]), col || pal.deep, ' opacity=".9"') + path('M' + P([p[0] - 3, p[1] - 2]) + 'L' + P([p[0] + 3, p[1] - 2]) + '" stroke="#fff" stroke-opacity=".35" stroke-width="1', 'none'); }).join(''); }

  /* ---------- silhouettes ---------- */
  var ARCH = {
    blob: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, cx = 60, o = '';
      var body = smoothQ(scaleAbout([[60, 32], [84, 38], [96, 62], [94, 88], [80, 102], [60, 105], [40, 102], [26, 88], [24, 62], [36, 38]], [60, 72], k));
      o += tailPath(c, pal, 92, 92, k);
      o += ell(44, 104, 11 * k, 5, pal.dark) + ell(76, 104, 11 * k, 5, pal.dark);
      o += earSet(c, pal, [38, 42], k);
      o += hornSet(c, pal, [44, 38], k, st);
      o += path(body, 'url(#g' + c._u + ')');
      o += path(smoothQ(scaleAbout([[60, 66], [78, 72], [80, 90], [60, 98], [40, 90], [42, 72]], [60, 82], k)), pal.belly, ' opacity=".55"');
      o += pattern(c, pal, 60, 84, 36, 40);
      o += path('M' + P([36, 52]) + 'Q' + P([44, 40]) + ' ' + P([58, 38]) + '" fill="none" stroke="#fff" stroke-opacity=".5" stroke-width="3" stroke-linecap="round', 'none');
      o += face(c, 60, 64, 1, pal, st);
      return o;
    },
    golem: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, o = '', cx = 60;
      o += ell(60, 108, 34 * k, 4, 'rgba(0,0,0,.18)');
      o += hornSet(c, pal, [40, 34], k, st);
      var armL = [[20, 56], [28, 50], [34, 62], [32, 84], [22, 90], [14, 78]];
      o += path(smoothQ(armL), pal.dark) + path(smoothQ(mirror(armL)), pal.dark);
      o += circ(23, 90, 8 * k, pal.base) + circ(97, 90, 8 * k, pal.base);
      var legs = [[38, 92], [52, 92], [52, 108], [36, 108]];
      o += path(smoothQ(legs), pal.dark) + path(smoothQ(mirror(legs)), pal.dark);
      var body = smoothQ(scaleAbout([[36, 34], [60, 28], [84, 34], [94, 60], [88, 96], [60, 102], [32, 96], [26, 60]], [60, 66], k));
      o += path(body, 'url(#g' + c._u + ')');
      o += path('M' + P([30, 70]) + 'Q' + P([60, 78]) + ' ' + P([90, 70]) + '" fill="none" stroke="' + pal.deep + '" stroke-opacity=".45" stroke-width="2', 'none');
      o += path('M' + P([44, 40]) + 'L' + P([50, 56]) + 'L' + P([42, 68]) + '" fill="none" stroke="' + pal.deep + '" stroke-opacity=".35" stroke-width="1.6" stroke-linecap="round', 'none');
      o += pattern(c, pal, 60, 92, 40, 40);
      if (st >= 2) o += plates(pal, [[34, 44], [86, 44], [60, 96]], pal.acc);
      if (st >= 3) o += plates(pal, [[26, 66], [94, 66], [60, 36]], pal.accD);
      o += face(c, 60, 56, 1.05, pal, st);
      return o;
    },
    beast: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, o = '';
      o += ell(60, 110, 28 * k, 4, 'rgba(0,0,0,.18)');
      o += tailPath(c, pal, 80, 98, k);
      var body = smoothQ(scaleAbout([[44, 74], [76, 74], [86, 94], [82, 108], [38, 108], [34, 94]], [60, 92], k));
      o += path(body, pal.dark);
      o += path(smoothQ(scaleAbout([[52, 82], [68, 82], [72, 100], [60, 106], [48, 100]], [60, 94], k)), pal.belly, ' opacity=".8"');
      o += ell(46, 108, 9 * k, 5, pal.base) + ell(74, 108, 9 * k, 5, pal.base);
      if (st >= 3) o += wingPair(pal, c, 78, 88, 0.9, pal.accD);
      o += earSet(c, pal, [38, 38], k);
      o += hornSet(c, pal, [42, 32], k, st);
      var head = smoothQ(scaleAbout([[60, 24], [86, 34], [94, 56], [84, 76], [60, 82], [36, 76], [26, 56], [34, 34]], [60, 54], k));
      o += path(head, 'url(#g' + c._u + ')');
      o += path(smoothQ(scaleAbout([[48, 62], [60, 58], [72, 62], [74, 74], [60, 80], [46, 74]], [60, 68], k)), pal.belly, ' opacity=".75"');
      o += pattern(c, pal, 60, 56, 40, 36);
      o += path('M' + P([36, 40]) + 'Q' + P([46, 30]) + ' ' + P([58, 28]) + '" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round', 'none');
      o += circ(60, 66, 2.8, '#3a2230') ;
      o += face(c, 60, 58, 1, pal, st).replace(/<path d="M[^"]*" fill="none" stroke="#1d1b26" stroke-width="1.8"/, function (m) { return m; });
      if (st >= 2) o += path(smoothQ([[34, 78], [44, 86], [60, 90], [76, 86], [86, 78], [76, 82], [60, 84], [44, 82]]), pal.acc, ' opacity=".9"');
      return o;
    },
    bird: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, o = '';
      o += ell(60, 110, 24 * k, 4, 'rgba(0,0,0,.18)');
      var wing = [[28, 58], [14, 66], [10, 84], [22, 94], [34, 86], [36, 68]];
      o += tailPath(c, pal, 78, 98, k);
      o += path(smoothQ(scaleAbout(wing, [40, 76], k)), pal.dark) + path(smoothQ(scaleAbout(mirror(wing), [80, 76], k)), pal.dark);
      if (st >= 3) o += wingPair(pal, c, 30, 66, 1.0, pal.accD);
      o += path('M' + P([48, 100]) + 'L' + P([46, 110]) + 'M' + P([72, 100]) + 'L' + P([74, 110]) + '" stroke="#e8a23a" stroke-width="3" stroke-linecap="round', 'none');
      o += hornSet(c, pal, [48, 34], k, st);
      var body = smoothQ(scaleAbout([[60, 28], [84, 38], [94, 64], [86, 92], [60, 104], [34, 92], [26, 64], [36, 38]], [60, 68], k));
      o += path(body, 'url(#g' + c._u + ')');
      o += path(smoothQ(scaleAbout([[60, 66], [78, 72], [76, 92], [60, 100], [44, 92], [42, 72]], [60, 84], k)), pal.belly, ' opacity=".85"');
      o += pattern(c, pal, 60, 84, 36, 40);
      o += path('M' + P([54, 66]) + 'L' + P([66, 66]) + 'L' + P([60, 76]) + 'Z', '#ffb43a') + path('M' + P([56, 67]) + 'L' + P([64, 67]) + 'L' + P([60, 71]) + 'Z', '#ffd36a');
      o += path('M' + P([34, 44]) + 'Q' + P([44, 34]) + ' ' + P([58, 32]) + '" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round', 'none');
      var f = face(c, 60, 56, 1, pal, st).replace(/<path d="M[^"]*Q[^"]*" fill="none" stroke="#1d1b26" stroke-width="1\.8[^>]*>/, '');
      o += f;
      return o;
    },
    drake: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, o = '';
      o += ell(60, 110, 30 * k, 4, 'rgba(0,0,0,.18)');
      o += wingPair(pal, c, 38, 70, st >= 2 ? 1.05 : 0.8, pal.accD);
      o += tailPath(Object.assign({}, c, { tail: c.tail === 'none' ? 'spike' : c.tail }), pal, 84, 98, k);
      var body = smoothQ(scaleAbout([[44, 70], [76, 70], [88, 92], [80, 108], [40, 108], [32, 92]], [60, 90], k));
      o += path(body, pal.dark);
      o += path(smoothQ(scaleAbout([[52, 76], [68, 76], [74, 98], [60, 106], [46, 98]], [60, 92], k)), pal.belly, ' opacity=".9"');
      o += ell(44, 108, 9 * k, 5, pal.base) + ell(76, 108, 9 * k, 5, pal.base);
      o += hornSet(Object.assign({}, c, { horn: c.horn === 'none' || !c.horn ? 'two' : c.horn }), pal, [42, 34], k, st);
      var head = smoothQ(scaleAbout([[60, 26], [84, 36], [92, 56], [86, 72], [74, 80], [60, 82], [46, 80], [34, 72], [28, 56], [36, 36]], [60, 54], k));
      o += path(head, 'url(#g' + c._u + ')');
      o += path(smoothQ(scaleAbout([[46, 62], [60, 58], [74, 62], [76, 74], [60, 80], [44, 74]], [60, 68], k)), pal.belly, ' opacity=".85"');
      o += circ(55, 68, 1.6, pal.deep) + circ(65, 68, 1.6, pal.deep);
      o += pattern(c, pal, 60, 56, 40, 36);
      o += path('M' + P([36, 42]) + 'Q' + P([46, 32]) + ' ' + P([58, 30]) + '" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="3" stroke-linecap="round', 'none');
      o += face(c, 60, 56, 1, pal, st);
      if (st >= 3) o += plates(pal, [[60, 84], [60, 94]], pal.acc);
      return o;
    },
    spirit: function (c, pal, st) {
      var k = 1 + (st - 1) * 0.07, o = '';
      var tail = [[60, 30], [80, 40], [90, 62], [84, 82], [92, 98], [80, 110], [66, 98], [60, 112], [54, 98], [40, 110], [28, 98], [36, 82], [30, 62], [40, 40]];
      o += circ(60, 66, 44 * k, hsl(c.hue, 70, 70, 0.14));
      o += path(smoothQ(scaleAbout(tail, [60, 72], k)), 'url(#g' + c._u + ')');
      o += path(smoothQ(scaleAbout([[60, 48], [76, 58], [78, 78], [60, 96], [42, 78], [44, 58]], [60, 74], k)), pal.light, ' opacity=".35"');
      o += earSet(c, pal, [40, 44], k);
      o += hornSet(c, pal, [46, 32], k, st);
      o += pattern(c, pal, 60, 88, 34, 40);
      var hands = path(smoothQ([[28, 70], [36, 66], [40, 74], [34, 82], [26, 78]]), pal.light, ' opacity=".9"') + path(smoothQ(mirror([[28, 70], [36, 66], [40, 74], [34, 82], [26, 78]])), pal.light, ' opacity=".9"');
      o += hands;
      o += face(c, 60, 62, 1.05, pal, st);
      if (st >= 2) o += '<path d="M' + P([22, 40]) + 'l3,-6l3,6l-3,6z M' + P([98, 50]) + 'l3,-6l3,6l-3,6z" fill="' + pal.acc + '" opacity=".9"/>';
      return o;
    }
  };

  /* ---------- assemblage ---------- */
  function svg(c, stage, opt) {
    opt = opt || {};
    var st = Math.max(1, Math.min(3, stage || 1)), pal = palette(c), r = RAR[c.rar] || RAR.C, id = ++UID, o = '';
    c = Object.assign({}, c, { _u: id });
    var defs = '<defs><radialGradient id="g' + id + '" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="' + pal.light + '"/><stop offset=".55" stop-color="' + pal.base + '"/><stop offset="1" stop-color="' + pal.dark + '"/></radialGradient>'
      + '<radialGradient id="a' + id + '" cx="50%" cy="55%" r="55%"><stop offset="0" stop-color="' + r.col + '" stop-opacity="' + (0.25 + r.glow * 0.5).toFixed(2) + '"/><stop offset="1" stop-color="' + r.col + '" stop-opacity="0"/></radialGradient></defs>';
    if (opt.silhouette) {
      var body = ARCH[c.arch](c, pal, 1);
      return '<svg viewBox="0 0 120 120" style="overflow:visible" class="crea" role="img" aria-label="Esprit inconnu"><g style="filter:brightness(0) opacity(.28)">' + defs.replace(/stop-color="[^"]*"/g, 'stop-color="#000"') + body + '</g></svg>';
    }
    if (!opt.bare) o += '<circle cx="60" cy="66" r="58" fill="url(#a' + id + ')"/>';
    if (!opt.bare && r.spark) { var i; for (i = 0; i < r.spark; i++) { var a = i * 2.399 + id, rr = 40 + (i % 3) * 8; o += '<path d="M' + P([60 + rr * cos(a), 66 + rr * 0.9 * sin(a)]) + 'm0,-3l1,2l2,1l-2,1l-1,2l-1,-2l-2,-1l2,-1z" fill="' + r.col + '" opacity=".85"/>'; } }
    if (st >= 3) o += halo(pal, 60, 14, 17, r.col);
    o += ARCH[c.arch](c, pal, st);
    return '<svg viewBox="0 0 120 120" style="overflow:visible" class="crea" role="img" aria-label="' + (c.name || 'Esprit').replace(/"/g, '') + '">' + defs + o + '</svg>';
  }

  window.CREA = { svg: svg, RAR: RAR, palette: palette, ARCH: ARCH };
})();
