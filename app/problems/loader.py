from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Problem, TestCase

_INT_FIELDS = {"time_limit_ms", "memory_limit_mb"}


def parse_problem_dir(path: Path) -> tuple[dict, list[dict]]:
    text = (path / "problem.md").read_text(encoding="utf-8")
    meta: dict = {"slug": path.name, "title": path.name,
                  "difficulty": "왕초보", "time_limit_ms": 1000,
                  "memory_limit_mb": 128}
    body = text
    if text.startswith("---"):
        _, front, body = text.split("---", 2)
        for line in front.strip().splitlines():
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key, value = key.strip(), value.strip()
            if key in _INT_FIELDS:
                meta[key] = int(value)
            elif key in ("title", "difficulty"):
                meta[key] = value
    meta["statement"] = body.strip()

    cases: list[dict] = []
    tests_dir = path / "tests"
    in_files = sorted(tests_dir.glob("*.in"),
                      key=lambda p: int(p.stem))
    for ordinal, in_file in enumerate(in_files, start=1):
        out_file = in_file.with_suffix(".out")
        cases.append({
            "ordinal": ordinal,
            "input": in_file.read_text(encoding="utf-8"),
            "expected_output": out_file.read_text(encoding="utf-8"),
            "is_sample": ordinal == 1,
        })
    return meta, cases


def sync_problem(session: Session, path: Path) -> Problem:
    meta, cases = parse_problem_dir(path)
    problem = session.scalar(
        select(Problem).where(Problem.slug == meta["slug"]))
    if problem is None:
        problem = Problem(slug=meta["slug"])
        session.add(problem)
    problem.title = meta["title"]
    problem.statement = meta["statement"]
    problem.difficulty = meta["difficulty"]
    problem.time_limit_ms = meta["time_limit_ms"]
    problem.memory_limit_mb = meta["memory_limit_mb"]
    problem.testcases.clear()
    session.flush()
    for c in cases:
        problem.testcases.append(TestCase(**c))
    return problem


def sync_all(session: Session, problems_dir: Path) -> list[Problem]:
    result = []
    for child in sorted(problems_dir.iterdir()):
        if child.is_dir() and (child / "problem.md").exists():
            result.append(sync_problem(session, child))
    return result
