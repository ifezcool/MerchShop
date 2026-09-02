import unittest
from unittest.mock import patch, MagicMock
import time
import config
from scrapers.ebay_scraper import EbayScraper

class TestEbayScraperComprehensive(unittest.TestCase):
    def setUp(self):
        self.scraper = EbayScraper()
        config.EBAY_CLIENT_ID = "test_client_id"
        config.EBAY_CLIENT_SECRET = "test_client_secret"
        config.EBAY_MARKETPLACE_ID = "EBAY_US"

    @patch("requests.post")
    @patch("requests.get")
    def test_search_full_flow(self, mock_get, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "access_token": "token_abc_123",
            "expires_in": 7200,
            "token_type": "Application Access Token"
        }
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {
            "itemSummaries": [
                {
                    "itemId": "v1|111|0",
                    "title": "Demon Slayer Tanjiro Figure",
                    "price": {"value": "39.99", "currency": "USD"},
                    "itemWebUrl": "https://www.ebay.com/itm/111",
                    "image": {"imageUrl": "https://i.ebayimg.com/00/s/tanjiro.jpg"},
                    "seller": {"feedbackPercentage": "98.8"}
                },
                {
                    # Missing image and seller rating
                    "itemId": "v1|222|0",
                    "title": "Demon Slayer Hoodie",
                    "price": {"value": "25.00", "currency": "USD"},
                    "itemWebUrl": "https://www.ebay.com/itm/222"
                }
            ]
        }
        mock_get.return_value = mock_get_resp

        results = self.scraper.search("Demon Slayer figure", product_type="figure", anime_title="Demon Slayer")

        self.assertEqual(len(results), 2)
        
        # Check Item 1
        self.assertEqual(results[0]["id"], "v1|111|0")
        self.assertEqual(results[0]["url"], "https://www.ebay.com/itm/111")
        self.assertEqual(results[0]["image_url"], "https://i.ebayimg.com/00/s/tanjiro.jpg")
        self.assertEqual(results[0]["price"], 39.99)
        self.assertEqual(results[0]["currency"], "USD")
        self.assertEqual(results[0]["store"], "eBay")
        self.assertEqual(results[0]["rating"], 4.9)

        # Check Item 2 (fallback image and default rating)
        self.assertEqual(results[1]["id"], "v1|222|0")
        self.assertEqual(results[1]["url"], "https://www.ebay.com/itm/222")
        self.assertTrue(len(results[1]["image_url"]) > 0)
        self.assertEqual(results[1]["price"], 25.00)
        self.assertEqual(results[1]["rating"], 4.8)

        # Verify headers passed to GET request
        call_headers = mock_get.call_args[1]["headers"]
        self.assertEqual(call_headers["Authorization"], "Bearer token_abc_123")
        self.assertEqual(call_headers["X-EBAY-C-MARKETPLACE-ID"], "EBAY_US")

    @patch("requests.post")
    def test_token_expiry_and_refresh(self, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "access_token": "token_1",
            "expires_in": 10, # expires almost immediately
            "token_type": "Application Access Token"
        }
        mock_post.return_value = mock_post_resp

        token1 = self.scraper._get_access_token()
        self.assertEqual(token1, "token_1")
        self.assertEqual(mock_post.call_count, 1)

        # Force token expiry
        self.scraper._token_expiry = time.time() - 10

        mock_post_resp2 = MagicMock()
        mock_post_resp2.status_code = 200
        mock_post_resp2.json.return_value = {
            "access_token": "token_2",
            "expires_in": 7200,
            "token_type": "Application Access Token"
        }
        mock_post.return_value = mock_post_resp2

        token2 = self.scraper._get_access_token()
        self.assertEqual(token2, "token_2")
        self.assertEqual(mock_post.call_count, 2)

    def test_empty_credentials_graceful(self):
        config.EBAY_CLIENT_ID = ""
        config.EBAY_CLIENT_SECRET = ""
        scraper = EbayScraper()
        results = scraper.search("Demon Slayer figure")
        self.assertEqual(results, [])

    @patch("requests.post")
    @patch("requests.get")
    def test_search_api_http_error_graceful(self, mock_get, mock_post):
        mock_post_resp = MagicMock()
        mock_post_resp.status_code = 200
        mock_post_resp.json.return_value = {
            "access_token": "valid_token",
            "expires_in": 7200,
        }
        mock_post.return_value = mock_post_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 500
        mock_get_resp.text = "Internal Server Error"
        mock_get.return_value = mock_get_resp

        config.EBAY_CLIENT_ID = "valid_id"
        config.EBAY_CLIENT_SECRET = "valid_secret"

        results = self.scraper.search("Demon Slayer")
        self.assertEqual(results, [])

if __name__ == "__main__":
    unittest.main()
