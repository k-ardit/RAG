# Conteneur 3 — `vectorisation`

Préparation des données, chunking, calcul des embeddings et construction de l'index FAISS.

## Rôle dans le pipeline

```
export → testexport → [ vectorisation ] → testvectorisation → … → chatbot
```

Cœur du RAG : transforme les évènements en base vectorielle interrogeable.

## Entrées et sorties

| Type   | Fichier                                       | Description                              |
|--------|-----------------------------------------------|------------------------------------------|
| Entrée | `/data/Flow02/OpenData/FichierFinal.xlsx`     | Données nettoyées du conteneur 1         |
| Sortie | `/data/Flow02/inputs/DataForChunk.xlsx`       | Données préparées pour le chunking (1 515 lignes) |
| Sortie | `/data/Flow02/vector_db/faiss_index.idx`      | Index FAISS (1 514 vecteurs × 1 024 dims)|
| Sortie | `/data/Flow02/vector_db/document_chunks.pkl`  | Chunks alignés avec l'index FAISS        |

## Étapes exécutées

### 1. `1.00_PreparationDonnees.py`
Enrichit `FichierFinal.xlsx` :

- renommage `longdescription_fr` → `description`, `conditions_fr` → `conditions` ;
- fusion `location_name + location_address` → `addresse` ;
- conversion des dates au format lisible ;
- calcul de la `dureeEvenement` ;
- duplication des lignes pour les évènements multi-dates (un identifiant par occurrence) ;
- injection de `"none"` dans toutes les cellules vides ;
- export dans `DataForChunk.xlsx` avec une colonne `Split2` servant de séparateur de chunks.

### 2. `2.00_Indexer.py`

Chunking, embeddings et indexation FAISS :

```python
RecursiveCharacterTextSplitter(
    separators=[",\"Split2\":null},"],
    chunk_size=1500,
    chunk_overlap=150,
    length_function=len,
    add_start_index=True,
)
```

- Embeddings : `mistral-embed` (dim 1 024), batch de 32.
- Normalisation L2 puis indexation dans un FAISS `IndexFlatIP` (similarité cosinus).
- Sérialisation : `faiss_index.idx` (index) + `document_chunks.pkl` (chunks avec `id`, `text`, `metadata`).

## Paramètres clés

Définis dans `scripts/scripts/utils/config.py` :

| Paramètre              | Valeur            |
|------------------------|-------------------|
| `EMBEDDING_MODEL`      | `mistral-embed`   |
| `CHUNK_SIZE`           | 1 500 caractères  |
| `CHUNK_OVERLAP`        | 150 caractères    |
| `EMBEDDING_BATCH_SIZE` | 32                |

## Construction et lancement

```bash
docker compose up --build vectorisation
```

## Stack

- **Image de base** : `ubuntu:jammy`
- **Dépendances clés** : `mistralai==0.4.2`, `langchain==0.3.23`, `faiss-cpu==1.10.0`, `pandas`, `openpyxl`, `python-dotenv`

## Configuration

```bash
MISTRAL_API_KEY=sk-...
```
