from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.config import TARGET_THRESHOLDS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", default="phase-a/ragas_results.csv")
    args = parser.parse_args()

    path = Path(__file__).resolve().parents[1] / args.results
    df = pd.read_csv(path)
    means = {metric: float(df[metric].mean()) for metric in TARGET_THRESHOLDS}
    failed = {metric: score for metric, score in means.items() if score < TARGET_THRESHOLDS[metric]}
    for metric, score in means.items():
        print(f"{metric}={score:.3f} target={TARGET_THRESHOLDS[metric]:.3f}")
    if failed:
        print(f"Eval gate failed: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
