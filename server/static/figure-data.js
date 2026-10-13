/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Animations des exercices du catalogue de départ, par identifiant (slug).
 * Chaque animation est une suite de poses clés (t en secondes) ; le moteur (figure.js) interpole et résout les articulations.
 * Coordonnées : 160 x 100, sol à y = 92, personnage de profil tourné vers la droite (f = 1) sauf mention contraire.
 */

/* ---- générateurs de mouvements cycliques (course, vélo, elliptique, escalier) ---- */
function fxCycle(n, T) { var k = []; for (var i = 0; i < n; i++) k.push(0); return k; }
function gaitKeys(o) {
  // o : lean, amp (amplitude de foulée), arm (amplitude des bras), T, n
  var n = o.n || 12, T = o.T || 1.2, A = o.amp || 1, L = o.lean || 8, keys = [], i;
  var LEG = [[0, 32, 12, 8], [0.15, 10, 30, 0], [0.35, -28, 18, -38], [0.5, -20, 100, -10], [0.7, 20, 105, 10], [0.88, 42, 45, 12], [1, 32, 12, 8]];
  function leg(ph) {
    ph = ((ph % 1) + 1) % 1; var j = 1; while (j < LEG.length - 1 && ph > LEG[j][0]) j++;
    var a = LEG[j - 1], b = LEG[j], k = (ph - a[0]) / (b[0] - a[0]);
    return [a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k, a[3] + (b[3] - a[3]) * k];
  }
  for (i = 0; i < n; i++) {
    var ph = i / n, l1 = leg(ph), l2 = leg(ph + 0.5);
    var t1 = l1[0] * A, t2 = l2[0] * A;
    var e1 = 19.6 * Math.cos(t1 * Math.PI / 180) + 18.6 * Math.cos((t1 - l1[1]) * Math.PI / 180), e2 = 19.6 * Math.cos(t2 * Math.PI / 180) + 18.6 * Math.cos((t2 - l2[1]) * Math.PI / 180);
    var hipY = 88 - Math.max(e1, e2) - (o.hipLift || 0);
    var sw = (o.arm || 38) * Math.cos(2 * Math.PI * (ph - 0.35));
    keys.push({ t: +(T * i / n).toFixed(3), p: { hip: [80, +hipY.toFixed(2)], tor: L, neck: 0, leg: { a: [+t1.toFixed(1), +l1[1].toFixed(1)] }, leg2: { a: [+t2.toFixed(1), +l2[1].toFixed(1)] }, ft: l1[2], ft2: l2[2], arm: { a: [+sw.toFixed(1), o.elbow || 85] }, arm2: { a: [+(-sw).toFixed(1), o.elbow || 85] }, fx: 0.55 + 0.45 * Math.abs(Math.sin(2 * Math.PI * ph)) } });
  }
  keys.push({ t: T, p: keys[0].p });
  return keys;
}
function orbitKeys(n, T, fn) { var keys = [], i; for (i = 0; i < n; i++) keys.push({ t: +(T * i / n).toFixed(3), p: fn(2 * Math.PI * i / n) }); keys.push({ t: T, p: keys[0].p }); return keys; }

window.FIGDATA = {

'developpe-couche': {
    f: 1, vb: '46 22 90 72', thumb: 2.6,
    scene: [{ t: 'floor', sx: 90, rx: 30 }, { t: 'line', x1: 60, y1: 40, x2: 60, y2: 92 }, { t: 'line', x1: 60, y1: 40, x2: 64, y2: 40 }, { t: 'bench', x: 64, w: 56, y: 71, h: 5 }],
    base: { hip: [100, 65], tor: -90, bend: 0, neck: 0, arm: { ik: 'bar', bend: -1 }, leg: { ik: [114, 88], bend: 1 }, ft: 0, bar: [79, 39.5], fx: 0 },
    props: [{ t: 'plate', at: 'bar', r: 8.5 }], muscles: ['pectoraux', 'triceps', 'epaules'],
    keys: [{ t: 0, p: {} }, { t: 1.7, p: { bar: [85, 57], fx: 0.2 } }, { t: 2.0, p: { bar: [85, 57], fx: 0.2 } }, { t: 2.6, fx: 1 }, { t: 3.2, p: { bar: [79, 39.5], fx: 0.4 } }, { t: 3.7, p: { bar: [79, 39.5], fx: 0.1 } }]
  },
  'curl-halteres': {
    f: 1, vb: '40 4 80 92', thumb: 1.2,
    scene: [{ t: 'floor', sx: 80, rx: 16 }],
    base: { hip: [80, 49.8], tor: 0, neck: 0, arm: { a: [4, 4] }, leg: { ik: [80, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'db', hand: 'both', r: 4.4 }], muscles: ['biceps', 'avantbras'],
    keys: [{ t: 0, p: {} }, { t: 1.2, p: { arm: { a: [10, 138] }, fx: 1 } }, { t: 1.6, p: { arm: { a: [10, 138] }, fx: 1 } }, { t: 3.2, p: { arm: { a: [4, 4] }, fx: 0.1 } }, { t: 3.6, p: {} }]
  },
  'elevations-laterales': {
    view: 'front', vb: '36 4 88 92', thumb: 1.3,
    scene: [{ t: 'floor', sx: 80, rx: 16 }],
    base: { hip: [80, 50], lean: 0, arm: { a: [8, 10] }, leg: { a: [3, 0] }, fx: 0 },
    props: [{ t: 'db' }], muscles: ['epaules', 'trapezes'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm: { a: [86, 10] }, fx: 1 } }, { t: 1.8, p: { arm: { a: [86, 10] }, fx: 1 } }, { t: 3.4, p: { arm: { a: [8, 10] }, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'gs': {
    f: 1, vb: '38 4 90 92', thumb: 2.65,
    scene: [{ t: 'floor', sx: 80, rx: 20 }],
    base: { hip: [80, 49.8], tor: 2, neck: 0, arm: { ik: [87, 33], bend: -1 }, leg: { ik: [82, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'db', hand: 'near', r: 4.8 }], muscles: ['quadriceps', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.7, p: { hip: [62, 71], tor: 35, neck: -22, arm: { ik: [83, 58], bend: -1 }, fx: 0.2 } }, { t: 2.1, p: { hip: [62, 71], tor: 35, neck: -22, arm: { ik: [83, 58], bend: -1 }, fx: 0.2 } }, { t: 2.65, fx: 1 }, { t: 3.2, p: { fx: 0.3 } }, { t: 3.7, p: { fx: 0.1 } }]
  },
  'tv': {
    f: 1, vb: '30 0 100 94', thumb: 1.6,
    scene: [{ t: 'floor', sx: 70, rx: 28 }, { t: 'rect', x: 52, y: 72, w: 20, h: 5, r: 2.4 }, { t: 'line', x1: 62, y1: 77, x2: 62, y2: 92 }, { t: 'line', x1: 100, y1: 5, x2: 100, y2: 92 }, { t: 'line', x1: 100, y1: 5, x2: 67, y2: 5 }, { t: 'circ', x: 67, y: 5, r: 2.4 }, { t: 'rect', x: 68, y: 58.5, w: 14, h: 4.5, r: 2.2 }],
    base: { hip: [62, 68], tor: -12, neck: 8, arm: { ik: 'bar', bend: -1 }, leg: { ik: [88, 88], bend: 1 }, ft: 0, bar: [68, 21], fx: 0 },
    props: [{ t: 'cable', from: [67, 5], to: 'hands' }, { t: 'handle' }], muscles: ['dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { bar: [63, 45.5], tor: -16, fx: 1 } }, { t: 1.8, p: { bar: [63, 45.5], tor: -16, fx: 1 } }, { t: 3.4, p: { bar: [68, 21], tor: -12, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'pompes': {
    f: 1, vb: '20 44 94 58.8', thumb: 1.6,
    scene: [{ t: 'floor', sx: 70, rx: 46 }],
    base: { hip: [66.4, 72.6], tor: 72.6, neck: 18, arm: { ik: [96, 89.8], bend: -1 }, leg: { ik: [30, 84], bend: 1 }, ft: 0, fx: 0 },
    muscles: ['pectoraux', 'triceps', 'epaules', 'abdos'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { hip: [67.9, 79], tor: 82.5, fx: 0.2 } }, { t: 1.8, p: { hip: [67.9, 79], tor: 82.5, fx: 0.2 } }, { t: 2.4, fx: 1 }, { t: 3.0, p: { fx: 0.4 } }, { t: 3.5, p: { fx: 0.1 } }]
  },
  'pc': {
    f: 1, vb: '14 24 104 70', thumb: 2.0,
    scene: [{ t: 'floor', sx: 70, rx: 40 }, { t: 'line', x1: 48, y1: 79, x2: 62, y2: 76 }, { t: 'line', x1: 48.6, y1: 76.9, x2: 24, y2: 59.7 }, { t: 'line', x1: 58, y1: 82, x2: 98, y2: 50 }, { t: 'line', x1: 58, y1: 82, x2: 58, y2: 92 }, { t: 'line', x1: 98, y1: 50, x2: 98, y2: 92 }],
    base: { hip: [52, 72], tor: -55, neck: 10, arm: { ik: [60, 66], bend: -1 }, leg: { ik: [71.7, 56.6], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'pad', at: 'sole', l: 26, h: 3.4 }], muscles: ['quadriceps', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.8, p: { leg: { ik: [81.2, 49.2], bend: 1 }, fx: 0.3 } }, { t: 2.2, p: { leg: { ik: [81.2, 49.2], bend: 1 }, fx: 0.3 } }, { t: 2.6, fx: 1 }, { t: 3.6, p: { fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'squat-smith': {
    f: 1, vb: '36 4 84 92', thumb: 2.4,
    scene: [{ t: 'floor', sx: 78, rx: 20 }, { t: 'line', x1: 72, y1: 6, x2: 72, y2: 92 }, { t: 'line', x1: 98, y1: 6, x2: 98, y2: 92 }],
    base: { hip: [80, 51], tor: 3, neck: 0, arm: { a: [-10, -160] }, leg: { ik: [82, 88], bend: 1 }, ft: 0, bar: { rel: 'spine', s: 24.5, off: -4.2 }, fx: 0 },
    props: [{ t: 'plate', at: 'bar', r: 6 }], muscles: ['quadriceps', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.7, p: { hip: [64, 71], tor: 36, neck: -22, fx: 0.2 } }, { t: 2.1, p: { hip: [64, 71], tor: 36, neck: -22, fx: 0.2 } }, { t: 2.7, fx: 1 }, { t: 3.2, p: { fx: 0.3 } }, { t: 3.7, p: { fx: 0.1 } }]
  },
  'fentes': {
    f: 1, vb: '34 4 90 92', thumb: 2.4,
    scene: [{ t: 'floor', sx: 78, rx: 34 }],
    base: { hip: [78, 56], tor: 2, neck: 0, arm: { a: [0, 0] }, leg: { ik: [98, 88], bend: 1 }, leg2: { ik: [56, 82], bend: 1 }, ft: 0, ft2: -55, fx: 0 },
    props: [{ t: 'db', hand: 'both', r: 4.6 }], muscles: ['quadriceps', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { hip: [78, 72], fx: 0.2 } }, { t: 2.0, p: { hip: [78, 72], fx: 0.2 } }, { t: 2.6, fx: 1 }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'split-squat-bulgare': {
    f: 1, vb: '30 4 100 92', thumb: 2.4,
    scene: [{ t: 'floor', sx: 78, rx: 30 }, { t: 'bench', x: 34, w: 24, y: 67, h: 4 }],
    base: { hip: [76, 56], tor: 8, neck: -4, arm: { a: [0, 0] }, leg: { ik: [94, 88], bend: 1 }, leg2: { ik: [50, 62], bend: 1 }, ft: 0, ft2: -95, fx: 0 },
    props: [{ t: 'db', hand: 'both', r: 4.4 }], muscles: ['quadriceps', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { hip: [76, 69], fx: 0.2 } }, { t: 2.0, p: { hip: [76, 69], fx: 0.2 } }, { t: 2.6, fx: 1 }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'leg-extension': {
    f: 1, vb: '30 16 100 78', thumb: 2.4,
    scene: [{ t: 'floor', sx: 74, rx: 30 }, { t: 'rect', x: 50, y: 74, w: 28, h: 4, r: 2 }, { t: 'line', x1: 52, y1: 76, x2: 46, y2: 48 }, { t: 'line', x1: 64, y1: 78, x2: 64, y2: 92 }],
    base: { hip: [60, 70], tor: -8, neck: 6, arm: { a: [-6, 40] }, leg: { a: [88, 88] }, ft: 0, fx: 0 },
    props: [{ t: 'plate', at: ['shank', 0.9, 3.4], r: 2.6 }], muscles: ['quadriceps'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { leg: { a: [88, 2] }, fx: 0.4 } }, { t: 2.3, fx: 1 }, { t: 3.5, p: { leg: { a: [88, 88] }, fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'lc': {
    f: -1, vb: '24 40 112 54', thumb: 2.2,
    scene: [{ t: 'floor', sx: 80, rx: 50 }, { t: 'rect', x: 40, y: 78, w: 70, h: 4, r: 2 }, { t: 'line', x1: 52, y1: 82, x2: 52, y2: 92 }, { t: 'line', x1: 100, y1: 82, x2: 100, y2: 92 }],
    base: { hip: [86, 72], tor: 88, neck: 8, arm: { a: [100, 8] }, leg: { a: [-90, 0] }, ft: 0, fx: 0 },
    props: [], muscles: ['ischios', 'mollets'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { leg: { a: [-90, 105] }, fx: 0.4 } }, { t: 2.4, fx: 1 }, { t: 3.6, p: { leg: { a: [-90, 0] }, fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'rdl': {
    f: 1, vb: '36 4 90 92', thumb: 2.3,
    scene: [{ t: 'floor', sx: 74, rx: 22 }],
    base: { hip: [76, 51], tor: 0, bend: 0, neck: 0, arm: { a: [0, 0] }, leg: { ik: [76, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'plate', hand: 'near', r: 7 }], muscles: ['ischios', 'fessiers', 'lombaires'],
    keys: [{ t: 0, p: {} }, { t: 1.8, p: { hip: [66, 51], tor: 62, bend: 8, neck: -26, fx: 0.2 } }, { t: 2.2, p: { hip: [66, 51], tor: 62, bend: 8, neck: -26, fx: 0.2 } }, { t: 2.8, fx: 1 }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'hip-thrust': {
    f: 1, vb: '30 40 100 56', thumb: 2.4,
    scene: [{ t: 'floor', sx: 72, rx: 38 }, { t: 'rect', x: 34, y: 70, w: 22, h: 5, r: 2 }, { t: 'line', x1: 40, y1: 75, x2: 40, y2: 92 }, { t: 'line', x1: 50, y1: 75, x2: 50, y2: 92 }],
    base: { hip: [73, 79], tor: -62, neck: 20, arm: { ik: 'bar', bend: -1 }, leg: { ik: [94, 88], bend: 1 }, ft: 0, bar: { rel: 'spine', s: 1.2, off: 4.6 }, fx: 0 },
    props: [{ t: 'plate', at: 'bar', r: 7 }], muscles: ['fessiers', 'ischios'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { hip: [75, 65], tor: -97, neck: 40, fx: 0.4 } }, { t: 2.3, fx: 1 }, { t: 3.6, p: { hip: [73, 79], tor: -62, neck: 20, fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'abduction': {
    view: 'back', vb: '36 4 88 92', thumb: 1.5,
    scene: [{ t: 'floor', sx: 80, rx: 22 }],
    base: { hip: [80, 50], lean: 0, arm: { a: [9, 14] }, legL: { a: [3, 0] }, legR: { a: [3, 0] }, fx: 0 },
    muscles: ['fessiers', 'obliques'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { legR: { a: [38, 0] }, fx: 1 } }, { t: 2.0, p: { legR: { a: [38, 0] }, fx: 1 } }, { t: 3.4, p: { legR: { a: [3, 0] }, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'mollets': {
    f: 1, vb: '38 -4 84 98', thumb: 1.6,
    scene: [{ t: 'floor', sx: 80, rx: 20 }, { t: 'rect', x: 66, y: 88, w: 26, h: 4, r: 1.6 }],
    base: { hip: [80, 45.8], tor: 0, neck: 0, arm: { a: [0, 0] }, leg: { ik: [80, 84], bend: 1 }, ft: 14, fx: 0 },
    props: [{ t: 'db', hand: 'both', r: 4.2 }], muscles: ['mollets'],
    keys: [{ t: 0, p: {} }, { t: 1.3, p: { hip: [80, 40], leg: { ik: [80, 78.4], bend: 1 }, ft: -48, fx: 0.5 } }, { t: 2.0, fx: 1 }, { t: 3.2, p: { hip: [80, 45.8], leg: { ik: [80, 84], bend: 1 }, ft: 14, fx: 0.1 } }, { t: 3.6, p: {} }]
  },
  'di': {
    f: 1, vb: '34 10 90 84', thumb: 2.4,
    scene: [{ t: 'floor', sx: 82, rx: 34 }, { t: 'line', x1: 86, y1: 74, x2: 65, y2: 53 }, { t: 'line', x1: 80, y1: 77, x2: 102, y2: 77 }, { t: 'line', x1: 90, y1: 77, x2: 90, y2: 92 }, { t: 'line', x1: 72, y1: 60, x2: 72, y2: 92 }],
    base: { hip: [90, 70], tor: -45, neck: 12, arm: { ik: 'bar', bend: -1 }, leg: { ik: [108, 88], bend: 1 }, ft: 0, bar: [76, 29], fx: 0 },
    props: [{ t: 'plate', at: 'bar', r: 4.6 }], muscles: ['pectoraux', 'epaules', 'triceps'],
    keys: [{ t: 0, p: {} }, { t: 1.7, p: { bar: [80, 45], fx: 0.2 } }, { t: 2.0, p: { bar: [80, 45], fx: 0.2 } }, { t: 2.6, fx: 1 }, { t: 3.2, p: { bar: [76, 29], fx: 0.4 } }, { t: 3.7, p: { bar: [76, 29], fx: 0.1 } }]
  },
  'chest-press': {
    f: 1, vb: '34 20 90 74', thumb: 2.2,
    scene: [{ t: 'floor', sx: 74, rx: 30 }, { t: 'rect', x: 48, y: 74, w: 26, h: 4, r: 2 }, { t: 'line', x1: 50, y1: 76, x2: 46, y2: 44 }, { t: 'line', x1: 62, y1: 78, x2: 62, y2: 92 }, { t: 'line', x1: 46, y1: 36, x2: 46, y2: 92 }],
    base: { hip: [58, 70], tor: -6, neck: 4, arm: { ik: 'bar', bend: -1 }, leg: { ik: [86, 88], bend: 1 }, ft: 0, bar: [66, 50], fx: 0 },
    props: [{ t: 'handle' }], muscles: ['pectoraux', 'triceps', 'epaules'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { bar: [80, 49], fx: 0.3 } }, { t: 1.8, p: { bar: [80, 49], fx: 0.3 } }, { t: 2.2, fx: 1 }, { t: 3.4, p: { bar: [66, 50], fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'ecartes': {
    view: 'front', vb: '14 0 132 94', thumb: 2.0,
    scene: [{ t: 'floor', sx: 80, rx: 16 }, { t: 'line', x1: 22, y1: 8, x2: 22, y2: 92 }, { t: 'line', x1: 138, y1: 8, x2: 138, y2: 92 }, { t: 'circ', c: 'fpr', x: 22, y: 8, r: 2.6 }, { t: 'circ', c: 'fpr', x: 138, y: 8, r: 2.6 }],
    base: { hip: [80, 50], lean: 0, arm: { a: [78, 14] }, leg: { a: [4, 0] }, fx: 0 },
    props: [{ t: 'cable', from: [22, 8], to: 'handL' }, { t: 'cable', from: [138, 8], to: 'handR' }, { t: 'handles' }], muscles: ['pectoraux', 'epaules'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { arm: { a: [24, 20] }, fx: 0.4 } }, { t: 2.1, p: { arm: { a: [24, 20] }, fx: 1 } }, { t: 3.4, p: { arm: { a: [78, 14] }, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'dips-assistes': {
    f: 1, vb: '36 6 88 88', thumb: 2.4,
    scene: [{ t: 'floor', sx: 90, rx: 30 }, { t: 'line', x1: 78, y1: 57, x2: 104, y2: 57 }, { t: 'line', x1: 100, y1: 57, x2: 100, y2: 92 }],
    base: { hip: [80, 56], tor: 8, neck: 0, arm: { ik: [84, 57], bend: -1 }, leg: { a: [20, 105] }, ft: 0, fx: 0 },
    props: [{ t: 'pad', at: ['thigh', 1, 0], dx: 0, dy: 5, l: 16, h: 3.4 }], muscles: ['triceps', 'pectoraux', 'epaules'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { hip: [80, 66], tor: 16, neck: -6, fx: 0.3 } }, { t: 2.0, p: { hip: [80, 66], tor: 16, neck: -6, fx: 0.3 } }, { t: 2.6, fx: 1 }, { t: 3.5, p: { fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'tractions-assistees': {
    f: 1, vb: '34 0 92 94', thumb: 2.2,
    scene: [{ t: 'floor', sx: 82, rx: 24 }, { t: 'line', x1: 54, y1: 14, x2: 80, y2: 14 }, { t: 'line', x1: 98, y1: 14, x2: 98, y2: 92 }, { t: 'line', x1: 80, y1: 14, x2: 98, y2: 14 }],
    base: { hip: [68, 62], tor: 0, neck: 0, arm: { ik: [66, 14], bend: -1 }, leg: { a: [-6, 80] }, ft: 0, fx: 0 },
    props: [{ t: 'pad', at: ['thigh', 1, 0], dy: 5, l: 16, h: 3.4 }], muscles: ['dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 1.8, p: { hip: [68, 46], neck: 6, fx: 0.4 } }, { t: 2.4, p: { hip: [68, 46], neck: 6, fx: 1 } }, { t: 3.8, p: { hip: [68, 62], neck: 0, fx: 0.1 } }, { t: 4.2, p: {} }]
  },
  'rs': {
    f: 1, vb: '34 20 96 74', thumb: 1.8,
    scene: [{ t: 'floor', sx: 78, rx: 36 }, { t: 'rect', x: 48, y: 76, w: 26, h: 4, r: 2 }, { t: 'line', x1: 62, y1: 80, x2: 62, y2: 92 }, { t: 'rect', x: 98, y: 76, w: 3, h: 16, r: 1 }],
    base: { hip: [60, 72], tor: 12, neck: -6, arm: { ik: 'bar', bend: -1 }, leg: { ik: [92, 88], bend: 1 }, ft: 0, bar: [84, 62], fx: 0 },
    props: [{ t: 'cable', from: [118, 62], to: 'hands' }, { t: 'handle' }], muscles: ['dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { tor: -4, neck: 4, bar: [64, 60], fx: 0.5 } }, { t: 2.0, p: { tor: -4, neck: 4, bar: [64, 60], fx: 1 } }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'rowing-haltere': {
    f: 1, vb: '34 20 94 74', thumb: 1.8,
    scene: [{ t: 'floor', sx: 70, rx: 34 }, { t: 'bench', x: 92, w: 30, y: 64, h: 5 }],
    base: { hip: [66, 52], tor: 78, neck: -30, arm: { a: [0, 0] }, arm2: { ik: [96, 62], bend: -1 }, leg: { ik: [70, 88], bend: 1 }, leg2: { ik: [56, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'db', hand: 'near', r: 4.4 }], muscles: ['dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm: { a: [-58, 58] }, fx: 0.5 } }, { t: 2.0, p: { arm: { a: [-58, 58] }, fx: 1 } }, { t: 3.4, p: { arm: { a: [0, 0] }, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'rowing-machine': {
    f: 1, vb: '34 20 96 74', thumb: 1.8,
    scene: [{ t: 'floor', sx: 78, rx: 36 }, { t: 'rect', x: 48, y: 76, w: 26, h: 4, r: 2 }, { t: 'line', x1: 62, y1: 80, x2: 62, y2: 92 }, { t: 'line', x1: 94, y1: 40, x2: 94, y2: 92 }, { t: 'line', x1: 94, y1: 64, x2: 100, y2: 64 }],
    base: { hip: [60, 72], tor: 22, neck: -10, arm: { ik: 'bar', bend: -1 }, leg: { ik: [84, 88], bend: 1 }, ft: 0, bar: [90, 60], fx: 0 },
    props: [{ t: 'pad', at: ['spine', 17, 6.2], a: 112, l: 22, h: 4 }, { t: 'line', a: 'hands', b: [96, 64] }, { t: 'handle' }], muscles: ['dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { bar: [74, 60], fx: 0.5 } }, { t: 2.0, p: { bar: [74, 60], fx: 1 } }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'pull-over': {
    f: 1, vb: '36 0 96 94', thumb: 1.0,
    scene: [{ t: 'floor', sx: 76, rx: 22 }, { t: 'line', x1: 108, y1: 8, x2: 108, y2: 92 }, { t: 'line', x1: 108, y1: 8, x2: 92, y2: 8 }, { t: 'circ', c: 'fpr', x: 92, y: 8, r: 2.4 }],
    base: { hip: [76, 50.6], tor: 12, neck: -8, arm: { a: [158, 0] }, leg: { ik: [78, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'cable', from: [92, 8], to: 'hands' }, { t: 'handle' }], muscles: ['dos', 'abdos'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { arm: { a: [26, 0] }, tor: 20, fx: 0.5 } }, { t: 2.2, p: { arm: { a: [26, 0] }, tor: 20, fx: 1 } }, { t: 3.6, p: { fx: 0.1 } }, { t: 4.0, p: {} }]
  },
  'extensions-lombaires': {
    f: 1, vb: '30 30 100 64', thumb: 2.2,
    scene: [{ t: 'floor', sx: 66, rx: 40 }, { t: 'line', x1: 44, y1: 86, x2: 86, y2: 46 }, { t: 'line', x1: 86, y1: 46, x2: 86, y2: 92 }, { t: 'line', x1: 48, y1: 82, x2: 48, y2: 92 }, { t: 'circ', c: 'fpr', x: 52, y: 78, r: 2.6 }],
    base: { hip: [78, 46], tor: 130, neck: 6, arm: { a: [4, 20] }, leg: { a: [-45, 0] }, ft: 0, fx: 0 },
    props: [], muscles: ['lombaires', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { tor: 78, neck: 0, fx: 0.4 } }, { t: 2.4, p: { tor: 78, fx: 1 } }, { t: 3.8, p: { tor: 130, neck: 6, fx: 0.1 } }, { t: 4.2, p: {} }]
  },
  'face-pull': {
    f: 1, vb: '36 0 100 94', thumb: 1.8,
    scene: [{ t: 'floor', sx: 78, rx: 22 }, { t: 'line', x1: 128, y1: 30, x2: 128, y2: 92 }, { t: 'circ', c: 'fpr', x: 124, y: 30, r: 2.4 }],
    base: { hip: [80, 50.6], tor: -3, neck: 0, arm: { ik: 'bar', bend: 1 }, leg: { ik: [80, 88], bend: 1 }, ft: 0, bar: [102, 29], fx: 0 },
    props: [{ t: 'cable', from: [124, 30], to: 'hands' }, { t: 'handle' }], muscles: ['epaules', 'trapezes', 'dos'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { bar: [88, 30], fx: 0.5 } }, { t: 2.0, p: { bar: [88, 30], fx: 1 } }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'de': {
    f: 1, vb: '34 4 90 90', thumb: 1.8,
    scene: [{ t: 'floor', sx: 74, rx: 30 }, { t: 'rect', x: 48, y: 74, w: 26, h: 4, r: 2 }, { t: 'line', x1: 50, y1: 76, x2: 46, y2: 44 }, { t: 'line', x1: 62, y1: 78, x2: 62, y2: 92 }, { t: 'line', x1: 46, y1: 20, x2: 46, y2: 92 }],
    base: { hip: [60, 72], tor: -4, neck: 0, arm: { ik: 'bar', bend: -1 }, leg: { ik: [86, 88], bend: 1 }, ft: 0, bar: [68, 50], fx: 0 },
    props: [{ t: 'handle' }], muscles: ['epaules', 'triceps', 'trapezes'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { bar: [64, 26], fx: 0.3 } }, { t: 1.9, p: { bar: [64, 26], fx: 0.3 } }, { t: 2.3, fx: 1 }, { t: 3.4, p: { bar: [68, 50], fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'developpe-militaire': {
    f: 1, vb: '34 4 90 90', thumb: 1.8,
    scene: [{ t: 'floor', sx: 70, rx: 30 }, { t: 'rect', x: 48, y: 74, w: 26, h: 4, r: 2 }, { t: 'line', x1: 52, y1: 76, x2: 48, y2: 40 }, { t: 'line', x1: 62, y1: 78, x2: 62, y2: 92 }, { t: 'line', x1: 50, y1: 56, x2: 50, y2: 92 }],
    base: { hip: [60, 72], tor: -4, neck: 0, arm: { ik: 'bar', bend: -1 }, leg: { ik: [86, 88], bend: 1 }, ft: 0, bar: [68, 50], fx: 0 },
    props: [{ t: 'plate', at: 'bar', r: 4.6 }], muscles: ['epaules', 'triceps', 'trapezes'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { bar: [64, 27], fx: 0.3 } }, { t: 1.9, p: { bar: [64, 27], fx: 0.3 } }, { t: 2.3, fx: 1 }, { t: 3.4, p: { bar: [68, 50], fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'oiseau': {
    view: 'back', vb: '30 4 100 92', thumb: 1.5,
    scene: [{ t: 'floor', sx: 80, rx: 18 }],
    base: { hip: [80, 50], lean: 0, arm: { a: [14, 14] }, leg: { a: [3, 0] }, fx: 0 },
    props: [{ t: 'db' }], muscles: ['dos', 'epaules', 'trapezes'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm: { a: [82, 12] }, fx: 1 } }, { t: 1.9, p: { arm: { a: [82, 12] }, fx: 1 } }, { t: 3.3, p: { arm: { a: [14, 14] }, fx: 0.1 } }, { t: 3.7, p: {} }]
  },
  'elevations-frontales': {
    f: 1, vb: '38 4 92 92', thumb: 1.8,
    scene: [{ t: 'floor', sx: 80, rx: 20 }],
    base: { hip: [80, 50.6], tor: 0, neck: 0, arm: { a: [4, 0] }, leg: { ik: [80, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'db', hand: 'near', r: 4.4 }], muscles: ['epaules', 'pectoraux'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm: { a: [88, 0] }, fx: 1 } }, { t: 1.9, p: { arm: { a: [88, 0] }, fx: 1 } }, { t: 3.3, p: { arm: { a: [4, 0] }, fx: 0.1 } }, { t: 3.7, p: {} }]
  },
  'curl-poulie': {
    f: 1, vb: '38 4 100 92', thumb: 1.5,
    scene: [{ t: 'floor', sx: 80, rx: 18 }, { t: 'circ', c: 'fpr', x: 122, y: 88, r: 2.6 }, { t: 'line', x1: 126, y1: 60, x2: 126, y2: 92 }],
    base: { hip: [80, 50.6], tor: 0, neck: 0, arm: { a: [6, 4] }, leg: { ik: [80, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'cable', from: [122, 88], to: 'hands' }, { t: 'handle' }], muscles: ['biceps', 'avantbras'],
    keys: [{ t: 0, p: {} }, { t: 1.3, p: { arm: { a: [10, 138] }, fx: 1 } }, { t: 1.7, p: { arm: { a: [10, 138] }, fx: 1 } }, { t: 3.2, p: { arm: { a: [6, 4] }, fx: 0.1 } }, { t: 3.6, p: {} }]
  },
  'preacher': {
    f: 1, vb: '34 20 90 74', thumb: 2.4,
    scene: [{ t: 'floor', sx: 74, rx: 30 }, { t: 'rect', x: 48, y: 74, w: 22, h: 4, r: 2 }, { t: 'line', x1: 58, y1: 78, x2: 58, y2: 92 }, { t: 'line', x1: 84, y1: 64, x2: 84, y2: 92 }],
    base: { hip: [58, 72], tor: 8, neck: -4, arm: { a: [42, 0] }, leg: { ik: [84, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'pad', at: ['upper', 0.5, -4.4], a: 48, l: 24, h: 3.4 }, { t: 'plate', hand: 'near', r: 4.2 }], muscles: ['biceps', 'avantbras'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm: { a: [42, 122] }, fx: 1 } }, { t: 1.9, p: { arm: { a: [42, 122] }, fx: 1 } }, { t: 3.4, p: { arm: { a: [42, 0] }, fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'triceps-poulie': {
    f: 1, vb: '36 0 100 94', thumb: 2.4,
    scene: [{ t: 'floor', sx: 78, rx: 20 }, { t: 'line', x1: 108, y1: 8, x2: 108, y2: 92 }, { t: 'line', x1: 108, y1: 8, x2: 92, y2: 8 }, { t: 'circ', c: 'fpr', x: 92, y: 8, r: 2.4 }],
    base: { hip: [78, 50.6], tor: 8, neck: -4, arm: { a: [-2, 86] }, leg: { ik: [78, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'cable', from: [92, 8], to: 'hands' }, { t: 'handle' }], muscles: ['triceps'],
    keys: [{ t: 0, p: {} }, { t: 1.3, p: { arm: { a: [-2, 4] }, fx: 1 } }, { t: 1.8, p: { arm: { a: [-2, 4] }, fx: 1 } }, { t: 3.2, p: { arm: { a: [-2, 86] }, fx: 0.1 } }, { t: 3.6, p: {} }]
  },
  'barre-front': {
    f: 1, vb: '46 22 90 72', thumb: 2.4,
    scene: [{ t: 'floor', sx: 90, rx: 30 }, { t: 'bench', x: 64, w: 56, y: 71, h: 5 }],
    base: { hip: [100, 65], tor: -90, neck: 0, arm: { a: [-172, 0] }, leg: { ik: [114, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'plate', hand: 'near', r: 4.8 }], muscles: ['triceps'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { arm: { a: [-172, 78] }, fx: 0.2 } }, { t: 1.9, p: { arm: { a: [-172, 78] }, fx: 0.2 } }, { t: 2.4, fx: 1 }, { t: 3.4, p: { arm: { a: [-172, 0] }, fx: 0.2 } }, { t: 3.8, p: { fx: 0.1 } }]
  },
  'dips-banc': {
    f: 1, vb: '30 30 100 64', thumb: 2.4,
    scene: [{ t: 'floor', sx: 82, rx: 34 }, { t: 'rect', x: 34, y: 70, w: 28, h: 5, r: 2 }, { t: 'line', x1: 40, y1: 75, x2: 40, y2: 92 }, { t: 'line', x1: 56, y1: 75, x2: 56, y2: 92 }],
    base: { hip: [68, 70], tor: 2, neck: 0, arm: { ik: [60, 69], bend: -1 }, leg: { ik: [100, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [], muscles: ['triceps', 'epaules', 'pectoraux'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { hip: [68, 82], fx: 0.3 } }, { t: 1.9, p: { hip: [68, 82], fx: 0.3 } }, { t: 2.4, fx: 1 }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'pl': {
    f: 1, vb: '14 48 104 46', thumb: 1.0,
    scene: [{ t: 'floor', sx: 70, rx: 46 }],
    base: { hip: [66, 80], tor: 76, neck: 12, arm: { a: [0, 90] }, leg: { ik: [30, 84.5], bend: 1 }, ft: 0, fx: 0.6 },
    muscles: ['abdos', 'lombaires', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.5, p: { hip: [66, 79.2], fx: 1 } }, { t: 3.0, p: { hip: [66, 80], fx: 0.6 } }]
  },
  'planche-laterale': {
    f: 1, vb: '14 40 104 54', thumb: 1.5,
    scene: [{ t: 'floor', sx: 70, rx: 46 }],
    base: { hip: [66, 80], tor: 76, neck: 12, arm: { a: [0, 90] }, arm2: { a: [180, 0] }, leg: { ik: [30, 84.5], bend: 1 }, ft: 0, fx: 0.4 },
    muscles: ['obliques', 'abdos'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { hip: [66, 77], fx: 1 } }, { t: 2.0, p: { hip: [66, 77], fx: 1 } }, { t: 3.4, p: { hip: [66, 80], fx: 0.4 } }]
  },
  'db': {
    f: 1, vb: '36 44 110 52', thumb: 2.0,
    scene: [{ t: 'floor', sx: 90, rx: 50 }, { t: 'rect', x: 30, y: 90.4, w: 112, h: 2, r: 1 }],
    base: { hip: [100, 84.2], tor: -90, neck: 0, arm: { a: [180, 0] }, arm2: { a: [180, 0] }, leg: { a: [180, 90] }, leg2: { a: [180, 90] }, ft: 0, fx: 0 },
    muscles: ['abdos', 'obliques'],
    keys: [{ t: 0, p: {} }, { t: 1.6, p: { leg: { a: [100, 0] }, arm2: { a: [-100, 0] }, fx: 1 } }, { t: 2.0, p: { leg: { a: [100, 0] }, arm2: { a: [-100, 0] }, fx: 1 } }, { t: 3.4, p: { fx: 0.2 } }, { t: 3.8, p: {} }]
  },
  'crunch-machine': {
    f: 1, vb: '34 20 90 74', thumb: 2.2,
    scene: [{ t: 'floor', sx: 74, rx: 30 }, { t: 'rect', x: 48, y: 76, w: 26, h: 4, r: 2 }, { t: 'line', x1: 50, y1: 78, x2: 48, y2: 40 }, { t: 'line', x1: 62, y1: 80, x2: 62, y2: 92 }, { t: 'line', x1: 78, y1: 36, x2: 78, y2: 92 }],
    base: { hip: [60, 72], tor: -2, neck: 0, arm: { a: [26, 118] }, leg: { ik: [86, 88], bend: 1 }, ft: 0, fx: 0 },
    props: [{ t: 'pad', at: ['spine', 18, 5.2], a: 94, l: 14, h: 4 }], muscles: ['abdos', 'obliques'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { tor: 20, bend: 22, neck: 8, fx: 0.5 } }, { t: 2.0, p: { tor: 20, bend: 22, neck: 8, fx: 1 } }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'releve-genoux': {
    f: 1, vb: '38 4 90 90', thumb: 2.0,
    scene: [{ t: 'floor', sx: 82, rx: 22 }, { t: 'line', x1: 70, y1: 26, x2: 70, y2: 70 }, { t: 'line', x1: 70, y1: 70, x2: 70, y2: 92 }, { t: 'rect', x: 76, y: 52, w: 20, h: 3.4, r: 1.7 }, { t: 'line', x1: 92, y1: 55, x2: 92, y2: 92 }],
    base: { hip: [78, 60], tor: -3, neck: 0, arm: { a: [2, 88] }, leg: { a: [4, 4] }, ft: 0, fx: 0 },
    muscles: ['abdos', 'obliques'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { leg: { a: [92, 94] }, tor: -6, fx: 0.6 } }, { t: 2.1, p: { leg: { a: [92, 94] }, tor: -6, fx: 1 } }, { t: 3.4, p: { fx: 0.1 } }, { t: 3.8, p: {} }]
  },
  'pallof': {
    f: 1, vb: '38 4 100 92', thumb: 2.0,
    scene: [{ t: 'floor', sx: 80, rx: 22 }, { t: 'line', x1: 128, y1: 36, x2: 128, y2: 92 }, { t: 'circ', c: 'fpr', x: 124, y: 36, r: 2.4 }],
    base: { hip: [80, 50.6], tor: -2, neck: 0, arm: { ik: 'bar', bend: -1 }, leg: { ik: [80, 88], bend: 1 }, ft: 0, bar: [86, 36], fx: 0 },
    props: [{ t: 'cable', from: [124, 36], to: 'hands' }, { t: 'handle' }], muscles: ['abdos', 'obliques'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { bar: [104, 31], fx: 0.6 } }, { t: 3.0, p: { bar: [104, 31], fx: 1 } }, { t: 4.2, p: { bar: [86, 36], fx: 0.2 } }, { t: 4.6, p: {} }]
  },
  'bird-dog': {
    f: 1, vb: '14 40 112 54', thumb: 2.0,
    scene: [{ t: 'floor', sx: 70, rx: 50 }],
    base: { hip: [52, 66], tor: 90, neck: -18, arm: { a: [0, 0] }, arm2: { a: [0, 0] }, leg: { a: [0, 90] }, leg2: { a: [0, 90] }, ft: 0, fx: 0 },
    muscles: ['abdos', 'lombaires', 'fessiers'],
    keys: [{ t: 0, p: {} }, { t: 1.4, p: { arm2: { a: [90, 0] }, leg: { a: [-90, 0] }, fx: 0.6 } }, { t: 2.6, p: { arm2: { a: [90, 0] }, leg: { a: [-90, 0] }, fx: 1 } }, { t: 4.0, p: { fx: 0.1 } }, { t: 4.4, p: {} }]
  },
  'course': {
    f: 1, lin: true, vb: '30 4 100 96', thumb: 0.2,
    scene: [{ t: 'floor', sx: 80, rx: 36 }, { t: 'rect', x: 40, y: 90.5, w: 80, h: 3, r: 1.5 }],
    base: { hip: [80, 52], tor: 10, neck: 0, fx: 0.6 },
    muscles: ['quadriceps', 'ischios', 'mollets', 'fessiers'],
    keys: gaitKeys({ lean: 10, amp: 1, arm: 42, T: 1.0, elbow: 88, hipLift: 2.5 })
  },
  'intervalles': {
    f: 1, lin: true, vb: '30 4 100 96', thumb: 0.2,
    scene: [{ t: 'floor', sx: 80, rx: 36 }, { t: 'rect', x: 40, y: 90.5, w: 80, h: 3, r: 1.5 }],
    base: { hip: [80, 52], tor: 16, neck: 0, fx: 0.8 },
    muscles: ['quadriceps', 'ischios', 'mollets', 'fessiers'],
    keys: gaitKeys({ lean: 16, amp: 1.25, arm: 52, T: 0.7, elbow: 92, hipLift: 3.5 })
  },
  'tapis-incline': {
    f: 1, lin: true, vb: '30 6 104 98', thumb: 0.3,
    scene: [{ t: 'path', c: 'fsh0', d: 'M34,100L132,83' }, { t: 'path', c: 'fpr', d: 'M34,100L132,83L132,88L34,105Z' }, { t: 'line', x1: 118, y1: 42, x2: 118, y2: 88 }, { t: 'line', x1: 100, y1: 42, x2: 118, y2: 42 }],
    base: { hip: [80, 52], tor: 12, neck: 0, fx: 0.5 },
    muscles: ['fessiers', 'mollets', 'quadriceps', 'ischios'],
    keys: gaitKeys({ lean: 12, amp: 0.62, arm: 22, T: 1.4, elbow: 80, hipLift: 5 })
  },
  'velo': {
    f: 1, lin: true, vb: '28 6 100 90', thumb: 0.3,
    scene: [{ t: 'floor', sx: 82, rx: 32 }, { t: 'rect', x: 56, y: 60, w: 18, h: 3, r: 1.5 }, { t: 'line', x1: 65, y1: 63, x2: 83, y2: 78 }, { t: 'line', x1: 83, y1: 78, x2: 94, y2: 53 }, { t: 'line', x1: 92, y1: 51, x2: 100, y2: 51 }, { t: 'circ', c: 'fpr', x: 102, y: 76, r: 10 }, { t: 'line', x1: 52, y1: 92, x2: 112, y2: 92 }, { t: 'line', x1: 83, y1: 78, x2: 83, y2: 92 }],
    base: { hip: [66, 54], tor: 30, neck: -18, arm: { ik: 'bar', bend: -1 }, ft: 0, ft2: 0, bar: [96, 51], fx: 0.6 },
    props: [{ t: 'line', a: [83, 78], b: 'foot' }, { t: 'line', a: [83, 78], b: 'foot2' }, { t: 'handle' }], muscles: ['quadriceps', 'fessiers', 'mollets'],
    keys: orbitKeys(16, 1.6, function (a) { return { leg: { ik: [83 + 8 * Math.cos(a), 73.5 + 8 * Math.sin(a)], bend: 1 }, leg2: { ik: [83 + 8 * Math.cos(a + Math.PI), 73.5 + 8 * Math.sin(a + Math.PI)], bend: 1 }, fx: 0.6 + 0.3 * Math.sin(a) }; })
  },
  'elliptique': {
    f: 1, lin: true, vb: '34 4 100 92', thumb: 0.3,
    scene: [{ t: 'floor', sx: 80, rx: 34 }, { t: 'line', x1: 106, y1: 36, x2: 106, y2: 88 }, { t: 'line', x1: 52, y1: 91, x2: 112, y2: 91 }],
    base: { hip: [80, 52], tor: 6, neck: 0, ft: 0, ft2: 0, fx: 0.6 },
    props: [{ t: 'pad', at: 'sole', fix: true, a: 0, l: 20, h: 2.6 }, { t: 'pad', at: 'sole2', fix: true, a: 0, l: 20, h: 2.6 }, { t: 'line', a: 'hands', b: [104, 80] }, { t: 'handle' }],
    muscles: ['quadriceps', 'fessiers', 'mollets'],
    keys: orbitKeys(16, 1.8, function (a) { return { leg: { ik: [80 + 11 * Math.cos(a), 84.5 + 3.2 * Math.sin(a)], bend: 1 }, leg2: { ik: [80 + 11 * Math.cos(a + Math.PI), 84.5 + 3.2 * Math.sin(a + Math.PI)], bend: 1 }, arm: { ik: [92 + 7 * Math.cos(a + Math.PI), 42 + 1.5 * Math.sin(a)], bend: -1 }, arm2: { ik: [92 + 7 * Math.cos(a), 42 + 1.5 * Math.sin(a + Math.PI)], bend: -1 }, fx: 0.6 + 0.3 * Math.sin(a) }; })
  },
  'stairmaster': {
    f: 1, lin: true, vb: '34 4 100 92', thumb: 0.3,
    scene: [{ t: 'floor', sx: 82, rx: 30 }, { t: 'line', x1: 104, y1: 40, x2: 104, y2: 92 }, { t: 'line', x1: 94, y1: 40, x2: 104, y2: 40 }],
    base: { hip: [80, 50], tor: 6, neck: 0, arm: { ik: [96, 41], bend: -1 }, ft: 0, ft2: 0, fx: 0.6 },
    props: [{ t: 'pad', at: 'sole', fix: true, a: 0, l: 24, h: 3 }, { t: 'pad', at: 'sole2', fix: true, a: 0, l: 24, h: 3 }],
    muscles: ['fessiers', 'quadriceps', 'mollets'],
    keys: [{ t: 0, p: { leg: { ik: [86, 86], bend: 1 }, leg2: { ik: [82, 74], bend: 1 }, hip: [80, 49] } }, { t: 0.9, p: { leg: { ik: [84, 80], bend: 1 }, leg2: { ik: [84, 80], bend: 1 }, hip: [80, 52] } }, { t: 1.8, p: { leg: { ik: [82, 74], bend: 1 }, leg2: { ik: [86, 86], bend: 1 }, hip: [80, 49] } }, { t: 2.7, p: { leg: { ik: [84, 80], bend: 1 }, leg2: { ik: [84, 80], bend: 1 }, hip: [80, 52] } }, { t: 3.6, p: { leg: { ik: [86, 86], bend: 1 }, leg2: { ik: [82, 74], bend: 1 }, hip: [80, 49] } }]
  },
  'rameur': {
    f: 1, lin: true, vb: '30 30 114 66', thumb: 0.3,
    scene: [{ t: 'floor', sx: 80, rx: 44 }, { t: 'line', x1: 44, y1: 88.4, x2: 114, y2: 88.4 }, { t: 'circ', c: 'fpr', x: 124, y: 74, r: 11 }, { t: 'line', x1: 124, y1: 74, x2: 120, y2: 88 }, { t: 'rect', x: 100, y: 78, w: 3, h: 10, r: 1 }],
    base: { hip: [84, 80], tor: 24, neck: -12, arm: { ik: 'bar', bend: -1 }, leg: { ik: [98, 85], bend: 1 }, ft: 0, bar: [114, 68], fx: 0.5 },
    props: [{ t: 'pad', at: ['spine', -3, 0], a: 0, l: 13, h: 3.4 }, { t: 'cable', from: [118, 70], to: 'hands' }, { t: 'handle' }], muscles: ['quadriceps', 'dos', 'biceps'],
    keys: [{ t: 0, p: {} }, { t: 0.7, p: { hip: [64, 80], tor: 28, bar: [97, 66], fx: 1 } }, { t: 1.2, p: { hip: [62, 80], tor: -20, neck: 4, bar: [78, 63], fx: 1 } }, { t: 1.6, p: { hip: [62, 80], tor: -22, neck: 4, bar: [66, 62], fx: 0.8 } }, { t: 2.0, p: { hip: [62, 80], tor: -22, bar: [78, 63], fx: 0.4 } }, { t: 2.6, p: { hip: [66, 80], tor: 24, bar: [97, 66], fx: 0.3 } }, { t: 3.4, p: { hip: [84, 80], tor: 24, bar: [114, 68], fx: 0.5 } }]
  }
};
