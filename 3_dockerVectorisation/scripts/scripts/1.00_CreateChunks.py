"""Ce script permet de ..."""


import pandas as pd
import json
from datetime import datetime
import os
import hashlib
import pickle


"""Récupération des données
data : Récupération des données néttoyées dans un format dataframe"""
data = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"], sheet_name="Sheet1")
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
            #dfToReturn = pd.concat([dfToReturn.astype(str), pd.DataFrame([row])], ignore_index=True)
    return dfToReturn


"""Ajout/modification des données utiles pour le RAG
- Renommage des colonnes longdescription_fr et conditions_fr
- Création de la colonne "adresse" (concaténation de la colonne location_name et location_address)
- Création de la colonne datesEvenement
- Création de la colonne dureeEvenement
- Duplication et suppression de certaines lignes qui ont plusieurs fois le même évènement, multidatés  (func duplicateAndRemoveEvent)
- Insertion de la valeur "none" dans toutes les cellules vides"""
data = data.rename(columns={"longdescription_fr": "description", "conditions_fr": "conditions"})
data["addresse"] = data["location_name"] + ", " + data["location_address"]
data["datesEvenement"] = data["timings"].apply(getBegin)
data["dureeEvenement"] = data["timings"].apply(getDuree)

pd.set_option('future.no_silent_downcasting', True)
data = data.fillna("none")

data = duplicateAndRemoveEvent(data)
""""""


"""Création du fichier prêt pour le chunking des données"""
dfFinal = pd.DataFrame({})
dfFinal["id"] = data["uid"]
dfFinal["text"] = "<h1>Description de l'évènement : </h1>" + data["description"].astype(str) + "<h1>Informations supplémentaires : </h1><p>- Les conditions sont les suivantes : " + data["conditions"].astype(str) + "<br>- L'évènement se déroule à l'adresse suivante : " + data["addresse"].astype(str) + "<br>- L'évènement aura lieu à la date suivante : " + data["datesEvenement"].astype(str) + "<br>- l'évènement durera : " + data["dureeEvenement"].astype(str) + "</p>"
dfFinal["metadata"] = "[{ motsCles : " + data["keywords_fr"].astype(str) + "},{ accessibilite : " + data["accessibility_label_fr"].astype(str) + "},{ coordonnees : " + data["location_coordinates"].astype(str) + "},{ telephone : " + data["location_phone"].astype(str) + "},{ site_web : " + data["location_website"].astype(str) + "}]"
dfFinal["model"] = os.environ["MODEL_EMBEDDING"]
dfFinal['rowHash'] = dfFinal.apply(lambda row: hashlib.md5(row.astype(str).str.cat(sep='|').encode()).hexdigest(),axis=1
)
# On tri les lignes par hash (pour avoir le même positionnement que les index de fin)
dfFinal = dfFinal.sort_values('rowHash')

dfFinal.to_excel(os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_XLSX"], index=False)
print("Fichier chunks.xlsx crée")


all_chunks = []
for idxc, row in dfFinal.iterrows():
    chunk_dict = {
        "id": row["id"], # Identifiant unique du chunk (doc_index_chunk_index)
        "text": row["text"],
        "metadata": {"metadata": row["metadata"]}
    }
    all_chunks.append(chunk_dict)


with open(os.environ["PATHDATA"] + os.environ["FOLDER_VECTORISATION"] + os.environ["FILE_CHUNKS_PKL"], 'wb') as f:
                pickle.dump(all_chunks, f)
#dfFinal.to_pickle(pathData + folderChunks + fileChunks2)
print("Fichier chunks.pkl crée")
""""""