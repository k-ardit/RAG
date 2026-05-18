"""Ce script permet de ..."""


import pandas as pd
import duckdb
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Récupération des données
1 : Récupération des données de hash
2 : Récupération des données néttoyées
3 : Instanciation de la variable idExport avec les données néttoyées"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
filePathHash = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_HASH"]

logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
final = pd.read_excel(filePathNettoye, sheet_name="Sheet1")
logging.info(f"Données nettoyées chargées - nombre de lignes : {len(final)}")

logging.info(f"Lecture du fichier de hash : {filePathHash}")
hashFiles = pd.read_excel(filePathHash, sheet_name="Sheet1")
logging.info(f"Données de hash chargées - nombre de lignes : {len(hashFiles)}")
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


"""Création de la table avec les colonnes
1 : Suppréssion de la table si elle existe
2 : Création de la table avec les colonnes"""
logging.info(f"Suppression de la table {database}.{table} si elle existe")
conn.sql("DROP TABLE IF EXISTS " + database + "." + table)

logging.info(f"Création de la table {database}.{table}")
conn.sql("CREATE TABLE " + database + "." + table + " (idExport VARCHAR, publicEvent VARCHAR, nbDoublons INTEGER, colValManquantes VARCHAR, textEmail VARCHAR, blockExtraction BOOLEAN);")
logging.info(f"Table {database}.{table} créée avec succès")
""""""


"""Insertion de la valeur idExport et hashPublicEvent du dernier export réalisé
idExport : Récupération de la valeur idExport du dernier export
hashPublicEvent : Récupération de la valeur du hash du dernier export
3 : Insertion des données dans la table"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
logging.info(f"Identifiant d'export récupéré : {idExport}")

hashPublicEvent = hashFiles.loc[hashFiles["idExport"] == idExport, "hashFilePublicEvent"].iloc[0]
logging.info(f"Hash du dernier export récupéré : {hashPublicEvent}")

logging.info(f"Insertion des données dans la table {database}.{table}")
conn.sql("INSERT INTO " + database + "." + table + " VALUES ('" + str(idExport) + "','" + hashPublicEvent + "',NULL,NULL,NULL,False)")
logging.info("Données insérées avec succès")
""""""


"""Affichage de la ligne d'export concernée"""
logging.info(f"Affichage de la ligne d'export pour idExport : {idExport}")
conn.sql("SELECT * FROM " + database + "." + table + " WHERE idExport LIKE '" + str(idExport) + "'").show()
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""