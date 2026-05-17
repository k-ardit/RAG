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


"""Récupération des données de test crée selon le dernier idExport
idExport : identifiant du dernier export
df_new : format dataframe des données de test"""
# Assignation de la variable idExport
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
# New data to append
df_new = conn.sql("SELECT * FROM " + database + "." + table + " where idExport = '" + str(idExport) + "' ;").df()
""""""


"""Insertion des données dans le fichier testsExport.xlsx (fichier pouvant ne pas exister ou dèjà contenir des données)
1 : Vérification de l'existance du fichier (création du fichier s'il n'existe pas)
2 : Récupération des anciennes données
3 : Concatenation des données
4 : Insertion de toutes les données (impossible de rajouter des données, il faut recréer le fichier)"""
if not os.path.exists(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORTTEST"] + os.environ["FILE_EXPORTTEST"]): # Si le fichier n'existe pas
    df_new.to_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORTTEST"] + os.environ["FILE_EXPORTTEST"], index=False) # création du fichier s'il n'existe pas
else : # si le fichier existe
    # Read existing data
    df_existing = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORTTEST"] + os.environ["FILE_EXPORTTEST"])
    # Append new data
    df_combined = pd.concat([df_existing, df_new])
    # Save the combined data to Excel
    df_combined.to_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORTTEST"] + os.environ["FILE_EXPORTTEST"], index=False)
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""