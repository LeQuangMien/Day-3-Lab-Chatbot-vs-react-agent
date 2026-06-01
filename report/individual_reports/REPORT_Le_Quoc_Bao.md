# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: Lê Quốc Bảo
- **Student ID**: 2A202600561
- **Date**: 01/06/2026

---

## I. Technical Contribution (15 Points)

Trong lab này, tôi phụ trách xây dựng lớp API cho hệ thống LLM và ReAct Agent, với mục tiêu tách rõ hai chế độ hoạt động: chatbot baseline và agent có khả năng suy luận đa bước.

### 1. Các module đã triển khai
- `src/api/main.py`: xây dựng FastAPI app và hai endpoint chính:
  - `POST /llm` để gọi trực tiếp LLM.
  - `POST /agent` để chạy ReAct agent.
- `tests/test_api.py`: viết test cho cả hai endpoint bằng fake provider/fake agent để tránh phụ thuộc mạng.
- `src/tools/utils.py`: chuẩn hoá text tiếng Việt để xử lý đúng các giá trị như `Hà Nội`.

### 2. Điểm nhấn kỹ thuật
- Tôi thiết kế request model bằng `Pydantic` để chuẩn hoá dữ liệu đầu vào.
- Tôi dùng `dependency injection` trong FastAPI để có thể thay provider hoặc agent bằng test double khi chạy unit test.
- Tôi chuyển phần import provider sang kiểu `lazy import` trong hàm `get_llm_provider()` để tránh lỗi import khi môi trường chưa cài đủ backend như `llama_cpp`.
- API trả về metadata rõ ràng như `model`, `usage`, `latency_ms`, `provider`, giúp thuận tiện cho phần telemetry và báo cáo.

### 3. Cách API kết nối với ReAct loop
- Endpoint `/llm` đóng vai trò baseline: gửi prompt và nhận câu trả lời trực tiếp từ model.
- Endpoint `/agent` khởi tạo `ReActAgent`, cho phép model chạy theo vòng lặp `Thought -> Action -> Observation`.
- Thiết kế này phù hợp với mục tiêu của lab vì cho phép so sánh trực tiếp giữa một chatbot trả lời ngay và một agent biết gọi tool để suy luận.

### 4. Bằng chứng kiểm thử
- Tôi đã viết test cho `/llm` và `/agent` trong `tests/test_api.py`.
- Test sử dụng fake provider/fake agent nên chạy ổn định trong môi trường local, không cần API key thật.
- Kết quả chạy `pytest tests/test_api.py -q` cho thấy cả hai endpoint đều hoạt động đúng.

---

## II. Debugging Case Study (10 Points)

### Problem Description
Khi chạy test lần đầu, API bị lỗi import vì `src/api/main.py` import trực tiếp `LocalProvider`, trong khi môi trường test chưa cài `llama_cpp`. Điều này làm cho toàn bộ module API không thể load, dù test chỉ cần mock provider.

### Log Source
- Lỗi xuất hiện ngay trong lúc pytest collect test.
- Thông báo chính là `ModuleNotFoundError: No module named 'llama_cpp'`.

### Diagnosis
Nguyên nhân không nằm ở logic của endpoint, mà nằm ở cách tổ chức import. Khi một module API import toàn bộ provider ở cấp file, Python sẽ cố load tất cả backend ngay lúc import, kể cả khi endpoint không dùng tới chúng.

### Solution
- Tôi chuyển import của `OpenAIProvider`, `GeminiProvider`, và `LocalProvider` vào bên trong `get_llm_provider()`.
- Tôi viết test bằng fake dependency để kiểm tra đúng hai route `/llm` và `/agent` mà không chạm tới backend thật.
- Sau khi sửa, test API chạy ổn định và không còn phụ thuộc vào provider chưa cài.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

### 1. Reasoning
ReAct tốt hơn chatbot ở chỗ nó không trả lời ngay khi chưa đủ dữ liệu. Với API `/agent`, model có thể đi qua nhiều bước suy luận rồi mới kết luận, thay vì đoán một câu trả lời trực tiếp.

### 2. Reliability
Chatbot có lợi thế khi câu hỏi đơn giản, ví dụ hỏi định nghĩa hoặc hỏi nhanh một câu ngắn. Tuy nhiên, khi bài toán cần nhiều điều kiện và dữ liệu thực tế, agent đáng tin hơn vì nó có thể gọi tool và kiểm chứng thông tin.

### 3. Observation
Phần `Observation` là điểm khác biệt lớn nhất. Nó biến output của tool thành phản hồi mới để model điều chỉnh bước tiếp theo. Nhờ đó, agent không chỉ “nói” mà còn biết “đọc kết quả”, rồi cập nhật suy luận dựa trên dữ liệu thật.

### 4. Kết luận cá nhân
Qua lab này, tôi hiểu rằng giá trị của agent không chỉ là trả lời đúng, mà là tạo ra một quy trình suy luận có thể kiểm tra được. API hai tầng `/llm` và `/agent` giúp thể hiện rất rõ sự khác biệt đó.

---

## IV. Future Improvements (5 Points)

- **Scalability**: Tách API thành nhiều router hơn khi hệ thống mở rộng, ví dụ `auth`, `catalog`, `agent`, `telemetry`.
- **Safety**: Thêm validation chặt hơn cho input, giới hạn số vòng lặp agent, và chuẩn hoá output tool trước khi đưa lại cho LLM.
- **Performance**: Cache kết quả cho các truy vấn lặp lại, và dùng queue bất đồng bộ nếu tool call hoặc provider call có độ trễ cao.
- **Observability**: Chuẩn hoá thêm log JSON và metric để so sánh latency, token usage, và lỗi parser giữa các phiên bản agent.

---


