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


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


index: Optional[faiss.Index] = None
document_chunks: List[Dict[str, any]] = []
FAISS_INDEX_FILE = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_INDEX"]
DOCUMENT_CHUNKS_FILE = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_XLSX"]
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
logging.info(f"Paramètres chargés - index Faiss : {FAISS_INDEX_FILE}, chunks : {DOCUMENT_CHUNKS_FILE}")

mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
logging.info("Client Mistral instancié")


def _load_index_and_chunks():
    """Charge l'index Faiss et les chunks si les fichiers existent."""
    if os.path.exists(FAISS_INDEX_FILE) and os.path.exists(DOCUMENT_CHUNKS_FILE):
        try:
            logging.info(f"Chargement de l'index Faiss depuis {FAISS_INDEX_FILE}...")
            global index
            index = faiss.read_index(FAISS_INDEX_FILE)

            logging.info(f"Chargement des chunks depuis {DOCUMENT_CHUNKS_FILE}...")
            global document_chunks
            document_chunks = pd.read_excel(DOCUMENT_CHUNKS_FILE, sheet_name="Sheet1").to_dict(orient='records')

            logging.info(f"Index ({index.ntotal} vecteurs) et {len(document_chunks)} chunks chargés avec succès")

        except Exception as e:
            logging.error(f"Erreur lors du chargement de l'index/chunks : {e}")
            index = None
            document_chunks = []
    else:
        logging.warning(f"Fichiers d'index Faiss ou de chunks non trouvés - index Faiss : {FAISS_INDEX_FILE}, chunks : {DOCUMENT_CHUNKS_FILE}")


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
        logging.warning("Recherche impossible : l'index Faiss n'est pas chargé ou est vide")
        return []
    if not MISTRAL_API_KEY:
        logging.error("Recherche impossible : MISTRAL_API_KEY manquante pour générer l'embedding de la requête")
        return []

    logging.info(f"Recherche des {k} chunks les plus pertinents pour : '{query_text}' (min_score : {min_score})")
    try:
        # 1. Générer l'embedding de la requête
        logging.info("Génération de l'embedding de la requête via Mistral")
        response = mistral_client.embeddings(
            model="mistral-embed",
            input=[query_text]
        )
        query_embedding = np.array([response.data[0].embedding]).astype('float32')
        logging.info("Embedding de la requête généré avec succès")

        # Normaliser l'embedding de la requête pour la similarité cosinus
        faiss.normalize_L2(query_embedding)

        # 2. Rechercher dans l'index Faiss
        search_k = k * 3 if min_score is not None else k
        logging.info(f"Recherche dans l'index Faiss - search_k : {search_k}")
        scores, indices = index.search(query_embedding, search_k)

        # 3. Formater les résultats
        results = []
        if indices.size > 0:
            for i, idx in enumerate(indices[0]):
                if 0 <= idx < len(document_chunks):
                    chunk = document_chunks[idx]
                    raw_score = float(scores[0][i])
                    similarity = raw_score * 100

                    min_score_percent = min_score * 100 if min_score is not None else 0
                    if min_score is not None and similarity < min_score_percent:
                        logging.debug(f"Document filtré (score {similarity:.2f}% < minimum {min_score_percent:.2f}%)")
                        continue

                    results.append({
                        "idx": idx,
                        "score": similarity,
                        "raw_score": raw_score,
                        "id": chunk["id"],
                        "text": chunk["text"],
                        "metadata": chunk["metadata"]
                    })
                else:
                    logging.warning(f"Index Faiss {idx} hors limites (taille des chunks : {len(document_chunks)})")

        # Trier par score
        results.sort(key=lambda x: x["score"], reverse=True)

        # Limiter au nombre demandé
        if len(results) > k:
            results = results[:k]

        if min_score is not None:
            min_score_percent = min_score * 100
            logging.info(f"{len(results)} chunks pertinents trouvés (score minimum : {min_score_percent:.2f}%)")
        else:
            logging.info(f"{len(results)} chunks pertinents trouvés")

        return results

    except MistralAPIException as e:
        logging.error(f"Erreur API Mistral lors de la génération de l'embedding de la requête : {e}")
        logging.error(f"Détails : Status Code={e.status_code}, Message={e.message}")
        return []
    except Exception as e:
        logging.error(f"Erreur inattendue lors de la recherche : {e}")
        return []


def getScoreAndKForEachChunk(Question: str, idToFind: [], k: int = 200, min_score: float = None):
    logging.info(f"Calcul du score et du rang pour la question : '{Question}' - identifiants recherchés : {idToFind}")
    Reponse = search(Question, k, min_score)

    identifiantK = []
    identifiantScore = []
    for val in idToFind:
        j = 0
        myKToAdd = "none"
        myScoreToAdd = "none"
        for doc in Reponse:
            j = j + 1
            if val == str(doc["id"]):
                myKToAdd = str(j)
                myScoreToAdd = doc["score"]

        identifiantK.append(str(val) + " : " + myKToAdd)
        identifiantScore.append(str(val) + " : " + str(myScoreToAdd))
        logging.info(f"Identifiant '{val}' - rang : {myKToAdd}, score : {myScoreToAdd}")

    dfToReturn = pd.DataFrame(columns=['Question', 'identifiant/k', 'identifiant/score'])
    dfToReturn.loc[len(dfToReturn)] = [Question, " - ".join(identifiantK), " - ".join(identifiantScore)]
    return dfToReturn


_load_index_and_chunks()


filePathQuestions = os.environ["PATHDATA"] + os.environ["FILE_QUESTION"]
logging.info(f"Lecture du fichier de questions : {filePathQuestions}")
dfQuestions = pd.read_excel(filePathQuestions)
logging.info(f"Questions chargées - nombre de questions : {len(dfQuestions)}")

dfQuestionsFinal = dfQuestions.copy().astype(str)

for idxe, row in dfQuestions.iterrows():
    logging.info(f"Traitement de la question {idxe + 1}/{len(dfQuestions)} : '{row['Question']}'")
    result = getScoreAndKForEachChunk(row["Question"], str(row["IdentifiantsATrouver"]).split(" - "), 210, 0.7)
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "identifiant/k"] = result.loc[result["Question"] == row["Question"], "identifiant/k"][0]
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "identifiant/score"] = result.loc[result["Question"] == row["Question"], "identifiant/score"][0]

filePathOutput = os.environ["PATHDATA"] + os.environ["FOLDER_TESTVECTORISATION"] + os.environ["FILE_QUESTION"]
logging.info(f"Écriture des résultats : {filePathOutput}")
dfQuestionsFinal.to_excel(filePathOutput, index=False)
logging.info(f"Résultats sauvegardés avec succès - nombre de questions traitées : {len(dfQuestionsFinal)}")

dfQuestionsFinal.head()