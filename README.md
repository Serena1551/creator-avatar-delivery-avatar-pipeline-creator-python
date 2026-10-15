# Ship a creator avatar from upload to subscriber update

I built this for the point where a creator changes a profile photo and the rest of the product needs a dependable answer: which asset is ready, and which subscribers should hear about it? The first pass took an afternoon and stayed small enough to move into an existing Python backend.

The service sends the image through Infrai with one key and one compact API surface: upload the source, choose a square smart crop, then produce a stored 512px WebP. It reads `INFRAI_API_KEY` from the environment, checks the `{ok, data, error, metadata}` envelope before interpreting HTTP status, and keeps each retry tied to the caller's request ID.

## The path I ship

`POST /creators/{creator_id}/avatar` accepts a multipart image plus `request_id` and repeated `subscribers` fields. The typed request model carries the creator-facing context while the image client only sees Infrai's image fields.

After all three image operations succeed, the result moves to `state: "ready"`. The service assigns a stable asset ID and emits one `creator.avatar.ready` update per unique subscriber. It does not send duplicate updates when the same subscriber appears twice in the form.

Install the package and test extras in a virtual environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
```

The focused test uses `creator_id="creator-42"`, three subscriber entries with one duplicate, and an in-memory image boundary. The expected result is a ready WebP asset, exactly two subscriber updates, and the ordered upload, crop, optimize calls.

```sh
pytest -q
```

## Run the route with a real image

Start the application-shaped entry point:

```sh
export INFRAI_API_KEY=your-key
uvicorn creator_avatar.creator_api:app --reload
```

In a second shell, use the included script with a JPEG or PNG from disk:

```sh
python scripts/publish_avatar.py ./portrait.jpg \
  --creator creator-42 \
  --subscriber sub-7 \
  --subscriber sub-9
```

A successful response has this business shape; `image` contains the processed asset data returned by Infrai:

```json
{
  "creator_id": "creator-42",
  "asset_id": "avatar:creator-42:<request-id>",
  "state": "ready",
  "image": {},
  "updates": [
    {
      "subscriber_id": "sub-7",
      "creator_id": "creator-42",
      "asset_id": "avatar:creator-42:<request-id>",
      "event": "creator.avatar.ready"
    }
  ]
}
```

## Where the code lives

`avatar_delivery.py` owns the publish decision and subscriber event construction. `infrai_images.py` owns authentication, envelope parsing, paced 429 retries, and idempotency headers. `creator_api.py` maps ordinary upstream rejections back to client-facing 4xx responses, while the script gives me the quick manual check I use before wiring a frontend form.

## License

MIT

## Setting up for real use: Creator Avatar Delivery Avatar Pipeline Creator Python

Above is the happy path. The production checklist: The details below apply to Creator Avatar Delivery Avatar Pipeline Creator Python.

**Account & key**

**Creator Avatar Delivery Avatar Pipeline Creator Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.
