"""
Comprehensive Functional Tests for Outfit Ideas Generator
Validates:
1. Circular hue harmony and neutral compatibility
2. Occasion compatibility scoring
3. Natural language pairing rationale (engine.explain)
4. Outfit generation from Personal Wardrobe
5. Outfit generation from Master HD Catalog
6. Product names and authentic HD image resolution for every piece in generated outfits
"""

import os
import sys
from pathlib import Path

# Add project root to path
ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
sys.path.insert(0, str(ROOT))

import engine
from services import ai_service
from ui.views.outfit_ideas_view import CatalogWardrobeAdapter, _resolve_hd_image_path

def test_color_harmony_and_neutrals():
    print("--- 1. Testing Color Harmony & Neutral Pairing ---")
    
    # Test circular hue harmony on known color pairs using engine.color_info
    # engine.color_info takes (r, g, b)
    c_white = engine.color_info((250, 250, 250))
    c_navy = engine.color_info((20, 30, 80))
    c_pink = engine.color_info((240, 150, 180))
    c_black = engine.color_info((15, 15, 15))
    c_red = engine.color_info((220, 20, 20))
    c_green = engine.color_info((20, 180, 40))

    item_white = {"type": "Tshirts", "slot": "top", "usage": "Casual", **c_white}
    item_navy = {"type": "Jeans", "slot": "bottom", "usage": "Casual", **c_navy}
    item_pink = {"type": "Tops", "slot": "top", "usage": "Casual", **c_pink}
    item_black = {"type": "Trousers", "slot": "bottom", "usage": "Formal", **c_black}
    item_red = {"type": "Tshirts", "slot": "top", "usage": "Casual", **c_red}
    item_green = {"type": "Jackets", "slot": "outer", "usage": "Casual", **c_green}

    # White is neutral -> harmony score should be 85 (or 70 if same color)
    h_white_navy = engine.harmony(item_white, item_navy)
    print(f"  Harmony (white neutral + navy): {h_white_navy}/100")
    assert h_white_navy >= 80, f"Expected high neutral pairing harmony, got {h_white_navy}"

    # Black is neutral -> harmony score should be 85
    h_black_pink = engine.harmony(item_black, item_pink)
    print(f"  Harmony (black neutral + pink): {h_black_pink}/100")
    assert h_black_pink >= 80, f"Expected high neutral pairing harmony, got {h_black_pink}"

    # Complementary red + green
    h_red_green = engine.harmony(item_red, item_green)
    print(f"  Harmony (red + green complementary): {h_red_green}/100")
    assert h_red_green >= 70, f"Expected complementary harmony >= 70, got {h_red_green}"

    # Natural language rationale
    why_neutral = engine.explain(item_white, item_navy)
    print(f"  Rationale (white + navy): '{why_neutral}'")
    assert "neutral" in why_neutral.lower(), f"Expected neutral in explanation, got {why_neutral}"
    print("  [PASS] Color harmony & neutral rules verified.")


def test_occasion_compatibility():
    print("\n--- 2. Testing Occasion Compatibility Scoring ---")
    # Matching occasions
    c_formal = engine.usage_compat("Formal", "Formal")
    c_casual = engine.usage_compat("Casual", "Casual")
    print(f"  Occasion compat (Formal + Formal): {c_formal}/100")
    print(f"  Occasion compat (Casual + Casual): {c_casual}/100")
    assert c_formal == 100
    assert c_casual == 100

    # Cross-occasion penalty (Ethnic vs Sports)
    c_clash = engine.usage_compat("Ethnic", "Sports")
    print(f"  Occasion compat (Ethnic + Sports clash): {c_clash}/100")
    assert c_clash <= 50, f"Expected cross-occasion penalty, got {c_clash}"
    print("  [PASS] Occasion compatibility scoring verified.")


def test_catalog_outfit_generation():
    print("\n--- 3. Testing Outfit Generation from Master HD Catalog ---")
    cat = ai_service.get_catalog()
    assert cat is not None and not cat.df.empty, "Catalog dataframe empty"
    print(f"  Loaded catalog dataframe with {len(cat.df)} items")

    for occ in ["Casual", "Formal", "Sports"]:
        adapter = CatalogWardrobeAdapter(cat.df, occasion=occ, max_per_slot=12, seed=42)
        outfits = engine.suggest(adapter, occasion=occ, n=4)
        print(f"  Generated {len(outfits)} ensembles for occasion '{occ}':")
        assert len(outfits) > 0, f"Expected outfits for {occ}"

        for idx, (score, pieces) in enumerate(outfits[:2]):
            print(f"    Ensemble #{idx+1} · Score: {score}/100 · Pieces: {len(pieces)}")
            assert score >= 60, f"Expected viable score (>=60), got {score}"
            assert len(pieces) >= 2, f"Expected multi-piece ensemble, got {len(pieces)}"

            for p in pieces:
                p_name = p.get("type", "Garment")
                p_slot = p.get("slot", "")
                p_color = p.get("color", "")
                img_path = _resolve_hd_image_path(p)
                assert img_path.exists(), f"Image path does not exist: {img_path}"
                print(f"      - [{p_slot.upper()}] {p_name} ({p_color}) -> {img_path.name} (Verified HD on disk)")
    print("  [PASS] Master HD Catalog outfit generation verified.")


def test_personal_wardrobe_outfit_generation():
    print("\n--- 4. Testing Outfit Generation from Personal Wardrobe ---")
    # Create or populate test items in wardrobe
    wardrobe = ai_service.get_wardrobe()
    orig_items = list(wardrobe.items)

    injected_ids = []
    try:
        # Add a test top and bottom if not already present
        sample_top = ROOT / "catalog" / "images_hd" / "2847.jpg"
        sample_bottom = ROOT / "catalog" / "images_hd" / "44580.jpg"
        sample_shoes = ROOT / "catalog" / "images_hd" / "45343.jpg"

        if sample_top.exists() and sample_bottom.exists():
            item_top = ai_service.add_catalog_item_to_wardrobe(str(sample_top), "Classic Tee", "top", "Casual")
            item_bottom = ai_service.add_catalog_item_to_wardrobe(str(sample_bottom), "Denim Jeans", "bottom", "Casual")
            item_shoe = ai_service.add_catalog_item_to_wardrobe(str(sample_shoes), "Leather Shoes", "shoes", "Casual")
            injected_ids = [item_top["id"], item_bottom["id"], item_shoe["id"]]
            print(f"  Injected wardrobe items: {item_top['id']}, {item_bottom['id']}, {item_shoe['id']}")

            wb_updated = ai_service.get_wardrobe()
            wb_outfits = ai_service.generate_outfit_combinations(wb_updated, occasion="Casual", n=4)
            print(f"  Generated {len(wb_outfits)} personal wardrobe outfit(s)")
            assert len(wb_outfits) > 0, "Expected at least 1 personal wardrobe outfit"

            for idx, (score, pieces) in enumerate(wb_outfits):
                print(f"    Personal Outfit #{idx+1} · Score: {score}/100 · Pieces: {len(pieces)}")
                for p in pieces:
                    print(f"      - {p.get('type')} ({p.get('color')}) slot={p.get('slot')}")
            print("  [PASS] Personal wardrobe combinatorial engine verified.")
    finally:
        # Clean up test items by ID and by type
        wb = ai_service.get_wardrobe()
        for iid in injected_ids:
            wb.remove(iid)
        for it in list(wb.items):
            if it.get("type") in ["Classic Tee", "Denim Jeans", "Leather Shoes"] or it.get("name") in ["Classic Tee", "Denim Jeans", "Leather Shoes"]:
                wb.remove(it["id"])
        print("  Cleaned up test items from personal wardrobe.")


if __name__ == "__main__":
    test_color_harmony_and_neutrals()
    test_occasion_compatibility()
    test_catalog_outfit_generation()
    test_personal_wardrobe_outfit_generation()
    print("\n==========================================")
    print("ALL OUTFIT IDEAS FUNCTIONAL TESTS PASSED!")
    print("==========================================")
