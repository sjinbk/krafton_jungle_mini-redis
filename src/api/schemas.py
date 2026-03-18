from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr


class SetValueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: StrictStr = Field(min_length=1)
    value: Any
    ttlSeconds: StrictInt | None = Field(default=None)


class ExpireRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ttlSeconds: StrictInt


class PerformanceCompareRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: StrictStr = Field(default="sample", min_length=1)
    iterations: StrictInt = Field(default=20)


class SeatReservationDemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    seatLimit: StrictInt = Field(default=50)
    requestCount: StrictInt = Field(default=100)

