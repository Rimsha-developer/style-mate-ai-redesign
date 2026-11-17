"""Parity test comparing services.ai_service directly against engine.py.
Ensures zero deviation in predictions, top-3 probabilities, colors, and occasion scores.
"""
import sys
import numpy as np
from PIL import Image
from pathlib import Path

# Set up paths
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from services import ai_service
import engine

print("=" * 65)
print("PHASE 3: SERVICE ADAPTER PARITY VERIFICATION")
print("=" * 65)

# Test Image: 6874.jpg (Dress from catalog)
test_img_path = _ROOT / "catalog/images/6874.jpg"
assert test_img_path.exists(), f"Image not found at {test_img_path}"

pil_img = Image.open(test_img_path).convert("RGB")
rgb_array = np.asarray(pil_img)

# 1. Direct call to original engine
raw_clf = ai_service.get_classifier("models")
raw_pred = raw_clf.predict(rgb_array)
raw_dom_rgb = engine.dominant_rgb(rgb_array)
raw_color = engine.color_info(raw_dom_rgb)

# 2. Call through new service adapter
service_pred = ai_service.analyze_single_garment(rgb_array)

print("\n[Prediction Parity Check]")
print(f"Original Engine Type:   {raw_pred['type']} ({raw_pred['conf']*100:.4f}%)")
print(f"Service Adapter Type:   {service_pred['type']} ({service_pred['conf_pct']}%)")
assert raw_pred["type"] == service_pred["type"], "Type mismatch!"
assert abs(raw_pred["conf"] - service_pred["conf"]) < 1e-6, "Confidence mismatch!"
print(">> Type & Confidence Parity: 100% MATCH")

print("\n[Top-3 Class Parity Check]")
for i in range(len(raw_pred["top3"])):
    raw_name, raw_p = raw_pred["top3"][i]
    svc_name, svc_p, svc_pct = service_pred["top3"][i]
    print(f"  Rank {i+1}: Raw={raw_name} ({raw_p*100:.3f}%) | Svc={svc_name} ({svc_p*100:.3f}%)")
    assert raw_name == svc_name, f"Top-3 rank {i} name mismatch!"
    assert abs(raw_p - svc_p) < 1e-6, f"Top-3 rank {i} probability mismatch!"
print(">> Top-3 Distribution Parity: 100% MATCH")

print("\n[Occasion Parity Check]")
print(f"Original Occasion:      {raw_pred['usage']} ({raw_pred['usage_conf']*100:.4f}%)")
print(f"Service Adapter Occasion: {service_pred['usage']} ({service_pred['usage_conf_pct']}%)")
assert raw_pred["usage"] == service_pred["usage"], "Occasion mismatch!"
assert abs(raw_pred["usage_conf"] - service_pred["usage_conf"]) < 1e-6, "Occasion confidence mismatch!"
print(">> Occasion Parity: 100% MATCH")

print("\n[Color Extraction Parity Check]")
print(f"Original Color:         {raw_color['color']} (RGB: {raw_color['rgb']}, Neutral: {raw_color['neutral']})")
print(f"Service Adapter Color:  {service_pred['color']} (RGB: {service_pred['rgb']}, Neutral: {service_pred['neutral']})")
assert raw_color["color"] == service_pred["color"], "Color name mismatch!"
assert raw_color["rgb"] == service_pred["rgb"], "RGB mismatch!"
assert raw_color["neutral"] == service_pred["neutral"], "Neutral flag mismatch!"
print(">> Color Extraction Parity: 100% MATCH")

print("\n" + "=" * 65)
print("SUCCESS: ALL ADAPTER PARITY ASSERTIONS PASSED (100% MATCH)")
print("=" * 65)
