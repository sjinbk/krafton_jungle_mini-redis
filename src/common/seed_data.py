from __future__ import annotations

from datetime import datetime, timedelta, timezone


def _build_dummy_items() -> list[dict[str, object]]:
    base_time = datetime(2026, 3, 17, 10, 0, tzinfo=timezone.utc)
    items: list[dict[str, object]] = []

    for index in range(98):
        item_number = index + 1
        items.append(
            {
                "key": "sample",
                "itemId": f"sample-{item_number}",
                "value": f"example payload {item_number}",
                "createdAt": base_time + timedelta(minutes=index),
            }
        )

    items.extend(
        [
            {
                "key": "alpha",
                "itemId": "alpha-1",
                "value": "alpha payload",
                "createdAt": datetime(2026, 3, 17, 12, 0, tzinfo=timezone.utc),
            },
            {
                "key": "beta",
                "itemId": "beta-1",
                "value": "beta payload",
                "createdAt": datetime(2026, 3, 17, 12, 1, tzinfo=timezone.utc),
            },
        ]
    )

    return items


DEFAULT_DUMMY_ITEMS = _build_dummy_items()

