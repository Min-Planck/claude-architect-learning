"""
Ví dụ minh họa Agentic Loop với tool use trong Claude Messages API.

Kịch bản: hỏi Claude thời tiết ở một thành phố. Claude sẽ gọi tool
`get_weather` (ở đây ta giả lập kết quả), rồi dùng kết quả đó để
trả lời bằng ngôn ngữ tự nhiên.
"""

import os
import anthropic
from dotenv import load_dotenv

load_dotenv()  # tải các biến môi trường từ file .env

client = anthropic.Anthropic()  # đọc API key từ biến môi trường ANTHROPIC_API_KEY

MODEL = os.environ.get("MODEL", "claude-haiku-4-5")  # đọc model từ biến môi trường MODEL

# 1. Định nghĩa tool: name, description, input_schema (JSON Schema)
tools = [
    {
        "name": "get_weather",
        "description": (
            "Lấy thông tin thời tiết hiện tại của một thành phố. "
            "Dùng khi người dùng hỏi về thời tiết ở một thành phố cụ thể. "
            "Output là chuỗi mô tả thời tiết."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "Tên thành phố, ví dụ: 'Hà Nội'",
                }
            },
            "required": ["city"],
        },
    }
]


def get_weather(city: str) -> str:
    """Hàm thật sẽ gọi API thời tiết ở đây, hàm này chỉ giả lập kết quả."""
    fake_data = {"Hà Nội": "28°C, có mây", "Bắc Ninh": "27°C, nắng nhẹ"}
    return fake_data.get(city, f"Không có dữ liệu thời tiết cho {city}")


def run_tool(tool_name: str, tool_input: dict) -> str:
    """Router: map tên tool -> hàm thực thi tương ứng."""
    if tool_name == "get_weather":
        return get_weather(**tool_input)
    raise ValueError(f"Không rõ tool: {tool_name}")


def agentic_loop(user_message: str) -> str:
    # Bắt đầu lịch sử hội thoại với message của user
    messages = [{"role": "user", "content": user_message}]
    MAX_LOOP_ITERATIONS = int(os.environ.get("MAX_LOOP_ITERATIONS", 50))
    iteration = 0

    while iteration < MAX_LOOP_ITERATIONS:
        # Bước 1: gửi request tới Claude
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system="Bạn là trợ lý thời tiết, trả lời ngắn gọn bằng tiếng Việt.",
            tools=tools,
            messages=messages,
        )

        # Bước 2: kiểm tra stop_reason
        if response.stop_reason == "end_turn":
            # Lấy toàn bộ text block để trả về câu trả lời cuối cùng
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        if response.stop_reason != "tool_use":
            # Bao quát các stop_reason khác: max_tokens, refusal, pause_turn, ...
            raise RuntimeError(f"stop_reason không xử lý: {response.stop_reason}")

        # Bước 3: response.content có thể chứa NHIỀU tool_use block cùng lúc
        # -> phải nối message assistant gốc, rồi chạy hết các tool trước khi
        #    gửi lại tool_result trong MỘT message user duy nhất.
        messages.append({"role": "assistant", "content": response.content})

        tool_result_blocks = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f'Calling tool "{block.name}" with input: {block.input}')
            result = run_tool(block.name, block.input)
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,  # PHẢI khớp với id của tool_use block
                    "content": result,
                }
            )
            print(f'Tool "{block.name}" returned: {result}')
        # Bước 4: tool_result nằm trong message role "user" (không có role "tool")
        messages.append({"role": "user", "content": tool_result_blocks})
        iteration += 1
        # Quay lại bước 1


if __name__ == "__main__":
    answer = agentic_loop("Thời tiết ở Bắc Ninh hôm nay thế nào?")
    print(answer)