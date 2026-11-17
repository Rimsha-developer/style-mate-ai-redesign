import json, uuid, colorsys, os
from pathlib import Path
import numpy as np, pandas as pd
from PIL import Image
from sklearn.cluster import KMeans

SLOT_TITLE = {"top": "Tops", "bottom": "Bottoms", "dress": "Dresses", "outer": "Outerwear", "shoes": "Shoes", "bag": "Bags"}
NEEDS = {"top": ["bottom", "shoes", "bag", "outer"], "bottom": ["top", "shoes", "bag", "outer"], "dress": ["shoes", "bag", "outer"],
         "outer": ["top", "bottom", "shoes"], "shoes": ["top", "bottom", "dress", "bag"], "bag": ["top", "bottom", "dress", "shoes"]}


# ---------------- Model ----------------
class Classifier:
    """Loads the exported multi-task model (type + colour + occasion) + KNN. Input = RGB float 0..255 (scaling is inside the model)."""
    def __init__(self, model_dir="models"):
        import tensorflow as tf, joblib
        d = Path(model_dir); self.L = json.load(open(d / "labels.json"))
        self.types, self.usages, self.slots = self.L["types"], self.L["usages"], self.L["slots"]

        # Ensure compatibility with Keras configs containing quantization_config
        _orig_dense_init = tf.keras.layers.Dense.__init__
        def _compat_dense(self, *args, **kwargs):
            kwargs.pop("quantization_config", None)
            return _orig_dense_init(self, *args, **kwargs)
        tf.keras.layers.Dense.__init__ = _compat_dense

        m = tf.keras.models.load_model(d / "stylemate_model.keras", compile=False)
        self.net = tf.keras.Model(m.input, [m.get_layer(self.L["feature_layer"]).output, *m.outputs])
        self.knn = self.scaler = None
        if self.L.get("decision") != "model":
            try: self.knn, self.scaler = joblib.load(d / "knn.pkl"), joblib.load(d / "scaler.pkl")
            except Exception as e: print("KNN not loaded, using the CNN only:", e)
        self.pose = None
        task = d / "pose_landmarker_full.task"
        if task.exists():
            from mediapipe_pipeline import FashionPosePipeline
            self.pose = FashionPosePipeline(str(task))

    @staticmethod
    def _prep(rgb): return np.asarray(Image.fromarray(rgb).convert("RGB").resize((224, 224)), dtype="float32")

    def _run(self, X):
        f, pt, pc, pu = [v.numpy() for v in self.net(X, training=False)]
        p = pt
        if self.knn is not None:
            pk = self.knn.predict_proba(self.scaler.transform(f))
            p = pk if self.L["decision"] == "knn" else (pt + pk) / 2
        return p, pu

    def _pack(self, p, pu):
        top = p.argsort()[::-1][:3]; t = self.types[top[0]]
        return {"type": t, "slot": self.slots[t], "conf": float(p[top[0]]), "top3": [(self.types[i], float(p[i])) for i in top],
                "usage": self.usages[int(pu.argmax())], "usage_conf": float(pu.max())}

    def predict(self, rgb):
        p, pu = self._run(self._prep(rgb)[None]); return self._pack(p[0], pu[0])

    def predict_paths(self, paths, progress=None, bs=16):
        out = []
        for k in range(0, len(paths), bs):
            X = np.stack([self._prep(np.asarray(Image.open(p).convert("RGB"))) for p in paths[k:k + bs]])
            p, pu = self._run(X); out += [self._pack(a, b) for a, b in zip(p, pu)]
            if progress: progress(min(1.0, (k + bs) / len(paths)))
        return out

    def body_crops(self, rgb):
        if self.pose is None: return None
        from garment_cropping import crop_garments
        lm = self.pose.detect(rgb)
        if lm is None: return None
        try: return crop_garments(rgb, lm)
        except ValueError: return None


# ---------------- Colour ----------------
def dominant_rgb(rgb):
    im = Image.fromarray(rgb).convert("RGB").resize((100, 100))
    core = np.asarray(im)[20:80, 20:80].reshape(-1, 3)
    keep = core[~(core.min(axis=1) > 235)]                      # drop white studio background
    px = keep if len(keep) > 0.15 * len(core) else core
    km = KMeans(3, n_init=3, random_state=0).fit(px)
    return [int(v) for v in km.cluster_centers_[np.bincount(km.labels_).argmax()]]


def fast_color(path):
    a = np.asarray(Image.open(path).convert("RGB").resize((48, 48)))[10:38, 10:38].reshape(-1, 3)
    keep = a[~(a.min(axis=1) > 235)]
    return [int(v) for v in np.median(keep if len(keep) > 0.15 * len(a) else a, axis=0)]


def color_info(rgb):
    h, s, v = colorsys.rgb_to_hsv(*(c / 255 for c in rgb))
    if v < 0.2: name = "black"
    elif s < 0.12: name = "white" if v > 0.85 else "gray"
    elif 0.05 < h < 0.15 and s < 0.35 and v > 0.6: name = "beige"
    elif 0.55 < h < 0.7 and v < 0.4: name = "navy"
    elif 0.5 < h < 0.68 and s < 0.5: name = "denim"
    else:
        name = next(n for lim, n in [(.04, "red"), (.11, "orange"), (.18, "yellow"), (.45, "green"), (.52, "teal"),
                                     (.7, "blue"), (.85, "purple"), (.95, "pink"), (1.01, "red")] if h < lim)
    return {"color": name, "neutral": name in {"black", "white", "gray", "beige", "navy", "denim"}, "hue": h, "rgb": list(rgb)}


def harmony(a, b):
    if a["neutral"] or b["neutral"]: return 70 if a["color"] == b["color"] else 85
    d = abs(a["hue"] - b["hue"]); d = min(d, 1 - d)
    if d < 0.04: return 80
    if d < 0.12: return 75
    if d > 0.4: return 85
    if 0.28 < d < 0.38: return 70
    return 40


_U = {("Casual", "Smart Casual"): 85, ("Smart Casual", "Formal"): 85, ("Casual", "Formal"): 55, ("Casual", "Sports"): 70,
      ("Sports", "Formal"): 20, ("Sports", "Party"): 30, ("Sports", "Smart Casual"): 45, ("Ethnic", "Casual"): 60,
      ("Ethnic", "Formal"): 65, ("Ethnic", "Party"): 75, ("Ethnic", "Sports"): 20, ("Ethnic", "Smart Casual"): 60,
      ("Party", "Formal"): 80, ("Party", "Casual"): 60, ("Party", "Smart Casual"): 75}


def usage_compat(a, b):
    if a == b: return 100
    if "Other" in (a, b): return 70
    return _U.get((a, b)) or _U.get((b, a)) or 60


def pair_score(a, b): return 0.55 * harmony(a, b) + 0.45 * usage_compat(a["usage"], b["usage"])


def explain(a, b):
    if a["neutral"] or b["neutral"]: c = f"{a['color']} + {b['color']}: neutral pairing"
    else:
        d = abs(a["hue"] - b["hue"]); d = min(d, 1 - d)
        c = f"{a['color']} + {b['color']}: " + ("same family" if d < .04 else "analogous" if d < .12 else "complementary" if d > .4 else "bold mix" if d > .28 else "may clash")
    u = f"both {a['usage']}" if a["usage"] == b["usage"] else f"{a['usage']} + {b['usage']}"
    return f"{c} · {u}"


# ---------------- Catalog ----------------
class Catalog:
    """Folder of product photos (+ optional catalog.csv with id, articleType, usage, gender). Built once, cached as catalog_index.csv."""
    def __init__(self, df): self.df = df

    @classmethod
    def load(cls, img_dir, clf, csv=None, progress=None):
        img_dir = Path(img_dir); cache = img_dir.parent / "catalog_index.csv"
        if cache.exists():
            d = pd.read_csv(cache); d = d[d.path.map(os.path.exists)]
            if len(d): return cls(d.reset_index(drop=True))
        files = sorted(p for p in img_dir.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
        rows = []
        if csv and os.path.exists(csv):
            c = pd.read_csv(csv); c["file"] = c["id"].astype(str) + ".jpg" if "id" in c else c["file"]
            c = c[c.articleType.isin(clf.types)]
            known = {p.name: p for p in files}
            for r in c.itertuples():
                p = known.get(r.file)
                if p is None: continue
                u = getattr(r, "usage", "Other"); u = u if u in clf.usages else "Other"
                rows.append({"path": str(p), "type": r.articleType, "usage": u, "gender": getattr(r, "gender", "Unisex")})
        else:
            low = {t.lower(): t for t in clf.types}
            pred = clf.predict_paths([str(p) for p in files], progress)
            for p, pr in zip(files, pred):
                t = low.get(p.parent.name.lower(), pr["type"])               # subfolder name wins over the model
                rows.append({"path": str(p), "type": t, "usage": pr["usage"], "gender": "Unisex"})
        d = pd.DataFrame(rows); d["slot"] = d.type.map(clf.slots)
        col = [color_info(fast_color(p)) for p in d.path]
        d["color"], d["neutral"], d["hue"] = [c["color"] for c in col], [c["neutral"] for c in col], [c["hue"] for c in col]
        d.to_csv(cache, index=False); return cls(d)


def recommend(cat, item, per_slot=4, occasion="Any", gender="Any", seed=0):
    """item: dict(slot, usage, color, neutral, hue). Returns {slot: DataFrame(top matches)}."""
    pool = cat.df
    if gender != "Any": pool = pool[pool.gender.isin([gender, "Unisex"])]
    if occasion != "Any": pool = pool[pool.usage.map(lambda u: usage_compat(occasion, u)) >= 70]
    rng = np.random.default_rng(seed); out = {}
    for s in NEEDS.get(item["slot"], []):
        sub = pool[pool.slot == s]
        if sub.empty: continue
        sc = np.array([pair_score(item, r) for r in sub.to_dict("records")]) + rng.uniform(0, 6, len(sub))
        top = sub.assign(score=sc).nlargest(per_slot, "score")
        top["why"] = [explain(item, r) for r in top.to_dict("records")]; out[s] = top
    return out


# ---------------- Wardrobe ----------------
class Wardrobe:
    def __init__(self, root="wardrobe"):
        self.root = Path(root); self.root.mkdir(exist_ok=True); self.db = self.root / "wardrobe.json"
        self.items = json.loads(self.db.read_text()) if self.db.exists() else []

    def _save(self): self.db.write_text(json.dumps(self.items, indent=1))

    def add(self, rgb, type_, slot, usage, conf=None):
        iid = uuid.uuid4().hex[:8]; path = self.root / f"{iid}.jpg"
        Image.fromarray(rgb).convert("RGB").save(path, quality=90)
        it = {"id": iid, "path": str(path), "type": type_, "slot": slot, "usage": usage, "conf": conf, "worn": 0, **color_info(dominant_rgb(rgb))}
        self.items.append(it); self._save(); return it

    def remove(self, iid):
        for it in self.items:
            if it["id"] == iid and os.path.exists(it["path"]): os.remove(it["path"])
        self.items = [i for i in self.items if i["id"] != iid]; self._save()

    def wear(self, ids):
        for it in self.items:
            if it["id"] in ids: it["worn"] += 1
        self._save()

    def by_slot(self, s): return [i for i in self.items if i["slot"] == s]


def suggest(wd, occasion="Any", n=6):
    bases = [(t, b) for t in wd.by_slot("top") for b in wd.by_slot("bottom")] + [(d,) for d in wd.by_slot("dress")]
    out = []
    for base in bases:
        pieces = list(base)
        for s in ("outer", "shoes", "bag"):                      # add the best-matching extra from each slot, if it fits
            best = max(wd.by_slot(s), key=lambda c: np.mean([pair_score(c, p) for p in pieces]), default=None)
            if best and np.mean([pair_score(best, p) for p in pieces]) >= 65: pieces.append(best)
        pairs = [pair_score(a, b) for i, a in enumerate(pieces) for b in pieces[i + 1:]] or [75]
        score = np.mean(pairs)
        if occasion != "Any": score += 0.15 * np.mean([usage_compat(occasion, p["usage"]) for p in pieces]) - 10
        score -= 2 * min(np.mean([p["worn"] for p in pieces]), 5)  # rotate what you wear
        out.append((round(max(0, min(100, score))), pieces))
    return sorted(out, key=lambda x: -x[0])[:n]
