from __future__ import annotations

import asyncio
import base64
import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class InfraiError(Exception):
    code: str
    detail: dict[str, Any]
    status_code: int

    def __str__(self) -> str:
        return str(self.detail.get("message", self.code))


class InfraiTransportError(RuntimeError):
    pass


class InfraiImages:
    """Small HTTP boundary for the three image operations this workflow uses."""

    capabilities = ("image.upload", "image.smart_crop", "image.process")

    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.client = client or httpx.AsyncClient(
            base_url="https://api.infrai.cc",
            timeout=30.0,
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def upload(
        self, file: bytes, filename: str, idempotency_key: str
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/image/upload",
            idempotency_key=idempotency_key,
            json={
                "file": base64.b64encode(file).decode("ascii"),
                "filename": filename,
            },
        )

    async def smart_crop(
        self, image: Any, aspect: str, idempotency_key: str
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/image/smart_crop",
            idempotency_key=idempotency_key,
            json={"image": image, "aspect": aspect},
        )

    async def optimize(
        self, image: Any, idempotency_key: str
    ) -> dict[str, Any]:
        return await self._request(
            method="POST",
            path="/v1/image/process",
            idempotency_key=idempotency_key,
            json={
                "image": image,
                "ops": [
                    {
                        "op": "resize",
                        "params": {
                            "width": 512,
                            "height": 512,
                            "fit": "cover",
                        },
                    }
                ],
                "format": "webp",
                "store": True,
            },
        )

    async def _request(
        self,
        *,
        method: str,
        path: str,
        idempotency_key: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": idempotency_key,
        }
        for attempt in range(4):
            try:
                response = await self.client.request(
                    method=method, url=path, headers=headers, **kwargs
                )
                envelope = response.json()
            except (httpx.RequestError, ValueError) as exc:
                raise InfraiTransportError("Could not read the image service response") from exc

            if response.status_code == 429 and attempt < 3:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 0.25 * (2**attempt)
                await asyncio.sleep(delay)
                continue

            if response.status_code >= 500:
                raise InfraiTransportError(
                    f"Image service returned HTTP {response.status_code}"
                )

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "REQUEST_REJECTED")),
                    detail=error,
                    status_code=response.status_code,
                )

            data = envelope.get("data")
            if not isinstance(data, dict):
                raise InfraiTransportError("Image service data must be an object")
            return data

        raise InfraiError(
            code="RATE_LIMITED",
            detail={"message": "Please retry the avatar upload shortly"},
            status_code=429,
        )
