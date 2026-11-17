"""
Download genuine HD images for catalog products from Myntra CDN.
"""
import asyncio
import aiohttp
import pandas as pd
from pathlib import Path
import PIL.Image
import io

ROOT = Path("/Users/aen./Downloads/Friend_file/stylemate_redesign")
LINKS_CSV = ROOT / "catalog" / "hd_links_matched.csv"
OUT_DIR = ROOT / "catalog" / "images_hd"
REPORT_CSV = ROOT / "catalog" / "hd_download_report.csv"

OUT_DIR.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "image/webp,image/apng,image/*,*/*;q=0.8"
}

async def fetch_one(session, row, semaphore, results):
    pid = str(row["id"])
    url = str(row["link"])
    out_path = OUT_DIR / f"{pid}.jpg"

    if out_path.exists() and out_path.stat().st_size > 2000:
        try:
            with PIL.Image.open(out_path) as im:
                w, h = im.size
                results.append({"id": pid, "status": "cached", "w": w, "h": h, "bytes": out_path.stat().st_size})
                return
        except Exception:
            pass

    async with semaphore:
        for attempt in range(3):
            try:
                async with session.get(url, headers=HEADERS, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) > 1000:
                            # Verify valid image
                            im = PIL.Image.open(io.BytesIO(content))
                            w, h = im.size
                            # Save RGB JPEG
                            im.convert("RGB").save(out_path, "JPEG", quality=95)
                            results.append({"id": pid, "status": "downloaded", "w": w, "h": h, "bytes": len(content)})
                            return
                        else:
                            results.append({"id": pid, "status": f"small_content_{len(content)}", "w": 0, "h": 0, "bytes": len(content)})
                            return
                    else:
                        if attempt == 2:
                            results.append({"id": pid, "status": f"http_{resp.status}", "w": 0, "h": 0, "bytes": 0})
            except Exception as e:
                if attempt == 2:
                    results.append({"id": pid, "status": f"error_{type(e).__name__}", "w": 0, "h": 0, "bytes": 0})
                await asyncio.sleep(0.5)

async def main():
    df = pd.read_csv(LINKS_CSV)
    print(f"Total links to download: {len(df)}")
    semaphore = asyncio.Semaphore(20) # 20 concurrent downloads
    results = []

    connector = aiohttp.TCPConnector(limit=30, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_one(session, row, semaphore, results) for _, row in df.iterrows()]
        
        # Track progress
        total = len(tasks)
        completed = 0
        for f in asyncio.as_completed(tasks):
            await f
            completed += 1
            if completed % 50 == 0 or completed == total:
                print(f"Progress: {completed} / {total} ({(completed/total)*100:.1f}%)")

    rep_df = pd.DataFrame(results)
    rep_df.to_csv(REPORT_CSV, index=False)
    print(f"\nDownload completed! Report saved to {REPORT_CSV}")
    print(rep_df["status"].value_counts())
    
    # Check dimensions
    valid = rep_df[rep_df["w"] >= 400]
    print(f"Valid HD images: {len(valid)} / {len(df)}")
    if len(valid) > 0:
        print(f"Average resolution: {valid['w'].mean():.0f} x {valid['h'].mean():.0f} px")

if __name__ == "__main__":
    asyncio.run(main())
