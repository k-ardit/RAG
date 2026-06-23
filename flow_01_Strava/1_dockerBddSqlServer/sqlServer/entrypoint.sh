#!/bin/bash

# ✅ Configurer l'agent AVANT de démarrer SQL Server
/opt/mssql/bin/mssql-conf set sqlagent.enabled true

# Démarrer SQL Server en arrière-plan
/opt/mssql/bin/sqlservr &
SQLSERVER_PID=$!

# Attendre que SQL Server soit prêt
echo "Attente de SQL Server..."
until /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MonMotDePasse123!" -Q "SELECT 1" -No &>/dev/null; do
    sleep 2
done
echo "SQL Server est prêt."

# Vérifier que l'agent tourne
echo "Vérification SQL Server Agent..."
/opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "MonMotDePasse123!" -No \
  -Q "SELECT servicename, status_desc FROM sys.dm_server_services WHERE servicename LIKE '%Agent%'"

# Garder le conteneur actif
wait $SQLSERVER_PID
