# RAG — Évènements publics de Nice

Pipeline Retrieval-Augmented Generation industrialisé pour interroger en langage naturel les évènements publics de la commune de Nice. Le projet enchaîne sept conteneurs Docker, de l'extraction OpenData jusqu'à un chatbot Streamlit, avec tests automatisés des données, de la récupération vectorielle et de la génération.

![Docker Compose](https://img.shields.io/badge/Docker%20Compose-orchestration-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![Mistral](https://img.shields.io/badge/Mistral-large--latest-FA520F)
![FAISS](https://img.shields.io/badge/FAISS-IndexFlatIP-005571)
![Streamlit](https://img.shields.io/badge/Streamlit-port%208501-FF4B4B?logo=streamlit&logoColor=white)

---

## Sommaire

- [Architecture](#architecture)
- [Démarrage rapide](#démarrage-rapide)
- [Détail des conteneurs](#détail-des-conteneurs)
- [Configuration](#configuration)
- [Données et artefacts](#données-et-artefacts)
- [Résultats](#résultats)
- [Stack technique](#stack-technique)
- [Structure du dépôt](#structure-du-dépôt)
- [Limites et perspectives](#limites-et-perspectives)
- [Auteur](#auteur)

---

## Architecture

Sept conteneurs Docker enchaînés séquentiellement via `depends_on: service_completed_successfully`. Chacun lit/écrit dans un volume partagé `./data/ → /data/` qui joue le rôle de bus de données.

```
┌────────┐   ┌─────────────┐   ┌──────────────┐   ┌───────────────────┐
│ export │ → │ testexport  │ → │ vectorisation│ → │ testvectorisation │
└────────┘   └─────────────┘   └──────────────┘   └─────────┬─────────┘
                                                            ▼
                                  ┌───────────┐   ┌───────────────┐   ┌─────────────┐
                                  │  chatbot  │ ← │   testragas   │ ← │ getresponse │
                                  └───────────┘   └───────────────┘   └─────────────┘
```

| # | Service               | Rôle                                         | Sortie principale                        |
|---|-----------------------|----------------------------------------------|------------------------------------------|
| 1 | `export`              | Téléchargement OpenData + nettoyage DuckDB   | `FichierFinal.xlsx`                      |
| 2 | `testexport`          | Tests qualité données + email                | `testsExport.xlsx`                       |
| 3 | `vectorisation`       | Chunking + embeddings + index FAISS          | `faiss_index.idx`, `document_chunks.pkl` |
| 4 | `testvectorisation`   | Test de récupération (k, score)              | `QuestionTest.xlsx`                      |
| 5 | `getresponse`         | Génération via Mistral Large                 | `QuestionTest.xlsx` (enrichi)            |
| 6 | `testragas`           | Évaluation Ragas (juge gpt-4o)               | `testRagas.xlsx`                         |
| 7 | `chatbot`             | Interface utilisateur Streamlit              | Application sur `:8501`                  |

Chaque conteneur a son propre README détaillé dans `RAG/<n>_docker*/README.md`.

---

## Démarrage rapide

### Prérequis

- Docker et Docker Compose
- Une clé API Mistral
- Une clé API OpenAI (pour le juge Ragas)
- Un compte mail (pour la notification du conteneur 2)

### Installation

git clone <url-du-repo>
cd RAG

Créer un fichier `.env` à la racine de `RAG/` :

MISTRAL_API_KEY=sk-...
OPENAI_API_KEY=sk-...
EMAIL_USER=votre@email.fr
EMAIL_PASSWORD=...

### Lancement du pipeline complet

docker compose up --build


Les six premiers conteneurs s'exécutent séquentiellement puis se terminent. Le conteneur `chatbot` reste en vie et expose l'application sur <http://localhost:8501>.

### Lancement à l'unité

# Régénérer uniquement l'index vectoriel
docker compose up --build vectorisation

# Relancer uniquement l'évaluation Ragas
docker compose up --build testragas

---

## Détail des conteneurs

### 1. `export` — Extraction et nettoyage

- Téléchargement via l'API OpenData OpenAgenda : commune de Nice, sur les 365 derniers jours.
- Stockage du JSON brut dans `publicEvent.json`.
- Import dans DuckDB, génération d'un hash MD5 + idExport historisés dans `hashFiles.xlsx`.
- Nettoyage : suppression des colonnes vides, des lignes sans `uid`, déduplication.
- Export final : `FichierFinal.xlsx` — ~650 lignes, 57 colonnes.

### 2. `testexport` — Qualité des données

- Vérifie que les données concernent bien Nice et l'année écoulée.
- Contrôle d'unicité sur les `uid`.
- Liste des colonnes avec valeurs manquantes.
- Stocke le résultat dans `testsExport.xlsx` et envoie un email récapitulatif.

### 3. `vectorisation` — Indexation FAISS

- vectorisation des chunks qui n'ont pas déjà été vectorisé (comparaison grace au hash de chaque ligne)
- Préparation de `chunk.xlsx` et `chunk.xlsx` (~ 1 500 lignes : `id, text, metadata`)..
- taille d'un chunk = une ligne Excel, `chunk_overlap = 0`.
- Embeddings `mistral-embed` (dim 1 024), par lots de 32, normalisés L2.
- Index FAISS `IndexFlatIP` → sérialisé dans `faiss_index.idx`.

### 4. `testvectorisation` — Test de récupération

- Grille de questions tests préparée manuellement (question, réponse attendue, identifiants Excel cibles).
- Recherche FAISS avec `k = 210` et `min_score = 0.7`.
- Récupère rang et score réel de chaque identifiant attendu.
- Stocke le résultat dans `QuestionTest.xlsx`.

### 5. `getresponse` — Génération Mistral

- Pour chaque question : embedding → recherche FAISS → prompt système → appel à `mistral-large-latest`.
- Paramètres de production retenus : `k = 100`, `min_score = 0.8`.
- Le prompt système oblige le modèle à ne s'appuyer que sur le contexte fourni et à émettre la liste des identifiants de sources en JSON en début de réponse.

### 6. `testragas` — Évaluation automatique

- Cadre Ragas, juge LLM externe `gpt-4o`, embeddings OpenAI.
- Trois métriques :
  - faithfulness — la réponse est-elle fidèle au contexte ?
  - context_precision — le contexte récupéré est-il pertinent ?
  - context_recall — les informations clés ont-elles été retrouvées ?
- Résultats dans `testRagas.xlsx`.

### 7. `chatbot` — Interface Streamlit

Interface graphique disponible sur <http://localhost:8501> :

- Sélection du modèle Mistral (Small / Large).
- Réglage du nombre de documents (1 → 250) et du score minimum.
- Classifieur de requêtes (mode RAG ou mode direct).
- Affichage des sources et scores.
- Historique persistant.

---

## Configuration

Variables d'environnement à définir dans `dockerCompose_Flow02/.env` :

| Variable          | Utilisé par                              | Description                                |
|-------------------|------------------------------------------|--------------------------------------------|
| `MISTRAL_API_KEY` | `vectorisation`, `getresponse`, `chatbot`| Clé API Mistral pour embeddings + chat     |
| `OPENAI_API_KEY`  | `testragas`                              | Clé OpenAI pour le juge Ragas (gpt-4o)     |
| `EMAIL_USER`      | `testexport`                             | Adresse d'envoi de l'email de notification |
| `EMAIL_PASSWORD`  | `testexport`                             | Mot de passe / app password associé        |

---


## Données et artefacts

Tous les conteneurs partagent le volume `./data → /data`.

data/
├── 01_export/
│   ├── publicEvent.json        # données brutes téléchargées
│   ├── FichierFinal.xlsx       # données nettoyées (658 lignes)
│   ├── hashFiles.xlsx          # hash + idExport historisés
├── 02_exportTest/
│   └── testsExport.xlsx        # résultats des tests qualité
├── 03_vectorisation/
│   ├── faiss_index.idx         # index FAISS (~1 500 vecteurs)
│   └── chunks.pkl              # chunks alignés avec l'index
│   └── vectors.xlsx            # vecteurs pour chaque chunk
│   ├── chunks.xlsx             # index FAISS (~1 500 vecteurs)
├── 04_testVectorisation/
│   ├── QuestionTest.xlsx       # grille de tests Q/R  
├── 05_reponse/
│   ├── QuestionTest.xlsx       # grille de tests Q/R   
├── 06_testRagas/
│   └── testRagas.xlsx          # résultats Ragas
├── QuestionTest.xlsx           # grille de tests Q/R  

---


## Résultats

Évaluation Ragas sur la grille de questions tests :

| Question                                  | faithfulness | context_precision | context_recall |
|-------------------------------------------|:------------:|:-----------------:|:--------------:|
| Q1 — Évènements 25 août 2025 à Nice       | 1.00         | 0.00              | 0.50           |
| Q2 — Durée évènement PROVALP 3D           | 1.00         | 1.00              | 1.00           |
| Q3 — Date évènement PROVALP 3D            | 1.00         | 1.00              | 1.00           |
| Q4 — Évènement Lycée Parc Impérial        | 1.00         | 1.00              | 1.00           |
| Moyenne                               | 1.00     | 0.75          | 0.875      |

- Aucune hallucination détectée : la faithfulness moyenne est de 1.00.
- Le décrochage sur Q1 vient du fait que la question vise plusieurs évènements simultanément ; un seul des deux chunks attendus a été récupéré.

---

## Stack technique

| Couche                | Briques                                                                |
|-----------------------|------------------------------------------------------------------------|
| Orchestration         | Docker, Docker Compose, volumes partagés Linux                         |
| Données               | OpenData OpenAgenda (API REST), DuckDB, Pandas, openpyxl               |
| Vectorisation         | LangChain, Mistral Embed, FAISS       |
| Génération            | Mistral Large (`mistral-large-latest`)                                 |
| Évaluation            | Ragas, OpenAI gpt-4o (juge), OpenAI embeddings                         |
| Interface             | Streamlit, SQLite                                                      |

---

## Structure du dépôt

RAG/
├── data/
│   └──                       # volume de données (artefacts du pipeline)
├── RAG/
│   ├── docker-compose.yml
│   ├── .env                          # clés API (non versionné)
│   ├── 1_dockerExport/
│   ├── 2_dockerTestExport/
│   ├── 3_dockerVectorisation/
│   ├── 4_dockerTestVectorisation/
│   ├── 5_dockerGetReponses/
│   ├── 6_dockerRagasTest/
│   └── 7_dockerChatBot/
├── RAG_Presentation.pptx             # présentation du projet (15 slides)
├── RAG_Rapport_Technique.docx        # rapport technique détaillé
└── README.md

---


## Limites et perspectives

- Questions multi-évènements : la `context_precision` chute lorsqu'une question recouvre plusieurs évènements. Piste : stratégie de chunking par date d'évènement.
- Grille de tests réduite (4 questions) : étendre à ~30 questions diversifiées pour gagner en représentativité statistique.
- Re-ranking : ajouter un cross-encoder entre FAISS et le LLM pour améliorer la précision du contexte fourni.
- CI/CD : déclencher automatiquement le pipeline à chaque détection d'un nouveau hash OpenData.
- Extension : le pipeline est paramétré par la zone géographique, l'effort pour ajouter une autre commune est marginal.

---


Projet 11 — OpenClassrooms — Mai 2026
