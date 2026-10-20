# SPDX-License-Identifier: AGPL-3.0-or-later
# Réglages propres à chaque séance (lot 2A) : un même exercice réglé 4 × 5 dans « Force », 3 × 12 dans « Volume »,
# sans réglage dans « Libre réglage ». Chaque séance affiche le sien, le conseil de charge et le minuteur l'utilisent,
# l'écran Programmes permet de régler et de revenir aux valeurs de l'exercice, le catalogue ne bouge pas.
# Mode local et mode serveur.
#   python3 tests/reglages_seance.py
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5116
env = dict(os.environ, DB_PATH="/tmp/reglages.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/reglages.db", "/tmp/reglages.db-wal", "/tmp/reglages.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
# l'exercice : un exercice à charge du catalogue, dont la cible n'est ni 5 ni 12 répétitions fixes
PREP = """async () => {
  const x = Object.values(EX).find(e => e.kind === 'weight' && !e.assisted && !e.per_side && !e.archived && e.target_max !== 5 && e.target_max !== 12 && e.sets !== 4);
  const mk = async n => { const r = await api('POST', '/api/workouts', {name: n}); await api('PUT', '/api/workouts/' + r.id, {name: n, items: [x.id]}); return r.id; };
  const force = await mk('Force'), volume = await mk('Volume'), libre = await mk('Libre réglage');
  await api('PUT', '/api/workouts/' + volume, {name: 'Volume', items: [x.id], settings: {[x.id]: {sets: 3, target_min: 12, target_max: 12, rest: 60}}});
  await api('POST', '/api/sessions', {day: '2026-10-15', entries: [{exercise_id: x.id, sets: [[60, 5], [60, 5], [60, 5], [60, 5]], effort: 3}]});
  await load(); return {x, force, volume, libre};
}"""
CARTE = "id => [...document.querySelectorAll('#app .card')].find(c => c.querySelector('input[id^=\"v' + id + '_\"]'))"
# lot 2C : explications et réglage « propre à ce programme » dans le repli « Détails » de la carte, ouvert avant lecture
def carte(pg, id): return pg.evaluate(f"id => {{ const c = ({CARTE})(id); if (c) c.querySelectorAll('details').forEach(d => d.open = true); return c ? c.innerText : ''; }}", id)
def conseil(t): return next((l for l in t.splitlines() if l.startswith("Conseil")), "")
def lignes(pg, id): return pg.evaluate(f"id => ({CARTE})(id).querySelectorAll('.row input[id$=\"l\"]').length", id)
def seance(pg, wid): pg.evaluate(f"go('seance'); pickWorkout({wid})"); time.sleep(.3)

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        for mode, url in (("local", "/?local=1"), ("serveur", "/")):
            ctx = b.new_context(viewport={"width": 390, "height": 844}); ctx.add_init_script(PROFIL_FAIT)
            pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.goto(f"http://127.0.0.1:{PORT}{url}"); pg.wait_for_selector(".tabbar button"); time.sleep(.4)
            d = pg.evaluate(PREP); x = d["x"]; cat0 = pg.evaluate(f"EX[{x['id']}]")
            print(f"--- mode {mode} : {x['name']} (catalogue {x['sets']} × {x['target_min']}-{x['target_max']}, repos {x['rest']} s)")

            # ---------------------------------------------------- écran Programmes : régler « Force » à 4 × 5, repos 180 s
            pg.evaluate(f"go('programmes'); selProg({d['force']})"); time.sleep(.3)
            li = pg.locator(".li", has_text=x["name"]).first
            ok("propre à ce programme" not in li.inner_text(), f"{mode} · Programmes : sans réglage, l'exercice montre les valeurs du catalogue ({li.inner_text().replace(chr(10), ' ')[:70]!r})")
            li.locator("button:has-text('Régler')").click(); time.sleep(.2)
            ok(pg.locator(".cfg").count() == 1 and f"Valeurs de l’exercice : {x['sets']} × " in pg.inner_text(".cfg"), f"{mode} · « Régler » ouvre le réglage, avec les valeurs de l'exercice en rappel")
            pg.fill("#c-sets", "4"); pg.fill("#c-min", "5"); pg.fill("#c-max", "5"); pg.fill("#c-rest", "180")
            pg.click(".cfg button:has-text('Valider')"); time.sleep(.2)
            ok("Modifications non enregistrées" in pg.inner_text("#app"), f"{mode} · réglage validé : modifications signalées non enregistrées")
            pg.click("button:has-text('Enregistrer le programme')"); time.sleep(.6)
            w = pg.evaluate(f"WO.find(w => w.id === {d['force']})")
            ok(w["settings"] == {str(x["id"]): {"sets": 4, "target_min": 5, "target_max": 5, "rest": 180}}, f"{mode} · réglage de « Force » enregistré ({w['settings']})")
            li = pg.locator(".li", has_text=x["name"]).first.inner_text()
            ok("4 × 5" in li and "repos 180 s" in li and "propre à ce programme" in li, f"{mode} · Programmes : la ligne montre 4 × 5, repos 180 s, propre à ce programme")

            # ---------------------------------------------------- écran Séance : chaque programme affiche le sien
            seance(pg, d["force"]); t = carte(pg, x["id"])
            ok("4 × 5" in t and "propre à ce programme" in t and "repos 180 s" in t and "Repos · 180 s" in t, f"{mode} · Séance « Force » : 4 × 5, repos 180 s")
            ok(conseil(t) == "Conseil : 61,5 kg × 5", f"{mode} · Séance « Force » : 4 séries de 5 à 60 kg réussies → le conseil propose 61,5 kg (+2,5 %)")
            ok(lignes(pg, x["id"]) == 4, f"{mode} · Séance « Force » : 4 lignes de série")
            seance(pg, d["volume"]); t = carte(pg, x["id"])
            ok("3 × 12" in t and "repos 60 s" in t and "propre à ce programme" in t, f"{mode} · Séance « Volume » : 3 × 12, repos 60 s")
            ok(conseil(t) == "Conseil : 60 kg × 12", f"{mode} · Séance « Volume » : mêmes séries passées, cible 12 → garder la charge")
            seance(pg, d["libre"]); t = carte(pg, x["id"]); cible = f"{x['target_min']}-{x['target_max']}" if x["target_min"] != x["target_max"] else f"{x['target_max']}"
            ok(f"{x['sets']} × {cible}" in t and f"repos {x['rest']} s" in t and "propre à ce programme" not in t, f"{mode} · Séance « Libre réglage » (témoin) : valeurs du catalogue")
            ok(conseil(t) == f"Conseil : 60 kg × {x['target_max']}", f"{mode} · témoin : avec la cible du catalogue ({x['target_max']}), le conseil n'est pas celui de « Force »")
            # mode focus et minuteur de repos
            seance(pg, d["force"]); pg.evaluate("startFocus()"); time.sleep(.3); pg.evaluate("document.querySelectorAll('.focus details').forEach(d => d.open = true)")
            ok("4 × 5" in pg.inner_text(".focus") and "propre à ce programme" in pg.inner_text(".focus"), f"{mode} · mode focus : 4 × 5")
            pg.click(".frow .tick >> nth=0"); time.sleep(.4); tm = pg.inner_text("#tm")
            ok(tm in ("3:00", "2:59"), f"{mode} · série validée en mode focus : minuteur de 180 s ({tm})")
            pg.evaluate("exitFocus(); TM(0)")
            # fiche exercice
            pg.evaluate(f"go('exercices'); openEx({x['id']})"); time.sleep(.3)
            t = pg.locator(".card", has_text="Dans mes programmes").inner_text()
            ok("Force (4 × 5, repos 180 s)" in t and "Volume (3 × 12, repos 60 s)" in t and "Libre réglage" in t and "Libre réglage (" not in t, f"{mode} · fiche exercice : réglage de chaque programme ({t!r})")

            # ---------------------------------------------------- retour aux valeurs de l'exercice
            pg.evaluate(f"go('programmes'); selProg({d['force']})"); time.sleep(.3)
            pg.locator(".li", has_text=x["name"]).first.locator("button:has-text('Régler')").click(); time.sleep(.2)
            pg.click("button:has-text('Revenir aux valeurs de l’exercice')"); pg.click("button:has-text('Enregistrer le programme')"); time.sleep(.6)
            ok(pg.evaluate(f"WO.find(w => w.id === {d['force']}).settings") == {}, f"{mode} · « Revenir aux valeurs de l'exercice » : réglage effacé")
            seance(pg, d["force"]); t = carte(pg, x["id"])
            ok(f"{x['sets']} × {cible}" in t and "propre à ce programme" not in t, f"{mode} · Séance « Force » : de nouveau les valeurs du catalogue")
            seance(pg, d["volume"]); ok("3 × 12" in carte(pg, x["id"]), f"{mode} · Séance « Volume » garde son propre réglage")
            ok(pg.evaluate(f"EX[{x['id']}]") == cat0, f"{mode} · l'exercice du catalogue n'a pas changé")
            ok(not errs, f"{mode} · aucune erreur JavaScript {errs[:2]}")
            ctx.close()
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
