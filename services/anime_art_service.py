import re
from typing import Dict, Any, List, Optional
import requests

_ANIME_ART_CACHE: Dict[str, Dict[str, Any]] = {}

ANILIST_GRAPHQL_URL = "https://graphql.anilist.co"

QUERY = """
query ($search: String) {
    Media (search: $search, type: ANIME) {
        id
        title {
            romaji
            english
            native
        }
        coverImage {
            extraLarge
            large
            medium
        }
        bannerImage
        characters (perPage: 8, sort: ROLE) {
            nodes {
                name {
                    full
                    native
                }
                image {
                    large
                    medium
                }
            }
        }
    }
}
"""

def clean_title(title: str) -> str:
    """Clean anime title for optimal search matching."""
    # Remove parenthetical tags like (TV), (Season 2), etc.
    cleaned = re.sub(r"\(.*?\)|\[.*?\]", "", title).strip()
    return cleaned or title

def fetch_anime_art(anime_title: str) -> Dict[str, Any]:
    """Fetch high-resolution official anime covers, banners, and character images."""
    normalized_key = anime_title.lower().strip()
    if normalized_key in _ANIME_ART_CACHE:
        return _ANIME_ART_CACHE[normalized_key]

    search_query = clean_title(anime_title)
    result = {
        "cover": "",
        "banner": "",
        "characters": [],
        "character_names": [],
    }

    try:
        resp = requests.post(
            ANILIST_GRAPHQL_URL,
            json={"query": QUERY, "variables": {"search": search_query}},
            timeout=8,
            headers={"User-Agent": "MyAnimeListMerchFinder/1.0"}
        )
        if resp.status_code == 200:
            media = resp.json().get("data", {}).get("Media", {})
            if media:
                cover_data = media.get("coverImage", {})
                result["cover"] = cover_data.get("extraLarge") or cover_data.get("large") or cover_data.get("medium") or ""
                result["banner"] = media.get("bannerImage") or ""
                
                chars = media.get("characters", {}).get("nodes", [])
                for c in chars:
                    c_name = c.get("name", {}).get("full") or ""
                    c_img = c.get("image", {}).get("large") or c.get("image", {}).get("medium") or ""
                    if c_name and c_img:
                        result["characters"].append({"name": c_name, "image": c_img})
                        result["character_names"].append(c_name)
    except Exception:
        pass

    _ANIME_ART_CACHE[normalized_key] = result
    return result

def get_product_thumbnail(anime_title: str, product_type: str, item_index: int = 0) -> str:
    """Get a high-resolution authentic character or anime visual for a product."""
    art = fetch_anime_art(anime_title)
    chars = art.get("characters", [])
    
    # For figures and apparel, use specific character portraits if available
    if chars:
        char_idx = item_index % len(chars)
        return chars[char_idx]["image"]
    
    # For posters and replicas, use cover or banner
    if product_type in ["poster", "replica"] and art.get("banner"):
        return art["banner"]
    
    if art.get("cover"):
        return art["cover"]
        
    return ""
