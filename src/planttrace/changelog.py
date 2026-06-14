from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ChangelogSection:
    title: str
    items: tuple[str, ...]


@dataclass(frozen=True)
class Release:
    version: str
    date: str
    tagline: str
    sections: tuple[ChangelogSection, ...]


# Newest first. Garder en tête à jour avec planttrace.__version__ à chaque release.
RELEASES: tuple[Release, ...] = (
    Release(
        version="0.3.0",
        date="14 juin 2026",
        tagline="La mise à jour en un clic, et des finitions.",
        sections=(
            ChangelogSection(
                "Nouveautés",
                (
                    "Mise à jour en un clic : quand une nouvelle version est disponible, l'application "
                    "la télécharge, l'installe à la place de l'ancienne et redémarre toute seule. "
                    "Votre index (.planttrace) n'est jamais touché.",
                    "Fenêtre « À propos » avec le logo, la version et un accès direct à ce journal.",
                ),
            ),
            ChangelogSection(
                "Améliorations",
                (
                    "Barre d'activité : le logo laisse place à un bouton « Rechercher » qui ouvre "
                    "la palette de commande (Ctrl+Maj+P).",
                ),
            ),
            ChangelogSection(
                "Corrections",
                (
                    "Repli de la barre d'activité : petit artefact « > » supprimé à côté du chevron.",
                ),
            ),
        ),
    ),
    Release(
        version="0.2.0",
        date="14 juin 2026",
        tagline="La preuve en un coup d'œil, et la recherche dans toute la base.",
        sections=(
            ChangelogSection(
                "Nouveautés",
                (
                    "Visionneuse de preuve : la page du PDF s'affiche directement dans l'application, "
                    "avec votre référence surlignée en jaune — plus besoin d'ouvrir Acrobat pour vérifier.",
                    "Recherche universelle (Ctrl+Maj+P) : tapez un tag, les résultats arrivent classés "
                    "par discipline (P&ID, Loop, Datasheet…) avec l'aperçu de la page à côté.",
                    "Master Tag Register : génère le registre au format client (Tags + liens "
                    "Tags-Documents) en fusionnant vos listes de tags existantes et les occurrences "
                    "trouvées dans les PDF indexés, avec une feuille de preuves.",
                    "Mode immersion (Ctrl+B) : masquez le panneau latéral pour donner toute la largeur "
                    "aux grands tableaux.",
                    "Mises à jour intégrées : un clic sur la version vérifie la dernière release "
                    "et ouvre ce journal des nouveautés.",
                ),
            ),
            ChangelogSection(
                "Améliorations",
                (
                    "Barre d'activité plus nette : la sélection est une pastille arrondie.",
                    "Le numéro de version est affiché en bas à droite.",
                ),
            ),
            ChangelogSection(
                "Corrections",
                (
                    "Les boutons d'action (Indexer, Chercher, Extraire) sont de nouveau bien visibles — "
                    "ils se fondaient dans le fond blanc.",
                    "Les boutons de choix de dossier sont visibles.",
                    "Panneau Règles : les tableaux affichent enfin toutes leurs lignes.",
                ),
            ),
        ),
    ),
    Release(
        version="0.1.0",
        date="13 juin 2026",
        tagline="Retrouver n'importe quelle référence dans des milliers de PDF — avec la preuve.",
        sections=(
            ChangelogSection(
                "Ce que fait PlantTrace",
                (
                    "100 % local : vos documents ne quittent jamais votre poste, aucune connexion requise.",
                    "Indexe des dossiers entiers de PDF industriels.",
                    "Cherche un tag ou une expression (FV1100, 10-P-12345, « fournisseur café »…) et renvoie "
                    "le fichier, la page, l'extrait et le type de preuve.",
                    "Plusieurs modes de recherche : exact (tags et instruments), texte, tolérant aux fautes, "
                    "sémantique, ou hybride.",
                    "OCR optionnel pour les plans scannés.",
                    "Couverture documentaire : sait quelles pages sont lisibles ou nécessitent un OCR.",
                    "Inventaire automatique des tags, lignes et documents selon vos règles projet.",
                    "Outils de contrôle : matrice de présence, familles de documents, conflits, "
                    "comparaison de révisions.",
                    "Exports Excel prêts à livrer (résultats, fiche d'une référence, livrable ZIP).",
                ),
            ),
        ),
    ),
)
