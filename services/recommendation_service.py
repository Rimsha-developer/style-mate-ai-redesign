"""
Recommendation Service
======================
Bridges AI garment classification results with the master HD product catalog.

When the AI classifies an uploaded garment (e.g., "Jeans", "Casual Shoes"),
this service queries the master catalog for matching products to surface
genuine HD product recommendations alongside the classification result.

Design rules:
- Never show unrelated products.
- Provide clear fallback messaging when no exact match exists.
- Use subcategory → category → occasion cascade for matching.
- Always expose a confidence label so the UI can distinguish exact vs. partial matches.
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
from services import master_catalog_service as mcs

# ---------------------------------------------------------------------------
# AI CLASS → CATALOG MAPPING
# Maps the 18 AI-supported class names to (category, subcategory) tuples
# as stored in master_products.json
# ---------------------------------------------------------------------------
AI_CLASS_TO_CATALOG: Dict[str, Dict[str, str]] = {
    # Topwear
    "Tshirts":     {"category": "Tops",     "subcategory": "T-shirts"},
    "Shirts":      {"category": "Tops",     "subcategory": "Shirts"},
    "Tops":        {"category": "Tops",     "subcategory": "Tops"},
    "Sweatshirts": {"category": "Tops",     "subcategory": "Sweatshirts"},
    "Sweaters":    {"category": "Tops",     "subcategory": "Sweaters"},
    "Kurtas":      {"category": "Tops",     "subcategory": "Kurtas"},
    # Outerwear
    "Jackets":     {"category": "Outerwear", "subcategory": "Jackets"},
    # Bottomwear
    "Jeans":       {"category": "Bottoms",  "subcategory": "Jeans"},
    "Trousers":    {"category": "Bottoms",  "subcategory": "Trousers"},
    "Track Pants": {"category": "Bottoms",  "subcategory": "Track Pants"},
    "Shorts":      {"category": "Bottoms",  "subcategory": "Shorts"},
    # Dresses
    "Dresses":     {"category": "Dresses",  "subcategory": "Dresses"},
    # Shoes
    "Casual Shoes":  {"category": "Shoes",  "subcategory": "Casual Shoes"},
    "Sports Shoes":  {"category": "Shoes",  "subcategory": "Sports Shoes"},
    "Formal Shoes":  {"category": "Shoes",  "subcategory": "Formal Shoes"},
    "Heels":         {"category": "Shoes",  "subcategory": "Heels"},
    "Flats":         {"category": "Shoes",  "subcategory": "Flats"},
    # Bags
    "Handbags":    {"category": "Bags",     "subcategory": "Handbags"},
}

# Fuzzy subcategory aliases so catalog entries with slightly different naming still match
_SUBCAT_ALIASES: Dict[str, List[str]] = {
    "T-shirts": ["Tshirts", "T Shirts", "T-Shirts"],
    "Shirts":   ["Shirts"],
    "Tops":     ["Tops"],
    "Sweatshirts": ["Sweatshirts"],
    "Sweaters": ["Sweaters"],
    "Kurtas":   ["Kurtas"],
    "Jackets":  ["Jackets"],
    "Jeans":    ["Jeans"],
    "Trousers": ["Trousers", "Pants"],
    "Track Pants": ["Track Pants", "Track Pant"],
    "Shorts":   ["Shorts"],
    "Dresses":  ["Dresses", "Dress"],
    "Casual Shoes": ["Casual Shoes"],
    "Sports Shoes": ["Sports Shoes", "Sport Shoes"],
    "Formal Shoes": ["Formal Shoes"],
    "Heels":    ["Heels"],
    "Flats":    ["Flats"],
    "Handbags": ["Handbags", "Handbag"],
}


def _build_alias_set(subcategory: str) -> set:
    """Return all case-insensitive aliases for a subcategory."""
    canon = subcategory.strip()
    aliases = {canon.lower()}
    for key, vals in _SUBCAT_ALIASES.items():
        all_names = [key] + vals
        if canon.lower() in [v.lower() for v in all_names]:
            aliases.update(v.lower() for v in all_names)
    return aliases


def get_recommendations(
    ai_class: str,
    gender: Optional[str] = None,
    occasion: Optional[str] = None,
    max_results: int = 8,
    hd_only: bool = False,
) -> Dict[str, Any]:
    """
    Return product recommendations for a detected AI garment class.

    Returns a dict:
    {
        "match_level": "exact" | "category" | "none",
        "match_label": str,          # human-readable explanation
        "products": List[Dict],       # up to max_results products
        "ai_class": str,
        "catalog_mapping": dict | None
    }
    """
    mapping = AI_CLASS_TO_CATALOG.get(ai_class)

    # --- Exact subcategory match ---
    if mapping:
        aliases = _build_alias_set(mapping["subcategory"])
        all_products = mcs._load_data()
        exact = [
            p for p in all_products
            if p.get("subcategory", "").lower() in aliases
        ]

        # Apply gender filter if provided (also keep Unisex)
        if gender and gender.lower() not in ("", "unisex"):
            exact = [
                p for p in exact
                if p.get("gender", "").lower() in (gender.lower(), "unisex", "")
            ]

        # Apply occasion filter if provided
        if occasion and occasion.lower() not in ("", "all"):
            exact_occ = [
                p for p in exact
                if p.get("occasion", "").lower() == occasion.lower()
            ]
            exact = exact_occ if exact_occ else exact  # fall back to no occasion filter

        # HD preferred first
        if hd_only:
            exact = [p for p in exact if p.get("is_hd")]
        else:
            exact = sorted(exact, key=lambda p: (not p.get("is_hd"), p.get("id", 0)))

        if exact:
            return {
                "match_level": "exact",
                "match_label": f"Exact match — showing {mapping['subcategory']} from the catalog",
                "products": exact[:max_results],
                "ai_class": ai_class,
                "catalog_mapping": mapping,
            }

        # Exact subcategory not found — try category-level
        category_products = mcs.list_products(
            category=mapping["category"],
            gender=gender,
            occasion=occasion,
            hd_only=hd_only,
        )
        if category_products:
            return {
                "match_level": "category",
                "match_label": f"No exact {mapping['subcategory']} match — showing similar {mapping['category']} styles",
                "products": category_products[:max_results],
                "ai_class": ai_class,
                "catalog_mapping": mapping,
            }

    # --- No mapping or no products found ---
    return {
        "match_level": "none",
        "match_label": (
            f"'{ai_class}' is not in the current catalog. No recommendations available."
            if mapping is None
            else f"No products found in the catalog for '{ai_class}'."
        ),
        "products": [],
        "ai_class": ai_class,
        "catalog_mapping": mapping,
    }


def get_similar_to_product(
    product: Dict[str, Any],
    max_results: int = 6,
) -> List[Dict[str, Any]]:
    """
    Return catalog products similar to a given product dict
    (same subcategory, same gender, different id).
    """
    pid = str(product.get("id", ""))
    subcat = product.get("subcategory", "")
    gender = product.get("gender", "")

    if not subcat:
        return []

    aliases = _build_alias_set(subcat)
    all_products = mcs._load_data()
    similar = [
        p for p in all_products
        if str(p.get("id")) != pid
        and p.get("subcategory", "").lower() in aliases
    ]

    if gender and gender.lower() not in ("unisex", ""):
        gender_filtered = [
            p for p in similar
            if p.get("gender", "").lower() in (gender.lower(), "unisex", "")
        ]
        similar = gender_filtered if gender_filtered else similar

    # HD first
    similar = sorted(similar, key=lambda p: (not p.get("is_hd"), p.get("id", 0)))
    return similar[:max_results]


def get_supported_classes() -> List[str]:
    """Return list of AI class names that have catalog mappings."""
    return list(AI_CLASS_TO_CATALOG.keys())
