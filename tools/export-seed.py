#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-or-later
# Régénère server/static/seed.json (catalogue de départ de la version sans serveur) à partir de server/seed.py.
# À relancer après toute modification de seed.py :  python3 tools/export-seed.py
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "server"))
from seed import CATALOGUE, LEGACY_CARDIO, WORKOUTS
out = os.path.join(ROOT, "server", "static", "seed.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(dict(exercises=CATALOGUE, workouts=[[n, s] for n, s in WORKOUTS], legacy_cardio=LEGACY_CARDIO),
              f, ensure_ascii=False, separators=(",", ":"))
print(out, os.path.getsize(out), "octets,", len(CATALOGUE), "exercices")
