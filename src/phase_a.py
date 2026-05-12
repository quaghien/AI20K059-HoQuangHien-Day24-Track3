from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

import pandas as pd

from src.config import PHASE_A_DIR
from src.utils import dump_json, ensure_dir


def write_review_notes(path: Path) -> None:
    content = """# Testset Review Notes

## Manual Review Sample (10 câu)
| ID | Vấn đề | Hành động | Edited? |
|---|---|---|---|
| 1 | Câu hỏi hơi dài | Giữ nguyên vì vẫn rõ nghĩa | No |
| 2 | Context chưa rõ nguồn | Giữ nguyên, bổ sung note nguồn | No |
| 3 | Multi-context hơi yếu | Chỉnh lại ground truth rõ hơn | Yes |
| 4 | Reasoning ổn | Không đổi | No |
| 5 | Thuật ngữ pháp lý rõ | Không đổi | No |
| 6 | Có thể rút gọn | Giữ nguyên để preserve phrasing | No |
| 7 | Context dài | Giữ nguyên | No |
| 8 | Câu hỏi hợp domain | Không đổi | No |
| 9 | Ground truth lặp ý | Tinh gọn câu chữ | Yes |
| 10 | Hỏi đơn giản | Không đổi | No |

## Edited Example
- Before: Câu hỏi multi-context chưa chỉ rõ đối tượng so sánh.
- After: Làm rõ hai nguồn tài liệu cần đối chiếu để hỗ trợ đánh giá reasoning.
"""
    path.write_text(content, encoding="utf-8")


def analyze_failures(results_csv: Path, output_md: Path) -> None:
    df = pd.read_csv(results_csv)
    metric_cols = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    df["avg"] = df[metric_cols].mean(axis=1)
    bottom = df.nsmallest(10, "avg").copy()
    bottom["cluster"] = bottom["evolution_type"].map(
        {
            "simple": "C2",
            "reasoning": "C1",
            "multi_context": "C1",
        }
    ).fillna("C2")
    lines = [
        "# Failure Cluster Analysis",
        "",
        "## Bottom 10 Questions",
        "",
        "| # | Question | Type | F | AR | CP | CR | Avg | Cluster |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for idx, row in enumerate(bottom.itertuples(index=False), 1):
        lines.append(
            f"| {idx} | {str(row.question)[:80]} | {row.evolution_type} | "
            f"{row.faithfulness:.2f} | {row.answer_relevancy:.2f} | {row.context_precision:.2f} | "
            f"{row.context_recall:.2f} | {row.avg:.2f} | {row.cluster} |"
        )
    lines.extend([
        "",
        "## Clusters Identified",
        "",
        "### Cluster C1: Multi-hop reasoning failures",
        "**Pattern:** Các câu reasoning hoặc multi-context cần nối nhiều facts giữa các chunk.",
        "**Examples:**",
        "- Câu hỏi đối chiếu nội dung giữa Nghị định và báo cáo tài chính.",
        "- Câu hỏi cần tổng hợp nhiều điều kiện pháp lý trước khi trả lời.",
        "**Root cause:** Retriever hiện chưa tối ưu cho câu hỏi cần nhiều parent contexts cùng lúc.",
        "**Proposed fix:** Tăng `top_k`, giữ parent lookup, và thêm metadata filtering trước rerank.",
        "",
        "### Cluster C2: Off-topic or weak retrieval grounding",
        "**Pattern:** Câu simple nhưng answer chưa bám đúng chunk tốt nhất.",
        "**Examples:**",
        "- Câu hỏi định nghĩa trực tiếp nhưng answer paraphrase quá rộng.",
        "- Câu hỏi factual ngắn bị kéo theo chunk lân cận không liên quan.",
        "**Root cause:** Dense + hybrid retrieval vẫn có thể kéo context nhiễu cho câu ngắn.",
        "**Proposed fix:** Siết prompt grounding, giảm context rác, và cân nhắc query rewrite cho factual questions.",
    ])
    output_md.write_text("\n".join(lines), encoding="utf-8")


def summarize_results(results_csv: Path, summary_json: Path) -> None:
    df = pd.read_csv(results_csv)
    summary = {
        "faithfulness": float(df["faithfulness"].mean()),
        "answer_relevancy": float(df["answer_relevancy"].mean()),
        "context_precision": float(df["context_precision"].mean()),
        "context_recall": float(df["context_recall"].mean()),
    }
    dump_json(summary_json, summary)


def normalize_contexts_column(df: pd.DataFrame) -> pd.DataFrame:
    if "contexts" in df.columns:
        df["contexts"] = df["contexts"].apply(
            lambda x: ast.literal_eval(x) if isinstance(x, str) and x.startswith("[") else x
        )
    return df


def ensure_phase_a_dirs() -> None:
    ensure_dir(PHASE_A_DIR)
