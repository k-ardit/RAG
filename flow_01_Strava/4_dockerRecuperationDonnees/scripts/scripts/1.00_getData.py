import pyodbc
import requests
import time
import os

CLIENT_ID     = os.getenv("STRAVA_CLIENT_ID")
CLIENT_SECRET = os.getenv("STRAVA_CLIENT_SECRET")

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('SQL_SERVER', 'sqlserver')},1433;"
    f"DATABASE={os.getenv('SQL_DATABASE', 'StravaDb')};"
    f"UID={os.getenv('SQL_USER', 'sa')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)


def get_connection():
    return pyodbc.connect(CONNECTION_STRING)


# ── Tokens ────────────────────────────────────────────────────────────────────

def get_all_athletes():
    sql = "SELECT IdEmploye, AthleteId, AccessToken, RefreshToken, ExpiresAt FROM StravaTokens"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        return [
            {
                "id_employe":    row.IdEmploye,
                "athlete_id":    row.AthleteId,
                "access_token":  row.AccessToken,
                "refresh_token": row.RefreshToken,
                "expires_at":    row.ExpiresAt
            }
            for row in cursor.fetchall()
        ]


def refresh_token(refresh_token):
    response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id":     CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type":    "refresh_token"
        }
    )
    if response.status_code != 200:
        raise Exception(f"Erreur refresh token : {response.text}")

    data = response.json()
    return data["access_token"], data["refresh_token"], data["expires_at"]


def update_tokens(athlete_id, access_token, refresh_token, expires_at):
    sql = """
        UPDATE StravaTokens
        SET AccessToken  = ?,
            RefreshToken = ?,
            ExpiresAt    = ?,
            UpdatedAt    = GETDATE()
        WHERE AthleteId  = ?
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, access_token, refresh_token, expires_at, athlete_id)
        conn.commit()


def get_valid_access_token(athlete):
    if time.time() >= athlete["expires_at"] - 60:
        print(f"  Token expiré → rafraîchissement...")
        access_token, new_refresh, new_expires = refresh_token(athlete["refresh_token"])
        update_tokens(athlete["athlete_id"], access_token, new_refresh, new_expires)
        return access_token
    return athlete["access_token"]


# ── Activités ─────────────────────────────────────────────────────────────────

def fetch_activities(access_token):
    """Récupère toutes les activités de l'athlète (gestion de la pagination)"""
    activities = []
    page = 1

    while True:
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params={"per_page": 100, "page": page}
        )

        if response.status_code != 200:
            raise Exception(f"Erreur API activités : {response.text}")

        batch = response.json()

        if not batch:
            break  # plus de pages

        activities.extend(batch)
        print(f"  Page {page} → {len(batch)} activité(s) récupérée(s)")
        page += 1

    return activities


def save_activities(id_employe, athlete_id, activities):
    sql = """
        MERGE StravaActivities AS cible
        USING (SELECT ? AS Id) AS source ON cible.Id = source.Id
        WHEN MATCHED THEN
            UPDATE SET
                Name      = ?,
                SportType = ?,
                StartDate = ?
        WHEN NOT MATCHED THEN
            INSERT (Id, IdEmploye, AthleteId, Name, SportType, StartDate)
            VALUES (?, ?, ?, ?, ?, ?);
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        for a in activities:
            cursor.execute(sql,
                a["id"],                    # USING source
                a.get("name"),              # UPDATE
                a.get("sport_type"),
                a.get("start_date"),
                a["id"],                    # INSERT
                id_employe,
                athlete_id,
                a.get("name"),
                a.get("sport_type"),
                a.get("start_date")
            )
        conn.commit()


# ── Principal ─────────────────────────────────────────────────────────────────

def sync_all_athletes():
    athletes = get_all_athletes()

    if not athletes:
        print("Aucun athlète trouvé en base.")
        return

    print(f"{len(athletes)} athlète(s) trouvé(s).\n")

    for athlete in athletes:
        id_employe = athlete["id_employe"]
        athlete_id = athlete["athlete_id"]
        print(f"[Employe {id_employe} / Athlete {athlete_id}] Synchronisation en cours...")

        try:
            access_token = get_valid_access_token(athlete)
            activities   = fetch_activities(access_token)
            save_activities(id_employe, athlete_id, activities)
            print(f"[Employe {id_employe}] {len(activities)} activite(s) sauvegardee(s).\n")

        except Exception as e:
            print(f"[Employe {id_employe}] Erreur : {e}\n")


if __name__ == "__main__":
    sync_all_athletes()