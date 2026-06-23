# POC Avantages Sportifs — Sport Data Solution

Automatisation du calcul des avantages employés à partir des données d'activité Strava.

## Avantages calculés

| Avantage | Règle |
|----------|-------|
| **Prime de trajet** | 5% du salaire brut annuel pour les salariés se déplaçant sportivement (marche/running, vélo/trottinette) |
| **5 Jours bien-être** | 5 jours de congés supplémentaires pour les salariés avec ≥ 15 activités sur les 12 derniers mois |

## Architecture

```
flow_01_Strava/        → OAuth Strava + collecte des activités (SQL Server + ASP.NET + Python)
flow_01_Slack/         → Notifications temps réel via CDC Debezium + Flask
flow_01_PowerBI/       → ETL, nettoyage, calcul des primes (DuckDB + Python)
dockerCompose_Kestra/  → Orchestration (Kestra Community Edition)
data/                  → Exports Excel et fichiers partagés
```

Les flows communiquent via le réseau Docker partagé `strava_network`.

## Prérequis

- Docker Desktop (avec TCP port 2375 activé pour Kestra sur Windows)
- Compte [Strava Developer](https://developers.strava.com/) (Client ID + Secret)
- Clé API [Google Maps Distance Matrix](https://developers.google.com/maps/documentation/distance-matrix)
- Webhook Slack configuré

## Démarrage rapide

```bash
# 1. Copier et remplir les fichiers .env
cp flow_01_Strava/.env.example flow_01_Strava/.env
cp flow_01_PowerBI/.env.example flow_01_PowerBI/.env
cp dockerCompose_Kestra/.env.example dockerCompose_Kestra/.env

# 2. Démarrer dans l'ordre
cd flow_01_Strava && docker-compose up -d
cd ../flow_01_Slack && docker-compose up -d
cd ../flow_01_PowerBI && docker-compose up -d
cd ../dockerCompose_Kestra && docker-compose up -d
```

Kestra est accessible sur **http://localhost:8080**

## Documentation

Voir [data/Documentation_Technique_Avantages_Sportifs.docx](data/Documentation_Technique_Avantages_Sportifs.docx) pour la documentation technique complète (~10 pages).

## Sécurité

Les fichiers `.env` sont exclus du git via `.gitignore`. Ne jamais committer de credentials.
