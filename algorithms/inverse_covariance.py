"""Inverse-covariance weighted fusion benchmarks."""
from __future__ import annotations

import numpy as np


def inverse_covariance_fusion(measurements: np.ndarray, covariances: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Fuse shape (samples, sensors, axes) using independent scalar variances.

    This benchmark does not model cross-sensor covariance; correlated errors can
    make its nominal covariance overconfident.
    """
    values = np.asarray(measurements, dtype=float)
    variance = np.asarray(covariances, dtype=float)
    if values.ndim != 3 or variance.ndim not in (2, 3) or np.any(variance <= 0):
        raise ValueError("measurements must be 3D and positive covariances are required")
    if variance.ndim == 2:
        variance = np.broadcast_to(variance, (values.shape[0],) + variance.shape)
    if variance.shape != values.shape:
        raise ValueError("covariances must have shape (sensors, axes) or measurements shape")
    precision = 1.0 / variance
    weights = precision / precision.sum(axis=1, keepdims=True)
    estimate = np.sum(weights * values, axis=1)
    fused_covariance = 1.0 / precision.sum(axis=1)
    return estimate, fused_covariance, weights
