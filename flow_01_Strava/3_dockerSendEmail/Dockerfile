FROM python:3.11-slim-bookworm

WORKDIR /app

COPY /scripts /scripts
COPY destinataires.xlsx .
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "/scripts/1.00_SendEmail.py"]
#CMD ["bash", "/scripts/scripts.sh"]