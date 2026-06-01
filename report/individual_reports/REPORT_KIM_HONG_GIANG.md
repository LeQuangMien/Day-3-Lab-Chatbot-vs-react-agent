# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Kim Hồng Giang
- **Student ID**: 2A202600600
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

*Describe your specific contribution to the codebase (e.g., implemented a specific tool, fixed the parser, etc.).*

- **Modules Implementated**: `app.js`, `index.html`, `style.css`
- **Code Highlights**: Chuyển mode Agent/LLM và cập nhật UI ở [app.js](app.js#L43-L70) + cấu trúc nút mode ở [index.html](index.html#L25-L82); gọi API và parse `steps` (Thought/Action/Observation) ở [app.js](app.js#L161-L186); render khối thinking steps trong bubble ở [app.js](app.js#L232-L255); UI/UX cho welcome, message bubble ở [style.css](style.css#L448-L629).
- **Documentation**: Frontend nhận input, gọi `POST /agent` khi ở Agent mode, parse mảng `steps` để hiển thị Thought → Action → Observation, rồi render vào bubble trả lời. Khi ở LLM mode, frontend gọi `POST /llm` và render câu trả lời trực tiếp, còn phần layout/UX (welcome screen, message styles, mode toggle) được định nghĩa ở [index.html](index.html#L98-L195) và [style.css](style.css#L134-L629).

---

## II. Debugging Case Study (10 Points)

*Analyze a specific failure event you encountered during the lab using the logging system.*

- **Problem Description**: Bài toán mua 2 MacBook Air M2 cần nhiều bước (tìm sản phẩm, kiểm tra tồn kho, áp mã giảm giá, tính tổng, tính phí ship). Agent đặt `max_steps=5` nên bị dừng khi vẫn chưa xong (cần tới bước 6-7).
- **Log Source**: Lượt chạy đầu bị dừng ở max steps [logs/2026-06-01.log](logs/2026-06-01.log#L6-L21); sau khi tăng `max_steps` lên 10 thì hoàn thành ở bước 7 [logs/2026-06-01.log](logs/2026-06-01.log#L22-L38).
- **Diagnosis**: Câu hỏi gồm nhiều hành động liên tiếp nên cần nhiều step hơn cấu hình mặc định (5). Giới hạn step quá thấp gây kết thúc sớm (`max_steps_reached`).
- **Solution**: Tăng giới hạn `max_steps` từ 5 lên 10 trong cấu hình Agent, sau đó lượt chạy hoàn thành đầy đủ các bước tính toán và trả về kết quả cuối.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

*Reflect on the reasoning capability difference.*

1.  **Reasoning**: Khối `Thought` giúp Agent tách nhỏ bài toán, nêu rõ mục tiêu từng bước (tìm sản phẩm → kiểm tra tồn → áp mã → tính ship), nên kiểm soát tốt hơn so với Chatbot trả lời một lượt dễ thiếu bước.
2.  **Reliability**: Agent có thể kém hơn khi cấu hình `max_steps` thấp hoặc khi tool-call bị lỗi cú pháp; Chatbot đôi khi trả lời nhanh nhưng có thể bỏ qua kiểm tra tồn kho hoặc phí ship.
3.  **Observation**: Phản hồi từ tool (tồn kho đủ, giá sau giảm, phí ship) giúp Agent điều chỉnh bước tiếp theo và sửa lỗi nhập tham số, đảm bảo kết quả cuối cùng chính xác hơn.

---

## IV. Future Improvements (5 Points)

*How would you scale this for a production-level AI agent system?*

- **Scalability**: Dùng sub-agent theo từng nhóm nhiệm vụ (search, pricing, shipping) để chia tải khi hệ thống có nhiều công cụ hơn.
- **Safety**: Thêm guardrails để kiểm tra đầu vào/đầu ra của tool, xác thực tham số và chặn hành động rủi ro trước khi thực thi.
- **Performance**: Dùng caching cho kết quả tool và phản hồi phổ biến để giảm độ trễ và chi phí.

---

> [!NOTE]
> Submit this report by renaming it to `REPORT_[YOUR_NAME].md` and placing it in this folder.
