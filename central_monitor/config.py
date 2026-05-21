import os
from dataclasses import dataclass


@dataclass
class Settings:
    db_path: str = "data/central_monitor.db"
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    prometheus_url: str = ""

    @classmethod
    def from_env(cls):
        return cls(
            db_path=os.getenv("CENTRAL_MONITOR_DB", cls.db_path),
            telegram_bot_token=os.getenv("CENTRAL_MONITOR_TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=os.getenv("CENTRAL_MONITOR_TELEGRAM_CHAT_ID", ""),
            prometheus_url=os.getenv("PROMETHEUS_URL", ""),
        )
