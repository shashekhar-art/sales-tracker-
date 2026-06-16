import os
from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DB_PATH", "sales_tracker.db")

FLASK_SECRET = os.getenv("FLASK_SECRET", "dev-secret-change-me")
API_KEY = os.getenv("API_KEY", "dev-api-key-change-me")

GEO_THRESHOLD_KM = float(os.getenv("GEO_THRESHOLD_KM", "5"))
MATCH_THRESHOLD = float(os.getenv("MATCH_THRESHOLD", "0.6"))
