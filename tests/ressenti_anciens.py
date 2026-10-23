# SPDX-License-Identifier: AGPL-3.0-or-later
# Ressenti à 3 choix (lot « Séance », 0.6.0) : les nouvelles séances enregistrent 2, 3 ou 4 ; les anciennes notes de 1 à 5 restent dans
# les données. Contrôlé ici, en mode serveur et en mode local : une note 1 s'affiche « Facile » et une note 5 « Dur » (Historique,
# « Ressenti : … » d'une séance modifiée, « Dernière fois » du conseil), et une note 1 revient identique après un export puis un import.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/ressenti_anciens.py
import os, subprocess, sys, tempfile, shutil, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5178
TMP = tempfile.mkdtemp(prefix="fonte-ressenti-")
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
INIT = """localStorage.setItem('muscu-profil', JSON.stringify({version: 1, imported: true, created: '2026-10-01T10:00:00', updated: '2026-10-01T10:00:00', answers: {}, program: null}));"""

from playwright.sync_api import sync_playwright
srv = None
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for mode in ("serveur", "local"):
            srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP,
                                   env=dict(os.environ, DB_PATH=os.path.join(TMP, mode + ".db"), PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(3)
            ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(INIT)
            pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if mode == "local" else "")); pg.wait_for_selector("#app .hero", timeout=10000)
            # deux anciennes séances, notées comme avant la 0.6.0 : 1 (très facile) et 5 (très dur), sur deux exercices différents
            ids = pg.evaluate("""async () => { const w = WO[0], [a, c] = w.items;
              const s1 = await api('POST', '/api/sessions', {day: '2026-10-10', workout_id: w.id, entries: [{exercise_id: a, sets: [[40, 10], [40, 10]], effort: 1}]});
              const s5 = await api('POST', '/api/sessions', {day: '2026-10-12', workout_id: w.id, entries: [{exercise_id: c, sets: [[30, 8], [30, 8]], effort: 5}]});
              await load(); return [s1.id, s5.id, a, c]; }""")
            pg.evaluate("document.querySelectorAll('.pr-overlay,.j-ov').forEach(o => o.remove())")
            st = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
            ok(sorted(e["effort"] for s in st for e in s["entries"]) == [1, 5], f"{mode} · notes 1 et 5 enregistrées telles quelles")
            # Historique : étiquette de ressenti de chaque exercice
            pg.evaluate("go('historique')"); pg.wait_for_timeout(300)
            tags = pg.evaluate("[...document.querySelectorAll('#app .card')].map(c => [c.querySelector('h2').textContent, [...c.querySelectorAll('td .tag:not(.rec)')].map(t => t.textContent.trim())])")
            vu = {h.split(" · ")[0]: t for h, t in tags}
            ok([x.lower() for x in vu.get("10/10/2026", [])] == ["facile"] and [x.lower() for x in vu.get("12/10/2026", [])] == ["dur"], f"{mode} · Historique : note 1 « facile », note 5 « dur » {vu}")
            # « Ressenti : … » quand on modifie une séance passée
            lignes = []
            for sid in ids[:2]:
                pg.evaluate("sid => editSession(sid)", sid); pg.wait_for_timeout(300)
                lignes.append(pg.evaluate("[...document.querySelectorAll('#app .feel1 b')].map(b => b.textContent)"))
                pg.evaluate("cancelEdit()")
            ok(lignes == [["Facile"], ["Dur"]], f"{mode} · séance modifiée : « Ressenti : Facile » (1), « Ressenti : Dur » (5) {lignes}")
            # « Dernière fois … · ressenti : … » dans le conseil de charge (Détails)
            dd = pg.evaluate("ids => ids.slice(2).map(x => { const d = document.createElement('div'); d.innerHTML = advice(EX[x], null, null); return (d.textContent.match(/ressenti : (Facile|Juste bien|Dur)/) || [])[1] || null; })", ids)
            ok(dd == ["Facile", "Dur"], f"{mode} · conseil de charge : « ressenti : Facile » (1) et « ressenti : Dur » (5) {dd}")
            # export puis import : la note 1 revient identique
            ex = pg.evaluate("fetch('/api/export').then(r => r.json())")
            notes = [e["effort"] for s in ex["sessions"] for e in s["entries"]]
            ok(sorted(notes) == [1, 5], f"{mode} · export : notes 1 et 5 telles quelles {notes}")
            pg.evaluate("e => api('POST', '/api/import', e)", ex); pg.wait_for_timeout(300)
            st2 = pg.evaluate("fetch('/api/state').then(r => r.json()).then(s => s.sessions)")
            ok(st2 == st and sorted(e["effort"] for s in st2 for e in s["entries"]) == [1, 5], f"{mode} · export puis import : séances identiques, note 1 revenue telle quelle")
            ok(not errs, f"{mode} · aucune erreur JavaScript {errs[:2]}")
            ctx.close(); srv.terminate(); srv.wait(); srv = None
        b.close()
finally:
    if srv: srv.kill()
    shutil.rmtree(TMP, ignore_errors=True)
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
