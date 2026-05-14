"""Ce script permet de ..."""


from datetime import datetime, timedelta
import duckdb
import pandas as pd
import os



"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
donneeNettoyee : fichier avec les données néttoyées"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
donneeNettoyee = "FichierFinal.xlsx"
""""""


"""Récupération des données
1 : Récupération des données néttoyéess"""
# Import des données néttoyées dans un format dataframe
final = pd.read_excel(pathData + folderOpenData + donneeNettoyee, sheet_name="Sheet1")
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


"""Assignation des variables idExport, textEmail et blockExtraction récupéré de la table selon idExport du dernier export
idExport : identifiant du dernier export
textEmail : valeur de la colonne textEmail selon idExport
blockExtraction : valeur de la colonne blockExtraction selon idExport"""
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
textEmail = conn.sql("SELECT textEmail FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
blockExtraction = conn.sql("SELECT blockExtraction FROM " + database + "." + table + " where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
if(textEmail) == None:
    textEmail = "" 
"""""" 


"""Vérification que toutes les données sont comprises dans la bonne période (l'année écoulée)
nbLines : nombre total de lignes des données téléchargées
firstBeginDate : Assignation de la date de départ voulue (aujourd'hui moins un an (365 jours, soit 8760 heures))"""
nbLines = final.shape[0]
# firstBeginDate = (datetime.now() - timedelta(hours=8760)).strftime("%Y/%m/%d")
firstBeginDate = pd.to_datetime(datetime.now() - timedelta(hours=8760), format="%Y-%m-%d")

# Requêtte pour vérifier que toutes les données sont comprise dans l'année passée (Colonne firstdate_begin)
def getCorrectDate(x):
    """_summary_
    Args:
        x (string): _description_
    Returns:
        string: _description_
    """
    return x.split(" ")[0]

nbLinesDate = final.loc[pd.to_datetime(final["firstdate_begin"].apply(getCorrectDate), format="%Y-%m-%d") >= firstBeginDate].shape[0]
if(nbLinesDate != nbLines):
    print("error")
    textEmail += "- Erreur date"
    blockExtraction = True
""""""


"""Vérification que toutes les données sont comprises dans la bonne zone géographique
nbLines : nombre total de lignes des données téléchargées
zoneGeographique : Assignation de la zone géographique voulue (Nice)"""
nbLines = final.shape[0]
zoneGeographique = "Nice"

# Requêtte pour vérifier que toutes les données sont à Nice ( Colonne location_city)
nbLinesFr = final.loc[final["location_city"] == zoneGeographique].shape[0]

# Vérification que toutes les lignes sont bien comprises dans la requêtte
if(nbLinesFr != nbLines):
    print("error")
    textEmail += "- Erreur localisation \"" + zoneGeographique + "\""
    blockExtraction = True
""""""


"""Update des valeurs textEmail et blockExtraction selon l'idExport de la table"""
# Update de la valeur textEmail
conn.sql("UPDATE " + database + "." + table + " SET textEmail = '" + str(textEmail) + "' where idExport = '"+ str(idExport) + "' ;")
# Update de la valeur blockExtraction
conn.sql("UPDATE " + database + "." + table + " SET blockExtraction = '" + str(blockExtraction) + "' where idExport = '"+ str(idExport) + "' ;")
""""""


"""Affichage de la ligne d'export concernée selon idExport"""
conn.sql("SELECT * FROM " + database + "." + table + " WHERE idExport LIKE '" + str(idExport) + "'").show()
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""