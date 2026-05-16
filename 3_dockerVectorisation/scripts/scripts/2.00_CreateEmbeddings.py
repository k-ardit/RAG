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
from langchain_core.documents import Document # Utilisé pour le format attendu par le splitter
import pandas as pd
import json
import os.path


"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
donneeNettoyee : fichier avec les données néttoyées"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
folderChunks = "chunks/"
folderVectors = "vectors/"
donneeNettoyee = "FichierFinal.xlsx"
fileChunk = "chunks.xlsx"
fileVectors = "vectors.xlsx"
""""""


"""Récupération des données
data : Récupération des données néttoyées dans un format dataframe"""
data = pd.read_excel(pathData + folderOpenData + donneeNettoyee, sheet_name="Sheet1").astype(str)
dataChunk = pd.read_excel(pathData + folderChunks + fileChunk, sheet_name="Sheet1").astype(str)
if os.path.exists(pathData + folderVectors + fileVectors):
    dfVectors = pd.read_excel(pathData + folderVectors + fileVectors, sheet_name="Sheet1").astype(str)
else:
     dfVectors = pd.DataFrame(columns=["hash", "vectors"]) # Création d'un dataframe vide avec uniquement la colonnne utilisée par la suite
""""""


# On garde les vecteurs déja existants
dfVectors = dfVectors[dfVectors['hash'].isin(dataChunk['rowHash'])]
print("nombre de vecteurs déjà existants : " + str(dfVectors.shape[0]))


# On récupère les chunk à vectoriser
dfChunksToEmbed = dataChunk[~dataChunk['rowHash'].isin(dfVectors['hash'])]
print("nombre de chunks à vectoriser : " + str(dfChunksToEmbed.shape[0]))


# On vectorise les chunks
if dfChunksToEmbed.shape[0] > 0:
    mistral_client = MistralClient(api_key=os.environ["MISTRAL_API_KEY"])
    model_embedding = os.environ["MODEL_EMBEDDING"]
    EMBEDDING_BATCH_SIZE = int(os.environ["EMBEDDING_BATCH_SIZE"]) # Taille des lots pour l'API d'embedding
    total_batches = (dfChunksToEmbed.shape[0] + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE
    #all_embeddings = []
    all_hash_embeddings = []
    print(f"Génération des embeddings pour {dfChunksToEmbed.shape[0]} chunks (modèle: {model_embedding})...")
    print("batch size = " + str(EMBEDDING_BATCH_SIZE))
    print("\n")
    j = 0
    for i in range(0, dfChunksToEmbed.shape[0], EMBEDDING_BATCH_SIZE):
        batch_num = (i // EMBEDDING_BATCH_SIZE) + 1
        batch_chunks = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]
        # print(dfChunksToEmbed["text"].tolist())
    
        texts_to_embed = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]["text"].tolist() # [chunk["text"] for chunk in batch_chunks]
        hashToAdd = dfChunksToEmbed[i:i + EMBEDDING_BATCH_SIZE]["rowHash"]
        print("\n")
        print(f"Traitement du lot {batch_num}/{total_batches} ({len(texts_to_embed)} chunks)")
    
        try:
            response = mistral_client.embeddings(
                model=model_embedding,
                input=texts_to_embed
            )
            batch_embeddings = [data.embedding for data in response.data]
            #all_embeddings.extend(batch_embeddings)
            for hash_val, vector in zip(hashToAdd, batch_embeddings):
                all_hash_embeddings.append({
                    'hash': hash_val,
                    'vectors': vector
                })
                j = j+1
                print("ligne " + str(j) + " vectorisé : " + hash_val)
        except MistralAPIException as e:
            logging.error(f"Erreur API Mistral lors de la génération d'embeddings (lot {batch_num}): {e}")
            logging.error(f"  Détails: Status Code='', Message={e.message}")
        except Exception as e:
            logging.error(f"Erreur inattendue lors de la génération d'embeddings (lot {batch_num}): {e}")

    if not all_hash_embeddings:
        print("Aucun embedding généré.")

    dfVectors = pd.concat([dfVectors, pd.DataFrame(all_hash_embeddings)], ignore_index=True)
    dfVectors.to_excel(pathData + folderVectors + fileVectors, index=False)

