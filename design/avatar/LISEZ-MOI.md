# Prototypes d'avatar (REFUSÉS, à ne pas reprendre tels quels)

Trois directions dessinées à la main en SVG par code : A « Héros », B « Mascotte », C « Sticker ».
Georgio les a regardées et **ne les trouve pas à la hauteur** (« les design ne me conviennent pas »).
Elles servent seulement de point de départ et d'exemples de ce qu'on ne veut pas : rendu mannequin pour A,
trop simple pour B, trop lourd pour C. Le code est volontairement laissé tel quel (pas de tests, pas de finition).

- `core.js` : outils de dessin (courbes lisses, tubes, palettes de peau).
- `styleA.js`, `styleB.js`, `styleC.js` : un rendu par direction, `render(options)` renvoie un SVG.
- `sheet.py` : planche de contrôle (Playwright). `dump.py` : écrit des SVG. `cmp.js` : comparatif.
- `propositions-refusees.png` : ce que Georgio a vu.

La nouvelle piste doit passer par Blender (voir CLAUDE.md, section « Avatar »).
