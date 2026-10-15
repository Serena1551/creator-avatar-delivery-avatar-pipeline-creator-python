from __future__ import annotations

import asyncio
from typing import Any

from creator_avatar.avatar_delivery import AvatarDeliveryService, AvatarUploadRequest


class RecordingImages:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any, str]] = []

    async def upload(
        self, file: bytes, filename: str, idempotency_key: str
    ) -> dict[str, Any]:
        self.calls.append(("upload", filename, idempotency_key))
        return {"image": "uploaded-image"}

    async def smart_crop(
        self, image: Any, aspect: str, idempotency_key: str
    ) -> dict[str, Any]:
        self.calls.append(("crop", aspect, idempotency_key))
        return {"image": "square-image"}

    async def optimize(
        self, image: Any, idempotency_key: str
    ) -> dict[str, Any]:
        self.calls.append(("optimize", image, idempotency_key))
        return {"image": "stored-webp", "format": "webp"}


def test_ready_avatar_notifies_each_subscriber_once() -> None:
    images = RecordingImages()
    request = AvatarUploadRequest(
        creator_id="creator-42",
        filename="studio-shot.jpg",
        subscribers=["sub-7", "sub-9", "sub-7"],
        request_id="req-avatar-2026",
    )

    result = asyncio.run(AvatarDeliveryService(images).publish(request, b"photo"))

    assert result.state == "ready"
    assert result.image == {"image": "stored-webp", "format": "webp"}
    assert [update.subscriber_id for update in result.updates] == ["sub-7", "sub-9"]
    assert all(update.asset_id == result.asset_id for update in result.updates)
    assert [call[0] for call in images.calls] == ["upload", "crop", "optimize"]
    assert [call[2] for call in images.calls] == [
        "req-avatar-2026:upload",
        "req-avatar-2026:crop",
        "req-avatar-2026:optimize",
    ]

