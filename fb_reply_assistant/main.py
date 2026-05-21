import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


BASE_DIR = Path(__file__).resolve().parent
PERSONA_PATH = BASE_DIR / "persona.txt"


class ReplyAssistantError(Exception):
    """Raised when the reply assistant cannot complete a request."""


def load_persona() -> str:
    """Load the assistant persona from persona.txt so it can be edited easily."""
    return PERSONA_PATH.read_text(encoding="utf-8").strip()


def build_prompt(sender_name: str, incoming_message: str) -> str:
    """Create the user prompt sent to the model."""
    return f"""
Người nhắn: {sender_name}
Tin nhắn nhận được: {incoming_message}

Hãy sinh đúng 3 câu trả lời Messenger theo 3 kiểu:
1. dễ thương
2. lịch sự
3. từ chối khéo

Yêu cầu output là JSON hợp lệ, không markdown, theo đúng format:
{{
  "de_thuong": "...",
  "lich_su": "...",
  "tu_choi_kheo": "..."
}}
""".strip()


def parse_model_json(raw_text: str) -> dict:
    """Parse JSON from the model response and validate required fields."""
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ReplyAssistantError("AI trả về sai định dạng JSON.") from exc

    required_keys = ["de_thuong", "lich_su", "tu_choi_kheo"]
    missing = [key for key in required_keys if not data.get(key)]
    if missing:
        raise ReplyAssistantError(f"AI trả về thiếu trường: {', '.join(missing)}")

    return data


def generate_replies(client: OpenAI, model: str, sender_name: str, incoming_message: str) -> dict:
    """Call OpenAI API and return three suggested Messenger replies."""
    persona = load_persona()

    response = client.responses.create(
        model=model,
        input=[
            {
                "role": "system",
                "content": persona,
            },
            {
                "role": "user",
                "content": build_prompt(sender_name, incoming_message),
            },
        ],
        max_output_tokens=400,
    )

    return parse_model_json(response.output_text.strip())


def print_replies(replies: dict) -> None:
    """Print replies in a simple terminal-friendly format."""
    print("\nGợi ý trả lời:")
    print(f"1. {replies['de_thuong']}")
    print(f"2. {replies['lich_su']}")
    print(f"3. {replies['tu_choi_kheo']}")


def main() -> None:
    load_dotenv(BASE_DIR / ".env")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()

    if not api_key:
        raise ReplyAssistantError("Chưa cấu hình OPENAI_API_KEY trong file .env")

    client = OpenAI(api_key=api_key)

    print("FB Reply Assistant")
    print("Nhập 'exit' để thoát. Tool này chỉ gợi ý trả lời cho tin nhắn đã nhận.\n")

    while True:
        sender_name = input("Tên người nhắn: ").strip()
        if sender_name.lower() in {"exit", "quit"}:
            break

        incoming_message = input("Nội dung tin nhắn: ").strip()
        if incoming_message.lower() in {"exit", "quit"}:
            break

        if not sender_name or not incoming_message:
            print("Vui lòng nhập đủ tên và nội dung tin nhắn.\n")
            continue

        try:
            replies = generate_replies(client, model, sender_name, incoming_message)
            print_replies(replies)
        except Exception as exc:
            print(f"Lỗi: {exc}")

        print()


if __name__ == "__main__":
    main()
