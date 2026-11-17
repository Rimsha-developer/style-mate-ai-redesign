"""
Extract the 22 HD images from benitomartin dataset in parallel using ThreadPoolExecutor.
"""
import duckdb
from pathlib import Path
import PIL.Image
import io
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
OUT_DIR = ROOT / "catalog" / "images_hd"
OUT_DIR.mkdir(parents=True, exist_ok=True)

file_map = {
    "train-00011-of-00014.parquet": [54225],
    "train-00002-of-00014.parquet": [52131, 33304, 13303],
    "train-00005-of-00014.parquet": [34041, 50194, 40990],
    "train-00010-of-00014.parquet": [18173, 33309, 26260, 41972],
    "train-00001-of-00014.parquet": [4920],
    "train-00006-of-00014.parquet": [9611],
    "train-00013-of-00014.parquet": [43586, 41010],
    "train-00000-of-00014.parquet": [40922, 26163, 9667],
    "train-00012-of-00014.parquet": [4901],
    "train-00003-of-00014.parquet": [16800, 27183],
    "train-00007-of-00014.parquet": [13672]
}

base_url = "https://huggingface.co/datasets/benitomartin/fashion-product-images-small-900x1200/resolve/main/data/"

def process_file(item):
    fname, pids = item
    url = base_url + fname
    id_list = ", ".join(map(str, pids))
    print(f"[{fname}] Starting extraction for {len(pids)} items: {id_list}")
    
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET http_timeout=60;")
    
    extracted = []
    try:
        rows = con.execute(f"""
            SELECT id, productDisplayName, articleType, baseColour, gender, usage, image.bytes
            FROM read_parquet('{url}')
            WHERE id IN ({id_list})
        """).fetchall()
        for r in rows:
            pid = str(r[0])
            name = r[1]
            img_bytes = r[6]
            im = PIL.Image.open(io.BytesIO(img_bytes))
            w, h = im.size
            out_file = OUT_DIR / f"{pid}.jpg"
            im.convert("RGB").save(out_file, "JPEG", quality=95)
            print(f"  ✓ Saved {pid}.jpg: {name} ({w}x{h} px)")
            extracted.append({
                "id": pid,
                "productDisplayName": name,
                "articleType": r[2],
                "baseColour": r[3],
                "gender": r[4],
                "usage": r[5],
                "w": w,
                "h": h
            })
    except Exception as e:
        print(f"  ✗ Error on {fname}: {e}")
    finally:
        con.close()
    return extracted

def main():
    all_saved = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_file, item) for item in file_map.items()]
        for f in as_completed(futures):
            res = f.result()
            all_saved.extend(res)

    pd.DataFrame(all_saved).to_csv(ROOT / "catalog" / "benitomartin_22_saved.csv", index=False)
    print(f"\nCompleted! Total 22 items saved: {len(all_saved)} / 22")

if __name__ == "__main__":
    main()
