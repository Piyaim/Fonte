# SPDX-License-Identifier: AGPL-3.0-or-later
# Refonte, lot 4 : menu ☰, « Mon profil », Données, Notifications (maquette validée le 30/10/2026), et règle de sélection du 30/10/2026.
# 1. Écrans du lot 4 (mode local ; Données aussi en mode serveur) :
#    - menu : 3 groupes, « Esprits » toujours dans la liste, onglet Esprits masqué puis remis par son interrupteur, pastilles de 44 px ;
#    - Données : avertissement framboise visible AVANT tout bouton d'import ; aucun bouton d'import orange ; deux exports séparés (local) ;
#      fichier choisi LU et décrit (séances, programmes, pesées) sans rien importer ; « Remplacer mes données » puis confirmation refusée :
#      rien ne change ; acceptée : données remplacées ; texte collé : même chemin ; fichier illisible ou d'un autre format : refusé, rien ne
#      change ; export de photos : « Ajouter les N photos », rien n'est remplacé ; depuis « Bienvenue » : « ‹ Retour au questionnaire »,
#      aucune action orange ; version serveur : pas d'export de photos ;
#    - Mon profil : pesée ajoutée par − / + et « Ajouter », supprimée par sa corbeille ; carte du poids à l'encre, sans objectif ;
#      détail santé par interrupteur ; « Refaire le questionnaire » ne remplace rien sans la confirmation ;
#    - Notifications : heures en − / + de 15 min (tour de minuit), jours, un seul « Son et vibration » pour les 3 messages du programme
#      (3 boutons de canal en tout), bloquées : réglages désactivés et lisibles, une seule action (« Activer les notifications »).
# 2. Règle de sélection, écrans des lots 1 à 4 × 6 couleurs × clair et sombre : tout choix sélectionné (aria-pressed, aria-current, .on)
#    est teinté (--sel-bg), bordé de la couleur (--sel-b), texte en encre, jamais plein ; interrupteur activé de la couleur (3:1 au moins) ;
#    une seule action pleine (fond --a) au plus par écran.
# 3. Aucun « IMC » ni mot de catégorie (surpoids, obésité, corpulence, insuffisance pondérale) affiché, replis ouverts, détail santé
#    affiché, sur le questionnaire (question 17, résumé), « Mon profil » et l'accueil, avec un IMC de 32 et de 17.
# 4. Mouvement réduit : aucune transition ni animation sur ces écrans (menu ouvert compris), pseudo-éléments compris.
# 5. Aucune erreur JavaScript, aucune requête sortante.
# Témoins : tests/lot4_temoins.py (une règle faussée à la fois dans une copie du code, FONTE_ROOT).
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot4.py
import json, os, re, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTIES = os.environ.get("LOT4_PARTIES", "1234")
ACCS = os.environ.get("LOT4_ACC", "orange,blue,green,violet,red,mono").split(",")
P1, P2 = 5201, 5202
TMP = tempfile.mkdtemp(prefix="fonte-lot4-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
PROCS = []
def serveur(port):
    pr = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={port})"], cwd=os.path.join(ROOT, "server"),
                          env=dict(os.environ, DB_PATH=os.path.join(TMP, f"{port}.db"), PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(pr); time.sleep(2.5)
    if pr.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {port} déjà pris ?)")
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
REP = {"prenom": "Léo", "age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "athletique", "objectifs2": ["forme"], "niveau": "reprise",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "oui"}
COQUE = """window.__N = Object.assign({perm: 'granted', exact: true, exactNeeded: true, sdk: 34, sent: [], calls: []}, JSON.parse(sessionStorage.getItem('__N') || '{}'));
window.FonteApp = {notifStatus: () => JSON.stringify({sdk: __N.sdk, perm: __N.perm, exact: __N.exact, exactNeeded: __N.exactNeeded, channels: __N.sdk >= 26, sent: __N.sent}),
  notifAskOnce: () => 0, notifRequest: () => __N.calls.push('request'), notifPlan: () => 0, notifTest: () => 0, restStart: () => true, restCancel: () => 0,
  openChannel: id => __N.calls.push('channel:' + id), exactRequest: () => 0, saveFile: (n, m, t) => { __N.saved = [n, t]; }, setIcon: () => {}, keepScreenOn: () => {}};"""
SEANCES = """async () => { let d = new Date(2026, 9, 5), k = 0; const end = new Date(2026, 10, 2);
  while (d <= end) { if ([1, 3, 5].includes(d.getDay())) { const w = WO[k % WO.length], wk = Math.floor(k / 3), day = new Date(d.getTime() - d.getTimezoneOffset() * 6e4).toISOString().slice(0, 10);
    await api('POST', '/api/sessions', {day, workout_id: w.id, workout_name: w.name, entries: w.items.map(i => { const e = EX[i];
      const s = e.kind === 'weight' ? [40 + 2.5 * Math.floor(wk / 2), 10 + wk % 2] : e.kind === 'cardio' ? [null, 20] : e.kind === 'time' ? [null, 30 + 5 * wk] : [null, 8 + wk];
      return {exercise_id: i, sets: e.kind === 'cardio' ? [s] : [s, s, s], effort: 3}; })}); k++; }
    d.setDate(d.getDate() + 1); }
  for (const [day, kg] of [['2026-10-20', 75.9], ['2026-10-27', 75.1], ['2026-11-03', 74.8]]) await api('POST', '/api/bodyweight', {day, kg}); await load(); }"""
OUVRIR = "document.querySelectorAll('#app details, #drawer details').forEach(d => d.open = true)"
BROU = "([a, i, m, r]) => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: m, i, redo: r}))"
# règle de sélection et action pleine, mesurées sur l'écran affiché
SEL = r"""() => {
  const col = v => { const i = document.createElement('i'); i.style.color = v; document.body.appendChild(i); const c = getComputedStyle(i).color; i.remove(); return c; };
  const SB = col('var(--sel-bg)'), SBO = col('var(--sel-b)'), A = col('var(--a)'), T = col('var(--t)');
  const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : ((v + .055) / 1.055) ** 2.4; }; return .2126 * f(m[0]) + .7152 * f(m[1]) + .0722 * f(m[2]); };
  const cr = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); };
  const bgOf = el => { for (let e = el; e; e = e.parentElement) { const c = getComputedStyle(e).backgroundColor, m = c.match(/[\d.]+/g); if (m && (m[3] === undefined || +m[3] > .5)) return c; } return getComputedStyle(document.body).backgroundColor; };
  const vis = el => { const r = el.getBoundingClientRect(); if (!r.width || !r.height) return false; for (let e = el; e; e = e.parentElement) { const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden') return false; } return !el.closest('details:not([open]) > :not(summary)'); };
  const zone = '#app, #drawer, .actbar, .bar';
  const sel = [...document.querySelectorAll(zone.split(', ').map(z => `${z} [aria-pressed="true"], ${z} [aria-current], ${z} button.on`).join(', '))]
    .filter(el => vis(el) && !el.matches('.swc, .chip.z, .tick, .tick *, .cal .cd, .tabbar *, svg *'));
  const pb = [], nom = el => (el.innerText || el.getAttribute('aria-label') || el.className).trim().replace(/\s+/g, ' ').slice(0, 24);
  for (const el of sel) { const s = getComputedStyle(el);
    if (s.backgroundColor === A) pb.push('pleine : ' + nom(el));
    else if (s.backgroundColor !== SB) pb.push('non teintée : ' + nom(el) + ' ' + s.backgroundColor);
    if (!(s.boxShadow.includes(SBO) || (s.borderTopColor === SBO && parseFloat(s.borderTopWidth) >= 1.5))) pb.push('sans bord de la couleur : ' + nom(el));
    if (s.color !== T) pb.push('texte pas en encre : ' + nom(el)); }
  for (const el of document.querySelectorAll('#app [role="switch"][aria-checked="true"]:not(:disabled), #drawer [role="switch"][aria-checked="true"]')) { if (!vis(el)) continue;
    const t = el.querySelector('.sw'), c = t ? getComputedStyle(t).backgroundColor : getComputedStyle(el, '::before').backgroundColor;
    if (c !== SBO) pb.push('interrupteur pas de la couleur : ' + nom(el)); else if (cr(c, bgOf(el)) < 3) pb.push('interrupteur sous 3:1 : ' + nom(el)); }
  const pleins = [...document.querySelectorAll(zone.split(', ').map(z => `${z} button, ${z} a, ${z} label.btn`).join(', '))]
    .filter(el => vis(el) && !el.matches('.swc, .tick, .tick *') && !el.closest('.cal') && getComputedStyle(el).backgroundColor === A).map(nom);
  return {pb, pleins, n: sel.length};
}"""
MOTS = re.compile(r"\bIMC\b|surpoids|obésité|corpulence|insuffisance pondérale", re.I)
MOUV = r"""() => [...document.querySelectorAll('#app *, #drawer *, .bar *, .actbar *, .tabbar *')].filter(e => !e.closest('.j-wrap, [data-jeu]'))
  .flatMap(e => [[e, null], [e, '::before'], [e, '::after']]).map(([e, p]) => { const s = getComputedStyle(e, p);
    const tr = s.transitionProperty !== 'none' && s.transitionDuration.split(',').some(d => parseFloat(d) > 0);
    return tr || s.animationName !== 'none' ? (e.className.baseVal ?? e.className) + (p || '') : null; }).filter(Boolean)"""

def prepare(pg, port, rep=REP, seances=True):
    pg.goto(f"http://127.0.0.1:{port}/?local=1"); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
    pg.evaluate(BROU, [rep, 16, "resume", False]); pg.reload()
    pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300)
    pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
    if seances and not pg.evaluate("SESS.length"): pg.evaluate(SEANCES)
    pg.evaluate("go('accueil')")

ext = []; errs = []
def page(b, port, w=390, h=844, scheme="light", coque=True, reduce=False):
    ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, reduced_motion="reduce" if reduce else "no-preference", accept_downloads=True)
    if coque: ctx.add_init_script(COQUE)
    ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(f"http://127.0.0.1:{port}") or r.request.url.startswith(("data:", "blob:")) else (ext.append(r.request.url), r.abort()))
    pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.clock.set_fixed_time("2026-11-04T10:00:00")
    return ctx, pg

# écrans des lots 1 à 4, atteints sur la même appli (données d'essai) : nom, fonction qui l'affiche
def ecrans(pg):
    def seance_ressenti():
        pg.evaluate("go('accueil')"); pg.click("#app .hero button:has-text('Démarrer la séance')"); pg.wait_for_selector(".focus")
        while pg.locator(".focus .frow.act .tick").count(): pg.locator(".focus .frow.act .tick").click(); pg.wait_for_timeout(80)
        pg.click(".bar button:has-text('Passer')"); pg.locator(".focus .feelb button").nth(1).click(); pg.locator(".focus .feelb button.on, .focus button:has-text('Changer')").first.wait_for()
        if pg.locator(".focus button:has-text('Changer')").count(): pg.click(".focus button:has-text('Changer')")
    def seance_liste(): pg.evaluate("exitFocus(); window.scrollTo(0, 0)")
    def fin_seance(): pg.evaluate("store(draftKey()); F = null; FOC = null; TMskip(); go('accueil')")
    def question(i, a):
        def f():
            pg.evaluate(BROU, [a, i, "q", True]); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000)
            pg.evaluate("go('profil'); PROFIL.redo()"); pg.wait_for_selector("#app .qcount", timeout=8000)
        return f
    def sans_brouillon(): pg.evaluate("localStorage.removeItem('muscu-profil-brouillon')"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000)
    return [
        ("accueil", lambda: pg.evaluate("go('accueil')"), None),
        ("séance, ressenti choisi", seance_ressenti, None), ("séance en liste", seance_liste, fin_seance),
        ("Progrès", lambda: pg.evaluate("go('progres')"), None), ("Progrès, jour choisi", lambda: (pg.evaluate("CAL = null; R()"), pg.click("#app .cal .cd.on >> nth=0")), None),
        ("Historique", lambda: pg.evaluate("go('historique')"), None),
        ("question à un choix", question(5, REP), None), ("questionnaire santé", question(13, dict(REP, sante={"poitrine": False, "coeur": True})), None),
        ("exercices à éviter", question(14, dict(REP, eviter=["leg-extension"])), sans_brouillon),
        ("Exercices, groupe choisi", lambda: pg.evaluate("catG = 'Jambes'; go('exercices')"), None),
        ("formulaire d'exercice", lambda: pg.evaluate("editOpen(Object.values(EX).find(e => e.name.startsWith('Développé couché'))); window.scrollTo(0, 0)"), lambda: pg.evaluate("editEx = null; go('accueil')")),
        ("Programmes ouvert", lambda: pg.evaluate("go('programmes'); progDraft.open = progDraft.items[1]; R()"), lambda: pg.evaluate("progDraft = null; go('accueil')")),
        ("Zones choisies", lambda: pg.evaluate("ZSEL = new Set(['pectoraux', 'dos']); ZMODE = 'pick'; go('zones')"), None),
        ("Zones, ma semaine", lambda: pg.evaluate("ZMODE = 'heat'; R()"), lambda: pg.evaluate("ZMODE = 'pick'; ZSEL = new Set(); go('accueil')")),
        ("menu ☰", lambda: pg.evaluate("go('accueil'); openMenu()"), lambda: pg.evaluate("closeMenu()")),
        ("Mon profil", lambda: pg.evaluate("go('profil')"), None), ("Données", lambda: pg.evaluate("go('donnees')"), None),
        ("Notifications", lambda: pg.evaluate("go('notifications')"), None)]

try:
    with sync_playwright() as p:
        b = p.chromium.launch(); serveur(P1)
        if "1" in PARTIES:
            ctx, pg = page(b, P1); prepare(pg, P1)
            # ---- menu
            pg.evaluate("openMenu()"); pg.wait_for_timeout(250)
            grp = pg.evaluate("[...document.querySelectorAll('#dnav .dgrp')].map(e => e.innerText)")
            ok(grp == ["Entraînement", "Suivi", "Réglages"], f"menu : 3 groupes ({grp})")
            items = pg.evaluate("[...document.querySelectorAll('#dnav button')].map(e => e.innerText.trim())")
            ok(len(items) == 11 and "Esprits" in items and all(pg.evaluate("[...document.querySelectorAll('#dnav button svg')].length") == 11 for _ in [0]), f"menu : 11 écrans avec une icône chacun, Esprits compris ({items})")
            sw = pg.evaluate("[...document.querySelectorAll('#drawer .swc')].map(e => { const r = e.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; })")
            ok(len(sw) == 6 and all(w >= 44 and h >= 44 for w, h in sw), f"menu : 6 pastilles de couleur de 44 px au moins ({sw})")
            pg.click("#drawer [role=switch][aria-label='Afficher l’onglet Esprits dans la barre du bas']"); pg.wait_for_timeout(200)
            ok(not pg.locator(".tabbar button:has-text('Esprits')").count() and pg.locator("#dnav button:has-text('Esprits')").count() == 1
               and pg.get_attribute("#drawer [role=switch][aria-label='Afficher l’onglet Esprits dans la barre du bas']", "aria-checked") == "false", "menu : onglet Esprits masqué, « Esprits » reste dans le menu")
            pg.click("#drawer [role=switch][aria-label='Afficher l’onglet Esprits dans la barre du bas']"); pg.wait_for_timeout(200)
            ok(pg.locator(".tabbar button:has-text('Esprits')").count() == 1, "menu : onglet Esprits remis par l’interrupteur")
            pg.click("#drawer .seg button:has-text('Femme')"); ok(pg.evaluate("GENDER") == "f" and pg.get_attribute("#drawer .seg button:has-text('Femme')", "aria-pressed") == "true", "menu : Homme / Femme en segments")
            pg.click("#drawer .seg button:has-text('Homme')"); pg.evaluate("closeMenu()")
            # ---- Données
            pg.evaluate("go('donnees')"); pg.wait_for_timeout(200)
            ordre = pg.evaluate("""() => { const w = [...document.querySelectorAll('#app .warn')].find(e => /remplace toutes tes données/.test(e.innerText)); if (!w) return 'absent';
              const A = getComputedStyle(document.documentElement).getPropertyValue('--a');
              const imp = [...document.querySelectorAll('#app button, #app label.btn')].filter(b => /Choisir un fichier|Remplacer|Lire ce texte|Ajouter les/.test(b.innerText));
              if (!imp.length) return 'aucun bouton d’import';
              const i = document.createElement('i'); i.style.color = 'var(--danger)'; document.body.appendChild(i); const D = getComputedStyle(i).color; i.remove();
              if (getComputedStyle(w).borderLeftColor !== D || getComputedStyle(w.querySelector('h3')).color !== D) return 'pas en framboise';
              return imp.every(b => w.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING) ? 'ok' : 'bouton avant l’avertissement'; }""")
            ok(ordre == "ok", f"Données : avertissement framboise visible avant tout bouton d’import ({ordre})")
            ok(pg.locator("#app a:has-text('Exporter mes séances')").count() == 1 and pg.locator("#app a:has-text('Exporter mes photos')").count() == 1, "Données : deux exports séparés (séances, photos)")
            def exporte(texte):   # la coque enregistre le fichier (FonteApp.saveFile), comme sur le téléphone
                pg.evaluate("__N.saved = null"); pg.click(f"#app a:has-text('{texte}')"); pg.wait_for_function("!!__N.saved", timeout=8000); return json.loads(pg.evaluate("__N.saved[1]"))
            export = exporte("Exporter mes séances"); n0 = len(export["sessions"])
            ok(export.get("format") == "suivi-muscu" and n0 > 5, f"Données : export des séances ({n0} séances)")
            neuf = dict(export, sessions=export["sessions"][:2], bodyweight=export["bodyweight"][:1])
            fic = os.path.join(TMP, "sauvegarde.json"); open(fic, "w", encoding="utf-8").write(json.dumps(neuf))
            avant = pg.evaluate("JSON.stringify([SESS.length, BW.length, WO.length])")
            pg.set_input_files("#bkf", fic); pg.wait_for_selector("#app .file", timeout=5000)
            desc = pg.inner_text("#app .file")
            ok("sauvegarde.json" in desc and "2 séances" in desc and "1 pesée" in desc and f"{len(neuf['workouts'])} programme" in desc, f"Données : fichier lu et décrit avant l’import ({desc!r})")
            ok(pg.evaluate("JSON.stringify([SESS.length, BW.length, WO.length])") == avant, "Données : rien n’est importé au choix du fichier")
            ok(f"Tes {n0} séances actuelles seront remplacées par les 2 de ce fichier." in pg.inner_text("#app"), "Données : « Tes N séances actuelles seront remplacées par les 2 de ce fichier. »")
            rb = pg.locator("#app button:has-text('Remplacer mes données')")
            ok(rb.count() == 1 and pg.evaluate("el => getComputedStyle(el).backgroundColor !== getComputedStyle(el).getPropertyValue('--a') && el.classList.contains('btn-d') && !!el.querySelector('svg')", rb.element_handle())
               and pg.evaluate("el => { const i = document.createElement('i'); i.style.background = 'var(--a)'; document.body.appendChild(i); const a = getComputedStyle(i).backgroundColor; i.remove(); return getComputedStyle(el).backgroundColor !== a; }", rb.element_handle()),
               "Données : « Remplacer mes données » en danger (framboise, icône), jamais orange")
            pg.once("dialog", lambda d: d.dismiss()); rb.click(); pg.wait_for_timeout(800)
            ok(pg.evaluate("JSON.stringify([SESS.length, BW.length, WO.length])") == avant, "Données : confirmation refusée, rien ne change")
            msgs = []; pg.on("dialog", lambda d: (msgs.append(d.message), d.accept()))
            pg.click("#app button:has-text('Remplacer mes données')"); pg.wait_for_timeout(1500)
            ok(any("REMPLACER" in m for m in msgs) and pg.evaluate("SESS.length") == 2 and pg.evaluate("BW.length") == 1, f"Données : confirmation acceptée, données remplacées ({pg.evaluate('SESS.length')} séances)")
            # texte collé, puis fichier illisible et fichier d'un autre format
            pg.evaluate("go('donnees')"); pg.evaluate(OUVRIR); pg.fill("#bk", json.dumps(export)); pg.click("#app button:has-text('Lire ce texte')"); pg.wait_for_selector("#app .file")
            ok("Texte collé" in pg.inner_text("#app .file") and pg.evaluate("SESS.length") == 2, "Données : texte collé lu et décrit, rien d’importé")
            pg.click("#app button:has-text('Remplacer mes données')"); pg.wait_for_timeout(1500)
            ok(pg.evaluate("SESS.length") == n0, "Données : texte collé importé après confirmation")
            for nom, contenu, attendu in (("cassé.json", "{pas du json", "pas lisible"), ("autre.json", json.dumps({"format": "autre", "x": 1}), "pas une sauvegarde")):
                fx = os.path.join(TMP, nom); open(fx, "w", encoding="utf-8").write(contenu); pg.evaluate("go('donnees')")
                pg.set_input_files("#bkf", fx); pg.wait_for_selector("#app .qerr", timeout=5000)
                ok(attendu in pg.inner_text("#app .qerr") and not pg.locator("#app button:has-text('Remplacer mes données'), #app button:has-text('Ajouter les')").count() and pg.evaluate("SESS.length") == n0,
                   f"Données : {nom} refusé, aucun bouton d’import, rien ne change")
            ph = exporte("Exporter mes photos")
            ph = dict(ph, photos=[{"day": "2026-11-01", "ts": 1, "note": "a", "full": "data:image/jpeg;base64,/9j/4AAQ", "thumb": "data:image/jpeg;base64,/9j/4AAQ"}] * 2) if not ph.get("photos") else ph
            fp = os.path.join(TMP, "photos.json"); open(fp, "w", encoding="utf-8").write(json.dumps(ph)); pg.evaluate("go('donnees')")
            pg.set_input_files("#bkf", fp); pg.wait_for_selector("#app .file:has-text('Export de photos')", timeout=5000)
            t = pg.inner_text("#app")
            ok("Rien n’est remplacé" in t and pg.locator(f"#app button:has-text('Ajouter les {len(ph['photos'])} photos')").count() == 1 and not pg.locator("#app button:has-text('Remplacer')").count(),
               f"Données : export de photos : « Ajouter les N photos », rien n’est remplacé")
            # ---- Mon profil
            pg.evaluate("go('profil')"); pg.wait_for_timeout(200); nb = pg.evaluate("BW.length")
            v0 = pg.input_value("#pw"); pg.click("#app button[aria-label='Plus 0,1 kg']"); v = pg.input_value("#pw")
            ok(abs(float(v.replace(",", ".")) - float(v0.replace(",", ".")) - .1) < 1e-9, f"Mon profil : + ajoute 0,1 kg ({v0} → {v})")
            pg.click("#app .card:has(h2:text('Poids de corps')) button:has-text('Ajouter')"); pg.wait_for_timeout(800)
            ok(pg.evaluate("BW.length") == nb + 1 and abs(pg.evaluate("BW[BW.length - 1].kg") - float(v.replace(",", "."))) < 1e-9, f"Mon profil : pesée ajoutée par + et « Ajouter » ({v} kg)")
            pg.evaluate(OUVRIR); pg.locator("#app .wrow button.btn-d").first.click(); pg.wait_for_timeout(800)
            ok(pg.evaluate("BW.length") == nb, "Mon profil : pesée supprimée par sa corbeille")
            carte = pg.evaluate("""() => { const c = [...document.querySelectorAll('#app .card')].find(e => /Poids de corps/.test(e.innerText)); if (!c) return 'absente';
              const col = v => { const i = document.createElement('i'); i.style.color = v; document.body.appendChild(i); const x = getComputedStyle(i).color; i.remove(); return x; };
              const okc = [col('var(--t)'), col('var(--m)')]; if (/objectif|idéal|trop|surpoids|maigr/i.test(c.innerText)) return 'jugement';
              const w = document.createTreeWalker(c, NodeFilter.SHOW_TEXT); for (let n; (n = w.nextNode());) { const e = n.parentElement; if (!n.textContent.trim() || e.closest('button.btn-d')) continue; if (!okc.includes(getComputedStyle(e).color)) return 'couleur ' + n.textContent.trim(); } return 'ok'; }""")
            ok(carte == "ok", f"Mon profil : poids à l’encre, sans objectif ({carte})")
            pg.click("#app [role=switch][aria-label='Détail santé']"); pg.wait_for_timeout(200)
            on = pg.get_attribute("#app [role=switch][aria-label='Détail santé']", "aria-checked"); t = pg.inner_text("#app")
            ok(on == "false" and "kcal" not in t, "Mon profil : détail santé masqué par son interrupteur")
            pg.click("#app [role=switch][aria-label='Détail santé']"); pg.wait_for_timeout(200)
            ok("kcal" in pg.inner_text("#app") and "Protéines" in pg.inner_text("#app"), "Mon profil : détail santé affiché (calories, protéines)")
            wo0 = pg.evaluate("JSON.stringify(WO.map(w => [w.id, w.name, w.items]))")
            pg.click("#app button:has-text('Refaire le questionnaire')"); pg.wait_for_selector("#app .qcount")
            pg.evaluate(BROU, [dict(REP, seances=2), 16, "resume", True]); pg.reload(); pg.wait_for_selector("#app", timeout=8000)
            pg.evaluate("go('profil'); PROFIL.redo()"); pg.click("button:has-text('Générer mon programme')"); pg.wait_for_selector("text=Remplacer tes programmes ?")
            ok(pg.evaluate("JSON.stringify(WO.map(w => [w.id, w.name, w.items]))") == wo0, "Mon profil : « Refaire le questionnaire » ne remplace rien avant la confirmation")
            pg.click("#tb-back"); pg.evaluate("PROFIL.quit(); localStorage.removeItem('muscu-profil-brouillon')"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000)
            # ---- Notifications
            pg.evaluate("go('notifications')"); pg.wait_for_timeout(200)
            h0 = pg.input_value("#app [data-n=rappel] input.tval")
            pg.click("#app button[aria-label='Heure du rappel : plus 15 minutes']"); h1 = pg.input_value("#app [data-n=rappel] input.tval")
            pg.click("#app button[aria-label='Fin des heures calmes : moins 15 minutes']"); fin = pg.evaluate("NOTIF._.settings().calme.to")
            for _ in range(33): pg.click("#app button[aria-label='Fin des heures calmes : moins 15 minutes']")
            ok((h0, h1) == ("18:00", "18:15") and fin == "07:45" and pg.evaluate("NOTIF._.settings().calme.to") == "23:30", f"Notifications : − et + de 15 min, tour de minuit ({h0} → {h1}, fin {fin} → {pg.evaluate('NOTIF._.settings().calme.to')})")
            d0 = pg.evaluate("NOTIF._.settings().rappel.days"); pg.click("#app .day[aria-label='mardi']")
            ok(pg.evaluate("NOTIF._.settings().rappel.days") == sorted(d0 + [1]) and pg.get_attribute("#app .day[aria-label='mardi']", "aria-pressed") == "true", "Notifications : jour ajouté au rappel")
            ch = pg.evaluate("[...document.querySelectorAll('#app .chan')].map(e => e.innerText.trim())")
            ok(len(ch) == 3 and ch[2] == "Son et vibration de ces 3 messages", f"Notifications : un seul « Son et vibration » pour les 3 messages du programme ({ch})")
            pg.click("#app .chan:has-text('ces 3 messages')"); ok("channel:programme" in pg.evaluate("__N.calls"), "Notifications : il ouvre le canal « programme »")
            pg.evaluate(OUVRIR); txt = pg.inner_text("#app").replace("Aucune notification sur les Esprits ni les jetons.", "")
            ok(not re.search(r"esprit|jeton|tirage|n.oublie|dommage|raté|manqu|d.affilée|tu dois", txt, re.I), "Notifications : ni Esprits ni jetons, aucun mot qui pousse ou culpabilise")
            pg.evaluate("sessionStorage.setItem('__N', JSON.stringify({perm: 'ask'}))"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000); pg.evaluate("go('notifications')")
            r = pg.evaluate("""() => ({dis: [...document.querySelectorAll('#app .noff button, #app .noff input')].every(e => e.disabled), n: document.querySelectorAll('#app .noff button').length,
              op: [...document.querySelectorAll('#app .noff, #app .noff *')].every(e => getComputedStyle(e).opacity === '1')})""")
            ok(r["dis"] and r["n"] > 8 and r["op"], f"Notifications bloquées : réglages désactivés, lisibles (aucune transparence) ({r})")
            pg.click("#app button:has-text('Activer les notifications')"); ok("request" in pg.evaluate("__N.calls"), "Notifications bloquées : « Activer les notifications » demande l’autorisation")
            ctx.close()
            # ---- Données depuis « Bienvenue », et version serveur
            ctx, pg = page(b, P1); pg.goto(f"http://127.0.0.1:{P1}/?local=1"); pg.evaluate("indexedDB.deleteDatabase('suivi-muscu'); localStorage.clear()"); pg.reload()
            pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000); pg.click("button:has-text('J’ai une sauvegarde')"); pg.wait_for_timeout(300)
            r = pg.evaluate(SEL)
            ok(pg.get_attribute("#tb-back", "aria-label") == "Retour au questionnaire" and not pg.locator("#tb-back[hidden]").count() and not r["pleins"],
               f"Données depuis « Bienvenue » : « ‹ Retour au questionnaire », aucune action pleine ({r['pleins']})")
            pg.click("#tb-back"); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=5000); ok(True, "Données depuis « Bienvenue » : « ‹ » revient au questionnaire")
            ctx.close(); serveur(P2)
            ctx, pg = page(b, P2, coque=False); pg.goto(f"http://127.0.0.1:{P2}/"); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
            pg.click("button:has-text('J’ai une sauvegarde')"); pg.wait_for_timeout(300)
            ok(pg.locator("#app a:has-text('Exporter mes séances')").count() == 1 and not pg.locator("#app a:has-text('Exporter mes photos')").count() and "serveur Fonte" in pg.inner_text("#app"),
               "Données, version serveur : export des séances seul, texte du serveur")
            pg.set_input_files("#bkf", fic); pg.wait_for_selector("#app .file"); pg.on("dialog", lambda d: d.accept())
            pg.click("#app button:has-text('Remplacer mes données')"); pg.wait_for_timeout(1500)
            ok(pg.evaluate("SESS.length") == 2, "Données, version serveur : import par fichier lu puis confirmé")
            ctx.close()
        if "2" in PARTIES or "4" in PARTIES:
            for scheme, tn in (("light", "clair"), ("dark", "sombre")):
                ctx, pg = page(b, P1, scheme=scheme, reduce="4" in PARTIES and "2" not in PARTIES); prepare(pg, P1)
                vus = 0
                for nom, aller, retour in ecrans(pg):
                    aller(); pg.wait_for_timeout(300); pg.evaluate(OUVRIR)
                    if "2" in PARTIES:
                        for acc in ACCS:
                            pg.evaluate(f"setAccent('{acc}')"); pg.wait_for_timeout(60); r = pg.evaluate(SEL); vus += r["n"]
                            ok(not r["pb"], f"sélection teintée · {tn} {acc} · {nom} {r['pb'][:3]}")
                            ok(len(r["pleins"]) <= 1, f"une seule action pleine · {tn} {acc} · {nom} {r['pleins']}")
                        pg.evaluate("setAccent('orange')")
                    if "4" in PARTIES and scheme == "light":
                        pg.emulate_media(reduced_motion="reduce"); pg.wait_for_timeout(50); m = pg.evaluate(MOUV)
                        ok(not m, f"mouvement réduit · {nom} : aucune transition ni animation {sorted(set(m))[:4]}"); pg.emulate_media(reduced_motion="no-preference")
                    if retour: retour()
                if "2" in PARTIES: ok(vus > 12 * len(ACCS), f"(témoin) des choix sélectionnés ont bien été mesurés ({vus})")
                ctx.close()
        if "3" in PARTIES:
            for rep, quoi in ((dict(REP, poids=101), "IMC de 32"), (dict(REP, poids=53), "IMC de 17")):
                ctx, pg = page(b, P1); pg.goto(f"http://127.0.0.1:{P1}/?local=1"); pg.evaluate("indexedDB.deleteDatabase('suivi-muscu'); localStorage.clear()")
                pg.reload(); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000)
                vus = []
                pg.evaluate(BROU, [rep, 16, "q", False]); pg.reload(); pg.wait_for_selector("#app .qcount", timeout=8000); pg.evaluate(OUVRIR); vus.append(("question 17", pg.inner_text("#app")))
                pg.evaluate(BROU, [rep, 16, "resume", False]); pg.reload(); pg.wait_for_selector("text=Ton résumé"); pg.evaluate(OUVRIR); vus.append(("résumé", pg.inner_text("#app")))
                pg.click("button:has-text('Générer mon programme')"); pg.wait_for_timeout(300); pg.evaluate(OUVRIR); vus.append(("confirmation", pg.inner_text("#app")))
                pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt"); pg.evaluate(OUVRIR); vus.append(("programme prêt", pg.inner_text("#app")))
                pg.evaluate("go('profil')"); pg.evaluate(OUVRIR); vus.append(("Mon profil", pg.inner_text("#app")))
                pg.evaluate("go('accueil')"); pg.evaluate(OUVRIR); vus.append(("accueil", pg.inner_text("#app")))
                pg.evaluate("go('seance')"); pg.evaluate(OUVRIR); vus.append(("séance", pg.inner_text("#app")))
                for ou, t in vus: ok(not MOTS.search(t), f"{quoi} · {ou} : ni « IMC » ni catégorie affichés {MOTS.findall(t)[:3]}")
                ok("Calories, protéines, sommeil" in vus[0][1], f"{quoi} · question 17 : « Calories, protéines, sommeil »")
                if "32" in quoi: ok("Repos un peu plus longs et cardio plus doux, d’après ta taille et ton poids." in vus[4][1], f"{quoi} · Mon profil : phrase neutre dans « Détails » du programme")
                ok(pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil')).answers.poids") == rep["poids"], f"{quoi} : réponses enregistrées inchangées")
                ctx.close()
        b.close()
finally:
    for pr in PROCS: pr.terminate()
ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
ok(not ext, f"aucune requête sortante {ext[:2]}")
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
