from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from openai import OpenAI

from src.config import JUDGE_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL
from src.utils import parse_json_with_fallback

PAIRWISE_PROMPT = """You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Output JSON only:
{{"winner": "A" or "B" or "tie", "reason": "..."}}
"""

ABSOLUTE_PROMPT = """Score the answer on 4 dimensions, each 1-5 scale:
1. Factual accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=unclear, 5=actionable)

Question: {question}
Answer: {answer}

Output JSON only:
{{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}}
"""


def _openai_client() -> OpenAI:
    _ = OPENAI_BASE_URL
    return OpenAI(api_key=OPENAI_API_KEY)


def parse_pairwise_output(text: str) -> dict[str, str]:
    parsed = parse_json_with_fallback(text, {"winner": "tie", "reason": "Parse error"})
    winner = parsed.get("winner", "tie")
    if winner not in {"A", "B", "tie"}:
        winner = "tie"
    return {"winner": winner, "reason": str(parsed.get("reason", "Parse error"))}


def parse_absolute_output(text: str) -> dict[str, float]:
    parsed = parse_json_with_fallback(
        text,
        {"accuracy": 3, "relevance": 3, "conciseness": 3, "helpfulness": 3},
    )
    dims = ["accuracy", "relevance", "conciseness", "helpfulness"]
    scores = {dim: int(parsed.get(dim, 3)) for dim in dims}
    overall = float(parsed.get("overall", sum(scores.values()) / 4))
    return {**scores, "overall": overall}


@dataclass
class JudgeResult:
    winner_after_swap: str
    run1_winner: str
    run2_winner: str
    run1_reason: str
    run2_reason: str


class PairwiseJudge:
    def __init__(self, model: str = JUDGE_MODEL) -> None:
        self.model = model
        self.client = _openai_client()

    def _call(self, prompt: str) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        return resp.choices[0].message.content or ""

    def judge_with_swap(self, question: str, answer_a: str, answer_b: str) -> JudgeResult:
        r1 = parse_pairwise_output(self._call(PAIRWISE_PROMPT.format(
            question=question, answer_a=answer_a, answer_b=answer_b
        )))
        r2 = parse_pairwise_output(self._call(PAIRWISE_PROMPT.format(
            question=question, answer_a=answer_b, answer_b=answer_a
        )))
        flipped = r2["winner"]
        if flipped == "A":
            flipped = "B"
        elif flipped == "B":
            flipped = "A"
        final_winner = r1["winner"] if r1["winner"] == flipped else "tie"
        return JudgeResult(
            winner_after_swap=final_winner,
            run1_winner=r1["winner"],
            run2_winner=flipped,
            run1_reason=r1["reason"],
            run2_reason=r2["reason"],
        )


class AbsoluteJudge:
    def __init__(self, model: str = JUDGE_MODEL) -> None:
        self.model = model
        self.client = _openai_client()

    def score(self, question: str, answer: str) -> dict[str, float]:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": ABSOLUTE_PROMPT.format(question=question, answer=answer)}],
            temperature=0.0,
        )
        return parse_absolute_output(resp.choices[0].message.content or "")
