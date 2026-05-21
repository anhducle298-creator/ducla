from storage.conversation_store import ConversationStore


class ChatService:
    def __init__(self, store: ConversationStore, app_name: str):
        self.store = store
        self.app_name = app_name

    def reply(self, user_id: str, message: str) -> str:
        self.store.add_message(user_id, "user", message)
        reply = self._build_local_reply(message)
        self.store.add_message(user_id, "assistant", reply)
        return reply

    def _build_local_reply(self, message: str) -> str:
        text = message.strip().lower()
        if text in {"alo", "hello", "hi", "xin chao", "chao"}:
            return "FaceBox nghe day. Ban muon hoi thong tin, tra cuu lich su hay cau hinh bot?"
        if "trang thai" in text or "status" in text:
            return "Chuc nang trang thai FaceBox se ket noi service/API o buoc tiep theo."
        if "help" in text or "tro giup" in text:
            return "Lenh goi y: alo, trang thai, lich su, cau hinh."
        return "Toi da nhan noi dung. Hien tai dang o che do local demo, chua ket noi AI provider."
