#!/usr/bin/env python3
"""
Convert AppleScabFDs dataset annotations to COCO JSON format.
Supports multi-class classification (healthy=1, scab=2).
New structure: apples/healthy/ and apples/scab/ subdirectories.
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image

def read_split_list(split_file: Path) -> List[str]:
    """Read image base names (without extension) from a split file."""
    if not split_file.exists():
        return []
    lines = [line.strip() for line in split_file.read_text(encoding="utf-8").splitlines()]
    return [line for line in lines if line]

def image_size(image_path: Path) -> Tuple[int, int]:
    """Return (width, height) for an image path using PIL."""
    with Image.open(image_path) as img:
        return img.width, img.height

def parse_csv_boxes(csv_path: Path) -> List[Dict]:
    """Parse a single CSV file and return bounding boxes with category IDs."""
    if not csv_path.exists():
        return []
    
    boxes = []
    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                x = float(row.get('x', 0))
                y = float(row.get('y', 0))
                width = float(row.get('width', 0))
                height = float(row.get('height', 0))
                label = int(row.get('label', 1))
                
                if width > 0 and height > 0:
                    boxes.append({
                        'bbox': [x, y, width, height],
                        'area': width * height,
                        'category_id': label
                    })
            except (ValueError, KeyError):
                continue
    
    return boxes

def collect_annotations_for_split(
    category_root: Path,
    split: str,
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Collect COCO dictionaries for images, annotations, and categories.
    Supports new structure: apples/healthy/ and apples/scab/ subdirectories.
    """
    sets_dir = category_root / "sets"
    split_file = sets_dir / f"{split}.txt"
    image_stems = set(read_split_list(split_file))
    
    if not image_stems:
        # Fall back to all images if no split file
        healthy_dir = category_root / "healthy" / "images"
        scab_dir = category_root / "scab" / "images"
        image_stems = set()
        if healthy_dir.exists():
            image_stems.update({p.stem for p in healthy_dir.glob("*.png")})
            image_stems.update({p.stem for p in healthy_dir.glob("*.jpg")})
            image_stems.update({p.stem for p in healthy_dir.glob("*.JPG")})
        if scab_dir.exists():
            image_stems.update({p.stem for p in scab_dir.glob("*.png")})
            image_stems.update({p.stem for p in scab_dir.glob("*.jpg")})
            image_stems.update({p.stem for p in scab_dir.glob("*.JPG")})
    
    images: List[Dict] = []
    anns: List[Dict] = []
    categories: List[Dict] = [
        {"id": 1, "name": "healthy", "supercategory": "apple_scab"},
        {"id": 2, "name": "scab", "supercategory": "apple_scab"}
    ]
    
    image_id_counter = 1
    ann_id_counter = 1
    
    # Check both healthy and scab subdirectories
    healthy_dir = category_root / "healthy"
    scab_dir = category_root / "scab"
    
    for stem in sorted(image_stems):
        # Try healthy directory first
        img_path = None
        subcategory = None
        csv_path = None
        
        for ext in ['.png', '.jpg', '.JPG', '.PNG']:
            test_path = healthy_dir / 'images' / f"{stem}{ext}"
            if test_path.exists():
                img_path = test_path
                subcategory = 'healthy'
                csv_path = healthy_dir / 'csv' / f"{stem}.csv"
                break
        
        # If not found in healthy, try scab
        if not img_path:
            for ext in ['.png', '.jpg', '.JPG', '.PNG']:
                test_path = scab_dir / 'images' / f"{stem}{ext}"
                if test_path.exists():
                    img_path = test_path
                    subcategory = 'scab'
                    csv_path = scab_dir / 'csv' / f"{stem}.csv"
                    break
        
        if not img_path:
            continue
        
        width, height = image_size(img_path)
        images.append({
            "id": image_id_counter,
            "file_name": f"apples/{subcategory}/images/{img_path.name}",
            "width": width,
            "height": height,
        })
        
        if csv_path and csv_path.exists():
            for box in parse_csv_boxes(csv_path):
                anns.append({
                    "id": ann_id_counter,
                    "image_id": image_id_counter,
                    "category_id": box['category_id'],
                    "bbox": box['bbox'],
                    "area": box['area'],
                    "iscrowd": 0,
                })
                ann_id_counter += 1
        
        image_id_counter += 1
    
    return images, anns, categories

def build_coco_dict(
    images: List[Dict],
    anns: List[Dict],
    categories: List[Dict],
    description: str,
) -> Dict:
    """Build a complete COCO dict from components."""
    return {
        "info": {
            "year": 2021,
            "version": "1.0.0",
            "description": description,
            "url": "https://www.kaggle.com/datasets/projectlzp201910094/applescabfds",
        },
        "images": images,
        "annotations": anns,
        "categories": categories,
        "licenses": [],
    }

def convert(
    root: Path,
    out_dir: Path,
    category: str,
    splits: List[str],
) -> None:
    """Convert selected category and splits to COCO JSON files."""
    out_dir.mkdir(parents=True, exist_ok=True)
    
    category_root = root / category
    
    for split in splits:
        images, anns, categories = collect_annotations_for_split(
            category_root, split
        )
        desc = f"AppleScabFDs {category} {split} split"
        coco = build_coco_dict(images, anns, categories, desc)
        out_path = out_dir / f"{category}_instances_{split}.json"
        out_path.write_text(json.dumps(coco, indent=2), encoding="utf-8")
        print(f"Generated: {out_path} ({len(images)} images, {len(anns)} annotations)")

def main():
    parser = argparse.ArgumentParser(description="Convert AppleScabFDs annotations to COCO JSON")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Dataset root directory",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output directory for COCO JSON files (default: <root>/annotations)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default="apples",
        help="Category name (default: apples)",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val", "test"],
        choices=["train", "val", "test"],
        help="Dataset splits to generate (default: train val test)",
    )
    
    args = parser.parse_args()
    
    if args.out is None:
        args.out = args.root / "annotations"
    
    convert(
        root=args.root,
        out_dir=args.out,
        category=args.category,
        splits=args.splits,
    )

if __name__ == "__main__":
    main()
