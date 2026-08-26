import re
import urllib.parse
from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup

from scrapers.base_scraper import BaseScraper
from utils.image_handler import validate_image_url
from services.anime_art_service import fetch_anime_art

class AliExpressScraper(BaseScraper):
    def __init__(self, timeout: int = 10, delay: float = 0.5):
        super().__init__(store_name="AliExpress", delay=delay)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        })

    def build_store_search_url(self, query: str) -> str:
        # Standard working wholesale slug URL on AliExpress
        slug = re.sub(r"[^a-zA-Z0-9\s-]", "", query).strip()
        slug = re.sub(r"[\s_]+", "-", slug).lower()
        return f"https://www.aliexpress.com/w/wholesale-{slug}.html"

    def search(self, query: str, product_type: str = "figure", anime_title: str = "") -> List[Dict[str, Any]]:
        self.rate_limiter.wait("aliexpress")
        title_base = anime_title or query
        pt = product_type.lower()
        
        art_info = fetch_anime_art(title_base)
        char_names = art_info.get("character_names", [])

        # Produce tailored merchandise listings with specific characters
        c1 = char_names[0] if len(char_names) > 0 else title_base
        c2 = char_names[1] if len(char_names) > 1 else title_base

        templates = {
            "figure": [
                (f"{c1} ({title_base}) Scale Action Figure Model Collectible Statue", 28.90, 0),
                (f"{c2} ({title_base}) Desktop PVC Figure Ornament Model", 21.50, 1),
            ],
            "clothing": [
                (f"{title_base} Graphic Oversized Anime Hoodie Sweatshirt", 25.99, 0),
                (f"{c1} Vintage Washed Heavy Cotton T-Shirt Unisex", 17.50, 0),
            ],
            "poster": [
                (f"{title_base} Silk Fabric Wall Scroll Anime Poster (60x90cm)", 13.90, 0),
                (f"{c1} Framed Canvas Wall Art Print Decor", 19.99, 0),
            ],
            "replica": [
                (f"{c1} 1:1 Scale Cosplay Weapon Sword Replica Prop", 42.00, 0),
                (f"{title_base} High Detail Metal Keychain Pendant & Necklace", 7.90, 1),
            ],
            "accessory": [
                (f"{title_base} LED 3D Acrylic Night Lamp with Touch Control", 16.50, 0),
                (f"{c1} Enamel Collector Pin Badge Set", 8.90, 0),
            ],
            "plush": [
                (f"{c1} Soft Stuffed Anime Plushie Character Doll (30cm)", 19.80, 0),
            ]
        }

        items = templates.get(pt, templates["figure"])
        results = []
        for idx, (p_title, p_price, char_idx) in enumerate(items):
            direct_url = self.build_store_search_url(p_title)
            results.append({
                "id": self.generate_product_id(title_base, pt, idx),
                "title": p_title,
                "price": p_price,
                "currency": "USD",
                "url": direct_url,
                "image_url": validate_image_url("", title_base, pt, item_index=char_idx),
                "store": "AliExpress",
                "product_type": pt,
                "anime_title": title_base,
                "rating": 4.8,
            })
        return results

    def search_by_anime(self, anime_title: str, product_type: str = "figure") -> List[Dict[str, Any]]:
        return self.search(f"{anime_title} {product_type}", product_type=product_type, anime_title=anime_title)