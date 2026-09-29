"""One-shot live acquisition and timestamp alignment using the existing client."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import numpy as np
import pandas as pd

from stream_client import GyroStreamClient


def collect_streams_once(ports: Iterable[int], samples_per_port: int, host: str = "127.0.0.1", timeout: float = 5.0) -> dict[int, list[dict[str, float]]]:
    ports = list(ports)
    def read(port: int) -> tuple[int, list[dict[str, float]]]:
        client = GyroStreamClient(host=host, port=port, timeout=timeout)
        try:
            return port, client.read_samples(samples_per_port)
        finally:
            client.close()
    with ThreadPoolExecutor(max_workers=len(ports)) as executor:
        return dict(executor.map(read, ports))


def align_streams(streams: dict[int, list[dict[str, float]]], tolerance: float) -> pd.DataFrame:
    if not streams:
        raise ValueError("streams must not be empty")
    frames = []
    for port, samples in sorted(streams.items()):
        label = "baseline" if port == 5009 else f"gyro{port - 5000}"
        frame = pd.DataFrame(samples).rename(columns={"x": f"{label}_x", "y": f"{label}_y", "z": f"{label}_z"})
        frames.append(frame)
    result = frames[0].sort_values("timestamp").drop_duplicates("timestamp")
    for frame in frames[1:]:
        result = pd.merge_asof(result.sort_values("timestamp"), frame.sort_values("timestamp"), on="timestamp", direction="nearest", tolerance=tolerance)
    result = result.dropna().sort_values("timestamp").reset_index(drop=True)
    if result.empty:
        raise ValueError("no synchronized samples remained after alignment")
    return result
