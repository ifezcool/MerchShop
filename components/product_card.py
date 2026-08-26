import streamlit as st
from typing import Dict, Any
from database.models import FavoriteModel, ActivityModel
from auth.session_manager import SessionManager
from utils.helpers import format_price

STORE_COLORS = {
    "AliExpress": "#FF4747",
    "Amazon": "#FF9900",
    "eBay": "#0064D2",
    "Etsy": "#F1641E",
    "Crunchyroll": "#F47521",
}

def render_product_card(product: Dict[str, Any], key_suffix: str = ""):
    """Render a clean, responsive product card with action buttons."""
    user_id = SessionManager.get_current_user_id()
    prod_id = str(product.get("id") or product.get("product_id") or hash(product.get("url", "")))
    is_fav = FavoriteModel.is_fav(user_id, prod_id)
    store = product.get("store", "Store")
    store_color = STORE_COLORS.get(store, "#6366F1")

    with st.container():
        # Store badge & Product type
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="background-color: {store_color}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">
                    {store}
                </span>
                <span style="color: #94A3B8; font-size: 11px; text-transform: uppercase;">
                    {product.get('product_type', 'item')}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Image
        img_url = product.get("image_url") or "https://placehold.co/400x400/1E293B/FFFFFF/png?text=Anime+Merch"
        st.image(img_url, use_column_width=True)

        # Title
        title = product.get("title", "Anime Merchandise")
        display_title = title if len(title) <= 55 else f"{title[:52]}..."
        st.markdown(f"**{display_title}**", help=title)

        # Price and Rating
        price_text = format_price(product.get("price"), product.get("currency", "USD"))
        rating = product.get("rating", 4.8)
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 4px 0 10px 0;">
                <span style="font-size: 18px; font-weight: 700; color: #10B981;">{price_text}</span>
                <span style="font-size: 12px; color: #F59E0B;">⭐ {rating:.1f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action buttons: Favorite + Store Link
        btn_col1, btn_col2 = st.columns([1, 2])
        
        with btn_col1:
            fav_icon = "❤️" if is_fav else "🤍"
            btn_key = f"fav_{prod_id}_{key_suffix}"
            if st.button(fav_icon, key=btn_key, help="Save to Favorites", use_container_width=True):
                new_state = FavoriteModel.toggle(user_id, product)
                ActivityModel.log(user_id, "favorited" if new_state else "unfavorited", prod_id, product)
                st.rerun()

        with btn_col2:
            url = product.get("url") or "#"
            st.link_button(f"Buy on {store}", url, use_container_width=True)
