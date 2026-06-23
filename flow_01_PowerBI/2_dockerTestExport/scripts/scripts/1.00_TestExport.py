import os
import logging
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import pandas as pd
import pyodbc
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Connexion SQL Server ───────────────────────────────────────────────────────
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

sql_engine = create_engine("mssql+pyodbc:///?odbc_connect=" + SQL_SERVER_CONN_STR)

# ── Config email (GMX) ────────────────────────────────────────────────────────
SMTP_HOST     = os.environ["EMAIL_SMTP_SERVER"]  
SMTP_PORT     = os.environ["EMAIL_SMTP_PORT"]
SMTP_USER     = os.environ["EMAIL_USER"]
SMTP_PASSWORD = os.environ["EMAIL_PASSWORD"]
EMAIL_TO      = os.environ["EMAIL_RECIPIENT"]

# ── Tables et colonnes clés ───────────────────────────────────────────────────
TABLES = {
    "StravaTokens_Nettoye":     ["AthleteId", "AccessToken", "RefreshToken"],
    "StravaActivities_Nettoye": ["Id", "AthleteId", "StartDate"],
    "activites_Nettoye":        ["Id", "AthleteId"],
    "Donnees_RH_Nettoye":       ["ID_salarie", "Nom", "Prenom"],
    "Donnees_Sportive_Nettoye": ["ID_salarie", "Sport"],
}

# ══════════════════════════════════════════════════════════════════════════════
# TESTS
# ══════════════════════════════════════════════════════════════════════════════
def test_structure(df: pd.DataFrame, table: str, cles: list) -> list[str]:
    erreurs = []

    if len(df) == 0:
        erreurs.append("Table vide")

    for col in cles:
        if col not in df.columns:
            erreurs.append(f"Colonne manquante : {col}")

    return erreurs


def test_qualite(df: pd.DataFrame, table: str, cles: list) -> list[str]:
    erreurs = []

    nb_doublons = df.duplicated(subset=cles).sum()
    if nb_doublons > 0:
        erreurs.append(f"{nb_doublons} doublon(s) détecté(s) sur {cles}")

    for col in cles:
        nb_nulles = df[col].isna().sum()
        if nb_nulles > 0:
            erreurs.append(f"{nb_nulles} valeur(s) nulle(s) dans la colonne clé : {col}")

    lignes_vides = len(df) - len(df.dropna(how="all"))
    if lignes_vides > 0:
        erreurs.append(f"{lignes_vides} ligne(s) entièrement vide(s)")

    return erreurs


def test_metier(df: pd.DataFrame, table: str) -> list[str]:
    erreurs = []

    if table == "StravaTokens_Nettoye":
        invalides = (~pd.to_numeric(df["ExpiresAt"], errors="coerce").gt(0)).sum()
        if invalides > 0:
            erreurs.append(f"{invalides} ExpiresAt invalide(s) (≤ 0)")

    if table == "StravaActivities_Nettoye":
        nb_futur = (pd.to_datetime(df["StartDate"], errors="coerce") > pd.Timestamp.today()).sum()
        if nb_futur > 0:
            erreurs.append(f"{nb_futur} activité(s) avec date dans le futur")

        invalides_slack = (~df["SlackMessage"].isin([0, 1])).sum()
        if invalides_slack > 0:
            erreurs.append(f"{invalides_slack} valeur(s) SlackMessage invalide(s)")

    if table == "Donnees_RH_Nettoye":
        if "Salaire_brut" in df.columns:
            hors_plage = (~df["Salaire_brut"].between(15_000, 500_000)).sum()
            if hors_plage > 0:
                erreurs.append(f"{hors_plage} salaire(s) hors plage [15 000 - 500 000 €]")

        if "Nb_jours_CP" in df.columns:
            hors_cp = (~df["Nb_jours_CP"].between(0, 50)).sum()
            if hors_cp > 0:
                erreurs.append(f"{hors_cp} valeur(s) Nb_jours_CP hors plage [0 - 50]")

        if "Type_contrat" in df.columns:
            contrats_valides = ["CDI", "CDD", "ALTERNANCE", "STAGE", "INTERIM"]
            invalides = (~df["Type_contrat"].isin(contrats_valides)).sum()
            if invalides > 0:
                erreurs.append(f"{invalides} type(s) de contrat invalide(s)")

    if table == "Donnees_Sportive_Nettoye":
        nb_nulles = df["Sport"].isna().sum()
        if nb_nulles > 0:
            erreurs.append(f"{nb_nulles} valeur(s) nulle(s) dans Sport")

    return erreurs


# ══════════════════════════════════════════════════════════════════════════════
# EXÉCUTION DES TESTS
# ══════════════════════════════════════════════════════════════════════════════
def run_tests() -> dict:
    """Exécute tous les tests et retourne un rapport par table."""
    rapport = {}

    for table, cles in TABLES.items():
        logging.info(f"{'='*50}")
        logging.info(f"[{table}] Début des tests")
        rapport[table] = {"erreurs": [], "nb_lignes": 0}

        try:
            df = pd.read_sql(f"SELECT * FROM {table}", sql_engine)
            rapport[table]["nb_lignes"] = len(df)

            erreurs_structure = test_structure(df, table, cles)
            erreurs_qualite   = test_qualite(df, table, cles)
            erreurs_metier    = test_metier(df, table)

            toutes_erreurs = erreurs_structure + erreurs_qualite + erreurs_metier
            rapport[table]["erreurs"] = toutes_erreurs

            if toutes_erreurs:
                for e in toutes_erreurs:
                    logging.error(f"[{table}] ✗ {e}")
            else:
                logging.info(f"[{table}] ✓ Tous les tests passés ({len(df)} lignes)")

        except Exception as e:
            rapport[table]["erreurs"].append(f"Erreur inattendue : {traceback.format_exc()}")
            logging.error(f"[{table}] Erreur : {e}")

    return rapport


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════════════════════════════════════
def build_email_body(rapport: dict, succes: bool) -> str:
    now    = datetime.now().strftime("%d/%m/%Y %H:%M")
    statut = "✅ SUCCÈS" if succes else "❌ ÉCHEC"

    lignes = [
        f"<h2>Rapport de tests ETL — {statut}</h2>",
        f"<p><b>Date :</b> {now}</p>",
        f"<p><b>Statut global :</b> {statut}</p>",
        "<hr>",
        "<table border='1' cellpadding='6' cellspacing='0' style='border-collapse:collapse;'>",
        "<tr style='background:#1E293B;color:white;'>"
        "<th>Table</th><th>Lignes</th><th>Statut</th><th>Détail</th></tr>",
    ]

    for table, info in rapport.items():
        ok      = len(info["erreurs"]) == 0
        couleur = "#D1FAE5" if ok else "#FEE2E2"
        icone   = "✅" if ok else "❌"
        detail  = "<br>".join(info["erreurs"]) if info["erreurs"] else "Aucune erreur"
        lignes.append(
            f"<tr style='background:{couleur};'>"
            f"<td>{table}</td>"
            f"<td>{info['nb_lignes']}</td>"
            f"<td>{icone}</td>"
            f"<td>{detail}</td></tr>"
        )

    lignes.append("</table>")
    return "\n".join(lignes)


def send_email(rapport: dict, succes: bool) -> None:
    sujet = f"[ETL DC3] Tests {'RÉUSSIS ✅' if succes else 'ÉCHOUÉS ❌'} — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = sujet
    msg["From"]    = SMTP_USER
    msg["To"]      = EMAIL_TO
    msg.attach(MIMEText(build_email_body(rapport, succes), "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())
        logging.info(f"Email envoyé à {EMAIL_TO}")
    except Exception as e:
        logging.error(f"Échec de l'envoi de l'email : {e}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    rapport = run_tests()

    succes = all(len(info["erreurs"]) == 0 for info in rapport.values())

    logging.info("=" * 50)
    logging.info(f"Résultat global : {'✅ SUCCÈS' if succes else '❌ ÉCHEC'}")

    send_email(rapport, succes)