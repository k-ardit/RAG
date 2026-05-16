FROM ubuntu:jammy

# Notre répertoire de travail sera la racine du système de fichier du conteneur
WORKDIR /·

# copie des fichiers nécessaires
COPY /scripts /scripts
COPY /requirements.txt /requirements/requirements.txt

# On met à jour les dépendances système afin de limiter les risques 
RUN apt update
RUN apt -y upgrade

# install build dependencies and needed tools
RUN apt-get -y install python3-pip=22.0.2+dfsg-1ubuntu0.7
RUN pip install --no-input $(cat /requirements/requirements.txt)

# lancer les scripts de migrations (ligne remplacée par le docker-compose pour une gestion du flux via Kestra)
CMD ["bash", "/scripts/scripts.sh"]