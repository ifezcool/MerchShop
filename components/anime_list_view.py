import streamlit as st
from typing import List, Dict, Any, Callable, Optional

STATUS_COLORS = {
    "watching": "🟢 Watching",
    "completed": "🔵 Completed",
    "plan_to_watch": "🟡 Plan to Watch",
    "on_hold": "🟠 On Hold",
    "dropped": "🔴 Dropped",
}

def render_anime_list_view(
    anime_list: List[Dict[str, Any]],
    on_search_anime: Optional[Callable[[str], None]] = None
):
    """Render anime library view with metadata and instant merch search buttons."""
    if not anime_list:
        st.info("No anime in this category. Try switching the status filter or connecting your MAL account.")
        return

    st.markdown(f"**Found {len(anime_list)} anime titles**")
    
    # 4-column grid for anime library
    cols_per_row = 4
    for i in range(0, len(anime_list), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            idx = i + j
            if idx < len(anime_list):
                anime = anime_list[idx]
                with cols[j]:
                    with st.container():
                        img_url = anime.get("image_url") or "https://placehold.co/225x320/1E293B/FFFFFF/png?text=Anime"
                        st.image(img_url, use_container_width=True)
                        
                        title = anime.get("title", "Untitled")
                        st.markdown(f"**{title}**")
                        
                        status = anime.get("watch_status", "watching").lower()
                        status_label = STATUS_COLORS.get(status, status.title())
                        score = anime.get("score")
                        score_label = f"⭐ {score}/10" if score else "⭐ Unrated"
                        
                        st.caption(f"{status_label} • {score_label}")
                        
                        btn_key = f"search_anime_{anime.get('mal_id', idx)}"
                        if st.button("🔎 Find Merch", key=btn_key, use_container_width=True):
                            if on_search_anime:
                                on_search_anime(title)
                            else:
                                st.session_state.selected_search_titles = [title]
                                st.session_state.active_tab = "Storefront"
                                st.rerun()
