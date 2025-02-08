import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_SERVICE = os.getenv("DB_SERVICE")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")

    @staticmethod
    def get_dsn():
        return f"(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST={Config.DB_HOST})(PORT={Config.DB_PORT}))(CONNECT_DATA=(SERVICE_NAME={Config.DB_SERVICE})))"
