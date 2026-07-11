import uvicorn

if __name__ == "__main__":
    # DB init + the in-process judge worker are started by the app's
    # lifespan handler (see app/web/main.py). This single process both
    # serves the site and judges submissions.
    uvicorn.run("app.web.main:app", host="127.0.0.1", port=8000, reload=False)
