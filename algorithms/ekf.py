"""Basic Kalman-filter-based gyro estimation for the research pipeline.

This is intentionally simple: a 2-state per-axis model with rate and bias.
It uses the fused 8-gyro average as the measurement input and writes a filtered
rate estimate for each axis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class BasicAxisEKF:
    def __init__(self, dt: float, process_noise: float = 1e-3, measurement_noise: float = 5e-2):
        self.dt = dt
        self.process_noise = process_noise
        self.measurement_noise = measurement_noise
        self.A = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=float)
        self.B = np.array([[self.dt], [0.0]], dtype=float)
        self.H = np.array([[1.0, 0.0]], dtype=float)
        self.Q = np.diag([process_noise, 1e-6])
        self.R = np.array([[measurement_noise]], dtype=float)
        self.x = np.zeros((2, 1), dtype=float)
        self.P = np.eye(2, dtype=float) * 1.0

    def update(self, measurement: float) -> float:
        # Prediction
        x_pred = self.A @ self.x + self.B @ np.array([[measurement]], dtype=float)
        P_pred = self.A @ self.P @ self.A.T + self.Q

        # Measurement update
        y = np.array([[measurement]], dtype=float) - self.H @ x_pred
        S = self.H @ P_pred @ self.H.T + self.R
        K = P_pred @ self.H.T @ np.linalg.inv(S)

        self.x = x_pred + K @ y
        self.P = (np.eye(2) - K @ self.H) @ P_pred

        return float(self.x[0, 0])


def run_basic_ekf(fused_df: pd.DataFrame, dt: float) -> pd.DataFrame:
    """Filter the fused x/y/z rate estimates using a simple 2-state Kalman model."""
    out = {"timestamp": fused_df["timestamp"].to_numpy()}

    for axis in ("x", "y", "z"):
        filt = []
        ekf = BasicAxisEKF(dt=dt)
        for value in fused_df[f"fused_{axis}"].to_numpy():
            filt.append(ekf.update(float(value)))
        out[f"ekf_{axis}"] = np.asarray(filt)

    return pd.DataFrame(out)


def compute_ekf_metrics(ekf_df: pd.DataFrame, baseline_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for axis in ("x", "y", "z"):
        err = ekf_df[f"ekf_{axis}"].to_numpy() - baseline_df[f"baseline_{axis}"].to_numpy()
        rows.append({
            "axis": axis,
            "mean_error": float(np.mean(err)),
            "mae": float(np.mean(np.abs(err))),
            "rmse": float(np.sqrt(np.mean(np.square(err)))),
            "max_abs_error": float(np.max(np.abs(err))),
            "std_error": float(np.std(err)),
            "latency_samples": 1,
        })
    return pd.DataFrame(rows)


def save_ekf_summary(metrics_df: pd.DataFrame, outpath: str):
    lines = [
        "BASIC EKF PERFORMANCE METRICS",
        "",
        "Definitions:",
        "- Mean error = mean(ekf - baseline)",
        "- MAE = mean(abs(ekf - baseline))",
        "- RMSE = sqrt(mean((ekf - baseline)^2))",
        "- Max abs error = max(abs(ekf - baseline))",
        "- Std error = std(ekf - baseline)",
        "- Latency reported in sample steps for the basic filter.",
        "",
    ]
    lines.extend(
        [
            f"Axis={row['axis']}: mean_error={row['mean_error']:.6f}, "
            f"MAE={row['mae']:.6f}, RMSE={row['rmse']:.6f}, "
            f"max_abs_error={row['max_abs_error']:.6f}, std_error={row['std_error']:.6f}, "
            f"latency_samples={row['latency_samples']}"
            for _, row in metrics_df.iterrows()
        ]
    )
    with open(outpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


if __name__ == "__main__":
    print("Basic EKF module for gyro rate filtering.")
