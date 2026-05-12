from __future__ import annotations

import asyncio
import time
from typing import Any

from openai import OpenAI

from src.config import GUARD_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL


def _openai_client() -> OpenAI:
    _ = OPENAI_BASE_URL
    return OpenAI(api_key=OPENAI_API_KEY)


def parse_guard_output(text: str) -> bool:
    lowered = text.lower()
    if "unsafe" in lowered:
        return False
    if "safe" in lowered:
        return True
    return False


class OutputGuard:
    def __init__(self, model: str = GUARD_MODEL) -> None:
        self.model = model
        self.client = _openai_client()

    def check_output(self, user_input: str, answer: str) -> tuple[bool, str, float]:
        started = time.perf_counter()
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Return a short verdict containing either SAFE or UNSAFE based on policy risk."},
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": answer},
            ],
            temperature=0.0,
        )
        raw_result = resp.choices[0].message.content or ""
        latency_ms = (time.perf_counter() - started) * 1000
        return parse_guard_output(raw_result), raw_result, latency_ms

    async def check_async(self, user_input: str, answer: str) -> tuple[bool, str, float]:
        return await asyncio.to_thread(self.check_output, user_input, answer)
