"""Client utilities for reading live gyroscope streams from the local TCP servers."""

from __future__ import annotations

import socket
from typing import Dict, List

import pandas as pd


class GyroStreamClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 5001, timeout: float = 5.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket = socket.create_connection((host, port), timeout=timeout)
        self.socket.settimeout(timeout)
        self.file = self.socket.makefile("r", encoding="utf-8")

    def read_sample(self):
        line = self.file.readline()
        if line == "":
            raise EOFError(f"No data received from {self.host}:{self.port}")
        parts = [p.strip() for p in line.strip().split(",")]
        if len(parts) != 4:
            raise ValueError(f"Unexpected stream payload from {self.host}:{self.port}: {line!r}")
        timestamp, x, y, z = parts
        return {
            "timestamp": float(timestamp),
            "x": float(x),
            "y": float(y),
            "z": float(z),
        }

    def read_samples(self, count: int):
        samples = []
        for _ in range(count):
            samples.append(self.read_sample())
        return samples

    def close(self):
        self.file.close()
        self.socket.close()


def connect_all_ports(ports: List[int], host: str = "127.0.0.1") -> Dict[int, GyroStreamClient]:
    clients = {}
    for port in ports:
        client = GyroStreamClient(host=host, port=port)
        clients[port] = client
    return clients


def collect_live_stream_data(ports: List[int], samples_per_port: int = 10, host: str = "127.0.0.1") -> pd.DataFrame:
    clients = connect_all_ports(ports, host=host)
    streams = {port: [] for port in ports}
    try:
        for port in ports:
            streams[port] = clients[port].read_samples(samples_per_port)

        records = []
        for port in ports:
            for sample in streams[port]:
                if port == 5009:
                    label = "baseline"
                else:
                    label = f"gyro{port - 5000}"
                records.append({
                    "timestamp": sample["timestamp"],
                    f"{label}_x": sample["x"],
                    f"{label}_y": sample["y"],
                    f"{label}_z": sample["z"],
                })
        df = pd.DataFrame(records)
        return df.groupby("timestamp", as_index=True).mean().reset_index()
    finally:
        for client in clients.values():
            client.close()


if __name__ == "__main__":
    data = collect_live_stream_data(list(range(5001, 5010)), samples_per_port=5)
    print(data.head())
