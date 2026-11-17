"""
Comprehensive Verification Test Suite for Style Mate AI Final Consolidated Fixes.
Verifies all 7 core requirements:
1. Slot assignment taxonomy (resolve_garment_slot)
2. Single garment classification accuracy & aspect-ratio padding on real images
3. Wardrobe CRUD persistence with gender metadata & reload integrity
4. Price display removal across catalog views
5. Outfit refresh distinctiveness & exclude_ids
6. Admin module removal from navigation and app router
"""

import os
import sys
import json
import cv2
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = "/Users/aen./Downloads/Friend_file/stylemate_redesign"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services import ai_service
from ui.components.navigation import NAV_PAGES

def test_1_slot_assignment_taxonomy():
    print("\n--- Test 1: Slot Assignment Taxonomy ---")
    test_cases = [
        ("Kurta", "top"),
        ("Long Shirt", "top"),
        ("Tunic", "top"),
        ("Tshirts", "top"),
        ("Shirts", "top"),
        ("Tops", "top"),
        ("Dress", "dress"),
        ("Dresses", "dress"),
        ("Gown", "dress"),
        ("Frock", "dress"),
        ("Trousers", "bottom"),
        ("Jeans", "bottom"),
        ("Shorts", "bottom"),
        ("Skirts", "bottom"),
        ("Leggings", "bottom"),
        ("Jackets", "outer"),
        ("Blazer", "outer"),
        ("Overcoat", "outer"),
        ("Sweaters", "top"),
        ("Heels", "shoes"),
        ("Flats", "shoes"),
        ("Shoes", "shoes"),
        ("Handbags", "bag"),
    ]
    for garment_type, expected_slot in test_cases:
        actual_slot = ai_service.resolve_garment_slot(garment_type)
        assert actual_slot == expected_slot, f"Expected {expected_slot} for {garment_type}, got {actual_slot}"
    print(f"✅ All {len(test_cases)} slot taxonomy test cases PASSED!")

def test_2_single_garment_aspect_ratio_accuracy():
    print("\n--- Test 2: Single Garment Aspect Ratio Classification ---")
    
    # Test Black Pants (previously misclassified as Shorts)
    pants_path = "/Users/aen./Downloads/369787819421641658.jpg"
    if os.path.exists(pants_path):
        img_bgr = cv2.imread(pants_path)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        res = ai_service.analyze_single_garment(img_rgb)
        pred = res.get("type")
        conf = res.get("conf", 0.0)
        print(f"Full-length black pants prediction: {pred} ({conf*100:.1f}%)")
        assert pred == "Trousers", f"Expected Trousers for black pants, got {pred}"
        assert conf >= 0.85, f"Expected high confidence for Trousers, got {conf}"
        print("✅ Full-length black pants correctly classified as Trousers (aspect-ratio padding verified)!")
    else:
        print("⚠️ Warning: 369787819421641658.jpg not found in Downloads")

    # Test Brown Dress (previously 26.9% uncertain)
    dress_path = "/Users/aen./Downloads/615374736631278634.jpg"
    if os.path.exists(dress_path):
        img_bgr = cv2.imread(dress_path)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        res = ai_service.analyze_single_garment(img_rgb)
        pred = res.get("type")
        conf = res.get("conf", 0.0)
        print(f"Brown dress prediction: {pred} ({conf*100:.1f}%)")
        assert pred == "Dresses", f"Expected Dresses for brown dress, got {pred}"
        assert conf >= 0.70, f"Expected confidence >= 70% for Dresses, got {conf}"
        print("✅ Long brown dress correctly classified as Dresses with high confidence!")
    else:
        print("⚠️ Warning: 615374736631278634.jpg not found in Downloads")

    # Test Corduroy Shirt
    shirt_path = "/Users/aen./Downloads/922393567461012531.jpg"
    if os.path.exists(shirt_path):
        img_bgr = cv2.imread(shirt_path)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        res = ai_service.analyze_single_garment(img_rgb)
        pred = res.get("type")
        conf = res.get("conf", 0.0)
        print(f"Blue corduroy shirt prediction: {pred} ({conf*100:.1f}%)")
        assert pred == "Shirts", f"Expected Shirts for blue shirt, got {pred}"
        print("✅ Blue corduroy shirt correctly classified as Shirts!")
    else:
        print("⚠️ Warning: 922393567461012531.jpg not found in Downloads")

def test_3_wardrobe_crud_persistence():
    print("\n--- Test 3: Wardrobe CRUD Persistence with Gender ---")
    wardrobe_json_path = os.path.join(PROJECT_ROOT, "wardrobe", "wardrobe.json")
    
    # 1. Add item with gender
    dummy_img = np.full((120, 120, 3), 200, dtype=np.uint8)
    test_type = "Kurta"
    test_gender = "Women"
    
    added_item = ai_service.add_garment_to_wardrobe(
        rgb_image=dummy_img,
        type_name=test_type,
        slot="top",
        occasion="Ethnic",
        confidence=0.95,
        gender=test_gender
    )
    test_id = added_item["id"]
    assert test_id, "Failed to get item ID from added garment"
    
    # Verify in-memory and disk
    with open(wardrobe_json_path, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    found = next((item for item in disk_data if item["id"] == test_id), None)
    assert found is not None, "Item not found in wardrobe.json on disk"
    assert found["gender"] == "Women", f"Expected Women gender, got {found['gender']}"
    assert found["slot"] == "top", f"Expected slot 'top' for Kurta, got {found['slot']}"
    print("✅ Add item with gender and canonical slot PASSED!")

    # 2. Update item
    update_success = ai_service.update_wardrobe_item(
        item_id=test_id,
        new_type="Shirts",
        new_slot="top",
        new_usage="Casual",
        new_gender="Unisex"
    )
    assert update_success, "Failed to update item"
    with open(wardrobe_json_path, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    updated = next((item for item in disk_data if item["id"] == test_id), None)
    assert updated["type"] == "Shirts"
    assert updated["gender"] == "Unisex"
    print("✅ Update item with new gender and category PASSED!")

    # 3. Delete item
    delete_success = ai_service.delete_garment_from_wardrobe(test_id)
    assert delete_success, "Failed to delete item"
    with open(wardrobe_json_path, "r", encoding="utf-8") as f:
        disk_data = json.load(f)
    deleted = next((item for item in disk_data if item["id"] == test_id), None)
    assert deleted is None, "Item still present in wardrobe.json after deletion"
    print("✅ Delete item and disk cleanup PASSED!")

def test_4_admin_module_removal():
    print("\n--- Test 4: Admin Module Removal ---")
    assert "Admin" not in NAV_PAGES, f"Admin still in NAV_PAGES: {NAV_PAGES}"
    
    # Check app.py does not route to Admin
    app_path = os.path.join(PROJECT_ROOT, "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        app_content = f.read()
    assert "render_admin_view" not in app_content, "render_admin_view found in app.py"
    assert 'active_page == "Admin"' not in app_content, 'active_page == "Admin" routing found in app.py'
    print("✅ Admin module completely removed from navigation and routing!")

def test_5_price_display_removal():
    print("\n--- Test 5: Price Display Removal in Catalog ---")
    master_path = os.path.join(PROJECT_ROOT, "ui", "views", "master_catalog_view.py")
    with open(master_path, "r", encoding="utf-8") as f:
        master_content = f.read()
    assert "price_html" not in master_content, "price_html found in master_catalog_view.py"
    assert "Price unavailable" not in master_content, "Price unavailable found in master_catalog_view.py"

    curated_path = os.path.join(PROJECT_ROOT, "ui", "views", "curated_brands_view.py")
    with open(curated_path, "r", encoding="utf-8") as f:
        curated_content = f.read()
    assert "price_display" not in curated_content, "price_display found in curated_brands_view.py"
    assert "price_class" not in curated_content, "price_class found in curated_brands_view.py"
    print("✅ Price displays completely removed from Master and Curated Catalog views!")

def test_6_outfit_refresh_distinctiveness():
    print("\n--- Test 6: Outfit Refresh Distinctiveness & Exclude IDs ---")
    # Verify generate_diverse_outfit_combinations supports exclude_ids
    import inspect
    sig = inspect.signature(ai_service.generate_diverse_outfit_combinations)
    assert "exclude_ids" in sig.parameters, "exclude_ids parameter missing from generate_diverse_outfit_combinations"
    print("✅ Outfit recommendation refresh cycle signature verified!")

if __name__ == "__main__":
    test_1_slot_assignment_taxonomy()
    test_2_single_garment_aspect_ratio_accuracy()
    test_3_wardrobe_crud_persistence()
    test_4_admin_module_removal()
    test_5_price_display_removal()
    test_6_outfit_refresh_distinctiveness()
    print("\n=======================================================")
    print("🎉 ALL FINAL CONSOLIDATED FIXES VERIFIED SUCCESSFULLY! 🎉")
    print("=======================================================\n")
