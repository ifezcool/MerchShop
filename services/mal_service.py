import time
from typing import List, Dict, Any, Optional
import requests
import streamlit as st

from config import get_mal_credentials, ANIME_LIST_TTL_SECONDS
from database.models import AnimeListModel, UserModel
from auth.session_manager import SessionManager

MAL_API_BASE = "https://api.myanimelist.net/v2"

# Curated high quality demo anime list for instant testing / demo mode
DEMO_ANIME_LIST = [
    {
        "mal_id": 16498,
        "title": "Attack on Titan",
        "image_url": "https://cdn.myanimelist.net/images/anime/10/47347l.jpg",
        "watch_status": "completed",
        "score": 10,
        "genres": ["Action", "Suspense", "Dark Fantasy"],
    },
    {
        "mal_id": 40748,
        "title": "Jujutsu Kaisen",
        "image_url": "https://cdn.myanimelist.net/images/anime/1171/109222l.jpg",
        "watch_status": "watching",
        "score": 9,
        "genres": ["Action", "Supernatural"],
    },
    {
        "mal_id": 38000,
        "title": "Demon Slayer: Kimetsu no Yaiba",
        "image_url": "https://cdn.myanimelist.net/images/anime/1286/99889l.jpg",
        "watch_status": "completed",
        "score": 9,
        "genres": ["Action", "Historical", "Supernatural"],
    },
    {
        "mal_id": 269,
        "title": "Bleach",
        "image_url": "https://cdn.myanimelist.net/images/anime/3/40451l.jpg",
        "watch_status": "watching",
        "score": 8,
        "genres": ["Action", "Adventure", "Supernatural"],
    },
    {
        "mal_id": 21,
        "title": "One Piece",
        "image_url": "https://cdn.myanimelist.net/images/anime/6/73245l.jpg",
        "watch_status": "watching",
        "score": 10,
        "genres": ["Action", "Adventure", "Fantasy"],
    },
    {
        "mal_id": 52991,
        "title": "Sousou no Frieren",
        "image_url": "https://cdn.myanimelist.net/images/anime/1015/138025l.jpg",
        "watch_status": "completed",
        "score": 10,
        "genres": ["Adventure", "Drama", "Fantasy"],
    },
    {
        "mal_id": 50265,
        "title": "Spy x Family",
        "image_url": "https://cdn.myanimelist.net/images/anime/1441/122795l.jpg",
        "watch_status": "plan_to_watch",
        "score": 8,
        "genres": ["Action", "Comedy"],
    },
    {
        "mal_id": 44511,
        "title": "Chainsaw Man",
        "image_url": "https://cdn.myanimelist.net/images/anime/1806/126216l.jpg",
        "watch_status": "completed",
        "score": 9,
        "genres": ["Action", "Supernatural", "Gore"],
    },
]


def fetch_from_mal_api(
    endpoint: str,
    access_token: Optional[str] = None,
    client_id: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Execute authenticated or Client-ID authorized request to MyAnimeList API v2."""
    headers = {"User-Agent": "MyAnimeListMerchFinder/1.0"}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    elif client_id:
        headers["X-MAL-CLIENT-ID"] = client_id
    else:
        raise ValueError("Either MAL access_token or client_id is required.")

    url = f"{MAL_API_BASE}/{endpoint.lstrip('/')}"
    resp = requests.get(url, headers=headers, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def parse_mal_animelist_response(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse the MAL API v2 animelist response JSON into clean list of items."""
    entries = data.get("data", [])
    parsed = []
    for item in entries:
        node = item.get("node", {})
        list_status = item.get("list_status", {})

        mal_id = node.get("id")
        title = node.get("title", "")
        pictures = node.get("main_picture", {}) or {}
        image_url = pictures.get("large") or pictures.get("medium") or ""
        watch_status = list_status.get("status", "watching")
        score = list_status.get("score")

        genres_raw = node.get("genres", [])
        genres = [g.get("name") for g in genres_raw if isinstance(g, dict) and g.get("name")]

        parsed.append(
            {
                "mal_id": mal_id,
                "title": title,
                "image_url": image_url,
                "watch_status": watch_status,
                "score": score,
                "genres": genres,
            }
        )
    return parsed


def get_user_anime_list(
    username: Optional[str] = None,
    status: Optional[str] = None,
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """Get the anime list for the current session or specified user.
    
    Supports:
    1. OAuth2 user (@me endpoint)
    2. Public username search (X-MAL-CLIENT-ID authorized)
    3. Local cached DB fallback
    4. Demo watchlist fallback
    """
    is_demo = st.session_state.get("is_demo_mode", False)
    if is_demo:
        if status and status.lower() != "all":
            return [a for a in DEMO_ANIME_LIST if a["watch_status"].lower() == status.lower()]
        return DEMO_ANIME_LIST

    current_user_id = SessionManager.get_current_user_id()
    access_token = st.session_state.get("mal_access_token")
    target_username = username or st.session_state.get("mal_username")

    # Check local DB cache first unless force_refresh
    if not force_refresh:
        cached_list = AnimeListModel.get_list(current_user_id, status=status)
        if cached_list:
            return cached_list

    creds = get_mal_credentials()
    client_id = creds["client_id"]

    # 1. Fetch via OAuth token if logged in
    if access_token:
        try:
            params = {
                "fields": "list_status,main_picture,genres,mean",
                "limit": 1000,
            }
            if status and status.lower() != "all":
                params["status"] = status.lower()

            raw_data = fetch_from_mal_api("users/@me/animelist", access_token=access_token, params=params)
            anime_list = parse_mal_animelist_response(raw_data)
            if anime_list:
                AnimeListModel.save_list(current_user_id, anime_list)
                return anime_list
        except Exception as e:
            st.warning(f"Unable to fetch live MAL anime list via OAuth: {e}")

    # 2. Fetch via Public Username + Client ID
    if target_username and target_username != "Guest" and client_id:
        try:
            params = {
                "fields": "list_status,main_picture,genres,mean",
                "limit": 1000,
            }
            if status and status.lower() != "all":
                params["status"] = status.lower()

            raw_data = fetch_from_mal_api(f"users/{target_username}/animelist", client_id=client_id, params=params)
            anime_list = parse_mal_animelist_response(raw_data)
            if anime_list:
                AnimeListModel.save_list(f"user_{target_username.lower()}", anime_list)
                return anime_list
        except Exception as e:
            st.warning(f"Could not load public list for '{target_username}': {e}")

    # Fallback to local cached data
    cached = AnimeListModel.get_list(current_user_id, status=status)
    if cached:
        return cached

    # If no data and no credentials, return demo items
    if not client_id and not access_token:
        if status and status.lower() != "all":
            return [a for a in DEMO_ANIME_LIST if a["watch_status"].lower() == status.lower()]
        return DEMO_ANIME_LIST

    return []