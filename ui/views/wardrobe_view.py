"""Style Mate AI - Digital Wardrobe View (Phase 4, Step 3)
Premium editorial interface for managing personal curated wardrobe items.

Features:
- Reads live from wardrobe/wardrobe.json via services.ai_service
- Cross-platform path normalization
- Supported slot categories: Tops, Bottoms, Dresses, Outerwear, Shoes, Handbags
- Responsive luxury clothing gallery
- Detailed inspection panel with editing and deletion
- Direct integration with AI Studio's save-to-wardrobe flow
"""

import os
from pathlib import Path
import streamlit as st
from PIL import Image

from services import ai_service
from ui.components.navigation import navigate_to
from ui.components.image_renderer import render_crisp_garment_html, render_inspector_garment_html


# ---------------------------------------------------------------------------
# Slot Filter Definitions (Strictly based on engine.SLOT_TITLE)
# ---------------------------------------------------------------------------
CATEGORY_FILTERS = [
    ("all", "All Items"),
    ("top", "Tops"),
    ("bottom", "Bottoms"),
    ("dress", "Dresses"),
    ("outer", "Outerwear"),
    ("shoes", "Shoes"),
    ("bag", "Handbags"),
]


def _render_item_card(item: dict, col, index: int):
    """Render a single wardrobe piece card inside a Streamlit column."""
    item_id = item["id"]
    item_type = item.get("type", "Garment")
    slot_title = item.get("slot_title", "Wardrobe Piece")
    color_name = item.get("color", "Unknown").title()
    hex_color = item.get("hex", "#8C827A")
    usage = item.get("usage", "Casual")
    conf_pct = item.get("conf_pct")
    worn = item.get("worn", 0)
    file_exists = item.get("file_exists", False)
    resolved_path = item.get("resolved_path", "")

    with col:
        # 1. Garment Image (Crisp, framed showcase, zero blur/stretch)
        st.markdown(
            render_crisp_garment_html(resolved_path, max_height=210, max_width=170, bg_color="#FFFFFF", container_height=220),
            unsafe_allow_html=True
        )

        # 2. Editorial Metadata Block
        conf_badge = f'<span style="color:#9A6B43;font-size:11px;font-weight:600;">{conf_pct}%</span>' if conf_pct else ""
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px solid #E8E3DA;border-radius:10px;padding:14px 16px;margin:8px 0 12px 0;">
                <div style="font-family:'Cinzel',serif;font-size:11px;letter-spacing:0.14em;color:#9A6B43;text-transform:uppercase;font-weight:700;margin-bottom:2px;">
                    {slot_title}
                </div>
                <div style="font-family:'Cinzel',serif;font-size:16px;font-weight:700;color:#1C1917;margin-bottom:8px;">
                    {item_type}
                </div>
                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;margin-bottom:6px;">
                    <span style="display:inline-flex;align-items:center;gap:4px;background:#F7F4EE;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#57534E;">
                        <span style="width:8px;height:8px;border-radius:50%;background:{hex_color};display:inline-block;border:1px solid rgba(0,0,0,0.15);"></span>
                        {color_name}
                    </span>
                    <span style="background:#F7F4EE;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#57534E;">
                        {usage}
                    </span>
                    <span style="background:#FAF8F5;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#8C827A;">
                        {item.get('gender', 'Unisex')}
                    </span>
                    <span style="background:#FAF8F5;border:1px solid #E8E3DA;border-radius:12px;padding:2px 8px;font-size:11px;color:#8C827A;">
                        Worn {worn}×
                    </span>
                </div>
                {conf_badge}
            </div>
            """,
            unsafe_allow_html=True
        )

        # 3. Action Buttons
        b1, b2 = st.columns([1, 1], gap="small")
        with b1:
            if st.button("Inspect", key=f"insp_{item_id}", use_container_width=True):
                st.session_state["selected_wardrobe_item_id"] = item_id
                st.rerun()
        with b2:
            if st.button("Delete", key=f"del_btn_{item_id}", use_container_width=True):
                st.session_state["confirm_delete_id"] = item_id
                st.rerun()


def _render_details_inspector(selected_item: dict):
    """Render full editorial details and management panel for a selected piece."""
    item_id = selected_item["id"]
    item_type = selected_item.get("type", "Garment")
    slot = selected_item.get("slot", "top")
    slot_title = selected_item.get("slot_title", "Tops")
    color_name = selected_item.get("color", "Unknown").title()
    hex_color = selected_item.get("hex", "#8C827A")
    rgb = selected_item.get("rgb", [128, 128, 128])
    usage = selected_item.get("usage", "Casual")
    conf_pct = selected_item.get("conf_pct")
    worn = selected_item.get("worn", 0)
    file_exists = selected_item.get("file_exists", False)
    resolved_path = selected_item.get("resolved_path", "")

    st.markdown(
        """
        <div style="background:#FFFFFF;border:1px solid #9A6B43;border-radius:14px;padding:24px 28px;margin-bottom:28px;box-shadow:0 8px 30px rgba(74,46,24,0.08);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <span style="font-family:'Cinzel',serif;font-size:12px;letter-spacing:0.18em;color:#9A6B43;text-transform:uppercase;font-weight:700;">
                    ✦ GARMENT INSPECTION & MANAGEMENT
                </span>
            </div>
        """,
        unsafe_allow_html=True
    )

    d_col_img, d_col_info = st.columns([1, 1.4], gap="large")

    with d_col_img:
        st.markdown(
            render_inspector_garment_html(resolved_path, max_height=340, max_width=260, bg_color="#FFFFFF"),
            unsafe_allow_html=True
        )

    with d_col_info:
        st.markdown(
            f"""
            <div style="font-family:'Cinzel',serif;font-size:24px;font-weight:700;color:#1C1917;margin-bottom:4px;">
                {item_type}
            </div>
            <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#8C827A;margin-bottom:16px;">
                Slot: <strong style="color:#4A2E18;">{slot_title}</strong> · ID: <code>{item_id}</code> · Recorded Occasion: <strong>{usage}</strong>
            </div>

            <!-- Color Palette Row -->
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:18px;padding:12px 14px;background:#FAF8F5;border-radius:8px;border:1px solid #E8E3DA;">
                <div style="width:36px;height:36px;border-radius:6px;background:{hex_color};border:1px solid rgba(0,0,0,0.12);"></div>
                <div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:600;font-size:14px;color:#1C1917;">{color_name}</div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:#8C827A;">{hex_color.upper()} · RGB({rgb[0]}, {rgb[1]}, {rgb[2]})</div>
                </div>
            </div>

            <!-- Stats Row -->
            <div style="display:flex;gap:18px;margin-bottom:20px;">
                <div style="background:#F7F4EE;border:1px solid #E8E3DA;border-radius:8px;padding:8px 14px;text-align:center;">
                    <div style="font-size:11px;color:#8C827A;text-transform:uppercase;">Times Worn</div>
                    <div style="font-size:18px;font-weight:700;color:#4A2E18;">{worn}</div>
                </div>
                <div style="background:#F7F4EE;border:1px solid #E8E3DA;border-radius:8px;padding:8px 14px;text-align:center;">
                    <div style="font-size:11px;color:#8C827A;text-transform:uppercase;">AI Confidence</div>
                    <div style="font-size:18px;font-weight:700;color:#4A2E18;">{conf_pct if conf_pct else '—'}%</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Edit Section
        with st.expander("✎  Edit Garment Details", expanded=False):
            clf = ai_service.get_classifier()
            supported_types = list(clf.types)
            supported_usages = list(clf.usages)
            slots_map = clf.slots

            # Smart index match: exact match -> keyword match -> slot match
            if item_type in supported_types:
                curr_type_idx = supported_types.index(item_type)
            else:
                match = next((t for t in supported_types if t.lower() in item_type.lower() or item_type.lower() in t.lower()), None)
                if not match:
                    match = next((t for t in supported_types if slots_map.get(t) == slot), supported_types[0])
                curr_type_idx = supported_types.index(match)

            new_type = st.selectbox("Garment Category", options=supported_types, index=curr_type_idx, key=f"edit_type_{item_id}")

            curr_usage_idx = supported_usages.index(usage) if usage in supported_usages else 0
            new_usage = st.selectbox("Occasion", options=supported_usages, index=curr_usage_idx, key=f"edit_usage_{item_id}")

            curr_gender = selected_item.get("gender", "Unisex")
            gender_opts = ["Women", "Men", "Unisex"]
            curr_g_idx = gender_opts.index(curr_gender) if curr_gender in gender_opts else 2
            new_gender = st.selectbox("Gender Compatibility", options=gender_opts, index=curr_g_idx, key=f"edit_gender_{item_id}")

            new_slot = ai_service.resolve_garment_slot(new_type) or slots_map.get(new_type, slot)
            st.caption(f"Automatic Slot Assignment: **{engine_slot_title(new_slot)}**")

            if st.button("Save Changes", key=f"save_edit_{item_id}", type="primary"):
                ai_service.update_wardrobe_item(item_id, new_type, new_slot, new_usage, new_gender=new_gender)
                st.session_state["wardrobe_flash_message"] = ("success", f"✓ Updated {new_type} ({engine_slot_title(new_slot)}, {new_gender}) successfully!")
                st.session_state.pop("selected_wardrobe_item_id", None)
                st.rerun()

        # Action Buttons
        btn_c1, btn_c2 = st.columns([1, 1], gap="small")
        with btn_c1:
            if st.button("Close Inspector", key=f"close_{item_id}", use_container_width=True):
                st.session_state.pop("selected_wardrobe_item_id", None)
                st.rerun()
        with btn_c2:
            if st.button("🗑  Delete Piece", key=f"insp_del_{item_id}", type="secondary", use_container_width=True):
                st.session_state["confirm_delete_id"] = item_id
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def engine_slot_title(slot_key: str) -> str:
    """Helper to return human-friendly slot title from engine."""
    supported = ai_service.get_supported_slots()
    return supported.get(slot_key, slot_key.title())


# ---------------------------------------------------------------------------
# Main Digital Wardrobe View Renderer
# ---------------------------------------------------------------------------

def render_wardrobe_view():
    """Render the full luxury digital wardrobe view."""

    # 0. Flash Message Display (survives reruns)
    flash = st.session_state.pop("wardrobe_flash_message", None)
    if flash:
        m_type, m_text = flash
        if m_type == "success":
            st.success(m_text)
        elif m_type == "error":
            st.error(m_text)

    # 1. Fetch live wardrobe items
    items = ai_service.list_wardrobe_items()
    total_count = len(items)

    # 2. Handle Delete Confirmation Dialog
    if st.session_state.get("confirm_delete_id"):
        del_id = st.session_state["confirm_delete_id"]
        # Find item details
        target_item = next((it for it in items if it["id"] == del_id), None)
        target_name = f"{target_item['type']} ({target_item['slot_title']})" if target_item else f"item {del_id}"

        st.warning(f"Are you sure you want to permanently delete **{target_name}** from your wardrobe?")
        col_yes, col_no = st.columns([1, 1])
        with col_yes:
            if st.button("Yes, Delete Piece", key="conf_yes_del", type="primary", use_container_width=True):
                ok = ai_service.delete_garment_from_wardrobe(del_id)
                st.session_state.pop("confirm_delete_id", None)
                if st.session_state.get("selected_wardrobe_item_id") == del_id:
                    st.session_state.pop("selected_wardrobe_item_id", None)
                if ok:
                    st.session_state["wardrobe_flash_message"] = ("success", f"✓ Permanently removed {target_name} from your digital wardrobe.")
                else:
                    st.session_state["wardrobe_flash_message"] = ("error", f"Item {del_id} could not be located on disk.")
                st.rerun()
        with col_no:
            if st.button("Cancel", key="conf_no_del", use_container_width=True):
                st.session_state.pop("confirm_delete_id", None)
                st.rerun()

    # 3. Header Section
    st.markdown(
        f"""
        <div style="border-bottom:1px solid #E8E3DA;padding-bottom:24px;margin-bottom:20px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-end;flex-wrap:wrap;gap:14px;">
                <div>
                    <div style="font-family:'Cinzel',serif;font-size:12px;letter-spacing:0.18em;color:#9A6B43;text-transform:uppercase;margin-bottom:6px;">
                        CURATED ARCHIVE
                    </div>
                    <h1 style="font-family:'Cinzel',serif;font-size:36px;font-weight:700;color:#1C1917;margin:0 0 6px 0;line-height:1.15;">
                        My Digital Wardrobe
                    </h1>
                    <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15px;color:#57534E;margin:0;">
                        Your personal style, thoughtfully curated.
                    </p>
                </div>
                <div>
                    <span class="wardrobe-kpi-pill">
                        ✦ {total_count} {'Piece' if total_count == 1 else 'Pieces'} in Collection
                    </span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Section Switcher Banner
    sw_c1, sw_c2 = st.columns([1.5, 1.1])
    with sw_c1:
        st.markdown(
            f"<div style='padding-top:8px;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:13px;color:#8C827A;'>"
            f"Personal Collection · <strong>{total_count}</strong> saved piece{'s' if total_count != 1 else ''}"
            f"</div>",
            unsafe_allow_html=True
        )
    with sw_c2:
        if st.button("🏷️  Explore Catalog (720 Pieces) →", key="btn_switch_to_cat", use_container_width=True):
            navigate_to("Fashion Catalog")

    st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

    # 4. Check If Wardrobe is Completely Empty
    if total_count == 0:
        st.markdown(
            """
            <div class="wardrobe-empty-box">
                <div style="font-size:42px;margin-bottom:16px;">👗</div>
                <div style="font-family:'Cinzel',serif;font-size:22px;font-weight:700;color:#1C1917;margin-bottom:10px;">
                    Your Wardrobe Is Currently Empty
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;color:#8C827A;max-width:440px;margin:0 auto 24px auto;line-height:1.6;">
                    Upload and analyze single garments or full outfits in the AI Studio, or browse our 720-piece fashion catalog 
                    and click <strong>Add to Wardrobe</strong> to curate your capsule collection.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        col_emp_l, col_emp_btn1, col_emp_btn2, col_emp_r = st.columns([1, 1.2, 1.2, 1], gap="medium")
        with col_emp_btn1:
            if st.button("Open AI Studio →", key="btn_empty_to_studio", type="primary", use_container_width=True):
                navigate_to("AI Studio")
        with col_emp_btn2:
            if st.button("Browse Catalog (720) →", key="btn_empty_to_cat", type="secondary", use_container_width=True):
                navigate_to("Fashion Catalog")
        return

    # 5. Selected Item Inspector (if open)
    selected_id = st.session_state.get("selected_wardrobe_item_id")
    if selected_id:
        selected_item = next((it for it in items if it["id"] == selected_id), None)
        if selected_item:
            _render_details_inspector(selected_item)
        else:
            st.session_state.pop("selected_wardrobe_item_id", None)

    # 6. Category Filter Navigation Bar
    if "wardrobe_filter" not in st.session_state:
        st.session_state["wardrobe_filter"] = "all"

    curr_filter = st.session_state["wardrobe_filter"]

    # Render category filter buttons in a neat row
    filter_cols = st.columns(len(CATEGORY_FILTERS), gap="small")
    for idx, (slot_key, label) in enumerate(CATEGORY_FILTERS):
        with filter_cols[idx]:
            is_active = (curr_filter == slot_key)
            # Count items in this category
            if slot_key == "all":
                count = total_count
            else:
                count = sum(1 for it in items if it.get("slot") == slot_key)

            button_label = f"{label} ({count})"
            if st.button(
                button_label,
                key=f"wfilter_{slot_key}",
                type="primary" if is_active else "secondary",
                use_container_width=True
            ):
                if curr_filter != slot_key:
                    st.session_state["wardrobe_filter"] = slot_key
                    st.rerun()

    st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

    # 7. Apply Filter
    if curr_filter == "all":
        filtered_items = items
    else:
        filtered_items = [it for it in items if it.get("slot") == curr_filter]

    # Empty category state
    if not filtered_items:
        category_name = next((label for k, label in CATEGORY_FILTERS if k == curr_filter), curr_filter)
        st.markdown(
            f"""
            <div style="background:#FFFFFF;border:1px dashed #E8E3DA;border-radius:12px;padding:48px 24px;text-align:center;margin:24px 0;">
                <div style="font-family:'Cinzel',serif;font-size:18px;font-weight:700;color:#1C1917;margin-bottom:8px;">
                    No pieces saved in {category_name}
                </div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#8C827A;margin-bottom:18px;">
                    Save a garment belonging to the {category_name} category to see it here.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("Show All Garments", key="btn_reset_filter"):
            st.session_state["wardrobe_filter"] = "all"
            st.rerun()
        return

    # 8. Responsive Clothing Gallery Grid (Balanced 4-Column Layout)
    cols_per_row = 4
    for i in range(0, len(filtered_items), cols_per_row):
        row_items = filtered_items[i:i + cols_per_row]
        cols = st.columns(cols_per_row, gap="medium")
        for j, it in enumerate(row_items):
            _render_item_card(it, cols[j], index=i + j)

    # 9. Bottom Footer Spacer
    st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)
