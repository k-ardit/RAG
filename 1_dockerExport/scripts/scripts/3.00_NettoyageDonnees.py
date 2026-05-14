"""Ce script permet de créer une réplique de la table contenant les données brutes et de la néttoyer (suppression des colonnes vides,
suppression des lignes en double (selon l'identifiant) et suppression des lignes qui n'ont pas d'identifiant)"""


import duckdb


"""Instanciation des paramètres de base de données DuckDB
database : base de donnée utilisé
table : table crée pour insérer les données brutes
tableNettoyee : table avec les données néttoyées"""
database = "openclassrooms"
table = "publicEvent"
tableNettoyee = "publicEventNettoyee"
""""""


"""Connexion à DuckDb"""
conn = duckdb.connect()
conn.sql("ATTACH '"+ database + ".db'")
""""""


"""Insertion des données brutes dans la table nettoyee
1 : Suppréssion de la table nettoyee si elle existe
2 : Création et insertion des données dans la table nettoyee"""
conn.sql("DROP TABLE IF EXISTS "+ database + "." + tableNettoyee)
conn.sql("CREATE TABLE " + database + "." + tableNettoyee + " AS SELECT * FROM " + database + "." + table + " ORDER BY uid")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppression des colonnes vides (avec affichage des informations de suppression)"""
# Affichage du nombre de colonnes avant suppréssion
print("Nombre de colonnes avant suppréssion des colonnes vides : " + str(conn.sql("SELECT column_count FROM duckdb_tables() WHERE table_name like '"+ tableNettoyee +"';").df().iloc[0].values[0]))
# Suppression des colonnes vides
publicEventNettoyeeDf = conn.sql("SELECT * FROM " + database + "." + tableNettoyee + ";").df()
totalLine = publicEventNettoyeeDf.shape[0]
for series_name, series in publicEventNettoyeeDf.items():
    if ((100 - series.loc[series.notna()].shape[0] / totalLine * 100 == 100)) :
        conn.sql("ALTER TABLE " + database + "." + tableNettoyee + " DROP COLUMN " + series_name+";")
        print("Colonne " + series_name + " supprimée")
# Affichage du nombre de colonnes après suppréssion
print("Nombre de colonnes après suppréssion des colonnes vides : " + str(conn.sql("SELECT column_count FROM duckdb_tables() WHERE table_name like '"+ tableNettoyee +"';").df().iloc[0].values[0]))
print("\n")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppréssion des lignes qui n'ont pas d'id (uid null)"""
# Affichage du nombre de lignes avant suppréssion des uid null
print("Nombre de lignes avant suppréssion des uid null : " + str(conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]))
# Suppression des lignes avec un uid null
conn.sql("DELETE FROM " + database + "." + tableNettoyee + " WHERE uid IS NULL;")
# Affichage du nombre de lignes après suppréssion des uid null
print("Nombre de lignes après suppréssion des uid null : " + str(conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]))
print("\n")
""""""


"""Nettoyage de la table nettoyee 
1 : Suppréssion des doublons selon le uid"""
# Affichage du nombre de lignes avant suppréssion doublons selon le uid
print("Nombre de lignes avant suppréssion des doublons : " + str(conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]))
# Suppression des doublons selon le uid
conn.sql("CREATE OR REPLACE TABLE " + database + "." + tableNettoyee + " AS SELECT DISTINCT ON(uid) * FROM " + database + "." + tableNettoyee)
# Affichage du nombre de lignes après suppréssion doublons selon le uid
print("Nombre de lignes après suppréssion des doublons : " + str(conn.sql("SELECT COUNT(*) FROM " + database + "." + tableNettoyee + ";").df().iloc[0].values[0]))
print("\n")
""""""


"""Déconnexion de DuckDb"""
conn.sql("DETACH " + database)
conn.close()
""""""