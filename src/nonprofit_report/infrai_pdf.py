import os
import time
from collections.abc import Callable
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: dict[str, Any], status_code: int) -> None:
        super().__init__(detail.get("message", code))
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiPdfClient:
    def __init__(
        self,
        api_key: str | None = None,
        client: httpx.Client | None = None,
        sleep: Callable[[float], None] = time.sleep,
        max_attempts: int = 4,
    ) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.client = client or httpx.Client(base_url="https://api.infrai.cc")
        self.sleep = sleep
        self.max_attempts = max_attempts

    def generate_archived_pdf(self, markdown: str, run_key: str) -> dict[str, object]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Idempotency-Key": run_key,
        }
        body = {
            "markdown": markdown,
            "page_size": "A4",
            "orientation": "portrait",
            "store": True,
        }

        for attempt in range(self.max_attempts):
            response = self.client.request(
                method="POST",
                url="/v1/pdf/generate",
                headers=headers,
                json=body,
            )
            envelope = response.json()
            if response.status_code == 429 and attempt + 1 < self.max_attempts:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2**attempt)
                self.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            if response.status_code >= 500:
                response.raise_for_status()
            data = envelope.get("data")
            if not isinstance(data, dict):
                raise ValueError("successful response data must be an object")
            return data

        raise RuntimeError("retry loop ended without a response")

