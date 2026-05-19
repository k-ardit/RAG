# Conteneur 4 — `testvectorisation`

Test de la qualité de la récupération vectorielle : pour chaque question d'une grille préparée manuellement, on vérifie le rang (k) et le score des chunks attendus dans les résultats FAISS.

## Rôle dans le pipeline

```
… → vectorisation → [ testvectorisation ] → getresponse → … → chatbot
```

Calibre les paramètres de recherche (`k`, `min_score`) en confrontant les résultats FAISS à une vérité terrain manuelle.

## Entrées et sorties

| Type   | Fichier                                        | Description                              |
|--------|------------------------------------------------|------------------------------------------|
| Entrée | `/data/03_vectorisation/faiss_index.idx`       | Index FAISS du conteneur 3               |
| Entrée | `/data/03_vectorisation/chunks.pkl`            | Chunks alignés sur l'index               |
| Entrée | `/data/QuestionTest.xlsx`                      | Grille de questions tests (manuelle) question + réponses attendues + identifiants|
| Sortie | `/data/04_testVectorisation/QuestionTest.xlsx` | Fichier complété avec rang et score      |

## Étapes exécutées

### `1.00_testVectorisation.py`

1. Charge l'index FAISS et les chunks.
2. Pour chaque question de `QuestionTest.xlsx` :
   - Calcule l'embedding via `mistral-embed`.
   - Recherche les k = 210 chunks les plus pertinents avec `min_score = 0.7`.
   - Pour chaque identifiant attendu (colonne `IdentifiantsATrouver`), récupère son rang et son score.
3. Sauvegarde dans les colonnes `identifiant/k` et `identifiant/score`.

## Schéma de `QuestionTest.xlsx`

| Champ                  | Description                                              |
|------------------------|----------------------------------------------------------|
| `Id`                   | Identifiant de la question                               |
| `Question`             | Question posée                                           |
| `ReponseAttendue`      | Réponse de référence rédigée par un humain               |
| `IdentifiantsATrouver` | Identifiants des lignes Excel sources attendues          |
| `identifiant/k`        | Rang de chaque identifiant dans la recherche FAISS       |
| `identifiant/score`    | Score (%) de chaque identifiant dans la recherche FAISS  |

## Résultats observés

Sur la grille de 4 questions tests, les chunks réellement pertinents apparaissent systématiquement avec un score > 80 %.
→ Paramètres retenus pour la production : `k = 100`, `min_score = 0.8`.

## Construction et lancement

```bash
docker compose up --build testvectorisation
```

## Stack

- Image de base : `ubuntu:jammy`
- Dépendances clés : `mistralai==0.4.2`, `faiss-cpu==1.10.0`, `pandas`, `openpyxl`

## Configuration

MISTRAL_API_KEY
