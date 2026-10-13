/* SPDX-License-Identifier: AGPL-3.0-or-later
 * Fonte : « Esprits de fonte », le mini-jeu de collection relié aux séances.
 * Règles de base (elles sont aussi affichées dans l'appli, onglet Esprits > Règles) :
 *  - les jetons se gagnent uniquement en s'entraînant, selon l'effort réel, avec un plafond par jour ;
 *  - aucun argent, aucune pub, aucune série à perdre : les jetons n'expirent jamais ;
 *  - le niveau et l'évolution d'un esprit viennent des séries réellement faites sur sa zone du corps ;
 *  - tirages : taux affichés, garantie d'Épique tous les 30 tirages et de Légendaire tous les 90.
 * L'état du jeu est dans localStorage (clé « muscu-jeu ») et suit l'export / l'import des données.
 */
(function () {
  'use strict';
  var KEY = 'muscu-jeu';
  var RK = ['C', 'U', 'R', 'E', 'L'];
  var RATES = { C: 0.58, U: 0.26, R: 0.11, E: 0.04, L: 0.01 };
  var PITY_E = 30, PITY_L = 90, DAY_CAP = 4, PULL_COST = 1, MULTI = 5;
  var SHARDS = { C: 4, U: 10, R: 30, E: 80, L: 200 };            // éclats reçus pour un doublon
  var PRICE = { C: 40, U: 100, R: 300, E: 800, L: 2000 };        // prix en éclats dans la boutique
  var ZN = { epaules: 'Épaules', pectoraux: 'Pectoraux', dos: 'Dos', biceps: 'Biceps', triceps: 'Triceps', abdos: 'Abdos', lombaires: 'Lombaires', fessiers: 'Fessiers', quadriceps: 'Quadriceps', ischios: 'Ischio-jambiers', mollets: 'Mollets' };

  /* ------------------------------------------------------------------ catalogue */
  // [id, nom, rareté, zone, silhouette, teinte, attributs]
  var CR = [
    ['gloumi', 'Gloumi', 'C', 'quadriceps', 'blob', 200, { eyes: 'round', ears: 'none', horn: 'none', tail: 'none', pat: 'dots', mouth: 'smile' }],
    ['pomo', 'Pomo', 'C', 'pectoraux', 'blob', 12, { eyes: 'happy', ears: 'round', horn: 'none', tail: 'none', pat: 'stripes', mouth: 'open' }],
    ['brindille', 'Brindille', 'C', 'dos', 'beast', 95, { eyes: 'round', ears: 'cat', horn: 'none', tail: 'curl', pat: 'stripes', mouth: 'smile' }],
    ['piaf', 'Piaf', 'C', 'epaules', 'bird', 30, { eyes: 'round', ears: 'none', horn: 'nub', tail: 'curl', pat: 'dots', mouth: 'smile' }],
    ['caillou', 'Caillou', 'C', 'mollets', 'golem', 35, { eyes: 'sleepy', ears: 'none', horn: 'none', tail: 'none', pat: 'dots', mouth: 'flat', sat: 25 }],
    ['biscotte', 'Biscotte', 'C', 'abdos', 'beast', 40, { eyes: 'happy', ears: 'round', horn: 'none', tail: 'curl', pat: 'dots', mouth: 'open' }],
    ['lumi', 'Lumi', 'C', 'lombaires', 'spirit', 190, { eyes: 'sleepy', ears: 'none', horn: 'none', tail: 'none', pat: 'dots', mouth: 'smile' }],
    ['bourdon', 'Bourdon', 'C', 'triceps', 'bird', 50, { eyes: 'round', ears: 'none', horn: 'none', tail: 'spike', pat: 'stripes', mouth: 'smile', shift: 150 }],
    ['moustache', 'Moustache', 'C', 'ischios', 'beast', 20, { eyes: 'round', ears: 'long', horn: 'none', tail: 'curl', pat: 'dots', mouth: 'smile' }],

    ['trotte', 'Trotte-Menu', 'U', 'quadriceps', 'beast', 150, { eyes: 'happy', ears: 'long', horn: 'none', tail: 'curl', pat: 'dots', mouth: 'smile' }],
    ['gambade', 'Gambade', 'U', 'mollets', 'bird', 170, { eyes: 'spark', ears: 'none', horn: 'crest', tail: 'spike', pat: 'bolt', mouth: 'open' }],
    ['rocaille', 'Rocaille', 'U', 'fessiers', 'golem', 18, { eyes: 'round', ears: 'none', horn: 'nub', tail: 'none', pat: 'stripes', mouth: 'smile' }],
    ['ondine', 'Ondine', 'U', 'dos', 'spirit', 205, { eyes: 'happy', ears: 'fin', horn: 'none', tail: 'none', pat: 'dots', mouth: 'smile' }],
    ['marteau', 'Petit-Marteau', 'U', 'biceps', 'golem', 5, { eyes: 'fierce', ears: 'none', horn: 'nub', tail: 'none', pat: 'bolt', mouth: 'flat' }],
    ['plume', 'Plume', 'U', 'epaules', 'bird', 260, { eyes: 'spark', ears: 'none', horn: 'two', tail: 'flame', pat: 'dots', mouth: 'smile' }],
    ['tortilla', 'Tortilla', 'U', 'abdos', 'drake', 120, { eyes: 'sleepy', ears: 'round', horn: 'nub', tail: 'curl', pat: 'dots', mouth: 'smile' }],

    ['griffe', 'Griffe', 'R', 'pectoraux', 'beast', 355, { eyes: 'fierce', ears: 'cat', horn: 'two', tail: 'spike', pat: 'stripes', mouth: 'fang' }],
    ['tonnerre', 'Tonnerre', 'R', 'triceps', 'drake', 55, { eyes: 'fierce', ears: 'none', horn: 'two', tail: 'spike', pat: 'bolt', mouth: 'fang' }],
    ['seisme', 'Séisme', 'R', 'quadriceps', 'golem', 25, { eyes: 'fierce', ears: 'none', horn: 'big', tail: 'none', pat: 'stripes', mouth: 'fang' }],
    ['pivoine', 'Pivoine', 'R', 'ischios', 'spirit', 320, { eyes: 'happy', ears: 'long', horn: 'crest', tail: 'none', pat: 'dots', mouth: 'open' }],
    ['rafale', 'Rafale', 'R', 'lombaires', 'bird', 190, { eyes: 'fierce', ears: 'fin', horn: 'crest', tail: 'spike', pat: 'bolt', mouth: 'smile' }],

    ['braise', 'Braise', 'E', 'fessiers', 'drake', 8, { eyes: 'fierce', ears: 'none', horn: 'big', tail: 'flame', pat: 'bolt', mouth: 'fang', shift: 40 }],
    ['aurore', 'Aurore', 'E', 'epaules', 'spirit', 285, { eyes: 'spark', ears: 'fin', horn: 'one', tail: 'none', pat: 'dots', mouth: 'smile' }],
    ['colosse', 'Colosse', 'E', 'dos', 'golem', 215, { eyes: 'fierce', ears: 'none', horn: 'big', tail: 'none', pat: 'stripes', mouth: 'flat', shift: 160 }],
    ['sphinx', 'Sphinx', 'E', 'abdos', 'beast', 265, { eyes: 'sleepy', ears: 'cat', horn: 'one', tail: 'curl', pat: 'stripes', mouth: 'smile' }],

    ['dragon', 'Dragon de Fonte', 'L', 'pectoraux', 'drake', 45, { eyes: 'fierce', ears: 'none', horn: 'big', tail: 'flame', pat: 'bolt', mouth: 'fang', shift: -20, sat: 80 }],
    ['phenix', 'Phénix', 'L', 'mollets', 'bird', 28, { eyes: 'spark', ears: 'none', horn: 'crest', tail: 'flame', pat: 'bolt', mouth: 'smile', shift: 20, sat: 85 }]
  ];
  var IT = [
    // tenue : [--f3, --f4]
    ['t-marine', 'Tenue bleu marine', 'C', 'tenue', ['#2f5d8a', '#4c7fb0']], ['t-foret', 'Tenue vert forêt', 'C', 'tenue', ['#2f7a57', '#4a9a74']], ['t-bordeaux', 'Tenue bordeaux', 'C', 'tenue', ['#8a2f4a', '#b04c68']],
    ['t-violet', 'Tenue violet nuit', 'U', 'tenue', ['#5b3f9a', '#7d62bd']], ['t-sable', 'Tenue sable', 'U', 'tenue', ['#b89a5f', '#d1b57e']], ['t-turquoise', 'Tenue turquoise', 'U', 'tenue', ['#1f8f99', '#3fb0ba']],
    ['t-corail', 'Tenue corail', 'R', 'tenue', ['#d9534f', '#ee7a6f']], ['t-or', 'Tenue or vieilli', 'R', 'tenue', ['#b8892a', '#d8aa48']],
    ['t-neon', 'Tenue néon rose', 'E', 'tenue', ['#d6247f', '#f0509f']], ['t-glace', 'Tenue glace', 'E', 'tenue', ['#6fc3e6', '#a9e0f5']],
    ['t-obsidienne', 'Tenue obsidienne dorée', 'L', 'tenue', ['#1b1b24', '#e7b53a']],
    // cheveux : [--f5]
    ['h-chatain', 'Cheveux châtain', 'C', 'cheveux', ['#7b5a45']], ['h-noir', 'Cheveux noirs', 'C', 'cheveux', ['#1c1a1f']],
    ['h-roux', 'Cheveux roux', 'U', 'cheveux', ['#b5532a']], ['h-blond', 'Cheveux blonds', 'U', 'cheveux', ['#d8b25a']],
    ['h-bleu', 'Cheveux bleus', 'R', 'cheveux', ['#2b6fd6']], ['h-violet', 'Cheveux violets', 'E', 'cheveux', ['#8e44e0']], ['h-argent', 'Cheveux argent', 'L', 'cheveux', ['#d9dfe6']],
    // muscle sollicité : [--fxc]
    ['m-rouge', 'Muscles rouge vif', 'C', 'muscle', ['#e5383b']], ['m-vert', 'Muscles vert menthe', 'U', 'muscle', ['#2fbf71']], ['m-cyan', 'Muscles cyan', 'U', 'muscle', ['#19b5c9']],
    ['m-bleu', 'Muscles bleu électrique', 'R', 'muscle', ['#2b78ff']], ['m-rose', 'Muscles rose vif', 'R', 'muscle', ['#ff4fa3']], ['m-violet', 'Muscles violet', 'E', 'muscle', ['#a85bff']], ['m-or', 'Muscles dorés', 'L', 'muscle', ['#ffc233']]
  ];
  var SLOTS = [['tenue', 'Tenue'], ['cheveux', 'Cheveux'], ['muscle', 'Muscles sollicités']];
  var CRE = {}, ITM = {};
  CR.forEach(function (a) { CRE[a[0]] = Object.assign({ id: a[0], name: a[1], rar: a[2], zone: a[3], arch: a[4], hue: a[5] }, a[6]); });
  IT.forEach(function (a) { ITM[a[0]] = { id: a[0], name: a[1], rar: a[2], slot: a[3], v: a[4] }; });

  /* ------------------------------------------------------------------ état */
  function blank() { return { v: 1, init: false, tokens: 0, shards: 0, pulls: 0, pe: 0, pl: 0, owned: {}, items: {}, team: [], equip: {}, awarded: {}, days: {}, wk: {}, opts: { sound: false, haptic: true, hide: false }, log: [] }; }
  var S = null;
  function load() {
    try { var o = JSON.parse(localStorage.getItem(KEY) || 'null'); if (o && o.v === 1) S = Object.assign(blank(), o); } catch (e) {}
    if (!S) S = blank();
    return S;
  }
  function save() { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch (e) {} }
  function st() { return S || load(); }
  var J = { rng: function () { var a = new Uint32Array(1); (window.crypto || window.msCrypto).getRandomValues(a); return a[0] / 4294967296; } };

  /* ------------------------------------------------------------------ lecture des séances (globales de l'appli) */
  function g(n) { return window.APPX ? window.APPX[n] : undefined; }   // passerelle exposée par index.html
  function sess() { var f = g('SESS'); return f ? f() : []; }
  function exs() { var f = g('EX'); return f ? f() : {}; }
  function zonesOfEx(e) { var f = g('zonesOf'); return f ? f(e) : { p: [], s: [] }; }
  function zoneSetsAll() {
    var out = {}, EXs = exs();
    sess().forEach(function (s) { s.entries.forEach(function (en) {
      var e = EXs[en.exercise_id]; if (!e || e.kind === 'cardio') return;
      var z = zonesOfEx(e), n = en.sets.length;
      z.p.forEach(function (k) { out[k] = (out[k] || 0) + n; }); z.s.forEach(function (k) { out[k] = (out[k] || 0) + n * 0.5; });
    }); });
    return out;
  }
  function sessionZones(s) {
    var o = {}, EXs = exs();
    s.entries.forEach(function (en) { var e = EXs[en.exercise_id]; if (e && e.kind !== 'cardio') { var z = zonesOfEx(e); z.p.concat(z.s).forEach(function (k) { o[k] = 1; }); } });
    return Object.keys(o);
  }
  function wkKey(day) { var f = g('mondayOf'); return f ? f(day) : day; }
  function levelOf(cid, zs) { var z = zs || zoneSetsAll(); return 1 + Math.floor(Math.sqrt(z[CRE[cid].zone] || 0)); }
  function stageOf(lv) { return lv >= 14 ? 3 : lv >= 6 ? 2 : 1; }

  /* ------------------------------------------------------------------ gains : uniquement via l'effort réel */
  function scoreSession(s) {
    var n = 0, ef = [], pr = 0, prs = g('computePRs');
    s.entries.forEach(function (en) { n += Math.min(6, en.sets.length); if (en.effort) ef.push(en.effort); });
    n = Math.min(24, n);
    try { var p = prs ? prs().bySession[s.id] : null; pr = p && p.length ? 1 : 0; } catch (e) {}
    var avg = ef.length ? ef.reduce(function (a, b) { return a + b; }, 0) / ef.length : 0;
    var lines = [];
    if (n >= 3) lines.push(['Séance terminée', 1]);
    if (n >= 10) lines.push(['10 séries ou plus', 1]);
    if (n >= 3 && pr) lines.push(['Record battu', 1]);
    if (n >= 3 && avg >= 3 && avg <= 4.5) lines.push(['Effort juste (ressenti « Juste bien » ou « Dur »)', 1]);
    return { sets: n, avg: avg, lines: lines, total: lines.reduce(function (a, l) { return a + l[1]; }, 0) };
  }
  function init() {
    var s = st();
    if (s.init) return;
    s.init = true; s.tokens = 3; sess().forEach(function (x) { s.awarded[x.id] = 0; });   // l'historique existant ne rapporte rien, un cadeau de bienvenue suffit
    s.owned.gloumi = { n: 0 }; s.team = ['gloumi'];
    s.log.unshift({ t: Date.now(), m: 'Bienvenue : 3 jetons et Gloumi' }); save();
  }
  // Appelé après l'enregistrement d'une NOUVELLE séance. Renvoie un compte rendu, ou null s'il n'y a rien à créditer.
  function award(sid) {
    init(); var s = st(), x = sess().find(function (z) { return z.id === sid; });
    if (!x || s.awarded[sid] != null) return null;
    var sc = scoreSession(x), gain = sc.total, lines = sc.lines.slice(), note = '';
    var used = s.days[x.day] || 0, room = Math.max(0, DAY_CAP - used);
    if (gain > room) { note = room ? 'Plafond de ' + DAY_CAP + ' jetons par jour atteint.' : 'Plafond de ' + DAY_CAP + ' jetons par jour déjà atteint : la séance compte pour tes stats, pas pour les jetons.'; gain = room; }
    s.days[x.day] = used + gain; s.awarded[sid] = gain; s.tokens += gain;
    // série d'éclats pour l'équipe : chaque esprit dont la zone a travaillé
    var zs = sessionZones(x), bond = 0;
    s.team.forEach(function (cid) { if (zs.indexOf(CRE[cid].zone) >= 0 && gain > 0) bond += 3; });
    if (bond) { s.shards += bond; lines.push(['Équipe : ' + bond / 3 + ' esprit' + (bond > 3 ? 's' : '') + ' entraîné' + (bond > 3 ? 's' : '') + ' (+' + bond + ' éclats)', 0]); }
    var q = quests(true);
    q.done.forEach(function (d) { lines.push([d.t, d.r]); });
    var lv = levelUps(); save();
    return { tokens: gain + q.done.reduce(function (a, d) { return a + d.r; }, 0), lines: lines, note: note, bond: bond, ups: lv, balance: s.tokens, sets: sc.sets };
  }
  // quêtes de la semaine : évaluées à partir des séances, créditées une seule fois par semaine
  function questList() {
    var s = st(), key = wkKey(g('today') ? g('today')() : new Date().toISOString().slice(0, 10));
    var mine = sess().filter(function (x) { return wkKey(x.day) === key; });
    var zset = {}; mine.forEach(function (x) { sessionZones(x).forEach(function (k) { zset[k] = 1; }); });
    var teamZ = {}; s.team.forEach(function (c) { teamZ[CRE[c].zone] = 1; });
    var tz = Object.keys(teamZ), W = g('WGOAL') || 3;
    return { key: key, list: [
      { id: 'obj', t: 'Objectif de la semaine : ' + W + ' séances', ok: mine.length >= W, p: Math.min(mine.length, W) + '/' + W, r: 2 },
      { id: 'var', t: 'Variété : 5 zones différentes', ok: Object.keys(zset).length >= 5, p: Math.min(Object.keys(zset).length, 5) + '/5', r: 1 },
      { id: 'eq', t: 'Équipe complète : travaille la zone de chacun de tes esprits', ok: tz.length >= 2 && tz.every(function (k) { return zset[k]; }), p: tz.filter(function (k) { return zset[k]; }).length + '/' + Math.max(tz.length, 2), r: 2 }
    ] };
  }
  function quests(claim) {
    var s = st(), q = questList(), w = s.wk[q.key] = s.wk[q.key] || {}, done = [];
    q.list.forEach(function (it) { it.claimed = !!w[it.id]; if (claim && it.ok && !w[it.id]) { w[it.id] = 1; s.tokens += it.r; done.push({ t: 'Quête : ' + it.t, r: it.r }); it.claimed = true; } });
    return { list: q.list, done: done };
  }
  var seenLv = null;
  function levelUps() {   // détecte les nouveaux stades d'évolution depuis la dernière consultation
    var s = st(), zs = zoneSetsAll(), ups = [], mem = s.stg = s.stg || {};
    Object.keys(s.owned).forEach(function (cid) { var stg = stageOf(levelOf(cid, zs)); if (mem[cid] == null) mem[cid] = stg; else if (stg > mem[cid]) { ups.push({ id: cid, stage: stg }); mem[cid] = stg; } });
    return ups;
  }

  /* ------------------------------------------------------------------ tirages */
  function rollRarity() {
    var s = st(), r = J.rng(), k;
    s.pe++; s.pl++;
    if (s.pl >= PITY_L) k = 'L';
    else if (s.pe >= PITY_E) k = J.rng() < 0.2 ? 'L' : 'E';
    else { var a = 0; k = 'C'; for (var i = 0; i < RK.length; i++) { a += RATES[RK[i]]; if (r < a) { k = RK[i]; break; } } }
    if (k === 'E' || k === 'L') s.pe = 0;
    if (k === 'L') s.pl = 0;
    return k;
  }
  function pick(arr) { return arr[Math.min(arr.length - 1, Math.floor(J.rng() * arr.length))]; }
  function pullOne() {
    var s = st(), k = rollRarity(), cs = CR.filter(function (c) { return c[2] === k; }), its = IT.filter(function (i) { return i[2] === k && !s.items[i[0]]; });
    var asItem = its.length && J.rng() < 0.35, res = { rar: k };
    if (asItem) { var it = pick(its); s.items[it[0]] = 1; res.kind = 'item'; res.id = it[0]; res.isNew = true; }
    else {
      var c = pick(cs); res.kind = 'crea'; res.id = c[0];
      if (s.owned[c[0]]) { s.owned[c[0]].n++; res.isNew = false; res.shards = SHARDS[k]; s.shards += SHARDS[k]; }
      else { s.owned[c[0]] = { n: 0 }; res.isNew = true; if (s.team.length < 3) s.team.push(c[0]); }
    }
    s.pulls++; return res;
  }
  function pull(n) {
    init(); var s = st(); n = n === MULTI ? MULTI : 1; var cost = n * PULL_COST;
    if (s.tokens < cost) return null;
    s.tokens -= cost; var out = []; for (var i = 0; i < n; i++) out.push(pullOne());
    s.log.unshift({ t: Date.now(), m: n + ' tirage' + (n > 1 ? 's' : '') + ' : ' + out.map(function (r) { return r.rar; }).join(' ') }); s.log.length = Math.min(s.log.length, 30);
    save(); return out;
  }
  function buy(kind, id) {
    var s = st(), o = kind === 'crea' ? CRE[id] : ITM[id]; if (!o) return false;
    var owned = kind === 'crea' ? s.owned[id] : s.items[id]; if (owned || s.shards < PRICE[o.rar]) return false;
    s.shards -= PRICE[o.rar];
    if (kind === 'crea') { s.owned[id] = { n: 0 }; if (s.team.length < 3) s.team.push(id); } else s.items[id] = 1;
    save(); return true;
  }
  function equip(slot, id) {
    var s = st(); if (id && !(s.items[id] && ITM[id].slot === slot)) return;
    if (id) s.equip[slot] = id; else delete s.equip[slot]; save(); applyWardrobe();
  }
  function toggleTeam(cid) {
    var s = st(), i = s.team.indexOf(cid); if (!s.owned[cid]) return;
    if (i >= 0) { if (s.team.length > 1) s.team.splice(i, 1); } else if (s.team.length < 3) s.team.push(cid); else s.team.shift(), s.team.push(cid);
    save();
  }
  var WARD_VARS = ['--f3', '--f4', '--f5', '--fxc'];
  function applyWardrobe() {
    var s = st(), root = document.documentElement;
    WARD_VARS.forEach(function (v) { root.style.removeProperty(v); });
    Object.keys(s.equip).forEach(function (sl) {
      var it = ITM[s.equip[sl]]; if (!it) return;
      if (sl === 'tenue') { root.style.setProperty('--f3', it.v[0]); root.style.setProperty('--f4', it.v[1]); }
      if (sl === 'cheveux') root.style.setProperty('--f5', it.v[0]);
      if (sl === 'muscle') root.style.setProperty('--fxc', it.v[0]);
    });
  }

  /* ------------------------------------------------------------------ rendu */
  var CSS = '.j-top{display:flex;gap:8px;margin:6px 0 10px}.j-top>div{flex:1;background:var(--c);border:1px solid var(--l);border-radius:12px;padding:8px 10px;text-align:center}.j-top b{display:block;font-size:22px}.j-top span{font-size:12px;color:var(--m)}'
    + '.j-sub{display:flex;gap:6px;margin:6px 0 10px;overflow-x:auto}.j-sub button{flex:1 0 auto;padding:9px 12px;border:2px solid var(--l);background:var(--c);color:var(--t);border-radius:10px;font:inherit;font-size:14px;font-weight:700}.j-sub button.on{background:var(--a);border-color:var(--a);color:var(--on)}'
    + '.j-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.j-card{position:relative;background:var(--c);border:2px solid var(--l);border-radius:12px;padding:4px 4px 8px;text-align:center;font-size:12px;color:var(--t);font-family:inherit;cursor:pointer}.j-card svg{width:100%;display:block}.j-card b{display:block;font-size:13px}.j-card small{color:var(--m)}'
    + '.j-card.lock{opacity:.55}.j-card.sel{outline:3px solid var(--a)}.j-r-C{border-color:#8fa3b3}.j-r-U{border-color:#52c27a}.j-r-R{border-color:#4aa3ff}.j-r-E{border-color:#b06bff}.j-r-L{border-color:#ffc233;box-shadow:0 0 12px #ffc23388}'
    + '.j-badge{position:absolute;top:4px;right:4px;font-size:11px;font-weight:700;border-radius:8px;padding:1px 6px;background:var(--bg);color:var(--t)}'
    + '.j-team{display:flex;gap:8px}.j-team .j-card{flex:1}'
    + '.j-q{display:flex;justify-content:space-between;gap:8px;padding:7px 0;border-top:1px solid var(--l);font-size:14px}.j-q:first-of-type{border-top:0}.j-q.ok{color:var(--a);font-weight:700}'
    + '.j-bar{height:6px;border-radius:3px;background:var(--l);overflow:hidden;margin:3px 0}.j-bar i{display:block;height:100%;background:var(--a)}'
    + '.j-ov{position:fixed;inset:0;z-index:30;background:rgba(8,12,18,.96);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:18px;color:#fff;text-align:center}'
    + '.j-ov .j-big{width:min(78vw,300px)}.j-ov h2{font-size:26px;margin:6px 0}.j-ov p{margin:4px 0;color:#ccd6df}.j-ov .go{max-width:320px}.j-ov .sm{background:transparent;color:#fff;border-color:#ffffff55;max-width:320px;width:100%;margin-top:8px}'
    + '.j-egg{width:120px;animation:j-shake .5s infinite}@keyframes j-shake{0%,100%{transform:rotate(0)}20%{transform:rotate(-9deg)}40%{transform:rotate(8deg)}60%{transform:rotate(-6deg)}80%{transform:rotate(5deg)}}'
    + '.j-flash{position:fixed;inset:0;z-index:31;pointer-events:none;animation:j-fl .7s ease-out forwards}@keyframes j-fl{0%{opacity:.95}100%{opacity:0}}'
    + '.j-pop{animation:j-pop .5s cubic-bezier(.2,1.4,.4,1)}@keyframes j-pop{0%{transform:scale(.3);opacity:0}100%{transform:scale(1);opacity:1}}'
    + '.j-rule li{margin:5px 0;font-size:14px}.j-tag{display:inline-block;border-radius:999px;padding:1px 8px;font-size:11px;font-weight:700;color:#10202b}'
    + '.j-pv{display:flex;gap:10px;align-items:center}.j-pv svg{width:46%;flex:none;background:var(--bg);border-radius:8px}'
    + '.j-sw{display:inline-block;width:18px;height:18px;border-radius:50%;border:2px solid var(--l);vertical-align:middle;margin-right:2px}'
    + '@media (prefers-reduced-motion:reduce){.j-egg,.j-pop,.j-flash{animation:none}}';
  function css() { if (document.getElementById('j-css')) return; var el = document.createElement('style'); el.id = 'j-css'; el.textContent = CSS; document.head.appendChild(el); }
  function E(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function tag(r) { var m = CREA.RAR[r]; return '<span class="j-tag" style="background:' + m.col + '">' + m.n + '</span>'; }
  function art(cid, stg, opt) { return CREA.svg(CRE[cid], stg, opt); }
  function itemArt(it) {
    if (it.slot === 'tenue') return '<span class="j-sw" style="background:' + it.v[0] + '"></span><span class="j-sw" style="background:' + it.v[1] + '"></span>';
    return '<span class="j-sw" style="background:' + it.v[0] + '"></span>';
  }
  var sub = 'tirage', sel = null;
  function head() {
    var s = st();
    return '<div class="j-top"><div><b>' + s.tokens + '</b><span>jeton' + (s.tokens > 1 ? 's' : '') + '</span></div><div><b>' + s.shards + '</b><span>éclats</span></div><div><b>' + Object.keys(s.owned).length + '/' + CR.length + '</b><span>esprits</span></div></div>';
  }
  function subnav() {
    return '<div class="j-sub" role="tablist">' + [['tirage', 'Tirage'], ['collection', 'Collection'], ['garde', 'Garde-robe'], ['boutique', 'Boutique'], ['regles', 'Règles']].map(function (t) { return '<button class="' + (sub === t[0] ? 'on' : '') + '" onclick="JEU.sub(\'' + t[0] + '\')">' + t[1] + '</button>'; }).join('') + '</div>';
  }
  function teamHtml() {
    var s = st(), zs = zoneSetsAll();
    return '<div class="j-team">' + s.team.map(function (cid) { var c = CRE[cid], lv = levelOf(cid, zs), stg = stageOf(lv); return '<div class="j-card j-r-' + c.rar + '" style="cursor:default">' + art(cid, stg) + '<b>' + E(c.name) + '</b><small>Niv. ' + lv + ' · ' + ZN[c.zone] + '</small></div>'; }).join('') + '</div>';
  }
  function questsHtml() {
    var q = quests(false);
    return '<section class="card"><h2>Quêtes de la semaine</h2><p class="m">Créditées toutes seules quand tu t\'entraînes.</p>' + q.list.map(function (it) { return '<div class="j-q ' + (it.ok ? 'ok' : '') + '"><span>' + (it.ok ? '✓ ' : '') + E(it.t) + '<br><small class="m">' + it.p + (it.claimed ? ' · reçu' : '') + '</small></span><span>+' + it.r + '</span></div>'; }).join('') + '</section>';
  }
  function vTirage() {
    var s = st(), toE = PITY_E - s.pe, toL = PITY_L - s.pl;
    var h = '<section class="card"><h2>Ton équipe</h2>' + teamHtml() + '<p class="m">Les esprits évoluent avec les séries que tu fais sur leur zone. Tu choisis l\'équipe dans la collection.</p></section>';
    h += '<section class="card"><h2>Tirage</h2><p class="m">Un jeton = un tirage. Les jetons viennent de tes séances, rien d\'autre.</p>'
      + '<button class="go" ' + (s.tokens >= 1 ? '' : 'disabled style="opacity:.5"') + ' onclick="JEU.pull(1)">Tirer (1 jeton)</button>'
      + '<button class="sm w" ' + (s.tokens >= MULTI ? '' : 'disabled style="opacity:.5"') + ' onclick="JEU.pull(' + MULTI + ')">Tirer ×' + MULTI + ' (' + MULTI + ' jetons)</button>'
      + '<p class="m" style="margin-top:8px">Épique ou mieux garanti dans ' + toE + ' tirage' + (toE > 1 ? 's' : '') + ' au plus, Légendaire dans ' + toL + ' au plus.</p>'
      + (s.tokens < 1 ? '<p class="m"><b>Plus de jeton ?</b> Termine une séance : tu en gagnes de 1 à ' + DAY_CAP + ' selon ton effort.</p>' : '') + '</section>';
    h += questsHtml();
    h += '<section class="card"><h2>Comment gagner des jetons</h2><ul class="j-rule" style="padding-left:18px;margin:6px 0"><li>Séance terminée (3 séries ou plus) : +1</li><li>10 séries ou plus : +1</li><li>Record battu : +1</li><li>Ressenti « Juste bien » ou « Dur » : +1</li><li>Maximum ' + DAY_CAP + ' jetons par jour. « À fond » ne rapporte pas plus : mieux vaut récupérer.</li></ul></section>';
    return h;
  }
  function vCollection() {
    var s = st(), zs = zoneSetsAll(), h = '<p class="m">Touche un esprit pour le voir. Équipe : jusqu\'à 3 esprits, marqués ★.</p>';
    ['L', 'E', 'R', 'U', 'C'].forEach(function (r) {
      var l = CR.filter(function (c) { return c[2] === r; });
      h += '<h3>' + CREA.RAR[r].n + ' · ' + l.filter(function (c) { return s.owned[c[0]]; }).length + '/' + l.length + '</h3><div class="j-grid">';
      l.forEach(function (c) {
        var cid = c[0], o = s.owned[cid];
        if (!o) h += '<div class="j-card lock">' + CREA.svg(CRE[cid], 1, { silhouette: true }) + '<b>???</b><small>' + ZN[c[3]] + '</small></div>';
        else { var lv = levelOf(cid, zs); h += '<button class="j-card j-r-' + r + '" onclick="JEU.show(\'' + cid + '\')">' + (s.team.indexOf(cid) >= 0 ? '<span class="j-badge">★</span>' : '') + art(cid, stageOf(lv)) + '<b>' + E(c[1]) + '</b><small>Niv. ' + lv + (o.n ? ' · ×' + (o.n + 1) : '') + '</small></button>'; }
      });
      h += '</div>';
    });
    return h;
  }
  function vGarde() {
    var s = st(), ex = Object.values(exs()), fd = window.FIGDATA || {}, pv = '';
    var e = ex.find(function (x) { return x.slug === 'curl-halteres' && fd[x.slug]; }) || ex.find(function (x) { return x.slug && fd[x.slug]; });
    if (e) { try { pv = g('figSvg')(e, fd[e.slug], true); } catch (er) {} }
    var h = '<section class="card"><h2>Aperçu</h2><div class="j-pv">' + pv + '<p class="m">Ta tenue, tes cheveux et la couleur des muscles sollicités se retrouvent dans toutes les animations d\'exercices.</p></div></section>';
    SLOTS.forEach(function (sl) {
      var mine = IT.filter(function (i) { return i[3] === sl[0]; });
      h += '<section class="card"><h2>' + sl[1] + ' <span class="m">· ' + mine.filter(function (i) { return s.items[i[0]]; }).length + '/' + mine.length + '</span></h2><div class="chips"><button class="chip ' + (s.equip[sl[0]] ? '' : 'on') + '" onclick="JEU.equip(\'' + sl[0] + '\',null)">Par défaut</button>'
        + mine.filter(function (i) { return s.items[i[0]]; }).map(function (i) { var it = ITM[i[0]]; return '<button class="chip ' + (s.equip[sl[0]] === it.id ? 'on' : '') + '" onclick="JEU.equip(\'' + sl[0] + '\',\'' + it.id + '\')">' + itemArt(it) + ' ' + E(it.name.replace(/^(Tenue|Cheveux|Muscles) ?/, '').trim() || it.name) + '</button>'; }).join('')
        + '</div>' + (mine.every(function (i) { return s.items[i[0]]; }) ? '<p class="m">Tout est débloqué.</p>' : '<p class="m">' + mine.filter(function (i) { return !s.items[i[0]]; }).length + ' à débloquer par tirage ou en boutique.</p>') + '</section>';
    });
    return h;
  }
  function vBoutique() {
    var s = st(), h = '<p class="m">Les doublons te donnent des éclats (Commune ' + SHARDS.C + ', Légendaire ' + SHARDS.L + '). Tu peux les dépenser ici pour choisir exactement ce que tu veux : pas de hasard.</p><p><b>' + s.shards + ' éclats</b></p>';
    var rows = [];
    CR.forEach(function (c) { if (!s.owned[c[0]]) rows.push(['crea', c[0], c[1], c[2], 'Esprit · ' + ZN[c[3]]]); });
    IT.forEach(function (i) { if (!s.items[i[0]]) rows.push(['item', i[0], i[1], i[2], 'Garde-robe']); });
    if (!rows.length) return h + '<p class="empty">Tu as tout. Bravo !</p>';
    rows.sort(function (a, b) { return PRICE[a[3]] - PRICE[b[3]]; });
    return h + '<div class="card">' + rows.map(function (r) { var p = PRICE[r[3]], can = s.shards >= p; return '<div class="j-q" style="cursor:pointer;align-items:center" onclick="JEU.preview(\'' + r[0] + '\',\'' + r[1] + '\')"><span>' + E(r[2]) + ' ' + tag(r[3]) + '<br><small class="m">' + r[4] + ' · toucher pour voir</small></span><button class="sm" ' + (can ? '' : 'disabled style="opacity:.5"') + ' onclick="event.stopPropagation();JEU.buy(\'' + r[0] + '\',\'' + r[1] + '\')">' + p + ' éclats</button></div>'; }).join('') + '</div>';
  }
  function vRegles() {
    var s = st(), pct = function (k) { return Math.round(RATES[k] * 100) + ' %'; };
    return '<section class="card"><h2>Taux de tirage</h2><p class="m">Affichés tels qu\'ils sont codés.</p><table>' + RK.slice().reverse().map(function (k) { return '<tr><td>' + tag(k) + '</td><td style="text-align:right">' + pct(k) + '</td></tr>'; }).join('') + '</table>'
      + '<p class="m">Garantie : Épique ou mieux tous les ' + PITY_E + ' tirages au plus, Légendaire tous les ' + PITY_L + ' au plus (compteurs actuels : ' + s.pe + ' et ' + s.pl + '). Chaque tirage donne 65 % d\'esprit et 35 % d\'objet de garde-robe, quand il en reste de cette rareté.</p></section>'
      + '<section class="card"><h2>Garde-fous</h2><ul class="j-rule" style="padding-left:18px"><li>Aucun achat, aucun argent réel, aucune publicité.</li><li>Les jetons ne s\'obtiennent qu\'en s\'entraînant. Maximum ' + DAY_CAP + ' par jour : s\'entraîner plus ne rapporte pas plus.</li><li>Aucune série à perdre : si tu pauses, tu ne perds rien, tes jetons n\'expirent jamais.</li><li>Le niveau d\'un esprit vient des séries réellement faites sur sa zone.</li><li>Tout est stocké sur ton téléphone, rien n\'est envoyé.</li><li>Les jeux de tirage peuvent donner envie d\'en refaire : si tu le sens, tu peux masquer l\'onglet ci-dessous.</li></ul></section>'
      + '<section class="card"><h2>Réglages</h2><div class="chips"><button class="chip ' + (s.opts.sound ? 'on' : '') + '" onclick="JEU.opt(\'sound\')">Sons</button><button class="chip ' + (s.opts.haptic ? 'on' : '') + '" onclick="JEU.opt(\'haptic\')">Vibrations</button><button class="chip ' + (s.opts.hide ? 'on' : '') + '" onclick="JEU.opt(\'hide\')">Masquer l\'onglet Esprits</button></div></section>';
  }
  function view() {
    init(); css(); var q = quests(true); if (q.done.length) { save(); toast2('+' + q.done.reduce(function (a, d) { return a + d.r; }, 0) + ' jeton(s) : quête accomplie'); }
    var body = sub === 'collection' ? vCollection() : sub === 'garde' ? vGarde() : sub === 'boutique' ? vBoutique() : sub === 'regles' ? vRegles() : vTirage();
    return head() + subnav() + body;
  }
  function toast2(m) { try { g('toast')(m); } catch (e) {} }
  function homeCard() {
    var s = st(); if (s.opts.hide) return ''; init(); css();
    var zs = zoneSetsAll(), q = quests(false), done = q.list.filter(function (i) { return i.ok; }).length;
    return '<section class="card" onclick="go(\'jeu\')" style="cursor:pointer"><div style="display:flex;justify-content:space-between;align-items:baseline"><h2>Esprits</h2><span class="m">' + s.tokens + ' jeton' + (s.tokens > 1 ? 's' : '') + ' · ' + done + '/' + q.list.length + ' quêtes</span></div>'
      + '<div class="j-team" style="margin-top:6px">' + s.team.map(function (cid) { var lv = levelOf(cid, zs); return '<div style="flex:1;text-align:center;font-size:12px">' + art(cid, stageOf(lv), { bare: true }) + '<b>' + E(CRE[cid].name) + '</b><br><span class="m">Niv. ' + lv + '</span></div>'; }).join('') + '</div></section>';
  }

  /* ------------------------------------------------------------------ overlays */
  function ov(html, cls) { var o = document.createElement('div'); o.className = 'j-ov ' + (cls || ''); o.setAttribute('role', 'dialog'); o.setAttribute('aria-modal', 'true'); o.innerHTML = html; document.body.appendChild(o); return o; }
  function closeOv(el) { var o = el.closest ? el.closest('.j-ov') : el; if (o) o.remove(); try { g('R')(); } catch (e) {} }
  function reduced() { return !!(window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches); }
  function beep(r) {
    if (!st().opts.sound) return;
    try { var A = window.AudioContext || window.webkitAudioContext, c = new A(), n = { C: 1, U: 2, R: 3, E: 4, L: 6 }[r], i; for (i = 0; i < n; i++) { var o = c.createOscillator(), gn = c.createGain(); o.frequency.value = 440 * Math.pow(1.26, i); gn.gain.value = 0.06; o.connect(gn); gn.connect(c.destination); o.start(c.currentTime + i * 0.09); o.stop(c.currentTime + i * 0.09 + 0.12); } } catch (e) {}
  }
  function buzz(r) { if (st().opts.haptic && navigator.vibrate) { try { navigator.vibrate(r === 'L' ? [60, 40, 60, 40, 120] : r === 'E' ? [50, 30, 80] : 20); } catch (e) {} } }
  function resultCard(res, i, total) {
    var r = CREA.RAR[res.rar], zs = null, inner, name, line;
    if (res.kind === 'crea') { var c = CRE[res.id]; inner = art(res.id, 1); name = c.name; line = res.isNew ? '<b style="color:#ffd45e">Nouveau !</b>' : 'Doublon : +' + res.shards + ' éclats'; }
    else { var it = ITM[res.id]; inner = '<div style="padding:40px 0;font-size:0">' + it.v.map(function (col) { return '<span style="display:inline-block;width:70px;height:70px;border-radius:50%;background:' + col + ';margin:0 6px;border:3px solid #fff"></span>'; }).join('') + '</div>'; name = it.name; line = '<b style="color:#ffd45e">Nouveau !</b> Garde-robe'; }
    return '<div class="j-pop"><div class="j-big">' + inner + '</div><h2>' + E(name) + '</h2><p>' + tag(res.rar) + '</p><p>' + line + '</p>' + (total > 1 ? '<p class="m" style="color:#aab">' + (i + 1) + '/' + total + '</p>' : '') + '</div>';
  }
  function playPull(results) {
    var best = results.reduce(function (a, r) { return RK.indexOf(r.rar) > RK.indexOf(a) ? r.rar : a; }, 'C');
    var o = ov('<div class="j-egg">' + eggSvg(CREA.RAR[best].col) + '</div><p>Un esprit se réveille…</p>');
    var i = 0;
    function flash(col) { var f = document.createElement('div'); f.className = 'j-flash'; f.style.background = col; document.body.appendChild(f); setTimeout(function () { f.remove(); }, 800); }
    function next() {
      if (i >= results.length) return summary();
      var r = results[i], col = CREA.RAR[r.rar].col; if (!reduced()) flash(col); beep(r.rar); buzz(r.rar);
      o.innerHTML = resultCard(r, i, results.length) + '<button class="go" id="j-n">' + (i + 1 < results.length ? 'Suivant' : (results.length > 1 ? 'Résumé' : 'Super')) + '</button>' + (results.length > 1 && i + 1 < results.length ? '<button class="sm" id="j-s">Tout passer</button>' : '');
      document.getElementById('j-n').onclick = function () { i++; if (i >= results.length || results.length === 1) { results.length === 1 ? closeOv(o) : summary(); } else next(); };
      var sk = document.getElementById('j-s'); if (sk) sk.onclick = function () { summary(); };
    }
    function summary() {
      o.innerHTML = '<h2>Tirage ×' + results.length + '</h2><div class="j-grid" style="width:100%;max-width:420px">' + results.map(function (r) { return r.kind === 'crea' ? '<div class="j-card j-r-' + r.rar + '" style="background:#0e161c;color:#fff">' + art(r.id, 1, { bare: true }) + '<small>' + E(CRE[r.id].name) + (r.isNew ? ' · nouveau' : '') + '</small></div>' : '<div class="j-card j-r-' + r.rar + '" style="background:#0e161c;color:#fff"><div style="padding:18px 0">' + ITM[r.id].v.map(function (col) { return '<span class="j-sw" style="width:26px;height:26px;background:' + col + '"></span>'; }).join('') + '</div><small>' + E(ITM[r.id].name) + '</small></div>'; }).join('') + '</div><button class="go" id="j-n2">Fermer</button>';
      document.getElementById('j-n2').onclick = function () { closeOv(o); };
    }
    if (reduced()) next(); else setTimeout(next, 1100);
  }
  function eggSvg(col) { return '<svg viewBox="0 0 100 120"><defs><radialGradient id="jeg" cx="40%" cy="30%" r="80%"><stop offset="0" stop-color="#fff"/><stop offset=".5" stop-color="' + col + '"/><stop offset="1" stop-color="#223"/></radialGradient></defs><path d="M50 8C72 8 88 50 88 78c0 22-17 36-38 36S12 100 12 78C12 50 28 8 50 8z" fill="url(#jeg)"/><path d="M28 70l10-8 8 10 8-10 10 8 8-6" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="3" stroke-linecap="round"/></svg>'; }
  function rewardOverlay(rep) {
    css();
    var lines = rep.lines.filter(function (l) { return l[1] > 0 || /Équipe/.test(l[0]); });
    var o = ov('<h2>' + (rep.tokens ? '+' + rep.tokens + ' jeton' + (rep.tokens > 1 ? 's' : '') : 'Séance enregistrée') + '</h2>'
      + lines.map(function (l) { return '<p>' + E(l[0]) + (l[1] ? ' <b>+' + l[1] + '</b>' : '') + '</p>'; }).join('')
      + (rep.note ? '<p style="color:#ffd45e">' + E(rep.note) + '</p>' : '')
      + (rep.ups.length ? '<h2 style="margin-top:14px">Évolution !</h2>' + rep.ups.map(function (u) { return '<div class="j-big j-pop" style="width:150px;margin:auto">' + art(u.id, u.stage) + '</div><p>' + E(CRE[u.id].name) + ' passe au stade ' + u.stage + '</p>'; }).join('') : '')
      + '<p style="margin-top:10px">Solde : ' + rep.balance + ' jeton' + (rep.balance > 1 ? 's' : '') + '</p>'
      + (rep.balance >= 1 ? '<button class="go" id="j-tt">Tirer maintenant</button>' : '') + '<button class="sm" id="j-la">' + (rep.balance >= 1 ? 'Plus tard' : 'Fermer') + '</button>');
    var tt = document.getElementById('j-tt'); if (tt) tt.onclick = function () { o.remove(); var r = pull(1); if (r) playPull(r); };
    document.getElementById('j-la').onclick = function () { closeOv(o); };
  }
  function preview(kind, id) {
    var s = st(), o = kind === 'crea' ? CRE[id] : ITM[id]; if (!o) return;
    var owned = kind === 'crea' ? !!s.owned[id] : !!s.items[id], can = s.shards >= PRICE[o.rar], body;
    if (kind === 'crea') {
      body = '<div style="display:flex;gap:6px;width:100%;max-width:420px">' + [1, 2, 3].map(function (n) { return '<div style="flex:1;text-align:center;font-size:12px;color:#ccd6df">' + art(id, n) + 'Stade ' + n + '</div>'; }).join('') + '</div>'
        + '<p>Zone : <b>' + ZN[o.zone] + '</b></p><p class="m" style="color:#aab">Il évolue avec tes séries sur cette zone : stade 2 au niveau 6, stade 3 au niveau 14.</p>';
    } else {
      var vars = o.slot === 'tenue' ? '--f3:' + o.v[0] + ';--f4:' + o.v[1] : o.slot === 'cheveux' ? '--f5:' + o.v[0] : '--fxc:' + o.v[0];
      var fd = window.FIGDATA || {}, ex = Object.values(exs()), e = ex.find(function (x) { return x.slug === 'curl-halteres' && fd[x.slug]; }) || ex.find(function (x) { return x.slug && fd[x.slug]; }), fig = '';
      if (e) { try { fig = g('figSvg')(e, fd[e.slug], true); } catch (er) {} }
      body = '<div style="width:100%;max-width:340px;background:var(--bg);border-radius:12px;padding:8px;' + vars + '">' + fig + '</div><p style="margin-top:8px">' + o.v.map(function (col) { return '<span class="j-sw" style="width:30px;height:30px;background:' + col + '"></span>'; }).join('')
        + '</p><p class="m" style="color:#aab">Aperçu sur le personnage, avec ta tenue actuelle pour le reste.</p>';
    }
    var ov2 = ov('<h2>' + E(o.name) + '</h2><p>' + tag(o.rar) + '</p>' + body
      + (owned ? '<p><b style="color:#ffd45e">Déjà débloqué</b></p>' : '<button class="go" id="j-by" ' + (can ? '' : 'disabled style="opacity:.5"') + '>Débloquer pour ' + PRICE[o.rar] + ' éclats' + (can ? '' : ' (tu en as ' + s.shards + ')') + '</button>')
      + '<button class="sm" id="j-pc">Fermer</button>');
    document.getElementById('j-pc').onclick = function () { closeOv(ov2); };
    var by = document.getElementById('j-by'); if (by && can) by.onclick = function () { buy(kind, id); toast2('Débloqué'); closeOv(ov2); };
  }
  function showCrea(cid) {
    var s = st(), c = CRE[cid], lv = levelOf(cid), stg = stageOf(lv), zs = zoneSetsAll(), sets = Math.round(zs[c.zone] || 0);
    var next = stg === 1 ? 6 : stg === 2 ? 14 : null, need = next ? Math.pow(next - 1, 2) : null, prev = stg === 1 ? 0 : Math.pow((stg === 2 ? 6 : 14) - 1, 2);
    var pct = next ? Math.min(100, Math.round((sets - prev) / (need - prev) * 100)) : 100;
    var o = ov('<div class="j-big j-pop">' + art(cid, stg) + '</div><h2>' + E(c.name) + '</h2><p>' + tag(c.rar) + ' · stade ' + stg + '/3 · niveau ' + lv + '</p><p>Zone : <b>' + ZN[c.zone] + '</b> · ' + sets + ' série' + (sets > 1 ? 's' : '') + ' faites</p>'
      + (next ? '<div style="width:260px"><div class="j-bar"><i style="width:' + pct + '%"></i></div></div><p class="m" style="color:#aab">Prochaine évolution au niveau ' + next + ' (' + need + ' séries sur ' + ZN[c.zone].toLowerCase() + ').</p>' : '<p>Stade maximum.</p>')
      + (s.owned[cid].n ? '<p class="m" style="color:#aab">Doublons : ' + s.owned[cid].n + '</p>' : '')
      + '<button class="go" id="j-tm">' + (s.team.indexOf(cid) >= 0 ? 'Retirer de l\'équipe' : 'Mettre dans l\'équipe') + '</button><button class="sm" id="j-cl">Fermer</button>');
    document.getElementById('j-tm').onclick = function () { toggleTeam(cid); closeOv(o); };
    document.getElementById('j-cl').onclick = function () { closeOv(o); };
  }

  /* ------------------------------------------------------------------ API publique */
  function rer() { try { g('R')(); } catch (e) {} }
  window.JEU = {
    state: st, init: init, award: award, rewardOverlay: rewardOverlay, view: view, homeCard: homeCard, applyWardrobe: applyWardrobe,
    hidden: function () { return !!st().opts.hide; },
    sub: function (k) { sub = k; rer(); },
    pull: function (n) { var r = pull(n); if (!r) return toast2('Pas assez de jetons'); playPull(r); },
    buy: function (kind, id) { if (buy(kind, id)) { toast2('Débloqué'); rer(); } },
    equip: function (sl, id) { equip(sl, id); rer(); },
    show: showCrea, preview: preview,
    opt: function (k) { var s = st(); s.opts[k] = !s.opts[k]; save(); if (k === 'hide' && s.opts.hide) { try { g('go')('accueil'); } catch (e) {} } else rer(); try { g('nav')(); } catch (e) {} },
    exportState: function () { var s = st(); return s.init ? JSON.parse(JSON.stringify(s)) : null; },
    importState: function (o) { if (o && o.v === 1) { S = Object.assign(blank(), o); save(); applyWardrobe(); } },
    // pour les tests
    _: { CR: CR, IT: IT, RATES: RATES, PITY_E: PITY_E, PITY_L: PITY_L, DAY_CAP: DAY_CAP, levelOf: levelOf, stageOf: stageOf, pull: pull, pullOne: pullOne, buy: buy, scoreSession: scoreSession, quests: quests, questList: questList, reset: function () { S = blank(); save(); }, rng: J, SHARDS: SHARDS, PRICE: PRICE, CRE: CRE, ITM: ITM }
  };
})();
