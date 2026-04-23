# Tìm hiểu chi tiết về các khía cạnh của AI agent

Note:
- Outline dưới đây chỉ là tham khảo, có thể điều chỉnh theo thực tế. Khuyến khích đào sâu và mở rộng hơn nữa.
- Em tạo các task nhỏ và update báo cáo (markdown) vào description/note để thuận tiện.
- Khuyến khích viết learning log mỗi ngày (5-10 dòng)

## Nền tảng Agent & Tool Use

**Task 1.1: Nghiên cứu khái niệm AI Agent**
- Đọc và viết note tổng hợp: Agent là gì, khác gì RAG/Chatbot/Workflow
- Tìm hiểu các thành phần: LLM, Memory, Tools, Planning
- Khi nào dùng agent, khi nào không

**Task 1.2: Tìm hiểu Tool Use / Function Calling**
- Đọc docs của Anthropic/OpenAI về function calling
- Hiểu JSON schema, tool description, cách LLM chọn tool
- Note: Chi tiết cách tool được đưa vào llm, chi phí tool call

**Task 1.3: Build Agent đầu tiên - Single tool**
- Viết agent đơn giản với 1 tool (calculator hoặc weather API)
- Không dùng framework, gọi API trực tiếp

**Task 1.4: Build ReAct Agent - Multi tool**
- Đọc paper ReAct (bản tóm tắt cũng được)
- Build agent với 3-4 tools: web search, calculator, file read
- Implement vòng lặp reason → act → observe
- Note: tham khảo khoá học của deeplearning.ai về build langgraph from scratch

---

## Frameworks & RAG Agent

**Task 2.1: So sánh orchestration frameworks**
- Tìm hiểu LangGraph (chủ yếu), Anthropic Agent SDK (tìm hiểu các feature), CrewAI, ...
- So sánh ưu/nhược, use case phù hợp
- **Output**: Bảng so sánh + đề xuất framework cho team

**Task 2.2: Rebuild ReAct Agent bằng framework**
- Dùng framework đã chọn (gợi ý LangGraph) build lại agent ở Task 1.4
- So sánh với bản tự viết: code ngắn hơn/dài hơn, dễ debug không, flexible không
- **Output**: Code + document so sánh

**Task 2.3: Build Agentic RAG**
- Tận dụng kiến thức RAG sẵn có
- Agent tự quyết định: khi nào search, query gì, có cần rewrite không, có cần search thêm không
- Implement query rewriting, multi-hop retrieval, self-reflection khi answer không đủ thông tin
- So sánh với RAG truyền thống trên cùng dataset
- **Output**: Code + evaluation report (accuracy, latency, cost)

**Task 2.4: Thêm Memory cho Agent**
- Implement short-term memory (conversation history)
- Implement long-term memory (lưu fact quan trọng vào vector DB)
- **Output**: Code + demo multi-turn conversation

---

## Advanced Patterns & Evaluation

**Task 3.1: Planning Agent**
- Build agent với pattern Plan-and-Execute
- Agent tạo plan trước, execute từng step, re-plan khi fail
- So sánh với ReAct: khi nào planning tốt hơn
- **Output**: Code + document phân tích trade-off

**Task 3.2: Multi-Agent System**
- Build hệ thống 2-3 agents cộng tác (ví dụ: researcher + writer + reviewer)
- Implement supervisor pattern hoặc sequential pattern
- **Output**: Code + diagram kiến trúc + demo

**Task 3.3: Evaluation & Observability**
- Tìm hiểu LangSmith/Langfuse, setup tracing cho các agent đã build
- Define metrics: task success rate, tool-call accuracy, cost, latency
- Chạy evaluation trên 20-30 test cases
- **Output**: Dashboard + evaluation report

---

## Production & Capstone

**Task 4.1: Production concerns**
- Implement: error handling, retry, timeout, cost tracking
- Tìm hiểu prompt injection, thêm basic guardrails
- Prompt caching để giảm cost
- Tìm hiểu về source leak của Claude Code
- Harness Engineering

**Task 4.2: Capstone Project**
- Chọn 1 bài toán thực tế của team/công ty để build agent end-to-end
- Yêu cầu: dùng tools + memory + evaluation
