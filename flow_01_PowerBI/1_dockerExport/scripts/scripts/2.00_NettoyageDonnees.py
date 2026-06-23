import os
import logging
import pyodbc
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Connexions ────────────────────────────────────────────────────────────────
# SQL Server
SERVER   = os.getenv("SQL_SERVER",   "sqlserver")
DATABASE = os.getenv("SQL_DATABASE", "StravaDb")
USER     = os.getenv("SQL_USER")
PASSWORD = os.getenv("SQL_PASSWORD")

SQL_SERVER_CONN_STR = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER},1433;"
    f"DATABASE={DATABASE};"
    f"UID={USER};"
    f"PWD={PASSWORD};"
    "TrustServerCertificate=yes;"
)

sql_engine = create_engine(
    "mssql+pyodbc:///?odbc_connect=" + SQL_SERVER_CONN_STR
)

# ══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE GÉNÉRIQUE (applicable à toutes les tables)
# ══════════════════════════════════════════════════════════════════════════════
def clean_generic(df: pd.DataFrame, table: str) -> pd.DataFrame:
    initial = len(df)
    logging.info(f"[{table}] {initial} lignes en entrée")

    # 1 — Doublons
    df = df.drop_duplicates()
    logging.info(f"[{table}] Doublons supprimés : {initial - len(df)}")

    # 2 — Valeurs nulles : supprime les lignes entièrement vides
    df = df.dropna(how="all")

    # 3 — Formats : strip sur toutes les colonnes texte
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()
        df[col] = df[col].replace("", None)   # chaînes vides → null

    # 4 — Casse uniforme sur les colonnes texte
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.title()

    logging.info(f"[{table}] {len(df)} lignes après nettoyage générique")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# NETTOYAGE SPÉCIFIQUE PAR TABLE
# ══════════════════════════════════════════════════════════════════════════════
def clean_StravaTokens(df: pd.DataFrame) -> pd.DataFrame:
    # Tokens obligatoires
    df = df.dropna(subset=["AccessToken", "RefreshToken", "AthleteId"])

    # ExpiresAt doit être un entier positif
    df = df[pd.to_numeric(df["ExpiresAt"], errors="coerce") > 0]

    # Pas de doublon sur AthleteId (1 token par athlète)
    df = df.drop_duplicates(subset=["AthleteId"], keep="last")

    return df


def clean_StravaActivities(df: pd.DataFrame) -> pd.DataFrame:
    # Champs obligatoires
    df = df.dropna(subset=["Id", "AthleteId", "StartDate"])

    # StartDate en datetime
    df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")
    df = df.dropna(subset=["StartDate"])

    # Pas d'activité dans le futur
    df = df[df["StartDate"] <= datetime.now()]

    # SlackMessage doit être 0 ou 1
    df["SlackMessage"] = df["SlackMessage"].fillna(0)
    df = df[df["SlackMessage"].isin([0, 1])]

    # Pas de doublon sur l'Id d'activité
    df = df.drop_duplicates(subset=["Id"], keep="last")

    return df


def clean_activites(df: pd.DataFrame) -> pd.DataFrame:
    # Champs obligatoires
    df = df.dropna(subset=["Id", "AthleteId"])

    # StartDate en datetime
    if "StartDate" in df.columns:
        df["StartDate"] = pd.to_datetime(df["StartDate"], errors="coerce")
        df = df[df["StartDate"] <= datetime.now()]

    # Pas de doublon sur Id
    df = df.drop_duplicates(subset=["Id"], keep="last")

    return df


def clean_Donnees_RH(df: pd.DataFrame) -> pd.DataFrame:

    # ── Renommage pour faciliter le traitement ────────────────────────────────
    df = df.rename(columns={
        "ID salarié":           "ID_salarie",
        "Nom":                  "Nom",
        "Prénom":               "Prenom",
        "Date de naissance":    "Date_naissance",
        "BU":                   "BU",
        "Date d'embauche":      "Date_embauche",
        "Salaire brut":         "Salaire_brut",
        "Type de contrat":      "Type_contrat",
        "Nombre de jours de CP":"Nb_jours_CP",
        "Adresse du domicile":  "Adresse",
        "Moyen de déplacement": "Moyen_deplacement",
    })

    # ── Doublons ──────────────────────────────────────────────────────────────
    df = df.drop_duplicates(subset=["ID_salarie"], keep="last")

    # ── Nulles obligatoires ───────────────────────────────────────────────────
    df = df.dropna(subset=["ID_salarie", "Nom", "Prenom"])

    # ── Formats dates ─────────────────────────────────────────────────────────
    df["Date_naissance"] = pd.to_datetime(df["Date_naissance"], errors="coerce")
    df["Date_embauche"]  = pd.to_datetime(df["Date_embauche"],  errors="coerce")

    # ── Outliers : âge entre 18 et 65 ans ────────────────────────────────────
    today = pd.Timestamp.today()
    df["age"] = (today - df["Date_naissance"]).dt.days // 365
    df = df[df["age"].between(18, 65)]
    df = df.drop(columns=["age"])

    # ── Outliers : salaire entre 15 000 et 500 000 € ─────────────────────────
    df["Salaire_brut"] = pd.to_numeric(df["Salaire_brut"], errors="coerce")
    df = df[df["Salaire_brut"].between(15_000, 500_000)]

    # ── Outliers : jours de CP entre 0 et 50 ─────────────────────────────────
    df["Nb_jours_CP"] = pd.to_numeric(df["Nb_jours_CP"], errors="coerce")
    df = df[df["Nb_jours_CP"].between(0, 50)]

    # ── Cohérence métier : standardisation Type de contrat ───────────────────
    df["Type_contrat"] = df["Type_contrat"].str.strip().str.upper()
    contrats_valides = ["CDI", "CDD", "ALTERNANCE", "STAGE", "INTERIM"]
    df = df[df["Type_contrat"].isin(contrats_valides)]

    # ── Cohérence métier : standardisation Moyen de déplacement ──────────────
    df["Moyen_deplacement"] = df["Moyen_deplacement"].str.strip().str.lower()
    df["Moyen_deplacement"] = df["Moyen_deplacement"].replace({
        "véhicule thermique/électrique": "Vehicule",
        "transports en commun":          "Transports en commun",
        "vélo":                          "Velo",
        "à pied":                        "A pied",
        "trottinette":                   "Trottinette",
    })

    return df


def clean_Donnees_Sportive(df: pd.DataFrame) -> pd.DataFrame:

    # ── Renommage ─────────────────────────────────────────────────────────────
    df = df.rename(columns={
        "ID salarié":         "ID_salarie",
        "Pratique d'un sport": "Sport",
    })

    # ── Doublons ──────────────────────────────────────────────────────────────
    df = df.drop_duplicates(subset=["ID_salarie"], keep="last")

    # ── Nulles : ID obligatoire ───────────────────────────────────────────────
    df = df.dropna(subset=["ID_salarie"])

    # ── Nulles Sport : NaN = pas de sport ────────────────────────────────────
    df["Sport"] = df["Sport"].fillna("Aucun")

    # ── Formats : casse uniforme ──────────────────────────────────────────────
    df["Sport"] = df["Sport"].str.strip().str.title()

    return df


# ══════════════════════════════════════════════════════════════════════════════
# FONCTION PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
CLEANING_RULES = {
    "StravaTokens":     clean_StravaTokens,
    "StravaActivities": clean_StravaActivities,
    "activites":        clean_activites,
    "Donnees_RH":       clean_Donnees_RH,
    "Donnees_Sportive": clean_Donnees_Sportive,
}

def clean_and_insert(table: str) -> None:
    logging.info(f"{'='*50}")
    logging.info(f"[{table}] Début du traitement")

    # 1 — Lecture depuis SQL Server
    with pyodbc.connect(SQL_SERVER_CONN_STR) as conn:
        df = pd.read_sql(f"SELECT * FROM {table}", conn)
    logging.info(f"[{table}] {len(df)} lignes lues depuis SQL Server")

    # 2 — Nettoyage générique
    df = clean_generic(df, table)

    # 3 — Nettoyage spécifique à la table
    before = len(df)
    df = CLEANING_RULES[table](df)
    logging.info(f"[{table}] Nettoyage spécifique : {before - len(df)} lignes supprimées")

    # 4 — Aperçu
    logging.info(f"[{table}] Aperçu des 5 premières lignes :")
    print(df.head())

    # 5 — Insertion dans SQL Server avec suffixe "Nettoye"
    target_table = f"{table}_Nettoye"
    logging.info(f"[{table}] Insertion dans {target_table}")
    df.to_sql(name=target_table, con=sql_engine, if_exists="replace", index=False)
    logging.info(f"[{table}] {len(df)} lignes insérées dans {target_table}")

    # 6 — Vérification
    df_check = pd.read_sql(f"SELECT TOP 5 * FROM {target_table}", sql_engine)
    logging.info(f"[{table}] Vérification depuis SQL Server :")
    print(df_check.to_string(index=False))


# ══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION
# ══════════════════════════════════════════════════════════════════════════════
for table in CLEANING_RULES.keys():
    clean_and_insert(table)

logging.info("Nettoyage de toutes les tables terminé avec succès")