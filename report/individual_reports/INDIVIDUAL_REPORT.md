# Individual Report: Lab 3 - Chatbot vs ReAct Agent

- **Student Name**: [Trần Ngọc Thụy]
- **Student ID**: [2A202600799]
- **Date**: 2026-06-01

---

## I. Technical Contribution (15 Points)

- **Modules Implemented**:
  - `src/tools/search_tool.py`: xây dựng công cụ tìm kiếm tài liệu bản địa.
  - `src/agent/agent.py`: hoàn thiện vòng ReAct, thêm parse Action/Final Answer, retry và guardrail.
  - `src/agent/chatbot.py`: tạo baseline chatbot so sánh.
  - `src/agent/run_demo.py`: thêm script demo so sánh chatbot và agent.
  - `src/telemetry/metrics.py`: theo dõi metric LLM request và ước lượng chi phí.
- **Code Highlights**:
  - `ReActAgent.run()` hiện hỗ trợ vòng lặp Thought → Action → Observation và chốt `Final Answer`.
  - `search_documents()` hiện dùng token matching để phù hợp với truy vấn tiếng Việt và tiếng Anh.
- **Documentation**:
  - README đã cập nhật hướng dẫn chạy demo.
  - Báo cáo nhóm và cá nhân đã chứa RCA, so sánh, và đề xuất cải tiến.

---

## II. Debugging Case Study (10 Points)

- **Problem Description**:
  - Ban đầu agent chỉ dừng khi LLM trả `Final Answer`, nhưng nếu LLM trả ra `Action` sai định dạng hoặc tool không tồn tại, agent có thể dừng sớm hoặc lặp vô hạn.
- **Log Source**:
  - `AGENT_START`, `LLM_RESPONSE`, `TOOL_CALL`, `OBSERVATION`, `FINAL_ANSWER`, `AGENT_END` trong log.
- **Diagnosis**:
  - Lỗi nằm ở parser action chưa đủ chặt, và thiếu guardrail khi tool trả lỗi.
- **Solution**:
  - Thêm `_extract_action()` với regex rõ ràng.
  - Thêm `max_retries` và event `PARSE_FAILURE`/`RETRY`.
  - Nếu tool trả lỗi, agent ghi lại và dừng với thông báo rõ ràng.

---

## III. Personal Insights: Chatbot vs ReAct (10 Points)

1. **Reasoning**:
   - Chatbot baseline trả về trực tiếp nội dung LLM sinh ra, có thể chỉ trả `Action` mà không hoàn thiện đáp án.
   - ReAct Agent tách rõ `Thought` và `Action`, giúp giám sát quá trình suy nghĩ và công cụ được gọi.
2. **Reliability**:
   - Agent có lợi thế với các tác vụ nhiều bước như tìm tài liệu, vì nó có thể gọi tool và dùng lại quan sát.
   - Chatbot đơn giản có thể nhanh hơn với câu hỏi ngắn, nhưng dễ sai khi cần thông tin cục bộ.
3. **Observation**:
   - Observation cung cấp phản hồi từ môi trường (tool) và giúp agent điều chỉnh bước tiếp theo.
   - Đây là điểm khác biệt chính giữa suy luận chuỗi và trả lời trực tiếp.

---

## IV. Future Improvements (5 Points)

- **Scalability**:
  - Kết hợp vector database để tìm kiếm nội dung nhanh với nhiều tài liệu hơn.
  - Dùng task queue cho các tool gọi ngoài như API web.
- **Safety**:
  - Thêm supervisor LLM kiểm tra tool call trước khi thực thi.
  - Kiểm tra đầu vào tool để tránh injection và lặp vô hạn.
- **Performance**:
  - Tích hợp nhiều provider (OpenAI, Gemini, local) và chọn theo chi phí hoặc độ trễ.
  - Triển khai bộ nhớ đệm kết quả tool để tránh gọi lặp lại cùng một truy vấn.

---

> [!NOTE]
> Đổi tên file thành `REPORT_[YourName].md` trước khi nộp nếu cần.
