"""Convert AppleScabFDs to a COCO-style JSON.

This converter creates COCO-formatted annotation files for splits defined in
``sets/*.txt`` (``all``, ``train``, ``val``, or ``test``).

Since AppleScabFDs is an image-level classification dataset, we represent the
label using a single image-covering bounding box per image. This keeps the
schema interoperable with COCO tooling and mirrors the structure used by
``AppleBBCH81`` in this repository.

Examples (CLI aligned with AppleBBCH81):
  python scripts/convert_to_coco.py --out annotations
  python scripts/convert_to_coco.py --out annotations --splits train val test --split-dir sets

Backward-compatible usage:
  python scripts/convert_to_coco.py --split all
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from PIL import Image


CLASS_TO_ID: Dict[str, int] = {"Healthy": 1, "Scab": 2}


@dataclass(frozen=True)
class CocoCategory:
    """COCO category representation."""

    id: int
    name: str
    supercategory: str


@dataclass(frozen=True)
class CocoImage:
    """COCO image representation."""

    id: int
    file_name: str
    width: int
    height: int


@dataclass(frozen=True)
class CocoAnnotation:
    """COCO annotation representation."""

    id: int
    image_id: int
    category_id: int
    bbox: Tuple[float, float, float, float]
    area: float
    iscrowd: int


def read_split_list(root: Path, split: str) -> List[Path]:
    """Read a split list and return relative image paths.

    Args:
        root: Dataset root path.
        split: One of ``all``, ``train``, ``val``, ``test``.

    Returns:
        List of relative paths to images.
    """

    list_path: Path = root / "sets" / f"{split}.txt"
    if not list_path.exists():
        raise FileNotFoundError(f"Split list not found: {list_path}")
    lines: List[str] = [ln.strip() for ln in list_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [Path(ln) for ln in lines]


def build_coco(root: Path, rel_paths: Iterable[Path], year: int, version: str) -> Dict[str, object]:
    """Construct a COCO dataset dictionary.

    Args:
        root: Dataset root path.
        rel_paths: Iterable of relative image paths (e.g., ``Healthy/xxx.jpg``).
        year: Year for the ``info`` block.
        version: Version string for the ``info`` block.

    Returns:
        COCO dictionary ready to be serialized.
    """

    images: List[CocoImage] = []
    annotations: List[CocoAnnotation] = []
    categories: List[CocoCategory] = [
        CocoCategory(id=CLASS_TO_ID["Healthy"], name="healthy", supercategory="applescabfds"),
        CocoCategory(id=CLASS_TO_ID["Scab"], name="scab", supercategory="applescabfds"),
    ]

    next_img_id: int = 1
    next_ann_id: int = 1

    for rel in rel_paths:
        abs_path: Path = root / rel
        if not abs_path.exists():
            # Skip missing entries gracefully
            continue
        with Image.open(abs_path) as im:
            width, height = im.size

        # Determine class from top-level folder name
        top_folder: str = rel.parts[0]
        if top_folder not in CLASS_TO_ID:
            # Ignore files not under Healthy/ or Scab/
            continue
        category_id: int = CLASS_TO_ID[top_folder]

        images.append(
            CocoImage(id=next_img_id, file_name=str(rel).replace("\\", "/"), width=width, height=height)
        )

        # Single full-image box to carry the class label
        bbox = (0.0, 0.0, float(width), float(height))
        area = float(width * height)
        annotations.append(
            CocoAnnotation(
                id=next_ann_id,
                image_id=next_img_id,
                category_id=category_id,
                bbox=bbox,
                area=area,
                iscrowd=0,
            )
        )

        next_img_id += 1
        next_ann_id += 1

    coco_dict: Dict[str, object] = {
        "info": {
            "year": year,
            "version": version,
            "description": "AppleScabFDs (classification via full-image boxes)",
            "url": "https://www.kaggle.com/datasets/projectlzp201910094/applescabfds",
        },
        "images": [img.__dict__ for img in images],
        "categories": [cat.__dict__ for cat in categories],
        "annotations": [
            {
                "id": ann.id,
                "image_id": ann.image_id,
                "category_id": ann.category_id,
                "bbox": list(ann.bbox),
                "area": ann.area,
                "iscrowd": ann.iscrowd,
            }
            for ann in annotations
        ],
    }
    return coco_dict


def save_coco(coco: Dict[str, object], out_path: Path) -> None:
    """Serialize and save COCO JSON to a file.

    Args:
        coco: COCO dictionary.
        out_path: Destination JSON path.
    """

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(coco, f, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Supports both the AppleBBCH81-style CLI and legacy flags.
    """

    parser = argparse.ArgumentParser(description="Convert AppleScabFDs to COCO JSON")
    # Common options
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Dataset root folder")
    parser.add_argument("--year", type=int, default=2024, help="Year in COCO info block")
    parser.add_argument("--version", type=str, default="1.0.0", help="Version in COCO info block")

    # AppleBBCH81-style options (accepted for parity; images/labels are unused here)
    parser.add_argument("--images", type=Path, default=None, help="[Ignored] Images directory (not used for AppleScabFDs)")
    parser.add_argument("--labels", type=Path, default=None, help="[Ignored] Labels directory (not used for AppleScabFDs)")
    parser.add_argument("--out", type=Path, default=None, help="Output directory to save COCO JSON(s); defaults to <root>/annotations")
    parser.add_argument("--splits", nargs="*", default=None, help="Optional list of splits to export (e.g., train val test). If omitted, exports a single 'all' JSON.")
    parser.add_argument("--split-dir", type=Path, default=None, help="Directory containing split files like train.txt, val.txt, test.txt. Defaults to <root>/sets")

    # Legacy option for single split
    parser.add_argument("--split", type=str, default=None, choices=["all", "train", "val", "test"], help="Which single split to export (legacy; use --splits instead)")

    return parser.parse_args()


def main() -> None:
    """Entry point for conversion to COCO JSON."""

    args = parse_args()
    root: Path = args.root
    out_dir: Path = args.out if args.out is not None else (root / "annotations")
    split_dir: Path = args.split_dir if args.split_dir is not None else (root / "sets")

    # Determine requested splits
    requested_splits: List[str]
    if args.splits is not None and len(args.splits) > 0:
        requested_splits = [str(s).strip() for s in args.splits]
    else:
        # Fall back to legacy --split or default to 'all'
        single_split: str = args.split if args.split is not None else "all"
        requested_splits = [single_split]

    for split in requested_splits:
        # Load paths from split list
        list_path: Path = split_dir / f"{split}.txt"
        if not list_path.exists():
            raise FileNotFoundError(f"Split list not found: {list_path}")
        rel_paths: List[Path] = [Path(ln.strip()) for ln in list_path.read_text(encoding="utf-8").splitlines() if ln.strip()]

        coco = build_coco(root, rel_paths, year=args.year, version=args.version)
        out_name: str = f"applescabfds_instances_{split}.json"
        save_coco(coco, out_dir / out_name)
        print(f"Wrote {out_dir.name}/{out_name} ({len(coco['images'])} images)")


if __name__ == "__main__":
    main()


