# AI Orchestration Frameworks

| Framework | Core Idea | Strength | Best Use Case |
|----------|----------|----------|--------------|
| LangGraph | Stateful graph (StateGraph), node = agent/task, explicit control flow | Kiểm soát flow cực chi tiết, state minh bạch, checkpoint/persistence, hỗ trợ loop/retry & human-in-the-loop, debug tốt | Workflow phức tạp, cần reliability cao, production system |
| Microsoft Agent Framework <br> (AutoGen + Semantic Kernel) | Multi-agent distributed system (actor model) + enterprise integration | Agent giao tiếp qua conversation (AutoGen), planning + memory + plugin (Semantic Kernel), async & distributed, phù hợp enterprise | Hệ multi-agent lớn, enterprise (Azure/.NET), cần scale & integration |
| CrewAI | Role-based collaboration (agent như team member với role/goal/backstory) | Dễ dùng, build nhanh, hỗ trợ workflow tuần tự & phân cấp, có sẵn tool (web/API/file) | Prototype nhanh, demo, business workflow đơn giản |
| Pydantic AI | Type-safe agent system (data validation-first) | Validate input/output chặt, giảm lỗi runtime, hỗ trợ MCP/A2A, durable execution, observability | System cần reliability cao, strict schema, production backend |
| Anthropic Agent SDK | Managed agent runtime (Claude-native) | Computer use, sandboxing, session persistence, infra managed hoàn toàn | Automation agent dùng Claude, không muốn tự quản infra |
| Google ADK | Cloud-native agent framework (Vertex AI + multimodal + A2A) | Tích hợp Gemini, hỗ trợ multimodal (text/image/audio/video), observability mạnh, scale tốt trong Google Cloud | Enterprise system trên Google Cloud, multimodal AI |
| LlamaIndex Workflows | Event-driven agent system + data-centric (RAG-first) | Kết nối data mạnh (DB, docs), event-based async flow, parallel execution, retry, observability reasoning | RAG system phức tạp, knowledge assistant, data-heavy AI |



# Đề xuất Framework 
---

## 1. Nếu ưu tiên tính ổn định doanh nghiệp và quy trình phức tạp

**Lựa chọn:** LangGraph  

**Lý do:**  
Khả năng kiểm soát trạng thái tuyệt đối và hỗ trợ Human-in-the-loop tốt nhất hiện nay giúp đảm bảo tính an toàn cho các ứng dụng tài chính hoặc y tế.

---

## 2. Nếu team sử dụng .NET hoặc cần triển khai phân tán trong Azure

**Lựa chọn:** Microsoft Agent Framework  

**Lý do:**  
Sự kết hợp giữa Semantic Kernel và AutoGen mang lại sự ổn định kiểu (Type safety) và khả năng mở rộng quy mô lớn cho các hệ thống phân tán.

---

## 3. Nếu cần bản demo hoạt động trong vài ngày (Fast Prototyping)

**Lựa chọn:** CrewAI  

**Lý do:**  
Bạn có thể định nghĩa các tác nhân bằng ngôn ngữ tự nhiên và có ngay một đội ngũ cộng tác mà không cần lo lắng về hạ tầng phức tạp ban đầu.

---

## 4. Nếu team chú trọng Code Quality và sử dụng Python làm chủ đạo

**Lựa chọn:** PydanticAI  

**Lý do:**  
Tận dụng tối đa sức mạnh của Python type hints, giúp giảm thiểu lỗi runtime và tăng tốc độ phát triển nhờ hỗ trợ tốt từ IDE.

---

## 5. Nếu bài toán tập trung vào tra cứu dữ liệu (Advanced RAG)

**Lựa chọn:** LlamaIndex Workflows  

**Lý do:**  
Khả năng xử lý tài liệu doanh nghiệp và tích hợp sâu với các vector database là không đối thủ trong phân khúc này.