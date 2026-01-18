from __future__ import annotations

import os
from typing import Any, Dict

import httpx


class UCPMockClient:
    def __init__(self) -> None:
        self.base_url = os.getenv("UCP_MOCK_URL", "")

    def process_payment(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.base_url:
            return {
                "status": "skipped",
                "message": "UCP_MOCK_URL не задан, платеж пропущен",
            }
        try:
            response = httpx.post(f"{self.base_url.rstrip('/')}/purchase", json=payload, timeout=10)
            response.raise_for_status()
            return {"status": "ok", "data": response.json()}
        except httpx.HTTPError as exc:
            return {"status": "error", "message": str(exc)}
