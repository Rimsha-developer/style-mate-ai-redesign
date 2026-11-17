"""Style Mate AI - AI Fashion Studio View (Phase 4, Step 2)
Premium editorial interface for garment classification using the original verified AI backend.

Tabs:
  1. Single Garment Analyzer — classify one uploaded garment.
  2. Full-Body / Multi-Garment  — detect pose crops + classify each region.

Rules:
- Calls ONLY services.ai_service (never engine.py directly from UI).
- Never modifies model files, weights, preprocessing, confidence thresholds, or engine.py.
- All style classes come from ui/styles.py LUXURY_CSS.
"""

import io
import streamlit as st
import numpy as np
from PIL import Image, ImageOps

from services import ai_service
from services import recommendation_service as rs
from services import master_catalog_service as mcs
from ui.components.navigation import navigate_to


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _hex_to_contrasting_text(hex_color: str) -> str:
    """Return #FFFFFF or #1C1917 based on luminance of given hex color."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return "#1C1917"
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.5 else "#1C1917"


# ---------------------------------------------------------------------------
# Shared Result Renderer
# ---------------------------------------------------------------------------

def _render_prediction_card(result: dict, image_rgb: np.ndarray, label: str = ""):
    """Render a full editorial analysis result card for one garment without raw HTML leaks."""

    garment_type = result["type"]
    conf_pct = result["conf_pct"]
    occasion = result["usage"]
    occ_conf_pct = result["usage_conf_pct"]
    top3 = result["top3"]
    color_name = result["color"]
    hex_color = result["hex"]
    rgb = result["rgb"]
    is_uncertain = result["is_uncertain"]
    neutral = result["neutral"]
    slot_title = result.get("slot_title", result.get("slot", "").title())

    # --- Confidence styling & badge ---
    if conf_pct >= 80 and not is_uncertain:
        conf_color = "#2A5A3A"
        conf_bg = "#EBF3ED"
        conf_label = f"Confidence: {conf_pct}%"
    elif conf_pct >= 60 and not is_uncertain:
        conf_color = "#4A2E18"
        conf_bg = "#F5EDE4"
        conf_label = f"Confidence: {conf_pct}%"
    else:
        conf_color = "#8A5A00"
        conf_bg = "#FFF8E7"
        conf_label = f"⚠️ Uncertain ({conf_pct}%)"

    # --- Occasion styling ---
    occasion_colors = {
        "Casual": ("#2D4A2D", "#EDF3ED"),
        "Formal": ("#1A2E4A", "#EDF1F7"),
        "Sports": ("#2D2A4A", "#EDEEF7"),
        "Ethnic": ("#4A2A2D", "#F7EDED"),
        "Smart Casual": ("#3A3020", "#F5F1E8"),
        "Party": ("#4A1A3A", "#F7EDF5"),
    }
    occ_colors = occasion_colors.get(occasion, ("#4A2E18", "#F5EDE4"))

    card_label_html = f"<div style='font-family:\"Cinzel\",serif;font-size:11px;letter-spacing:0.16em;color:#9A6B43;text-transform:uppercase;font-weight:700;margin-bottom:8px;'>{label}</div>" if label else ""

    # Build Top 3 candidate probability breakdown bars
    top3_bars_html = ""
    for i, (name, prob, pct) in enumerate(top3):
        bar_width = max(3, int(pct))
        bar_color = "#4A2E18" if i == 0 else "#9A6B43" if i == 1 else "#C4BAB0"
        name_weight = "700" if i == 0 else "500"
        top3_bars_html += f"""<div style="margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;margin-bottom:3px;">
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:{name_weight};color:#1C1917;">{name}</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;font-weight:600;color:#57534E;">{pct}%</span>
</div>
<div style="background:#F0ECE4;border-radius:4px;height:7px;overflow:hidden;">
<div style="background:{bar_color};width:{bar_width}%;height:100%;border-radius:4px;"></div>
</div>
</div>"""

    # Low confidence / uncertain classification card
    low_conf_warning = ""
    if is_uncertain or conf_pct < 60:
        runner_up = f" (runner-up: <strong>{top3[1][0]}</strong> at {top3[1][2]}%)" if len(top3) > 1 else ""
        low_conf_warning = f"""<div style="background:#FFFBF0;border:1px solid #F5D87A;border-radius:8px;padding:14px 18px;margin-top:20px;">
<div style="font-weight:700;color:#7A5C00;font-size:13px;margin-bottom:4px;">
⚠️ Low Classification Confidence ({conf_pct}%){runner_up}
</div>
<div style="font-size:12px;color:#57534E;line-height:1.5;">
The AI model is uncertain about this item (confidence below 60% or narrow margin with runner-up).
<br/>• If this is an accessory (such as a <em>Watch, Sunglasses, Belt, Jewellery, Hat, or Scarf</em>), these items are <strong>not supported</strong> by the 18-class neural network. Only <strong>Handbags</strong> are supported among accessories.
<br/>• For pants, trousers, or skirts, ensure the image is upright and closely cropped.
<br/>• You can verify or manually adjust the garment category below when saving to your wardrobe.
</div>
</div>"""

    neutral_tag = " · Neutral" if neutral else ""
    card_html = f"""<div style="background:#FFFFFF;border:1px solid #E8E3DA;border-radius:12px;padding:28px 32px;margin:8px 0 20px 0;box-shadow:0 4px 20px rgba(28,25,23,0.04);">
{card_label_html}
<div style="font-size:11px;letter-spacing:0.16em;text-transform:uppercase;color:#9A6B43;font-weight:700;margin-bottom:4px;">
IDENTIFIED GARMENT
</div>
<div style="font-family:'Cinzel',serif;font-size:32px;font-weight:800;color:#1C1917;letter-spacing:-0.5px;line-height:1.15;margin-bottom:12px;">
{garment_type}
</div>
<div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:22px;">
<span style="background:{conf_bg};color:{conf_color};border-radius:50px;padding:5px 16px;font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:700;">
{conf_label}
</span>
<span style="background:#F7F4EE;border:1px solid #E8E3DA;color:#57534E;border-radius:50px;padding:5px 14px;font-size:12px;font-weight:600;text-transform:uppercase;">
Slot: {slot_title}
</span>
</div>
<div style="margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid #F0ECE4;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#8C827A;margin-bottom:8px;">
SUITABLE OCCASION
</div>
<span style="background:{occ_colors[1]};color:{occ_colors[0]};border-radius:50px;padding:5px 16px;font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:600;">
{occasion}
</span>
<span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:#8C827A;margin-left:8px;">
({occ_conf_pct}% occasion confidence)
</span>
</div>
<div style="margin-bottom:22px;padding-bottom:18px;border-bottom:1px solid #F0ECE4;">
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#8C827A;margin-bottom:8px;">
DOMINANT COLOR
</div>
<div style="display:flex;align-items:center;gap:14px;">
<div style="width:48px;height:48px;border-radius:8px;background:{hex_color};border:1px solid rgba(0,0,0,0.12);flex-shrink:0;"></div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15px;font-weight:700;color:#1C1917;">
{color_name}{neutral_tag}
</div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:#8C827A;margin-top:2px;">
{hex_color.upper()} · RGB({rgb[0]}, {rgb[1]}, {rgb[2]})
</div>
</div>
</div>
</div>
<div>
<div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:11px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#8C827A;margin-bottom:12px;">
TOP 3 CANDIDATE PREDICTIONS
</div>
{top3_bars_html}
</div>
{low_conf_warning}
</div>"""

    st.html(card_html)
    return result

    return result  # pass through for wardrobe save


# ---------------------------------------------------------------------------
# Save-to-Wardrobe Widget
# ---------------------------------------------------------------------------

def _render_save_to_wardrobe(result: dict, image_rgb: np.ndarray, key_prefix: str):
    """Expandable wardrobe save panel with gender tagging, canonical slot assignment, and duplicate protection."""
    with st.expander("💾  Save to My Wardrobe", expanded=False):
        st.markdown(
            "<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:13px;color:#57534E;margin-bottom:12px;'>"
            "Confirm garment details before saving to your digital wardrobe.</p>",
            unsafe_allow_html=True
        )
        col_a, col_b = st.columns(2)
        with col_a:
            confirmed_type = st.selectbox(
                "Garment Type",
                options=result.get("types_list", [result["type"]]),
                index=result.get("types_list", [result["type"]]).index(result["type"])
                       if result["type"] in result.get("types_list", []) else 0,
                key=f"{key_prefix}_wtype"
            )
            confirmed_occasion = st.selectbox(
                "Occasion",
                options=result.get("usages_list", [result["usage"]]),
                index=result.get("usages_list", [result["usage"]]).index(result["usage"])
                       if result["usage"] in result.get("usages_list", []) else 0,
                key=f"{key_prefix}_wocc"
            )
            default_gender = "Women" if confirmed_type in ["Dresses", "Heels"] else "Unisex"
            gender_opts = ["Women", "Men", "Unisex"]
            confirmed_gender = st.selectbox(
                "Gender Compatibility",
                options=gender_opts,
                index=gender_opts.index(default_gender),
                key=f"{key_prefix}_wgender"
            )
        with col_b:
            # Canonical slot assignment
            resolved_slot = ai_service.resolve_garment_slot(confirmed_type) or result.get("slot", "top")
            slot_title = ai_service.get_slot_title(resolved_slot)
            st.markdown(
                f"<div style='margin-top:28px;padding:12px 16px;background:#FAF8F5;border-radius:8px;"
                f"border:1px solid #E8E3DA;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:13px;color:#57534E;'>"
                f"<b>Slot:</b> {slot_title}<br>"
                f"<b>Gender:</b> {confirmed_gender}<br>"
                f"<b>Color:</b> {result['color']}  ·  {result['hex'].upper()}<br>"
                f"<b>Confidence:</b> {result['conf_pct']}%"
                f"</div>",
                unsafe_allow_html=True
            )

        save_tracker_key = f"{key_prefix}_saved_item_id"
        already_saved_id = st.session_state.get(save_tracker_key)
        if already_saved_id:
            st.info(f"✓ Saved to digital wardrobe (Item ID: `{already_saved_id}`)")
        else:
            if st.button("✓  Confirm & Save", key=f"{key_prefix}_wsave", type="primary"):
                try:
                    saved = ai_service.add_garment_to_wardrobe(
                        rgb_image=image_rgb,
                        type_name=confirmed_type,
                        slot=resolved_slot,
                        occasion=confirmed_occasion,
                        confidence=result["conf"],
                        gender=confirmed_gender
                    )
                    st.session_state[save_tracker_key] = saved["id"]
                    st.toast(f"✓ Saved {confirmed_type} to wardrobe!", icon="👗")
                    st.success(f"✓  Saved to wardrobe — {confirmed_type} ({confirmed_occasion}, {confirmed_gender})")
                except Exception as e:
                    st.error(f"Save failed: {e}")


# ---------------------------------------------------------------------------
# HD Catalog Recommendations
# ---------------------------------------------------------------------------

def _render_recommendations(result: dict, key_prefix: str = "sg"):
    """Render HD catalog recommendations based on AI classification."""
    ai_class = result.get("type", "")
    usage = result.get("usage", "")
    
    st.markdown('<hr style="border-color:#ece8e0;margin:32px 0 24px 0">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div style="margin-bottom:20px;">
            <div style="font-family:'Cinzel',serif;font-size:12px;letter-spacing:0.16em;color:#9A6B43;text-transform:uppercase;margin-bottom:6px;">CATALOG SYNERGY</div>
            <h3 style="font-family:'Cinzel',serif;font-size:22px;font-weight:700;color:#1C1917;margin:0 0 6px 0;">HD Catalog Recommendations</h3>
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;color:#57534E;margin:0;">
                Matching items curated from our genuine high-resolution fashion collection.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    rec_data = rs.get_recommendations(ai_class=ai_class, occasion=usage, max_results=4)
    products = rec_data.get("products", [])
    match_level = rec_data.get("match_level", "none")
    match_label = rec_data.get("match_label", "")
    
    if match_level == "exact":
        st.markdown(
            f'<div style="background:#eef6f0;border-left:4px solid #2a5a3a;padding:10px 14px;border-radius:4px;font-size:13px;color:#1a3a22;margin-bottom:20px;font-weight:500;">✓ {match_label}</div>',
            unsafe_allow_html=True
        )
    elif match_level == "category":
        st.markdown(
            f'<div style="background:#fef9ee;border-left:4px solid #d4a373;padding:10px 14px;border-radius:4px;font-size:13px;color:#6b4724;margin-bottom:20px;">ℹ️ {match_label}</div>',
            unsafe_allow_html=True
        )
    else:
        supported_str = ", ".join(sorted(list(mcs.AI_SUPPORTED_CLASSES)))
        st.markdown(
            f"""
            <div style="background:#FAF8F5;border:1px solid #E8E3DA;padding:16px 20px;border-radius:8px;margin-bottom:20px;">
                <div style="font-weight:600;color:#1C1917;font-size:14px;margin-bottom:6px;">Category Clarification</div>
                <div style="font-size:13px;color:#57534E;line-height:1.5;">
                    The AI model currently supports 18 Western fashion categories: <em>{supported_str}</em>.<br>
                    Accessories like watches, belts, jewellery, and sunglasses are not trained categories in this model.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        return

    if not products:
        st.info("No matching products found in the catalog.")
        return

    # Render products in columns
    cols = st.columns(len(products))
    for i, prod in enumerate(products):
        with cols[i]:
            img_path = mcs.get_absolute_image_path(prod)
            name = prod.get("name", "Product")
            brand = prod.get("brand", "Curated")
            is_hd = prod.get("is_hd", False)
            
            # Image display
            if img_path and img_path.exists():
                st.image(str(img_path), use_container_width=True)
            else:
                st.markdown('<div style="height:200px;background:#f0ede8;display:flex;align-items:center;justify-content:center;color:#a08870;font-size:12px;">No Image</div>', unsafe_allow_html=True)
            
            hd_badge = '<span style="background:#2a5a3a;color:#fff;font-size:9px;padding:2px 6px;border-radius:4px;font-weight:600;">HD</span>' if is_hd else ''
            st.markdown(
                f"""
                <div style="padding:6px 0;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2px;">
                        <span style="font-size:10px;color:#8C827A;text-transform:uppercase;font-weight:600;">{brand}</span>
                        {hd_badge}
                    </div>
                    <div style="font-size:13px;font-weight:600;color:#1C1917;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{name}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            if st.button("➕ Wardrobe", key=f"{key_prefix}_rec_wb_{prod.get('id')}_{i}", use_container_width=True):
                if img_path and img_path.exists():
                    try:
                        ai_service.add_catalog_item_to_wardrobe(
                            catalog_item_path=str(img_path),
                            type_name=name,
                            slot=prod.get("slot", "top"),
                            usage=prod.get("occasion", "Casual")
                        )
                        st.toast(f"Added {name} to wardrobe!", icon="👗")
                    except Exception as ex:
                        st.error(f"Error: {ex}")
                else:
                    st.warning("Product image unavailable.")


# ---------------------------------------------------------------------------
# Tab 1: Single Garment Analyzer
# ---------------------------------------------------------------------------

def _render_single_garment_tab():
    st.markdown(
        """
        <div style="margin:28px 0 22px 0;">
            <div style="font-family:'Cinzel',serif;font-size:13px;letter-spacing:0.16em;color:#9A6B43;text-transform:uppercase;margin-bottom:8px;">INTELLIGENT ANALYSIS</div>
            <h2 style="font-family:'Cinzel',serif;font-size:28px;font-weight:700;color:#1C1917;margin:0 0 10px 0;line-height:1.2;">Single Garment Classifier</h2>
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15px;color:#57534E;max-width:560px;line-height:1.65;margin:0;">
                Upload any single clothing item. The AI will identify its type, dominant color, and occasion using 
                the ensemble CNN + KNN architecture — giving you an editorial-precision breakdown.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_upload, col_result = st.columns([1, 1.5], gap="large")

    with col_upload:
        st.markdown(
            "<p style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:11px;font-weight:600;"
            "letter-spacing:0.1em;text-transform:uppercase;color:#8C827A;margin-bottom:8px;'>UPLOAD GARMENT</p>",
            unsafe_allow_html=True
        )
        uploaded = st.file_uploader(
            "Drop an image here",
            type=["png", "jpg", "jpeg", "webp"],
            key="sg_uploader",
            label_visibility="collapsed"
        )

        if uploaded:
            # Clear previous results if new file uploaded
            curr_file_id = getattr(uploaded, "file_id", getattr(uploaded, "name", None))
            if st.session_state.get("sg_active_file_id") != curr_file_id:
                st.session_state["sg_active_file_id"] = curr_file_id
                st.session_state.pop("sg_last_result", None)
                st.session_state.pop("sg_last_image", None)
                st.session_state.pop("sg_analyzing", None)

            img_pil = ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
            st.image(img_pil, use_container_width=True, caption="Uploaded garment")

            st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

            if st.button("✦  Analyze Garment", key="sg_analyze", type="primary", use_container_width=True):
                st.session_state["sg_analyzing"] = True

    with col_result:
        if uploaded and st.session_state.get("sg_analyzing"):
            img_pil = ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
            img_rgb = np.array(img_pil)

            with st.spinner("Analyzing garment..."):
                try:
                    result = ai_service.analyze_single_garment(img_rgb)
                    st.session_state["sg_last_result"] = result
                    st.session_state["sg_last_image"] = img_rgb
                    st.session_state["sg_analyzing"] = False
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.session_state["sg_analyzing"] = False
                    return

        if uploaded and st.session_state.get("sg_last_result") is not None:
            result = st.session_state["sg_last_result"]
            img_rgb = st.session_state["sg_last_image"]
            _render_prediction_card(result, img_rgb)
            _render_save_to_wardrobe(result, img_rgb, key_prefix="sg")
            _render_recommendations(result, key_prefix="sg")

        elif not uploaded:
            # Placeholder prompt
            st.markdown(
                """
                <div style="border:2px dashed #E8E3DA;border-radius:12px;padding:60px 32px;text-align:center;background:#FAF8F5;margin-top:16px;">
                    <div style="font-size:36px;margin-bottom:16px;">👗</div>
                    <div style="font-family:'Cinzel',serif;font-size:15px;color:#8C827A;letter-spacing:0.06em;">Upload a garment to begin analysis</div>
                    <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#C4BAB0;margin-top:8px;">PNG · JPG · JPEG · WEBP</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    # Reset state when file cleared
    if not uploaded:
        st.session_state.pop("sg_active_file_id", None)
        st.session_state.pop("sg_analyzing", None)
        st.session_state.pop("sg_last_result", None)
        st.session_state.pop("sg_last_image", None)


# ---------------------------------------------------------------------------
# Tab 2: Full-Body / Multi-Garment
# ---------------------------------------------------------------------------

def _render_multi_garment_tab():
    st.markdown(
        """
        <div style="margin:28px 0 22px 0;">
            <div style="font-family:'Cinzel',serif;font-size:13px;letter-spacing:0.16em;color:#9A6B43;text-transform:uppercase;margin-bottom:8px;">POSE-AWARE CROPPING</div>
            <h2 style="font-family:'Cinzel',serif;font-size:28px;font-weight:700;color:#1C1917;margin:0 0 10px 0;line-height:1.2;">Full-Body Multi-Garment</h2>
            <p style="font-family:'Plus Jakarta Sans',sans-serif;font-size:15px;color:#57534E;max-width:560px;line-height:1.65;margin:0;">
                Upload a full-body photo. MediaPipe detects body keypoints, crops the upper and lower garment 
                regions separately, and classifies each one independently.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded = st.file_uploader(
        "Drop a full-body photo",
        type=["png", "jpg", "jpeg", "webp"],
        key="mg_uploader",
        label_visibility="collapsed"
    )

    if uploaded:
        # Clear previous multi-garment results if a new file is uploaded
        curr_file_id = getattr(uploaded, "file_id", getattr(uploaded, "name", None))
        if st.session_state.get("mg_active_file_id") != curr_file_id:
            st.session_state["mg_active_file_id"] = curr_file_id
            st.session_state.pop("mg_pose_result", None)
            st.session_state.pop("mg_crop_results", None)
            st.session_state.pop("mg_fallback_result", None)
            st.session_state.pop("mg_analyzing", None)

        img_pil = ImageOps.exif_transpose(Image.open(uploaded)).convert("RGB")
        img_rgb = np.array(img_pil)

        col_prev, col_btn = st.columns([2, 1], gap="medium")
        with col_prev:
            st.image(img_pil, use_container_width=True, caption="Full-body upload")
        with col_btn:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("✦  Detect & Analyze", key="mg_analyze", type="primary", use_container_width=True):
                st.session_state["mg_analyzing"] = True

        if st.session_state.get("mg_analyzing"):
            with st.spinner("Detecting pose and cropping garments..."):
                try:
                    pose_result = ai_service.analyze_full_body_crops(img_rgb)
                    st.session_state["mg_pose_result"] = pose_result
                except Exception as e:
                    st.error(f"Pose detection failed: {e}")
                    st.session_state.pop("mg_analyzing", None)
                    return

            if not pose_result["has_pose"]:
                # Fallback: analyze full image as a single garment
                with st.spinner("Running single-garment fallback..."):
                    try:
                        fallback_res = ai_service.analyze_single_garment(img_rgb)
                        st.session_state["mg_fallback_result"] = fallback_res
                    except Exception as e:
                        st.error(f"Fallback analysis failed: {e}")
            else:
                parts = pose_result["parts"]
                crop_results = {}
                for part_name, crop_rgb in parts.items():
                    try:
                        pred = ai_service.analyze_single_garment(crop_rgb)
                        crop_results[part_name] = (pred, crop_rgb)
                    except Exception as e:
                        st.error(f"{part_name} analysis failed: {e}")
                st.session_state["mg_crop_results"] = crop_results

            st.session_state["mg_analyzing"] = False

        # Render cached results
        pose_res = st.session_state.get("mg_pose_result")
        if pose_res is not None:
            if not pose_res["has_pose"]:
                st.markdown(
                    """
                    <div style="background:#FEF3CD;border:1px solid #F5D87A;border-radius:10px;padding:18px 22px;margin:16px 0;
                                font-family:'Plus Jakarta Sans',sans-serif;font-size:14px;color:#7A5C00;">
                        ⚠  <strong>No body pose detected</strong> — the uploaded photo did not yield clear body landmarks.
                        Switching to single-garment classification of the full image.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                fallback_res = st.session_state.get("mg_fallback_result")
                if fallback_res is not None:
                    _render_prediction_card(fallback_res, img_rgb, label="Single Garment (Fallback)")
                    _render_save_to_wardrobe(fallback_res, img_rgb, key_prefix="mg_fallback")
            else:
                parts = pose_res["parts"]  # {"Upper body": ndarray, "Lower body": ndarray}
                st.markdown(
                    "<div style='font-family:\"Plus Jakarta Sans\",sans-serif;font-size:13px;font-weight:600;"
                    "letter-spacing:0.08em;text-transform:uppercase;color:#9A6B43;margin:22px 0 16px 0;'>✓ Pose Detected — 2 Garment Regions Found</div>",
                    unsafe_allow_html=True
                )

                crop_cols = st.columns(len(parts), gap="large")
                for i, (part_name, crop_rgb) in enumerate(parts.items()):
                    crop_pil = Image.fromarray(crop_rgb)
                    with crop_cols[i]:
                        st.image(crop_pil, use_container_width=True, caption=f"{part_name} crop")

                st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                crop_results = st.session_state.get("mg_crop_results", {})
                if crop_results:
                    result_cols = st.columns(len(crop_results), gap="large")
                    for i, (part_name, (pred, crop_rgb)) in enumerate(crop_results.items()):
                        with result_cols[i]:
                            _render_prediction_card(pred, crop_rgb, label=part_name)
                            _render_save_to_wardrobe(pred, crop_rgb, key_prefix=f"mg_{i}")

                    for i, (part_name, (pred, crop_rgb)) in enumerate(crop_results.items()):
                        with st.expander(f"✨ HD Recommendations for {part_name} ({pred.get('type')})", expanded=(i == 0)):
                            _render_recommendations(pred, key_prefix=f"mg_rec_{i}")

    else:
        st.markdown(
            """
            <div style="border:2px dashed #E8E3DA;border-radius:12px;padding:60px 32px;text-align:center;background:#FAF8F5;margin-top:16px;">
                <div style="font-size:36px;margin-bottom:16px;">🧍</div>
                <div style="font-family:'Cinzel',serif;font-size:15px;color:#8C827A;letter-spacing:0.06em;">Upload a full-body photo to begin</div>
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;color:#C4BAB0;margin-top:8px;">Works best with clear, well-lit full-body shots</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.session_state.pop("mg_active_file_id", None)
        st.session_state.pop("mg_analyzing", None)
        st.session_state.pop("mg_pose_result", None)
        st.session_state.pop("mg_crop_results", None)
        st.session_state.pop("mg_fallback_result", None)


# ---------------------------------------------------------------------------
# Main Entry Point
# ---------------------------------------------------------------------------

def render_ai_studio():
    """Render the AI Fashion Studio page."""

    # Page header
    st.markdown(
        """
        <div style="border-bottom:1px solid #E8E3DA;padding-bottom:22px;margin-bottom:4px;">
            <span style="font-family:'Cinzel',serif;font-size:11px;letter-spacing:0.2em;color:#9A6B43;text-transform:uppercase;">
                PHASE 4 · STEP 2
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    tab1, tab2 = st.tabs(["  🧥  Single Garment  ", "  🧍  Full-Body Multi-Garment  "])

    with tab1:
        _render_single_garment_tab()

    with tab2:
        _render_multi_garment_tab()

    # Footer spacer
    st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <div style="border-top:1px solid #E8E3DA;padding-top:20px;text-align:center;font-family:'Plus Jakarta Sans',sans-serif;font-size:12px;color:#C4BAB0;">
            CNN + KNN Ensemble · Original Engine · Confidence Thresholds: 60% absolute · 25% margin
        </div>
        """,
        unsafe_allow_html=True
    )
