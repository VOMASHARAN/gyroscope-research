"""Visualization utilities: time-series and correlation matrix plotting."""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

from config import *
from data_utils import ensure_project_dirs


def plot_time_series(df: pd.DataFrame, axis: str, outpath: str, num_to_plot: int = 8):
    ensure_project_dirs()
    cols = [c for c in df.columns if c.startswith('gyro') and c.endswith(f'_{axis}')]
    plt.figure(figsize=(10, 6))
    for c in cols[:num_to_plot]:
        plt.plot(df['timestamp'], df[c], label=c)
    plt.xlabel('Time (s)')
    plt.ylabel(f'Gyro {axis.upper()} (arb)')
    plt.legend(loc='upper right', fontsize='small')
    plt.title(f'{axis.upper()} axis readings')
    plt.grid(True)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath)
    plt.close()


def plot_corr_matrix(mat: np.ndarray, outpath: str, title: str = ''):
    ensure_project_dirs()
    plt.figure(figsize=(6, 5))
    im = plt.imshow(mat, vmin=-1, vmax=1, cmap='coolwarm')
    plt.colorbar(im)
    plt.title(title)
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath)
    plt.close()


def plot_correlation_distribution(correlations: np.ndarray, outpath: str):
    ensure_project_dirs()
    plt.figure(figsize=(6, 4))
    plt.hist(correlations, bins=20, edgecolor='black')
    plt.axvline(x=0.40, color='r', linestyle='--', label='target=0.40')
    plt.axvline(x=0.55, color='orange', linestyle='--', label='preferred=0.55')
    plt.axvline(x=0.70, color='m', linestyle='--', label='absolute=0.70')
    plt.legend()
    plt.title('Distribution of pairwise correlations')
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    plt.savefig(outpath)
    plt.close()


def plot_fusion_vs_baseline(fused_df: pd.DataFrame, baseline_df: pd.DataFrame, outdir: str = 'plots/fusion'):
    ensure_project_dirs()
    os.makedirs(outdir, exist_ok=True)
    for axis in ('x', 'y', 'z'):
        plt.figure(figsize=(10, 5))
        plt.plot(fused_df['timestamp'], fused_df[f'fused_{axis}'], label='Fused', linewidth=1.6)
        plt.plot(baseline_df['timestamp'], baseline_df[f'baseline_{axis}'], label='Baseline', linewidth=1.2, alpha=0.9)
        plt.xlabel('Time (s)')
        plt.ylabel(f'Angular rate {axis.upper()}')
        plt.title(f'Fused vs Baseline - {axis.upper()} axis')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, f'fused_vs_baseline_{axis}.png'))
        plt.close()


def plot_fusion_error(fused_df: pd.DataFrame, baseline_df: pd.DataFrame, outdir: str = 'plots/fusion'):
    ensure_project_dirs()
    os.makedirs(outdir, exist_ok=True)
    for axis in ('x', 'y', 'z'):
        error = fused_df[f'fused_{axis}'].to_numpy() - baseline_df[f'baseline_{axis}'].to_numpy()
        plt.figure(figsize=(10, 4))
        plt.plot(fused_df['timestamp'], error, color='tab:red')
        plt.axhline(0.0, color='black', linewidth=0.8, linestyle='--')
        plt.xlabel('Time (s)')
        plt.ylabel(f'Error ({axis.upper()})')
        plt.title(f'Fusion error - {axis.upper()} axis')
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(os.path.join(outdir, f'fused_error_{axis}.png'))
        plt.close()


if __name__ == "__main__":
    print("Visualization helpers; import and use from main.py or analysis scripts.")
