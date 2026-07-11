from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = PROJECT_ROOT / "problems"
DB_PATH = PROJECT_ROOT / "ktoj.sqlite3"
DB_URL = f"sqlite:///{DB_PATH}"
