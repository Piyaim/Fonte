# SPDX-License-Identifier: AGPL-3.0-or-later
# Module (pas un test) : importer et exporter par l'écran Données, quelle que soit la version du code ouverte dans la page.
# - Depuis la 0.7.3 (lot 4) : le texte collé est d'abord LU et décrit, puis « Remplacer mes données » (ou « Ajouter … ») et la
#   confirmation ; liens « Exporter mes séances » et « Exporter mes photos ».
# - Avant : zone de texte, bouton « Importer », liens « Télécharger l'export » et « Télécharger les photos ».
# Les tests de migration ouvrent les deux (code d'une ancienne version et code actuel) : la page affichée décide du chemin.
NOUVEAU = "#app button:has-text('Lire ce texte'), #app label.btn:has-text('Choisir un fichier')"

def nouvelle(pg):
    return pg.locator(NOUVEAU).count() > 0

def importer_texte(pg, texte, attente=1500):
    """Importe `texte` (JSON) depuis l'écran Données déjà affiché ; les boîtes de confirmation doivent être acceptées par le test."""
    if nouvelle(pg):
        pg.evaluate("document.querySelectorAll('#app details').forEach(d => d.open = true)")
        pg.fill("#bk", texte); pg.click("#app button:has-text('Lire ce texte')"); pg.wait_for_selector("#app .file", timeout=8000)
        if pg.locator("#app .file ~ .qerr").count():   # fichier refusé dès la lecture : aucun bouton d'import, rien n'est importé
            pg.wait_for_timeout(attente); return
        pg.click("#app button:has-text('Remplacer mes données'), #app button:has-text('Ajouter les'), #app button:has-text('Ajouter la photo')")
    else:
        pg.fill("#bk", texte)
        b = pg.locator("button.go:has-text('Importer')")
        (b if b.count() else pg.locator("button:has-text('Importer')")).first.click()
    pg.wait_for_timeout(attente)

def lien_export(pg, photos=False):
    """Texte du lien d'export de l'écran Données affiché (séances, ou photos)."""
    if nouvelle(pg): return "Exporter mes photos" if photos else "Exporter mes séances"
    return "Télécharger les photos" if photos else "Télécharger l'export"
