"""Ce script permet de ..."""


import pandas as pd
import duckdb
import os


"""Récupération des données
1 : Récupération des données néttoyées dans un format dataframe"""
final = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"], sheet_name="Sheet1")
""""""


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisée
table : table crée pour insérer les données brutes"""
database = "openclassrooms"
table = "resultExtract"
""""""


"""Connexion à DuckDb"""
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
""""""


"""Assignation des variables idExport, textEmail et blockExtraction récupéré de la table selon idExport du dernier export
idExport : identifiant du dernier export
textEmail : valeur de la colonne textEmail selon idExport
blockExtraction : valeur de la colonne blockExtraction selon idExport"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
textEmail = conn.sql("SELECT textEmail FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
blockExtraction = conn.sql("SELECT blockExtraction FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
if(textEmail) == None:
    textEmail = "" 
"""""" 


"""Vérification qu'il n'y a pas de doublons, et modification des variables textEmail et blockExtraction selon le résultat
nbDoublons : nombre total de lignes des données téléchargées"""
# Requêtte pour vrécupérer le nombre de doublons
nbDoublons = final["uid"].shape[0] - final["uid"].drop_duplicates().shape[0]
if (nbDoublons != 0):
    textEmail += "- doublons"
    blockExtraction = True
""""""


"""Update des valeurs nbDoublons, textEmail et blockExtraction selon l'idExport du dernier export"""
# Update de la valeur nbDoublons
conn.sql("UPDATE " + database + "." + table + " SET nbDoublons = " + str(nbDoublons) + " where idExport = '"+ str(idExport) + "' ;")
# Update de la valeur textEmail
conn.sql("UPDATE " + database + "." + table + " SET textEmail = '" + str(textEmail) + "' where idExport = '"+ str(idExport) + "' ;")
# Update de la valeur blockExtraction
conn.sql("UPDATE " + database + "." + table + " SET blockExtraction = '" + str(blockExtraction) + "' where idExport = '"+ str(idExport) + "' ;")
""""""


"""Affichage de la ligne d'export concernée selon idExport"""
conn.sql("SELECT * FROM " + database + "." + table + " WHERE idExport LIKE '" + str(idExport) + "'").show()
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""