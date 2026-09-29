"""Federated local random-walk filters with an information-form master."""
from __future__ import annotations

import numpy as np

from .central_kf import run_central_kf


def run_federated_kf(sensor_data: np.ndarray, timestamps: np.ndarray, measurement_variance: np.ndarray, process_variance: float = 1e-5) -> dict[str, np.ndarray]:
    z = np.asarray(sensor_data, float)
    r = np.asarray(measurement_variance, float)
    if r.shape != z.shape:
        r = np.broadcast_to(r, z.shape)
    local_estimates, local_covariances = [], []
    for sensor in range(z.shape[1]):
        result = run_central_kf(z[:, sensor: sensor + 1, :], timestamps, r[:, sensor: sensor + 1, :], process_variance)
        local_estimates.append(result["estimate"]); local_covariances.append(result["covariance"])
    estimates, covariances = [], []
    for index in range(len(z)):
        information = np.zeros((3, 3)); weighted = np.zeros(3)
        for sensor in range(z.shape[1]):
            precision = np.linalg.pinv(local_covariances[sensor][index])
            information += precision; weighted += precision @ local_estimates[sensor][index]
        covariance = np.linalg.pinv(information)
        estimates.append(covariance @ weighted); covariances.append((covariance + covariance.T) / 2.0)
    return {"estimate": np.asarray(estimates), "covariance": np.asarray(covariances), "local_estimates": np.asarray(local_estimates), "local_covariances": np.asarray(local_covariances)}
