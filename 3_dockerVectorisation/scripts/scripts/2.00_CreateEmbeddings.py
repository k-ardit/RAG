"""
Ce script permet de vectoriser les chunks crée à l'étape précédente,les chunks déjà vectorisé sont récupéré pour éviter 
une vectorisation innutile via Mistral.
Un tri par hash est ensuite effectué pour garder une cohérence entre tout les fichiers (chunks.xlsx, chunks.pkl, vectors.xlsx, faiss_index.idx).
Au final, un fichier vectors.xlsx est crée.
"""


# utils/vector_store.py
import hashlib
import os
import pickle
import faiss
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from mistralai.client import MistralClient
from mistralai.exceptions import MistralAPIException
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import pandas as pd
import json
import os.path


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Récupération des données
data : Récupération des données dans un format dataframe"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
filePathChunks = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_XLSX"]
filePathVectors = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_VECTORS"]

logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
data = pd.read_excel(filePathNettoye, sheet_name="Sheet1").astype(str)
logging.info(f"Données nettoyées chargées - nombre de lignes : {len(data)}")

logging.info(f"Lecture du fichier de chunks : {filePathChunks}")
dataChunk = pd.read_excel(filePathChunks, sheet_name="Sheet1").astype(str)
logging.info(f"Chunks chargés - nombre de lignes : {len(dataChunk)}")

if os.path.exists(filePathVectors):
    logging.info(f"Fichier de vecteurs existant, chargement : {filePathVectors}")
    dfVectors = pd.read_excel(filePathVectors, sheet_name="Sheet1").astype(str)
    logging.info(f"Vecteurs chargés - nombre de lignes : {len(dfVectors)}")
else:
    logging.warning(f"Fichier de vecteurs inexistant, création d'un dataframe vide : {filePathVectors}")
    dfVectors = pd.DataFrame(columns=["hash", "vectors"])
""""""


# On garde les vecteurs déjà existants
dfVectors = dfVectors[dfVectors['hash'].isin(dataChunk['rowHash'])]
logging.info(f"Nombre de vecteurs déjà existants : {dfVectors.shape[0]}")


# On récupère les chunks à vectoriser
dfChunksToEmbed = dataChunk[~dataChunk['rowHash'].isin(dfVectors['hash'])]
logging.info(f"Nombre de chunks à vectoriser : {dfChunksToEmbed.shape[0]}")


# On vectorise les chunks
if dfChunksToEmbed.shape[0] > 0:
    mistral_client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
    model_embedding = os.environ["MODEL_EMBEDDING"]
    EMBEDDING_BATCH_SIZE = int(os.environ["EMBEDDING_BATCH_SIZE"])
    total_batches = (dfChunksToEmbed.shape[0] + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

    all_hash_embeddings = []
    logging.info(f"Génération des embeddings pour {dfChunksToEmbed.shape[0]} chunks - modèle : {model_embedding}, batch size : {EMBEDDING_BATCH_SIZE}, nombre de lots : {total_batches}")

    j = 0
    for i in range(0, dfChunksToEmbed.shape[0], EMBEDDING_BATCH_SIZE):
        batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
        batch_chunks = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]

        texts_to_embed = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]["text"].tolist()
        hashToAdd = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]["rowHash"]
        logging.info(f"Traitement du lot {batch_num}/{total_batches} ({len(texts_to_embed)} chunks)")

        try:
            response = mistral_client.embeddings(
                model=model_embedding,
                input=texts_to_embed
            )
            batch_embeddings = [data.embedding for data in response.data]
            for hash_val, vector in zip(hashToAdd, batch_embeddings):
                all_hash_embeddings.append({
                    'hash': hash_val,
                    'vectors': vector
                })
                j = j + 1
                logging.info(f"Ligne {j}/{dfChunksToEmbed.shape[0]} vectorisée - hash : {hash_val}")

        except MistralAPIException as e:
            logging.error(f"Erreur API Mistral lors de la génération d'embeddings (lot {batch_num}/{total_batches}) : {e}")
            logging.error(f"Détails : Message={e.message}")
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la génération d'embeddings (lot {batch_num}/{total_batches}) : {e}")

    if not all_hash_embeddings:
        logging.warning("Aucun embedding généré")
    else:
        logging.info(f"Embeddings générés avec succès - nombre total : {len(all_hash_embeddings)}")

    dfVectors = pd.concat([dfVectors, pd.DataFrame(all_hash_embeddings)], ignore_index=True)
    logging.info(f"Nouveaux vecteurs ajoutés - nombre total de vecteurs : {len(dfVectors)}")
else:
    logging.info("Aucun chunk à vectoriser, tous les vecteurs sont déjà à jour")


logging.info("Tri des vecteurs par hash")
dfVectors = dfVectors.sort_values('hash')

logging.info(f"Écriture du fichier de vecteurs : {filePathVectors}")
dfVectors.to_excel(filePathVectors, index=False)
logging.info(f"Fichier de vecteurs sauvegardé avec succès - nombre de lignes : {len(dfVectors)}")