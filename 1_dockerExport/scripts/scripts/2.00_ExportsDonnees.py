"""Ce script permet d'insérer les données brutes dans une table DuckDb (avec persistance des données), 
de récupérer le hash des données afin de le sauvegardé dans un fichier (hashFile.xlsx, utile pour la
phase de test), de créer un identifiant d'export (current datetime) pour le rajouter dans la table et le fichier hashFile.xlsx"""


import pandas as pd
import duckdb
from datetime import datetime
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


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


"""Insertion des données brutes dans la table
1 : Suppréssion de la table si elle existe
2 : Création et insertion des données dans la table"""
filePath = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_BRUT"]
logging.info(f"Suppression de la table {database}.{table} si elle existe")
conn.sql("DROP TABLE IF EXISTS "+ database + "." + table)

logging.info(f"Création de la table {database}.{table} depuis le fichier : {filePath}")
conn.sql("CREATE TABLE " + database + "." + table + " AS SELECT * FROM read_json('" + filePath + "')")
logging.info(f"Table {database}.{table} créée avec succès")
""""""


"""Récupération du hash des données de la table et création d'un idExport pour la phase de test future
cdt : current date time, sera utilisé comme identifiant d'export (idExport) pour la suite du processus d'export et de test
hashPublicEvent : hash des données de la table
new_data : Données structurée à insérer dans le fichier hashFiles.xlsx (contenant le hash et l'idExport (cdt))
df_new : format dataframe des données structurée"""
cdt = datetime.now()
logging.info(f"Génération de l'identifiant d'export (idExport) : {cdt}")

logging.info("Calcul du hash global de la table")
hashPublicEvent = conn.sql("SELECT md5(string_agg(openclassrooms.publicEvent::text, '')) FROM openclassrooms.publicEvent;").df().iloc[0].values[0]
logging.info(f"Hash global calculé : {hashPublicEvent}")

new_data = {'hashFilePublicEvent': [hashPublicEvent], 'idExport': [str(cdt)]}
df_new = pd.DataFrame(new_data)
""""""


"""Ajout du hash pour chaque ligne"""
logging.info("Ajout de la colonne rowHash dans la table")
conn.sql("ALTER TABLE openclassrooms.publicEvent ADD COLUMN rowHash VARCHAR;")
conn.sql("UPDATE openclassrooms.publicEvent SET rowHash = md5(openclassrooms.publicEvent::text);")
logging.info("Hash par ligne calculé et inséré avec succès")
""""""


"""Insertion des données dans le fichier hashFiles.xlsx (fichier pouvant ne pas exister ou dèjà contenir des données)
1 : Vérification de l'existance du fichier (création du fichier s'il n'existe pas)
2 : Récupération des anciennes données
3 : Concatenation des données  
4 : Insertion de toutes les données (impossible de rajouter des données, il faut recréer le fichier)"""
hashFilePath = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_HASH"]

if not os.path.exists(hashFilePath):
    logging.warning(f"Fichier {hashFilePath} inexistant, création en cours")
    df_new.to_excel(hashFilePath, index=False)
    logging.info(f"Fichier {hashFilePath} créé avec succès")
else:
    logging.info(f"Fichier {hashFilePath} existant, ajout des nouvelles données")
    df_existing = pd.read_excel(hashFilePath)
    logging.info(f"Nombre de lignes existantes : {len(df_existing)}")
    df_combined = pd.concat([df_existing, df_new])
    df_combined.to_excel(hashFilePath, index=False)
    logging.info(f"Fichier {hashFilePath} mis à jour avec succès - nombre de lignes total : {len(df_combined)}")
""""""


"""Ajout de la colonne idExport et des données dans la table
1 : Ajout de la colonne
2 : Ajout des données dans la colonne"""
logging.info("Ajout de la colonne idExport dans la table")
conn.sql("ALTER TABLE openclassrooms.publicEvent ADD COLUMN idExport datetime;")
conn.sql("UPDATE openclassrooms.publicEvent set idExport='" + str(cdt) + "';")
logging.info(f"Colonne idExport ajoutée et renseignée avec la valeur : {cdt}")
""""""


"""Affichage des données de la table"""
logging.info("Affichage des données de la table")
print(conn.sql("SELECT * FROM openclassrooms.publicEvent;"))
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""