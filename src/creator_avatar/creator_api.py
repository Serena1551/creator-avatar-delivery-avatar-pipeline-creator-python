from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from .avatar_delivery import AvatarDelivery, AvatarDeliveryService, AvatarUploadRequest
from .infrai_images import InfraiError, InfraiImages, InfraiTransportError

app = FastAPI(title="Creator Avatar Delivery")


@app.post("/creators/{creator_id}/avatar", response_model=AvatarDelivery)
async def upload_creator_avatar(
    creator_id: str,
    image: UploadFile = File(),
    request_id: str = Form(),
    subscribers: list[str] = Form(default=[]),
) -> AvatarDelivery:
    request = AvatarUploadRequest(
        creator_id=creator_id,
        filename=image.filename or "avatar",
        subscribers=subscribers,
        request_id=request_id,
    )
    client = InfraiImages()
    try:
        return await AvatarDeliveryService(client).publish(request, await image.read())
    except InfraiError as exc:
        status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=exc.detail) from exc
    except InfraiTransportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    finally:
        await client.close()
