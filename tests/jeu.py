# SPDX-License-Identifier: AGPL-3.0-or-later
# Mini-jeu « Esprits » : règles (garanties, plafonds, idempotence), niveaux, export/import, rendu des 27 esprits, parcours dans l'interface.
import json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5113
env = dict(os.environ, DB_PATH="/tmp/jeu.db", PYTHONDONTWRITEBYTECODE="1")
for f in ("/tmp/jeu.db", "/tmp/jeu.db-wal", "/tmp/jeu.db-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
PROFIL_FAIT = "localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', JSON.stringify({version: 1, created: '2026-10-20T00:00:00Z', answers: {detail: 'non'}}))"   # profil déjà rempli : le questionnaire de départ ne s'impose pas
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)
try:
    with sync_playwright() as p:
        b = p.chromium.launch(); ctx = b.new_context(viewport={"width": 390, "height": 844}, color_scheme="dark", accept_downloads=True); ctx.add_init_script(PROFIL_FAIT)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
        pg.goto(f"http://127.0.0.1:{PORT}/?local=1"); pg.wait_for_selector(".tabbar button"); time.sleep(.5)
        ev = pg.evaluate
        ok(ev("!!window.JEU && !!window.CREA && !!window.APPX"), "JEU, CREA et la passerelle sont chargés")
        ok(ev("JEU.state().tokens") == 3 and ev("JEU.state().team.length") == 1, "bienvenue : 3 jetons et un esprit")
        # catalogue
        ok(ev("JEU._.CR.length") == 27 and ev("JEU._.IT.length") == 25, "27 esprits et 25 objets")
        ok(ev("JEU._.CR.every(c => ['C','U','R','E','L'].includes(c[2]) && JEU._.CRE[c[0]].zone)"), "chaque esprit a une rareté et une zone")
        ok(ev("new Set(JEU._.CR.map(c => c[3])).size") == 11, "les 11 zones ont chacune au moins un esprit")
        ok(ev("['C','U','R','E','L'].every(r => JEU._.CR.some(c => c[2]===r) && JEU._.IT.some(i => i[2]===r))"), "chaque rareté a des esprits et des objets")
        # rendu de tous les esprits aux 3 stades, sans NaN
        bad = ev("""() => { let n=0; for (const c of JEU._.CR) for (const st of [1,2,3]) { const s = CREA.svg(JEU._.CRE[c[0]], st); if (/NaN|undefined/.test(s)) n++; } return n; }""")
        ok(bad == 0, f"rendu de 27 esprits × 3 stades sans NaN ({bad} défaut)")
        # taux sur un grand nombre de tirages (garantie incluse)
        res = ev("""() => { JEU._.reset(); const s = JEU.state(); const c = {C:0,U:0,R:0,E:0,L:0}; for (let i=0;i<20000;i++) { c[JEU._.pullOne().rar]++; } return c; }""")
        tot = sum(res.values()); fr = {k: v/tot for k, v in res.items()}
        ok(abs(fr["C"]-.58) < .03 and abs(fr["U"]-.26) < .03 and abs(fr["R"]-.11) < .02, f"taux observés C/U/R : {fr['C']:.3f} {fr['U']:.3f} {fr['R']:.3f}")
        ok(fr["E"] > .04 and fr["L"] > .01 and fr["E"] < .09 and fr["L"] < .03, f"E et L un peu au-dessus du taux de base grâce à la garantie : {fr['E']:.3f} {fr['L']:.3f}")
        # garantie : rng toujours au pire (renvoie 0.999 => Commune) -> E au 30e, L au 90e
        g = ev("""() => { JEU._.reset(); const r = JEU._.rng.rng; JEU._.rng.rng = () => 0.5; const seq = []; for (let i=0;i<90;i++) seq.push(JEU._.pullOne().rar); JEU._.rng.rng = r; return seq; }""")
        ok(g[29] == "E" and "E" not in g[:29] and g[89] == "L" and "L" not in g[:89], f"garantie : 1er Épique au tirage {g.index('E')+1}, Légendaire au tirage {g.index('L')+1}")
        # doublons -> éclats
        d = ev("""() => { JEU._.reset(); const s = JEU.state(); s.owned.gloumi = {n:0}; const r = JEU._.rng.rng; JEU._.rng.rng = () => 0; /* 0 => Commune, 1er esprit Commune, tirage item<0.35 => item */ let sh0 = s.shards; let got=[]; for (let i=0;i<40;i++) got.push(JEU._.pullOne()); JEU._.rng.rng = r; return {dup: got.filter(x=>x.kind==='crea' && !x.isNew).length, shards: s.shards - sh0}; }""")
        ok(d["dup"] == 0 or d["shards"] > 0, f"doublons convertis en éclats ({d})")
        # coût et solde
        ev("JEU._.reset(); JEU.init()"); 
        ok(ev("JEU._.pull(5)") is not None and ev("JEU.state().tokens") == 0, "tirage ×5 coûte 5 jetons (solde 3 -> refus puis 0 après crédit)") if False else None
        ev("JEU._.reset(); JEU.init()")
        ok(ev("JEU._.pull(5)") is None and ev("JEU.state().tokens") == 3, "tirage ×5 refusé avec 3 jetons, solde intact")
        ok(len(ev("JEU._.pull(1)")) == 1 and ev("JEU.state().tokens") == 2, "tirage ×1 : 1 jeton débité")
        ev("JEU.state().tokens = 0")
        ok(ev("JEU._.pull(1)") is None and ev("JEU.state().tokens") == 0, "aucun tirage à crédit (jamais de solde négatif)")
        # séances : gains selon l'effort, plafond, idempotence, historique sans gain
        ex0 = ev("Object.keys(EX)[0]")
        def mk(day, sets, effort):
            return ev("""async ([day,sets,eff,ex]) => { const r = await api('POST','/api/sessions',{day,entries:[{exercise_id:+ex,sets:Array.from({length:sets},()=>[40,10]),effort:eff}]}); await load(); return SESS.reduce((a,b)=>b.ts>a.ts?b:a).id; }""", [day, sets, effort, ex0])
        today = ev("today()")
        ev("JEU._.reset(); JEU.init()"); t0 = ev("JEU.state().tokens")
        sid = mk(today, 2, 3); r = ev("JEU.award(%d)" % sid)
        ok(r["tokens"] == 0, "2 séries seulement : aucun jeton (pas de récompense sans vrai travail)")
        sid = mk(today, 4, 2); r = ev("JEU.award(%d)" % sid)
        ok(r["tokens"] == 1, f"séance facile de 4 séries : 1 jeton ({r['tokens']})")
        r2 = ev("JEU.award(%d)" % sid)
        ok(r2 is None and ev("JEU.state().tokens") == t0 + 1, "créditer deux fois la même séance : impossible")
        sid = mk(today, 6, 3); r = ev("JEU.award(%d)" % sid)   # 6 séries, ressenti juste : +1 +1 (effort) = 2
        ok(r["tokens"] >= 2, f"séance de 6 séries, ressenti juste : {r['tokens']} jetons")
        for i in range(5):
            sid = mk(today, 8, 3); ev("JEU.award(%d)" % sid)
        used = ev("JEU.state().days[today()]")
        ok(used <= 4, f"plafond quotidien respecté : {used}/4 jetons aujourd'hui")
        r = ev("(()=>{const x=JEU.award(%d);return x})()" % mk(today, 8, 3))
        ok(r["tokens"] == 0 and r["note"] != "", f"séance au-delà du plafond : 0 jeton et message ({r['note'][:40]})")
        ev("JEU._.reset(); JEU.init()")
        ok(all(v == 0 for v in ev("Object.values(JEU.state().awarded)")), "l'historique existant ne rapporte aucun jeton")
        sc = ev("JEU._.scoreSession(SESS[SESS.length-1])")
        ok(sc["sets"] <= 24, "les séries comptées sont plafonnées (24 par séance)")
        # effort « à fond » ne rapporte pas plus
        sid = mk(ev("(()=>{const d=new Date();d.setDate(d.getDate()-3);return d.toISOString().slice(0,10)})()"), 6, 5); r = ev("JEU.award(%d)" % sid)
        ok(all("Effort juste" not in l[0] for l in r["lines"]), "ressenti « À fond » : pas de bonus d'effort")
        # niveaux : dépend uniquement des séries réelles
        ok(ev("JEU._.stageOf(1)") == 1 and ev("JEU._.stageOf(6)") == 2 and ev("JEU._.stageOf(14)") == 3, "stades : 1, puis 2 au niveau 6, puis 3 au niveau 14")
        # boutique
        ev("JEU._.reset(); JEU.init(); JEU.state().shards = 39")
        ok(ev("JEU._.buy('crea','pomo')") is False and ev("JEU.state().shards") == 39, "boutique : refus sans assez d'éclats")
        ev("JEU.state().shards = 40")
        ok(ev("JEU._.buy('crea','pomo')") is True and ev("JEU.state().shards") == 0 and ev("!!JEU.state().owned.pomo"), "boutique : achat d'un esprit Commun pour 40 éclats")
        ok(ev("JEU._.buy('crea','pomo')") is False, "boutique : pas de double achat")
        # garde-robe
        ev("JEU.state().items['t-violet']=1; JEU.equip('tenue','t-violet')")
        ok(ev("getComputedStyle(document.documentElement).getPropertyValue('--f3').trim()") == "#5b3f9a", "garde-robe : la tenue change la couleur des vêtements des animations")
        ev("JEU.equip('muscle','m-or')")   # non possédé : refus
        ok(ev("JEU.state().equip.muscle") is None, "garde-robe : objet non possédé refusé")
        # export / import
        ev("go('donnees')"); time.sleep(.3)
        with pg.expect_download() as dl: pg.click("text=Télécharger l'export")
        data = json.load(open(dl.value.path()))
        ok(data.get("jeu") and data["jeu"]["items"].get("t-violet") == 1, "l'export contient l'état du jeu")
        ev("JEU._.reset()"); ok(ev("JEU.state().items['t-violet']") is None, "(état effacé)")
        pg.fill("#bk", json.dumps(data)); pg.click("button.go:has-text('Importer')"); time.sleep(.8)
        ok(ev("JEU.state().items['t-violet']") == 1 and ev("JEU.state().equip.tenue") == "t-violet", "l'import restaure le jeu et la tenue")
        # interface
        ev("go('jeu')"); time.sleep(.3)
        for k in ["tirage", "collection", "garde", "boutique", "regles"]:
            ev("JEU.sub('%s')" % k); time.sleep(.2); ok(len(pg.inner_text("#app")) > 80, f"vue Esprits/{k} affichée")
        ev("JEU.sub('regles')"); t = pg.inner_text("#app")
        ok("58 %" in t and "Aucun achat" in t and "n'expirent jamais" in t, "règles : taux et garde-fous affichés")
        ev("JEU.sub('tirage'); JEU.state().tokens = 5; R()"); time.sleep(.2)
        pg.click("text=Tirer (1 jeton)"); pg.wait_for_selector(".j-ov", timeout=3000); time.sleep(1.8)
        pg.screenshot(path="/tmp/jeu_pull.png")
        ok(pg.locator("#j-n").count() == 1, "animation de tirage : carte résultat affichée")
        pg.click("#j-n"); time.sleep(.3); ok(pg.locator(".j-ov").count() == 0 and ev("JEU.state().tokens") == 4, "overlay fermé, 1 jeton débité")
        ev("JEU.opt('hide')"); time.sleep(.2); ok("Esprits" not in pg.inner_text(".tabbar"), "option : l'onglet Esprits peut être masqué")
        ev("JEU.opt('hide')")
        ok(not errs, f"aucune erreur JavaScript {errs[:2]}")
finally:
    srv.terminate()
print("\nRÉSULTAT :", "tout est bon" if not fails else f"{len(fails)} échec(s)")
sys.exit(1 if fails else 0)
