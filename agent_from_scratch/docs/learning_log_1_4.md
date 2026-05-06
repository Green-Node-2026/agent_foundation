# Learning Log: Agent From Scratch - Task 1.4

- Trong Task 1.4 này, em đã xây dựng thành công một lớp `Agent` chuyên biệt để điều phối (orchestration) toàn bộ luồng xử lý, giúp tách biệt logic điều khiển khỏi server và các công cụ.
- Em đã mở rộng khả năng của agent bằng cách thêm các tool mới:
    - `get_weather`: Tích hợp Weather API để lấy dữ liệu thời gian thực.
    - `list_files` và `process_file`: Cho phép agent tương tác với hệ thống tệp cục bộ và chuyển đổi tài liệu sang Markdown để xử lý nội dung.
- Em đã thiết kế một `SYSTEM_PROMPT` chuyên sâu, quy định rõ ràng các quy tắc cốt lõi (CORE RULES) và cung cấp các ví dụ Few-shot giúp model nắm bắt được luồng suy nghĩ (thought flow) và cách phối hợp nhiều tool cùng lúc (multi-step reasoning).
- Em đã hiện thực hóa bộ nhớ tạm thời (temporary memory) cho hội thoại hiện tại, giúp agent duy trì ngữ cảnh xuyên suốt các lượt tương tác. Định hướng tương lai là mở rộng sang quản lý nhiều session đồng thời và bộ nhớ dài hạn (long-term memory).
- Để hệ thống trực quan hơn, em đã vẽ các sơ đồ kiến trúc (Diagram) mô tả luồng dữ liệu giữa Agent, LLM Wrapper, Tools và Frontend, giúp việc nắm bắt cấu trúc tổng thể dễ dàng hơn.
- Qua việc tích hợp nhiều tool, em hiểu sâu hơn về cách model "suy luận" để chọn tool dựa trên mô tả tham số (Pydantic) và cách xử lý kết quả trả về để dẫn dắt đến câu trả lời cuối cùng.
- **Dự định sắp tới:**
    - Phát triển Tool Sandbox: Cho phép agent tự viết và thực thi code Python trong môi trường an toàn.
    - Tích hợp ArXiv Tool: Hỗ trợ tìm kiếm và tóm tắt các bài báo khoa học trực tiếp.

---
*Cập nhật ngày: 06/05/2026*
