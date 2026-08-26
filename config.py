import os
from pathlib import Path
from utils.helpers import load_env_file

# Auto-load .env file if present
load_env_file()

# Base project directory
BASE_DIR = Path(__file__).resolve().parent

# MyAnimeList OAuth2 credentials (can be set via .env or in-app UI)
MAL_CLIENT_ID = os.getenv("MAL_CLIENT_ID", "")
MAL_CLIENT_SECRET = os.getenv("MAL_CLIENT_SECRET", "")
MAL_REDIRECT_URI = os.getenv("MAL_REDIRECT_URI", "http://localhost:8501")

# Supabase (optional for now, falls back to local SQLite DB)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Server and caching settings
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
ANIME_LIST_TTL_SECONDS = int(os.getenv("ANIME_LIST_TTL_SECONDS", str(7 * 24 * 60 * 60)))  # 7 days
PRODUCT_SEARCH_TTL_SECONDS = int(os.getenv("PRODUCT_SEARCH_TTL_SECONDS", str(24 * 60 * 60)))  # 24 hours

# Supported e-commerce stores
SUPPORTED_STORES = ["AliExpress", "Amazon", "eBay", "Etsy", "Crunchyroll"]

# Supported product categories
PRODUCT_CATEGORIES = [
    "all",
    "figure",
    "clothing",
    "poster",
    "replica",
    "accessory",
    "plush",
]

def get_mal_credentials():
    """Retrieve current MAL credentials dynamically."""
    return {
        "client_id": os.getenv("MAL_CLIENT_ID", MAL_CLIENT_ID),
        "client_secret": os.getenv("MAL_CLIENT_SECRET", MAL_CLIENT_SECRET),
        "redirect_uri": os.getenv("MAL_REDIRECT_URI", MAL_REDIRECT_URI),
    }

def update_mal_credentials(client_id: str, client_secret: str = "", redirect_uri: str = "http://localhost:8501"):
    """Update runtime and environment MAL credentials."""
    global MAL_CLIENT_ID, MAL_CLIENT_SECRET, MAL_REDIRECT_URI
    MAL_CLIENT_ID = client_id.strip()
    MAL_CLIENT_SECRET = client_secret.strip()
    MAL_REDIRECT_URI = redirect_uri.strip() or "http://localhost:8501"
    os.environ["MAL_CLIENT_ID"] = MAL_CLIENT_ID
    os.environ["MAL_CLIENT_SECRET"] = MAL_CLIENT_SECRET
    os.environ["MAL_REDIRECT_URI"] = MAL_REDIRECT_URI