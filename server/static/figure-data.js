/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Animations des exercices du catalogue de départ, par identifiant (slug).
 * Chaque animation est une suite de poses clés (t en secondes) ; le moteur (figure.js) interpole et résout les articulations.
 * Coordonnées : 160 x 100, sol à y = 92, personnage de profil tourné vers la droite (f = 1) sauf mention contraire.
 */
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
  }
};
