#!/usr/bin/env python3
"""Train YOLO26 on the local BDD100K dataset."""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent
DEFAULT_DATASET_ROOT = REPO_ROOT / "datasets/BDD100k"
DEFAULT_DATA_CONFIG = REPO_ROOT / "ultralytics/cfg/datasets/BDD100k.yaml"
DEFAULT_MODEL = REPO_ROOT / "yolo26s.pt"


def parse_batch(value: str) -> int | float:
    try:
        numeric = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid batch value: {value}") from exc
    return int(numeric) if numeric.is_integer() else numeric


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_CONFIG, help="Dataset YAML config.")
    parser.add_argument("--model", default=str(DEFAULT_MODEL), help="Model checkpoint or model yaml.")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=parse_batch, default=-1, help="Batch size. Use -1 for auto batch.")
    parser.add_argument("--device", default="auto", help="Training device: auto, cpu, mps, or CUDA device id.")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--project", default=str(REPO_ROOT / "runs/train"))
    parser.add_argument("--name", default="bdd100k-yolo26s")
    parser.add_argument("--overwrite-labels", action="store_true", help="Re-generate existing YOLO txt labels.")
    return parser.parse_args()


def ensure_absolute(path: Path) -> Path:
    path = path.expanduser()
    return path if path.is_absolute() else (REPO_ROOT / path).resolve()


def ensure_dataset(dataset_root: Path) -> None:
    train_images = dataset_root / "images/100k/train"
    train_labels = dataset_root / "labels/100k/train"
    if not train_images.exists() or not train_labels.exists():
        raise FileNotFoundError(
            f"BDD100K dataset structure not found under {dataset_root}. "
            "Expected images/100k/train and labels/100k/train."
        )


def ensure_yolo_labels(dataset_root: Path, overwrite: bool) -> None:
    train_labels = dataset_root / "labels/100k/train"
    has_txt = any(train_labels.glob("*.txt"))
    if has_txt and not overwrite:
        return

    print("YOLO labels not found or overwrite requested. Converting BDD100K JSON annotations first...")
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts/convert_bdd100k_to_yolo.py"),
        "--dataset-root",
        str(dataset_root),
    ]
    if overwrite:
        cmd.append("--overwrite")
    subprocess.run(cmd, check=True)


def build_resolved_data_yaml(dataset_root: Path) -> str:
    yaml_text = "\n".join(
        [
            f"path: {dataset_root}",
            "train: images/100k/train",
            "val: images/100k/val",
            "test: images/100k/test",
            "",
            "names:",
            "  0: person",
            "  1: rider",
            "  2: car",
            "  3: bus",
            "  4: truck",
            "  5: bike",
            "  6: motor",
            "  7: traffic light",
            "  8: traffic sign",
            "  9: train",
            "",
        ]
    )
    with tempfile.NamedTemporaryFile("w", suffix="-bdd100k.yaml", delete=False, encoding="utf-8") as tmp:
        tmp.write(yaml_text)
        return tmp.name


def resolve_device(device: str) -> str:
    if device != "auto":
        return device

    import torch

    if torch.cuda.is_available():
        return "0"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def main() -> None:
    args = parse_args()
    dataset_root = ensure_absolute(args.dataset_root)
    model_path = ensure_absolute(Path(args.model))

    ensure_dataset(dataset_root)
    ensure_yolo_labels(dataset_root, args.overwrite_labels)

    if not model_path.exists() and not str(args.model).endswith((".yaml", ".yml", ".pt")):
        raise FileNotFoundError(f"Model file not found: {model_path}")

    try:
        import torch
        from ultralytics import YOLO
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(
            "Failed to import Ultralytics. Install dependencies first with 'pip install -e .' in the repo root."
        ) from exc

    device = resolve_device(args.device)
    data = build_resolved_data_yaml(dataset_root)
    print(f"Using device: {device}")
    print(f"Using data config: {data}")
    if device == "cpu" and hasattr(torch.backends, "mps") and torch.backends.mps.is_built():
        print("MPS is built into PyTorch but not available in the current environment, so training will run on CPU.")

    model = YOLO(str(model_path) if model_path.exists() else args.model)
    model.train(
        data=data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=device,
        workers=args.workers,
        project=args.project,
        name=args.name,
    )


if __name__ == "__main__":
    main()
