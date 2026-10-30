# SPDX-License-Identifier: AGPL-3.0-or-later
# Témoins de tests/lot3.py : pour chaque contrôle, une règle faussée dans une COPIE du code (le dépôt n'est jamais modifié),
# puis lot3.py relancé sur cette copie (FONTE_ROOT) avec seulement la partie utile ; le contrôle visé doit échouer.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot3_temoins.py
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "server/static/"
# (nom, fichier, texte d'origine, texte faussé, parties de lot3.py, morceau du message d'échec attendu, couleurs mesurées)
T = [
    ("deuxième action orange (Zones)", S + "index.html", '<button class="btn-t" style="margin:4px 0 0 -8px" onclick="ZSEL.clear()', '<button class="btn btn-p" style="margin:4px 0 0 -8px" onclick="ZSEL.clear()', "3", "une action orange au plus", "orange"),
    ("boutons − et + de 36 px", S + "index.html", ".l3 .step .pm{width:48px;height:48px", ".l3 .step .pm{width:36px;height:36px", "3", "cibles de 44", "orange"),
    ("texte gris trop pâle", S + "tokens.css", "--mute:#685e55;", "--mute:#a89e95;", "3", "texte 4,5:1", "orange"),
    ("vignettes trop larges", S + "index.html", ".l3 .li .th{width:76px", ".l3 .li .th{width:476px", "3", "aucun débordement", "orange"),
    ("mot « manquée »", S + "index.html", "'<span class=\"info\">Touche au moins une zone.</span>'", "'<span class=\"info\">Séance manquée.</span>'", "3", "manqué", "orange"),
    ("ancienne couleur danger", S + "tokens.css", "--danger:#741a3a;", "--danger:#a3261b;", "3", "liens « danger »", "orange,red"),
    ("« Retirer » sans icône", S + "index.html", "${ico3('trash')}Retirer", "Retirer", "3", "liens « danger »", "orange"),
    ("numéros des étapes en framboise", S + "index.html", "color:var(--at);line-height:1.1}   /* numéros", "color:var(--danger);line-height:1.1}   /* numéros", "3", "numéros de « Comment le faire »", "orange"),
    ("santé : « Non » coché d'avance", S + "profil.js", "answers: {detail: 'non', sante: {}}", "answers: {detail: 'non', sante: {poitrine: false, vertiges: false, coeur: false, tension: false, articulaire: false, traitement: false, autre: false}}", "2", "santé", ""),
    ("santé : « Suivant » actif sans réponse", S + "profil.js", "${n < 7 ? 'disabled' : ''}", "${n < 0 ? 'disabled' : ''}", "2", "santé", ""),
    ("typographie : espaces insécables oubliés", S + "profil.js", "function view() { return typo(view0()); }", "function view() { return view0(); }", "2", "espace insécable", ""),
    ("requête sortante", S + "profil.js", "<p class=\"lead\">${QS.length} questions", "<img src=\"https://example.com/x.png\" alt=\"\"><p class=\"lead\">${QS.length} questions", "2", "aucune requête sortante", ""),
    ("attente perdue en changeant de programme", S + "index.html", "function selProg(id) { progW = id;", "function selProg(id) { PDR = {}; progW = id;", "4", "autre programme ouvert", ""),
    ("attente perdue au rechargement", S + "index.html", "let PDR = recall('muscu-prog-attente') || {};", "let PDR = {};", "4", "rechargement", ""),
    ("attente perdue à la fermeture du navigateur", S + "index.html", "let PDR = recall('muscu-prog-attente') || {};",
     "let PDR = (sessionStorage.getItem('pdr-vu') ? recall('muscu-prog-attente') : null) || {}; sessionStorage.setItem('pdr-vu', '1');", "4", "fermeture complète du navigateur", ""),
    ("séance lancée avec la version en attente", S + "index.html", "F && F.wid ? WO.find(w => w.id === F.wid) : null); }", "F && F.wid ? (PDR[F.wid] || WO.find(w => w.id === F.wid)) : null); }", "4", "version enregistrée", ""),
    ("pas de ligne neutre sur l'écran Séance", S + "index.html", "return w && progPending(w.id) ? ", "return false ? ", "4", "ligne neutre", ""),
    ("texte qui promet trop", S + "index.html", "Gardé si tu changes d’onglet ou de programme.", "Gardé même si tu fermes l’appli.", "4", "ne promet", ""),
    ("« Annuler » sans effet", S + "index.html", "function progCancel() { delete PDR[progDraft.id];", "function progCancel() {", "4", "« Annuler » efface", ""),
    ("réglage du programme oublié à l'affichage", S + "index.html", "settings: JSON.parse(JSON.stringify(w.settings || {})), base: progSnap(w)", "settings: {}, base: progSnap(w)", "1", "réglage propre au programme affiché", ""),
    ("données 0.7.1 changées à l'ouverture (serveur)", "server/app.py", "    have = {r[\"name\"] for r in c.execute(\"PRAGMA table_info(workout_item)\")}", "    c.execute(\"UPDATE session SET notes = ''\")\n    have = {r[\"name\"] for r in c.execute(\"PRAGMA table_info(workout_item)\")}", "1", "mode serveur : données de la 0.7.1 rouvertes", ""),
    ("données 0.7.1 changées à l'ouverture (local)", S + "local-backend.js", "    for (const s of w.session) for (const f of SESSION_TIMES) if (!(f in s)) { s[f] = null; changed = true; }", "    for (const s of w.session) { for (const f of SESSION_TIMES) if (!(f in s)) { s[f] = null; changed = true; } s.notes = ''; }", "1", "mode local : données de la 0.7.1 rouvertes", ""),
]
fails = []
for nom, f, a, b, parties, attendu, acc in T:
    tmp = tempfile.mkdtemp(prefix="fonte-temoin3-"); shutil.copytree(os.path.join(ROOT, "server"), os.path.join(tmp, "server"), ignore=shutil.ignore_patterns("__pycache__", "*.db"))
    p = os.path.join(tmp, f); s = open(p, encoding="utf-8").read()
    if s.count(a) != 1: print("ÉCHEC", nom, ": texte d'origine introuvable ou en double (le témoin ne s'applique plus)"); fails.append(nom); continue
    open(p, "w", encoding="utf-8").write(s.replace(a, b))
    env = dict(os.environ, FONTE_ROOT=tmp, LOT3_PARTIES=parties, **({"LOT3_ACC": acc} if acc else {}))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "lot3.py")], env=env, capture_output=True, text=True, timeout=1500)
    vise = [l for l in r.stdout.splitlines() if l.startswith("ÉCHEC") and attendu in l]
    print(("OK    " if vise else "ÉCHEC "), f"témoin « {nom} » : {'le contrôle échoue' if vise else 'le contrôle ne voit rien'}" + (f" ({vise[0][7:110]}…)" if vise else ""))
    if not vise: fails.append(nom); print(r.stdout[-1500:], r.stderr[-800:])
    shutil.rmtree(tmp, ignore_errors=True)
print("\n" + (f"TOUS LES TÉMOINS ({len(T)}) FONT ÉCHOUER LEUR CONTRÔLE" if not fails else f"{len(fails)} ÉCHEC(S)"))
sys.exit(1 if fails else 0)
