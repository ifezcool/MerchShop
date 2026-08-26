import os
import json
import sqlite3
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

DATA_DIR = Path(__file__).resolve().parent.parent / ".data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "merchshop.db"


def get_connection():
    """Get a SQLite connection with row factory enabled."""
    conn = sqlite3.connect(str(DB_PATH), timeout=10.0)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize local SQLite database tables matching the project architecture."""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                mal_username TEXT UNIQUE,
                mal_user_id INTEGER UNIQUE,
                access_token TEXT,
                refresh_token TEXT,
                created_at REAL,
                last_login REAL
            )
        """)

        # anime_lists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anime_lists (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                mal_anime_id INTEGER,
                anime_title TEXT,
                anime_image_url TEXT,
                watch_status TEXT,
                score INTEGER,
                last_synced REAL,
                UNIQUE(user_id, mal_anime_id)
            )
        """)

        # products
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                anime_id INTEGER,
                anime_title TEXT,
                product_title TEXT,
                product_url TEXT,
                image_url TEXT,
                price REAL,
                currency TEXT DEFAULT 'USD',
                store TEXT,
                product_type TEXT,
                asin_or_product_id TEXT,
                last_updated REAL,
                is_available INTEGER DEFAULT 1,
                UNIQUE(store, asin_or_product_id)
            )
        """)

        # search_cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_cache (
                id TEXT PRIMARY KEY,
                anime_title TEXT,
                store TEXT,
                product_type TEXT,
                search_query TEXT,
                results_json TEXT,
                cached_at REAL,
                expires_at REAL,
                UNIQUE(anime_title, store, product_type)
            )
        """)

        # user_favorites
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_favorites (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                product_id TEXT,
                product_title TEXT,
                product_url TEXT,
                image_url TEXT,
                price REAL,
                currency TEXT DEFAULT 'USD',
                store TEXT,
                anime_title TEXT,
                product_type TEXT,
                favorited_at REAL,
                UNIQUE(user_id, product_id)
            )
        """)

        # user_activity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                id TEXT PRIMARY KEY,
                user_id TEXT,
                product_id TEXT,
                action_type TEXT,
                details TEXT,
                timestamp REAL
            )
        """)

        conn.commit()


# Initialize database on module import
init_db()


class LocalDB:
    """Local SQLite-backed database manager providing CRUD operations."""

    @staticmethod
    def upsert_user(username: str, user_id: Optional[int] = None, access_token: str = "", refresh_token: str = "") -> Dict[str, Any]:
        uid = f"user_{username.lower()}"
        now = time.time()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (id, mal_username, mal_user_id, access_token, refresh_token, created_at, last_login)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mal_username) DO UPDATE SET
                    mal_user_id = COALESCE(excluded.mal_user_id, users.mal_user_id),
                    access_token = CASE WHEN excluded.access_token != '' THEN excluded.access_token ELSE users.access_token END,
                    refresh_token = CASE WHEN excluded.refresh_token != '' THEN excluded.refresh_token ELSE users.refresh_token END,
                    last_login = excluded.last_login
            """, (uid, username, user_id, access_token, refresh_token, now, now))
            conn.commit()
            return {"id": uid, "mal_username": username, "mal_user_id": user_id}

    @staticmethod
    def get_user(username: str) -> Optional[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(mal_username) = ?", (username.lower(),))
            row = cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    def save_anime_list(user_id: str, anime_list: List[Dict[str, Any]]):
        now = time.time()
        with get_connection() as conn:
            cursor = conn.cursor()
            for a in anime_list:
                item_id = f"{user_id}_{a.get('mal_id')}"
                cursor.execute("""
                    INSERT INTO anime_lists (id, user_id, mal_anime_id, anime_title, anime_image_url, watch_status, score, last_synced)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, mal_anime_id) DO UPDATE SET
                        anime_title = excluded.anime_title,
                        anime_image_url = excluded.anime_image_url,
                        watch_status = excluded.watch_status,
                        score = excluded.score,
                        last_synced = excluded.last_synced
                """, (
                    item_id,
                    user_id,
                    a.get("mal_id"),
                    a.get("title", ""),
                    a.get("image_url", ""),
                    a.get("watch_status", "watching"),
                    a.get("score"),
                    now
                ))
            conn.commit()

    @staticmethod
    def get_anime_list(user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            if status and status.lower() != "all":
                cursor.execute("""
                    SELECT mal_anime_id as mal_id, anime_title as title, anime_image_url as image_url, watch_status, score
                    FROM anime_lists WHERE user_id = ? AND LOWER(watch_status) = ?
                    ORDER BY anime_title ASC
                """, (user_id, status.lower()))
            else:
                cursor.execute("""
                    SELECT mal_anime_id as mal_id, anime_title as title, anime_image_url as image_url, watch_status, score
                    FROM anime_lists WHERE user_id = ?
                    ORDER BY anime_title ASC
                """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_cached_search(anime_title: str, store: str = "all", product_type: str = "all") -> Optional[List[Dict[str, Any]]]:
        now = time.time()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT results_json FROM search_cache
                WHERE LOWER(anime_title) = ? AND LOWER(store) = ? AND LOWER(product_type) = ? AND expires_at > ?
            """, (anime_title.lower(), store.lower(), product_type.lower(), now))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row["results_json"])
                except Exception:
                    return None
            return None

    @staticmethod
    def set_cached_search(anime_title: str, store: str, product_type: str, search_query: str, results: List[Dict[str, Any]], ttl_seconds: int = 86400):
        now = time.time()
        expires = now + ttl_seconds
        cache_id = f"{anime_title.lower()}_{store.lower()}_{product_type.lower()}"
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO search_cache (id, anime_title, store, product_type, search_query, results_json, cached_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(anime_title, store, product_type) DO UPDATE SET
                    search_query = excluded.search_query,
                    results_json = excluded.results_json,
                    cached_at = excluded.cached_at,
                    expires_at = excluded.expires_at
            """, (
                cache_id,
                anime_title.lower(),
                store.lower(),
                product_type.lower(),
                search_query,
                json.dumps(results),
                now,
                expires
            ))
            conn.commit()

    @staticmethod
    def toggle_favorite(user_id: str, product: Dict[str, Any]) -> bool:
        """Toggle favorite for a user. Returns True if now favorited, False if removed."""
        prod_id = str(product.get("product_id") or product.get("id") or hash(product.get("url", "")))
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM user_favorites WHERE user_id = ? AND product_id = ?", (user_id, prod_id))
            row = cursor.fetchone()
            if row:
                cursor.execute("DELETE FROM user_favorites WHERE user_id = ? AND product_id = ?", (user_id, prod_id))
                conn.commit()
                return False
            else:
                fav_id = f"{user_id}_{prod_id}"
                cursor.execute("""
                    INSERT INTO user_favorites (
                        id, user_id, product_id, product_title, product_url, image_url, price, currency, store, anime_title, product_type, favorited_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    fav_id,
                    user_id,
                    prod_id,
                    product.get("title", "Product"),
                    product.get("url", ""),
                    product.get("image_url", ""),
                    product.get("price"),
                    product.get("currency", "USD"),
                    product.get("store", "Store"),
                    product.get("anime_title", ""),
                    product.get("product_type", "merchandise"),
                    time.time()
                ))
                conn.commit()
                return True

    @staticmethod
    def is_favorite(user_id: str, product_id: str) -> bool:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM user_favorites WHERE user_id = ? AND product_id = ?", (user_id, str(product_id)))
            return cursor.fetchone() is not None

    @staticmethod
    def get_favorites(user_id: str) -> List[Dict[str, Any]]:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT product_id, product_title as title, product_url as url, image_url, price, currency, store, anime_title, product_type, favorited_at
                FROM user_favorites WHERE user_id = ?
                ORDER BY favorited_at DESC
            """, (user_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def log_activity(user_id: str, action_type: str, product_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        import uuid
        now = time.time()
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO user_activity (id, user_id, product_id, action_type, details, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                user_id,
                product_id,
                action_type,
                json.dumps(details or {}),
                now
            ))
            conn.commit()
