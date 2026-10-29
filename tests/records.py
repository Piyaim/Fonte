# SPDX-License-Identifier: AGPL-3.0-or-later
# Records et jeton « Progression » (règle du 23/10/2026), mode serveur, sur de vraies séances :
# - affichage (étiquette « record » de l'Historique, écran de fin, Progrès) : une charge jamais faite sur l'exercice, quel que soit
#   le nombre de reps ; assistance plus faible que toutes les précédentes ; au poids du corps, le lest compte comme une charge
#   (séries lestées et non lestées comparées séparément) ; le cardio n'a pas de record ; plus de reps à charge égale = gain en gris ;
# - jeton « Progression » : un record selon cette règle OU un meilleur score d'Epley (ancienne règle, cardio compris), au moins 3 séries.
# Cas de Georgio :
#   1. 42,5 kg × 10 puis 42,5 kg × 12 : pas d'étiquette record, « +2 reps » en gris, mais +1 jeton ;
#   2. 42,5 kg × 12 puis 45 kg × 9 : étiquette record (« Avant : 42,5 kg × 12 ») et +1 jeton ;
#   3. cardio 15 min puis 20 min : pas d'étiquette record, mais +1 jeton ;
#   4. traction assistée 30 kg puis 25 kg d'assistance, avec moins de reps : record ;
#   5. dips sans lest 10 reps, puis lest 5 kg × 6 : record ; puis sans lest 11 reps : record ; puis sans lest 10 reps : pas record.
#   6. séance sans lest après un historique où toutes les séries étaient lestées : pas un record (une première fois, décision du 23/10) ;
#   7. même exercice deux fois (ou trois) dans une séance (lot 2) : la meilleure série de la séance, comparée aux séances précédentes
#      seulement ; une seule étiquette « record » par exercice et par séance ; jeton « Progression » une seule fois ;
#      première séance d'un exercice fait deux fois : pas de record (la 2e fois ne se compare pas à la 1re de la même séance).
#      Le serveur (app.py) et le mode local (local-backend.js) rendent un exercice saisi deux fois en UNE ligne avec toutes ses séries :
#      le détail montre donc une ligne, et computePRs réunit aussi les séries d'un même exercice s'il en trouvait deux.
# Les étiquettes sont lues dans le détail de chaque séance (écran du lot 2) et le nombre de records dans la liste de l'Historique.
# Témoins : FONTE_ROOT=dossier d'une autre version du code (par exemple celle du commit 08f52a0) ; ce test doit alors échouer.
#   Cas 7 : comme les données arrivent déjà réunies, le code de 764a6e1 passe aussi ce cas (il ne prouve que le résultat affiché).
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/records.py
import os, subprocess, sys, tempfile, time
from playwright.sync_api import sync_playwright
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "server"); PORT = 5181
TMP = tempfile.mkdtemp(prefix="fonte-records-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                       env=dict(os.environ, DB_PATH=os.path.join(TMP, "s.db"), PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(2.5)
# séances : [jour, [[exercice, séries], ...]] ; « filler » = 3 séries identiques à chaque fois (ni record, ni gain, ni Epley)
X = {"presse": {"name": "Presse test", "grp": "Jambes", "kind": "weight", "target_min": 8, "target_max": 12},
     "dev": {"name": "Développé test", "grp": "Pectoraux", "kind": "weight", "target_min": 6, "target_max": 12},
     "velo": {"name": "Vélo test", "grp": "Cardio", "kind": "cardio", "target_min": 15, "target_max": 30},
     "trac": {"name": "Traction assistée test", "grp": "Dos", "kind": "weight", "assisted": True, "target_min": 6, "target_max": 10},
     "dips": {"name": "Dips test", "grp": "Pectoraux", "kind": "reps", "target_min": 6, "target_max": 15},
     "dipl": {"name": "Dips lestés test", "grp": "Pectoraux", "kind": "reps", "target_min": 6, "target_max": 15},
     "squat": {"name": "Squat test", "grp": "Jambes", "kind": "weight", "target_min": 3, "target_max": 10},
     "fente": {"name": "Fente test", "grp": "Jambes", "kind": "weight", "target_min": 8, "target_max": 10},
     "filler": {"name": "Gainage test", "grp": "Abdos et gainage", "kind": "time", "target_min": 30, "target_max": 30}}
F3 = [[None, 30]] * 3
S = [("2026-09-01", [("presse", [[42.5, 10]] * 3)]), ("2026-09-02", [("presse", [[42.5, 12]] * 3)]),
     ("2026-09-03", [("dev", [[42.5, 12]] * 3)]), ("2026-09-04", [("dev", [[45, 9]] * 3)]),
     ("2026-09-05", [("velo", [[None, 15]]), ("filler", F3)]), ("2026-09-06", [("velo", [[None, 20]]), ("filler", F3)]),
     ("2026-09-07", [("trac", [[30, 8]] * 3)]), ("2026-09-08", [("trac", [[25, 6]] * 3)]),
     ("2026-09-09", [("dips", [[None, 10]] * 3)]), ("2026-09-10", [("dips", [[5, 6]] * 3)]),
     ("2026-09-11", [("dips", [[None, 11]] * 3)]), ("2026-09-12", [("dips", [[None, 10]] * 3)]),
     ("2026-09-13", [("dipl", [[5, 8]] * 3)]), ("2026-09-14", [("dipl", [[7.5, 6]] * 3)]), ("2026-09-15", [("dipl", [[None, 12]] * 3)]),
     ("2026-09-16", [("squat", [[50, 10]] * 3)]), ("2026-09-17", [("squat", [[50, 10]]), ("squat", [[57.5, 5]]), ("squat", [[60, 3]])]),
     ("2026-09-18", [("fente", [[20, 10]] * 2), ("fente", [[22.5, 8]] * 2)])]
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.clock.set_fixed_time("2026-09-20T10:00:00")
        pg.goto(f"http://127.0.0.1:{PORT}/"); pg.wait_for_selector("#app", timeout=8000); pg.wait_for_timeout(500)
        pg.evaluate("JEU.view()")   # le jeu commence avant les séances : elles pourront rapporter des jetons
        ids = pg.evaluate("""async ([X, S]) => { const ex = {};
          for (const k in X) ex[k] = (await api('POST', '/api/exercises', Object.assign({sets: 3, rest: 90}, X[k]))).id;
          const sid = {};
          for (const [day, en] of S) sid[day] = (await api('POST', '/api/sessions', {day, workout_name: 'Test', entries: en.map(([k, sets]) => ({exercise_id: ex[k], sets}))})).id;
          await load(); return {ex, sid}; }""", [X, S])
        sid, ex = ids["sid"], ids["ex"]
        # ce que le détail de chaque séance affiche (étiquettes de chaque exercice), et le nombre de records de la liste de l'Historique
        # (rendu appelé directement : sans questionnaire rempli, l'appli affiche le questionnaire à la place des onglets)
        H = pg.evaluate("""() => { const out = {}, d = document.createElement('div');
          for (const s of SESS) { HDET = s.id; d.innerHTML = vHisto();
            out[s.day] = [...d.querySelectorAll('.sd .ex')].map(x => [x.querySelector('.exh b').textContent, [...x.querySelectorAll('.tag')].map(t => t.textContent)]); }
          HDET = null; return out; }""")
        LISTE = pg.evaluate("""() => { HDET = null; const d = document.createElement('div'); d.innerHTML = vHisto();
          return Object.fromEntries([...d.querySelectorAll('.hlist .lrow')].map((r, i) => [SESS[SESS.length - 1 - i].day, (r.querySelector('.tag.rec') || {}).textContent || ''])); }""")
        def rows(day, name): return [r[1] for r in H.get(day, []) if r[0] == X[name]["name"]]
        def tags(day, name):   # étiquettes de l'exercice dans la séance du jour (toutes ses lignes réunies)
            r = rows(day, name); return [t for x in r for t in x] if r else None
        def jeton(day):   # lignes de jetons de la séance (JEU.award, comme à l'enregistrement)
            r = pg.evaluate(f"JEU.award({sid[day]})"); return [l[0] for l in (r or {}).get("lines", [])]
        def rec(day, name): return "record" in (tags(day, name) or [])

        # 1. même charge, plus de reps : gain en gris, pas de record, mais le jeton « Progression »
        t, j = tags("2026-09-02", "presse"), jeton("2026-09-02")
        ok(t is not None and "record" not in t and "+2 reps" in t, f"1. 42,5 kg × 10 puis × 12 : pas d'étiquette record, « +2 reps » en gris {t}")
        ok("Progression" in j, f"1. … mais +1 jeton « Progression » {j}")
        # 2. charge jamais faite, moins de reps : record (Epley le refusait : 58,5 < 59,5) et jeton
        pr = pg.evaluate(f"(computePRs().bySession[{sid['2026-09-04']}] || []).map(r => [r.ex.name, recTxt(r.ex, r.set), recAvant(r)])")
        ok(rec("2026-09-04", "dev"), f"2. 42,5 kg × 12 puis 45 kg × 9 : étiquette record {tags('2026-09-04', 'dev')}")
        ok(pr == [["Développé test", "45 kg × 9", "Avant : 42,5 kg × 12"]], f"2. écran de fin : « 45 kg × 9 », « Avant : 42,5 kg × 12 » {pr}")
        ok("Progression" in jeton("2026-09-04"), "2. … et +1 jeton « Progression »")
        # 3. cardio : jamais de record, mais le jeton (ancienne règle)
        ok(not rec("2026-09-06", "velo") and tags("2026-09-06", "velo") is not None, f"3. cardio 15 puis 20 min : pas d'étiquette record {tags('2026-09-06', 'velo')}")
        j = jeton("2026-09-06"); ok("Progression" in j, f"3. … mais +1 jeton « Progression » {j}")
        # 4. assistance plus faible, moins de reps : record
        ok(rec("2026-09-08", "trac"), f"4. traction assistée 30 puis 25 kg d'assistance (6 reps au lieu de 8) : record {tags('2026-09-08', 'trac')}")
        # 5. dips : lest, puis sans lest
        ok(rec("2026-09-10", "dips"), f"5. dips 10 reps puis lest 5 kg × 6 : record {tags('2026-09-10', 'dips')}")
        ok(rec("2026-09-11", "dips"), f"5. puis sans lest 11 reps : record {tags('2026-09-11', 'dips')}")
        ok(not rec("2026-09-12", "dips") and tags("2026-09-12", "dips") is not None, f"5. puis sans lest 10 reps : pas record {tags('2026-09-12', 'dips')}")
        # témoins : la première fois n'est jamais un record ; une séance sans progrès ne rapporte pas le jeton
        ok(not any(rec(d, k) for d, k in (("2026-09-01", "presse"), ("2026-09-03", "dev"), ("2026-09-07", "trac"), ("2026-09-09", "dips"))), "première fois sur un exercice : pas de record")
        j = jeton("2026-09-12"); ok(j and "Progression" not in j and "Séance terminée" in j, f"(témoin) dips 11 puis 10 reps : pas de jeton « Progression » {j}")
        # 6. sans lest après un historique entièrement lesté : une première fois, pas un record
        ok(rec("2026-09-14", "dipl"), f"6. (témoin) lest 5 kg × 8 puis 7,5 kg × 6 : record {tags('2026-09-14', 'dipl')}")
        t = tags("2026-09-15", "dipl"); ok(t is not None and "record" not in t and not any(x.startswith("+") for x in t), f"6. puis sans lest 12 reps : ni record ni gain {t}")
        # 7. même exercice trois fois dans une séance
        pr = pg.evaluate(f"(computePRs().bySession[{sid['2026-09-17']}] || []).map(r => [r.ex.name, recTxt(r.ex, r.set), recAvant(r)])")
        ok(pr == [["Squat test", "60 kg × 3", "Avant\u00a0: 50 kg × 10"]], f"7. squat 50 × 10, puis 57,5 × 5 et 60 × 3 dans la même séance : un seul record, la meilleure série, « Avant : 50 kg × 10 » {pr}")
        r7 = rows("2026-09-17", "squat")
        n7 = pg.evaluate(f"SESS.find(s => s.id === {sid['2026-09-17']}).entries.map(e => e.sets.length)")
        ok(n7 == [3] and len(r7) == 1 and r7[0].count("record") == 1, f"7. détail : une ligne de squat avec ses 3 séries, une seule étiquette « record » {n7} {r7}")
        ok(LISTE.get("2026-09-17") == "1 record", f"7. Historique : « 1 record » pour cette séance {LISTE.get('2026-09-17')!r}")
        j = jeton("2026-09-17"); ok(j.count("Progression") == 1, f"7. jeton « Progression » une seule fois {j}")
        r8 = rows("2026-09-18", "fente"); p8 = pg.evaluate(f"(computePRs().bySession[{sid['2026-09-18']}] || []).length")
        ok(len(r8) == 1 and not any("record" in x for x in r8) and p8 == 0, f"7. première séance de fentes, faites deux fois (20 puis 22,5 kg) : pas de record {r8} {p8}")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        b.close()
finally:
    srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
