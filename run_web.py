import uvicorn

from app.db.session import init_db

if __name__ == "__main__":
    init_db()
    uvicorn.run("app.web.main:app", host="127.0.0.1", port=8000, reload=False)
