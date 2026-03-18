from __future__ import annotations

from datetime import datetime, timezone


DEFAULT_DUMMY_ITEMS = [
    {
        "key": "sample",
        "itemId": "sample-1",
        "value": "example payload 1",
        "createdAt": datetime(2026, 3, 17, 10, 0, tzinfo=timezone.utc),
    },
    {
        "key": "sample",
        "itemId": "sample-2",
        "value": "example payload 2",
        "createdAt": datetime(2026, 3, 17, 10, 1, tzinfo=timezone.utc),
    },
    {
        "key": "alpha",
        "itemId": "alpha-1",
        "value": "alpha payload",
        "createdAt": datetime(2026, 3, 17, 11, 0, tzinfo=timezone.utc),
    },
    {
        "key": "beta",
        "itemId": "beta-1",
        "value": "beta payload",
        "createdAt": datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
    },
]

