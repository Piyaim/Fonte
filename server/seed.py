# SPDX-License-Identifier: AGPL-3.0-or-later
# Catalogue de départ : utilisé UNE SEULE FOIS, à la création de la base.
# Ensuite tout se modifie depuis l'onglet « Exercices » de l'appli.
#
# kind : weight = charge × reps | reps = reps (lest facultatif)
#        time   = secondes (lest facultatif) | cardio = minutes (+ niveau facultatif)
# green : repère 🟢 de ta liste
# assisted : machine à assistance (progresser = BAISSER la charge)
# Les slugs pc, di, tv, rdl, pl, gs, de, rs, lc, db, velo, tapis-incline,
# rameur, course reprennent les identifiants de l'ancienne appli HTML : c'est ce
# qui permet d'importer ton export localStorage sans rien perdre.

def ex(slug, name, grp, kind, sets, tmin, tmax, rest, focus, tip,
       green=0, per_side=0, assisted=0, diagram=None):
    return dict(slug=slug, name=name, grp=grp, kind=kind, sets=sets,
                target_min=tmin, target_max=tmax, rest=rest, focus=focus,
                tip=tip, green=green, per_side=per_side, assisted=assisted,
                diagram=diagram)

# Schémas repris tels quels de l'ancienne appli (h = têtes départ/fin,
# q = décor, a = départ en pointillés, b = fin en trait plein)
D = {
 'pc': {'h':[9,31,9,31],'q':'14,36 28,48;4,54 36,58','a':'28,48 46,28 54,40','b':'28,48 52,38 68,30'},
 'di': {'h':[14,32,14,32],'q':'12,38 40,52 50,52;18,38 36,48 44,58','a':'24,40 32,46 28,38','b':'24,40 28,20'},
 'tv': {'h':[46,16,46,16],'q':'46,24 50,44 66,44 66,58;30,6 70,6','a':'46,24 50,8','b':'46,24 38,34 42,20'},
 'rdl':{'h':[50,10,76,31],'q':'','a':'50,16 50,38 52,50 50,60;50,22 52,40','b':'70,32 46,38 50,50 48,60;70,32 68,52'},
 'pl': {'h':[-9,-9,18,30],'q':'4,58 96,58','a':'','b':'22,34 80,46 92,58;24,36 24,56'},
 'gs': {'h':[50,10,44,24],'q':'','a':'50,16 50,38 52,50 50,60;50,22 58,26','b':'44,32 36,48 56,46 50,60;44,36 54,36'},
 'de': {'h':[44,14,44,14],'q':'44,22 44,46 60,46 60,60;38,16 38,50','a':'44,22 34,32 44,24','b':'44,22 46,4'},
 'rs': {'h':[50,12,50,12],'q':'50,22 46,46 66,46 66,58','a':'50,22 76,26','b':'50,22 42,34 56,32'},
 'lc': {'h':[8,34,8,34],'q':'14,40 50,40 66,40;4,46 74,46','a':'66,40 86,42','b':'66,40 70,18'},
 'db': {'h':[14,48,14,48],'q':'22,50 50,50;4,56 96,56','a':'50,50 58,34 70,34;22,50 22,30','b':'50,50 82,50;22,50 6,50'},
}

CATALOGUE = [
 # ---------- Jambes ----------
 ex('pc','Presse à cuisses','Jambes','weight',3,10,12,90,'Quadriceps, fessiers',
    "Pieds largeur d'épaules, genoux dans l'axe, sans verrouiller les genoux.",green=1,diagram=D['pc']),
 ex('gs','Goblet squat','Jambes','weight',3,10,12,90,'Base du squat, très pédagogique',
    "Haltère contre la poitrine, talons au sol, genoux dans l'axe, dos droit.",diagram=D['gs']),
 ex('squat-smith','Squat à la Smith machine','Jambes','weight',3,8,12,120,'Trajectoire guidée',
    "Pieds légèrement devant la barre, descends en gardant le dos neutre, pousse dans les talons.",green=1),
 ex('fentes','Fentes avant / marchées (haltères)','Jambes','weight',3,10,12,90,'Fessiers, quadriceps, équilibre',
    "Grand pas, genou avant au-dessus du pied, buste droit, genou arrière frôle le sol.",per_side=1),
 ex('split-squat-bulgare','Split squat bulgare','Jambes','weight',3,8,10,90,'Plus avancé, à garder pour plus tard',
    "Pied arrière sur le banc, descente verticale, genou avant stable. Commence sans charge.",per_side=1),
 ex('leg-extension','Leg extension','Jambes','weight',3,12,15,60,'Isolation des quadriceps',
    "Dos calé, monte sans à-coup, marque une pause en haut, redescends lentement.",green=1),
 ex('lc','Leg curl assis ou couché','Jambes','weight',3,12,12,60,'Ischio-jambiers',
    "Hanches plaquées, mouvement fluide, retour lent (2-3 s).",green=1,diagram=D['lc']),
 ex('rdl','Soulevé de terre roumain','Jambes','weight',3,10,10,120,'Ischios, fessiers, dos (haltères ou barre)',
    "Dos plat, hanches vers l'arrière, charge près des jambes, genoux souples.",diagram=D['rdl']),
 ex('hip-thrust','Hip thrust (Smith ou barre)','Jambes','weight',3,10,12,90,'Fessiers',
    "Haut du dos sur le banc, menton rentré, pousse dans les talons, serre les fessiers en haut.",),
 ex('abduction','Abduction / adduction','Jambes','weight',3,12,15,60,'Hanches',
    "Dos calé, mouvement contrôlé, pas d'élan, retour lent.",green=1),
 ex('mollets','Mollets debout ou assis','Jambes','weight',3,12,15,60,'Mollets',
    "Amplitude complète : étirement en bas, pause d'une seconde en haut.",green=1),

 # ---------- Pectoraux ----------
 ex('developpe-couche','Développé couché (barre ou haltères)','Pectoraux','weight',3,8,12,120,'Référence',
    "Omoplates serrées, pieds au sol, barre au bas des pectoraux, coudes à 45°."),
 ex('di','Développé incliné haltères','Pectoraux','weight',3,10,12,90,'Haut des pectoraux',
    "Omoplates serrées, coudes à 45° du buste, descente contrôlée.",diagram=D['di']),
 ex('chest-press','Chest press machine','Pectoraux','weight',3,10,12,90,'Idéal au début',
    "Poignées à hauteur de poitrine, dos calé, pousse sans décoller les épaules.",green=1),
 ex('pompes','Pompes (au sol ou mains surélevées)','Pectoraux','reps',3,8,15,60,'Sans matériel',
    "Corps gainé et aligné, coudes à 45°, poitrine près du sol. Mains surélevées pour faciliter."),
 ex('ecartes','Écartés poulies ou pec deck','Pectoraux','weight',3,12,15,60,'Isolation',
    "Coudes légèrement fléchis et fixes, rapproche les mains en serrant les pectoraux."),
 ex('dips-assistes','Dips assistés','Pectoraux','weight',3,8,12,90,'Pectoraux, triceps',
    "Charge = assistance : progresser, c'est la baisser. Épaules basses, descente contrôlée.",green=1,assisted=1),

 # ---------- Dos ----------
 ex('tv','Tirage vertical','Dos','weight',3,10,12,90,'Grand dorsal',
    "Tire vers le haut de la poitrine, buste fixe, sans balancer.",green=1,diagram=D['tv']),
 ex('tractions-assistees','Tractions assistées','Dos','weight',3,6,10,120,'Progression vers les tractions libres',
    "Charge = assistance : progresser, c'est la baisser. Monte la poitrine vers la barre.",green=1,assisted=1),
 ex('rs','Rowing assis poulie','Dos','weight',3,10,12,90,'Milieu du dos',
    "Dos droit, coudes vers l'arrière, serre les omoplates.",green=1,diagram=D['rs']),
 ex('rowing-haltere','Rowing haltère à un bras','Dos','weight',3,10,12,60,'Dos, appui sur banc',
    "Main et genou sur le banc, dos plat, tire le coude vers la hanche.",per_side=1),
 ex('rowing-machine','Rowing machine / T-bar','Dos','weight',3,10,12,90,'Épaisseur du dos',
    "Poitrine contre l'appui, tire les coudes en arrière, pas d'à-coup.",green=1),
 ex('pull-over','Pull-over poulie haute','Dos','weight',3,12,15,60,'Dorsaux en isolation',
    "Bras presque tendus, ramène la barre vers les cuisses en gardant le buste fixe."),
 ex('extensions-lombaires','Extensions lombaires (banc à 45°)','Dos','reps',3,12,15,60,'Lombaires',
    "À faire léger et lentement. Monte jusqu'à l'alignement, jamais en hyperextension."),
 ex('face-pull','Face pull (poulie, corde)','Dos','weight',3,12,15,60,"Arrière d'épaules, posture",
    "Corde à hauteur des yeux, tire vers le visage en écartant les mains, coudes hauts."),

 # ---------- Épaules ----------
 ex('de','Développé épaules machine','Épaules','weight',3,10,12,90,'Épaules',
    "Dos calé, pousse sans cambrer, coudes non bloqués en haut.",green=1,diagram=D['de']),
 ex('developpe-militaire','Développé militaire haltères (assis)','Épaules','weight',3,8,12,90,'Épaules',
    "Dossier droit, haltères à hauteur d'oreilles, pousse sans cambrer."),
 ex('elevations-laterales','Élévations latérales (haltères ou poulie)','Épaules','weight',3,12,15,60,"Largeur d'épaules",
    "Coudes légèrement fléchis, monte jusqu'à l'horizontale, pas d'élan, charge légère."),
 ex('oiseau','Oiseau (haltères ou machine inversée)','Épaules','weight',3,12,15,60,"Arrière d'épaules",
    "Buste penché ou poitrine contre l'appui, écarte les bras en serrant les omoplates.",green=1),
 ex('elevations-frontales','Élévations frontales','Épaules','weight',3,10,12,60,'À utiliser peu',
    "Les épaules travaillent déjà beaucoup en poussée. Monte à hauteur d'épaules, sans élan."),

 # ---------- Bras ----------
 ex('curl-halteres','Curl haltères (alterné ou marteau)','Bras','weight',3,10,12,60,'Biceps',
    "Coudes collés au buste, pas de balancement, descente lente."),
 ex('curl-poulie','Curl poulie basse ou barre EZ','Bras','weight',3,10,12,60,'Biceps',
    "Coudes fixes, monte sans reculer le buste, contrôle la descente."),
 ex('preacher','Pupitre à biceps (preacher)','Bras','weight',3,10,12,60,'Biceps',
    "Aisselles calées sur le pupitre, ne tends pas brutalement en bas.",green=1),
 ex('triceps-poulie','Extensions triceps poulie haute (corde ou barre)','Bras','weight',3,12,15,60,'Triceps',
    "Coudes collés au corps, seuls les avant-bras bougent, tends complètement en bas."),
 ex('barre-front','Barre au front / extension nuque haltère','Bras','weight',3,10,12,60,'Triceps, à faire léger',
    "Coudes fixes et serrés, descente lente, charge légère pour ménager les coudes."),
 ex('dips-banc','Dips banc ou kickback','Bras','reps',3,10,15,60,'Triceps',
    "Épaules basses, descente jusqu'à 90° aux coudes, pas plus."),

 # ---------- Abdos et gainage ----------
 ex('pl','Planche','Abdos et gainage','time',3,30,30,60,'Base',
    "Corps aligné tête-talons, ventre et fessiers serrés.",diagram=D['pl']),
 ex('planche-laterale','Planche latérale','Abdos et gainage','time',3,20,30,45,'Obliques',
    "Coude sous l'épaule, hanches hautes, corps aligné.",per_side=1),
 ex('db','Dead bug','Abdos et gainage','reps',3,10,10,60,'Très sûr pour le dos',
    "Bas du dos plaqué au sol, bras et jambe opposés bougent lentement.",per_side=1,diagram=D['db']),
 ex('crunch-machine','Crunch machine ou poulie','Abdos et gainage','weight',3,12,15,60,'Grand droit',
    "Enroule le buste, les hanches ne bougent pas, expire en contractant.",green=1),
 ex('releve-genoux','Relevé de genoux suspendu (chaise romaine)','Abdos et gainage','reps',3,10,12,60,'Bas des abdos',
    "Dos calé, monte les genoux en enroulant le bassin, sans balancer."),
 ex('pallof','Pallof press (poulie)','Abdos et gainage','weight',3,10,12,45,'Anti-rotation, gainage profond',
    "De profil à la poulie, pousse les mains devant toi sans laisser le buste tourner.",per_side=1),
 ex('bird-dog','Bird dog','Abdos et gainage','reps',3,10,10,45,'Stabilité lombaire',
    "À quatre pattes, tends bras et jambe opposés, dos immobile, tiens 2 s.",per_side=1),

 # ---------- Cardio ----------
 ex('tapis-incline','Tapis incliné','Cardio','cardio',1,15,30,0,'Marche rapide en pente, doux pour les articulations',
    "Ne te tiens pas aux barres. Niveau = pente en %."),
 ex('velo','Vélo','Cardio','cardio',1,15,30,0,'Faible impact',"Selle à hauteur de hanche, jambe presque tendue en bas."),
 ex('rameur','Rameur','Cardio','cardio',1,10,20,0,'Cardio complet, soigne la technique',
    "Ordre : jambes, buste, bras ; retour dans l'ordre inverse. Dos droit."),
 ex('elliptique','Elliptique (cross-trainer)','Cardio','cardio',1,15,30,0,'Impact très faible',"Posture droite, pousse aussi avec les bras."),
 ex('stairmaster','Escalier (stairmaster)','Cardio','cardio',1,10,20,0,'Exigeant',"Commence lentement, ne t'appuie pas de tout ton poids sur les barres."),
 ex('course','Course à pied','Cardio','cardio',1,15,30,0,'Sur tapis ou en extérieur',"Allure où tu peux encore parler."),
 ex('intervalles','Intervalles','Cardio','cardio',1,10,20,0,'Ex. 30 s rapide / 90 s facile, vélo ou rameur',
    "5 min d'échauffement avant, retour au calme après."),
]

WORKOUTS = [
 ('Séance A', ['pc', 'di', 'tv', 'rdl', 'pl']),
 ('Séance B', ['gs', 'de', 'rs', 'lc', 'db']),
]

# Correspondance du sélecteur cardio de l'ancienne appli
LEGACY_CARDIO = {'Vélo': 'velo', 'Tapis incliné': 'tapis-incline',
                 'Rameur': 'rameur', 'Course': 'course'}
