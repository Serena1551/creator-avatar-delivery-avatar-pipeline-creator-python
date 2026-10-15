from __future__ import annotations

import argparse
import json
import mimetypes
import uuid
from pathlib import Path

import httpx


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish a creator avatar locally")
    parser.add_argument("image", type=Path)
    parser.add_argument("--creator", required=True)
    parser.add_argument("--subscriber", action="append", default=[])
    parser.add_argument("--service", default="http://127.0.0.1:8000")
    args = parser.parse_args()

    content_type = mimetypes.guess_type(args.image.name)[0] or "application/octet-stream"
    with args.image.open("rb") as image_file:
        response = httpx.request(
            method="POST",
            url=f"{args.service}/creators/{args.creator}/avatar",
            data={
                "request_id": str(uuid.uuid4()),
                "subscribers": args.subscriber,
            },
            files={"image": (args.image.name, image_file, content_type)},
            timeout=60.0,
        )
    response.raise_for_status()
    print(json.dumps(response.json(), indent=2))


if __name__ == "__main__":
    main()

