"""
Master HD Catalog View
=======================
Premium fashion catalog browsing experience for all 746 master products.
- Uses genuine HD images from catalog/images_hd/ (699+ products)
- Falls back gracefully to thumbnail with "Low Res" badge
- 4-column responsive grid with pagination
- Full-featured filter bar: Category, Subcategory, Brand, Gender, Occasion, HD Only, Search
- Inline product inspector with Similar Items panel
- Save to Wardrobe button
"""
from __future__ import annotations

import base64
import pathlib
import streamlit as st
from services import master_catalog_service as mcs
from services import ai_service
from services import recommendation_service as rs

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

PAGE_SIZE = 12

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@st.cache_data(max_entries=1000, show_spinner=False)
def _image_b64_cached(path_str: str) -> str:
    try:
        p = pathlib.Path(path_str)
        return base64.b64encode(p.read_bytes()).decode()
    except Exception:
        return ""


def _image_b64(path: pathlib.Path) -> str:
    return _image_b64_cached(str(path))


def _gender_color(g: str) -> str:
    return {"Men": "#1a2d4a", "Women": "#6b3a52", "Unisex": "#3a4a3a",
            "Boys": "#1a3a5a", "Girls": "#6b2a4a"}.get(g, "#4a4a4a")


def _occ_color(o: str) -> str:
    return {"Casual": "#7a6a4a", "Formal": "#2a3a4a", "Sports": "#2a5a3a",
            "Ethnic": "#5a3a2a", "Party": "#5a3a5a",
            "Smart Casual": "#4a4a3a"}.get(o, "#5a5a5a")


def _source_badge(src: str) -> str:
    if src == "curated_brands":
        return '<span style="background:#6b3a52;color:#fff;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:600;letter-spacing:.5px">✦ Curated</span>'
    elif src == "admin_uploaded":
        return '<span style="background:#3a5a3a;color:#fff;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:600;letter-spacing:.5px">Custom</span>'
    return ""


def _hd_badge(is_hd: bool = True) -> str:
    return '<span style="background:#2a5a3a;color:#fff;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:600">HD</span>'


def _render_card(item: dict, img_path, idx: int, page_key: str = ""):
    pid = str(item.get("id", idx))
    brand = item.get("brand", "")
    name = item.get("name", pid)
    price = item.get("price", "")
    category = item.get("category", "")
    subcategory = item.get("subcategory", "")
    gender = item.get("gender", "")
    occasion = item.get("occasion", "")
    color = item.get("color", "")
    is_hd = item.get("is_hd", False)
    source = item.get("source", "")

    # Build image HTML
    if img_path and img_path.exists():
        b64 = _image_b64(img_path)
        img_html = (
            f'<img src="data:image/jpeg;base64,{b64}" '
            f'style="width:100%;height:280px;object-fit:contain;background:#f7f5f0;'
            f'display:block;border-radius:0;" alt="{name}" />'
        )
    else:
        img_html = (
            '<div style="width:100%;height:280px;background:#f0ede8;display:flex;'
            'align-items:center;justify-content:center;color:#a08870;font-size:12px;">No Image</div>'
        )

    display_name = name if name and name != pid else (subcategory or category or "Product")
    display_brand = brand if brand else "Editorial Collection"

    badge_top_left = f'<div style="position:absolute;top:8px;left:8px;display:flex;gap:4px;flex-wrap:wrap;z-index:2;">{_hd_badge(is_hd)}{_source_badge(source)}</div>'
    badge_bot_right = (
        f'<div style="position:absolute;bottom:8px;right:8px;display:flex;gap:3px;z-index:2;">'
        f'<span style="background:{_gender_color(gender)};color:#fff;font-size:9px;padding:2px 5px;border-radius:4px;font-weight:600;">{gender}</span>'
        f'<span style="background:{_occ_color(occasion)};color:#fff;font-size:9px;padding:2px 5px;border-radius:4px;font-weight:600;">{occasion}</span>'
        f'</div>'
    )

    card_html = (
        f'<div style="background:#fff;border-radius:4px;overflow:hidden;box-shadow:0 1px 6px rgba(0,0,0,.08);margin-bottom:4px;border:1px solid #ece8e0;">'
        f'<div style="position:relative;width:100%;height:280px;background:#f7f5f0;overflow:hidden;">'
        f'{img_html}'
        f'{badge_top_left}'
        f'{badge_bot_right}'
        f'</div>'
        f'<div style="padding:10px 12px 8px;">'
        f'<div style="font-size:10px;color:#8a7a6a;text-transform:uppercase;letter-spacing:.8px;font-weight:600;margin-bottom:2px;">{display_brand}</div>'
        f'<div style="font-size:13px;font-weight:600;color:#1a1a1a;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{display_name}">{display_name}</div>'
        f'<div style="font-size:11px;color:#8a7a6a;margin-top:2px;">{subcategory or category} · {color.title() if color else "—"}</div>'
        f'</div>'
        f'</div>'
    )
    st.html(card_html)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔍 Details", key=f"mci_{page_key}_{pid}_{idx}", use_container_width=True):
            st.session_state["mc_inspector_id"] = pid
            st.rerun()
    with c2:
        if st.button("➕ Wardrobe", key=f"mcw_{page_key}_{pid}_{idx}", use_container_width=True):
            if img_path and img_path.exists():
                try:
                    ai_service.add_catalog_item_to_wardrobe(
                        catalog_item_path=str(img_path),
                        type_name=name or subcategory or category,
                        slot=item.get("slot", "top"),
                        usage=occasion or "Casual",
                        gender=item.get("gender", "Unisex")
                    )
                    st.toast(f"✓ {display_name} added to wardrobe!", icon="👗")
                except Exception as e:
                    st.error(f"Could not add: {e}")
            else:
                st.warning("Image not available for this product.")


def _render_inspector(item: dict):
    """Full product inspector panel."""
    pid = str(item.get("id", ""))
    brand = item.get("brand", "Editorial Collection")
    name = item.get("name", pid)
    category = item.get("category", "")
    subcategory = item.get("subcategory", "")
    gender = item.get("gender", "")
    occasion = item.get("occasion", "")
    color = item.get("color", "")
    desc = item.get("description", "")
    url = item.get("url", "")
    is_hd = item.get("is_hd", False)
    source = item.get("source", "")
    img_path = mcs.get_absolute_image_path(item)

    st.markdown(
        '<div style="background:#fff;border-radius:8px;padding:28px 24px;'
        'border:1px solid #ece8e0;margin-bottom:24px">',
        unsafe_allow_html=True
    )

    # Back button
    if st.button("← Back to Catalog", key="mc_back"):
        st.session_state.pop("mc_inspector_id", None)
        st.rerun()

    st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)

    col_img, col_meta = st.columns([1, 1], gap="large")

    with col_img:
        if img_path and img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.markdown(
                '<div style="height:400px;background:#f0ede8;display:flex;align-items:center;'
                'justify-content:center;color:#a08870;border-radius:4px">No Image Available</div>',
                unsafe_allow_html=True
            )
        # HD status
        res_label = "Genuine HD Image" if is_hd else "Thumbnail (Low Res)"
        res_color = "#2a5a3a" if is_hd else "#7a5a3a"
        st.markdown(
            f'<div style="text-align:center;margin-top:8px">'
            f'<span style="background:{res_color};color:#fff;font-size:11px;'
            f'padding:3px 10px;border-radius:12px;font-weight:600">{res_label}</span></div>',
            unsafe_allow_html=True
        )

    with col_meta:
        st.markdown(
            f'<div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;'
            f'letter-spacing:1px;font-weight:600;margin-bottom:4px">{brand}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div style="font-size:22px;font-weight:700;color:#1a1a1a;'
            f'line-height:1.3;margin-bottom:16px">{name}</div>',
            unsafe_allow_html=True
        )

        # Attributes table
        attrs = [
            ("Category", f"{category} → {subcategory}" if subcategory else category),
            ("Gender", gender),
            ("Occasion", occasion),
            ("Color", color.title() if color else "—"),
            ("Product ID", pid),
            ("Source", {"curated_brands": "Curated HD Brand", "original_catalog": "AI Dataset Product",
                        "admin_uploaded": "Admin Upload"}.get(source, source)),
        ]
        rows_html = "".join(
            f'<tr><td style="color:#8a7a6a;font-size:12px;padding:4px 12px 4px 0;'
            f'white-space:nowrap;font-weight:600">{k}</td>'
            f'<td style="color:#1a1a1a;font-size:13px;padding:4px 0">{v}</td></tr>'
            for k, v in attrs if v
        )
        st.markdown(
            f'<table style="border-collapse:collapse;width:100%">{rows_html}</table>',
            unsafe_allow_html=True
        )

        if desc:
            st.markdown(
                f'<div style="margin-top:16px;font-size:13px;color:#4a4a4a;line-height:1.6">{desc}</div>',
                unsafe_allow_html=True
            )

        # Action buttons
        st.markdown('<div style="height:20px"></div>', unsafe_allow_html=True)
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            if img_path and img_path.exists():
                if st.button("➕ Save to My Wardrobe", key=f"mc_save_insp_{pid}", use_container_width=True):
                    try:
                        ai_service.add_catalog_item_to_wardrobe(
                            catalog_item_path=str(img_path),
                            type_name=name or subcategory or category,
                            slot=item.get("slot", "top"),
                            usage=occasion or "Casual",
                            gender=item.get("gender", "Unisex")
                        )
                        st.success("Added to My Wardrobe!")
                    except Exception as e:
                        st.error(f"Could not save: {e}")
        with btn_col2:
            if url:
                st.link_button("🔗 View Original", url, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Similar items
    similar = rs.get_similar_to_product(item, max_results=4)
    if similar:
        st.markdown(
            '<div style="font-size:16px;font-weight:700;color:#1a1a1a;'
            'margin:24px 0 16px;text-transform:uppercase;letter-spacing:.8px">'
            'Similar Styles</div>',
            unsafe_allow_html=True
        )
        s_cols = st.columns(4)
        for i, s_item in enumerate(similar):
            s_path = mcs.get_absolute_image_path(s_item)
            with s_cols[i % 4]:
                _render_card(s_item, s_path, idx=i + 9000, page_key="sim")


# ---------------------------------------------------------------------------
# FILTER BAR
# ---------------------------------------------------------------------------

def _render_filters() -> dict:
    """Render the filter bar and return selected filter values."""
    st.markdown(
        '<div style="background:#fff;padding:16px 20px;border-radius:6px;'
        'border:1px solid #d8d2c7;margin-bottom:20px">',
        unsafe_allow_html=True
    )
    f1, f2, f3, f4, f5 = st.columns([2.5, 2, 2, 1.5, 1.5])

    with f1:
        search = st.text_input("🔍 Search", placeholder="Brand, garment type, color…", key="mc_search", label_visibility="collapsed")

    with f2:
        cats = ["All Categories"] + mcs.get_categories()
        cat = st.selectbox("Category", cats, key="mc_cat", label_visibility="collapsed")
        cat = None if cat == "All Categories" else cat

    with f3:
        if cat:
            subcats = ["All Types"] + mcs.get_subcategories(cat)
        else:
            subcats = ["All Types"]
        sub = st.selectbox("Type", subcats, key="mc_sub", label_visibility="collapsed")
        sub = None if sub == "All Types" else sub

    with f4:
        genders = ["All Genders"] + mcs.get_genders()
        gender = st.selectbox("Gender", genders, key="mc_gender", label_visibility="collapsed")
        gender = None if gender == "All Genders" else gender

    with f5:
        occs = ["All Occasions"] + mcs.get_occasions()
        occ = st.selectbox("Occasion", occs, key="mc_occ", label_visibility="collapsed")
        occ = None if occ == "All Occasions" else occ

    st.markdown('</div>', unsafe_allow_html=True)

    return {
        "search": search.strip() if search else None,
        "category": cat,
        "subcategory": sub,
        "gender": gender,
        "occasion": occ,
    }


# ---------------------------------------------------------------------------
# STATS BAR
# ---------------------------------------------------------------------------

def _render_stats(stats: dict, filtered_count: int):
    total = stats.get("total", 0)
    hd_count = stats.get("hd_count", 0)
    hd_pct = stats.get("hd_percentage", 0)
    curated = stats.get("curated_count", 0)
    admin = stats.get("admin_count", 0)

    st.markdown(
        f"""
        <div style="display:flex;gap:24px;margin-bottom:20px;flex-wrap:wrap">
          <div style="background:#fff;padding:12px 20px;border-radius:4px;border:1px solid #ece8e0;min-width:140px">
            <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:.8px">Total Pieces</div>
            <div style="font-size:24px;font-weight:700;color:#1a1a1a">{total}</div>
          </div>
          <div style="background:#fff;padding:12px 20px;border-radius:4px;border:1px solid #ece8e0;min-width:140px">
            <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:.8px">Genuine HD</div>
            <div style="font-size:24px;font-weight:700;color:#2a5a3a">{hd_count} <span style="font-size:14px;color:#6a9a7a">({hd_pct:.0f}%)</span></div>
          </div>
          <div style="background:#fff;padding:12px 20px;border-radius:4px;border:1px solid #ece8e0;min-width:140px">
            <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:.8px">Curated Brands</div>
            <div style="font-size:24px;font-weight:700;color:#6b3a52">{curated}</div>
          </div>
          <div style="background:#fff;padding:12px 20px;border-radius:4px;border:1px solid #ece8e0;min-width:140px">
            <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:.8px">Showing</div>
            <div style="font-size:24px;font-weight:700;color:#1a1a1a">{filtered_count}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ---------------------------------------------------------------------------
# MAIN RENDER
# ---------------------------------------------------------------------------

def render_master_catalog_view():
    """Render the full Master HD Catalog page."""

    # Header
    st.markdown(
        """
        <div style="margin-bottom:28px">
          <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:2px;
                      margin-bottom:6px">Style Mate AI · Fashion Catalog</div>
          <div style="font-size:32px;font-weight:800;color:#1a1a1a;letter-spacing:-1px;
                      line-height:1.1;margin-bottom:8px">Master HD Catalog</div>
          <div style="font-size:15px;color:#6a5a4a;font-style:italic">
            746 high-resolution Western fashion pieces. Unified editorial catalog.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Inspector mode
    inspector_id = st.session_state.get("mc_inspector_id")
    if inspector_id:
        item = mcs.get_product(str(inspector_id))
        if item:
            _render_inspector(item)
            return
        else:
            st.session_state.pop("mc_inspector_id", None)

    # Filters
    filters = _render_filters()

    # Fetch products
    products = mcs.list_products(
        category=filters["category"],
        subcategory=filters["subcategory"],
        gender=filters["gender"],
        occasion=filters["occasion"],
        search=filters["search"],
        hd_only=False,
    )

    # Stats
    stats = mcs.get_stats()
    _render_stats(stats, len(products))

    if not products:
        st.markdown(
            '<div style="text-align:center;padding:60px 0;color:#8a7a6a;font-size:16px">'
            '🔍 No products match your filters. Try adjusting the search or category.</div>',
            unsafe_allow_html=True
        )
        return

    # Source filter - Curated Brands filter on the unified catalog
    source_options = ["All Pieces (746)", "✦ Curated Brands Only (26)"]
    src_tab = st.radio(
        "Catalog Filter",
        source_options,
        horizontal=True,
        key="mc_source_tab",
        label_visibility="collapsed"
    )
    if src_tab == "✦ Curated Brands Only (26)":
        products = [p for p in products if p.get("source") == "curated_brands"]

    if not products:
        st.markdown(
            '<div style="text-align:center;padding:40px 0;color:#8a7a6a;font-size:15px">'
            'No products from this source match your filters.</div>',
            unsafe_allow_html=True
        )
        return

    # Pagination
    total_pages = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)
    if "mc_page" not in st.session_state:
        st.session_state["mc_page"] = 1
    # Reset page when filters change
    filter_key = str(filters)
    if st.session_state.get("_mc_last_filter") != filter_key:
        st.session_state["mc_page"] = 1
        st.session_state["_mc_last_filter"] = filter_key

    page = st.session_state["mc_page"]
    page = max(1, min(page, total_pages))
    start = (page - 1) * PAGE_SIZE
    page_products = products[start: start + PAGE_SIZE]

    # Pagination controls (top)
    _render_pagination(page, total_pages, len(products), "top")

    # 4-column product grid
    num_cols = 4
    for row_start in range(0, len(page_products), num_cols):
        row = page_products[row_start: row_start + num_cols]
        cols = st.columns(num_cols)
        for col_idx, item in enumerate(row):
            img_path = mcs.get_absolute_image_path(item)
            with cols[col_idx]:
                _render_card(item, img_path, idx=start + row_start + col_idx, page_key=f"p{page}")

    # Pagination controls (bottom)
    _render_pagination(page, total_pages, len(products), "bot")


def _render_pagination(page: int, total_pages: int, total_items: int, suffix: str):
    """Render prev/page-info/next pagination row."""
    if total_pages <= 1:
        return

    pc1, pc2, pc3 = st.columns([1, 3, 1])
    with pc1:
        if page > 1:
            if st.button("← Previous", key=f"mc_prev_{suffix}", use_container_width=True):
                st.session_state["mc_page"] = page - 1
                st.rerun()
    with pc2:
        st.markdown(
            f'<div style="text-align:center;color:#8a7a6a;font-size:13px;padding:8px 0">'
            f'Page {page} of {total_pages} &nbsp;·&nbsp; {total_items} products</div>',
            unsafe_allow_html=True
        )
    with pc3:
        if page < total_pages:
            if st.button("Next →", key=f"mc_next_{suffix}", use_container_width=True):
                st.session_state["mc_page"] = page + 1
                st.rerun()
