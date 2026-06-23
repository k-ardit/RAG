"""
Validation des déclarations de mode de déplacement des salariés.
Utilise l'API Google Maps pour calculer la distance domicile → entreprise
et signale les incohérences selon les règles métier.
"""
import os
import logging
import requests
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

import pandas as pd
from sqlalchemy import create_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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

# ── Config ────────────────────────────────────────────────────────────────────
GOOGLE_MAPS_KEY  = os.environ["GOOGLE_MAPS_API_KEY"]
COMPANY_ADDRESS  = "1362 Av. des Platanes, 34970 Lattes"

# Règles métier : mode de déplacement → (mode Google Maps, distance max en km)
REGLES = {
    "marche/running":        {"mode": "walking",  "max_km": 15},
    "vélo/trottinette/autres": {"mode": "bicycling", "max_km": 25},
    "transports en commun":  {"mode": "transit",  "max_km": None},  # pas de limite
    "véhicule thermique/électrique": {"mode": "driving", "max_km": None},
}

# ── Config email ──────────────────────────────────────────────────────────────
SMTP_HOST = os.environ["EMAIL_SMTP_SERVER"]
SMTP_PORT = int(os.environ["EMAIL_SMTP_PORT"])
SMTP_USER = os.environ["EMAIL_USER"]
SMTP_PASS = os.environ["EMAIL_PASSWORD"]
EMAIL_TO  = os.environ["EMAIL_RECIPIENT"]


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE MAPS
# ══════════════════════════════════════════════════════════════════════════════
def get_distance_km(adresse_origine: str, mode: str) -> float | None:
    """Calcule la distance en km entre l'adresse du salarié et l'entreprise."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins":      adresse_origine,
        "destinations": COMPANY_ADDRESS,
        "mode":         mode,
        "key":          GOOGLE_MAPS_KEY,
        "language":     "fr",
        "region":       "fr",
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data     = response.json()
        element  = data["rows"][0]["elements"][0]

        if element["status"] != "OK":
            logging.warning(f"Google Maps status : {element['status']} pour {adresse_origine}")
            return None

        return round(element["distance"]["value"] / 1000, 2)   # mètres → km

    except Exception as e:
        logging.error(f"Erreur Google Maps pour {adresse_origine} : {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# VALIDATION
# ══════════════════════════════════════════════════════════════════════════════
def valider_declarations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pour chaque salarié concerné, calcule la distance et vérifie la cohérence.
    Retourne un DataFrame des anomalies détectées.
    """
    anomalies = []

    for _, row in df.iterrows():
        moyen = str(row["Moyen_deplacement"]).strip().lower() if pd.notna(row["Moyen_deplacement"]) else None

        if moyen not in REGLES:
            logging.warning(f"Mode inconnu pour salarié {row['ID_salarie']} : '{moyen}'")
            continue

        regle = REGLES[moyen]

        # Pas de limite de distance pour ce mode → on ignore
        if regle["max_km"] is None:
            continue

        logging.info(f"[{row['ID_salarie']}] {row['Nom']} {row['Prenom']} — calcul distance ({moyen})")
        distance_km = get_distance_km(row["Adresse"], regle["mode"])

        if distance_km is None:
            anomalies.append({
                "ID_salarie":       row["ID_salarie"],
                "Nom":              row["Nom"],
                "Prenom":           row["Prenom"],
                "Adresse":          row["Adresse"],
                "Moyen_deplacement":moyen,
                "Distance_km":      None,
                "Max_autorise_km":  regle["max_km"],
                "Statut":           "⚠️ Adresse non trouvée",
            })
        elif distance_km > regle["max_km"]:
            anomalies.append({
                "ID_salarie":       row["ID_salarie"],
                "Nom":              row["Nom"],
                "Prenom":           row["Prenom"],
                "Adresse":          row["Adresse"],
                "Moyen_deplacement":moyen,
                "Distance_km":      distance_km,
                "Max_autorise_km":  regle["max_km"],
                "Statut":           f"❌ Distance trop grande ({distance_km} km > {regle['max_km']} km)",
            })
        else:
            logging.info(f"  → OK ({distance_km} km ≤ {regle['max_km']} km)")

    return pd.DataFrame(anomalies)


# ══════════════════════════════════════════════════════════════════════════════
# EMAIL
# ══════════════════════════════════════════════════════════════════════════════
def send_email(df_anomalies: pd.DataFrame) -> None:
    nb      = len(df_anomalies)
    succes  = nb == 0
    statut  = "✅ Aucune anomalie détectée" if succes else f"❌ {nb} anomalie(s) détectée(s)"
    sujet   = f"[ETL] Validation déclarations déplacement — {statut} — {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    if succes:
        corps = f"<h2>{statut}</h2><p>Toutes les déclarations sont cohérentes avec les règles de distance.</p>"
    else:
        tableau = df_anomalies.to_html(index=False, border=1, justify="center")
        corps   = f"""
        <h2>{statut}</h2>
        <p>Les salariés suivants ont une déclaration incohérente avec leur adresse domicile :</p>
        <style>
            table {{ border-collapse: collapse; font-family: Arial; font-size: 13px; }}
            th {{ background: #1E293B; color: white; padding: 8px; }}
            td {{ padding: 6px; border: 1px solid #CBD5E1; }}
            tr:nth-child(even) {{ background: #F1F5F9; }}
        </style>
        {tableau}
        <p style='color:#64748B;margin-top:20px;'>
            Règles appliquées :<br>
            • Marche / Running → max <b>15 km</b><br>
            • Vélo / Trottinette / Autres → max <b>25 km</b>
        </p>
        """

    msg             = MIMEMultipart("alternative")
    msg["Subject"]  = sujet
    msg["From"]     = SMTP_USER
    msg["To"]       = EMAIL_TO
    msg.attach(MIMEText(corps, "html"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, EMAIL_TO, msg.as_string())

    logging.info(f"Email envoyé à {EMAIL_TO}")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    logging.info("Chargement de Donnees_RH_Nettoye depuis SQL Server")
    df_rh = pd.read_sql("SELECT * FROM Donnees_RH_Nettoye", sql_engine)
    logging.info(f"{len(df_rh)} salariés chargés")

    logging.info("Validation des déclarations via Google Maps...")
    df_anomalies = valider_declarations(df_rh)

    if len(df_anomalies) == 0:
        logging.info("✅ Aucune anomalie détectée")
    else:
        logging.warning(f"❌ {len(df_anomalies)} anomalie(s) détectée(s)")
        print(df_anomalies.to_string(index=False))

        # Sauvegarde des anomalies en base
        df_anomalies.to_sql(
            name="Declarations_Anomalies",
            con=sql_engine,
            if_exists="replace",
            index=False
        )
        logging.info("Anomalies sauvegardées dans la table Declarations_Anomalies")

    send_email(df_anomalies)
