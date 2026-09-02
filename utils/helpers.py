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

def update_env_file(key_values: Dict[str, str], env_path: str = ".env") -> bool:
    """Update or append specific key-value pairs in .env while preserving existing contents."""
    p = Path(env_path)
    lines = []
    if p.is_file():
        try:
            with open(p, "r", encoding="utf-8") as f:
                lines = f.readlines()
        except Exception:
            lines = []

    remaining_keys = set(key_values.keys())
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and "=" in stripped:
            k, _ = stripped.split("=", 1)
            k = k.strip()
            if k in key_values:
                new_lines.append(f"{k}={key_values[k]}\n")
                remaining_keys.discard(k)
                continue
        new_lines.append(line)

    for k in sorted(remaining_keys):
        new_lines.append(f"{k}={key_values[k]}\n")

    try:
        with open(p, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        for k, v in key_values.items():
            os.environ[k] = v
        return True
    except Exception:
        return False

