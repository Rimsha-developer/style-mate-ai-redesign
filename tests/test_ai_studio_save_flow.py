"""
Verification test for AI Studio Save-to-Wardrobe workflow.
Tests:
1. Verify get_slot_title works across all supported slots
2. Save Dress to My Wardrobe (Women, slot=dress)
3. Save Heels to My Wardrobe (Women, slot=shoes)
4. Verify persistence in wardrobe/wardrobe.json
5. Verify reload and data integrity
6. Clean up test entries
"""

import os
import sys
import json
import numpy as np

PROJECT_ROOT = "/Users/aen./Downloads/Friend_file/stylemate_redesign"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from services import ai_service

def test_slot_title():
    print("\n--- 1. Testing get_slot_title helper ---")
    slots = ["top", "bottom", "dress", "outer", "shoes", "bag"]
    expected = ["Tops", "Bottoms", "Dresses", "Outerwear", "Shoes", "Bags"]
    for s, exp in zip(slots, expected):
        title = ai_service.get_slot_title(s)
        assert title == exp, f"Expected {exp} for {s}, got {title}"
    print(f"✅ All {len(slots)} slot titles verified: {expected}")

def test_save_dress_and_heels():
    print("\n--- 2. Testing Save Dress and Heels to Wardrobe ---")
    wardrobe_json_path = os.path.join(PROJECT_ROOT, "wardrobe", "wardrobe.json")

    # 1. Dress
    dress_rgb = np.full((120, 120, 3), (85, 45, 30), dtype=np.uint8) # Brown dress color
    dress_saved = ai_service.add_garment_to_wardrobe(
        rgb_image=dress_rgb,
        type_name="Dresses",
        slot=ai_service.resolve_garment_slot("Dresses"),
        occasion="Casual",
        confidence=0.81,
        gender="Women"
    )
    assert dress_saved is not None, "Failed to save Dress"
    dress_id = dress_saved["id"]
    print(f"✅ Dress saved with ID: {dress_id}")

    # 2. Heels
    heels_rgb = np.full((120, 120, 3), (120, 20, 40), dtype=np.uint8)
    heels_saved = ai_service.add_garment_to_wardrobe(
        rgb_image=heels_rgb,
        type_name="Heels",
        slot=ai_service.resolve_garment_slot("Heels"),
        occasion="Casual",
        confidence=0.608,
        gender="Women"
    )
    assert heels_saved is not None, "Failed to save Heels"
    heels_id = heels_saved["id"]
    print(f"✅ Heels saved with ID: {heels_id}")

    # 3. Verify disk persistence in wardrobe.json
    print("\n--- 3. Verifying Disk Persistence in wardrobe.json ---")
    with open(wardrobe_json_path, "r", encoding="utf-8") as f:
        disk_items = json.load(f)

    disk_dress = next((item for item in disk_items if item["id"] == dress_id), None)
    assert disk_dress is not None, f"Dress {dress_id} not found in wardrobe.json"
    assert disk_dress["type"] == "Dresses", f"Expected type Dresses, got {disk_dress['type']}"
    assert disk_dress["slot"] == "dress", f"Expected slot dress, got {disk_dress['slot']}"
    assert disk_dress["gender"] == "Women", f"Expected gender Women, got {disk_dress['gender']}"
    print(f"✅ Disk verification for Dress PASSED: {disk_dress['type']} ({disk_dress['slot']}, {disk_dress['gender']})")

    disk_heels = next((item for item in disk_items if item["id"] == heels_id), None)
    assert disk_heels is not None, f"Heels {heels_id} not found in wardrobe.json"
    assert disk_heels["type"] == "Heels", f"Expected type Heels, got {disk_heels['type']}"
    assert disk_heels["slot"] == "shoes", f"Expected slot shoes, got {disk_heels['slot']}"
    assert disk_heels["gender"] == "Women", f"Expected gender Women, got {disk_heels['gender']}"
    print(f"✅ Disk verification for Heels PASSED: {disk_heels['type']} ({disk_heels['slot']}, {disk_heels['gender']})")

    # 4. Verify list_wardrobe_items reload
    print("\n--- 4. Verifying list_wardrobe_items() reload ---")
    loaded_items = ai_service.list_wardrobe_items()
    loaded_dress = next((i for i in loaded_items if i["id"] == dress_id), None)
    loaded_heels = next((i for i in loaded_items if i["id"] == heels_id), None)
    assert loaded_dress is not None and loaded_dress["file_exists"], "Loaded dress missing or file does not exist"
    assert loaded_heels is not None and loaded_heels["file_exists"], "Loaded heels missing or file does not exist"
    assert loaded_dress["slot_title"] == "Dresses", f"Expected Dresses, got {loaded_dress['slot_title']}"
    assert loaded_heels["slot_title"] == "Shoes", f"Expected Shoes, got {loaded_heels['slot_title']}"
    print("✅ list_wardrobe_items() reloaded both garments with verified image files!")

    # 5. Clean up test items
    print("\n--- 5. Clean up test garments ---")
    ai_service.delete_garment_from_wardrobe(dress_id)
    ai_service.delete_garment_from_wardrobe(heels_id)

    with open(wardrobe_json_path, "r", encoding="utf-8") as f:
        final_disk = json.load(f)
    assert not any(item["id"] == dress_id for item in final_disk), "Dress not deleted"
    assert not any(item["id"] == heels_id for item in final_disk), "Heels not deleted"
    print("✅ Cleanup verified: test garments removed cleanly from disk and json.")

if __name__ == "__main__":
    test_slot_title()
    test_save_dress_and_heels()
    print("\n==================================================")
    print("🎉 AI STUDIO SAVE WORKFLOW VERIFIED SUCCESSFULLY! 🎉")
    print("==================================================\n")
