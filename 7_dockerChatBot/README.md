# Conteneur 7 — `chatbot`

Application Streamlit exposant un chatbot interactif. Dernier maillon du pipeline : tout le reste alimente cette interface.

## Rôle dans le pipeline

```
… → testragas → [ chatbot ]
```

Contrairement aux six conteneurs précédents (qui s'exécutent puis se terminent), ce conteneur reste en vie et expose un serveur web.

## Accès

Une fois le conteneur démarré : <http://localhost:8501>

Mapping de ports dans `docker-compose.yml` :

ports:
  - 8501:8501

## Entrées et sorties

| Type     | Fichier                                       | Description                              |
|----------|-----------------------------------------------|------------------------------------------|
| Entrée   | `/data/03_vectorisation/faiss_index.idx`      | Index FAISS                              |
| Entrée   | `/data/03_vectorisation/chunks.pkl`           | Chunks alignés sur l'index               |
| Sortie   | `/etc/database/interactions.db`               | Journal SQLite des interactions          |

## Fonctionnalités

- Sélection du modèle : Mistral Small (rapide) ou Mistral Large (précis).
- Réglage de la récupération : nombre de documents (1 → 250) et score minimum (slider %).
- Classifieur de requêtes : route automatiquement la question entre mode RAG et mode direct.
- Affichage des sources : pour chaque réponse RAG, expand "Sources utilisées" avec score, catégorie et extrait.
- Historique persistant : la conversation se conserve d'une question à l'autre.
- Bouton "Nouvelle conversation" : reset de l'historique.

## Trois modes de réponse

Le classifieur (`utils/query_classifier.py`) décide quel prompt système utiliser.

| Mode             | Condition                                          | Comportement                                  |
|------------------|----------------------------------------------------|-----------------------------------------------|
| RAG              | Question liée aux évènements + chunks pertinents   | Réponse ancrée sur le contexte récupéré       |
| RAG sans résultat| Question liée aux évènements + aucun chunk         | Indique poliment l'absence d'information      |
| Direct           | Question hors périmètre                            | Réponse sur les connaissances générales       |

## Construction et lancement

docker compose up --build chatbot


Le pipeline complet (avec dépendances) :

docker compose up --build

## Stack

- Image de base : `ubuntu:jammy`
- Dépendances clés : `streamlit==1.44.1`, `mistralai==0.4.2`, `faiss-cpu==1.10.0`, `SQLAlchemy==2.0.40`, `plotly==6.0.1`, `streamlit-feedback==0.1.4`

## Configuration

MISTRAL_API_KEY


Le code applicatif détaillé (modules `utils/`, `MistralChat.py`, `indexer.py`) est documenté dans [`scripts/scripts/README.md`](scripts/scripts/README.md).
dans notre cas le script indexer.py (création des index) n'est pas utilisé, le travail est fait en amont dans les conteneurs précédents pour être adapté à nos données.