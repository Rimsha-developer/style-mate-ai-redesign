"""Phase 2 Prediction Verification Test Script
Uses in-memory Dense.from_config adapter, imports original engine.py untouched,
verifies KNN + Scaler loading, and runs exact predictions on 3 catalog images.
"""
import os
import json
import numpy as np
from PIL import Image
import keras
import tensorflow as tf

# 1. In-memory Keras adapter (strips quantization_config=None only)
_orig_dense_from_config = keras.layers.Dense.from_config

def _safe_dense_from_config(config):
    if "quantization_config" in config and config["quantization_config"] is None:
        config.pop("quantization_config")
    return _orig_dense_from_config(config)

keras.layers.Dense.from_config = _safe_dense_from_config

# 2. Import original engine without modifying engine.py
import engine

print("=" * 60)
print("PHASE 2: PREDICTION VERIFICATION TEST")
print("=" * 60)

# 3. Instantiate original Classifier
clf = engine.Classifier("models")

print("\n--- Model & Component Verification ---")
print(f"Classifier initialized: OK")
print(f"Total garment classes: {len(clf.types)}")
print(f"Total occasion classes: {len(clf.usages)}")
print(f"KNN model loaded: {clf.knn is not None} (type: {type(clf.knn).__name__})")
print(f"Scaler loaded: {clf.scaler is not None} (type: {type(clf.scaler).__name__})")
if clf.knn is not None:
    print(f"KNN prototypes count: {clf.knn.n_samples_fit_}")
    print(f"KNN neighbors (k): {clf.knn.n_neighbors}")
print(f"Pose Landmarker pipeline loaded: {clf.pose is not None}")

# 4. Define 3 sample images from catalog
test_samples = [
    {
        "id": "6874",
        "path": "catalog/images/6874.jpg",
        "expected_type": "Dresses",
        "expected_usage": "Casual"
    },
    {
        "id": "14117",
        "path": "catalog/images/14117.jpg",
        "expected_type": "Jeans",
        "expected_usage": "Casual"
    },
    {
        "id": "15259",
        "path": "catalog/images/15259.jpg",
        "expected_type": "Casual Shoes",
        "expected_usage": "Casual"
    }
]

print("\n--- Running Predictions on 3 Catalog Samples ---")
results = []

for sample in test_samples:
    img_path = sample["path"]
    assert os.path.exists(img_path), f"Image not found: {img_path}"
    
    # Load RGB image exactly as in original app.py
    pil_img = Image.open(img_path).convert("RGB")
    rgb = np.asarray(pil_img)
    
    # Exact original prediction call
    pred = clf.predict(rgb)
    
    # Exact original color extraction
    dom_rgb = engine.dominant_rgb(rgb)
    col_info = engine.color_info(dom_rgb)
    
    res = {
        "id": sample["id"],
        "path": img_path,
        "predicted_type": pred["type"],
        "type_conf": pred["conf"],
        "top3": pred["top3"],
        "predicted_slot": pred["slot"],
        "predicted_usage": pred["usage"],
        "usage_conf": pred["usage_conf"],
        "detected_color": col_info["color"],
        "color_rgb": col_info["rgb"],
        "is_neutral": col_info["neutral"]
    }
    results.append(res)
    
    print(f"\n[Sample {sample['id']}] Expected: {sample['expected_type']} | {sample['expected_usage']}")
    print(f"  → Predicted Garment: {pred['type']} (Confidence: {pred['conf'] * 100:.2f}%) [Slot: {pred['slot']}]")
    print(f"  → Top-3 Distribution: {', '.join([f'{t}: {c*100:.1f}%' for t, c in pred['top3']])}")
    print(f"  → Predicted Occasion: {pred['usage']} (Confidence: {pred['usage_conf'] * 100:.2f}%)")
    print(f"  → Detected Color: {col_info['color']} (RGB: {col_info['rgb']}, Neutral: {col_info['neutral']})")

print("\n" + "=" * 60)
print("TEST SUMMARY: ALL 3 PREDICTIONS COMPLETED")
print("=" * 60)
