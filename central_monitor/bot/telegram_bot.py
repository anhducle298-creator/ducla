class TelegramBot:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id

    def start(self):
        raise NotImplementedError("Telegram bot will be implemented later")
