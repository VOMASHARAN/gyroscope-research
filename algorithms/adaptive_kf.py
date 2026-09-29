"""Innovation-based adaptive random-walk Kalman filter."""
from __future__ import annotations

import numpy as np


def run_adaptive_kf(measurements: np.ndarray, timestamps: np.ndarray, nominal_variance: float = 1e-3, process_variance: float = 1e-5, forgetting: float = 0.97, adaptation_gain: float = 0.05) -> dict[str, np.ndarray]:
    z = np.asarray(measurements, float)
    t = np.asarray(timestamps, float)
    if z.ndim != 2 or z.shape[1] != 3 or len(z) != len(t):
        raise ValueError("measurements must have shape (samples, 3)")
    x = np.zeros(3); p = np.eye(3); r = np.full(3, nominal_variance)
    estimates, covariances, innovations, r_history = [], [], [], []
    for index, value in enumerate(z):
        dt = max(float(t[index] - t[index - 1]), np.finfo(float).eps) if index else 1.0
        p = p + np.eye(3) * process_variance * dt
        innovation = value - x
        s = p.diagonal() + r
        gain = p.diagonal() / s
        x = x + gain * innovation
        p = np.diag((1.0 - gain) * p.diagonal())
        observed = np.maximum(innovation * innovation - p.diagonal(), np.finfo(float).eps)
        r = forgetting * r + (1.0 - forgetting) * ((1.0 - adaptation_gain) * r + adaptation_gain * observed)
        estimates.append(x.copy()); covariances.append(p.copy()); innovations.append(innovation.copy()); r_history.append(r.copy())
    return {"estimate": np.asarray(estimates), "covariance": np.asarray(covariances), "innovation": np.asarray(innovations), "measurement_variance": np.asarray(r_history)}
