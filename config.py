"""Configuration for the 8-gyroscope simulation project.
All important simulation parameters are centralized here so they can be tuned easily.
"""
from typing import Final

NUM_GYROS: Final = 8
SAMPLE_RATE: Final = 200.0        # Hz
DURATION: Final = 60.0           # seconds

WHITE_NOISE_STD: Final = 0.01    # std dev of white noise (rad/s)
ARW_COEFFICIENT: Final = 0.005   # ARW coefficient (rad/s/sqrt(Hz)) - interpretation in README
RRW_COEFFICIENT: Final = 1e-5    # RRW coefficient (rad/s^2 / sqrt(Hz))

MARKOV_STD: Final = 0.02         # std dev for Markov process
MARKOV_TIME_CONSTANT: Final = 5.0 # seconds

COMMON_COMPONENT_STRENGTH: Final = 0.037  # scale applied to the common component before mixing
BASELINE_NOISE_SCALE: Final = 0.25
BASELINE_COMMON_SCALE: Final = 1.20

RANDOM_SEED: Final = 42

# Correlation acceptance targets
TARGET_CORRELATION: Final = 0.40
PREFERRED_CORRELATION_MAX: Final = 0.55
ABSOLUTE_CORRELATION_MAX: Final = 0.70

# Tuning settings
TUNING_ENABLED: Final = True
TUNING_TOLERANCE: Final = 0.02  # acceptable +/- around TARGET_CORRELATION
TUNING_MAX_ITERS: Final = 12

# Output paths (relative to project root)
RAW_CSV: Final = "data/raw/gyro_readings.csv"
BASELINE_RAW_CSV: Final = "data/baseline/baseline_gyro_readings.csv"
PAIRWISE_CSV: Final = "data/results/pairwise_correlations.csv"
CORR_MATRIX_X: Final = "data/results/correlation_matrix_x.csv"
CORR_MATRIX_Y: Final = "data/results/correlation_matrix_y.csv"
CORR_MATRIX_Z: Final = "data/results/correlation_matrix_z.csv"
BASELINE_CORR_CSV: Final = "data/results/baseline_correlations.csv"
RESULTS_SUMMARY: Final = "results/final_summary.txt"
DATASET_OUTPUT_DIR: Final = "data/organized"
FUSED_OUTPUT: Final = "data/fused_output.xlsx"
EKF_OUTPUT: Final = "data/ekf_output.xlsx"
FUSION_METRICS_CSV: Final = "data/results/fusion_metrics.csv"
EKF_METRICS_CSV: Final = "data/results/ekf_metrics.csv"
FUSION_SUMMARY: Final = "results/fusion_summary.txt"
EKF_SUMMARY: Final = "results/ekf_summary.txt"

# Plot paths
PLOT_GYRO_X: Final = "plots/gyro_x_readings.png"
PLOT_GYRO_Y: Final = "plots/gyro_y_readings.png"
PLOT_GYRO_Z: Final = "plots/gyro_z_readings.png"
PLOT_CORR_X: Final = "plots/correlation_matrix_x.png"
PLOT_CORR_Y: Final = "plots/correlation_matrix_y.png"
PLOT_CORR_Z: Final = "plots/correlation_matrix_z.png"
PLOT_CORR_DIST: Final = "plots/correlation_distribution.png"

# Allan deviation plot folder
ALLAN_PLOT_FOLDER: Final = "plots/allan_deviation/"
