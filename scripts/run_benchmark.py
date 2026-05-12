from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "phase-c" / "latency_benchmark.csv"
    df = pd.read_csv(path)
    for col in ["L1", "L2", "L3", "total"]:
        if col in df.columns:
            print(
                f"{col}: "
                f"P50={df[col].quantile(0.50):.1f}ms "
                f"P95={df[col].quantile(0.95):.1f}ms "
                f"P99={df[col].quantile(0.99):.1f}ms"
            )


if __name__ == "__main__":
    main()
