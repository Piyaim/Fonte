# SPDX-License-Identifier: AGPL-3.0-or-later
# Lot 2C, partie 1 : moins de texte, plus direct (le fonctionnement ne change pas). Dates simulées (horloge de Playwright).
# - une carte de proposition (phase, semaine légère, reprise) : 25 mots visibles au plus hors « Détails » et hors boutons,
#   titre de 6 mots au plus, une seule phrase de 15 mots au plus ;
# - le bloc d'un exercice dans Séance affiche une seule ligne de conseil (ni rappel de phase, ni 1RM hors « Détails ») ;
# - les replis « Détails » sont fermés par défaut et leur bouton fait au moins 44 px de haut ;
# - toujours visibles, jamais dans un repli : avertissement médical et « Arrête l'exercice… » (résumé), « Consulte un médecin »
#   (santé « Oui »), messages de blessure, bouton « Démarrer la séance » en tête de l'accueil.
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
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", a)
            pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); time.sleep(.2)
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
        ok(any(l == ["Conseil : 50 kg × 12"] for _, _, l in r), f"Séance : conseil chiffré sur une ligne {r[:1]}")
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
        ok(re.fullmatch(r"Semaine légère jusqu’au [a-z]{3}\. \d\d/\d\d : −20 %", t.strip()) is not None, f"semaine légère en cours : une ligne {t.strip()!r}")
        le(pg, J(35), "seance"); pg.evaluate(f"pickWorkout({wa})"); time.sleep(.3)
        r = bloc_exercice(pg, "Séance, semaine légère")
        ok(any(l == ["Conseil : 40 kg × 10 (semaine légère)"] for _, _, l in r), f"Séance, semaine légère : « Conseil : 40 kg × 10 (semaine légère) » {r[:1]}")
        ok(not errs, f"aucune erreur JavaScript (accueil, Séance) {errs[:2]}"); ctx.close()

        # reprise (22 jours sans séance) et semaine légère après une pause (8 jours)
        ctx, pg, errs = page(J(0)); s = gen(pg, BASE); wa = s["workouts"][0]["id"]; pc = next(e["id"] for e in s["exercises"] if e["slug"] == "pc")
        pg.evaluate(SEANCES, [{"day": J(k), "workout_id": wa, "entries": [{"exercise_id": pc, "sets": [[50, 10]] * 3, "effort": 3}]} for k in (0, 2, 4)])
        le(pg, J(12)); carte_ok(pg, "[data-offer=allegee]", "carte « Bon retour ! » (semaine légère après une pause)")
        le(pg, J(26)); t = carte_ok(pg, "[data-offer=reprise]", "carte « Bon retour ! » (reprise)")
        ok("Bon retour !" in t and "On reprend à 80 % pendant 7 jours." in t, "reprise : titre et phrase")
        pg.click("[data-offer=reprise] button:has-text('Accepter')"); time.sleep(.4); carte_ok(pg, "[data-light]", "reprise en cours")
        ok(not errs, f"aucune erreur JavaScript (reprise) {errs[:2]}"); ctx.close()

        # phase 3 (intermédiaire : phase 2 d'emblée, phase 3 en semaine 13)
        ctx, pg, errs = page(J(0)); s = gen(pg, prof(niveau="intermediaire", seances=2, jours=["lun", "jeu"])); wa, wb = [w["id"] for w in s["workouts"]]
        pc = next(e["id"] for e in s["exercises"] if e["slug"] == "pc")
        pg.evaluate(SEANCES, [{"day": J(k), "workout_id": [wa, wb][i % 2], "entries": [{"exercise_id": pc, "sets": [[50, 10]] * 3, "effort": 3}]} for i, k in enumerate(range(0, 84, 7))])
        le(pg, J(84), "profil"); carte_ok(pg, "[data-offer=phase]", "carte « Phase 3 prête »")   # dans « Mon profil » : la semaine légère passe avant sur l'accueil
        ok(not errs, f"aucune erreur JavaScript (phase 3) {errs[:2]}"); ctx.close()

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
