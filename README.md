# gyroscope_2

8-MEMS gyroscope simulation, synchronized signal generation, correlation analysis, live port streaming, and research-grade filtering.

Overview
--------
This project simulates an array of 8 MEMS gyroscopes and generates stochastic noise components:
- White noise
- Angle Random Walk (ARW)
- Rate Random Walk (RRW)
- First-order Gauss-Markov noise

A configurable shared component introduces controlled correlation between sensors. The project also includes:
- offline CSV/Excel data export
- per-gyro dataset generation
- baseline comparison
- arithmetic-mean fusion
- basic EKF filtering
- a live TCP stream layer exposing G1-G8 on ports 5001-5008 and the baseline on port 5009

The live stream layer reuses the same underlying simulator output so the generated sensors remain synchronized and the notebook can connect to actual localhost data streams.

The notebook has two deliberately separate paths:
- **OFFLINE REFERENCE DATA** loads saved CSV files for reproducibility checks only.
- **LIVE 9-PORT EXPERIMENT** connects to ports 5001-5009, aligns timestamps without interpolation, validates the streams, and performs correlation, equal-weight fusion, baseline comparison, and EKF processing using only the received live batch.

The live notebook now implements a scalar linear-Gaussian IMM and a documented single-target probabilistic measurement association (PMA) stage. PMA is JPDA-like, not full classical JPDA: it has no multi-target joint-event enumeration or clutter/track-existence model. Allan deviation and selectable live ARW/RRW extraction are also included; short records honestly report `INSUFFICIENT_DATA` or `SLOPE_NOT_CONCLUSIVE` rather than inventing coefficients.

Quickstart
----------
1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1    # PowerShell
# or
.\.venv\Scripts\activate.bat    # cmd.exe
```

2. Install requirements:

```powershell
pip install -r requirements.txt
```

3. Start the live 8-gyro stream server:

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python stream_server.py
```

4. Verify the ports:

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python check_ports.py
```

5. Open the notebook to connect to the live streams:

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\jupyter notebook .\notebooks\gyro_experiment.ipynb
```

6. Run the offline full pipeline if needed:

```powershell
cd "C:\Users\shara\Downloads\gyroscope_2 - Copy"
.\.venv\Scripts\python main.py
```

Files and structure
-------------------
- config.py: central parameters and output configuration
- gyro_simulator.py: generates the common signal and 8 sensor streams
- baseline_gyro_simulator.py: baseline reference signal
- noise_models.py: white noise, ARW, RRW, and Gauss-Markov implementations
- correlation_analysis.py: pairwise correlation and validation summaries
- allan_variance.py: Allan deviation computations
- visualization.py: time-series and correlation plots
- stream_server.py: live socket server for ports 5001-5009
- stream_client.py: live client utilities and DataFrame assembly for G1-G8 plus baseline
- check_ports.py: port listening verification
- algorithms/fusion.py: arithmetic-mean fusion
- algorithms/ekf.py: basic Kalman-style filtering
- algorithms/imm.py: scalar linear-Gaussian IMM (interaction, KF updates, likelihoods)
- algorithms/association.py: gated single-target PMA/JPDA-like association
- README.md, requirements.txt, PROJECT_FILE_DOCUMENTATION.md

Notes on the noise models
------------------------
- ARW is modeled by integrating scaled white noise increments; units are consistent with rad/s when coefficients are in rad/s/sqrt(Hz).
- RRW is modeled similarly but helps represent slower drift behavior.
- Gauss-Markov (first-order) is used to represent low-frequency and correlated noise behavior.

Correlation tuning
------------------
A simple tuning routine adjusts the common component strength to approach the target average correlation. The code regenerates stochastic signals and compares actual computed correlation rather than fabricating values.

Reproducibility
---------------
Set RANDOM_SEED in config.py to reproduce the same generated dataset. Changing the seed will create another randomized realization.

Running pieces independently
---------------------------
- `python gyro_simulator.py` to generate/save the base sensor data
- `python correlation_analysis.py` to compute correlations from the generated data
- `python stream_server.py` to start the live 8-port local server
- `python check_ports.py` to verify 5001-5009 are active
- `python main.py` to run the full offline simulation and analysis pipeline
- Run `notebooks/gyro_experiment.ipynb` with `stream_server.py` running for the live pipeline. Generated live CSVs, plots, metrics, and summary are written under `data/results/`.

Scientific integrity
--------------------
The program generates real stochastic signals and reports actual correlations and metrics. It does not fake outputs to force a result.

License
-------
This project is provided as-is for research and educational use.

