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


def key_not_found(message: str = "Requested key does not exist") -> AppError:
    return AppError(status_code=404, code="KEY_NOT_FOUND", message=message)

