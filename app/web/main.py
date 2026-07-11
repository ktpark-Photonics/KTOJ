import markdown as md
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select

from app.db.models import Problem, Submission
from app.db.session import SessionLocal, init_db
from app.judge import verdicts
from app.judge.background import start_inprocess_worker
from app.judge.languages import LANGUAGES

LAST_PROBLEM_COOKIE = "last_problem"


@asynccontextmanager
async def lifespan(app: "FastAPI"):
    # On boot: ensure tables exist, then run the judge worker in-process
    # (a daemon thread) so a single `run_web.py` serves and judges.
    init_db()
    start_inprocess_worker()
    yield


app = FastAPI(title="KTOJ", lifespan=lifespan)
templates = Jinja2Templates(
    directory=str(Path(__file__).parent / "templates"))
templates.env.filters["markdown"] = lambda text: md.markdown(
    text or "", extensions=["fenced_code"])


@app.get("/", response_class=HTMLResponse)
def problem_list(request: Request):
    with SessionLocal() as s:
        problems = s.scalars(select(Problem).order_by(Problem.id)).all()
        solved = set(s.scalars(
            select(Submission.problem_id)
            .where(Submission.status == verdicts.AC).distinct()).all())
    return templates.TemplateResponse(
        request, "problem_list.html",
        {"problems": problems, "solved": solved, "active_tab": "problems"})


@app.get("/problems/{slug}", response_class=HTMLResponse)
def problem_detail(request: Request, slug: str):
    with SessionLocal() as s:
        problem = s.scalar(select(Problem).where(Problem.slug == slug))
        if problem is None:
            raise HTTPException(404, "problem not found")
        samples = [c for c in problem.testcases if c.is_sample]
        ctx = {"problem": problem, "samples": samples, "active_tab": "solve"}
    resp = templates.TemplateResponse(request, "problem_detail.html", ctx)
    # Remember the last problem opened so the "풀이" tab can return here.
    resp.set_cookie(LAST_PROBLEM_COOKIE, slug, max_age=60 * 60 * 24 * 30,
                    samesite="lax")
    return resp


@app.get("/solve")
def solve(request: Request):
    slug = request.cookies.get(LAST_PROBLEM_COOKIE)
    if slug:
        with SessionLocal() as s:
            exists = s.scalar(select(Problem.id).where(Problem.slug == slug))
        if exists is not None:
            return RedirectResponse(f"/problems/{slug}", status_code=303)
    return templates.TemplateResponse(
        request, "solve_empty.html", {"active_tab": "solve"})


@app.post("/problems/{slug}/submit")
def submit(slug: str, language: str = Form(...),
           source_code: str = Form(...)):
    with SessionLocal() as s:
        problem = s.scalar(select(Problem).where(Problem.slug == slug))
        if problem is None:
            raise HTTPException(404, "problem not found")
        if language not in LANGUAGES:
            raise HTTPException(400, f"unsupported language: {language}")
        sub = Submission(problem_id=problem.id, language=language,
                         source_code=source_code)
        s.add(sub)
        s.commit()
        sub_id = sub.id
    return RedirectResponse(f"/submissions/{sub_id}", status_code=303)


@app.get("/submissions", response_class=HTMLResponse)
def submission_list(request: Request):
    with SessionLocal() as s:
        subs = s.scalars(
            select(Submission).order_by(Submission.id.desc())).all()
        titles = {p.id: p.title
                  for p in s.scalars(select(Problem)).all()}
        rows = [{
            "id": x.id,
            "title": titles.get(x.problem_id, "(삭제된 문제)"),
            "status": x.status,
            "time_ms": x.time_ms,
            "failed_case_no": x.failed_case_no,
            "created_at": x.created_at,
        } for x in subs]
    return templates.TemplateResponse(
        request, "submissions.html", {"rows": rows, "active_tab": "history"})


@app.get("/submissions/{sub_id}", response_class=HTMLResponse)
def submission_detail(request: Request, sub_id: int):
    with SessionLocal() as s:
        sub = s.get(Submission, sub_id)
        if sub is None:
            raise HTTPException(404, "submission not found")
        problem = s.get(Problem, sub.problem_id)
        ctx = {"sub": sub, "problem": problem, "active_tab": "history"}
    return templates.TemplateResponse(request, "submission_detail.html", ctx)


@app.get("/submissions/{sub_id}/status", response_class=HTMLResponse)
def submission_status(request: Request, sub_id: int):
    with SessionLocal() as s:
        sub = s.get(Submission, sub_id)
        if sub is None:
            raise HTTPException(404, "submission not found")
    return templates.TemplateResponse(
        request, "_submission_status.html", {"sub": sub})
