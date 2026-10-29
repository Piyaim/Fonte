# SPDX-License-Identifier: AGPL-3.0-or-later
# Plafond de 4 jetons par jour, quêtes comprises (décision A du 23/10/2026, report des quêtes) : ce qu'une journée rapporte
# vraiment (solde mesuré), ce que l'écran de fin annonce, les jetons de quête en attente (jamais perdus, crédités seulement à
# une séance, jamais à l'ouverture de l'onglet Esprits), les règles affichées, l'export et l'import (mode local).
# Témoin : échoue sur le code de la 0.7.0 (FONTE_ROOT=dossier sorti par `git archive v0.7.0`).
import json, os, re, subprocess, sys, time
ROOT = os.environ.get("FONTE_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "server"); PORT = 5117; DB = "/tmp/plafond.db"
env = dict(os.environ, DB_PATH=DB, PYTHONDONTWRITEBYTECODE="1")
for f in (DB, DB + "-wal", DB + "-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
# Prépare : exercices non cardio couvrant au moins 5 zones principales, équipe de 2 esprits dont les zones sont couvertes.
PREP = """() => { const z = {}, ids = [];
  for (const e of Object.values(EX)) { if (e.kind === 'cardio' || e.kind === 'assisted') continue; const p = APPX.zonesOf(e).p.filter(k => !z[k]);
    if (p.length) { ids.push(e.id); p.forEach(k => z[k] = 1); } if (ids.length >= 5 && Object.keys(z).length >= 5) break; }
  const cre = Object.keys(JEU._.CRE).filter(c => z[JEU._.CRE[c].zone]).slice(0, 2);
  return {ids, zones: Object.keys(z), cre}; }"""
MK = """async ([day, ids, sets, kg]) => { await api('POST', '/api/sessions', {day, entries: ids.map(id => ({exercise_id: id, sets: Array.from({length: sets}, () => [kg, 10]), effort: 3}))});
  await load(); return SESS.reduce((a, b) => b.ts > a.ts ? b : a).id; }"""
# Efface les séances, remet le jeu à zéro avec l'équipe choisie ; renvoie le solde de départ.
RESET = """async (cre) => { for (const x of SESS.slice()) await api('DELETE', '/api/sessions/' + x.id); await load();
  JEU._.reset(); JEU.init(); const s = JEU.state(); cre.forEach(c => s.owned[c] = {n: 0}); s.team = cre.slice(); return s.tokens; }"""
GAGNE = "JEU._.quests(false).list.filter(q => q.ok).reduce((a, q) => a + q.r, 0)"   # jetons de quêtes gagnés cette semaine
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, accept_downloads=True); ctx.add_init_script(PROFIL_FAIT)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector(".tabbar button"); pg.wait_for_timeout(500)
        ev = pg.evaluate
        prep = ev(PREP); ids = prep["ids"]
        ok(len(prep["zones"]) >= 5 and len(prep["cre"]) == 2, f"préparation : {len(ids)} exercices, {len(prep['zones'])} zones, équipe {prep['cre']}")
        cap = ev("JEU._.DAY_CAP"); ok(cap == 4, f"plafond codé : {cap} jetons par jour")
        today = ev("today()"); hier = ev("(d) => { const t = new Date(d + 'T12:00:00'); t.setDate(t.getDate() - 1); return t.toISOString().slice(0, 10); }", today)
        attente = lambda: ev("JEU.state().pend || 0")

        # 1. fin de séance : trois séances le même jour, quêtes « Variété », « Équipe complète », « Objectif de la semaine »
        t0 = ev(RESET, prep["cre"]); reps = []
        for kg in (40, 45, 50):
            reps.append(ev("(id) => JEU.award(id)", ev(MK, [today, ids, 3, kg])))
        ann = [r["tokens"] for r in reps]; gain = ev("JEU.state().tokens") - t0
        print("      annonces :", ann, "· gain réel :", gain, "· en attente :", attente())
        ok(gain <= cap, f"3 séances le même jour, quêtes comprises : {gain} jetons gagnés (au plus {cap})")
        ok(all(a <= cap for a in ann) and sum(ann) <= cap, f"écrans de fin : {ann}, jamais plus de {cap} sur la journée")
        ok(sum(ann) == gain, f"ce qui est annoncé est ce qui est crédité ({sum(ann)} annoncés, {gain} crédités)")
        ok(gain == cap, f"le plafond reste atteignable : {gain} jetons pour cette journée chargée")
        gq = ev(GAGNE)
        ok(gq == 5, f"(quêtes de la semaine gagnées : {gq} jetons)")
        # aucun jeton de quête perdu : crédités (lignes « Jetons de quête ») + en attente = jetons des quêtes accomplies
        qc = sum(l[1] for r in reps for l in r["lines"] if l[0] == "Jetons de quête")
        ok(qc + attente() == gq, f"aucun jeton de quête perdu : {qc} crédités + {attente()} en attente = {gq}")
        # écran de fin de la 3e séance : annonce bornée, lignes = total, ligne neutre « en attente »
        html = ev("(r) => JEU.rewardHtml(r)", reps[2])
        m = re.search(r'class="tok">\+(\d+) jeton', html); n = int(m.group(1)) if m else 0
        lignes = sum(int(x) for x in re.findall(r"<b>\+(\d+)</b>", html))
        ok(n == reps[2]["tokens"] and lignes == n, f"écran de fin : « +{n} », lignes {lignes}")
        txt = re.sub(r"<[^>]+>", " ", html)
        ok(attente() == 0 or f"{attente()} jeton{'s' if attente() > 1 else ''} de quête en attente" in txt, f"écran de fin : ligne « {attente()} jetons de quête en attente »")
        ok(not re.search(r"reviens|demain|plus que|expire|avant|vite|dépêche", txt, re.I), "écran de fin : aucun appel à revenir ni compte à rebours")
        # l'onglet Esprits ne crédite pas les jetons en attente
        pd, tk = attente(), ev("JEU.state().tokens")
        ev("go('jeu')"); pg.wait_for_timeout(300); ev("go('accueil')"); pg.reload(); pg.wait_for_selector(".tabbar button"); ev("go('jeu')"); pg.wait_for_timeout(300)
        ok(pd > 0 and attente() == pd and ev("JEU.state().tokens") == tk, f"ouvrir l'appli et l'onglet Esprits : rien n'est crédité ({pd} toujours en attente)")
        ok(f"{pd} jeton{'s' if pd > 1 else ''} de quête en attente" in pg.inner_text("#app"), "onglet Esprits : les jetons en attente sont affichés")
        # export puis import (mode local) : l'attente suit
        ev("go('donnees')"); pg.wait_for_timeout(300)
        with pg.expect_download() as dl: pg.click("text=Télécharger l'export")
        data = json.load(open(dl.value.path(), encoding="utf-8"))
        ok(data.get("jeu", {}).get("pend") == pd, f"export : jetons en attente dans la clé jeu ({data.get('jeu', {}).get('pend')})")
        ev("JEU._.reset()"); ok(attente() == 0, "(état effacé)")
        pg.fill("#bk", json.dumps(data)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1000)
        ok(attente() == pd and ev("JEU.state().tokens") == tk, f"import : {attente()} jetons en attente et solde {ev('JEU.state().tokens')} restaurés")
        # export de la 0.7.0 (clé jeu sans « pend ») : import sans erreur, rien en attente, solde gardé tel quel
        ancien = json.loads(json.dumps(data)); ancien["jeu"].pop("pend", None); ancien["jeu"]["tokens"] = 9
        pg.fill("#bk", json.dumps(ancien)); pg.click("button.go:has-text('Importer')"); pg.wait_for_timeout(1000)
        ok(attente() == 0 and ev("JEU.state().tokens") == 9, "export 0.7.0 sans jetons en attente : importé, solde de 9 gardé tel quel (ni recalculé ni retiré)")
        ev("(d) => JEU.importState(d)", data["jeu"]); ok(attente() == pd, "(état avec jetons en attente remis)")
        # séance suivante, un autre jour (place libre) : l'attente est créditée, dans la limite du jour
        rep = ev("(id) => JEU.award(id)", ev(MK, [hier, ids[:1], 3, 30]))
        ok(rep["tokens"] <= cap and attente() == max(0, pd - (rep["tokens"] - 1)) and any(l[0] == "Jetons de quête" and l[1] > 0 for l in rep["lines"]),
           f"séance suivante avec de la place : +{rep['tokens']}, dont jetons de quête ; reste en attente {attente()}")
        ok(ev("JEU.state().days[%s]" % json.dumps(hier)) <= cap, "le jour de cette séance reste sous le plafond")

        # 2. quêtes accomplies à l'ouverture de l'onglet Esprits (séances non créditées, comme après un import)
        t0 = ev(RESET, prep["cre"])
        for kg in (40, 45, 50): ev(MK, [today, ids, 3, kg])
        ev("go('jeu')"); pg.wait_for_timeout(300)
        g2 = ev("JEU.state().tokens") - t0
        ok(g2 == 0 and attente() == ev(GAGNE) == 5, f"onglet Esprits : quêtes notées faites, 0 jeton crédité, {attente()} en attente (aucun perdu)")
        rep = ev("(id) => JEU.award(id)", ev(MK, [today, ids[:1], 3, 30]))
        ok(rep["tokens"] <= cap and ev("JEU.state().days[today()]") <= cap and ev("JEU.state().tokens") - t0 + attente() == 5 + 1,
           f"séance suivante : +{rep['tokens']} (séance + quêtes), plafond tenu, rien de perdu ({attente()} en attente)")
        ev("go('accueil')")

        # 3. règles : même phrase sur la page Règles et dans « Comment gagner des jetons »
        for sub, nom in (("regles", "page Règles"), ("tirage", "« Comment gagner des jetons »")):
            ev("go('jeu'); JEU.sub('%s')" % sub); pg.wait_for_timeout(200)
            t = pg.inner_text("#app")
            ok("Maximum 4" in t and "quêtes comprises" in t and "attendent ta prochaine séance" in t, f"{nom} : plafond de 4 par jour, quêtes comprises, report à la séance suivante")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
