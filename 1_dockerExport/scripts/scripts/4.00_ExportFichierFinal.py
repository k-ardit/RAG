"""Ce script permet de créer le fichier .xlsx avec les données néttoyées"""

import duckdb
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisée
table : table crée pour insérer les données brutes"""
database = "openclassrooms"
table = "publicEvent"
""""""


"""Connexion à DuckDb"""
logging.info(f"Connexion à DuckDB - base de données : {database}.db")
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
logging.info("Connexion à DuckDB réussie")
""""""


"""Création du fichier .xlsx avec les données néttoyées
1 : Récupération des données dans un dataframe
2 : Création du fichier avec les données"""
logging.info(f"Récupération des données depuis la table {database}.{table}")
finalDf = conn.sql("SELECT * FROM " + database + "." + table + ";").df().astype("str")
logging.info(f"Données récupérées avec succès - nombre de lignes : {len(finalDf)}, nombre de colonnes : {len(finalDf.columns)}")

filePath = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
logging.info(f"Écriture du fichier Excel : {filePath}")
finalDf.to_excel(filePath, index=False)
logging.info("Fichier Excel créé avec succès")
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""