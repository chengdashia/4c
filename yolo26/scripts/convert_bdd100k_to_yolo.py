#!/usr/bin/env python3
"""Convert BDD100K detection JSON annotations to Ultralytics YOLO TXT labels."""

from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image


BDD100K_CLASSES = [
    "person",
    "rider",
    "car",
    "bus",
    "truck",
    "bike",
    "motor",
    "traffic light",
    "traffic sign",
    "train",
]
CLASS_TO_ID = {name: i for i, name in enumerate(BDD100K_CLASSES)}
REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=REPO_ROOT / "datasets/BDD100k",
        help="BDD100K dataset root containing images/100k and labels/100k.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        choices=["train", "val", "test"],
        help="Dataset splits to convert.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing YOLO .txt labels.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=8,
        help="Number of worker threads used during conversion.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional max number of files to convert per split for quick testing.",
    )
    return parser.parse_args()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def convert_one(json_path: Path, image_dir: Path, overwrite: bool) -> tuple[str, int]:
    txt_path = json_path.with_suffix(".txt")
    if txt_path.exists() and not overwrite:
        return "skipped", 0

    image_path = image_dir / f"{json_path.stem}.jpg"
    if not image_path.exists():
        return "missing_image", 0

    with image_path.open("rb") as im_file:
        width, height = Image.open(im_file).size

    data = json.loads(json_path.read_text(encoding="utf-8"))
    objects = data.get("frames", [{}])[0].get("objects", [])
    lines = []

    for obj in objects:
        category = obj.get("category")
        box = obj.get("box2d")
        if category not in CLASS_TO_ID or not box:
            continue

        x1 = clamp(float(box["x1"]), 0.0, float(width))
        y1 = clamp(float(box["y1"]), 0.0, float(height))
        x2 = clamp(float(box["x2"]), 0.0, float(width))
        y2 = clamp(float(box["y2"]), 0.0, float(height))
        bw, bh = x2 - x1, y2 - y1
        if bw <= 0 or bh <= 0:
            continue

        x_center = ((x1 + x2) / 2) / width
        y_center = ((y1 + y2) / 2) / height
        w_norm = bw / width
        h_norm = bh / height
        cls = CLASS_TO_ID[category]
        lines.append(f"{cls} {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")

    txt_path.write_text("".join(lines), encoding="utf-8")
    return "converted", len(lines)


def convert_split(root: Path, split: str, overwrite: bool, workers: int, limit: int) -> None:
    image_dir = root / "images" / "100k" / split
    label_dir = root / "labels" / "100k" / split
    json_files = sorted(label_dir.glob("*.json"))
    if limit > 0:
        json_files = json_files[:limit]

    if not image_dir.exists() or not label_dir.exists():
        raise FileNotFoundError(f"Missing split directories: {image_dir} or {label_dir}")

    converted = skipped = missing = total_boxes = 0
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for status, box_count in pool.map(lambda p: convert_one(p, image_dir, overwrite), json_files):
            if status == "converted":
                converted += 1
                total_boxes += box_count
            elif status == "skipped":
                skipped += 1
            elif status == "missing_image":
                missing += 1

    print(
        f"[{split}] files={len(json_files)} converted={converted} skipped={skipped} "
        f"missing_images={missing} boxes={total_boxes}"
    )


def main() -> None:
    args = parse_args()
    args.dataset_root = args.dataset_root.expanduser()
    if not args.dataset_root.is_absolute():
        args.dataset_root = (REPO_ROOT / args.dataset_root).resolve()
    for split in args.splits:
        convert_split(args.dataset_root, split, args.overwrite, args.workers, args.limit)


if __name__ == "__main__":
    main()
