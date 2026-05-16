import faiss
import pickle
import logging
import os
from typing import List, Dict, Tuple, Optional
import numpy as np
import pickle
import logging
from typing import List, Dict, Tuple, Optional
from mistralai.client import MistralClient
from mistralai.exceptions import MistralAPIException
import pandas as pd

# Récupération des données
#pathVector = "C:\\Users\\TWB\\Desktop\\openClassrooms\\Projet_11\\data\\Flow02\\vector_db\\"
#pathVector = "C:\\Users\\ardit\\Desktop\\Projet_11\\data\\Flow02\\vector_db\\"
pathVector="/data/Flow02/vector_db/"
#pathQuestion = "C:\\Users\\TWB\\Desktop\\openClassrooms\\Projet_11\\data\\Flow02\\QuestionTest\\"
#pathQuestion = "C:\\Users\\ardit\\Desktop\\Projet_11\\data\\Flow02\\QuestionTest\\"
pathQuestion="/data/Flow02/QuestionTest/"

"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
donneeNettoyee : fichier avec les données néttoyées"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
donneeNettoyee = "FichierFinal.xlsx"
folderIndex = "index/"
fileIndex = "faiss_index.idx"
folderChunks = "chunks/"
fileChunks = "chunks.xlsx"
folderQuestion = "questionsTest/"
fileQuestion = "QuestionTest.xlsx"
""""""

index: Optional[faiss.Index] = None
document_chunks: List[Dict[str, any]] = []
FAISS_INDEX_FILE = pathData + folderIndex + fileIndex
DOCUMENT_CHUNKS_FILE = pathData + folderChunks + fileChunks
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)

def _load_index_and_chunks():
    """Charge l'index Faiss et les chunks si les fichiers existent."""
    if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
        try:

            logging.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
            global index
            index = faiss.read_index(FAISS_INDEX_FILE)
            
            logging.info(f"Chargement des chunks depuis {DOCUMENT_CHUNKS_FILE}...")
            global document_chunks
            document_chunks = pd.read_excel(pathData + folderChunks + fileChunks, sheet_name="Sheet1").to_dict(orient='records')
            
            logging.info(f"Index ({index.ntotal} vecteurs) et {len(document_chunks)} chunks chargés.")
            
        except Exception as e:
            logging.error(f"Erreur lors du chargement de l'index/chunks: {e}")
            index = None
            document_chunks = []
    else:
        logging.warning("Fichiers d'index Faiss ou de chunks non trouvés. L'index est vide.")

def search(query_text: str, k: int = 200, min_score: float = None) -> List[Dict[str, any]]:
    """
    Recherche les k chunks les plus pertinents pour une requête.

    Args:
        query_text: Texte de la requête
        k: Nombre de résultats à retourner
        min_score: Score minimum (entre 0 et 1) pour inclure un résultat

    Returns:
        Liste des chunks pertinents avec leurs scores
    """    
    if index is None or not document_chunks:
        logging.warning("Recherche impossible: l'index Faiss n'est pas chargé ou est vide.")
        return []
    if not MISTRAL_API_KEY:
            logging.error("Recherche impossible: MISTRAL_API_KEY manquante pour générer l'embedding de la requête.")
            return []

    logging.info(f"Recherche des {k} chunks les plus pertinents pour: '{query_text}'")
    try:
        # 1. Générer l'embedding de la requête
        response = mistral_client.embeddings(
            model="mistral-embed",
            input=[query_text] # La requête doit être une liste
        )
        query_embedding = np.array([response.data[0].embedding]).astype('float32')

        # Normaliser l'embedding de la requête pour la similarité cosinus
        faiss.normalize_L2(query_embedding)

        # 2. Rechercher dans l'index Faiss
        # Pour IndexFlatIP: scores = produit scalaire (plus grand = meilleur)
        # indices: index des chunks correspondants dans self.document_chunks
        # Demander plus de résultats si un score minimum est spécifié
        search_k = k * 3 if min_score is not None else k
        scores, indices = index.search(query_embedding, search_k)
        # 3. Formater les résultats
        results = []
        if indices.size > 0: # Vérifier s'il y a des résultats
            for i, idx in enumerate(indices[0]):
                if 0 <= idx < len(document_chunks): # Vérifier la validité de l'index
                    chunk = document_chunks[idx]
                    # Convertir le score en similarité (0-1)
                    # Pour IndexFlatIP avec vecteurs normalisés, le score est déjà entre -1 et 1
                    # On le convertit en pourcentage (0-100%)
                    raw_score = float(scores[0][i])
                    similarity = raw_score * 100

                    # Filtrer les résultats en fonction du score minimum
                    # Le min_score est entre 0 et 1, mais similarity est en pourcentage (0-100)
                    min_score_percent = min_score * 100 if min_score is not None else 0
                    if min_score is not None and similarity < min_score_percent:
                        logging.debug(f"Document filtré (score {similarity:.2f}% < minimum {min_score_percent:.2f}%)")
                        continue

                    results.append({
                        "idx":idx,
                        "score": similarity, # Score de similarité en pourcentage
                        "raw_score": raw_score, # Score brut pour débogage
                        "id": chunk["id"],
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    })
                else:
                    logging.warning(f"Index Faiss {idx} hors limites (taille des chunks: {len(document_chunks)}).")

        # Trier par score (similarité la plus élevée en premier)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limiter au nombre demandé (k) si nécessaire
        if len(results) > k:
            results = results[:k]

        if min_score is not None:
            min_score_percent = min_score * 100
            logging.info(f"{len(results)} chunks pertinents trouvés (score minimum: {min_score_percent:.2f}%).")
        else:
            logging.info(f"{len(results)} chunks pertinents trouvés.")

        return results

    except MistralAPIException as e:
        logging.error(f"Erreur API Mistral lors de la génération de l'embedding de la requête: {e}")
        logging.error(f"  Détails: Status Code={e.status_code}, Message={e.message}")
        return []
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la recherche: {e}")
        return []

def getScoreAndKForEachChunk(Question: str, idToFind: [], k: int = 200, min_score: float = None):   
    Reponse = search(Question, k, min_score)
    # print(Reponse)
    RIdList = []
    identifiantK = []
    identifiantScore = []
    for val in idToFind:
        #print(val)
        j = 0
        myKToAdd = "none"
        myScoreToAdd = "none"
        for doc in Reponse:
            #print(str(doc["id"]) + " - " + val)
            j = j+1
            if val == str(doc["id"]):
                #print(doc["id"])
                myKToAdd = str(j)
                myScoreToAdd = doc["score"]
                
                
        identifiantK.append(str(val) + " : " + myKToAdd)
        identifiantScore.append(str(val) + " : " + str(myScoreToAdd))

    dfToReturn = pd.DataFrame(columns=['Question','identifiant/k', 'identifiant/score'])
    dfToReturn.loc[len(dfToReturn)] = [Question , " - ".join(identifiantK), " - ".join(identifiantScore)]
    return dfToReturn

_load_index_and_chunks()

dfQuestions = pd.read_excel(pathData + folderQuestion + fileQuestion)

dfQuestionsFinal = dfQuestions.copy().astype(str)

for idxe, row in dfQuestions.iterrows():
    result = getScoreAndKForEachChunk(row["Question"], str(row["IdentifiantsATrouver"]).split(" - "), 210, 0.7)
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "identifiant/k"] = result.loc[result["Question"] == row["Question"], "identifiant/k"][0]
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "identifiant/score"] = result.loc[result["Question"] == row["Question"], "identifiant/score"][0]
    
dfQuestionsFinal.to_excel(pathData + folderQuestion + fileQuestion, index=False)

dfQuestionsFinal.head()