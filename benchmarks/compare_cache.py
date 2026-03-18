from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.app import create_app
from src.common.config import Settings
from src.service.performance_benchmark_service import PerformanceBenchmarkService


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare cold origin path vs warm cache path.")
    parser.add_argument("--key", default="sample")
    parser.add_argument("--iterations", type=int, default=20)
    args = parser.parse_args()

    service = PerformanceBenchmarkService(
        settings=Settings.from_env(),
        app_factory=create_app,
    )
    result = service.compare_cache(key=args.key, iterations=args.iterations)

    print("Mini Redis benchmark")
    print(f"key={result['key']}")
    print(f"iterations={result['iterations']}")
    print(f"api_cold_avg_ms={result['apiTiming']['coldAvgMs']:.3f}")
    print(f"api_warm_avg_ms={result['apiTiming']['warmAvgMs']:.3f}")
    print(f"api_saved_ms={result['apiTiming']['savedMs']:.3f}")
    print(f"api_speedup_ratio={result['apiTiming']['speedupRatio']:.3f}")
    print(f"service_cold_avg_ms={result['serviceTiming']['coldAvgMs']:.3f}")
    print(f"service_warm_avg_ms={result['serviceTiming']['warmAvgMs']:.3f}")
    print(f"service_saved_ms={result['serviceTiming']['savedMs']:.3f}")
    print(f"service_speedup_ratio={result['serviceTiming']['speedupRatio']:.3f}")


if __name__ == "__main__":
    main()
