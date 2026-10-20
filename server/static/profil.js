// SPDX-License-Identifier: AGPL-3.0-or-later
/* Fonte : questionnaire de départ, profil et programme généré (lot 1).
   - Le questionnaire s'affiche au lancement tant que le profil n'existe pas. Il n'efface aucune donnée.
   - Réponses en cours : localStorage « muscu-profil-brouillon », enregistrées à chaque saisie (quitter ne perd rien).
   - Profil validé : localStorage « muscu-profil » (version 1). Il suit l'export et l'import, comme l'état du jeu.
   - Le programme passe par les routes existantes : séries, répétitions et repos sont des champs de l'exercice
     (/api/exercises), un programme ne porte que l'ordre des exercices (/api/workouts).
   Conseils d'entraînement généraux : ce n'est ni un avis médical, ni une table validée par un professionnel. */
(function () {
  'use strict';
  const KEY = 'muscu-profil', DKEY = 'muscu-profil-brouillon';
  const A = () => window.APPX;
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  const dec = (v, d = 1) => String(Math.round(v * 10 ** d) / 10 ** d).replace('.', ',');
  const kcal = v => String(Math.round(v / 10) * 10).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const get = k => { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } };
  const put = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, JSON.stringify(v)); } catch (e) {} };
  const nowIso = () => new Date().toISOString();

  /* ------------------------------------------------------------------ bibliothèque d'exercices
     Pour chaque exercice du catalogue de départ (slug) : schéma moteur, type (poly = polyarticulaire, iso = isolation),
     matériel (l'un ou l'autre suffit), niveau (1 à 3), impact, zones à protéger, remplaçant.
     Lignes « PDF » : schéma, matériel, niveau et remplaçant viennent du cahier des charges. Tout le reste, dont toutes
     les contre-indications et tous les impacts, est une proposition À RELIRE PAR UN PROFESSIONNEL (non validée médicalement).
     Les exercices créés par l'utilisateur sont absents de cette table : le générateur les ignore. */
  const LIB = {
    'pc':                   ['squat',       'poly', ['machine'],                    1, 'faible', ['genoux', 'dos'],     'gs'],                   // PDF
    'gs':                   ['squat',       'poly', ['halteres'],                   1, 'faible', ['genoux'],            'pc'],                   // PDF
    'squat-smith':          ['squat',       'poly', ['smith'],                      2, 'faible', ['genoux', 'dos'],     'pc'],                   // PDF
    'fentes':               ['fente',       'poly', ['halteres', 'pdc'],            2, 'faible', ['genoux', 'hanches'], 'pc'],                   // PDF
    'split-squat-bulgare':  ['fente',       'poly', ['halteres', 'pdc'],            3, 'faible', ['genoux', 'hanches'], 'fentes'],
    'leg-extension':        ['iso-jambes',  'iso',  ['machine'],                    1, 'faible', ['genoux'],            'pc'],                   // PDF
    'lc':                   ['iso-jambes',  'iso',  ['machine'],                    1, 'faible', [],                    'rdl'],                  // PDF
    'rdl':                  ['charniere',   'poly', ['halteres', 'barre'],          2, 'faible', ['dos'],               'lc'],                   // PDF
    'hip-thrust':           ['charniere',   'poly', ['smith', 'barre'],             2, 'faible', ['hanches'],           'lc'],                   // PDF
    'abduction':            ['iso-jambes',  'iso',  ['machine'],                    1, 'faible', ['hanches'],           'hip-thrust'],
    'mollets':              ['iso-jambes',  'iso',  ['machine', 'halteres', 'pdc'], 1, 'faible', [],                    null],
    'developpe-couche':     ['poussee-h',   'poly', ['barre', 'halteres'],          2, 'faible', ['epaules', 'poignets'], 'chest-press'],
    'di':                   ['poussee-h',   'poly', ['halteres'],                   2, 'faible', ['epaules'],           'chest-press'],          // PDF
    'chest-press':          ['poussee-h',   'poly', ['machine'],                    1, 'faible', [],                    'pompes'],               // PDF
    'pompes':               ['poussee-h',   'poly', ['pdc'],                        1, 'faible', ['poignets'],          'chest-press'],
    'ecartes':              ['iso-pecs',    'iso',  ['poulie', 'machine'],          1, 'faible', ['epaules'],           'chest-press'],
    'dips-assistes':        ['poussee-v',   'poly', ['machine'],                    2, 'faible', ['epaules'],           'chest-press'],
    'tv':                   ['tirage-v',    'poly', ['poulie'],                     1, 'faible', [],                    'tractions-assistees'],  // PDF
    'tractions-assistees':  ['tirage-v',    'poly', ['machine'],                    2, 'faible', ['epaules'],           'tv'],
    'rs':                   ['tirage-h',    'poly', ['poulie'],                     1, 'faible', [],                    'rowing-haltere'],       // PDF
    'rowing-haltere':       ['tirage-h',    'poly', ['halteres'],                   1, 'faible', [],                    'rs'],
    'rowing-machine':       ['tirage-h',    'poly', ['machine'],                    1, 'faible', [],                    'rs'],
    'pull-over':            ['iso-dos',     'iso',  ['poulie'],                     2, 'faible', ['epaules'],           'tv'],
    'extensions-lombaires': ['charniere',   'iso',  ['machine'],                    1, 'faible', ['dos'],               'bird-dog'],
    'face-pull':            ['tirage-h',    'iso',  ['poulie'],                     1, 'faible', [],                    'oiseau'],               // PDF
    'de':                   ['poussee-v',   'poly', ['machine'],                    1, 'faible', ['epaules'],           'developpe-militaire'],  // PDF
    'developpe-militaire':  ['poussee-v',   'poly', ['halteres'],                   2, 'faible', ['epaules', 'dos'],    'de'],
    'elevations-laterales': ['iso-epaules', 'iso',  ['halteres', 'poulie'],         1, 'faible', ['epaules'],           'oiseau'],
    'oiseau':               ['iso-epaules', 'iso',  ['halteres', 'machine'],        1, 'faible', [],                    'face-pull'],
    'elevations-frontales': ['iso-epaules', 'iso',  ['halteres'],                   1, 'faible', ['epaules'],           'elevations-laterales'],
    'curl-halteres':        ['iso-bras',    'iso',  ['halteres'],                   1, 'faible', [],                    'curl-poulie'],          // PDF
    'curl-poulie':          ['iso-bras',    'iso',  ['poulie', 'barre'],            1, 'faible', [],                    'curl-halteres'],
    'preacher':             ['iso-bras',    'iso',  ['machine'],                    1, 'faible', ['poignets'],          'curl-poulie'],
    'triceps-poulie':       ['iso-bras',    'iso',  ['poulie'],                     1, 'faible', [],                    'dips-assistes'],        // PDF
    'barre-front':          ['iso-bras',    'iso',  ['barre', 'halteres'],          2, 'faible', ['poignets'],          'triceps-poulie'],
    'dips-banc':            ['iso-bras',    'iso',  ['pdc', 'halteres'],            1, 'faible', ['epaules', 'poignets'], 'triceps-poulie'],
    'pl':                   ['tronc',       'poly', ['pdc'],                        1, 'faible', [],                    'db'],                   // PDF
    'planche-laterale':     ['tronc',       'poly', ['pdc'],                        2, 'faible', ['epaules'],           'pl'],
    'db':                   ['tronc',       'poly', ['pdc'],                        1, 'faible', [],                    'pl'],                   // PDF
    'crunch-machine':       ['tronc',       'iso',  ['machine', 'poulie'],          1, 'faible', ['dos'],               'db'],
    'releve-genoux':        ['tronc',       'iso',  ['machine'],                    2, 'faible', ['dos'],               'db'],
    'pallof':               ['tronc',       'poly', ['poulie'],                     2, 'faible', [],                    'planche-laterale'],     // PDF
    'bird-dog':             ['tronc',       'poly', ['pdc'],                        1, 'faible', [],                    'db'],
    'tapis-incline':        ['cardio',      null,   ['cardio'],                     1, 'faible', [],                    'velo'],                 // PDF
    'velo':                 ['cardio',      null,   ['cardio'],                     1, 'faible', [],                    'elliptique'],           // PDF
    'rameur':               ['cardio',      null,   ['cardio'],                     1, 'faible', ['dos'],               'velo'],                 // PDF
    'elliptique':           ['cardio',      null,   ['cardio'],                     1, 'faible', [],                    'velo'],                 // PDF
    'stairmaster':          ['cardio',      null,   ['cardio'],                     2, 'moyen',  ['genoux'],            'velo'],
    'course':               ['cardio',      null,   ['pdc'],                        2, 'eleve',  ['genoux', 'hanches'], 'velo'],
    'intervalles':          ['cardio',      null,   ['cardio'],                     2, 'moyen',  [],                    'velo']
  };
  const FROM_PDF = ['pc', 'gs', 'squat-smith', 'fentes', 'rdl', 'hip-thrust', 'leg-extension', 'lc', 'chest-press', 'di', 'de', 'tv', 'rs',
    'face-pull', 'curl-halteres', 'triceps-poulie', 'pl', 'db', 'pallof', 'tapis-incline', 'velo', 'rameur', 'elliptique'];
  const LIEUX = {complete: ['machine', 'smith', 'poulie', 'halteres', 'barre', 'pdc', 'cardio'], machines: ['machine', 'smith', 'poulie', 'pdc', 'cardio'],
    halteres: ['halteres', 'pdc'], pdc: ['pdc']};

  /* ------------------------------------------------------------------ structure des séances
     Une séance = des emplacements par ordre de priorité. On prend les premiers selon la durée ; en phase 1, pas
     d'isolation (le bloc complémentaire commence en phase 2). Chaque emplacement essaie ses exercices dans l'ordre. */
  const S = (label, role, c) => ({label, role, c});
  const SQ = 'Jambes (squat)', PU = 'Poussée', TI = 'Tirage', TR = 'Tronc', CH = 'Charnière de hanche', FE = 'Fente';
  const FB_A = [S(SQ, 'main', ['pc', 'squat-smith', 'gs', 'fentes']), S(PU, 'main', ['di', 'chest-press', 'developpe-couche', 'pompes']),
    S(TI, 'main', ['tv', 'tractions-assistees', 'rowing-haltere', 'rs']), S(TR, 'core', ['pl', 'db', 'bird-dog', 'planche-laterale']),
    S(CH, 'main', ['rdl', 'hip-thrust', 'lc']), S('Isolation des épaules', 'iso', ['elevations-laterales', 'oiseau']),
    S('Isolation des bras', 'iso', ['curl-halteres', 'curl-poulie', 'preacher'])];
  const FB_B = [S(SQ, 'main', ['gs', 'pc', 'squat-smith', 'fentes']), S(PU, 'main', ['de', 'developpe-militaire', 'chest-press', 'pompes']),
    S(TI, 'main', ['rs', 'rowing-machine', 'rowing-haltere', 'tv']), S(TR, 'core', ['db', 'pl', 'bird-dog', 'planche-laterale']),
    S(CH, 'main', ['lc', 'rdl', 'hip-thrust']), S('Isolation des bras', 'iso', ['triceps-poulie', 'dips-banc', 'barre-front']),
    S('Mollets', 'iso', ['mollets'])];
  const HAUT = [S('Poussée horizontale', 'main', ['di', 'chest-press', 'developpe-couche', 'pompes']), S('Tirage vertical', 'main', ['tv', 'tractions-assistees', 'rowing-haltere']),
    S(TR, 'core', ['pl', 'db', 'bird-dog']), S('Tirage horizontal', 'main', ['rs', 'rowing-machine', 'rowing-haltere']),
    S('Poussée verticale', 'main', ['de', 'developpe-militaire', 'pompes']), S('Isolation des épaules', 'iso', ['elevations-laterales', 'oiseau']),
    S('Isolation des bras', 'iso', ['curl-halteres', 'curl-poulie', 'triceps-poulie'])];
  const BAS = [S(SQ, 'main', ['pc', 'squat-smith', 'gs', 'fentes']), S(CH, 'main', ['rdl', 'hip-thrust', 'lc']), S(TR, 'core', ['db', 'pl', 'bird-dog']),
    S(FE, 'main', ['fentes', 'gs', 'split-squat-bulgare']), S('Charnière de hanche (2)', 'main', ['hip-thrust', 'rdl']),
    S('Isolation des jambes', 'iso', ['lc', 'leg-extension']), S('Mollets', 'iso', ['mollets', 'abduction'])];
  const PUSH = [S('Poussée horizontale', 'main', ['di', 'chest-press', 'developpe-couche', 'pompes']), S('Poussée verticale', 'main', ['de', 'developpe-militaire']),
    S(TR, 'core', ['pl', 'planche-laterale', 'db']), S('Poussée horizontale (2)', 'main', ['chest-press', 'pompes', 'developpe-couche']),
    S('Dips', 'main', ['dips-assistes', 'pompes']), S('Isolation des épaules', 'iso', ['elevations-laterales', 'elevations-frontales']),
    S('Isolation des triceps', 'iso', ['triceps-poulie', 'dips-banc', 'barre-front'])];
  const PULL = [S('Tirage vertical', 'main', ['tv', 'tractions-assistees', 'rowing-haltere']), S('Tirage horizontal', 'main', ['rs', 'rowing-machine', 'rowing-haltere']),
    S(TR, 'core', ['db', 'bird-dog', 'pl']), S('Tirage horizontal (2)', 'main', ['rowing-machine', 'rowing-haltere', 'rs']),
    S('Tirage vertical (2)', 'main', ['tractions-assistees', 'tv']), S('Arrière des épaules', 'iso', ['face-pull', 'oiseau']),
    S('Isolation des biceps', 'iso', ['curl-halteres', 'curl-poulie', 'preacher'])];
  const LEGS = [S(SQ, 'main', ['gs', 'pc', 'squat-smith', 'fentes']), S(FE, 'main', ['fentes', 'split-squat-bulgare', 'gs']), S(TR, 'core', ['pallof', 'pl', 'db']),
    S(CH, 'main', ['rdl', 'hip-thrust', 'lc']), S('Charnière de hanche (2)', 'main', ['hip-thrust', 'rdl']),
    S('Isolation des quadriceps', 'iso', ['leg-extension']), S('Mollets', 'iso', ['mollets'])];
  const HAUT2 = [S('Poussée horizontale', 'main', ['chest-press', 'di', 'pompes']), S('Tirage vertical', 'main', ['tv', 'tractions-assistees', 'rowing-haltere']),
    S(TR, 'core', ['planche-laterale', 'pl', 'db']), S('Tirage horizontal', 'main', ['rowing-machine', 'rs', 'rowing-haltere']),
    S('Poussée verticale', 'main', ['developpe-militaire', 'de', 'pompes']), S('Arrière des épaules', 'iso', ['oiseau', 'elevations-laterales']),
    S('Isolation des bras', 'iso', ['curl-poulie', 'curl-halteres', 'triceps-poulie'])];
  const BAS2 = [S(SQ, 'main', ['squat-smith', 'pc', 'gs', 'fentes']), S(CH, 'main', ['hip-thrust', 'rdl', 'lc']), S(TR, 'core', ['bird-dog', 'db', 'pl']),
    S(FE, 'main', ['fentes', 'gs']), S('Charnière de hanche (2)', 'main', ['rdl', 'hip-thrust']),
    S('Isolation des ischios', 'iso', ['lc', 'leg-extension']), S('Hanches', 'iso', ['abduction', 'mollets'])];
  const STRUCT = {
    2: [['Séance A', FB_A], ['Séance B', FB_B]], 3: [['Séance A', FB_A], ['Séance B', FB_B]],
    4: [['Haut du corps', HAUT], ['Bas du corps', BAS]],
    5: [['Poussée', PUSH], ['Tirage', PULL], ['Jambes', LEGS], ['Haut du corps', HAUT2], ['Bas du corps', BAS2]]
  };
  const STRUCT_TXT = {2: 'Corps entier : séances A et B en alternance.', 3: 'Corps entier : A, B, A une semaine, puis B, A, B la suivante.',
    4: 'Haut du corps et bas du corps, deux fois chacun dans la semaine.', 5: 'Poussée, tirage, jambes, puis haut et bas du corps.'};
  const NB_EX = {30: 4, 45: 5, 60: 6, 75: 7};
  const CARDIO_MIN = {30: [5, 10], 45: [10, 15], 60: [15, 20], 75: [20, 20]};
  const EASY_CARDIO = ['velo', 'tapis-incline', 'elliptique', 'rameur', 'stairmaster', 'course'];

  /* séries, répétitions (ou secondes), repos : phase 1 commune à tous les objectifs, phase 2 selon l'objectif */
  const PRM = {
    p1:         {poly: [3, 10, 12, 90], hinge: [3, 10, 10, 120], iso: [3, 12, 12, 60]},
    muscle:     {poly: [3, 8, 12, 90],  hinge: [3, 8, 12, 120],  iso: [3, 10, 12, 60]},
    force:      {poly: [4, 4, 6, 150],  hinge: [4, 4, 6, 180],   iso: [3, 8, 10, 90]},
    endurance:  {poly: [3, 15, 20, 45], hinge: [3, 15, 20, 60],  iso: [3, 15, 20, 30]},
    athletique: {poly: [3, 8, 12, 90],  hinge: [3, 8, 10, 120],  iso: [3, 10, 12, 60]},
    gras:       {poly: [3, 10, 15, 60], hinge: [3, 10, 15, 60],  iso: [3, 12, 15, 45]},
    forme:      {poly: [3, 10, 12, 90], hinge: [3, 10, 12, 90],  iso: [3, 10, 12, 60]}
  };
  const CORE = {p1: {time: [3, 30, 30, 60], reps: [3, 10, 10, 60], weight: [3, 10, 12, 60]},
    p2: {time: [3, 30, 45, 60], reps: [3, 10, 12, 60], weight: [3, 12, 15, 60]}};
  /* phase 3 (hybride) : trois séances ondulatoires par objectif. PROPOSITION DE CLAUDE, À VALIDER PAR GEORGIO.
     force = charges lourdes, peu de répétitions ; volume = volume et endurance ; puissance = montée rapide avec une
     charge modérée (la bibliothèque n'a aucun saut), puis le cardio le plus long. Le tronc garde les valeurs de phase 2. */
  const PRM3 = {
    muscle:     {force: {poly: [4, 5, 7, 150], hinge: [4, 5, 7, 180], iso: [3, 8, 10, 90]},  volume: {poly: [3, 10, 12, 75], hinge: [3, 10, 12, 90], iso: [3, 12, 15, 60]},
                 puissance: {poly: [4, 4, 6, 120], hinge: [4, 4, 6, 150], iso: [3, 10, 12, 60]}},
    force:      {force: {poly: [5, 3, 5, 180], hinge: [5, 3, 5, 180], iso: [3, 6, 8, 90]},   volume: {poly: [3, 8, 10, 120], hinge: [3, 8, 10, 120], iso: [3, 10, 12, 60]},
                 puissance: {poly: [5, 3, 3, 150], hinge: [5, 3, 3, 150], iso: [2, 8, 10, 60]}},
    endurance:  {force: {poly: [3, 6, 8, 120], hinge: [3, 6, 8, 120], iso: [2, 10, 12, 60]}, volume: {poly: [3, 15, 20, 45], hinge: [3, 15, 20, 60], iso: [3, 15, 20, 30]},
                 puissance: {poly: [3, 6, 8, 90], hinge: [3, 6, 8, 90], iso: [2, 12, 15, 45]}},
    athletique: {force: {poly: [4, 4, 6, 150], hinge: [4, 4, 6, 180], iso: [3, 8, 10, 90]},  volume: {poly: [3, 10, 12, 75], hinge: [3, 10, 12, 90], iso: [3, 12, 15, 45]},
                 puissance: {poly: [4, 3, 5, 120], hinge: [4, 3, 5, 150], iso: [3, 10, 12, 60]}},
    gras:       {force: {poly: [3, 6, 8, 120], hinge: [3, 6, 8, 120], iso: [3, 10, 12, 60]}, volume: {poly: [3, 12, 15, 45], hinge: [3, 12, 15, 60], iso: [3, 15, 15, 45]},
                 puissance: {poly: [3, 6, 8, 90], hinge: [3, 6, 8, 90], iso: [3, 12, 15, 45]}},
    forme:      {force: {poly: [3, 6, 8, 120], hinge: [3, 6, 8, 120], iso: [3, 10, 12, 60]}, volume: {poly: [3, 12, 15, 60], hinge: [3, 12, 15, 75], iso: [3, 12, 15, 45]},
                 puissance: {poly: [3, 6, 8, 90], hinge: [3, 6, 8, 90], iso: [3, 10, 12, 60]}}
  };
  const TYPES = ['force', 'volume', 'puissance'];   // phase 3 : le programme n° i prend le type TYPES[i % 3]
  const TYPE_TXT = {force: 'force', volume: 'volume et endurance', puissance: 'puissance et cardio'};
  const START = {jamais: 1, reprise: 1, debutant: 1, intermediaire: 2, avance: 3};   // phase de départ selon le niveau déclaré
  // saut et kettlebell swing : aucun dans la bibliothèque aujourd'hui ; s'il en arrive un, il est marqué ici
  const PLIO = new Set(['kettlebell-swing', 'box-jump', 'sauts', 'burpees', 'jumping-jacks']);

  /* ------------------------------------------------------------------ questionnaire */
  const OBJ = [['muscle', 'Prendre du muscle'], ['gras', 'Perdre du gras'], ['force', 'Gagner en force'], ['endurance', 'Améliorer l’endurance'],
    ['athletique', 'Corps athlétique (muscle et cardio)'], ['forme', 'Remise en forme générale']];
  const SANTE = [['poitrine', 'As-tu une douleur à la poitrine pendant un effort ?'], ['vertiges', 'As-tu des vertiges ou des malaises ?'],
    ['coeur', 'As-tu un problème cardiaque connu ?'], ['tension', 'As-tu une tension élevée ?'],
    ['articulaire', 'As-tu une douleur articulaire qui limite l’effort ?'], ['traitement', 'Suis-tu un traitement médical en ce moment ?'],
    ['autre', 'As-tu une autre raison de ne pas faire d’effort ?']];
  const JOURS = [['lun', 'Lundi'], ['mar', 'Mardi'], ['mer', 'Mercredi'], ['jeu', 'Jeudi'], ['ven', 'Vendredi'], ['sam', 'Samedi'], ['dim', 'Dimanche']];
  const ZONES_CI = ['epaules', 'dos', 'genoux', 'hanches', 'poignets'];
  const QS = [
    {k: 'prenom', t: 'text', q: 'Comment t’appelles-tu ?', h: 'Facultatif. Ton prénom sert seulement à personnaliser l’appli.', opt: true, s: 'Prénom'},
    {k: 'age', t: 'num', q: 'Quel âge as-tu ?', unit: 'ans', min: 16, max: 75, int: true, s: 'Âge', err: 'Indique un âge entre 16 et 75 ans.'},
    {k: 'sexe', t: 'one', q: 'Quel est ton sexe ?', h: 'Facultatif. Sert uniquement à estimer tes besoins caloriques.', opt: true, s: 'Sexe',
      o: [['f', 'Femme'], ['h', 'Homme'], ['nr', 'Je préfère ne pas répondre']]},
    {k: 'taille', t: 'num', q: 'Quelle est ta taille ?', unit: 'cm', min: 120, max: 230, int: true, s: 'Taille', err: 'Indique une taille entre 120 et 230 cm.'},
    {k: 'poids', t: 'num', q: 'Quel est ton poids ?', unit: 'kg', min: 30, max: 250, h: 'Une décimale possible, par exemple 72,5.', s: 'Poids', err: 'Indique un poids entre 30 et 250 kg.'},
    {k: 'objectif', t: 'one', q: 'Quel est ton objectif principal ?', o: OBJ, s: 'Objectif principal'},
    {k: 'objectifs2', t: 'multi', q: 'As-tu des objectifs secondaires ?', h: 'Choisis 1 ou 2 réponses.', max: 2, s: 'Objectifs secondaires',
      o: [...OBJ, ['mobilite', 'Mobilité et posture']]},
    {k: 'niveau', t: 'one', q: 'Où en es-tu aujourd’hui ?', s: 'Niveau',
      o: [['jamais', 'Jamais pratiqué'], ['reprise', 'Reprise après un arrêt de plus d’un an'], ['debutant', 'Débutant (moins de 6 mois)'],
        ['intermediaire', 'Intermédiaire (6 mois à 2 ans)'], ['avance', 'Avancé (plus de 2 ans)']]},
    {k: 'passe', t: 'multi', q: 'Quel est ton passé sportif ?', h: 'Plusieurs réponses possibles.', none: 'aucun', s: 'Passé sportif',
      o: [['club', 'Sport en club dans l’enfance'], ['scolaire', 'Sport scolaire seulement'], ['muscu', 'Musculation'], ['endurance', 'Sport d’endurance'],
        ['collectif', 'Sport collectif'], ['aucun', 'Aucun']]},
    {k: 'seances', t: 'one', q: 'Combien de séances par semaine ?', s: 'Séances par semaine', o: [[2, '2 séances'], [3, '3 séances'], [4, '4 séances'], [5, '5 séances']]},
    {k: 'duree', t: 'one', q: 'Combien de temps dure une séance ?', s: 'Durée d’une séance', o: [[30, '30 minutes'], [45, '45 minutes'], [60, '60 minutes'], [75, '75 minutes']]},
    {k: 'lieu', t: 'one', q: 'Où t’entraînes-tu ?', s: 'Lieu',
      o: [['complete', 'Salle complète'], ['machines', 'Salle (machines uniquement)'], ['halteres', 'Haltères à la maison'], ['pdc', 'Poids du corps seulement']]},
    {k: 'blessures', t: 'multi', q: 'As-tu des blessures ou des douleurs ?', h: 'Plusieurs réponses possibles. L’appli écarte les exercices déconseillés pour ces zones.',
      none: 'aucune', s: 'Blessures ou douleurs',
      o: [['aucune', 'Aucune'], ['epaules', 'Épaules'], ['dos', 'Dos et lombaires'], ['genoux', 'Genoux'], ['hanches', 'Hanches'], ['poignets', 'Poignets et coudes'], ['autre', 'Autre']]},
    {k: 'sante', t: 'sante', q: 'Questionnaire de santé', h: 'Réponds par oui ou par non à chaque question.', s: 'Questionnaire de santé'},
    {k: 'eviter', t: 'eviter', q: 'Y a-t-il des exercices que tu veux éviter ?', h: 'Facultatif. Touche les exercices à écarter de ton programme.', opt: true, s: 'Exercices à éviter'},
    {k: 'jours', t: 'multi', q: 'Quels jours es-tu disponible ?', s: 'Jours disponibles', o: JOURS},
    {k: 'detail', t: 'one', q: 'Veux-tu voir le détail santé (IMC, besoins caloriques, protéines, repères nutrition) ?', s: 'Détail santé',
      h: 'Tu pourras changer d’avis plus tard dans « Mon profil ».', o: [['non', 'Non, juste mon programme'], ['oui', 'Oui, montre-moi le détail']]}
  ];
  const QI = Object.fromEntries(QS.map((q, i) => [q.k, i]));

  const parseNum = v => { if (typeof v === 'number') return v; const s = String(v ?? '').trim().replace(',', '.'); return /^\d+(\.\d+)?$/.test(s) ? +s : NaN; };
  function check(q, a) {   // message d'erreur, ou '' si la réponse convient
    const v = a[q.k];
    if (q.t === 'text') { const s = String(v || '').trim(); return !s || (s.length >= 2 && s.length <= 30) ? '' : 'Le prénom doit faire entre 2 et 30 caractères.'; }
    if (q.t === 'num') {
      const t = String(v ?? '').trim().replace(',', '.'), n = parseNum(v);
      if (!(n >= q.min && n <= q.max)) return q.err;
      return (q.int ? /^\d+$/ : /^\d+(\.\d)?$/).test(t) ? '' : q.int ? q.err + ' Sans décimale.' : q.err + ' Une seule décimale.';
    }
    if (q.t === 'one') return q.opt || q.o.some(o => o[0] === v) ? '' : 'Choisis une réponse.';
    if (q.t === 'multi') {
      const l = Array.isArray(v) ? v : [];
      if (!l.length) return q.k === 'jours' ? `Choisis au moins ${a.seances || 1} jour${(a.seances || 1) > 1 ? 's' : ''}.` : 'Choisis au moins une réponse.';
      if (q.k === 'jours' && a.seances && l.length < a.seances) return `Choisis au moins ${a.seances} jours : tu as prévu ${a.seances} séances par semaine.`;
      if (q.max && l.length > q.max) return `${q.max} réponses au maximum.`;
      return '';
    }
    if (q.t === 'sante') return SANTE.every(([k]) => a.sante && typeof a.sante[k] === 'boolean') ? '' : 'Réponds aux 7 questions.';
    return '';
  }
  function clean(a) {   // réponses validées, dans leur forme enregistrée
    const o = Object.assign({}, a);
    o.prenom = String(a.prenom || '').trim();
    ['age', 'taille', 'poids'].forEach(k => { o[k] = parseNum(a[k]); });
    o.poids = Math.round(o.poids * 10) / 10;
    o.sexe = a.sexe || null;
    o.blessures_autre = (a.blessures || []).includes('autre') ? String(a.blessures_autre || '').trim().slice(0, 200) : '';
    o.eviter = (a.eviter || []).filter(s => LIB[s]);
    return o;
  }

  /* ------------------------------------------------------------------ IMC et indicateurs */
  function bmiOf(kg, cm) { const m = cm / 100; return Math.round(kg / (m * m) * 10 + 1e-9) / 10; }   // arrondi à une décimale
  function bmiBand(b) {
    if (b < 18.5) return {k: 'insuf', t: 'Insuffisance pondérale', fx: 'Cardio à la durée basse. La prise de muscle est conseillée en priorité, avec une légère hausse calorique.'};
    if (b < 25) return {k: 'normal', t: 'Corpulence normale', fx: 'Aucun ajustement lié à l’IMC.'};
    if (b < 30) return {k: 'surpoids', t: 'Surpoids', fx: 'Cardio à faible impact en premier choix, progression des charges habituelle.'};
    if (b < 35) return {k: 'obe1', t: 'Obésité modérée', fx: 'Cardio à faible impact (vélo, marche inclinée, elliptique), sans sauts ni course.'};
    return {k: 'obe2', t: 'Obésité sévère', fx: 'Cardio à faible impact (vélo, marche inclinée, elliptique), sans sauts ni course. Avant de commencer, un avis médical est conseillé.'};
  }
  function energy(a) {   // formule de Mifflin-St Jeor ; rien sans réponse sur le sexe
    if (a.sexe !== 'f' && a.sexe !== 'h') return null;
    const mb = 10 * a.poids + 6.25 * a.taille - 5 * a.age + (a.sexe === 'h' ? 5 : -161);
    const f = a.seances >= 5 ? 1.725 : a.seances === 4 ? 1.55 : 1.375;
    return {mb, need: mb * f, f};
  }

  /* ------------------------------------------------------------------ génération du programme */
  function bySlug() {
    const m = {}; Object.values(A().EX()).forEach(e => { if (!e.archived && LIB[e.slug]) m[e.slug] = e; }); return m;
  }
  function context(a0, phase) {   // phase : celle du programme en cours, sinon celle de départ du niveau déclaré
    const a = clean(a0), bmi = bmiOf(a.poids, a.taille), sante = SANTE.some(([k]) => a.sante && a.sante[k] === true);
    return {a, bmi, sante, minor: a.age < 18, phase: phase || START[a.niveau] || 1,
      inj: (a.blessures || []).filter(z => ZONES_CI.includes(z)), avoid: new Set(a.eviter || []), lieu: new Set(LIEUX[a.lieu] || []),
      maxLevel: ['jamais', 'reprise', 'debutant'].includes(a.niveau) ? 2 : 3, lowImpact: sante || bmi >= 30, ex: bySlug()};
  }
  function usable(slug, x) {   // l'exercice peut-il entrer dans le programme ? (les blessures sont traitées à part)
    const L = LIB[slug];
    if (!L || !x.ex[slug] || x.avoid.has(slug)) return false;
    if (!L[2].some(m => x.lieu.has(m)) || L[3] > x.maxLevel) return false;
    if (x.lowImpact && L[4] !== 'faible') return false;                         // IMC de 30 ou plus, ou « Oui » santé
    if (x.sante && (slug === 'intervalles' || slug === 'course')) return false;  // jamais d'intervalles ni de course avec un « Oui » santé
    if (x.minor && slug === 'intervalles') return false;                          // profils protégés : cardio continu et facile
    if (PLIO.has(slug) && (x.phase < 3 || x.bmi >= 30)) return false;            // ni sauts ni kettlebell swings avant la phase 3, ni avec un IMC de 30 ou plus
    return true;
  }
  const hurts = (slug, x) => LIB[slug][5].filter(z => x.inj.includes(z));
  const ZL = {epaules: 'épaules', dos: 'dos', genoux: 'genoux', hanches: 'hanches', poignets: 'poignets et coudes'};
  // « même type » : même famille de schéma moteur (poussée horizontale ou verticale, tirage horizontal ou vertical, etc.)
  const family = slug => { const s = LIB[slug][0]; return s.startsWith('poussee') ? 'poussee' : s.startsWith('tirage') ? 'tirage' : s; };
  const FAM = {squat: 'Squat', fente: 'Fente', poussee: 'Poussée', tirage: 'Tirage', charniere: 'Charnière de hanche', tronc: 'Tronc', cardio: 'Cardio',
    'iso-jambes': 'Isolation des jambes', 'iso-pecs': 'Isolation des pectoraux', 'iso-dos': 'Isolation du dos', 'iso-epaules': 'Isolation des épaules', 'iso-bras': 'Isolation des bras'};
  const ZP = {epaules: 'aux épaules', dos: 'au dos', genoux: 'aux genoux', hanches: 'aux hanches', poignets: 'aux poignets ou aux coudes'};
  const zonePhrase = z => z.map(k => ZP[k]).join(' et ');
  const exName = (slug, x) => x.ex[slug] ? x.ex[slug].name : slug;
  function buildWorkout(name, slots, x, usedAll) {
    const w = {name, items: [], missing: [], notes: [], removed: []}, picked = [];
    for (const s of slots.filter(s => x.phase > 1 || s.role !== 'iso').slice(0, NB_EX[x.a.duree])) {
      const free = s.c.filter(sl => usable(sl, x) && !picked.some(p => p.slug === sl));
      let slug = free.find(sl => !usedAll.has(sl)) || free[0];
      if (!slug) { w.missing.push(s.label); continue; }
      const z = hurts(slug, x);
      if (z.length) {   // blessure : le remplaçant, sinon un autre exercice du même type, sinon rien (jamais un exercice déconseillé)
        const fit = sl => usable(sl, x) && !hurts(sl, x).length && !picked.some(p => p.slug === sl);
        const r = LIB[slug][6], zt = z.map(k => ZL[k]).join(', ');
        const pool = [...new Set([...s.c, ...Object.keys(LIB).filter(k => family(k) === family(slug))])].filter(fit);
        const alt = r && fit(r) ? r : pool.find(sl => !usedAll.has(sl)) || pool[0];
        if (!alt) { w.notes.push(`${FAM[family(slug)]} : aucun exercice de ce type ne convient à ta blessure ${zonePhrase(z)}. Demande conseil à un professionnel de santé.`); w.removed.push(s.label); continue; }
        w.notes.push(`à la place de ${exName(slug, x)} : ${exName(alt, x)} (${zt}).`); slug = alt;
      }
      picked.push({slug, role: s.role});
    }
    const rank = {main: 0, iso: 1, core: 2};
    w.items = picked.map((p, i) => [p, i]).sort((a, b) => rank[a[0].role] - rank[b[0].role] || a[1] - b[1]).map(([p]) => p);
    return w;
  }
  function cardioMinutes(x) {
    const [lo, hi] = CARDIO_MIN[x.a.duree];
    if (x.a.objectif === 'gras' || x.a.objectif === 'endurance') return [hi, hi];
    if (x.a.objectif === 'force' || x.bmi < 18.5) return [lo, lo];
    return [lo, hi];
  }
  function cardioFor(i, x, n) {
    // intervalles en fin de 1re séance (phase 2), ou de la séance « puissance et cardio » (phase 3 ; la dernière s'il n'y a que 2 programmes) ; jamais pour un profil protégé
    const intervals = x.phase > 1 && (x.a.objectif === 'endurance' || x.a.objectif === 'athletique') && i === (x.phase === 3 ? Math.min(2, n - 1) : 0) && usable('intervalles', x) && !hurts('intervalles', x).length;
    if (intervals) return 'intervalles';
    const easy = EASY_CARDIO.filter(s => usable(s, x) && !hurts(s, x).length);
    return easy.length ? easy[i % easy.length] : null;
  }
  function params(slug, x, type) {   // type : séance de phase 3 (force, volume, puissance)
    const L = LIB[slug], e = x.ex[slug];
    if (L[0] === 'cardio') {
      const [lo, hi] = x.cardio, m = x.phase === 3 ? {force: [lo, lo], puissance: [hi, hi]}[type] || [lo, hi] : [lo, hi];
      return {sets: 1, min: m[0], max: m[1], rest: 0};
    }
    let r;
    if (L[0] === 'tronc') {
      r = CORE[x.phase === 1 ? 'p1' : 'p2'][e.kind === 'time' ? 'time' : e.kind === 'reps' ? 'reps' : 'weight'].slice();
      if (x.phase > 1 && (x.a.objectif === 'endurance' || x.a.objectif === 'gras')) r[3] = 45;
    } else {
      const cat = L[1] === 'iso' ? 'iso' : L[0] === 'charniere' ? 'hinge' : 'poly';
      r = (x.phase === 3 ? PRM3[x.a.objectif][type || 'force'] : PRM[x.phase === 1 ? 'p1' : x.a.objectif])[cat].slice();
    }
    if ((x.minor || x.sante) && r[1] < 8) { r[1] = 8; r[2] = Math.max(r[2], 10); }   // pas de répétitions maximales
    if (x.sante) r[0] = 2;                                                            // programme allégé
    if (x.bmi >= 30 && r[3] > 0) r[3] = Math.min(180, r[3] + 30);                    // IMC de 30 ou plus : repos +30 s, 3 min au plus
    return {sets: r[0], min: r[1], max: r[2], rest: r[3]};
  }
  function plan(a0, phase) {
    const x = context(a0, phase); x.cardio = cardioMinutes(x);
    const usedAll = new Set(), workouts = STRUCT[x.a.seances].map(([name, slots], i) => {
      const w = buildWorkout(name, slots, x, usedAll);
      w.items.forEach(p => usedAll.add(p.slug));
      const c = cardioFor(i, x, STRUCT[x.a.seances].length);
      if (c) w.items.push({slug: c, role: 'cardio'}); else w.missing.push('Cardio');
      w.type = x.phase === 3 ? TYPES[i % 3] : null; w.prm = {};
      w.items.forEach(p => { w.prm[p.slug] = params(p.slug, x, w.type); });
      return w;
    });
    const prm = {};   // réglages par exercice (le premier programme qui le contient) : identiques partout hors phase 3
    workouts.forEach(w => w.items.forEach(p => { if (!prm[p.slug]) prm[p.slug] = w.prm[p.slug]; }));
    return {x, workouts, prm};
  }

  /* ------------------------------------------------------------------ textes */
  const restTxt = r => r < 120 ? `${r} s` : `${Math.floor(r / 60)} min${r % 60 ? ' ' + (r % 60) : ''}`;
  function prmTxt(e, p) {
    const rg = p.min === p.max ? `${p.min}` : `${p.min} à ${p.max}`;
    if (e.kind === 'cardio') return `${rg} min`;
    return `${p.sets} × ${rg}${e.kind === 'time' ? ' s' : ''}${e.per_side ? ' par côté' : ''} · repos ${restTxt(p.rest)}`;
  }
  function phaseTxt(phase, niveau) {
    if (phase === 1) return niveau === 'debutant' ? 'Phase 1 raccourcie : 2 semaines de réadaptation (charges légères, 2 à 3 répétitions en réserve, jamais jusqu’à l’échec), puis phase 2.'
      : 'Phase 1 : réadaptation, 4 semaines. Technique et tendons : charges légères, 2 à 3 répétitions en réserve, jamais jusqu’à l’échec, tempo 2-0-1 (descente en 2 s, montée en 1 s).';
    if (phase === 2) return 'Phase 2 : progression. 1 à 2 répétitions en réserve ; ajoute de la charge dès que toutes les séries sont réussies.';
    return 'Phase 3 : hybride. Chaque séance a son rôle : force, volume et endurance, ou puissance et cardio (montée rapide avec une charge modérée).';
  }
  function adaptations(pl) {   // ce que l'appli adapte, sans jugement ; l'IMC n'est nommé que si le détail santé est affiché
    const x = pl.x, a = x.a, out = [], show = a.detail === 'oui';
    out.push(phaseTxt(x.phase, a.niveau));
    if (x.phase < 3) out.push('Le passage à la phase suivante te sera proposé sur l’accueil, au bon moment : rien ne change sans ton accord.');
    if (x.phase === 3) out.push(pl.workouts.map(w => `${w.name} : ${TYPE_TXT[w.type]}`).join(' ; ') + '.');
    if (x.sante) out.push('Programme allégé (2 séries par exercice), sans effort maximal, sans intervalles ni course.');
    if (x.minor) out.push('Charges légères et technique d’abord, sans répétitions maximales, cardio continu et facile.');
    if (x.bmi >= 30 && !x.sante) out.push(show ? 'IMC de 30 ou plus : cardio à faible impact, sans sauts ni course.' : 'Cardio à faible impact, sans sauts ni course.');
    else if (x.bmi < 18.5 && show) out.push('IMC sous 18,5 : cardio à la durée basse.');
    if (x.bmi >= 30) out.push(show ? 'IMC de 30 ou plus : repos allongés de 30 s (3 min au plus).' : 'Repos allongés de 30 s (3 min au plus).');
    const notes = [...new Set(pl.workouts.flatMap(w => w.notes))];
    notes.forEach(t => out.push(t.startsWith('à la place') ? 'Blessure ou douleur : ' + t : t));
    if ((a.blessures || []).includes('autre')) out.push(`Pour la douleur « ${a.blessures_autre || 'autre'} », l’appli ne peut pas adapter le programme toute seule : écarte les exercices concernés à la question « Exercices à éviter » et demande conseil à un professionnel de santé.`);
    if (x.avoid.size) out.push(`${x.avoid.size} exercice${x.avoid.size > 1 ? 's' : ''} écarté${x.avoid.size > 1 ? 's' : ''} à ta demande.`);
    if (a.objectif === 'endurance' && x.phase > 1) out.push('Le circuit prévu pour l’endurance arrivera dans une prochaine version.');
    if (pl.workouts.some(w => w.items.some(p => p.slug === 'intervalles'))) out.push('Intervalles en fin de première séance : par exemple 30 s rapides, 90 s faciles.');
    return out.filter(Boolean);
  }
  function missingTxt(pl) {
    const m = {};
    pl.workouts.forEach(w => w.missing.forEach(l => (m[l] = m[l] || []).push(w.name)));
    return Object.entries(m).map(([l, ws]) => `${l} (${ws.join(', ')})`);
  }
  const WARN = '<div class="qwarn"><p>Cette appli ne remplace pas un avis médical. En cas de doute, consulte un médecin avant de commencer.</p><p>Arrête l’exercice en cas de douleur vive, de vertige ou de gêne à la poitrine.</p></div>';
  const SANTE_WARN = '<div class="qwarn" role="alert"><p><b>Consulte un médecin avant de commencer.</b></p><p>Tu as répondu « Oui » à une question de santé. L’appli te proposera un programme allégé, sans effort maximal ni intervalles.</p></div>';
  const MINOR_WARN = '<div class="qwarn"><p><b>Tu as moins de 18 ans.</b> Demande l’accord d’un parent et, si possible, fais-toi encadrer. Charges légères, la technique d’abord.</p></div>';
  function healthBlock(a0) {
    const a = clean(a0), b = bmiOf(a.poids, a.taille), band = bmiBand(b), en = energy(a);
    let h = `<div class="card"><h2>Détail santé</h2><p class="qbig"><b>IMC : ${dec(b)}</b> · ${band.t}</p><p class="m">L’IMC est un repère général. Il ne distingue pas le muscle de la graisse.</p><p>Ce que l’appli adapte : ${esc(band.fx)}</p>`;
    if (en) {
      h += `<p>Dépense de base estimée : <b>${kcal(en.mb)} kcal</b> par jour. Besoin quotidien estimé : <b>${kcal(en.need)} kcal</b> (${a.seances} séances par semaine).</p>`;
      const g = {muscle: [200, 300, 1], gras: [300, 500, -1]}[a.objectif];
      if (g) h += `<p>${g[2] > 0 ? 'Prise de muscle : légère hausse' : 'Perte de gras : léger déficit'} d’environ ${g[0]} à ${g[1]} kcal, soit ${kcal(en.need + g[2] * g[0])} à ${kcal(en.need + g[2] * g[1])} kcal par jour.</p>`;
      else if (a.objectif === 'forme') h += '<p>Remise en forme : calories d’équilibre, autour de ton besoin quotidien.</p>';
    } else h += '<p class="m">Sans réponse sur le sexe, l’appli n’estime pas le besoin calorique.</p>';
    h += `<p>Protéines : 1,6 à 2 g par kg de poids de corps et par jour, soit ${Math.round(a.poids * 1.6)} à ${Math.round(a.poids * 2)} g.</p><p>Sommeil : vise 7 à 8 heures par nuit.</p>`;
    return h + '<p class="m">Les recommandations nutritionnelles sont des repères généraux, pas un régime personnalisé.</p></div>';
  }
  function answerTxt(q, a) {
    const v = a[q.k], lab = val => (q.o.find(o => o[0] === val) || [, ''])[1];
    if (q.t === 'text') return String(v || '').trim() || 'Non renseigné';
    if (q.t === 'num') { const n = parseNum(v); return isNaN(n) ? 'À compléter' : `${dec(n)} ${q.unit}`; }
    if (q.t === 'one') return v == null ? (q.opt ? 'Non renseigné' : 'À compléter') : lab(v);
    if (q.t === 'multi') { const l = (v || []).map(lab); if (q.k === 'blessures' && (v || []).includes('autre') && a.blessures_autre) l[l.length - 1] += ` (${a.blessures_autre})`; return l.join(', ') || 'À compléter'; }
    if (q.t === 'sante') { if (check(q, a)) return 'À compléter'; const n = SANTE.filter(([k]) => a.sante[k]).length; return n ? `${n} réponse${n > 1 ? 's' : ''} « Oui »` : 'Tout « Non »'; }
    if (q.t === 'eviter') { const n = (v || []).length; return n ? (v || []).map(s => exName(s, {ex: bySlug()})).join(', ') : 'Aucun'; }
    return '';
  }

  /* ------------------------------------------------------------------ progression (lot 2B)
     État rangé dans le profil (même clé, version 1, champs ajoutés ; il suit donc l'export et l'import) :
     - program.ids : programmes générés, dans l'ordre ; program.start : début du programme ; program.phase_start : début de la phase ;
       program.history : phases acceptées. Sans ids valides (programmes supprimés, renommés avant la migration, ou gardés), phases
       et placement restent inactifs.
     - cycle.light : semaines allégées et reprises acceptées [{kind, start, end}] ; cycle.later : date à partir de laquelle une
       proposition reportée (« Plus tard ») revient.
     Rien ne compte les séances non faites : seul l'écart depuis la dernière séance déclenche une proposition. */
  const DAY = 864e5;
  const dn = iso => { const [y, m, d] = iso.split('-').map(Number); return Date.UTC(y, m - 1, d) / DAY; };
  const addD = (iso, k) => new Date((dn(iso) + k) * DAY).toISOString().slice(0, 10);
  const dow = iso => (new Date(dn(iso) * DAY).getUTCDay() + 6) % 7;   // lundi = 0
  const monday = iso => addD(iso, -dow(iso));
  const localDay = ms => { const d = new Date(ms); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
  const frDay = (iso, opt) => new Date(dn(iso) * DAY).toLocaleDateString('fr-FR', Object.assign({weekday: 'long', day: 'numeric', month: 'long', timeZone: 'UTC'}, opt));
  const todayIso = () => A().today();
  const DOW = {lun: 0, mar: 1, mer: 2, jeu: 3, ven: 4, sam: 5, dim: 6};

  function upgrade() {   // profil d'avant le lot 2B : retrouve les programmes générés par leur nom (ordre de génération)
    const o = get(KEY); if (!valid(o) || !o.program || Array.isArray(o.program.ids)) return;
    const WO = A().WO(), ids = (o.program.workouts || []).map(n => (WO.find(w => w.name === n) || {}).id);
    if (!ids.length || ids.some(id => id == null) || new Set(ids).size !== ids.length) return;   // essayé de nouveau au prochain lancement
    const st = localDay(Date.parse(o.program.generated) || Date.parse(o.created) || Date.now());
    o.program = Object.assign({}, o.program, {ids, start: st, phase_start: st, history: [{phase: o.program.phase, start: st}]});
    put(KEY, o);
  }
  function managed(o) {   // programme généré dont tous les programmes existent encore, questionnaire rempli
    if (o && o.program && !Array.isArray(o.program.ids)) { upgrade(); o = profile(); }   // profil d'avant le lot 2B arrivé par un import
    const p = o && o.program;
    if (!filled(o) || !p || !Array.isArray(p.ids) || !p.ids.length || !p.start) return null;
    const WO = A().WO(); return p.ids.every(id => WO.some(w => w.id === id)) ? p : null;
  }
  const cycleOf = o => Object.assign({light: [], later: {}}, o.cycle || {});
  function lastDay(t) { const d = A().SESS().map(s => s.day).filter(x => x <= t).sort(); return d[d.length - 1] || null; }
  function lightNow(o, t) { return cycleOf(o).light.filter(l => l.start <= t && t <= l.end).pop() || null; }
  function cycleStart(o) {
    const c = cycleOf(o), p = o.program && o.program.start ? [o.program.start] : [];
    return [localDay(Date.parse(o.created) || 0), ...p, ...c.light.map(l => addD(l.end, 1))].sort().pop();
  }
  const P1_DAYS = lvl => lvl === 'debutant' ? 14 : 28;
  const P2_FROM = lvl => ({debutant: 14, intermediaire: 0, avance: 0}[lvl] ?? 28);   // jour du programme où la phase 2 commence normalement
  function phaseOffer(o, t) {
    const p = managed(o); if (!p) return null;
    const lvl = o.answers.niveau, d = dn(t) - dn(p.phase_start || p.start);
    if (p.phase === 1 && d >= P1_DAYS(lvl)) return {k: 'phase', to: 2};
    if (p.phase === 2 && (lvl === 'avance' || d >= 84 - P2_FROM(lvl))) return {k: 'phase', to: 3};   // phase 2 jusqu'à la semaine 12
    return null;
  }
  function offers(t) {   // propositions du jour, par ordre de priorité : reprise, semaine allégée, passage de phase
    t = t || todayIso();
    const o = profile(); if (!o) return [];
    const c = cycleOf(o), last = lastDay(t), gap = last ? dn(t) - dn(last) : null, out = [];
    const free = k => !c.later[k] || c.later[k] <= t, after = c.light.some(l => last && l.start > last);
    if (gap !== null && gap >= 22 && !after) { if (free('reprise')) out.push({k: 'reprise'}); }   // plus de 3 semaines sans séance
    else if (gap !== null && !lightNow(o, t) && free('allegee')) {
      if (gap >= 8 && !after) out.push({k: 'allegee', why: 'pause'});                         // une semaine entière sans séance
      else if (gap <= 7) { const st = cycleStart(o); if (dn(t) - dn(st) >= 35 && last >= st) out.push({k: 'allegee', why: 'cycle'}); }   // toutes les 5 à 6 semaines
    }
    const ph = phaseOffer(o, t); if (ph && free('phase')) out.push(ph);
    return out;
  }
  const typeOf = (i, phase) => phase === 3 ? TYPES[i % 3] : null;
  function phaseSettings(o, to) {   // nouveaux réglages des programmes générés ; seuls les exercices de la bibliothèque changent
    const p = managed(o), x = context(o.answers, to), EX = A().EX(); x.cardio = cardioMinutes(x);
    return p.ids.map((wid, i) => {
      const w = A().WO().find(v => v.id === wid), settings = JSON.parse(JSON.stringify(w.settings || {})), type = typeOf(i, to);
      w.items.forEach(id => { const e = EX[id]; if (!e || !LIB[e.slug] || !x.ex[e.slug]) return; const n = params(e.slug, x, type); settings[id] = {sets: n.sets, target_min: n.min, target_max: n.max, rest: n.rest}; });
      return {w, type, settings};
    });
  }
  let BUSY = false;
  async function accept(k) {
    const o = profile(), t = todayIso(); if (!o || BUSY) return;
    const c = cycleOf(o);
    if (k === 'phase') {
      const ph = phaseOffer(o, t); if (!ph) return;
      BUSY = true;
      try {
        for (const {w, settings} of phaseSettings(o, ph.to)) await A().api('PUT', `/api/workouts/${w.id}`, {name: w.name, items: w.items, settings});
        o.program = Object.assign({}, o.program, {phase: ph.to, phase_start: t, history: [...(o.program.history || []), {phase: ph.to, start: t}]});
      } catch (e) { BUSY = false; await A().load(); A().toast('Changement de phase interrompu : ' + e.message); A().R(); return; }
      BUSY = false; await A().load();
    } else c.light = [...c.light, {kind: k, start: t, end: addD(t, 6)}];
    delete c.later[k]; o.cycle = c; o.updated = nowIso(); put(KEY, o);
    A().toast({phase: 'Nouvelle phase enregistrée : réglages de tes séances mis à jour.', allegee: 'Semaine allégée lancée pour 7 jours.', reprise: 'Reprise en douceur lancée pour 7 jours.'}[k]);
    A().R();
  }
  function later(k) {
    const o = profile(); if (!o) return;
    const c = cycleOf(o); c.later = Object.assign({}, c.later, {[k]: addD(todayIso(), 7)}); o.cycle = c; put(KEY, o);
    A().toast('D’accord, on t’en reparle dans 7 jours.'); A().R();
  }

  /* placement sur les jours choisis (question 16) : pour 3 séances A, B, A puis B, A, B ; jamais deux jours de suite pour un
     même groupe musculaire quand c'est possible (le tronc et les lombaires ne comptent pas, le cardio non plus) */
  function groupsOf(wid) {
    const w = A().WO().find(v => v.id === wid), EX = A().EX(), z = new Set();
    (w ? w.items : []).forEach(id => { const e = EX[id]; if (e && !e.archived && e.kind !== 'cardio') A().zonesOf(e).p.forEach(k => { if (k !== 'abdos' && k !== 'lombaires') z.add(k); }); });
    return z;
  }
  function seqFor(n, k, wk) { return Array.from({length: n}, (_, i) => k === 2 && n % 2 ? (i + wk) % 2 : i % k); }
  function combos(a, n) { if (!n) return [[]]; if (a.length < n) return []; const [h, ...r] = a; return [...combos(r, n - 1).map(c => [h, ...c]), ...combos(r, n)]; }
  function weekPlan(o, p, mon) {
    const days = [...new Set((o.answers.jours || []).map(j => DOW[j]).filter(d => d !== undefined))].sort((a, b) => a - b);
    const n = Math.min(o.answers.seances || p.ids.length, days.length), k = p.ids.length;
    if (!n) return [];
    const wk = Math.round((dn(mon) - dn(monday(p.start))) / 7), seq = seqFor(n, k, wk), nxt = seqFor(n, k, wk + 1), G = p.ids.map(groupsOf);
    const share = (i, j) => i === j || [...G[i]].some(z => G[j].has(z));
    let best = null, bs = Infinity;
    for (const c of combos(days, n)) {
      let conf = 0, spread = 0;
      for (let i = 0; i < n; i++) {
        const gap = i < n - 1 ? c[i + 1] - c[i] : c[0] + 7 - c[n - 1];
        if (gap === 1 && share(seq[i], i < n - 1 ? seq[i + 1] : nxt[0])) conf++;
        spread += (gap - 7 / n) ** 2;
      }
      const sc = conf * 1000 + spread;
      if (sc < bs - 1e-9) { bs = sc; best = c; }
    }
    return best.map((d, i) => ({day: addD(mon, d), wid: p.ids[seq[i]]}));
  }
  function schedule(t) {   // null sans questionnaire rempli ni programme généré : l'accueil garde « la séance qui suit la dernière faite »
    t = t || todayIso();
    const o = profile(), p = managed(o); if (!p || !Array.isArray(o.answers.jours)) return null;
    const mon = monday(t), slots = [...weekPlan(o, p, mon), ...weekPlan(o, p, addD(mon, 7))];
    if (!slots.length) return null;
    const td = slots.find(s => s.day === t), done = td && A().SESS().some(s => s.day === t && s.workout_id === td.wid);
    return {today: td && !done ? td : null, planned: !!td, next: slots.find(s => s.day > t), week: slots.filter(s => s.day < addD(mon, 7))};
  }
  function coach(t) {   // ce qu'il faut au conseil de charge
    t = t || todayIso();
    const o = profile(), p = managed(o), c = o ? cycleOf(o) : {light: []};
    return {phase: p ? p.phase : null, light: o ? lightNow(o, t) : null, periods: c.light};
  }

  /* cartes : accueil (sous le bouton de séance) et « Mon profil » */
  function offerCard(f, o) {
    const p = o.program, t = todayIso();
    let title, body;
    if (f.k === 'reprise') { title = 'Bon retour ! On reprend en douceur.'; body = '<p>Pendant 7 jours, l’appli te propose environ 80 % de tes dernières charges. Ensuite, la progression reprend normalement.</p>'; }
    else if (f.k === 'allegee') {
      title = f.why === 'pause' ? 'Bon retour ! Une semaine plus légère pour reprendre le rythme.' : 'Semaine allégée';
      body = (f.why === 'pause' ? '' : '<p>Tu t’entraînes régulièrement depuis 5 semaines : bravo ! Une semaine plus légère aide le corps à récupérer, et donc à progresser.</p>')
        + '<p>Charges environ 20 % plus basses, même nombre de séances. Elle se termine seule au bout de 7 jours.</p>';
    } else {
      const lst = phaseSettings(o, f.to), EX = A().EX();
      title = f.to === 2 ? 'Passer à la phase 2 : progression' : 'Passer à la phase 3 : hybride';
      body = `<p>${f.to === 2 ? `Tes ${P1_DAYS(o.answers.niveau) / 7} semaines de réadaptation sont faites : bravo !` : 'Tes semaines de progression sont faites : bravo !'} ${esc(phaseTxt(f.to, o.answers.niveau))}</p>`
        + lst.map(({w, type, settings}) => { const id = w.items.find(i => EX[i] && LIB[EX[i].slug] && LIB[EX[i].slug][0] !== 'cardio' && LIB[EX[i].slug][0] !== 'tronc'), s = id && settings[id];
          return `<div class="qex"><b>${esc(w.name)}${type ? ' : ' + TYPE_TXT[type] : ''}</b>${s ? `<span>par exemple ${esc(EX[id].name)} : ${esc(prmTxt(EX[id], {sets: s.sets, min: s.target_min, max: s.target_max, rest: s.rest}))}</span>` : ''}</div>`; }).join('')
        + '<p class="m">Seuls les réglages de tes séances changent (séries, répétitions, repos) : tes exercices et ton historique restent les mêmes.</p>';
    }
    return `<section class="card offer" data-offer="${f.k}"><h2>${esc(title)}</h2>${body}<div class="offb"><button class="go" onclick="PROFIL.accept('${f.k}')">Accepter</button><button class="sm" onclick="PROFIL.later('${f.k}')">Plus tard</button></div></section>`;
  }
  function lightCard(l) {
    return `<section class="card offer" data-light="${l.kind}"><h2>${l.kind === 'reprise' ? 'Reprise en douceur' : 'Semaine allégée'}</h2><p>${l.kind === 'reprise' ? 'Environ 80 % de tes dernières charges' : 'Charges environ 20 % plus basses'}, jusqu’au ${esc(frDay(l.end))} inclus. Le conseil de charge de chaque exercice en tient compte.</p></section>`;
  }
  function homeCards() {   // une seule carte à la fois : la semaine allégée ou la reprise en cours, sinon la première proposition
    const o = profile(); if (!o) return '';
    const t = todayIso(), l = lightNow(o, t); if (l) return lightCard(l);
    const f = offers(t)[0]; return f ? offerCard(f, o) : '';
  }
  function progressHtml(o) {   // bloc « Ta progression » de « Mon profil »
    const t = todayIso(), p = managed(o), l = lightNow(o, t), fs = offers(t), sch = schedule(t);
    let h = '<div class="card"><h2>Ta progression</h2>';
    if (p) {
      const wk = Math.floor((dn(t) - dn(p.phase_start || p.start)) / 7) + 1;
      h += `<p><b>Phase ${p.phase}</b> depuis le ${esc(frDay(p.phase_start || p.start, {weekday: undefined}))} (semaine ${wk}).</p><p class="m">${esc(phaseTxt(p.phase, o.answers.niveau))}</p>`;
      if (p.phase === 3) h += `<p class="m">${p.ids.map((id, i) => { const w = A().WO().find(v => v.id === id); return `${esc(w.name)} : ${TYPE_TXT[typeOf(i, 3)]}`; }).join(' ; ')}.</p>`;
      if (sch) h += `<p>Cette semaine : ${sch.week.map(s => `${esc(frDay(s.day, {day: undefined, month: undefined}))} ${esc((A().WO().find(w => w.id === s.wid) || {}).name || '')}`).join(', ')}.</p>`;
    } else h += '<p class="m">Phases et placement sur tes jours : ils fonctionnent avec un programme généré par l’appli.</p>';
    h += '</div>';
    if (l) h += lightCard(l);
    return h + fs.map(f => offerCard(f, o)).join('');
  }

  /* ------------------------------------------------------------------ état de l'écran */
  const valid = o => !!(o && o.version === 1 && o.answers && typeof o.answers === 'object');
  const profile = () => { const o = get(KEY); return valid(o) ? o : null; };
  // profil créé par un import sans profil : questionnaire non rempli (jamais imposé, toujours proposé dans « Mon profil »)
  const filled = o => !!(o && !o.imported && !QS.some(q => check(q, o.answers)));
  let D = null;                       // brouillon : {version, answers, mode, i, redo}
  let P = {mode: 'home', ret: false, err: '', plan: null, busy: false};
  const fresh = () => ({version: 1, answers: {detail: 'non', sante: {}}, mode: 'intro', i: 0, redo: false});
  const saveD = () => put(DKEY, D);
  function draft() { if (!D) { D = get(DKEY); if (!D || D.version !== 1 || !D.answers) D = null; } return D; }
  const render = () => { A().R(); window.scrollTo(0, 0); setTimeout(() => { const t = document.getElementById('qh'); if (t) t.focus({preventScroll: true}); }, 0); };
  function to(mode, i) {
    P.mode = mode; P.err = '';
    if (D && ['intro', 'q', 'resume'].includes(mode)) { D.mode = mode; if (i !== undefined) D.i = i; saveD(); }
    render();
  }

  function init() {   // vrai si le questionnaire doit s'imposer
    upgrade();
    if (profile()) { P.mode = 'home'; return false; }
    if (!draft()) { D = fresh(); saveD(); }
    D.redo = false; P.mode = D.mode || 'intro'; return true;
  }
  function enter() {   // ouverture de « Mon profil » depuis le menu
    if (profile() && !['q', 'resume'].includes(P.mode)) P.mode = 'home';
  }
  function title() {
    return {intro: 'Bienvenue', q: 'Questionnaire', resume: 'Résumé', confirm: 'Confirmation', done: 'Ton programme'}[P.mode] || (profile() ? 'Mon profil' : 'Bienvenue');
  }

  /* ---------- saisies */
  function typed(v) {
    const q = QS[D.i]; D.answers[q.k] = v; saveD();
    if (q.k === 'age') { const n = parseNum(v), el = document.getElementById('qlive'); if (el) el.innerHTML = n >= 16 && n < 18 ? MINOR_WARN : ''; }
  }
  function typedOther(v) { D.answers.blessures_autre = v.slice(0, 200); saveD(); }
  function pick(j) {
    const q = QS[D.i]; D.answers[q.k] = q.o[j][0];
    if (q.k === 'objectif' && Array.isArray(D.answers.objectifs2)) D.answers.objectifs2 = D.answers.objectifs2.filter(v => v !== q.o[j][0]);
    P.err = ''; saveD(); A().R();
  }
  function tog(j) {
    const q = QS[D.i], v = q.o[j][0], l = (D.answers[q.k] || []).slice(), at = l.indexOf(v);
    P.err = '';
    if (at >= 0) l.splice(at, 1);
    else if (q.none && v === q.none) l.splice(0, l.length, v);
    else {
      if (q.none) { const n = l.indexOf(q.none); if (n >= 0) l.splice(n, 1); }
      if (q.max && l.length >= q.max) P.err = `${q.max} réponses au maximum : retire d’abord une réponse.`; else l.push(v);
    }
    D.answers[q.k] = q.o.map(o => o[0]).filter(x => l.includes(x)); saveD(); A().R();
  }
  function yn(k, v) { D.answers.sante = Object.assign({}, D.answers.sante, {[k]: v}); P.err = ''; saveD(); A().R(); }
  function togEv(slug) {
    const l = (D.answers.eviter || []).slice(), at = l.indexOf(slug);
    if (at >= 0) l.splice(at, 1); else l.push(slug);
    D.answers.eviter = l; saveD(); A().R();
  }
  function next() {
    const q = QS[D.i], e = check(q, D.answers);
    if (e) { P.err = e; A().R(); const el = document.getElementById('qerr'); if (el) el.scrollIntoView({block: 'center'}); return; }
    if (q.t === 'num') D.answers[q.k] = parseNum(D.answers[q.k]);
    if (q.t === 'text') D.answers[q.k] = String(D.answers[q.k] || '').trim();
    if (P.ret || D.i >= QS.length - 1) { P.ret = false; return to('resume'); }
    to('q', D.i + 1);
  }
  function back() {
    if (P.ret) { P.ret = false; return to('resume'); }
    if (D.i > 0) return to('q', D.i - 1);
    if (D.redo) return quit();
    to('intro');
  }
  function edit(i) { P.ret = true; to('q', i); }
  function start() { to('q', 0); }
  function setDetail(on) {
    if (P.mode === 'home') { const o = profile(); if (o) { o.answers.detail = on ? 'oui' : 'non'; o.updated = nowIso(); put(KEY, o); } }
    else { D.answers.detail = on ? 'oui' : 'non'; saveD(); }
    A().R();
  }
  // phase pour générer : jamais en recul (la phase du programme en cours si elle est plus avancée que celle de départ du niveau)
  function phaseFor(a) { const o = profile(), p = o && o.program; return Math.max(START[a.niveau] || 1, p && p.phase || 0); }
  function generate() {
    const bad = QS.findIndex(q => check(q, D.answers));
    if (bad >= 0) { P.ret = true; to('q', bad); P.err = check(QS[bad], D.answers); A().R(); return; }
    P.plan = plan(D.answers, phaseFor(D.answers)); to('confirm');
  }
  function redo() {
    const o = profile();
    if (!draft() || !D.redo) { D = fresh(); if (o && !o.imported) D.answers = JSON.parse(JSON.stringify(o.answers)); D.redo = true; D.i = 0; }
    D.mode = D.mode === 'intro' ? 'q' : D.mode; saveD(); to(D.mode, D.i);
  }
  function quit() { P.ret = false; to('home'); }        // le brouillon reste : « Reprendre le questionnaire »
  function dropDraft() { if (!confirm('Abandonner les réponses en cours ? Ton profil actuel ne change pas.')) return; D = null; put(DKEY, null); to('home'); }

  function saveProfile(program) {   // program null : aucun programme généré ; undefined : celui d'avant est gardé (ni l'un ni l'autre ne touche aux programmes)
    const prev = profile(), a = clean(D.answers);
    const o = {version: 1, created: prev ? prev.created : nowIso(), updated: nowIso(), answers: a, bmi: bmiOf(a.poids, a.taille), program: program || (prev && program === undefined ? prev.program : null)};
    if (prev && prev.cycle) o.cycle = prev.cycle;   // semaines allégées, reprises et propositions reportées : gardées
    put(KEY, o);
    D = null; put(DKEY, null);
  }
  /* Un import réussi fait sauter le questionnaire : profil de l'export s'il y en a un, sinon profil gardé s'il existe,
     sinon profil « importé, questionnaire non rempli ». Les programmes importés ne sont pas touchés. */
  function afterImport(o) {
    if (o && valid(o.profil)) put(KEY, o.profil);
    else if (!profile()) put(KEY, {version: 1, imported: true, created: nowIso(), updated: nowIso(), answers: {}, program: null});
    D = null; put(DKEY, null); P.mode = 'home'; P.plan = null; P.ret = false;
  }
  function keep() {   // « Garder mes programmes » : ni programme ni exercice modifié
    if (P.busy) return;
    saveProfile(undefined); P.plan = null; P.mode = 'home';   // programme généré avant : gardé, avec sa phase
    A().toast('Profil enregistré. Tes programmes n’ont pas changé.'); A().go('accueil');
  }
  function regen() {   // depuis « Mon profil » : générer à partir du profil, avec la même confirmation
    const o = profile(); if (!o) return;
    D = fresh(); D.answers = JSON.parse(JSON.stringify(o.answers)); D.redo = true; saveD(); P.ret = false; to('resume');
  }

  /* ---------- application du programme : rien ne change avant ce clic */
  async function apply() {
    if (P.busy) return;
    const pl = P.plan, x = pl.x, api = A().api, old = A().WO().map(w => w.id);
    P.busy = true; A().R();
    try {
      const ids = [];
      for (const w of pl.workouts) {   // 1. nouveaux programmes (avant toute suppression : une coupure ne laisse jamais sans programme)
        const r = await api('POST', '/api/workouts', {name: w.name}), settings = {};
        w.items.forEach(p => { const n = w.prm[p.slug]; settings[x.ex[p.slug].id] = {sets: n.sets, target_min: n.min, target_max: n.max, rest: n.rest}; });
        // séries, répétitions et repos : réglages propres à la séance ; les exercices du catalogue ne sont pas modifiés
        await api('PUT', `/api/workouts/${r.id}`, {name: w.name, items: w.items.map(p => x.ex[p.slug].id), settings});
        ids.push(r.id);
      }
      A().forgetWorkouts(old);          // les séances en cours non enregistrées sont gardées
      for (const id of old) await api('DELETE', `/api/workouts/${id}`);   // l'historique garde son nom de séance (workout_id passe à NULL)
      await api('POST', '/api/workouts/order', {ids});
      const prev = profile() && profile().program, t = todayIso(), same = prev && prev.phase === x.phase && prev.start;
      saveProfile({generated: nowIso(), phase: x.phase, level: clean(D.answers).niveau, structure: x.a.seances, workouts: pl.workouts.map(w => w.name), ids,
        start: prev && prev.start || t, phase_start: same ? prev.phase_start : t, history: same ? prev.history : [...(prev && prev.history || []), {phase: x.phase, start: t}]});
      await A().load();
      P.busy = false; to('done');
    } catch (e) {
      P.busy = false;
      try { await A().load(); } catch (e2) {}
      A().toast('Remplacement interrompu : ' + e.message + '. Vérifie l’onglet Programmes.'); A().R();
    }
  }

  /* ------------------------------------------------------------------ écrans */
  function opt(on, label, onclick, multi, extra) {
    return `<button class="qopt${on ? ' on' : ''}" onclick="${onclick}" aria-pressed="${on}"${extra || ''}><span class="qck${multi ? ' qsq' : ''}" aria-hidden="true">${on ? '✓' : ''}</span><span>${esc(label)}</span></button>`;
  }
  function vIntro() {
    const n = A().SESS().length;
    return `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">Bienvenue dans Fonte</h2>
      <p>Avant de commencer, ${QS.length} questions courtes (environ 3 minutes) pour te proposer un programme adapté.</p>
      <p class="m">Tes réponses restent sur cet appareil. Tu peux quitter à tout moment : elles sont gardées.</p>
      ${n ? `<p class="m">Ton historique (${n} séance${n > 1 ? 's' : ''}) est conservé. Tes programmes actuels ne changeront qu’après ta confirmation, à la fin.</p>` : ''}
      <p class="m">L’appli donne des conseils d’entraînement généraux. Elle ne remplace ni un médecin ni un coach.</p>
      <button class="go" onclick="PROFIL.start()">Commencer</button>
      <button class="sm w" onclick="go('donnees')">J’ai une sauvegarde : l’importer</button></div>`;
  }
  function vQuestion() {
    const i = Math.min(D.i || 0, QS.length - 1), q = QS[i], a = D.answers;
    let h = `<div class="qprog"><span class="m">Question ${i + 1} sur ${QS.length}</span><div class="pbar" role="progressbar" aria-label="Progression du questionnaire" aria-valuemin="1" aria-valuemax="${QS.length}" aria-valuenow="${i + 1}"><i style="width:${(i + 1) / QS.length * 100}%"></i></div></div>`;
    h += `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">${esc(q.q)}</h2>`;
    let hint = q.h || '';
    if (q.k === 'jours') hint = `Au moins ${a.seances || 'autant de'} jour${a.seances > 1 ? 's' : ''}, un par séance. L’appli place tes séances sur ces jours, avec un jour de repos entre deux séances qui travaillent les mêmes muscles quand c’est possible.`;
    if (hint) h += `<p class="m">${esc(hint)}</p>`;
    if (q.t === 'text') h += `<label class="qlab">Prénom<input id="qin" class="qinp" value="${esc(a[q.k] || '')}" maxlength="30" autocomplete="given-name" oninput="PROFIL.typed(this.value)" onkeydown="if(event.key==='Enter')PROFIL.next()"></label>`;
    if (q.t === 'num') {
      const n = parseNum(a[q.k]);
      h += `<label class="qlab">${esc(q.s)} (${q.unit})<span class="qnum"><input id="qin" class="qinp" value="${esc(a[q.k] ?? '')}" inputmode="${q.int ? 'numeric' : 'decimal'}" autocomplete="off" oninput="PROFIL.typed(this.value)" onkeydown="if(event.key==='Enter')PROFIL.next()" aria-describedby="qerr"><b>${q.unit}</b></span></label>`;
      if (q.k === 'age') h += `<div id="qlive">${n >= 16 && n < 18 ? MINOR_WARN : ''}</div>`;
    }
    if (q.t === 'one') h += `<div role="radiogroup" aria-labelledby="qh">${q.o.map((o, j) => opt(a[q.k] === o[0], o[1], `PROFIL.pick(${j})`, false, ' role="radio" aria-checked="' + (a[q.k] === o[0]) + '"')).join('')}</div>`;
    if (q.t === 'multi') {
      const l = a[q.k] || [], o2 = q.k === 'objectifs2' ? q.o.filter(o => o[0] !== a.objectif) : q.o;
      h += `<div role="group" aria-labelledby="qh">${o2.map(o => opt(l.includes(o[0]), o[1], `PROFIL.tog(${q.o.indexOf(o)})`, true)).join('')}</div>`;
      if (q.k === 'blessures' && l.includes('autre')) h += `<label class="qlab" style="margin-top:10px">Précise si tu veux (facultatif)<input class="qinp" value="${esc(a.blessures_autre || '')}" maxlength="200" oninput="PROFIL.typedOther(this.value)"></label>`;
    }
    if (q.t === 'sante') {
      const s = a.sante || {};
      h += SANTE.map(([k, t]) => `<div class="qyn"><span>${esc(t)}</span><div class="qynb" role="group" aria-label="${esc(t)}">
        <button class="${s[k] === true ? 'on' : ''}" onclick="PROFIL.yn('${k}',true)" aria-pressed="${s[k] === true}">Oui</button>
        <button class="${s[k] === false ? 'on' : ''}" onclick="PROFIL.yn('${k}',false)" aria-pressed="${s[k] === false}">Non</button></div></div>`).join('');
      if (SANTE.some(([k]) => s[k] === true)) h += SANTE_WARN;
    }
    if (q.t === 'eviter') {
      const ex = Object.values(A().EX()).filter(e => !e.archived && LIB[e.slug]), l = a.eviter || [], grps = [...new Set(ex.map(e => e.grp))];
      h += `<p class="m">${l.length ? l.length + ' exercice' + (l.length > 1 ? 's' : '') + ' écarté' + (l.length > 1 ? 's' : '') : 'Aucun exercice écarté.'}</p>`;
      h += grps.map(g => `<h3>${esc(g)}</h3><div class="qchips">${ex.filter(e => e.grp === g).sort((x, y) => x.name.localeCompare(y.name, 'fr')).map(e =>
        `<button class="qchip${l.includes(e.slug) ? ' on' : ''}" onclick="PROFIL.togEv('${e.slug}')" aria-pressed="${l.includes(e.slug)}">${esc(e.name)}</button>`).join('')}</div>`).join('');
    }
    h += `<p id="qerr" class="qerr" role="alert">${esc(P.err)}</p>`;
    h += `<div class="qnav"><button class="sm" onclick="PROFIL.back()">${P.ret ? 'Annuler' : '‹ Retour'}</button><button class="go" onclick="PROFIL.next()">${P.ret ? 'Valider' : i === QS.length - 1 ? 'Voir le résumé' : 'Suivant'}</button></div></div>`;
    if (D.redo && !P.ret) h += `<button class="sm w" onclick="PROFIL.quit()">Quitter (tes réponses sont gardées)</button>`;
    return h;
  }
  function programPreview(pl, title) {
    const x = pl.x, a = x.a, miss = missingTxt(pl);
    let h = `<div class="card"><h2>${title || 'Ton programme'}</h2><p>${esc(STRUCT_TXT[a.seances])}</p><ul class="qul">${adaptations(pl).map(t => `<li>${esc(t)}</li>`).join('')}</ul>`;
    if (miss.length) h += `<p class="qmiss"><b>Il manque dans la bibliothèque, pour ton lieu d’entraînement ou tes réponses :</b> ${esc(miss.join(' ; '))}. Les séances concernées auront moins d’exercices.</p>`;
    return h + '</div>';
  }
  function cardioEnd(w) { const c = w.items.find(p => p.role === 'cardio'); return !c ? '' : c.slug === 'intervalles' ? ', puis des intervalles' : ', puis un cardio facile'; }
  function workoutsHtml(pl) {
    return pl.workouts.map(w => `<div class="card"><h2>${esc(w.name)}</h2>${w.items.map(p => { const e = pl.x.ex[p.slug]; return `<div class="qex"><b>${esc(e.name)}</b><span>${esc(prmTxt(e, w.prm[p.slug]))}</span></div>`; }).join('')}
      <p class="m">${w.items.filter(p => p.role !== 'cardio').length} exercices de force${cardioEnd(w)}. Échauffement de 8 à 10 minutes avant, étirements de 3 à 5 minutes après.</p></div>`).join('');
  }
  function answersHtml(a, editable) {
    return `<div class="card"><h2>Tes réponses</h2>${QS.map((q, i) => { const bad = editable && check(q, a); return `<div class="qrow"><div><span class="m">${esc(q.s)}</span><p${bad ? ' class="qerr"' : ''}>${esc(answerTxt(q, a))}</p></div>${editable ? `<button class="sm" onclick="PROFIL.edit(${i})" aria-label="Modifier : ${esc(q.s)}">Modifier</button>` : ''}</div>`; }).join('')}</div>`;
  }
  function detailToggle(on) {
    return `<button class="sm w qtog" onclick="PROFIL.setDetail(${!on})" aria-pressed="${on}">${on ? 'Masquer le détail santé' : 'Afficher le détail santé'}</button>`;
  }
  function vResume() {
    const a = D.answers, ok = !QS.some(q => check(q, a)), x = ok ? context(a) : null;
    let h = `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">${a.prenom ? esc(String(a.prenom).trim()) + ', voici ton résumé' : 'Voici ton résumé'}</h2><p class="m">Vérifie tes réponses : chacune se modifie avant de générer le programme.</p></div>`;
    if (x && x.sante) h += SANTE_WARN;
    if (x && x.minor) h += MINOR_WARN;
    if (ok) { h += programPreview(plan(a, phaseFor(a))); h += detailToggle(a.detail === 'oui'); if (a.detail === 'oui') h += healthBlock(a); }
    h += WARN + answersHtml(a, true);
    h += ok ? `<button class="go" onclick="PROFIL.generate()">Générer mon programme</button>` : `<p class="qerr">Complète les réponses marquées avant de générer le programme.</p><button class="go" onclick="PROFIL.generate()">Compléter</button>`;
    if (D.redo) h += `<button class="sm w" onclick="PROFIL.quit()">Quitter (tes réponses sont gardées)</button>`;
    return h;
  }
  function vConfirm() {
    const pl = P.plan, WO = A().WO(), EX = A().EX(), dr = A().pendingDraft();
    let h = `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">Avant de remplacer tes programmes</h2><p>Rien ne change tant que tu ne confirmes pas.</p>${A().SESS().length ? '<p class="m">Ton historique de séances reste intact : chaque séance passée garde son nom.</p>' : ''}${dr ? '<p class="m">Ta séance en cours non enregistrée est conservée.</p>' : ''}</div>`;
    h += `<div class="card"><h2>Programmes supprimés</h2>${WO.length ? WO.map(w => `<div class="qex"><b>${esc(w.name)}</b><span>${w.items.filter(i => EX[i]).length} exercices</span></div>`).join('') : '<p class="m">Aucun programme à supprimer.</p>'}</div>`;
    h += `<div class="card"><h2>Nouveaux programmes</h2><p class="m">Séries, répétitions et repos de chaque séance. Ils valent dans ce programme seulement : tes exercices ne sont pas modifiés.</p></div>`;
    h += pl.workouts.map(w => `<div class="card"><h2>${esc(w.name)}${w.type ? ' : ' + TYPE_TXT[w.type] : ''}</h2>${w.items.map(p => { const e = pl.x.ex[p.slug]; return `<div class="qex"><b>${esc(e.name)}</b><span>${esc(prmTxt(e, w.prm[p.slug]))}</span></div>`; }).join('')}</div>`).join('');
    const miss = missingTxt(pl);
    if (miss.length) h += `<p class="qmiss"><b>Manquants :</b> ${esc(miss.join(' ; '))}.</p>`;
    h += `<button class="go" onclick="PROFIL.apply()" ${P.busy ? 'disabled' : ''}>${P.busy ? 'Remplacement en cours…' : 'Remplacer mes programmes'}</button><button class="sm w" onclick="PROFIL.keep()" ${P.busy ? 'disabled' : ''}>Garder mes programmes</button><p class="m">« Garder mes programmes » enregistre ton profil sans toucher à tes programmes ni à tes exercices. Tu pourras générer le programme plus tard depuis « Mon profil ».</p><button class="sm w" onclick="PROFIL.cancel()" ${P.busy ? 'disabled' : ''}>Annuler</button>`;
    return h;
  }
  function currentPlan() { const o = profile(); return filled(o) ? plan(o.answers, phaseFor(o.answers)) : null; }
  function vDone() {
    const o = profile(), pl = currentPlan();
    let h = `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">Ton programme est prêt</h2><p>${o && o.answers.prenom ? esc(o.answers.prenom) + ', tes' : 'Tes'} séances sont dans l’onglet Séance. L’accueil te propose la séance prévue, sur les jours que tu as choisis.</p></div>`;
    if (pl) h += programPreview(pl) + workoutsHtml(pl);
    return h + WARN + `<button class="go" onclick="PROFIL.home();go('accueil')">Aller à l’accueil</button>`;
  }
  function vHome() {
    const o = profile();
    if (!o) return vIntro();
    const a = o.answers, pl = currentPlan(), d = draft();
    if (o.imported) {   // sauvegarde importée sans profil : le questionnaire est proposé, jamais imposé
      let h = `<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">Mon profil</h2><p>Tes données viennent d’une sauvegarde importée le ${new Date(o.created).toLocaleDateString('fr-FR')}. Tes programmes sont gardés tels quels.</p>
        <p class="m">Le questionnaire de départ n’a pas été rempli. Il te propose un programme adapté à tes réponses. Tes programmes ne changent qu’après ta confirmation.</p>`;
      h += d && d.redo ? `<button class="go" onclick="PROFIL.redo()">Reprendre le questionnaire</button><button class="sm w" onclick="PROFIL.dropDraft()">Abandonner les réponses en cours</button>`
        : `<button class="go" onclick="PROFIL.redo()">Remplir le questionnaire</button>`;
      return h + '</div>' + WARN;
    }
    let h =`<div class="card qcard"><h2 id="qh" tabindex="-1" class="qt">${a.prenom ? esc(a.prenom) : 'Mon profil'}</h2><p class="m">Profil créé le ${new Date(o.created).toLocaleDateString('fr-FR')}${o.program ? ', programme généré le ' + new Date(o.program.generated).toLocaleDateString('fr-FR') : ''}.</p>`;
    h += d && d.redo ? `<button class="go" onclick="PROFIL.redo()">Reprendre le questionnaire</button><button class="sm w" onclick="PROFIL.dropDraft()">Abandonner les réponses en cours</button>`
      : `<button class="go" onclick="PROFIL.redo()">Refaire le questionnaire</button><button class="sm w" onclick="PROFIL.regen()">Générer un programme à partir de ce profil</button><p class="m">Un nouveau programme ne remplace les tiens qu’après ta confirmation.</p>`;
    if (!o.program) h += '<p class="m">Tu as gardé tes propres programmes : aucun programme n’a été généré.</p>';
    h += '</div>';
    h += progressHtml(o);
    if (pl) h += programPreview(pl, o.program ? 'Ton programme' : 'Programme proposé (non appliqué)');
    h += detailToggle(a.detail === 'oui');
    if (a.detail === 'oui' && pl) h += healthBlock(a);
    return h + WARN + answersHtml(a, false);
  }
  function view() {
    if (profile() && !(draft() && D.redo) && ['intro', 'q', 'resume', 'confirm'].includes(P.mode)) P.mode = 'home';   // profil restauré par un import
    if (['intro', 'q', 'resume'].includes(P.mode) && !draft()) { D = fresh(); saveD(); }
    if (P.mode === 'confirm' && !P.plan) P.mode = 'resume';
    return {intro: vIntro, q: vQuestion, resume: vResume, confirm: vConfirm, done: vDone, home: vHome}[P.mode]();
  }
  function phaseLine() {   // ligne « phase » de l'onglet Séance : phase du programme (sinon celle du niveau déclaré), semaine allégée ou reprise
    const o = profile(); if (!o || !filled(o)) return '';
    const p = managed(o), ph = p ? p.phase : START[o.answers.niveau] || 1, l = lightNow(o, todayIso());
    const txt = {1: 'Phase 1 : réadaptation. Reste à 2-3 reps de l\'échec, technique avant charge.', 2: 'Phase 2 : progression. Ajoute charge ou reps dès que toutes les séries sont réussies.',
      3: 'Phase 3 : hybride. Chaque séance a son rôle : force, volume et endurance, puissance et cardio.'}[ph];
    return (l ? (l.kind === 'reprise' ? 'Reprise en douceur : environ 80 % de tes charges cette semaine. ' : 'Semaine allégée : charges environ 20 % plus basses. ') : '') + txt;
  }

  window.PROFIL = {
    init, enter, title, view, phaseLine, imposed: () => !profile(), filled: () => filled(profile()), afterImport,
    schedule, coach, offers, homeCards, accept, later,
    start, typed, typedOther, pick, tog, yn, togEv, next, back, edit, setDetail, generate, apply, keep, regen, redo, quit, dropDraft,
    cancel: () => { P.plan = null; to('resume'); }, home: () => { P.mode = 'home'; },
    exportState: () => profile(),
    importState: o => { if (valid(o)) put(KEY, o); },
    // pour les tests
    _: {adaptations, LIB, FROM_PDF, LIEUX, STRUCT, PRM, PRM3, CORE, NB_EX, CARDIO_MIN, QS, SANTE, PLIO, bmiOf, bmiBand, energy, plan, params, check, clean, context, usable, weekPlan, phaseSettings, groupsOf}
  };
})();
