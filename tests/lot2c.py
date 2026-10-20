# SPDX-License-Identifier: AGPL-3.0-or-later
# Lot 2C, dates simulées (horloge de Playwright).
# Partie 1 : moins de texte, plus direct (le fonctionnement ne change pas) :
# - une carte de proposition (phase, semaine légère, reprise) : 25 mots visibles au plus hors « Détails » et hors boutons,
#   titre de 6 mots au plus, une seule phrase de 15 mots au plus ;
# - le bloc d'un exercice dans Séance affiche une seule ligne de conseil (ni rappel de phase, ni 1RM hors « Détails ») ;
# - les replis « Détails » sont fermés par défaut et leur bouton fait au moins 44 px de haut ;
# - toujours visibles, jamais dans un repli : avertissement médical et « Arrête l'exercice… » (résumé), « Consulte un médecin »
#   (santé « Oui »), messages de blessure, bouton « Démarrer la séance » en tête de l'accueil.
# Partie 2 : pas de série à perdre ; « séances au total » remplace « semaines d’affilée » (aucun chiffre de série à 0 après 22 jours sans séance).
# Partie 3 : séance C « puissance et cardio » ajoutée au passage en phase 3 avec 2 programmes (acceptation, « Plus tard », genoux,
# santé « Oui » et profils protégés, rotation A, B, C sur 3 semaines, séance C supprimée, Avancé, 5 séances, « Garder mes programmes »).
#   python3 tests/lot2c.py
import json, os, re, subprocess, sys, time
from datetime import date, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5143
env = dict(os.environ, DB_PATH="/tmp/lot2c.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/lot2c.db", "/tmp/lot2c.db-wal", "/tmp/lot2c.db-shm"):
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
SEANCES = "async l => { for (const s of l) await api('POST', '/api/sessions', s); await load(); R(); }"
# texte visible d'un élément hors replis « Détails » (et hors boutons si demandé) ; mots = suites qui contiennent une lettre ou un chiffre
VISIBLE = """([el, sansBoutons]) => { const c = el.cloneNode(true); c.querySelectorAll('details' + (sansBoutons ? ',button' : '')).forEach(x => x.remove());
  const h = document.createElement('div'); h.style.cssText = 'position:absolute;left:-9999px;width:358px'; h.appendChild(c); document.body.appendChild(h);
  const t = c.innerText; h.remove(); return t; }"""
mots = lambda t: len(re.findall(r"[\w’'\-,.]*[^\W_][\w’'\-,.]*", t))
phrases = lambda t: [p for p in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý«])", t.strip()) if p]

OUVRIR = "document.querySelectorAll('#app details').forEach(d => d.open = true)"
VUES = ["accueil", "seance", "progres", "jeu", "profil"]
# pour chaque largeur, « % » et « : » doivent être sur la même ligne que le caractère qui précède l'espace
COUPURE = """sel => { const el = document.querySelector(sel), b = el.querySelector('b'), tn = b.firstChild, s = tn.textContent, out = [];
  const top = i => { const r = document.createRange(); r.setStart(tn, i); r.setEnd(tn, i + 1); return Math.round(r.getBoundingClientRect().top); };
  for (let w = 360; w >= 100; w -= 2) { el.style.width = w + 'px';
    for (const ch of ['%', ':']) { const i = s.lastIndexOf(ch); if (i > 1 && top(i) !== top(i - 2)) out.push(w + ' px : « ' + ch + ' » seul'); } }
  el.style.width = ''; return out; }"""

def carte_ok(pg, sel, nom):
    """règles d'écriture d'une carte de proposition"""
    el = pg.locator(sel).first
    t = el.evaluate(VISIBLE.replace("([el, sansBoutons])", "(el)").replace("sansBoutons", "true"))
    h2 = el.locator("h2").inner_text() if el.locator("h2").count() else ""
    corps = t.replace(h2, "", 1).strip()
    n = mots(t)
    ok(n <= 25, f"{nom} : {n} mots visibles hors « Détails » et hors boutons (25 au plus) {t!r}")
    ok(mots(h2) <= 6, f"{nom} : titre de {mots(h2)} mots (6 au plus) {h2!r}")
    ok(len(phrases(corps)) <= 1 and mots(corps) <= 15, f"{nom} : une seule phrase de 15 mots au plus {corps!r}")
    ok(not re.search(r"\(", corps), f"{nom} : pas de parenthèse explicative")
    return t

def details_fermes(pg, nom):
    r = pg.evaluate("""() => [...document.querySelectorAll('#app details')].map(d => ({open: d.open, h: d.querySelector('summary').getBoundingClientRect().height, s: d.querySelector('summary').textContent}))""")
    ok(r and all(not d["open"] for d in r), f"{nom} : {len(r)} replis, tous fermés par défaut")
    ok(all(d["h"] >= 44 for d in r), f"{nom} : boutons des replis d'au moins 44 px ({sorted({round(d['h']) for d in r})})")

def bloc_exercice(pg, nom):
    """chaque bloc d'exercice de l'écran Séance : une seule ligne de conseil visible"""
    blocs = pg.locator("#app .card:has(input[id^=v])")
    res = []
    for i in range(blocs.count()):
        el = blocs.nth(i)
        t = el.evaluate(VISIBLE.replace("([el, sansBoutons])", "(el)").replace("sansBoutons", "false"))
        sug = el.evaluate("el => [...el.querySelectorAll('.sug')].filter(s => !s.closest('details')).length")
        lignes = [l for l in t.splitlines() if l.startswith("Conseil") or re.search(r"jamais jusqu|1RM|Garde |vise |passe à|Semaine légère :|Reprise en douceur :", l)]
        res.append((el.locator("h2").inner_text(), sug, lignes))
    mauvais = [r for r in res if r[1] != 1 or len(r[2]) != 1]
    ok(res and not mauvais, f"{nom} : {len(res)} blocs d'exercice, une seule ligne de conseil chacun {mauvais[:2] or res[:1]}")
    return res

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        def page(jour, w=390):
            ctx = b.new_context(viewport={"width": w, "height": 844})
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time(jour + "T10:00:00")
            pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector("#app .card", timeout=8000); time.sleep(.3)
            return ctx, pg, errs
        def le(pg, jour, vue="accueil"):
            pg.clock.set_fixed_time(jour + "T10:00:00"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000)
            pg.evaluate(f"go('{vue}')"); time.sleep(.3)
        def resume(pg, a):
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: !!localStorage.getItem('muscu-profil')}))", a)
            pg.reload(); pg.wait_for_selector("#app .card"); pg.evaluate("localStorage.getItem('muscu-profil') && (go('profil'), PROFIL.redo())")   # profil existant : « Reprendre le questionnaire »
            pg.wait_for_selector("button:has-text('Générer mon programme')"); time.sleep(.2)
        def gen(pg, a):
            resume(pg, a); pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
            pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            pg.evaluate("go('accueil')"); time.sleep(.2)
            return pg.evaluate("fetch('/api/state').then(r => r.json())")
        def visible(pg, sel="#app"): return pg.locator(sel).first.evaluate(VISIBLE.replace("([el, sansBoutons])", "(el)").replace("sansBoutons", "false"))

        # =============================================================== Bienvenue, résumé, confirmation
        ctx, pg, errs = page(J(0))
        t = visible(pg)
        ok("17 questions, 3 minutes" in t and "Commencer" in t and "J’ai une sauvegarde" in t and "Ce n’est pas un avis médical." in t, f"Bienvenue : phrase, deux boutons, ligne d'avertissement ({mots(t)} mots)")
        ok(mots(t) <= 35, f"Bienvenue : {mots(t)} mots visibles (35 au plus)")
        resume(pg, prof(blessures=["genoux"]))
        t = visible(pg)
        ok("ne remplace pas un avis médical" in t and "Arrête l’exercice en cas de douleur vive, de vertige ou de gêne à la poitrine." in t, "résumé : avertissement médical visible, hors repli")
        ok("aucun exercice de ce type ne convient à ta blessure aux genoux" in t, "résumé : message de blessure visible, hors repli")
        puces = pg.locator("#app .card:has(h2:text-is('Ton programme')) > ul.qul > li").count()
        ok(1 <= puces <= 3, f"résumé : « Ton programme » en {puces} puces (3 au plus)")
        ok(pg.locator("#app details:has(summary:text-is('Tes réponses'))").count() == 1, "résumé : « Tes réponses » est un repli")
        details_fermes(pg, "résumé")
        pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
        t = visible(pg)
        ok(all(pg.locator(f"#app button:has-text('{x}')").is_visible() for x in ("Remplacer mes programmes", "Garder mes programmes", "Annuler")), "confirmation : les trois boutons restent visibles")
        ok("Développé incliné haltères" in t and " × " not in t and "repos" not in t, "confirmation : noms d'exercices visibles, réglages dans « Détails »")
        details_fermes(pg, "confirmation")
        pg.click("button:has-text('Annuler')"); time.sleep(.2)
        resume(pg, prof(sante=dict(NON, coeur=True)))
        t = visible(pg)
        ok("Consulte un médecin avant de commencer." in t, "santé « Oui » : « Consulte un médecin » visible, hors repli")
        ok(not errs, f"aucune erreur JavaScript (questionnaire) {errs[:2]}"); ctx.close()

        # =============================================================== accueil et cartes de proposition, écran Séance
        ctx, pg, errs = page(J(0)); s = gen(pg, BASE); wa, wb = [w["id"] for w in s["workouts"]]
        ex = {e["slug"]: e["id"] for e in s["exercises"]}
        jours = [0, 2, 4, 7, 9, 11, 14, 16, 18, 21]
        pg.evaluate(SEANCES, [{"day": J(k), "workout_id": [wa, wb][i % 2], "entries": [{"exercise_id": ex["pc"], "sets": [[50, 10]] * 3, "effort": 3},
                              {"exercise_id": ex["di"] if i % 2 == 0 else ex["de"], "sets": [[16, 12]] * 3, "effort": 3}]} for i, k in enumerate(jours)])
        le(pg, J(23))
        h = visible(pg, "#app .hero")
        ok("6 exercices · prévue aujourd’hui" in h and "Dernière : il y a 2 j" in h and "Démarrer la séance" in h, f"accueil, jour de séance : carte courte {h!r}")
        ok(pg.evaluate("document.getElementById('app').firstElementChild.classList.contains('hero')"), "accueil : « Démarrer la séance » en tête")
        le(pg, J(28), "seance"); pg.evaluate(f"pickWorkout({wa})"); time.sleep(.3)
        r = bloc_exercice(pg, "Séance, phase 1")
        ok(any(l == ["Conseil\u00a0: 50 kg × 12"] for _, _, l in r), f"Séance : conseil chiffré sur une ligne {r[:1]}")
        ok("jamais jusqu’à l’échec" in pg.text_content("#app") and "jamais jusqu’à l’échec" not in visible(pg), "Séance : rappel de phase 1 présent, mais dans « Détails »")
        ok("1RM" in pg.text_content("#app") and "1RM" not in visible(pg), "Séance : 1RM sorti de l'écran, dans « Détails »")
        details_fermes(pg, "Séance")
        pg.evaluate("startFocus()"); time.sleep(.3)
        t = visible(pg, ".focus"); ok(t.count("Conseil") == 1 and "1RM" not in t, "mode focus : une seule ligne de conseil")
        pg.evaluate("exitFocus()")
        le(pg, J(28)); carte_ok(pg, "[data-offer=phase]", "carte « Phase 2 prête »")
        ok(pg.inner_text("[data-offer=phase] h2") == "Phase 2 prête" and "Charges un peu plus lourdes : 3 × 8-12." in pg.inner_text("[data-offer=phase]"), "carte de phase 2 : titre et phrase")
        details_fermes(pg, "accueil avec carte de phase")
        pg.evaluate("go('profil')"); time.sleep(.3)
        carte_ok(pg, "[data-offer=phase]", "Mon profil, carte de phase")
        puces = pg.locator("#app .card:has(h2:text-is('Ton programme')) > ul.qul > li").count()
        ok(1 <= puces <= 3 and pg.locator("#app details:has(summary:text-is('Tes réponses'))").count() == 1, f"Mon profil : {puces} puces, « Tes réponses » en repli")
        details_fermes(pg, "Mon profil")
        pg.evaluate("go('accueil')"); time.sleep(.2); pg.click("[data-offer=phase] button:has-text('Plus tard')"); time.sleep(.3)
        le(pg, J(35)); carte_ok(pg, "[data-offer=allegee]", "carte « Semaine légère ? »")
        pg.click("[data-offer=allegee] button:has-text('Accepter')"); time.sleep(.4)
        t = carte_ok(pg, "[data-light]", "semaine légère en cours")
        ok(re.fullmatch(r"Semaine légère jusqu’au [a-z]{3}\. \d\d/\d\d\u00a0: −20\u00a0%", t.strip()) is not None, f"semaine légère en cours : une ligne, espaces insécables avant « : » et « % » {t.strip()!r}")
        # « % » et « : » jamais seuls en début de ligne : la carte est rétrécie de 360 à 100 px, 2 px par 2 px
        seuls = pg.evaluate(COUPURE, "[data-light]")
        ok(not seuls, f"semaine légère en cours : « % » et « : » restent sur la ligne de la valeur, de 100 à 360 px de large {seuls[:3]}")
        vus, petits = [], []
        for v in VUES:
            pg.evaluate(f"go('{v}')" + ("; JEU.sub('regles')" if v == "jeu" else "")); time.sleep(.2); pg.evaluate(OUVRIR)   # Esprits : les taux sont dans « Règles »
            vus += [f"{v} : …{m.group(0)}" for m in re.finditer(r".{0,25}[^\S\u00a0][%]", pg.inner_text("#app"))]
            petits += pg.evaluate("v => [...document.querySelectorAll('#app button, #app summary')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => v + ' : ' + e.innerText.trim().slice(0, 20) + ' (' + Math.round(e.getBoundingClientRect().height) + ' px)')", v)
        ok(not vus, f"aucun « % » précédé d'une espace sécable (accueil, Séance, Progrès, Esprits > Règles, Mon profil, replis ouverts) {vus[:3]}")
        ok(not petits, f"tous les boutons visibles font au moins 44 px de haut (accueil, Séance, Progrès, Esprits > Règles, Mon profil) {petits[:4]}")
        le(pg, J(35), "seance"); pg.evaluate(f"pickWorkout({wa})"); time.sleep(.3)
        r = bloc_exercice(pg, "Séance, semaine légère")
        ok(any(l == ["Conseil\u00a0: 40 kg × 10 (semaine légère)"] for _, _, l in r), f"Séance, semaine légère : « Conseil : 40 kg × 10 (semaine légère) » {r[:1]}")
        ok(not errs, f"aucune erreur JavaScript (accueil, Séance) {errs[:2]}"); ctx.close()

        # reprise (22 jours sans séance) et semaine légère après une pause (8 jours)
        ctx, pg, errs = page(J(0)); s = gen(pg, BASE); wa = s["workouts"][0]["id"]; pc = next(e["id"] for e in s["exercises"] if e["slug"] == "pc")
        pg.evaluate(SEANCES, [{"day": J(k), "workout_id": wa, "entries": [{"exercise_id": pc, "sets": [[50, 10]] * 3, "effort": 3}]} for k in (0, 2, 4)])
        le(pg, J(12)); carte_ok(pg, "[data-offer=allegee]", "carte « Bon retour ! » (semaine légère après une pause)")
        # partie 2 : pas de série à perdre. Après 22 jours sans séance, aucun compteur de série à 0 ; « séances au total » ne baisse jamais
        le(pg, J(26))
        tu = pg.evaluate("() => [...document.querySelectorAll('#app .tiles > div')].map(d => [d.querySelector('b').textContent.trim(), d.querySelector('span').textContent.trim()])")
        zero = [x for x in tu if x[0] == "0" and re.search(r"affil|série|semaine|record", x[1], re.I)]
        ok(["3", "séances au total"] in tu and not zero, f"22 jours sans séance : « 3 séances au total » à l'accueil, aucun chiffre de série à 0 {tu}")
        vus = []
        for v in ("accueil", "progres", "seance"):
            pg.evaluate(f"go('{v}')"); time.sleep(.2); pg.evaluate("document.querySelectorAll('#app details').forEach(d => d.open = true)")
            if re.search(r"affilée|Série à lancer", pg.inner_text("body")): vus.append(v)
        ok(not vus, f"plus de « semaines d'affilée » ni de « Série à lancer » (accueil, Progrès, Séance) {vus}")
        ok("3 séances au total" in pg.evaluate("go('progres'), document.getElementById('app').innerText"), "Progrès : « 3 séances au total »")
        pg.evaluate("go('accueil')"); time.sleep(.2)
        t = carte_ok(pg, "[data-offer=reprise]", "carte « Bon retour ! » (reprise)")
        ok("Bon retour !" in t and "On reprend à 80\u00a0% pendant 7 jours." in t, "reprise : titre et phrase")
        pg.click("[data-offer=reprise] button:has-text('Accepter')"); time.sleep(.4); carte_ok(pg, "[data-light]", "reprise en cours")
        ok(not errs, f"aucune erreur JavaScript (reprise) {errs[:2]}"); ctx.close()

        # phase 3 (intermédiaire : phase 2 d'emblée, phase 3 en semaine 13)
        ctx, pg, errs = page(J(0)); s = gen(pg, prof(niveau="intermediaire", seances=2, jours=["lun", "jeu"])); wa, wb = [w["id"] for w in s["workouts"]]
        pc = next(e["id"] for e in s["exercises"] if e["slug"] == "pc")
        pg.evaluate(SEANCES, [{"day": J(k), "workout_id": [wa, wb][i % 2], "entries": [{"exercise_id": pc, "sets": [[50, 10]] * 3, "effort": 3}]} for i, k in enumerate(range(0, 84, 7))])
        le(pg, J(84), "profil"); carte_ok(pg, "[data-offer=phase]", "carte « Phase 3 prête »")   # dans « Mon profil » : la semaine légère passe avant sur l'accueil
        ok(not errs, f"aucune erreur JavaScript (phase 3) {errs[:2]}"); ctx.close()

        # =============================================================== partie 3 : séance C « puissance et cardio » en phase 3
        ETAT = "fetch('/api/state').then(r => r.json()).then(s => ({ex: s.exercises.map(e => { const o = Object.assign({}, e); delete o.used; return o; }), sessions: s.sessions, workouts: s.workouts}))"
        PROF = "JSON.parse(localStorage.getItem('muscu-profil'))"
        LIB = None
        def jusqua_phase3(a):
            """programme généré (intermédiaire : phase 2 d'emblée), une séance par semaine, puis le jour 84 (phase 3 proposée)"""
            ctx, pg, errs = page(J(0)); s = gen(pg, a); wa, wb = [w["id"] for w in s["workouts"]]
            pc = next(e["id"] for e in s["exercises"] if e["slug"] in ("pc", "gs", "pompes"))
            pg.evaluate(SEANCES, [{"day": J(k), "workout_id": [wa, wb][i % 2], "entries": [{"exercise_id": pc, "sets": [[50, 10]] * 3, "effort": 3}]} for i, k in enumerate(range(0, 84, 7))])
            le(pg, J(84), "profil")
            return ctx, pg, errs, wa, wb
        def reglage(st, wid, slug):
            w = next(w for w in st["workouts"] if w["id"] == wid); e = next(e for e in st["ex"] if e["slug"] == slug)
            v = w["settings"].get(str(e["id"])); return v and [v["sets"], v["target_min"], v["target_max"], v["rest"]]
        A2 = prof(niveau="intermediaire", seances=2, jours=["lun", "jeu"])

        # acceptation : 3 programmes, rôles et réglages corrects ; rien d'autre ne change
        ctx, pg, errs, wa, wb = jusqua_phase3(A2)
        LIB = pg.evaluate("PROFIL._.LIB")
        t = pg.inner_text("[data-offer=phase]")
        ok("Phase 3 prête" in t and "Une 3e séance s’ajoute : puissance et cardio." in t, f"carte de phase 3 : « Phase 3 prête », « Une 3e séance s’ajoute : puissance et cardio. » {t[:90]!r}")
        pg.evaluate(OUVRIR); d = pg.inner_text("[data-offer=phase] details")
        lignes = [l.strip() for l in d.splitlines() if l.strip() and l.strip() != "Détails"]
        n_c = pg.locator("[data-offer=phase] details ul.qnames li").count()
        ok(lignes[0] == "Séance C\u00a0: puissance et cardio" and n_c >= 4 and lignes[1:1 + n_c] == [l.strip() for l in pg.locator("[data-offer=phase] details ul.qnames li").all_inner_texts()]
           and lignes[1 + n_c:] == ["A\u00a0: force · B\u00a0: volume et endurance · C\u00a0: puissance et cardio", "Ton historique reste le même."],
           f"Détails de « Phase 3 prête » : liste de la séance C ({n_c} exercices), une ligne par séance, l'historique, rien d'autre {lignes[:1] + lignes[1 + n_c:]}")
        ok("bravo" not in d and "Tes semaines" not in d and "gardent leurs exercices" not in d and "hybride" not in d, "Détails de « Phase 3 prête » : l'ancien long texte a disparu")
        avant = pg.evaluate(ETAT)
        pg.click("[data-offer=phase] button:has-text('Accepter')"); pg.wait_for_timeout(1200)
        apres = pg.evaluate(ETAT); pr = pg.evaluate(PROF)["program"]
        ok([w["name"] for w in apres["workouts"]] == ["Séance A", "Séance B", "Séance C"], f"« Accepter » : 3 programmes {[w['name'] for w in apres['workouts']]}")
        wc = apres["workouts"][2]["id"]
        ok(pr["phase"] == 3 and pr["ids"] == [wa, wb, wc] and pr["extra"] == wc and pr["rot"] == J(84), f"profil : phase 3, programmes suivis A, B, C {pr['ids']}, séance C marquée")
        ok(apres["ex"] == avant["ex"] and apres["sessions"] == avant["sessions"] and [w["items"] for w in apres["workouts"][:2]] == [w["items"] for w in avant["workouts"]],
           "« Accepter » : catalogue, historique et exercices de A et B inchangés")
        ok(reglage(apres, wa, "di") == [4, 4, 6, 150] and reglage(apres, wb, "de") == [3, 10, 12, 75], f"A = force (4 × 4-6, 150 s), B = volume (3 × 10-12, 75 s) {reglage(apres, wa, 'di')} {reglage(apres, wb, 'de')}")
        c = apres["workouts"][2]; exs = {e["id"]: e for e in apres["ex"]}; sl = [exs[i]["slug"] for i in c["items"]]
        force_ = [x for x in sl if LIB[x][0] != "cardio"]
        ok(len(force_) == 6 and all(LIB[x][1] == "poly" and LIB[x][0] != "tronc" for x in force_), f"C : corps entier, 6 exercices polyarticulaires pour 60 min ({force_})")
        ok({LIB[x][0].split("-")[0] for x in force_} >= {"squat", "poussee", "tirage", "charniere"}, "C : jambes, poussée, tirage et charnière (corps entier)")
        bon = all(reglage(apres, wc, x) == ([4, 3, 5, 150] if LIB[x][0] == "charniere" else [4, 3, 5, 120]) for x in force_)
        ok(bon, f"C = puissance et cardio : 4 × 3-5, repos 120 s (charnière 150 s) {[reglage(apres, wc, x) for x in force_][:3]}")
        ok(sl[-1] == "intervalles" and reglage(apres, wc, "intervalles") == [1, 20, 20, 0], f"C : cardio à la fin, durée haute (20 min), intervalles pour l'objectif athlétique ({sl[-1]})")
        # rotation A, B, C sur 3 semaines (lundi et jeudi), qui continue d'une semaine à l'autre
        o = pg.evaluate(PROF); nom = {wa: "A", wb: "B", wc: "C"}
        sem = [[nom[x["wid"]] for x in pg.evaluate("([o, m]) => PROFIL._.weekPlan(o, o.program, m)", [o, J(84 + 7 * k)])] for k in range(3)]
        ok(sem == [["A", "B"], ["C", "A"], ["B", "C"]], f"rotation sur 3 semaines : A B | C A | B C {sem}")
        s3 = [[nom[x["wid"]] for x in pg.evaluate("([o, m]) => PROFIL._.weekPlan(Object.assign({}, o, {answers: Object.assign({}, o.answers, {seances: 3, jours: ['lun', 'mer', 'ven']})}), o.program, m)", [o, J(84 + 7 * k)])] for k in range(2)]
        s4 = [[nom[x["wid"]] for x in pg.evaluate("([o, m]) => PROFIL._.weekPlan(Object.assign({}, o, {answers: Object.assign({}, o.answers, {seances: 4, jours: ['lun', 'mar', 'jeu', 'ven']})}), o.program, m)", [o, J(84 + 7 * k)])] for k in range(2)]
        ok(s3 == [["A", "B", "C"], ["A", "B", "C"]] and s4 == [["A", "B", "C", "A"], ["B", "C", "A", "B"]], f"rotation avec 3 et 4 séances par semaine {s3} {s4}")
        le(pg, J(87)); h = pg.inner_text("#app .hero h2")
        ok(h == "Séance B", f"jeudi de la semaine 13 : l'accueil propose la séance B ({h})")
        # séance C supprimée par l'utilisateur : la rotation revient à A, B ; phase et historique intacts
        pg.evaluate(f"api('DELETE', '/api/workouts/{wc}').then(load)"); pg.wait_for_timeout(400); o = pg.evaluate(PROF)
        sem = [[nom[x["wid"]] for x in pg.evaluate("([o, m]) => PROFIL._.weekPlan(o, Object.assign({}, o.program, {ids: o.program.ids.slice(0, 2)}), m)", [o, J(91 + 7 * k)])] for k in range(2)]
        ok(pg.evaluate("PROFIL.coach().phase") == 3 and [nom[x["wid"]] for x in pg.evaluate("PROFIL.schedule().week")] in (["A", "B"], ["B", "A"]) and sem == [["A", "B"], ["A", "B"]],
           f"séance C supprimée : la rotation revient à A, B, phase 3 gardée {sem}")
        ok(not errs, f"aucune erreur JavaScript (séance C) {errs[:2]}"); ctx.close()

        # « Plus tard » : rien ne change
        ctx, pg, errs, wa, wb = jusqua_phase3(A2)
        avant = pg.evaluate(ETAT); p0 = pg.evaluate(PROF)["program"]
        pg.click("[data-offer=phase] button:has-text('Plus tard')"); pg.wait_for_timeout(600)
        ok(pg.evaluate(ETAT) == avant and pg.evaluate(PROF)["program"] == p0, "« Plus tard » : aucun programme ajouté, aucun réglage changé, profil du programme identique")
        ok(not errs, f"aucune erreur JavaScript (« Plus tard ») {errs[:2]}"); ctx.close()

        # blessure aux genoux : C sans exercice déconseillé (par l'acceptation, puis sur 36 combinaisons du générateur)
        ctx, pg, errs, wa, wb = jusqua_phase3(prof(niveau="intermediaire", seances=2, jours=["lun", "jeu"], blessures=["genoux"]))
        pg.click("[data-offer=phase] button:has-text('Accepter')"); pg.wait_for_timeout(1200)
        st = pg.evaluate(ETAT); c = st["workouts"][-1]; exs = {e["id"]: e for e in st["ex"]}; sl = [exs[i]["slug"] for i in c["items"]]
        ok(c["name"] == "Séance C" and len(sl) >= 4 and not [x for x in sl if "genoux" in LIB[x][5]], f"genoux, acceptation : séance C sans exercice déconseillé ({sl})")
        GEN = "([a, ph]) => PROFIL._.plan(a, ph).workouts.map(w => ({name: w.name, items: w.items.map(p => p.slug)}))"
        viol, n, temoin = [], 0, 0
        for se in (2, 3, 4):
            for lieu in ("complete", "machines", "halteres", "pdc"):
                for d in (30, 60, 75):
                    ws = pg.evaluate(GEN, [prof(seances=se, lieu=lieu, duree=d, niveau="avance", blessures=["genoux"]), 3]); n += 1
                    cc = [w for w in ws if w["name"] == "Séance C"]; viol += [(se, lieu, d, x) for w in cc for x in w["items"] if "genoux" in LIB[x][5] or (LIB[x][0] != "cardio" and LIB[x][1] != "poly")]
                    w0 = [w for w in pg.evaluate(GEN, [prof(seances=se, lieu=lieu, duree=d, niveau="avance"), 3]) if w["name"] == "Séance C"]
                    temoin += any("genoux" in LIB[x][5] for w in w0 for x in w["items"])
        ok(not viol, f"genoux : séance C sans exercice déconseillé ni isolation, {n} programmes {viol[:3]}")
        ok(temoin >= n // 2, f"(témoin : sans blessure, la séance C contient bien ces exercices : {temoin}/{n})")
        # santé « Oui » et autres profils protégés : C sans intervalles
        prot = {"santé « Oui »": dict(sante=dict(NON, coeur=True)), "moins de 18 ans": dict(age=16), "IMC 32": dict(poids=92.5)}
        for nom_, k in prot.items():
            bad = [(o_, se) for o_ in ("endurance", "athletique") for se in (2, 4) for w in pg.evaluate(GEN, [prof(objectif=o_, seances=se, niveau="avance", **k), 3])
                   if w["name"] == "Séance C" and ("intervalles" in w["items"] or "course" in w["items"] or not w["items"] or w["items"][-1] not in LIB or LIB[w["items"][-1]][0] != "cardio")]
            ok(not bad, f"{nom_} : séance C sans intervalles, cardio continu et facile à la fin {bad[:2]}")
        t_ = [w["items"][-1] for w in pg.evaluate(GEN, [prof(objectif="endurance", niveau="avance"), 3]) if w["name"] == "Séance C"]
        ok(t_ == ["intervalles"], f"(témoin : sans profil protégé, objectif endurance → intervalles en fin de séance C {t_})")
        t_ = [w["items"][-1] for w in pg.evaluate(GEN, [prof(objectif="muscle", niveau="avance"), 3]) if w["name"] == "Séance C"]
        ok(t_ and t_[0] != "intervalles", f"objectif muscle : pas d'intervalles en séance C ({t_})")
        ok(not errs, f"aucune erreur JavaScript (blessures, santé) {errs[:2]}"); ctx.close()

        # Avancé : A, B et C dès la génération ; 5 séances : rien ne change ; « Garder mes programmes » : pas de séance C
        ctx, pg, errs = page(J(0)); s = gen(pg, prof(niveau="avance", seances=2, jours=["lun", "jeu"])); pr = pg.evaluate(PROF)["program"]
        ok([w["name"] for w in s["workouts"]] == ["Séance A", "Séance B", "Séance C"] and pr["phase"] == 3 and pr["ids"] == [w["id"] for w in s["workouts"]] and pr["extra"] == s["workouts"][2]["id"],
           f"Avancé, 2 séances : A, B et C dès la génération {[w['name'] for w in s['workouts']]}")
        st = pg.evaluate(ETAT); wa, wb, wc = [w["id"] for w in s["workouts"]]
        ok(reglage(st, wa, "di") == [4, 4, 6, 150] and reglage(st, wb, "de") == [3, 10, 12, 75], "Avancé : A = force, B = volume")
        s = gen(pg, prof(niveau="avance", seances=4, jours=["lun", "mar", "jeu", "ven"]))
        ok([w["name"] for w in s["workouts"]] == ["Haut du corps", "Bas du corps", "Séance C"], f"Avancé, 4 séances : Haut, Bas et C {[w['name'] for w in s['workouts']]}")
        s = gen(pg, prof(niveau="avance", seances=5, jours=["lun", "mar", "mer", "jeu", "ven"]))
        ok([w["name"] for w in s["workouts"]] == ["Poussée", "Tirage", "Jambes", "Haut du corps", "Bas du corps"], "Avancé, 5 séances : rien ne change, pas de séance C")
        n0 = len(s["workouts"]); resume(pg, prof(niveau="avance", seances=2, jours=["lun", "jeu"])); pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
        ok(pg.locator("#app h2:has-text('Séance C')").count() == 1, "confirmation d'un profil Avancé : la séance C est annoncée")
        pg.click("button:has-text('Garder mes programmes')"); time.sleep(.4)
        ok(len(pg.evaluate(ETAT)["workouts"]) == n0, "« Garder mes programmes » : aucune séance C ajoutée")
        ok(not errs, f"aucune erreur JavaScript (Avancé) {errs[:2]}"); ctx.close()

        # 360 px : pas de défilement horizontal sur les écrans allégés
        ctx, pg, errs = page(J(0), 360); gen(pg, BASE); larges = []
        for v in ("accueil", "seance", "profil"):
            pg.evaluate(f"go('{v}')"); time.sleep(.2)
            if pg.evaluate("document.documentElement.scrollWidth > innerWidth"): larges.append(v)
        ok(not larges, f"360 px : pas de défilement horizontal {larges}"); ctx.close()
finally:
    srv.terminate()
print("\n" + (f"{len(fails)} ÉCHEC(S)" if fails else "Tout est OK"))
sys.exit(1 if fails else 0)
