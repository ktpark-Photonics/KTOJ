from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Problem
from app.problems.loader import parse_problem_dir, sync_all, sync_problem


def _make_problem_dir(root: Path) -> Path:
    d = root / "a-plus-b"
    (d / "tests").mkdir(parents=True)
    (d / "problem.md").write_text(
        "---\n"
        "title: A+B\n"
        "difficulty: 왕초보\n"
        "time_limit_ms: 1000\n"
        "memory_limit_mb: 128\n"
        "---\n"
        "# A+B\n두 정수의 합을 출력하시오.\n",
        encoding="utf-8")
    (d / "tests" / "1.in").write_text("1 2\n", encoding="utf-8")
    (d / "tests" / "1.out").write_text("3\n", encoding="utf-8")
    (d / "tests" / "2.in").write_text("10 20\n", encoding="utf-8")
    (d / "tests" / "2.out").write_text("30\n", encoding="utf-8")
    return d


def test_parse_problem_dir(tmp_path):
    d = _make_problem_dir(tmp_path)
    meta, cases = parse_problem_dir(d)
    assert meta["slug"] == "a-plus-b"
    assert meta["title"] == "A+B"
    assert meta["difficulty"] == "왕초보"
    assert meta["time_limit_ms"] == 1000
    assert "두 정수의 합" in meta["statement"]
    assert len(cases) == 2
    assert cases[0]["ordinal"] == 1
    assert cases[0]["is_sample"] is True
    assert cases[0]["expected_output"] == "3\n"
    assert cases[1]["is_sample"] is False


def test_sync_problem_upserts(tmp_path):
    d = _make_problem_dir(tmp_path)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        sync_problem(s, d)
        s.commit()
        sync_problem(s, d)  # 두 번째 동기화해도 중복 안 생김
        s.commit()
        problems = s.query(Problem).all()
        assert len(problems) == 1
        assert len(problems[0].testcases) == 2


def test_sync_all(tmp_path):
    _make_problem_dir(tmp_path)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        result = sync_all(s, tmp_path)
        s.commit()
        assert len(result) == 1
