"""Ce script permet de ..."""


import pandas as pd
import duckdb
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Instanciation des variables de dossiers et fichiers"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
donneeNettoyee = "FichierFinal.xlsx"
""""""


"""Récupération des données
1 : Récupération des données néttoyées dans un format dataframe"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
final = pd.read_excel(filePathNettoye, sheet_name="Sheet1")
logging.info(f"Données nettoyées chargées - nombre de lignes : {len(final)}")
""""""


"""Instanciation des paramètres de base de données DuckDB"""
database = "openclassrooms"
table = "resultExtract"
""""""


"""Connexion à DuckDb"""
logging.info(f"Connexion à DuckDB - base de données : {database}.db")
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
logging.info("Connexion à DuckDB réussie")
""""""


"""Assignation des variables idExport, textEmail et blockExtraction"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
logging.info(f"Identifiant d'export récupéré : {idExport}")

textEmail = conn.sql("SELECT textEmail FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
blockExtraction = conn.sql("SELECT blockExtraction FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
logging.info(f"Valeurs récupérées depuis la table - textEmail : {textEmail}, blockExtraction : {blockExtraction}")

if(textEmail) == None:
    textEmail = ""
""""""


"""Récupération des colonnes avec au moins une valeur null"""
columnWithNullValue = []

for series_name, series in final.items():
    if(series.loc[series.isna()].shape[0] > 0):
        columnWithNullValue.append(series_name)
        logging.warning(f"Colonne avec valeur(s) manquante(s) détectée : {series_name} ({series.loc[series.isna()].shape[0]} valeur(s) nulle(s))")

columnWithNullValueStr = ' - '.join(columnWithNullValue)

if columnWithNullValue:
    logging.info(f"Colonnes avec valeurs manquantes : {columnWithNullValueStr}")
else:
    logging.info("Vérification des valeurs manquantes : OK")

textEmail = conn.sql("SELECT textEmail FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
if(textEmail) == None:
    textEmail = ""
if columnWithNullValue != "":
    textEmail += "- valeurs manquantes :" + columnWithNullValueStr

for series_name, series in final.items():
    if(series.loc[series.isna()].shape[0] == 100):
        logging.error(f"Colonne entièrement vide détectée : {series_name} - blockExtraction mis à True")
        blockExtraction = True
""""""


"""Update des valeurs colValManquantes, textEmail et blockExtraction selon l'idExport du dernier export"""
logging.info(f"Mise à jour de la table {database}.{table} pour idExport : {idExport}")
conn.sql("UPDATE " + database + "." + table + " SET colValManquantes = '" + columnWithNullValueStr + "' where idExport = '"+ str(idExport) + "' ;")
conn.sql("UPDATE " + database + "." + table + " SET textEmail = '" + str(textEmail) + "' where idExport = '"+ str(idExport) + "' ;")
conn.sql("UPDATE " + database + "." + table + " SET blockExtraction = '" + str(blockExtraction) + "' where idExport = '"+ str(idExport) + "' ;")
logging.info(f"Table mise à jour - colValManquantes : {columnWithNullValueStr}, textEmail : {textEmail}, blockExtraction : {blockExtraction}")
""""""


"""Affichage de la ligne d'export concernée selon idExport"""
logging.info(f"Affichage de la ligne d'export pour idExport : {idExport}")
conn.sql("SELECT * FROM " + database + "." + table + " WHERE idExport LIKE '" + str(idExport) + "'").show()
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""