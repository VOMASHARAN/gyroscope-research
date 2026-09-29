import numpy as np

from algorithms.adaptive_kf import run_adaptive_kf
from algorithms.central_kf import run_central_kf
from algorithms.covariance_intersection import covariance_intersection
from algorithms.dataset import ExperimentDataset, apply_degradation, validate_dataset
from algorithms.evaluation import correlation_matrices, error_metrics, latency_summary
from algorithms.federated_kf import run_federated_kf
from algorithms.inverse_covariance import inverse_covariance_fusion
from algorithms.rts_smoother import rts_smooth


def synthetic_data(samples=32, sensors=8):
    rng = np.random.default_rng(12)
    timestamps = np.arange(samples, dtype=float) * 0.01
    truth = np.column_stack((np.sin(timestamps), np.cos(timestamps), timestamps))
    values = truth[:, None, :] + rng.normal(0, 0.02, (samples, sensors, 3))
    return timestamps, truth, values


def test_dataset_and_degradation_contract():
    timestamps, truth, values = synthetic_data()
    dataset = ExperimentDataset(timestamps, values, truth_data=truth, sample_rate=100.0)
    assert validate_dataset(dataset)["status"] == "PASS"
    degraded = apply_degradation(dataset, {"sensor": 2, "bias": [1.0, 0.0, 0.0]})
    assert degraded.gyro_data[0, 2, 0] > dataset.gyro_data[0, 2, 0]


def test_inverse_covariance_weights_and_mean_limit():
    _, _, values = synthetic_data()
    variances = np.full((8, 3), 0.02**2)
    estimate, covariance, weights = inverse_covariance_fusion(values, variances)
    assert estimate.shape == (len(values), 3)
    assert covariance.shape == (len(values), 3)
    assert np.allclose(weights.sum(axis=1), 1.0)
    assert np.allclose(weights[:, 0], 1 / 8)


def test_filters_ci_rts_and_covariance_validity():
    timestamps, _, values = synthetic_data()
    variances = np.full((8, 3), 0.02**2)
    central = run_central_kf(values, timestamps, variances)
    federated = run_federated_kf(values, timestamps, variances)
    adaptive = run_adaptive_kf(values.mean(axis=1), timestamps)
    smoothed = rts_smooth(central["estimate"], central["covariance"], timestamps)
    estimate, covariance, weight = covariance_intersection(
        central["estimate"][-1], central["covariance"][-1],
        federated["estimate"][-1], federated["covariance"][-1],
    )
    assert central["estimate"].shape == federated["estimate"].shape == (len(values), 3)
    assert np.isfinite(adaptive["estimate"]).all()
    assert np.isfinite(smoothed["estimate"]).all()
    assert np.allclose(central["covariance"], np.swapaxes(central["covariance"], 1, 2))
    assert np.all(np.linalg.eigvalsh(central["covariance"]) >= -1e-10)
    assert np.isfinite(estimate).all() and np.isfinite(covariance).all()
    assert 0.0 <= weight <= 1.0


def test_correlation_metrics_and_latency():
    timestamps, truth, values = synthetic_data()
    matrices = correlation_matrices(values, truth)
    assert set(matrices) == {"x", "y", "z"}
    assert all(matrix.shape == (8, 8) for matrix in matrices.values())
    metrics = error_metrics(values.mean(axis=1), truth, sample_rate=100.0)
    assert metrics["rmse"] >= 0.0
    latency = latency_summary(lambda: np.sum(values), repeats=3)
    assert latency["p95_ms"] >= latency["min_ms"]
    assert latency["p99_ms"] >= latency["min_ms"]
