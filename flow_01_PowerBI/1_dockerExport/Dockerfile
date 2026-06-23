FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt

# Pré-requis + dépôt Microsoft + ODBC Driver (tout en une couche)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    apt-transport-https \
    ca-certificates \
    && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc \
        | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft-prod.gpg] \
        https://packages.microsoft.com/debian/12/prod bookworm main" \
        > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends \
       msodbcsql18 \
       unixodbc-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python
RUN pip install --no-cache-dir -r requirements.txt

COPY scripts/ scripts/
CMD ["sh", "scripts/scripts.sh"]