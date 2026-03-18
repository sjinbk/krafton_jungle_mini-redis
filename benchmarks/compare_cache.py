from __future__ import annotations

import argparse
from pathlib import Path
from statistics import mean
import sys
from time import perf_counter

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.app import create_app


def measure_requests(client: TestClient, *, key: str, clear_before_each: bool, iterations: int) -> list[float]:
    durations: list[float] = []

    for _ in range(iterations):
        if clear_before_each:
            client.app.state.demo_cache_service.clear_cache_key(key)

        started_at = perf_counter()
        response = client.get("/demo/data-cache", params={"key": key})
        elapsed_ms = (perf_counter() - started_at) * 1_000

        if response.status_code != 200:
            raise RuntimeError(response.text)
        if response.json()["data"]["items"] == []:
            raise RuntimeError(f"No seeded data found for key={key}")

        durations.append(elapsed_ms)

    return durations


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare cold origin path vs warm cache path.")
    parser.add_argument("--key", default="sample")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()

    app = create_app()

    with TestClient(app) as client:
        cold_durations = measure_requests(
            client,
            key=args.key,
            clear_before_each=True,
            iterations=args.iterations,
        )

        client.app.state.demo_cache_service.clear_cache_key(args.key)
        prime_response = client.get("/demo/data-cache", params={"key": args.key})
        if prime_response.status_code != 200:
            raise RuntimeError(prime_response.text)

        warm_durations = measure_requests(
            client,
            key=args.key,
            clear_before_each=False,
            iterations=args.iterations,
        )

    print("Mini Redis benchmark")
    print(f"key={args.key}")
    print(f"iterations={args.iterations}")
    print(f"cold_avg_ms={mean(cold_durations):.3f}")
    print(f"warm_avg_ms={mean(warm_durations):.3f}")


if __name__ == "__main__":
    main()
