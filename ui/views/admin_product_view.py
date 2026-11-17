"""
Admin Product Management View
===============================
Full CRUD interface for the master product catalog.

Features:
- Single product upload with image preview
- Bulk CSV import with column validator
- Edit existing products (pre-filled form)
- Delete with confirmation dialog
- Search + filter admin product list
- AI Supported badge per subcategory
- Access gated by a simple session-state password
"""
from __future__ import annotations

import io
import os
import pathlib
import base64
from typing import Optional
import pandas as pd
import streamlit as st
from PIL import Image

from services import master_catalog_service as mcs

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

TAXONOMY = mcs.TAXONOMY
AI_SUPPORTED = mcs.AI_SUPPORTED_CLASSES

# ---------------------------------------------------------------------------
# Auth gate (Secrets / Environment Variable Configuration)
# ---------------------------------------------------------------------------

def _get_configured_admin_password() -> Optional[str]:
    """Retrieve the admin password securely from Streamlit secrets or environment variables.
    
    Returns None if no password is configured (denies access by default).
    Zero hardcoded passwords exist in the application code.
    """
    # 1. Check Streamlit secrets (.streamlit/secrets.toml)
    try:
        if hasattr(st, "secrets"):
            if "admin_password" in st.secrets:
                val = st.secrets["admin_password"]
                if val and str(val).strip():
                    return str(val).strip()
            if "auth" in st.secrets and "admin_password" in st.secrets["auth"]:
                val = st.secrets["auth"]["admin_password"]
                if val and str(val).strip():
                    return str(val).strip()
    except Exception:
        pass

    # 2. Check environment variables
    for env_var in ["STYLEMATE_ADMIN_PASSWORD", "ADMIN_PASSWORD"]:
        val = os.environ.get(env_var)
        if val and val.strip():
            return val.strip()

    return None


def _check_auth() -> bool:
    if st.session_state.get("admin_authed"):
        return True

    expected_pw = _get_configured_admin_password()

    st.markdown(
        """
        <div style="max-width:440px;margin:50px auto 20px auto;background:#fff;padding:36px;
                    border-radius:8px;border:1px solid #ece8e0;text-align:center">
          <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:2px;
                      margin-bottom:12px">Style Mate AI</div>
          <div style="font-size:22px;font-weight:800;color:#1a1a1a;margin-bottom:4px">Admin Access</div>
          <div style="font-size:13px;color:#8a7a6a;margin-bottom:20px">Product Management Portal</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if not expected_pw:
        st.markdown(
            """
            <div style="max-width:440px;margin:0 auto;background:#FFF5F5;border:1px solid #FED7D7;
                        border-radius:8px;padding:20px;color:#9B2C2C;font-size:13px;line-height:1.5;">
              <div style="font-weight:700;font-size:14px;margin-bottom:6px;">🔒 Admin Authentication Not Configured</div>
              Admin access is disabled because no administrator password has been set.
              <br><br>
              <strong>To enable Admin access:</strong>
              <ul style="margin:8px 0 0 16px;padding:0;">
                <li>Set the <code>STYLEMATE_ADMIN_PASSWORD</code> environment variable, or</li>
                <li>Add <code>admin_password = "..."</code> to <code>.streamlit/secrets.toml</code>.</li>
              </ul>
            </div>
            """,
            unsafe_allow_html=True
        )
        return False

    with st.form("admin_login"):
        pw = st.text_input("Password", type="password", label_visibility="collapsed",
                           placeholder="Enter admin password")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        if submitted:
            if pw and pw.strip() == expected_pw:
                st.session_state["admin_authed"] = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _image_b64(path: pathlib.Path) -> str:
    return base64.b64encode(path.read_bytes()).decode()


def _ai_badge(subcategory: str) -> str:
    is_supported = subcategory in AI_SUPPORTED or any(
        s.lower() == subcategory.lower() for s in AI_SUPPORTED
    )
    if is_supported:
        return '<span style="background:#2a5a3a;color:#fff;font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600">✓ AI Supported</span>'
    return '<span style="background:#7a5a3a;color:#fff;font-size:10px;padding:2px 7px;border-radius:4px;font-weight:600">✗ Not in AI Model</span>'


# ---------------------------------------------------------------------------
# UPLOAD FORM
# ---------------------------------------------------------------------------

def _render_upload_form():
    """Single-product upload form."""
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:16px">'
        '➕ Add New Product</div>',
        unsafe_allow_html=True
    )

    with st.form("admin_add_product", clear_on_submit=True):
        c1, c2 = st.columns([1, 1], gap="large")

        with c1:
            uploaded_img = st.file_uploader(
                "Product Image", type=["jpg", "jpeg", "png", "webp"],
                help="Upload a clear product photo (JPG/PNG). Recommended: at least 500×600 px."
            )
            if uploaded_img:
                img = Image.open(uploaded_img)
                st.image(img, caption=f"{img.width}×{img.height} px", use_container_width=True)

        with c2:
            name = st.text_input("Product Name *", placeholder="e.g. Classic Oxford Shirt")
            brand = st.text_input("Brand", placeholder="e.g. Calvin Klein (or leave blank)")

            cat_options = list(TAXONOMY.keys())
            cat = st.selectbox("Category *", cat_options)
            sub_options = TAXONOMY.get(cat, [])
            sub = st.selectbox("Subcategory *", sub_options)

            # Show AI support badge
            if sub:
                st.markdown(_ai_badge(sub), unsafe_allow_html=True)

            g_col, occ_col = st.columns(2)
            with g_col:
                gender = st.selectbox("Gender", mcs.get_genders())
            with occ_col:
                occasion = st.selectbox("Occasion", ["Casual", "Formal", "Sports", "Ethnic", "Party", "Smart Casual"])

            color = st.text_input("Color", placeholder="e.g. Navy Blue")
            price_col, curr_col = st.columns([3, 1])
            with price_col:
                price_val = st.text_input("Price", placeholder="e.g. 49.99")
            with curr_col:
                currency = st.selectbox("Currency", ["USD", "INR", "GBP", "EUR"])
            description = st.text_area("Description", placeholder="Short product description (optional)")
            url = st.text_input("Original URL", placeholder="https://... (optional)")

        submitted = st.form_submit_button("💾 Save Product", use_container_width=True)
        if submitted:
            errors = []
            if not name.strip():
                errors.append("Product name is required.")
            if errors:
                for e in errors:
                    st.error(e)
            else:
                # Build price string
                price_str = ""
                if price_val.strip():
                    try:
                        pf = float(price_val.strip())
                        symbols = {"USD": "$", "INR": "₹", "GBP": "£", "EUR": "€"}
                        price_str = f"{symbols.get(currency, '$')}{pf:.2f}"
                    except ValueError:
                        price_str = price_val.strip()

                img_bytes = None
                if uploaded_img:
                    uploaded_img.seek(0)
                    img_bytes = uploaded_img.read()

                try:
                    result = mcs.add_product(
                        name=name.strip(),
                        brand=brand.strip(),
                        category=cat,
                        subcategory=sub,
                        gender=gender,
                        price=price_str,
                        currency=currency,
                        description=description.strip(),
                        url=url.strip(),
                        color=color.strip(),
                        occasion=occasion,
                        image_bytes=img_bytes,
                        image_filename=uploaded_img.name if uploaded_img else None,
                    )
                    if result.get("success"):
                        st.success(f"✓ Product '{name}' saved successfully! ID: {result['product']['id']}")
                        mcs.reload_catalog()
                    else:
                        st.error(f"Failed: {result.get('error', 'Unknown error')}")
                except Exception as ex:
                    st.error(f"Error saving product: {ex}")


# ---------------------------------------------------------------------------
# CSV BULK IMPORT
# ---------------------------------------------------------------------------

def _render_csv_import():
    """CSV bulk import panel."""
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:12px">'
        '📋 Bulk Import via CSV</div>',
        unsafe_allow_html=True
    )

    # Template download
    template_cols = ["name", "brand", "category", "subcategory", "gender",
                     "price", "currency", "occasion", "color", "description", "url"]
    template_df = pd.DataFrame(columns=template_cols)
    template_csv = template_df.to_csv(index=False)

    st.download_button(
        "⬇ Download CSV Template",
        data=template_csv,
        file_name="product_import_template.csv",
        mime="text/csv"
    )

    st.markdown(
        '<div style="font-size:12px;color:#8a7a6a;margin:8px 0 16px">'
        f'Required columns: <code>name, category, subcategory</code>. '
        f'All other columns are optional.</div>',
        unsafe_allow_html=True
    )

    uploaded_csv = st.file_uploader("Upload CSV file", type=["csv"], key="admin_csv_upload")
    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            st.markdown(f"**Preview** ({len(df)} rows):")
            st.dataframe(df.head(10), use_container_width=True)

            # Validate required columns
            required = {"name", "category", "subcategory"}
            missing = required - set(df.columns.str.lower())
            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}")
            else:
                if st.button("✅ Import All Rows", key="admin_csv_import_btn"):
                    with st.spinner("Importing products…"):
                        result = mcs.import_csv(df)
                    if result.get("success"):
                        st.success(
                            f"✓ Imported {result.get('imported', 0)} products. "
                            f"Skipped: {result.get('skipped', 0)}."
                        )
                        mcs.reload_catalog()
                    else:
                        st.error(f"Import failed: {result.get('error')}")

        except Exception as ex:
            st.error(f"Could not read CSV: {ex}")


# ---------------------------------------------------------------------------
# PRODUCT LIST (ADMIN)
# ---------------------------------------------------------------------------

def _render_product_list():
    """Searchable admin list with edit/delete per product."""
    st.markdown(
        '<div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:16px">'
        '📦 Manage Products</div>',
        unsafe_allow_html=True
    )

    # Filters
    fc1, fc2, fc3 = st.columns([3, 2, 2])
    with fc1:
        search = st.text_input("Search products", placeholder="Name, brand, ID…",
                               key="admin_list_search", label_visibility="collapsed")
    with fc2:
        cats = ["All Categories"] + mcs.get_categories()
        cat_f = st.selectbox("Category filter", cats, key="admin_list_cat",
                             label_visibility="collapsed")
    with fc3:
        sources = ["All Sources", "curated_brands", "original_catalog", "admin_uploaded"]
        src_f = st.selectbox("Source filter", sources, key="admin_list_src",
                             label_visibility="collapsed")

    products = mcs.list_products(
        category=None if cat_f == "All Categories" else cat_f,
        search=search.strip() if search else None,
        source=None if src_f == "All Sources" else src_f,
    )

    st.markdown(
        f'<div style="font-size:13px;color:#8a7a6a;margin-bottom:12px">'
        f'Showing {len(products)} products</div>',
        unsafe_allow_html=True
    )

    if not products:
        st.info("No products match the current filters.")
        return

    # Paginate to 20 per page
    admin_page = st.session_state.get("admin_list_page", 1)
    total_admin_pages = max(1, (len(products) + 19) // 20)
    admin_page = max(1, min(admin_page, total_admin_pages))
    start = (admin_page - 1) * 20
    page_items = products[start: start + 20]

    # Header row
    h1, h2, h3, h4, h5, h6 = st.columns([0.5, 2.5, 2, 1.5, 1, 1.5])
    for col, label in zip([h1, h2, h3, h4, h5, h6],
                           ["", "Name / Brand", "Category", "Gender", "HD", "Actions"]):
        col.markdown(
            f'<div style="font-size:10px;color:#8a7a6a;text-transform:uppercase;'
            f'letter-spacing:.8px;font-weight:600;padding-bottom:6px">{label}</div>',
            unsafe_allow_html=True
        )

    for item in page_items:
        pid = str(item.get("id", ""))
        img_path = mcs.get_absolute_image_path(item)
        name = item.get("name", pid)
        brand = item.get("brand", "")
        cat_label = f"{item.get('category', '')} → {item.get('subcategory', '')}"
        gender = item.get("gender", "")
        is_hd = "✅" if item.get("is_hd") else "☐"
        source = item.get("source", "")

        col_img, col_name, col_cat, col_gender, col_hd, col_act = st.columns([0.5, 2.5, 2, 1.5, 1, 1.5])

        with col_img:
            if img_path and img_path.exists():
                st.image(str(img_path), width=48)
            else:
                st.markdown(
                    '<div style="width:48px;height:60px;background:#f0ede8;border-radius:2px"></div>',
                    unsafe_allow_html=True
                )

        with col_name:
            st.markdown(
                f'<div style="font-size:13px;font-weight:600;color:#1a1a1a">{name}</div>'
                f'<div style="font-size:11px;color:#8a7a6a">{brand or "No brand"} · #{pid}</div>',
                unsafe_allow_html=True
            )

        with col_cat:
            st.markdown(
                f'<div style="font-size:12px;color:#4a4a4a">{cat_label}</div>',
                unsafe_allow_html=True
            )

        with col_gender:
            st.markdown(
                f'<div style="font-size:12px;color:#4a4a4a">{gender}</div>',
                unsafe_allow_html=True
            )

        with col_hd:
            st.markdown(
                f'<div style="font-size:14px">{is_hd}</div>',
                unsafe_allow_html=True
            )

        with col_act:
            ea, da = st.columns(2)
            with ea:
                if source not in ("original_catalog",):
                    if st.button("✏", key=f"adm_edit_{pid}", help="Edit product"):
                        st.session_state["admin_edit_id"] = pid
                        st.rerun()
                else:
                    st.markdown(
                        '<span style="font-size:10px;color:#c0b0a0">AI data</span>',
                        unsafe_allow_html=True
                    )
            with da:
                if source not in ("original_catalog", "curated_brands"):
                    if st.button("🗑", key=f"adm_del_{pid}", help="Delete product"):
                        st.session_state["admin_confirm_delete"] = pid
                        st.rerun()
                else:
                    st.markdown(
                        '<span style="font-size:10px;color:#c0b0a0">protected</span>',
                        unsafe_allow_html=True
                    )

    # Pagination
    if total_admin_pages > 1:
        p1, p2, p3 = st.columns([1, 3, 1])
        with p1:
            if admin_page > 1:
                if st.button("← Prev", key="adm_prev"):
                    st.session_state["admin_list_page"] = admin_page - 1
                    st.rerun()
        with p2:
            st.markdown(
                f'<div style="text-align:center;color:#8a7a6a;font-size:13px;padding:8px 0">'
                f'Page {admin_page} of {total_admin_pages}</div>',
                unsafe_allow_html=True
            )
        with p3:
            if admin_page < total_admin_pages:
                if st.button("Next →", key="adm_next"):
                    st.session_state["admin_list_page"] = admin_page + 1
                    st.rerun()


# ---------------------------------------------------------------------------
# EDIT FORM
# ---------------------------------------------------------------------------

def _render_edit_form(product_id: str):
    """Pre-filled edit form for an existing product."""
    item = mcs.get_product(product_id)
    if not item:
        st.error(f"Product {product_id} not found.")
        st.session_state.pop("admin_edit_id", None)
        return

    st.markdown(
        f'<div style="font-size:18px;font-weight:700;color:#1a1a1a;margin-bottom:16px">'
        f'✏️ Edit Product #{product_id}</div>',
        unsafe_allow_html=True
    )
    if st.button("← Cancel Edit", key="admin_cancel_edit"):
        st.session_state.pop("admin_edit_id", None)
        st.rerun()

    with st.form("admin_edit_form"):
        c1, c2 = st.columns([1, 1], gap="large")

        with c1:
            img_path = mcs.get_absolute_image_path(item)
            if img_path and img_path.exists():
                st.image(str(img_path), use_container_width=True)
            new_img = st.file_uploader("Replace Image (optional)", type=["jpg", "jpeg", "png", "webp"],
                                       key=f"edit_img_{product_id}")

        with c2:
            name = st.text_input("Product Name *", value=item.get("name", ""))
            brand = st.text_input("Brand", value=item.get("brand", ""))

            cat_options = list(TAXONOMY.keys())
            cur_cat = item.get("category", cat_options[0])
            cat_idx = cat_options.index(cur_cat) if cur_cat in cat_options else 0
            cat = st.selectbox("Category", cat_options, index=cat_idx)

            sub_options = TAXONOMY.get(cat, [])
            cur_sub = item.get("subcategory", sub_options[0] if sub_options else "")
            sub_idx = sub_options.index(cur_sub) if cur_sub in sub_options else 0
            sub = st.selectbox("Subcategory", sub_options, index=sub_idx) if sub_options else st.text_input("Subcategory", value=cur_sub)

            g_opts = mcs.get_genders()
            cur_g = item.get("gender", "Men")
            g_idx = g_opts.index(cur_g) if cur_g in g_opts else 0
            gender = st.selectbox("Gender", g_opts, index=g_idx)

            occ_opts = ["Casual", "Formal", "Sports", "Ethnic", "Party", "Smart Casual"]
            cur_occ = item.get("occasion", "Casual")
            occ_idx = occ_opts.index(cur_occ) if cur_occ in occ_opts else 0
            occasion = st.selectbox("Occasion", occ_opts, index=occ_idx)

            color = st.text_input("Color", value=item.get("color", ""))
            price = st.text_input("Price", value=item.get("price", ""))
            description = st.text_area("Description", value=item.get("description", ""))
            url = st.text_input("URL", value=item.get("url", ""))

        submitted = st.form_submit_button("💾 Save Changes", use_container_width=True)
        if submitted:
            updates = {
                "name": name.strip(),
                "brand": brand.strip(),
                "category": cat,
                "subcategory": sub,
                "gender": gender,
                "occasion": occasion,
                "color": color.strip(),
                "price": price.strip(),
                "description": description.strip(),
                "url": url.strip(),
            }
            if new_img:
                new_img.seek(0)
                img_bytes = new_img.read()
                # Save new image
                ext = pathlib.Path(new_img.name).suffix or ".jpg"
                dest = ROOT / "catalog" / "images_custom" / f"{product_id}{ext}"
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(img_bytes)
                updates["image_path"] = f"catalog/images_custom/{product_id}{ext}"
                updates["is_hd"] = True

            result = mcs.update_product(product_id, updates)
            if result.get("success"):
                st.success("✓ Product updated successfully!")
                mcs.reload_catalog()
                st.session_state.pop("admin_edit_id", None)
                st.rerun()
            else:
                st.error(f"Failed: {result.get('error')}")


# ---------------------------------------------------------------------------
# DELETE CONFIRMATION
# ---------------------------------------------------------------------------

def _render_delete_confirm(product_id: str):
    """Confirmation dialog before deleting."""
    item = mcs.get_product(product_id)
    name = item.get("name", product_id) if item else product_id

    st.warning(f"⚠️ Are you sure you want to delete **{name}** (#{product_id})? This cannot be undone.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🗑 Yes, Delete", key="admin_del_confirm", type="primary"):
            result = mcs.delete_product(product_id)
            if result.get("success"):
                st.success(f"Deleted product #{product_id}.")
                mcs.reload_catalog()
            else:
                st.error(f"Delete failed: {result.get('error')}")
            st.session_state.pop("admin_confirm_delete", None)
            st.rerun()
    with c2:
        if st.button("Cancel", key="admin_del_cancel"):
            st.session_state.pop("admin_confirm_delete", None)
            st.rerun()


# ---------------------------------------------------------------------------
# MAIN RENDER
# ---------------------------------------------------------------------------

def render_admin_view():
    """Render the Admin Product Management page."""

    # Auth gate
    if not _check_auth():
        return

    # Header
    st.markdown(
        """
        <div style="margin-bottom:28px">
          <div style="font-size:11px;color:#8a7a6a;text-transform:uppercase;letter-spacing:2px;
                      margin-bottom:6px">Style Mate AI · Admin</div>
          <div style="font-size:32px;font-weight:800;color:#1a1a1a;letter-spacing:-1px;
                      line-height:1.1;margin-bottom:8px">Product Management</div>
          <div style="font-size:15px;color:#6a5a4a;font-style:italic">
            Add, edit, delete, and import fashion products into the master catalog.
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Sign-out button
    if st.button("🔓 Sign Out", key="admin_signout"):
        st.session_state.pop("admin_authed", None)
        st.rerun()

    # Stats
    stats = mcs.get_stats()
    s1, s2, s3, s4 = st.columns(4)
    for col, label, val in [
        (s1, "Total Products", stats["total"]),
        (s2, "HD Images", stats["hd_count"]),
        (s3, "Curated HD", stats["curated_count"]),
        (s4, "Admin Uploads", stats["admin_count"]),
    ]:
        col.markdown(
            f'<div style="background:#fff;padding:12px 16px;border-radius:4px;'
            f'border:1px solid #ece8e0;text-align:center">'
            f'<div style="font-size:10px;color:#8a7a6a;text-transform:uppercase;'
            f'letter-spacing:.8px;margin-bottom:4px">{label}</div>'
            f'<div style="font-size:22px;font-weight:700;color:#1a1a1a">{val}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown('<div style="height:24px"></div>', unsafe_allow_html=True)

    # Handle special states
    edit_id = st.session_state.get("admin_edit_id")
    confirm_del_id = st.session_state.get("admin_confirm_delete")

    if confirm_del_id:
        _render_delete_confirm(confirm_del_id)
        st.markdown('<hr style="border-color:#ece8e0;margin:24px 0">', unsafe_allow_html=True)

    if edit_id:
        _render_edit_form(edit_id)
        st.markdown('<hr style="border-color:#ece8e0;margin:24px 0">', unsafe_allow_html=True)

    # Main tabs
    tab_add, tab_csv, tab_list = st.tabs(["➕ Add Product", "📋 Bulk CSV Import", "📦 Manage Products"])

    with tab_add:
        _render_upload_form()

    with tab_csv:
        _render_csv_import()

    with tab_list:
        _render_product_list()
