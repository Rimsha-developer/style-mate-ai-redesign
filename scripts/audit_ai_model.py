"""
Comprehensive Audit & Evaluation of MobileNetV2 + KNN Fashion Classifier
Tests representative samples across all 18 trained classes.
Reports exact top-1 accuracy, top-3 hit rate, average confidence, confusion patterns, and slot accuracy.
"""
import sys
from pathlib import Path

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
sys.path.insert(0, str(ROOT))

import json
import pandas as pd
import numpy as np
from PIL import Image
from engine import Classifier
CAT_CSV = ROOT / "catalog" / "catalog.csv"
IMG_DIR = ROOT / "catalog" / "images_hd"

def run_audit():
    print("Initializing StyleMate Classifier (MobileNetV2 + KNN Ensemble)...")
    clf = Classifier(model_dir=str(ROOT / "models"))
    print(f"Loaded classifier. Types: {len(clf.types)}, Decision rule: {clf.L.get('decision')}")

    df = pd.read_csv(CAT_CSV)
    print(f"Total catalog records: {len(df)}")
    
    # Select up to 10 samples per articleType that have HD images
    samples = []
    for atype, group in df.groupby("articleType"):
        valid = [pid for pid in group["id"] if (IMG_DIR / f"{pid}.jpg").exists()]
        selected = valid[:10]
        for pid in selected:
            samples.append({"id": pid, "true_type": atype})

    sample_df = pd.DataFrame(samples)
    print(f"Selected {len(sample_df)} representative test samples across {sample_df['true_type'].nunique()} classes.")

    results = []
    for _, row in sample_df.iterrows():
        pid = row["id"]
        true_type = row["true_type"]
        img_path = IMG_DIR / f"{pid}.jpg"
        
        im = Image.open(img_path).convert("RGB")
        rgb = np.asarray(im)
        pred = clf.predict(rgb)
        
        pred_type = pred["type"]
        pred_slot = pred["slot"]
        conf = pred["conf"]
        top3 = [t for t, _ in pred["top3"]]
        
        true_slot = clf.slots.get(true_type, "unknown")
        
        is_top1 = (pred_type.lower() == true_type.lower())
        is_top3 = (true_type.lower() in [t.lower() for t in top3])
        is_slot_correct = (pred_slot == true_slot)
        
        results.append({
            "id": pid,
            "true_type": true_type,
            "pred_type": pred_type,
            "true_slot": true_slot,
            "pred_slot": pred_slot,
            "conf": conf,
            "is_top1": is_top1,
            "is_top3": is_top3,
            "is_slot_correct": is_slot_correct,
            "top3": top3
        })

    res_df = pd.DataFrame(results)
    
    top1_acc = res_df["is_top1"].mean() * 100
    top3_acc = res_df["is_top3"].mean() * 100
    slot_acc = res_df["is_slot_correct"].mean() * 100
    avg_conf = res_df["conf"].mean()

    print("\n" + "="*60)
    print("--- MODEL AUDIT RESULTS SUMMARY ---")
    print("="*60)
    print(f"Total Test Samples Evaluated: {len(res_df)}")
    print(f"Overall Top-1 Classification Accuracy: {top1_acc:.2f}%")
    print(f"Overall Top-3 Classification Accuracy: {top3_acc:.2f}%")
    print(f"Overall Slot Assignment Accuracy:      {slot_acc:.2f}%")
    print(f"Average Top-1 Prediction Confidence:   {avg_conf:.3f}")
    
    print("\nPer-Class Top-1 Accuracy & Confusions:")
    print("-" * 60)
    per_class = []
    for ttype, grp in res_df.groupby("true_type"):
        acc = grp["is_top1"].mean() * 100
        slot_ok = grp["is_slot_correct"].mean() * 100
        c_mean = grp["conf"].mean()
        # Find most common confusion if any
        wrong = grp[~grp["is_top1"]]
        confused_with = wrong["pred_type"].value_counts().to_dict() if len(wrong) > 0 else "None"
        per_class.append({
            "Class": ttype,
            "Samples": len(grp),
            "Top-1 Acc": f"{acc:.1f}%",
            "Slot Acc": f"{slot_ok:.1f}%",
            "Avg Conf": f"{c_mean:.2f}",
            "Confused With": str(confused_with)
        })
        print(f"  {ttype:15s} | Acc: {acc:5.1f}% | Slot: {slot_ok:5.1f}% | Conf: {c_mean:.2f} | Confused: {confused_with}")

    out_csv = ROOT / "catalog" / "ai_model_audit_report.csv"
    res_df.to_csv(out_csv, index=False)
    print(f"\nDetailed per-sample audit report saved to {out_csv}")

if __name__ == "__main__":
    run_audit()
