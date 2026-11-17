"""
Fetch the remaining 21 HD images from benitomartin dataset sequentially.
"""
import duckdb
from pathlib import Path
import PIL.Image
import io

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
OUT_DIR = ROOT / "catalog" / "images_hd"
OUT_DIR.mkdir(parents=True, exist_ok=True)

file_map = [
    ("train-00000-of-00014.parquet", [40922, 26163, 9667]),
    ("train-00001-of-00014.parquet", [4920]),
    ("train-00002-of-00014.parquet", [52131, 33304, 13303]),
    ("train-00003-of-00014.parquet", [16800, 27183]),
    ("train-00005-of-00014.parquet", [34041, 50194, 40990]),
    ("train-00006-of-00014.parquet", [9611]),
    ("train-00007-of-00014.parquet", [13672]),
    ("train-00010-of-00014.parquet", [18173, 33309, 26260, 41972]),
    ("train-00012-of-00014.parquet", [4901]),
    ("train-00013-of-00014.parquet", [43586, 41010])
]

base_url = "https://huggingface.co/datasets/benitomartin/fashion-product-images-small-900x1200/resolve/main/data/"

con = duckdb.connect()
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute("SET http_timeout=120;")

total_saved = 0
for fname, pids in file_map:
    # Filter to only those not yet saved
    pending = [p for p in pids if not (OUT_DIR / f"{p}.jpg").exists() or (OUT_DIR / f"{p}.jpg").stat().st_size < 2000]
    if not pending:
        continue
    url = base_url + fname
    id_list = ", ".join(map(str, pending))
    print(f"[{fname}] Fetching {len(pending)} items: {id_list}")
    try:
        rows = con.execute(f"""
            SELECT id, productDisplayName, image.bytes
            FROM read_parquet('{url}')
            WHERE id IN ({id_list})
        """).fetchall()
        for r in rows:
            pid = str(r[0])
            name = r[1]
            img_bytes = r[2]
            im = PIL.Image.open(io.BytesIO(img_bytes))
            w, h = im.size
            out_file = OUT_DIR / f"{pid}.jpg"
            im.convert("RGB").save(out_file, "JPEG", quality=95)
            print(f"  ✓ Saved {pid}.jpg: {name} ({w}x{h} px)")
            total_saved += 1
    except Exception as e:
        print(f"  ✗ Error on {fname}: {e}")

print(f"\nFinished! Newly saved: {total_saved} items.")
