# Tutoriel PlantTrace

Ce guide explique comment utiliser PlantTrace de A a Z pour retrouver des references dans un gros dossier de PDF industriels.

## 1. Lancer PlantTrace

Ouvrir PowerShell dans le dossier PlantTrace :

```powershell
cd "C:\Users\yoann.dumont\Desktop\VSCODE\Agent'Art\PlantTrace"
.\run_gui.ps1
```

Si l'interface ne s'ouvre pas, verifier l'environnement :

```powershell
python tools\check_environment.py
```

Les points indispensables sont `pymupdf`, `pyside6`, `openpyxl` et `numpy`.

## 2. Choisir les dossiers

Dans l'interface :

- `Index local` : dossier ou PlantTrace stocke son index `.planttrace`.
- `Dossier PDF source` : dossier qui contient les PDF a analyser.

Le dossier PDF source peut contenir des sous-dossiers. PlantTrace indexe tous les fichiers `*.pdf` trouves dedans.

Conseil : garder `Index local` dans un dossier de travail PlantTrace, et pointer `Dossier PDF source` vers le dossier documentaire. Eviter de stocker l'index dans un dossier PDF verrouille, reseau, lecture seule ou synchronise si SQLite renvoie une erreur d'ouverture.

## 3. Indexer les PDF

Cliquer sur `Indexer`.

PlantTrace lit chaque PDF, chaque page, et stocke :

- le chemin du fichier,
- le numero de page,
- le texte extrait,
- une version normalisee pour les tags industriels,
- des morceaux de texte pour la recherche fuzzy et semantique.

Utiliser `Force` quand les PDF ont ete modifies ou quand il faut reconstruire l'index.

## 4. Lire la couverture

Apres indexation, le panneau affiche :

- `docs` : nombre de PDF connus.
- `pages` : nombre total de pages indexees.
- `texte` : pages avec texte exploitable.
- `OCR requis` : pages scannees ou sans texte.
- `OCR echec` : pages pour lesquelles l'OCR a echoue.

Si `OCR requis` est superieur a zero, une absence de resultat ne prouve pas que la reference n'existe pas dans les scans. Elle prouve seulement qu'elle n'existe pas dans le texte indexe.

## 5. Chercher une reference exacte

Exemples :

```text
FV1100
FV-1100
10-P-12345
JB42
HS 0900
```

Mode conseille : `hybrid`.

Pour les tags, PlantTrace normalise les separateurs. Une recherche `FV1100` peut retrouver `FV-1100`, `FV 1100` ou `FV_1100`.

## 6. Chercher une phrase ou un mot

Exemples :

```text
fournisseur cafe
armoire automate
liste instruments
vanne securite
```

Mode conseille : `hybrid` ou `text`.

Le resultat donne le PDF, la page et un extrait avec les mots retrouves.

## 7. Chercher avec une approximation

Exemple :

```text
fourniseur cafee
```

Mode conseille : `fuzzy`.

Ce mode tolere les petites fautes de frappe. Il est utile quand un mot est incertain, mais un resultat fuzzy doit etre relu via l'extrait et le PDF.

## 8. Ouvrir le PDF source

Double-cliquer sur une ligne de resultat.

PlantTrace ouvre le PDF dans le lecteur par defaut Windows. La page est indiquee dans la colonne `Page`.

## 9. Exporter vers Excel

Cliquer sur `Export XLSX`.

Le fichier contient :

- requete,
- type de match,
- chemin PDF,
- page,
- score,
- extrait,
- statut page,
- statut document.

C'est le livrable typique pour une revue projet, une verification de references ou un suivi de cross-citations.

## 10. OCR des PDF scannes

PlantTrace sait appeler Tesseract, mais l'executable Windows doit etre installe sur le poste.

Verifier :

```powershell
python tools\check_environment.py
```

Si `tesseract_exe` est vide, l'OCR systeme n'est pas installe.

Une fois Tesseract installe :

```powershell
planttrace index --project . --pdf-root "D:\Projet\PDF" --ocr --ocr-lang eng
```

Pour du francais, utiliser `--ocr-lang fra` si le pack de langue Tesseract francais est installe.

## 11. Recherche semantique locale

Le semantique est optionnel et 100% local. PlantTrace ne telecharge aucun modele tout seul.

Placer un modele SentenceTransformers local ici :

```text
.planttrace\models\embedding-model
```

Puis construire les vecteurs :

```powershell
planttrace embed --project .
```

Ensuite utiliser le mode `semantic` ou `hybrid`.

## 12. Commandes utiles sans interface

Indexer :

```powershell
planttrace index --project . --pdf-root "D:\Projet\PDF" --force
```

Chercher et exporter :

```powershell
planttrace search --project . --query FV1100 --mode hybrid --output FV1100.xlsx
```

Voir la couverture :

```powershell
planttrace coverage --project .
```

Verifier le semantique :

```powershell
planttrace semantic-status --project .
```

Extraire automatiquement les references du corpus :

```powershell
planttrace extract --project . --output extraction.xlsx
```

## 13. Mode Extraction

Le mode `Extraction` ne part pas d'une recherche utilisateur. Il parcourt tout l'index et remonte les references candidates selon les regles projet.

Sortie :

```text
Type | Valeur | Regle | Fichier | Page | Extrait | Confiance | Statuts
```

Types par defaut :

- `TAG` : tags instrument ou equipement comme `FV1100`, `FV-1100`, `PT2045`.
- `LINE` : lignes tuyauterie comme `10-P-12345`.
- `DOC` : numeros document projet comme `HTI199-VEN-ELE-...`.
- `INITIALS` : initiales comme `JDY`, `DBT`, avec confiance basse.

Ce mode sert a faire un inventaire documentaire : "quelles references existent dans ces PDF ?".

## 14. Regles projet

L'onglet `Regles` permet de creer, modifier, tester et sauvegarder les patterns utilises par l'extraction. Ces regles sont deterministes : elles evitent de faire deviner au logiciel ce qu'est un tag.

Les regles par defaut sont volontairement prudentes. Sur un vrai projet, il faudra les ajuster si les conventions tag/ligne/document changent.

Chaque regle contient :

- `Nom` : libelle lisible.
- `Type` : `TAG`, `LINE`, `DOC`, `INITIALS` ou `CUSTOM`.
- `Pattern` : expression reguliere.
- `Confiance` : `high`, `medium` ou `low`.
- `Active` : la regle est utilisee ou ignoree par l'extraction.

Workflow conseille :

1. Selectionner une regle existante ou cliquer `Ajouter`.
2. Saisir/modifier le pattern.
3. Coller un extrait PDF dans `Test regle`.
4. Cliquer `Tester`.
5. Verifier les valeurs detectees.
6. Cliquer `Sauvegarder`.
7. Relancer `Extraction`.

Exemple de regle tag instrumentation :

```text
Nom: Tags instrumentation projet
Type: TAG
Pattern: \b(FV|PV|PT|TT|XV)[-_ ]?\d{3,5}[A-Z]?\b
Confiance: high
Active: oui
```

La stoplist sert a ignorer les faux positifs projet. Une valeur par ligne :

```text
BP13
RJ45
PLAN619
```

Ces fichiers sont sauvegardes localement dans `.planttrace/rules.json` et `.planttrace/stoplist.txt`.

## 15. Regle d'interpretation des resultats

Un resultat positif est une preuve localisee : fichier, page, extrait.

Un resultat absent est une absence dans le texte indexe. Si des pages sont `OCR requis` ou `OCR echec`, il faut traiter ces pages avant de conclure documentairement.
