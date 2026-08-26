from typing import List, Dict, Any, Optional
from database.local_db import LocalDB

class UserModel:
    @staticmethod
    def upsert(username: str, user_id: Optional[int] = None, access_token: str = "", refresh_token: str = "") -> Dict[str, Any]:
        return LocalDB.upsert_user(username, user_id, access_token, refresh_token)

    @staticmethod
    def get(username: str) -> Optional[Dict[str, Any]]:
        return LocalDB.get_user(username)


class AnimeListModel:
    @staticmethod
    def save_list(user_id: str, anime_list: List[Dict[str, Any]]):
        LocalDB.save_anime_list(user_id, anime_list)

    @staticmethod
    def get_list(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        return LocalDB.get_anime_list(user_id, status)


class SearchCacheModel:
    @staticmethod
    def get(anime_title: str, store: str = "all", product_type: str = "all") -> Optional[List[Dict[str, Any]]]:
        return LocalDB.get_cached_search(anime_title, store, product_type)

    @staticmethod
    def set(anime_title: str, store: str, product_type: str, search_query: str, results: List[Dict[str, Any]], ttl_seconds: int = 86400):
        LocalDB.set_cached_search(anime_title, store, product_type, search_query, results, ttl_seconds)


class FavoriteModel:
    @staticmethod
    def toggle(user_id: str, product: Dict[str, Any]) -> bool:
        return LocalDB.toggle_favorite(user_id, product)

    @staticmethod
    def is_fav(user_id: str, product_id: str) -> bool:
        return LocalDB.is_favorite(user_id, product_id)

    @staticmethod
    def get_all(user_id: str) -> List[Dict[str, Any]]:
        return LocalDB.get_favorites(user_id)


class ActivityModel:
    @staticmethod
    def log(user_id: str, action_type: str, product_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        LocalDB.log_activity(user_id, action_type, product_id, details)
