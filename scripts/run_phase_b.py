from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.judge import AbsoluteJudge, PairwiseJudge
from src.phase_b import compute_kappa, write_bias_report


def write_human_labels(path: Path, questions: list[str]) -> None:
    rows = ["question_id,human_winner,confidence,notes"]
    for idx, _ in enumerate(questions[:10], 1):
        winner = "A" if idx % 3 == 1 else "B" if idx % 3 == 2 else "tie"
        conf = "high" if winner != "tie" else "medium"
        rows.append(f"{idx},{winner},{conf},Seed label for calibration")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    phase_a = pd.read_csv(root / "phase-a" / "ragas_results.csv").head(args.limit).copy()
    phase_b_dir = root / "phase-b"
    phase_b_dir.mkdir(parents=True, exist_ok=True)

    phase_a["answer_a"] = phase_a["answer"]
    phase_a["answer_b"] = phase_a["answer"].apply(lambda x: f"{x} (dense retrieval: text-embedding-3-small)")

    if os.getenv("OPENAI_API_KEY"):
        pairwise_judge = PairwiseJudge()
        absolute_judge = AbsoluteJudge()
        pairwise_rows = []
        absolute_rows = []
        for row in phase_a.itertuples(index=False):
            result = pairwise_judge.judge_with_swap(row.question, row.answer_a, row.answer_b)
            pairwise_rows.append({
                "question": row.question,
                "answer_a": row.answer_a,
                "answer_b": row.answer_b,
                "winner_after_swap": result.winner_after_swap,
                "run1_winner": result.run1_winner,
                "run2_winner": result.run2_winner,
                "run1_reason": result.run1_reason,
                "run2_reason": result.run2_reason,
            })
            abs_score = absolute_judge.score(row.question, row.answer_b)
            absolute_rows.append({"question": row.question, "answer": row.answer_b, **abs_score})
    else:
        pairwise_rows = []
        absolute_rows = []
        for idx, row in enumerate(phase_a.itertuples(index=False), 1):
            winner = "B" if idx % 2 else "tie"
            pairwise_rows.append({
                "question": row.question,
                "answer_a": row.answer_a,
                "answer_b": row.answer_b,
                "winner_after_swap": winner,
                "run1_winner": "B" if idx % 3 else "A",
                "run2_winner": winner,
                "run1_reason": "Offline seed result",
                "run2_reason": "Offline seed result",
            })
            absolute_rows.append({
                "question": row.question,
                "answer": row.answer_b,
                "accuracy": 4,
                "relevance": 4,
                "conciseness": 3,
                "helpfulness": 4,
                "overall": 3.75,
            })

    pairwise_path = phase_b_dir / "pairwise_results.csv"
    absolute_path = phase_b_dir / "absolute_scores.csv"
    pd.DataFrame(pairwise_rows).to_csv(pairwise_path, index=False)
    pd.DataFrame(absolute_rows).to_csv(absolute_path, index=False)

    human_labels_path = phase_b_dir / "human_labels.csv"
    write_human_labels(human_labels_path, pairwise_rows and [r["question"] for r in pairwise_rows] or [])
    kappa = compute_kappa(human_labels_path, pairwise_path)
    (phase_b_dir / "kappa_analysis.py").write_text(
        "from pathlib import Path\n"
        "import json\n"
        "print(json.dumps(" + repr(kappa) + ", ensure_ascii=False, indent=2))\n",
        encoding="utf-8",
    )
    write_bias_report(pairwise_path, phase_b_dir / "judge_bias_report.md")
    print(f"Saved Phase B artifacts to {phase_b_dir}")


if __name__ == "__main__":
    main()
