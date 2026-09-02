"""Helpers for file and directory handling and simple utilities."""
from pathlib import Path
import os
from typing import Iterable


def ensure_dirs(paths: Iterable[str]):
    for p in paths:
        Path(p).parent.mkdir(parents=True, exist_ok=True)


def ensure_project_dirs(root: str = "."):
    dirs = [
        os.path.join(root, "data", "raw"),
        os.path.join(root, "data", "processed"),
        os.path.join(root, "data", "results"),
        os.path.join(root, "data", "baseline"),
        os.path.join(root, "data", "organized"),
        os.path.join(root, "plots"),
        os.path.join(root, "plots", "allan_deviation"),
        os.path.join(root, "results"),
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def save_text(path: str, text: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))
