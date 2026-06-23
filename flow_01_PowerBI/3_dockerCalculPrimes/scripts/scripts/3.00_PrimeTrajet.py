"""
Prime de trajet (Prime 1)
Calcule la prime pour les salariés venant au bureau en pratiquant
une activité sportive (marche, running, vélo, trottinette...).
Prime = TAUX_PRIME x salaire annuel brut

Paramètres configurables en haut du script.
"""
import logging
import os
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Paramètres métier (à faire évoluer selon les décisions RH) ────────────────
TAUX_PRIME = 0.05   # 5% du salaire annuel brut

MODES_ELIGIBLES = [
    "marche/running",
    "vélo/trottinette/autres",
]

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
def calculer_prime_trajet(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filtre les salariés éligibles et calcule leur prime de trajet.
    Éligible = mode de déplacement sportif déclaré dans les RH.
    """
    # Filtrage des modes éligibles
    df["Moyen_deplacement_lower"] = df["Moyen_deplacement"].str.lower().str.strip()
    df_eligibles = df[df["Moyen_deplacement_lower"].isin(MODES_ELIGIBLES)].copy()

    logging.info(f"{len(df_eligibles)} / {len(df)} salariés éligibles à la prime de trajet")

    # Calcul de la prime
    df_eligibles["Taux_prime"]     = TAUX_PRIME
    df_eligibles["Montant_prime"]  = (df_eligibles["Salaire_brut"] * TAUX_PRIME).round(2)
    df_eligibles["Date_calcul"]    = datetime.now()
    df_eligibles["Annee_calcul"]   = datetime.now().year

    # Sélection des colonnes utiles pour PowerBI
    df_result = df_eligibles[[
        "ID_salarie",
        "Nom",
        "Prenom",
        "BU",
        "Salaire_brut",
        "Moyen_deplacement",
        "Taux_prime",
        "Montant_prime",
        "Date_calcul",
        "Annee_calcul",
    ]].reset_index(drop=True)

    return df_result


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    # Chargement
    logging.info("Chargement de Donnees_RH_Nettoye...")
    df_rh = pd.read_sql("SELECT * FROM Donnees_RH_Nettoye", sql_engine)

    if df_rh.empty:
        logging.error("Donnees_RH_Nettoye est vide — arrêt du script.")
        exit(1)
    logging.info(f"{len(df_rh)} salariés chargés")

    # Calcul
    df_prime = calculer_prime_trajet(df_rh)

    if df_prime.empty:
        logging.error("Aucun salarié éligible à la prime de trajet — arrêt du script.")
        exit(1)

    # Vérification jointure RH (salariés sans correspondance = Nom NaN)
    nb_sans_rh = df_prime["Nom"].isna().sum()
    if nb_sans_rh > 0:
        logging.warning(f"{nb_sans_rh} salarié(s) éligibles sans correspondance dans Donnees_RH_Nettoye.")

    # Aperçu
    logging.info("Aperçu des 5 premières lignes :")
    print(df_prime.head().to_string(index=False))

    # Stats
    logging.info(f"Montant total des primes : {df_prime['Montant_prime'].sum():,.2f} EUR")
    logging.info(f"Prime moyenne            : {df_prime['Montant_prime'].mean():,.2f} EUR")
    logging.info(f"Prime min                : {df_prime['Montant_prime'].min():,.2f} EUR")
    logging.info(f"Prime max                : {df_prime['Montant_prime'].max():,.2f} EUR")

    # Insertion dans SQL Server
    logging.info("Insertion dans Prime_Trajet...")
    df_prime.to_sql(name="Prime_Trajet", con=sql_engine, if_exists="replace", index=False)
    logging.info(f"{len(df_prime)} lignes inserees dans Prime_Trajet")

    # Vérification
    df_check = pd.read_sql("SELECT TOP 5 * FROM Prime_Trajet", sql_engine)
    print(df_check.to_string(index=False))

    # Export Excel
    os.makedirs("/data", exist_ok=True)
    xlsx_path = f"/data/Prime_Trajet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    df_prime.to_excel(xlsx_path, index=False)
    logging.info(f"Export Excel : {xlsx_path}")
