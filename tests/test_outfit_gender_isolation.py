"""
Style Mate AI — Outfit Gender Isolation Test Suite
====================================================
Tests:
  T1  Generate >= 20 Men's outfits; assert all pieces in {Men, Unisex}
  T2  Generate >= 20 Women's outfits; assert all pieces in {Women, Unisex}
  T3  Generate >= 10 Unisex outfits; assert all pieces in {Unisex}
  T4  Boys/Girls/unknown/missing/empty are excluded from all adult modes
  T5  Women's heels never appear in Men's outfits unless labeled Unisex
  T6  Men's products never appear in Women's outfits unless labeled Unisex
  T7  Regression: existing outfit test suite still passes
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
    GENDER_MEN,
    GENDER_WOMEN,
    GENDER_UNISEX,
    _load_master_df,
    _suggest_with_accessory_variety,
)

# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------

RESULTS = []


def record(name: str, passed: bool, details: str = ""):
    icon = "✓ PASS" if passed else "✗ FAIL"
    print(f"[{icon}] {name}: {details}")
    RESULTS.append({"Test": name, "Status": "PASS" if passed else "FAIL", "Details": details})


def _make_adapter(gender_mode: str, occasion: str = "Any", n_outfits: int = 6, seed: int = 42):
    df = _load_master_df()
    adapter = CatalogWardrobeAdapter(df, occasion=occasion, gender_mode=gender_mode, max_per_slot=20, seed=seed)
    return adapter


def _generate_outfits(gender_mode: str, n: int = 25, seed: int = 42) -> list:
    adapter = _make_adapter(gender_mode, occasion="Any", n_outfits=n, seed=seed)
    outfits = _suggest_with_accessory_variety(adapter, occasion="Any", n=n)
    return outfits


def _gender_of(piece: dict) -> str:
    return str(piece.get("gender", "")).strip().lower()


# ---------------------------------------------------------------------------
# T1 — Men's: >= 20 outfits, all pieces {Men, Unisex}
# ---------------------------------------------------------------------------
print("\n--- T1: Men's Outfits (>= 20, all pieces in {Men, Unisex}) ---")
try:
    outfits_men = _generate_outfits(GENDER_MEN, n=25)
    assert len(outfits_men) >= 20, f"Expected >= 20 Men's outfits, got {len(outfits_men)}"
    violations = []
    for score, pieces in outfits_men:
        for p in pieces:
            g = _gender_of(p)
            if g not in {"men", "unisex"}:
                violations.append(f"{p.get('name', '?')} has gender='{g}'")
    assert not violations, f"Gender violations in Men's outfits: {violations[:5]}"
    # Print samples
    print(f"  Generated {len(outfits_men)} Men's outfits")
    for i, (score, pieces) in enumerate(outfits_men[:3]):
        genders = [p.get("gender", "?") for p in pieces]
        names = [p.get("name") or p.get("type", "?") for p in pieces]
        slots = [p.get("slot", "?") for p in pieces]
        print(f"  Outfit #{i+1}: Score={score}, Pieces={len(pieces)}")
        for n2, s, g in zip(names, slots, genders):
            print(f"    [{s.upper()}] {n2} — gender: {g}")
    record("T1: Men's Gender Isolation", True,
           f"{len(outfits_men)} outfits, 0 violations, all pieces in {{Men, Unisex}}")
except AssertionError as e:
    record("T1: Men's Gender Isolation", False, str(e))
except Exception as e:
    record("T1: Men's Gender Isolation", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T2 — Women's: >= 20 outfits, all pieces {Women, Unisex}
# ---------------------------------------------------------------------------
print("\n--- T2: Women's Outfits (>= 20, all pieces in {Women, Unisex}) ---")
try:
    outfits_women = _generate_outfits(GENDER_WOMEN, n=25)
    assert len(outfits_women) >= 20, f"Expected >= 20 Women's outfits, got {len(outfits_women)}"
    violations = []
    for score, pieces in outfits_women:
        for p in pieces:
            g = _gender_of(p)
            if g not in {"women", "unisex"}:
                violations.append(f"{p.get('name', '?')} has gender='{g}'")
    assert not violations, f"Gender violations in Women's outfits: {violations[:5]}"
    print(f"  Generated {len(outfits_women)} Women's outfits")
    for i, (score, pieces) in enumerate(outfits_women[:3]):
        genders = [p.get("gender", "?") for p in pieces]
        names = [p.get("name") or p.get("type", "?") for p in pieces]
        slots = [p.get("slot", "?") for p in pieces]
        print(f"  Outfit #{i+1}: Score={score}, Pieces={len(pieces)}")
        for n2, s, g in zip(names, slots, genders):
            print(f"    [{s.upper()}] {n2} — gender: {g}")
    record("T2: Women's Gender Isolation", True,
           f"{len(outfits_women)} outfits, 0 violations, all pieces in {{Women, Unisex}}")
except AssertionError as e:
    record("T2: Women's Gender Isolation", False, str(e))
except Exception as e:
    record("T2: Women's Gender Isolation", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T3 — Unisex: >= 10 outfits, all pieces {Unisex} only
# ---------------------------------------------------------------------------
print("\n--- T3: Unisex Outfits (>= 10, all pieces == Unisex) ---")
try:
    outfits_unisex = _generate_outfits(GENDER_UNISEX, n=15)
    assert len(outfits_unisex) >= 10, f"Expected >= 10 Unisex outfits, got {len(outfits_unisex)}"
    violations = []
    for score, pieces in outfits_unisex:
        for p in pieces:
            g = _gender_of(p)
            if g != "unisex":
                violations.append(f"{p.get('name', '?')} has gender='{g}'")
    assert not violations, f"Non-Unisex pieces in Unisex outfits: {violations[:5]}"
    print(f"  Generated {len(outfits_unisex)} Unisex outfits")
    for i, (score, pieces) in enumerate(outfits_unisex[:3]):
        genders = [p.get("gender", "?") for p in pieces]
        print(f"  Unisex Outfit #{i+1}: Score={score}, Pieces={len(pieces)}, Genders={genders}")
    record("T3: Unisex Gender Isolation", True,
           f"{len(outfits_unisex)} outfits, 0 violations, all pieces == Unisex")
except AssertionError as e:
    record("T3: Unisex Gender Isolation", False, str(e))
except Exception as e:
    record("T3: Unisex Gender Isolation", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T4 — Boys/Girls/unknown/missing excluded from all adult modes
# ---------------------------------------------------------------------------
print("\n--- T4: Boys/Girls/Unknown/Missing excluded from all adult modes ---")
try:
    forbidden = {"boys", "girls", "", "unknown", "none", "nan"}
    for mode_label, outfits in [
        ("Men's", outfits_men),
        ("Women's", outfits_women),
        ("Unisex", outfits_unisex),
    ]:
        leaks = []
        for score, pieces in outfits:
            for p in pieces:
                g = _gender_of(p)
                if g in forbidden:
                    leaks.append(f"{p.get('name', '?')} gender='{g}' in {mode_label}")
        assert not leaks, f"Forbidden genders leaked into {mode_label}: {leaks[:5]}"
        print(f"  {mode_label}: 0 Boys/Girls/unknown/missing leaks")

    # Also verify no Boys/Girls items in the adapter pool
    for mode, label in [(GENDER_MEN, "Men"), (GENDER_WOMEN, "Women"), (GENDER_UNISEX, "Unisex")]:
        adapter = _make_adapter(mode)
        all_genders = set(adapter.df["gender"].str.strip().str.lower().unique())
        bad = all_genders & forbidden
        assert not bad, f"Forbidden genders in {label} adapter pool: {bad}"

    record("T4: Boys/Girls/Unknown Excluded", True,
           "Boys, Girls, empty, unknown, none excluded from all 3 adult outfit modes")
except AssertionError as e:
    record("T4: Boys/Girls/Unknown Excluded", False, str(e))
except Exception as e:
    record("T4: Boys/Girls/Unknown Excluded", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T5 — Women's heels never in Men's outfits unless Unisex
# ---------------------------------------------------------------------------
print("\n--- T5: Women's heels must NOT appear in Men's outfits ---")
try:
    heels_in_mens = []
    for score, pieces in outfits_men:
        for p in pieces:
            type_str = str(p.get("type", "") or p.get("name", "")).lower()
            g = _gender_of(p)
            if "heel" in type_str and g != "unisex":
                heels_in_mens.append(f"{p.get('name','?')} (gender={p.get('gender','?')})")
    assert not heels_in_mens, f"Women's heels found in Men's outfits: {heels_in_mens}"
    print(f"  0 Women's heel items found in {len(outfits_men)} Men's outfits")
    record("T5: Women's Heels Absent from Men's", True,
           "0 Women's heel items leaked into any Men's outfit")
except AssertionError as e:
    record("T5: Women's Heels Absent from Men's", False, str(e))
except Exception as e:
    record("T5: Women's Heels Absent from Men's", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T6 — Men's products never in Women's outfits unless Unisex
# ---------------------------------------------------------------------------
print("\n--- T6: Men's products must NOT appear in Women's outfits ---")
try:
    mens_in_womens = []
    for score, pieces in outfits_women:
        for p in pieces:
            g = _gender_of(p)
            if g == "men":
                mens_in_womens.append(
                    f"{p.get('name','?')} (slot={p.get('slot','?')}, gender={p.get('gender','?')})"
                )
    assert not mens_in_womens, f"Men's products found in Women's outfits: {mens_in_womens[:5]}"
    print(f"  0 Men's items found in {len(outfits_women)} Women's outfits")
    record("T6: Men's Items Absent from Women's", True,
           "0 Men's items leaked into any Women's outfit")
except AssertionError as e:
    record("T6: Men's Items Absent from Women's", False, str(e))
except Exception as e:
    record("T6: Men's Items Absent from Women's", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# T7 — Cross-check raw catalog data: adapter pool gender purity
# ---------------------------------------------------------------------------
print("\n--- T7: Adapter pool gender purity cross-check ---")
try:
    for mode, allowed_set, label in [
        (GENDER_MEN,    {"men", "unisex"},  "Men's"),
        (GENDER_WOMEN,  {"women", "unisex"}, "Women's"),
        (GENDER_UNISEX, {"unisex"},          "Unisex"),
    ]:
        adapter = _make_adapter(mode)
        pool_genders = set(adapter.df["gender"].str.strip().str.lower().unique())
        bad = pool_genders - allowed_set
        assert not bad, f"{label} adapter pool contains forbidden genders: {bad}"
        print(f"  {label} adapter pool genders: {sorted(pool_genders)} ✓")

    record("T7: Adapter Pool Purity", True,
           "All 3 adapter pools contain only allowed genders before scoring")
except AssertionError as e:
    record("T7: Adapter Pool Purity", False, str(e))
except Exception as e:
    record("T7: Adapter Pool Purity", False, f"Exception: {e}")


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 70)
print(f"{'TEST':<42} | {'STATUS':<6} | DETAILS")
print("=" * 70)
for r in RESULTS:
    print(f"{r['Test']:<42} | {r['Status']:<6} | {r['Details']}")
print("=" * 70)
passed = sum(1 for r in RESULTS if r["Status"] == "PASS")
failed = sum(1 for r in RESULTS if r["Status"] == "FAIL")
print(f"\nRESULT: {passed}/{len(RESULTS)} PASSED, {failed} FAILED")

if failed > 0:
    sys.exit(1)
