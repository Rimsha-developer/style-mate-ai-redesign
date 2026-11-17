"""Style Mate AI - Fashion Catalog View (Step 3: Fashion Catalog & Brand Exploration)
Premium editorial browsing interface for the pre-existing 720-garment fashion catalog.

Features:
- Accesses original 720 catalog garments and images from catalog/
- Clear separation from personal wardrobe (does not pollute user wardrobe)
- Filter by category slot, gender/demographic, occasion, color, and product ID search
- Responsive pagination for high-performance browsing
- "Add to My Wardrobe" action to copy any catalog piece into personal wardrobe
- High-resolution editorial garment inspection
"""

import os
import math
from pathlib import Path
import streamlit as st
from PIL import Image

from services import ai_service
from ui.components.navigation import navigate_to
from ui.components.image_renderer import render_crisp_garment_html, render_inspector_garment_html

CATEGORY_FILTERS = [
    ("all", "All Items"),
    ("top", "Tops"),
    ("bottom", "Bottoms"),
    ("dress", "Dresses"),
    ("outer", "Outerwear"),
    ("shoes", "Shoes"),
    ("bag", "Handbags"),
]

COLOR_HEX_MAP = {
    "black": "#1C1917",
    "white": "#F7F4EE",
    "gray": "#78716C",
    "red": "#DC2626",
    "orange": "#EA580C",
    "beige": "#D6C7B2",
    "navy": "#1E3A8A",
    "blue": "#2563EB",
    "denim": "#3B82F6",
    "green": "#16A34A",
    "yellow": "#CA8A04",
    "pink": "#DB2777",
    "purple": "#7C3AED",
    "teal": "#0D9488",
}


def _render_catalog_card(item: dict, col, index: int):
    """Render a single product card in the catalog grid."""
    item_id = item["id"]
    item_type = item.get("type", "Garment")
    slot_title = item.get("slot_title", "Category")
    usage = item.get("usage", "Casual")
    gender = item.get("gender", "Unisex")
    color_name = str(item.get("color", "unknown")).title()
    hex_color = COLOR_HEX_MAP.get(str(item.get("color", "")).lower(), "#8C827A")
    file_path = item.get("path", "")
    file_exists = item.get("file_exists", False)

    with col:
        # Crisp Garment Image (Lanczos super-sampled, crisp-edges, zero stretch)
        st.markdown(
            render_crisp_garment_html(file_path, max_height=210, max_width=170, bg_color="#FFFFFF", container_height=220),
            unsafe_allow_html=True
        )

        # Metadata Block
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid #E8E3DA;border-radius:10px;padding:12px 14px;margin:6px 0 10px 0;">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
                    <span style="font-family:'Cinzel',serif;font-size:10px;letter-spacing:0.14em;color:#9A6B43;text-transform:uppercase;font-weight:700;">
                        {slot_title} · {gender}
                    </span>
                    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:10px;color:#8C827A;font-weight:600;">
                        #{item_id}
                    </span>
                </div>
                <div style="font-family:'Cinzel',serif;font-size:15px;font-weight:700;color:#1C1917;margin-bottom:8px;">
                    {item_type}
                </div>
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                    <span style="display:inline-flex;align-items:center;gap:4px;background:#F7F4EE;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#57534E;">
                        <span style="width:8px;height:8px;border-radius:50%;background:{hex_color};display:inline-block;border:1px solid rgba(0,0,0,0.15);"></span>
                        {color_name}
                    </span>
                    <span style="background:#F7F4EE;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#57534E;">
                        {usage}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Action Buttons
        b1, b2 = st.columns([1, 1], gap="small")
        with b1:
            if st.button("Inspect", key=f"cat_insp_{item_id}_{index}", use_container_width=True):
                st.session_state["selected_catalog_item"] = item
                st.rerun()
        with b2:
            if st.button("➕ Wardrobe", key=f"cat_add_{item_id}_{index}", use_container_width=True):
                try:
                    ai_service.add_catalog_item_to_wardrobe(
                        catalog_item_path=file_path,
                        type_name=item_type,
                        slot=item.get("slot", "top"),
                        usage=usage,
                        gender=item.get("gender", "Unisex")
                    )
                    st.success(f"Added #{item_id} to Wardrobe!")
                except Exception as e:
                    st.error(f"Error adding: {e}")


def _render_catalog_inspector(item: dict):
    """Detailed inspection modal/card for a selected catalog piece."""
    item_id = item["id"]
    item_type = item.get("type", "Garment")
    slot_title = item.get("slot_title", "Category")
    usage = item.get("usage", "Casual")
    gender = item.get("gender", "Unisex")
    color_name = str(item.get("color", "unknown")).title()
    hex_color = COLOR_HEX_MAP.get(str(item.get("color", "")).lower(), "#8C827A")
    file_path = item.get("path", "")
    neutral = item.get("neutral", False)

    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid #9A6B43;border-radius:14px;padding:24px 28px;margin-bottom:28px;box-shadow:0 8px 30px rgba(74,46,24,0.08);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <span style="font-family:'Cinzel',serif;font-size:12px;letter-spacing:0.18em;color:#9A6B43;text-transform:uppercase;font-weight:700;">
                    ✦ CATALOG PIECE INSPECTOR
                </span>
            </div>
        """,
        unsafe_allow_html=True
    )

    col_img, col_info = st.columns([1, 1.4], gap="large")

    with col_img:
        st.markdown(
            render_inspector_garment_html(file_path, max_height=340, max_width=260, bg_color="#FFFFFF"),
            unsafe_allow_html=True
        )

    with col_info:
        st.markdown(
            f"""
            <div style="font-family:'Cinzel',serif;font-size:26px;font-weight:700;color:#1C1917;margin-bottom:4px;">
                {item_type}
            </div>
            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#8C827A;margin-bottom:18px;">
                Product ID: <strong>#{item_id}</strong> · Category: <strong style="color:#4A2E18;">{slot_title}</strong> · Demographic: <strong>{gender}</strong>
            </div>

            <!-- Color Palette -->
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:12px 14px;background:#FAF8F5;border-radius:8px;border:1px solid #E8E3DA;">
                <div style="width:36px;height:36px;border-radius:6px;background:{hex_color};border:1px solid rgba(0,0,0,0.12);"></div>
                <div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;font-size:14px;color:#1C1917;">
                        {color_name}{' · Neutral' if neutral else ''}
                    </div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:#8C827A;">
                        Occasion: {usage}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        b_add, b_close = st.columns([1.2, 1], gap="small")
        with b_add:
            if st.button("➕  Save Piece to My Wardrobe", key=f"insp_cat_add_{item_id}", type="primary", use_container_width=True):
                try:
                    ai_service.add_catalog_item_to_wardrobe(
                        catalog_item_path=file_path,
                        type_name=item_type,
                        slot=item.get("slot", "top"),
                        usage=usage,
                        gender=item.get("gender", "Unisex")
                    )
                    st.success(f"✓ #{item_id} {item_type} successfully added to your personal wardrobe!")
                except Exception as e:
                    st.error(f"Save failed: {e}")
        with b_close:
            if st.button("Close Inspector", key=f"insp_cat_close_{item_id}", use_container_width=True):
                st.session_state.pop("selected_catalog_item", None)
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def render_catalog_view():
    """Render the luxury Fashion Catalog browsing view."""

    # 1. Header with direct switcher to Personal Wardrobe
    st.markdown(
        """
        <div style="border-bottom:1px solid #E8E3DA;padding-bottom:20px;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:14px;">
                <div>
                    <div style="font-family:'Cinzel',serif;font-size:12px;letter-spacing:0.18em;color:#9A6B43;text-transform:uppercase;margin-bottom:6px;">
                        EDITORIAL READY-TO-WEAR ARCHIVE
                    </div>
                    <h1 style="font-family:'Cinzel',serif;font-size:36px;font-weight:700;color:#1C1917;margin:0 0 6px 0;line-height:1.15;">
                        Fashion Catalog
                    </h1>
                    <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15px;color:#57534E;margin:0;">
                        Explore 720 curated apparel and footwear pieces from our verified fashion archive.
                    </p>
                </div>
                <div>
                    <span class="wardrobe-kpi-pill">
                        ✦ 720 Curated Pieces Available
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Navigation pill to Personal Wardrobe
    c_sw1, c_sw2 = st.columns([1.5, 1])
    with c_sw2:
        if st.button("🧺  Go to My Personal Wardrobe →", key="btn_go_to_personal_wd", use_container_width=True):
            navigate_to("My Wardrobe")

    # 2. Selected Inspector
    if st.session_state.get("selected_catalog_item"):
        _render_catalog_inspector(st.session_state["selected_catalog_item"])

    # 3. Filter Controls
    f_col1, f_col2, f_col3, f_col4 = st.columns([1.4, 1, 1, 1], gap="medium")

    with f_col1:
        search_query = st.text_input(
            "Search Archive",
            value=st.session_state.get("cat_search", ""),
            placeholder="Search by type (e.g. Jeans, Shoes) or ID",
            key="input_cat_search"
        )
        st.session_state["cat_search"] = search_query

    with f_col2:
        gender_options = ["All", "Men", "Women", "Unisex"]
        sel_gender = st.selectbox("Demographic", options=gender_options, index=0, key="cat_sel_gender")

    with f_col3:
        usage_options = ["All", "Casual", "Sports", "Formal", "Ethnic", "Smart Casual"]
        sel_usage = st.selectbox("Occasion", options=usage_options, index=0, key="cat_sel_usage")

    with f_col4:
        color_options = ["All", "black", "white", "gray", "red", "orange", "beige", "navy", "blue", "denim", "green", "yellow", "pink", "purple", "teal"]
        sel_color = st.selectbox("Dominant Color", options=color_options, index=0, key="cat_sel_color")

    # 4. Category Slot Tabs / Filter Buttons
    if "cat_slot_filter" not in st.session_state:
        st.session_state["cat_slot_filter"] = "all"

    curr_slot = st.session_state["cat_slot_filter"]
    slot_cols = st.columns(len(CATEGORY_FILTERS), gap="small")
    for idx, (slot_key, label) in enumerate(CATEGORY_FILTERS):
        with slot_cols[idx]:
            is_active = (curr_slot == slot_key)
            if st.button(
                label,
                key=f"cat_slot_btn_{slot_key}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                if curr_slot != slot_key:
                    st.session_state["cat_slot_filter"] = slot_key
                    st.session_state["cat_page"] = 1
                    st.rerun()

    # 5. Fetch Filtered Catalog Items
    items = ai_service.list_catalog_items(
        slot=curr_slot,
        gender=sel_gender,
        occasion=sel_usage,
        color=sel_color,
        search=search_query
    )
    total_found = len(items)

    st.markdown(
        f"""
        <div style="margin:16px 0 18px 0;display:flex;justify-content:space-between;align-items:center;">
            <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#8C827A;">
                Showing <strong>{total_found}</strong> matching garments
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    if total_found == 0:
        st.markdown(
            """
            <div class="wardrobe-empty-box">
                <div style="font-size:36px;margin-bottom:12px;">🔍</div>
                <div style="font-family:'Cinzel',serif;font-size:20px;font-weight:700;color:#1C1917;margin-bottom:8px;">
                    No Catalog Pieces Found
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#8C827A;">
                    Try adjusting your category, demographic, or color filters to discover more items.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    # 6. Pagination Controls (20 pieces per page in balanced 4-column editorial grid)
    page_size = 20
    total_pages = max(1, math.ceil(total_found / page_size))

    if "cat_page" not in st.session_state:
        st.session_state["cat_page"] = 1

    curr_page = max(1, min(st.session_state["cat_page"], total_pages))
    start_idx = (curr_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_found)
    page_items = items[start_idx:end_idx]

    # 7. Responsive Clothing Grid (Balanced 4-Column Layout)
    cols_per_row = 4
    for i in range(0, len(page_items), cols_per_row):
        row_items = page_items[i:i + cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for j, it in enumerate(row_items):
            _render_catalog_card(it, cols[j], index=start_idx + i + j)

    # 8. Pagination Navigation Footer
    st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
    p_prev, p_info, p_next = st.columns([1, 2, 1], gap="small")
    with p_prev:
        if st.button("← Previous", disabled=(curr_page <= 1), key="cat_btn_prev", use_container_width=True):
            st.session_state["cat_page"] = curr_page - 1
            st.rerun()
    with p_info:
        st.markdown(
            f"<div style='text-align:center;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:13px;color:#57534E;padding-top:6px;'>"
            f"Page <strong>{curr_page}</strong> of <strong>{total_pages}</strong> · Showing {start_idx + 1}–{end_idx} of {total_found}"
            f"</div>",
            unsafe_allow_html=True
        )
    with p_next:
        if st.button("Next →", disabled=(curr_page >= total_pages), key="cat_btn_next", use_container_width=True):
            st.session_state["cat_page"] = curr_page + 1
            st.rerun()

    st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
