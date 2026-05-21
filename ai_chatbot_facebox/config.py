import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None


@dataclass(frozen=True)
class Config:
    app_name: str
    app_env: str
    database_path: str
    telegram_bot_token: str
    telegram_allowed_chat_ids: set[str]
    ai_provider: str
    openai_api_key: str
    openai_model: str


def _parse_chat_ids(raw_value: str) -> set[str]:
    return {item.strip() for item in raw_value.split(",") if item.strip()}


def load_config() -> Config:
    if load_dotenv:
        load_dotenv()

    return Config(
        app_name=os.getenv("APP_NAME", "AI Chat Bot FaceBox"),
        app_env=os.getenv("APP_ENV", "dev"),
        database_path=os.getenv("DATABASE_PATH", "data/facebox_chat.db"),
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        telegram_allowed_chat_ids=_parse_chat_ids(os.getenv("TELEGRAM_ALLOWED_CHAT_IDS", "")),
        ai_provider=os.getenv("AI_PROVIDER", "local"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
    )
