"""Live TCP streaming interface for the 8-gyro simulator.

This module reuses the existing GyroscopeSimulator to generate a synchronized
8-gyro dataset and exposes each gyro on its own localhost TCP port.
The live stream layer is intentionally thin and does not replace the underlying
simulation logic.
"""

from __future__ import annotations

import socket
import threading
import time
from typing import Dict, Iterable, List, Tuple

from config import DURATION, NUM_GYROS, SAMPLE_RATE
from gyro_simulator import GyroscopeSimulator
from baseline_gyro_simulator import BaselineGyroSimulator


class GyroStreamServer:
    """Serve each gyro on a unique localhost port using the same timestamped signal."""

    PORTS: Dict[int, int | str] = {5001: 1, 5002: 2, 5003: 3, 5004: 4, 5005: 5, 5006: 6, 5007: 7, 5008: 8, 5009: "baseline"}

    def __init__(self, host: str = "127.0.0.1", sample_rate: float = SAMPLE_RATE, duration: float = DURATION):
        self.host = host
        self.sample_rate = sample_rate
        self.duration = duration
        self.sim = GyroscopeSimulator(sample_rate=sample_rate, duration=duration, num_gyros=NUM_GYROS)
        self.common_signal = self.sim.generate_common_component()
        self.df = self.sim.generate_all(common_signal=self.common_signal)
        self.baseline_sim = BaselineGyroSimulator(sample_rate=sample_rate, duration=duration)
        self.baseline_df = self.baseline_sim.generate_all(common_signal=self.common_signal)
        self.stop_event = threading.Event()
        self.threads: List[threading.Thread] = []

    def _gyro_rows_for_port(self, gyro_id: int | str) -> Iterable[Tuple[float, float, float, float]]:
        if gyro_id == "baseline":
            for _, row in self.baseline_df.iterrows():
                timestamp = float(row["timestamp"])
                x = float(row["baseline_x"])
                y = float(row["baseline_y"])
                z = float(row["baseline_z"])
                yield timestamp, x, y, z
            return

        for _, row in self.df.iterrows():
            timestamp = float(row["timestamp"])
            x = float(row[f"gyro{gyro_id}_x"])
            y = float(row[f"gyro{gyro_id}_y"])
            z = float(row[f"gyro{gyro_id}_z"])
            yield timestamp, x, y, z

    def _serve_port(self, port: int, gyro_id: int | str):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, port))
            server.listen(5)
            label = "BASELINE" if gyro_id == "baseline" else f"Gyro {gyro_id}"
            print(f"{label} -> listening on {self.host}:{port}")
            while not self.stop_event.is_set():
                try:
                    conn, _ = server.accept()
                except OSError:
                    break
                with conn:
                    conn.settimeout(5.0)
                    try:
                        for timestamp, x, y, z in self._gyro_rows_for_port(gyro_id):
                            payload = f"{timestamp:.6f},{x:.6f},{y:.6f},{z:.6f}\n"
                            conn.sendall(payload.encode("utf-8"))
                            time.sleep(1.0 / self.sample_rate)
                    except (BrokenPipeError, OSError, socket.timeout):
                        pass

    def start(self):
        for port, gyro_id in self.PORTS.items():
            thread = threading.Thread(target=self._serve_port, args=(port, gyro_id), daemon=True)
            thread.start()
            self.threads.append(thread)
        print("All gyros and baseline are broadcasting on localhost ports 5001-5009")

    def stop(self):
        self.stop_event.set()
        for thread in self.threads:
            thread.join(timeout=2.0)


if __name__ == "__main__":
    server = GyroStreamServer()
    server.start()
    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("Stopping gyro stream server...")
        server.stop()
