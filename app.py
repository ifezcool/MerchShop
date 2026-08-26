import os
import streamlit as st

from config import (
    get_mal_credentials,
    update_mal_credentials,
    SUPPORTED_STORES,
    PRODUCT_CATEGORIES,
)
from auth.mal_auth import authenticate_callback, get_mal_auth_url
from auth.session_manager import SessionManager
from database.models import FavoriteModel, ActivityModel, UserModel
from database.supabase_client import db_client
from services.mal_service import get_user_anime_list
from services.search_service import coordinate_search
from components.product_card import render_product_card
from components.anime_list_view import render_anime_list_view
from components.storefront import render_storefront_grid
from utils.helpers import format_price

# --- 1. Page Configuration ---
st.set_page_config(
    page_title="MyAnimeList Merchandise Finder",
    page_icon="🎌",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- 2. Process OAuth2 Callback ---
# Must execute before any UI rendering to catch redirect code from MAL
authenticate_callback()

# --- 3. Custom CSS Styling ---
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            background: linear-gradient(90deg, #3B82F6 0%, #8B5CF6 50%, #EC4899 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.2rem;
        }
        .subtitle {
            font-size: 1.05rem;
            color: #94A3B8;
            margin-bottom: 1.5rem;
        }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s ease-in-out;
        }
        .user-badge {
            background-color: #1E293B;
            border: 1px solid #334155;
            padding: 8px 12px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- 4. Sidebar: User & Filter Controls ---
with st.sidebar:
    st.markdown("## 🎌 **Merch Finder**")
    
    current_username = SessionManager.get_current_username()
    is_logged_in = SessionManager.is_authenticated()
    creds = get_mal_credentials()
    has_credentials = bool(creds["client_id"])

    # User Profile / Status Display
    if is_logged_in:
        auth_type = "OAuth User" if SessionManager.is_oauth_authenticated() else ("Demo Mode" if st.session_state.get("is_demo_mode") else "Public Profile")
        st.markdown(
            f"""
            <div class="user-badge">
                <div style="font-size: 11px; color: #38BDF8; font-weight: bold; text-transform: uppercase;">{auth_type}</div>
                <div style="font-size: 16px; font-weight: 700; color: #F8FAFC;">{current_username}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("🚪 Disconnect / Switch User", use_container_width=True):
            SessionManager.clear_session()
            st.rerun()
    else:
        st.info("💡 Not connected. Log in, enter a MAL username, or use Demo Mode.")

    st.divider()

    # Anime Watch Status Filter
    st.markdown("### 📋 Watchlist Filter")
    status_filter = st.selectbox(
        "Watch Status",
        ["All", "Watching", "Completed", "Plan_to_Watch", "On_Hold", "Dropped"],
        index=0,
    )

    st.divider()

    # Store & Product Filters
    st.markdown("### 🛒 Merchandise Filters")
    store_filter = st.selectbox("Store Provider", ["All"] + SUPPORTED_STORES, index=0)
    category_filter = st.selectbox("Product Category", ["all", "figure", "clothing", "poster", "replica", "accessory", "plush"], index=0)
    sort_filter = st.selectbox("Sort By", ["Best Match", "Price: Low to High", "Price: High to Low", "Top Rated"], index=0)
    max_price = st.slider("Max Price (USD)", min_value=5.0, max_value=300.0, value=150.0, step=5.0)

    st.divider()
    st.caption(f"💾 Storage: **{db_client.get_provider_name()}**")


# --- 5. Main Header ---
st.markdown('<div class="main-header">🎌 MyAnimeList Merchandise Finder</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Turn your anime watchlist into a curated shopping storefront across AliExpress, Amazon, and eBay.</div>',
    unsafe_allow_html=True,
)


# --- 6. Authentication & Connection Bar (If Not Connected) ---
if not is_logged_in:
    auth_col1, auth_col2, auth_col3 = st.columns([1.2, 1.2, 1])

    with auth_col1:
        with st.expander("🔑 **Connect MyAnimeList Account (OAuth)**", expanded=has_credentials):
            if has_credentials:
                auth_url = get_mal_auth_url()
                st.markdown(
                    f"""
                    <a href="{auth_url}" target="_self" style="text-decoration: none;">
                        <div style="background-color: #2E51A2; color: white; text-align: center; padding: 10px; border-radius: 8px; font-weight: 700; margin: 10px 0;">
                            🔗 Log in with MyAnimeList
                        </div>
                    </a>
                    """,
                    unsafe_allow_html=True,
                )
                st.caption("Standard OAuth2 flow: Log in securely on MAL to sync your private watchlist.")
            else:
                st.warning("⚠️ MAL Client ID not configured yet. See '⚙️ Settings' tab to enter credentials.")

    with auth_col2:
        with st.expander("👤 **Search by MAL Username**", expanded=not has_credentials):
            input_username = st.text_input("Enter MyAnimeList username:", placeholder="e.g. chocobo, Syncro")
            if st.button("Load Public Watchlist", use_container_width=True, type="primary"):
                if input_username.strip():
                    SessionManager.set_user_session(username=input_username.strip())
                    st.toast(f"Loaded profile for **{input_username.strip()}**", icon="🎌")
                    st.rerun()
                else:
                    st.error("Please enter a username.")

    with auth_col3:
        with st.expander("⚡ **Instant Demo Mode**", expanded=True):
            st.write("Test the storefront immediately with popular anime:")
            if st.button("🚀 Launch Demo Mode", use_container_width=True):
                SessionManager.set_user_session(username="Demo User", is_demo=True)
                st.toast("Loaded Demo Mode with curated anime watchlist!", icon="✨")
                st.rerun()

    st.divider()


# --- 7. Main Navigation Tabs ---
tab_storefront, tab_watchlist, tab_favorites, tab_settings = st.tabs([
    "🛍️ Merchandise Storefront",
    "📺 My Anime Watchlist",
    "❤️ Saved Favorites",
    "⚙️ App Setup & Credentials",
])


# --- TAB 1: Merchandise Storefront ---
with tab_storefront:
    # Fetch anime watchlist for current user
    filter_val = status_filter.lower() if status_filter != "All" else None
    anime_list = get_user_anime_list(status=filter_val)

    if not anime_list:
        st.info("No anime available in your list. Connect your MAL account or enter a username to browse!")
    else:
        # Search Control Box
        with st.container():
            st.markdown("#### 🔍 Select Anime to Search")
            anime_titles = [a["title"] for a in anime_list]
            
            # Default selection
            default_selection = st.session_state.get("selected_search_titles", anime_titles[:3])
            # Filter default selection to valid items
            default_selection = [t for t in default_selection if t in anime_titles]
            if not default_selection and anime_titles:
                default_selection = [anime_titles[0]]

            sel_col1, sel_col2 = st.columns([3, 1])
            with sel_col1:
                selected_titles = st.multiselect(
                    "Anime titles:",
                    options=anime_titles,
                    default=default_selection,
                    help="Select which anime to find merchandise for",
                )
            with sel_col2:
                st.write("") # alignment spacing
                search_all_btn = st.button("Search All Anime", use_container_width=True)
                if search_all_btn:
                    selected_titles = anime_titles

            # Search action button
            search_action_col1, search_action_col2 = st.columns([2, 2])
            with search_action_col1:
                execute_search = st.button("🔥 Search for Merchandise", type="primary", use_container_width=True)
            with search_action_col2:
                force_refresh = st.checkbox("Force fresh search (bypass cache)", value=False)

        st.divider()

        # Run Search if triggered or read from session
        if execute_search:
            if not selected_titles:
                st.warning("Please select at least one anime title.")
            else:
                with st.spinner("Searching e-commerce retailers for merchandise..."):
                    results = coordinate_search(
                        selected_anime_titles=selected_titles,
                        anime_status=filter_val,
                        product_type=category_filter,
                        store=store_filter,
                        force_refresh=force_refresh,
                    )
                    st.session_state.search_results = results
                    st.toast("Search complete!", icon="✅")

        # Render Storefront
        current_results = st.session_state.get("search_results", {})
        if current_results:
            render_storefront_grid(
                results_by_anime=current_results,
                store_filter=store_filter,
                category_filter=category_filter,
                sort_by=sort_filter,
                max_price=max_price,
            )
        else:
            # First-time search helper
            st.info("👆 Click **'Search for Merchandise'** to find figures, clothing, posters, and replicas for your selected anime!")


# --- TAB 2: Anime Watchlist ---
with tab_watchlist:
    st.markdown("### 📺 Your Synced Anime Watchlist")
    filter_val = status_filter.lower() if status_filter != "All" else None
    anime_list = get_user_anime_list(status=filter_val)
    
    top_col1, top_col2 = st.columns([3, 1])
    with top_col2:
        if st.button("🔄 Refresh Watchlist from MAL", use_container_width=True):
            anime_list = get_user_anime_list(status=filter_val, force_refresh=True)
            st.toast("Watchlist refreshed!", icon="✨")
            st.rerun()

    def on_single_anime_search(title: str):
        st.session_state.selected_search_titles = [title]
        with st.spinner(f"Searching merchandise for {title}..."):
            results = coordinate_search(
                selected_anime_titles=[title],
                product_type=category_filter,
                store=store_filter,
            )
            st.session_state.search_results = results
        st.toast(f"Found merch for {title}!", icon="🛍️")

    render_anime_list_view(anime_list, on_search_anime=on_single_anime_search)


# --- TAB 3: Saved Favorites ---
with tab_favorites:
    st.markdown("### ❤️ Saved Favorites & Wishlist")
    user_id = SessionManager.get_current_user_id()
    favorites = FavoriteModel.get_all(user_id)

    if not favorites:
        st.info("You haven't saved any favorites yet. Click the ❤️ icon on any product card in the Storefront to save it here!")
    else:
        # Wishlist summary stats
        total_items = len(favorites)
        total_price = sum(f.get("price") or 0.0 for f in favorites)
        
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        stat_col1.metric("Saved Items", f"{total_items}")
        stat_col2.metric("Estimated Total Cost", format_price(total_price))
        stat_col3.metric("Stores", f"{len(set(f.get('store', '') for f in favorites))}")

        st.divider()

        # Render favorites in grid
        fav_cols_per_row = 3
        for i in range(0, len(favorites), fav_cols_per_row):
            cols = st.columns(fav_cols_per_row)
            for j in range(fav_cols_per_row):
                idx = i + j
                if idx < len(favorites):
                    with cols[j]:
                        render_product_card(favorites[idx], key_suffix=f"fav_tab_{idx}")
            st.write("")


# --- TAB 4: App Setup & Credentials ---
with tab_settings:
    st.markdown("### ⚙️ MyAnimeList App Credentials & Multi-User Setup")
    
    st.markdown(
        """
        To allow **multiple users** to log in and search via your registered MyAnimeList App,
        enter your MAL Developer credentials below. They are saved in `.env` and applied immediately.
        """
    )

    current_creds = get_mal_credentials()
    
    with st.form("mal_config_form"):
        form_client_id = st.text_input(
            "MAL Client ID",
            value=current_creds["client_id"],
            placeholder="e.g. 8a3f91b7d...",
            help="Found on your MyAnimeList Developer page (Client ID)"
        )
        form_client_secret = st.text_input(
            "MAL Client Secret (Optional / Web App)",
            value=current_creds["client_secret"],
            type="password",
            placeholder="e.g. 5d92a...",
            help="Optional for PKCE public clients, required for web clients"
        )
        form_redirect_uri = st.text_input(
            "MAL App Redirect URI",
            value=current_creds["redirect_uri"] or "http://localhost:8501",
            placeholder="http://localhost:8501",
            help="Must match exactly what you registered in your MAL Developer API Config"
        )

        submitted = st.form_submit_button("💾 Save Credentials & Apply", type="primary")
        if submitted:
            update_mal_credentials(form_client_id, form_client_secret, form_redirect_uri)
            
            # Write to .env file
            try:
                env_content = f"MAL_CLIENT_ID={form_client_id.strip()}\nMAL_CLIENT_SECRET={form_client_secret.strip()}\nMAL_REDIRECT_URI={form_redirect_uri.strip()}\n"
                with open(".env", "w", encoding="utf-8") as f:
                    f.write(env_content)
                st.success("✅ Credentials saved to `.env` and applied to active session!")
            except Exception as e:
                st.warning(f"Credentials updated in runtime session (could not write .env: {e})")
            st.rerun()

    st.markdown("---")
    st.markdown("#### 📘 How to configure your MyAnimeList App (1-minute guide):")
    st.markdown(
        """
        1. Go to **[MyAnimeList API Config](https://myanimelist.net/apiconfig)**.
        2. Click **Create ID** (or edit your existing app).
        3. Fill in:
           - **App Type**: `Web` or `Other`
           - **App Redirect URL**: `http://localhost:8501` *(must match exactly)*
           - **Commercial / Non-Commercial**: Non-Commercial
        4. Copy the **Client ID** (and Client Secret if Web) and paste it into the form above.
        5. Now **any user** can click **"Log in with MyAnimeList"** on your app to connect their watchlist seamlessly!
        """
    )