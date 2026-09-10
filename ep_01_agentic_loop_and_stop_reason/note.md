## Kiến thức chung

### Mảng `messages`
- `messages` là tham số bắt buộc, chứa lịch sử hội thoại dưới dạng mảng các message.
- Mỗi message chỉ thuộc 1 trong 2 role:
    + `user`: Tin nhắn từ người dùng, hoặc `tool_result` (kết quả tool) — vẫn dùng role `user`.
    + `assistant`: Tin nhắn Claude trả lời, hoặc `tool_use` (yêu cầu gọi tool).

- API là stateless: mỗi request độc lập, không lưu trạng thái phía server. 
  → Muốn duy trì hội thoại nhiều lượt, phải tự gửi lại toàn bộ lịch sử `messages` ở mỗi lần gọi.

### Role `system`
- `system` không nằm trong mảng `messages`, nó là một tham số riêng với `messages`, sùng để định nghĩa vai trò, giới hạn hành vi, hoặc bối cảnh cho Claude trong suốt lượt trả lời đó.
- Vì API stateless, `system` có thể thay đổi giữa các lượt gọi trong cùng một phiên chat (do phía client tự quản lý), server không ép buộc phải nhất quán qua các lượt.

## Agentic Loop

- Về bản chất, đây vẫn là vòng lặp kiểu **ReAct** (Reason + Act).
- Vòng đời (life cycle) gồm 4 bước:
    1. Gửi request tới Claude.
    2. Kiểm tra `stop_reason` trong response:
        - Nếu `stop_reason = "tool_use"` → sang bước 3.
        - Nếu `stop_reason = "end_turn"` → dừng vòng lặp.
    3. Thực thi tool tương ứng (dựa trên `tool_use` block Claude trả về).
    4. Nối kết quả tool (`tool_result`) vào body của request tiếp theo, rồi quay lại bước 1.

## Các quy tắc thiết kế

- `end_turn` nên là điều kiện duy nhất để thoát vòng lặp ReAct (tránh dừng loop dựa trên đoán logic riêng, vì Claude có thể cần gọi tool nhiều lần liên tiếp).
- Mỗi `tool_result` phải có `tool_use_id` khớp chính xác với `id` của `tool_use` block tương ứng mà Claude đã trả về trước đó (không phải khớp với "định nghĩa tool" — mà là khớp với ID của lần gọi tool cụ thể đó).
- API là stateless → luôn phải gửi lại toàn bộ lịch sử tin nhắn ở mỗi lượt gọi.