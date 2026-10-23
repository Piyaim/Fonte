// SPDX-License-Identifier: AGPL-3.0-or-later
// Données d'essai de la maquette du lot 2 (lot2/lot2.html) : 16 séances du 21/09 au 04/11/2026 (lundi, mercredi, vendredi, séances A et B),
// charges au pas du matériel et double progression, deux séances saisies après coup (9 et 16 octobre, sans durée), 6 pesées.
// Fonction appelée par la page (pg.evaluate) ; plus = true : 4 séances la semaine du 2 novembre.
async (plus) => {
  const EXS = {
    pc: {n: 'Presse à cuisses', k: 'weight', s: 3, r: [10, 12], kg: 40, pas: 2.5, g: 'Jambes'}, di: {n: 'Développé incliné haltères', k: 'weight', s: 3, r: [10, 12], kg: 14, pas: 2, d0: 1, g: 'Pectoraux'},
    tv: {n: 'Tirage vertical', k: 'weight', s: 3, r: [10, 12], kg: 35, pas: 2.5, g: 'Dos'}, rdl: {n: 'Soulevé de terre roumain', k: 'weight', s: 3, r: [8, 10], kg: 16, pas: 2, d0: 1, g: 'Jambes'},
    pl: {n: 'Planche', k: 'time', s: 3, sec: 30, g: 'Abdos et gainage'}, velo: {n: 'Vélo', k: 'cardio', min: 15, niv: 6, g: 'Cardio'},
    gs: {n: 'Goblet squat', k: 'weight', s: 3, r: [10, 12], kg: 16, pas: 2, d0: 1, g: 'Jambes'}, de: {n: 'Développé épaules machine', k: 'weight', s: 3, r: [10, 12], kg: 25, pas: 2.5, g: 'Épaules'},
    rs: {n: 'Rowing assis poulie', k: 'weight', s: 3, r: [10, 12], kg: 35, pas: 2.5, d0: 1, g: 'Dos'}, lc: {n: 'Leg curl assis', k: 'weight', s: 3, r: [10, 12], kg: 25, pas: 2.5, g: 'Jambes'},
    db: {n: 'Dead bug', k: 'reps', s: 3, reps: 8, g: 'Abdos et gainage'}, tapis: {n: 'Tapis incliné', k: 'cardio', min: 15, niv: 5, g: 'Cardio'}};
  const id = {};
  for (const k in EXS) { const e = EXS[k]; id[k] = (await api('POST', '/api/exercises', {name: e.n, grp: e.g, kind: e.k, sets: 3, target_min: e.r ? e.r[0] : 10, target_max: e.r ? e.r[1] : 12, rest: 90})).id; }
  const WOD = {A: ['pc', 'di', 'tv', 'rdl', 'pl', 'velo'], B: ['gs', 'de', 'rs', 'lc', 'db', 'tapis']};
  let DAYS = ['2026-09-21','2026-09-23','2026-09-25','2026-09-28','2026-09-30','2026-10-02','2026-10-05','2026-10-07','2026-10-09','2026-10-12','2026-10-16','2026-10-19','2026-10-21','2026-10-23','2026-11-02','2026-11-04'];
  if (plus) DAYS = [...DAYS.slice(0, 15), '2026-11-03', '2026-11-04', '2026-11-04'];
  const ST = {};
  for (let i = 0; i < DAYS.length; i++) {
    const day = DAYS[i], w = i % 2 ? 'B' : 'A', n = Math.floor(i / 2), fc = [3, 3, 2, 3, 4, 3];
    const entries = WOD[w].map((k, j) => { const e = EXS[k]; let sets;
      if (e.k === 'weight') { const s = ST[k] = ST[k] || {kg: e.kg, reps: e.r[0] + (e.d0 || 0)}, tired = (n + (e.d0 || 0)) % 3 === 1 && s.reps > e.r[0];
        sets = Array.from({length: e.s}, (_, q) => [s.kg, q === e.s - 1 && tired ? s.reps - 1 : s.reps]);
        if (sets.every(x => x[1] >= e.r[1])) { s.kg += e.pas; s.reps = e.r[0]; } else s.reps = Math.min(e.r[1], s.reps + 1); }
      else if (e.k === 'time') sets = Array.from({length: e.s}, () => [null, e.sec + 5 * Math.floor(n / 3)]);
      else if (e.k === 'reps') sets = Array.from({length: e.s}, () => [null, e.reps + Math.floor(n / 3)]);
      else sets = [[e.niv + Math.floor(n / 3), e.min + 5 * Math.floor(n / 4)]];
      return {exercise_id: id[k], sets, effort: e.k === 'cardio' ? null : fc[(i + j) % 6]}; });
    const live = !['2026-10-09', '2026-10-16'].includes(day), [y, m, d] = day.split('-').map(Number), t0 = new Date(y, m - 1, d, 18, 0).getTime();
    await api('POST', '/api/sessions', {day, workout_name: 'Séance ' + w, notes: i === 13 ? 'Épaule un peu raide au début, ça passe après l’échauffement.' : '', entries,
      start_ts: live ? t0 : null, end_ts: live ? t0 + (46 + (i * 7) % 13) * 60000 : null});
  }
  for (const [day, kg] of [['2026-09-21', 75.4], ['2026-09-28', 75.1], ['2026-10-05', 75.3], ['2026-10-12', 74.9], ['2026-10-19', 74.8], ['2026-11-02', 74.9]]) await api('POST', '/api/bodyweight', {day, kg});
  await load(); R(); }
