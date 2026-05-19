# Conteneur 1 — `export`

Téléchargement, export brut et nettoyage des évènements publics de la ville de Nice depuis OpenData OpenAgenda. C'est le **point d'entrée** du pipeline RAG.

## Rôle dans le pipeline

```
[ export ] → testexport → vectorisation → … → chatbot
```

Premier maillon : produit le jeu de données nettoyé qui alimentera l'ensemble du pipeline.

## Entrées et sorties

| Type   | Fichier                                    | Description                                  |
|--------|--------------------------------------------|----------------------------------------------|
| Sortie | `/data/01_export/publicEvent.json`         | Données brutes téléchargées depuis OpenData  |
| Sortie | `/data/01_export/hashFiles.xlsx`           | Hash MD5 + idExport historisés               |
| Sortie | `/data/01_export/FichierFinal.xlsx`        | Données nettoyées (658 lignes, 57 colonnes)  |

## Étapes exécutées

Le script `scripts/scripts.sh` enchaîne quatre programmes Python.

### 1. `1.00_TelechargementsFichiers.py`
Télécharge les évènements publics niçois sur les 365 derniers jours via l'API OpenAgenda d'OpenDataSoft. Filtres appliqués : `location_city='Nice'` et `firstdate_begin >= today - 8760h`. Sauvegarde le résultat dans `publicEvent.json`.

### 2. `2.00_ExportsDonnees.py`
Importe le JSON dans une base DuckDB (`openclassrooms.db`), table `publicEvent`. Calcule un hash MD5 du fichier brut et de chaque lignes et l'idExport (timestamp), historisés dans `hashFiles.xlsx` pour la traçabilité.

### 3. `3.00_NettoyageDonnees.py`
Crée une réplique nettoyée (`publicEventNettoyee`) :

- suppression des colonnes 100 % vides ;
- suppression des lignes sans `uid` ;
- déduplication par `uid`.

### 4. `4.00_ExportFichierFinal.py`
Exporte la table nettoyée dans `FichierFinal.xlsx`.

## Construction et lancement

Depuis `RAG/` :

```bash
# Dans le pipeline complet
docker compose up --build export

# Build local et exécution autonome
docker compose build export
docker compose up export
```

## Stack

- Image de base : `alpine:edge`
- Dépendances (apk) : `python3`, `py3-pandas`, `py3-duckdb`, `py3-openpyxl`, `py3-requests`, `bash`
- DuckDB est récupéré depuis le repository `edge/testing` (le seul à l'embarquer).


