# SPDX-License-Identifier: AGPL-3.0-or-later
# Questionnaire de départ et programme généré (lot 1) : IMC, exemple du cahier des charges, blessures, santé,
# nombre d'exercices, reprise d'un questionnaire quitté, remplacement des programmes après confirmation
# (mode local ET mode serveur), historique intact, brouillon de séance gardé, export et import du profil.
#   python3 tests/profil.py
# Les valeurs attendues sont écrites ici en dur (et non relues dans profil.js) : si une règle est faussée dans
# profil.js, le test doit échouer.
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5114
env = dict(os.environ, DB_PATH="/tmp/profil.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/profil.db", "/tmp/profil.db-wal", "/tmp/profil.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
OUVRIR = "document.querySelectorAll('#app details').forEach(d => d.open = true)"   # lot 2C : explications et réglages sont dans des replis « Détails »

NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
BASE = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "athletique", "objectifs2": ["forme"],
        "niveau": "reprise", "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"],
        "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
def prof(**k):
    a = json.loads(json.dumps(BASE)); a.update(k); return a
# exemple du cahier des charges (page 7) : reprise, corps athlétique, 3 séances de 60 min en salle, phase 1
EX_A = ["pc", "di", "tv", "rdl", "pl"]; EX_B = ["gs", "de", "rs", "lc", "db"]
EX_PRM = {"pc": [3, 10, 12, 90], "di": [3, 10, 12, 90], "tv": [3, 10, 12, 90], "rdl": [3, 10, 10, 120], "pl": [3, 30, 30, 60],
          "gs": [3, 10, 12, 90], "de": [3, 10, 12, 90], "rs": [3, 10, 12, 90], "lc": [3, 12, 12, 60], "db": [3, 10, 10, 60]}
# table des contre-indications « genoux » proposée (à relire par Georgio) : écrite ici en dur
GENOUX = {"pc", "gs", "squat-smith", "fentes", "split-squat-bulgare", "leg-extension", "stairmaster", "course"}
EPAULES = {"developpe-couche", "di", "ecartes", "dips-assistes", "tractions-assistees", "pull-over", "de", "developpe-militaire", "elevations-laterales",
           "elevations-frontales", "dips-banc", "planche-laterale"}
POUSSEE = {"developpe-couche", "di", "chest-press", "pompes", "dips-assistes", "de", "developpe-militaire"}
CACHE = ["IMC", "kcal", "Obésité", "Surpoids", "Corpulence", "Insuffisance pondérale"]   # rien de tout cela si le détail santé est masqué
CARDIO = {"tapis-incline", "velo", "rameur", "elliptique", "stairmaster", "course", "intervalles"}
PLAN = "a => { const p = PROFIL._.plan(a); return {w: p.workouts.map(w => ({name: w.name, items: w.items.map(i => i.slug), missing: w.missing, notes: w.notes})), prm: p.prm}; }"
# exercices du catalogue, sans les champs qui bougent seuls (« used » change dès qu'une séance est enregistrée)
CATA = "fetch('/api/state').then(r => r.json()).then(s => s.exercises.map(e => { const o = Object.assign({}, e); delete o.used; return o; }))"
REG = "s => Object.fromEntries(s.workouts.map(w => [w.name, w.settings]))"

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        def page(local=True, dark=False):
            ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark" if dark else "light", accept_downloads=True)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if local else "")); pg.wait_for_selector("#app button:has-text('Commencer')", timeout=8000); time.sleep(.4)
            return ctx, pg, errs
        ctx, pg, errs = page()
        ev = pg.evaluate

        # ------------------------------------------------------------ IMC : 12 cas, dont les limites 18,5 / 25 / 30 / 35
        cas = [(74, 200, 18.5, "Corpulence normale"), (73.6, 200, 18.4, "Insuffisance pondérale"), (100, 200, 25.0, "Surpoids"),
               (99.6, 200, 24.9, "Corpulence normale"), (120, 200, 30.0, "Obésité modérée"), (119.6, 200, 29.9, "Surpoids"),
               (140, 200, 35.0, "Obésité sévère"), (139.6, 200, 34.9, "Obésité modérée"), (65, 170, 22.5, "Corpulence normale"),
               (76.5, 175, 25.0, "Surpoids"), (45, 175, 14.7, "Insuffisance pondérale"), (160, 170, 55.4, "Obésité sévère")]
        for kg, cm, imc, tr in cas:
            r = ev("([kg, cm]) => { const b = PROFIL._.bmiOf(kg, cm); return [b, PROFIL._.bmiBand(b).t]; }", [kg, cm])
            ok(r == [imc, tr], f"IMC {kg} kg, {cm} cm : {r[0]} ({r[1]}), attendu {imc} ({tr})")
        en = ev("PROFIL._.energy({sexe:'f', poids:70, taille:170, age:40, seances:3})")
        ok(abs(en["mb"] - 1401.5) < .01 and abs(en["need"] - 1401.5 * 1.375) < .01, f"Mifflin-St Jeor, femme 70 kg 170 cm 40 ans : {en['mb']} kcal, besoin {round(en['need'])}")
        ok(ev("PROFIL._.energy({sexe:'nr', poids:70, taille:170, age:40, seances:3})") is None, "sans réponse sur le sexe : pas de besoin calorique")

        # ------------------------------------------------------------ exemple du cahier des charges
        r = ev(PLAN, BASE)
        ok([w["name"] for w in r["w"]] == ["Séance A", "Séance B"], f"3 séances par semaine : programmes {[w['name'] for w in r['w']]}")
        ok(r["w"][0]["items"][:-1] == EX_A, f"Séance A = {r['w'][0]['items']}")
        ok(r["w"][1]["items"][:-1] == EX_B, f"Séance B = {r['w'][1]['items']}")
        ok(all(w["items"][-1] in CARDIO and w["items"][-1] != "intervalles" for w in r["w"]), f"cardio facile en fin de séance : {[w['items'][-1] for w in r['w']]}")
        ok(all([r["prm"][s]["sets"], r["prm"][s]["min"], r["prm"][s]["max"], r["prm"][s]["rest"]] == v for s, v in EX_PRM.items()),
           "séries, répétitions et repos de l'exemple (3 × 10-12, 90 s ; soulevé de terre 3 × 10, 2 min ; leg curl 3 × 12, 60 s ; planche 3 × 30 s ; dead bug 3 × 10)")
        ok(all(r["prm"][w["items"][-1]]["min"] == 15 and r["prm"][w["items"][-1]]["max"] == 20 for w in r["w"]), "cardio de 15 à 20 minutes")
        ok(not any(w["missing"] or w["notes"] for w in r["w"]), "rien ne manque, aucun remplacement")

        # ------------------------------------------------------------ blessure genoux
        viol, avec, n = [], 0, 0
        for se in (2, 3, 4, 5):
            for lieu in ("complete", "machines", "halteres", "pdc"):
                for niv in ("reprise", "intermediaire"):
                    for d in (30, 75):
                        n += 1
                        r1 = ev(PLAN, prof(seances=se, lieu=lieu, niveau=niv, duree=d, blessures=["genoux"]))
                        viol += [(se, lieu, s) for w in r1["w"] for s in w["items"] if s in GENOUX]
                        r0 = ev(PLAN, prof(seances=se, lieu=lieu, niveau=niv, duree=d))
                        avec += any(s in GENOUX for w in r0["w"] for s in w["items"])
        ok(not viol, f"genoux : aucun exercice contre-indiqué dans {n} programmes ({viol[:3]})")
        ok(avec >= n // 2, f"témoin : sans blessure, ces exercices sont bien présents ({avec}/{n} programmes)")
        r1 = ev(PLAN, prof(blessures=["genoux"]))
        ok(any("aucun exercice de ce type" in t or "à la place de" in t for w in r1["w"] for t in w["notes"]), f"genoux : le remplacement ou le retrait est expliqué ({r1['w'][0]['notes'][:1]})")
        sq = [t for w in ev(PLAN, prof(blessures=["genoux"]))["w"] for t in w["notes"] if "aucun exercice de ce type" in t]
        ok(any(t.startswith("Squat") and "blessure aux genoux" in t and "professionnel de santé" in t for t in sq), f"genoux : message « aucun exercice de ce type » pour le squat ({sq[:1]})")
        viol = []
        for se in (2, 3, 4, 5):
            for lieu in ("complete", "machines", "halteres", "pdc"):
                for niv in ("reprise", "intermediaire"):
                    r1 = ev(PLAN, prof(seances=se, lieu=lieu, niveau=niv, duree=75, blessures=["epaules"]))
                    viol += [(se, lieu, s) for w in r1["w"] for s in w["items"] if s in EPAULES]
        ok(not viol, f"épaules : aucun exercice contre-indiqué dans 32 programmes ({viol[:3]})")
        r1 = ev(PLAN, prof(blessures=["epaules"]))
        ok(any(s in POUSSEE for s in r1["w"][1]["items"]), f"épaules : la séance B contient au moins une poussée ({r1['w'][1]['items']})")
        ok("chest-press" in r1["w"][0]["items"] and "di" not in r1["w"][0]["items"], "épaules : développé incliné haltères remplacé par la chest press machine (remplaçant du cahier des charges)")

        # ------------------------------------------------------------ santé « Oui » : pas d'intervalles, pas de course, programme allégé
        oui = dict(NON, tension=True)
        bad, temoin = [], set()
        for obj in ("endurance", "athletique", "force"):
            for lieu in ("complete", "pdc"):
                r1 = ev(PLAN, prof(objectif=obj, niveau="intermediaire", lieu=lieu, sante=oui))
                bad += [s for w in r1["w"] for s in w["items"] if s in ("intervalles", "course")]
                bad += [s for s, v in r1["prm"].items() if s not in CARDIO and (v["sets"] != 2 or v["min"] < 8)]
                r0 = ev(PLAN, prof(objectif=obj, niveau="intermediaire", lieu=lieu))
                temoin |= {s for w in r0["w"] for s in w["items"] if s in ("intervalles", "course")}
        ok(not bad, f"santé « Oui » : ni intervalles, ni course, 2 séries, pas de répétitions maximales ({bad[:4]})")
        ok(temoin == {"intervalles", "course"}, f"témoin : sans « Oui », intervalles et course apparaissent ({sorted(temoin)})")
        mn = ev(PLAN, prof(age=16, objectif="force", niveau="intermediaire"))
        ok(all(v["min"] >= 8 for s, v in mn["prm"].items() if s not in CARDIO), "moins de 18 ans : pas de répétitions maximales (8 au minimum)")
        ob = ev(PLAN, prof(poids=95, taille=170, lieu="pdc", objectif="endurance", niveau="intermediaire"))   # IMC 32,9
        ok(not any(s in ("course", "intervalles", "stairmaster") for w in ob["w"] for s in w["items"]), "IMC de 30 ou plus : cardio à faible impact seulement")

        # ------------------------------------------------------------ nombre d'exercices selon la durée
        NB = {30: 4, 45: 5, 60: 6, 75: 7}; badn = []
        for se in (2, 3, 4, 5):
            for d, nb in NB.items():
                for niv, attendu in (("intermediaire", nb), ("reprise", min(nb, 5))):   # phase 1 : pas d'isolation, donc 5 au plus
                    r1 = ev(PLAN, prof(seances=se, duree=d, niveau=niv))
                    for w in r1["w"]:
                        force = [s for s in w["items"] if s not in CARDIO]
                        if len(force) != attendu or len(set(force)) != len(force) or w["missing"]: badn.append((se, d, niv, w["name"], len(force)))
        ok(not badn, f"nombre d'exercices conforme à la durée (4, 5, 6, 7 ; 5 au plus en phase 1), sans doublon : {badn[:3]}")
        st = ev(PLAN, prof(seances=5))
        ok([w["name"] for w in st["w"]] == ["Poussée", "Tirage", "Jambes", "Haut du corps", "Bas du corps"], "5 séances : poussée, tirage, jambes, haut, bas")
        ok([w["name"] for w in ev(PLAN, prof(seances=4))["w"]] == ["Haut du corps", "Bas du corps"], "4 séances : haut et bas du corps")
        pdc = ev(PLAN, prof(lieu="pdc"))
        ok(any("Tirage" in m for w in pdc["w"] for m in w["missing"]), f"poids du corps : il manque un tirage, signalé ({pdc['w'][0]['missing']})")
        ok(all(s in ("pompes", "fentes", "pl", "db", "bird-dog", "planche-laterale", "dips-banc", "mollets", "course") for w in pdc["w"] for s in w["items"]), "poids du corps : aucun exercice qui demande du matériel")
        av = ev(PLAN, prof(eviter=["di", "tv"]))
        ok("di" not in av["w"][0]["items"] and "tv" not in av["w"][0]["items"], "exercices à éviter : exclus du programme")
        ok(ev("(() => { const e = Object.values(EX); return Object.keys(PROFIL._.LIB).length === 50 && Object.keys(PROFIL._.LIB).every(s => e.some(x => x.slug === s)); })()"), "la table couvre les 50 exercices du catalogue")

        # ------------------------------------------------------------ témoins : une règle faussée doit être détectée
        t = ev("""a => { const L = PROFIL._.LIB, k = L.pc[5]; L.pc[5] = []; const p = PROFIL._.plan(a); L.pc[5] = k; return p.workouts.flatMap(w => w.items.map(i => i.slug)); }""", prof(blessures=["genoux"]))
        ok("pc" in t, "témoin : si la presse à cuisses perd sa contre-indication genoux, le contrôle la trouve dans le programme")
        t = ev("""a => { const P = PROFIL._.PRM.p1.hinge, k = P.slice(); P[3] = 90; const p = PROFIL._.plan(a); P.splice(0, 4, ...k); return p.prm.rdl.rest; }""", BASE)
        ok(t == 90 and ev(PLAN, BASE)["prm"]["rdl"]["rest"] == 120, "témoin : un repos faussé change bien le résultat comparé à l'exemple, puis la règle est remise")

        # ------------------------------------------------------------ interface : questionnaire imposé, quitté, repris
        ok(pg.locator(".tabbar").is_hidden() and pg.locator("#menu-btn").is_hidden(), "questionnaire imposé : barre du bas et menu masqués")
        ok("Bienvenue dans Fonte" in pg.inner_text("#app"), "écran d'accueil du questionnaire")
        ev("async () => { await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: 1, entries: [{exercise_id: 1, sets: [[50, 10], [50, 9]], effort: 3}]}); await load(); }")
        ev("""localStorage.setItem('muscu-draft', JSON.stringify({mode:'new', sid:null, wid:1, wname:'Séance A', ids:[1,2], day:'2026-10-20', notes:'brouillon témoin', vals:{1:[['55','8']]}, dirty:true}))""")
        hist0 = ev("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
        pg.click("button:has-text(\"Commencer\")"); time.sleep(.2)
        ok("Question 1 sur 17" in pg.inner_text("#app"), "question 1 sur 17")
        pg.fill("#qin", "Léa"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        pg.fill("#qin", "12"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        ok("Question 2 sur 17" in pg.inner_text("#app") and "entre 16 et 75" in pg.inner_text("#qerr"), "âge 12 : refusé sur place, sans retour au début")
        pg.fill("#qin", "17"); time.sleep(.1); ok("moins de 18 ans" in pg.inner_text("#app"), "âge 17 : message sur l'accord d'un parent")
        pg.fill("#qin", "40"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        pg.click("button:has-text(\"Femme\")"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        pg.fill("#qin", "170"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        pg.fill("#qin", "66,5"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        pg.click("button:has-text(\"Corps athlétique\")"); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        ok("Question 7 sur 17" in pg.inner_text("#app"), "arrivé à la question 7")
        pg.reload(); pg.wait_for_selector("#app .qcount:text-is('Question 7 sur 17')"); time.sleep(.4)   # l'utilisateur quitte l'appli puis revient
        ok("Question 7 sur 17" in pg.inner_text("#app"), "après fermeture : retour à la question 7")
        pg.click("#tb-back[aria-label='Question précédente']"); time.sleep(.2); pg.click("#tb-back[aria-label='Question précédente']"); time.sleep(.2)
        ok(pg.input_value("#qin") == "66.5" or pg.input_value("#qin") == "66,5", f"réponses retrouvées (poids : {pg.input_value('#qin')})")
        d = ev("JSON.parse(localStorage.getItem('muscu-profil-brouillon')).answers")
        ok(d["prenom"] == "Léa" and d["age"] == 40 and d["objectif"] == "athletique", "brouillon : prénom, âge, objectif enregistrés")
        # question à choix multiple : 2 au maximum, l'objectif principal n'est pas proposé
        pg.click("button:has-text(\"Suivant\")"); time.sleep(.2); pg.click("button:has-text(\"Suivant\")"); time.sleep(.2)
        ok("Corps athlétique" not in pg.inner_text("#app"), "objectifs secondaires : l'objectif principal n'est pas proposé")
        pg.click("button:has-text(\"Prendre du muscle\")"); pg.click("button:has-text(\"Mobilité et posture\")"); pg.click("button:has-text(\"Gagner en force\")"); time.sleep(.2)
        ok("au maximum" in pg.inner_text("#qerr") and ev("JSON.parse(localStorage.getItem('muscu-profil-brouillon')).answers.objectifs2.length") == 2, "objectifs secondaires : 2 au maximum")
        # la suite des réponses : brouillon complet, comme si les questions avaient été remplies
        ev("a => { const d = JSON.parse(localStorage.getItem('muscu-profil-brouillon')); d.answers = a; d.mode = 'resume'; localStorage.setItem('muscu-profil-brouillon', JSON.stringify(d)); }",
           prof(niveau="intermediaire", objectif="force", seances=4, jours=["lun", "mar", "jeu", "ven"]))
        pg.reload(); pg.wait_for_selector("#app #qh:text-is('Ton résumé')"); time.sleep(.4)
        pg.evaluate(OUVRIR); tx = pg.inner_text("#app")   # replis ouverts : « IMC » absent de tout l'écran
        ok("Léa, vérifie puis génère ton programme." in tx and "IMC" not in tx and "kcal" not in tx, "résumé, détail santé masqué : ni IMC ni calories, replis ouverts compris")
        pg.click("button:has-text(\"Afficher le détail santé\")"); time.sleep(.2); tx = pg.inner_text("#app")
        ok("IMC\u00a0: 22,8" in tx and "Il ne distingue pas le muscle de la graisse" in tx and "kcal" in tx, "détail santé affiché : IMC, message neutre, calories")
        ok("ne remplace pas un avis médical" in tx and "douleur vive" in tx, "avertissements du cahier des charges affichés")
        pg.click("button:has-text(\"Masquer le détail santé\")"); time.sleep(.2)
        # confirmation : Annuler ne change rien
        avant = ev("fetch('/api/state').then(r => r.json())"); cata0 = ev(CATA)
        pg.click("button:has-text(\"Générer mon programme\")"); time.sleep(.3); pg.evaluate(OUVRIR); tx = pg.inner_text("#app")
        ok("Séance A et Séance B seront retirés." in tx and "Haut du corps\u00a0: Développé incliné haltères (4 × 4 à 6 · repos 2 min 30)" in tx, "confirmation : programmes retirés, nouveaux programmes et réglages de chaque séance")
        ok("Exercices modifiés" not in tx and "valent partout" not in tx and "→" not in tx, "confirmation : plus de section « Exercices modifiés » ni d'avertissement « ces réglages valent partout »")
        ok("séance en cours non enregistrée est conservée" in tx, "confirmation : le brouillon de séance est annoncé conservé")
        pg.click("#tb-back[aria-label='Retour au résumé']"); time.sleep(.3)   # « ‹ » remplace « Annuler » (lot 3)
        apres = ev("fetch('/api/state').then(r => r.json())")
        ok(avant == apres and ev("localStorage.getItem('muscu-profil')") is None and pg.locator("#app #qh").inner_text() == "Ton résumé", "« ‹ » (ancien « Annuler ») : aucune donnée modifiée, pas de profil, retour au résumé")
        # confirmation : Remplacer
        pg.click("button:has-text(\"Générer mon programme\")"); time.sleep(.3); pg.click("button:has-text(\"Remplacer\")"); pg.wait_for_selector("text=Ton programme est prêt", timeout=5000)
        s = ev("fetch('/api/state').then(r => r.json())")
        ok([w["name"] for w in s["workouts"]] == ["Haut du corps", "Bas du corps"] and not {w["id"] for w in s["workouts"]} & {1, 2}, "programmes remplacés par Haut / Bas du corps")
        h = s["sessions"]
        ok(len(h) == len(hist0) == 1 and h[0]["workout_id"] is None and h[0]["workout_name"] == "Séance A" and h[0]["entries"] == hist0[0]["entries"], "mode local : historique intact, workout_id à NULL, nom de séance gardé")
        cata1 = ev(CATA); diff = [a["slug"] for a, b in zip(cata0, cata1) if a != b]
        ok(len(cata0) == len(cata1) == 50 and not diff, f"générateur : catalogue d'exercices identique avant et après ({diff[:4]})")
        ok(any(e["slug"] == "di" and [e["sets"], e["target_min"], e["target_max"], e["rest"]] != [4, 4, 6, 150] for e in cata0), "(témoin : le développé incliné du catalogue n'a pas déjà les réglages générés)")
        di = next(e for e in s["exercises"] if e["slug"] == "di"); hc = next(w for w in s["workouts"] if w["name"] == "Haut du corps")
        ok(hc["settings"].get(str(di["id"])) == {"sets": 4, "target_min": 4, "target_max": 6, "rest": 150}, f"réglages enregistrés dans la séance Haut du corps (développé incliné : {hc['settings'].get(str(di['id']))})")
        ok(all(set(w["settings"]) == {str(i) for i in w["items"]} for w in s["workouts"]), "chaque exercice des séances générées a son réglage de séance")
        dr = ev("JSON.parse(localStorage.getItem('muscu-draft'))")
        ok(dr and dr["notes"] == "brouillon témoin" and dr["vals"]["1"] == [["55", "8"]] and dr["wid"] is None, "brouillon de séance conservé (rattaché à « séance libre »)")
        pr = ev("JSON.parse(localStorage.getItem('muscu-profil'))")
        ok(pr["version"] == 1 and pr["answers"]["objectif"] == "force" and ev("localStorage.getItem('muscu-profil-brouillon')") is None, "profil enregistré (version 1), brouillon du questionnaire effacé")
        ok(pg.locator(".tabbar").is_visible(), "après validation : navigation de retour")
        pg.reload(); pg.wait_for_selector(".tabbar button"); time.sleep(.3)
        ok("Bienvenue" not in pg.inner_text("#app") and pg.locator(".tabbar").is_visible(), "au lancement suivant : plus de questionnaire")
        pg.evaluate("go('seance'); exitFocus()"); time.sleep(.3)   # Aperçu : toute la séance, notes comprises
        ok(pg.input_value("#f-notes") == "brouillon témoin", "onglet Séance : le brouillon s'affiche avec ses valeurs")
        pg.evaluate("go('seance')"); pg.evaluate(f"pickWorkout({hc['id']}); exitFocus()"); time.sleep(.3)
        pg.evaluate(OUVRIR); crd = pg.locator(".card", has_text="Développé incliné haltères").first.inner_text()
        ok("4 × 4-6" in crd and "propre à ce programme" in crd and "150 s" in crd, f"écran Séance : le développé incliné affiche le réglage de la séance ({crd[:60]!r})")
        pg.evaluate("go('accueil')"); time.sleep(.2)
        # Mon profil, Refaire le questionnaire, Quitter
        pg.click("#menu-btn"); time.sleep(.3); ok("Mon profil" in pg.inner_text("#dnav"), "menu : entrée « Mon profil »")
        pg.click("#dnav >> text=Mon profil"); time.sleep(.3); pg.evaluate(OUVRIR); tx = pg.inner_text("#app")
        ok("Refaire le questionnaire" in tx and "IMC" not in tx, "Mon profil : résumé sans détail santé, bouton « Refaire le questionnaire »")
        pg.click("button:has-text(\"Refaire le questionnaire\")"); time.sleep(.2)
        ok(pg.input_value("#qin") == "Léa", "refaire : réponses précédentes préremplies")
        pg.click("button:has-text(\"Quitter\")"); time.sleep(.2)
        ok("Reprendre le questionnaire" in pg.inner_text("#app") and ev("JSON.parse(localStorage.getItem('muscu-profil')).answers.objectif") == "force", "quitter : profil inchangé, questionnaire à reprendre")

        # ------------------------------------------------------------ export et import
        ev("go('donnees')"); time.sleep(.3)
        ok("réponses au questionnaire de santé" in pg.inner_text("#app"), "écran Données : l'export contient les réponses santé")
        with pg.expect_download() as dl: pg.click("text=Télécharger l'export")
        data = json.load(open(dl.value.path()))
        ok(data.get("profil", {}).get("answers", {}).get("sante", {}).get("tension") is False and data["profil"]["version"] == 1, "l'export contient la clé « profil »")
        ev("localStorage.removeItem('muscu-profil'); localStorage.removeItem('muscu-profil-brouillon')"); pg.reload(); pg.wait_for_selector("#app button:has-text('Commencer')"); time.sleep(.3)
        ok("Bienvenue dans Fonte" in pg.inner_text("#app"), "(profil effacé : questionnaire imposé)")
        pg.click("button:has-text(\"J’ai une sauvegarde\")"); time.sleep(.3)
        pg.fill("#bk", json.dumps(data)); pg.click("button.go:has-text('Importer')"); time.sleep(.8)
        ok(ev("JSON.parse(localStorage.getItem('muscu-profil') || 'null')") == data["profil"] and not ev("PROFIL.imposed()"), "import avec « profil » : profil restauré, questionnaire levé")
        sans = dict(data); sans.pop("profil"); sans.pop("jeu", None)
        ev("go('donnees')"); time.sleep(.3); pg.fill("#bk", json.dumps(sans)); pg.click("button.go:has-text('Importer')"); time.sleep(.8)
        ok(ev("JSON.parse(localStorage.getItem('muscu-profil'))") == data["profil"] and len(ev("fetch('/api/state').then(r => r.json())")["sessions"]) == 1, "import d'un ancien export sans « profil » : accepté, profil actuel inchangé")
        ok(not errs, f"aucune erreur JavaScript (local) {errs[:2]}")

        # ------------------------------------------------------------ question des blessures : « Aucune » exclusive, « Autre » ouvre un champ
        ctx3, pg3, errs3 = page()
        pg3.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'q', i: 12, redo: false}))", prof(blessures=[]))
        pg3.reload(); pg3.wait_for_selector("text=Question 13 sur 17")
        bl = lambda: pg3.evaluate("JSON.parse(localStorage.getItem('muscu-profil-brouillon')).answers.blessures")
        pg3.click("button.qo:has-text('Genoux')"); pg3.click("button.qo:has-text('Épaules')")
        ok(bl() == ["epaules", "genoux"], f"blessures : deux zones cochées ({bl()})")
        pg3.click("button.qo:has-text('Aucune')"); ok(bl() == ["aucune"], f"cocher « Aucune » décoche les zones ({bl()})")
        pg3.click("button.qo:has-text('Genoux')"); ok(bl() == ["genoux"], f"cocher une zone décoche « Aucune » ({bl()})")
        ok(pg3.locator("#app input[oninput*='typedOther']").count() == 0, "sans « Autre », pas de champ de texte")
        pg3.click("button.qo:has-text('Autre')"); time.sleep(.2)
        ok(pg3.locator("#app input[oninput*='typedOther']").count() == 1, "« Autre » ouvre le champ de texte libre")
        pg3.fill("#app input[oninput*='typedOther']", "tendinite au talon"); time.sleep(.1)
        ok(pg3.evaluate("JSON.parse(localStorage.getItem('muscu-profil-brouillon')).answers.blessures_autre") == "tendinite au talon", "texte libre enregistré")

        # ------------------------------------------------------------ IMC caché pour de vrai : IMC 32, « Non, juste mon programme »
        ok(ev("PROFIL._.bmiOf(92.5, 170)") == 32, "(profil d'essai : IMC 32)")
        pg3.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", prof(poids=92.5, detail="non"))
        pg3.reload(); pg3.wait_for_selector("button:has-text('Générer mon programme')")
        def cache(nom):
            pg3.evaluate(OUVRIR); t = pg3.inner_text("#app"); vus = [m for m in CACHE if m in t]
            ok(not vus, f"IMC caché, écran {nom} : aucun de {CACHE} ({vus})"); return t
        t = cache("résumé"); ok("Cardio à faible impact, sans sauts" in t, "IMC caché : l'adaptation est écrite sans sa raison")
        pg3.click("button:has-text('Générer mon programme')"); time.sleep(.3); cache("confirmation")
        pg3.click("button:has-text('Remplacer')"); pg3.wait_for_selector("text=Ton programme est prêt"); cache("« Ton programme est prêt »")
        pg3.evaluate("go('profil')"); time.sleep(.3); cache("« Mon profil »")
        pg3.click("button:has-text('Afficher le détail santé')"); time.sleep(.2)
        ok("IMC\u00a0: 32" in pg3.inner_text("#app") and "Obésité modérée" in pg3.inner_text("#app"), "témoin : détail affiché, l'IMC et sa tranche apparaissent")
        ok(not errs3, f"aucune erreur JavaScript (blessures, IMC caché) {errs3[:2]}")

        # ------------------------------------------------------------ « Garder mes programmes »
        ctx4, pg4, errs4 = page()
        avant = pg4.evaluate("fetch('/api/state').then(r => r.json())")
        pg4.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", prof(objectif="force", niveau="intermediaire"))
        pg4.reload(); pg4.wait_for_selector("button:has-text('Générer mon programme')"); pg4.click("button:has-text('Générer mon programme')"); time.sleep(.3)
        pg4.evaluate(OUVRIR); ok("4 × 4 à 6" in pg4.inner_text("#app"), "(la confirmation annonce des réglages différents du catalogue)")
        pg4.click("button:has-text('Garder mes programmes')"); time.sleep(.5)
        apres = pg4.evaluate("fetch('/api/state').then(r => r.json())")
        pr = pg4.evaluate("JSON.parse(localStorage.getItem('muscu-profil'))")
        ok(apres == avant, "garder mes programmes : programmes et exercices identiques à avant")
        ok(pr and pr["version"] == 1 and pr["program"] is None and pr["answers"]["objectif"] == "force", "garder mes programmes : profil enregistré, sans programme généré")
        pg4.reload(); pg4.wait_for_selector(".tabbar button"); time.sleep(.3)
        ok(pg4.locator(".tabbar").is_visible() and "Bienvenue" not in pg4.inner_text("#app"), "garder mes programmes : le questionnaire ne revient plus au lancement")
        pg4.evaluate("go('profil')"); time.sleep(.3); pg4.click("button:has-text('Générer un programme à partir de ce profil')"); time.sleep(.3)
        pg4.click("button:has-text('Générer mon programme')"); time.sleep(.3)
        ok(pg4.locator("#app #qh").inner_text() == "Remplacer tes programmes\u00a0?" and "seront retirés." in pg4.inner_text("#app"), "Mon profil : générer plus tard passe par la même confirmation")
        pg4.click("button:has-text('Remplacer')"); pg4.wait_for_selector("text=Ton programme est prêt", timeout=5000)
        s4 = pg4.evaluate("fetch('/api/state').then(r => r.json())")
        ok([w["name"] for w in s4["workouts"]] == ["Séance A", "Séance B"] and pg4.evaluate("JSON.parse(localStorage.getItem('muscu-profil')).program.phase") == 2, "Mon profil : programme généré et appliqué ensuite")
        ok(not errs4, f"aucune erreur JavaScript (garder) {errs4[:2]}")

        # ------------------------------------------------------------ mode serveur : app.py met bien workout_id à NULL
        ctx2, pg2, errs2 = page(local=False)
        pg2.evaluate("async () => { await api('POST', '/api/sessions', {day: '2026-10-13', workout_id: 2, entries: [{exercise_id: 3, sets: [[30, 10]]}]}); await load(); }")
        pg2.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", BASE)
        pg2.reload(); pg2.wait_for_selector("text=Générer mon programme"); pg2.click("button:has-text(\"Générer mon programme\")"); time.sleep(.3)
        pg2.click("button:has-text(\"Remplacer\")"); pg2.wait_for_selector("text=Ton programme est prêt", timeout=5000)
        s2 = pg2.evaluate("fetch('/api/state').then(r => r.json())")
        mine = [x for x in s2["sessions"] if x["day"] == "2026-10-13"]
        ok(len(mine) == 1 and mine[0]["workout_id"] is None and mine[0]["workout_name"] == "Séance B" and mine[0]["entries"][0]["sets"] == [[30, 10]], "mode serveur : historique intact, workout_id à NULL (app.py)")
        ok([w["name"] for w in s2["workouts"]] == ["Séance A", "Séance B"] and not {w["id"] for w in s2["workouts"]} & {1, 2}, "mode serveur : nouveaux programmes A et B")
        ok(not errs2, f"aucune erreur JavaScript (serveur) {errs2[:2]}")
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
