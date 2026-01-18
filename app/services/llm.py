from __future__ import annotations

import os
from typing import Any, Dict, List

from openai import OpenAI


class LLMService:
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    def generate_reply(self, system_prompt: str, messages: List[Dict[str, str]]) -> str:
        if not self.client:
            return "LLM ключ не настроен. Я могу показать каталог и оформить заказ."
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, *messages],
            temperature=0.2,
        )
        return response.choices[0].message.content or ""


class IntentDetector:
    @staticmethod
    def detect(message: str) -> str:
        lowered = message.lower()
        if any(keyword in lowered for keyword in ["куп", "buy", "order", "закаж"]):
            return "purchase"
        if any(keyword in lowered for keyword in ["каталог", "товар", "list", "show"]):
            return "catalog"
        return "chat"
