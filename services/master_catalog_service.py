"""
Master Catalog Service
======================
Unified product catalog backend supporting:
- Full browsing & filtering of 746+ master products (720 original + 26 curated + custom admin products).
- Dynamic category & subcategory taxonomy.
- Permanent Product Upload and Management System (single & bulk upload, edit, delete, CSV import).
- Image format & size validations.
- Real-time disk persistence to catalog/master_products.json.
- Full isolation from personal user wardrobe.
"""

import json
import uuid
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MASTER_JSON = ROOT / "catalog" / "master_products.json"
CUSTOM_IMG_DIR = ROOT / "catalog" / "images_custom"
CUSTOM_IMG_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# CATEGORY & SUBCATEGORY TAXONOMY
# ---------------------------------------------------------------------------
TAXONOMY = {
    "Tops": ["Shirts", "T-shirts", "Tops", "Blouses", "Kurtas", "Sweatshirts", "Sweaters", "Hoodies"],
    "Bottoms": ["Trousers", "Jeans", "Shorts", "Track Pants", "Skirts"],
    "Dresses": ["Dresses", "Gowns", "Jumpsuits"],
    "Outerwear": ["Jackets", "Coats", "Blazers", "Cardigans"],
    "Shoes": ["Casual Shoes", "Sports Shoes", "Formal Shoes", "Heels", "Flats", "Sneakers", "Sandals", "Boots"],
    "Bags": ["Handbags", "Backpacks", "Tote Bags", "Clutches"],
    "Accessories": ["Watches", "Belts", "Sunglasses", "Jewellery", "Scarves", "Hats"]
}

CATEGORY_TO_SLOT = {
    "Tops": "top",
    "Bottoms": "bottom",
    "Dresses": "dress",
    "Outerwear": "outer",
    "Shoes": "shoes",
    "Bags": "bag",
    "Accessories": "accessory"
}

AI_SUPPORTED_CLASSES = {
    "Tshirts", "Shirts", "Tops", "Sweatshirts", "Sweaters", "Jackets",
    "Kurtas", "Jeans", "Trousers", "Track Pants", "Shorts", "Dresses",
    "Casual Shoes", "Sports Shoes", "Formal Shoes", "Heels", "Flats", "Handbags"
}

_CACHE: Optional[List[Dict[str, Any]]] = None

def _load_data() -> List[Dict[str, Any]]:
    global _CACHE
    if _CACHE is None:
        if MASTER_JSON.exists():
            try:
                _CACHE = json.loads(MASTER_JSON.read_text(encoding="utf-8"))
            except Exception:
                _CACHE = []
        else:
            _CACHE = []
    return _CACHE

def _save_data():
    global _CACHE
    if _CACHE is not None:
        MASTER_JSON.write_text(json.dumps(_CACHE, indent=2, ensure_ascii=False), encoding="utf-8")

def reload_catalog():
    global _CACHE
    _CACHE = None
    return _load_data()

# ---------------------------------------------------------------------------
# PUBLIC QUERY APIS
# ---------------------------------------------------------------------------
def list_products(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    gender: Optional[str] = None,
    occasion: Optional[str] = None,
    source: Optional[str] = None,
    search: Optional[str] = None,
    hd_only: bool = False
) -> List[Dict[str, Any]]:
    """List products with optional multi-attribute filtering."""
    items = _load_data()
    filtered = []
    
    q = search.lower().strip() if search else None

    for it in items:
        if hd_only and not it.get("is_hd"):
            continue
        if category and category != "All" and it.get("category", "").lower() != category.lower():
            continue
        if subcategory and subcategory != "All" and it.get("subcategory", "").lower() != subcategory.lower():
            continue
        if brand and brand != "All" and it.get("brand", "").lower() != brand.lower():
            continue
        if gender and gender != "All":
            it_gender = it.get("gender", "").lower()
            if it_gender != "unisex" and it_gender != gender.lower():
                continue
        if occasion and occasion != "All" and it.get("occasion", "").lower() != occasion.lower():
            continue
        if source and source != "All" and it.get("source", "").lower() != source.lower():
            continue
        if q:
            searchable = " ".join([
                str(it.get("id", "")),
                it.get("name", ""),
                it.get("brand", ""),
                it.get("category", ""),
                it.get("subcategory", ""),
                it.get("color", ""),
                it.get("occasion", "")
            ]).lower()
            if q not in searchable:
                continue
        filtered.append(it)
    return filtered

def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve single product by ID."""
    for it in _load_data():
        if str(it.get("id")) == str(product_id):
            return it
    return None

def get_absolute_image_path(item: Dict[str, Any]) -> Optional[Path]:
    """Resolve relative image path to absolute filesystem path."""
    rel = item.get("image_path", "")
    if not rel:
        return None
    p = ROOT / rel
    return p if p.exists() else None

def get_categories() -> List[str]:
    return list(TAXONOMY.keys())

def get_subcategories(category: Optional[str] = None) -> List[str]:
    if category and category in TAXONOMY:
        return TAXONOMY[category]
    all_subs = set()
    for subs in TAXONOMY.values():
        all_subs.update(subs)
    return sorted(list(all_subs))

def get_brands() -> List[str]:
    items = _load_data()
    brands = sorted({it.get("brand", "") for it in items if it.get("brand")})
    return brands

def get_genders() -> List[str]:
    return ["Men", "Women", "Unisex", "Boys", "Girls"]

def get_occasions() -> List[str]:
    items = _load_data()
    occasions = sorted({it.get("occasion", "") for it in items if it.get("occasion")})
    return occasions if occasions else ["Casual", "Formal", "Sports", "Ethnic", "Party", "Smart Casual"]

def get_stats() -> Dict[str, Any]:
    items = _load_data()
    total = len(items)
    hd_count = sum(1 for it in items if it.get("is_hd"))
    admin_count = sum(1 for it in items if it.get("source") == "admin_uploaded")
    curated_count = sum(1 for it in items if it.get("source") == "curated_brands")
    orig_count = sum(1 for it in items if it.get("source") == "original_catalog")
    return {
        "total": total,
        "hd_count": hd_count,
        "hd_percentage": (hd_count / total * 100) if total > 0 else 0,
        "admin_count": admin_count,
        "curated_count": curated_count,
        "orig_count": orig_count
    }

# ---------------------------------------------------------------------------
# PRODUCT MANAGEMENT (ADMIN CRUD)
# ---------------------------------------------------------------------------
def add_product(
    name: str,
    brand: str,
    category: str,
    subcategory: str,
    gender: str,
    price: str,
    currency: str = "USD",
    description: str = "",
    url: str = "",
    color: str = "Black",
    occasion: str = "Casual",
    image_bytes: Optional[bytes] = None,
    image_filename: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new product with full validation. Saves image to catalog/images_custom/.
    Immediately persists to master_products.json.
    """
    # Validations
    if not name or not name.strip():
        return {"success": False, "error": "Product name is required."}
    if not category or category not in TAXONOMY:
        return {"success": False, "error": f"Invalid category: {category}"}
    # Generate unique ID
    pid = f"PROD-{uuid.uuid4().hex[:8].upper()}"
    
    if image_bytes:
        if len(image_bytes) > 15 * 1024 * 1024:
            return {"success": False, "error": "Image file exceeds 15MB limit."}

        # Verify image integrity
        try:
            import io
            im = Image.open(io.BytesIO(image_bytes))
            w, h = im.size
            ext = im.format.lower() if im.format else "jpg"
            if ext == "jpeg": ext = "jpg"
        except Exception as e:
            return {"success": False, "error": f"Invalid image file: {e}"}

        filename = f"{pid}.{ext}"
        dest_path = CUSTOM_IMG_DIR / filename
        
        # Save image
        im.convert("RGB").save(dest_path, "JPEG", quality=95)
        rel_path = f"catalog/images_custom/{filename}"
        is_hd = bool(w >= 400 and h >= 400)
    else:
        rel_path = ""
        w, h = 0, 0
        is_hd = False

    # Determine slot and AI support
    slot = CATEGORY_TO_SLOT.get(category, "accessory")
    is_ai_supported = subcategory in AI_SUPPORTED_CLASSES
    ai_class = subcategory if is_ai_supported else None

    # Format price
    clean_price = price.strip() if price else "Price unavailable"
    if clean_price and not clean_price.startswith("$") and clean_price != "Price unavailable":
        try:
            val = float(clean_price.replace(",", ""))
            clean_price = f"${val:.2f}"
        except ValueError:
            pass

    new_item = {
        "id": pid,
        "name": name.strip(),
        "brand": brand.strip() if brand else "Editorial Collection",
        "category": category,
        "subcategory": subcategory,
        "slot": slot,
        "gender": gender,
        "occasion": occasion,
        "color": color,
        "price": clean_price,
        "currency": currency,
        "description": description.strip() if description else f"{brand} {name} for {gender.lower()}.",
        "url": url.strip() if url else "",
        "image_path": rel_path,
        "is_hd": (w >= 400 and h >= 400),
        "width": w,
        "height": h,
        "source": "admin_uploaded",
        "is_ai_supported": is_ai_supported,
        "ai_class": ai_class
    }

    items = _load_data()
    items.insert(0, new_item) # Insert at top
    _save_data()
    return {"success": True, "product": new_item}

def update_product(product_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update fields of an existing product."""
    items = _load_data()
    for it in items:
        if str(it.get("id")) == str(product_id):
            for k, v in updates.items():
                if k not in ["id", "image_path", "source"]:
                    it[k] = v
            # Update slot if category changed
            if "category" in updates:
                it["slot"] = CATEGORY_TO_SLOT.get(it["category"], "accessory")
            if "subcategory" in updates:
                it["is_ai_supported"] = it["subcategory"] in AI_SUPPORTED_CLASSES
                it["ai_class"] = it["subcategory"] if it["is_ai_supported"] else None
            _save_data()
            return {"success": True, "product": it}
    return {"success": False, "error": f"Product {product_id} not found."}

def delete_product(product_id: str) -> Dict[str, Any]:
    """Delete a product from the master catalog and optionally remove custom image."""
    items = _load_data()
    found = None
    for idx, it in enumerate(items):
        if str(it.get("id")) == str(product_id):
            found = items.pop(idx)
            break
            
    if found:
        # Delete image if custom upload
        if found.get("source") == "admin_uploaded":
            img_p = ROOT / found.get("image_path", "")
            if img_p.exists() and "images_custom" in str(img_p):
                try: img_p.unlink()
                except Exception: pass
        _save_data()
        return {"success": True, "deleted_id": product_id}
    return {"success": False, "error": f"Product {product_id} not found."}

def import_csv(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Bulk import products from DataFrame or CSV.
    Expected columns: name, brand, category, subcategory, gender, price
    Optional: occasion, color, description, url, image_path
    """
    required = ["name", "category"]
    missing = [col for col in required if col not in df.columns]
    if missing:
        return {"success": False, "error": f"Missing required columns in CSV: {missing}"}

    success_count = 0
    errors = []
    items = _load_data()

    for idx, row in df.iterrows():
        name = str(row.get("name", "")).strip()
        if not name:
            errors.append(f"Row {idx+1}: missing name")
            continue
        cat = str(row.get("category", "Tops")).strip()
        subcat = str(row.get("subcategory", name)).strip()
        brand = str(row.get("brand", "Editorial Collection")).strip()
        gender = str(row.get("gender", "Unisex")).strip()
        price = str(row.get("price", "Price unavailable")).strip()
        occ = str(row.get("occasion", "Casual")).strip()
        color = str(row.get("color", "Other")).strip()
        desc = str(row.get("description", "")).strip()
        url = str(row.get("url", "")).strip()
        
        # Determine slot
        slot = CATEGORY_TO_SLOT.get(cat, "top")
        is_ai_supported = subcat in AI_SUPPORTED_CLASSES
        ai_class = subcat if is_ai_supported else None
        
        pid = f"PROD-{uuid.uuid4().hex[:8].upper()}"

        new_item = {
            "id": pid,
            "name": name,
            "brand": brand,
            "category": cat,
            "subcategory": subcat,
            "slot": slot,
            "gender": gender,
            "occasion": occ,
            "color": color,
            "price": price,
            "currency": "USD",
            "description": desc if desc else f"{brand} {name}.",
            "url": url,
            "image_path": "catalog/images/15259.jpg", # placeholder until image uploaded
            "is_hd": False,
            "width": 60,
            "height": 80,
            "source": "admin_uploaded",
            "is_ai_supported": is_ai_supported,
            "ai_class": ai_class
        }
        items.insert(0, new_item)
        success_count += 1

    if success_count > 0:
        _save_data()
    return {"success": True, "imported": success_count, "errors": errors}
