"""Ce script permet de créer le fichier .xlsx avec les données néttoyées"""

import duckdb
import os

"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
fichier : nom du fichier avec les données nétoyées"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
fichier = "FichierFinal.xlsx"
""""""


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
finalDf.to_excel(pathData + folderOpenData + fichier, index=False)
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""