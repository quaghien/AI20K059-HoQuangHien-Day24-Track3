from __future__ import annotations

import asyncio
import time
from typing import Any

from src.config import SAFE_REFUSAL


async def audit_log(user_input: str, answer: str, timings: dict[str, float]) -> None:
    _ = (user_input, answer, timings)
    await asyncio.sleep(0)


def refuse_response() -> str:
    return SAFE_REFUSAL


async def guarded_pipeline(user_input: str, input_guard, rag_adapter, output_guard) -> tuple[str, dict[str, float]]:
    timings: dict[str, float] = {}
    t0 = time.perf_counter()
    pii_task = asyncio.create_task(input_guard.sanitize_async(user_input))
    topic_task = asyncio.create_task(input_guard.check_topic_async(user_input))
    inj_task = asyncio.create_task(input_guard.detect_injection_async(user_input))
    sanitized, _ = await pii_task
    topic_ok, topic_reason = await topic_task
    injected, injection_reason = await inj_task
    timings["L1"] = (time.perf_counter() - t0) * 1000
    if not topic_ok:
        return topic_reason, timings
    if injected:
        return f"Blocked: {injection_reason}", timings

    t0 = time.perf_counter()
    rag_result = await asyncio.to_thread(rag_adapter.run_rag, sanitized)
    answer = rag_result["answer"]
    timings["L2"] = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    safe, _, _ = await output_guard.check_async(sanitized, answer)
    timings["L3"] = (time.perf_counter() - t0) * 1000
    if not safe:
        return refuse_response(), timings

    asyncio.create_task(audit_log(user_input, answer, timings))
    timings["total"] = timings["L1"] + timings["L2"] + timings["L3"]
    return answer, timings
