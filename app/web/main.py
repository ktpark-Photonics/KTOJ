import markdown as md
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select

from app.db.models import Problem, Submission
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


@app.post("/problems/{slug}/submit")
def submit(slug: str, language: str = Form(...),
           source_code: str = Form(...)):
    with SessionLocal() as s:
        problem = s.scalar(select(Problem).where(Problem.slug == slug))
        if problem is None:
            raise HTTPException(404, "problem not found")
        sub = Submission(problem_id=problem.id, language=language,
                         source_code=source_code)
        s.add(sub)
        s.commit()
        sub_id = sub.id
    return RedirectResponse(f"/submissions/{sub_id}", status_code=303)


@app.get("/submissions/{sub_id}", response_class=HTMLResponse)
def submission_detail(request: Request, sub_id: int):
    with SessionLocal() as s:
        sub = s.get(Submission, sub_id)
        if sub is None:
            raise HTTPException(404, "submission not found")
        problem = s.get(Problem, sub.problem_id)
        ctx = {"sub": sub, "problem": problem}
    return templates.TemplateResponse(request, "submission_detail.html", ctx)


@app.get("/submissions/{sub_id}/status", response_class=HTMLResponse)
def submission_status(request: Request, sub_id: int):
    with SessionLocal() as s:
        sub = s.get(Submission, sub_id)
        if sub is None:
            raise HTTPException(404, "submission not found")
    return templates.TemplateResponse(
        request, "_submission_status.html", {"sub": sub})
