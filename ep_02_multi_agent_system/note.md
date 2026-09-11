### Hệ multi-agent

- Why need — 4 lý do chính:
    + Tràn context: dồn hết tool call + suy luận vào 1 agent dễ gây context overflow.
    + Câu trả lời chung chung: agent làm nhiều việc → prompt phải bao quát → mất chiều sâu.
    + Tăng tốc trả lời: nhiều agent độc lập làm việc song song → chạy song song nhanh hơn tuần tự.
    + Reliability/Isolation: lỗi ở 1 sub-agent không lan ra toàn hệ thống.

- Đánh đổi: multi-agent tốn nhiều token hơn đáng kể so với single-agent do mỗi sub-agent có context + system prompt riêng, cộng thêm bước tổng hợp. Do đó chỉ nên dùng khi task có thể tách thành nhiều nhánh độc lập, và cần cải thiện tốc độ. 

- How to design: 1 Coordinate Node (lead/orchestrator) + nhiều sub-agent chuyên biệt.
    + Coordinate: nhận task, phân loại, dùng tool `Task` để spawn sub-agent. Không sub-agent nào được phép spawn thêm sub-agent khác, trừ thiết kế hierarchical-coordinate.
    + Mỗi sub-agent định nghĩa dạng JSON: name, description, prompts, tool_allowed.

### Nguyên tắc thiết kế

- Sub-agent không tự lưu context history — mỗi lần khởi tạo là tờ giấy trắng, nếu cần context, Coordinate chịu trách nhiệm chọn lọc và truyền xuống.
- Sub-agent phải tự chắt lọc kết quả thành finding trước khi trả về,
  không trả raw data lên Coordinate tránh làm tràn context của Coordinate.
- Song song hóa việc chạy sub-agent, tránh gối đầu tuần tự (sequential).
- Thêm synthesize node (hoặc để Coordinate tổng hợp) để gắn kết kết quả:
  khử trùng lặp, giải quyết mâu thuẫn giữa các finding, trích dẫn nguồn.
- Ưu tiên mô tả What (mục tiêu) + Why (bối cảnh/lý do), để agent tự suy luận cách làm, hạn chế ép How chi tiết từng bước trừ khi tác vụ cần tính xác định cao (compliance, thao tác nhạy cảm), thì vẫn nên chỉ rõ các bước bắt buộc.