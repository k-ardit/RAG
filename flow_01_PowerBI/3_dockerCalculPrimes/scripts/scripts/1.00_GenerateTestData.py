"""
Génération des flux de données de test pour les 12 derniers mois.
Pour chaque salarié pratiquant un sport (Donnees_Sportive_Nettoye),
génère des activités Strava simulées et les insère dans StravaActivities.
Ces données alimenteront le channel Slack (DC2).
"""
import os
import logging
import random
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Connexion SQL Server ───────────────────────────────────────────────────────
# SQL Server
SERVER   = os.getenv("SQL_SERVER",   "sqlserver")
DATABASE = os.getenv("SQL_DATABASE", "StravaDb")
USER     = os.getenv("SQL_USER")
PASSWORD = os.getenv("SQL_PASSWORD")

SQL_CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER},1433;"
    f"DATABASE={DATABASE};"
    f"UID={USER};"
    f"PWD={PASSWORD};"
    "TrustServerCertificate=yes;"
)

sql_engine = create_engine("mssql+pyodbc:///?odbc_connect=" + SQL_CONN_STR)

# ── Correspondance sport déclaré → type Strava ────────────────────────────────
SPORT_MAP = {
    "runing":          "Run",
    "running":         "Run",
    "randonnée":       "Hike",
    "tennis":          "Tennis",
    "natation":        "Swim",
    "football":        "Soccer",
    "rugby":           "Rugby",
    "badminton":       "Badminton",
    "voile":           "Sailing",
    "boxe":            "Boxing",
    "judo":            "Martial Arts",
    "escalade":        "RockClimbing",
    "triathlon":       "Triathlon",
    "équitation":      "Riding",
    "tennis de table": "TableTennis",
    "basketball":      "Basketball",
}

# Noms d'activités par sport
NOMS_ACTIVITE = {
    "Run":          ["Sortie course",     "Footing matinal",  "Run du soir",    "Entraînement cardio"],
    "Hike":         ["Randonnée",          "Sortie nature",    "Trek",           "Marche sportive"],
    "Tennis":       ["Match de tennis",   "Entraînement",     "Session tennis", "Match amical"],
    "Swim":         ["Natation",           "Session piscine",  "Longueurs",      "Entraînement natation"],
    "Soccer":       ["Match football",    "Entraînement foot","Foot en salle",  "Session foot"],
    "Rugby":        ["Match rugby",       "Entraînement",     "Session rugby",  "Mêlée d'entraînement"],
    "Badminton":    ["Session badminton", "Match amical",     "Entraînement",   "Tournoi"],
    "Sailing":      ["Sortie voile",      "Navigation",       "Régate",         "Session voile"],
    "Boxing":       ["Session boxe",      "Entraînement boxe","Sparring",       "Cardio boxe"],
    "Martial Arts": ["Session judo",      "Entraînement",     "Kata",           "Randori"],
    "RockClimbing": ["Escalade",          "Session bloc",     "Voie indoor",    "Grimpe extérieure"],
    "Triathlon":    ["Entraînement tri",  "Session triathlon","Brick training", "Nage-vélo-course"],
    "Riding":       ["Équitation",        "Balade à cheval",  "Session dressage","Obstacle"],
    "TableTennis":  ["Ping-pong",         "Match TT",         "Entraînement TT","Tournoi interne"],
    "Basketball":   ["Match basket",      "Entraînement",     "3x3",            "Session basket"],
}


# ══════════════════════════════════════════════════════════════════════════════
# GÉNÉRATION DES ACTIVITÉS
# ══════════════════════════════════════════════════════════════════════════════
def random_date_last_12_months() -> datetime:
    """Génère une date aléatoire dans les 12 derniers mois."""
    today    = datetime.now()
    debut    = today - timedelta(days=365)
    delta    = (today - debut).days
    return debut + timedelta(days=random.randint(0, delta))


def generer_activites(df_sport: pd.DataFrame) -> pd.DataFrame:
    """
    Pour chaque salarié avec un sport déclaré,
    génère entre 15 et 25 activités sur les 12 derniers mois.
    En données de test, ID_salarie est utilisé comme AthleteId.
    """
    activites = []

    logging.info(f"{len(df_sport)} salariés avec sport déclaré")

    for _, row in df_sport.iterrows():
        sport_declare = str(row["Sport"]).strip().lower()
        sport_type    = SPORT_MAP.get(sport_declare, "Workout")
        id_employe    = int(row["ID_salarie"])
        noms          = NOMS_ACTIVITE.get(sport_type, ["Activité sportive"])

        nb_activites = random.randint(15, 25)

        for i in range(nb_activites):
            start_date = random_date_last_12_months()
            activites.append({
                "Id":           int(f"{id_employe}{i:03d}"),
                "IdEmploye":    id_employe,
                "AthleteId":    id_employe,   # AthleteId = IdEmploye en données de test
                "Name":         random.choice(noms),
                "SportType":    sport_type,
                "StartDate":    start_date,
                "SlackMessage": 0,
            })

    df = pd.DataFrame(activites)
    df = df.sort_values("StartDate").reset_index(drop=True)
    logging.info(f"{len(df)} activites generees pour {df['IdEmploye'].nunique()} employes")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # Chargement des données
    logging.info("Chargement de Donnees_Sportive_Nettoye...")
    df_sport = pd.read_sql(
        "SELECT * FROM Donnees_Sportive_Nettoye WHERE Sport IS NOT NULL AND Sport != 'Aucun'",
        sql_engine
    )
    logging.info(f"{len(df_sport)} salariés avec un sport déclaré")

    # Génération (pas besoin de StravaTokens pour les données de test)
    df_activites = generer_activites(df_sport)

    # Aperçu
    logging.info("Aperçu des activités générées :")
    print(df_activites.head(10).to_string(index=False))

    # Stats
    logging.info("Statistiques par sport :")
    print(df_activites.groupby("SportType")["Id"].count().rename("Nb_activites").to_string())

    # Insertion dans SQL Server
    logging.info("Insertion dans StravaActivities_TestData...")
    df_activites.to_sql(
        name="StravaActivities_TestData",
        con=sql_engine,
        if_exists="replace",
        index=False
    )
    logging.info(f"✅ {len(df_activites)} activités insérées dans StravaActivities_TestData")

    # Vérification
    df_check = pd.read_sql("SELECT TOP 5 * FROM StravaActivities_TestData", sql_engine)
    print(df_check.to_string(index=False))
