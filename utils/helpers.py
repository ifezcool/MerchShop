import os
import re
from pathlib import Path
from typing import Dict, Any, Optional

def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """Simple standard-library .env file parser that populates os.environ."""
    env_vars = {}
    if not env_path:
        candidates = [
            Path(".env"),
            Path(__file__).resolve().parent.parent / ".env",
            Path.cwd() / ".env"
        ]
        for p in candidates:
            if p.is_file():
                env_path = str(p)
                break

    if env_path and Path(env_path).is_file():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    env_vars[key] = val
                    if key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass
    return env_vars

def format_price(price: Optional[float], currency: str = "USD") -> str:
    """Format price nicely with currency symbol."""
    if price is None:
        return "Price on site"
    symbol = "$" if currency == "USD" else f"{currency} "
    return f"{symbol}{price:.2f}"

def sanitize_filename(name: str) -> str:
    """Sanitize string for safe filenames."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()
