#!/usr/bin/env python3
"""List the models an API key can reach and try each with a tiny request.

Use it to pick SCOUT_MODEL values that work for your key right now:

    SCOUT_API_KEY=... python3 scripts/probe_models.py

It reads the same SCOUT_API_URL as the scout and derives the model list URL
from it. Each text model gets one one-word request, so this uses a handful of
free-tier calls. It prints a table and never fails the run.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

from scout import API_URL, USER_AGENT

SKIP = ("embedding", "image", "tts", "audio", "veo", "imagen", "aqa", "live", "robotics", "vision", "gemma",
        "transcribe", "computer-use", "customtools", "-pro")  # pro models have no free tier
LIMIT = 15
PAUSE = 2
TIMEOUT = 20


def call(url: str, key: str, payload: dict | None = None) -> tuple[int, str]:
    data = json.dumps(payload).encode() if payload else None
    headers = {"Authorization": f"Bearer {key}", "User-Agent": USER_AGENT}
    if data:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status, response.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as error:
        return error.code, " ".join(error.read()[:200].decode("utf-8", "replace").split())
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        return 0, str(error)


def usable(model_id: str) -> bool:
    name = model_id.lower()
    return "gemini" in name and not any(word in name for word in SKIP)


def main() -> int:
    key = os.environ.get("SCOUT_API_KEY", "")
    if not key:
        print("SCOUT_API_KEY is not set", file=sys.stderr)
        return 0
    status, body = call(API_URL.rsplit("/chat/completions", 1)[0] + "/models", key)
    if status != 200:
        print(f"could not list models: HTTP {status}: {body[:200]}")
        return 0
    ids = sorted(m["id"].removeprefix("models/") for m in json.loads(body).get("data", []))
    print(f"{len(ids)} models listed; probing up to {LIMIT} text models\n")
    print("| model | result |")
    print("| --- | --- |")
    for model in [i for i in ids if usable(i)][:LIMIT]:
        status, body = call(API_URL, key, {"model": model, "messages": [{"role": "user", "content": "Reply with the word ok."}], "max_tokens": 16})
        print(f"| `{model}` | {'works' if status == 200 else f'HTTP {status}: ' + body[:80].replace('|', '/')} |")
        time.sleep(PAUSE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
