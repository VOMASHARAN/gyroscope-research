"""Main entry point to run the full simulation, analysis, and plotting pipeline."""
import os
import pandas as pd
import numpy as np

from config import *
from data_utils import ensure_project_dirs, save_text
from gyro_simulator import GyroscopeSimulator
from baseline_gyro_simulator import BaselineGyroSimulator
from algorithms.fusion import fuse_gyros, compute_error_metrics, save_fusion_summary
from algorithms.ekf import run_basic_ekf, compute_ekf_metrics, save_ekf_summary
import correlation_analysis as ca
import visualization as viz
from allan_variance import plot_allan_for_series


def find_suitable_common_component_strength(sim: GyroscopeSimulator, target: float = TARGET_CORRELATION, tol: float = TUNING_TOLERANCE, max_iters: int = TUNING_MAX_ITERS):
    """Simple binary-search-like tuning over a scaling factor to try to reach target average correlation.
    This does not force the matrix, it only adjusts common_strength and regenerates signals.
    """
    low, high = 0.0, 2.0
    best = sim.common_strength
    best_diff = float('inf')

    for it in range(max_iters):
        mid = (low + high) / 2.0
        sim.common_strength = mid
        df = sim.generate_all()
        # compute average correlation quickly for X axis (proxy) then overall
        pairs = []
        for axis in ("x","y","z"):
            pw = ca.compute_pairwise(df, axis)
            pairs.append(pw)
        all_pw = pd.concat(pairs, ignore_index=True)
        avg = all_pw['correlation'].mean()
        diff = abs(avg - target)
        if diff < best_diff:
            best = mid
            best_diff = diff
        # narrow search
        if avg < target:
            low = mid
        else:
            high = mid
        if diff <= tol:
            break
    sim.common_strength = best
    return best


def main():
    ensure_project_dirs()
    sim = GyroscopeSimulator()

    if TUNING_ENABLED:
        print("Tuning common component strength to approach target correlation (this may take a few iterations)...")
        chosen = find_suitable_common_component_strength(sim)
        print(f"Selected common_strength={chosen:.4f}")

    common_signal = sim.generate_common_component()
    df = sim.generate_all(common_signal)
    sim.save_raw(df)
    sim.save_individual_sensor_datasets(df)

    baseline = BaselineGyroSimulator()
    baseline_df = baseline.generate_all(common_signal)
    baseline.save_raw(baseline_df)
    baseline_df.to_excel(os.path.join('data', 'baseline', 'baseline.xlsx'), index=False)
    baseline_df.to_excel(os.path.join('data', 'baseline.xlsx'), index=False)

    # run correlation analysis
    ca.run_full_analysis(RAW_CSV, BASELINE_RAW_CSV)

    # plots
    viz.plot_time_series(df, 'x', PLOT_GYRO_X)
    viz.plot_time_series(df, 'y', PLOT_GYRO_Y)
    viz.plot_time_series(df, 'z', PLOT_GYRO_Z)

    # correlation matrices load and plot
    mat_x = pd.read_csv(CORR_MATRIX_X).values
    mat_y = pd.read_csv(CORR_MATRIX_Y).values
    mat_z = pd.read_csv(CORR_MATRIX_Z).values
    viz.plot_corr_matrix(mat_x, PLOT_CORR_X, title='X axis correlation matrix')
    viz.plot_corr_matrix(mat_y, PLOT_CORR_Y, title='Y axis correlation matrix')
    viz.plot_corr_matrix(mat_z, PLOT_CORR_Z, title='Z axis correlation matrix')

    # distribution
    all_pw = pd.read_csv(PAIRWISE_CSV)
    viz.plot_correlation_distribution(all_pw['correlation'].values, PLOT_CORR_DIST)

    # basic arithmetic mean fusion
    gyro_frames = {}
    for g in range(1, NUM_GYROS + 1):
        gyro_frames[g] = pd.read_csv(os.path.join(DATASET_OUTPUT_DIR, f'gyro_{g}.csv'))
    fused_df = fuse_gyros(gyro_frames)
    fused_df.to_excel(FUSED_OUTPUT, index=False)

    metrics_df = compute_error_metrics(fused_df, baseline_df)
    metrics_df.to_csv(FUSION_METRICS_CSV, index=False)
    save_fusion_summary(metrics_df, FUSION_SUMMARY)

    viz.plot_fusion_vs_baseline(fused_df, baseline_df)
    viz.plot_fusion_error(fused_df, baseline_df)

    # Basic EKF on fused rate estimates
    ekf_df = run_basic_ekf(fused_df, dt=1.0 / SAMPLE_RATE)
    ekf_df.to_excel(EKF_OUTPUT, index=False)
    ekf_metrics_df = compute_ekf_metrics(ekf_df, baseline_df)
    ekf_metrics_df.to_csv(EKF_METRICS_CSV, index=False)
    save_ekf_summary(ekf_metrics_df, EKF_SUMMARY)

    # Allan deviation for gyro1_x/y/z as examples
    df_raw = pd.read_csv(RAW_CSV)
    plot_allan_for_series(df_raw['gyro1_x'].values, SAMPLE_RATE, ALLAN_PLOT_FOLDER + 'gyro1_x_allan.png', label='gyro1_x')
    plot_allan_for_series(df_raw['gyro1_y'].values, SAMPLE_RATE, ALLAN_PLOT_FOLDER + 'gyro1_y_allan.png', label='gyro1_y')
    plot_allan_for_series(df_raw['gyro1_z'].values, SAMPLE_RATE, ALLAN_PLOT_FOLDER + 'gyro1_z_allan.png', label='gyro1_z')

    print('All outputs saved under gyroscope_2/')


if __name__ == "__main__":
    main()
