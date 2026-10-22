# SPDX-License-Identifier: AGPL-3.0-or-later
# Lot 2B, avec des dates simulées (horloge de Playwright) :
# phases (bonne semaine, « Plus tard » = 7 jours, « Accepter » ne change que les réglages de séance), semaine allégée (−20 %),
# reprise en douceur (80 %, après 22 jours sans séance et pas après 20), jamais le mot « manquée », placement sur les jours,
# conseil de charge combiné (cas du cahier des charges, baisse, priorités, « dernière fois » du même programme),
# IMC de 30 ou plus (repos +30 s plafonné à 3 min, raison cachée), bouton « Démarrer la séance » toujours en tête de l'accueil,
# boutons ↑ ↓ ✕ de 44 px, sécurité (phase 1, sauts, profils protégés), export et import de l'état du programme.
# Les valeurs attendues sont écrites ici en dur : une règle faussée dans le code doit faire échouer le test.
#   python3 tests/lot2b.py
import itertools, json, os, re, subprocess, sys, time
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5118
env = dict(os.environ, DB_PATH="/tmp/lot2b.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/lot2b.db", "/tmp/lot2b.db-wal", "/tmp/lot2b.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

D0 = date(2026, 11, 2)                 # un lundi
J = lambda k: (D0 + timedelta(days=k)).isoformat()
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
BASE = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "athletique", "objectifs2": ["forme"],
        "niveau": "reprise", "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"],
        "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
def prof(**k):
    a = json.loads(json.dumps(BASE)); a.update(k); return a
MANQUE = re.compile(r"manqué", re.I)   # manqué, manquée, manquées (pas « il manque un exercice »)
VUES = ["accueil", "seance", "zones", "progres", "historique", "exercices", "programmes", "profil", "donnees"]
ETAT = "fetch('/api/state').then(r => r.json()).then(s => ({ex: s.exercises.map(e => { const o = Object.assign({}, e); delete o.used; return o; }), sessions: s.sessions, workouts: s.workouts, bw: s.bodyweight}))"
SEANCES = "async l => { for (const s of l) await api('POST', '/api/sessions', s); await load(); R(); }"
EFFACER = "async () => { for (const s of SESS) await api('DELETE', '/api/sessions/' + s.id); await load(); }"
TXT = "[...d.querySelectorAll('p')].map(p => p.textContent).join('\\n')"   # une ligne par paragraphe du conseil
CONSEIL = "([x, w]) => { const d = document.createElement('div'); d.innerHTML = advice(exIn(EX[x], WO.find(v => v.id === w)), null, w); return " + TXT + "; }"
PROFIL = "JSON.parse(localStorage.getItem('muscu-profil') || 'null')"
OUVRIR = "document.querySelectorAll('#app details').forEach(d => d.open = true)"   # lot 2C : replis « Détails » ouverts avant lecture
SETP = "p => localStorage.setItem('muscu-profil', JSON.stringify(p))"

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        def page(jour, local=True, w=390):
            ctx = b.new_context(viewport={"width": w, "height": 844})
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time(jour + "T10:00:00")
            pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if local else "")); pg.wait_for_selector("#app .card", timeout=8000); time.sleep(.3)
            return ctx, pg, errs
        def le(pg, jour):          # même appareil, un autre jour
            pg.clock.set_fixed_time(jour + "T10:00:00"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.3)
        def gen(pg, a):            # questionnaire rempli puis « Remplacer mes programmes »
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", a)
            pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
            pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            pg.evaluate("go('accueil')"); time.sleep(.2)
            return pg.evaluate("fetch('/api/state').then(r => r.json())")
        def slug(s, sl): return next(e for e in s["exercises"] if e["slug"] == sl)
        def offres(pg): return [f["k"] + str(f.get("to", "")) for f in pg.evaluate("PROFIL.offers()")]
        def accueil(pg):          # bouton de séance en tête : premier élément de l'accueil et premier bouton
            pg.evaluate("go('accueil')"); time.sleep(.2)
            return pg.evaluate("""() => { const a = document.getElementById('app'), f = a.firstElementChild, b = a.querySelector('button');
              return {hero: f.classList.contains('hero'), bouton: b ? b.textContent.trim() : '', dansHero: !!(b && f.contains(b)), titre: f.querySelector('h2').textContent,
                      texte: f.innerText, carte: [...a.querySelectorAll('[data-offer],[data-light]')].map(c => c.dataset.offer || 'en cours:' + c.dataset.light),
                      apres: [...a.children].indexOf(a.querySelector('[data-offer],[data-light]'))}; }""")
        def bouton_en_tete(pg, nom):
            h = accueil(pg)
            ok(h["hero"] and h["bouton"] == "Démarrer la séance" and h["dansHero"] and h["apres"] in (-1, 1),
               f"accueil, {nom} : « Démarrer la séance » est le premier élément (cartes dessous : {h['carte']}, position {h['apres']})")
            return h
        def sans_manquee(pg, nom):
            vus = []
            for v in VUES:
                pg.evaluate(f"go('{v}')"); time.sleep(.15); pg.evaluate(OUVRIR)
                if MANQUE.search(pg.inner_text("body")): vus.append(v)
            ok(not vus, f"« manquée » absent de tous les écrans ({nom}) {vus}")
            pg.evaluate("go('accueil')")
        def seances(pg, jours, wids, ex, sets, effort=3):
            pg.evaluate(SEANCES, [{"day": j, "workout_id": wids[i % len(wids)], "entries": [{"exercise_id": ex, "sets": sets, "effort": effort}]} for i, j in enumerate(jours)])

        # =============================================================== 1. phases (niveau « reprise » : phase 1 de 4 semaines)
        ctx, pg, errs = page(J(0)); s0 = gen(pg, BASE)
        wa, wb = [w["id"] for w in s0["workouts"]]; di = slug(s0, "di")["id"]; rdl = slug(s0, "rdl")["id"]; de = slug(s0, "de")["id"]; pc = slug(s0, "pc")["id"]
        pr = pg.evaluate(PROFIL)
        ok(pr["program"]["phase"] == 1 and pr["program"]["start"] == J(0) and pr["program"]["ids"] == [wa, wb], f"programme généré le {J(0)} : phase 1, programmes suivis {pr['program']['ids']}")
        seances(pg, [J(k) for k in range(0, 130, 3)], [wa, wb], pc, [[40, 10], [40, 10], [40, 10]])
        ok("jamais jusqu’à l’échec" in pg.evaluate(CONSEIL, [pc, wa]), "phase 1 : le conseil de charge rappelle « jamais jusqu’à l’échec »")
        le(pg, J(27)); ok("phase2" not in offres(pg) and "phase" not in accueil(pg)["carte"], "jour 27 : pas encore de passage de phase")
        le(pg, J(28)); h = bouton_en_tete(pg, "carte de phase")
        ok("phase2" in offres(pg) and h["carte"] == ["phase"], f"jour 28 (semaine 5) : passage en phase 2 proposé sur l'accueil ({h['carte']})")
        t = pg.inner_text("[data-offer=phase]")
        ok("Phase 2 prête" in t and "Accepter" in t and "Plus tard" in t and "tes exercices et ton historique restent" in pg.text_content("[data-offer=phase]"), "carte de phase : texte, « Accepter » et « Plus tard »")
        sans_manquee(pg, "jour 28")
        pg.click("[data-offer=phase] button:has-text('Plus tard')"); time.sleep(.3)
        ok(pg.evaluate(PROFIL)["cycle"]["later"]["phase"] == J(35) and "phase2" not in offres(pg), "« Plus tard » : reproposé le jour 35 (7 jours après)")
        le(pg, J(34)); ok("phase2" not in offres(pg), "jour 34 : toujours reporté")
        le(pg, J(35)); ok("phase2" in offres(pg), "jour 35 : passage de phase reproposé")
        pg.evaluate("go('profil')"); time.sleep(.3)
        ok(pg.locator("[data-offer=phase]").count() == 1, "la proposition est aussi dans « Mon profil »")
        avant = pg.evaluate(ETAT)
        ok(next(w for w in avant["workouts"] if w["id"] == wa)["settings"][str(di)] == {"sets": 3, "target_min": 10, "target_max": 12, "rest": 90}, "(témoin : avant, réglages de phase 1, 3 × 10-12)")
        pg.click("[data-offer=phase] button:has-text('Accepter')"); time.sleep(1)
        apres = pg.evaluate(ETAT)
        ok(apres["ex"] == avant["ex"] and apres["sessions"] == avant["sessions"] and apres["bw"] == avant["bw"], "« Accepter » : catalogue d'exercices et historique identiques")
        ok([(w["id"], w["name"], w["items"]) for w in apres["workouts"]] == [(w["id"], w["name"], w["items"]) for w in avant["workouts"]], "« Accepter » : mêmes programmes, mêmes exercices dans le même ordre")
        sa = next(w for w in apres["workouts"] if w["id"] == wa)["settings"]
        ok(sa[str(di)] == {"sets": 3, "target_min": 8, "target_max": 12, "rest": 90} and sa[str(rdl)] == {"sets": 3, "target_min": 8, "target_max": 10, "rest": 120},
           f"« Accepter » : réglages de séance de phase 2 (développé incliné 3 × 8-12, 90 s ; soulevé de terre roumain 3 × 8-10, 2 min) {sa[str(di)]}")
        pr = pg.evaluate(PROFIL)["program"]
        ok(pr["phase"] == 2 and pr["phase_start"] == J(35) and "phase" not in pg.evaluate(PROFIL)["cycle"]["later"], "profil : phase 2 depuis le jour 35")
        ok("jamais jusqu’à l’échec" not in pg.evaluate(CONSEIL, [pc, wa]), "phase 2 : plus de rappel de phase 1 dans le conseil")
        # phase 3 : 8 semaines de phase 2 (semaines 5 à 12)
        le(pg, J(90)); ok("phase3" not in offres(pg), "phase 2 commencée le jour 35 : pas de phase 3 au jour 90")
        le(pg, J(91)); ok("phase3" in offres(pg), "jour 91 (8 semaines de phase 2) : phase 3 proposée")
        pg.evaluate("go('profil')"); time.sleep(.3); t = pg.text_content("[data-offer=phase]")
        ok("A\u00a0: force · B\u00a0: volume et endurance" in t, "carte de phase 3 : rôle de chaque séance")
        pg.click("[data-offer=phase] button:has-text('Accepter')"); time.sleep(1)
        s3 = pg.evaluate(ETAT); a3 = next(w for w in s3["workouts"] if w["id"] == wa)["settings"]; b3 = next(w for w in s3["workouts"] if w["id"] == wb)["settings"]
        ok(a3[str(di)] == {"sets": 4, "target_min": 4, "target_max": 6, "rest": 150} and b3[str(de)] == {"sets": 3, "target_min": 10, "target_max": 12, "rest": 75},
           f"phase 3 : Séance A en force (4 × 4-6, 150 s), Séance B en volume (3 × 10-12, 75 s) {a3[str(di)]} {b3[str(de)]}")
        # lot 2C (décision de Georgio) : avec 2 programmes, la phase 3 ajoute une séance C ; A et B gardent leurs exercices
        ok(s3["ex"] == avant["ex"] and [w["items"] for w in s3["workouts"]][:2] == [w["items"] for w in avant["workouts"]] and [w["name"] for w in s3["workouts"]][2:] == ["Séance C"],
           "phase 3 : catalogue et exercices de A et B inchangés, séance C ajoutée (lot 2C)")
        # export puis import ailleurs : l'état du programme suit
        pg.evaluate("go('donnees')"); time.sleep(.2)
        exp = pg.evaluate("fetch('/api/export').then(r => r.json())")
        ok(exp["profil"]["program"]["phase"] == 3 and exp["profil"]["program"]["ids"][:2] == [wa, wb] and len(exp["profil"]["program"]["ids"]) == 3 and "cycle" in exp["profil"], "l'export contient la phase, les programmes suivis et le cycle")
        ok(not errs, f"aucune erreur JavaScript (phases) {errs[:2]}"); ctx.close()
        ctx, pg, errs = page(J(92))
        pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3); pg.fill("#bk", json.dumps(exp)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1500)
        ok(pg.evaluate(PROFIL) == exp["profil"] and pg.evaluate("PROFIL.coach().phase") == 3, "import sur un autre appareil : profil, phase 3 et cycle restaurés")
        ok(not errs, f"aucune erreur JavaScript (import) {errs[:2]}"); ctx.close()

        # débutant (phase 1 de 2 semaines), intermédiaire (phase 2 d'emblée), avancé (phase 3 d'emblée ; ancien profil en phase 2)
        ctx, pg, errs = page(J(0)); gen(pg, prof(niveau="debutant"))
        le(pg, J(13)); ok("phase2" not in offres(pg), "débutant, jour 13 : pas encore")
        le(pg, J(14)); ok("phase2" in offres(pg), "débutant, jour 14 (semaine 3) : phase 2 proposée")
        ctx.close()
        ctx, pg, errs = page(J(0)); gen(pg, prof(niveau="intermediaire"))
        ok(pg.evaluate(PROFIL)["program"]["phase"] == 2, "intermédiaire : phase 2 d'emblée")
        le(pg, J(83)); ok("phase3" not in offres(pg), "intermédiaire, jour 83 : pas encore de phase 3")
        le(pg, J(84)); ok("phase3" in offres(pg), "intermédiaire, jour 84 (semaine 13) : phase 3 proposée")
        ctx.close()
        ctx, pg, errs = page(J(0)); sv = gen(pg, prof(niveau="avance"))
        pa = pg.evaluate(PROFIL); sva = sv["workouts"][0]["settings"][str(slug(sv, "di")["id"])]
        ok(pa["program"]["phase"] == 3 and sva == {"sets": 4, "target_min": 4, "target_max": 6, "rest": 150} and not offres(pg), f"avancé : phase 3 d'emblée (Séance A en force {sva}), rien à proposer")
        pa["program"]["phase"] = 2; pg.evaluate(SETP, pa); le(pg, J(1))
        ok("phase3" in offres(pg), "avancé resté en phase 2 (profil d'avant le lot 2B) : phase 3 proposée tout de suite")
        ok(not errs, f"aucune erreur JavaScript (niveaux) {errs[:2]}"); ctx.close()

        # mode serveur : le passage de phase réécrit les réglages par l'API du serveur
        ctx, pg, errs = page(J(0), local=False); ss = gen(pg, BASE); wsa = ss["workouts"][0]["id"]; dis = slug(ss, "di")["id"]
        le(pg, J(28)); pg.click("[data-offer=phase] button:has-text('Accepter')"); time.sleep(1)
        st = pg.evaluate("fetch('/api/state').then(r => r.json())")
        ok(next(w for w in st["workouts"] if w["id"] == wsa)["settings"][str(dis)] == {"sets": 3, "target_min": 8, "target_max": 12, "rest": 90}, "mode serveur : passage en phase 2 enregistré par app.py")
        ok(not errs, f"aucune erreur JavaScript (serveur) {errs[:2]}"); ctx.close()

        # =============================================================== 2. semaine allégée (−20 %) ; 3. reprise en douceur (80 %)
        ctx, pg, errs = page(J(0)); s0 = gen(pg, prof(niveau="intermediaire")); wa, wb = [w["id"] for w in s0["workouts"]]; pc = slug(s0, "pc")["id"]
        tp = pg.evaluate("w => WO.find(x => x.id === w).settings", wa)[str(pc)]
        seances(pg, [J(k) for k in range(0, 91, 3)], [wa], pc, [[50, tp["target_min"]]] * 3)
        le(pg, J(34)); ok("allegee" not in offres(pg), "jour 34 : pas encore de semaine allégée")
        le(pg, J(35)); h = bouton_en_tete(pg, "semaine allégée proposée")
        ok(h["carte"] == ["allegee"] and "Semaine légère" in pg.inner_text("[data-offer=allegee]"), "jour 35 (5 semaines) : semaine allégée proposée")
        c0 = pg.evaluate(CONSEIL, [pc, wa]); ok("Conseil\u00a0: 50 kg ×" in c0 and "40 kg" not in c0, f"(témoin : avant, le conseil garde 50 kg) {c0.splitlines()[1]!r}")
        wo0 = pg.evaluate(ETAT)["workouts"]
        pg.click("[data-offer=allegee] button:has-text('Accepter')"); time.sleep(.5)
        c1 = pg.evaluate(CONSEIL, [pc, wa])
        ok(c1.splitlines()[1].startswith("Conseil\u00a0: 40 kg") and "(semaine légère)" in c1 and "environ 20\u00a0% de moins que 50 kg" in c1, f"semaine allégée : 40 kg proposés au lieu de 50 (−20 %) {c1.splitlines()[1]!r}")
        ok(pg.evaluate(ETAT)["workouts"] == wo0, "semaine allégée : programmes et réglages inchangés (même nombre de séances)")
        h = bouton_en_tete(pg, "semaine allégée en cours"); ok(h["carte"] == ["en cours:allegee"], "accueil : semaine allégée en cours, sous le bouton")
        sans_manquee(pg, "semaine allégée")
        le(pg, J(41)); ok("(semaine légère)" in pg.evaluate(CONSEIL, [pc, wa]), "jour 41 : semaine allégée toujours en cours (7 jours)")
        le(pg, J(42)); c2 = pg.evaluate(CONSEIL, [pc, wa])
        ok("semaine légère" not in c2 and "Conseil\u00a0: 50 kg" in c2 and "allegee" not in offres(pg), "jour 42 : la semaine allégée s'est terminée seule, conseil normal (base : séance d'avant)")
        le(pg, J(76)); ok("allegee" not in offres(pg), "jour 76 : pas de nouvelle semaine allégée (5 semaines après la fin de la précédente)")
        le(pg, J(77)); ok("allegee" in offres(pg), "jour 77 : semaine allégée reproposée (cycle suivant)")
        ok(not errs, f"aucune erreur JavaScript (semaine allégée) {errs[:2]}"); ctx.close()

        ctx, pg, errs = page(J(0)); s0 = gen(pg, prof(niveau="intermediaire")); wa = s0["workouts"][0]["id"]; pc = slug(s0, "pc")["id"]
        tp = pg.evaluate("w => WO.find(x => x.id === w).settings", wa)[str(pc)]
        seances(pg, [J(0), J(3), J(6), J(10)], [wa], pc, [[50, tp["target_min"]]] * 3)
        le(pg, J(17)); ok(offres(pg) == [], "dernière séance il y a 7 jours : rien à proposer")
        le(pg, J(18)); ok(offres(pg) == ["allegee"] and "Bon retour" in pg.inner_text("[data-offer=allegee]"), "il y a 8 jours (une semaine entière sans séance) : semaine allégée proposée, message positif")
        le(pg, J(30)); ok("reprise" not in offres(pg), "il y a 20 jours : pas de reprise")
        sans_manquee(pg, "20 jours sans séance")
        le(pg, J(31)); ok("reprise" not in offres(pg), "il y a 21 jours : pas de reprise")
        le(pg, J(32)); h = bouton_en_tete(pg, "reprise proposée")
        ok(offres(pg) == ["reprise"] and h["carte"] == ["reprise"] and "Bon retour !" in pg.inner_text("[data-offer=reprise]") and "On reprend à 80\u00a0% pendant 7 jours." in pg.inner_text("[data-offer=reprise]"), "il y a 22 jours : reprise en douceur proposée, « Bon retour ! On reprend à 80 % pendant 7 jours. »")
        sans_manquee(pg, "22 jours sans séance")
        pg.click("[data-offer=reprise] button:has-text('Accepter')"); time.sleep(.5)
        c1 = pg.evaluate(CONSEIL, [pc, wa])
        ok(c1.splitlines()[1].startswith("Conseil\u00a0: 40 kg") and "(reprise)" in c1 and "80\u00a0% de 50 kg" in c1, f"reprise : 80 % des charges (40 kg au lieu de 50) {c1.splitlines()[1]!r}")
        h = bouton_en_tete(pg, "reprise en cours"); ok(h["carte"] == ["en cours:reprise"], "accueil : reprise en cours, sous le bouton")
        pg.evaluate("go('seance')"); time.sleep(.2); ok("Reprise en douceur" in pg.inner_text("#app"), "onglet Séance : la reprise est annoncée")
        sans_manquee(pg, "reprise en cours")
        # « manquée » : le contrôle sait le trouver (témoin)
        pg.evaluate("document.getElementById('app').insertAdjacentHTML('beforeend', '<p>Séance manquée</p>')")
        ok(MANQUE.search(pg.inner_text("body")), "(témoin : le mot ajouté exprès est bien détecté)")
        ok(not errs, f"aucune erreur JavaScript (reprise) {errs[:2]}"); ctx.close()

        # =============================================================== 4. placement sur les jours
        ctx, pg, errs = page(J(0)); s0 = gen(pg, BASE); wa, wb = [w["id"] for w in s0["workouts"]]
        sem = lambda k: pg.evaluate("j => PROFIL.schedule(j).week.map(s => [s.day, s.wid])", J(k))
        ok(sem(0) == [[J(0), wa], [J(2), wb], [J(4), wa]], f"semaine 1 : lundi A, mercredi B, vendredi A {sem(0)}")
        ok(sem(7) == [[J(7), wb], [J(9), wa], [J(11), wb]], f"semaine 2 : lundi B, mercredi A, vendredi B {sem(7)}")
        h = bouton_en_tete(pg, "jour de séance")
        ok(h["titre"] == "Séance A" and "prévue aujourd’hui" in h["texte"] and "Jour de repos" not in h["texte"], "lundi : la séance prévue (Séance A) est proposée")
        le(pg, J(1)); h = bouton_en_tete(pg, "jour de repos")
        ok(h["titre"] == "Séance B" and "prévue demain" in h["texte"] and "Jour de repos : la récupération compte aussi" in h["texte"], "mardi (repos) : séance suivante en tête, ligne sur le repos dessous")
        sans_manquee(pg, "jour de repos")
        le(pg, J(2)); pg.evaluate(SEANCES, [{"day": J(2), "workout_id": wb, "entries": [{"exercise_id": slug(s0, "gs")["id"], "sets": [[20, 10]]}]}])
        h = accueil(pg); ok(h["titre"] == "Séance A" and "prévue vendredi" in h["texte"] and h["bouton"] == "Démarrer la séance", "mercredi, séance B faite : la suivante (vendredi, A) est proposée")
        le(pg, J(3)); ok(accueil(pg)["titre"] == "Séance A", "jeudi : toujours la séance de vendredi, rien n'est compté comme non fait")
        # tous les choix de jours possibles : jours choisis respectés, le moins possible de jours de suite pour un même groupe
        mk = """async ([n, l]) => { const ids = []; for (const [nom, sl] of l) { const r = await api('POST', '/api/workouts', {name: nom});
                  await api('PUT', '/api/workouts/' + r.id, {name: nom, items: sl.map(s => Object.values(EX).find(e => e.slug === s).id)}); ids.push(r.id); } await load(); return ids; }"""
        jeux = {"corps entier A/B": [wa, wb],
                "haut / bas": pg.evaluate(mk, [0, [["Haut", ["di", "tv", "rs"]], ["Bas", ["pc", "rdl", "lc"]]]]),
                "poussée / tirage / jambes / haut / bas": pg.evaluate(mk, [0, [["P", ["di", "de"]], ["T", ["tv", "rs"]], ["J", ["pc", "fentes"]], ["H", ["chest-press", "rowing-machine"]], ["B", ["gs", "rdl"]]]])}
        G = {k: [set(pg.evaluate("w => [...PROFIL._.groupsOf(w)]", w)) for w in ids] for k, ids in jeux.items()}
        NOMS = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]
        def seq(n, k, wk): return [((i + wk) % 2 if k == 2 and n % 2 else i % k) for i in range(n)]
        def conflits(c, n, k, g, wk):
            s, nx, z = seq(n, k, wk), seq(n, k, wk + 1), 0
            for i in range(n):
                gap = c[i + 1] - c[i] if i < n - 1 else c[0] + 7 - c[n - 1]
                a, bb = s[i], (s[i + 1] if i < n - 1 else nx[0])
                if gap == 1 and (a == bb or g[a] & g[bb]): z += 1
            return z
        hors, pire, cas, naif = [], [], 0, 0
        for nom, ids in jeux.items():
            k = len(ids)
            for n in ((2, 3) if k == 2 and nom.startswith("corps") else (4,) if k == 2 else (5,)):
                for r in range(n, 8):
                    for ch in itertools.combinations(range(7), r):
                        for wk in (0, 1):
                            o = {"answers": {"jours": [NOMS[d] for d in ch], "seances": n}}
                            pl = pg.evaluate("([o, p, m]) => PROFIL._.weekPlan(o, p, m)", [o, {"ids": ids, "start": J(0)}, J(7 * wk)])
                            got = [date.fromisoformat(x["day"]).weekday() for x in pl]; cas += 1
                            if not set(got) <= set(ch) or len(got) != n: hors.append((nom, ch, got)); continue
                            best = min(conflits(c, n, k, G[nom], wk) for c in itertools.combinations(ch, n))
                            if conflits(got, n, k, G[nom], wk) != best: pire.append((nom, ch, got))
                            if conflits(list(ch[:n]), n, k, G[nom], wk) > best: naif += 1
        ok(not hors, f"placement : {cas} cas, séances toujours sur des jours choisis, autant que de séances {hors[:2]}")
        ok(not pire, f"placement : jamais deux jours de suite pour un même groupe quand un autre choix l'évite {pire[:2]}")
        ok(naif > 50, f"(témoin : prendre simplement les premiers jours choisis mettrait un même groupe deux jours de suite dans {naif} cas évitables)")
        ok(G["haut / bas"][0].isdisjoint(G["haut / bas"][1]) and G["corps entier A/B"][0] & G["corps entier A/B"][1], "(groupes : haut et bas séparés, A et B partagent des muscles)")
        ok(not errs, f"aucune erreur JavaScript (placement) {errs[:2]}"); ctx.close()

        # profil importé sans questionnaire : ni phase ni placement, l'accueil garde « la séance qui suit la dernière faite »
        ctx, pg, errs = page(J(0)); exp0 = pg.evaluate("fetch('/api/export').then(r => r.json())"); exp0.pop("profil", None)
        w0 = exp0["workouts"]; exp0["sessions"] = [{"id": 1, "day": J(-2), "ts": 1, "workout_id": w0[0]["id"], "workout_name": w0[0]["name"], "notes": "", "entries": [{"exercise_id": w0[0]["items"][0], "sets": [[30, 10]]}]}]
        pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3); pg.fill("#bk", json.dumps(exp0)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1500)
        h = bouton_en_tete(pg, "profil importé sans questionnaire")
        ok(h["titre"] == w0[1]["name"] and pg.evaluate("PROFIL.schedule()") is None and pg.evaluate("PROFIL.coach().phase") is None and "phase" not in "".join(offres(pg)),
           f"profil importé : séance qui suit la dernière faite ({h['titre']}), ni placement ni phase")
        pg.evaluate("go('seance')"); time.sleep(.2); ok("Phase" not in pg.inner_text("#app"), "profil importé : l'onglet Séance n'annonce aucune phase")
        sans_manquee(pg, "profil importé")
        ok(not errs, f"aucune erreur JavaScript (importé) {errs[:2]}"); ctx.close()

        # =============================================================== 5. conseil de charge combiné
        ctx, pg, errs = page(J(0)); s0 = gen(pg, prof(niveau="intermediaire"))
        x = slug(s0, "chest-press")["id"]; pl_ = slug(s0, "pl")["id"]
        wa, wb = pg.evaluate("""async ([x, p]) => { const ids = []; for (const n of ['Test A', 'Test B']) { const r = await api('POST', '/api/workouts', {name: n});
          await api('PUT', '/api/workouts/' + r.id, {name: n, items: [x, p], settings: {[x]: {sets: 3, target_min: 10, target_max: 12, rest: 90}, [p]: {sets: 3, target_min: 30, target_max: 45, rest: 60}}}); ids.push(r.id); }
          await load(); return ids; }""", [x, pl_])
        def cas_(liste, light=None, nom=""):
            pg.evaluate(EFFACER)
            pr = pg.evaluate(PROFIL); pr["cycle"] = {"light": light or [], "later": {}}; pg.evaluate(SETP, pr)
            pg.evaluate(SEANCES, [{"day": j, "workout_id": w, "entries": [{"exercise_id": x, "sets": st, "effort": ef}]} for j, w, st, ef in liste])
            return pg.evaluate(CONSEIL, [x, wa])
        T = lambda n, reps, kg=40: [[kg, reps]] * n
        le(pg, J(20))
        c = cas_([(J(18), wa, T(3, 12), 3)])
        ok(c.splitlines()[1] == "Conseil\u00a0: 42,5 kg × 10" and "Toutes les séries au haut de la fourchette" in c, f"cahier des charges : 3 × 12 à 40 kg (fourchette 10-12) → 42,5 kg (pas de 2,5 kg déduit de l'historique) et retour à 10 reps {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, [[40, 11], [40, 12], [40, 12]], 3)]); ok(c.splitlines()[1] == "Conseil\u00a0: 40 kg × 12", "(témoin : une série sous le haut de la fourchette → garder 40 kg)")
        c = cas_([(J(15), wa, [[40, 8], [40, 9], [40, 10]], 3), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 3)])
        ok(c.splitlines()[1] == "Conseil\u00a0: 35-37,5 kg × 10" and "Deux séances de suite sous ta fourchette" in c, f"baisse : 2 séances de suite sous la fourchette → 35 à 37,5 kg (pas de 2,5 kg) {c.splitlines()[1]!r}")
        c = cas_([(J(15), wa, [[40, 9], [40, 9], [40, 10], [40, 10]], 3), (J(18), wa, [[40, 9], [40, 10], [40, 9], [40, 10]], 3)]); ok("35-37,5 kg" in c, "baisse : la moitié des séries sous la fourchette suffit")
        c = cas_([(J(15), wa, [[40, 12]] * 3, 3), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 3)]); ok("Deux séances de suite" not in c, "(témoin : une seule séance sous la fourchette → pas de baisse)")
        c = cas_([(J(15), wa, [[40, 9], [40, 10], [40, 10]], 3), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 3)]); ok("Deux séances de suite" not in c, "(témoin : un tiers des séries sous la fourchette → séance non comptée)")
        dl = [{"kind": "allegee", "start": J(13), "end": J(16)}]
        c = cas_([(J(15), wa, [[40, 8], [40, 8], [40, 10]], 3), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 3)], light=dl)
        ok("Deux séances de suite" not in c and "semaine légère" not in c, "séance de semaine allégée : ne compte pas pour la baisse")
        c = cas_([(J(15), wa, [[40, 8], [40, 8], [40, 10]], 3), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 3)], light=[{"kind": "reprise", "start": J(13), "end": J(16)}])
        ok("Deux séances de suite" not in c, "séance de reprise : ne compte pas pour la baisse")
        rep_ = [{"kind": "reprise", "start": J(19), "end": J(25)}]; all_ = [{"kind": "allegee", "start": J(19), "end": J(25)}]; rate = [(J(15), wa, [[40, 8], [40, 8], [40, 10]], 5), (J(18), wa, [[40, 8], [40, 8], [40, 10]], 5)]
        c = cas_(rate, light=rep_); ok(c.splitlines()[1].startswith("Conseil\u00a0: 32,5 kg") and "(reprise)" in c, f"priorité 1 : la reprise passe avant la baisse {c.splitlines()[1]!r}")
        c = cas_(rate, light=all_); ok(c.splitlines()[1].startswith("Conseil\u00a0: 32,5 kg") and "(semaine légère)" in c, f"priorité 2 : la semaine allégée passe avant la baisse {c.splitlines()[1]!r}")
        c = cas_(rate); ok(c.splitlines()[1].startswith("Conseil\u00a0: 35-37,5 kg"), f"priorité 3 : la baisse passe avant le ressenti 5 {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, T(3, 12), 5)]); ok(c.splitlines()[1] == "Conseil\u00a0: garde 40 kg" and "« dur »" in c, f"priorité 4 : ancien ressenti 5 (« à fond », lu « dur ») passe avant la montée {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, T(3, 12), 4)]); ok(c.splitlines()[1] == "Conseil\u00a0: garde 40 kg" and "« dur »" in c, f"priorité 4 : ressenti « Dur » (4) passe avant la montée (règle du 22/10/2026) {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, T(3, 12), 3)]); ok(c.splitlines()[1] == "Conseil\u00a0: 42,5 kg × 10", f"(témoin : ressenti « Juste bien » au haut de la fourchette → montée) {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, T(3, 10), 2)]); ok(c.splitlines()[1].startswith("Conseil\u00a0: 42,5 kg") and "Ressenti facile" in c, f"priorité 5 : ressenti 2, toutes les séries au minimum → montée {c.splitlines()[1]!r}")
        c = cas_([(J(18), wa, T(3, 9), 2)]); ok("on monte" not in c, "(témoin : ressenti 2 mais une série sous le minimum → pas de montée)")
        # « dernière fois » du même programme
        c = cas_([(J(15), wa, T(3, 10), 3), (J(18), wb, T(3, 10, 70), 3)])
        cb = pg.evaluate(CONSEIL, [x, wb]); cl = pg.evaluate("x => { const d = document.createElement('div'); d.innerHTML = advice(EX[x], null, null); return " + TXT + "; }", x)
        ok(c.startswith("Dernière\u00a0: 3 × 10 à 40 kg") and "Conseil\u00a0: 40 kg" in c, f"Test A : « dernière fois » et conseil d'après la dernière séance Test A (40 kg), pas la plus récente {c.splitlines()[0]!r}")
        ok(cb.startswith("Dernière\u00a0: 3 × 10 à 70 kg") and cl.startswith("Dernière\u00a0: 3 × 10 à 70 kg"), "Test B et séance libre : la plus récente (70 kg)")
        c = cas_([(J(18), wb, T(3, 10, 70), 3)]); ok(c.startswith("Dernière (Test B)\u00a0: 3 × 10 à 70 kg"), "Test A jamais fait : dernière séance de l'exercice, avec le nom de l'autre programme")
        cas_([(J(15), wa, T(3, 10), 3), (J(18), wb, T(3, 10, 70), 3)])
        pg.evaluate("go('seance')"); pg.evaluate(f"pickWorkout({wa})"); time.sleep(.3)
        ok(pg.input_value(f"#v{x}_0l") == "40" and "Dernière\u00a0: 3 × 10 à 40 kg" in pg.inner_text("#app"), "écran Séance Test A : lignes préremplies et « dernière fois » à 40 kg")
        # exercice en secondes : +5 à 10 s ou une série
        pg.evaluate(EFFACER); pg.evaluate(SEANCES, [{"day": J(18), "workout_id": wa, "entries": [{"exercise_id": pl_, "sets": [[None, 45]] * 3, "effort": 3}]}])
        c = pg.evaluate(CONSEIL, [pl_, wa]); ok(c.splitlines()[1] == "Conseil\u00a0: +5 à 10 s par série" and "Ou une série de plus" in c, f"exercice en secondes : +5 à 10 s ou une série {c.splitlines()[1]!r}")
        ok(not errs, f"aucune erreur JavaScript (conseil) {errs[:2]}"); ctx.close()

        # =============================================================== 6. IMC de 30 ou plus ; sécurité ; boutons de 44 px
        ctx, pg, errs = page(J(0))
        bad, tem = [], 0
        for ph in (1, 2, 3):
            for se in (2, 3, 5):
                for obj in ("muscle", "force", "endurance"):
                    n0 = pg.evaluate("([a, f]) => PROFIL._.plan(a, f).workouts.map(w => w.prm)", [prof(seances=se, objectif=obj), ph])
                    n1 = pg.evaluate("([a, f]) => PROFIL._.plan(a, f).workouts.map(w => w.prm)", [prof(seances=se, objectif=obj, poids=92.5), ph])
                    for w0_, w1_ in zip(n0, n1):
                        for sl, v in w0_.items():
                            if sl in w1_ and v["rest"] > 0:
                                tem += w1_[sl]["rest"] != v["rest"]
                                if w1_[sl]["rest"] != min(180, v["rest"] + 30): bad.append((ph, se, obj, sl, v["rest"], w1_[sl]["rest"]))
        ok(not bad and tem > 100, f"IMC 32 : repos +30 s, 3 min au plus, dans les 3 phases ({tem} repos allongés) {bad[:3]}")
        ok(pg.evaluate("a => PROFIL._.plan(a, 2).prm.rdl.rest", prof(objectif="force", niveau="intermediaire", poids=92.5)) == 180, "IMC 32, force : soulevé de terre roumain 180 s (150 + 30 plafonné à 180)")
        pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", prof(poids=92.5))
        pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); pg.evaluate(OUVRIR); t = pg.inner_text("#app")
        ok("Repos allongés de 30 s" in t and "IMC" not in t and "kcal" not in t, "IMC caché : repos allongés annoncés sans leur raison")
        pg.click("button:has-text('Afficher le détail santé')"); time.sleep(.2); pg.evaluate(OUVRIR)
        ok("IMC de 30 ou plus : repos allongés de 30 s" in pg.inner_text("#app"), "(témoin : détail affiché, la raison apparaît)")
        pg.click("button:has-text('Masquer le détail santé')"); time.sleep(.2)
        pg.click("button:has-text('Générer mon programme')"); time.sleep(.3); pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt")
        le(pg, J(28))
        vus = []
        for v in VUES:
            pg.evaluate(f"go('{v}')"); time.sleep(.15); pg.evaluate(OUVRIR)
            if "IMC" in pg.inner_text("body") or "kcal" in pg.inner_text("body"): vus.append(v)
        ok(not vus, f"IMC caché, jour 28 : ni « IMC » ni « kcal » sur aucun écran, carte de phase comprise {vus}")
        ok("phase2" in offres(pg), "(la carte de phase était bien proposée pendant ce contrôle)")
        # sécurité
        prot = []
        for nom, a in (("santé « Oui »", prof(objectif="endurance", seances=5, sante=dict(NON, tension=True))), ("moins de 18 ans", prof(objectif="endurance", seances=5, age=16)),
                       ("IMC 32", prof(objectif="endurance", seances=5, poids=92.5))):
            r = pg.evaluate("a => { const p = PROFIL._.plan(a, 3); return {items: p.workouts.flatMap(w => w.items.map(i => i.slug)), prm: p.workouts.flatMap(w => Object.entries(w.prm))}; }", a)
            if "intervalles" in r["items"]: prot.append((nom, "intervalles"))
            if nom != "IMC 32" and any(v["min"] < 8 for sl, v in r["prm"] if sl not in ("velo", "tapis-incline", "elliptique", "rameur", "stairmaster", "course", "intervalles")): prot.append((nom, "moins de 8"))
            if nom.startswith("santé") and any(v["sets"] != 2 for sl, v in r["prm"]  if sl not in ("velo", "tapis-incline", "elliptique", "rameur", "intervalles")): prot.append((nom, "séries"))
        ok(not prot, f"phase 3, profils protégés : cardio continu sans intervalles, 8 répétitions au moins, programme allégé avec « Oui » santé {prot[:3]}")
        ok("intervalles" in pg.evaluate("a => PROFIL._.plan(a, 3).workouts.flatMap(w => w.items.map(i => i.slug))", prof(objectif="endurance", seances=5)), "(témoin : sans protection, la séance « puissance et cardio » a des intervalles)")
        pl3 = pg.evaluate("a => PROFIL._.plan(a, 3).workouts.map(w => [w.name, w.type])", prof(seances=5))
        ok(pl3 == [["Poussée", "force"], ["Tirage", "volume"], ["Jambes", "puissance"], ["Haut du corps", "force"], ["Bas du corps", "volume"]], f"phase 3, 5 séances : force, volume, puissance, force, volume {pl3}")
        sw = pg.evaluate("""async () => { const r = await api('POST', '/api/exercises', {name: 'Kettlebell swing', grp: 'Jambes', kind: 'weight', sets: 3, target_min: 10, target_max: 15, rest: 60});
          await load(); const L = PROFIL._.LIB; L['kettlebell-swing'] = ['charniere', 'poly', ['halteres'], 1, 'faible', [], null]; const e = EX[r.id]; e.slug = 'kettlebell-swing';
          const u = (ph, kg) => { const x = PROFIL._.context(Object.assign({}, %s, {poids: kg}), ph); return PROFIL._.usable('kettlebell-swing', x); };
          const out = [u(1, 66), u(2, 66), u(3, 66), u(3, 92.5)]; delete L['kettlebell-swing']; return out; }""" % json.dumps(BASE))
        ok(sw == [False, False, True, False], f"kettlebell swing (ajouté pour l'essai) : refusé en phases 1 et 2 et avec un IMC de 30, accepté en phase 3 {sw}")
        # boutons ↑ ↓ ✕ de l'écran Programmes
        for w in (390, 360):
            pg.set_viewport_size({"width": w, "height": 844}); pg.evaluate("go('programmes')"); time.sleep(.3)
            bx = pg.evaluate("[...document.querySelectorAll('.li .mv')].map(b => { const r = b.getBoundingClientRect(); return [r.width, r.height]; })")
            ok(len(bx) >= 6 and all(a >= 44 and h_ >= 44 for a, h_ in bx), f"Programmes à {w} px : boutons ↑ ↓ ✕ d'au moins 44 × 44 px ({min(min(a, h_) for a, h_ in bx):.0f} px au plus petit)")
            ok(pg.evaluate("document.documentElement.scrollWidth <= innerWidth"), f"Programmes à {w} px : pas de défilement horizontal")
        ok(not errs, f"aucune erreur JavaScript (IMC, sécurité) {errs[:2]}"); ctx.close()

        # =============================================================== le mot « manquée » n'est dans aucun fichier de l'interface
        src = [f for f in os.listdir(os.path.join(APP, "static")) if f.endswith((".js", ".html")) and MANQUE.search(open(os.path.join(APP, "static", f), encoding="utf-8").read())]
        ok(not src, f"« manquée » absent du code de l'interface {src}")
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
