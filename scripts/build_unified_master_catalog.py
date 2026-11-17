"""
Build the Unified Master Fashion Catalog database.
Merges:
1. All 720 original catalog products with their authentic HD images and metadata.
2. The 26 Curated Brand Collection products.
Generates catalog/master_products.json with comprehensive taxonomy.
"""
import json, re
import pandas as pd
from pathlib import Path
import PIL.Image

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
CAT_CSV = ROOT / "catalog" / "catalog.csv"
IDX_CSV = ROOT / "catalog" / "catalog_index.csv"
LINKS_CSV = ROOT / "catalog" / "hd_links_matched.csv"
CURATED_JSON = ROOT / "curated_catalog" / "curated_products.json"
HD_IMG_DIR = ROOT / "catalog" / "images_hd"
FALLBACK_IMG_DIR = ROOT / "catalog" / "images"
MASTER_JSON = ROOT / "catalog" / "master_products.json"

AI_SUPPORTED_MAP = {
    "Tshirts": ("Tops", "T-shirts", "top"),
    "Shirts": ("Tops", "Shirts", "top"),
    "Tops": ("Tops", "Tops", "top"),
    "Sweatshirts": ("Tops", "Sweatshirts", "top"),
    "Sweaters": ("Tops", "Sweaters", "top"),
    "Kurtas": ("Tops", "Kurtas", "top"),
    "Jeans": ("Bottoms", "Jeans", "bottom"),
    "Trousers": ("Bottoms", "Trousers", "bottom"),
    "Track Pants": ("Bottoms", "Track Pants", "bottom"),
    "Shorts": ("Bottoms", "Shorts", "bottom"),
    "Dresses": ("Dresses", "Dresses", "dress"),
    "Jackets": ("Outerwear", "Jackets", "outer"),
    "Casual Shoes": ("Shoes", "Casual Shoes", "shoes"),
    "Sports Shoes": ("Shoes", "Sports Shoes", "shoes"),
    "Formal Shoes": ("Shoes", "Formal Shoes", "shoes"),
    "Heels": ("Shoes", "Heels", "shoes"),
    "Flats": ("Shoes", "Flats", "shoes"),
    "Handbags": ("Bags", "Handbags", "bag"),
}

KNOWN_BRANDS = [
    "Arrow", "Adidas", "Puma", "Nike", "Reebok", "Levis", "Highlander",
    "Peter England", "John Miller", "Indigo Nation", "Gini and Jony", "Proline",
    "Mark Taylor", "Palm Tree", "Doodle", "Titan", "Fastrack", "Fossil",
    "Elle", "United Colors of Benetton", "Wrangler", "Lee", "Vans", "Converse",
    "Woodland", "Bata", "Catwalk", "Lavie", "Caprese", "Baggit", "Lino Perros",
    "Turtle", "Basics", "Mod acc", "French Connection", "Tommy Hilfiger", "Spykar",
    "Flying Machine", "Mufti", "Scullers", "Louis Philippe", "Van Heusen", "Allen Solly",
    "Raymond", "Park Avenue", "Parx", "ColorPlus", "Blackberrys", "Fabindia", "Biba",
    "W", "Aurelia", "Global Desi", "AND", "Forever 21", "Zara", "Mango", "H&M"
]

def extract_brand_and_name(raw_text: str, default_type: str, default_gender: str):
    if not raw_text or not isinstance(raw_text, str):
        return "Editorial Collection", f"{default_gender} {default_type}"
    clean = raw_text.replace("-", " ").strip()
    
    # Try finding known brand
    matched_brand = None
    for b in sorted(KNOWN_BRANDS, key=len, reverse=True):
        if re.search(r'\b' + re.escape(b) + r'\b', clean, re.IGNORECASE):
            matched_brand = b
            break
            
    if matched_brand:
        return matched_brand, clean
    
    # Otherwise use first 1-2 words as brand if title-case
    words = clean.split()
    if len(words) >= 3 and words[0].isupper():
        return words[0], clean
    return "Editorial Collection", clean

def build():
    print("Building unified master catalog...")
    df_cat = pd.read_csv(CAT_CSV)
    df_idx = pd.read_csv(IDX_CSV)
    df_links = pd.read_csv(LINKS_CSV) if LINKS_CSV.exists() else pd.DataFrame()

    link_lookup = {}
    if not df_links.empty:
        for _, r in df_links.iterrows():
            pid = str(r["id"])
            link = str(r["link"])
            fname = link.split("/")[-1]
            m = re.match(r"^([A-Za-z0-9\-]+)_[a-f0-9]+_images\.jpg", fname)
            raw = m.group(1) if m else None
            link_lookup[pid] = {
                "raw_name": raw,
                "link": link
            }

    master_items = []
    
    # 1. Process all 720 original products
    for idx, row in df_cat.iterrows():
        pid = str(row["id"])
        atype = str(row["articleType"])
        usage = str(row["usage"])
        gender = str(row["gender"])
        
        # Color from index
        color = "Other"
        match_idx = df_idx[df_idx["path"].str.contains(f"/{pid}\\.", na=False)]
        if not match_idx.empty:
            color = match_idx.iloc[0].get("color", "Other")

        cat, subcat, slot = AI_SUPPORTED_MAP.get(atype, ("Accessories", atype, "accessory"))
        
        # Extract brand and name
        raw_text = link_lookup.get(pid, {}).get("raw_name")
        brand, product_name = extract_brand_and_name(raw_text, atype, gender)
        
        # Check image availability
        hd_path = HD_IMG_DIR / f"{pid}.jpg"
        fallback_path = FALLBACK_IMG_DIR / f"{pid}.jpg"
        
        is_hd = False
        img_rel = f"catalog/images/{pid}.jpg"
        img_w, img_h = 60, 80
        
        if hd_path.exists() and hd_path.stat().st_size > 2000:
            try:
                with PIL.Image.open(hd_path) as im:
                    img_w, img_h = im.size
                    if img_w >= 400:
                        is_hd = True
                        img_rel = f"catalog/images_hd/{pid}.jpg"
            except Exception:
                pass

        master_items.append({
            "id": pid,
            "name": product_name,
            "brand": brand,
            "category": cat,
            "subcategory": subcat,
            "slot": slot,
            "gender": gender,
            "occasion": usage,
            "color": color,
            "price": "Price unavailable",
            "currency": "USD",
            "description": f"Authentic {gender.lower()} {subcat.lower()} styled in {color.lower()} for {usage.lower()} wear.",
            "url": link_lookup.get(pid, {}).get("link", ""),
            "image_path": img_rel,
            "is_hd": is_hd,
            "width": img_w,
            "height": img_h,
            "source": "original_catalog",
            "is_ai_supported": True,
            "ai_class": atype
        })

    print(f"Processed 720 original products. Genuine HD: {sum(1 for x in master_items if x['is_hd'])} / 720")

    # 2. Integrate the 26 Curated HD Brand Collection products
    if CURATED_JSON.exists():
        curated_data = json.loads(CURATED_JSON.read_text())
        for c in curated_data:
            c_cat = c.get("category", "Tops")
            c_slot = c.get("slot", "top")
            # Map category to subcategory
            subcat = c.get("name", "").split()[0]
            master_items.append({
                "id": c.get("id"),
                "name": c.get("name"),
                "brand": c.get("brand"),
                "category": c_cat,
                "subcategory": c.get("name"),
                "slot": c_slot,
                "gender": c.get("gender", "Unisex"),
                "occasion": c.get("occasion", "Casual"),
                "color": c.get("color", "white"),
                "price": c.get("price", "$110.00"),
                "currency": "USD",
                "description": f"Curated luxury fashion piece from {c.get('brand')} collection.",
                "url": "",
                "image_path": c.get("image_path"),
                "is_hd": True,
                "width": c.get("width", 736),
                "height": c.get("height", 736),
                "source": "curated_brands",
                "is_ai_supported": (c_slot in ["top", "bottom", "dress", "outer", "shoes", "bag"]),
                "ai_class": "Casual Shoes" if c_cat == "Shoes" else ("Jeans" if "jeans" in c.get("name", "").lower() else "Shirts")
            })
        print(f"Integrated {len(curated_data)} curated HD products. Total master products: {len(master_items)}")

    # Save to JSON and CSV
    MASTER_JSON.write_text(json.dumps(master_items, indent=2, ensure_ascii=False))
    pd.DataFrame(master_items).to_csv(ROOT / "catalog" / "master_products.csv", index=False)
    print(f"Master catalog saved to {MASTER_JSON}")

if __name__ == "__main__":
    build()
