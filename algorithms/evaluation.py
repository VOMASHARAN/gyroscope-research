"""Shared accuracy, latency, correlation, and consistency metrics."""
from __future__ import annotations

import time
from typing import Callable

import numpy as np
import pandas as pd


def error_metrics(estimate: np.ndarray, reference: np.ndarray, sample_rate: float | None = None) -> dict[str, float]:
    error = np.asarray(estimate, float) - np.asarray(reference, float)
    result = {"mae": float(np.mean(np.abs(error))), "rmse": float(np.sqrt(np.mean(error ** 2))), "bias": float(np.mean(error)), "std": float(np.std(error)), "max_abs_error": float(np.max(np.abs(error)))}
    if sample_rate and len(error) > 1:
        endpoint_drift = np.asarray(error[-1] - error[0], dtype=float)
        result["drift_per_hour"] = float(np.linalg.norm(endpoint_drift) / ((len(error) - 1) / sample_rate) * 3600.0)
    else:
        result["drift_per_hour"] = float("nan")
    return result


def latency_summary(call: Callable[[], object], repeats: int = 1) -> dict[str, float]:
    values = []
    for _ in range(repeats):
        start = time.perf_counter(); call(); values.append((time.perf_counter() - start) * 1000.0)
    data = np.asarray(values)
    return {"mean_ms": float(np.mean(data)), "median_ms": float(np.median(data)), "min_ms": float(np.min(data)), "max_ms": float(np.max(data)), "p95_ms": float(np.percentile(data, 95)), "p99_ms": float(np.percentile(data, 99)), "throughput_hz": float(1000.0 / np.mean(data))}


def correlation_matrices(sensor_data: np.ndarray, truth: np.ndarray | None = None) -> dict[str, np.ndarray]:
    data = np.asarray(sensor_data, float)
    if data.ndim != 3 or data.shape[2] != 3:
        raise ValueError("sensor_data must have shape (samples, sensors, 3)")
    source = data if truth is None else data - np.asarray(truth, float)[:, None, :]
    return {axis: np.corrcoef(source[:, :, index], rowvar=False) for index, axis in enumerate("xyz")}


def nis(innovations: np.ndarray, innovation_covariances: np.ndarray) -> np.ndarray:
    values = []
    for innovation, covariance in zip(innovations, innovation_covariances):
        values.append(float(innovation @ np.linalg.pinv(covariance) @ innovation))
    return np.asarray(values)


def comparison_table(results: dict[str, np.ndarray], reference: np.ndarray, sample_rate: float | None = None) -> pd.DataFrame:
    rows = []
    for name, estimate in results.items():
        row = {"algorithm": name}; row.update(error_metrics(estimate, reference, sample_rate)); rows.append(row)
    return pd.DataFrame(rows)
