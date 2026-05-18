"""Ce script permet de créer une réplique de la table contenant les données brutes et de la néttoyer (suppression des colonnes vides,
suppression des lignes en double (selon l'identifiant) et suppression des lignes qui n'ont pas d'identifiant)"""


import duckdb
import logging


"""Configuration des logs"""
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
""""""


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisé
table : table crée pour insérer les données brutes
tableNettoyee : table avec les données néttoyées"""
database = "openclassrooms"
table = "publicEvent"
tableNettoyee = "publicEventNettoyee"
""""""


"""Connexion à DuckDb"""
logging.info(f"Connexion à DuckDB - base de données : {database}.db")
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
logging.info("Connexion à DuckDB réussie")
""""""


"""Insertion des données brutes dans la table nettoyee
1 : Suppréssion de la table nettoyee si elle existe
2 : Création et insertion des données dans la table nettoyee"""
logging.info(f"Suppression de la table {database}.{tableNettoyee} si elle existe")
conn.sql("DROP TABLE IF EXISTS "+ database + "." + tableNettoyee)

logging.info(f"Création de la table {database}.{tableNettoyee} depuis {database}.{table}")
conn.sql("CREATE TABLE " + database + "." + tableNettoyee + " AS SELECT * FROM " + database + "." + table + " ORDER BY uid")
logging.info(f"Table {database}.{tableNettoyee} créée avec succès")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppression des colonnes vides (avec affichage des informations de suppression)"""
nbColAvant = conn.sql("SELECT column_count FROM duckdb_tables() WHERE table_name like '"+ tableNettoyee +"';").df().iloc[0].values[0]
logging.info(f"Nombre de colonnes avant suppression des colonnes vides : {nbColAvant}")

publicEventNettoyeeDf = conn.sql("SELECT * FROM " + database + "." + tableNettoyee + ";").df()
totalLine = publicEventNettoyeeDf.shape[0]

for series_name, series in publicEventNettoyeeDf.items():
    if ((100 - series.loc[series.notna()].shape[0] / totalLine * 100 == 100)) :
        conn.sql("ALTER TABLE " + database + "." + tableNettoyee + " DROP COLUMN " + series_name+";")
        logging.info(f"Colonne vide supprimée : {series_name}")

nbColApres = conn.sql("SELECT column_count FROM duckdb_tables() WHERE table_name like '"+ tableNettoyee +"';").df().iloc[0].values[0]
logging.info(f"Nombre de colonnes après suppression des colonnes vides : {nbColApres} ({nbColAvant - nbColApres} colonnes supprimées)")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppréssion des lignes qui n'ont pas d'id (uid null)"""
nbLignesAvant = conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]
logging.info(f"Nombre de lignes avant suppression des uid null : {nbLignesAvant}")

conn.sql("DELETE FROM " + database + "." + tableNettoyee + " WHERE uid IS NULL;")

nbLignesApres = conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]
logging.info(f"Nombre de lignes après suppression des uid null : {nbLignesApres} ({nbLignesAvant - nbLignesApres} lignes supprimées)")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppréssion des doublons selon le uid"""
nbLignesAvant = conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]
logging.info(f"Nombre de lignes avant suppression des doublons : {nbLignesAvant}")

conn.sql("CREATE OR REPLACE TABLE " + database + "." + tableNettoyee + " AS SELECT DISTINCT ON(uid) * FROM " + database + "." + tableNettoyee)

nbLignesApres = conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]
logging.info(f"Nombre de lignes après suppression des doublons : {nbLignesApres} ({nbLignesAvant - nbLignesApres} doublons supprimés)")
""""""


"""Déconnexion de DuckDb"""
logging.info(f"Déconnexion de DuckDB - base de données : {database}")
conn.sql("DETACH " + database)
conn.close()
logging.info("Déconnexion réussie")
""""""