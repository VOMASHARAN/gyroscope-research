"""Baseline gyroscope simulator.

This shares the same underlying motion structure as the main multi-gyro simulator,
while using lower noise levels to mimic a more accurate reference sensor.
"""

import os

import numpy as np
import pandas as pd

from config import (
    BASELINE_COMMON_SCALE,
    BASELINE_NOISE_SCALE,
    BASELINE_RAW_CSV,
    DURATION,
    RANDOM_SEED,
    SAMPLE_RATE,
    WHITE_NOISE_STD,
    ARW_COEFFICIENT,
    RRW_COEFFICIENT,
    MARKOV_STD,
    MARKOV_TIME_CONSTANT,
)
import noise_models as nm
from gyro_simulator import GyroscopeSimulator


class BaselineGyroSimulator(GyroscopeSimulator):
    def __init__(self, sample_rate: float = SAMPLE_RATE, duration: float = DURATION,
                 seed: int = RANDOM_SEED, common_strength: float = BASELINE_COMMON_SCALE,
                 noise_scale: float = BASELINE_NOISE_SCALE):
        super().__init__(sample_rate=sample_rate, duration=duration, seed=seed, common_strength=common_strength)
        self.noise_scale = noise_scale

    def generate_all(self, common_signal: np.ndarray | None = None) -> pd.DataFrame:
        t = self.time_vector()
        common = common_signal if common_signal is not None else self.generate_common_component()
        data = {"timestamp": t}

        for axis in ("x", "y", "z"):
            wn = nm.white_noise(WHITE_NOISE_STD * self.noise_scale, self.samples, self.rng)
            arw = nm.arw_process(ARW_COEFFICIENT * self.noise_scale, self.dt, self.samples, self.rng)
            rrw = nm.rrw_process(RRW_COEFFICIENT * self.noise_scale, self.dt, self.samples, self.rng)
            mark = nm.gauss_markov_process(MARKOV_STD * self.noise_scale, MARKOV_TIME_CONSTANT, self.dt, self.samples, self.rng)
            signal = self.common_strength * common + wn + arw + rrw + mark
            data[f"baseline_{axis}"] = signal

        return pd.DataFrame(data)

    def save_raw(self, df: pd.DataFrame, path: str = BASELINE_RAW_CSV):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False)


if __name__ == "__main__":
    sim = BaselineGyroSimulator()
    baseline_df = sim.generate_all()
    sim.save_raw(baseline_df)
    print(f"Saved baseline data to {BASELINE_RAW_CSV} with {len(baseline_df)} samples")
