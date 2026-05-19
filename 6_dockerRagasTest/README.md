# Conteneur 6 — `testragas`

Évaluation automatique du couple récupération + génération via le framework **Ragas**, avec un juge LLM externe (`gpt-4o`).

## Rôle dans le pipeline

```
… → getresponse → [ testragas ] → chatbot
```

Mesure objective de la qualité du RAG sur la grille de questions tests, pour détecter régressions et axes d'amélioration.

## Entrées et sorties

| Type   | Fichier                                       | Description                                     |
|--------|-----------------------------------------------|-------------------------------------------------|
| Entrée | `/data/05_reponse/QuestionTest.xlsx`          | Questions + réponses générées + contextes       |
| Sortie | `/data/06_testRagas/testRagas.xlsx`           | Résultats Ragas (faithfulness, precision, recall) |

## Métriques évaluées

| Métrique             | Volet         | Question posée                                   |
|----------------------|---------------|--------------------------------------------------|
| `faithfulness`       | Génération    | La réponse est-elle fidèle au contexte ?         |
| `context_precision`  | Récupération  | Le contexte retourné est-il pertinent ?          |
| `context_recall`     | Récupération  | Les informations clés ont-elles été retrouvées ? |

## Étapes exécutées

### `1.00_ragasTest.py`

1. Charge `QuestionTest.xlsx` (questions, réponses générées, contextes, vérité terrain).
2. Construit un `Dataset` HuggingFace au format attendu par Ragas.
3. Initialise le juge LLM (`ChatOpenAI` modèle `gpt-4o`) et les embeddings OpenAI.
4. Lance l'évaluation `evaluate(dataset, metrics, llm, embeddings)`.
5. Convertit le résultat en DataFrame et l'exporte dans `testRagas.xlsx`.

## Résultats obtenus

| Question                                | faithfulness | context_precision | context_recall |
|-----------------------------------------|:------------:|:-----------------:|:--------------:|
| Q1 — Évènements 25 août 2025 à Nice     | 1.00         | 0.00              | 0.50           |
| Q2 — Durée évènement PROVALP 3D         | 1.00         | 1.00              | 1.00           |
| Q3 — Date évènement PROVALP 3D          | 1.00         | 1.00              | 1.00           |
| Q4 — Évènement Lycée Parc Impérial      | 1.00         | 1.00              | 1.00           |
| Moyenne                             | 1.00    | 0.75          | 0.875     |

## Construction et lancement

```bash
docker compose up --build testragas
```

## Stack

- Image de base : `ubuntu:jammy`
- Dépendances clés : `ragas==0.4.3`, `langchain-openai==1.2.1`, `openai==2.32.0`, `datasets==4.8.5`, `pandas`, `openpyxl`

## Configuration

```bash
OPENAI_API_KEY=sk-...
```
