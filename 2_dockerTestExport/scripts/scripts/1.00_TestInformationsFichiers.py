"""Ce script permet de ..."""


import pandas as pd
import duckdb
import os


"""Récupération des données
1 : Récupération des données de hash
2 : Récupération des données néttoyées
3 : Instanciation de la variable idExport avec les données néttoyées"""
# Import des données néttoyées dans un format dataframe
final = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"], sheet_name="Sheet1")
# Import des données de hash dans un format dataframe
hashFiles = pd.read_excel(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_HASH"], sheet_name="Sheet1")
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


"""Création de la table avec les colonnes
1 : Suppréssion de la table si elle existe
2 : Création de la table avec les colonnes"""
conn.sql("DROP TABLE IF EXISTS " + database + "." + table)
conn.sql("CREATE TABLE " + database + "." + table + " (idExport VARCHAR, publicEvent VARCHAR, nbDoublons INTEGER, colValManquantes VARCHAR, textEmail VARCHAR, blockExtraction BOOLEAN);")
""""""


"""Insertion de la valeur idExport et hashPublicEvent du dernier export réalisé
idExport : Récupération de la valeur idExport du dernier export
hashPublicEvent : Récupération de la valeur du hash du dernier export
3 : Insertion des données dans la table"""
# Assignation de la variable idExport
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
# Instanciation de la variable hashPublicEvent (avec la valeur du hash correspondant au dernier idExport)
hashPublicEvent = hashFiles.loc[hashFiles["idExport"] == idExport, "hashFilePublicEvent"].iloc[0]
# Insertion des données dans DuckDB
conn.sql("INSERT INTO " + database + "." + table + " VALUES ('" + str(idExport) + "','" + hashPublicEvent + "',NULL,NULL,NULL,False)")
""""""


"""Affichage de la ligne d'export concernée"""
conn.sql("SELECT * FROM " + database + "." + table + " WHERE idExport LIKE '" + str(idExport) + "'").show()
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""