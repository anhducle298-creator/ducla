from config import Settings
from db import init_db


def main():
    settings = Settings.from_env()
    init_db(settings.db_path)
    print("Central monitor project initialized")
    print(f"Database: {settings.db_path}")


if __name__ == "__main__":
    main()
