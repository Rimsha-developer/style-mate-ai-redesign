"""
Extract HD images for the 22 catalog products found in benitomartin dataset.
"""
import duckdb
from pathlib import Path
import PIL.Image
import io
import pandas as pd

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
OUT_DIR = ROOT / "catalog" / "images_hd"
OUT_DIR.mkdir(parents=True, exist_ok=True)

missing_ids = [13303, 13672, 16800, 18173, 26163, 26260, 27183, 33304, 33309, 34041, 40922, 40990, 41010, 41972, 43586, 4901, 4920, 50194, 52131, 54225, 9611, 9667]

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")

urls = [f"https://huggingface.co/datasets/benitomartin/fashion-product-images-small-900x1200/resolve/main/data/train-{i:05d}-of-00014.parquet" for i in range(14)]
con.execute("CREATE TABLE missing (id BIGINT)")
values = ", ".join([f"({x})" for x in missing_ids])
con.execute(f"INSERT INTO missing VALUES {values}")

print(f"Extracting 22 images from benitomartin dataset...")
res = con.execute(f"""
    SELECT p.id, p.productDisplayName, p.articleType, p.baseColour, p.gender, p.usage, p.image.bytes
    FROM read_parquet({urls}) p
    JOIN missing m ON p.id = m.id
""").fetchall()

print(f"Retrieved {len(res)} items from parquet!")
saved_meta = []
for row in res:
    pid = str(row[0])
    name = row[1]
    atype = row[2]
    color = row[3]
    gender = row[4]
    usage = row[5]
    img_bytes = row[6]
    
    out_path = OUT_DIR / f"{pid}.jpg"
    im = PIL.Image.open(io.BytesIO(img_bytes))
    w, h = im.size
    im.convert("RGB").save(out_path, "JPEG", quality=95)
    print(f"  Saved {pid}.jpg - {name} ({w}x{h} px)")
    saved_meta.append({
        "id": pid,
        "productDisplayName": name,
        "articleType": atype,
        "baseColour": color,
        "gender": gender,
        "usage": usage,
        "w": w,
        "h": h
    })

pd.DataFrame(saved_meta).to_csv(ROOT / "catalog" / "benitomartin_22_saved.csv", index=False)
print("Done extracting all 22 HD images!")
