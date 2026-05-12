from __future__ import annotations

import csv
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from openai import OpenAI

from src.config import DATA_DIR, JUDGE_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL, PHASE_A_DIR, SEED_TESTSET_PATH
from src.phase_a import ensure_phase_a_dirs, write_review_notes


def _openai_client() -> OpenAI:
    _ = OPENAI_BASE_URL
    return OpenAI(api_key=OPENAI_API_KEY)


def load_seed_testset() -> list[dict[str, str]]:
    if SEED_TESTSET_PATH.exists():
        return json.loads(SEED_TESTSET_PATH.read_text(encoding="utf-8"))
    return []


def build_snippets() -> list[dict[str, str]]:
    snippets = []
    for path in sorted(DATA_DIR.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 120]
        for idx, para in enumerate(paragraphs[:20]):
            snippets.append({"source": path.name, "text": para[:900], "snippet_id": f"{path.stem}-{idx}"})
    return snippets


def generate_with_llm() -> list[dict[str, str]]:
    client = _openai_client()
    snippets = build_snippets()
    simple_pool = snippets[:25]
    reasoning_pool = snippets[25:38]
    multi_pairs = [(snippets[i], snippets[-(i + 1)]) for i in range(12)]
    rows: list[dict[str, str]] = []

    for item in simple_pool:
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": "Tạo đúng 1 câu hỏi factual ngắn và 1 ground truth từ đoạn trích. Trả JSON."},
                {"role": "user", "content": item["text"]},
            ],
            temperature=0.2,
        )
        content = resp.choices[0].message.content or ""
        try:
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception:
            parsed = {
                "question": f"Tóm tắt nội dung chính của đoạn trong {item['source']} là gì?",
                "ground_truth": item["text"][:240],
            }
        rows.append({
            "question": parsed["question"],
            "ground_truth": parsed["ground_truth"],
            "contexts": str([item["text"]]),
            "evolution_type": "simple",
        })

    for item in reasoning_pool:
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {"role": "system", "content": "Tạo đúng 1 câu hỏi reasoning cần suy luận từ đoạn trích và 1 ground truth. Trả JSON."},
                {"role": "user", "content": item["text"]},
            ],
            temperature=0.3,
        )
        content = resp.choices[0].message.content or ""
        try:
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception:
            parsed = {
                "question": f"Từ đoạn trong {item['source']}, có thể suy ra điều gì quan trọng nhất?",
                "ground_truth": item["text"][:240],
            }
        rows.append({
            "question": parsed["question"],
            "ground_truth": parsed["ground_truth"],
            "contexts": str([item["text"]]),
            "evolution_type": "reasoning",
        })

    for left, right in multi_pairs:
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Tạo đúng 1 câu hỏi multi-context cần kết hợp 2 đoạn và 1 ground truth. Trả JSON.",
                },
                {"role": "user", "content": f"Snippet A:\n{left['text']}\n\nSnippet B:\n{right['text']}"},
            ],
            temperature=0.3,
        )
        content = resp.choices[0].message.content or ""
        try:
            parsed = json.loads(content.strip().removeprefix("```json").removesuffix("```").strip())
        except Exception:
            parsed = {
                "question": f"So sánh thông tin chính giữa {left['source']} và {right['source']}.",
                "ground_truth": f"{left['text'][:120]} ... {right['text'][:120]}",
            }
        rows.append({
            "question": parsed["question"],
            "ground_truth": parsed["ground_truth"],
            "contexts": str([left["text"], right["text"]]),
            "evolution_type": "multi_context",
        })
    return rows[:50]


def augment_rows(rows: list[dict[str, str]], target_size: int = 50) -> list[dict[str, str]]:
    if len(rows) >= target_size:
        return rows[:target_size]
    snippets = build_snippets()
    idx = 0
    while len(rows) < target_size and idx < len(snippets):
        item = snippets[idx]
        evolution_type = "simple" if len(rows) < 25 else "reasoning" if len(rows) < 38 else "multi_context"
        context_list = [item["text"]]
        if evolution_type == "multi_context" and len(snippets) > idx + 1:
            context_list.append(snippets[-(idx + 1)]["text"])
        rows.append({
            "question": f"Nội dung chính của đoạn trích trong {item['source']} là gì?",
            "ground_truth": item["text"][:280],
            "contexts": str(context_list),
            "evolution_type": evolution_type,
        })
        idx += 1
    return rows[:target_size]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--llm", action="store_true", help="Generate testset fresh with OpenAI instead of local seed.")
    args = parser.parse_args()
    ensure_phase_a_dirs()
    seed_rows = load_seed_testset()
    if args.llm:
        rows = generate_with_llm() if OPENAI_API_KEY else seed_rows
    else:
        rows = seed_rows or (generate_with_llm() if OPENAI_API_KEY else [])
    rows = augment_rows(rows)
    if not rows:
        raise RuntimeError("No local seed testset found and OPENAI_API_KEY is missing.")
    SEED_TESTSET_PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    out_path = PHASE_A_DIR / "testset_v1.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["question", "ground_truth", "contexts", "evolution_type"])
        writer.writeheader()
        writer.writerows(rows)
    write_review_notes(PHASE_A_DIR / "testset_review_notes.md")
    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
