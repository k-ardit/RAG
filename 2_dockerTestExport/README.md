# Conteneur 2 — `testexport`

Tests qualité des données produites par le conteneur 1, export du rapport de tests et envoi d'un email récapitulatif.

## Rôle dans le pipeline

```
export → [ testexport ] → vectorisation → … → chatbot
```

Garde-fou qualité : si une dérive est détectée sur les données OpenData (changement de schéma, doublons, valeurs manquantes critiques), elle est tracée dans `testsExport.xlsx` et signalée par email.

## Entrées et sorties

| Type   | Fichier                                     | Description                                     |
|--------|---------------------------------------------|-------------------------------------------------|
| Entrée | `/data/Flow02/OpenData/FichierFinal.xlsx`   | Données nettoyées du conteneur 1                |
| Entrée | `/data/Flow02/OpenData/hashFiles.xlsx`      | Hash + idExport courant                         |
| Sortie | `/data/Flow02/OpenData/testsExport.xlsx`    | Rapport historisé des tests                     |
| Action | —                                           | Envoi d'un email récapitulatif                  |

## Étapes exécutées

`scripts/scripts.sh` enchaîne six scripts Python.

### 1. `1.00_TestInformationsFichiers.py`
Récupère le hash et l'idExport courants depuis `hashFiles.xlsx` pour les injecter dans le rapport de tests.

### 2. `2.00_TestRequette.py`
Vérifie que les données générées par le conteneur 1 concernent bien **Nice** et **l'année écoulée** (cohérence avec les filtres OpenData).

### 3. `3.00_TestsAbsenceDoublons.py`
Contrôle d'unicité sur la colonne `uid`. Recense le nombre de doublons éventuels.

### 4. `4.00_TestAbsenceValeursManquantes.py`
Identifie les colonnes contenant au moins une cellule vide et les liste dans le rapport.

### 5. `5.00_ExportTests.py`
Consolide tous les résultats dans `testsExport.xlsx`. Schéma :

| Champ                | Description                                        |
|----------------------|----------------------------------------------------|
| `idExport`           | Identifiant d'export (timestamp)                   |
| `publicEvent`        | Hash MD5 du fichier brut                           |
| `nbDoublons`         | Nombre de doublons détectés                        |
| `colValManquantes`   | Liste des colonnes avec valeurs manquantes         |
| `textEmail`          | Corps de l'email récapitulatif                     |
| `blockExtraction`    | `True` si un test bloquant a échoué                |

### 6. `6.00_EnvoiEmail.py`
Envoie un email à l'utilisateur configuré avec le `textEmail` ci-dessus.

## Construction et lancement

```bash
docker compose up --build testexport
```

## Stack

- **Image de base** : `alpine:edge`
- **Dépendances** (apk) : `python3`, `py3-pandas`, `py3-duckdb`, `py3-openpyxl`, `py3-scipy`, `bash`

## Configuration

Variables requises dans `dockerCompose_Flow02/.env` :

```bash
EMAIL_USER=votre@email.fr
EMAIL_PASSWORD=...
```
