import oracledb
from app.config import Config

def get_db_connection():
    try:
        connection = oracledb.connect(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            dsn=Config.get_dsn()
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None
