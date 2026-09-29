"""Central linear Kalman filter for a three-axis random-walk state."""
from __future__ import annotations

import numpy as np


def run_central_kf(sensor_data: np.ndarray, timestamps: np.ndarray, measurement_variance: np.ndarray, process_covariance: np.ndarray | float = 1e-5, initial_state: np.ndarray | None = None, initial_covariance: np.ndarray | float = 1.0) -> dict[str, np.ndarray]:
    z = np.asarray(sensor_data, dtype=float)
    t = np.asarray(timestamps, dtype=float)
    if z.ndim != 3 or z.shape[2] != 3 or len(t) != len(z):
        raise ValueError("sensor_data must have shape (samples, sensors, 3) and match timestamps")
    sensors = z.shape[1]
    r = np.asarray(measurement_variance, dtype=float)
    if r.shape == (sensors, 3):
        r = np.broadcast_to(r, (len(z), sensors, 3))
    if r.shape != z.shape or np.any(r <= 0):
        raise ValueError("measurement_variance must have sensor/axis shape or full data shape")
    q = np.broadcast_to(np.asarray(process_covariance, dtype=float), (3,))
    p0 = np.broadcast_to(np.asarray(initial_covariance, dtype=float), (3,)).copy()
    x = np.zeros(3) if initial_state is None else np.asarray(initial_state, dtype=float).copy()
    p = p0.copy()
    estimates, covariances, innovations, innovation_covariances = [], [], [], []
    h = np.tile(np.eye(3), (sensors, 1))
    for index in range(len(z)):
        dt = max(float(t[index] - t[index - 1]), np.finfo(float).eps) if index else 1.0
        p = p + np.diag(q * dt)
        observation = z[index].reshape(-1)
        r_matrix = np.diag(r[index].reshape(-1))
        innovation = observation - h @ x
        s = h @ p @ h.T + r_matrix
        gain = np.linalg.solve(s, (p @ h.T).T).T
        x = x + gain @ innovation
        identity = np.eye(3)
        p = (identity - gain @ h) @ p @ (identity - gain @ h).T + gain @ r_matrix @ gain.T
        p = (p + p.T) / 2.0
        estimates.append(x.copy()); covariances.append(p.copy()); innovations.append(innovation); innovation_covariances.append(s.copy())
    return {"estimate": np.asarray(estimates), "covariance": np.asarray(covariances), "innovation": np.asarray(innovations), "innovation_covariance": np.asarray(innovation_covariances)}
