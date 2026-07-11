from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Problem, Submission, TestCase
from app.judge.runner import RunResult
from app.judge.worker import claim_next, judge_submission


def _seed(session):
    p = Problem(slug="a-plus-b", title="A+B", statement="", difficulty="왕초보",
                time_limit_ms=1000, memory_limit_mb=128)
    p.testcases.append(TestCase(ordinal=1, input="1 2\n",
                                expected_output="3\n", is_sample=True))
    p.testcases.append(TestCase(ordinal=2, input="10 20\n",
                                expected_output="30\n"))
    session.add(p)
    session.commit()
    return p


def _fresh_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_all_correct_gives_ac():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python",
                     source_code="a,b=map(int,input().split());print(a+b)")
    s.add(sub); s.commit()

    def fake_run(language, source_code, stdin_text, time_limit_ms,
                 memory_limit_mb, run_id):
        total = sum(int(x) for x in stdin_text.split())
        return RunResult("OK", f"{total}\n", "", 0, 12)

    judge_submission(sub, p, fake_run)
    assert sub.status == "AC"
    assert sub.time_ms == 12


def test_wrong_answer_records_case():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python", source_code="x")
    s.add(sub); s.commit()

    def fake_run(*a, **k):
        return RunResult("OK", "999\n", "", 0, 5)

    judge_submission(sub, p, fake_run)
    assert sub.status == "WA"
    assert sub.failed_case_no == 1


def test_syntax_error_gives_ce():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python",
                     source_code="def (:")  # 문법 오류
    s.add(sub); s.commit()

    def fake_run(*a, **k):
        raise AssertionError("runner should not be called on CE")

    judge_submission(sub, p, fake_run)
    assert sub.status == "CE"


def test_tle_propagates():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python", source_code="x=1")
    s.add(sub); s.commit()

    def fake_run(*a, **k):
        return RunResult("TLE", "", "", None, 1000)

    judge_submission(sub, p, fake_run)
    assert sub.status == "TLE"


def test_claim_next_marks_judging():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python", source_code="x=1")
    s.add(sub); s.commit()
    claimed = claim_next(s)
    assert claimed.id == sub.id
    assert claimed.status == "JUDGING"
    assert claim_next(s) is None
