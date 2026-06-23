import os
import logging
import duckdb
import pyodbc
import pandas as pd
from sqlalchemy import create_engine
from datetime import datetime

# ── Connexions ────────────────────────────────────────────────────────────────

# DuckDB (base en mémoire)
duck_conn = duckdb.connect()
duck_conn.sql("CREATE SCHEMA IF NOT EXISTS strava")

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
    f"mssql+pyodbc:///?odbc_connect={SQL_SERVER_CONN_STR}"
)

# Timestamp d'export
cdt = datetime.now()


# ── Étape 1 : Chargement des sources dans DuckDB ──────────────────────────────

# Depuis SQL Server
logging.info("Chargement de StravaActivities depuis SQL Server")
with pyodbc.connect(SQL_SERVER_CONN_STR) as sql_conn:
    df_activites = pd.read_sql("SELECT * FROM StravaActivities", sql_conn)
duck_conn.register("_tmp", df_activites)
duck_conn.sql("CREATE TABLE strava.activites AS SELECT * FROM _tmp")
duck_conn.unregister("_tmp")

# Depuis Excel
logging.info("Chargement de Donnees_RH depuis Excel")
df_rh = pd.read_excel(os.environ["PATHDATA"] + "Donnees_RH.xlsx")
duck_conn.register("_tmp", df_rh)
duck_conn.sql("CREATE TABLE strava.Donnees_RH AS SELECT * FROM _tmp")
duck_conn.unregister("_tmp")

logging.info("Chargement de Donnees_Sportive depuis Excel")
df_sportive = pd.read_excel(os.environ["PATHDATA"] + "Donnees_Sportive.xlsx")
duck_conn.register("_tmp", df_sportive)
duck_conn.sql("CREATE TABLE strava.Donnees_Sportive AS SELECT * FROM _tmp")
duck_conn.unregister("_tmp")

# ── Étape 2 : Traitement + insertion SQL Server ────────────────────────────────

def load_table(
    duck_conn: duckdb.DuckDBPyConnection,
    sql_engine,
    database: str,
    table: str,
    id_export: datetime
) -> None:
    """
    Sur une table DuckDB existante :
    1. Ajoute rowHash (hash md5 par ligne)
    2. Ajoute idExport (timestamp)
    3. Affiche un aperçu
    4. Insère la table dans SQL Server
    """
    full_table = f"{database}.{table}"

    # 1 — Hash par ligne
    logging.info(f"[{table}] Ajout de rowHash")
    duck_conn.sql(f"ALTER TABLE {full_table} ADD COLUMN rowHash VARCHAR")
    duck_conn.sql(f"UPDATE {full_table} SET rowHash = md5({full_table}::text)")

    # 2 — Colonne idExport
    logging.info(f"[{table}] Ajout de idExport")
    duck_conn.sql(f"ALTER TABLE {full_table} ADD COLUMN idExport TIMESTAMP")
    duck_conn.sql(f"UPDATE {full_table} SET idExport = '{id_export}'")

    # 3 — Aperçu
    print(duck_conn.sql(f"SELECT * FROM {full_table} LIMIT 5"))

    # 4 — Insertion dans SQL Server
    logging.info(f"[{table}] Insertion dans SQL Server")
    df = duck_conn.sql(f"SELECT * FROM {full_table}").df()
    df.to_sql(name=table, con=sql_engine, if_exists="replace", index=False)
    logging.info(f"[{table}] Insertion terminée avec succès")
    
    # 5 — Vérification : récupération et affichage des 5 premières lignes depuis SQL Server
    logging.info(f"[{table}] Vérification des données insérées dans SQL Server")
    df_check = pd.read_sql(f"SELECT TOP 5 * FROM {table}", sql_engine)
    print(df_check.to_string(index=False))
    logging.info(f"[{table}] Vérification terminée")


load_table(duck_conn, sql_engine, "strava", "activites",       id_export=cdt)
load_table(duck_conn, sql_engine, "strava", "Donnees_RH",      id_export=cdt)
load_table(duck_conn, sql_engine, "strava", "Donnees_Sportive", id_export=cdt)

duck_conn.close()