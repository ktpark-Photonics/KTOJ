import markdown as md
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select

from app.db.models import Problem
from app.db.session import SessionLocal

app = FastAPI(title="KTOJ")
templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates"))
templates.env.filters["markdown"] = lambda text: md.markdown(
    text or "", extensions=["fenced_code"])


@app.get("/", response_class=HTMLResponse)
def problem_list(request: Request):
    with SessionLocal() as s:
        problems = s.scalars(select(Problem).order_by(Problem.id)).all()
    return templates.TemplateResponse(
        request, "problem_list.html", {"problems": problems})


@app.get("/problems/{slug}", response_class=HTMLResponse)
def problem_detail(request: Request, slug: str):
    with SessionLocal() as s:
        problem = s.scalar(select(Problem).where(Problem.slug == slug))
        if problem is None:
            raise HTTPException(404, "problem not found")
        samples = [c for c in problem.testcases if c.is_sample]
        ctx = {"problem": problem, "samples": samples}
    return templates.TemplateResponse(request, "problem_detail.html", ctx)
