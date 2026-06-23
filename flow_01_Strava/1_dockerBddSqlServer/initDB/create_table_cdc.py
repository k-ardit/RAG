import pyodbc
import time
import os

SERVER   = os.getenv("SQL_SERVER",   "sqlserver")
DATABASE = os.getenv("SQL_DATABASE", "StravaDb")
USER     = os.getenv("SQL_USER",     "sa")
PASSWORD = os.getenv("SQL_PASSWORD")
if not PASSWORD:
    raise ValueError("SQL_PASSWORD est obligatoire")

POWERBI_USER     = os.getenv("POWERBI_USER",     "powerbi_user")
POWERBI_PASSWORD = os.getenv("POWERBI_PASSWORD")
if not POWERBI_PASSWORD:
    raise ValueError("POWERBI_PASSWORD est obligatoire")

DEBEZIUM_USER     = os.getenv("DEBEZIUM_USER",     "debezium_user")
DEBEZIUM_PASSWORD = os.getenv("DEBEZIUM_PASSWORD")
if not DEBEZIUM_PASSWORD:
    raise ValueError("DEBEZIUM_PASSWORD est obligatoire")

MASTER_CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER},1433;"
    "DATABASE=master;"
    f"UID={USER};"
    f"PWD={PASSWORD};"
    "TrustServerCertificate=yes;"
)

CONNECTION_STRING = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    f"SERVER={SERVER},1433;"
    f"DATABASE={DATABASE};"
    f"UID={USER};"
    f"PWD={PASSWORD};"
    "TrustServerCertificate=yes;"
)

def wait_for_sql_server(retries=20, delay=10):
    for i in range(retries):
        try:
            conn = pyodbc.connect(MASTER_CONNECTION_STRING, timeout=5)
            conn.close()
            print("SQL Server est prêt.")
            return True
        except pyodbc.Error as e:
            print(f"SQL Server pas encore prêt ({i + 1}/{retries}) : {e}")
            time.sleep(delay)
    return False

def create_database():
    with pyodbc.connect(MASTER_CONNECTION_STRING, autocommit=True) as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = '{DATABASE}')
            CREATE DATABASE {DATABASE}
        """)
        print(f"Base de données '{DATABASE}' prête.")

def create_table_tokens():
    sql = """
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'StravaTokens'
        )
        CREATE TABLE StravaTokens
        (
            Id            INT IDENTITY(1,1) PRIMARY KEY,
            IdEmploye     INT           NOT NULL UNIQUE,
            AthleteId     BIGINT        NOT NULL UNIQUE,
            AccessToken   NVARCHAR(255) NOT NULL,
            RefreshToken  NVARCHAR(255) NOT NULL,
            ExpiresAt     BIGINT        NOT NULL,
            Scope         NVARCHAR(255) NULL,
            CreatedAt     DATETIME      NOT NULL DEFAULT GETDATE(),
            UpdatedAt     DATETIME      NOT NULL DEFAULT GETDATE()
        )
    """
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print("Table StravaTokens créée avec succès.")

def create_activities_table():
    sql = """
        IF NOT EXISTS (
            SELECT 1 FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_NAME = 'StravaActivities'
        )
        CREATE TABLE StravaActivities
        (
            Id           BIGINT        NOT NULL PRIMARY KEY,
            IdEmploye    INT           NOT NULL,
            AthleteId    BIGINT        NOT NULL,
            Name         NVARCHAR(255) NULL,
            SportType    NVARCHAR(50)  NULL,
            StartDate    DATETIME      NULL,
            SlackMessage BIT           NOT NULL DEFAULT 0,

            CONSTRAINT FK_StravaActivities_Athlete
                FOREIGN KEY (AthleteId) REFERENCES StravaTokens(AthleteId)
        )
    """
    with pyodbc.connect(CONNECTION_STRING) as conn:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        print("Table StravaActivities créée avec succès.")

def enable_cdc():
    with pyodbc.connect(CONNECTION_STRING, autocommit=True) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM sys.databases
                WHERE name = 'StravaDb' AND is_cdc_enabled = 1
            )
            EXEC sys.sp_cdc_enable_db
        """)
        print("CDC activé sur la base StravaDb.")

        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM cdc.change_tables
                WHERE source_object_id = OBJECT_ID('dbo.StravaActivities')
            )
            EXEC sys.sp_cdc_enable_table
                @source_schema = 'dbo',
                @source_name   = 'StravaActivities',
                @role_name     = NULL
        """)
        print("CDC activé sur StravaActivities.")

        cursor.execute("""
            IF NOT EXISTS (
                SELECT 1 FROM cdc.change_tables
                WHERE source_object_id = OBJECT_ID('dbo.StravaTokens')
            )
            EXEC sys.sp_cdc_enable_table
                @source_schema = 'dbo',
                @source_name   = 'StravaTokens',
                @role_name     = NULL
        """)
        print("CDC activé sur StravaTokens.")

def create_users():
    with pyodbc.connect(MASTER_CONNECTION_STRING, autocommit=True) as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = '{POWERBI_USER}')
            CREATE LOGIN {POWERBI_USER} WITH PASSWORD = '{POWERBI_PASSWORD}'
        """)

        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = '{DEBEZIUM_USER}')
            CREATE LOGIN {DEBEZIUM_USER} WITH PASSWORD = '{DEBEZIUM_PASSWORD}'
        """)

        print("Logins créés.")

    with pyodbc.connect(CONNECTION_STRING, autocommit=True) as conn:
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '{POWERBI_USER}')
            BEGIN
                CREATE USER {POWERBI_USER} FOR LOGIN {POWERBI_USER};
                ALTER ROLE db_datareader ADD MEMBER {POWERBI_USER};
            END
        """)

        cursor.execute(f"""
            IF NOT EXISTS (SELECT 1 FROM sys.database_principals WHERE name = '{DEBEZIUM_USER}')
            BEGIN
                CREATE USER {DEBEZIUM_USER} FOR LOGIN {DEBEZIUM_USER};
                ALTER ROLE db_datareader ADD MEMBER {DEBEZIUM_USER};
                GRANT VIEW DATABASE STATE TO {DEBEZIUM_USER};
            END
        """)

        print("Users créés dans StravaDb.")

if __name__ == "__main__":
    if not wait_for_sql_server():
        print("Impossible de se connecter à SQL Server.")
        exit(1)

    create_database()
    create_table_tokens()
    create_activities_table()
    enable_cdc()
    create_users()