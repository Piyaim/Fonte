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
# Témoin : FONTE_ROOT=dossier d'une autre version du code (par exemple celle du commit 08f52a0) ; ce test doit alors échouer.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/records.py
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
     "filler": {"name": "Gainage test", "grp": "Abdos et gainage", "kind": "time", "target_min": 30, "target_max": 30}}
F3 = [[None, 30]] * 3
S = [("2026-09-01", [("presse", [[42.5, 10]] * 3)]), ("2026-09-02", [("presse", [[42.5, 12]] * 3)]),
     ("2026-09-03", [("dev", [[42.5, 12]] * 3)]), ("2026-09-04", [("dev", [[45, 9]] * 3)]),
     ("2026-09-05", [("velo", [[None, 15]]), ("filler", F3)]), ("2026-09-06", [("velo", [[None, 20]]), ("filler", F3)]),
     ("2026-09-07", [("trac", [[30, 8]] * 3)]), ("2026-09-08", [("trac", [[25, 6]] * 3)]),
     ("2026-09-09", [("dips", [[None, 10]] * 3)]), ("2026-09-10", [("dips", [[5, 6]] * 3)]),
     ("2026-09-11", [("dips", [[None, 11]] * 3)]), ("2026-09-12", [("dips", [[None, 10]] * 3)])]
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
        # ce que l'Historique affiche pour chaque séance (étiquettes de chaque ligne)
        H = pg.evaluate("""() => { const d = document.createElement('div'); d.innerHTML = vHisto(); const out = {};
          [...d.querySelectorAll('.card')].forEach(c => { const day = c.querySelector('h2').textContent.slice(0, 10);
            out[day] = [...c.querySelectorAll('tr')].map(r => [r.cells[0].childNodes[0].textContent, [...r.querySelectorAll('.tag')].map(t => t.textContent)]); });
          return out; }""")
        def tags(day, name):   # étiquettes de l'exercice dans la séance du jour (jj/mm/aaaa dans l'Historique)
            y, m, d = day.split("-"); row = [r for r in H.get(f"{d}/{m}/{y}", []) if r[0] == X[name]["name"]]
            return row[0][1] if row else None
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
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
        b.close()
finally:
    srv.terminate()
print("\n" + ("ÉCHEC : " + str(len(fails)) + " contrôle(s)" if fails else "Tout est bon."))
sys.exit(1 if fails else 0)
