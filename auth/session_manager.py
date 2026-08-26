import streamlit as st
from typing import Optional, Dict, Any

class SessionManager:
    """Manages the user's active session state in Streamlit."""

    @staticmethod
    def get_current_user_id() -> str:
        """Returns the active user's identifier for caching/favorites."""
        if "mal_username" in st.session_state and st.session_state.mal_username:
            return f"user_{st.session_state.mal_username.lower()}"
        return "guest_user"

    @staticmethod
    def get_current_username() -> str:
        """Returns the display name of the current user."""
        return st.session_state.get("mal_username", "Guest")

    @staticmethod
    def is_authenticated() -> bool:
        """Returns True if the user is authenticated via OAuth or has loaded an anime list."""
        return (
            bool(st.session_state.get("mal_access_token"))
            or bool(st.session_state.get("mal_username"))
            or bool(st.session_state.get("is_demo_mode"))
        )

    @staticmethod
    def is_oauth_authenticated() -> bool:
        """Returns True if user logged in via MAL OAuth."""
        return bool(st.session_state.get("mal_access_token"))

    @staticmethod
    def set_user_session(
        username: str,
        user_id: Optional[int] = None,
        access_token: Optional[str] = None,
        refresh_token: Optional[str] = None,
        is_demo: bool = False
    ):
        """Set user session information in Streamlit."""
        st.session_state.mal_username = username
        st.session_state.mal_user_id = user_id
        if access_token:
            st.session_state.mal_access_token = access_token
        if refresh_token:
            st.session_state.mal_refresh_token = refresh_token
        st.session_state.is_demo_mode = is_demo

    @staticmethod
    def clear_session():
        """Log out / clear current user session."""
        keys_to_clear = [
            "mal_access_token",
            "mal_refresh_token",
            "mal_username",
            "mal_user_id",
            "is_demo_mode",
            "cached_anime_list",
            "search_results"
        ]
        for key in keys_to_clear:
            st.session_state.pop(key, None)
