/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Fonte : personnage articulé en SVG (vue de profil et vue de face).
 * Le corps est construit à partir d'un squelette : les membres sont des « tubes » à profil anatomique,
 * les bras et les jambes se placent par cinématique inverse (la main reste sur la barre, le pied reste au sol),
 * et les muscles travaillés s'allument en couleur d'accent au rythme de l'effort.
 * API : FIG.svg(spec, opts) -> chaîne SVG statique ; FIG.live(svgEl, spec, opts) -> boucle d'animation.
 */
(function () {
  'use strict';
  var RAD = Math.PI / 180, sin = Math.sin, cos = Math.cos, sqrt = Math.sqrt, PI = Math.PI;
  var FLOOR = 92, CLIP_N = 0;

  /* ------------------------------------------------------------ petits outils vectoriels */
  function add(a, b) { return [a[0] + b[0], a[1] + b[1]]; }
  function sub(a, b) { return [a[0] - b[0], a[1] - b[1]]; }
  function mul(a, k) { return [a[0] * k, a[1] * k]; }
  function len(a) { return sqrt(a[0] * a[0] + a[1] * a[1]); }
  function unit(a) { var l = len(a) || 1; return [a[0] / l, a[1] / l]; }
  function lerp(a, b, t) { return a + (b - a) * t; }
  function lerp2(a, b, t) { return [lerp(a[0], b[0], t), lerp(a[1], b[1], t)]; }
  function smoothstep(a, b, x) { var t = Math.max(0, Math.min(1, (x - a) / (b - a))); return t * t * (3 - 2 * t); }
  function n1(x) { return (Math.round(x * 10) / 10).toString(); }
  function P(p) { return n1(p[0]) + ',' + n1(p[1]); }

  /* spline fermée / ouverte passant par les points (Catmull-Rom converti en Bézier) */
  function smoothCut(fr, bk) {   // deux flancs lissés reliés par des coupes droites (vêtements)
    var d = smooth(fr, false), b = bk.slice().reverse(), n = b.length, i, p0, p1, p2, p3;
    d += 'L' + P(b[0]);
    for (i = 0; i < n - 1; i++) {
      p0 = b[Math.max(i - 1, 0)]; p1 = b[i]; p2 = b[i + 1]; p3 = b[Math.min(i + 2, n - 1)];
      d += 'C' + P([p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]) + ' ' + P([p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]) + ' ' + P(p2);
    }
    return d + 'Z';
  }
  function smooth(pts, closed) {
    var n = pts.length, d = 'M' + P(pts[0]), i, p0, p1, p2, p3, c1, c2, last = closed ? n : n - 1;
    for (i = 0; i < last; i++) {
      p0 = pts[closed ? (i - 1 + n) % n : Math.max(i - 1, 0)]; p1 = pts[i]; p2 = pts[(i + 1) % n];
      p3 = pts[closed ? (i + 2) % n : Math.min(i + 2, n - 1)];
      c1 = [p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6];
      c2 = [p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6];
      d += 'C' + P(c1) + ' ' + P(c2) + ' ' + P(p2);
    }
    return d + (closed ? 'Z' : '');
  }

  /* profil par stations [[t, avant, arrière], ...] -> [avant, arrière] */
  function prof(arr, t) {
    if (t <= arr[0][0]) return [arr[0][1], arr[0][2]];
    for (var i = 1; i < arr.length; i++) {
      if (t <= arr[i][0]) {
        var a = arr[i - 1], b = arr[i], k = (t - a[0]) / (b[0] - a[0]);
        k = k * k * (3 - 2 * k) * 0.6 + k * 0.4;
        return [lerp(a[1], b[1], k), lerp(a[2], b[2], k)];
      }
    }
    var z = arr[arr.length - 1]; return [z[1], z[2]];
  }

  /* ------------------------------------------------------------ corps (proportions) */
  var BODY = {
    m: {
      sc: 1, neck: 3.2, torso: 24, upper: 13.6, fore: 12, thigh: 19.6, shank: 18.6, ankle: 4,
      spine: [[-4.5, 3.8, 4.4], [-1, 6.2, 5.0], [3, 5.2, 5.0], [8, 4.1, 4.7], [12, 4.3, 4.5], [16, 5.3, 5.5], [20, 6.0, 6.4], [24, 5.0, 4.8], [27, 3.4, 3.6], [29, 2.7, 2.8]],
      thigh_p: [[0, 5.0, 5.4], [0.3, 5.7, 5.2], [0.62, 5.0, 4.5], [1, 3.5, 3.5]],
      shank_p: [[0, 3.5, 3.5], [0.22, 3.4, 4.5], [0.6, 2.8, 3.4], [1, 2.0, 2.0]],
      upper_p: [[0, 3.7, 3.7], [0.3, 3.6, 3.4], [0.7, 2.9, 3.0], [1, 2.5, 2.5]],
      fore_p: [[0, 2.6, 2.6], [0.28, 2.9, 2.9], [1, 1.8, 1.8]],
      neckR: 2.7, hair: 'short', head: 1
    },
    f: {
      sc: 1, neck: 3.2, torso: 24, upper: 13.6, fore: 12, thigh: 19.6, shank: 18.6, ankle: 4,
      spine: [[-4.5, 4.4, 4.6], [-1, 5.5, 6.0], [3, 5.2, 5.2], [8, 4.4, 4.2], [12, 4.2, 3.9], [16, 4.5, 5.0], [19.5, 4.6, 6.4], [24, 4.6, 4.2], [27, 3.2, 3.0], [29, 2.4, 2.4]],
      thigh_p: [[0, 5.2, 5.8], [0.3, 5.5, 5.4], [0.62, 4.6, 4.6], [1, 3.2, 3.2]],
      shank_p: [[0, 3.2, 3.2], [0.22, 3.1, 4.0], [0.6, 2.5, 3.0], [1, 1.8, 1.8]],
      upper_p: [[0, 3.2, 3.2], [0.3, 3.1, 3.0], [0.7, 2.5, 2.6], [1, 2.2, 2.2]],
      fore_p: [[0, 2.3, 2.3], [0.28, 2.5, 2.5], [1, 1.6, 1.6]],
      neckR: 2.3, hair: 'pony', head: 0.96
    }
  };
  var FOOT = [[-2.9, -1.6], [-3.7, 1.4], [-3.3, 4.0], [7.2, 4.0], [9.4, 3.2], [8.8, 1.8], [5, 0.7], [2.4, -1.0], [0.4, -1.8]];
  var HEAD = [[-5.0, 1.3], [-4.6, 4.6], [-1.6, 6.5], [2.4, 5.7], [4.2, 3.7], [4.7, 2.2], [5.8, 0.4], [4.9, -0.7], [5.0, -1.9], [4.1, -4.3], [1.6, -5.3], [-2.6, -4.8], [-4.5, -2.0]];
  var HAIR_M = [[-5.4, 0.6], [-5.1, 4.8], [-1.8, 7.0], [2.8, 6.2], [4.6, 4.0], [3.2, 3.6], [0.4, 3.9], [-2.2, 2.6], [-3.1, -0.4]];
  var HAIR_F = [[-5.5, -0.8], [-5.2, 4.8], [-1.8, 7.2], [3.0, 6.4], [4.7, 4.0], [3.0, 3.4], [0.2, 3.8], [-2.4, 1.6], [-3.4, -2.2], [-4.8, -3.6]];

  /* ------------------------------------------------------------ cinématique */
  /* IK à deux os : racine R, cible T, longueurs a et b, côté du coude/genou (bend = ±1, relatif à la normale avant) */
  function ik2(R, T, a, b, bend, f) {
    var d = sub(T, R), l = len(d), u = unit(d), x, h, n;
    if (l > a + b - 0.01) { l = a + b - 0.01; T = add(R, mul(u, l)); }
    if (l < Math.abs(a - b) + 0.01) l = Math.abs(a - b) + 0.01;
    x = (a * a - b * b + l * l) / (2 * l); h = sqrt(Math.max(0, a * a - x * x));
    n = [u[1] * f, -u[0] * f];
    return { mid: add(add(R, mul(u, x)), mul(n, h * bend)), end: add(R, mul(u, l)) };
  }
  function dirFK(theta, f) { return [f * sin(theta * RAD), cos(theta * RAD)]; }   // 0 = vers le bas, + = vers l'avant
  function frontNormal(d, f) { return [d[1] * f, -d[0] * f]; }

  /* ------------------------------------------------------------ construction de formes */
  function tubeSeg(A, B, arr, f, o) {
    o = o || {};
    var d = unit(sub(B, A)), n = frontNormal(d, f), L = len(sub(B, A)), N = 10, i, t, c, pr, fr = [], bk = [], infl = o.infl || 0, avg;
    for (i = 0; i <= N; i++) {
      t = i / N; c = add(A, mul(d, L * t)); pr = prof(arr, t);
      fr.push(add(c, mul(n, pr[0] + infl))); bk.push(sub(c, mul(n, pr[1] + infl)));
    }
    pr = prof(arr, 1); avg = (pr[0] + pr[1]) / 2;
    var out = fr.slice();
    if (o.capE !== false) out.push(add(B, mul(d, avg * 0.62 + infl)));
    out = out.concat(bk.reverse());
    if (o.capS) { pr = prof(arr, 0); out.push(sub(A, mul(d, (pr[0] + pr[1]) / 2 * 0.6))); }
    return smooth(out, true);
  }
  function tubeRange(A, B, arr, f, t0, t1, infl) {   // portion d'un membre (pour les vêtements)
    var P0 = lerp2(A, B, t0), P1 = lerp2(A, B, t1), sub2 = arr.map(function (r) { return [(r[0] - t0) / (t1 - t0), r[1], r[2]]; });
    var a = prof(arr, t0), b = prof(arr, t1);
    sub2 = [[0, a[0], a[1]]].concat(arr.filter(function (r) { return r[0] > t0 && r[0] < t1; }).map(function (r) { return [(r[0] - t0) / (t1 - t0), r[1], r[2]]; }), [[1, b[0], b[1]]]);
    var d = unit(sub(P1, P0)), n = frontNormal(d, f), L = len(sub(P1, P0)), N = 8, fr = [], bk = [], i, t, c, pr;
    for (i = 0; i <= N; i++) { t = i / N; c = add(P0, mul(d, L * t)); pr = prof(sub2, t); fr.push(add(c, mul(n, pr[0] + (infl || 0)))); bk.push(sub(c, mul(n, pr[1] + (infl || 0)))); }
    return smoothCut(fr, bk);
  }
  function circle(c, r) { return 'M' + n1(c[0] - r) + ',' + n1(c[1]) + 'a' + n1(r) + ',' + n1(r) + ' 0 1 0 ' + n1(2 * r) + ',0a' + n1(r) + ',' + n1(r) + ' 0 1 0 ' + n1(-2 * r) + ',0Z'; }

  /* patch musculaire sur un membre : zone entre t0 et t1, côté 'f' avant, 'b' arrière, 'fb' les deux */
  function limbPatch(A, B, arr, f, t0, t1, side, k0, k1) {
    var d = unit(sub(B, A)), n = frontNormal(d, f), L = len(sub(B, A)), N = 9, i, t, w, c, pr, inner = [], outer = [];
    for (i = 0; i <= N; i++) {
      t = t0 + (t1 - t0) * i / N; w = Math.pow(sin(PI * i / N), 0.4); c = add(A, mul(d, L * t)); pr = prof(arr, t);
      if (side === 'f') { inner.push(add(c, mul(n, pr[0] * k0 * w))); outer.push(add(c, mul(n, pr[0] * k1 * w))); }
      else if (side === 'b') { inner.push(sub(c, mul(n, pr[1] * k0 * w))); outer.push(sub(c, mul(n, pr[1] * k1 * w))); }
      else { inner.push(sub(c, mul(n, pr[1] * k1 * w))); outer.push(add(c, mul(n, pr[0] * k1 * w))); }
    }
    return smooth(outer.concat(inner.reverse()), true);
  }

  /* ------------------------------------------------------------ résolution d'une pose de profil */
  function solveSide(p, B, f) {
    var sc = B.sc, g = {}, H = p.hip, tau = (p.tor || 0), bet = (p.bend || 0), u0 = [f * sin(tau * RAD), -cos(tau * RAD)], u1 = [f * sin((tau + bet) * RAD), -cos((tau + bet) * RAD)];
    // colonne : intégration le long de la tangente (mélange u0 -> u1 autour de la taille)
    function tang(s) { var k = smoothstep(7, 19, s); return unit(lerp2(u0, u1, k)); }
    var SP = [], step = 0.5, i0 = 12;   // positions de la colonne de s = -6 à 33 (index = (s + 6) * 2)
    (function () {
      var pos = H, s, k;
      SP[i0] = H;
      for (k = i0 + 1, s = 0; k <= 78; k++, s += step) { pos = add(pos, mul(tang(s + step / 2), step * sc)); SP[k] = pos; }
      pos = H; for (k = i0 - 1, s = 0; k >= 0; k--, s -= step) { pos = sub(pos, mul(tang(0), step * sc)); SP[k] = pos; }
    })();
    function spinePos(s) { var x = (Math.max(-6, Math.min(33, s)) + 6) * 2, i = Math.floor(x), fr = x - i; return i >= 78 ? SP[78] : lerp2(SP[i], SP[i + 1], fr); }
    g.spinePos = spinePos; g.tang = function (s) { return tang(Math.max(0, s)); };
    g.S = spinePos(B.torso); g.NB = spinePos(B.torso + 4.5);
    var tn = tang(B.torso), nk = (tau + bet + (p.neck || 0)), nd = [f * sin(nk * RAD), -cos(nk * RAD)];
    g.nd = nd; g.head = add(g.NB, mul(nd, (B.neck + 4.5) * sc * B.head));
    g.fv = [-nd[1] * f, nd[0] * f];
    g.H = H; g.f = f; g.sc = sc;
    // membres : near / far
    function limb(spec, root, l1, l2, kind) {
      var o = {}, lim1 = l1 * sc, lim2 = l2 * sc, th1, th2, e, w, tgt;
      if (spec.ik) {
        tgt = spec.ik === 'bar' ? p.bar : spec.ik;
        var r = ik2(root, tgt, lim1, lim2, spec.bend == null ? 1 : spec.bend, f); o.mid = r.mid; o.end = r.end;
      } else {
        th1 = spec.a[0]; th2 = kind === 'leg' ? th1 - spec.a[1] : th1 + spec.a[1];
        o.mid = add(root, mul(dirFK(th1, f), lim1)); o.end = add(o.mid, mul(dirFK(th2, f), lim2));
      }
      o.root = root; return o;
    }
    var shoulder = g.S, hipFar = add(H, [-f * 0.3, 0]);
    var armN = p.arm || { a: [0, 5] }, armF = p.arm2 || armN, legN = p.leg || { a: [0, 0] }, legF = p.leg2 || legN;
    g.armN = limb(armN, shoulder, B.upper, B.fore, 'arm'); g.armF = limb(armF, add(shoulder, [-f * 0.8, -0.4]), B.upper, B.fore, 'arm');
    g.legN = limb(legN, H, B.thigh, B.shank, 'leg'); g.legF = limb(legF, hipFar, B.thigh, B.shank, 'leg');
    g.footN = footGeom(g.legN, legN, p, f, 0); g.footF = footGeom(g.legF, legF, p, f, 1);
    return g;
  }
  function footGeom(leg, spec, p, f, far) {
    var sd = unit(sub(leg.end, leg.mid)), n = frontNormal(sd, f), ft = (far ? (p.ft2 != null ? p.ft2 : p.ft) : p.ft) || 0, al = -ft * f * RAD;
    var fd = [n[0] * cos(al) - n[1] * sin(al), n[0] * sin(al) + n[1] * cos(al)], up = [fd[1] * f * -1, fd[0] * f];
    // repère du pied : x = avant (fd), y = bas (perpendiculaire côté sol)
    var down = [-fd[1] * f, fd[0] * f];
    // le bas du pied est du côté opposé à la jambe (vers le sol quand la jambe est verticale)
    if (down[0] * sd[0] + down[1] * sd[1] < 0) down = mul(down, -1);
    return { A: leg.end, fd: fd, dn: down };
  }

  /* ------------------------------------------------------------ dessin d'un corps de profil */
  var PATCH_SIDE = {
    // muscle -> liste de patches : [partie, t0, t1, côté, k0, k1] ; pour le tronc : ['torso', s0, s1, côté, k0, k1]
    quadriceps: [['thigh', 0.14, 0.92, 'f', 0.28, 0.92]],
    ischios: [['thigh', 0.1, 0.92, 'b', 0.28, 0.92]],
    mollets: [['shank', 0.04, 0.62, 'b', 0.28, 0.92]],
    fessiers: [['torso', -3.5, 5.5, 'b', 0.28, 0.94], ['thigh', 0.0, 0.2, 'b', 0.28, 0.92]],
    biceps: [['upper', 0.12, 0.88, 'f', 0.28, 0.92]],
    triceps: [['upper', 0.1, 0.88, 'b', 0.28, 0.92]],
    avantbras: [['fore', 0.06, 0.78, 'fb', 0, 0.85]],
    pectoraux: [['torso', 15, 25, 'f', 0.28, 0.94]],
    abdos: [['torso', 2.5, 14.5, 'f', 0.28, 0.92]],
    dos: [['torso', 10, 25, 'b', 0.28, 0.94]],
    lombaires: [['torso', 1, 11, 'b', 0.28, 0.94]],
    trapezes: [['torso', 21, 29, 'b', 0.28, 0.94]],
    obliques: [['torso', 4, 14, 'f', 0.28, 0.92]],
    epaules: [['delt']]
  };

  function drawSide(spec, p, opt) {
    var f = spec.f || 1, B = BODY[opt.g || 'm'], g = solveSide(p, B, f), out = [], sc = B.sc, i, m, pt, fx = p.fx || 0;
    function path(d, cls, extra) { out.push('<path class="' + cls + '" d="' + d + '"' + (extra || '') + '/>'); }
    function torsoPts(s0, s1, infl, noCap) {   // contour du tronc entre deux stations
      var st = B.spine.filter(function (r) { return r[0] > s0 && r[0] < s1; }), rows = [[s0].concat(prof2(B.spine, s0))].concat(st, [[s1].concat(prof2(B.spine, s1))]), fr = [], bk = [];
      rows.forEach(function (r) { var c = g.spinePos(r[0] * 1), tn = g.tang(Math.max(0, r[0])), d = mul(tn, -1), n = frontNormal(d, f); fr.push(add(c, mul(n, (r[2] * sc + infl)))); bk.push(sub(c, mul(n, (r[1] * sc + infl)))); });
      if (!noCap) {
        var top = rows[rows.length - 1], tc = g.spinePos(top[0]), td = g.tang(top[0]), bt = rows[0], bc = g.spinePos(bt[0]), btd = g.tang(bt[0]);
        fr.push(add(tc, mul(td, 1.2))); bk.unshift(sub(bc, mul(btd, 1.2)));
        return smooth(fr.concat(bk.slice(1).reverse()).concat([bk[0]]), true);
      }
      return smoothCut(fr, bk);
    }
    function prof2(arr, s) {
      if (s <= arr[0][0]) return [arr[0][1], arr[0][2]];
      for (var j = 1; j < arr.length; j++) if (s <= arr[j][0]) { var a = arr[j - 1], b = arr[j], k = (s - a[0]) / (b[0] - a[0]); return [lerp(a[1], b[1], k), lerp(a[2], b[2], k)]; }
      var z = arr[arr.length - 1]; return [z[1], z[2]];
    }
    function torsoPatch(s0, s1, side, k0, k1) {
      var N = 10, inner = [], outer = [], j, s, w, c, tn, n, pr;
      for (j = 0; j <= N; j++) {
        s = s0 + (s1 - s0) * j / N; w = Math.pow(sin(PI * j / N), 0.4); c = g.spinePos(s); tn = g.tang(Math.max(0, s)); n = frontNormal(mul(tn, -1), f); pr = prof2(B.spine, s);
        if (side === 'f') { inner.push(add(c, mul(n, pr[1] * sc * k0 * w))); outer.push(add(c, mul(n, pr[1] * sc * k1 * w))); }
        else { inner.push(sub(c, mul(n, pr[0] * sc * k0 * w))); outer.push(sub(c, mul(n, pr[0] * sc * k1 * w))); }
      }
      return smooth(outer.concat(inner.reverse()), true);
    }
    // ------ ordre de dessin
    var floorY = FLOOR;
    // ombre et décor
    (spec.scene || []).forEach(function (s) { out.push(sceneEl(s, p, g)); });
    // bras du fond
    path(tubeSeg(g.armF.root, g.armF.mid, mapP(B.upper_p, sc), f, { capS: true, capE: false }), 'fbk');
    path(tubeSeg(g.armF.mid, g.armF.end, mapP(B.fore_p, sc), f, { capE: false }), 'fbk');
    path(circle(g.armF.mid, prof(mapP(B.upper_p, sc), 1)[0]), 'fbk');
    path(handPath(g.armF, f, sc), 'fbk');
    // jambe du fond
    path(tubeSeg(g.legF.root, g.legF.mid, mapP(B.thigh_p, sc), f, { capS: true, capE: false }), 'fbk');
    path(tubeSeg(g.legF.mid, g.legF.end, mapP(B.shank_p, sc), f, { capE: false }), 'fbk');
    path(circle(g.legF.mid, Math.max(prof(mapP(B.thigh_p, sc), 1)[0], prof(mapP(B.shank_p, sc), 0)[0])), 'fbk');
    path(footPath(g.footF, f, sc), 'fsh2');
    // tronc, jambe proche, puis vêtements découpés par la silhouette (clip) : coupes nettes et alignées
    var uid = 'c' + (++CLIP_N), torsoD = torsoPts(-4.5, B.torso + 4.6, 0), thighN = tubeSeg(g.legN.root, g.legN.mid, mapP(B.thigh_p, sc), f, { capS: true, capE: false }),
      thighF = tubeSeg(g.legF.root, g.legF.mid, mapP(B.thigh_p, sc), f, { capS: true, capE: false });
    function bandTorso(s0, s1, W) {
      var fr = [], bk = [], j, n = 4, s, c, d, nn;
      for (j = 0; j <= n; j++) { s = s0 + (s1 - s0) * j / n; c = g.spinePos(s); d = mul(g.tang(Math.max(0, s)), -1); nn = frontNormal(d, f); fr.push(add(c, mul(nn, W))); bk.push(sub(c, mul(nn, W))); }
      return 'M' + fr.concat(bk.reverse()).map(P).join('L') + 'Z';
    }
    function bandLimb(A, Bp, t0, t1, W) {
      var d = unit(sub(Bp, A)), nn = frontNormal(d, f), L = len(sub(Bp, A)), p0 = add(A, mul(d, L * t0)), p1 = add(A, mul(d, L * t1));
      return 'M' + [add(p0, mul(nn, W)), add(p1, mul(nn, W)), sub(p1, mul(nn, W)), sub(p0, mul(nn, W))].map(P).join('L') + 'Z';
    }
    out.push('<clipPath id="' + uid + 'a"><path d="' + torsoD + '"/><path d="' + thighN + '"/></clipPath><clipPath id="' + uid + 'b"><path d="' + torsoD + '"/></clipPath><clipPath id="' + uid + 'c"><path d="' + thighF + '"/></clipPath>');
    path(torsoD, 'fb');
    path(thighN, 'fb');
    path(tubeSeg(g.legN.mid, g.legN.end, mapP(B.shank_p, sc), f, { capE: false }), 'fb');
    path(circle(g.legN.mid, Math.max(prof(mapP(B.thigh_p, sc), 1)[0], prof(mapP(B.shank_p, sc), 0)[0]) * 1.0), 'fb');
    out.push('<g clip-path="url(#' + uid + 'a)"><path class="fcl" d="' + bandTorso(-6, 2.8, 9) + '"/><path class="fcl" d="' + bandLimb(g.legN.root, g.legN.mid, -0.1, 0.36, 9) + '"/></g>');
    if (spec.top !== false) out.push('<g clip-path="url(#' + uid + 'b)"><path class="fcl2" d="' + bandTorso(8.5, B.torso + 0.4, 9) + '"/></g>');
    path(footPath(g.footN, f, sc), 'fsh');
    // cou + tête
    path(tubeSeg(g.NB, add(g.NB, mul(g.nd, (B.neck + 1.2) * sc)), [[0, B.neckR * sc, B.neckR * sc], [1, B.neckR * sc * 0.92, B.neckR * sc * 0.92]], f), 'fb');
    var hs = B.head;
    function hp(lx, ly) { return add(g.head, add(mul(g.fv, lx * hs), mul(g.nd, ly * hs))); }
    path(smooth(HEAD.map(function (q) { return hp(q[0], q[1]); }), true), 'fb');
    path(smooth((B.hair === 'pony' ? HAIR_F : HAIR_M).map(function (q) { return hp(q[0], q[1]); }), true), 'fhr');
    if (B.hair === 'pony') {
      var base = hp(-4.8, 2.4), D = g.fv[1] < -0.6 ? g.nd : unit(add(mul([0, 1], 0.72), mul(g.fv, -0.28))), N = [-D[1], D[0]];   // allongée sur le dos : la queue repose sur le banc
      path(smooth([add(base, mul(N, 1.9)), add(add(base, mul(D, 3.6)), mul(N, 2.4)), add(base, mul(D, 8.8)), add(add(base, mul(D, 3.4)), mul(N, -2.1)), add(base, mul(N, -1.7))], true), 'fhr');
    }
    // muscles (derrière le bras proche, par-dessus le tronc et les jambes)
    var act = spec.muscles || [], alpha = (0.04 + 0.96 * Math.pow(Math.max(0, Math.min(1, fx)), 1.4)).toFixed(2);
    function patches(list, near) {
      list.forEach(function (key) {
        (PATCH_SIDE[key] || []).forEach(function (q) {
          var d;
          if (q[0] === 'delt') { var dd = unit(sub(g.armN.mid, g.armN.root)); d = ellipsePath(add(g.armN.root, mul(dd, 2.6 * sc)), 3.5 * sc, 6.2 * sc, Math.atan2(-dd[0], dd[1]) / RAD); }
          else if (q[0] === 'torso') d = torsoPatch(q[1], q[2], q[3] === 'b' ? 'b' : 'f', q[4], q[5]);
          else {
            var map = { thigh: [g.legN.root, g.legN.mid, B.thigh_p], shank: [g.legN.mid, g.legN.end, B.shank_p], upper: [g.armN.root, g.armN.mid, B.upper_p], fore: [g.armN.mid, g.armN.end, B.fore_p] }[q[0]];
            d = limbPatch(map[0], map[1], mapP(map[2], sc), f, q[1], q[2], q[3], q[4], q[5]);
          }
          out.push('<path class="fm" d="' + d + '" style="opacity:' + alpha + '"/>');
        });
      });
    }
    if (act.length) patches(act);
    // bras proche
    path(tubeSeg(g.armN.root, g.armN.mid, mapP(B.upper_p, sc), f, { capS: true, capE: false }), 'fb');
    path(tubeSeg(g.armN.mid, g.armN.end, mapP(B.fore_p, sc), f, { capE: false }), 'fb');
    path(circle(g.armN.mid, prof(mapP(B.upper_p, sc), 1)[0] * 1.0), 'fb');
    path(handPath(g.armN, f, sc), 'fb');
    if (act.length) {   // muscles des bras par-dessus la peau du bras
      var armOnly = act.filter(function (k) { return k === 'biceps' || k === 'triceps' || k === 'avantbras' || k === 'epaules'; });
      patches(armOnly);
    }
    // accessoires devant
    (spec.props || []).forEach(function (pr) { out.push(propEl(pr, p, g, f, B)); });
    return out.join('');
  }
  function mapP(arr, sc) { return arr.map(function (r) { return [r[0], r[1] * sc, r[2] * sc]; }); }
  function handPath(arm, f, sc) {
    var d = unit(sub(arm.end, arm.mid)), e = add(arm.end, mul(d, 4.6 * sc)), n = frontNormal(d, f);
    return smooth([add(arm.end, mul(n, 1.9 * sc)), add(lerp2(arm.end, e, 0.6), mul(n, 2.3 * sc)), add(e, mul(d, 0.5)), sub(lerp2(arm.end, e, 0.6), mul(n, 2.1 * sc)), sub(arm.end, mul(n, 1.7 * sc))], true);
  }
  function footPath(ft, f, sc) {
    return smooth(FOOT.map(function (q) { return add(ft.A, add(mul(ft.fd, q[0] * sc), mul(ft.dn, q[1] * sc))); }), true);
  }

  /* ------------------------------------------------------------ décor et accessoires */
  function sceneEl(s, p, g) {
    var t = s.t;
    if (t === 'floor') return '<path class="fsh0" d="M' + (s.x1 == null ? 4 : s.x1) + ',' + FLOOR + 'H' + (s.x2 == null ? 156 : s.x2) + '" />' + (s.shadow === false ? '' : '<ellipse class="fsd" cx="' + n1(s.sx == null ? g.H[0] : s.sx) + '" cy="' + (FLOOR + 1.2) + '" rx="' + (s.rx || 22) + '" ry="2.2"/>');
    if (t === 'bench') { var x = s.x, w = s.w, y = s.y, hh = s.h || 5; return '<g class="fpr"><rect x="' + x + '" y="' + y + '" width="' + w + '" height="' + hh + '" rx="2.4"/><path class="fprl" d="M' + (x + 6) + ',' + (y + hh) + 'V' + FLOOR + 'M' + (x + w - 6) + ',' + (y + hh) + 'V' + FLOOR + '"/></g>'; }
    if (t === 'rect') return '<rect class="fpr" x="' + s.x + '" y="' + s.y + '" width="' + s.w + '" height="' + s.h + '" rx="' + (s.r == null ? 1.5 : s.r) + '"/>';
    if (t === 'line') return '<path class="fprl" d="M' + s.x1 + ',' + s.y1 + 'L' + s.x2 + ',' + s.y2 + '"/>';
    if (t === 'path') return '<path class="' + (s.c || 'fprl') + '" d="' + s.d + '"/>';
    if (t === 'circ') return '<circle class="' + (s.c || 'fpr') + '" cx="' + s.x + '" cy="' + s.y + '" r="' + s.r + '"/>';
    return '';
  }
  function handPt(g, near) { var a = near === false ? g.armF : g.armN, d = unit(sub(a.end, a.mid)); return add(a.end, mul(d, 2.6)); }
  function propEl(pr, p, g, f, B) {
    var t = pr.t, at;
    if (t === 'plate' || t === 'db') {
      var r = pr.r || (t === 'db' ? 4.2 : 8), pts = pr.at === 'bar' ? [p.bar] : Array.isArray(pr.at) ? [pr.at] : pr.hand === 'both' ? [handPt(g, false), handPt(g)] : [handPt(g)];
      return pts.map(function (a) { return '<g class="fpl"><circle cx="' + n1(a[0]) + '" cy="' + n1(a[1]) + '" r="' + r + '"/><circle class="fhub" cx="' + n1(a[0]) + '" cy="' + n1(a[1]) + '" r="' + n1(Math.max(1.1, r * 0.2)) + '"/></g>'; }).join('');
    }
    if (t === 'cable') {
      at = pr.to === 'hands' || !pr.to ? handPt(g) : pr.to;
      return '<path class="fcab" d="M' + P(pr.from) + 'L' + P(at) + '"/>';
    }
    if (t === 'line') { var a = pr.a === 'hands' ? handPt(g) : pr.a, b = pr.b === 'hands' ? handPt(g) : pr.b; return '<path class="fcab" d="M' + P(a) + 'L' + P(b) + '"/>'; }
    if (t === 'handle') { var h = handPt(g); return '<circle class="fhub" cx="' + n1(h[0]) + '" cy="' + n1(h[1]) + '" r="1.8"/>'; }
    return '';
  }

  /* ------------------------------------------------------------ vue de face / de dos */
  var FB = {
    m: { sw: 11.0, hipx: 4.4, tw: [[-4.6, 7.4], [-1, 8.7], [3, 8.4], [8, 7.3], [12, 7.5], [16, 8.7], [20, 9.9], [23.5, 10.9], [26, 8.4], [28, 4.8], [29.6, 2.8]], thigh_p: [[0, 5.5, 4.6], [0.3, 5.9, 4.3], [0.65, 4.8, 3.8], [1, 3.3, 3.3]], shank_p: [[0, 3.3, 3.3], [0.25, 3.7, 3.0], [0.6, 2.9, 2.6], [1, 1.9, 1.9]], upper_p: [[0, 3.8, 3.6], [0.3, 3.6, 3.2], [0.7, 2.9, 2.7], [1, 2.4, 2.4]], fore_p: [[0, 2.5, 2.4], [0.28, 2.9, 2.6], [1, 1.7, 1.7]], neckR: 2.8, head: [4.6, 6.0] },
    f: { sw: 9.4, hipx: 4.7, tw: [[-4.6, 8.0], [-1, 9.7], [3, 9.3], [8, 6.9], [12, 6.0], [16, 7.2], [20, 8.2], [23.5, 9.4], [26, 7.4], [28, 4.2], [29.6, 2.4]], thigh_p: [[0, 5.5, 4.8], [0.3, 5.6, 4.5], [0.65, 4.5, 3.8], [1, 3.0, 3.0]], shank_p: [[0, 3.0, 3.0], [0.25, 3.3, 2.9], [0.6, 2.6, 2.4], [1, 1.7, 1.7]], upper_p: [[0, 3.3, 3.1], [0.3, 3.1, 2.8], [0.7, 2.5, 2.4], [1, 2.1, 2.1]], fore_p: [[0, 2.2, 2.1], [0.28, 2.5, 2.3], [1, 1.5, 1.5]], neckR: 2.3, head: [4.3, 5.8] }
  };
  function interpS(arr, s) {
    if (s <= arr[0][0]) return arr[0][1];
    for (var j = 1; j < arr.length; j++) if (s <= arr[j][0]) { var a = arr[j - 1], b = arr[j], k = (s - a[0]) / (b[0] - a[0]); k = k * k * (3 - 2 * k); return lerp(a[1], b[1], k); }
    return arr[arr.length - 1][1];
  }
  var HEADF = [[0, 6.0], [2.6, 5.4], [4.2, 3.2], [4.5, 0.4], [3.8, -2.6], [2.3, -4.8], [0, -5.9], [-2.3, -4.8], [-3.8, -2.6], [-4.5, 0.4], [-4.2, 3.2], [-2.6, 5.4]];
  var HAIRF_M = [[-4.9, 2.4], [-4.6, 5.1], [0, 7.0], [4.6, 5.1], [4.9, 2.4], [3.7, 3.7], [1.2, 4.6], [-1.6, 4.4], [-3.7, 3.6]];
  var HAIRF_F = [[-5.2, -4.6], [-5.3, 2.4], [-4.7, 5.3], [0, 7.2], [4.7, 5.3], [5.3, 2.4], [5.2, -4.6], [3.9, -5.2], [3.9, 2.3], [2.2, 4.3], [-0.6, 4.6], [-3.6, 3.4], [-3.9, 2.3], [-3.9, -5.2]];
  var HAIRB_M = [[-4.8, -2.6], [-5.0, 2.4], [-4.5, 5.4], [0, 7.1], [4.5, 5.4], [5.0, 2.4], [4.8, -2.6], [2.8, -4.3], [0, -4.0], [-2.8, -4.3]];
  var HAIRB_F = [[-5.3, -7.5], [-5.4, 2.4], [-4.7, 5.4], [0, 7.2], [4.7, 5.4], [5.4, 2.4], [5.3, -7.5], [2.6, -8.8], [-2.6, -8.8]];

  /* formes des muscles du tronc en (s, fraction de demi-largeur), moitié droite ; la gauche en est le miroir */
  var TORSO_M = {
    front: {
      pectoraux: [[[24.8, 0.1], [25.2, 0.6], [23.8, 0.93], [21, 0.98], [18.3, 0.86], [16.8, 0.55], [17.4, 0.14], [21, 0.05]]],
      abdos: [[[14.8, 0.05], [14.9, 0.33], [12.7, 0.35], [12.6, 0.05]], [[12.2, 0.05], [12.3, 0.36], [10.1, 0.36], [10, 0.05]], [[9.6, 0.05], [9.7, 0.36], [7.5, 0.35], [7.4, 0.05]], [[7.0, 0.05], [7.1, 0.34], [4.9, 0.32], [4.8, 0.05]], [[4.4, 0.05], [4.5, 0.3], [2.6, 0.26], [2.5, 0.05]]],
      obliques: [[[14.2, 0.44], [14.6, 0.78], [10.5, 0.95], [5.5, 0.92], [3.6, 0.66], [6.5, 0.5], [11, 0.46]]],
      trapezes: [[[28.4, 0.22], [27.2, 0.62], [25.2, 1.0], [24.2, 0.84], [26.2, 0.5], [27.6, 0.2]]]
    },
    back: {
      trapezes: [[[28.6, 0.1], [27.4, 0.55], [25.2, 0.96], [22.5, 0.62], [18.5, 0.22], [16.8, 0.05], [21, 0.04], [25, 0.05]]],
      dos: [[[22.6, 0.5], [22.2, 1.0], [18.5, 0.98], [13.5, 0.8], [10.2, 0.48], [12, 0.26], [16, 0.4], [19.8, 0.52]], [[24.4, 0.14], [24.6, 0.72], [22.8, 0.6], [22.0, 0.18]]],
      lombaires: [[[12.4, 0.05], [12.6, 0.3], [8, 0.34], [3.2, 0.26], [2.6, 0.05]]],
      fessiers: [[[2.6, 0.05], [3.0, 0.8], [0.5, 0.97], [-2.6, 0.86], [-4.0, 0.5], [-3.6, 0.06]]],
      obliques: [[[11.5, 0.5], [11.6, 0.95], [6, 0.93], [4.2, 0.68], [8, 0.52]]]
    }
  };

  function solveFront(p, B, f) {
    var sc = B.sc || 1, g = { sc: sc }, lean = (p.lean || 0) * RAD, up = [sin(lean), -cos(lean)], rt = [cos(lean), sin(lean)], H = p.hip;
    g.H = H; g.up = up; g.rt = rt;
    function sp(s) { return add(H, mul(up, s * sc)); }
    g.sp = sp;
    g.shR = add(sp(23.8), mul(rt, B.sw * sc)); g.shL = sub(sp(23.8), mul(rt, B.sw * sc));
    function limb(spec, root, l1, l2, side) {
      var o = { root: root, side: side }, th1, th2, d1, d2;
      if (spec.ik) {
        var tgt = spec.ik === 'bar' ? p.bar : spec.ik, r = ik2(root, tgt, l1 * sc, l2 * sc, (spec.bend == null ? 1 : spec.bend) * side, 1);
        o.mid = r.mid; o.end = r.end; return o;
      }
      th1 = spec.a[0]; th2 = th1 + (spec.a[1] || 0);
      d1 = [side * sin(th1 * RAD), cos(th1 * RAD)]; d2 = [side * sin(th2 * RAD), cos(th2 * RAD)];
      o.mid = add(root, mul(d1, l1 * sc)); o.end = add(o.mid, mul(d2, l2 * sc)); return o;
    }
    var aR = p.armR || p.arm || { a: [6, 4] }, aL = p.armL || p.arm || { a: [6, 4] }, lR = p.legR || p.leg || { a: [3, 0] }, lL = p.legL || p.leg || { a: [3, 0] };
    g.armR = limb(aR, g.shR, B.upper, B.fore, 1); g.armL = limb(aL, g.shL, B.upper, B.fore, -1);
    g.legR = limb(lR, add(H, mul(rt, B.hipx * sc)), B.thigh, B.shank, 1); g.legL = limb(lL, sub(H, mul(rt, B.hipx * sc)), B.thigh, B.shank, -1);
    var nb = sp(B.torso + 4.6); g.NB = nb; g.head = add(nb, mul(up, 7.6 * sc));
    return g;
  }
  function shoeF(A, side, sc, rot) {
    var pts = [[-3.2, -1.8], [-3.9, 1.4], [-2.4, 4.3], [2.6, 4.4], [4.4, 2.6], [3.9, -1.8]], r = (rot == null ? 10 : rot) * RAD * side;
    return smooth(pts.map(function (q) { var x = q[0] * side * 1, y = q[1], cx = x * cos(r) - y * sin(r), cy = x * sin(r) + y * cos(r); return [A[0] + cx * sc, A[1] + cy * sc + 1.0 * sc]; }), true);
  }
  var FRONT_MUSCLES = {   // muscle -> patches de membres [partie, t0, t1, côté, k0, k1]
    quadriceps: { front: [['thigh', 0.12, 0.9, 'fb', 0, 0.86]] },
    adducteurs: { front: [['thigh', 0.08, 0.66, 'b', 0.2, 0.92]] },
    ischios: { back: [['thigh', 0.1, 0.9, 'fb', 0, 0.86]] },
    mollets: { back: [['shank', 0.06, 0.62, 'fb', 0, 0.9]], front: [['shank', 0.08, 0.7, 'fb', 0.1, 0.78]] },
    biceps: { front: [['upper', 0.14, 0.88, 'fb', 0, 0.84]] },
    triceps: { back: [['upper', 0.1, 0.88, 'fb', 0, 0.86]] },
    avantbras: { front: [['fore', 0.06, 0.8, 'fb', 0, 0.84]], back: [['fore', 0.06, 0.8, 'fb', 0, 0.84]] }
  };
  function torsoMirror(poly, g, B, sign) {
    return poly.map(function (q) { var hw = interpS(B.tw, q[0]) * g.sc; return add(g.sp(q[0]), mul(g.rt, sign * q[1] * hw)); });
  }
  /* renvoie { muscle: [chemins d] } pour une vue donnée */
  function frontPatches(g, B, view) {
    var res = {}, key, sc = g.sc;
    function put(k, d) { (res[k] = res[k] || []).push(d); }
    var tm = TORSO_M[view];
    Object.keys(tm).forEach(function (k) { tm[k].forEach(function (poly) { [1, -1].forEach(function (sg) { put(k, smooth(torsoMirror(poly, g, B, sg), true)); }); }); });
    // épaules : deltoïdes
    [g.armR, g.armL].forEach(function (A) {
      var dd = unit(sub(A.mid, A.root)), c = add(A.root, mul(dd, 3.4 * sc));
      put('epaules', ellipsePath(c, 3.6 * sc, 6.2 * sc, Math.atan2(-dd[0], dd[1]) / RAD));
    });
    Object.keys(FRONT_MUSCLES).forEach(function (k) {
      var list = FRONT_MUSCLES[k][view]; if (!list) return;
      list.forEach(function (q) {
        [[g.legR, B.thigh, B.shank, 1], [g.legL, B.thigh, B.shank, -1], [g.armR, B.upper, B.fore, 1], [g.armL, B.upper, B.fore, -1]].forEach(function (it) {
          var part = q[0], A, Bp, arr;
          if (part === 'thigh' && it[0] === g.legR || part === 'thigh' && it[0] === g.legL) { A = it[0].root; Bp = it[0].mid; arr = B.thigh_p; }
          else if (part === 'shank' && (it[0] === g.legR || it[0] === g.legL)) { A = it[0].mid; Bp = it[0].end; arr = B.shank_p; }
          else if (part === 'upper' && (it[0] === g.armR || it[0] === g.armL)) { A = it[0].root; Bp = it[0].mid; arr = B.upper_p; }
          else if (part === 'fore' && (it[0] === g.armR || it[0] === g.armL)) { A = it[0].mid; Bp = it[0].end; arr = B.fore_p; }
          else return;
          put(k, limbPatch(A, Bp, mapP(arr, sc), it[3], q[1], q[2], q[3], q[4], q[5]));
        });
      });
    });
    return res;
  }
  function ellipsePath(c, rx, ry, rot) {
    var pts = [], i, a, r = (rot || 0) * RAD; for (i = 0; i < 10; i++) { a = i / 10 * 2 * PI; var x = rx * cos(a), y = ry * sin(a); pts.push([c[0] + x * cos(r) - y * sin(r), c[1] + x * sin(r) + y * cos(r)]); }
    return smooth(pts, true);
  }

  /* corps de face ou de dos ; patches : fonction (muscle, chemins) -> chaîne SVG (ou null pour le style d'exercice) */
  function drawFront(spec, p, opt) {
    var B0 = BODY[opt.g || 'm'], B = FB[opt.g || 'm'], view = opt.view || (spec && spec.view === 'back' ? 'back' : 'front'), out = [], sc = B0.sc;
    B = Object.assign({}, B, { sc: sc, torso: 24, upper: B0.upper, fore: B0.fore, thigh: B0.thigh, shank: B0.shank });
    var g = solveFront(p, B, 1), tw = B.tw;
    function path(d, cls, extra) { out.push('<path class="' + cls + '" d="' + d + '"' + (extra || '') + '/>'); }
    (spec && spec.scene || []).forEach(function (s) { out.push(sceneEl(s, p, { H: g.H })); });
    // jambes
    [[g.legL, -1], [g.legR, 1]].forEach(function (it) {
      var L = it[0], sd = it[1];
      path(tubeSeg(L.root, L.mid, mapP(B.thigh_p, sc), sd, { capS: true, capE: false }), 'fb');
      path(tubeSeg(L.mid, L.end, mapP(B.shank_p, sc), sd, { capE: false }), 'fb');
      path(circle(L.mid, Math.max(prof(mapP(B.thigh_p, sc), 1)[0], prof(mapP(B.shank_p, sc), 0)[0])), 'fb');
      path(shoeF(L.end, sd, sc, opt.footRot), 'fsh');
    });
    // tronc
    var rows = [-4.6, -1, 3, 8, 12, 16, 20, 23.5, 26, 28, 29.6], fr = [], bk = [];
    rows.forEach(function (s) { var c = g.sp(s), w = interpS(tw, s) * sc; fr.push(add(c, mul(g.rt, w))); bk.push(sub(c, mul(g.rt, w))); });
    var torsoD = smooth(fr.concat([add(g.sp(-6.2), mul(g.rt, 0.5)), sub(g.sp(-6.2), mul(g.rt, 0.5))].slice(0, 0)).concat(bk.slice().reverse()), true);
    var hipRound = [add(g.sp(-4.6), mul(g.rt, interpS(tw, -4.6) * sc)), add(g.sp(-6.4), mul(g.rt, 3 * sc)), add(g.sp(-6.8), [0, 0]), sub(g.sp(-6.4), mul(g.rt, 3 * sc)), sub(g.sp(-4.6), mul(g.rt, interpS(tw, -4.6) * sc))];
    torsoD = smooth(fr.slice(1).concat(bk.slice(1).reverse()).concat([bk[0]]).concat(hipRound.slice(1, 4)).concat([fr[0]]).slice(0, 0).concat(fr.slice().concat(bk.slice().reverse())), true);
    var fullTorso = smooth([].concat(fr.slice(1), bk.slice(1).reverse()).length ? fr.slice(1).concat(bk.slice(1).reverse()) : [], true);
    var pts = fr.slice().reverse(); // du cou vers le bas côté droit
    var outline = [];
    for (var i = fr.length - 1; i >= 0; i--) outline.push(fr[i]);
    outline.push(add(g.sp(-6.3), mul(g.rt, 2.6 * sc)), g.sp(-6.8), sub(g.sp(-6.3), mul(g.rt, 2.6 * sc)));
    for (i = 0; i < bk.length; i++) outline.push(bk[i]);
    torsoD = smooth(outline, true);
    path(torsoD, 'fb');
    var uid = 'k' + (++CLIP_N);
    function bandF(s0, s1, W) { return 'M' + [add(g.sp(s0), mul(g.rt, W)), add(g.sp(s1), mul(g.rt, W)), sub(g.sp(s1), mul(g.rt, W)), sub(g.sp(s0), mul(g.rt, W))].map(P).join('L') + 'Z'; }
    function bandL(A, Bp, t0, t1, W) { var d = unit(sub(Bp, A)), nn = [d[1], -d[0]], L = len(sub(Bp, A)), p0 = add(A, mul(d, L * t0)), p1 = add(A, mul(d, L * t1)); return 'M' + [add(p0, mul(nn, W)), add(p1, mul(nn, W)), sub(p1, mul(nn, W)), sub(p0, mul(nn, W))].map(P).join('L') + 'Z'; }
    var thR = tubeSeg(g.legR.root, g.legR.mid, mapP(B.thigh_p, sc), 1, { capS: true, capE: false }), thL = tubeSeg(g.legL.root, g.legL.mid, mapP(B.thigh_p, sc), -1, { capS: true, capE: false });
    out.push('<clipPath id="' + uid + 'a"><path d="' + torsoD + '"/><path d="' + thR + '"/><path d="' + thL + '"/></clipPath><clipPath id="' + uid + 'b"><path d="' + torsoD + '"/></clipPath>');
    out.push('<g clip-path="url(#' + uid + 'a)"><path class="fcl" d="' + bandF(-7, 2.9, 14) + '"/><path class="fcl" d="' + bandL(g.legR.root, g.legR.mid, -0.1, 0.36, 9) + '"/><path class="fcl" d="' + bandL(g.legL.root, g.legL.mid, -0.1, 0.36, 9) + '"/></g>');
    if (!spec || spec.top !== false) out.push('<g clip-path="url(#' + uid + 'b)"><path class="fcl2" d="' + bandF(9, 24.4, 14) + '"/></g>');
    // détails anatomiques légers
    out.push(frontDetails(g, B, view));
    // cou
    path(tubeSeg(g.NB, add(g.NB, mul(g.up, 4.2 * sc)), [[0, B.neckR * sc, B.neckR * sc], [1, B.neckR * sc * 0.92, B.neckR * sc * 0.92]], 1), 'fb');
    // tête
    var hs = B0.head, hw = B.head[0] / 4.6;
    function hp(q) { return add(g.head, add(mul(g.rt, q[0] * hs * hw), mul(g.up, q[1] * hs))); }
    path(smooth(HEADF.map(hp), true), 'fb');
    var hairD = view === 'back' ? (B0.hair === 'pony' ? HAIRB_F : HAIRB_M) : (B0.hair === 'pony' ? HAIRF_F : HAIRF_M);
    path(smooth(hairD.map(hp), true), 'fhr');
    // bras
    [[g.armL, -1], [g.armR, 1]].forEach(function (it) {
      var A = it[0], sd = it[1];
      path(tubeSeg(A.root, A.mid, mapP(B.upper_p, sc), sd, { capS: true, capE: false }), 'fb');
      path(tubeSeg(A.mid, A.end, mapP(B.fore_p, sc), sd, { capE: false }), 'fb');
      path(circle(A.mid, prof(mapP(B.upper_p, sc), 1)[0]), 'fb');
      path(circle(A.root, 3.6 * sc), 'fb');
      var dd = unit(sub(A.end, A.mid)), hand = add(A.end, mul(dd, 4.3 * sc));
      path(smooth([add(A.end, mul([dd[1], -dd[0]], 1.9 * sc)), add(lerp2(A.end, hand, 0.6), mul([dd[1], -dd[0]], 2.2 * sc)), add(hand, mul(dd, 0.6)), sub(lerp2(A.end, hand, 0.6), mul([dd[1], -dd[0]], 2.2 * sc)), sub(A.end, mul([dd[1], -dd[0]], 1.7 * sc))], true), 'fb');
    });
    // muscles
    var pat = frontPatches(g, B, view);
    if (opt.patches) { out.push(opt.patches(pat)); }
    else {
      var fx = p.fx || 0, alpha = (0.04 + 0.96 * Math.pow(Math.max(0, Math.min(1, fx)), 1.4)).toFixed(2);
      ((spec && spec.muscles) || []).forEach(function (k) { (pat[k] || []).forEach(function (d) { out.push('<path class="fm" d="' + d + '" style="opacity:' + alpha + '"/>'); }); });
    }
    (spec && spec.props || []).forEach(function (pr) { out.push(propFront(pr, p, g, B)); });
    return out.join('');
  }
  function frontDetails(g, B, view) {
    var sc = g.sc, o = [], sp = g.sp, rt = g.rt, c;
    function line(pts) { o.push('<path class="fln" d="' + smooth(pts, false) + '"/>'); }
    if (view === 'front') {
      [1, -1].forEach(function (sg) {
        line([add(sp(26.6), mul(rt, sg * 1.4 * sc)), add(sp(26.0), mul(rt, sg * 5.5 * sc)), add(sp(25.0), mul(rt, sg * 9.0 * sc))]);   // clavicule
      });
      line([sp(25.4), sp(2.4)].map(function (q, i) { return q; }));   // ligne médiane
      c = sp(3.4); o.push('<circle class="flh" cx="' + n1(c[0]) + '" cy="' + n1(c[1]) + '" r="0.5"/>');
    } else {
      line([sp(28.6), sp(18), sp(2.2)]);   // colonne
      [1, -1].forEach(function (sg) { line([add(sp(22.4), mul(rt, sg * 1.6 * sc)), add(sp(19.5), mul(rt, sg * 5.4 * sc)), add(sp(15), mul(rt, sg * 5.0 * sc))]); });
    }
    return o.join('');
  }
  function propFront(pr, p, g, B) {
    var t = pr.t, a, b;
    function hand(A) { var d = unit(sub(A.end, A.mid)); return add(A.end, mul(d, 2.4)); }
    if (t === 'db') { return [g.armL, g.armR].map(function (A) { var h = hand(A); return '<g class="fdb"><rect x="' + n1(h[0] - 2.2) + '" y="' + n1(h[1] - 3.4) + '" width="4.4" height="6.8" rx="1.2"/><path d="M' + n1(h[0] - 2.2) + ',' + n1(h[1]) + 'H' + n1(h[0] + 2.2) + '"/></g>'; }).join(''); }
    if (t === 'barH') { a = hand(g.armL); b = hand(g.armR); var ext = pr.ext == null ? 12 : pr.ext, y = (a[1] + b[1]) / 2, x0 = Math.min(a[0], b[0]) - ext, x1 = Math.max(a[0], b[0]) + ext;
      return '<path class="fcab2" d="M' + n1(x0) + ',' + n1(y) + 'H' + n1(x1) + '"/><rect class="fpl2" x="' + n1(x0 + 1.4) + '" y="' + n1(y - 6.5) + '" width="2.6" height="13" rx="1"/><rect class="fpl2" x="' + n1(x1 - 4) + '" y="' + n1(y - 6.5) + '" width="2.6" height="13" rx="1"/>'; }
    if (t === 'cable') { var tgt = pr.to === 'handL' ? hand(g.armL) : hand(g.armR); return '<path class="fcab" d="M' + P(pr.from) + 'L' + P(tgt) + '"/>'; }
    if (t === 'handles') { return [g.armL, g.armR].map(function (A) { var h = hand(A); return '<circle class="fhub" cx="' + n1(h[0]) + '" cy="' + n1(h[1]) + '" r="1.8"/>'; }).join(''); }
    return '';
  }

  var ZONE_POSE = { hip: [80, 50], lean: 0, arm: { a: [10, 3] }, leg: { a: [4, 0] }, fx: 0 };
  /* corps statique de face ou de dos pour l'onglet Zones : wrap(patches) renvoie le balisage des zones cliquables */
  function zoneBody(view, g, wrap) { return drawFront({ view: view }, ZONE_POSE, { g: g, view: view, patches: wrap, footRot: 8 }); }
  /* ------------------------------------------------------------ interpolation des poses */
  function deepMerge(a, b) {
    if (b == null) return a; if (a == null) return b;
    if (Array.isArray(a) || Array.isArray(b) || typeof b !== 'object') return b;
    var o = {}, k; for (k in a) o[k] = a[k]; for (k in b) o[k] = deepMerge(a[k], b[k]); return o;
  }
  function blend(a, b, t) {
    if (typeof a === 'number' && typeof b === 'number') return lerp(a, b, t);
    if (Array.isArray(a) && Array.isArray(b) && a.length === b.length) return a.map(function (v, i) { return blend(v, b[i], t); });
    if (a && b && typeof a === 'object' && typeof b === 'object' && !Array.isArray(a)) {
      var o = {}, k; for (k in a) o[k] = k in b ? blend(a[k], b[k], t) : a[k]; for (k in b) if (!(k in a)) o[k] = b[k]; return o;
    }
    return t < 0.5 ? a : b;
  }
  function prepare(spec) {
    if (spec._k) return spec;
    var pk = [], fk = [];
    spec.keys.forEach(function (k) {
      if (k.p) pk.push({ t: k.t, p: deepMerge(spec.base || {}, k.p) });
      var fx = k.fx != null ? k.fx : (k.p && k.p.fx != null ? k.p.fx : (spec.base && spec.base.fx != null && k.p ? spec.base.fx : null));
      if (fx != null) fk.push({ t: k.t, v: fx });
    });
    spec._k = pk; spec._f = fk; spec._T = spec.keys[spec.keys.length - 1].t; return spec;
  }
  function ease(k) { return 0.5 - 0.5 * cos(PI * Math.max(0, Math.min(1, k))); }
  function track(ks, t, get) {
    var i; for (i = 1; i < ks.length; i++) if (t <= ks[i].t) break;
    if (i >= ks.length) i = ks.length - 1;
    var a = ks[i - 1], b = ks[i], k = b.t === a.t ? 1 : (t - a.t) / (b.t - a.t);
    return [a, b, ease(k)];
  }
  function poseAt(spec, time) {
    prepare(spec);
    var T = spec._T, t = ((time % T) + T) % T, r = track(spec._k, t), p = blend(r[0].p, r[1].p, r[2]);
    if (spec._f.length) { var q = track(spec._f, t); p.fx = lerp(q[0].v, q[1].v, q[2]); }
    return p;
  }

  /* ------------------------------------------------------------ API */
  function sideSvg(spec, time, opt) {
    opt = opt || {};
    return (spec.view === 'front' || spec.view === 'back' ? drawFront : drawSide)(spec, poseAt(spec, time), opt);
  }
  /* animation : un <svg data-fig="slug"> dont le premier enfant <g> est redessiné ~30 fois par seconde tant qu'il est à l'écran */
  function live(svg, spec, opt) {
    var g = svg.firstElementChild, t0 = null, off = 0, paused = false, last = 0;
    svg.addEventListener('click', function () { paused = !paused; if (!paused) t0 = null; });
    function tick(now) {
      if (!svg.isConnected) return;
      if (!paused && !document.hidden && now - last > 32) {
        var r = svg.getBoundingClientRect();
        if (r.bottom > 0 && r.top < (window.innerHeight || 800)) {
          if (t0 === null) t0 = now - off * 1000;
          off = (now - t0) / 1000; last = now;
          g.innerHTML = sideSvg(spec, off, opt());
        }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }
  function scan() {
    var list = document.querySelectorAll('svg[data-fig]:not([data-on])'), i, el, spec;
    for (i = 0; i < list.length; i++) {
      el = list[i]; el.setAttribute('data-on', '1'); spec = window.FIGDATA && window.FIGDATA[el.getAttribute('data-fig')];
      if (spec) live(el, spec, function () { return { g: window.FIG_GENDER || 'm' }; });
    }
  }
  var STYLE_ID = 'fig-style';
  var VB_SIDE = '0 0 160 100';

  window.FIG = { solveSide: solveSide, zoneBody: zoneBody, live: live, scan: scan, RAD: RAD, FLOOR: FLOOR, smooth: smooth, tubeSeg: tubeSeg, limbPatch: limbPatch, circle: circle, prof: prof, mapP: mapP, BODY: BODY, poseAt: poseAt, prepare: prepare, sideSvg: sideSvg, drawFront: drawFront, frontPatches: frontPatches, solveFront: solveFront, FB: FB, VB_SIDE: VB_SIDE, add: add, sub: sub, mul: mul, unit: unit, lerp2: lerp2, frontNormal: frontNormal, ik2: ik2, dirFK: dirFK, P: P, n1: n1, HEAD: HEAD, HAIR_M: HAIR_M, HAIR_F: HAIR_F, deepMerge: deepMerge, blend: blend };
})();
