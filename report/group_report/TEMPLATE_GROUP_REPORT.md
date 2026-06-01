# Group Report: Lab 3 - Production-Grade Agentic System

- **Team Name**: 103
- **Team Members**: Kim Hồng Giang, Lê Quốc Bảo, Lê Quang Miền
- **Deployment Date**: [2026-06-01]

---

## 1. Executive Summary

*Brief overview of the agent's goal and success rate compared to the baseline chatbot.*

- **Success Rate**: 95% trên 10 test cases
- **Key Outcome**: Agent xử lý tốt các câu hỏi nhiều bước nhờ vòng lặp Thought → Action → Observation và gọi tool đúng ngữ cảnh, ổn định hơn so với chatbot baseline.

---

## 2. System Architecture & Tooling

### 2.1 ReAct Loop Implementation
Mô hình ReAct chạy theo vòng lặp Thought → Action → Observation: Agent phân tích yêu cầu, chọn tool phù hợp để gọi, nhận quan sát từ tool và cập nhật suy luận. Vòng lặp này lặp lại cho đến khi đủ thông tin để trả lời cuối cùng cho người dùng.

### 2.2 Tool Definitions (Inventory)
| Tool Name | Input Format | Use Case |
| :--- | :--- | :--- |
| `search_product` | `json` | Tìm sản phẩm theo từ khóa và giá tối đa (tùy chọn). |
| `check_stock` | `json` | Kiểm tra tồn kho theo `product_id` và `quantity`. |
| `apply_discount` | `json` | Áp mã giảm giá cho giá sản phẩm. |
| `calculate_shipping` | `json` | Tính phí vận chuyển theo khối lượng và địa điểm. |
| `calculator` | `json` | Tính toán biểu thức số học an toàn. |

### 2.3 LLM Providers Used
- **Primary**: GPT-4o
- **Secondary (Backup)**: Chưa triển khai (không có fallback)

---

## 3. Telemetry & Performance Dashboard

*Analyze the industry metrics collected during the final test run.*

- **Average Latency (P50)**: 1168.5 ms
- **Max Latency (P99)**: 2081.6 ms
- **Average Tokens per Task**: 3867.7 tokens
- **Total Cost of Test Suite**: Chưa đo

---

## 4. Root Cause Analysis (RCA) - Failure Traces

*Deep dive into why the agent failed.*

### Case Study: Bị chặn do giới hạn số bước
- **Input**: "Tôi muốn mua 2 chiếc MacBook Air M2, giao đến Hà Nội. Nếu dùng mã STUDENT5 thì tổng tiền cuối cùng là bao nhiêu? Hãy kiểm tra tồn kho trước khi tính tiền."
- **Observation**: Agent dừng ở `max_steps_reached` khi cấu hình `max_steps=5`, trong khi bài toán cần 6-7 bước để hoàn tất.
- **Root Cause**: Giới hạn số bước đặt quá thấp so với độ dài chuỗi thao tác (tìm sản phẩm → kiểm tra tồn kho → áp mã → tính tổng → tính phí ship).

---

## 5. Ablation Studies & Experiments

### Experiment 1: Prompt v1 vs Prompt v2
- **Diff**: Bổ sung hướng dẫn “tính toán số học trước khi gọi tool” và nhắc kiểm tra định dạng tham số hợp lệ.
- **Result**: Giảm lỗi gọi tool sai tham số và giảm số lần dừng sớm do xử lý lại bước.

### Experiment 2 (Bonus): Chatbot vs Agent
| Case | Chatbot Result | Agent Result | Winner |
| :--- | :--- | :--- | :--- |
| Simple Q | Đúng | Đúng | Hòa |
| Multi-step | Thiếu bước/thiếu kiểm tra | Đúng (đầy đủ bước) | **Agent** |

---

## 6. Production Readiness Review

*Considerations for taking this system to a real-world environment.*

- **Security**: Cần sanitize user input trước khi đưa vào LLM để chống prompt injection. Giới hạn kích thước output từ `ast.literal_eval` tránh OOM attack. Restrict CORS về domain cụ thể, không mở `*`.
- **Guardrails**: Giới hạn `max_steps` tối đa 10 bước để kiểm soát chi phí API. Thêm rate limiting per-IP để chống abuse. Triển khai token budget và cost circuit breaker ngắt khi vượt ngưỡng. Set timeout 30-60s cho mỗi LLM call. Quản lý context window bằng sliding window hoặc summarization để tránh overflow.
- **Scaling**: Chuyển endpoints sang `async def` và dùng async HTTP client để xử lý đồng thời. Thêm Redis cache cho tool results và LLM responses giảm latency. Export metrics ra Prometheus/Datadog thay vì chỉ lưu in-memory. Transition sang LangGraph cho complex branching và multi-agent orchestration khi hệ thống lớn hơn.

---

> [!NOTE]
> Submit this report by renaming it to `GROUP_REPORT_[TEAM_NAME].md` and placing it in this folder.
