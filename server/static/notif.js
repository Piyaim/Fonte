// SPDX-License-Identifier: AGPL-3.0-or-later
/* Notifications (version 0.5.0) : seulement dans l'appli Android, où la coque Java (FonteApp) les programme et les envoie,
   même appli fermée. Rien ne passe par le réseau.
   - Réglages dans localStorage, clé muscu-notif (version 1). Ils restent sur le téléphone : ils ne sont pas dans l'export.
   - La page calcule le plan des 14 prochains jours (heure et texte de chaque notification) et le confie à la coque à chaque
     changement. Tout ce qui fait changer le plan (séance enregistrée, proposition acceptée, réglage) passe par la page.
   - Garde-fous : une notification par jour au plus (la fin du repos à part), rien pendant les heures calmes, jamais de relance
     (après 7 jours sans séance, un seul « Bon retour », puis plus rien jusqu'à la prochaine séance), une seule fois par
     événement, aucun mot de reproche (voir tests/notifications.py), rien sur les Esprits ni les jetons. La coque vérifie à nouveau les heures
     calmes, le plafond et les événements déjà envoyés au moment d'envoyer. */
(function () {
  const KEY = 'muscu-notif', A = () => window.APPX, HORIZON = 14, PAUSE = 7;
  const DAY = 864e5;
  const dn = iso => { const [y, m, d] = iso.split('-').map(Number); return Date.UTC(y, m - 1, d) / DAY; };
  const addD = (iso, k) => new Date((dn(iso) + k) * DAY).toISOString().slice(0, 10);
  const dow = iso => (new Date(dn(iso) * DAY).getUTCDay() + 6) % 7;   // lundi = 0
  const isoOf = ms => { const d = new Date(ms); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
  const mins = hm => { const m = /^(\d\d):(\d\d)$/.exec(hm || ''); return m ? +m[1] * 60 + +m[2] : null; };
  const atOf = (iso, hm) => { const [y, mo, d] = iso.split('-').map(Number), m = mins(hm); return new Date(y, mo - 1, d, Math.floor(m / 60), m % 60).getTime(); };
  const quiet = (m, c) => { const f = mins(c.from), t = mins(c.to); if (f == null || t == null || f === t) return false; return f < t ? m >= f && m < t : m >= f || m < t; };
  const DOW = {lun: 0, mar: 1, mer: 2, jeu: 3, ven: 4, sam: 5, dim: 6};
  const JOURS = ['lundi', 'mardi', 'mercredi', 'jeudi', 'vendredi', 'samedi', 'dimanche'];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const pl = (n, w) => `${n} ${w}${n > 1 ? 's' : ''}`;

  /* ---------------------------------------------------------------- coque Android */
  function app() { try { return window.FonteApp && typeof window.FonteApp.notifStatus === 'function' ? window.FonteApp : null; } catch (e) { return null; } }
  let ST = null;
  function status() {   // {sdk, perm: granted | ask | settings, exact, exactNeeded, channels, sent: [clés déjà envoyées]}
    if (!ST) { const f = app(); try { ST = f ? JSON.parse(f.notifStatus()) : null; } catch (e) { ST = null; } }
    return ST;
  }

  /* ---------------------------------------------------------------- réglages */
  function defaults() {
    const o = window.PROFIL && PROFIL.exportState ? PROFIL.exportState() : null;
    const j = o && o.answers && Array.isArray(o.answers.jours) ? [...new Set(o.answers.jours.map(x => DOW[x]).filter(x => x !== undefined))].sort() : [];
    return {version: 1, on: true, rappel: {on: true, days: j.length ? j : [0, 3], time: '18:00'}, repos: {on: false},
      etapes: {on: true}, retour: {on: true}, bilan: {on: true}, calme: {from: '21:00', to: '08:00'}, since: A().today()};
  }
  function saved() { try { const o = JSON.parse(localStorage.getItem(KEY) || 'null'); return o && o.version === 1 ? o : null; } catch (e) { return null; } }
  function settings() { return saved() || defaults(); }
  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }

  /* ---------------------------------------------------------------- plan */
  const seance = w => /^Séance /.test(w.name) ? w.name : 'Séance ' + w.name;
  const nEx = w => w.items.filter(i => A().EX()[i] && !A().EX()[i].archived).length;
  function workoutFor(d) {   // la séance prévue ce jour-là (placement du programme), sinon celle qui suit la dernière faite
    const sch = window.PROFIL && PROFIL.schedule ? PROFIL.schedule(d) : null;
    return (sch && sch.today && A().WO().find(w => w.id === sch.today.wid)) || A().nextWorkout();
  }
  function rappel(d) {
    const w = workoutFor(d);
    if (!w) return {ch: 'rappels', title: 'C’est l’heure de ta séance', text: 'Touche pour la composer.'};
    const n = nEx(w);
    return {ch: 'rappels', title: `${seance(w)} prête : ${pl(n, 'exercice')}`, text: 'Touche pour commencer.'};
  }
  function etape(d, used) {   // passage de phase ou semaine légère du cycle (pas celle d'après une pause : la pause a son propre message)
    if (!window.PROFIL || !PROFIL.offers) return null;
    const o = PROFIL.exportState(), p = o && o.program;
    for (const f of PROFIL.offers(d)) {
      if (f.k === 'phase' && p) {
        const key = `phase:${f.to}:${p.start}`; if (used.has(key)) continue;
        if (f.to === 2) return {key, ch: 'programme', title: 'Phase 2 prête', text: 'Ouvre Fonte pour voir ce qui change.'};
        const c = PROFIL._ && PROFIL._.planC ? PROFIL._.planC(o, 3) : null;
        return {key, ch: 'programme', title: 'Phase 3 prête', text: c ? 'Une 3e séance s’ajoute : puissance et cardio.' : 'Chaque séance prend un rôle : force, volume ou puissance.'};
      }
      if (f.k === 'allegee' && f.why === 'cycle') {
        const key = `allegee:${PROFIL.cycleKey()}`; if (used.has(key)) continue;
        return {key, ch: 'programme', title: 'Semaine légère prête', text: 'Charges à −20 % pendant 7 jours, si tu veux.'};
      }
    }
    return null;
  }
  function retour(d, last) {
    const next = window.PROFIL && PROFIL.offers ? PROFIL.offers(addD(d, 1)) : [], w = A().nextWorkout();
    const text = next.some(f => f.k === 'allegee') ? 'Une semaine légère t’attend, si tu veux.'
      : w ? `Ta ${seance(w).replace(/^Séance/, 'séance')} est prête, à ton rythme.` : 'Ta prochaine séance t’attend, à ton rythme.';
    return {key: 'retour:' + last, ch: 'programme', title: 'Bon retour quand tu veux', text};
  }
  function bilan(d) {   // seulement ce qui a été fait ; rien si aucune séance cette semaine
    const mon = addD(d, -6), wk = A().SESS().filter(s => s.day >= mon && s.day <= d);
    if (!wk.length) return null;
    const EX = A().EX(), z = new Set(), pr = A().computePRs().bySession;
    let sets = 0, rec = 0;
    wk.forEach(s => { rec += (pr[s.id] || []).length; s.entries.forEach(en => { sets += (en.sets || []).length; const e = EX[en.exercise_id]; if (e) A().zonesOf(e).p.forEach(k => z.add(k)); }); });
    const parts = [sets && pl(sets, 'série'), z.size && `${z.size} zone${z.size > 1 ? 's' : ''} travaillée${z.size > 1 ? 's' : ''}`, rec && pl(rec, 'record')].filter(Boolean);
    return {ch: 'programme', title: `Ta semaine : ${pl(wk.length, 'séance')}`, text: parts.join(' · ') || 'Bravo pour ta semaine.'};
  }
  /* une notification par jour au plus, dans l'ordre : rappel de séance, étape du programme (sinon reportée au jour libre suivant),
     bon retour, bilan du dimanche ; toutes à l'heure du rappel, jamais pendant les heures calmes */
  function plan(now, s, sent) {
    s = s || settings(); now = now || Date.now();
    if (!s.on || quiet(mins(s.rappel.time), s.calme)) return [];
    const t0 = isoOf(now), days = A().SESS().map(x => x.day).filter(x => x <= t0).sort(), last = days[days.length - 1] || null;
    const ref = last || s.since || t0, used = new Set(sent || []), out = [];
    for (let k = 0; k < HORIZON; k++) {
      const d = addD(t0, k), at = atOf(d, s.rappel.time), gap = dn(d) - dn(ref);
      if (at <= now) continue;
      let c = null;
      if (gap < PAUSE) {
        if (s.rappel.on && s.rappel.days.includes(dow(d)) && !A().SESS().some(x => x.day === d)) c = Object.assign({key: 'rappel:' + d}, rappel(d));
        if (!c && s.etapes.on) c = etape(d, used);
        if (!c && s.bilan.on && dow(d) === 6) { const b = bilan(d); if (b) c = Object.assign({key: 'bilan:' + d}, b); }
      } else if (gap === PAUSE && last && s.retour.on && !used.has('retour:' + last)) c = retour(d, last);
      if (c) { c.at = at; out.push(c); used.add(c.key); }
    }
    return out;
  }
  // format confié à la coque : une ligne d'en-tête (heures calmes), puis une ligne par notification, champs séparés par des tabulations
  const clean = v => String(v).replace(/[\t\r\n]+/g, ' ');
  function serialize(s, items) { return [['calme', s.calme.from, s.calme.to], ...items.map(i => [i.at, i.key, i.ch, i.title, i.text])].map(r => r.map(clean).join('\t')).join('\n'); }

  let LAST = null, TMR = null, ASKED = false;
  function syncNow() {
    TMR = null;
    const f = app(); if (!f) return;
    if (!ASKED && window.PROFIL && !PROFIL.imposed()) { ASKED = true; try { f.notifAskOnce(); } catch (e) {} }   // une fois le questionnaire rempli
    const st = status();
    let txt = '';
    if (st && st.perm === 'granted') {
      if (!saved()) save(defaults());   // l'activation fixe la date de départ et les jours par défaut
      const s = settings(); txt = s.on ? serialize(s, plan(Date.now(), s, st.sent)) : '';
      if (!s.on || !s.repos.on) try { f.restCancel(); } catch (e) {}
    }
    if (txt !== LAST) { LAST = txt; try { f.notifPlan(txt); } catch (e) {} }
  }
  function sync() { if (app() && !TMR) TMR = setTimeout(syncNow, 300); }
  function onStatus() { ST = null; if (A() && A().view() === 'notifications') A().R(); sync(); }

  /* fin du repos : appelée par le minuteur ; la coque l'envoie seulement si l'appli n'est pas à l'écran */
  function rest(sec, next) {
    const f = app(), st = status(), s = settings();
    if (!f) return;
    try {
      if (!st || st.perm !== 'granted' || !s.on || !s.repos.on || !sec) f.restCancel();
      else f.restStart(sec, 'Repos terminé', next || 'C’est reparti quand tu veux.');
    } catch (e) {}
  }

  /* ---------------------------------------------------------------- page */
  const SW = (on, lab, fn, dis) => `<button class="sw2" role="switch" aria-checked="${on}" aria-label="${esc(lab)}" onclick="${fn}"${dis ? ' disabled' : ''}></button>`;
  const det = inner => `<details class="det"><summary>Détails</summary>${inner}</details>`;
  function card(k, t, phrase, on, dis, extra, more, ch) {
    const st = status();
    return `<section class="card${dis ? ' off' : ''}" data-n="${k}"><div class="ntg"><div><h2>${t}</h2><p class="m">${phrase}</p></div>${SW(on, t, `NOTIF.tog('${k}')`, dis)}</div>${extra || ''}`
      + (ch && st && st.channels ? `<button class="sm nfull" onclick="NOTIF.channel('${ch}')"${dis ? ' disabled' : ''}>Son et vibration</button>` : '') + (more ? det(more) : '') + '</section>';
  }
  function view() {
    const f = app();
    if (!f) return '<section class="card"><h2>Notifications</h2><p class="m">Disponibles seulement dans l’appli Android.</p>'
      + det('<p class="m">Un navigateur ne peut pas envoyer de rappel fiable quand Fonte est fermée. L’appli Android le fait sans réseau.</p>') + '</section>';
    ST = null;
    const st = status() || {}, s = settings(), ok = st.perm === 'granted', off = !ok || !s.on, err = quiet(mins(s.rappel.time), s.calme);
    let h = '';
    if (!ok) h += '<section class="card nwarn"><h2>Notifications bloquées</h2><p class="m">Android les bloque pour Fonte.</p><button class="go" onclick="NOTIF.enable()">Activer les notifications</button></section>';
    h += card('on', 'Notifications', 'Rappels et messages de Fonte.', s.on, !ok, '', '<p class="m">Une notification par jour au plus, hors fin du repos.</p><p class="m">Jamais de relance si tu ne réagis pas.</p>'
      + '<p class="m">Aucune notification sur les Esprits ni les jetons.</p><p class="m">Tout reste sur ton téléphone, sans réseau.</p>');
    const days = '<div class="days">' + JOURS.map((j, i) => { const on = s.rappel.days.includes(i); return `<button class="chip${on ? ' on' : ''}" aria-label="${j}" aria-pressed="${on}" onclick="NOTIF.day(${i})"${off ? ' disabled' : ''}>${j[0].toUpperCase()}</button>`; }).join('') + '</div>';
    h += card('rappel', 'Rappel de séance', 'Le jour prévu, à l’heure choisie.', s.rappel.on, off,
      days + `<div class="trow"><span>Heure</span><input type="time" value="${esc(s.rappel.time)}" aria-label="Heure du rappel" onchange="NOTIF.time(this.value)"${off ? ' disabled' : ''}></div>`
      + (err ? '<p class="qerr">Cette heure tombe dans les heures calmes.</p>' : ''),
      '<p class="m">Exemple : « Séance B prête : 6 exercices ».</p><p class="m">Après 7 jours sans séance, les rappels s’arrêtent jusqu’à ta prochaine séance.</p>', 'rappels');
    const noExact = s.repos.on && st.exactNeeded && !st.exact;
    h += card('repos', 'Fin du repos', 'Te prévient même écran verrouillé.', s.repos.on, off,
      noExact && !off ? '<p class="qmiss">Autorisation « Alarmes et rappels » refusée : la fin du repos reste dans l’appli.</p><button class="sm nfull" onclick="NOTIF.exact()">Autoriser les alarmes</button>' : '',
      '<p class="m">Demande l’autorisation « Alarmes et rappels » pour sonner à la seconde près.</p><p class="m">Sans elle, le minuteur de l’appli marche comme avant.</p><p class="m">Seule notification permise pendant les heures calmes.</p>', 'repos');
    h += card('etapes', 'Étapes du programme', 'Phase suivante ou semaine légère prête.', s.etapes.on, off, '', '<p class="m">Un seul message par étape. Rien ne change sans « Accepter » dans l’appli.</p>', 'programme');
    h += card('retour', 'Bon retour', 'Un seul message après 7 jours sans séance.', s.retour.on, off, '', '<p class="m">« Bon retour quand tu veux ». Un seul par pause, puis plus rien.</p>', 'programme');
    h += card('bilan', 'Bilan du dimanche', 'Ce que tu as fait dans la semaine.', s.bilan.on, off, '', '<p class="m">Envoyé à l’heure du rappel. Rien si tu n’as fait aucune séance.</p>', 'programme');
    h += `<section class="card${off ? ' off' : ''}"><h2>Heures calmes</h2><p class="m">Rien n’est envoyé pendant ces heures.</p><div class="trow"><span>De</span>`
      + `<input type="time" value="${esc(s.calme.from)}" aria-label="Début des heures calmes" onchange="NOTIF.calme('from',this.value)"${off ? ' disabled' : ''}><span>à</span>`
      + `<input type="time" value="${esc(s.calme.to)}" aria-label="Fin des heures calmes" onchange="NOTIF.calme('to',this.value)"${off ? ' disabled' : ''}></div></section>`;
    h += `<button class="sm nfull" onclick="NOTIF.test()"${off ? ' disabled' : ''}>Envoyer une notification d’essai</button>`;
    return h;
  }
  function change(fn) { const s = settings(); fn(s); save(s); A().R(); }
  function tog(k) {
    change(s => { if (k === 'on') s.on = !s.on; else s[k].on = !s[k].on; });
    const s = settings(), st = status(), f = app();
    if (k === 'repos' && s.repos.on && st && st.exactNeeded && !st.exact && f) try { f.exactRequest(); } catch (e) {}   // demandée seulement ici
  }
  function day(i) { change(s => { const d = new Set(s.rappel.days); d.has(i) ? d.delete(i) : d.add(i); s.rappel.days = [...d].sort(); }); }
  function time(v) { if (mins(v) == null) return A().R(); change(s => { s.rappel.time = v; }); }
  function calme(k, v) { if (mins(v) == null) return A().R(); change(s => { s.calme[k] = v; }); }
  function test() { const f = app(); if (f) try { f.notifTest('Notification d’essai', 'Les notifications de Fonte fonctionnent.'); } catch (e) {} }

  window.NOTIF = {
    view, sync, onStatus, rest, tog, day, time, calme, test,
    enable: () => { const f = app(); if (f) try { f.notifRequest(); } catch (e) {} },
    channel: id => { const f = app(); if (f) try { f.openChannel(id); } catch (e) {} },
    exact: () => { const f = app(); if (f) try { f.exactRequest(); } catch (e) {} },
    // pour les tests
    _: {plan, serialize, settings, defaults, quiet, mins, syncNow}
  };
})();
