"""
Ce script permet d'effectuer un test avec la librairie Ragas.
Ce test nous renvoie le résultat des métriques qu'on souhaite.
Il nous faut 
    - la liste des métriques (dans notre cas : faithfulness, context_precision, context_recall)
    - la liste des questions
    - la liste des réponses voulue
    - la liste des réponses obtenues via Mistral
    - la liste des chunks (contextes) utilisé par Mistral
"""


import os
import traceback
import pandas as pd
from datasets import Dataset
from langchain_openai import ChatOpenAI
import openai
import pickle
from ragas import evaluate
from ragas.embeddings import OpenAIEmbeddings
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


filePathQuestions = os.environ["PATHDATA"] + os.environ["FOLDER_REPONSE"] + os.environ["FILE_QUESTION"]
logging.info(f"Lecture du fichier de questions/réponses : {filePathQuestions}")
dfQuestion = pd.read_excel(filePathQuestions)
logging.info(f"Données chargées - nombre de questions : {len(dfQuestion)}")

questions_test = dfQuestion["Question"]
answers = dfQuestion["Reponse"]
ground_truths = dfQuestion["ReponseAttendue"]
logging.info("Colonnes questions, réponses et vérités terrain récupérées")

logging.info("Construction des contextes pour Ragas")
placeholder_contexts = []
for val in dfQuestion["ContextList"]:
    myTab = []
    myTab.append(val)
    placeholder_contexts.append(myTab)
logging.info(f"Contextes construits - nombre de contextes : {len(placeholder_contexts)}")

evaluation_data = {
    "question": questions_test,
    "answer": answers,
    "contexts": placeholder_contexts,
    "ground_truth": ground_truths,
}

logging.info("Création du dataset Ragas")
evaluation_dataset = Dataset.from_dict(evaluation_data)
logging.info(f"Dataset Ragas créé - aperçu : {evaluation_dataset}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logging.warning("OPENAI_API_KEY non trouvée dans les variables d'environnement")
else:
    logging.info("OPENAI_API_KEY chargée avec succès")

try:
    logging.info("Initialisation du LLM (gpt-4o) et des embeddings OpenAI")
    llm2 = ChatOpenAI(model="gpt-4o")
    openai_client = openai.OpenAI()
    embeddings2 = OpenAIEmbeddings(client=openai_client)
    logging.info("LLM et embeddings initialisés avec succès")

    # 2. Définition des métriques à calculer
    metrics_to_evaluate = [
        faithfulness,
        #answer_relevancy,
        context_precision,
        context_recall,
    ]
    logging.info(f"Métriques sélectionnées : {[m.name for m in metrics_to_evaluate]}")

    # 3. Lancement de l'évaluation Ragas
    logging.info("Lancement de l'évaluation Ragas (peut prendre du temps)...")
    results = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics_to_evaluate,
        llm=llm2,
        embeddings=embeddings2
    )
    logging.info("Évaluation Ragas terminée avec succès")

    # Conversion du résultat en dataframe
    results_df = results.to_pandas()
    logging.info(f"Résultats convertis en DataFrame - nombre de lignes : {len(results_df)}")

    # Export des résultats sous format .xlsx
    filePathRagas = os.environ["PATHDATA"] + os.environ["FOLDER_RAGASTEST"] + os.environ["FILE_RAGASTEST"]
    logging.info(f"Export des résultats Ragas : {filePathRagas}")
    results_df.to_excel(filePathRagas)
    logging.info("Fichier de résultats Ragas sauvegardé avec succès")

    # 4. Affichage des résultats sous forme de DataFrame
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', 4)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 150)
    #logging.info(f"Résultats de l'évaluation :\n{results_df.to_string()}")

    # 5. Calcul et affichage des scores moyens
    average_scores = results_df.mean(numeric_only=True)
    logging.info(f"Scores moyens sur l'ensemble du dataset :\n{average_scores.to_string()}")

except Exception as e:
    logging.error(f"Erreur lors de l'initialisation ou de l'évaluation Ragas : {e}")
    logging.error(f"Traceback :\n{traceback.format_exc()}")