# Flow 01 Strava — Collecte OAuth et stockage

Ce flow gère l'autorisation OAuth Strava des salariés et la collecte de leurs activités dans SQL Server.

## Conteneurs

| Conteneur | Image | Rôle |
|-----------|-------|------|
| `sqlserver` | mssql/server:2022 | Base de données SQL Server avec CDC activé |
| `init_db` | python:3.11-slim | Initialisation one-shot des tables et CDC |
| `send_email` | python:3.11-slim | Envoi des emails d'invitation OAuth |
| `webapp` | ASP.NET Core MVC | Serveur OAuth — reçoit le callback Strava |
| `getdata` | python:3.11-slim | Synchronisation périodique des activités |

## Schéma SQL

### StravaTokens
```sql
Id INT IDENTITY PRIMARY KEY
IdEmploye INT NOT NULL UNIQUE     -- lien avec les données RH
AthleteId BIGINT NOT NULL UNIQUE  -- identifiant Strava
AccessToken NVARCHAR(255)
RefreshToken NVARCHAR(255)
ExpiresAt BIGINT
```

### StravaActivities
```sql
Id BIGINT PRIMARY KEY             -- id Strava de l'activité
IdEmploye INT NOT NULL            -- lien direct avec les données RH
AthleteId BIGINT NOT NULL
Name NVARCHAR(255)
SportType NVARCHAR(50)
StartDate DATETIME
SlackMessage BIT DEFAULT 0        -- 1 = notification Slack envoyée
```

## Flux OAuth

```
Email avec &state=IdEmploye
    → Autorisation sur strava.com
    → Callback /Home/Callback?code=XXX&state=IdEmploye
    → Sauvegarde token en base (IdEmploye + AthleteId)
    → Synchronisation des activités toutes les 2 min (via Kestra)
```

Le paramètre `state` dans l'URL OAuth permet de lier chaque autorisation à l'identifiant employé RH **sans nécessiter de compte utilisateur dans l'application**.

## Variables d'environnement (.env)

```
GMX_USER=                   # Email SMTP expéditeur
GMX_PASSWORD=               # Mot de passe SMTP
EMAIL_TO=                   # Email destinataire des rapports
STRAVA_CLIENT_ID=           # Client ID Strava Developer
STRAVA_CLIENT_SECRET=       # Client Secret Strava Developer
STRAVA_CALLBACK_URL=        # http://localhost:44350/Home/Callback
SQL_SERVER=sqlserver
SQL_DATABASE=StravaDb
SQL_USER=sa
SQL_PASSWORD=               # Mot de passe SQL Server
```

## Démarrage

```bash
docker-compose up -d

# Envoyer les emails d'invitation aux salariés
docker exec <send_email_container> python /scripts/1.00_SendEmail.py
```

> **Note** : Ce flow crée le réseau Docker `strava_network` utilisé par les autres flows.
