from typing import List, Dict, Any, Optional
from database.models import SearchCacheModel
from config import PRODUCT_SEARCH_TTL_SECONDS

class CacheService:
    """Handles product search caching with configurable TTL."""

    @staticmethod
    def get_cached_results(anime_title: str, store: str = "all", product_type: str = "all") -> Optional[List[Dict[str, Any]]]:
        return SearchCacheModel.get(anime_title, store, product_type)

    @staticmethod
    def save_results(anime_title: str, store: str, product_type: str, search_query: str, results: List[Dict[str, Any]], ttl: int = PRODUCT_SEARCH_TTL_SECONDS):
        SearchCacheModel.set(anime_title, store, product_type, search_query, results, ttl)
