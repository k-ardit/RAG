# Flow 01 Slack — Notifications temps réel

Ce flow surveille les nouvelles activités Strava via Change Data Capture (CDC) et envoie des notifications Slack en temps réel, **sans Kafka**.

## Conteneurs

| Conteneur | Image | Rôle |
|-----------|-------|------|
| `debezium` | debezium/server | Capture CDC SQL Server → envoie en HTTP |
| `slack` | python:3.11-slim + Flask | Reçoit les événements et poste sur Slack |

## Architecture CDC sans Kafka

```
SQL Server (CDC activé)
    → Debezium Server (FileOffsetBackingStore + FileSchemaHistory)
    → HTTP POST http://slack:5000/events
    → Flask app
    → Slack Webhook
    → UPDATE SlackMessage=1 en base
```

Debezium est configuré en mode **HTTP sink** avec stockage fichier des offsets (pas de broker Kafka requis).

## Configuration Debezium (application.properties)

```properties
debezium.source.connector.class=io.debezium.connector.sqlserver.SqlServerConnector
debezium.source.database.hostname=sqlserver
debezium.source.table.include.list=dbo.StravaActivities,dbo.StravaTokens
debezium.sink.type=http
debezium.sink.http.url=http://slack:5000/events
debezium.source.offset.storage=org.apache.kafka.connect.storage.FileOffsetBackingStore
debezium.source.offset.storage.file.filename=/debezium/data/offsets.dat
```

## Comportement du service Flask

- Écoute sur le port **5000**
- Filtre uniquement les événements `op = "c"` (INSERT) sur `StravaActivities`
- Ignore les `UPDATE` et les événements sur `StravaTokens`
- Après envoi Slack : met à jour `SlackMessage = 1` pour éviter les doublons
- Message Slack : nom de l'athlète, nom de l'activité, type de sport, date

## Réseau

Utilise le réseau externe `strava_network` créé par `flow_01_Strava`.

## Démarrage

```bash
docker-compose up -d
```

Le flow démarre automatiquement et surveille la base en continu.
