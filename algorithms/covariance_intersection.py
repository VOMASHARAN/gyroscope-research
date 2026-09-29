"""Covariance Intersection for unknown cross-correlation."""
from __future__ import annotations

import numpy as np


def covariance_intersection(x1: np.ndarray, p1: np.ndarray, x2: np.ndarray, p2: np.ndarray, grid_size: int = 101) -> tuple[np.ndarray, np.ndarray, float]:
    x1, x2 = np.asarray(x1, float), np.asarray(x2, float)
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
    if x1.shape != x2.shape or p1.shape != p2.shape or p1.shape != (x1.size, x1.size):
        raise ValueError("CI inputs must contain matching vectors and square covariances")
    best = None
    for weight in np.linspace(0.0, 1.0, grid_size):
        information = weight * np.linalg.pinv(p1) + (1.0 - weight) * np.linalg.pinv(p2)
        covariance = np.linalg.pinv(information)
        estimate = covariance @ (weight * np.linalg.pinv(p1) @ x1 + (1.0 - weight) * np.linalg.pinv(p2) @ x2)
        score = float(np.trace(covariance))
        if best is None or score < best[0]:
            best = (score, estimate, (covariance + covariance.T) / 2.0, weight)
    assert best is not None
    return best[1], best[2], float(best[3])


def sequential_ci(estimates: np.ndarray, covariances: np.ndarray) -> dict[str, np.ndarray]:
    x, p = np.asarray(estimates[0], float), np.asarray(covariances[0], float)
    weights = []
    for index in range(1, len(estimates)):
        x, p, weight = covariance_intersection(x, p, estimates[index], covariances[index])
        weights.append(weight)
    return {"estimate": x, "covariance": p, "weights": np.asarray(weights)}
