import time
from typing import Dict

class RateLimiter:
    """Thread-safe / session-friendly in-memory rate limiter."""
    def __init__(self, calls_per_second: float = 2.0):
        self.interval = 1.0 / max(0.1, calls_per_second)
        self._last_call_time: Dict[str, float] = {}

    def wait(self, key: str = "default") -> None:
        """Wait if needed before allowing the next API / scraper call."""
        now = time.time()
        last_time = self._last_call_time.get(key, 0.0)
        elapsed = now - last_time
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self._last_call_time[key] = time.time()

# Global default limiter for scraping and external APIs
default_limiter = RateLimiter(calls_per_second=2.0)
