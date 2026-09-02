"""Correlation analysis for the simulated gyroscopes.
Computes pairwise Pearson correlations per axis, saves pairwise CSV and 8x8 matrices, and computes statistics.
"""
from typing import List, Tuple
import pandas as pd
import numpy as np
import os
from scipy.stats import pearsonr

from config import *
from data_utils import ensure_project_dirs, save_text


def compute_pairwise(df: pd.DataFrame, axis: str) -> pd.DataFrame:
    cols = [c for c in df.columns if c.startswith("gyro") and c.endswith(f"_{axis}")]
    n = len(cols)
    results = []
    for i in range(n):
        for j in range(i + 1, n):
            a = df[cols[i]].values
            b = df[cols[j]].values
            r = np.corrcoef(a, b)[0, 1]
            results.append({"axis": axis, "gyro_a": cols[i], "gyro_b": cols[j], "correlation": float(r)})
    return pd.DataFrame(results)


def correlation_matrix(df: pd.DataFrame, axis: str) -> np.ndarray:
    cols = [c for c in df.columns if c.startswith("gyro") and c.endswith(f"_{axis}")]
    data = df[cols].values
    return np.corrcoef(data, rowvar=False)


def compute_stats(pairwise_df: pd.DataFrame) -> dict:
    arr = pairwise_df["correlation"].values
    return {
        "average": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "minimum": float(np.min(arr)),
        "maximum": float(np.max(arr)),
        "std": float(np.std(arr)),
        "below_055": int(np.sum(arr < PREFERRED_CORRELATION_MAX)),
        "above_055": int(np.sum(arr >= PREFERRED_CORRELATION_MAX)),
        "above_070": int(np.sum(arr > ABSOLUTE_CORRELATION_MAX)),
    }


def validate_correlations(all_pairwise: pd.DataFrame, tolerance: float = TUNING_TOLERANCE) -> Tuple[bool, str]:
    stats = compute_stats(all_pairwise)
    avg = stats["average"]
    tgt = TARGET_CORRELATION
    pref_min = tgt - tolerance
    pref_max = tgt + tolerance

    if stats["maximum"] > ABSOLUTE_CORRELATION_MAX:
        return False, f"FAIL: some pairwise correlation {stats['maximum']:.3f} exceeds absolute maximum {ABSOLUTE_CORRELATION_MAX}"
    if not (pref_min <= avg <= pref_max):
        return False, f"FAIL: average correlation {avg:.3f} outside preferred [{pref_min:.3f},{pref_max:.3f}]"
    return True, f"PASS: average {avg:.3f} within preferred range [{pref_min:.3f},{pref_max:.3f}]"


def compute_baseline_correlations(df: pd.DataFrame, baseline_df: pd.DataFrame) -> pd.DataFrame:
    results = []
    for g in range(1, len([c for c in df.columns if c.startswith('gyro') and c.endswith('_x')]) + 1):
        for axis in ("x", "y", "z"):
            sensor_col = f"gyro{g}_{axis}"
            ref_col = f"baseline_{axis}"
            if sensor_col not in df.columns or ref_col not in baseline_df.columns:
                continue
            corr = np.corrcoef(df[sensor_col].values, baseline_df[ref_col].values)[0, 1]
            results.append({
                "gyro": f"gyro{g}",
                "axis": axis,
                "reference": ref_col,
                "correlation": float(corr),
            })
    return pd.DataFrame(results)


def run_full_analysis(raw_csv: str = RAW_CSV, baseline_csv: str | None = None):
    ensure_project_dirs()
    df = pd.read_csv(raw_csv)

    pairwise_frames = []
    matrices = {}
    stats_by_axis = {}

    for axis in ("x", "y", "z"):
        pw = compute_pairwise(df, axis)
        pairwise_frames.append(pw)
        mat = correlation_matrix(df, axis)
        matrices[axis] = mat
        stats_by_axis[axis] = compute_stats(pw)
        # save matrix
        os.makedirs(os.path.dirname(globals()[f"CORR_MATRIX_{axis.upper()}"].lower()), exist_ok=True)
        pd.DataFrame(mat).to_csv(globals()[f"CORR_MATRIX_{axis.upper()}"], index=False)

    all_pw = pd.concat(pairwise_frames, ignore_index=True)
    os.makedirs(os.path.dirname(PAIRWISE_CSV), exist_ok=True)
    all_pw.to_csv(PAIRWISE_CSV, index=False)

    baseline_pw = pd.DataFrame()
    if baseline_csv is not None:
        baseline_df = pd.read_csv(baseline_csv)
        baseline_pw = compute_baseline_correlations(df, baseline_df)
        os.makedirs(os.path.dirname(BASELINE_CORR_CSV), exist_ok=True)
        baseline_pw.to_csv(BASELINE_CORR_CSV, index=False)

    overall_stats = compute_stats(all_pw)
    valid, msg = validate_correlations(all_pw)

    # summary text
    lines = []
    lines.append("CORRELATION STATISTICS\n")
    for axis in ("x", "y", "z"):
        s = stats_by_axis[axis]
        lines.append(f"{axis.upper()} axis: avg={s['average']:.4f}, min={s['minimum']:.4f}, max={s['maximum']:.4f}")
    lines.append("\nOVERALL:")
    lines.append(f"average={overall_stats['average']:.4f}, max={overall_stats['maximum']:.4f}")
    if not baseline_pw.empty:
        lines.append("\nBASELINE-CORRELATION SUMMARY:")
        for _, row in baseline_pw.iterrows():
            lines.append(f"{row['gyro']}_{row['axis']} vs {row['reference']}: {row['correlation']:.4f}")
    lines.append(f"VALIDATION: {msg}")

    save_text(RESULTS_SUMMARY, "\n".join(lines))
    print("Saved pairwise correlations, matrices, and baseline comparisons.")
    print(msg)


if __name__ == "__main__":
    run_full_analysis()
