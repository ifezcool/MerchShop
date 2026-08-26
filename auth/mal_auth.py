import os
import secrets
import time
import urllib.parse
from typing import Dict, Any, Optional, Tuple
import requests
import streamlit as st

from config import get_mal_credentials, BASE_DIR
from database.models import UserModel
from auth.session_manager import SessionManager

AUTHORIZE_URL = "https://myanimelist.net/v1/oauth2/authorize"
TOKEN_URL = "https://myanimelist.net/v1/oauth2/token"
USER_ME_URL = "https://api.myanimelist.net/v2/users/@me"

# Server-side PKCE state store: state -> (code_verifier, timestamp)
_PKCE_STORAGE: Dict[str, Tuple[str, float]] = {}


def generate_code_verifier() -> str:
    """Generate a random 128-character URL-safe PKCE code verifier."""
    token = secrets.token_urlsafe(96)
    return token[:128]


def get_mal_auth_url(custom_redirect_uri: Optional[str] = None) -> str:
    """Generate the MAL OAuth2 authorization URL with PKCE challenge."""
    creds = get_mal_credentials()
    client_id = creds["client_id"]
    redirect_uri = custom_redirect_uri or creds["redirect_uri"]

    if not client_id:
        return "#"

    code_verifier = generate_code_verifier()
    state = secrets.token_hex(16)

    # Clean expired PKCE tokens (> 1 hour old)
    now = time.time()
    for s in list(_PKCE_STORAGE.keys()):
        if now - _PKCE_STORAGE[s][1] > 3600:
            _PKCE_STORAGE.pop(s, None)

    # Store code_verifier for this state
    _PKCE_STORAGE[state] = (code_verifier, now)

    params = {
        "response_type": "code",
        "client_id": client_id,
        "code_challenge": code_verifier,
        "code_challenge_method": "plain",
        "state": state,
        "redirect_uri": redirect_uri,
    }
    return f"{AUTHORIZE_URL}?{urllib.parse.urlencode(params)}"


def exchange_code_for_token(code: str, state: Optional[str] = None, custom_redirect_uri: Optional[str] = None) -> Dict[str, Any]:
    """Exchange authorization code for an access token using stored PKCE code_verifier."""
    creds = get_mal_credentials()
    client_id = creds["client_id"]
    client_secret = creds["client_secret"]
    redirect_uri = custom_redirect_uri or creds["redirect_uri"]

    # Retrieve code_verifier from PKCE storage
    code_verifier = None
    if state and state in _PKCE_STORAGE:
        code_verifier, _ = _PKCE_STORAGE.pop(state)
    elif _PKCE_STORAGE:
        # Fallback to most recent verifier
        most_recent_state = list(_PKCE_STORAGE.keys())[-1]
        code_verifier, _ = _PKCE_STORAGE.pop(most_recent_state)
    else:
        # If storage missing (e.g. server restarted), generate a placeholder
        code_verifier = generate_code_verifier()

    data = {
        "client_id": client_id,
        "grant_type": "authorization_code",
        "code": code,
        "code_verifier": code_verifier,
        "redirect_uri": redirect_uri,
    }
    if client_secret:
        data["client_secret"] = client_secret

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "MyAnimeListMerchFinder/1.0",
    }

    resp = requests.post(TOKEN_URL, data=data, headers=headers, timeout=15)
    if resp.status_code != 200:
        error_msg = f"MAL Token Error ({resp.status_code}): {resp.text}"
        raise ValueError(error_msg)
    return resp.json()


def fetch_mal_user_profile(access_token: str) -> Dict[str, Any]:
    """Fetch profile info of the currently authenticated MAL user."""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "User-Agent": "MyAnimeListMerchFinder/1.0",
    }
    resp = requests.get(USER_ME_URL, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json()


def authenticate_callback():
    """Check and process the OAuth2 redirect callback parameters in Streamlit."""
    query_params = getattr(st, "query_params", None)
    if query_params is None:
        try:
            query_params = st.experimental_get_query_params()
        except Exception:
            query_params = {}

    code = None
    state = None
    
    if hasattr(query_params, "get"):
        raw_code = query_params.get("code")
        raw_state = query_params.get("state")
        code = raw_code[0] if isinstance(raw_code, list) else raw_code
        state = raw_state[0] if isinstance(raw_state, list) else raw_state

    if code:
        try:
            token_data = exchange_code_for_token(code, state)
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")

            # Get user info from MAL
            profile = fetch_mal_user_profile(access_token)
            username = profile.get("name", "MAL_User")
            user_id = profile.get("id")

            # Save in database
            UserModel.upsert(username, user_id, access_token, refresh_token)

            # Set session
            SessionManager.set_user_session(
                username=username,
                user_id=user_id,
                access_token=access_token,
                refresh_token=refresh_token
            )

            # Clear query params
            if hasattr(st, "query_params") and hasattr(st.query_params, "clear"):
                st.query_params.clear()
            elif hasattr(st, "experimental_set_query_params"):
                st.experimental_set_query_params()

            st.toast(f"🎉 Successfully logged in as **{username}**!", icon="✅")
            st.rerun()
        except Exception as e:
            st.error(f"Authentication failed: {e}")