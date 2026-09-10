import os
from dotenv import load_dotenv

load_dotenv()

ODDS_API_KEY = os.getenv("ODDS_API_KEY")
ODDS_API_BASE_URL = os.getenv("ODDS_API_BASE_URL")

if not ODDS_API_KEY:
    raise RuntimeError("ODDS_API_KEY is not set — add it to backend/.env")

if not ODDS_API_BASE_URL:
    raise RuntimeError("ODDS_API_BASE_URL is not set — add it to backend/.env")