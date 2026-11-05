#!/usr/bin/env python3
"""
Downloads car damage images from HuggingFace parquet files.
Saves to data/images/ and writes data/cases.json with metadata.
Usage: python3 src/download_dataset.py [per_class=8]
"""
import sys, json, base64, io, os
from pathlib import Path
import urllib.request
import pyarrow.parquet as pq

PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 8
LABEL_NAMES = ["F_Breakage", "F_Crushed", "F_Normal", "R_Breakage", "R_Crushed", "R_Normal"]
SEVERITY    = {"F_Normal": 0, "R_Normal": 0, "F_Breakage": 2, "R_Breakage": 2, "F_Crushed": 4, "R_Crushed": 4}
PARQUET_URLS = [
    "https://huggingface.co/datasets/SaiVaibhavS/comprehensive-car-damage/resolve/refs%2Fconvert%2Fparquet/default/train/0000.parquet",
    "https://huggingface.co/datasets/SaiVaibhavS/comprehensive-car-damage/resolve/refs%2Fconvert%2Fparquet/default/train/0001.parquet",
]

ROOT = Path(__file__).parent.parent
IMAGES_DIR = ROOT / "data" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

print(f"Downloading parquet files...")
tables = []
for url in PARQUET_URLS:
    tmp = f"/tmp/car_damage_{PARQUET_URLS.index(url)}.parquet"
    if not os.path.exists(tmp):
        print(f"  {url.split('/')[-1]}")
        urllib.request.urlretrieve(url, tmp)
    tables.append(pq.read_table(tmp))

import pyarrow as pa
table = pa.concat_tables(tables)
print(f"Loaded {len(table)} rows")

# Collect PER_CLASS per label
buckets = {i: [] for i in range(6)}
for i in range(len(table)):
    label_idx = table["label"][i].as_py()
    if len(buckets[label_idx]) < PER_CLASS:
        img_bytes = table["image"][i].as_py()["bytes"]
        buckets[label_idx].append((i, img_bytes))
    if all(len(v) >= PER_CLASS for v in buckets.values()):
        break

cases = []
total = sum(len(v) for v in buckets.values())
done = 0

for label_idx, items in buckets.items():
    label = LABEL_NAMES[label_idx]
    for row_idx, img_bytes in items:
        filename = f"{len(cases)}_{label}.jpg"
        abs_path = IMAGES_DIR / filename
        abs_path.write_bytes(img_bytes)

        cases.append({
            "imgSrc": f"/images/{filename}",
            "label": label,
            "zone": "frontal" if label_idx < 3 else "trasera",
            "isDamaged": label not in ("F_Normal", "R_Normal"),
            "severityGT": SEVERITY[label],
        })
        done += 1
        print(f"\r  {done}/{total}", end="", flush=True)

print(f"\nSaved {len(cases)} images to data/images/")
out = ROOT / "data" / "cases.json"
out.write_text(json.dumps(cases, indent=2))
print(f"Metadata → data/cases.json")
