# SPDX-License-Identifier: AGPL-3.0-or-later
# Pour les anciens tests de migration (migration.py, migration_lot2b.py, migration_v031.py à migration_v060.py), écrits avant
# l'ajout du début et de la fin de séance (start_ts, end_ts). Ils comparent à l'identique les données d'une ancienne version et
# celles que relit le code actuel ; or le code actuel ajoute ces deux champs, vides, à chaque séance existante.
# brancher() les retire de tout ce que le test relit (page.evaluate, fichiers JSON, SQLite) en notant leurs valeurs ;
# bilan() vérifie ensuite qu'ils ont bien été vus et qu'ils étaient TOUS vides (une ancienne séance ne reçoit jamais de durée).
# Tout le reste est toujours comparé à l'identique. Le test complet du nouveau champ : migration_v061.py et duree.py.
# Même chose pour « pend » (jetons de quête en attente, 0.7.1), ajouté à 0 à l'état du jeu relu ou exporté par le code actuel :
# retiré de l'état du jeu, puis bilan() vérifie qu'il valait toujours 0. Test complet : plafond.py et migration_v070.py.
# Les semaines vides de « wk » (aucune quête faite) sont aussi ignorées des deux côtés.
import json as _json
CHAMPS = ("start_ts", "end_ts")
VUS = []
PEND = []

def sans_duree(o):
    if isinstance(o, (list, tuple)): return type(o)(sans_duree(x) for x in o)
    if isinstance(o, dict):
        seance = "day" in o and "workout_name" in o
        if o.get("v") == 1 and "awarded" in o and "tokens" in o:   # état du jeu
            if "pend" in o: PEND.append(o["pend"])
            # semaine vide de « wk » : l'ancien code la créait en mémoire en lisant seulement les quêtes (elle passait dans
            # l'export), le code de la 0.7.1 ne l'écrit plus ; elle ne contient aucune quête faite
            return {k: ({w: sans_duree(q) for w, q in v.items() if q} if k == "wk" and isinstance(v, dict) else sans_duree(v)) for k, v in o.items() if k != "pend"}
        if seance: VUS.extend(o[f] for f in CHAMPS if f in o)
        return {k: sans_duree(v) for k, v in o.items() if not (seance and k in CHAMPS)}
    return o

class _Json:   # remplace « json » dans le test : seules les lectures sont filtrées
    dumps = staticmethod(_json.dumps); dump = staticmethod(_json.dump); load = staticmethod(_json.load)
    loads = staticmethod(lambda *a, **k: sans_duree(_json.loads(*a, **k)))

def brancher(g):
    from playwright.sync_api import Page
    if not getattr(Page.evaluate, "_sans_duree", False):
        ev = Page.evaluate
        def evaluate(self, *a, **k): return sans_duree(ev(self, *a, **k))
        evaluate._sans_duree = True; Page.evaluate = evaluate
    g["json"] = _Json
    if "sqlite_brut" in g:
        f = g["sqlite_brut"]; g["sqlite_brut"] = lambda *a: sans_duree(f(*a))

def bilan(ok):
    ok(all(v == 0 for v in PEND), f"jetons de quête en attente : 0 dans tout état du jeu relu ({len(PEND)} vus)")
    ok(len(VUS) > 0 and all(v is None for v in VUS),
       f"début et fin de séance : ajoutés à chaque séance relue par le code actuel, tous vides ({len(VUS)} champs, {sum(v is not None for v in VUS)} remplis)")
