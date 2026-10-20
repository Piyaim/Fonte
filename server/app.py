# SPDX-License-Identifier: AGPL-3.0-or-later
"""Fonte : catalogue d'exercices éditable, programmes, séances, poids de corps."""
import json
import os
import re
import sqlite3
import time
import unicodedata
from datetime import date

from flask import Flask, g, jsonify, request, send_from_directory

from seed import CATALOGUE, LEGACY_CARDIO, WORKOUTS

DB_PATH = os.environ.get("DB_PATH", "/data/suivi.db")
KINDS = ("weight", "reps", "time", "cardio")
EX_FIELDS = ("name", "grp", "kind", "sets", "target_min", "target_max", "rest",
             "focus", "tip", "green", "per_side", "assisted")
# réglages propres à un exercice dans un programme (lot 2A) : NULL = valeur de l'exercice
ITEM_FIELDS = ("sets", "target_min", "target_max", "rest")

app = Flask(__name__, static_folder="static", static_url_path="/static")

SCHEMA = """
CREATE TABLE IF NOT EXISTS exercise(
  id INTEGER PRIMARY KEY,
  slug TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  grp TEXT NOT NULL,
  kind TEXT NOT NULL,
  sets INTEGER NOT NULL DEFAULT 3,
  target_min INTEGER,
  target_max INTEGER,
  rest INTEGER NOT NULL DEFAULT 90,
  focus TEXT NOT NULL DEFAULT '',
  tip TEXT NOT NULL DEFAULT '',
  green INTEGER NOT NULL DEFAULT 0,
  per_side INTEGER NOT NULL DEFAULT 0,
  assisted INTEGER NOT NULL DEFAULT 0,
  diagram TEXT,
  archived INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER
);
CREATE TABLE IF NOT EXISTS workout(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  position INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS workout_item(
  workout_id INTEGER NOT NULL REFERENCES workout(id) ON DELETE CASCADE,
  exercise_id INTEGER NOT NULL REFERENCES exercise(id),
  position INTEGER NOT NULL,
  sets INTEGER,
  target_min INTEGER,
  target_max INTEGER,
  rest INTEGER,
  PRIMARY KEY(workout_id, exercise_id)
);
CREATE TABLE IF NOT EXISTS session(
  id INTEGER PRIMARY KEY,
  day TEXT NOT NULL,
  ts INTEGER NOT NULL,
  workout_id INTEGER REFERENCES workout(id) ON DELETE SET NULL,
  workout_name TEXT NOT NULL DEFAULT '',
  notes TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS entry(
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  exercise_id INTEGER NOT NULL REFERENCES exercise(id),
  idx INTEGER NOT NULL,
  load REAL,
  value REAL
);
CREATE INDEX IF NOT EXISTS entry_ex ON entry(exercise_id);
CREATE INDEX IF NOT EXISTS entry_session ON entry(session_id);
CREATE TABLE IF NOT EXISTS effort(
  session_id INTEGER NOT NULL REFERENCES session(id) ON DELETE CASCADE,
  exercise_id INTEGER NOT NULL REFERENCES exercise(id),
  level INTEGER NOT NULL,
  PRIMARY KEY(session_id, exercise_id)
);
CREATE TABLE IF NOT EXISTS bodyweight(
  id INTEGER PRIMARY KEY,
  day TEXT NOT NULL,
  ts INTEGER NOT NULL,
  kg REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS photo(
  id INTEGER PRIMARY KEY,
  day TEXT NOT NULL,
  ts INTEGER NOT NULL,
  note TEXT NOT NULL DEFAULT ''
);
"""


# ---------------------------------------------------------------- base
def connect():
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    c.execute("PRAGMA journal_mode=WAL")
    return c


def db():
    if "db" not in g:
        g.db = connect()
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    c = g.pop("db", None)
    if c is not None:
        c.close()


def now_ms():
    return int(time.time() * 1000)


def slugify(name):
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "exercice"


def unique_slug(c, name):
    base = slugify(name)
    slug, n = base, 2
    while c.execute("SELECT 1 FROM exercise WHERE slug=?", (slug,)).fetchone():
        slug, n = f"{base}-{n}", n + 1
    return slug


def insert_exercise(c, d, slug=None):
    cur = c.execute(
        """INSERT INTO exercise(slug,name,grp,kind,sets,target_min,target_max,rest,
           focus,tip,green,per_side,assisted,diagram,archived,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (slug or unique_slug(c, d["name"]), d["name"], d["grp"], d["kind"], d["sets"],
         d["target_min"], d["target_max"], d["rest"], d["focus"], d["tip"],
         d["green"], d["per_side"], d["assisted"],
         json.dumps(d["diagram"]) if d.get("diagram") else None,
         int(d.get("archived", 0)), now_ms()))
    return cur.lastrowid


def migrate(c):
    """Bases créées avant le lot 2A : ajoute les réglages par séance (colonnes vides = valeurs de l'exercice)."""
    have = {r["name"] for r in c.execute("PRAGMA table_info(workout_item)")}
    for f in ITEM_FIELDS:
        if f not in have:
            c.execute(f"ALTER TABLE workout_item ADD COLUMN {f} INTEGER")


def init_db():
    c = connect()
    with c:
        c.executescript(SCHEMA)
        migrate(c)
        if not c.execute("SELECT 1 FROM exercise LIMIT 1").fetchone():
            ids = {e["slug"]: insert_exercise(c, e, e["slug"]) for e in CATALOGUE}
            for pos, (name, slugs) in enumerate(WORKOUTS):
                wid = c.execute("INSERT INTO workout(name,position) VALUES(?,?)",
                                (name, pos)).lastrowid
                for i, s in enumerate(slugs):
                    c.execute("INSERT INTO workout_item(workout_id,exercise_id,position) VALUES(?,?,?)",
                              (wid, ids[s], i))
    c.close()


# ---------------------------------------------------------------- validation
class Bad(Exception):
    pass


@app.errorhandler(Bad)
def bad(e):
    return jsonify(error=str(e)), 400


def body():
    d = request.get_json(silent=True)
    if not isinstance(d, dict):
        raise Bad("Corps JSON attendu")
    return d


def clean_int(v, lo, hi, default=None):
    if v in (None, ""):
        return default
    try:
        v = int(float(v))
    except (TypeError, ValueError):
        raise Bad(f"Nombre invalide : {v!r}")
    return max(lo, min(hi, v))


def clean_num(v):
    if v in (None, ""):
        return None
    try:
        v = float(str(v).replace(",", "."))
    except ValueError:
        raise Bad(f"Nombre invalide : {v!r}")
    if not (-10000 <= v <= 100000):
        raise Bad("Valeur hors limites")
    return v


def clean_day(v):
    v = (v or "").strip()
    if not v:
        return date.today().isoformat()
    try:
        return date.fromisoformat(v).isoformat()
    except ValueError:
        raise Bad("Date invalide (AAAA-MM-JJ)")


def clean_exercise(d):
    name = str(d.get("name", "")).strip()[:120]
    grp = str(d.get("grp", "")).strip()[:60]
    kind = d.get("kind")
    if not name:
        raise Bad("Le nom est obligatoire")
    if not grp:
        raise Bad("Le groupe musculaire est obligatoire")
    if kind not in KINDS:
        raise Bad("Type de saisie invalide")
    tmin = clean_int(d.get("target_min"), 1, 1000)
    tmax = clean_int(d.get("target_max"), 1, 1000, tmin)
    if tmin and tmax and tmax < tmin:
        tmin, tmax = tmax, tmin
    return dict(
        name=name, grp=grp, kind=kind,
        sets=clean_int(d.get("sets"), 1, 10, 3),
        target_min=tmin, target_max=tmax,
        rest=clean_int(d.get("rest"), 0, 600, 90),
        focus=str(d.get("focus", "")).strip()[:200],
        tip=str(d.get("tip", "")).strip()[:1000],
        green=1 if d.get("green") else 0,
        per_side=1 if d.get("per_side") else 0,
        assisted=1 if d.get("assisted") and kind == "weight" else 0,
    )


def clean_item(d):
    """Réglages d'un exercice dans un programme ; None ou {} = valeurs de l'exercice."""
    if d is None:
        d = {}
    if not isinstance(d, dict):
        raise Bad("Réglage invalide : objet attendu")
    tmin = clean_int(d.get("target_min"), 1, 1000)
    tmax = clean_int(d.get("target_max"), 1, 1000, tmin)
    if tmin is None:
        tmin = tmax
    if tmin and tmax and tmax < tmin:
        tmin, tmax = tmax, tmin
    return dict(sets=clean_int(d.get("sets"), 1, 10), target_min=tmin, target_max=tmax,
                rest=clean_int(d.get("rest"), 0, 600))


def clean_settings(v):
    """{"id d'exercice": réglages} -> {id: réglages nettoyés}."""
    if v is None:
        return {}
    if not isinstance(v, dict):
        raise Bad("settings doit être un objet")
    return {clean_int(k, 1, 10**9): clean_item(d) for k, d in v.items()}


def write_items(c, wid, items, settings):
    c.execute("DELETE FROM workout_item WHERE workout_id=?", (wid,))
    for p, i in enumerate(items):
        s = settings.get(i) or {}
        c.execute("""INSERT INTO workout_item(workout_id,exercise_id,position,sets,target_min,target_max,rest)
                     VALUES(?,?,?,?,?,?,?)""", (wid, i, p, *(s.get(f) for f in ITEM_FIELDS)))


def ex_row(r):
    d = dict(r)
    d["diagram"] = json.loads(d["diagram"]) if d["diagram"] else None
    d["used"] = bool(db().execute("SELECT 1 FROM entry WHERE exercise_id=? LIMIT 1",
                                  (d["id"],)).fetchone())
    return d


def workouts_list(c):
    out = []
    for w in c.execute("SELECT * FROM workout ORDER BY position, id"):
        rows = c.execute("SELECT * FROM workout_item WHERE workout_id=? ORDER BY position",
                         (w["id"],)).fetchall()
        settings = {str(r["exercise_id"]): {f: r[f] for f in ITEM_FIELDS}
                    for r in rows if any(r[f] is not None for f in ITEM_FIELDS)}
        out.append(dict(id=w["id"], name=w["name"], position=w["position"],
                        items=[r["exercise_id"] for r in rows], settings=settings))
    return out


def sessions_list(c, where="", args=()):
    rows = c.execute(f"SELECT * FROM session {where} ORDER BY day, ts, id", args).fetchall()
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    ent = {}
    q = ",".join("?" * len(ids))
    for e in c.execute(f"SELECT * FROM entry WHERE session_id IN ({q}) ORDER BY session_id, id",
                       ids):
        ent.setdefault(e["session_id"], {}).setdefault(e["exercise_id"], []).append(
            [e["load"], e["value"]])
    eff = {(f["session_id"], f["exercise_id"]): f["level"]
           for f in c.execute(f"SELECT * FROM effort WHERE session_id IN ({q})", ids)}
    return [dict(id=r["id"], day=r["day"], ts=r["ts"], workout_id=r["workout_id"],
                 workout_name=r["workout_name"], notes=r["notes"],
                 entries=[dict(exercise_id=k, sets=v, effort=eff.get((r["id"], k)))
                      for k, v in ent.get(r["id"], {}).items()])
            for r in rows]


def write_entries(c, sid, entries):
    if not isinstance(entries, list):
        raise Bad("entries doit être une liste")
    known = {r[0] for r in c.execute("SELECT id FROM exercise")}
    n = 0
    for e in entries:
        exid = clean_int(e.get("exercise_id"), 1, 10**9)
        if exid not in known:
            raise Bad(f"Exercice inconnu : {exid}")
        lv = clean_int(e.get("effort"), 1, 5)
        if lv:
            c.execute("INSERT OR REPLACE INTO effort(session_id,exercise_id,level) VALUES(?,?,?)",
                      (sid, exid, lv))
        for i, s in enumerate((e.get("sets") or [])[:20]):
            load, value = clean_num(s[0]), clean_num(s[1])
            if load is None and value is None:
                continue
            c.execute("INSERT INTO entry(session_id,exercise_id,idx,load,value) VALUES(?,?,?,?,?)",
                      (sid, exid, i, load, value))
            n += 1
    return n


# ---------------------------------------------------------------- routes
@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.get("/healthz")
def healthz():
    db().execute("SELECT 1").fetchone()
    return "ok"


@app.get("/api/state")
def state():
    c = db()
    return jsonify(
        exercises=[ex_row(r) for r in c.execute("SELECT * FROM exercise ORDER BY grp, name")],
        workouts=workouts_list(c),
        sessions=sessions_list(c),
        bodyweight=[dict(r) for r in c.execute("SELECT * FROM bodyweight ORDER BY day, ts")],
    )


# --- exercices
@app.post("/api/exercises")
def ex_create():
    d = clean_exercise(body())
    c = db()
    with c:
        new_id = insert_exercise(c, d)
    return jsonify(ex_row(c.execute("SELECT * FROM exercise WHERE id=?", (new_id,)).fetchone())), 201


@app.put("/api/exercises/<int:eid>")
def ex_update(eid):
    d = clean_exercise(body())
    c = db()
    with c:
        cur = c.execute(
            f"UPDATE exercise SET {', '.join(f + '=?' for f in EX_FIELDS)}, updated_at=? WHERE id=?",
            [d[f] for f in EX_FIELDS] + [now_ms(), eid])
    if not cur.rowcount:
        return jsonify(error="Exercice introuvable"), 404
    return jsonify(ex_row(c.execute("SELECT * FROM exercise WHERE id=?", (eid,)).fetchone()))


@app.post("/api/exercises/<int:eid>/archive")
def ex_archive(eid):
    flag = 1 if body().get("archived") else 0
    c = db()
    with c:
        cur = c.execute("UPDATE exercise SET archived=?, updated_at=? WHERE id=?",
                        (flag, now_ms(), eid))
        if flag:
            c.execute("DELETE FROM workout_item WHERE exercise_id=?", (eid,))
    if not cur.rowcount:
        return jsonify(error="Exercice introuvable"), 404
    return jsonify(ok=True)


@app.delete("/api/exercises/<int:eid>")
def ex_delete(eid):
    c = db()
    if c.execute("SELECT 1 FROM entry WHERE exercise_id=? LIMIT 1", (eid,)).fetchone():
        return jsonify(error="Exercice déjà utilisé dans des séances : archive-le plutôt."), 409
    with c:
        c.execute("DELETE FROM workout_item WHERE exercise_id=?", (eid,))
        c.execute("DELETE FROM exercise WHERE id=?", (eid,))
    return jsonify(ok=True)


# --- programmes
@app.post("/api/workouts")
def wo_create():
    name = str(body().get("name", "")).strip()[:80]
    if not name:
        raise Bad("Nom obligatoire")
    c = db()
    with c:
        pos = c.execute("SELECT COALESCE(MAX(position),-1)+1 FROM workout").fetchone()[0]
        wid = c.execute("INSERT INTO workout(name,position) VALUES(?,?)", (name, pos)).lastrowid
    return jsonify(id=wid), 201


@app.put("/api/workouts/<int:wid>")
def wo_update(wid):
    d = body()
    name = str(d.get("name", "")).strip()[:80]
    items = d.get("items", [])
    if not name:
        raise Bad("Nom obligatoire")
    if not isinstance(items, list):
        raise Bad("items doit être une liste")
    c = db()
    active = {r[0] for r in c.execute("SELECT id FROM exercise WHERE archived=0")}
    seen = []
    for i in items:
        i = clean_int(i, 1, 10**9)
        if i not in active:
            raise Bad(f"Exercice inconnu ou archivé : {i}")
        if i not in seen:
            seen.append(i)
    if "settings" in d:   # réglages envoyés : ils remplacent les anciens
        settings = clean_settings(d["settings"])
    else:                 # pas envoyés (ancienne interface) : on garde ceux des exercices restés dans le programme
        settings = {r["exercise_id"]: {f: r[f] for f in ITEM_FIELDS}
                    for r in c.execute("SELECT * FROM workout_item WHERE workout_id=?", (wid,))}
    with c:
        if not c.execute("UPDATE workout SET name=? WHERE id=?", (name, wid)).rowcount:
            return jsonify(error="Programme introuvable"), 404
        write_items(c, wid, seen, settings)
    return jsonify(ok=True)


@app.post("/api/workouts/order")
def wo_order():
    ids = body().get("ids", [])
    c = db()
    with c:
        for p, i in enumerate(ids):
            c.execute("UPDATE workout SET position=? WHERE id=?", (p, clean_int(i, 1, 10**9)))
    return jsonify(ok=True)


@app.delete("/api/workouts/<int:wid>")
def wo_delete(wid):
    c = db()
    with c:
        c.execute("DELETE FROM workout WHERE id=?", (wid,))
    return jsonify(ok=True)


# --- séances
def session_payload(c, d):
    wid = clean_int(d.get("workout_id"), 1, 10**9)
    wname = str(d.get("workout_name", "")).strip()[:80]
    if wid:
        w = c.execute("SELECT name FROM workout WHERE id=?", (wid,)).fetchone()
        if not w:
            wid = None
        elif not wname:
            wname = w["name"]
    return wid, wname or "Séance libre", clean_day(d.get("day")), str(d.get("notes", ""))[:4000]


@app.post("/api/sessions")
def sess_create():
    d = body()
    c = db()
    wid, wname, day, notes = session_payload(c, d)
    with c:
        sid = c.execute("INSERT INTO session(day,ts,workout_id,workout_name,notes) VALUES(?,?,?,?,?)",
                        (day, now_ms(), wid, wname, notes)).lastrowid
        if not write_entries(c, sid, d.get("entries")):
            raise Bad("Aucune série saisie")
    return jsonify(id=sid), 201


@app.put("/api/sessions/<int:sid>")
def sess_update(sid):
    d = body()
    c = db()
    wid, wname, day, notes = session_payload(c, d)
    with c:
        if not c.execute("UPDATE session SET day=?, workout_id=?, workout_name=?, notes=? WHERE id=?",
                         (day, wid, wname, notes, sid)).rowcount:
            return jsonify(error="Séance introuvable"), 404
        c.execute("DELETE FROM entry WHERE session_id=?", (sid,))
        c.execute("DELETE FROM effort WHERE session_id=?", (sid,))
        if not write_entries(c, sid, d.get("entries")):
            raise Bad("Aucune série saisie")
    return jsonify(ok=True)


@app.delete("/api/sessions/<int:sid>")
def sess_delete(sid):
    c = db()
    with c:
        c.execute("DELETE FROM session WHERE id=?", (sid,))
    return jsonify(ok=True)


# --- poids de corps
@app.post("/api/bodyweight")
def bw_add():
    d = body()
    kg = clean_num(d.get("kg"))
    if not kg or not (20 <= kg <= 400):
        raise Bad("Poids invalide")
    c = db()
    with c:
        c.execute("INSERT INTO bodyweight(day,ts,kg) VALUES(?,?,?)",
                  (clean_day(d.get("day")), now_ms(), kg))
    return jsonify(ok=True), 201


@app.delete("/api/bodyweight/<int:bid>")
def bw_delete(bid):
    c = db()
    with c:
        c.execute("DELETE FROM bodyweight WHERE id=?", (bid,))
    return jsonify(ok=True)


# --- photos de progression (fichiers dans le volume /data/photos, jamais envoyés ailleurs)
PHOTO_DIR = os.path.join(os.path.dirname(DB_PATH) or ".", "photos")


def is_jpeg(b):
    return len(b) > 500 and b[:3] == b"\xff\xd8\xff"


@app.get("/api/photos")
def photos_list():
    rows = db().execute("SELECT id,day,ts,note FROM photo ORDER BY day, ts").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/photos")
def photo_add():
    img, th = request.files.get("img"), request.files.get("thumb")
    if not img or not th:
        raise Bad("Photo manquante")
    a, t = img.read(6 * 1024 * 1024 + 1), th.read(1024 * 1024 + 1)
    if len(a) > 6 * 1024 * 1024 or len(t) > 1024 * 1024:
        raise Bad("Photo trop lourde")
    if not (is_jpeg(a) and is_jpeg(t)):
        raise Bad("Format JPEG attendu")
    day = clean_day(request.form.get("day"))
    note = (request.form.get("note") or "").strip()[:200]
    os.makedirs(PHOTO_DIR, exist_ok=True)
    c = db()
    with c:
        pid = c.execute("INSERT INTO photo(day,ts,note) VALUES(?,?,?)", (day, now_ms(), note)).lastrowid
        with open(os.path.join(PHOTO_DIR, f"{pid}.jpg"), "wb") as f:
            f.write(a)
        with open(os.path.join(PHOTO_DIR, f"{pid}_t.jpg"), "wb") as f:
            f.write(t)
    return jsonify(id=pid), 201


@app.get("/photos/<int:pid>/<kind>")
def photo_file(pid, kind):
    if kind not in ("full", "thumb"):
        return "", 404
    r = send_from_directory(PHOTO_DIR, f"{pid}.jpg" if kind == "full" else f"{pid}_t.jpg", mimetype="image/jpeg")
    r.headers["Cache-Control"] = "private, max-age=86400"
    return r


@app.delete("/api/photos/<int:pid>")
def photo_delete(pid):
    c = db()
    with c:
        c.execute("DELETE FROM photo WHERE id=?", (pid,))
    for n in (f"{pid}.jpg", f"{pid}_t.jpg"):
        try:
            os.remove(os.path.join(PHOTO_DIR, n))
        except OSError:
            pass
    return jsonify(ok=True)


# --- application installable (PWA) : manifeste et icônes à la couleur choisie (patch F)
import struct
import zlib

from flask import Response, abort

ICON_ACC = {
    "orange": ((255, 122, 26), "#e8590c"), "blue": ((77, 171, 247), "#1971c2"),
    "green": ((81, 207, 102), "#2b8a3e"), "violet": ((151, 117, 250), "#7048e8"),
    "red": ((255, 107, 107), "#e03131"), "mono": ((255, 255, 255), "#111111"),
}
_ICON_CACHE = {}


def _icon_png(size, bg):
    """Haltère sombre sur fond de couleur, dessiné sans bibliothèque (rectangles arrondis, lissage 2x2)."""
    if (size, bg) in _ICON_CACHE:
        return _ICON_CACHE[(size, bg)]
    fg = (14, 22, 28)
    S = size * 2
    u = S * (0.78 if size == 512 else 0.9) / 100
    c = S / 2
    m = [bytearray(S) for _ in range(S)]

    def rr(x0, y0, x1, y1, r):
        X0, X1, Y0, Y1, R = round(c + x0 * u), round(c + x1 * u), round(c + y0 * u), round(c + y1 * u), max(1, round(r * u))
        for y in range(Y0, Y1):
            k = min(y - Y0, Y1 - 1 - y)
            ins = 0 if k >= R else round(R - (R * R - (R - k - 0.5) ** 2) ** 0.5)
            if X1 - ins > X0 + ins:
                m[y][X0 + ins:X1 - ins] = b"\xff" * (X1 - X0 - 2 * ins)

    rr(-30, -5, 30, 5, 3)
    for s in (-1, 1):
        for a, b, h, r in ((24, 34, 20, 4), (34, 42, 13, 4), (42, 50, 5, 3)):
            a, b = sorted((s * a, s * b))
            rr(a, -h, b, h, r)
    luts = [bytes(round(bg[i] + (fg[i] - bg[i]) * v / 1020) for v in range(1021)) for i in range(3)]
    raw = bytearray()
    for y in range(size):
        a, b = m[2 * y], m[2 * y + 1]
        sm = [p + q + r + t for p, q, r, t in zip(a[0::2], a[1::2], b[0::2], b[1::2])]
        row = bytearray(size * 3)
        for i in range(3):
            row[i::3] = bytes(luts[i][v] for v in sm)
        raw += b"\x00" + row

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    _ICON_CACHE[(size, bg)] = png
    return png


def _acc():
    k = request.args.get("c", "orange")
    return k if k in ICON_ACC else "orange"


@app.get("/icon/<int:size>.png")
def pwa_icon(size):
    if size not in (180, 192, 512):
        abort(404)
    r = Response(_icon_png(size, ICON_ACC[_acc()][0]), mimetype="image/png")
    r.headers["Cache-Control"] = "public, max-age=86400"
    return r


@app.get("/manifest.webmanifest")
def pwa_manifest():
    with open(os.path.join(app.static_folder, "manifest.webmanifest"), encoding="utf-8") as f:
        mf = json.load(f)
    k = _acc()
    if k != "orange":
        mf["theme_color"] = ICON_ACC[k][1]
        mf["icons"] = [
            {"src": f"/icon/192.png?c={k}", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": f"/icon/512.png?c={k}", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
        ]
    r = Response(json.dumps(mf, ensure_ascii=False), mimetype="application/manifest+json")
    r.headers["Cache-Control"] = "no-cache"
    return r


@app.get("/sw.js")
def pwa_sw():
    r = send_from_directory(app.static_folder, "sw.js", mimetype="application/javascript")
    r.headers["Cache-Control"] = "no-cache"
    return r


# --- export / import
@app.get("/api/export")
def export():
    c = db()
    data = dict(
        format="suivi-muscu", version=1, exported_at=now_ms(),
        exercises=[dict(r) for r in c.execute("SELECT * FROM exercise ORDER BY id")],
        workouts=workouts_list(c),
        sessions=sessions_list(c),
        bodyweight=[dict(r) for r in c.execute("SELECT * FROM bodyweight ORDER BY id")],
    )
    resp = jsonify(data)
    resp.headers["Content-Disposition"] = (
        f'attachment; filename="suivi-muscu-{date.today().isoformat()}.json"')
    return resp


def fr_to_iso(s):
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{1,2})/(\d{4})\s*", str(s or ""))
    if not m:
        raise Bad(f"Date de l'ancienne appli illisible : {s!r}")
    return date(int(m[3]), int(m[2]), int(m[1])).isoformat()


def import_legacy(c, o):
    """Format de l'ancienne appli HTML : {L:[séances], W:[[jj/mm/aaaa, kg]]}. Ajoute, ne remplace rien."""
    slug2id = {r["slug"]: r["id"] for r in c.execute("SELECT id, slug FROM exercise")}
    wname2id = {r["name"]: r["id"] for r in c.execute("SELECT id, name FROM workout")}
    added = skipped = 0
    for s in o.get("L") or []:
        ts = int(s.get("ts") or 0)
        if ts and c.execute("SELECT 1 FROM session WHERE ts=?", (ts,)).fetchone():
            skipped += 1
            continue
        wname = f"Séance {s.get('s', '')}".strip()
        entries = []
        for old_id, sets in (s.get("x") or {}).items():
            if old_id not in slug2id:
                raise Bad(f"Exercice de l'ancienne appli inconnu : {old_id}")
            entries.append(dict(exercise_id=slug2id[old_id], sets=sets))
        cardio = s.get("c") or []
        if len(cardio) == 2 and cardio[0]:
            slug = LEGACY_CARDIO.get(cardio[1])
            if slug in slug2id:
                entries.append(dict(exercise_id=slug2id[slug], sets=[[None, cardio[0]]]))
        sid = c.execute("INSERT INTO session(day,ts,workout_id,workout_name,notes) VALUES(?,?,?,?,?)",
                        (fr_to_iso(s.get("d")), ts or now_ms(), wname2id.get(wname), wname,
                         str(s.get("n") or ""))).lastrowid
        write_entries(c, sid, entries)
        added += 1
    bw = 0
    for d, kg in o.get("W") or []:
        day = fr_to_iso(d)
        if not c.execute("SELECT 1 FROM bodyweight WHERE day=? AND kg=?", (day, kg)).fetchone():
            c.execute("INSERT INTO bodyweight(day,ts,kg) VALUES(?,?,?)", (day, now_ms(), float(kg)))
            bw += 1
    return dict(mode="ancienne appli (ajout)", sessions=added, doublons_ignores=skipped,
                pesees=bw)


def import_full(c, o):
    """Format exporté par ce service : REMPLACE toute la base."""
    for t in ("effort", "entry", "session", "workout_item", "workout", "bodyweight", "exercise"):
        c.execute(f"DELETE FROM {t}")
    for e in o.get("exercises") or []:
        c.execute("""INSERT INTO exercise(id,slug,name,grp,kind,sets,target_min,target_max,rest,
                     focus,tip,green,per_side,assisted,diagram,archived,updated_at)
                     VALUES(:id,:slug,:name,:grp,:kind,:sets,:target_min,:target_max,:rest,
                     :focus,:tip,:green,:per_side,:assisted,:diagram,:archived,:updated_at)""", e)
    for w in o.get("workouts") or []:
        c.execute("INSERT INTO workout(id,name,position) VALUES(?,?,?)",
                  (w["id"], w["name"], w.get("position", 0)))
        write_items(c, w["id"], w.get("items") or [], clean_settings(w.get("settings")))   # export d'avant le lot 2A : pas de « settings »
    for s in o.get("sessions") or []:
        c.execute("INSERT INTO session(id,day,ts,workout_id,workout_name,notes) VALUES(?,?,?,?,?,?)",
                  (s["id"], s["day"], s["ts"], s.get("workout_id"), s.get("workout_name", ""),
                   s.get("notes", "")))
        write_entries(c, s["id"], s.get("entries") or [])
    for b in o.get("bodyweight") or []:
        c.execute("INSERT INTO bodyweight(id,day,ts,kg) VALUES(?,?,?,?)",
                  (b["id"], b["day"], b["ts"], b["kg"]))
    return dict(mode="sauvegarde complète (remplacement)",
                exercices=len(o.get("exercises") or []),
                sessions=len(o.get("sessions") or []))


@app.post("/api/import")
def do_import():
    o = body()
    c = db()
    try:
        with c:
            if o.get("format") == "suivi-muscu":
                res = import_full(c, o)
            elif isinstance(o.get("L"), list):
                res = import_legacy(c, o)
            else:
                raise Bad("Format non reconnu : ni export de ce service, ni export de l'ancienne appli")
    except (KeyError, TypeError, sqlite3.Error) as e:
        raise Bad(f"Import refusé, base inchangée : {e}")
    return jsonify(res)


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
