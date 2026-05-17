# app.py
import streamlit as st
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import logging
import datetime
from streamlit_feedback import streamlit_feedback # Importez le composant
from typing import List, Dict, Tuple, Optional
from mistralai.exceptions import MistralAPIException
import numpy as np
import pandas as pd
import faiss
import pickle
import logging
import os
from typing import List, Dict, Tuple, Optional


index: Optional[faiss.Index] = None
document_chunks: List[Dict[str, any]] = []
FAISS_INDEX_FILE = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_INDEX"]
DOCUMENT_CHUNKS_FILE = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_XLSX"]
k = 210
min_score = 0.77
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
mistral_client = MistralClient(api_key=MISTRAL_API_KEY)
model_embedding = os.environ["MODEL_EMBEDDING"]

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
            model=model_embedding,
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
                        "id": chunk["id"],
                        "score": similarity, # Score de similarité en pourcentage
                        "raw_score": raw_score, # Score brut pour débogage
                        "text": chunk["text"],
                        "metadata": chunk["metadata"] # Contient source, category, chunk_id_in_doc, start_index etc.
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

def getAnswer(Question: str):
    
    retrieved_docs = search(Question, k, min_score)
        
    # context_str = "\n\n---\n\n".join([
    #     f"Source: {doc['metadata'].get('source', 'Spécifique OpenData')} (Score: {doc['score']:.4f})\nContenu: {doc['text']}"
    #     for doc in retrieved_docs
    # ])

    system_prompt = f"""Vous êtes un assistant virtuel pour des évènements situés à Nice.
    Répondez à la question de l'utilisateur en vous basant UNIQUEMENT sur le contexte fourni ci-dessous. Soyez concis et précis.
    Renvoyez premièrement la réponse.
    Ensuite, renvoyez uniquement la liste des identifiants qui permettent de répondre à la question séparé par une virgule, s'il n'y en a pas, renvoyez none.
        
    Contexte fourni:
    ---
    {retrieved_docs}
    ---
    """
    
    user_message = ChatMessage(role="user", content=Question)
    system_message = ChatMessage(role="system", content=system_prompt)
    messages_for_api = [system_message, user_message]
    
    # 3. Appel à l'API Mistral Chat
    logging.info(f"Appel de l'API Mistral Chat avec le modèle mistral-large-latest...")
    chat_response = mistral_client.chat(
     model="mistral-large-latest",
     messages=messages_for_api
    )
    response_text = chat_response.choices[0].message.content
    logging.info(response_text)

    # 4. Retourner et afficher la réponse
    print(response_text)
    print("\n")
    return response_text

_load_index_and_chunks()

dfQuestions = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_TESTVECTORISATION"] + os.environ["FILE_QUESTION"])

dfQuestionsFinal = dfQuestions.copy()

i = 0
for idxe, row in dfQuestions.iterrows():
    result = getAnswer(row["Question"])
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "Reponse"] = "\n\n".join(result.split("\n\n")[:-1])
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "IdContext"] = result.split("\n\n")[-1]

    currentContext = []
    idContexts = result.split("\n\n")[-1].split(",")
    for val in idContexts: 
        if val == 0:
            break
        for val2 in document_chunks:
            if str(val2["id"]) == val:
                currentContext.append(val2)
    dfQuestionsFinal.loc[dfQuestionsFinal["Question"] == row["Question"], "ContextList"] = str(currentContext)

    i = i+1
    print("Question " + str(i) + " effectué")

dfQuestionsFinal.to_excel(os.environ["PATHDATA"] + os.environ["FOLDER_REPONSE"] + os.environ["FILE_QUESTION"], index=False)

dfQuestionsFinal.head()