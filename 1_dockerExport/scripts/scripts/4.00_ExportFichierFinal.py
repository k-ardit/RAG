"""Ce script permet de créer le fichier .xlsx avec les données néttoyées"""

import duckdb
import os


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisée
table : table crée pour insérer les données brutes"""
database = "openclassrooms"
table = "publicEvent"
""""""


"""Connexion à DuckDb"""
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
""""""


"""Création du fichier .xlsx avec les données néttoyées
1 : Récupération des données dans un dataframe
2 : Création du fichier avec les données"""
# Create dataframe with data
finalDf = conn.sql("SELECT * FROM " + database + "." + table + ";").df().astype("str")
# Save the data to Excel
finalDf.to_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"], index=False)
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""