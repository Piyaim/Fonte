# SPDX-License-Identifier: AGPL-3.0-or-later
# La typographie (espace insécable avant « : ? ! ; » et après « « », fonction typo de profil.js) n'agit qu'à l'affichage.
# Modes local et serveur : prénom « Jo : a ? b ! », exercice « Test : a ? b », astuce et note de séance avec « ! » et « ; »,
# tous saisis à l'écran. L'affichage du résumé porte bien les espaces insécables (sinon le test ne prouve rien) ; les données
# enregistrées, l'export, puis l'import dans une appli neuve et son nouvel export gardent les textes octet pour octet, sans
# aucune espace insécable (ni «   » échappé).
# Témoins : /home/PM/Claude-applications/Fonte-appli/fonte-travail/refonte/lot3/temoins_typo.py (FONTE_ROOT = copie faussée).
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/typographie_donnees.py
import json, os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server")
P1, P2 = 5193, 5194
TMP = tempfile.mkdtemp(prefix="fonte-typo-")
PRENOM, NOM, ASTUCE, NOTE = "Jo : a ? b !", "Test : a ? b", "Dos droit ; souffle !", "Bravo ! Fini ; ok ? « oui »"
NON = {k: False for k in ("poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre")}
REP = {"age": 35, "sexe": "f", "taille": 178, "poids": 75, "objectif": "force", "objectifs2": ["forme"], "niveau": "intermediaire",
       "passe": ["aucun"], "seances": 3, "duree": 60, "lieu": "complete", "blessures": ["aucune"], "sante": NON, "eviter": [], "jours": ["lun", "mer", "ven"], "detail": "non"}
BV = "#app button:has-text('Commencer')"
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
PROCS = []
def serveur(port, nom):
    pr = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={port})"], cwd=APP,
                          env=dict(os.environ, DB_PATH=os.path.join(TMP, nom + ".db"), PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    PROCS.append(pr); time.sleep(2.5)
    if pr.poll() is not None: raise SystemExit(f"le serveur ne démarre pas (port {port} déjà pris ?)")
    return pr
def telecharger(pg):
    pg.evaluate("go('donnees')"); time.sleep(.3)
    with pg.expect_download() as dl: pg.click("text=Télécharger l'export")
    return open(dl.value.path(), "rb").read()
def sans_date(o): return {k: v for k, v in o.items() if k != "exported_at"}
def propre(octets, quoi, m):   # chaque texte présent tel quel (UTF-8), aucune espace insécable, ni brute ni échappée
    ok(all(json.dumps(t, ensure_ascii=False).encode() in octets or json.dumps(t).encode() in octets for t in quoi)
       and " ".encode() not in octets and b"\\u00a0" not in octets.lower(), m)

try:
    with sync_playwright() as p:
        b = p.chromium.launch(); errs = []
        for mode in ("local", "serveur"):
            srv = serveur(P1, "a-" + mode); q = "?local=1" if mode == "local" else ""
            ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); pg = ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{P1}/{q}"); pg.wait_for_selector(BV, timeout=8000)
            # 1. prénom saisi à l'écran (question 1), puis les autres réponses
            pg.click(BV); pg.wait_for_selector("#qin"); pg.fill("#qin", PRENOM); pg.click("button:has-text('Suivant')"); time.sleep(.2)
            pg.evaluate("r => { const d = JSON.parse(localStorage.getItem('muscu-profil-brouillon')); Object.assign(d.answers, r); d.mode = 'resume'; d.i = 16; localStorage.setItem('muscu-profil-brouillon', JSON.stringify(d)); }", REP)
            pg.reload(); pg.wait_for_selector("#app #qh:text-is('Ton résumé')")
            ok("Jo : a ? b !, vérifie" in pg.inner_text("#app"), f"{mode} · (affichage : le résumé met les espaces insécables, la typographie agit bien)")
            ok(pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil-brouillon')).answers.prenom") == PRENOM, f"{mode} · brouillon : prénom enregistré tel que saisi")
            pg.click("button:has-text('Générer mon programme')"); time.sleep(.3); pg.click("button:has-text('Remplacer')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            ok(pg.evaluate("JSON.parse(localStorage.getItem('muscu-profil')).answers.prenom") == PRENOM, f"{mode} · profil : prénom enregistré tel que saisi, après le résumé, la confirmation et « Programme prêt »")
            # 2. exercice créé à l'écran, avec une astuce
            pg.evaluate("PROFIL.home(); go('exercices')"); time.sleep(.3); pg.click("[aria-label='Nouvel exercice']"); pg.wait_for_selector("#e-name")
            pg.fill("#e-name", NOM); pg.fill("#e-tip", ASTUCE); pg.click("button:has-text('Créer l’exercice')"); time.sleep(.6)
            x = pg.evaluate("n => Object.values(EX).find(e => e.name === n) || null", NOM)
            ok(bool(x) and x["tip"] == ASTUCE, f"{mode} · exercice et astuce enregistrés tels que saisis ({x and x['name']!r})")
            # 3. séance avec une note, saisie dans l'Aperçu
            pg.evaluate("go('seance'); pickWorkout(WO[0].id); exitFocus()"); time.sleep(.3)
            i0 = pg.evaluate("F.ids[0]"); pg.fill(f"#v{i0}_0l", "40"); pg.fill(f"#v{i0}_0v", "10"); pg.fill("#f-notes", NOTE)
            pg.click("button:has-text('Enregistrer la séance')"); time.sleep(1)
            ok(pg.evaluate("SESS.some(s => s.notes === %s)" % json.dumps(NOTE)), f"{mode} · note de séance enregistrée telle que saisie")
            # tous les écrans qui affichent ces textes, profil compris
            for v in ("accueil", "historique", "progres", "programmes", "profil"): pg.evaluate(f"go('{v}')"); time.sleep(.2)
            pg.evaluate(f"go('exercices'); openEx({x['id']})"); time.sleep(.3)
            st = pg.evaluate("fetch('/api/state').then(r => r.json())")
            ok(any(e["name"] == NOM and e["tip"] == ASTUCE for e in st["exercises"]) and any(s["notes"] == NOTE for s in st["sessions"]), f"{mode} · données relues après tous les écrans : identiques")
            # 4. export, octet pour octet
            ex1 = telecharger(pg)
            propre(ex1, [NOM, ASTUCE, NOTE] + ([PRENOM] if mode == "local" else []), f"{mode} · export : textes tels que saisis, aucune espace insécable")
            ok(not any(" " in str(v) for v in (pg.evaluate("Object.values(localStorage).join('')"),)), f"{mode} · localStorage : aucune espace insécable")
            ctx.close(); srv.terminate(); srv.wait()
            # 5. import dans une appli neuve, puis nouvel export
            srv = serveur(P2, "b-" + mode)
            ctx = b.new_context(viewport={"width": 390, "height": 844}, service_workers="block"); pg = ctx.new_page()
            pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{P2}/{q}"); pg.wait_for_selector(BV, timeout=8000)
            pg.click("button:has-text('J’ai une sauvegarde')"); time.sleep(.3); pg.fill("#bk", ex1.decode()); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(2000)
            pg.evaluate("go('accueil')"); pg.reload(); pg.wait_for_selector("#app .hero", timeout=8000)
            for v in ("historique", "programmes", "profil"): pg.evaluate(f"go('{v}')"); time.sleep(.2)
            ex2 = telecharger(pg)
            propre(ex2, [NOM, ASTUCE, NOTE] + ([PRENOM] if mode == "local" else []), f"{mode} · export après import : textes tels que saisis, aucune espace insécable")
            ok(sans_date(json.loads(ex2)) == sans_date(json.loads(ex1)), f"{mode} · export après import identique au premier (hors date d'export)")
            # mode local : la clé « id » des exercices du catalogue de départ change de place après un import (local-backend.js, inchangé
            # par le lot 3) ; les octets se comparent donc clés triées, et les textes saisis, octet pour octet, par propre()
            canon = lambda o: json.dumps(sans_date(json.loads(o)), ensure_ascii=False, sort_keys=True).encode()
            ok(canon(ex2) == canon(ex1), f"{mode} · mêmes octets, clés triées (hors date d'export)")
            ctx.close(); srv.terminate(); srv.wait()
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
finally:
    for pr in PROCS:
        if pr.poll() is None: pr.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
