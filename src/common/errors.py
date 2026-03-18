from __future__ import annotations


class AppError(Exception):
    def __init__(self, *, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def invalid_key(message: str = "Key must be a non-empty string") -> AppError:
    return AppError(status_code=400, code="INVALID_KEY", message=message)


def invalid_ttl(
    message: str = "ttlSeconds must be a positive integer greater than zero",
) -> AppError:
    return AppError(status_code=400, code="INVALID_TTL", message=message)


def invalid_iterations(
    message: str = "iterations must be an integer between 1 and 100",
) -> AppError:
    return AppError(status_code=400, code="INVALID_ITERATIONS", message=message)


def invalid_burst_count(
    message: str = "count must be an integer between 1 and 50",
) -> AppError:
    return AppError(status_code=400, code="INVALID_BURST_COUNT", message=message)


def invalid_scenario(
    message: str = (
        "scenario must be one of sameKeyKvGetBurst, "
        "differentKeyKvGetBurst, demoCacheGetBurst"
    ),
) -> AppError:
    return AppError(status_code=400, code="INVALID_SCENARIO", message=message)


def key_not_found(message: str = "Requested key does not exist") -> AppError:
    return AppError(status_code=404, code="KEY_NOT_FOUND", message=message)


def benchmark_data_not_found(
    message: str = "Benchmark data for the requested key does not exist",
) -> AppError:
    return AppError(status_code=404, code="BENCHMARK_DATA_NOT_FOUND", message=message)
