"""
Curated Brands & HD Catalog Service
====================================
Handles loading and filtering of the 26-item genuine HD product catalog.
Completely independent from the AI training dataset (catalog/catalog_index.csv).
"""

import json
import pathlib
from typing import Optional

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
_CATALOG_JSON = _PROJECT_ROOT / "curated_catalog" / "curated_products.json"


# ---------------------------------------------------------------------------
# Internal loader (cached in module-level variable for session performance)
# ---------------------------------------------------------------------------
_cache: Optional[list] = None


def _load() -> list:
    global _cache
    if _cache is None:
        if not _CATALOG_JSON.exists():
            _cache = []
        else:
            _cache = json.loads(_CATALOG_JSON.read_text(encoding="utf-8"))
    return _cache


def reload():
    """Force a fresh reload from disk (call after writes)."""
    global _cache
    _cache = None
    return _load()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def list_curated_products(
    brand: Optional[str] = None,
    category: Optional[str] = None,
    gender: Optional[str] = None,
    occasion: Optional[str] = None,
    search: Optional[str] = None,
) -> list[dict]:
    """
    Return curated HD products, optionally filtered.
    All arguments are case-insensitive substring / exact matches.
    """
    items = _load()
    results = []
    for item in items:
        if brand and brand != "All" and item.get("brand", "").lower() != brand.lower():
            continue
        if category and category != "All" and item.get("category", "").lower() != category.lower():
            continue
        if gender and gender != "All":
            item_gender = item.get("gender", "").lower()
            # "unisex" matches any gender filter
            if item_gender != "unisex" and item_gender != gender.lower():
                continue
        if occasion and occasion != "All" and item.get("occasion", "").lower() != occasion.lower():
            continue
        if search:
            q = search.lower()
            searchable = " ".join([
                item.get("brand", ""),
                item.get("name", ""),
                item.get("category", ""),
                item.get("color", ""),
            ]).lower()
            if q not in searchable:
                continue
        results.append(item)
    return results


def get_product_by_id(product_id: str) -> Optional[dict]:
    """Return a single product dict by its HD-xxx id, or None."""
    for item in _load():
        if item.get("id") == product_id:
            return item
    return None


def get_brands() -> list[str]:
    """Return sorted unique brand names."""
    brands = sorted({item.get("brand", "") for item in _load() if item.get("brand")})
    return brands


def get_categories() -> list[str]:
    """Return sorted unique category names."""
    cats = sorted({item.get("category", "") for item in _load() if item.get("category")})
    return cats


def get_genders() -> list[str]:
    return ["Men", "Women", "Unisex"]


def get_occasions() -> list[str]:
    occ = sorted({item.get("occasion", "") for item in _load() if item.get("occasion")})
    return occ


def get_absolute_image_path(item: dict) -> Optional[pathlib.Path]:
    """
    Resolve the image_path field (relative to project root) to an absolute path.
    Returns None if the file doesn't exist.
    """
    rel = item.get("image_path", "")
    if not rel:
        return None
    abs_path = _PROJECT_ROOT / rel
    return abs_path if abs_path.exists() else None


def get_total_count() -> int:
    return len(_load())
