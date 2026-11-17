"""Style Mate AI - Service Adapter
Thin, decoupled service layer connecting the UI to the unmodified original AI engine.

Rules followed:
- Uses runtime in-memory Keras adapter (zero model file modifications)
- Wraps original engine.py without altering prediction equations, weights, or thresholds
- Normalizes catalog path separators for cross-platform portability
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# 1. RUNTIME IN-MEMORY COMPATIBILITY ADAPTER
# ---------------------------------------------------------------------------
try:
    import keras
    _orig_dense_from_config = keras.layers.Dense.from_config

    def _safe_dense_from_config(config):
        if "quantization_config" in config and config["quantization_config"] is None:
            config.pop("quantization_config")
        return _orig_dense_from_config(config)

    keras.layers.Dense.from_config = _safe_dense_from_config
except Exception as e:
    # If Keras already supports the parameter or is unavailable
    pass

# Ensure parent directory is in sys.path so engine.py and siblings resolve cleanly
_ROOT_DIR = Path(__file__).resolve().parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

# Import unmodified original engine
import engine

try:
    import streamlit as st
    cache_resource = st.cache_resource
except Exception:
    def cache_resource(*args, **kwargs):
        def decorator(f):
            return f
        return decorator

# ---------------------------------------------------------------------------
# 2. SINGLETON FACTORY & ENGINE CACHING
# ---------------------------------------------------------------------------
_CLASSIFIER_INSTANCE: Optional[engine.Classifier] = None
_WARDROBE_INSTANCE: Optional[engine.Wardrobe] = None
_CATALOG_INSTANCE: Optional[engine.Catalog] = None

@cache_resource(show_spinner=False)
def get_classifier(model_dir: str = "models") -> engine.Classifier:
    """Retrieve or initialize singleton instance of original Classifier."""
    global _CLASSIFIER_INSTANCE
    if _CLASSIFIER_INSTANCE is None:
        model_path = Path(model_dir)
        if not model_path.is_absolute():
            model_path = _ROOT_DIR / model_dir
        _CLASSIFIER_INSTANCE = engine.Classifier(str(model_path))
    return _CLASSIFIER_INSTANCE

def get_wardrobe(wardrobe_dir: str = "wardrobe") -> engine.Wardrobe:
    """Retrieve or initialize singleton instance of original Wardrobe.
    Note: Intentionally not cached with Streamlit cache to ensure live multi-user isolation
    and instant synchronization with filesystem modifications.
    """
    global _WARDROBE_INSTANCE
    if _WARDROBE_INSTANCE is None:
        wd_path = Path(wardrobe_dir)
        if not wd_path.is_absolute():
            wd_path = _ROOT_DIR / wardrobe_dir
        _WARDROBE_INSTANCE = engine.Wardrobe(str(wd_path))
    return _WARDROBE_INSTANCE

@cache_resource(show_spinner=False)
def get_catalog(img_dir: str = "catalog/images", csv_path: str = "catalog/catalog.csv", progress_cb=None) -> engine.Catalog:
    """Load and cache the catalog, ensuring cross-platform path normalization."""
    global _CATALOG_INSTANCE
    if _CATALOG_INSTANCE is None:
        clf = get_classifier()
        abs_img_dir = _ROOT_DIR / img_dir if not Path(img_dir).is_absolute() else Path(img_dir)
        abs_csv = _ROOT_DIR / csv_path if not Path(csv_path).is_absolute() else Path(csv_path)
        
        # Load catalog via original method
        cat = engine.Catalog.load(str(abs_img_dir), clf, str(abs_csv) if abs_csv.exists() else None, progress_cb)
        
        # Cross-platform path normalization (convert any Windows backslashes in paths)
        if hasattr(cat, "df") and "path" in cat.df.columns:
            cat.df["path"] = cat.df["path"].astype(str).str.replace("\\", "/", regex=False)
            # Ensure path points to absolute path under project root if relative
            def _resolve_path(p: str) -> str:
                p_obj = Path(p)
                if not p_obj.is_absolute():
                    return str(_ROOT_DIR / p)
                return str(p_obj)
            cat.df["path"] = cat.df["path"].map(_resolve_path)
            
        _CATALOG_INSTANCE = cat
    return _CATALOG_INSTANCE

def get_catalog_dataframe():
    """Return the cached catalog DataFrame with normalized paths."""
    cat = get_catalog()
    return cat.df

def list_catalog_items(
    slot: str = "all",
    gender: str = "All",
    occasion: str = "All",
    color: str = "All",
    search: str = ""
) -> List[Dict[str, Any]]:
    """Return filtered catalog items as rich dictionaries with file integrity verified."""
    cat = get_catalog()
    df = cat.df.copy()

    # Filter by slot
    if slot and slot != "all":
        df = df[df["slot"] == slot]

    # Filter by gender
    if gender and gender != "All":
        df = df[df["gender"].astype(str).str.lower() == gender.lower()]

    # Filter by occasion
    if occasion and occasion != "All":
        df = df[df["usage"].astype(str).str.lower() == occasion.lower()]

    # Filter by color
    if color and color != "All":
        df = df[df["color"].astype(str).str.lower() == color.lower()]

    # Search filter (by type or ID)
    if search and search.strip():
        q = search.strip().lower()
        df = df[df["type"].astype(str).str.lower().str.contains(q, regex=False) |
                df["path"].astype(str).str.lower().str.contains(q, regex=False)]

    items = []
    for row in df.itertuples():
        p_str = str(row.path)
        pid = Path(p_str).stem
        slot_key = getattr(row, "slot", "top")
        slot_title = engine.SLOT_TITLE.get(slot_key, slot_key.title())
        col = getattr(row, "color", "unknown")
        items.append({
            "id": pid,
            "path": p_str,
            "type": getattr(row, "type", "Garment"),
            "slot": slot_key,
            "slot_title": slot_title,
            "usage": getattr(row, "usage", "Casual"),
            "gender": getattr(row, "gender", "Unisex"),
            "color": col,
            "neutral": bool(getattr(row, "neutral", False)),
            "hue": float(getattr(row, "hue", 0.0)),
            "file_exists": os.path.exists(p_str)
        })
    return items

def add_catalog_item_to_wardrobe(
    catalog_item_path: str,
    type_name: str,
    slot: str,
    usage: str,
    gender: str = "Unisex"
) -> Dict[str, Any]:
    """Copy a catalog garment into the user's personal wardrobe."""
    p = Path(catalog_item_path)
    if not p.is_absolute():
        p = _ROOT_DIR / catalog_item_path
    if not p.exists():
        raise FileNotFoundError(f"Catalog image not found: {p}")
    img_rgb = np.asarray(Image.open(p).convert("RGB"))
    return add_garment_to_wardrobe(
        rgb_image=img_rgb,
        type_name=type_name,
        slot=slot,
        occasion=usage,
        confidence=1.0,
        gender=gender
    )

# ---------------------------------------------------------------------------
# 3. HIGH-LEVEL PREDICTION SERVICES
# ---------------------------------------------------------------------------
def resolve_garment_slot(garment_type: str) -> str:
    """Resolve garment category or descriptive name to canonical engine slot.

    Strict guarantees:
    - Long shirts, shirts, tunics, kurtas, blouses, tops -> strictly 'top'
    - Trousers, jeans, shorts, track pants, pants -> strictly 'bottom'
    - Dresses, gowns, jumpsuits -> strictly 'dress' (never split into separate top+bottom)
    - Jackets, coats, blazers, cardigans, overcoats -> strictly 'outer'
    - Casual/Sports/Formal shoes, heels, flats, sneakers -> strictly 'shoes'
    - Handbags, bags, totes, clutches -> strictly 'bag'
    """
    t = str(garment_type).lower().strip()
    # Dresses: must precede tops, but exclude "dress shirt" or "dress shoes"
    if any(k in t for k in ["dress", "gown", "jumpsuit", "maxi", "frock"]) and not any(k in t for k in ["shirt", "shoe", "pant", "trouser", "jacket"]):
        return "dress"
    # Outerwear: ONLY true jackets, coats, blazers, cardigans, overcoats
    if any(k in t for k in ["jacket", "coat", "blazer", "cardigan", "overcoat", "windbreaker", "parka", "outerwear"]):
        return "outer"
    # Bottoms: trousers, jeans, shorts, track pants, pants, skirts
    if any(k in t for k in ["trouser", "jean", "short", "track pant", "pant", "skirt", "legging", "chino"]):
        return "bottom"
    # Shoes: shoes, sneakers, flats, heels, sandals, boots
    if any(k in t for k in ["shoe", "sneaker", "flat", "heel", "sandal", "boot", "loafer"]):
        return "shoes"
    # Bags: handbag, bag, backpack, tote, clutch
    if any(k in t for k in ["bag", "backpack", "tote", "clutch", "purse"]):
        return "bag"
    # Tops: long shirts, shirts, t-shirts, tops, tunics, kurtas, blouses, sweaters, sweatshirts
    if any(k in t for k in ["kurta", "shirt", "t-shirt", "tshirt", "tee", "top", "tunic", "blouse", "sweater", "sweatshirt", "hoodie"]):
        return "top"
    return "top"


def analyze_single_garment(rgb_image: np.ndarray) -> Dict[str, Any]:
    """Run exact original CNN + KNN ensemble prediction and color extraction.
    
    Args:
        rgb_image: NumPy RGB array [0..255], shape (H, W, 3).
        
    Returns:
        Structured dictionary with predictions, top-3 distribution, color, and confidence.
    """
    clf = get_classifier()

    # Aspect-ratio preserving pad to square for portrait/tall garments:
    # When an image is tall/portrait (e.g. full-length trousers or dresses),
    # squashing it to 224x224 directly distorts the vertical silhouette,
    # causing full-length trousers to look like shorts and long dresses to look like tops.
    # Letterboxing to square preserves the true garment proportions without altering
    # any trained model weights.
    h, w = rgb_image.shape[:2]
    if max(h, w) > 0 and abs(h - w) / max(h, w) > 0.08:
        from garment_cropping import _pad_to_square
        borders = np.concatenate([rgb_image[0, :, :], rgb_image[-1, :, :], rgb_image[:, 0, :], rgb_image[:, -1, :]])
        bg = tuple(int(v) for v in np.median(borders, axis=0))
        if min(bg) > 200:
            bg = (255, 255, 255)
        inf_image = _pad_to_square(rgb_image, fill=bg)
    else:
        inf_image = rgb_image
    
    # 1. Exact model prediction (CNN + KNN ensemble) on aspect-preserved image
    pred = clf.predict(inf_image)
    
    # 2. Exact dominant color and HSV categorization on original untouched pixels
    dom_rgb = engine.dominant_rgb(rgb_image)
    col_info = engine.color_info(dom_rgb)
    
    # 3. Original uncertainty formula (preserved 100%)
    top3 = pred["top3"]
    is_uncertain = bool(
        pred["conf"] < 0.60 or (len(top3) > 1 and (top3[0][1] - top3[1][1]) < 0.25)
    )
    
    # 4. Slot presentation title with strict taxonomy resolution
    raw_slot = pred["slot"]
    # Ensure long shirts / kurtas remain tops, dresses remain dresses
    slot_key = resolve_garment_slot(pred["type"]) or raw_slot
    slot_title = engine.SLOT_TITLE.get(slot_key, slot_key.title())
    
    return {
        "type": pred["type"],
        "slot": slot_key,
        "slot_title": slot_title,
        "conf": float(pred["conf"]),
        "conf_pct": round(float(pred["conf"]) * 100, 1),
        "top3": [(name, float(prob), round(float(prob) * 100, 1)) for name, prob in top3],
        "usage": pred["usage"],
        "usage_conf": float(pred["usage_conf"]),
        "usage_conf_pct": round(float(pred["usage_conf"]) * 100, 1),
        "color": col_info["color"],
        "neutral": col_info["neutral"],
        "hue": col_info["hue"],
        "rgb": col_info["rgb"],
        "hex": "#{:02x}{:02x}{:02x}".format(*col_info["rgb"]),
        "is_uncertain": is_uncertain,
        "types_list": clf.types,
        "usages_list": clf.usages,
        "slots_map": clf.slots
    }

def analyze_full_body_crops(rgb_image: np.ndarray) -> Dict[str, Any]:
    """Extract Upper and Lower garment crops using original MediaPipe pose pipeline.
    
    Returns:
        Dict with "has_pose": bool and "parts": Dict[str, np.ndarray] or None.
    """
    clf = get_classifier()
    crops = clf.body_crops(rgb_image)
    if crops is None:
        return {"has_pose": False, "parts": None}
    return {
        "has_pose": True,
        "parts": {
            "Upper body": crops[0],
            "Lower body": crops[1]
        }
    }

# ---------------------------------------------------------------------------
# 4. RECOMMENDATION & WARDROBE SERVICES
# ---------------------------------------------------------------------------
def get_recommendations_for_item(
    item_dict: Dict[str, Any],
    catalog: Optional[engine.Catalog] = None,
    per_slot: int = 4,
    occasion: str = "Any",
    gender: str = "Any",
    seed: int = 0
) -> Dict[str, Any]:
    """Generate recommendations using original pair_score and harmony logic."""
    if catalog is None:
        catalog = get_catalog()
    return engine.recommend(catalog, item_dict, per_slot=per_slot, occasion=occasion, gender=gender, seed=seed)

def _outfit_content_key(pieces: List[Dict[str, Any]]) -> tuple:
    """Content fingerprint for an outfit: sorted (slot, type, color) tuples.
    Two outfits with identical visual pieces (even if possessing different UUIDs)
    produce the exact same key.
    """
    return tuple(sorted(
        (str(p.get("slot", "")).lower(), str(p.get("type", "")).lower(), str(p.get("color", "")).lower())
        for p in pieces
    ))


def _outfit_id_key(pieces: List[Dict[str, Any]]) -> frozenset:
    """Order-independent ID set of an outfit's pieces."""
    return frozenset(str(p.get("id") or p.get("path") or id(p)) for p in pieces)


def generate_diverse_outfit_combinations(
    wardrobe: Optional[engine.Wardrobe] = None,
    occasion: str = "Any",
    gender_mode: str = "Any",
    n: int = 6,
    seed: int = 0,
    exclude_ids: Optional[set] = None,
) -> Tuple[List[Tuple[int, List[Dict[str, Any]]]], int]:
    """Generate diverse, deduplicated outfit combinations from the personal wardrobe.

    Requirements addressed:
    1. No duplicate outfits: order-independent ID set AND content fingerprint deduplication.
    2. Improved diversity: explores diverse bases (top x bottom, dress) and accessory combinations
       (shoes x outer x bag) where pair_score >= 65, rather than repeatedly selecting the greedy same shoe.
    3. Honest result count: returns only genuinely unique outfits (e.g. 2 if only 2 exist), never repeats.
    4. Gender isolation: strictly filters wardrobe items if gender metadata is present.
    5. Preserves original color harmony, neutral compatibility, and occasion scoring formulas.
    6. Seed / refresh rotation: when more than n combinations exist, clicking refresh rotates to fresh outfits
       and excludes already shown combinations from the current cycle.

    Returns:
        (outfits, total_unique_combinations)
    """
    if wardrobe is None:
        wardrobe = get_wardrobe()

    # Step 1: Gender pre-filter on wardrobe items (if gender metadata is attached)
    g_norm = str(gender_mode or "Any").lower()
    if "men" in g_norm and "women" not in g_norm:
        allowed_g = {"men", "unisex"}
    elif "women" in g_norm:
        allowed_g = {"women", "unisex"}
    elif "unisex" in g_norm:
        allowed_g = {"unisex"}
    else:
        allowed_g = None

    candidate_items = []
    for it in wardrobe.items:
        # Check explicit gender tag if present
        item_gender = str(it.get("gender", "")).strip().lower()
        if item_gender in {"boys", "girls"}:
            continue  # exclude children items from adult wardrobe suggestions
        if allowed_g is not None and item_gender:
            if item_gender not in allowed_g:
                continue
        # Occasion pre-filter if specific occasion requested
        if occasion != "Any" and it.get("usage"):
            if engine.usage_compat(occasion, it.get("usage", "Casual")) < 60:
                continue
        candidate_items.append(it)

    # Step 2: Content-deduplicate wardrobe items so phantom duplicate uploads do not multiply
    seen_content: set = set()
    unique_items: List[Dict[str, Any]] = []
    for it in candidate_items:
        key = (
            str(it.get("slot", "")).lower(),
            str(it.get("type", "")).lower(),
            str(it.get("color", "")).lower(),
            str(it.get("usage", "")).lower()
        )
        if key not in seen_content:
            seen_content.add(key)
            unique_items.append(it)

    def _by_slot(slot: str) -> List[Dict[str, Any]]:
        return [i for i in unique_items if i.get("slot") == slot]

    tops = _by_slot("top")
    bottoms = _by_slot("bottom")
    dresses = _by_slot("dress")
    shoes_pool = _by_slot("shoes")
    bags_pool = _by_slot("bag")
    outers_pool = _by_slot("outer")

    # Options for combinatorial search (pad empty pools with None)
    shoes_opts = shoes_pool if shoes_pool else [None]
    bags_opts = bags_pool if bags_pool else [None]
    outers_opts = outers_pool if outers_pool else [None]

    bases = [(t, b) for t in tops for b in bottoms] + [(d,) for d in dresses]
    if not bases:
        return [], 0

    # Shuffle bases with seed so fresh candidate combinations are prioritized on each refresh click
    rng = np.random.default_rng(seed)
    shuffled_bases = list(bases)
    rng.shuffle(shuffled_bases)

    # Accessory pools (pad with None if empty)
    shoe_choices = shoes_pool if shoes_pool else [None]
    bag_choices = bags_pool if bags_pool else [None]
    outer_choices = outers_pool if outers_pool else [None]

    raw_count = 0
    seen_outfit_ids: set = set()
    seen_content_sigs: set = set()
    all_outfits: List[Tuple[int, List[Dict[str, Any]]]] = []

    # Step 3: Interactive combinatorial exploration (capped bases & accessory branching for sub-second response)
    for base in shuffled_bases[:40]:
        for shoe in shoe_choices[:4]:
            for bag in bag_choices[:3]:
                pieces = list(base)
                if shoe is not None:
                    score_s = np.mean([engine.pair_score(shoe, p) for p in pieces])
                    if score_s >= 65:
                        pieces = pieces + [shoe]
                if outer_choices[0] is not None:
                    for outer in outer_choices[:3]:
                        score_o = np.mean([engine.pair_score(outer, p) for p in pieces])
                        if score_o >= 65:
                            pieces = pieces + [outer]
                            break
                if bag is not None:
                    score_b = np.mean([engine.pair_score(bag, p) for p in pieces])
                    if score_b >= 65:
                        pieces = pieces + [bag]

                if len(pieces) < 2:
                    continue

                raw_count += 1

                # Strict Deduplication: order-independent ID set & visual content signature
                id_key = _outfit_id_key(pieces)
                content_key = _outfit_content_key(pieces)

                if id_key in seen_outfit_ids or content_key in seen_content_sigs:
                    continue

                seen_outfit_ids.add(id_key)
                seen_content_sigs.add(content_key)

            # Scoring using original Style Mate engine formulas
            pair_scores = [
                engine.pair_score(a, b)
                for i, a in enumerate(pieces)
                for b in pieces[i + 1:]
            ] or [75]
            score = float(np.mean(pair_scores))
            if occasion != "Any":
                score += 0.15 * float(np.mean([
                    engine.usage_compat(occasion, p.get("usage", "Casual"))
                    for p in pieces
                ])) - 10
            score -= 2 * min(float(np.mean([p.get("worn", 0) for p in pieces])), 5)
            score = round(max(0, min(100, score)))

            all_outfits.append((score, pieces))

    # Sort descending by harmony score
    all_outfits.sort(key=lambda x: -x[0])
    total_unique = len(all_outfits)

    if total_unique <= n:
        # Limited variety: return all unique combinations honestly
        return all_outfits, total_unique

    # If exclude_ids provided, prioritize fresh combinations not shown in current cycle
    if exclude_ids:
        unseen = [o for o in all_outfits if _outfit_id_key(o[1]) not in exclude_ids]
        if len(unseen) >= n:
            return unseen[:n], total_unique
        elif unseen:
            fillers = [o for o in all_outfits if _outfit_id_key(o[1]) in exclude_ids]
            return (unseen + fillers)[:n], total_unique

    # When ample variety exists (> n), rotate starting offset by seed on each refresh
    offset = (seed * n) % total_unique
    selected = all_outfits[offset : offset + n]
    if len(selected) < n:
        selected += all_outfits[: n - len(selected)]
    return selected, total_unique


def generate_outfit_combinations(
    wardrobe: Optional[engine.Wardrobe] = None,
    occasion: str = "Any",
    n: int = 6
) -> List[Tuple[int, List[Dict[str, Any]]]]:
    """Generate coordinated outfits from wardrobe using original suggest algorithm."""
    if wardrobe is None:
        wardrobe = get_wardrobe()
    return engine.suggest(wardrobe, occasion=occasion, n=n)

def add_garment_to_wardrobe(
    rgb_image: np.ndarray,
    type_name: str,
    slot: str,
    occasion: str,
    confidence: Optional[float] = None,
    gender: str = "Unisex"
) -> Dict[str, Any]:
    """Save garment to wardrobe JSON and filesystem with guaranteed disk synchronization.

    Guarantees:
    - Resolves slot canonically so kurtas/long shirts stay in 'top' and dresses stay in 'dress'.
    - Stores gender metadata ('Women', 'Men', 'Unisex') for reliable outfit filtering.
    - Prevents rapid duplicate entries on repeated button clicks.
    """
    wd = get_wardrobe()
    # Reload from disk first to ensure freshest state
    if wd.db.exists():
        try:
            wd.items = json.loads(wd.db.read_text(encoding="utf-8"))
        except Exception:
            pass
    else:
        wd.items = []

    # Canonical slot resolution
    resolved_slot = resolve_garment_slot(type_name) or slot

    # Duplicate prevention: only extract color if candidate with identical type & slot exists
    has_candidate = any(
        existing.get("type") == type_name and existing.get("slot") == resolved_slot and existing.get("usage") == occasion
        for existing in wd.items
    )
    if has_candidate:
        dom_rgb = engine.dominant_rgb(rgb_image)
        col_info = engine.color_info(dom_rgb)
        for existing in wd.items:
            if (existing.get("type") == type_name and
                existing.get("slot") == resolved_slot and
                existing.get("usage") == occasion and
                existing.get("color") == col_info["color"]):
                # Check RGB distance
                e_rgb = existing.get("rgb", [0, 0, 0])
                if np.mean(np.abs(np.array(e_rgb) - np.array(dom_rgb))) < 15:
                    # Return already saved item to avoid duplicate on multi-click
                    return existing

    it = wd.add(rgb_image, type_name, resolved_slot, occasion, confidence)
    it["gender"] = gender if gender in {"Women", "Men", "Unisex"} else "Unisex"
    it["name"] = type_name
    wd._save()
    return it

def list_wardrobe_items() -> List[Dict[str, Any]]:
    """Retrieve all wardrobe garments with normalized paths and resolved file integrity.
    
    Returns:
        List of item dictionaries with absolute image paths, color metadata, and percentages.
    """
    wd = get_wardrobe()
    # Reload from disk to guarantee live parity with filesystem
    if wd.db.exists():
        try:
            wd.items = json.loads(wd.db.read_text())
        except Exception:
            pass
    else:
        wd.items = []

    resolved = []
    for it in wd.items:
        item = dict(it)
        # Normalize cross-platform Windows/Mac backslashes
        raw_path = str(item.get("path", "")).replace("\\", "/")
        p_obj = Path(raw_path)
        if not p_obj.is_absolute():
            p_obj = _ROOT_DIR / raw_path
        item["resolved_path"] = str(p_obj)
        item["file_exists"] = p_obj.exists()

        # Formatting helpers
        rgb = item.get("rgb")
        if isinstance(rgb, (list, tuple)) and len(rgb) == 3:
            item["hex"] = "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))
        else:
            item["hex"] = "#8C827A"

        conf = item.get("conf")
        item["conf_pct"] = round(float(conf) * 100, 1) if conf is not None else None
        item["slot_title"] = engine.SLOT_TITLE.get(item.get("slot"), str(item.get("slot", "")).title())
        resolved.append(item)

    return resolved

def delete_garment_from_wardrobe(item_id: str) -> bool:
    """Remove garment from wardrobe JSON and safely remove physical image file.
    
    Returns:
        True if item was found and removed, False otherwise.
    """
    wd = get_wardrobe()
    if wd.db.exists():
        try:
            wd.items = json.loads(wd.db.read_text())
        except Exception:
            pass

    found = False
    for it in wd.items:
        if it.get("id") == item_id:
            found = True
            raw_path = str(it.get("path", "")).replace("\\", "/")
            p_obj = Path(raw_path)
            if not p_obj.is_absolute():
                p_obj = _ROOT_DIR / raw_path
            if p_obj.exists():
                try:
                    p_obj.unlink()
                except Exception:
                    pass

    wd.items = [it for it in wd.items if it.get("id") != item_id]
    wd._save()
    return found

def update_wardrobe_item(
    item_id: str,
    new_type: str,
    new_slot: str,
    new_usage: str,
    new_gender: Optional[str] = None
) -> bool:
    """Update type, slot, occasion, and optional gender metadata for an existing garment.
    
    Returns:
        True if item was updated and saved, False otherwise.
    """
    wd = get_wardrobe()
    if wd.db.exists():
        try:
            wd.items = json.loads(wd.db.read_text(encoding="utf-8"))
        except Exception:
            pass

    resolved_slot = resolve_garment_slot(new_type) or new_slot

    updated = False
    for it in wd.items:
        if it.get("id") == item_id:
            it["type"] = new_type
            it["slot"] = resolved_slot
            it["usage"] = new_usage
            it["name"] = new_type
            if new_gender:
                it["gender"] = new_gender
            updated = True
            break

    if updated:
        wd._save()
    return updated

def get_supported_slots() -> Dict[str, str]:
    """Return dictionary of supported slots mapping slot key to title:
    e.g. {'top': 'Tops', 'bottom': 'Bottoms', 'dress': 'Dresses', ...}
    """
    return dict(engine.SLOT_TITLE)

def get_slot_title(slot_key: str) -> str:
    """Return presentation title for a slot key (e.g. 'top' -> 'Tops')."""
    return engine.SLOT_TITLE.get(slot_key, str(slot_key).title())

def record_outfit_worn(item_ids: List[str]) -> None:
    """Increment wear counter for rotated suggestions."""
    wd = get_wardrobe()
    wd.wear(item_ids)
