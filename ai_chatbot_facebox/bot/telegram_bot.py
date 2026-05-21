class TelegramFaceBoxBot:
    def __init__(self, token: str, allowed_chat_ids: set[str], chat_service):
        self.token = token
        self.allowed_chat_ids = allowed_chat_ids
        self.chat_service = chat_service

    def run(self):
        if not self.token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not configured")
        try:
            import telebot
        except ImportError as exc:
            raise RuntimeError("Install pyTelegramBotAPI before running Telegram bot") from exc

        bot = telebot.TeleBot(self.token)

        def is_allowed(message):
            return not self.allowed_chat_ids or str(message.chat.id) in self.allowed_chat_ids

        @bot.message_handler(func=lambda message: True)
        def handle_message(message):
            if not is_allowed(message):
                return
            reply = self.chat_service.reply(str(message.chat.id), message.text or "")
            bot.reply_to(message, reply)

        bot.infinity_polling(timeout=30, long_polling_timeout=30)
