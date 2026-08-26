import hashlib
from typing import Optional
from services.anime_art_service import get_product_thumbnail, fetch_anime_art

def validate_image_url(url: Optional[str], fallback_title: str = "Anime Merch", product_type: str = "figure", item_index: int = 0) -> str:
    """Ensure image URL is a real high-quality image of the anime or character."""
    if url and isinstance(url, str) and url.startswith("http") and "placehold.co" not in url:
        return url
    
    # Resolve official anime/character high-resolution artwork
    real_thumb = get_product_thumbnail(fallback_title, product_type, item_index)
    if real_thumb:
        return real_thumb

    # Fallback to anime cover if available
    art = fetch_anime_art(fallback_title)
    if art.get("cover"):
        return art["cover"]

    # Final aesthetic fallback
    hash_val = int(hashlib.md5(fallback_title.encode("utf-8")).hexdigest()[:6], 16)
    bg_colors = ["1E1B4B", "0F172A", "1E293B", "312E81", "18181B"]
    bg = bg_colors[hash_val % len(bg_colors)]
    text = f"{fallback_title[:18]}+{product_type.title()}"
    return f"https://placehold.co/400x400/{bg}/FFFFFF/png?text={text}"
