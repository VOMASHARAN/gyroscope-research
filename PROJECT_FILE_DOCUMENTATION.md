# Gyroscope Project - File Documentation

## 1. Project Overview

This project is a standalone Python research pipeline for simulating an eight-gyro IMU-style sensor array, generating correlated sensor noise, saving synchronized datasets, comparing with a baseline, and running basic fusion and filtering analyses. The project contains both an offline simulation pipeline and a verified live 9-port TCP stream layer for ports 5001-5009.

The current architecture is not ROS-based. It is a Python research project designed to generate realistic gyroscope signals, expose them as live localhost streams, verify the ports, and support notebook-based analysis.

Current architecture summary:

Common True Signal
       -
8 Sensor Models
       -
8 Continuous Live Streams
       -
Ports 5001-5009
       -
Notebook Connection + Live Collection
       -
Synchronization Check
       -
Correlation / Fusion / Baseline Comparison

Current project state:
- Completed: offline generation, baseline reference, basic fusion, EKF filtering, project documentation, live 8-port TCP stream layer, live baseline stream on port 5009.
- Currently implemented: standalone Python research code with a verified live streaming layer.
- Verified: all nine ports are listening, responding, and producing timestamped X/Y/Z samples.
- Implemented: scalar linear-Gaussian IMM, single-target PMA association, and live Allan/ARW/RRW/accuracy-latency notebook stages. Full classical JPDA remains NOT IMPLEMENTED.

## 2. Project Architecture

The project is a standalone Python design, not a ROS node architecture.

### Architecture map

Common True Signal
       -
8 Sensor Models with per-sensor noise realizations
       -
8 synchronized time-series datasets
       -
8 gyro streams on ports 5001-5008 plus baseline on port 5009
       -
Baseline reference stream on port 5009
       -
Notebook / client connection and live sample collection
       -
Timestamp synchronization validation
       -
Correlation analysis
       -
Basic arithmetic-mean fusion
       -
IMM + single-target PMA association
       -
Basic EKF filtering + baseline comparison

### Stage status

- COMPLETED: common signal generation, 8-gyro simulator, baseline simulation, offline data export, correlation analysis, arithmetic fusion, EKF pipeline, live 8-port streams, baseline stream on 5009, live port verification.
- CURRENTLY IMPLEMENTED: standalone Python research code and live socket stream layer.
- VERIFIED: 8 gyros generated, baseline stream active, ports 5001-5009 responding, notebook receives live samples, timestamped X/Y/Z payloads are present.
- COMPLETED: the notebook now runs live receive, timestamp alignment, validation, correlation, equal-weight fusion, baseline comparison, and EKF processing.
- PASS: IMM, PMA association, and live Allan deviation/ARW/RRW extraction
  stages (with honest status reporting).
- NOT IMPLEMENTED: full classical JPDA multi-target joint-event association.
- Executed live run (1,000 samples): Allan deviation PASS; ARW and RRW
  extraction executed but were `SLOPE_NOT_CONCLUSIVE` for the selected live
  record, so no scientific coefficients are claimed.

## 3. Complete File / Folder Inventory

### Root-level project files

| Path | Type | Purpose | Status |
|---|---|---|---|
| README.md | Documentation | project overview and quickstart | Active |
| main.py | Python | runs the end-to-end simulation pipeline | Active |
| config.py | Python | central constants for sample rate, duration, output paths, and thresholds | Active |
| data_utils.py | Python | creates folders and saves text outputs | Active |
| gyro_simulator.py | Python | generates the shared true signal and the 8 synchronized gyro streams | Active |
| baseline_gyro_simulator.py | Python | creates the baseline reference using the same underlying motion | Active |
| noise_models.py | Python | implements white noise, ARW, RRW, and Gauss-Markov noise | Active |
| correlation_analysis.py | Python | computes pairwise correlation and validation summaries | Active |
| visualization.py | Python | plots time series, correlation matrices, and fusion comparison graphs | Active |
| allan_variance.py | Python | computes Allan deviation for sample signals | Active |
| stream_server.py | Python | starts the verified 8-port live TCP broadcast layer | Active |
| stream_client.py | Python | reads live gyro samples from 5001-5009 and assembles a DataFrame | Active |
| check_ports.py | Python | verifies that each port is listening and responding | Active |
| requirements.txt | Setup | dependency list for the project | Active |
| PROJECT_FILE_DOCUMENTATION.md | Documentation | project description, architecture, and current status | Active |
| .venv | Environment | local Python environment | Active |

### Algorithms package

| Path | Type | Purpose | Status |
|---|---|---|---|
| algorithms/__init__.py | Python | package marker | Active |
| algorithms/fusion.py | Python | arithmetic-mean fusion and error metrics | Active |
| algorithms/ekf.py | Python | basic per-axis EKF implementation | Active |
| algorithms/imm.py | Python | linear-Gaussian scalar IMM with distinct process-noise models | PASS |
| algorithms/association.py | Python | gated single-target PMA/JPDA-like association | PASS; not full JPDA |

#### IMM and PMA formulation

`algorithms/imm.py` uses scalar random-walk models
`x_k = x_(k-1) + w_j`, with model-specific process variances `q_j`, and
measurement `z_k = x_k + v`.  At each sample it computes
`c_j = sum_i mu_i p_ij`, interaction weights
`mu_(i|j) = mu_i p_ij / c_j`, mixed means/covariances, Kalman
predict/update likelihoods, normalized model probabilities, and the
probability-weighted estimate/covariance.

`algorithms/association.py` is PMA: each scalar sensor measurement is gated by
`(z - x)^2 / (P + R)`, then weighted by its Gaussian innovation likelihood and
sensor prior.  Weights and a missed-detection hypothesis (using
`P_D` and constant clutter density) are normalized before producing a weighted
measurement and Kalman update.  It is intentionally **not full classical
JPDA**: there is no multi-target joint-event enumeration, track-existence
logic, or spatially varying clutter model.

### Data folders and outputs

| Path | Type | Purpose | Status |
|---|---|---|---|
| data/raw | Folder | raw generated output | Active |
| data/organized | Folder | per-gyro CSV/XLSX exports for G1-G8 | Active |
| data/baseline | Folder | baseline output and baseline metrics | Active |
| data/baseline.xlsx | Excel | baseline reference dataset | Active |
| data/fused_output.xlsx | Excel | arithmetic-mean fused output | Active |
| data/ekf_output.xlsx | Excel | EKF filtered output | Active |
| results | Folder | summaries and metrics text files | Active |
| plots | Folder | generated plots for signals and metrics | Active |

### Notebook

| Path | Type | Purpose | Status |
|---|---|---|---|
| notebooks/gyro_experiment.ipynb | Notebook | offline analysis and live port connection/data collection for G1-G8 | Active and verified |

## 4. File-by-File Explanation

### main.py

- Function names: find_suitable_common_component_strength, main
- What it does:
  - ensures the project folders exist
  - initializes the gyroscope simulator
  - optionally tunes common-strength toward a target correlation
  - generates all eight gyro streams and baseline data
  - saves CSV and Excel outputs
  - runs correlation analysis, fusion, and EKF steps
  - saves plot and summary artifacts
- Inputs: config values from config.py
- Outputs: generated datasets and summary artifacts under data/, results/, and plots/
- Usage: active
- Architecture: standalone Python research pipeline, not ROS

### config.py

- Constant names: NUM_GYROS, SAMPLE_RATE, DURATION, RANDOM_SEED, TARGET_CORRELATION, and others
- What it does: defines simulation parameters, output paths, tuning thresholds, and accepted validation settings
- Inputs: none at runtime; values are imported by modules
- Outputs: configuration values used across the project
- Usage: active
- Architecture: standalone Python

### data_utils.py

- Functions: ensure_dirs, ensure_project_dirs, save_text, clamp
- What it does: creates required folders and writes summary files
- Inputs: paths and text payloads
- Outputs: directories and text outputs
- Usage: active
- Architecture: standalone Python

### gyro_simulator.py

- Class: GyroscopeSimulator
- Methods: __post_init__, time_vector, generate_common_component, generate_all, save_raw, save_individual_sensor_datasets
- What it does:
  - builds the common underlying true motion signal
  - generates eight synchronized gyro streams
  - adds white noise, ARW, RRW, and Gauss-Markov components
  - saves organized outputs for each gyro
- Inputs: simulation configuration and random seed
- Outputs: synchronized gyro datasets for G1-G8
- Usage: active
- Architecture: standalone Python model

### baseline_gyro_simulator.py

- Class: BaselineGyroSimulator
- Methods: __init__, generate_all, save_raw
- What it does:
  - creates a baseline reference stream using the same common signal
  - saves baseline outputs for comparison
- Inputs: same time base and common motion signal as the sensor array
- Outputs: baseline CSV/Excel data
- Usage: active
- Architecture: standalone Python model

### noise_models.py

- Functions: white_noise, arw_process, rrw_process, gauss_markov_process
- What it does: produces the stochastic noise models used by the sensors
- Inputs: std. deviation, dt, vector length, RNG handle
- Outputs: noise arrays added to the simulation
- Usage: active
- Architecture: standalone Python

### correlation_analysis.py

- Functions: compute_pairwise, correlation_matrix, compute_stats, validate_correlations, compute_baseline_correlations, run_full_analysis
- What it does:
  - computes pairwise Pearson correlations for X/Y/Z signals
  - builds correlation matrices and summaries
  - evaluates baseline vs gyro relationships
- Inputs: gyro data frames and optional baseline data
- Outputs: CSV summaries and correlation matrices
- Usage: active
- Architecture: standalone Python

### visualization.py

- Functions: plot_time_series, plot_corr_matrix, plot_correlation_distribution, plot_fusion_vs_baseline, plot_fusion_error
- What it does: generates time-series and error plots for the research pipeline
- Inputs: DataFrames and output paths
- Outputs: plot image files
- Usage: active
- Architecture: standalone Python

### allan_variance.py

- Functions: allan_deviation, plot_allan_for_series
- What it does: computes Allan deviation for example gyro signals and saves plots
- Inputs: signal arrays and sample rate
- Outputs: Allan deviation plots
- Usage: active
- Architecture: standalone Python

### algorithms/fusion.py

- Functions: fuse_gyros, compute_error_metrics, save_fusion_summary
- What it does:
  - combines the eight synchronized gyro streams by arithmetic mean
  - computes error metrics versus baseline
  - saves fusion summary metrics
- Inputs: per-gyro DataFrames
- Outputs: fused DataFrame and metrics summary
- Usage: active
- Architecture: standalone Python

### algorithms/ekf.py

- Classes: BasicAxisEKF
- Functions: run_basic_ekf, compute_ekf_metrics, save_ekf_summary
- What it does: runs a lightweight EKF-style per-axis smoothing on the fused output and saves metrics
- Inputs: fused DataFrame and dt
- Outputs: filtered DataFrame and EKF metrics
- Usage: active
- Architecture: standalone Python

### stream_server.py

- Class: GyroStreamServer
- Methods: __init__, _gyro_rows_for_port, _serve_port, start, stop
- What it does:
  - reuses the same synchronized simulator output
  - exposes G1-G8 on ports 5001-5008 plus baseline on port 5009 over localhost TCP
  - sends one timestamped X/Y/Z sample at a time
- Inputs: host, sample rate, duration
- Outputs: live stream data on 5001-5009
- Usage: active and verified
- Architecture: standalone Python socket layer added on top of the simulator, not ROS

### stream_client.py

- Class: GyroStreamClient
- Functions: connect_all_ports, collect_live_stream_data
- What it does:
  - connects to the live gyroscope ports
  - reads sample payloads
  - packages them into a combined DataFrame with timestamp and axis columns
- Inputs: port list and host
- Outputs: live DataFrame from G1-G8
- Usage: active and verified
- Architecture: standalone Python client layer

### check_ports.py

- Function: check_port
- What it does:
  - attempts to open a TCP connection to a port
  - confirms the port is listening and responding
- Inputs: port number and host
- Outputs: PASS/FAIL status for each port
- Usage: active and verified
- Architecture: standalone Python port verification utility

### notebooks/gyro_experiment.ipynb

- Purpose: live 9-port experiment; offline files are reference-only
- Data sources:
  - offline CSV/Excel files checked as reference-only
  - live socket data from ports 5001-5009
- Ports used: 5001-5009
- Analysis performed: live correlation heatmaps, basic fusion, IMM independent check, PMA association, IMM+PMA processing, EKF, Allan deviation, ARW/RRW extraction, accuracy, latency, and accuracy-vs-latency plots
- Offline files are reference-only; no offline fallback is used.
- Completion status: live receive, alignment, correlation, fusion, IMM, PMA, EKF, Allan deviation, ARW/RRW handling, accuracy, and latency stages are implemented. Full classical JPDA is NOT IMPLEMENTED.

### configuration/setup files

- requirements.txt: dependency list for Python scientific packages and OpenPyXL
- .venv: local virtual environment used for running the project

### data files

- data/raw/gyro_readings.csv: generated raw data for the full 8-gyro dataset
- data/organized/gyro_1.csv ... gyro_8.csv: per-gyro CSV files
- data/organized/gyro_1.xlsx ... gyro_8.xlsx: per-gyro Excel files
- data/baseline/baseline_gyro_readings.csv: baseline output generated with the shared true signal
- data/baseline.xlsx: baseline Excel export
- data/fused_output.xlsx: arithmetic mean fusion output
- data/ekf_output.xlsx: EKF output
- results/*.txt: summary metrics and validation text
- plots/*.png: generated plots
- data/results/live_alignment_summary.csv, live_correlation_matrix_*.csv:
  artifacts from the current aligned live batch
- data/results/live_imm_association.csv, live_ekf_processed.csv,
  live_accuracy_metrics.csv, live_latency_*.csv:
  processed live estimates, accuracy, and `perf_counter` latency
- data/results/live_allan_deviation.csv/.png and
  live_accuracy_vs_latency.csv/.png: generated live research plots
- data/results/live_raw_streams.png, live_correlation_heatmaps.png,
  live_processed_estimates.png, and live_processed_errors.png: live visual
  diagnostics

## 5. Distinguish Old ROS Code from New Python Research Code

### Existing / Legacy ROS Architecture

No ROS architecture was found in the current project folder.

- No launch files were found.
- No ROS package metadata was found.
- No rospy or roscpp nodes were present.
- No Publisher/Subscriber implementation was found.
- No ROS topics or messages were present.

Conclusion: there is no active ROS code retained in this project. The project is not a ROS package and is not using ROS runtime features.

### New Standalone Python Research Architecture

This is the active architecture:
- shared common-signal generation
- sensor/noise models
- eight synchronized sensor streams
- local TCP socket layer on ports 5001-5009
- notebook live-client collection
- baseline comparison and fusion logic
- EKF filtering and metrics

This is the live, active architecture currently being used. The older ROS-related structures are not present in this folder.

## 6. Potentially Unused / Duplicate Files

- __pycache__: generated cache; not source logic
- data/ generated artifacts: useful for analysis, but not the active logic
- Excel and CSV duplicates: both formats are retained for convenience and to support notebook analysis
- results summary files: generated from the same underlying pipeline; useful for reference but not the core logic
- notebooks/gyro_experiment.ipynb: active and useful, but it is not the source of the actual sensor generation

No file is deleted as part of this review, per requirement.

## 7. How to Run Everything

### Terminal 1 - Start simulator / live stream server

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python stream_server.py
```

This starts the live localhost stream server and exposes G1-G8 on ports 5001-5008 plus the baseline stream on port 5009.

### Terminal 2 - Verify ports

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python check_ports.py
```

Expected result: all ports 5001-5009 report LISTENING and PASS.

### Terminal 3 - Start notebook

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\jupyter notebook .\notebooks\gyro_experiment.ipynb
```

This notebook connects to the live ports and runs the experiment from live samples. Offline CSV files are not used by correlation, fusion, baseline comparison, or EKF processing.

### Optional - Offline pipeline

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python main.py
```

This runs the offline simulation and analysis workflow.

## 8. Final Verification Report

```text
8 Gyro Generation:              PASS
Common True Signal:             PASS
Individual Sensor Models:       PASS
ARW:                            UNKNOWN
RRW:                            UNKNOWN
Markovian Noise:                PASS

Port 5001 / Gyro 1:             PASS
Port 5002 / Gyro 2:             PASS
Port 5003 / Gyro 3:             PASS
Port 5004 / Gyro 4:             PASS
Port 5005 / Gyro 5:             PASS
Port 5006 / Gyro 6:             PASS
Port 5007 / Gyro 7:             PASS
Port 5008 / Gyro 8:             PASS
Port 5009 / Baseline:           PASS

Notebook Created:               YES
Notebook Connects to G1-G8:     PASS
Notebook Connects to Baseline:  PASS
Timestamp Synchronization:      PASS
Baseline Simulator:             YES
Baseline Port 5009:             PASS

Correlation Analysis:           YES
Basic Fusion:                   PASS
IMM (linear Gaussian):          PASS
PMA association:                PASS (single target; not full JPDA)
Live Allan deviation:           PASS
Live ARW/RRW extraction:        UNKNOWN (slope not conclusive)
Baseline Comparison:            YES
```

## 9. Final Verification Summary

1. What files currently exist.
   - The project contains a standalone Python gyroscope research pipeline, generated data artifacts, a baseline simulator, and a verified live TCP 8-port stream layer.

2. What each important file does.
   - The core simulator is in gyro_simulator.py; the live stream is in stream_server.py; the live client is in stream_client.py; the port verifier is in check_ports.py; the notebook is in notebooks/gyro_experiment.ipynb; the analysis is in correlation_analysis.py and algorithms/*.

3. Which files are actually being used.
   - The active runtime files are: gyro_simulator.py, stream_server.py, stream_client.py, check_ports.py, main.py, config.py, data_utils.py, correlation_analysis.py, visualization.py, algorithms/fusion.py, algorithms/ekf.py, and notebooks/gyro_experiment.ipynb.

4. Whether all eight ports are really working.
   - Yes. Each of the eight localhost ports 5001-5008 was verified live and is responding.

5. Whether the notebook is really connected to all eight ports.
   - Yes. The notebook/client workflow successfully connected to all eight ports and read live sample batches. The baseline port 5009 is also connected and producing data.

6. Whether the streams are synchronized.
   - Yes, at the sample level. The stream server uses the same underlying simulation time base and emits timestamped samples; the client combines them by timestamp into a single DataFrame.

7. Whether the baseline exists.
   - Yes, the baseline simulator exists in baseline_gyro_simulator.py and is used in the offline pipeline. The live baseline port 5009 is now active and verified.

8. What is completed.
   - Offline simulation, baseline comparison, fusion, EKF, live 8-port streaming, baseline port 5009, live connection and verification, and full project documentation.

9. What remains to be built.
   - Full classical JPDA remains future work. Implemented PMA is single-target and has no clutter spatial model or multi-target joint-event enumeration.

10. What the exact next development step should be.
   - IMM and PMA are implemented and exercised by focused smoke tests; the notebook runs them on current aligned live data.

# CURRENT IMPLEMENTATION STATUS

8 Gyro Generation:              PASS
Common True Signal:             PASS
Individual Sensor Models:       PASS
ARW:                            UNKNOWN
RRW:                            UNKNOWN
Markovian Noise:                PASS

Port 5001 / Gyro 1:             PASS
Port 5002 / Gyro 2:             PASS
Port 5003 / Gyro 3:             PASS
Port 5004 / Gyro 4:             PASS
Port 5005 / Gyro 5:             PASS
Port 5006 / Gyro 6:             PASS
Port 5007 / Gyro 7:             PASS
Port 5008 / Gyro 8:             PASS
Port 5009 / Baseline:           PASS

Notebook Created:               YES
Notebook Connects to G1-G8:     PASS
Notebook Connects to Baseline:  PASS
Timestamp Synchronization:      PASS
Baseline Simulator:             YES
Baseline Port 5009:             PASS

Correlation Analysis:           YES
Basic Fusion:                   PASS
IMM (linear Gaussian):          PASS
PMA association:                PASS (single target; not full JPDA)
Live Allan deviation:           PASS
Live ARW/RRW extraction:        UNKNOWN (slope not conclusive)
Baseline Comparison:            YES
