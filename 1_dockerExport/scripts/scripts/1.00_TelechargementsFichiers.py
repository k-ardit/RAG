"""Ce script permet de télécharger les données publiques des évènements de la ville de Nice sur 
l'année écoulée via le site https://public.opendatasoft.com et de créer un fichier json
contenant ces données"""

import requests
import json
from datetime import datetime, timedelta
import os


"""Téléchargement des données brutes via l'API opendatasoft
firstBeginDate : Assignation de la date de départ voulue (aujourd'hui moins un an (365 jours, soit 8760 heures))
zoneGeographique : Assignation de la zone géographique voulue (Nice)
response : téléchargement des données via l'API opendatasoft avec les variables firstBeginDate et zoneGeographique"""
firstBeginDate = (datetime.now() - timedelta(hours=8760)).strftime("%Y/%m/%d")
zoneGeographique = "Nice"
response = requests.get("https://public.opendatasoft.com/api/explore/v2.1/catalog/datasets/evenements-publics-openagenda/exports/json/?lang=fr&limit=1000&offset=0&select=*&where=firstdate_begin>='" + firstBeginDate + "'+and+location_city='" + zoneGeographique + "'")
""""""


"""Création du fichier json (publicEvent.json) avec les données téléchargés via l'API"""
json_str = json.dumps(json.loads(response.content), indent=4)
print("Nombre de caractères : " + str(len(json_str)))
with open(os.environ["PATHDATA"] + os.environ["FOLDER_EXPORT"] + os.environ["FILE_EXPORT_BRUT"], "w") as f:
    f.write(json_str)
""""""

