"""Single-target probabilistic measurement association (PMA).

For one predicted scalar target and one measurement from each sensor, PMA
gates measurements using the innovation Mahalanobis distance, evaluates each
Gaussian innovation likelihood, and normalizes likelihoods together with an
explicit missed-detection hypothesis.  This is JPDA-like association for a
single target, not full classical JPDA: it has no multi-target joint event
enumeration, clutter spatial model, or track-existence logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np


@dataclass
class PMAResult:
    fused_measurement: Optional[float]
    updated_state: float
    updated_covariance: float
    association_weights: np.ndarray
    gated: np.ndarray
    innovation_likelihoods: np.ndarray
    missed_detection_probability: float
    mahalanobis_squared: np.ndarray

    def __getitem__(self, key):
        return getattr(self, key)


def pma_update(
    measurements: Sequence[float],
    predicted_state: float,
    predicted_covariance: float,
    measurement_noise: float | Sequence[float],
    gate_threshold: float = 9.0,
    sensor_priors: Optional[Sequence[float]] = None,
    detection_probability: float = 0.95,
    clutter_density: float = 1.0,
) -> PMAResult:
    """Perform a gated, normalized single-target association and update.

    ``gate_threshold`` is a squared Mahalanobis threshold. ``clutter_density`` is
    the constant spatial clutter density used for the missed-detection hypothesis.
    Association
    weights over the returned measurements sum to one minus the missed
    detection probability; the missed-detection hypothesis is returned
    separately.  The fused measurement is the weighted measurement conditional
    on association, and the state update uses its effective average noise.
    """
    z = np.asarray(measurements, dtype=float)
    if z.ndim != 1 or z.size == 0:
        raise ValueError("measurements must be a non-empty 1D sequence")
    if not np.isfinite(z).all() or predicted_covariance < 0 or gate_threshold <= 0:
        raise ValueError("measurements, covariance, and gate threshold are invalid")
    r = np.asarray(measurement_noise, dtype=float)
    if r.ndim == 0:
        r = np.full(z.size, float(r))
    if r.shape != z.shape or np.any(r <= 0):
        raise ValueError("measurement_noise must be positive scalar or one value per measurement")
    if not 0 < detection_probability <= 1:
        raise ValueError("detection_probability must be in (0, 1]")
    if clutter_density <= 0:
        raise ValueError("clutter_density must be positive")
    if sensor_priors is None:
        priors = np.full(z.size, 1.0 / z.size)
    else:
        priors = np.asarray(sensor_priors, dtype=float)
        if priors.shape != z.shape or np.any(priors < 0) or priors.sum() <= 0:
            raise ValueError("sensor_priors must be non-negative and match measurements")
        priors = priors / priors.sum()
    innovation = z - float(predicted_state)
    innovation_covariance = float(predicted_covariance) + r
    d2 = innovation * innovation / innovation_covariance
    gated = d2 <= gate_threshold
    likelihoods = np.exp(-0.5 * d2) / np.sqrt(2.0 * np.pi * innovation_covariance)
    raw = detection_probability * priors * likelihoods * gated
    # A constant clutter spatial density makes the hypothesis units explicit.
    # PMA is not a hidden hard selector; weak evidence retains missed mass.
    denominator = float((1.0 - detection_probability) * clutter_density + raw.sum())
    weights = raw / denominator
    missed = float((1.0 - detection_probability) * clutter_density / denominator)
    if weights.sum() > 0:
        fused = float(np.sum(weights * z) / weights.sum())
        effective_r = float(np.sum((weights / weights.sum()) * r))
        gain = float(predicted_covariance / (predicted_covariance + effective_r))
        updated_state = float(predicted_state + gain * (fused - predicted_state))
        updated_covariance = float((1.0 - gain) * predicted_covariance)
    else:
        fused = None
        updated_state = float(predicted_state)
        updated_covariance = float(predicted_covariance)
    return PMAResult(
        fused, updated_state, updated_covariance, weights, gated, likelihoods,
        missed, d2
    )


def associate_measurements(*args, **kwargs) -> PMAResult:
    """Alias with a descriptive name for callers that do not use ``PMA``."""
    return pma_update(*args, **kwargs)


probabilistic_measurement_association = pma_update


class ProbabilisticMeasurementAssociation:
    """Stateful convenience wrapper for repeated scalar PMA updates."""

    def __init__(self, measurement_noise: float | Sequence[float], **kwargs):
        self.measurement_noise = measurement_noise
        self.kwargs = kwargs

    def update(self, measurements, predicted_state, predicted_covariance):
        return pma_update(
            measurements, predicted_state, predicted_covariance,
            self.measurement_noise, **self.kwargs
        )


PMA = ProbabilisticMeasurementAssociation
