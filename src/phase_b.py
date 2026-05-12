from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.metrics import cohen_kappa_score

from src.utils import dump_json


def compute_kappa(human_csv: Path, pairwise_csv: Path) -> dict[str, float | str]:
    human = pd.read_csv(human_csv)
    pairwise = pd.read_csv(pairwise_csv).head(len(human))
    score = cohen_kappa_score(human["human_winner"], pairwise["winner_after_swap"])
    interpretation = (
        "almost perfect" if score >= 0.81 else
        "substantial" if score >= 0.61 else
        "moderate" if score >= 0.41 else
        "fair" if score >= 0.21 else
        "slight"
    )
    return {"kappa": float(score), "interpretation": interpretation}


def write_bias_report(pairwise_csv: Path, output_md: Path) -> None:
    df = pd.read_csv(pairwise_csv)
    a_win_rate = (df["run1_winner"] == "A").mean() if len(df) else 0.0
    tie_rate = (df["winner_after_swap"] == "tie").mean() if len(df) else 0.0
    lines = [
        "# Judge Bias Report",
        "",
        "## Quantified Biases",
        "",
        "| Bias | Observation |",
        "|---|---|",
        f"| Position bias | Answer A thắng ở run1: {a_win_rate:.2%} |",
        f"| Tie inflation | Tỷ lệ tie sau swap-and-average: {tie_rate:.2%} |",
        "",
        "## Notes",
        "- Swap-and-average đã được bật để giảm position bias.",
        "- Nếu tie rate quá cao, nên xem lại độ phân biệt giữa Version A và Version B.",
    ]
    output_md.write_text("\n".join(lines), encoding="utf-8")
