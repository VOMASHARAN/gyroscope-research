"""Interacting multiple-model filtering for scalar gyro-rate estimates.

The implementation is a linear Gaussian random-walk IMM.  Each model has a
different process-noise variance, while all models share the scalar
measurement model ``z = x + v``.  Transition probabilities, interaction
(mixing), Kalman prediction/update, Gaussian likelihoods, and the combined
estimate are explicit so the result is inspectable in experiments.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

import numpy as np
import pandas as pd


@dataclass
class IMMResult:
    estimate: float
    covariance: float
    model_probabilities: np.ndarray
    model_estimates: np.ndarray
    model_covariances: np.ndarray
    likelihoods: np.ndarray


class LinearGaussian1DIMM:
    """Scalar random-walk IMM with candidate models having distinct ``q``."""

    def __init__(
        self,
        process_noises: Sequence[float] = (1e-5, 1e-3, 1e-2),
        measurement_noise: float = 1e-3,
        transition_matrix: Optional[Sequence[Sequence[float]]] = None,
        initial_probabilities: Optional[Sequence[float]] = None,
        initial_state: float = 0.0,
        initial_covariance: float = 1.0,
    ):
        q = np.asarray(process_noises, dtype=float)
        if q.ndim != 1 or len(q) == 0 or np.any(q < 0):
            raise ValueError("process_noises must be a non-empty sequence of variances")
        if measurement_noise <= 0:
            raise ValueError("measurement_noise must be positive")
        n = len(q)
        if transition_matrix is None:
            transition = np.full((n, n), 0.05 / max(n - 1, 1))
            np.fill_diagonal(transition, 0.95 if n > 1 else 1.0)
        else:
            transition = np.asarray(transition_matrix, dtype=float)
            if transition.shape != (n, n):
                raise ValueError("transition_matrix must be square with one row per model")
            if np.any(transition < 0) or np.any(np.isclose(transition.sum(axis=1), 0.0)):
                raise ValueError("transition_matrix rows must be non-negative and non-zero")
            transition = transition / transition.sum(axis=1, keepdims=True)
        if initial_probabilities is None:
            probabilities = np.full(n, 1.0 / n)
        else:
            probabilities = np.asarray(initial_probabilities, dtype=float)
            if probabilities.shape != (n,) or np.any(probabilities < 0) or probabilities.sum() <= 0:
                raise ValueError("initial_probabilities must be non-negative and non-zero")
            probabilities = probabilities / probabilities.sum()
        if initial_covariance <= 0:
            raise ValueError("initial_covariance must be positive")
        self.process_noises = q
        self.measurement_noise = float(measurement_noise)
        self.transition_matrix = transition
        self.model_probabilities = probabilities
        self.model_estimates = np.full(n, float(initial_state))
        self.model_covariances = np.full(n, float(initial_covariance))
        self.last_result: Optional[IMMResult] = None

    @property
    def n_models(self) -> int:
        return len(self.process_noises)

    def reset(self, state: float = 0.0, covariance: float = 1.0) -> None:
        if covariance <= 0:
            raise ValueError("covariance must be positive")
        self.model_probabilities = np.full(self.n_models, 1.0 / self.n_models)
        self.model_estimates = np.full(self.n_models, float(state))
        self.model_covariances = np.full(self.n_models, float(covariance))
        self.last_result = None

    def _interaction(self) -> tuple[np.ndarray, np.ndarray]:
        """Return mixed initial conditions and predicted model probabilities."""
        prior = self.model_probabilities @ self.transition_matrix
        prior = np.maximum(prior, np.finfo(float).tiny)
        prior /= prior.sum()
        mixing = (self.model_probabilities[:, None] * self.transition_matrix) / prior[None, :]
        mixed_x = mixing.T @ self.model_estimates
        mixed_p = np.empty(self.n_models)
        for j in range(self.n_models):
            delta = self.model_estimates - mixed_x[j]
            mixed_p[j] = np.sum(mixing[:, j] * (self.model_covariances + delta * delta))
        return mixed_x, np.maximum(mixed_p, np.finfo(float).eps)

    def step(self, measurement: float, dt: float = 1.0) -> IMMResult:
        """Consume one scalar measurement and return the combined posterior."""
        if dt <= 0:
            raise ValueError("dt must be positive")
        if not np.isfinite(measurement):
            raise ValueError("measurement must be finite")
        mixed_x, mixed_p = self._interaction()
        estimates = mixed_x.copy()
        covariances = mixed_p + self.process_noises * float(dt)
        likelihoods = np.empty(self.n_models)
        for j in range(self.n_models):
            innovation = float(measurement - estimates[j])
            innovation_cov = float(covariances[j] + self.measurement_noise)
            gain = covariances[j] / innovation_cov
            estimates[j] += gain * innovation
            covariances[j] = max((1.0 - gain) * covariances[j], np.finfo(float).eps)
            likelihoods[j] = np.exp(
                -0.5 * innovation * innovation / innovation_cov
            ) / np.sqrt(2.0 * np.pi * innovation_cov)
        posterior = mixed_x * 0.0 + self.model_probabilities @ self.transition_matrix
        posterior *= likelihoods
        if not np.isfinite(posterior).all() or posterior.sum() <= 0:
            posterior = np.full(self.n_models, 1.0 / self.n_models)
        else:
            posterior /= posterior.sum()
        estimate = float(posterior @ estimates)
        covariance = float(posterior @ (covariances + (estimates - estimate) ** 2))
        self.model_probabilities = posterior
        self.model_estimates = estimates
        self.model_covariances = covariances
        self.last_result = IMMResult(
            estimate, covariance, posterior.copy(), estimates.copy(),
            covariances.copy(), likelihoods.copy()
        )
        return self.last_result

    def filter(self, measurements: Iterable[float], dt: float = 1.0) -> pd.DataFrame:
        rows = []
        for index, value in enumerate(measurements):
            result = self.step(float(value), dt=dt)
            row = {
                "index": index,
                "estimate": result.estimate,
                "covariance": result.covariance,
            }
            row.update({f"model_probability_{i}": p for i, p in enumerate(result.model_probabilities)})
            rows.append(row)
        return pd.DataFrame(rows)


def run_imm(
    measurements: Iterable[float],
    process_noises: Sequence[float] = (1e-5, 1e-3, 1e-2),
    measurement_noise: float = 1e-3,
    dt: float = 1.0,
    **kwargs,
) -> pd.DataFrame:
    """Convenience wrapper returning the scalar IMM time series."""
    return LinearGaussian1DIMM(
        process_noises=process_noises,
        measurement_noise=measurement_noise,
        **kwargs,
    ).filter(measurements, dt=dt)


# Short aliases make the public algorithm convenient in small experiments.
IMMFilter = LinearGaussian1DIMM
imm_filter = run_imm
