from app.db.session import init_db
from app.judge.worker import run_forever

if __name__ == "__main__":
    init_db()
    run_forever()
