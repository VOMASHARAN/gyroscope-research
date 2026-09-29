"""Canonical experiment dataset and validation utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ExperimentDataset:
    timestamps: np.ndarray
    gyro_data: np.ndarray
    baseline_data: np.ndarray | None = None
    truth_data: np.ndarray | None = None
    sample_rate: float | None = None
    experiment_id: str = "experiment"

    def __post_init__(self) -> None:
        timestamps = np.asarray(self.timestamps, dtype=float)
        gyro_data = np.asarray(self.gyro_data, dtype=float)
        if timestamps.ndim != 1 or gyro_data.ndim != 3 or gyro_data.shape[0] != len(timestamps):
            raise ValueError("timestamps and gyro_data must have shapes (samples,) and (samples, sensors, axes)")
        if gyro_data.shape[1] == 0 or gyro_data.shape[2] != 3:
            raise ValueError("gyro_data must contain at least one sensor and three axes")
        if not np.isfinite(timestamps).all() or not np.isfinite(gyro_data).all():
            raise ValueError("timestamps and gyro_data must be finite")
        if len(timestamps) > 1 and np.any(np.diff(timestamps) <= 0):
            raise ValueError("timestamps must be strictly increasing")
        for name in ("baseline_data", "truth_data"):
            value = getattr(self, name)
            if value is not None and (np.asarray(value).shape != (len(timestamps), 3) or not np.isfinite(value).all()):
                raise ValueError(f"{name} must have shape (samples, 3) and finite values")
        if self.sample_rate is not None and self.sample_rate <= 0:
            raise ValueError("sample_rate must be positive")

    @property
    def sample_count(self) -> int:
        return len(self.timestamps)

    @property
    def sensor_count(self) -> int:
        return self.gyro_data.shape[1]

    @property
    def duration(self) -> float:
        return float(self.timestamps[-1] - self.timestamps[0]) if self.sample_count > 1 else 0.0

    @property
    def mean_dt(self) -> float:
        return float(np.mean(np.diff(self.timestamps))) if self.sample_count > 1 else float("nan")

    def to_frame(self) -> pd.DataFrame:
        frame = {"timestamp": self.timestamps}
        for sensor in range(self.sensor_count):
            for axis, index in zip("xyz", range(3)):
                frame[f"gyro{sensor + 1}_{axis}"] = self.gyro_data[:, sensor, index]
        for label, values in (("baseline", self.baseline_data), ("truth", self.truth_data)):
            if values is not None:
                for axis, index in zip("xyz", range(3)):
                    frame[f"{label}_{axis}"] = values[:, index]
        return pd.DataFrame(frame)

    @classmethod
    def from_frames(cls, gyro_frame: pd.DataFrame, baseline_frame: pd.DataFrame | None = None, truth_frame: pd.DataFrame | None = None, sample_rate: float | None = None, experiment_id: str = "experiment") -> "ExperimentDataset":
        required = ["timestamp"] + [f"gyro{i}_{axis}" for i in range(1, 9) for axis in "xyz"]
        missing = sorted(set(required) - set(gyro_frame.columns))
        if missing:
            raise ValueError(f"missing gyro columns: {missing}")
        timestamps = gyro_frame["timestamp"].to_numpy(float)
        gyro = gyro_frame[[f"gyro{i}_{axis}" for i in range(1, 9) for axis in "xyz"]].to_numpy(float).reshape(-1, 8, 3)
        def optional(frame: pd.DataFrame | None, prefix: str) -> np.ndarray | None:
            if frame is None:
                return None
            if not np.array_equal(timestamps, frame["timestamp"].to_numpy(float)):
                raise ValueError(f"{prefix} timestamps do not match gyro timestamps")
            return frame[[f"{prefix}_{axis}" for axis in "xyz"]].to_numpy(float)
        return cls(timestamps, gyro, optional(baseline_frame, "baseline"), optional(truth_frame, "truth"), sample_rate, experiment_id)

    @classmethod
    def from_csv(cls, gyro_path: str, baseline_path: str | None = None, truth_path: str | None = None, sample_rate: float | None = None, experiment_id: str = "experiment") -> "ExperimentDataset":
        return cls.from_frames(pd.read_csv(gyro_path), pd.read_csv(baseline_path) if baseline_path else None, pd.read_csv(truth_path) if truth_path else None, sample_rate, experiment_id)


def validate_dataset(dataset: ExperimentDataset) -> dict[str, object]:
    dt = np.diff(dataset.timestamps)
    return {
        "status": "PASS",
        "sample_count": dataset.sample_count,
        "sensor_count": dataset.sensor_count,
        "finite": bool(np.isfinite(dataset.gyro_data).all()),
        "duplicate_timestamps": bool(len(np.unique(dataset.timestamps)) != dataset.sample_count),
        "mean_dt": float(np.mean(dt)) if len(dt) else float("nan"),
        "min_dt": float(np.min(dt)) if len(dt) else float("nan"),
        "max_dt": float(np.max(dt)) if len(dt) else float("nan"),
        "duration": dataset.duration,
        "has_baseline": dataset.baseline_data is not None,
        "has_truth": dataset.truth_data is not None,
    }


def apply_degradation(dataset: ExperimentDataset, scenario: Mapping[str, object] | None = None, seed: int = 0) -> ExperimentDataset:
    scenario = scenario or {}
    data = dataset.gyro_data.copy()
    sensor = int(scenario.get("sensor", 0))
    rng = np.random.default_rng(seed)
    if "noise_scale" in scenario:
        scale = float(scenario["noise_scale"])
        data[:, sensor, :] += rng.normal(0.0, scale, size=data[:, sensor, :].shape)
    if "bias" in scenario:
        data[:, sensor, :] += np.asarray(scenario["bias"], dtype=float)
    if "corrupt_slice" in scenario:
        start, stop = scenario["corrupt_slice"]
        data[int(start):int(stop), sensor, :] = np.nan
    if np.isnan(data).any():
        data = np.nan_to_num(data, nan=0.0)
    return ExperimentDataset(dataset.timestamps.copy(), data, None if dataset.baseline_data is None else dataset.baseline_data.copy(), None if dataset.truth_data is None else dataset.truth_data.copy(), dataset.sample_rate, dataset.experiment_id)
