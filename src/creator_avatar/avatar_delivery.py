from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, Field


class AvatarUploadRequest(BaseModel):
    creator_id: str = Field(min_length=1, max_length=80)
    filename: str = Field(min_length=1, max_length=180)
    subscribers: list[str] = Field(default_factory=list, max_length=500)
    request_id: str = Field(min_length=8, max_length=120)


class SubscriberUpdate(BaseModel):
    subscriber_id: str
    creator_id: str
    asset_id: str
    event: Literal["creator.avatar.ready"] = "creator.avatar.ready"


class AvatarDelivery(BaseModel):
    creator_id: str
    asset_id: str
    state: Literal["ready"]
    image: dict[str, Any]
    updates: list[SubscriberUpdate]


class ImagePipeline(Protocol):
    async def upload(
        self, file: bytes, filename: str, idempotency_key: str
    ) -> dict[str, Any]:
        raise AssertionError("protocol signature")

    async def smart_crop(
        self, image: Any, aspect: str, idempotency_key: str
    ) -> dict[str, Any]:
        raise AssertionError("protocol signature")

    async def optimize(
        self, image: Any, idempotency_key: str
    ) -> dict[str, Any]:
        raise AssertionError("protocol signature")


class AvatarDeliveryService:
    def __init__(self, images: ImagePipeline) -> None:
        self.images = images

    async def publish(
        self, request: AvatarUploadRequest, content: bytes
    ) -> AvatarDelivery:
        uploaded = await self.images.upload(
            content, request.filename, f"{request.request_id}:upload"
        )
        cropped = await self.images.smart_crop(
            uploaded, "1:1", f"{request.request_id}:crop"
        )
        optimized = await self.images.optimize(
            cropped, f"{request.request_id}:optimize"
        )
        asset_id = f"avatar:{request.creator_id}:{request.request_id}"
        updates = [
            SubscriberUpdate(
                subscriber_id=subscriber_id,
                creator_id=request.creator_id,
                asset_id=asset_id,
            )
            for subscriber_id in dict.fromkeys(request.subscribers)
        ]
        return AvatarDelivery(
            creator_id=request.creator_id,
            asset_id=asset_id,
            state="ready",
            image=optimized,
            updates=updates,
        )
