import smtplib
import os
import pandas as pd
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ── Configuration GMX ─────────────────────────────────────────────────────────
SMTP_SERVER  = "mail.gmx.com"
SMTP_PORT    = 587
GMX_USER     = os.getenv("GMX_USER")
GMX_PASSWORD = os.getenv("GMX_PASSWORD")
EXCEL_FILE   = os.getenv("EXCEL_FILE")


STRAVA_CLIENT_ID  = os.getenv("STRAVA_CLIENT_ID")
STRAVA_CALLBACK   = os.getenv("STRAVA_CALLBACK_URL")


def load_recipients(filepath):
    """Charge la liste des destinataires depuis le fichier Excel"""
    df = pd.read_excel(filepath)

    required_columns = {"Nom", "Prenom", "Email", "Id"}
    missing = required_columns - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes dans le fichier Excel : {missing}")

    df = df.dropna(subset=["Email", "Id"])
    df["Id"] = df["Id"].astype(int)

    print(f"{len(df)} destinataire(s) chargé(s) depuis {filepath}")
    return df


def build_strava_url(id_salarie):
    """Génère le lien OAuth Strava avec l'ID salarié dans le paramètre state."""
    return (
        f"https://www.strava.com/oauth/authorize"
        f"?client_id={STRAVA_CLIENT_ID}"
        f"&response_type=code"
        f"&redirect_uri={STRAVA_CALLBACK}"
        f"&approval_prompt=force"
        f"&scope=read,activity:read_all"
        f"&state={id_salarie}"
    )


def build_email_body(nom, prenom, id_salarie):
    strava_url = build_strava_url(id_salarie)
    return f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Bonjour {prenom} {nom},</h2>
        <p>Pour autoriser l'accès à vos données Strava, veuillez cliquer sur le lien suivant :</p>
        <p>
        <a href="{strava_url}">Droits d'accès Strava</a>
        </p>
    </body>
    </html>
    """


def send_email(smtp, email_to, nom, prenom, id_salarie):
    msg = MIMEMultipart()
    msg["From"]    = GMX_USER
    msg["To"]      = email_to
    msg["Subject"] = f"Droits d'accès Strava — {datetime.now().strftime('%d/%m/%Y')}"

    msg.attach(MIMEText(build_email_body(nom, prenom, id_salarie), "html", "utf-8"))
    smtp.sendmail(GMX_USER, email_to, msg.as_string())


def send_all_emails():
    recipients = load_recipients(EXCEL_FILE)

    success = 0
    errors  = 0

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(GMX_USER, GMX_PASSWORD)
        print("Connexion SMTP établie.\n")

        for _, row in recipients.iterrows():
            try:
                send_email(smtp, row["Email"], row["Nom"], row["Prenom"], row["Id"])
                print(f"Email envoye -> {row['Prenom']} {row['Nom']} ({row['Email']}) [state={row['Id']}]")
                success += 1
            except Exception as e:
                print(f"Echec -> {row['Email']} : {e}")
                errors += 1

    print(f"\nTermine — {success} envoye(s), {errors} erreur(s).")


if __name__ == "__main__":
    send_all_emails()
