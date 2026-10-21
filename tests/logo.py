# SPDX-License-Identifier: AGPL-3.0-or-later
# Vérifie le logo (tools/logo.py) : les dessins Android, relus ici par un traducteur indépendant
# (VectorDrawable -> SVG), doivent donner la même image que le SVG du menu et rester dans la zone visible.
import io, os, re
import xml.etree.ElementTree as ET
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "android", "app", "src", "main", "res")
ICONS = os.path.join(ROOT, "server", "static", "icons")
A = "{http://schemas.android.com/apk/res/android}"
ok = lambda c, m: print(("OK    " if c else "ÉCHEC "), m)
COULEURS = ["orange", "blue", "green", "violet", "red", "mono"]


def couleur(v):
    v = v.lstrip("#")
    a, rgb = (int(v[:2], 16) / 255, v[2:]) if len(v) == 8 else (1, v)
    return f"#{rgb}", round(a, 4)


def vd_vers_svg(chemin, pre):
    """Traduit un VectorDrawable en SVG (seulement ce que le logo utilise ; le reste fait échouer)."""
    racine = ET.parse(chemin).getroot()
    defs, n = [], [0]

    def elem(e):
        if e.tag == "group":
            px, py = float(e.get(A + "pivotX", 0)), float(e.get(A + "pivotY", 0))
            r = float(e.get(A + "rotation", 0))
            sx, sy = float(e.get(A + "scaleX", 1)), float(e.get(A + "scaleY", 1))
            return f'<g transform="translate({px} {py}) rotate({r}) scale({sx} {sy}) translate({-px} {-py})">' + "".join(elem(c) for c in e) + "</g>"
        assert e.tag == "path", e.tag
        d = e.get(A + "pathData")
        if e.get(A + "fillColor"):
            c, a = couleur(e.get(A + "fillColor"))
            return f'<path d="{d}" fill="{c}" fill-opacity="{a}"/>'
        g = e.find("{http://schemas.android.com/aapt}attr/gradient")
        assert g is not None, "peinture inconnue"
        n[0] += 1; gid = f"{pre}{n[0]}"
        stops = "".join(f'<stop offset="{i.get(A + "offset")}" stop-color="{couleur(i.get(A + "color"))[0]}" stop-opacity="{couleur(i.get(A + "color"))[1]}"/>' for i in g)
        if g.get(A + "type") == "linear":
            defs.append(f'<linearGradient id="{gid}" gradientUnits="userSpaceOnUse" x1="{g.get(A + "startX")}" y1="{g.get(A + "startY")}" x2="{g.get(A + "endX")}" y2="{g.get(A + "endY")}">{stops}</linearGradient>')
        else:
            assert g.get(A + "type") == "radial"
            defs.append(f'<radialGradient id="{gid}" gradientUnits="userSpaceOnUse" cx="{g.get(A + "centerX")}" cy="{g.get(A + "centerY")}" r="{g.get(A + "gradientRadius")}">{stops}</radialGradient>')
        return f'<path d="{d}" fill="url(#{gid})"/>'

    corps = "".join(elem(c) for c in racine)
    return corps, "".join(defs)


def rendu(pg, svg, t):
    pg.set_viewport_size({"width": t, "height": t})
    pg.set_content(f'<html><body style="margin:0;background:transparent">{svg}</body></html>')
    return Image.open(io.BytesIO(pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": t, "height": t}))).convert("RGBA")


def ecart(a, b):
    """Écart moyen par canal (0 à 255) entre deux images."""
    d = ImageChops.difference(a, b).convert("L")
    return sum(i * c for i, c in enumerate(d.histogram())) / (a.size[0] * a.size[1])


fg = os.path.join(RES, "drawable", "ic_fg.xml")
mono = os.path.join(RES, "drawable", "ic_fg_mono.xml")
txt_fg, txt_mono = open(fg, encoding="utf-8").read(), open(mono, encoding="utf-8").read()
ok("<gradient" in txt_fg and "android:rotation" in txt_fg, "avant-plan : dégradés et haltère incliné")
ok("<gradient" not in txt_mono and "fillColor" in txt_mono, "silhouette (icône à thème) : couleur pleine, sans dégradé")
ok('xmlns:aapt="http://schemas.android.com/aapt"' in txt_fg, "espace de noms aapt déclaré (sinon l'APK ne se construit pas)")

T = 216  # 2 px par unité de la grille de 108
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(device_scale_factor=1)
    corps_fg, defs_fg = vd_vers_svg(fg, "f")
    for k in COULEURS:
        corps_bg, defs_bg = vd_vers_svg(os.path.join(RES, "drawable", f"ic_bg_{k}.xml"), "b")
        android = rendu(pg, f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 72 72" width="{T}" height="{T}"><defs>{defs_bg}{defs_fg}</defs>{corps_bg}{corps_fg}</svg>', T)
        menu = rendu(pg, re.sub(r'width="72" height="72"', f'width="{T}" height="{T}"', open(os.path.join(ICONS, f"logo-{k}.svg"), encoding="utf-8").read(), count=1), T)
        e = ecart(android, menu)
        ok(e < 1.0, f"{k} : l'icône Android et le logo du menu sont le même dessin (écart moyen {e:.2f} sur 255)")
    # zone de sécurité : rayon 33 autour du centre de la grille de 108 (au-delà, certains lanceurs coupent)
    corps_m, defs_m = vd_vers_svg(mono, "m")
    im = rendu(pg, f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 108 108" width="{T}" height="{T}"><defs>{defs_m}</defs>{corps_m}</svg>', T)
    px = im.load(); s = T / 108
    hors = [(x, y) for y in range(T) for x in range(T) if px[x, y][3] > 40 and ((x + .5) / s - 54) ** 2 + ((y + .5) / s - 54) ** 2 > 33 ** 2]
    ok(not hors, f"l'haltère tient dans la zone visible de toutes les formes d'icône ({len(hors)} pixels dehors)")
    plein = sum(1 for y in range(T) for x in range(T) if px[x, y][3] > 40) / (T * T)
    ok(plein > .04, f"la silhouette n'est pas vide ({plein:.0%} de la grille)")
    # témoin : un dessin décalé doit être détecté (sinon la comparaison ne prouve rien)
    corps_bg, defs_bg = vd_vers_svg(os.path.join(RES, "drawable", "ic_bg_orange.xml"), "b")
    decale = rendu(pg, f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="18 18 72 72" width="{T}" height="{T}"><defs>{defs_bg}{defs_fg}</defs>{corps_bg}<g transform="rotate(8 54 54)">{corps_fg}</g></svg>', T)
    menu = rendu(pg, re.sub(r'width="72" height="72"', f'width="{T}" height="{T}"', open(os.path.join(ICONS, "logo-orange.svg"), encoding="utf-8").read(), count=1), T)
    ok(ecart(decale, menu) >= 1.0, f"témoin : un haltère tourné de 8° est bien repéré (écart {ecart(decale, menu):.2f})")
    b.close()
