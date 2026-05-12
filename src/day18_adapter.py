from __future__ import annotations

import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from openai import OpenAI
from rank_bm25 import BM25Okapi

from src.config import DATA_DIR, EMBEDDING_MODEL, GENERATION_MODEL, OPENAI_API_KEY, OPENAI_BASE_URL


def _openai_client() -> OpenAI:
    _ = OPENAI_BASE_URL
    return OpenAI(api_key=OPENAI_API_KEY)


def _tokenize(text: str) -> list[str]:
    return text.lower().replace("\n", " ").split()


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    numerator = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return numerator / (norm_a * norm_b)


@dataclass
class ChunkRecord:
    text: str
    source: str
    parent_id: str


class IndependentRAGAdapter:
    def __init__(self) -> None:
        self.client = _openai_client()
        self._chunks: list[ChunkRecord] = []
        self._bm25: BM25Okapi | None = None
        self._embeddings: list[list[float]] = []
        self._built = False

    def _load_docs(self) -> list[tuple[str, str]]:
        docs = []
        for path in sorted(DATA_DIR.glob("*.md")):
            docs.append((path.name, path.read_text(encoding="utf-8")))
        return docs

    def _chunk_doc(self, source: str, text: str, parent_size: int = 1600, child_size: int = 500) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        parent_text = ""
        parent_idx = 0
        for para in paragraphs:
            if len(parent_text) + len(para) > parent_size and parent_text:
                chunks.extend(self._split_parent(source, parent_text, parent_idx, child_size))
                parent_idx += 1
                parent_text = ""
            parent_text += para + "\n\n"
        if parent_text.strip():
            chunks.extend(self._split_parent(source, parent_text, parent_idx, child_size))
        return chunks

    def _split_parent(self, source: str, parent_text: str, parent_idx: int, child_size: int) -> list[ChunkRecord]:
        parent_id = f"{source}:{parent_idx}"
        children: list[ChunkRecord] = []
        for start in range(0, len(parent_text), child_size):
            child = parent_text[start:start + child_size].strip()
            if child:
                children.append(ChunkRecord(text=child, source=source, parent_id=parent_id))
        return children

    def build(self) -> None:
        if self._built:
            return
        docs = self._load_docs()
        for source, text in docs:
            self._chunks.extend(self._chunk_doc(source, text))
        tokenized = [_tokenize(chunk.text) for chunk in self._chunks]
        self._bm25 = BM25Okapi(tokenized)
        texts = [chunk.text for chunk in self._chunks]
        resp = self.client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
        self._embeddings = [item.embedding for item in resp.data]
        self._built = True

    def _retrieve(self, question: str, top_k: int = 5) -> list[ChunkRecord]:
        self.build()
        assert self._bm25 is not None
        bm25_scores = self._bm25.get_scores(_tokenize(question))
        q_emb = self.client.embeddings.create(model=EMBEDDING_MODEL, input=[question]).data[0].embedding
        fused = []
        for idx, chunk in enumerate(self._chunks):
            dense_score = _cosine_similarity(q_emb, self._embeddings[idx])
            hybrid = float(bm25_scores[idx]) + (dense_score * 5.0)
            fused.append((hybrid, chunk))
        fused.sort(key=lambda x: x[0], reverse=True)
        selected = []
        seen_parents: set[str] = set()
        for _, chunk in fused:
            if chunk.parent_id in seen_parents:
                continue
            selected.append(chunk)
            seen_parents.add(chunk.parent_id)
            if len(selected) >= top_k:
                break
        return selected

    def run_rag(self, question: str) -> dict[str, Any]:
        started = time.perf_counter()
        contexts = self._retrieve(question)
        context_text = "\n\n---\n\n".join(
            f"[{item.source}]\n{item.text}" for item in contexts
        )
        resp = self.client.chat.completions.create(
            model=GENERATION_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Bạn là trợ lý RAG cho tài liệu pháp lý và tài chính tiếng Việt. "
                        "Chỉ dùng thông tin trong CONTEXT. Nếu không đủ bằng chứng thì nói rõ không tìm thấy trong tài liệu."
                    ),
                },
                {
                    "role": "user",
                    "content": f"CONTEXT:\n{context_text}\n\nQUESTION: {question}",
                },
            ],
            temperature=0.0,
        )
        answer = resp.choices[0].message.content or ""
        latency_ms = (time.perf_counter() - started) * 1000
        return {
            "answer": answer.strip(),
            "contexts": [item.text for item in contexts],
            "source_ids": [item.parent_id for item in contexts],
            "latency_ms": latency_ms,
        }


class StubRAGAdapter:
    """Fast local fallback for tests and offline smoke runs."""

    def run_rag(self, question: str) -> dict[str, Any]:
        answer = f"Stub answer for: {question}"
        contexts = [f"Stub context for {question}"]
        return {"answer": answer, "contexts": contexts, "source_ids": None, "latency_ms": 1.0}
