# Conteneur 5 — `getresponse`

Génération des réponses via l'API Mistral à partir des questions tests, en s'appuyant sur l'index FAISS.

## Rôle dans le pipeline

```
… → testvectorisation → [ getresponse ] → testragas → chatbot
```

Pour chaque question de la grille de tests, génère une réponse et stocke les chunks utilisés. Le fichier résultant alimente l'évaluation Ragas du conteneur 6.

## Entrées et sorties

| Type     | Fichier                                       | Description                              |
|----------|-----------------------------------------------|------------------------------------------|
| Entrée   | `/data/03_vectorisation/faiss_index.idx`      | Index FAISS                              |
| Entrée   | `/data/03_vectorisation/chunks.pkl`           | Chunks alignés sur l'index               |
| Entrée   | `/data/04_testVectorisation/QuestionTest.xlsx`| Questions + réponses attendues + identifiants + rang + score       |
| Sortie   | `/data/05_reponse/QuestionTest.xlsx`          | Fichier enrichi (`Reponse`, `IdContext`, `ContextList`) |

## Étapes exécutées

### `getReponses.py`

Pour chaque question :

1. Calcule l'embedding via `mistral-embed`.
2. Recherche les k = 100 chunks les plus pertinents avec `min_score = 0.8` (paramètres retenus après calibrage par le conteneur 4).
3. Construit le prompt avec un prompt système strict (cf. ci-dessous).
4. Appelle `mistral-large-latest` (chat).
5. Extrait la liste des identifiants de sources émise en JSON en début de réponse.
6. Stocke `Reponse`, `IdContext` et `ContextList` dans `QuestionTest.xlsx`.

## Prompt système

```
Vous êtes un assistant virtuel pour des évènements situés à Nice.
Répondez à la question de l'utilisateur en vous basant UNIQUEMENT sur
le contexte fourni ci-dessous. Mettez la liste des identifiants des
sources en format JSON dès le début afin de pouvoir les extraire.
Si l'information n'est pas dans le contexte, dites que vous ne savez
pas ou que l'information n'est pas disponible dans les documents fournis.
Soyez concis et précis. Citez vos sources si possible (par exemple, en
mentionnant les informations trouvées dans les métadonnées) et l'identifiant
du document.

Contexte fourni :
---
{context_str}
---
```

## Paramètres

| Paramètre        | Valeur                  |
|------------------|-------------------------|
| Modèle LLM       | `mistral-large-latest`  |
| Modèle embedding | `mistral-embed`         |
| `k`              | 100                     |
| `min_score`      | 0.80                    |

## Construction et lancement

```bash
docker compose up --build getresponse
```

## Stack

- Image de base : `ubuntu:jammy`
- Dépendances clés : `mistralai==0.4.2`, `faiss-cpu==1.10.0`, `pandas`, `openpyxl`

## Configuration

MISTRAL_API_KEY
