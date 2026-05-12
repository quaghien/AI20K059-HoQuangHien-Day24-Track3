# Lab 24 — Full Evaluation & Guardrail System

**Họ tên:** Hồ Quang Hiển  
**MSSV:** 2A202600059

## Overview
Repo triển khai hệ thống Evaluation & Guardrail cho RAG pipeline trên corpus nội bộ (Nghị định 13/2023 và Báo cáo tài chính). Hệ thống gồm 4 phase: RAGAS evaluation, LLM-as-judge, guardrails stack, và blueprint document. Dense retrieval dùng `text-embedding-3-small`; judge, generation và guardrail classification đều dùng GPT family. Guardrails bao gồm: PII redaction bằng regex VN, topic validator theo keyword, injection detector đa pattern, và output safety guard theo heuristic LlamaGuard-style.

Mọi phase đều có script riêng, output đúng thư mục, test nội bộ không phụ thuộc API, và có chế độ offline để kiểm tra pipeline artifact trước khi điền key thật.

## Setup
```bash
pip install -r requirements.txt
```

Điền key vào file `.env`:
```bash
OPENAI_API_KEY=...
OPENAI_JUDGE_MODEL=gpt-4o-mini
OPENAI_GUARD_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
```

## Run
```bash
python scripts/generate_testset.py
python scripts/run_phase_a.py --offline
python scripts/run_phase_b.py
python scripts/run_phase_c.py
python scripts/run_benchmark.py
pytest
```

## Results Summary

### Phase A (RAGAS Evaluation)
- Test set: 50 câu (50% simple, 25% reasoning, 25% multi-context)
- Faithfulness: 0.71 | Answer Relevancy: 0.72 | Context Precision: 0.64 | Context Recall: 0.70
- **Tổng cost eval:** ~$0.80 (50 questions × 4 metrics × gpt-4o-mini, ước tính offline)
- **Observation:** Context Precision (0.64) < target 0.70 → retriever kéo context nhiễu cho câu ngắn. Answer Relevancy (0.72) < target 0.80 → câu multi-context cần thêm re-ranking. Xem `phase-a/failure_analysis.md` để biết 3 failure clusters.

### Phase B (LLM-as-Judge)
- Pairwise: 30 câu với swap-and-average (position bias mitigated)
- Absolute scoring: 4 dimensions (accuracy, relevance, conciseness, helpfulness)
- Cohen's kappa vs human: -0.14 (worse than chance — see root cause in `phase-b/judge_bias_report.md`)
- **Root cause kappa thấp:** Answers A/B trong test set là stub text gần giống nhau → judge đánh tie 50%, human label theo logic khác. Sẽ cải thiện với RAG answers thật.
- Position bias: A thắng 33% ở run1, giảm xuống 16.7% sau swap-and-average.

### Phase C (Guardrails Stack)
- PII detection rate: 10/10 = 100% (latency P95 < 5ms — pure regex, không cần API)
- Topic validator: keyword-based, từ chối gracefully với thông báo hướng dẫn
- Adversarial defense: 20/20 = 100% detection rate (DAN, roleplay, split, encoding, indirect)
- Output guard (LlamaGuard-style): 10/10 unsafe detected, 0/10 false positive trên safe outputs
- Latency benchmark (100 queries): L1 P95 < 50ms ✓, L3 P95 < 100ms ✓
- Xem `phase-c/latency_benchmark.csv` và `phase-c/output_guard_results.csv`

### Phase D (Blueprint)
- 8 SLOs định nghĩa với alert thresholds và severity
- Architecture diagram (Mermaid) — defense-in-depth 4 layers
- Alert playbook: 3 incidents (faithfulness drop, adversarial bypass, P95 latency spike)
- Cost estimate: ~$193/month tại 100k queries/month

## Demo Video
https://youtu.be/JToeo4TzkEI

## Lessons Learned
RAGAS evaluation giúp phát hiện rằng context precision là điểm yếu nhất của RAG pipeline — điều mà "demo chạy được" hoàn toàn che giấu. LLM-as-judge với swap-and-average là cách thực tế nhất để giảm position bias, nhưng cần human calibration với answer thật (không phải stub) để kappa có ý nghĩa. Guardrails với regex VN + injection pattern matching đạt 95% adversarial defense rate mà không cần API — điều này rất quan trọng cho latency budget.
