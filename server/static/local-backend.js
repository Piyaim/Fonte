// SPDX-License-Identifier: AGPL-3.0-or-later
/* Fonte : serveur local.
   Quand l'appli tourne SANS serveur (coque Android, ou adresse /?local=1 dans un navigateur), les appels
   /api/* de la page sont traités ici et les données vivent dans IndexedDB, sur l'appareil.
   Ce fichier reproduit server/app.py : mêmes routes, mêmes réponses, mêmes règles de validation.
   Hors mode local, il ne fait presque rien (il fournit seulement photoUrl et exportClick). */
(function () {
  'use strict';
  const LOCAL = location.hostname === 'appassets.androidplatform.net' || /[?&]local=1(&|$)/.test(location.search);
  window.FONTE_LOCAL = LOCAL;

  const PHURL = {};
  window.photoUrl = (id, kind) => LOCAL ? (PHURL[id + ':' + kind] || '') : '/photos/' + id + '/' + kind;

  /* ------------------------------------------------------------------ icône (dessinée, pour le logo dans l'appli) */
  const ICON_BG = {orange: '#ff7a1a', blue: '#4dabf7', green: '#51cf66', violet: '#9775fa', red: '#ff6b6b'};
  window.FONTE_ICON = (key, size) => {
    const c = document.createElement('canvas'); c.width = c.height = size;
    const g = c.getContext('2d'), u = size * 0.9 / 100, m = size / 2;
    g.fillStyle = ICON_BG[key] || ICON_BG.orange; g.fillRect(0, 0, size, size); g.fillStyle = '#0e161c';
    const rr = (x0, y0, x1, y1, r) => { g.beginPath(); g.roundRect(m + x0 * u, m + y0 * u, (x1 - x0) * u, (y1 - y0) * u, r * u); g.fill(); };
    rr(-30, -5, 30, 5, 3);
    for (const s of [-1, 1]) for (const [a, b, h, r] of [[24, 34, 20, 4], [34, 42, 13, 4], [42, 50, 5, 3]]) {
      const lo = Math.min(s * a, s * b), hi = Math.max(s * a, s * b); rr(lo, -h, hi, h, r);
    }
    return c.toDataURL('image/png');
  };

  /* ------------------------------------------------------------------ export (lien « Télécharger ») */
  function download(name, mime, text) {
    if (window.FonteApp && window.FonteApp.saveFile) { window.FonteApp.saveFile(name, mime, text); return; }
    const a = document.createElement('a'), u = URL.createObjectURL(new Blob([text], {type: mime}));
    a.href = u; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(u), 10000);
  }
  window.exportClick = (kind) => {
    if (!LOCAL) return true;
    (async () => {
      try {
        if (kind === 'photos') download('fonte-photos-' + today() + '.json', 'application/json', JSON.stringify(await exportPhotos()));
        else download('fonte-' + today() + '.json', 'application/json', JSON.stringify(exportData()));
      } catch (e) { alert('Export impossible : ' + e.message); }
    })();
    return false;
  };

  if (!LOCAL) return;

  /* ------------------------------------------------------------------ outils */
  class Bad extends Error {}
  class Http extends Error { constructor(status, msg) { super(msg); this.status = status; } }
  const KINDS = ['weight', 'reps', 'time', 'cardio'];
  const EX_FIELDS = ['name', 'grp', 'kind', 'sets', 'target_min', 'target_max', 'rest', 'focus', 'tip', 'green', 'per_side', 'assisted'];
  const ITEM_FIELDS = ['sets', 'target_min', 'target_max', 'rest'];   // réglages propres à un exercice dans un programme (lot 2A) : null = valeur de l'exercice
  const NUMRE = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/;
  const nowMs = () => Date.now();
  const truthy = v => Array.isArray(v) ? v.length > 0 : (v && typeof v === 'object') ? Object.keys(v).length > 0 : !!v;
  const isNone = v => v === null || v === undefined || v === '';
  const lt = (a, b) => a < b ? -1 : a > b ? 1 : 0;   // ordre binaire, comme SQLite

  function today() {
    const d = new Date();
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }
  function cleanInt(v, lo, hi, def = null) {
    if (isNone(v)) return def;
    let n;
    if (typeof v === 'number') n = v;
    else if (typeof v === 'boolean') n = v ? 1 : 0;
    else if (typeof v === 'string' && NUMRE.test(v.trim())) n = parseFloat(v);
    else throw new Bad(`Nombre invalide : '${v}'`);
    if (!isFinite(n)) throw new Bad(`Nombre invalide : '${v}'`);
    return Math.max(lo, Math.min(hi, Math.trunc(n)));
  }
  function cleanNum(v) {
    if (isNone(v)) return null;
    const s = (typeof v === 'string' ? v : typeof v === 'number' ? String(v) : '#').replace(',', '.').trim();
    if (!NUMRE.test(s)) throw new Bad(`Nombre invalide : '${v}'`);
    const n = parseFloat(s);
    if (!(n >= -10000 && n <= 100000)) throw new Bad('Valeur hors limites');
    return n;
  }
  function cleanDay(v) {
    const s = (v === null || v === undefined ? '' : String(v)).trim();
    if (!s) return today();
    const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
    if (m) {
      const d = new Date(+m[1], +m[2] - 1, +m[3]);
      if (d.getFullYear() === +m[1] && d.getMonth() === +m[2] - 1 && d.getDate() === +m[3]) return s;
    }
    throw new Bad('Date invalide (AAAA-MM-JJ)');
  }
  const str = (v, n) => String(v === undefined || v === null ? '' : v).trim().slice(0, n);
  function slugify(name) {
    const s = name.normalize('NFKD').replace(/[^\x00-\x7f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return s || 'exercice';
  }
  function uniqueSlug(w, name) {
    const base = slugify(name); let slug = base, n = 2;
    while (w.exercise.some(e => e.slug === slug)) slug = base + '-' + n++;
    return slug;
  }
  function nextId(w, t) { return w[t].reduce((m, r) => Math.max(m, r.id), 0) + 1; }
  function ins(w, t, row) { row.id = row.id === undefined ? nextId(w, t) : row.id; w[t].push(row); return row.id; }
  function cleanExercise(d) {
    const name = str(d.name, 120), grp = str(d.grp, 60), kind = d.kind;
    if (!name) throw new Bad('Le nom est obligatoire');
    if (!grp) throw new Bad('Le groupe musculaire est obligatoire');
    if (!KINDS.includes(kind)) throw new Bad('Type de saisie invalide');
    let tmin = cleanInt(d.target_min, 1, 1000), tmax = cleanInt(d.target_max, 1, 1000, tmin);
    if (tmin && tmax && tmax < tmin) [tmin, tmax] = [tmax, tmin];
    return {
      name, grp, kind, sets: cleanInt(d.sets, 1, 10, 3), target_min: tmin, target_max: tmax,
      rest: cleanInt(d.rest, 0, 600, 90), focus: str(d.focus, 200), tip: str(d.tip, 1000),
      green: truthy(d.green) ? 1 : 0, per_side: truthy(d.per_side) ? 1 : 0, assisted: truthy(d.assisted) && kind === 'weight' ? 1 : 0
    };
  }
  function insertExercise(w, d, slug) {
    return ins(w, 'exercise', {
      slug: slug || uniqueSlug(w, d.name), name: d.name, grp: d.grp, kind: d.kind, sets: d.sets,
      target_min: d.target_min, target_max: d.target_max, rest: d.rest, focus: d.focus, tip: d.tip,
      green: d.green, per_side: d.per_side, assisted: d.assisted,
      diagram: d.diagram ? JSON.stringify(d.diagram) : null, archived: +(d.archived || 0), updated_at: nowMs()
    });
  }
  function cleanItem(d) {   // réglages d'un exercice dans un programme ; null ou {} = valeurs de l'exercice
    if (d === null || d === undefined) d = {};
    if (typeof d !== 'object' || Array.isArray(d)) throw new Bad('Réglage invalide : objet attendu');
    let tmin = cleanInt(d.target_min, 1, 1000), tmax = cleanInt(d.target_max, 1, 1000, tmin);
    if (tmin === null) tmin = tmax;
    if (tmin && tmax && tmax < tmin) [tmin, tmax] = [tmax, tmin];
    return {sets: cleanInt(d.sets, 1, 10), target_min: tmin, target_max: tmax, rest: cleanInt(d.rest, 0, 600)};
  }
  function cleanSettings(v) {   // {"id d'exercice": réglages} -> Map(id -> réglages nettoyés)
    const out = new Map();
    if (v === null || v === undefined) return out;
    if (typeof v !== 'object' || Array.isArray(v)) throw new Bad('settings doit être un objet');
    for (const [k, d] of Object.entries(v)) out.set(cleanInt(k, 1, 1e9), cleanItem(d));
    return out;
  }
  function writeItems(w, wid, items, settings) {
    w.workout_item = w.workout_item.filter(i => i.workout_id !== wid);
    items.forEach((i, p) => {
      const s = settings.get(i) || {}, row = {workout_id: wid, exercise_id: i, position: p};
      for (const f of ITEM_FIELDS) row[f] = s[f] === undefined ? null : s[f];
      w.workout_item.push(row);
    });
  }
  function migrate(w) {   // données créées avant le lot 2A : ajoute les réglages vides ; vrai si quelque chose a changé
    let changed = false;
    for (const i of w.workout_item) for (const f of ITEM_FIELDS) if (!(f in i)) { i[f] = null; changed = true; }
    return changed;
  }
  const exRow = (w, r) => Object.assign({}, r, {diagram: r.diagram ? JSON.parse(r.diagram) : null, used: w.entry.some(e => e.exercise_id === r.id)});
  function workoutsList(w) {
    return [...w.workout].sort((a, b) => a.position - b.position || a.id - b.id).map(x => {
      const rows = w.workout_item.filter(i => i.workout_id === x.id).sort((a, b) => a.position - b.position), settings = {};
      for (const r of rows) if (ITEM_FIELDS.some(f => r[f] !== null && r[f] !== undefined)) settings[r.exercise_id] = Object.fromEntries(ITEM_FIELDS.map(f => [f, r[f] === undefined ? null : r[f]]));
      return {id: x.id, name: x.name, position: x.position, items: rows.map(i => i.exercise_id), settings};
    });
  }
  function sessionsList(w) {
    const rows = [...w.session].sort((a, b) => lt(a.day, b.day) || a.ts - b.ts || a.id - b.id);
    const ent = new Map();
    for (const e of [...w.entry].sort((a, b) => a.session_id - b.session_id || a.id - b.id)) {
      if (!ent.has(e.session_id)) ent.set(e.session_id, new Map());
      const m = ent.get(e.session_id);
      if (!m.has(e.exercise_id)) m.set(e.exercise_id, []);
      m.get(e.exercise_id).push([e.load, e.value]);
    }
    const eff = new Map(w.effort.map(f => [f.session_id + ':' + f.exercise_id, f.level]));
    return rows.map(r => ({
      id: r.id, day: r.day, ts: r.ts, workout_id: r.workout_id, workout_name: r.workout_name, notes: r.notes,
      entries: [...(ent.get(r.id) || new Map()).entries()].map(([k, v]) => ({exercise_id: k, sets: v, effort: eff.has(r.id + ':' + k) ? eff.get(r.id + ':' + k) : null}))
    }));
  }
  function writeEntries(w, sid, entries) {
    if (!Array.isArray(entries)) throw new Bad('entries doit être une liste');
    const known = new Set(w.exercise.map(e => e.id));
    let n = 0;
    for (const e of entries) {
      const exid = cleanInt(e.exercise_id, 1, 1e9);
      if (!known.has(exid)) throw new Bad('Exercice inconnu : ' + exid);
      const lv = cleanInt(e.effort, 1, 5);
      if (lv) {
        w.effort = w.effort.filter(f => !(f.session_id === sid && f.exercise_id === exid));
        w.effort.push({session_id: sid, exercise_id: exid, level: lv});
      }
      (e.sets || []).slice(0, 20).forEach((s, i) => {
        const load = cleanNum(s[0]), value = cleanNum(s[1]);
        if (load === null && value === null) return;
        ins(w, 'entry', {session_id: sid, exercise_id: exid, idx: i, load, value}); n++;
      });
    }
    return n;
  }
  function sessionPayload(w, d) {
    let wid = cleanInt(d.workout_id, 1, 1e9), wname = str(d.workout_name, 80);
    if (wid) {
      const x = w.workout.find(o => o.id === wid);
      if (!x) wid = null; else if (!wname) wname = x.name;
    }
    return [wid, wname || 'Séance libre', cleanDay(d.day), String(d.notes === undefined || d.notes === null ? '' : d.notes).slice(0, 4000)];
  }
  function dropSession(w, sid) {
    w.session = w.session.filter(s => s.id !== sid);
    w.entry = w.entry.filter(e => e.session_id !== sid);
    w.effort = w.effort.filter(f => f.session_id !== sid);
  }

  /* ------------------------------------------------------------------ stockage (IndexedDB) */
  let H = null;
  const open = () => new Promise((res, rej) => {
    const r = indexedDB.open('fonte', 1);
    r.onupgradeneeded = () => { r.result.createObjectStore('kv'); r.result.createObjectStore('blob'); };
    r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error);
  });
  const req = (store, mode, fn) => new Promise((res, rej) => {
    const t = H.transaction(store, mode), r = fn(t.objectStore(store));
    t.oncomplete = () => res(r && r.result); t.onerror = () => rej(t.error); t.onabort = () => rej(t.error);
  });
  const kvGet = k => req('kv', 'readonly', s => s.get(k));
  const kvPut = (k, v) => req('kv', 'readwrite', s => s.put(v, k));
  const blobPut = (k, b) => req('blob', 'readwrite', s => s.put(b, k));
  const blobGet = k => req('blob', 'readonly', s => s.get(k));
  const blobDel = k => req('blob', 'readwrite', s => s.delete(k));

  let db = null, queue = Promise.resolve();
  const EMPTY = () => ({exercise: [], workout: [], workout_item: [], session: [], entry: [], effort: [], bodyweight: [], photo: []});
  let LEGACY_CARDIO = {};

  function seedDb(s) {
    const w = EMPTY(), ids = {};
    for (const e of s.exercises) ids[e.slug] = insertExercise(w, e, e.slug);
    s.workouts.forEach(([name, slugs], pos) => {
      const wid = ins(w, 'workout', {name, position: pos});
      writeItems(w, wid, slugs.map(sl => ids[sl]), new Map());
    });
    return w;
  }
  const realFetch = window.fetch.bind(window);
  async function loadPhotoUrls() {
    for (const k of Object.keys(PHURL)) { URL.revokeObjectURL(PHURL[k]); delete PHURL[k]; }
    for (const p of db.photo) for (const kind of ['full', 'thumb']) {
      const b = await blobGet(p.id + ':' + kind); if (b) PHURL[p.id + ':' + kind] = URL.createObjectURL(b);
    }
  }
  const ready = (async () => {
    H = await open();
    try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch (e) { /* facultatif */ }
    const r = await realFetch('/static/seed.json'); if (!r.ok) throw new Error('seed.json introuvable');
    const seed = await r.json(); LEGACY_CARDIO = seed.legacy_cardio;
    db = await kvGet('db');
    if (!db) { db = seedDb(seed); await kvPut('db', db); }
    else if (migrate(db)) await kvPut('db', db);
    await loadPhotoUrls();
  })();

  /** Applique une modification sur une copie, ne la garde que si tout a réussi (comme une transaction SQL). */
  function mutate(fn) {
    const run = async () => { const w = structuredClone(db); const r = await fn(w); await kvPut('db', w); db = w; return r; };
    const p = queue.then(run, run); queue = p.catch(() => {}); return p;
  }

  /* ------------------------------------------------------------------ routes (reprennent server/app.py) */
  const ok = (body, status = 200) => ({status, body});
  const asBody = d => { if (!d || typeof d !== 'object' || Array.isArray(d)) throw new Bad('Corps JSON attendu'); return d; };
  const R = [];
  const route = (method, re, fn) => R.push([method, new RegExp('^' + re + '$'), fn]);

  function exportData() {
    const jeu = window.JEU ? window.JEU.exportState() : null;
    const out = {
      format: 'suivi-muscu', version: 1, exported_at: nowMs(),
      exercises: [...db.exercise].sort((a, b) => a.id - b.id).map(e => Object.assign({}, e)),
      workouts: workoutsList(db), sessions: sessionsList(db),
      bodyweight: [...db.bodyweight].sort((a, b) => a.id - b.id)
    };
    if (jeu) out.jeu = jeu;   // état du mini-jeu : absent tant qu'on n'a pas ouvert l'onglet Esprits
    const profil = window.PROFIL ? window.PROFIL.exportState() : null;
    if (profil) out.profil = profil;   // questionnaire de départ (réponses de santé comprises) : absent tant qu'il n'est pas validé
    return out;
  }
  const toDataUrl = b => new Promise((res, rej) => { const f = new FileReader(); f.onload = () => res(f.result); f.onerror = () => rej(f.error); f.readAsDataURL(b); });
  async function exportPhotos() {
    const out = [];
    for (const p of [...db.photo].sort((a, b) => lt(a.day, b.day) || a.ts - b.ts)) {
      out.push({id: p.id, day: p.day, ts: p.ts, note: p.note, full: await toDataUrl(await blobGet(p.id + ':full')), thumb: await toDataUrl(await blobGet(p.id + ':thumb'))});
    }
    return {format: 'fonte-photos', version: 1, exported_at: nowMs(), photos: out};
  }

  route('GET', '/api/state', async () => ok({
    exercises: [...db.exercise].sort((a, b) => lt(a.grp, b.grp) || lt(a.name, b.name)).map(r => exRow(db, r)),
    workouts: workoutsList(db), sessions: sessionsList(db),
    bodyweight: [...db.bodyweight].sort((a, b) => lt(a.day, b.day) || a.ts - b.ts)
  }));

  route('POST', '/api/exercises', async (b) => mutate(w => { const d = cleanExercise(asBody(b())); const id = insertExercise(w, d); return ok(exRow(w, w.exercise.find(e => e.id === id)), 201); }));
  route('PUT', '/api/exercises/(\\d+)', async (b, id) => mutate(w => {
    const d = cleanExercise(asBody(b())), e = w.exercise.find(x => x.id === +id);
    if (!e) return ok({error: 'Exercice introuvable'}, 404);
    for (const f of EX_FIELDS) e[f] = d[f];
    e.updated_at = nowMs(); return ok(exRow(w, e));
  }));
  route('POST', '/api/exercises/(\\d+)/archive', async (b, id) => mutate(w => {
    const flag = truthy(asBody(b()).archived) ? 1 : 0, e = w.exercise.find(x => x.id === +id);
    if (!e) return ok({error: 'Exercice introuvable'}, 404);
    e.archived = flag; e.updated_at = nowMs();
    if (flag) w.workout_item = w.workout_item.filter(i => i.exercise_id !== +id);
    return ok({ok: true});
  }));
  route('DELETE', '/api/exercises/(\\d+)', async (b, id) => mutate(w => {
    if (w.entry.some(e => e.exercise_id === +id)) return ok({error: 'Exercice déjà utilisé dans des séances : archive-le plutôt.'}, 409);
    w.workout_item = w.workout_item.filter(i => i.exercise_id !== +id);
    w.effort = w.effort.filter(f => f.exercise_id !== +id);
    w.exercise = w.exercise.filter(e => e.id !== +id);
    return ok({ok: true});
  }));

  route('POST', '/api/workouts', async (b) => mutate(w => {
    const name = str(asBody(b()).name, 80); if (!name) throw new Bad('Nom obligatoire');
    const pos = w.workout.reduce((m, x) => Math.max(m, x.position), -1) + 1;
    return ok({id: ins(w, 'workout', {name, position: pos})}, 201);
  }));
  route('PUT', '/api/workouts/(\\d+)', async (b, id) => mutate(w => {
    const d = asBody(b()), name = str(d.name, 80), items = d.items === undefined ? [] : d.items;
    if (!name) throw new Bad('Nom obligatoire');
    if (!Array.isArray(items)) throw new Bad('items doit être une liste');
    const active = new Set(w.exercise.filter(e => !e.archived).map(e => e.id)), seen = [];
    for (let i of items) {
      i = cleanInt(i, 1, 1e9);
      if (!active.has(i)) throw new Bad('Exercice inconnu ou archivé : ' + i);
      if (!seen.includes(i)) seen.push(i);
    }
    let settings;
    if ('settings' in d) settings = cleanSettings(d.settings);   // réglages envoyés : ils remplacent les anciens
    else settings = new Map(w.workout_item.filter(i => i.workout_id === +id).map(i => [i.exercise_id, i]));   // pas envoyés : on garde ceux des exercices restés
    const x = w.workout.find(o => o.id === +id); if (!x) return ok({error: 'Programme introuvable'}, 404);
    x.name = name;
    writeItems(w, +id, seen, settings);
    return ok({ok: true});
  }));
  route('POST', '/api/workouts/order', async (b) => mutate(w => {
    const ids = asBody(b()).ids === undefined ? [] : asBody(b()).ids;
    ids.forEach((i, p) => { const x = w.workout.find(o => o.id === cleanInt(i, 1, 1e9)); if (x) x.position = p; });
    return ok({ok: true});
  }));
  route('DELETE', '/api/workouts/(\\d+)', async (b, id) => mutate(w => {
    w.workout = w.workout.filter(x => x.id !== +id);
    w.workout_item = w.workout_item.filter(i => i.workout_id !== +id);
    w.session.forEach(s => { if (s.workout_id === +id) s.workout_id = null; });
    return ok({ok: true});
  }));

  route('POST', '/api/sessions', async (b) => mutate(w => {
    const d = asBody(b()), [wid, wname, day, notes] = sessionPayload(w, d);
    const sid = ins(w, 'session', {day, ts: nowMs(), workout_id: wid, workout_name: wname, notes});
    if (!writeEntries(w, sid, d.entries)) throw new Bad('Aucune série saisie');
    return ok({id: sid}, 201);
  }));
  route('PUT', '/api/sessions/(\\d+)', async (b, id) => mutate(w => {
    const d = asBody(b()), [wid, wname, day, notes] = sessionPayload(w, d), s = w.session.find(x => x.id === +id);
    if (!s) return ok({error: 'Séance introuvable'}, 404);
    Object.assign(s, {day, workout_id: wid, workout_name: wname, notes});
    w.entry = w.entry.filter(e => e.session_id !== +id); w.effort = w.effort.filter(f => f.session_id !== +id);
    if (!writeEntries(w, +id, d.entries)) throw new Bad('Aucune série saisie');
    return ok({ok: true});
  }));
  route('DELETE', '/api/sessions/(\\d+)', async (b, id) => mutate(w => { dropSession(w, +id); return ok({ok: true}); }));

  route('POST', '/api/bodyweight', async (b) => mutate(w => {
    const d = asBody(b()), kg = cleanNum(d.kg);
    if (!kg || !(kg >= 20 && kg <= 400)) throw new Bad('Poids invalide');
    ins(w, 'bodyweight', {day: cleanDay(d.day), ts: nowMs(), kg});
    return ok({ok: true}, 201);
  }));
  route('DELETE', '/api/bodyweight/(\\d+)', async (b, id) => mutate(w => { w.bodyweight = w.bodyweight.filter(x => x.id !== +id); return ok({ok: true}); }));

  /* photos : les fichiers vont dans le magasin 'blob' d'IndexedDB */
  const isJpeg = async b => b.size > 500 && new Uint8Array(await b.slice(0, 3).arrayBuffer()).join() === '255,216,255';
  route('GET', '/api/photos', async () => ok([...db.photo].sort((a, b) => lt(a.day, b.day) || a.ts - b.ts).map(p => ({id: p.id, day: p.day, ts: p.ts, note: p.note}))));
  route('POST', '/api/photos', async (b, form) => {
    const img = form && form.get('img'), th = form && form.get('thumb');
    if (!img || !th || typeof img === 'string' || typeof th === 'string') throw new Bad('Photo manquante');
    if (img.size > 6 * 1024 * 1024 || th.size > 1024 * 1024) throw new Bad('Photo trop lourde');
    if (!(await isJpeg(img) && await isJpeg(th))) throw new Bad('Format JPEG attendu');
    const day = cleanDay(form.get('day')), note = String(form.get('note') || '').trim().slice(0, 200);
    let pid;
    const r = await mutate(w => { pid = ins(w, 'photo', {day, ts: nowMs(), note}); return ok({id: pid}, 201); });
    await blobPut(pid + ':full', img); await blobPut(pid + ':thumb', th);
    PHURL[pid + ':full'] = URL.createObjectURL(img); PHURL[pid + ':thumb'] = URL.createObjectURL(th);
    return r;
  });
  route('DELETE', '/api/photos/(\\d+)', async (b, id) => {
    const r = await mutate(w => { w.photo = w.photo.filter(p => p.id !== +id); return ok({ok: true}); });
    for (const kind of ['full', 'thumb']) { await blobDel(id + ':' + kind); if (PHURL[id + ':' + kind]) { URL.revokeObjectURL(PHURL[id + ':' + kind]); delete PHURL[id + ':' + kind]; } }
    return r;
  });

  route('GET', '/api/export', async () => ok(exportData()));

  function frToIso(s) {
    const m = /^\s*(\d{1,2})\/(\d{1,2})\/(\d{4})\s*$/.exec(String(s === undefined || s === null ? '' : s));
    if (!m) throw new Bad(`Date de l'ancienne appli illisible : '${s}'`);
    const d = new Date(+m[3], +m[2] - 1, +m[1]);
    if (d.getFullYear() !== +m[3] || d.getMonth() !== +m[2] - 1 || d.getDate() !== +m[1]) throw new Bad(`Date de l'ancienne appli illisible : '${s}'`);
    return d.getFullYear() + '-' + String(m[2]).padStart(2, '0') + '-' + String(m[1]).padStart(2, '0');
  }
  function importLegacy(w, o) {
    const slug2id = new Map(w.exercise.map(e => [e.slug, e.id])), wname2id = new Map(w.workout.map(x => [x.name, x.id]));
    let added = 0, skipped = 0;
    for (const s of o.L || []) {
      const ts = parseInt(s.ts || 0, 10) || 0;
      if (ts && w.session.some(x => x.ts === ts)) { skipped++; continue; }
      const wname = ('Séance ' + (s.s === undefined || s.s === null ? '' : s.s)).trim(), entries = [];
      for (const [oldId, sets] of Object.entries(s.x || {})) {
        if (!slug2id.has(oldId)) throw new Bad("Exercice de l'ancienne appli inconnu : " + oldId);
        entries.push({exercise_id: slug2id.get(oldId), sets});
      }
      const cardio = s.c || [];
      if (cardio.length === 2 && cardio[0]) {
        const slug = LEGACY_CARDIO[cardio[1]];
        if (slug && slug2id.has(slug)) entries.push({exercise_id: slug2id.get(slug), sets: [[null, cardio[0]]]});
      }
      const sid = ins(w, 'session', {day: frToIso(s.d), ts: ts || nowMs(), workout_id: wname2id.has(wname) ? wname2id.get(wname) : null, workout_name: wname, notes: String(s.n || '')});
      writeEntries(w, sid, entries); added++;
    }
    let bw = 0;
    for (const [d, kg] of o.W || []) {
      const day = frToIso(d);
      if (!w.bodyweight.some(x => x.day === day && x.kg === kg)) { ins(w, 'bodyweight', {day, ts: nowMs(), kg: parseFloat(kg)}); bw++; }
    }
    return {mode: 'ancienne appli (ajout)', sessions: added, doublons_ignores: skipped, pesees: bw};
  }
  const need = (o, keys) => { for (const k of keys) if (!(k in o)) throw new Error("'" + k + "'"); };
  function importFull(w, o) {
    for (const t of ['effort', 'entry', 'session', 'workout_item', 'workout', 'bodyweight', 'exercise']) w[t] = [];
    for (const e of o.exercises || []) {
      need(e, ['id', 'slug', 'name', 'grp', 'kind', 'sets', 'target_min', 'target_max', 'rest', 'focus', 'tip', 'green', 'per_side', 'assisted', 'diagram', 'archived', 'updated_at']);
      w.exercise.push({id: e.id, slug: e.slug, name: e.name, grp: e.grp, kind: e.kind, sets: e.sets, target_min: e.target_min, target_max: e.target_max, rest: e.rest, focus: e.focus, tip: e.tip, green: e.green, per_side: e.per_side, assisted: e.assisted, diagram: e.diagram, archived: e.archived, updated_at: e.updated_at});
    }
    for (const x of o.workouts || []) {
      need(x, ['id', 'name']);
      w.workout.push({id: x.id, name: x.name, position: x.position === undefined ? 0 : x.position});
      writeItems(w, x.id, x.items || [], cleanSettings(x.settings));   // export d'avant le lot 2A : pas de « settings »
    }
    for (const s of o.sessions || []) {
      need(s, ['id', 'day', 'ts']);
      w.session.push({id: s.id, day: s.day, ts: s.ts, workout_id: s.workout_id === undefined ? null : s.workout_id, workout_name: s.workout_name || '', notes: s.notes || ''});
      writeEntries(w, s.id, s.entries || []);
    }
    for (const x of o.bodyweight || []) { need(x, ['id', 'day', 'ts', 'kg']); w.bodyweight.push({id: x.id, day: x.day, ts: x.ts, kg: x.kg}); }
    if (o.jeu && window.JEU) window.JEU.importState(o.jeu);
    if (o.profil && window.PROFIL) window.PROFIL.importState(o.profil);   // export sans profil (anciennes versions) : profil actuel inchangé
    return {mode: 'sauvegarde complète (remplacement)', exercices: (o.exercises || []).length, sessions: (o.sessions || []).length};
  }
  async function importPhotos(o) {
    let added = 0, skipped = 0;
    for (const p of o.photos || []) {
      if (db.photo.some(x => x.ts === p.ts && x.day === p.day)) { skipped++; continue; }
      const full = await (await realFetch(p.full)).blob(), thumb = await (await realFetch(p.thumb)).blob();
      let pid;
      await mutate(w => { pid = ins(w, 'photo', {day: cleanDay(p.day), ts: p.ts, note: String(p.note || '').slice(0, 200)}); });
      await blobPut(pid + ':full', full); await blobPut(pid + ':thumb', thumb);
      PHURL[pid + ':full'] = URL.createObjectURL(full); PHURL[pid + ':thumb'] = URL.createObjectURL(thumb); added++;
    }
    return {mode: 'photos (ajout)', photos: added, doublons_ignores: skipped};
  }
  route('POST', '/api/import', async (b) => {
    const o = asBody(b());
    if (o.format === 'fonte-photos') return ok(await importPhotos(o));
    return mutate(w => {
      try {
        if (o.format === 'suivi-muscu') return ok(importFull(w, o));
        if (Array.isArray(o.L)) return ok(importLegacy(w, o));
      } catch (e) {
        if (e instanceof Bad) throw e;
        throw new Bad('Import refusé, base inchangée : ' + e.message);
      }
      throw new Bad("Format non reconnu : ni export de ce service, ni export de l'ancienne appli");
    });
  });

  /* ------------------------------------------------------------------ interception de fetch */
  window.fetch = async function (input, init) {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (url.origin !== location.origin || !(url.pathname.startsWith('/api/') || url.pathname.startsWith('/photos/'))) return realFetch(input, init);
    const method = ((init && init.method) || (typeof input !== 'string' && input.method) || 'GET').toUpperCase();
    const rawBody = init && init.body;
    const send = (status, body) => new Response(JSON.stringify(body), {status, headers: {'Content-Type': 'application/json'}});
    await ready;
    for (const [m, re, fn] of R) {
      const mt = m === method && re.exec(url.pathname);
      if (!mt) continue;
      try {
        const form = rawBody instanceof FormData ? rawBody : null;
        const body = () => { if (typeof rawBody !== 'string') return null; try { return JSON.parse(rawBody); } catch (e) { return null; } };
        const r = await fn(body, ...mt.slice(1), form);
        return send(r.status, r.body);
      } catch (e) {
        if (e instanceof Bad) return send(400, {error: e.message});
        console.error(e); return send(500, {error: 'Erreur interne : ' + e.message});
      }
    }
    return send(404, {error: 'Introuvable'});
  };
})();
