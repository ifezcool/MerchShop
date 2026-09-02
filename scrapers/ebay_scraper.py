import base64
import logging
import os
import time
import urllib.parse
from typing import List, Dict, Any, Optional
import requests

from scrapers.base_scraper import BaseScraper
from utils.image_handler import validate_image_url
import config

logger = logging.getLogger(__name__)

class EbayScraper(BaseScraper):
    def __init__(self, delay: float = 0.5):
        super().__init__(store_name="eBay", delay=delay)
        self._access_token: Optional[str] = None
        self._token_expiry: float = 0.0

    def _get_access_token(self) -> Optional[str]:
        """Fetch or reuse cached eBay application access token via client credentials grant."""
        # Return cached token if valid (with 60-second buffer)
        if self._access_token and time.time() < (self._token_expiry - 60):
            return self._access_token

        client_id = getattr(config, "EBAY_CLIENT_ID", "") or os.getenv("EBAY_CLIENT_ID", "")
        client_secret = getattr(config, "EBAY_CLIENT_SECRET", "") or os.getenv("EBAY_CLIENT_SECRET", "")

        if not client_id or not client_secret:
            logger.warning("eBay API credentials not configured. Please set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env.")
            return None

        auth_raw = f"{client_id}:{client_secret}"
        auth_b64 = base64.b64encode(auth_raw.encode("utf-8")).decode("utf-8")
        headers = {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        try:
            resp = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers=headers,
                data=data,
                timeout=10,
            )
            if resp.status_code != 200:
                logger.error(f"Failed to obtain eBay OAuth token: HTTP {resp.status_code} - {resp.text}")
                return None

            token_data = resp.json()
            access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 7200)

            if not access_token:
                logger.error(f"eBay OAuth response did not contain access_token: {token_data}")
                return None

            self._access_token = access_token
            self._token_expiry = time.time() + float(expires_in)
            return self._access_token
        except Exception as e:
            logger.error(f"Exception during eBay OAuth token request: {e}")
            return None

    def build_store_search_url(self, query: str) -> str:
        """Fallback URL generator for search queries on eBay."""
        encoded = urllib.parse.quote_plus(query)
        return f"https://www.ebay.com/sch/i.html?_nkw={encoded}&_sacat=0"

    def search(self, query: str, product_type: str = "figure", anime_title: str = "") -> List[Dict[str, Any]]:
        """Search eBay Browse API for real product listings."""
        self.rate_limiter.wait("ebay")
        title_base = anime_title or query
        pt = product_type.lower()

        search_query = query.strip() if query else f"{title_base} {pt}".strip()
        if not search_query:
            return []

        token = self._get_access_token()
        if not token:
            return []

        marketplace_id = getattr(config, "EBAY_MARKETPLACE_ID", "EBAY_US") or "EBAY_US"
        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": marketplace_id,
            "Accept": "application/json",
        }
        params = {
            "q": search_query,
            "limit": 10,
        }

        try:
            resp = requests.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers=headers,
                params=params,
                timeout=10,
            )
            if resp.status_code != 200:
                logger.error(f"eBay Browse API search failed: HTTP {resp.status_code} - {resp.text}")
                return []

            data = resp.json()
            item_summaries = data.get("itemSummaries", [])
            results = []

            for item in item_summaries:
                item_id = str(item.get("itemId") or item.get("legacyItemId") or "")
                title = item.get("title", "")

                price_obj = item.get("price", {})
                try:
                    price_val = float(price_obj.get("value", 0.0))
                except (ValueError, TypeError):
                    price_val = 0.0
                currency = price_obj.get("currency", "USD")

                # Direct listing URL
                item_url = item.get("itemWebUrl") or self.build_store_search_url(title or search_query)

                # Real product photo URL passed through validator
                raw_image_url = item.get("image", {}).get("imageUrl", "")
                image_url = validate_image_url(raw_image_url, fallback_title=title_base, product_type=pt)

                # Seller rating
                seller_feedback = item.get("seller", {}).get("feedbackPercentage")
                rating = 4.8
                if seller_feedback:
                    try:
                        rating = round((float(seller_feedback) / 100.0) * 5.0, 1)
                    except (ValueError, TypeError):
                        rating = 4.8

                results.append({
                    "id": item_id,
                    "title": title,
                    "price": price_val,
                    "currency": currency,
                    "url": item_url,
                    "image_url": image_url,
                    "store": "eBay",
                    "product_type": pt,
                    "anime_title": title_base,
                    "rating": rating,
                })

            return results
        except Exception as e:
            logger.error(f"Exception during eBay search for '{search_query}': {e}")
            return []
