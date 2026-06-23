from flask import Flask, request, jsonify
import requests
import pyodbc
import os
from datetime import datetime

app = Flask(__name__)

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", os.getenv('URL_SLACK'))

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={os.getenv('SQL_SERVER', 'sqlserver')},1433;"
    f"DATABASE={os.getenv('SQL_DATABASE', 'StravaDb')};"
    f"UID={os.getenv('SQL_USER', 'sa')};"
    f"PWD={os.getenv('SQL_PASSWORD')};"
    "TrustServerCertificate=yes;"
)


def send_slack_message(activity_id, athlete_id, name, sport_type, start_date):
    message = (
        f":running: *Nouvelle activité Strava détectée !*\n"
        f"• *Athlète* : {athlete_id}\n"
        f"• *Activité* : {name}\n"
        f"• *Type* : {sport_type}\n"
        f"• *Date* : {datetime.fromtimestamp(start_date / 1000)}"
    )

    response = requests.post(SLACK_WEBHOOK_URL, json={"text": message})
    return response.status_code == 200


def update_slack_message(activity_id, sent):
    sql = "UPDATE StravaActivities SET SlackMessage = ? WHERE Id = ?"
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, 1 if sent else 0, activity_id)
        conn.commit()
    print(f"[Slack] SlackMessage mis à jour → {sent} pour activité {activity_id}")


@app.route("/events", methods=["POST"])
def receive_event():
    body      = request.get_json(force=True)
    payload   = body.get("payload", {})
    operation = payload.get("op")
    table     = payload.get("source", {}).get("table")
    after     = payload.get("after", {})

    print(f"[Slack] {table} → {operation}")

    if operation == "c" and table == "StravaActivities":
        activity_id = after.get("Id")

        sent = send_slack_message(
            activity_id = activity_id,
            athlete_id  = after.get("AthleteId"),
            name        = after.get("Name"),
            sport_type  = after.get("SportType"),
            start_date  = after.get("StartDate")
        )

        # ✅ Mise à jour du champ SlackMessage en base
        update_slack_message(activity_id, sent)

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
