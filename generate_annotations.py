import os
import json
import random
import time
from PIL import Image

def generate_id():
    rand_part = random.randint(10**6, 10**7-1)  # 7位
    ts_part = int(str(int(time.time()*1000))[-3:])  # 毫秒后三位
    return int(f"{rand_part}{ts_part}")

category_map = {
    "Healthy": {"id": 1000000000, "name": "healthy"},
    "Scab": {"id": 1000000001, "name": "scab"}
}

for category in ["Healthy", "Scab"]:
    folder = category
    if not os.path.exists(folder):
        continue
    for fname in os.listdir(folder):
        if not fname.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        img_path = os.path.join(folder, fname)
        try:
            with Image.open(img_path) as img:
                width, height = img.size
                fmt = img.format
        except Exception:
            width, height, fmt = 0, 0, "JPG"
        size = os.path.getsize(img_path)
        image_id = generate_id()
        json_data = {
            "info": {
                "description": "data",
                "version": "1.0",
                "year": 2025,
                "contributor": "search engine",
                "source": "no_augmentation",
                "license": {
                    "name": "Creative Commons Attribution 4.0 International",
                    "url": "https://creativecommons.org/licenses/by/4.0/"
                }
            },
            "images": [
                {
                    "id": image_id,
                    "width": width,
                    "height": height,
                    "file_name": fname,
                    "size": size,
                    "format": fmt,
                    "url": "",
                    "hash": "",
                    "status": "success"
                }
            ],
            "annotations": [],
            "categories": [
                {
                    "id": category_map[category]["id"],
                    "name": category_map[category]["name"],
                    "supercategory": "applescabfds"
                }
            ]
        }
        json_path = os.path.join(folder, os.path.splitext(fname)[0] + ".json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        print(f"Generated {json_path}") 