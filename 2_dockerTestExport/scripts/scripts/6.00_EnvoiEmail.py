"""Ce script permet d'envoyer un email informatif avec en contenu le resultat du test de l'export"""


import duckdb
import pandas as pd
import smtplib
import os


"""Instanciation des variables de dossiers et fichiers
pathData : dossier qui contient toutes les données
folderOpenData : dossier qui contient les données téléchargées brutes (json), les hash historisé des données (hashFiles.xsls),
                les données exportées néttoyées (fichierFinal.xlsx) et le rapport de test de téléchargement et de néttoyage (testExport.xlsx)
donneeNettoyee : fichier avec les données néttoyées
fichierTest : fichier contenant le resultat des tests"""
pathData = os.environ["PATHDATA"]
folderOpenData = "opendata/"
donneeNettoyee = "FichierFinal.xlsx"
""""""


"""Instanciation des paramètres de serveurs d'email"""
utilisateur = os.environ["EMAIL_USER"]
password = os.environ["EMAIL_PASSWORD"]
server_smtp = os.environ["EMAIL_SMTP_SERVER"]
port_smtp = os.environ["EMAIL_SMTP_PORT"]
email_recipient = os.environ["EMAIL_RECIPIENT"]
""""""


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisée
table : table ou on insère les données de test"""
database = "openclassrooms"
table = "resultExtract"
""""""


"""Connexion à DuckDb"""
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
""""""


"""Récupération des données
final : Récupération des données néttoyées dans un format dataframe
idExport : Récupération de idExport de l'export"""
final = pd.read_excel(pathData + folderOpenData + donneeNettoyee, sheet_name="Sheet1")
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
""""""


"""Récupération du texte à envoyer par email"""
textEmail = conn.sql("SELECT textEmail FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
""""""


"""Récupération de la valeur blockExtraction pour savoir si l'export est bon et si on peut continuer"""
blockExtraction = conn.sql("SELECT blockExtraction FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
""""""


"""Ajustement de l'email (objet et corps de l'email) à envoyer selon les données répurérés de textEmail et blockExtraction"""
if blockExtraction == True:
    subject = 'Echec de l export des donnees '
    textEmail = 'Export des evenements echoue (erreurs : ' + textEmail + ')'
elif blockExtraction == False:
    subject = 'Export effectue sans erreurs'
    textEmail = 'Export des evenements reussi : ' +  '(informations supplementaires '+  textEmail + ')'
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""


"""envoie de l'email"""
headers = ["From: " + utilisateur,
           "Subject: " + subject,
           "To: " + email_recipient,
           "MIME-Version: 1.0",
           "Content-Type: text/html"]
headers = "\r\n".join(headers)
session = smtplib.SMTP(server_smtp, port_smtp)
session.ehlo()
session.starttls()
session.ehlo()
session.login(utilisateur, password)
session.sendmail(utilisateur, email_recipient, headers + "\r\n\r\n" + "" + textEmail + "")
session.quit()
""""""