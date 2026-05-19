"""
Ce script permet de créer les chunks qui seront utilisés pour la vectorisation dans le script suivant.
dans notre cas, il y'a un chunk par ligne Excel car il n'y a pas de liens sémantiques entre les lignes Excel (pas d'overload).
Une selection et une modification des données est faite pour les besoins du RAG.
Au final, deux fichiers sont crées, un fichier .xlsx pour le test du RAG et un fichier .pkl pour une utilisation
avec le chatbot du conteneur 7.
Les chunks sont trié par hash pour garder une cohérence entre tout les fichiers (chunks.xlsx, chunks.pkl, vectors.xlsx, faiss_index.idx)
"""


import pandas as pd
import json
from datetime import datetime
import os
import hashlib
import pickle
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Récupération des données
data : Récupération des données néttoyées dans un format dataframe"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
data = pd.read_excel(filePathNettoye, sheet_name="Sheet1")
logging.info(f"Données nettoyées chargées - nombre de lignes : {len(data)}")
""""""


def getBegin(x):
    """Récupération des dates de début des évènements sous un format plus lisible
    Args:
        x (string): exemple de format de la chaine d'entrée : [{"begin": "2025-04-28T08:30:00+02:00", "end": "2025-04-28T18:00:00+02:00"}, {"begin": "2025-04-29T08:30:00+02:00", "end": "2025-04-29T21:30:00+02:00"}]
    Returns:
        string: format de retour : 28-April-2025 08:30:00, 29-April-2025 08:30:00
    """
    json_str = json.loads(x)
    finalStr = []
    for val in json_str:
        finalStr.append(datetime.strptime(val["begin"].replace("+01:00", "").replace("+02:00", "").replace("T", " "), '%Y-%m-%d %H:%M:%S').strftime("%d-%B-%Y %H:%M:%S"))
    return ', '.join(finalStr)


def getDuree(x):
    """Récupération de la durée d'un évènement
    Args:
        x (string): exemple de format de la chaine d'entrée : [{"begin": "2025-04-28T08:30:00+02:00", "end": "2025-04-28T18:00:00+02:00"}, {"begin": "2025-04-29T08:30:00+02:00", "end": "2025-04-29T21:30:00+02:00"}]
    Returns:
        string: format de retour : 0 days 09:30:00
    """
    end = datetime.fromisoformat(json.loads(x)[0]["end"])
    begin = datetime.fromisoformat(json.loads(x)[0]["begin"])
    return end - begin


def duplicateAndRemoveEvent(dfVar: pd.DataFrame):
    """Duplication des lignes qui ont plusieurs évènements (plusieurs hotaires de départ, colonne "datesEvenement"), avec modification de l'uid
        Args:
            dfVar (DataFrame): 
    Returns:
        DataFrame : Avec certaines lignes dupliquées puis supprimées
    """
    dfToReturn = pd.DataFrame(columns=dfVar.columns)
    for idx, row in dfVar.iterrows():
        if len(row["datesEvenement"].split(", ")) > 1:
            i = 0
            for date in row["datesEvenement"].split(", "):
                i = i + 1
                dfToReturn.loc[len(dfToReturn)] = row
                dfToReturn.loc[len(dfToReturn) - 1, "datesEvenement"] = date
                dfToReturn.loc[len(dfToReturn) - 1, "uid"] = str(row["uid"]) + "-" + str(i)
        elif len(row["datesEvenement"].split(", ")) <= 1:
            dfToReturn.loc[len(dfToReturn)] = row
    return dfToReturn


"""Ajout/modification des données utiles pour le RAG"""
logging.info("Renommage des colonnes longdescription_fr et conditions_fr")
data = data.rename(columns={"longdescription_fr": "description", "conditions_fr": "conditions"})

logging.info("Création de la colonne adresse")
data["addresse"] = data["location_name"] + ", " + data["location_address"]

logging.info("Création de la colonne datesEvenement")
data["datesEvenement"] = data["timings"].apply(getBegin)

logging.info("Création de la colonne dureeEvenement")
data["dureeEvenement"] = data["timings"].apply(getDuree)

logging.info("Remplacement des valeurs vides par 'none'")
pd.set_option('future.no_silent_downcasting', True)
data = data.fillna("none")

nbLignesAvant = len(data)
logging.info(f"Duplication des lignes multi-datées - nombre de lignes avant : {nbLignesAvant}")
data = duplicateAndRemoveEvent(data)
logging.info(f"Duplication terminée - nombre de lignes après : {len(data)} ({len(data) - nbLignesAvant} lignes ajoutées)")
""""""


"""Création du fichier prêt pour le chunking des données"""
logging.info("Construction du dataframe final pour le chunking")
dfFinal = pd.DataFrame({})
dfFinal["id"] = data["uid"]
dfFinal["text"] = "<h1>Date de l'évènement : </h1>" + " <p>l'évènement se déroule le " + data["datesEvenement"].str.split(" ").str[0] + " à " + data["datesEvenement"].str.split(" ").str[1]  +  "</p><h1>Description de l'évènement : </h1><p>" + data["description"].astype(str) + "<h1>Informations supplémentaires : </p></h1><p>- Les conditions sont les suivantes : " + data["conditions"].astype(str) + "<br>- L'évènement se déroule à l'adresse suivante : " + data["addresse"].astype(str) + "l'évènement se déroule le " +  data["datesEvenement"] + "<br>- l'évènement durera : " + data["dureeEvenement"].astype(str) + "</p>"
dfFinal["metadata"] = "[{ motsCles : " + data["keywords_fr"].astype(str) + "},{ accessibilite : " + data["accessibility_label_fr"].astype(str) + "},{ coordonnees : " + data["location_coordinates"].astype(str) + "},{ telephone : " + data["location_phone"].astype(str) + "},{ site_web : " + data["location_website"].astype(str) + "}]"
dfFinal["model"] = os.environ["MODEL_EMBEDDING"]

logging.info("Calcul du hash par ligne")
dfFinal['rowHash'] = dfFinal.apply(lambda row: hashlib.md5(row.astype(str).str.cat(sep='|').encode()).hexdigest(), axis=1)

logging.info("Tri des lignes par hash")
dfFinal = dfFinal.sort_values('rowHash')
logging.info(f"Dataframe final prêt - nombre de lignes : {len(dfFinal)}")

filePathChunksXlsx = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_XLSX"]
logging.info(f"Écriture du fichier chunks Excel : {filePathChunksXlsx}")
dfFinal.to_excel(filePathChunksXlsx, index=False)
logging.info("Fichier chunks.xlsx créé avec succès")


logging.info("Construction de la liste de chunks pour le fichier pickle")
all_chunks = []
for idxc, row in dfFinal.iterrows():
    chunk_dict = {
        "id": row["id"],
        "text": row["text"],
        "metadata": {"metadata": row["metadata"]}
    }
    all_chunks.append(chunk_dict)
logging.info(f"Nombre de chunks construits : {len(all_chunks)}")


# Création d'un fichier .pkl pour une utilisation avec le chatbot dans le conteneur 7
filePathChunksPkl = os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_PKL"]
logging.info(f"Écriture du fichier chunks pickle : {filePathChunksPkl}")
with open(filePathChunksPkl, 'wb') as f:
    pickle.dump(all_chunks, f)
logging.info("Fichier chunks.pkl créé avec succès")
""""""