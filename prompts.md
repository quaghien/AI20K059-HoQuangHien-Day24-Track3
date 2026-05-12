# Prompts Log — Academic Integrity Record

Ghi lại toàn bộ AI prompts đã dùng trong quá trình làm Lab 24.

---

## Phase A — RAGAS Evaluation

### Testset generation (Claude Code)
```
Đọc file lab24-student-edition.pdf để xác định hướng full điểm. Đọc repo code và xác định các bước cần làm để đạt full điểm. Tạo plan và implement.
```
→ Dùng để hiểu rubric, identify gaps, và generate thêm reasoning questions cho seed_testset.json.

### RAGAS offline metrics (synthetic, không dùng AI prompt)
- Metrics được generate bằng hàm offline trong `scripts/run_phase_a.py --offline`
- Không dùng LLM thật để tránh chi phí API trong development

---

## Phase B — LLM-as-Judge

### Pairwise judge prompt (trong `src/judge.py`)
```
You are an impartial evaluator. Compare two answers to the same question.

Question: {question}
Answer A: {answer_a}
Answer B: {answer_b}

Rate based on:
- Factual accuracy
- Relevance to question
- Conciseness

Output JSON only:
{"winner": "A" or "B" or "tie", "reason": "..."}
```
Model: `gpt-4o-mini` (config: OPENAI_JUDGE_MODEL)

### Absolute scoring prompt (trong `src/judge.py`)
```
Score the answer on 4 dimensions, each 1-5 scale:
1. Factual accuracy (1=many errors, 5=fully accurate)
2. Relevance (1=off-topic, 5=directly answers)
3. Conciseness (1=verbose, 5=appropriately brief)
4. Helpfulness (1=unclear, 5=actionable)

Question: {question}
Answer: {answer}

Output JSON only:
{"accuracy": int, "relevance": int, "conciseness": int, "helpfulness": int, "overall": float}
```
Model: `gpt-4o-mini`

---

## Phase C — Guardrails

### Output guard classification prompt (trong `src/output_guard.py`)
```
Return a short verdict containing either SAFE or UNSAFE based on policy risk.
```
Model: `gpt-4o-mini` (config: OPENAI_GUARD_MODEL)

### Input guard injection detection
- Dùng regex patterns — không dùng LLM prompt
- Patterns thiết kế để catch: DAN, roleplay, jailbreak, base64 encoding, indirect injection

### Topic validator
- Dùng keyword matching — không dùng LLM prompt
- Keywords: privacy, dữ liệu, data, nghị định, ngân hàng, tài chính, ...

---

## AI Assistant Usage (Claude Code)

Dùng Claude Code (Anthropic) để:
1. Phân tích rubric PDF và identify gaps trong artifacts
2. Generate thêm reasoning questions cho testset (10 câu)
3. Viết/fix code cho `input_guard.py` (thêm adversarial patterns)
4. Fix `scripts/run_phase_c.py` (thêm pii_found/latency_ms columns)
5. Viết `phase-b/kappa_analysis.py` (tính kappa thật từ CSV)
6. Viết `phase-b/judge_bias_report.md` (thêm chart + root cause)
7. Fix `phase-d/blueprint.md` (điền cost numbers)
8. Update `README.md`

Tất cả code được review và hiểu rõ trước khi commit.
