"""
Style Mate AI — Outfit Ideas Recommendation Diversity & Deduplication Test Suite
==================================================================================
Tests:
  T1. No Duplicate Outfits: all generated outfits have unique order-independent ID sets
  T2. Content Uniqueness: no visual duplicates (same garment type, slot, and color)
  T3. Limited Wardrobe Variety: honest result count (returns exactly K unique outfits, no padding)
  T4. Sufficient Wardrobe Variety: generates >= 6 distinct combinations exploring alternative pieces
  T5. Accessory Variety Exploration: alternative shoes, outers, bags are explored rather than only one greedy pick
  T6. Gender Isolation Preserved: Men's never has Women's pieces; Women's never has Men's pieces
  T7. Master HD Catalog Collections Diversity: catalog mode generates strictly unique outfits
"""

import sys
import json
from pathlib import Path
import numpy as np

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
sys.path.insert(0, str(ROOT))

import engine
from services import ai_service
from ui.views.outfit_ideas_view import (
    CatalogWardrobeAdapter,
    _suggest_with_accessory_variety,
    _deduplicate_outfit_list,
    _load_master_df,
    GENDER_MEN,
    GENDER_WOMEN,
    GENDER_UNISEX,
)

RESULTS = []


def record(name: str, passed: bool, details: str = ""):
    icon = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{icon}] {name}: {details}")
    RESULTS.append({"Test": name, "Status": "PASS" if passed else "FAIL", "Details": details})


class MockWardrobe:
    """Mock Wardrobe for controlled testing of combinatorial variety and edge cases."""
    def __init__(self, items):
        self.items = items

    def by_slot(self, slot: str):
        return [i for i in self.items if i.get("slot") == slot]


# ---------------------------------------------------------------------------
# T1: No Duplicate Outfits (Order-Independent ID Uniqueness)
# ---------------------------------------------------------------------------
print("\n--- T1: No Duplicate Outfits (Order-Independent ID Set) ---")
try:
    wd = ai_service.get_wardrobe()
    outfits, raw_count = ai_service.generate_diverse_outfit_combinations(wd, occasion="Any", n=10)
    seen_id_sets = set()
    has_dup = False

    for idx, (score, pieces) in enumerate(outfits):
        id_set = frozenset(str(p.get("id") or p.get("path")) for p in pieces)
        if id_set in seen_id_sets:
            has_dup = True
            break
        seen_id_sets.add(id_set)

    assert not has_dup, "Found duplicate outfit by piece ID set!"
    assert len(outfits) == len(seen_id_sets), "Outfit count does not match unique ID sets"
    record("T1: No Duplicate Outfits", True,
           f"{len(outfits)} unique outfits generated from current wardrobe, 0 ID set duplicates")
except AssertionError as e:
    record("T1: No Duplicate Outfits", False, str(e))
except Exception as e:
    record("T1: No Duplicate Outfits", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T2: Content Uniqueness (No Visual Clones)
# ---------------------------------------------------------------------------
print("\n--- T2: Content Uniqueness (Visual Signature Dedup) ---")
try:
    # Test deduplicator directly with duplicated inputs
    dummy_piece_a1 = {"id": "uuid-1", "slot": "top", "type": "Shirts", "color": "black", "usage": "Casual"}
    dummy_piece_a2 = {"id": "uuid-2", "slot": "top", "type": "Shirts", "color": "black", "usage": "Casual"}  # clone
    dummy_piece_b = {"id": "uuid-3", "slot": "bottom", "type": "Jeans", "color": "denim", "usage": "Casual"}
    dummy_piece_s = {"id": "uuid-4", "slot": "shoes", "type": "Flats", "color": "beige", "usage": "Casual"}

    # Two outfits that look identical to the user but have different top UUIDs
    outfit1 = (95, [dummy_piece_a1, dummy_piece_b, dummy_piece_s])
    outfit2 = (95, [dummy_piece_a2, dummy_piece_b, dummy_piece_s])  # visual duplicate
    # An outfit with reordered pieces
    outfit1_reordered = (95, [dummy_piece_s, dummy_piece_b, dummy_piece_a1])

    raw_list = [outfit1, outfit2, outfit1_reordered]
    deduped = _deduplicate_outfit_list(raw_list, max_items=6)

    assert len(deduped) == 1, f"Expected exactly 1 unique outfit after content dedup, got {len(deduped)}"
    record("T2: Content Uniqueness", True, "Visual duplicate items with different UUIDs and reordered pieces correctly collapsed to 1")
except AssertionError as e:
    record("T2: Content Uniqueness", False, str(e))
except Exception as e:
    record("T2: Content Uniqueness", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T3: Limited Wardrobe Variety (Honest Result Count)
# ---------------------------------------------------------------------------
print("\n--- T3: Limited Wardrobe Variety (Honest Result Count) ---")
try:
    # A tiny wardrobe with exactly 1 top, 1 bottom, 1 shoe -> exactly 1 unique outfit possible
    limited_items = [
        {"id": "lim-top", "slot": "top", "type": "Tshirts", "usage": "Casual", **engine.color_info((250, 250, 250)), "worn": 0},
        {"id": "lim-bot", "slot": "bottom", "type": "Jeans", "usage": "Casual", **engine.color_info((25, 45, 95)), "worn": 0},
        {"id": "lim-sho", "slot": "shoes", "type": "Flats", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
    ]
    lim_wd = MockWardrobe(limited_items)
    outfits, raw_count = ai_service.generate_diverse_outfit_combinations(lim_wd, occasion="Casual", n=6)

    assert len(outfits) == 1, f"Expected honest count of 1 outfit, got {len(outfits)}"
    assert raw_count == 1, f"Expected 1 raw combo, got {raw_count}"
    record("T3: Limited Wardrobe Variety", True,
           f"Honest count returned: {len(outfits)} outfit when only 1 is physically possible (no padding/repeats)")
except AssertionError as e:
    record("T3: Limited Wardrobe Variety", False, str(e))
except Exception as e:
    record("T3: Limited Wardrobe Variety", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T4: Sufficient Wardrobe Variety (Multi-piece Combinatorial Expansion)
# ---------------------------------------------------------------------------
print("\n--- T4: Sufficient Wardrobe Variety ---")
try:
    # Rich wardrobe: 3 tops, 3 bottoms, 3 shoes, 2 outers, 2 bags
    rich_items = [
        {"id": "t1", "type": "Tshirts", "slot": "top", "usage": "Casual", **engine.color_info((250, 250, 250)), "worn": 0},
        {"id": "t2", "type": "Shirts", "slot": "top", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
        {"id": "t3", "type": "Tops", "slot": "top", "usage": "Casual", **engine.color_info((220, 150, 180)), "worn": 0},
        {"id": "b1", "type": "Jeans", "slot": "bottom", "usage": "Casual", **engine.color_info((25, 45, 95)), "worn": 0},
        {"id": "b2", "type": "Trousers", "slot": "bottom", "usage": "Casual", **engine.color_info((200, 190, 170)), "worn": 0},
        {"id": "b3", "type": "Shorts", "slot": "bottom", "usage": "Casual", **engine.color_info((30, 30, 30)), "worn": 0},
        {"id": "s1", "type": "Casual Shoes", "slot": "shoes", "usage": "Casual", **engine.color_info((245, 245, 245)), "worn": 0},
        {"id": "s2", "type": "Flats", "slot": "shoes", "usage": "Casual", **engine.color_info((180, 140, 100)), "worn": 0},
        {"id": "s3", "type": "Heels", "slot": "shoes", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
        {"id": "o1", "type": "Jackets", "slot": "outer", "usage": "Casual", **engine.color_info((30, 40, 80)), "worn": 0},
        {"id": "o2", "type": "Sweaters", "slot": "outer", "usage": "Casual", **engine.color_info((230, 220, 200)), "worn": 0},
        {"id": "g1", "type": "Handbags", "slot": "bag", "usage": "Casual", **engine.color_info((150, 100, 50)), "worn": 0},
        {"id": "g2", "type": "Clutches", "slot": "bag", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
    ]
    rich_wd = MockWardrobe(rich_items)
    outfits, raw_count = ai_service.generate_diverse_outfit_combinations(rich_wd, occasion="Casual", n=6)

    assert len(outfits) == 6, f"Expected 6 diverse outfits, got {len(outfits)}"
    # Verify all 6 are distinct
    id_sets = [frozenset(p["id"] for p in pieces) for score, pieces in outfits]
    assert len(set(id_sets)) == 6, "Expected 6 unique ID sets"

    # Verify diversity across tops and bottoms
    used_tops = set(p["id"] for score, pieces in outfits for p in pieces if p["slot"] == "top")
    used_bottoms = set(p["id"] for score, pieces in outfits for p in pieces if p["slot"] == "bottom")
    assert len(used_tops) >= 2, f"Expected at least 2 distinct tops used, got {len(used_tops)}"
    assert len(used_bottoms) >= 2, f"Expected at least 2 distinct bottoms used, got {len(used_bottoms)}"

    record("T4: Sufficient Wardrobe Variety", True,
           f"Generated {len(outfits)} distinct outfits across {len(used_tops)} tops and {len(used_bottoms)} bottoms")
except AssertionError as e:
    record("T4: Sufficient Wardrobe Variety", False, str(e))
except Exception as e:
    record("T4: Sufficient Wardrobe Variety", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T5: Accessory Variety Exploration
# ---------------------------------------------------------------------------
print("\n--- T5: Accessory Variety Exploration ---")
try:
    # 1 base top + 1 bottom, but 3 different shoes -> should explore multiple shoes!
    acc_items = [
        {"id": "top-base", "slot": "top", "type": "Tshirts", "usage": "Casual", **engine.color_info((250, 250, 250)), "worn": 0},
        {"id": "bot-base", "slot": "bottom", "type": "Jeans", "usage": "Casual", **engine.color_info((25, 45, 95)), "worn": 0},
        {"id": "shoe-white", "slot": "shoes", "type": "Casual Shoes", "usage": "Casual", **engine.color_info((250, 250, 250)), "worn": 0},
        {"id": "shoe-black", "slot": "shoes", "type": "Flats", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
        {"id": "shoe-beige", "slot": "shoes", "type": "Loafers", "usage": "Casual", **engine.color_info((210, 190, 160)), "worn": 0},
    ]
    acc_wd = MockWardrobe(acc_items)
    outfits, raw_count = ai_service.generate_diverse_outfit_combinations(acc_wd, occasion="Casual", n=3)

    assert len(outfits) == 3, f"Expected 3 distinct outfits with different shoes, got {len(outfits)}"
    shoes_used = [p["id"] for score, pieces in outfits for p in pieces if p["slot"] == "shoes"]
    assert len(set(shoes_used)) == 3, f"Expected 3 distinct shoes used, got {len(set(shoes_used))}"

    record("T5: Accessory Variety Exploration", True,
           f"All 3 compatible shoes utilized in distinct combinations: {shoes_used}")
except AssertionError as e:
    record("T5: Accessory Variety Exploration", False, str(e))
except Exception as e:
    record("T5: Accessory Variety Exploration", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T6: Gender Isolation Preserved in Personal Wardrobe
# ---------------------------------------------------------------------------
print("\n--- T6: Gender Isolation Preserved in Personal Wardrobe ---")
try:
    tagged_items = [
        {"id": "w-top", "slot": "top", "type": "Tops", "gender": "Women", "usage": "Casual", **engine.color_info((250, 250, 250)), "worn": 0},
        {"id": "m-top", "slot": "top", "type": "Shirts", "gender": "Men", "usage": "Casual", **engine.color_info((30, 40, 80)), "worn": 0},
        {"id": "u-bot", "slot": "bottom", "type": "Jeans", "gender": "Unisex", "usage": "Casual", **engine.color_info((25, 45, 95)), "worn": 0},
        {"id": "w-sho", "slot": "shoes", "type": "Heels", "gender": "Women", "usage": "Casual", **engine.color_info((20, 20, 20)), "worn": 0},
        {"id": "m-sho", "slot": "shoes", "type": "Formal Shoes", "gender": "Men", "usage": "Casual", **engine.color_info((100, 70, 40)), "worn": 0},
    ]
    tag_wd = MockWardrobe(tagged_items)

    # Test Women mode
    outfits_w, _ = ai_service.generate_diverse_outfit_combinations(tag_wd, occasion="Casual", gender_mode=GENDER_WOMEN, n=6)
    for score, pieces in outfits_w:
        for p in pieces:
            assert p.get("gender") in {"Women", "Unisex", None}, f"Men's item {p['id']} leaked into Women's outfit!"

    # Test Men mode
    outfits_m, _ = ai_service.generate_diverse_outfit_combinations(tag_wd, occasion="Casual", gender_mode=GENDER_MEN, n=6)
    for score, pieces in outfits_m:
        for p in pieces:
            assert p.get("gender") in {"Men", "Unisex", None}, f"Women's item {p['id']} leaked into Men's outfit!"

    record("T6: Gender Isolation Preserved", True, "Zero cross-gender contamination in Personal Wardrobe outfit generation")
except AssertionError as e:
    record("T6: Gender Isolation Preserved", False, str(e))
except Exception as e:
    record("T6: Gender Isolation Preserved", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T7: Master HD Catalog Collections Diversity & Deduplication
# ---------------------------------------------------------------------------
print("\n--- T7: Master HD Catalog Collections Diversity & Deduplication ---")
try:
    master_df = _load_master_df()
    for mode, label in [(GENDER_WOMEN, "Women"), (GENDER_MEN, "Men"), (GENDER_UNISEX, "Unisex")]:
        adapter = CatalogWardrobeAdapter(master_df, occasion="Casual", gender_mode=mode, max_per_slot=14, seed=42)
        outfits = _suggest_with_accessory_variety(adapter, occasion="Casual", n=6)
        assert len(outfits) > 0, f"Expected outfits for {label} in Catalog mode"

        # Check order-independent ID set uniqueness
        seen_ids = set()
        for idx, (score, pieces) in enumerate(outfits):
            id_set = frozenset(str(p.get("id")) for p in pieces)
            assert id_set not in seen_ids, f"Duplicate outfit in Catalog mode for {label} at index {idx}!"
            seen_ids.add(id_set)

    record("T7: Catalog Collections Diversity", True, "Women, Men, and Unisex catalog outfits verified 100% unique (0 duplicate ID sets)")
except AssertionError as e:
    record("T7: Catalog Collections Diversity", False, str(e))
except Exception as e:
    record("T7: Catalog Collections Diversity", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 80)
print(f"{'TEST NAME':<44} | {'STATUS':<6} | {'DETAILS'}")
print("=" * 80)
for r in RESULTS:
    print(f"{r['Test']:<44} | {r['Status']:<6} | {r['Details']}")
print("=" * 80)

all_passed = all(r["Status"] == "PASS" for r in RESULTS)
print(f"\nOVERALL RESULT: {'ALL TESTS PASSED (7/7)' if all_passed else 'SOME TESTS FAILED'}\n")
sys.exit(0 if all_passed else 1)
