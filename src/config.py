from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[1]
load_dotenv(ROOT_DIR / ".env")

DATA_DIR = ROOT_DIR / "data"
PHASE_A_DIR = ROOT_DIR / "phase-a"
PHASE_B_DIR = ROOT_DIR / "phase-b"
PHASE_C_DIR = ROOT_DIR / "phase-c"
PHASE_D_DIR = ROOT_DIR / "phase-d"
SEED_TESTSET_PATH = ROOT_DIR / "data" / "seed_testset.json"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip()
if not OPENAI_BASE_URL:
    os.environ.pop("OPENAI_BASE_URL", None)
JUDGE_MODEL = os.getenv("OPENAI_JUDGE_MODEL", "gpt-5.4-nano")
GUARD_MODEL = os.getenv("OPENAI_GUARD_MODEL", "gpt-5.4-nano")
GENERATION_MODEL = os.getenv("OPENAI_GENERATION_MODEL", "gpt-5.4-nano")
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

TARGET_THRESHOLDS = {
    "faithfulness": 0.85,
    "answer_relevancy": 0.80,
    "context_precision": 0.70,
    "context_recall": 0.75,
}

TOPIC_KEYWORDS = {
    "privacy", "dữ liệu", "data", "nghị định", "ngân hàng", "báo cáo",
    "tài chính", "bctc", "cá nhân", "compliance", "bảo vệ", "thông tin",
}

SAFE_REFUSAL = (
    "Mình chỉ hỗ trợ câu hỏi liên quan tới bộ tài liệu pháp lý và tài chính trong bài lab này. "
    "Bạn có thể hỏi lại theo hướng dữ liệu cá nhân, nghị định hoặc báo cáo tài chính."
)
