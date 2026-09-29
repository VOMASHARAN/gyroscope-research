"""Offline Rauch-Tung-Striebel smoother for a random-walk state."""
from __future__ import annotations

import numpy as np


def rts_smooth(filtered_states: np.ndarray, filtered_covariances: np.ndarray, timestamps: np.ndarray, process_covariance: np.ndarray | float = 1e-5) -> dict[str, np.ndarray]:
    x = np.asarray(filtered_states, float); p = np.asarray(filtered_covariances, float); t = np.asarray(timestamps, float)
    if x.ndim != 2 or p.shape != (len(x), x.shape[1], x.shape[1]) or len(t) != len(x):
        raise ValueError("invalid forward-filter shapes")
    smooth_x, smooth_p = x.copy(), p.copy()
    q = np.diag(np.broadcast_to(np.asarray(process_covariance, float), (x.shape[1],)))
    for index in range(len(x) - 2, -1, -1):
        dt = max(float(t[index + 1] - t[index]), np.finfo(float).eps)
        predicted_p = p[index] + q * dt
        gain = p[index] @ np.linalg.pinv(predicted_p)
        smooth_x[index] = x[index] + gain @ (smooth_x[index + 1] - x[index])
        smooth_p[index] = p[index] + gain @ (smooth_p[index + 1] - predicted_p) @ gain.T
        smooth_p[index] = (smooth_p[index] + smooth_p[index].T) / 2.0
    return {"estimate": smooth_x, "covariance": smooth_p, "offline_only": np.array(True)}
