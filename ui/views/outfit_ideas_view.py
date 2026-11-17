"""
Style Mate AI — Harmonious Outfit Ideas View
==============================================
Intelligent combinatorial wardrobe outfit generator utilizing:
- Circular hue harmony & color compatibility checks from original engine
- Neutral pairing evaluations
- Occasion compatibility matrices
- Natural language pairing rationale (engine.explain)
- Dual source support: Personal Digital Wardrobe & Master HD Catalog Collections
- Strict gender isolation: Men / Women / Unisex — filtered BEFORE all scoring
- Graceful empty/sparse wardrobe fallback
"""

import base64
import json
import itertools
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import streamlit as st
import numpy as np
import pandas as pd

import engine
from services import ai_service
from services import master_catalog_service as mcs

ROOT = Path(__file__).resolve().parent.parent.parent
MASTER_JSON = ROOT / "catalog" / "master_products.json"

# ---------------------------------------------------------------------------
# GENDER CONSTANTS
# ---------------------------------------------------------------------------
GENDER_MEN = "👔 Men's Outfits"
GENDER_WOMEN = "👗 Women's Outfits"
GENDER_UNISEX = "✨ Unisex / Shared Outfits"

_GENDER_ALLOWED = {
    GENDER_MEN:    {"men", "unisex"},
    GENDER_WOMEN:  {"women", "unisex"},
    GENDER_UNISEX: {"unisex"},
}

_GENDER_BADGE_COLORS = {
    "men":    ("#D6EAF8", "#1A5276", "Men"),
    "women":  ("#FDEDEC", "#7B241C", "Women"),
    "unisex": ("#EAF7F0", "#1D6A45", "Unisex"),
    "boys":   ("#FEF9E7", "#7D6608", "Boys"),
    "girls":  ("#F9EBF9", "#6C3483", "Girls"),
}


def _gender_badge_html(gender_raw: str) -> str:
    """Return a small colored badge span for the given raw gender string."""
    key = str(gender_raw).strip().lower() if gender_raw else "unknown"
    bg, fg, label = _GENDER_BADGE_COLORS.get(key, ("#F0ECE4", "#57534E", str(gender_raw or "?").title()))
    return (
        f'<span style="background:{bg};color:{fg};font-size:10px;font-weight:700;'
        f'padding:2px 8px;border-radius:10px;letter-spacing:0.06em;'
        f'text-transform:uppercase;">{label}</span>'
    )


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _image_b64(path: Path) -> str:
    try:
        return base64.b64encode(path.read_bytes()).decode()
    except Exception:
        return ""


def _resolve_hd_image_path(piece: dict) -> Path:
    """Resolve piece to its authentic HD image path if available."""
    # 1. image_path field (master catalog entries)
    if "image_path" in piece:
        p = ROOT / piece["image_path"]
        if p.exists():
            return p
    # 2. path field (engine catalog entries) — try images_hd first
    orig_path = piece.get("path", "")
    if orig_path:
        stem = Path(orig_path).stem
        hd_cand = ROOT / "catalog" / "images_hd" / f"{stem}.jpg"
        if hd_cand.exists():
            return hd_cand
        p = ROOT / orig_path
        if p.exists():
            return p
    return ROOT / "catalog" / "images_hd" / "15259.jpg"


# ---------------------------------------------------------------------------
# MASTER 746-ITEM DATAFRAME
# ---------------------------------------------------------------------------

def _load_master_df() -> pd.DataFrame:
    """
    Build a unified 746-row DataFrame from master_products.json enriched with
    color / neutral / hue from the engine's catalog_index.csv.

    Columns returned (minimum set needed by engine.suggest + gender filter):
        path, type, usage, gender, slot, color, neutral, hue,
        image_path, name, id, worn
    """
    # Load 720-item engine catalog (has accurate color/neutral/hue from PIL)
    cat = ai_service.get_catalog()
    df_engine = cat.df.copy()
    df_engine["_fname"] = df_engine["path"].map(lambda p: Path(str(p)).name)

    # Load 746-item master products
    with open(MASTER_JSON, encoding="utf-8") as f:
        master = json.load(f)
    df_master = pd.DataFrame(master)

    # Map occasion field: master uses 'occasion', engine uses 'usage'
    if "occasion" in df_master.columns and "usage" not in df_master.columns:
        df_master["usage"] = df_master["occasion"]
    elif "occasion" in df_master.columns:
        # Prefer the master's occasion value if it exists
        df_master["usage"] = df_master["occasion"]

    df_master["_fname"] = df_master["image_path"].map(lambda p: Path(str(p)).name)

    # Merge to pull color / neutral / hue from engine catalog (720 items)
    # For the 26 curated brands, derive from their 'color' string field
    color_map = df_engine.set_index("_fname")[["color", "neutral", "hue"]].to_dict("index")

    rows = []
    for _, row in df_master.iterrows():
        fname = row["_fname"]
        if fname in color_map:
            color = color_map[fname]["color"]
            neutral = color_map[fname]["neutral"]
            hue = color_map[fname]["hue"]
        else:
            # Derive color info from the product's color name string
            color_name = str(row.get("color", "gray")).lower().strip()
            # Map common strings to engine-compatible neutrals
            if color_name in {"black", "white", "gray", "grey", "beige", "navy", "denim", "cream", "off-white", "off white"}:
                color = color_name if color_name != "grey" else "gray"
                neutral = True
                hue = 0.0
            else:
                color = color_name
                neutral = False
                hue = 0.5  # neutral mid-wheel fallback

        type_str = str(row.get("ai_class") or row.get("category") or "Garment")
        resolved_slot = ai_service.resolve_garment_slot(type_str) or str(row.get("slot") or "top")

        rows.append({
            "path":       str(ROOT / row["image_path"]),
            "image_path": str(row["image_path"]),
            "type":       type_str,
            "usage":      str(row.get("usage") or row.get("occasion") or "Casual"),
            "gender":     str(row.get("gender") or ""),
            "slot":       resolved_slot,
            "color":      color,
            "neutral":    neutral,
            "hue":        hue,
            "name":       str(row.get("name") or ""),
            "id":         str(row.get("id") or ""),
            "worn":       0,
        })

    df = pd.DataFrame(rows)
    return df


# ---------------------------------------------------------------------------
# CATALOG WARDROBE ADAPTER WITH GENDER PRE-FILTERING
# ---------------------------------------------------------------------------

class CatalogWardrobeAdapter:
    """
    Adapts catalog items into Wardrobe-compatible interface for engine.suggest.
    Gender filtering is applied FIRST, before any scoring or slot grouping.
    """
    def __init__(
        self,
        df: pd.DataFrame,
        occasion: str = "Any",
        gender_mode: str = GENDER_WOMEN,
        max_per_slot: int = 16,
        seed: int = 42,
    ):
        self.df = df.copy()

        # ---- STEP 1: GENDER PRE-FILTER (BEFORE EVERYTHING ELSE) ----
        allowed = _GENDER_ALLOWED.get(gender_mode, {"women", "unisex"})
        gender_norm = self.df["gender"].astype(str).str.strip().str.lower()
        gender_mask = gender_norm.isin(allowed)
        self.df = self.df[gender_mask].reset_index(drop=True)

        # ---- STEP 2: Occasion compatibility filter ----
        if occasion != "Any":
            compat_mask = self.df["usage"].map(
                lambda u: engine.usage_compat(occasion, u) >= 60
            )
            if compat_mask.any():
                self.df = self.df[compat_mask].reset_index(drop=True)

        self.seed = seed
        self.max_per_slot = max_per_slot
        self.gender_mode = gender_mode

    def by_slot(self, slot: str) -> List[Dict[str, Any]]:
        sub = self.df[self.df["slot"] == slot]
        if sub.empty:
            return []
        sampled = sub.sample(n=min(len(sub), self.max_per_slot), random_state=self.seed)
        records = sampled.to_dict("records")
        for r in records:
            if "worn" not in r:
                r["worn"] = 0
            if not r.get("id"):
                r["id"] = Path(str(r.get("path", "item"))).stem
        return records


# ---------------------------------------------------------------------------
# UNISEX MULTI-COMBINATION SUGGEST
# ---------------------------------------------------------------------------

def _deduplicate_outfit_list(
    outfits: List[Tuple[int, List[Dict[str, Any]]]],
    max_items: int = 6
) -> List[Tuple[int, List[Dict[str, Any]]]]:
    """Strictly deduplicate an outfit list by order-independent product ID set
    AND visual content signature (slot + type + color).
    Guarantees no repeated outfits or reordered permutations.
    """
    unique_outfits = []
    seen_id_sets: set = set()
    seen_content_sigs: set = set()

    for score, pieces in outfits:
        # 1. Order-independent ID set
        id_set = frozenset(str(p.get("id") or p.get("path") or id(p)) for p in pieces)
        # 2. Content signature
        content_sig = tuple(sorted((
            str(p.get("slot", "")).lower(),
            str(p.get("type", "") or p.get("name", "")).lower(),
            str(p.get("color", "")).lower()
        ) for p in pieces))

        if id_set in seen_id_sets or content_sig in seen_content_sigs:
            continue

        seen_id_sets.add(id_set)
        seen_content_sigs.add(content_sig)
        unique_outfits.append((score, pieces))
        if len(unique_outfits) >= max_items:
            break

    return unique_outfits


def _suggest_with_accessory_variety(
    adapter: CatalogWardrobeAdapter,
    occasion: str,
    n: int,
    seed: int = 0,
    exclude_ids: Optional[set] = None,
    return_total: bool = False,
):
    """Extended engine.suggest that explores alternative accessory combinations
    to generate >= n distinct outfits even with limited base pieces, strictly
    deduplicates all outcomes so no identical or reordered outfits appear, and
    prioritizes fresh, unseen combinations across refresh clicks.
    """
    tops = adapter.by_slot("top")
    bottoms = adapter.by_slot("bottom")
    dresses = adapter.by_slot("dress")
    outers = adapter.by_slot("outer")
    shoes_pool = adapter.by_slot("shoes")
    bags_pool = adapter.by_slot("bag")

    bases = [(t, b) for t in tops for b in bottoms] + [(d,) for d in dresses]
    if not bases:
        return [], 0

    effective_seed = seed if seed != 0 else adapter.seed

    # Shuffle bases with seed so fresh candidate combinations are prioritized on each refresh click
    rng = np.random.default_rng(effective_seed)
    shuffled_bases = list(bases)
    rng.shuffle(shuffled_bases)

    # Accessory pools (pad with None if empty)
    shoe_choices = shoes_pool if shoes_pool else [None]
    bag_choices = bags_pool if bags_pool else [None]
    outer_choices = outers if outers else [None]

    all_outfits: List[Tuple[int, List[Dict[str, Any]]]] = []

    # Explore combinations across bases and accessories
    # Evaluate up to 40 shuffled bases for interactive performance while guaranteeing diversity
    for base in shuffled_bases[:40]:
        for shoe in shoe_choices[:4]:
            for bag in bag_choices[:3]:
                pieces = list(base)
                if shoe:
                    score_s = np.mean([engine.pair_score(shoe, p) for p in pieces])
                    if score_s >= 65:
                        pieces = pieces + [shoe]
                if outer_choices[0] is not None:
                    for outer in outer_choices[:3]:
                        score_o = np.mean([engine.pair_score(outer, p) for p in pieces])
                        if score_o >= 65:
                            pieces = pieces + [outer]
                            break
                if bag:
                    score_b = np.mean([engine.pair_score(bag, p) for p in pieces])
                    if score_b >= 65:
                        pieces = pieces + [bag]

                if len(pieces) < 2:
                    continue

                pair_scores = [engine.pair_score(a, b)
                               for i, a in enumerate(pieces)
                               for b in pieces[i + 1:]] or [75]
                score = float(np.mean(pair_scores))
                if occasion != "Any":
                    score += 0.15 * float(np.mean([engine.usage_compat(occasion, p["usage"]) for p in pieces])) - 10
                score -= 2 * min(float(np.mean([p.get("worn", 0) for p in pieces])), 5)
                score = round(max(0, min(100, score)))

                all_outfits.append((score, pieces))

    all_outfits.sort(key=lambda x: -x[0])
    deduped = _deduplicate_outfit_list(all_outfits, max_items=max(n * 6, 60))
    total_unique = len(deduped)

    if total_unique <= n:
        res = deduped
        return (res, total_unique) if return_total else res

    # If exclude_ids provided, prioritize fresh combinations not shown in previous cycles
    if exclude_ids:
        unseen = [o for o in deduped if _outfit_id_key(o[1]) not in exclude_ids]
        if len(unseen) >= n:
            res = _deduplicate_outfit_list(unseen[:n], max_items=n)
            return (res, total_unique) if return_total else res
        elif unseen:
            fillers = [o for o in deduped if _outfit_id_key(o[1]) in exclude_ids]
            res = _deduplicate_outfit_list((unseen + fillers)[:n], max_items=n)
            return (res, total_unique) if return_total else res

    # When ample combinations exist, rotate starting offset using seed
    offset = (effective_seed * n) % total_unique
    selected = deduped[offset : offset + n]
    if len(selected) < n:
        selected += deduped[: n - len(selected)]
    res = _deduplicate_outfit_list(selected, max_items=n)
    return (res, total_unique) if return_total else res


# ---------------------------------------------------------------------------
# OUTFIT CARD RENDERER
# ---------------------------------------------------------------------------

def _render_outfit_card(
    score: int,
    pieces: list,
    occasion: str,
    idx: int,
    source_type: str = "catalog",
):
    """Render a single harmonious outfit card with gender badges on each piece."""
    if score >= 90:
        score_bg, score_fg, rating = "#EBF3ED", "#2A5A3A", "Exceptional Harmony"
    elif score >= 75:
        score_bg, score_fg, rating = "#F5EDE4", "#4A2E18", "Harmonious Ensemble"
    else:
        score_bg, score_fg, rating = "#F9F3EC", "#9A6B43", "Balanced Match"

    # Compute harmony explanations between all pairs
    explanations = []
    for i, a in enumerate(pieces):
        for b in pieces[i + 1:]:
            why = engine.explain(a, b)
            if why and why not in explanations:
                explanations.append(why)

    st.markdown(
        f"""
<div style="background:#FFFFFF;border:1px solid #E8E3DA;border-radius:12px;padding:24px 28px;
            margin-bottom:28px;box-shadow:0 4px 20px rgba(28,25,23,0.04);">
  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;
              border-bottom:1px solid #F0ECE4;padding-bottom:16px;margin-bottom:20px;">
    <div>
      <span style="font-family:'Cinzel',serif;font-size:11px;letter-spacing:0.16em;text-transform:uppercase;color:#9A6B43;font-weight:700;">
        CURATED ENSEMBLE #{idx + 1}
      </span>
      <div style="font-family:'Cinzel',serif;font-size:22px;font-weight:700;color:#1C1917;margin-top:2px;">
        {occasion if occasion != 'Any' else 'Versatile'} Occasion
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:10px;">
      <span style="background:{score_bg};color:{score_fg};border-radius:50px;padding:6px 18px;
                   font-family:'Plus Jakarta Sans',sans-serif;font-size:13px;font-weight:700;">
        ★ {score} / 100 · {rating}
      </span>
    </div>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # Piece cards side-by-side
    cols = st.columns(len(pieces), gap="medium")
    for i, p in enumerate(pieces):
        with cols[i]:
            img_path = _resolve_hd_image_path(p)
            slot_title = engine.SLOT_TITLE.get(p.get("slot"), str(p.get("slot", "")).title())
            p_name = p.get("name") or p.get("type", "Garment")
            color = str(p.get("color", "")).title()
            usage = p.get("usage", "Casual")
            p_gender = str(p.get("gender", "")).strip()
            gender_badge = _gender_badge_html(p_gender)

            if img_path.exists():
                b64 = _image_b64(img_path)
                img_tag = (
                    f'<img src="data:image/jpeg;base64,{b64}" '
                    f'style="width:100%;height:220px;object-fit:contain;'
                    f'background:#FAF8F5;border-radius:6px;" alt="{p_name}" />'
                )
            else:
                img_tag = (
                    '<div style="height:220px;background:#FAF8F5;display:flex;'
                    'align-items:center;justify-content:center;color:#8C827A;'
                    'font-size:12px;">Image</div>'
                )

            st.markdown(
                f"""
<div style="text-align:center;background:#FAF8F5;padding:12px;border-radius:8px;border:1px solid #F0ECE4;">
  <div style="font-size:10px;letter-spacing:0.12em;text-transform:uppercase;font-weight:700;color:#9A6B43;margin-bottom:6px;">
    {slot_title}
  </div>
  {img_tag}
  <div style="font-size:13px;font-weight:600;color:#1C1917;margin-top:8px;line-height:1.3;">
    {p_name}
  </div>
  <div style="font-size:11px;color:#8C827A;margin-top:2px;">
    {color} · {usage}
  </div>
  <div style="margin-top:5px;">
    {gender_badge}
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )

    # Harmony rationale
    if explanations:
        expl_html = "".join([
            f'<span style="background:#F7F4EE;border:1px solid #E8E3DA;color:#57534E;'
            f'font-size:11px;padding:4px 12px;border-radius:20px;font-weight:500;">'
            f'✓ {e}</span>'
            for e in explanations[:3]
        ])
        st.markdown(
            f"""
<div style="margin-top:18px;padding-top:14px;border-top:1px solid #F0ECE4;">
  <div style="font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:#8C827A;margin-bottom:8px;">
    HARMONY RATIONALE (CIRCULAR HUE &amp; NEUTRALS):
  </div>
  <div style="display:flex;gap:8px;flex-wrap:wrap;">
    {expl_html}
  </div>
</div>
            """,
            unsafe_allow_html=True,
        )

    # Action buttons
    act_col1, act_col2 = st.columns([1, 1])
    with act_col1:
        if source_type == "catalog":
            if st.button(
                "➕ Save All Pieces to Wardrobe",
                key=f"oi_save_all_{idx}",
                use_container_width=True,
            ):
                count_saved = 0
                for p in pieces:
                    try:
                        p_img = _resolve_hd_image_path(p)
                        ai_service.add_catalog_item_to_wardrobe(
                            catalog_item_path=str(p_img),
                            type_name=p.get("type", "Garment"),
                            slot=p.get("slot", "top"),
                            usage=p.get("usage", "Casual"),
                        )
                        count_saved += 1
                    except Exception:
                        pass
                st.toast(f"✓ Saved {count_saved} pieces to your Digital Wardrobe!", icon="👗")
        else:
            if st.button(
                "✓ Mark Outfit as Worn Today",
                key=f"oi_mark_worn_{idx}",
                use_container_width=True,
            ):
                pids = [str(p.get("id")) for p in pieces if p.get("id")]
                ai_service.record_outfit_worn(pids)
                st.toast("✓ Outfit recorded! Rotation algorithm updated.", icon="✨")
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# MAIN VIEW
# ---------------------------------------------------------------------------

def render_outfit_ideas_view():
    """Main entrypoint for the Harmonious Outfit Ideas page."""

    # Editorial Header
    st.markdown(
        """
<div style="margin-bottom:28px;">
  <div style="font-family:'Cinzel',serif;font-size:11px;color:#9A6B43;text-transform:uppercase;letter-spacing:2px;margin-bottom:6px;">
    STYLE MATE AI · ENSEMBLE INTELLIGENCE
  </div>
  <div style="font-family:'Cinzel',serif;font-size:32px;font-weight:800;color:#1C1917;letter-spacing:-0.5px;line-height:1.1;margin-bottom:8px;">
    Harmonious Outfit Generator
  </div>
  <div style="font-size:15px;color:#57534E;font-style:italic;max-width:720px;line-height:1.5;">
    Combinatorial wardrobe suggestions scored by circular hue harmony, neutral balance, and occasion
    heuristics using the trained Style Mate AI engine. Gender filtering is applied strictly before scoring.
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Control Bar ----
    ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([1.6, 1.2, 1.4], gap="medium")

    with ctrl_c1:
        source_mode = st.radio(
            "Ensemble Source",
            ["✨ Master HD Catalog Collections", "👔 My Personal Wardrobe"],
            index=0,
            horizontal=True,
            key="oi_source_mode",
            label_visibility="collapsed",
        )

    with ctrl_c2:
        gender_mode = st.selectbox(
            "Gender",
            [GENDER_WOMEN, GENDER_MEN, GENDER_UNISEX],
            index=0,
            key="oi_gender_mode",
            label_visibility="collapsed",
        )

    with ctrl_c3:
        occasions = ["Any Occasion", "Casual", "Formal", "Sports", "Ethnic", "Party", "Smart Casual"]
        selected_occ = st.selectbox(
            "Occasion", occasions, key="oi_occasion_select", label_visibility="collapsed"
        )
        occ_query = "Any" if selected_occ == "Any Occasion" else selected_occ

    # Dedicated, prominent button for generating new outfits on each click
    btn_c1, btn_c2 = st.columns([2.0, 1.4], gap="medium")
    with btn_c1:
        if st.button("✨  Generate New Outfits / Refresh Recommendations", key="oi_refresh_btn", type="primary", use_container_width=True):
            st.session_state["oi_seed"] = st.session_state.get("oi_seed", 0) + 1
            st.rerun()

    current_seed = st.session_state.get("oi_seed", 0)
    with btn_c2:
        st.markdown(
            f"<div style='padding-top:10px;font-family:\"Plus Jakarta Sans\",sans-serif;font-size:12px;color:#8C827A;'>"
            f"Active Generation Cycle: <strong>#{current_seed + 1}</strong> · Rotates candidate combinations</div>",
            unsafe_allow_html=True
        )

    # Gender mode info banner
    gender_info = {
        GENDER_WOMEN:  ("👗", "Women's Outfits",  "Only Women and Unisex products are included. Men's, Boys', and Girls' products are excluded."),
        GENDER_MEN:    ("👔", "Men's Outfits",    "Only Men and Unisex products are included. Women's, Boys', and Girls' products are excluded."),
        GENDER_UNISEX: ("✨", "Unisex Outfits",   "Only explicitly Unisex products are included. No Men's or Women's items appear here."),
    }
    g_icon, g_title, g_desc = gender_info.get(gender_mode, gender_info[GENDER_WOMEN])
    st.markdown(
        f"""
<div style="background:#F7F4EE;border:1px solid #E8E3DA;border-radius:8px;padding:10px 16px;
            margin:8px 0 20px 0;display:flex;align-items:center;gap:12px;">
  <span style="font-size:20px;">{g_icon}</span>
  <div>
    <strong style="font-size:13px;color:#1C1917;">{g_title}</strong>
    <span style="font-size:12px;color:#57534E;margin-left:8px;">{g_desc}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<hr style='border-color:#E8E3DA;margin:0 0 24px 0;'>", unsafe_allow_html=True)

    # ---- Mode 1: Personal Wardrobe ----
    if "My Personal Wardrobe" in source_mode:
        wardrobe = ai_service.get_wardrobe()
        total_items = len(wardrobe.items)
        tops = len(wardrobe.by_slot("top"))
        bottoms = len(wardrobe.by_slot("bottom"))
        dresses = len(wardrobe.by_slot("dress"))

        if total_items < 2 or (tops == 0 and dresses == 0) or (bottoms == 0 and dresses == 0):
            st.markdown(
                f"""
<div style="background:#FFFBF0;border:1px solid #F5D87A;border-radius:12px;padding:32px 36px;margin:20px 0;text-align:center;">
  <div style="font-size:32px;margin-bottom:12px;">👗</div>
  <div style="font-family:'Cinzel',serif;font-size:20px;font-weight:700;color:#1C1917;margin-bottom:8px;">
    Personal Wardrobe Needs More Pieces
  </div>
  <div style="font-size:14px;color:#57534E;max-width:580px;margin:0 auto 20px auto;line-height:1.6;">
    Your digital wardrobe currently contains <strong>{total_items} piece(s)</strong>
    ({tops} tops, {bottoms} bottoms, {dresses} dresses).
    To assemble complete outfits, please add at least one Top and one Bottom (or a Dress)
    via the AI Studio or Catalog.
  </div>
</div>
                """,
                unsafe_allow_html=True,
            )
            c1, c2, c3 = st.columns([1, 1.8, 1])
            with c2:
                if st.button(
                    "✦ Generate Outfits from Master HD Catalog Instead",
                    key="oi_switch_cat",
                    type="primary",
                    use_container_width=True,
                ):
                    st.rerun()
            return

        seen_wb_ids = st.session_state.get("oi_wb_seen_ids", set())
        with st.spinner("Calculating harmonious combinations from your wardrobe..."):
            outfits, total_unique = ai_service.generate_diverse_outfit_combinations(
                wardrobe, occasion=occ_query, gender_mode=gender_mode, n=6, seed=current_seed, exclude_ids=seen_wb_ids
            )
            # Track seen outfit ID sets for subsequent refresh cycles
            for _, pieces in outfits:
                seen_wb_ids.add(frozenset(str(p.get("id") or p.get("path") or id(p)) for p in pieces))
            if len(seen_wb_ids) > 120:
                seen_wb_ids = set()
            st.session_state["oi_wb_seen_ids"] = seen_wb_ids

        if not outfits:
            st.warning(
                f"⚠️ No compatible outfits found for **{g_title}** in **{selected_occ}**. "
                f"Try selecting a different occasion or adding more garments to your collection."
            )
            return

        st.markdown(
            f"<div style='font-family:Cinzel,serif;font-size:13px;letter-spacing:0.12em;"
            f"text-transform:uppercase;color:#8C827A;margin-bottom:12px;'>"
            f"Showing {len(outfits)} unique personalized outfit{'s' if len(outfits) > 1 else ''} from your wardrobe (Generation #{current_seed + 1})</div>",
            unsafe_allow_html=True,
        )

        # Honest result count notice when wardrobe has limited unique combinations
        if total_unique < 6:
            st.markdown(
                f"""
<div style="background:#FFFBF0;border:1px solid #F5D87A;border-radius:8px;padding:12px 18px;margin-bottom:20px;display:flex;align-items:center;gap:10px;">
  <span style="font-size:18px;">💡</span>
  <span style="font-size:13px;color:#7A5510;">
    <strong>Wardrobe Variety Notice:</strong> {total_unique} distinct harmonious combination{'s' if total_unique > 1 else ''} could be formed with your current wardrobe items. Add more tops, bottoms, shoes, or outerwear to unlock additional ensemble variety.
  </span>
</div>
                """,
                unsafe_allow_html=True,
            )

        for idx, (score, pieces) in enumerate(outfits):
            _render_outfit_card(score, pieces, occ_query, idx, source_type="wardrobe")

    # ---- Mode 2: Master HD Catalog (746 items, gender-filtered) ----
    else:
        with st.spinner(f"Curating harmonious {g_title} from 746 Master HD products…"):
            master_df = _load_master_df()
            adapter = CatalogWardrobeAdapter(
                master_df,
                occasion=occ_query,
                gender_mode=gender_mode,
                max_per_slot=16,
                seed=current_seed,
            )

            # Check if there are enough base pieces
            tops = adapter.by_slot("top")
            bottoms = adapter.by_slot("bottom")
            dresses = adapter.by_slot("dress")
            has_bases = (tops and bottoms) or dresses

            if not has_bases:
                st.warning(
                    f"⚠️ Not enough compatible products for **{g_title}** in **{selected_occ}**. "
                    f"Try selecting *Any Occasion* or a different gender category."
                )
                return

            seen_cat_ids = st.session_state.get("oi_cat_seen_ids", set())
            outfits, total_unique = _suggest_with_accessory_variety(
                adapter, occasion=occ_query, n=6, seed=current_seed, exclude_ids=seen_cat_ids, return_total=True
            )
            # Track seen outfit combinations across refresh clicks
            for _, pieces in outfits:
                seen_cat_ids.add(frozenset(str(p.get("id") or p.get("path") or id(p)) for p in pieces))
            if len(seen_cat_ids) > 120:
                seen_cat_ids = set()
            st.session_state["oi_cat_seen_ids"] = seen_cat_ids

        if not outfits:
            st.warning(
                f"⚠️ No compatible outfits found for **{g_title}** in **{selected_occ}**. "
                f"Not enough compatible products exist for this combination."
            )
            return

        # Count items in filtered pool
        pool_size = len(adapter.df)
        st.markdown(
            f"<div style='font-family:Cinzel,serif;font-size:13px;letter-spacing:0.12em;"
            f"text-transform:uppercase;color:#8C827A;margin-bottom:16px;'>"
            f"Showing {len(outfits)} {g_title} · {pool_size} eligible products from 746 HD catalog (Generation #{current_seed + 1})</div>",
            unsafe_allow_html=True,
        )

        if total_unique < 6:
            st.markdown(
                f"""
<div style="background:#FFFBF0;border:1px solid #F5D87A;border-radius:8px;padding:12px 18px;margin-bottom:20px;display:flex;align-items:center;gap:10px;">
  <span style="font-size:18px;">💡</span>
  <span style="font-size:13px;color:#7A5510;">
    <strong>Catalog Variety Notice:</strong> {total_unique} distinct harmonious combination{'s' if total_unique > 1 else ''} could be formed for this criteria.
  </span>
</div>
                """,
                unsafe_allow_html=True,
            )

        for idx, (score, pieces) in enumerate(outfits):
            _render_outfit_card(score, pieces, occ_query, idx, source_type="catalog")
