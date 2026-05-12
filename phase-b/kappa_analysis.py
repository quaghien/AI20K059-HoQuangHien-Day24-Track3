"""Compute Cohen's kappa between human labels and LLM judge."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

ROOT = Path(__file__).resolve().parents[1]


def _normalize(label: str) -> str:
    label = str(label).strip().upper()
    if label in {"A", "ANSWER_A"}:
        return "A"
    if label in {"B", "ANSWER_B"}:
        return "B"
    return "tie"


def main() -> None:
    human_df = pd.read_csv(ROOT / "phase-b" / "human_labels.csv")
    judge_df = pd.read_csv(ROOT / "phase-b" / "pairwise_results.csv")

    n = len(human_df)
    human_labels = [_normalize(x) for x in human_df["human_winner"].tolist()]
    judge_labels = [_normalize(x) for x in judge_df.head(n)["winner_after_swap"].tolist()]

    kappa = cohen_kappa_score(human_labels, judge_labels)

    if kappa < 0:
        interpretation = "worse_than_chance"
    elif kappa < 0.2:
        interpretation = "slight"
    elif kappa < 0.4:
        interpretation = "fair"
    elif kappa < 0.6:
        interpretation = "moderate"
    elif kappa < 0.8:
        interpretation = "substantial"
    else:
        interpretation = "almost_perfect"

    result = {"kappa": round(kappa, 4), "interpretation": interpretation, "n_samples": n}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
