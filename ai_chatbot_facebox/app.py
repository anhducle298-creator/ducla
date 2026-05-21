from config import load_config
from services.chat_service import ChatService
from storage.conversation_store import ConversationStore


def main():
    config = load_config()
    store = ConversationStore(config.database_path)
    chat = ChatService(store=store, app_name=config.app_name)

    print(f"{config.app_name} initialized")
    print(f"Database: {config.database_path}")
    print("Demo chat. Type 'exit' to quit.")

    while True:
        user_text = input("You: ").strip()
        if user_text.lower() in {"exit", "quit"}:
            break
        if not user_text:
            continue
        reply = chat.reply(user_id="console", message=user_text)
        print(f"Bot: {reply}")


if __name__ == "__main__":
    main()
