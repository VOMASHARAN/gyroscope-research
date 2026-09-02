"""Basic sensor-fusion utilities for the multi-gyro research pipeline."""

from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def fuse_gyros(gyro_data: Dict[int, pd.DataFrame]) -> pd.DataFrame:
    """Simple arithmetic mean fusion across synchronized gyroscope streams."""
    if not gyro_data:
        raise ValueError("gyro_data must contain at least one sensor stream")

    ordered_ids = sorted(gyro_data.keys())
    timestamps = gyro_data[ordered_ids[0]]["timestamp"].to_numpy()
    fused = {"timestamp": timestamps}

    for axis in ("x", "y", "z"):
        axis_values = [gyro_data[g][f"gyro{g}_{axis}"].to_numpy() for g in ordered_ids]
        fused[f"fused_{axis}"] = np.mean(np.column_stack(axis_values), axis=1)

    return pd.DataFrame(fused)


def compute_error_metrics(fused_df: pd.DataFrame, baseline_df: pd.DataFrame) -> pd.DataFrame:
    """Compute mean error, MAE, RMSE, max absolute error, and std dev of error."""
    rows = []
    for axis in ("x", "y", "z"):
        err = fused_df[f"fused_{axis}"].to_numpy() - baseline_df[f"baseline_{axis}"].to_numpy()
        rows.append({
            "axis": axis,
            "mean_error": float(np.mean(err)),
            "mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(np.square(err)))),
            "max_abs_error": float(np.max(np.abs(err))),
            "std_error": float(np.std(err)),
        })
    return pd.DataFrame(rows)


def save_fusion_summary(metrics_df: pd.DataFrame, outpath: str):
    lines = [
        "FUSION PERFORMANCE METRICS",
        "",
        "Definitions:",
        "- Mean error = mean(fused - baseline)",
        "- MAE = mean(abs(fused - baseline))",
        "- RMSE = sqrt(mean((fused - baseline)^2))",
        "- Max abs error = max(abs(fused - baseline))",
        "- Std error = std(fused - baseline)",
        "",
    ]
    lines.extend(
        [
            f"Axis={row['axis']}: mean_error={row['mean_error']:.6f}, "
            f"MAE={row['mae']:.6f}, RMSE={row['rmse']:.6f}, "
            f"max_abs_error={row['max_abs_error']:.6f}, std_error={row['std_error']:.6f}"
            for _, row in metrics_df.iterrows()
        ]
    )
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    print("Basic mean-fusion module for multi-gyro sensor fusion.")
