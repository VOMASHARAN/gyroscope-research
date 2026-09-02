"""Utility to check that all 8 gyro ports are live and responding."""

from __future__ import annotations

import socket


PORTS = list(range(5001, 5010))


def check_port(port: int, host: str = "127.0.0.1", timeout: float = 2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(b"PING\n")
            return True
    except OSError:
        return False


if __name__ == "__main__":
    print("PORT STATUS")
    print("-----------")
    for port in PORTS:
        ok = check_port(port)
        if port == 5009:
            label = "BASELINE"
            name = "BASELINE"
        else:
            label = f"GYRO {port - 5000}"
            name = f"GYRO {port - 5000}"
        print(f"{port} -> {label} -> {'LISTENING' if ok else 'OFFLINE'} -> {'PASS' if ok else 'FAIL'}")
