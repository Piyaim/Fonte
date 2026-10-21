# SPDX-License-Identifier: AGPL-3.0-or-later
# Notifications (version 0.5.0), avec des dates simulées (horloge de Playwright) et une fausse coque FonteApp qui note chaque appel :
# page Notifications (version serveur : explication seule ; appli : valeurs par défaut, autorisation refusée, « Alarmes et rappels »
# demandée seulement en activant la fin du repos, son et vibration par canal, Android 7 sans canaux, notification d'essai),
# demande d'autorisation une fois le questionnaire rempli, planification (rappels sur les jours choisis, une par jour au plus,
# heures calmes, étape du programme une seule fois et reportée au jour libre suivant, bilan du dimanche, « Bon retour » une seule
# fois et plus rien ensuite, aucune notification des Esprits ni des jetons, aucun mot « raté » ou « manqué »), fin du repos,
# réglages hors de l'export, aucune requête sortante.
# Les valeurs attendues sont écrites ici en dur : une règle faussée dans notif.js doit faire échouer le test.
#   FONTCONFIG_FILE=/home/PM/Fonte/tests/polices-chromium.conf .venv/bin/python tests/notifications.py
import json, os, re, subprocess, sys, time
from datetime import date, datetime, timedelta
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); APP = os.path.join(ROOT, "server"); PORT = 5171
DB = "/tmp/notifications.db"
for f in (DB, DB + "-wal", DB + "-shm"):
    if os.path.exists(f): os.remove(f)
srv = subprocess.Popen([sys.executable, "-c", f"import app;app.init_db();app.app.run(port={PORT})"], cwd=APP, env=dict(os.environ, DB_PATH=DB, PYTHONDONTWRITEBYTECODE="1"), stdout=subprocess.PIPE, stderr=subprocess.STDOUT); time.sleep(3)
from playwright.sync_api import sync_playwright
fails = []
def ok(c, m):
    print(("OK    " if c else "ÉCHEC "), m)
    if not c: fails.append(m)

D0 = date(2026, 11, 2)                 # un lundi
J = lambda k: (D0 + timedelta(days=k)).isoformat()
NON = {k: False for k in ["poitrine", "vertiges", "coeur", "tension", "articulaire", "traitement", "autre"]}
BASE = {"prenom": "Léa", "age": 40, "sexe": "f", "taille": 170, "poids": 66, "objectif": "athletique", "objectifs2": ["forme"],
        "niveau": "intermediaire", "passe": ["aucun"], "seances": 2, "duree": 60, "lieu": "complete", "blessures": ["aucune"],
        "sante": NON, "eviter": [], "jours": ["lun", "jeu"], "detail": "non"}
# fausse coque Android : même interface que MainActivity.Bridge ; __N règle l'état (autorisation, alarmes exactes, version d'Android)
COQUE = """window.__N = Object.assign({calls: [], perm: 'granted', exact: true, exactNeeded: true, sdk: 34, sent: []}, JSON.parse(sessionStorage.getItem('__N') || '{}'));
window.FonteApp = {
  notifStatus: () => JSON.stringify({sdk: __N.sdk, perm: __N.perm, exact: __N.exact, exactNeeded: __N.exactNeeded, channels: __N.sdk >= 26, sent: __N.sent}),
  notifAskOnce: () => __N.calls.push(['ask']), notifRequest: () => __N.calls.push(['request']), notifPlan: t => __N.calls.push(['plan', t]),
  notifTest: (a, b) => __N.calls.push(['test', a, b]), restStart: (s, a, b) => { __N.calls.push(['rest', s, a, b]); return true; },
  restCancel: () => __N.calls.push(['restCancel']), openChannel: id => __N.calls.push(['channel', id]), exactRequest: () => __N.calls.push(['exact']),
  saveFile: () => {}, setIcon: () => {}
};"""
CALLS = "k => __N.calls.filter(c => c[0] === k)"
PLAN = "s => NOTIF._.plan(Date.now(), s || NOTIF._.settings(), __N.sent).map(i => ({key: i.key, ch: i.ch, title: i.title, text: i.text, day: (d => { d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); })(new Date(i.at)), h: new Date(i.at).getHours(), m: new Date(i.at).getMinutes()}))"
SEANCES = "async l => { for (const s of l) await api('POST', '/api/sessions', s); await load(); R(); }"
OUVRIR = "document.querySelectorAll('#app details').forEach(d => d.open = true)"
INTERDIT = re.compile(r"manqu|raté|esprit|jeton|tirage|gloumi|pomo|éclat", re.I)
sortantes = []

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        def page(jour, coque=True, local=True, profil=None, n=None, heure="10:00:00"):
            ctx = b.new_context(viewport={"width": 390, "height": 844}); errs = []
            ctx.on("request", lambda r: sortantes.append(r.url) if not r.url.startswith(f"http://127.0.0.1:{PORT}/") and not r.url.startswith(("data:", "blob:")) else None)
            if n: ctx.add_init_script(f"sessionStorage.setItem('__N', {json.dumps(json.dumps(n))})")
            if coque: ctx.add_init_script(COQUE)
            if profil: ctx.add_init_script(f"localStorage.getItem('muscu-profil') || localStorage.setItem('muscu-profil', {json.dumps(json.dumps(profil))})")
            pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e))); pg.on("dialog", lambda d: d.accept())
            pg.clock.set_fixed_time(f"{jour}T{heure}")
            pg.goto(f"http://127.0.0.1:{PORT}/" + ("?local=1" if local else "")); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.5)
            return ctx, pg, errs
        def le(pg, jour, heure="10:00:00"):
            pg.clock.set_fixed_time(f"{jour}T{heure}"); pg.reload(); pg.wait_for_selector("#app .card, #app .hero", timeout=8000); time.sleep(.4)
        def gen(pg, a):            # questionnaire rempli puis « Remplacer mes programmes »
            pg.evaluate("a => localStorage.setItem('muscu-profil-brouillon', JSON.stringify({version: 1, answers: a, mode: 'resume', i: 16, redo: false}))", a)
            pg.reload(); pg.wait_for_selector("button:has-text('Générer mon programme')"); pg.click("button:has-text('Générer mon programme')"); time.sleep(.3)
            pg.click("button:has-text('Remplacer mes programmes')"); pg.wait_for_selector("text=Ton programme est prêt", timeout=8000)
            pg.evaluate("go('accueil')"); time.sleep(.2)
            return pg.evaluate("fetch('/api/state').then(r => r.json())")
        def seance(pg, jour, wid=None):
            s = pg.evaluate("fetch('/api/state').then(r => r.json())"); ex = s["exercises"][0]["id"]
            pg.evaluate(SEANCES, [{"day": jour, "workout_id": wid, "entries": [{"exercise_id": ex, "sets": [[20, 10], [20, 10], [20, 10]], "effort": 3}]}])
        def notifs(pg): pg.evaluate("go('notifications')"); time.sleep(.3)

        # ---------------------------------------------------------------- version serveur (navigateur) : explication seule
        ctx, pg, errs = page(J(0), coque=False, local=False, profil={"version": 1, "created": "2026-10-20T00:00:00Z", "imported": True, "answers": {}})
        notifs(pg); t = pg.inner_text("#app")
        ok("Disponibles seulement dans l’appli Android." in t and pg.locator("#app [role=switch]").count() == 0, "version serveur : explication, aucun réglage")
        ok("Notifications" in pg.evaluate("document.getElementById('dnav').textContent"), "entrée « Notifications » dans le menu")
        ok(pg.evaluate("[...document.querySelectorAll('#dnav button')].map(b => b.textContent).join('|')").endswith("Mon profil|Notifications|Données"), "menu : entre « Mon profil » et « Données »")
        ctx.close()

        # ---------------------------------------------------------------- questionnaire pas encore rempli : pas de demande d'autorisation
        ctx, pg, errs = page(J(0), n={"perm": "ask"})
        time.sleep(.6)
        ok(pg.evaluate(CALLS, "ask") == [], "questionnaire imposé : la demande d'autorisation attend")
        a = gen(pg, BASE); time.sleep(.8)
        ok(len(pg.evaluate(CALLS, "ask")) == 1, f"questionnaire rempli : demande d'autorisation (une fois) ({len(pg.evaluate(CALLS, 'ask'))})")
        plans = pg.evaluate(CALLS, "plan")
        ok(all(c[1] == "" for c in plans), "sans autorisation : aucun plan confié à la coque")
        notifs(pg); t = pg.inner_text("#app")
        ok("Notifications bloquées" in t and "Android les bloque pour Fonte." in t, "autorisation refusée : carte « Notifications bloquées »")
        ok(pg.locator("#app .days .chip[disabled]").count() == 7 and pg.locator("#app button:has-text('Envoyer une notification d’essai')").is_disabled(), "autorisation refusée : réglages grisés")
        pg.click("button:has-text('Activer les notifications')"); time.sleep(.2)
        ok(len(pg.evaluate(CALLS, "request")) == 1, "« Activer les notifications » passe par la coque (demande système ou réglages Android)")
        le(pg, J(0)); time.sleep(.6)
        ok(len(pg.evaluate(CALLS, "ask")) == 1, "à l'ouverture suivante, la page redemande à la coque, qui ne redemande qu'une fois (contrôlé dans MainActivity)")
        ctx.close()

        # ---------------------------------------------------------------- valeurs par défaut, autorisation accordée
        ctx, pg, errs = page(J(0))
        a = gen(pg, BASE); W = {w["name"]: w for w in a["workouts"]}
        notifs(pg); t = pg.inner_text("#app")
        on = pg.evaluate("[...document.querySelectorAll('#app [role=switch]')].map(s => s.getAttribute('aria-label') + '=' + s.getAttribute('aria-checked'))")
        ok(on == ["Notifications=true", "Rappel de séance=true", "Fin du repos=false", "Étapes du programme=true", "Bon retour=true", "Bilan du dimanche=true"], f"interrupteurs par défaut : {on}")
        jours = pg.evaluate("[...document.querySelectorAll('#app .days .chip')].map(c => c.getAttribute('aria-pressed'))")
        ok(jours == ["true", "false", "false", "true", "false", "false", "false"], f"jours du rappel = jours du questionnaire (lundi, jeudi) : {jours}")
        hs = pg.evaluate("[...document.querySelectorAll('#app input[type=time]')].map(i => i.value)")
        ok(hs == ["18:00", "21:00", "08:00"], f"rappel à 18:00, heures calmes de 21:00 à 08:00 : {hs}")
        ok(pg.locator("#app button:has-text('Son et vibration')").count() == 5, "un bouton « Son et vibration » par type (Android 8 et plus)")
        ok("Son et vibration / Vibration" not in t and pg.locator("#app :text-is('Silencieux')").count() == 0, "plus de choix « Son et vibration / Vibration / Silencieux »")
        pg.locator("[data-n=repos] button:has-text('Son et vibration')").click(); pg.locator("[data-n=bilan] button:has-text('Son et vibration')").click(); pg.locator("[data-n=rappel] button:has-text('Son et vibration')").click()
        ok([c[1] for c in pg.evaluate(CALLS, "channel")] == ["repos", "programme", "rappels"], "chaque bouton ouvre le réglage Android de son canal")
        # écriture : titre de 6 mots au plus, une phrase de 15 mots au plus, le reste dans « Détails »
        cartes = pg.evaluate("[...document.querySelectorAll('#app section.card')].map(c => [c.querySelector('h2').textContent, (c.querySelector('h2 + p') || {}).textContent || ''])")
        ok(all(len(h.split()) <= 6 and len(ph.split()) <= 15 for h, ph in cartes), f"cartes courtes : {[x for x in cartes if len(x[0].split()) > 6 or len(x[1].split()) > 15]}")
        ok(pg.evaluate("[...document.querySelectorAll('#app details')].every(d => !d.open && d.querySelector('summary').getBoundingClientRect().height >= 44)"), "replis « Détails » fermés, 44 px")
        pg.evaluate(OUVRIR); t = pg.inner_text("#app")
        petits = pg.evaluate("[...document.querySelectorAll('#app button, #app input, #app summary')].filter(e => e.offsetParent).map(e => [e.textContent.trim() || e.getAttribute('aria-label'), Math.round(e.getBoundingClientRect().height), Math.round(e.getBoundingClientRect().width)]).filter(x => x[1] < 44 || x[2] < 44)")
        ok(not petits, f"cibles de 44 px au moins à 390 px : {petits}")
        ok(not INTERDIT.search(t.replace("Aucune notification sur les Esprits ni les jetons.", "")), "page : ni « raté », ni « manqué », ni Esprits (hors la phrase qui dit qu'il n'y en a pas)")
        pg.set_viewport_size({"width": 360, "height": 800}); time.sleep(.2)
        petits = pg.evaluate("[...document.querySelectorAll('#app .days .chip')].map(e => Math.round(e.getBoundingClientRect().width)).filter(w => w < 44)")
        ok(not petits and not pg.evaluate("document.documentElement.scrollWidth > innerWidth"), f"360 px : jours de 44 px, pas de défilement horizontal ({petits})")
        pg.set_viewport_size({"width": 390, "height": 844})
        # notification d'essai
        pg.click("button:has-text('Envoyer une notification d’essai')"); time.sleep(.2)
        ok(pg.evaluate(CALLS, "test") == [["test", "Notification d’essai", "Les notifications de Fonte fonctionnent."]], "notification d'essai : textes validés")
        # « Alarmes et rappels » : demandée seulement en activant la fin du repos, et seulement si elle manque
        ok(pg.evaluate(CALLS, "exact") == [], "« Alarmes et rappels » jamais demandée d'office")
        pg.evaluate("__N.exact = false"); pg.evaluate("NOTIF.onStatus()"); time.sleep(.2)
        pg.click("[data-n=repos] [role=switch]"); time.sleep(.3)
        ok(len(pg.evaluate(CALLS, "exact")) == 1, "fin du repos activée sans l'autorisation : écran « Alarmes et rappels » demandé")
        ok("la fin du repos reste dans l’appli" in pg.inner_text("#app"), "autorisation absente : la page le dit")
        pg.click("[data-n=repos] [role=switch]"); pg.evaluate("__N.exact = true"); pg.evaluate("NOTIF.onStatus()"); time.sleep(.2)
        pg.click("[data-n=repos] [role=switch]"); time.sleep(.3)
        ok(len(pg.evaluate(CALLS, "exact")) == 1 and "reste dans l’appli" not in pg.inner_text("#app"), "autorisation déjà donnée : rien n'est redemandé")
        # fin du repos : texte validé, première série non validée de l'exercice en cours
        wa = W["Séance A"]; pg.evaluate("wid => { pickWorkout(wid); go('seance'); }", wa["id"]); time.sleep(.3)
        pg.evaluate("startFocus()"); time.sleep(.2)
        e0 = pg.evaluate("(() => { const id = F.ids.filter(i => EX[i])[0]; return [id, EX[id].name, rowsFor(exF(id)).length]; })()")
        pg.evaluate("id => togDone(id, 0)", e0[0]); time.sleep(.2)
        r = pg.evaluate(CALLS, "rest")
        ok(r and r[-1][2] == "Repos terminé" and r[-1][3] == f"Prochaine série : {e0[1]}, série 2 sur {e0[2]}.", f"fin du repos : « Prochaine série : {e0[1]}, série 2 sur {e0[2]}. » ({r[-1:] if r else r})")
        pg.evaluate("go('notifications')"); time.sleep(.2); pg.click("[data-n=repos] [role=switch]"); time.sleep(.2)
        n0 = len(pg.evaluate(CALLS, "rest")); pg.evaluate("TM(60)"); time.sleep(.2)
        ok(len(pg.evaluate(CALLS, "rest")) == n0 and pg.evaluate(CALLS, "restCancel"), "fin du repos désactivée : aucune alarme, l'alarme en cours est annulée")
        # interrupteur général
        pg.click("[data-n=on] [role=switch]"); time.sleep(.6)
        ok(pg.evaluate(CALLS, "plan")[-1][1] == "", "interrupteur général coupé : plan vidé dans la coque")
        pg.click("[data-n=on] [role=switch]"); time.sleep(.6)
        last = pg.evaluate(CALLS, "plan")[-1][1]
        ok(last.split("\n")[0] == "calme\t21:00\t08:00" and len(last.split("\n")) > 1, "interrupteur rallumé : plan confié à la coque, heures calmes en tête")
        ok(all(len(l.split("\t")) == 5 for l in last.split("\n")[1:]), "chaque ligne du plan : heure, clé, canal, titre, texte")
        # réglages hors de l'export
        ex = pg.evaluate("fetch('/api/export').then(r => r.json())")
        ok("notif" not in json.dumps(list(ex.keys())) and "muscu-notif" not in json.dumps(ex), "réglages des notifications absents de l'export")
        ctx.close()

        # ---------------------------------------------------------------- Android 7 : pas de canaux, pas de bouton « Son et vibration »
        ctx, pg, errs = page(J(0), n={"sdk": 24, "exactNeeded": False}, profil={"version": 1, "created": "2026-10-20T00:00:00Z", "imported": True, "answers": {}})
        notifs(pg)
        ok(pg.locator("#app button:has-text('Son et vibration')").count() == 0 and pg.locator("#app [role=switch]").count() == 6, "Android 7 : réglages présents, sans bouton de canal")
        pg.click("[data-n=repos] [role=switch]"); time.sleep(.2)
        ok(pg.evaluate(CALLS, "exact") == [] and "reste dans l’appli" not in pg.inner_text("#app"), "Android 7 à 11 : fin du repos sans autorisation à demander")
        ctx.close()

        # ---------------------------------------------------------------- planification
        ctx, pg, errs = page(J(0))
        a = gen(pg, BASE); W = {w["name"]: w for w in a["workouts"]}
        seance(pg, J(-1), W["Séance B"]["id"])          # dernière séance : dimanche
        le(pg, J(0))
        P = pg.evaluate(PLAN)
        keys = [x["key"] for x in P]
        ok(keys == [f"rappel:{J(0)}", f"rappel:{J(3)}", f"retour:{J(-1)}"], f"lundi 10:00, dernière séance la veille : rappels lundi et jeudi, « Bon retour » le dimanche suivant, puis rien : {keys}")
        ok(all(x["h"] == 18 and x["m"] == 0 for x in P), "toutes à 18:00")
        ok(len({x["day"] for x in P}) == len(P), "une notification par jour au plus")
        r0 = P[0]
        ok(r0["title"] == "Séance A prête : " + f"{sum(1 for i in W['Séance A']['items'])} exercices" and r0["text"] == "Touche pour commencer." and r0["ch"] == "rappels",
           f"rappel : « {r0['title']} » / « {r0['text']} »")
        bon = P[-1]
        ok(bon["title"] == "Bon retour quand tu veux" and bon["day"] == J(6) and bon["ch"] == "programme", f"« Bon retour » 7 jours après la dernière séance : {bon}")
        ok(bon["text"] in ("Ta séance A est prête, à ton rythme.", "Une semaine légère t’attend, si tu veux."), f"« Bon retour » : texte validé ({bon['text']})")
        tous = " ".join(x["title"] + " " + x["text"] for x in P)
        ok(not INTERDIT.search(tous), "aucun mot « raté », « manqué », ni Esprits ou jetons")
        # heures calmes
        S = pg.evaluate("NOTIF._.settings()")
        for calme, attendu in ((["17:00", "19:00"], 0), (["21:00", "08:00"], len(P)), (["18:00", "18:30"], 0), (["18:01", "08:00"], len(P))):
            s2 = json.loads(json.dumps(S)); s2["calme"] = {"from": calme[0], "to": calme[1]}
            ok(len(pg.evaluate(PLAN, s2)) == attendu, f"heures calmes {calme[0]}-{calme[1]}, rappel à 18:00 : {attendu} notification(s)")
        s2 = json.loads(json.dumps(S)); s2["rappel"]["time"] = "07:30"
        ok(pg.evaluate(PLAN, s2) == [], "rappel à 07:30 avec les heures calmes 21:00-08:00 : rien")
        pg.evaluate("NOTIF.time('07:30')"); notifs(pg)
        ok("Cette heure tombe dans les heures calmes." in pg.inner_text("#app"), "la page signale un rappel dans les heures calmes")
        pg.evaluate("NOTIF.time('18:00')")
        # « Bon retour » une seule fois, puis plus rien
        pg.evaluate(f"__N.sent = ['retour:{J(-1)}']")
        ok([x["key"] for x in pg.evaluate(PLAN)] == [f"rappel:{J(0)}", f"rappel:{J(3)}"], "« Bon retour » déjà envoyé : pas une deuxième fois")
        pg.evaluate("__N.sent = []")
        for k in (7, 8, 12, 30):
            le(pg, J(k)); P2 = pg.evaluate(PLAN)
            ok(P2 == [], f"pause de {k + 1} jours : aucune relance ({[x['key'] for x in P2]})")
        le(pg, J(6), "19:00:00")
        ok(pg.evaluate(PLAN) == [], "dimanche 19:00, « Bon retour » passé : plus rien")
        # séance du jour faite : pas de rappel ce jour-là
        le(pg, J(0)); seance(pg, J(0), W["Séance A"]["id"]); le(pg, J(0))
        P = pg.evaluate(PLAN); keys = [x["key"] for x in P]
        ok(f"rappel:{J(0)}" not in keys and f"rappel:{J(3)}" in keys, f"séance faite aujourd'hui : pas de rappel aujourd'hui ({keys})")
        # bilan du dimanche : seulement ce qui a été fait
        bil = [x for x in P if x["key"].startswith("bilan:")]
        ok(len(bil) == 1 and bil[0]["day"] == J(6) and bil[0]["title"] == "Ta semaine : 1 séance" and bil[0]["text"].startswith("3 séries"), f"bilan du dimanche : {bil}")
        s2 = json.loads(json.dumps(pg.evaluate("NOTIF._.settings()"))); s2["rappel"]["days"] = [6]
        P3 = pg.evaluate(PLAN, s2)
        ok([x["key"] for x in P3 if x["day"] == J(6)] == [f"rappel:{J(6)}"], "dimanche avec rappel : le rappel passe, le bilan attend (une par jour)")
        le(pg, J(7)); P3 = pg.evaluate(PLAN)
        ok(not any(x["key"].startswith("bilan:") for x in P3), f"semaine sans séance : pas de bilan ({[x['key'] for x in P3]})")
        # étape du programme : passage en phase 2 prêt (phase 1 commencée il y a 4 semaines), une seule fois, au premier jour libre
        le(pg, J(0))
        pg.evaluate(f"(() => {{ const o = JSON.parse(localStorage.getItem('muscu-profil')); o.program.start = o.program.phase_start = '{J(-28)}'; o.program.phase = 1; o.program.history = [{{phase: 1, start: '{J(-28)}'}}]; o.answers.niveau = 'intermediaire'; localStorage.setItem('muscu-profil', JSON.stringify(o)); }})()")
        le(pg, J(1)); P = pg.evaluate(PLAN)
        ph = [x for x in P if x["key"].startswith("phase:")]
        ok(len(ph) == 1 and ph[0]["day"] == J(1) and ph[0]["title"] == "Phase 2 prête" and ph[0]["text"] == "Ouvre Fonte pour voir ce qui change.",
           f"phase 2 prête : un seul message sur 14 jours, le jour même (mardi, sans rappel) : {[(x['key'], x['day']) for x in ph]}")
        s2 = json.loads(json.dumps(pg.evaluate("NOTIF._.settings()"))); s2["rappel"]["days"] = [1, 2]
        P = pg.evaluate(PLAN, s2); ph = [x for x in P if x["key"].startswith("phase:")]
        ok([x["day"] for x in ph] == [J(3)] and [x["key"] for x in P if x["day"] in (J(1), J(2))] == [f"rappel:{J(1)}", f"rappel:{J(2)}"],
           f"rappels mardi et mercredi : la phase attend le jeudi, premier jour libre ({[(x['key'], x['day']) for x in P]})")
        ok(pg.evaluate("PROFIL.offers()").__len__() > 0, "(témoin : la proposition de phase existe bien sur l'accueil)")
        pg.evaluate(f"__N.sent = ['{ph[0]['key']}']")
        ok(not any(x["key"].startswith("phase:") for x in pg.evaluate(PLAN)), "étape déjà notifiée : pas une deuxième fois")
        pg.evaluate("__N.sent = []")
        s2 = json.loads(json.dumps(pg.evaluate("NOTIF._.settings()"))); s2["etapes"]["on"] = False
        ok(not any(x["key"].startswith("phase:") for x in pg.evaluate(PLAN, s2)), "étapes désactivées : rien")
        # aucune notification liée aux Esprits ni aux jetons : jetons, tirage et quêtes ne changent pas le plan
        avant = pg.evaluate(PLAN)
        pg.evaluate("(() => { const j = JSON.parse(localStorage.getItem('muscu-jeu') || '{}'); j.tokens = 50; localStorage.setItem('muscu-jeu', JSON.stringify(j)); })()"); le(pg, J(1))
        ok(pg.evaluate(PLAN) == avant, "50 jetons en réserve : plan identique, aucune notification d'Esprit")
        ok(pg.evaluate("NOTIF._.plan.toString() + NOTIF._.settings.toString()").lower().count("jeu") == 0, "le calcul du plan ne lit pas l'état du jeu")
        ok(not INTERDIT.search(" ".join(x["title"] + " " + x["text"] for x in avant)), "aucun texte d'Esprit, de jeton, de « raté » ni de « manqué »")
        ok(not errs, f"erreurs JavaScript : {errs}")
        ctx.close()
        b.close()
finally:
    srv.terminate()
ok(not sortantes, f"aucune requête sortante : {sortantes[:5]}")
print("\n" + ("Tout est bon." if not fails else f"{len(fails)} ÉCHEC(S)"))
sys.exit(1 if fails else 0)
