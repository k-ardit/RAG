"""Ce script permet de ..."""


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


"""Récupération des données de test crée selon le dernier idExport
idExport : identifiant du dernier export
df_new : format dataframe des données de test"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
logging.info(f"Identifiant d'export récupéré : {idExport}")

df_new = conn.sql("SELECT * FROM " + database + "." + table + " where idExport = '" + str(idExport) + "' ;").df()
logging.info(f"Données de test récupérées depuis {database}.{table} - nombre de lignes : {len(df_new)}")
""""""


"""Insertion des données dans le fichier testsExport.xlsx"""
filePathTest = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORTTEST"] + os.environ["FILE_EXPORTTEST"]

if not os.path.exists(filePathTest):
    logging.warning(f"Fichier {filePathTest} inexistant, création en cours")
    df_new.to_excel(filePathTest, index=False)
    logging.info(f"Fichier {filePathTest} créé avec succès")
else:
    logging.info(f"Fichier {filePathTest} existant, ajout des nouvelles données")
    df_existing = pd.read_excel(filePathTest)
    logging.info(f"Nombre de lignes existantes : {len(df_existing)}")
    df_combined = pd.concat([df_existing, df_new])
    df_combined.to_excel(filePathTest, index=False)
    logging.info(f"Fichier {filePathTest} mis à jour avec succès - nombre de lignes total : {len(df_combined)}")
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""