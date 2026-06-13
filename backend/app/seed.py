from app.constants import DEMO_USER_ID
from app.services.demo_user import ensure_demo_user
from app.storage import load_store, save_store


def seed() -> None:
    store = load_store()
    ensure_demo_user(store)
    save_store(store)
    print("Seed completed.")


def main() -> None:
    seed()


if __name__ == "__main__":
    main()
