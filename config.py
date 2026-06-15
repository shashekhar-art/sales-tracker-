import os
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_NAME = os.getenv("DB_NAME", "sales_tracker")

FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-secret-change-me")
API_KEY = os.getenv("API_KEY", "dev-api-key-change-me")

GEO_THRESHOLD_KM = float(os.getenv("GEO_THRESHOLD_KM", "5"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.6"))
