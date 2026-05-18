"""Ce script permet de télécharger les données publiques des évènements de la ville de Nice sur 
l'année écoulée via le site https://public.opendatasoft.com et de créer un fichier json
contenant ces données"""

import requests
import json
from datetime import datetime, timedelta
import os
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Téléchargement des données brutes via l'API opendatasoft
firstBeginDate : Assignation de la date de départ voulue (aujourd'hui moins un an (365 jours, soit 8760 heures))
zoneGeographique : Assignation de la zone géographique voulue (Nice)
response : téléchargement des données via l'API opendatasoft avec les variables firstBeginDate et zoneGeographique"""
firstBeginDate = (datetime.now() - timedelta(hours=8760)).strftime("%Y/%m/%d")
zoneGeographique = "Nice"

logging.info(f"Téléchargement des données depuis OpenDataSoft - ville : {zoneGeographique}, date de départ : {firstBeginDate}")

response = requests.get("https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/evenements-publics-openagenda/exports/json/?lang=fr&limit=1000&offset=0&select=*&where=firstdate_begin>='" + firstBeginDate + "'+and+location_city='" + zoneGeographique + "'")

if response.status_code == 200:
    logging.info(f"Téléchargement réussi - statut HTTP : {response.status_code}")
else:
    logging.error(f"Échec du téléchargement - statut HTTP : {response.status_code}")
    exit(1)
""""""


"""Création du fichier json (publicEvent.json) avec les données téléchargés via l'API"""
json_str = json.dumps(json.loads(response.content), indent=4)

logging.info(f"Nombre de caractères récupérés : {len(json_str)}")

filePath = os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_BRUT"]
logging.info(f"Écriture du fichier JSON : {filePath}")

with open(filePath, "w") as f:
    f.write(json_str)

logging.info("Fichier JSON créé avec succès")
""""""