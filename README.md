# PlantTrace PDF CrossRef

PlantTrace est un outil desktop local pour retrouver des references croisees dans de gros dossiers PDF industriels.

Il fait une seule chose : indexer des PDF, chercher une reference ou une expression, retourner le fichier, la page, l'extrait et le type de preuve, puis exporter le resultat.

## Demarrage

```powershell
cd "C:\Users\yoann.dumont\Desktop\VSCODE\Agent'Art\PlantTrace"
python tools\check_environment.py
.\run_gui.ps1
```

Le guide complet est dans [TUTORIEL.md](TUTORIEL.md).

Dans l'interface :

1. `Projet` : dossier ou sera stocke l'index `.planttrace`.
2. `PDF` : dossier racine contenant les PDF a indexer.
3. `Indexer` : parse tous les PDF, pages et textes.
4. `Recherche` : entrer `FV1100`, `10-P-12345`, `fournisseur cafe`, etc.
5. `Export XLSX` : exporte les resultats affiches.

## Commandes

```powershell
planttrace index --project . --pdf-root "D:\Projet\PDF" --force
planttrace search --project . --query FV1100 --mode hybrid --output results.xlsx
planttrace coverage --project .
planttrace semantic-status --project .
```

Modes de recherche :

- `exact` : meilleur choix pour tags, vannes, lignes, instruments, borniers.
- `text` : plein texte BM25 pour mots et phrases.
- `fuzzy` : tolere les petites fautes de frappe.
- `semantic` : embeddings locaux uniquement si un modele local est installe.
- `hybrid` : exact + texte + semantic si disponible, puis fuzzy si rien ne sort.

## OCR

PlantTrace detecte les pages sans texte. Pour OCRiser les scans, installer l'executable Windows Tesseract puis lancer :

```powershell
planttrace index --project . --pdf-root "D:\Projet\PDF" --ocr --ocr-lang eng
```

Sans Tesseract, les pages scannees restent marquees `ocr_required`; ce statut apparait dans la couverture et les resultats.

## Semantique locale

PlantTrace ne telecharge pas de modele. Pour activer le mode semantique, placer un modele SentenceTransformers local ici :

```text
.planttrace\models\embedding-model
```

Puis lancer :

```powershell
planttrace embed --project .
planttrace search --project . --query "fournisseur de cafe" --mode semantic
```

## Preuve et audit

Chaque resultat indique :

- `match_type` : exact, OCR-normalise, texte, fuzzy ou semantic.
- `document_path` : PDF source.
- `page` : page trouvee.
- `excerpt` : extrait de preuve.
- `page_status` : `ok`, `ocr_ok`, `ocr_required` ou `ocr_failed`.
- `document_status` : couverture documentaire du PDF.

Une absence signifie : aucune occurrence dans le corpus indexe et les pages OCRisees disponibles.
