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

