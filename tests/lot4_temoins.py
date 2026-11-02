# SPDX-License-Identifier: AGPL-3.0-or-later
# Témoins de tests/lot4.py : pour chaque contrôle, une règle faussée dans une COPIE du code (le dépôt n'est jamais modifié),
# puis lot4.py relancé sur cette copie (FONTE_ROOT) avec seulement la partie utile ; le contrôle visé doit échouer.
#   FONTCONFIG_FILE=/home/PM/Claude-applications/Fonte-appli/Fonte/tests/polices-chromium.conf .venv/bin/python tests/lot4_temoins.py
import os, shutil, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = "server/static/"
# (nom, fichier, texte d'origine, texte faussé, parties de lot4.py, morceau du message d'échec attendu, couleurs mesurées)
T = [
    ("import en orange", S + "index.html", '<button class="btn btn-s btn-d w" onclick="doImport()">', '<button class="btn btn-p w" onclick="doImport()">', "1", "« Remplacer mes données » en danger", ""),
    ("import dès le choix du fichier", S + "index.html", "  IMP = {name, text, o, kind, err:", "  if (kind === 'remplace') api('POST', '/api/import', o).then(load);\n  IMP = {name, text, o, kind, err:", "1", "rien n’est importé au choix du fichier", ""),
    ("confirmation de l'import retirée", S + "index.html", "if (o.format === 'suivi-muscu' && !confirm(", "if (false && !confirm(", "1", "confirmation refusée, rien ne change", ""),
    ("avertissement de l'import retiré", S + "index.html", '<div class="warn" role="note"><h3>${ico4(\'warn\')}L’import', '<div class="note" role="note"><h3>${ico4(\'warn\')}L’import', "1", "avertissement framboise visible", ""),
    ("fichier non décrit", S + "index.html", "<b>${esc(I.name || 'Texte collé')}</b>${desc ? `<span>${esc(desc)}</span>` : ''}", "<b>${esc(I.name || 'Texte collé')}</b>", "1", "fichier lu et décrit", ""),
    ("photos qui remplacent", S + "index.html", "'Ces photos s’ajoutent aux tiennes. Rien n’est remplacé.'", "'Ces photos remplacent les tiennes.'", "1", "export de photos", ""),
    ("orange depuis « Bienvenue »", S + "index.html", "imposed ? impCard() + expCard(true)", "imposed ? impCard() + expCard(false)", "1", "Données depuis « Bienvenue »", ""),
    ("Esprits retiré du menu avec l'onglet", S + "index.html", "l.filter(k => k !== 'jeu' || window.JEU)", "l.filter(k => k !== 'jeu' || jeuOn())", "1", "« Esprits » reste dans le menu", ""),
    ("pas de 5 min au lieu de 15", S + "notif.js", "onclick=\"NOTIF.shift('${k}',15)\"", "onclick=\"NOTIF.shift('${k}',5)\"", "1", "− et + de 15 min", ""),
    ("un « Son et vibration » par message", S + "notif.js", "+ CHAN('programme', 'Son et vibration de ces 3 messages', off)", "+ CHAN('programme', 'Son et vibration', off) + CHAN('programme', 'Son et vibration', off) + CHAN('programme', 'Son et vibration', off)", "1", "un seul « Son et vibration »", ""),
    ("réglages bloqués grisés par transparence", S + "index.html", ".l4 .noff .pm{background:none;", ".l4 .noff{opacity:.5}\n.l4 .noff .pm{background:none;", "1", "lisibles", ""),
    ("poids en couleur", S + "index.html", ".l4 .bw span{color:var(--m);", ".l4 .bw b{color:var(--at)}\n.l4 .bw span{color:var(--m);", "1", "poids à l’encre", ""),
    ("pesée : + sans effet", S + "profil.js", "el.value = dec(Math.max(0, Math.round((base + k * .1) * 10) / 10));", "el.value = dec(base);", "1", "+ ajoute 0,1 kg", ""),
    ("sélection à l'encre (segments)", S + "index.html", '.l3 .seg button[aria-pressed="true"]{background:var(--sel-bg);color:var(--t);box-shadow:inset 0 0 0 2px var(--sel-b)}', '.l3 .seg button[aria-pressed="true"]{background:var(--t);color:var(--bg)}', "2", "sélection teintée", "orange"),
    ("sélection pleine (onglets de séance)", S + "index.html", ".tabs button.on{background:var(--sel-bg);", ".tabs button.on{background:var(--a);", "2", "sélection teintée", "orange"),
    ("interrupteur à l'encre", S + "index.html", '.l3 .swrow[aria-checked="true"] .sw{background:var(--sel-b)}', '.l3 .swrow[aria-checked="true"] .sw{background:var(--t)}', "2", "interrupteur pas de la couleur", "orange"),
    ("ressenti choisi sans bord", S + "index.html", ".feel .feelb button.on{background:var(--sel-bg);color:var(--t);box-shadow:inset 0 0 0 2px var(--sel-b)}", ".feel .feelb button.on{background:var(--sel-bg);color:var(--t);box-shadow:none}", "2", "sans bord de la couleur", "green"),
    ("deux actions pleines (séance en liste)", S + "index.html", '<button class="sm" style="width:100%;min-height:52px" onclick="startFocus()">', '<button class="go" onclick="startFocus()">', "2", "une seule action pleine", "orange"),
    ("IMC de retour dans le détail santé", S + "profil.js", "let h = '<div class=\"hsante\">';", "let h = `<div class=\"hsante\"><p>IMC : ${dec(bmiOf(a.poids, a.taille))}</p>`;", "3", "ni « IMC » ni catégorie", ""),
    ("catégorie dans les adaptations", S + "profil.js", "'Repos un peu plus longs et cardio plus doux, d’après ta taille et ton poids.'", "'Surpoids : repos un peu plus longs et cardio plus doux.'", "3", "ni « IMC » ni catégorie", ""),
    ("ancienne question 17", S + "profil.js", "h: 'Calories, protéines, sommeil. Modifiable", "h: 'IMC, calories, protéines. Modifiable", "3", "ni « IMC » ni catégorie", ""),
    ("transitions en mouvement réduit", S + "index.html", "@media (prefers-reduced-motion:reduce){*,*::before,*::after{transition:none!important}}", "", "4", "mouvement réduit", ""),
]
fails = []
for nom, f, a, b, parties, attendu, acc in T:
    tmp = tempfile.mkdtemp(prefix="fonte-temoin4-"); shutil.copytree(os.path.join(ROOT, "server"), os.path.join(tmp, "server"), ignore=shutil.ignore_patterns("__pycache__", "*.db"))
    p = os.path.join(tmp, f); s = open(p, encoding="utf-8").read()
    if s.count(a) != 1: print("ÉCHEC", nom, ": texte d'origine introuvable ou en double (le témoin ne s'applique plus)"); fails.append(nom); continue
    open(p, "w", encoding="utf-8").write(s.replace(a, b))
    env = dict(os.environ, FONTE_ROOT=tmp, LOT4_PARTIES=parties, **({"LOT4_ACC": acc} if acc else {}))
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tests", "lot4.py")], env=env, capture_output=True, text=True, timeout=1500)
    vise = [l for l in r.stdout.splitlines() if l.startswith("ÉCHEC") and attendu in l]
    print(("OK    " if vise else "ÉCHEC "), f"témoin « {nom} » : {'le contrôle échoue' if vise else 'le contrôle ne voit rien'}" + (f" ({vise[0][7:110]}…)" if vise else ""))
    if not vise: fails.append(nom); print(r.stdout[-1500:], r.stderr[-800:])
    shutil.rmtree(tmp, ignore_errors=True)
print("\n" + (f"TOUS LES TÉMOINS ({len(T)}) FONT ÉCHOUER LEUR CONTRÔLE" if not fails else f"{len(fails)} ÉCHEC(S)"))
sys.exit(1 if fails else 0)
