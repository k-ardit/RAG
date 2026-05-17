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
folderRagas = "ragasTest/"
fileRagas = "testRagas.xlsx"
""""""

dfQuestion = pd.read_excel(pathData + folderQuestion + fileQuestion)

questions_test = dfQuestion["Question"]

answers = dfQuestion["Reponse"]

ground_truths = dfQuestion["ReponseAttendue"] 

placeholder_contexts = []
for val in dfQuestion["ContextList"]:
    myTab = []
    myTab.append(val)
    placeholder_contexts.append(myTab)
# placeholder_contexts = dfQuestion["ContextList"]

# Création du dictionnaire pour le Dataset
evaluation_data = {
    "question": questions_test,
    "answer": answers,
    "contexts": placeholder_contexts,
    "ground_truth": ground_truths, # Inclusion de la vérité terrain
}
    
# Créer l'objet Dataset
evaluation_dataset = Dataset.from_dict(evaluation_data)
print("\n--- Aperçu du Dataset formaté pour Ragas ---")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

try:

    llm2 = ChatOpenAI(model="gpt-4o")
    openai_client = openai.OpenAI()
    embeddings2 = OpenAIEmbeddings(client=openai_client)

    print("LLM et Embeddings initialisés.")
    
    # 2. Définition des métriques à calculer
    metrics_to_evaluate = [
        faithfulness,       # Génération: fidèle au contexte ?
        #answer_relevancy,   # Génération: réponse pertinente à la question ?
        context_precision,  # Récupération: contexte précis (peu de bruit) ?
        context_recall,     # Récupération: infos clés récupérées (nécessite ground_truth) ?
    ]
    print(f"Métriques sélectionnées: {[m.name for m in metrics_to_evaluate]}")

    # 3. Lancement de l'évaluation Ragas
    print("\nLancement de l'évaluation Ragas (peut prendre du temps)...")
    results = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics_to_evaluate,
        llm=llm2, # LLM pour juger certaines métriques
        embeddings=embeddings2 # Embeddings pour juger d'autres métriques
    )
    print("\n--- Évaluation Ragas terminée ---")

    # Conversion du résultat en dataframe
    results_df = results.to_pandas()

    # Export des résultats sour format .xlsx
    results_df.to_excel(pathData + folderRagas + fileRagas)

    # 4. Affichage des résultats sous forme de DataFrame
    print("\n--- Résultats de l'évaluation (DataFrame) ---")
    
    # Paramétrage d'affichage
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 150) # Ajustez si nécessaire
    print(results_df)

    # 5. Calcul et affichage des scores moyens
    print("\n--- Scores Moyens (sur tout le dataset) ---")
    average_scores = results_df.mean(numeric_only=True)
    print(average_scores)
except Exception as e:
    print(f"\n❌ ERREUR lors de l'initialisation ou de l'évaluation Ragas : {e}")
    print("\nTraceback:")
    traceback.print_exc()

