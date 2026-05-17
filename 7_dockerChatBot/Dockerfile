# utilisation de la version "edge" car c'est le seul à avoir le package DuckDB
FROM ubuntu:jammy

# Notre répertoire de travail sera la racine du système de fichier du conteneur
WORKDIR /·

# add "testing" repository for duckdb in alpine (seul repositorie à avoir DuckDB)
#RUN echo 'https://dl-cdn.alpinelinux.org/alpine/edge/testing' >> /etc/apk/repositories

# copie des fichiers nécessaires
COPY /scripts /scripts
COPY /requirements.txt /requirements/requirements.txt

# On met à jour les dépendances système afin de limiter les risques 
RUN apt update
RUN apt -y upgrade

# Assignation de la variable d'environnement pour des installation non interactive
#ENV DEBIAN_FRONTEND noninteractive

# install build dependencies and needed tools
RUN apt-get -y install python3-pip=22.0.2+dfsg-1ubuntu0.7
RUN pip install --no-input $(cat /requirements/requirements.txt)

# lancer les scripts de migrations (ligne remplacée par le docker-compose pour une gestion du flux via Kestra)
CMD ["bash", "/scripts/scripts.sh"]