# utils/vector_store.py
import os
import faiss
import numpy as np
import pandas as pd
import ast


"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
donneeNettoyee : fichier avec les données néttoyées"""
pathData = os.environ["PATHDATA"]
folderVectors = "vectors/"
folderIndex = "index/"
fileVectors = "vectors.xlsx"
fileIndex = "faiss_index.idx"
""""""


doneeVectorisee = pd.read_excel(pathData + folderVectors + fileVectors, sheet_name="Sheet1")
# On tri les lignes par hash (pour avoir le même positionnement que les chunks de début)
doneeVectorisee.sort_values('hash')

all_embeddings = []

for idxc, rowc in doneeVectorisee.iterrows():
    all_embeddings.append(np.array(ast.literal_eval(rowc["vectors"]), dtype='float32'))

embeddings = np.array(all_embeddings).astype('float32')

# 3. Créer l'index Faiss optimisé pour la similarité cosinus
dimension = embeddings.shape[1]
print(f"Création de l'index Faiss optimisé pour la similarité cosinus avec dimension {dimension}...")

# Normaliser les embeddings pour la similarité cosinus
faiss.normalize_L2(embeddings)

# Créer un index pour la similarité cosinus (IndexFlatIP = produit scalaire)
index = faiss.IndexFlatIP(dimension)
index.add(embeddings)
print(f"Index Faiss créé avec {index.ntotal} vecteurs.")

try:
    print(f"Sauvegarde de l'index Faiss ...")
    faiss.write_index(index, pathData + folderIndex + fileIndex)
    # print(f"Sauvegarde des chunks dans {DOCUMENT_CHUNKS_FILE}...")
    # with open(DOCUMENT_CHUNKS_FILE, 'wb') as f:
    #     pickle.dump(self.document_chunks, f)
    print("Index sauvegardés avec succès.")
except Exception as e:
    print(f"Erreur lors de la sauvegarde de l'index/chunks: {e}")
