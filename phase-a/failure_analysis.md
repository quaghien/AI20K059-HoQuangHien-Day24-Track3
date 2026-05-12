# Failure Cluster Analysis

## Bottom 10 Questions

| # | Question | Type | F | AR | CP | CR | Avg | Cluster |
|---|---|---|---|---|---|---|---|---|
| 1 | Dựa trên cả hai đoạn, hãy nêu các biện pháp bảo vệ dữ liệu cá nhân ở cấp độ lưu  | multi_context | 0.56 | 0.64 | 0.52 | 0.59 | 0.58 | C1 |
| 2 | Theo Snippet A, dữ liệu cá nhân bao gồm những loại thông tin nào và dữ liệu cá n | multi_context | 0.56 | 0.65 | 0.52 | 0.60 | 0.58 | C1 |
| 3 | Dựa trên Snippet A và Snippet B, hãy xác định: (1) Snippet A đang thể hiện loại  | multi_context | 0.56 | 0.66 | 0.52 | 0.61 | 0.59 | C1 |
| 4 | Dựa trên Snippet A và Snippet B, hãy xác định: (1) tên hoạt động sản xuất kinh d | multi_context | 0.58 | 0.64 | 0.54 | 0.60 | 0.59 | C1 |
| 5 | Theo Nghị định trong Snippet A, quy định về bảo vệ dữ liệu cá nhân áp dụng cho n | multi_context | 0.58 | 0.66 | 0.54 | 0.59 | 0.59 | C1 |
| 6 | Dựa trên cả Snippet A và Snippet B, hãy xác định nội dung nào được liệt kê về tr | multi_context | 0.60 | 0.65 | 0.52 | 0.61 | 0.59 | C1 |
| 7 | Dựa trên Snippet A và Snippet B, hãy xác định: (1) Snippet A đang viện dẫn những | multi_context | 0.60 | 0.64 | 0.52 | 0.63 | 0.60 | C1 |
| 8 | Theo Snippet A, “xử lý dữ liệu cá nhân tự động” là gì, và theo Snippet B thì chủ | multi_context | 0.60 | 0.66 | 0.52 | 0.62 | 0.60 | C1 |
| 9 | Dựa trên cả Snippet A và Snippet B, hãy xác định: trong các nội dung được nêu, đ | multi_context | 0.58 | 0.65 | 0.54 | 0.63 | 0.60 | C1 |
| 10 | Theo Snippet A, những loại dữ liệu cá nhân nào được liệt kê là dữ liệu nhạy cảm, | multi_context | 0.62 | 0.64 | 0.54 | 0.61 | 0.60 | C1 |

## Clusters Identified

### Cluster C1: Multi-hop reasoning failures
**Pattern:** Các câu reasoning hoặc multi-context cần nối nhiều facts giữa các chunk.
**Examples:**
- Câu hỏi đối chiếu nội dung giữa Nghị định và báo cáo tài chính.
- Câu hỏi cần tổng hợp nhiều điều kiện pháp lý trước khi trả lời.
**Root cause:** Retriever hiện chưa tối ưu cho câu hỏi cần nhiều parent contexts cùng lúc.
**Proposed fix:** Tăng `top_k`, giữ parent lookup, và thêm metadata filtering trước rerank.

### Cluster C2: Off-topic or weak retrieval grounding
**Pattern:** Câu simple nhưng answer chưa bám đúng chunk tốt nhất.
**Examples:**
- Câu hỏi định nghĩa trực tiếp nhưng answer paraphrase quá rộng.
- Câu hỏi factual ngắn bị kéo theo chunk lân cận không liên quan.
**Root cause:** Dense + hybrid retrieval vẫn có thể kéo context nhiễu cho câu ngắn.
**Proposed fix:** Siết prompt grounding, giảm context rác, và cân nhắc query rewrite cho factual questions.