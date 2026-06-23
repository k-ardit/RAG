FROM kestra/kestra:latest

USER root

# Installation du CLI Docker
RUN apt-get update && apt-get install -y \
        curl \
        gnupg2 \
        apt-transport-https \
        ca-certificates \
    && curl -fsSL https://download.docker.com/linux/debian/gpg \
        | gpg --dearmor -o /usr/share/keyrings/docker.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker.gpg] \
        https://download.docker.com/linux/debian bookworm stable" \
        > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y docker-ce-cli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Sur Windows : pas de socket Unix, connexion via TCP
ENV DOCKER_HOST=tcp://host.docker.internal:2375

USER kestra
