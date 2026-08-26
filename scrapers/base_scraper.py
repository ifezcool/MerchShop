import abc
import urllib.parse
from typing import List, Dict, Any, Optional
from utils.rate_limiter import default_limiter

class BaseScraper(abc.ABC):
    """Abstract base class for e-commerce store search and scrapers."""

    def __init__(self, store_name: str, delay: float = 1.0):
        self.store_name = store_name
        self.delay = delay
        self.rate_limiter = default_limiter

    @abc.abstractmethod
    def search(self, query: str, product_type: str = "figure", anime_title: str = "") -> List[Dict[str, Any]]:
        """Search store for matching products and return standard product dicts."""
        pass

    def build_store_search_url(self, query: str) -> str:
        """Generate direct search URL on retailer platform."""
        return f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}"

    def generate_product_id(self, anime_title: str, product_type: str, index: int) -> str:
        """Create a deterministic unique product ID."""
        import hashlib
        raw = f"{self.store_name}_{anime_title}_{product_type}_{index}".lower()
        return hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
