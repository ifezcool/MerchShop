import os
from typing import Optional, Any
from database.local_db import LocalDB
from config import SUPABASE_URL, SUPABASE_KEY

class DatabaseClient:
    """Database client that seamlessly routes to Supabase when configured or uses LocalDB."""
    def __init__(self):
        self.supabase_url = SUPABASE_URL or os.getenv("SUPABASE_URL", "")
        self.supabase_key = SUPABASE_KEY or os.getenv("SUPABASE_KEY", "")
        self.client: Optional[Any] = None
        self.is_supabase_connected = False

        if self.supabase_url and self.supabase_key:
            try:
                # If supabase-py is installed, attempt client initialization
                from supabase import create_client
                self.client = create_client(self.supabase_url, self.supabase_key)
                self.is_supabase_connected = True
            except Exception:
                self.is_supabase_connected = False

    def get_provider_name(self) -> str:
        return "Supabase (PostgreSQL)" if self.is_supabase_connected else "Local SQLite Database"

db_client = DatabaseClient()
