from app.config import PROBLEMS_DIR
from app.db.session import get_session, init_db
from app.problems.loader import sync_all


def main() -> None:
    init_db()
    with get_session() as session:
        problems = sync_all(session, PROBLEMS_DIR)
    print(f"seeded {len(problems)} problems")


if __name__ == "__main__":
    main()
