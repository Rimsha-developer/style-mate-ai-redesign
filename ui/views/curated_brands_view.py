"""
Curated Brands & HD Catalog View
===================================
Premium editorial product catalog using genuine HD product images.
Completely separate from the AI training dataset and from My Digital Wardrobe.
"""

import streamlit as st
import base64
import pathlib
from services import curated_catalog_service as ccs
from services import ai_service

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _image_to_base64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def _gender_badge_color(gender: str) -> str:
    return {
        "Men": "#1a2d4a",
        "Women": "#6b3a52",
        "Unisex": "#3a4a3a",
    }.get(gender, "#4a4a4a")


def _occasion_badge_color(occasion: str) -> str:
    return {
        "Casual": "#7a6a4a",
        "Formal": "#2a3a4a",
        "Sports": "#3a5a3a",
        "Ethnic": "#5a3a2a",
        "Party": "#5a3a5a",
    }.get(occasion, "#5a5a5a")


def render_product_card(item: dict, img_path, idx: int):
    """Render a single HD product card."""
    pid = item["id"]
    brand = item.get("brand", "")
    name = item.get("name", "")
    category = item.get("category", "")
    gender = item.get("gender", "")
    occasion = item.get("occasion", "")
    color = item.get("color", "")

    # Build image HTML
    if img_path and img_path.exists():
        b64 = _image_to_base64(img_path)
        img_html = f'<img src="data:image/jpeg;base64,{b64}" class="curated-card-img" alt="{name}" />'
    else:
        img_html = '<div class="curated-card-img-placeholder">No Image</div>'

    gender_color = _gender_badge_color(gender)
    occ_color = _occasion_badge_color(occasion)

    card_html = f"""
    <div class="curated-card" id="card-{pid}">
        <div class="curated-card-img-wrap">
            {img_html}
            <div class="curated-card-badges">
                <span class="curated-badge" style="background:{gender_color}">{gender}</span>
                <span class="curated-badge" style="background:{occ_color}">{occasion}</span>
            </div>
        </div>
        <div class="curated-card-body">
            <div class="curated-brand">{brand}</div>
            <div class="curated-name">{name}</div>
            <div class="curated-meta">{category} · {color.title()}</div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    col_inspect, col_save = st.columns(2)
    with col_inspect:
        if st.button("🔍 Inspect", key=f"inspect_{pid}_{idx}", use_container_width=True):
            st.session_state["curated_inspector_id"] = pid
            st.rerun()
    with col_save:
        if st.button("➕ Wardrobe", key=f"save_{pid}_{idx}", use_container_width=True):
            if img_path and img_path.exists():
                try:
                    ai_service.add_catalog_item_to_wardrobe(
                        catalog_item_path=str(img_path),
                        type_name=name,
                        slot=item.get("slot", "top"),
                        usage=occasion
                    )
                    st.success("Added to wardrobe!")
                except Exception as e:
                    st.error(f"Could not add: {e}")
            else:
                st.error("Image not found.")


def render_inspector(item: dict, img_path):
    """Render the full-screen product inspector panel."""
    brand = item.get("brand", "")
    name = item.get("name", "")
    category = item.get("category", "")
    gender = item.get("gender", "")
    occasion = item.get("occasion", "")
    color = item.get("color", "")
    pid = item.get("id", "")
    dims = f"{item.get('width', '—')} × {item.get('height', '—')} px"

    st.markdown('<div class="inspector-backdrop">', unsafe_allow_html=True)

    col_img, col_meta = st.columns([1, 1], gap="large")

    with col_img:
        if img_path and img_path.exists():
            st.image(str(img_path), use_container_width=True)
        else:
            st.markdown("*Image not available.*")

    with col_meta:
        st.markdown(f"""
        <div class="inspector-brand">{brand}</div>
        <div class="inspector-name">{name}</div>
        <hr class="inspector-divider"/>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <table class="inspector-table">
            <tr><td class="it-label">Category</td><td class="it-val">{category}</td></tr>
            <tr><td class="it-label">Gender</td><td class="it-val">{gender}</td></tr>
            <tr><td class="it-label">Occasion</td><td class="it-val">{occasion}</td></tr>
            <tr><td class="it-label">Colour</td><td class="it-val">{color.title()}</td></tr>
            <tr><td class="it-label">Resolution</td><td class="it-val">{dims}</td></tr>
            <tr><td class="it-label">Product ID</td><td class="it-val">{pid}</td></tr>
        </table>
        """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)

        if st.button("➕ Save to My Wardrobe", key=f"inspector_save_{pid}", use_container_width=True):
            if img_path and img_path.exists():
                try:
                    ai_service.add_catalog_item_to_wardrobe(
                        catalog_item_path=str(img_path),
                        type_name=name,
                        slot=item.get("slot", "top"),
                        usage=occasion
                    )
                    st.success("✓ Added to My Wardrobe!")
                except Exception as e:
                    st.error(f"Could not add to wardrobe: {e}")
            else:
                st.error("Image file not found.")

        st.markdown("<br/>", unsafe_allow_html=True)
        if st.button("← Back to Catalog", key=f"inspector_back_{pid}", use_container_width=True):
            st.session_state.pop("curated_inspector_id", None)
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


def _inject_curated_css():
    st.markdown("""
    <style>
    /* ── Curated Catalog Cards ───────────────────────────────────── */
    .curated-card {
        background: #faf9f6;
        border: 1px solid #e8e0d0;
        border-radius: 4px;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 100%;
        transition: box-shadow 0.25s ease;
    }
    .curated-card:hover {
        box-shadow: 0 8px 32px rgba(0,0,0,0.12);
    }
    .curated-card-img-wrap {
        position: relative;
        width: 100%;
        aspect-ratio: 3/4;
        background: #f5f4f0;
        overflow: hidden;
    }
    .curated-card-img {
        width: 100%;
        height: 100%;
        object-fit: contain;
        object-position: center;
        display: block;
        image-rendering: -webkit-optimize-contrast;
        image-rendering: crisp-edges;
    }
    .curated-card-img-placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
        color: #9a8a7a;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.8rem;
    }
    .curated-card-badges {
        position: absolute;
        top: 8px;
        left: 8px;
        display: flex;
        flex-direction: column;
        gap: 4px;
    }
    .curated-badge {
        color: #fff;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 2px;
    }
    .curated-card-body {
        padding: 12px 14px 10px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        flex: 1;
    }
    .curated-brand {
        font-family: 'Cinzel', serif;
        font-size: 0.65rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        color: #b8955a;
        font-weight: 500;
        margin-bottom: 2px;
    }
    .curated-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.75rem;
        color: #2a2016;
        font-weight: 500;
        line-height: 1.35;
        min-height: 2.7em;
    }
    .curated-meta {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.65rem;
        color: #9a8a6a;
        margin-top: 4px;
    }
    .curated-price {
        font-family: 'Cinzel', serif;
        font-size: 0.85rem;
        color: #2a2016;
        font-weight: 600;
        margin-top: 6px;
    }
    .curated-price-na {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.72rem;
        color: #b0a090;
        font-style: italic;
        margin-top: 6px;
    }

    /* ── Filter Bar ─────────────────────────────────────────────── */
    .curated-filter-bar {
        background: #faf9f6;
        border: 1px solid #e8e0d0;
        border-radius: 4px;
        padding: 16px 20px;
        margin-bottom: 24px;
    }

    /* ── Inspector ──────────────────────────────────────────────── */
    .inspector-backdrop {
        background: #faf9f6;
        border: 1px solid #e8e0d0;
        border-radius: 4px;
        padding: 32px;
        margin: 16px 0 32px;
    }
    .inspector-brand {
        font-family: 'Cinzel', serif;
        font-size: 0.75rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: #b8955a;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .inspector-name {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.3rem;
        color: #2a2016;
        font-weight: 600;
        line-height: 1.4;
        margin-bottom: 4px;
    }
    .inspector-divider {
        border: none;
        border-top: 1px solid #e8e0d0;
        margin: 16px 0;
    }
    .inspector-price {
        font-family: 'Cinzel', serif;
        font-size: 1.5rem;
        color: #2a2016;
        font-weight: 700;
        margin-bottom: 20px;
    }
    .inspector-price-na {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1rem;
        color: #b0a090;
        font-style: italic;
        margin-bottom: 20px;
    }
    .inspector-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.82rem;
    }
    .inspector-table tr {
        border-bottom: 1px solid #f0ebe0;
    }
    .it-label {
        color: #9a8a6a;
        font-weight: 500;
        padding: 8px 0;
        width: 40%;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.72rem;
    }
    .it-val {
        color: #2a2016;
        font-weight: 400;
        padding: 8px 0;
    }

    /* ── Header ─────────────────────────────────────────────────── */
    .curated-header {
        margin-bottom: 8px;
    }
    .curated-header-title {
        font-family: 'Cinzel', serif;
        font-size: 2.2rem;
        color: #2a2016;
        font-weight: 700;
        letter-spacing: 0.05em;
        line-height: 1.1;
    }
    .curated-header-sub {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.9rem;
        color: #7a6a5a;
        font-weight: 300;
        letter-spacing: 0.05em;
        margin-top: 6px;
    }
    .curated-count-pill {
        display: inline-block;
        background: #2a2016;
        color: #e8d5b0;
        font-family: 'Cinzel', serif;
        font-size: 0.65rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        padding: 4px 12px;
        border-radius: 20px;
        margin-top: 10px;
    }
    .curated-disclaimer {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.75rem;
        color: #9a8a6a;
        background: #f5f0e8;
        border-left: 3px solid #b8955a;
        padding: 10px 16px;
        border-radius: 0 4px 4px 0;
        margin: 16px 0 24px;
    }

    /* ── Pagination ──────────────────────────────────────────────── */
    .curated-pag-info {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.8rem;
        color: #9a8a6a;
        text-align: center;
        margin: 8px 0;
    }
    </style>
    """, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main view
# ---------------------------------------------------------------------------

def render_curated_brands_view():
    _inject_curated_css()

    # ── Inspector mode ──────────────────────────────────────────────────────
    inspector_id = st.session_state.get("curated_inspector_id")
    if inspector_id:
        item = ccs.get_product_by_id(inspector_id)
        if item:
            # Header (back button at top)
            st.markdown(f"""
            <div class="curated-header">
                <div class="curated-header-title">Product Detail</div>
                <div class="curated-header-sub">Curated Brands & Collections</div>
            </div>
            """, unsafe_allow_html=True)
            img_path = ccs.get_absolute_image_path(item)
            render_inspector(item, img_path)
            return
        else:
            st.session_state.pop("curated_inspector_id", None)

    # ── Page Header ─────────────────────────────────────────────────────────
    total_items = ccs.get_total_count()
    st.markdown(f"""
    <div class="curated-header">
        <div class="curated-header-title">Curated Brands &amp; Collections</div>
        <div class="curated-header-sub">
            Genuine high-definition fashion pieces, carefully selected for editorial quality.
        </div>
        <span class="curated-count-pill">{total_items} Pieces in This Collection</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="curated-disclaimer">
        These are curated editorial pieces with verified brand and pricing information.
        AI style recommendations are powered by a separate dataset of 720 items.
    </div>
    """, unsafe_allow_html=True)

    # ── Filter Row ──────────────────────────────────────────────────────────
    st.markdown('<div class="curated-filter-bar">', unsafe_allow_html=True)

    brands = ["All"] + ccs.get_brands()
    categories = ["All"] + ccs.get_categories()
    genders = ["All"] + ccs.get_genders()
    occasions = ["All"] + ccs.get_occasions()

    fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 1.5, 1.5, 2.5])
    with fc1:
        sel_brand = st.selectbox("Brand", brands, key="cb_brand")
    with fc2:
        sel_cat = st.selectbox("Category", categories, key="cb_cat")
    with fc3:
        sel_gender = st.selectbox("Gender", genders, key="cb_gender")
    with fc4:
        sel_occ = st.selectbox("Occasion", occasions, key="cb_occ")
    with fc5:
        search_q = st.text_input("Search", placeholder="e.g. adidas, blue jeans…", key="cb_search")

    st.markdown("</div>", unsafe_allow_html=True)

    # ── Filter products ─────────────────────────────────────────────────────
    products = ccs.list_curated_products(
        brand=sel_brand if sel_brand != "All" else None,
        category=sel_cat if sel_cat != "All" else None,
        gender=sel_gender if sel_gender != "All" else None,
        occasion=sel_occ if sel_occ != "All" else None,
        search=search_q.strip() if search_q else None,
    )

    if not products:
        st.markdown("""
        <div style="text-align:center; padding: 60px 20px; color: #9a8a6a;
                    font-family: 'Plus Jakarta Sans', sans-serif;">
            <div style="font-size:2.5rem; margin-bottom:16px;">🏷️</div>
            <div style="font-size:1.1rem; font-weight:500;">No pieces match your filters</div>
            <div style="font-size:0.85rem; margin-top:8px;">
                Try adjusting your brand, category, or search query.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Pagination ──────────────────────────────────────────────────────────
    PAGE_SIZE = 12
    total_pages = max(1, (len(products) + PAGE_SIZE - 1) // PAGE_SIZE)

    if "curated_page" not in st.session_state:
        st.session_state["curated_page"] = 1
    # Reset page if filters changed
    page = st.session_state.get("curated_page", 1)
    page = max(1, min(page, total_pages))

    start = (page - 1) * PAGE_SIZE
    page_products = products[start : start + PAGE_SIZE]

    showing_start = start + 1
    showing_end = start + len(page_products)
    st.markdown(
        f'<div class="curated-pag-info">Showing {showing_start}–{showing_end} of {len(products)} pieces</div>',
        unsafe_allow_html=True,
    )

    # ── Grid ────────────────────────────────────────────────────────────────
    COLS = 4
    rows = [page_products[i : i + COLS] for i in range(0, len(page_products), COLS)]

    for row in rows:
        cols = st.columns(COLS, gap="medium")
        for col, item in zip(cols, row):
            with col:
                img_path = ccs.get_absolute_image_path(item)
                render_product_card(item, img_path, idx=products.index(item))

    # ── Pagination controls ─────────────────────────────────────────────────
    if total_pages > 1:
        st.markdown("<br/>", unsafe_allow_html=True)
        pc1, pc2, pc3 = st.columns([1, 2, 1])
        with pc1:
            if page > 1:
                if st.button("← Previous", key="curated_prev", use_container_width=True):
                    st.session_state["curated_page"] = page - 1
                    st.rerun()
        with pc2:
            st.markdown(
                f'<div style="text-align:center;font-family:\'Plus Jakarta Sans\',sans-serif;'
                f'font-size:0.8rem;color:#9a8a6a;padding-top:8px;">Page {page} of {total_pages}</div>',
                unsafe_allow_html=True,
            )
        with pc3:
            if page < total_pages:
                if st.button("Next →", key="curated_next", use_container_width=True):
                    st.session_state["curated_page"] = page + 1
                    st.rerun()
