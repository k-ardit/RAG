FROM python:3.11-slim-bookworm

# Installation du driver ODBC 18 pour SQL Server
RUN apt-get update && apt-get install -y \
        curl gnupg2 apt-transport-https \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
        https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Notre répertoire de travail sera la racine du système de fichier du conteneur
WORKDIR /·

# copie des fichiers nécessaires
COPY /scripts /scripts
COPY /requirements.txt /requirements/requirements.txt

RUN pip install --no-cache-dir -r /requirements/requirements.txt

CMD ["bash", "/scripts/scripts.sh"]
