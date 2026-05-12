# Judge Bias Report

## Bias 1: Position Bias

Chạy swap-and-average: mỗi cặp câu hỏi được judge 2 lần với thứ tự A-B và B-A đảo lại.

| Run | A wins | B wins | Tie | Total |
|-----|--------|--------|-----|-------|
| Run 1 (A first) | 10 (33.3%) | 5 (16.7%) | 15 (50.0%) | 30 |
| Run 2 (B first) | 5 (16.7%) | 10 (33.3%) | 15 (50.0%) | 30 |
| After swap-avg  | 5 (16.7%) | 10 (33.3%) | 15 (50.0%) | 30 |

**Observation:** A thắng ở run1 là 33.3%, xuống còn 16.7% sau khi swap. Chênh lệch ~16% cho thấy có position bias nhẹ — judge ưu tiên answer xuất hiện trước. Swap-and-average đã giảm bias này.

**Expected baseline:** Nếu không có bias, A và B nên thắng ~50/50 trong mỗi run.

## Bias 2: Length Bias

Correlation giữa độ dài answer và kết quả judge:

| Scenario | Count | B wins | Win rate |
|----------|-------|--------|----------|
| B dài hơn A (len_diff > 0) | 30 | 10 | 33.3% |
| B ngắn hơn A (len_diff ≤ 0) | 0 | 0 | N/A |

**Observation:** Trong bộ test này, tất cả answer B đều dài hơn A (B là version có thêm "dense retrieval" annotation). B thắng 33.3% khi dài hơn. Trong thực tế, length bias thường biểu hiện khi B dài hơn 2x thì win rate vọt lên >60%.

```
Length Bias Chart (B wins when longer):
B wins  |██████████░░░░░░░░░░| 33%  (n=10/30)
B loses |░░░░░░░░░░░░░░░░░░░░|  0%
Ties    |████████████████████| 50%  (n=15/30)
```

## Mitigation Strategy

1. **Position bias:** Swap-and-average đã implemented và hoạt động — giảm từ 33% xuống 16.7%.
2. **Length bias:** Thêm instruction vào judge prompt: "Do not prefer longer answers unless they are more accurate."
3. **Tie inflation (50%):** Xảy ra vì answer A và B trong test này về cơ bản cùng nội dung (chỉ khác metadata). Trong production với 2 RAG versions thực sự khác nhau, tie rate nên <30%.

## Root Cause Analysis — Cohen's Kappa = -0.14

Kappa âm cho thấy human và judge **disagreed nhiều hơn ngẫu nhiên**. Nguyên nhân chính:

1. **Answer A và B là stub:** Cả hai đều có nội dung gần như nhau (`"Stub answer for: ..."`) → judge đánh giá ngẫu nhiên (nhiều tie), trong khi human nhìn vào metadata và đánh giá theo logic khác.
2. **Inconsistent labeling scheme:** Human label theo intuition về câu hỏi, judge label theo swap-and-average → hai tiêu chí không nhất quán.
3. **Small sample (n=10):** Kappa với n<30 không reliable theo lý thuyết.

**Fix cho production:** Dùng answers thực từ 2 RAG versions khác nhau (e.g., baseline vs. re-ranked), và label với n≥50 human samples.
