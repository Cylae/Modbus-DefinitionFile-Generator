# Plan d'Amélioration - Générateur de Définition Modbus

Ce document décrit le plan à long terme pour l'amélioration, l'optimisation et l'ajout de fonctionnalités à l'application.

## Phase 1: Amélioration des Tests

L'objectif est de construire une suite de tests robuste qui garantit la fiabilité du parser.

1.  **Refactoriser `test_parser.py` en un vrai framework de test.**
    *   Introduire `unittest` ou `pytest`.
    *   Créer des cas de test avec des assertions pour valider les résultats.
2.  **Créer des tests unitaires pour `parser.py`.**
    *   Tester `_is_header_row` avec différentes variations de headers.
    *   Tester `_parse_row_with_map` avec des données valides et invalides (erreurs de type, cellules manquantes).
    *   Tester `_is_stop_header` pour s'assurer qu'il arrête bien le parsing.
    *   Tester la logique de continuation de ligne pour la description (`scope`).
3.  **Étendre les tests de bout en bout.**
    *   Créer un répertoire `test_data` avec une collection de PDF de test.
    *   Inclure des PDF avec des mises en page différentes (de `Equipementiers/`).
    *   Inclure un PDF malformé ou un fichier non-PDF pour tester la gestion des erreurs.
    *   Pour chaque PDF de test, avoir un fichier `.json` ou `.csv` "attendu" pour comparer le résultat du parsing.

## Phase 2: Amélioration du Code du Parser

Basé sur les résultats des tests, améliorer la robustesse et la flexibilité du parser.

1.  **Améliorer la détection des en-têtes.**
    *   Ajouter plus de mots-clés à `HEADER_KEYWORDS` basés sur les PDF de `Equipementiers/`.
    *   Gérer les cas où les en-têtes sont sur plusieurs lignes.
2.  **Améliorer la gestion des types de données.**
    *   Gérer plus de types de données (ex: `INT32`, `UINT64`, `FLOAT32`).
    *   Extraire la taille du registre (`num_reg`) de manière plus fiable.
3.  **Améliorer la gestion des erreurs.**
    *   Remplacer le `except Exception` générique par des exceptions plus spécifiques.
    *   Fournir des messages d'erreur plus clairs à l'utilisateur via l'interface graphique.

## Phase 3: Amélioration de l'Interface Graphique (GUI)

1.  **Afficher la progression.** Ajouter une barre de progression pour le parsing des PDF longs.
2.  **Afficher les résultats.** Montrer un aperçu des données parsées dans l'interface avant de sauvegarder.
3.  **Améliorer le feedback d'erreur.** Afficher les erreurs de parsing directement dans l'interface au lieu de la console.
