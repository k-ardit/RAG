"""Ce script permet d'envoyer un email informatif avec en contenu le resultat du test de l'export"""


import duckdb
import pandas as pd
import smtplib
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Instanciation des paramètres de serveurs d'email"""
utilisateur = os.environ["EMAIL_USER"]
password = os.environ["EMAIL_PASSWORD"]
server_smtp = os.environ["EMAIL_SMTP_SERVER"]
port_smtp = os.environ["EMAIL_SMTP_PORT"]
email_recipient = os.environ["EMAIL_RECIPIENT"]
logging.info(f"Paramètres email chargés - serveur SMTP : {server_smtp}:{port_smtp}, expéditeur : {utilisateur}, destinataire : {email_recipient}")
""""""


"""Instanciation des paramètres de base de données DuckDB"""
database = "openclassrooms"
table = "resultExtract"
""""""


"""Connexion à DuckDb"""
logging.info(f"Connexion à DuckDB - base de données : {database}.db")
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
logging.info("Connexion à DuckDB réussie")
""""""


"""Récupération des données"""
filePathNettoye = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_NETTOYE"]
logging.info(f"Lecture du fichier de données nettoyées : {filePathNettoye}")
final = pd.read_excel(filePathNettoye, sheet_name="Sheet1")
idExport = final[['idExport']].drop_duplicates().iloc[0]["idExport"]
logging.info(f"Identifiant d'export récupéré : {idExport}")
""""""


"""Récupération du texte à envoyer par email"""
textEmail = conn.sql("SELECT textEmail FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["textEmail"]
logging.info(f"Texte email récupéré : {textEmail}")
""""""


"""Récupération de la valeur blockExtraction"""
blockExtraction = conn.sql("SELECT blockExtraction FROM openclassrooms.resultExtract where idExport = '"+ str(idExport) + "' ;").df().iloc[0]["blockExtraction"]
logging.info(f"Valeur blockExtraction récupérée : {blockExtraction}")
""""""


"""Ajustement de l'email selon textEmail et blockExtraction"""
if blockExtraction == True:
    subject = 'Echec de l export des donnees '
    textEmail = 'Export des evenements echoue (erreurs : ' + textEmail + ')'
    logging.error(f"Export en échec - sujet : '{subject}', contenu : '{textEmail}'")
elif blockExtraction == False:
    subject = 'Export effectue sans erreurs'
    textEmail = 'Export des evenements reussi : ' + '(informations supplementaires ' + textEmail + ')'
    logging.info(f"Export réussi - sujet : '{subject}', contenu : '{textEmail}'")
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""


"""Envoi de l'email"""
logging.info(f"Connexion au serveur SMTP : {server_smtp}:{port_smtp}")
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
logging.info("Authentification SMTP réussie")

session.sendmail(utilisateur, email_recipient, headers + "\r\n\r\n" + "" + textEmail + "")
logging.info(f"Email envoyé avec succès à : {email_recipient}")

session.quit()
logging.info("Connexion SMTP fermée")
""""""