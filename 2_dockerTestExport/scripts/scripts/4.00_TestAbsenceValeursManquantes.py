"""Ce script permet de ..."""


import pandas as pd
import duckdb
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
1 : Récupération des données néttoyées dans un format dataframe"""
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


"""Récupératioon des colonnes avec au moins une valeur null, et assignation des variables textEmail et blockExtraction selon le résultat
nbDoublons : nombre total de lignes des données téléchargées
columnWithNullValue : liste des colonnes avec au moins une valeur nulle
columnWithNullValueStr : concaténation des colonnes avec au moins une valeur nulle"""
# Instanciation de la variable columnWithNullValue
columnWithNullValue = []

# Ajout des valeurs à la variable columnWithNullValue (avec la liste des colonnes qui ont au moins une valeur vide : non bloquant)
for series_name, series in final.items():
    if(series.loc[series.isna()].shape[0] > 0) :
        columnWithNullValue.append(series_name)

# Concaténation des valeurs contenue dans la liste columnWithNullValue avec un séparateur (" - ") afin de mettre à jour la variable textEmail
columnWithNullValueStr = ' - '.join(columnWithNullValue)

# UPDATE de la valeur textEmail
textEmail = conn.sql("SELECT textEmail FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
if(textEmail) == None:
    textEmail = ""
if columnWithNullValue != "":
    textEmail += "- valeurs manquantes :" + columnWithNullValueStr

# Assignation de la valeur True à la variable blockExtraction si une colonne est entièrement vide (qui aurait dû être supprimmée lors de la phase d'export)
for series_name, series in final.items():
    if(series.loc[series.isna()].shape[0] == 100) :
        blockExtraction = True    
""""""


"""Update des valeurs colValManquantes, textEmail et blockExtraction selon l'idExport du dernier export"""
# Update de la valeur colValManquantes
conn.sql("UPDATE " + database + "." + table + " SET colValManquantes = '" + columnWithNullValueStr + "' where idExport = '"+ str(idExport) + "' ;")
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