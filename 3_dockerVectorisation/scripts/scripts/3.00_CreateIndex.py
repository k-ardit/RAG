# utils/vector_store.py
import os
import faiss
import numpy as np
import pandas as pd
import ast
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


filePathVectors = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_VECTORS"]
logging.info(f"Lecture du fichier de vecteurs : {filePathVectors}")
doneeVectorisee = pd.read_excel(filePathVectors, sheet_name="Sheet1")
logging.info(f"Vecteurs chargés - nombre de lignes : {len(doneeVectorisee)}")

logging.info("Tri des vecteurs par hash")
doneeVectorisee.sort_values('hash')

logging.info("Conversion des vecteurs en numpy arrays float32")
all_embeddings = []
for idxc, rowc in doneeVectorisee.iterrows():
    all_embeddings.append(np.array(ast.literal_eval(rowc["vectors"]), dtype='float32'))

embeddings = np.array(all_embeddings).astype('float32')
logging.info(f"Conversion terminée - shape des embeddings : {embeddings.shape}")


# Créer l'index Faiss optimisé pour la similarité cosinus
dimension = embeddings.shape[1]
logging.info(f"Création de l'index Faiss - similarité cosinus, dimension : {dimension}")

logging.info("Normalisation des embeddings (L2) pour la similarité cosinus")
faiss.normalize_L2(embeddings)

index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
logging.info(f"Index Faiss créé avec succès - nombre de vecteurs indexés : {index.ntotal}")


try:
    filePathIndex = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_INDEX"]
    logging.info(f"Sauvegarde de l'index Faiss : {filePathIndex}")
    faiss.write_index(index, filePathIndex)
    logging.info("Index Faiss sauvegardé avec succès")
except Exception as e:
    logging.error(f"Erreur lors de la sauvegarde de l'index Faiss : {e}")