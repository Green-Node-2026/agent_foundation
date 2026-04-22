# Task 1.1 — Nghiên cứu khái niệm AI Agent 
- Đọc Anthropic "Building effective agents" + OpenAI agent guide
- So sánh Agent vs RAG vs Chatbot vs Workflow (bảng)
- Note 4 thành phần: LLM / Memory / Tools / Planning
- Khi nào nên / không nên dùng agent

## Khái niệm về Agents và so sánh với RAG/Chatbot/Workflow
### Định nghĩa
- AI Agents là các hệ thống trong đó LLM tự động điều phối và quản lý tiến trình xử lý, đồng thời sử dụng các công cụ sẵn có để hoàn thành nhiệm vụ do người dùng giao.
- Ưu điểm: Tự chủ việc ra quyết định thực hiện các tools, và có khả năng thích nghi khi context thay đổi. 
- Hạn chế: Khó khăn trong việc quyết định đường đi để dẫn đến kết quả nếu khả năng suy luận không tốt.

### Agents vs RAG / Chatbot / Workflow
| System | Mục đích sử dụng | Tính năng đặc trưng 
|---|---|---
| Agents | Tự động thực hiện các nhiệm vụ để đạt mục tiêu được giao | LLMs nắm quyền quyết định tools và sử dụng chúng để đạt được kết quả | 
| RAG | Cải thiện trả lời các câu hỏi dựa vào tri thức sẵn có bằng LLM | Lấy các đoạn chunks liên quan từ Documents để tạo câu trả lời dựa vào LLMs |
| Chatbot | Trò chuyện với người dùng | Sử dụng LLMs để tương tác với người dùng dựa trên các câu hỏi được thiết lập sẵn hoặc câu hỏi mới từ người dùng |
| Workflow | Tự động hóa một quy trình để đạt kết quả cuối cùng | LLMs chỉ đóng vai trò là người tổng hợp kết quả và trả về kết quả cuối |

### Agents loops
```
Input: user's prompt Q
Available tools T
State S <- initialize with Q

While not done:
    thought <- Reason(S, T)
    action <- SelectTool(thought, T)
    observation <- Execute(action)
    S <- UpdateState(S, thought, action, observation)

    if Validate(S):
        return FinalAnswer(S)
```

### LLM / Memory / Tools / Planning
**LLM**: là chương trình trí tuệ nhân tạo có khả năng nhận diện và tạo văn bản. LLMs được huấn luyện trên dữ liệu văn bản rất lớn nhằm học cách biểu diễn và sinh ngôn ngữ. Dựa vào đó, LLMs có khả năng thực hiện các nhiệm vụ như: hỏi đáp, tóm tắt, hay đóng vai trò cụ thể trong các framework như AI Agents/ RAG / Workflow / Chatbot.

**Memory**: Trong AI Agents có 2 loại Memory là **Short-term memory** và **Long-term memory**

- **Short-term memory**: là bộ nhớ ngắn hạn của AI agent, dùng để lưu giữ ngữ cảnh gần đây và trạng thái tạm thời của phiên làm việc hiện tại. Nó giúp agent duy trì sự liên tục trong suy luận và ra quyết định, đặc biệt trong các tác vụ nhiều bước hoặc hội thoại nhiều lượt. Các memory đó thường được lưu trong bộ nhớ tạm (RAM), cache, hoặc cơ sở dữ liệu, tùy theo kiến trúc và backend được sử dụng.
- **Long-term memory**: bộ nhớ dài hạn của AI agent, dùng để lưu trữ thông tin lâu dài và có thể được tái sử dụng qua nhiều phiên làm việc hoặc trong thời gian dài. Nó giúp agent duy trì tri thức, cá nhân hóa trải nghiệm và tái sử dụng những gì đã biết từ trước. Các memory đó thường được lưu trữ trong cơ sở dữ liệu, vector database, tùy theo kiến trúc và backend của hệ thống.

### Khi nào dùng agent, khi nào không cần
- Nếu 1 rule-based hoặc 1 workflow xử lý tốt 95% các case thì không cần sử dụng AI Agents.
- Nếu 1 task quá phức tạp, mà cần nhiều nhánh, nhiều bước để đưa ra kết quả thì AI Agents sẽ được sử dụng.
- Để tổng quát hóa, chúng ta có thể sử dụng 1 bộ đánh giá các tiêu chí nên sử dụng AI Agents hoặc gọi Workflow cố định bằng cách thiết lập các tiêu chí tính điểm bằng **LLM lightweight classifier** để đánh giá như:
    - Mức độ rõ ràng của quy tắc
    - Mức độ mơ hồ của đầu vào
    - Nhu cầu suy luận nhiều bước
    - Độ nhạy về chi phí và độ trễ
    - Nhu cầu sử dụng các tools
    - Khả năng kiểm chứng đầu ra

```mermaid
flowchart TD
    A[Task description] --> B[LLM lightweight classifier]
    B --> C[Đánh giá các tiêu chí]
    C --> D[Tính điểm Agent / Workflow]
    D --> E{Score Agent > Score Workflow?}
    E -- Có --> F[Dùng AI Agent]
    E -- Không --> G[Dùng Workflow cố định / Rule-based]
```