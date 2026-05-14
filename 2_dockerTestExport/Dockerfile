# utilisation de la version "edge" car c'est le seul à avoir le package DuckDB
FROM alpine:edge

# Notre répertoire de travail sera la racine du système de fichier du conteneur
WORKDIR /·

# add "testing" repository for duckdb in alpine (seul repositorie à avoir DuckDB)
RUN echo 'https://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories

# copie des fichiers nécessaires
COPY /scripts /scripts
COPY /requirements.txt /requirements/requirements.txt

# On met à jour les dépendances système afin de limiter les risques 
RUN apk update
RUN apk upgrade

# install build dependencies and needed tools
RUN apk add $(cat /requirements/requirements.txt)

# lancer les scripts de migrations (ligne remplacée par le docker-compose pour une gestion du flux via Kestra)
CMD ["bash", "/scripts/scripts.sh"]