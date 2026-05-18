"""Ce script permet de vérifier que les données néttoyées sont toutes dans la zone géographique voulue et dans l'année écoulée"""


from datetime import datetime, timedelta
import duckdb
import pandas as pd
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Récupération des données
1 : Récupération des données néttoyéess"""
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


"""Vérification que toutes les données sont comprises dans la bonne période (l'année écoulée)
nbLines : nombre total de lignes des données téléchargées
firstBeginDate : Assignation de la date de départ voulue (aujourd'hui moins un an (365 jours, soit 8760 heures))"""
nbLines = final.shape[0]
firstBeginDate = pd.to_datetime(datetime.now() - timedelta(hours=8785), format="%Y-%m-%d")
logging.info(f"Vérification des dates - date limite : {firstBeginDate.strftime('%Y-%m-%d')}, nombre de lignes total : {nbLines}")

def getCorrectDate(x):
    """_summary_
    Args:
        x (string): _description_
    Returns:
        string: _description_
    """
    return x.split(" ")[0]

nbLinesDate = final.loc[pd.to_datetime(final["firstdate_begin"].apply(getCorrectDate), format="%Y-%m-%d") >= firstBeginDate].shape[0]
logging.info(f"Lignes dans la bonne période : {nbLinesDate}/{nbLines}")

if(nbLinesDate != nbLines):
    logging.error(f"Erreur date - {nbLines - nbLinesDate} ligne(s) hors de la période attendue")
    textEmail += "- Erreur date"
    blockExtraction = True
else:
    logging.info("Vérification des dates : OK")
""""""


"""Vérification que toutes les données sont comprises dans la bonne zone géographique
nbLines : nombre total de lignes des données téléchargées
zoneGeographique : Assignation de la zone géographique voulue (Nice)"""
nbLines = final.shape[0]
zoneGeographique = "Nice"
logging.info(f"Vérification de la zone géographique : {zoneGeographique}, nombre de lignes total : {nbLines}")

nbLinesFr = final.loc[final["location_city"] == zoneGeographique].shape[0]
logging.info(f"Lignes dans la bonne zone géographique : {nbLinesFr}/{nbLines}")

if(nbLinesFr != nbLines):
    logging.error(f"Erreur localisation - {nbLines - nbLinesFr} ligne(s) hors de la zone \"{zoneGeographique}\"")
    textEmail += "- Erreur localisation \"" + zoneGeographique + "\""
    blockExtraction = True
else:
    logging.info("Vérification de la zone géographique : OK")
""""""


"""Update des valeurs textEmail et blockExtraction selon l'idExport de la table"""
logging.info(f"Mise à jour de la table {database}.{table} pour idExport : {idExport}")
conn.sql("UPDATE " + database + "." + table + " SET textEmail = '" + str(textEmail) + "' where idExport = '"+ str(idExport) + "' ;")
conn.sql("UPDATE " + database + "." + table + " SET blockExtraction = '" + str(blockExtraction) + "' where idExport = '"+ str(idExport) + "' ;")
logging.info(f"Table mise à jour - textEmail : {textEmail}, blockExtraction : {blockExtraction}")
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