"""
Ví dụ minh họa mô hình multi-agent orchestrator-worker với Claude API:

- Coordinate Node (lead agent): nhận câu hỏi của user, dùng tool `spawn_subagent`
  để giao việc cho các sub-agent chuyên biệt, chạy SONG SONG, rồi tổng hợp
  (synthesize) kết quả thành câu trả lời cuối cùng.
- Sub-agent: mỗi lần được spawn là một context HOÀN TOÀN MỚI (không nhớ gì
  từ các lượt trước), có system prompt riêng, chỉ trả về 1 string kết quả
  (finding đã được distill), không trả raw data.

Kịch bản demo: so sánh nhanh 2 framework backend (FastAPI vs Django) để
Coordinate quyết định nên dùng cái nào cho một dự án cụ thể.
"""

import os
import json
from concurrent.futures import ThreadPoolExecutor

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")


# ---------------------------------------------------------------------------
# 1. Định nghĩa các "loại" sub-agent (tương đương file .md trong .claude/agents/)
#    Ở đây ta định nghĩa bằng dict trong code cho gọn, thay vì đọc từ file.
# ---------------------------------------------------------------------------
SUBAGENT_REGISTRY = {
    "fastapi-researcher": {
        "description": "Phân tích ưu/nhược điểm của FastAPI cho một use case cụ thể.",
        "system_prompt": (
            "Bạn là chuyên gia FastAPI. Nhiệm vụ: đưa ra đánh giá NGẮN GỌN "
            "(dưới 100 từ) về ưu/nhược điểm của FastAPI cho use case được giao. "
            "Chỉ trả về kết luận đã chắt lọc, không trình bày quá trình suy nghĩ."
        ),
    },
    "django-researcher": {
        "description": "Phân tích ưu/nhược điểm của Django cho một use case cụ thể.",
        "system_prompt": (
            "Bạn là chuyên gia Django. Nhiệm vụ: đưa ra đánh giá NGẮN GỌN "
            "(dưới 100 từ) về ưu/nhược điểm của Django cho use case được giao. "
            "Chỉ trả về kết luận đã chắt lọc, không trình bày quá trình suy nghĩ."
        ),
    },
}


# ---------------------------------------------------------------------------
# 2. Tool `spawn_subagent` — đây là bản rút gọn của tool `Task` trong Claude Code.
#    Coordinate Node sẽ gọi tool này (có thể gọi NHIỀU LẦN trong 1 lượt phản hồi
#    để chạy song song).
# ---------------------------------------------------------------------------
tools = [
    {
        "name": "spawn_subagent",
        "description": (
            "Giao một nhiệm vụ chuyên biệt cho một sub-agent với context HOÀN TOÀN MỚI. "
            "Dùng khi cần ý kiến chuyên sâu, độc lập từ nhiều góc nhìn khác nhau. "
            "Có thể gọi nhiều lần trong cùng 1 lượt để các sub-agent chạy song song."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "subagent_type": {
                    "type": "string",
                    "enum": list(SUBAGENT_REGISTRY.keys()),
                    "description": "Loại sub-agent cần spawn.",
                },
                "prompt": {
                    "type": "string",
                    "description": "Nhiệm vụ đầy đủ giao cho sub-agent.",
                },
            },
            "required": ["subagent_type", "prompt"],
        },
    }
]


def run_subagent(subagent_type: str, prompt: str) -> str:
    """
    Thực thi 1 sub-agent, dùng system prompt riêng, chỉ có 1 lượt hỏi-đáp rồi trả kết quả.
    """
    config = SUBAGENT_REGISTRY[subagent_type]

    response = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=config["system_prompt"],
        messages=[{"role": "user", "content": prompt}],  # context sạch, không có gì trước đó
    )
    return "".join(block.text for block in response.content if block.type == "text")


def run_subagents_in_parallel(spawn_requests: list[dict]) -> list[dict]:
    """
    Chạy nhiều sub-agent CÙNG LÚC bằng ThreadPoolExecutor, tương ứng với việc
    Coordinate gọi nhiều tool_use `spawn_subagent` trong cùng 1 response.
    """
    with ThreadPoolExecutor(max_workers=len(spawn_requests)) as executor:
        futures = {
            executor.submit(run_subagent, req["subagent_type"], req["prompt"]): req
            for req in spawn_requests
        }
        results = []
        for future, req in futures.items():
            results.append({"request": req, "result": future.result()})
        return results


# ---------------------------------------------------------------------------
# 3. Coordinate Node (lead agent) — vòng lặp agentic thông thường, chỉ khác là
#    tool nó gọi là `spawn_subagent` thay vì tool nghiệp vụ thông thường.
# ---------------------------------------------------------------------------
def coordinate(user_question: str) -> str:
    messages = [{"role": "user", "content": user_question}]
    MAX_LOOP_ITERATIONS = int(os.environ.get("MAX_LOOP_ITERATIONS", 50))
    iteration = 0
    coordinator_system = (
        "Bạn là Coordinate Node điều phối các sub-agent chuyên biệt. "
        "Khi cần ý kiến chuyên sâu từ nhiều góc nhìn, hãy gọi tool spawn_subagent "
        "(có thể gọi nhiều lần cùng lúc để chạy song song). "
        "Sau khi có đủ kết quả từ các sub-agent, hãy TỔNG HỢP (không liệt kê rời rạc) "
        "thành một khuyến nghị mạch lạc."
    )

    while MAX_LOOP_ITERATIONS > iteration:
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=coordinator_system,
            tools=tools,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            return "".join(
                block.text for block in response.content if block.type == "text"
            )

        if response.stop_reason != "tool_use":
            raise RuntimeError(f"stop_reason không xử lý: {response.stop_reason}")

        # Nối message assistant gốc (có thể chứa NHIỀU tool_use block spawn_subagent)
        messages.append({"role": "assistant", "content": response.content})

        # Gom tất cả các lệnh spawn_subagent trong lượt này lại để chạy song song
        spawn_calls = [b for b in response.content if b.type == "tool_use"]
        spawn_requests = [
            {"subagent_type": b.input["subagent_type"], "prompt": b.input["prompt"]}
            for b in spawn_calls
        ]

        print(f"[Coordinate] Spawn {len(spawn_requests)} sub-agent song song: "
              f"{[r['subagent_type'] for r in spawn_requests]}")

        parallel_results = run_subagents_in_parallel(spawn_requests)

        # Ghép kết quả từng sub-agent với đúng tool_use_id tương ứng
        tool_result_blocks = []
        for block, res in zip(spawn_calls, parallel_results):
            tool_result_blocks.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,  # bắt buộc khớp với id của tool_use
                    "content": res["result"],  # chỉ trả finding đã chắt lọc, không raw data
                }
            )

        # tool_result nằm trong message role "user"
        messages.append({"role": "user", "content": tool_result_blocks})
        # Quay lại đầu vòng lặp để Coordinate tổng hợp
        iteration += 1

if __name__ == "__main__":
    question = (
        "Tôi đang xây một API backend cho hệ thống realtime chat, "
        "khoảng 5 dev, cần scale nhanh. Nên chọn FastAPI hay Django?"
    )
    final_answer = coordinate(question)
    print("\n=== Kết luận cuối cùng của Coordinate ===")
    print(final_answer)