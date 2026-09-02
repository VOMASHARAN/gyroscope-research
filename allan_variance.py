"""Allan variance / Allan deviation analysis for gyro data.
"""
import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt

from config import *
from data_utils import ensure_project_dirs


def allan_deviation(data: np.ndarray, sample_rate: float) -> (np.ndarray, np.ndarray):
    """Compute Allan deviation for a 1D time series.
    Returns (taus, adev)
    """
    n = len(data)
    if n < 2:
        return np.array([]), np.array([])
    dt = 1.0 / sample_rate
    max_m = int(np.floor(n / 2))
    ms = np.unique(np.logspace(0, np.log10(max_m), num=50, dtype=int))
    taus = ms * dt
    adev = []
    for m in ms:
        # compute cluster averages
        if m == 0:
            adev.append(np.nan)
            continue
        k = int(np.floor(n / m))
        if k < 2:
            adev.append(np.nan)
            continue
        reshaped = data[:k * m].reshape((k, m))
        means = reshaped.mean(axis=1)
        diff = np.diff(means)
        adev.append(np.sqrt(0.5 * np.mean(diff * diff)))
    return taus, np.array(adev)


def plot_allan_for_series(series: np.ndarray, sample_rate: float, outpath: str, label: str = ""):
    ensure_project_dirs()
    taus, adev = allan_deviation(series, sample_rate)
    plt.figure(figsize=(6, 4))
    plt.loglog(taus, adev, marker='o')
    plt.xlabel('Tau (s)')
    plt.ylabel('Allan deviation')
    plt.title(f'Allan deviation {label}')
    plt.grid(True, which='both')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath)
    plt.close()


if __name__ == "__main__":
    print("This module provides functions to compute and plot Allan deviation. Run from other scripts.")
