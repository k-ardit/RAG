"""Ce script permet de vérifier que les données néttoyées dans le conteneur précédent n'ont pas de doublons (fichierFinal.xlsx)."""


import pandas as pd
import duckdb
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Récupération des données
1 : Récupération des données néttoyées dans un format dataframe"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
final = pd.read_excel(filePathNettoye, sheet_name="Sheet1")
logging.info(f"Données nettoyées chargées - nombre de lignes : {len(final)}")
""""""


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisée
table : table crée pour insérer les données brutes"""
database = "openclassrooms"
table = "resultExtract"
""""""


"""Connexion à DuckDb"""
logging.info(f"Connexion à DuckDB - base de données : {database}.db")
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
logging.info("Connexion à DuckDB réussie")
""""""


"""Assignation des variables idExport, textEmail et blockExtraction récupéré de la table selon idExport du dernier export
idExport : identifiant du dernier export
textEmail : valeur de la colonne textEmail selon idExport
blockExtraction : valeur de la colonne blockExtraction selon idExport"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
logging.info(f"Identifiant d'export récupéré : {idExport}")

textEmail = conn.sql("SELECT textEmail FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
blockExtraction = conn.sql("SELECT blockExtraction FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
logging.info(f"Valeurs récupérées depuis la table - textEmail : {textEmail}, blockExtraction : {blockExtraction}")

if(textEmail) == None:
    textEmail = ""
""""""


"""Vérification qu'il n'y a pas de doublons, et modification des variables textEmail et blockExtraction selon le résultat
nbDoublons : nombre total de lignes des données téléchargées"""
nbDoublons = final["uid"].shape[0] - final["uid"].drop_duplicates().shape[0]
logging.info(f"Vérification des doublons - nombre de doublons détectés : {nbDoublons}")

if (nbDoublons != 0):
    logging.error(f"Erreur doublons - {nbDoublons} doublon(s) détecté(s) sur la colonne uid")
    textEmail += "- doublons"
    blockExtraction = True
else:
    logging.info("Vérification des doublons : OK")
""""""


"""Update des valeurs nbDoublons, textEmail et blockExtraction selon l'idExport du dernier export"""
logging.info(f"Mise à jour de la table {database}.{table} pour idExport : {idExport}")
conn.sql("UPDATE " + database + "." + table + " SET nbDoublons = " + str(nbDoublons) + " where idExport = '"+ str(idExport) + "' ;")
conn.sql("UPDATE " + database + "." + table + " SET textEmail = '" + str(textEmail) + "' where idExport = '"+ str(idExport) + "' ;")
conn.sql("UPDATE " + database + "." + table + " SET blockExtraction = '" + str(blockExtraction) + "' where idExport = '"+ str(idExport) + "' ;")
logging.info(f"Table mise à jour - nbDoublons : {nbDoublons}, textEmail : {textEmail}, blockExtraction : {blockExtraction}")
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