"""GyroscopeSimulator
Generates 8 gyroscopes each with X/Y/Z axes and the configured noise components.
"""
from typing import Tuple
import numpy as np
import pandas as pd
from dataclasses import dataclass
import os

from config import *
import noise_models as nm
from data_utils import ensure_project_dirs


@dataclass
class GyroscopeSimulator:
    sample_rate: float = SAMPLE_RATE
    duration: float = DURATION
    num_gyros: int = NUM_GYROS
    seed: int = RANDOM_SEED
    common_strength: float = COMMON_COMPONENT_STRENGTH

    def __post_init__(self):
        self.dt = 1.0 / self.sample_rate
        self.samples = int(self.sample_rate * self.duration)
        self.rng = np.random.default_rng(self.seed)
        ensure_project_dirs()

    def time_vector(self) -> np.ndarray:
        return np.linspace(0.0, self.duration, self.samples, endpoint=False)

    def generate_common_component(self) -> np.ndarray:
        # common component is a smooth low-frequency signal: use Gauss-Markov with long tau
        return nm.gauss_markov_process(sigma=1.0, tau=max(1.0, self.duration / 5.0), dt=self.dt, size=self.samples, rng=self.rng)

    def generate_all(self, common_signal: np.ndarray | None = None) -> pd.DataFrame:
        t = self.time_vector()
        common = common_signal if common_signal is not None else self.generate_common_component()
        data = {"timestamp": t}

        # For each gyro and axis, generate the composite signal
        for g in range(1, self.num_gyros + 1):
            for axis in ("x", "y", "z"):
                # independent components
                wn = nm.white_noise(WHITE_NOISE_STD, self.samples, self.rng)
                arw = nm.arw_process(ARW_COEFFICIENT, self.dt, self.samples, self.rng)
                rrw = nm.rrw_process(RRW_COEFFICIENT, self.dt, self.samples, self.rng)
                mark = nm.gauss_markov_process(MARKOV_STD, MARKOV_TIME_CONSTANT, self.dt, self.samples, self.rng)

                # mix common component with per-gyro scaling to avoid identical sensors
                per_gyro_scale = 1.0 + self.rng.normal(scale=0.05)
                common_mixed = self.common_strength * per_gyro_scale * common

                signal = common_mixed + wn + arw + rrw + mark
                data[f"gyro{g}_{axis}"] = signal

        df = pd.DataFrame(data)
        return df

    def save_raw(self, df: pd.DataFrame, path: str = RAW_CSV):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)

    def save_individual_sensor_datasets(self, df: pd.DataFrame, output_dir: str = DATASET_OUTPUT_DIR, include_excel: bool = True):
        os.makedirs(output_dir, exist_ok=True)
        for g in range(1, self.num_gyros + 1):
            cols = ["timestamp"] + [f"gyro{g}_{axis}" for axis in ("x", "y", "z")]
            sensor_df = df[cols].copy()
            csv_path = os.path.join(output_dir, f"gyro_{g}.csv")
            sensor_df.to_csv(csv_path, index=False)
            if include_excel:
                try:
                    sensor_df.to_excel(os.path.join(output_dir, f"gyro_{g}.xlsx"), index=False)
                except ImportError:
                    pass


def main():
    sim = GyroscopeSimulator()
    df = sim.generate_all()
    sim.save_raw(df)
    print(f"Saved raw CSV to {RAW_CSV} with {len(df)} samples and {len(df.columns)-1} channels")


if __name__ == "__main__":
    main()
