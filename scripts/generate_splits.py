"""Utilities for generating dataset splits for AppleScabFDs.

This script scans class folders (``Healthy`` and ``Scab``) for image files
and creates text files under ``sets/`` that list relative image paths for
``train``, ``val``, ``test``, and ``all`` splits. Stratified splitting by
class is performed with user-configurable ratios.

Usage:
  python scripts/generate_splits.py --train 0.8 --val 0.1 --test 0.1 --seed 42

Notes:
- Images are kept in their original folders; paths are written as
  ``Healthy/xxx.jpg`` or ``Scab/xxx.jpg``.
- Only image files are considered. Sidecar JSON files (if any) are ignored.
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


IMAGE_EXTENSIONS: Tuple[str, ...] = (".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG")
CLASS_FOLDERS: Tuple[str, str] = ("Healthy", "Scab")


def find_class_dirs(root: Path) -> Dict[str, Path]:
    """Find class directories case-insensitively under the root.

    Args:
        root: Dataset root path.

    Returns:
        Mapping from canonical class name (``Healthy``/``Scab``) to actual Path.
    """

    mapping: Dict[str, Path] = {}
    if not root.exists():
        return mapping
    lowercase_to_actual: Dict[str, Path] = {
        p.name.lower(): p for p in root.iterdir() if p.is_dir()
    }
    for canonical in CLASS_FOLDERS:
        actual: Optional[Path] = lowercase_to_actual.get(canonical.lower())
        if actual is not None:
            mapping[canonical] = actual
    return mapping


def find_images(root: Path, class_dir: Path) -> List[Path]:
    """Collect all image paths for a given class, recursively.

    Args:
        root: Dataset root path (folder containing class subfolders).
        class_dir: Actual class subfolder path.

    Returns:
        List of image paths relative to ``root``.
    """

    images: List[Path] = []
    if not class_dir.exists():
        return images
    for path in sorted(class_dir.rglob("*")):
        if path.is_file() and path.suffix in IMAGE_EXTENSIONS:
            images.append(path.relative_to(root))
    return images


def stratified_split(
    healthy: Sequence[Path],
    scab: Sequence[Path],
    train_ratio: float,
    val_ratio: float,
    seed: int,
) -> Tuple[List[Path], List[Path], List[Path]]:
    """Split two class lists into train/val/test with the same ratios.

    Args:
        healthy: Healthy class image paths.
        scab: Scab class image paths.
        train_ratio: Proportion for training split.
        val_ratio: Proportion for validation split.
        seed: Random seed.

    Returns:
        Tuple of (train, val, test) lists of Paths (relative paths).
    """

    rng = random.Random(seed)
    healthy_list: List[Path] = list(healthy)
    scab_list: List[Path] = list(scab)
    rng.shuffle(healthy_list)
    rng.shuffle(scab_list)

    def split_one(items: Sequence[Path]) -> Tuple[List[Path], List[Path], List[Path]]:
        n: int = len(items)
        n_train: int = int(n * train_ratio)
        n_val: int = int(n * val_ratio)
        train_items: List[Path] = list(items[:n_train])
        val_items: List[Path] = list(items[n_train : n_train + n_val])
        test_items: List[Path] = list(items[n_train + n_val :])
        return train_items, val_items, test_items

    h_train, h_val, h_test = split_one(healthy_list)
    s_train, s_val, s_test = split_one(scab_list)

    train = h_train + s_train
    val = h_val + s_val
    test = h_test + s_test

    # Maintain deterministic order for reproducibility
    train.sort()
    val.sort()
    test.sort()
    return train, val, test


def write_list(paths: Iterable[Path], out_file: Path) -> None:
    """Write relative paths to a text file.

    Args:
        paths: Iterable of relative ``Path`` entries.
        out_file: Output file path.
    """

    out_file.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = [str(p).replace("\\", "/") for p in paths]
    out_file.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(description="Generate train/val/test splits for AppleScabFDs")
    parser.add_argument("--root", type=Path, default=None, help="Dataset root folder (defaults to auto-detect)")
    parser.add_argument("--train", type=float, default=0.8, help="Train ratio (default: 0.8)")
    parser.add_argument("--val", type=float, default=0.1, help="Val ratio (default: 0.1)")
    parser.add_argument("--test", type=float, default=0.1, help="Test ratio (default: 0.1)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    return parser.parse_args()


def main() -> None:
    """Entry point for generating splits.

    Validates ratios, discovers images, performs a stratified split, and writes
    lists to the ``sets/`` directory.
    """

    args = parse_args()
    total_ratio: float = args.train + args.val + args.test
    if not (abs(total_ratio - 1.0) < 1e-6):
        raise ValueError(f"Ratios must sum to 1.0, got {total_ratio:.3f}")

    # Auto-detect root if not provided
    candidate_roots: List[Path] = []
    if args.root is not None:
        candidate_roots.append(args.root)
    candidate_roots.extend([
        Path(__file__).resolve().parents[1],  # datasets/AppleScabFDs
        Path.cwd(),
    ])

    root: Optional[Path] = None
    class_dirs: Dict[str, Path] = {}
    for cand in candidate_roots:
        mapping = find_class_dirs(cand)
        if {"Healthy", "Scab"}.issubset(mapping.keys()):
            root = cand
            class_dirs = mapping
            break

    if root is None:
        raise FileNotFoundError(
            "Could not locate dataset root with 'Healthy/' and 'Scab/' subfolders. "
            "Pass --root explicitly."
        )

    healthy_images: List[Path] = find_images(root, class_dirs["Healthy"])
    scab_images: List[Path] = find_images(root, class_dirs["Scab"])

    if not healthy_images and not scab_images:
        raise FileNotFoundError(
            f"No images found under '{class_dirs['Healthy'].name}/' or '{class_dirs['Scab'].name}/' in {root}"
        )

    train, val, test = stratified_split(healthy_images, scab_images, args.train, args.val, args.seed)

    write_list(healthy_images + scab_images, root / "sets" / "all.txt")
    write_list(train, root / "sets" / "train.txt")
    write_list(val, root / "sets" / "val.txt")
    write_list(test, root / "sets" / "test.txt")

    print(f"Root: {root}")
    print(f"Healthy images: {len(healthy_images)} | Scab images: {len(scab_images)}")
    print("Created:")
    for name in ("all", "train", "val", "test"):
        print(f" - sets/{name}.txt")


if __name__ == "__main__":
    main()


