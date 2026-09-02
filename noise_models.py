"""Noise model implementations for gyroscope simulation.
Includes white noise, ARW (angle random walk), RRW (rate random walk), and first-order Markov (Gauss-Markov).
"""
from typing import Tuple
import numpy as np


def white_noise(std: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """Zero-mean Gaussian white noise."""
    return rng.normal(loc=0.0, scale=std, size=size)


def arw_process(arw_coeff: float, dt: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Angle Random Walk (ARW) modelled as the integral of white noise scaled by ARW coefficient.
    The discrete implementation uses increments ~ N(0, (arw_coeff^2) * dt).
    Units: if arw_coeff is rad/s/sqrt(Hz), integrated samples are in rad/s.
    """
    # increments with variance (arw_coeff^2) * dt
    increments = rng.normal(scale=arw_coeff * np.sqrt(dt), size=size)
    # cumulative sum gives a random-walk-like behavior appropriate for ARW contribution
    return np.cumsum(increments)


def rrw_process(rrw_coeff: float, dt: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    Rate Random Walk (RRW): modelled as an integrated white noise as well, but with different scaling
    and interpretation: RRW affects the rate drift over time (a second-order effect relative to white noise).
    Discrete implementation uses increments ~ N(0, rrw_coeff * sqrt(dt)) and cumulative sum.
    """
    increments = rng.normal(scale=rrw_coeff * np.sqrt(dt), size=size)
    return np.cumsum(increments)


def gauss_markov_process(sigma: float, tau: float, dt: float, size: int, rng: np.random.Generator) -> np.ndarray:
    """
    First-order Gauss-Markov: x[k+1] = alpha*x[k] + w[k] where alpha = exp(-dt/tau)
    w[k] is zero-mean Gaussian with variance = sigma^2 * (1 - alpha^2)
    This yields a stationary process with std approx sigma.
    """
    alpha = np.exp(-dt / tau) if tau > 0 else 0.0
    var_w = sigma * sigma * (1.0 - alpha * alpha)
    x = np.zeros(size)
    for k in range(1, size):
        x[k] = alpha * x[k - 1] + rng.normal(scale=np.sqrt(var_w))
    return x
