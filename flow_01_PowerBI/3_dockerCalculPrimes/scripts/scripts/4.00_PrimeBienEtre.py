"""
5 Jours Bien-être (Prime 2)
Accorde 5 jours de bien-être aux salariés ayant au minimum
NB_ACTIVITES_MIN activités physiques sur les 12 derniers mois.
Les activités sont lues depuis StravaActivities_TestData (test)
ou StravaActivities (prod).

Paramètres configurables en haut du script.
"""
import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Paramètres métier (à faire évoluer selon les décisions RH) ────────────────
NB_ACTIVITES_MIN  = 15    # nombre minimum d'activités pour être éligible
NB_JOURS_BIENETRE = 5     # nombre de jours accordés
SOURCE_ACTIVITES  = "StravaActivities_TestData"   # ou "StravaActivities" en prod

# ── Connexion SQL Server ───────────────────────────────────────────────────────
SQL_CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('SQL_SERVER', 'sqlserver')},1433;"
    f"DATABASE={os.getenv('SQL_DATABASE', 'StravaDb')};"
    f"UID={os.getenv('SQL_USER', 'sa')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)
sql_engine = create_engine("mssql+pyodbc:///?odbc_connect=" + SQL_CONN_STR)


# ══════════════════════════════════════════════════════════════════════════════
# CALCUL
# ══════════════════════════════════════════════════════════════════════════════
def calculer_prime_bienetre(
    df_activites: pd.DataFrame,
    df_rh: pd.DataFrame,
) -> pd.DataFrame:
    """
    1. Filtre les activités des 12 derniers mois
    2. Compte les activités par salarié
    3. Identifie les salariés éligibles (>= NB_ACTIVITES_MIN)
    4. Joint avec les données RH pour enrichir
    Note: StravaActivities_TestData contient déjà IdEmploye.
    En prod, StravaActivities devra être enrichie via StravaTokens.
    """
    # 1 — Filtrage 12 derniers mois
    date_limite = datetime.now() - timedelta(days=365)
    df_activites["StartDate"] = pd.to_datetime(df_activites["StartDate"])
    df_12mois = df_activites[df_activites["StartDate"] >= date_limite].copy()
    logging.info(f"{len(df_12mois)} activités sur les 12 derniers mois")

    # 2 — Comptage par salarié
    df_comptage = (
        df_12mois
        .groupby("IdEmploye")
        .agg(
            Nb_activites      = ("Id", "count"),
            Sports_pratiques  = ("SportType", lambda x: ", ".join(sorted(x.unique()))),
            Derniere_activite = ("StartDate", "max"),
        )
        .reset_index()
    )

    # 3 — Filtrage éligibles
    df_eligibles = df_comptage[df_comptage["Nb_activites"] >= NB_ACTIVITES_MIN].copy()
    logging.info(f"{len(df_eligibles)} / {df_comptage['IdEmploye'].nunique()} salariés éligibles")

    # 4 — Jointure avec RH → infos salarié (IdEmploye côté activités = ID_salarie côté RH)
    df_result = df_eligibles.merge(
        df_rh[["ID_salarie", "Nom", "Prenom", "BU", "Salaire_brut", "Type_contrat"]],
        left_on="IdEmploye",
        right_on="ID_salarie",
        how="left"
    ).drop(columns=["ID_salarie"])

    # 5 — Colonnes résultat
    df_result["Nb_jours_bienetre"] = NB_JOURS_BIENETRE
    df_result["Seuil_activites"]   = NB_ACTIVITES_MIN
    df_result["Eligible"]          = True
    df_result["Date_calcul"]       = datetime.now()
    df_result["Annee_calcul"]      = datetime.now().year

    df_result = df_result[[
        "IdEmploye",
        "Nom",
        "Prenom",
        "BU",
        "Salaire_brut",
        "Type_contrat",
        "Nb_activites",
        "Sports_pratiques",
        "Derniere_activite",
        "Seuil_activites",
        "Eligible",
        "Nb_jours_bienetre",
        "Date_calcul",
        "Annee_calcul",
    ]].reset_index(drop=True)

    return df_result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":

    # Chargement des activités
    logging.info(f"Chargement des activites depuis {SOURCE_ACTIVITES}...")
    df_activites = pd.read_sql(f"SELECT * FROM {SOURCE_ACTIVITES}", sql_engine)

    if df_activites.empty:
        logging.error(f"{SOURCE_ACTIVITES} est vide — arrêt du script.")
        exit(1)
    logging.info(f"{len(df_activites)} activites chargees")

    # Chargement RH
    logging.info("Chargement de Donnees_RH_Nettoye...")
    df_rh = pd.read_sql("SELECT * FROM Donnees_RH_Nettoye", sql_engine)

    if df_rh.empty:
        logging.error("Donnees_RH_Nettoye est vide — arrêt du script.")
        exit(1)

    # Calcul
    df_prime = calculer_prime_bienetre(df_activites, df_rh)

    if df_prime.empty:
        logging.error(f"Aucun salarié avec {NB_ACTIVITES_MIN} activites ou plus — arrêt du script.")
        exit(1)

    # Vérification jointure RH (salariés sans correspondance = Nom NaN)
    nb_sans_rh = df_prime["Nom"].isna().sum()
    if nb_sans_rh > 0:
        logging.warning(f"{nb_sans_rh} salarié(s) éligibles sans correspondance dans Donnees_RH_Nettoye.")

    # Aperçu
    logging.info("Aperçu des 5 premières lignes :")
    print(df_prime.head().to_string(index=False))

    # Stats par BU
    logging.info("Eligibles par BU :")
    print(df_prime.groupby("BU")["IdEmploye"].count().rename("Nb_eligibles").to_string())

    # Insertion dans SQL Server
    logging.info("Insertion dans Prime_BienEtre...")
    df_prime.to_sql(name="Prime_BienEtre", con=sql_engine, if_exists="replace", index=False)
    logging.info(f"{len(df_prime)} lignes inserees dans Prime_BienEtre")

    # Vérification
    df_check = pd.read_sql("SELECT TOP 5 * FROM Prime_BienEtre", sql_engine)
    print(df_check.to_string(index=False))

    # Export Excel
    os.makedirs("/data", exist_ok=True)
    xlsx_path = f"/data/Prime_BienEtre_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df_prime.to_excel(xlsx_path, index=False)
    logging.info(f"Export Excel : {xlsx_path}")
