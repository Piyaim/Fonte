# SPDX-License-Identifier: AGPL-3.0-or-later
"""Logo de Fonte (proposition B « Élan », choisie le 21/10/2026) : un seul modèle, toutes les sorties.

Le modèle est fait de tracés, de dégradés linéaires ou radiaux et de groupes (rotation, échelle).
Pas de flou ni de masque : tout se traduit tel quel en VectorDrawable (dégradés pris en charge
par Android depuis l'API 24, la version minimale de l'appli).

Grille : 108 x 108 (calque d'icône adaptative Android). Le lanceur montre le carré central de 72 ;
la forme utile tient dans le cercle de sécurité de rayon 33 autour de (54, 54).
L'haltère est le même pour toutes les couleurs ; seul le fond change avec la couleur choisie.

Usage (depuis la racine du dépôt, Playwright + Chromium requis pour les PNG) :
    python3 tools/logo.py            # écrit toutes les sorties
    python3 tools/logo.py --svg-only # seulement les SVG et les XML Android (sans Chromium)
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "android", "app", "src", "main", "res")

# clair, moyen, foncé (fond en dégradé de haut en bas)
COULEURS = {
    "orange": ("#ff9a3c", "#ff7a1a", "#d9500b"),
    "blue":   ("#6cbcfa", "#4dabf7", "#1c7ed6"),
    "green":  ("#7ee08e", "#51cf66", "#2f9e44"),
    "violet": ("#ae94fb", "#9775fa", "#7048e8"),
    "red":    ("#ff8a8a", "#ff6b6b", "#e03131"),
    "mono":   ("#ffffff", "#f1f3f5", "#cfd5db"),
}

# ------------------------------------------------------------------ modèle
# peinture : ("plein", couleur, opacité) | ("lin", x1, y1, x2, y2, arrêts) | ("rad", cx, cy, r, arrêts)
# arrêt : (position 0..1, couleur, opacité)
FONTE = [(0, "#56636e", 1), (.18, "#36424b", 1), (.55, "#1a232a", 1), (1, "#090d10", 1)]
CHROME = [(0, "#c9d2d9", 1), (.3, "#ffffff", 1), (.62, "#8794a0", 1), (1, "#2f3940", 1)]


def fond(cle):
    c1, c2, c3 = COULEURS[cle]
    carre = "M0,0H108V108H0Z"
    return [
        {"d": carre, "p": ("lin", 0, 0, 0, 108, [(0, c1, 1), (.55, c2, 1), (1, c3, 1)])},
        {"d": carre, "p": ("rad", 46, 36, 46, [(0, "#ffffff", .30), (1, "#ffffff", 0)])},
    ]


def cercle(cx, cy, r):
    return f"M{cx - r:.2f},{cy:.2f}A{r},{r} 0 1 1 {cx + r:.2f},{cy:.2f}A{r},{r} 0 1 1 {cx - r:.2f},{cy:.2f}Z"


def cylindre(x0, x1, cy, h, e):
    """Pièce couchée vue de trois quarts : corps de x0 à x1 (bout gauche bombé), face visible à droite."""
    y0, y1 = cy - h, cy + h
    corps = f"M{x0:.2f},{y0:.2f}H{x1:.2f}A{e},{h} 0 0 1 {x1:.2f},{y1:.2f}H{x0:.2f}A{e},{h} 0 0 1 {x0:.2f},{y0:.2f}Z"
    face = f"M{x1 - e:.2f},{cy:.2f}A{e},{h} 0 1 1 {x1 + e:.2f},{cy:.2f}A{e},{h} 0 1 1 {x1 - e:.2f},{cy:.2f}Z"
    return corps, face


def haltere(silhouette=False):
    """Avant-plan. silhouette=True : formes pleines sans ombre (icône à thème d'Android 13)."""
    cy, e = 54, 2.8
    pieces = [(22.5, 26.5, 3.6), (26.5, 31.5, 9.5), (31.5, 38, 14),   # gauche : embout, petit et grand disque
              (38, 70, 2.6),                                          # poignée
              (70, 76.5, 14), (76.5, 81.5, 9.5), (81.5, 85.5, 3.6)]   # droite
    formes = []
    for k, (x0, x1, h) in enumerate(pieces):
        poignee = k == 3
        ee = 1.0 if poignee else e * (.55 if h < 5 else 1)
        corps, face = cylindre(x0, x1, cy, h, ee)
        if silhouette:
            formes += [{"d": corps, "p": ("plein", "#ffffff", 1)}, {"d": face, "p": ("plein", "#ffffff", 1)}]
        elif poignee:
            formes += [{"d": corps, "p": ("lin", 0, cy - h, 0, cy + h, CHROME)},
                       {"d": face, "p": ("lin", 0, cy - h, 0, cy + h, [(0, "#e6ebef", 1), (1, "#6d7a85", 1)])}]
        else:
            formes += [{"d": corps, "p": ("lin", 0, cy - h, 0, cy + h, FONTE)},
                       {"d": face, "p": ("rad", round(x1 - .8, 2), round(cy - h * .45, 2), round(h * 1.5, 2),
                                         [(0, "#7d8a95", 1), (.45, "#3d4952", 1), (1, "#151c21", 1)])}]
    groupe = {"groupe": formes, "pivot": (54, 54), "rotation": -24, "echelle": (.94, .94)}
    if silhouette:
        return [groupe]
    # ombre au sol : disque à dégradé radial, aplati par un groupe (pas d'ellipse dans un dégradé VectorDrawable)
    ombre = {"groupe": [{"d": cercle(55, 80, 30), "p": ("rad", 55, 80, 30, [(0, "#000000", .40), (.55, "#000000", .22), (1, "#000000", 0)])}],
             "pivot": (55, 80), "rotation": 0, "echelle": (1, round(4.2 / 30, 4))}
    return [ombre, groupe]


# ------------------------------------------------------------------ sortie SVG
def _svg(formes, defs, pre):
    out = []
    for f in formes:
        if "groupe" in f:
            (px, py), (sx, sy) = f["pivot"], f["echelle"]
            out.append(f'<g transform="translate({px} {py}) rotate({f["rotation"]}) scale({sx} {sy}) translate({-px} {-py})">'
                       + _svg(f["groupe"], defs, pre) + "</g>")
            continue
        p = f["p"]
        if p[0] == "plein":
            fill = f'fill="{p[1]}"' + (f' fill-opacity="{p[2]}"' if p[2] != 1 else "")
        else:
            gid = f"{pre}{len(defs)}"
            arrets = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a}"' if a != 1 else "") + "/>" for o, c, a in p[-1])
            if p[0] == "lin":
                defs.append(f'<linearGradient id="{gid}" x1="{p[1]}" y1="{p[2]}" x2="{p[3]}" y2="{p[4]}" gradientUnits="userSpaceOnUse">{arrets}</linearGradient>')
            else:
                defs.append(f'<radialGradient id="{gid}" cx="{p[1]}" cy="{p[2]}" r="{p[3]}" gradientUnits="userSpaceOnUse">{arrets}</radialGradient>')
            fill = f'fill="url(#{gid})"'
        out.append(f'<path d="{f["d"]}" {fill}/>')
    return "".join(out)


def svg(cle, vue=(0, 0, 108, 108), pre="g"):
    defs = []
    corps = _svg(fond(cle) + haltere(), defs, pre)
    x, y, w, h = vue
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x} {y} {w} {h}" width="{w}" height="{h}">'
            f'<defs>{"".join(defs)}</defs>{corps}</svg>')


# ------------------------------------------------------------------ sortie VectorDrawable
def _argb(c, a):
    return "#" + f"{round(a * 255):02x}" + c[1:] if a != 1 else c


def _vd(formes, ind="    "):
    out = []
    for f in formes:
        if "groupe" in f:
            (px, py), (sx, sy) = f["pivot"], f["echelle"]
            attrs = f'android:pivotX="{px}" android:pivotY="{py}"'
            if f["rotation"]:
                attrs += f' android:rotation="{f["rotation"]}"'
            if (sx, sy) != (1, 1):
                attrs += f' android:scaleX="{sx}" android:scaleY="{sy}"'
            out.append(f"{ind}<group {attrs}>\n" + _vd(f["groupe"], ind + "    ") + f"{ind}</group>\n")
            continue
        p = f["p"]
        if p[0] == "plein":
            out.append(f'{ind}<path android:fillColor="{_argb(p[1], p[2])}" android:pathData="{f["d"]}"/>\n')
            continue
        if p[0] == "lin":
            g = f'android:type="linear" android:startX="{p[1]}" android:startY="{p[2]}" android:endX="{p[3]}" android:endY="{p[4]}"'
        else:
            g = f'android:type="radial" android:centerX="{p[1]}" android:centerY="{p[2]}" android:gradientRadius="{p[3]}"'
        items = "".join(f'{ind}            <item android:offset="{o}" android:color="{_argb(c, a)}"/>\n' for o, c, a in p[-1])
        out.append(f'{ind}<path android:pathData="{f["d"]}">\n'
                   f'{ind}    <aapt:attr name="android:fillColor">\n'
                   f'{ind}        <gradient {g}>\n{items}{ind}        </gradient>\n'
                   f'{ind}    </aapt:attr>\n{ind}</path>\n')
    return "".join(out)


def vector(formes, titre):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            f"<!-- SPDX-License-Identifier: AGPL-3.0-or-later -->\n<!-- {titre} Fichier généré par tools/logo.py : ne pas modifier à la main. -->\n"
            '<vector xmlns:android="http://schemas.android.com/apk/res/android"\n'
            '    xmlns:aapt="http://schemas.android.com/aapt"\n'
            '    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">\n'
            + _vd(formes) + "</vector>\n")


def adaptive(cle):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">\n'
            f'    <background android:drawable="@drawable/ic_bg_{cle}" />\n'
            '    <foreground android:drawable="@drawable/ic_fg" />\n'
            '    <monochrome android:drawable="@drawable/ic_fg_mono" />\n'
            '</adaptive-icon>\n')


# ------------------------------------------------------------------ écriture
def ecrire(chemin, texte):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    with open(chemin, "w", encoding="utf-8", newline="\n") as f:
        f.write(texte)


def suffixe(cle):
    return "" if cle == "orange" else "_" + cle


def sorties_texte():
    ecrire(os.path.join(RES, "drawable", "ic_fg.xml"), vector(haltere(), "Logo : haltère (avant-plan)."))
    ecrire(os.path.join(RES, "drawable", "ic_fg_mono.xml"), vector(haltere(True), "Logo : silhouette pour l'icône à thème (Android 13+)."))
    for cle in COULEURS:
        ecrire(os.path.join(RES, "drawable", f"ic_bg_{cle}.xml"), vector(fond(cle), f"Logo : fond {cle}."))
        ecrire(os.path.join(RES, "mipmap-anydpi-v26", f"ic_launcher{suffixe(cle)}.xml"), adaptive(cle))
        # logo dans l'appli (menu, onglet) : la partie visible de l'icône, carré central de 72
        ecrire(os.path.join(ROOT, "server", "static", "icons", f"logo-{cle}.svg"), svg(cle, (18, 18, 72, 72)))


def sorties_png():
    """Images matricielles. WebP (avec perte légère, qualité 90) partout où c'est possible :
    un dégradé en PNG pèse 5 à 10 fois plus lourd, et la réduction de couleurs fait des bandes."""
    import io
    from PIL import Image
    from playwright.sync_api import sync_playwright
    travaux = []  # (chemin, couleur, taille, vue, rayon des coins en fraction de la taille)
    for cle in COULEURS:
        for d, t in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
            # anciens Android (7.x) : la partie visible, en carré aux coins arrondis
            travaux.append((os.path.join(RES, f"mipmap-{d}", f"ic_launcher{suffixe(cle)}.webp"), cle, t, (18, 18, 72, 72), .22))
        # version serveur (PWA « maskable » : un peu plus de marge, carré plein) ; 180 = icône Apple, en PNG
        for t, ext in ((180, "png"), (192, "webp"), (512, "webp")):
            travaux.append((os.path.join(ROOT, "server", "icons", f"icon-{cle}-{t}.{ext}"), cle, t, (12, 12, 84, 84), 0))
    for t in (192, 512):  # icônes par défaut de la version serveur (orange), dans le cache hors ligne
        travaux.append((os.path.join(ROOT, "server", "static", "icons", f"icon-{t}.webp"), "orange", t, (12, 12, 84, 84), 0))
    travaux.append((os.path.join(ROOT, "fastlane", "metadata", "android", "en-US", "images", "icon.png"), "orange", 512, (18, 18, 72, 72), .22))
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=1)
        for chemin, cle, t, vue, rayon in travaux:
            s = svg(cle, vue).replace(f'width="{vue[2]}" height="{vue[3]}"', f'width="{t}" height="{t}"')
            pg.set_viewport_size({"width": t, "height": t})
            pg.set_content(f'<html><body style="margin:0;background:transparent">'
                           f'<div style="width:{t}px;height:{t}px;border-radius:{rayon * t}px;overflow:hidden">{s}</div></body></html>')
            im = Image.open(io.BytesIO(pg.screenshot(omit_background=True, clip={"x": 0, "y": 0, "width": t, "height": t}))).convert("RGBA")
            os.makedirs(os.path.dirname(chemin), exist_ok=True)
            if chemin.endswith(".webp"):
                im.save(chemin, "WEBP", quality=90, method=6)
            else:
                (im if rayon else im.convert("RGB")).save(chemin, "PNG", optimize=True)
        b.close()
    return len(travaux)


if __name__ == "__main__":
    sorties_texte()
    n = 0 if "--svg-only" in sys.argv else sorties_png()
    print(f"Logo écrit : XML Android, SVG du menu{f' et {n} images' if n else ''}.")
