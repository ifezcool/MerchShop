import streamlit as st
from typing import List, Dict, Any
from components.product_card import render_product_card

def render_storefront_grid(
    results_by_anime: Dict[str, List[Dict[str, Any]]],
    store_filter: str = "All",
    category_filter: str = "all",
    sort_by: str = "Best Match",
    max_price: float = 200.0,
):
    """Render the main storefront product grid grouped by anime with filters applied."""
    if not results_by_anime:
        st.info("👋 Select anime from your list above and click **'Search for Merchandise'** to browse products!")
        return

    total_products_displayed = 0

    for anime_title, products in results_by_anime.items():
        # Apply store filter
        filtered = products
        if store_filter.lower() != "all":
            filtered = [p for p in filtered if p.get("store", "").lower() == store_filter.lower()]

        # Apply category filter
        if category_filter.lower() != "all":
            filtered = [p for p in filtered if p.get("product_type", "").lower() == category_filter.lower()]

        # Apply price filter
        filtered = [p for p in filtered if (p.get("price") is None or p.get("price") <= max_price)]

        # Sorting
        if sort_by == "Price: Low to High":
            filtered.sort(key=lambda x: x.get("price") if x.get("price") is not None else float("inf"))
        elif sort_by == "Price: High to Low":
            filtered.sort(key=lambda x: x.get("price") if x.get("price") is not None else -1, reverse=True)
        elif sort_by == "Top Rated":
            filtered.sort(key=lambda x: x.get("rating", 0), reverse=True)

        if not filtered:
            continue

        total_products_displayed += len(filtered)

        st.markdown(f"### 🎯 {anime_title}")
        st.caption(f"Showing {len(filtered)} items")

        # 3-column product grid
        cols_per_row = 3
        for i in range(0, len(filtered), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                idx = i + j
                if idx < len(filtered):
                    with cols[j]:
                        render_product_card(filtered[idx], key_suffix=f"{anime_title[:10]}_{idx}")
            st.write("")  # Spacing between rows

        st.divider()

    if total_products_displayed == 0:
        st.warning("No products match the selected filters. Try widening your price range or selecting 'All' stores/categories.")
