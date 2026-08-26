import time
from typing import List, Dict, Any, Optional
import streamlit as st

from scrapers.aliexpress_scraper import AliExpressScraper
from scrapers.amazon_scraper import AmazonScraper
from scrapers.ebay_scraper import EbayScraper
from services.cache_service import CacheService
from services.mal_service import get_user_anime_list

SCRAPERS = {
    "aliexpress": AliExpressScraper(),
    "amazon": AmazonScraper(),
    "ebay": EbayScraper(),
}

def build_search_query(anime_title: str, product_type: str) -> str:
    """Construct a clean search query for the e-commerce store."""
    if product_type.lower() == "all":
        return f"{anime_title} merchandise"
    
    # Custom query enhancements based on anime titles
    custom_keywords = {
        "bleach": {"replica": "Bleach Ichigo Zanpakuto sword replica"},
        "attack on titan": {"replica": "Attack on Titan ODM gear sword replica"},
        "demon slayer": {"replica": "Demon Slayer Tanjiro Nichirin sword replica"},
        "one piece": {"replica": "One Piece Zoro Enma Shusui katana sword replica"},
    }

    t_lower = anime_title.lower()
    for key, overrides in custom_keywords.items():
        if key in t_lower and product_type.lower() in overrides:
            return overrides[product_type.lower()]

    return f"{anime_title} {product_type}"


def search_merchandise_for_anime(
    anime_title: str,
    product_type: str = "figure",
    store: str = "all",
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """Search for merchandise for a single anime across selected stores."""
    # Check cache first
    if not force_refresh:
        cached = CacheService.get_cached_results(anime_title, store=store, product_type=product_type)
        if cached:
            return cached

    active_scrapers = []
    if store.lower() == "all":
        active_scrapers = list(SCRAPERS.values())
    else:
        scraper_key = store.lower()
        if scraper_key in SCRAPERS:
            active_scrapers = [SCRAPERS[scraper_key]]
        else:
            active_scrapers = list(SCRAPERS.values())

    categories_to_search = [product_type] if product_type.lower() != "all" else ["figure", "clothing", "poster", "accessory"]

    all_products = []
    query = build_search_query(anime_title, product_type)

    for cat in categories_to_search:
        cat_query = build_search_query(anime_title, cat)
        for scraper in active_scrapers:
            try:
                results = scraper.search(cat_query, product_type=cat, anime_title=anime_title)
                all_products.extend(results)
            except Exception:
                pass

    # Deduplicate by product ID
    seen_ids = set()
    deduped = []
    for p in all_products:
        pid = p.get("id") or p.get("url")
        if pid not in seen_ids:
            seen_ids.add(pid)
            deduped.append(p)

    # Save in cache
    if deduped:
        CacheService.save_results(anime_title, store, product_type, query, deduped)

    return deduped


def coordinate_search(
    selected_anime_titles: Optional[List[str]] = None,
    anime_status: Optional[str] = None,
    product_type: str = "figure",
    store: str = "all",
    force_refresh: bool = False
) -> Dict[str, List[Dict[str, Any]]]:
    """Coordinate multi-anime search across e-commerce providers with progress feedback."""
    titles = selected_anime_titles or []
    if not titles:
        anime_list = get_user_anime_list(status=anime_status)
        titles = [a["title"] for a in anime_list]

    results_by_anime: Dict[str, List[Dict[str, Any]]] = {}
    if not titles:
        return results_by_anime

    progress_bar = st.progress(0, text="Initializing merchandise search...")
    status_text = st.empty()

    for idx, title in enumerate(titles):
        status_text.markdown(f"🔍 Searching merchandise for **{title}** ({idx + 1}/{len(titles)})...")
        results = search_merchandise_for_anime(
            anime_title=title,
            product_type=product_type,
            store=store,
            force_refresh=force_refresh
        )
        results_by_anime[title] = results
        progress_bar.progress((idx + 1) / len(titles))
        time.sleep(0.1)

    progress_bar.empty()
    status_text.empty()
    return results_by_anime