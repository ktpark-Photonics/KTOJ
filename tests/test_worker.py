from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, Problem, Submission, TestCase
from app.judge.runner import RunResult
from app.judge.worker import claim_next, judge_submission, process_once


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


def test_time_ms_is_max_across_cases():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python",
                     source_code="a,b=map(int,input().split());print(a+b)")
    s.add(sub); s.commit()
    times = iter([10, 42])

    def fake_run(language, source_code, stdin_text, time_limit_ms,
                 memory_limit_mb, run_id):
        total = sum(int(x) for x in stdin_text.split())
        return RunResult("OK", f"{total}\n", "", 0, next(times))

    judge_submission(sub, p, fake_run)
    assert sub.status == "AC"
    assert sub.time_ms == 42


def test_runtime_error_status_maps_to_re():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python", source_code="x=1")
    s.add(sub); s.commit()

    def fake_run(*a, **k):
        return RunResult("RE", "", "boom", 1, 3)

    judge_submission(sub, p, fake_run)
    assert sub.status == "RE"
    assert sub.failed_case_no == 1


def test_process_once_isolates_runner_exception():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python", source_code="x=1")
    s.add(sub); s.commit()

    def boom(*a, **k):
        raise RuntimeError("runner exploded")

    worked = process_once(s, boom)
    assert worked is True
    s.refresh(sub)
    assert sub.status == "IE"
    assert "runner exploded" in (sub.message or "")


def test_problem_without_testcases_gives_ie():
    s = _fresh_session()
    p = Problem(slug="empty", title="Empty", statement="", difficulty="왕초보",
                time_limit_ms=1000, memory_limit_mb=128)
    s.add(p); s.commit()
    sub = Submission(problem_id=p.id, language="python", source_code="print(1)")
    s.add(sub); s.commit()

    def must_not_run(*a, **k):
        raise AssertionError("runner should not run without testcases")

    judge_submission(sub, p, must_not_run)
    assert sub.status == "IE"


def test_indentation_error_message_preserves_name():
    s = _fresh_session()
    p = _seed(s)
    sub = Submission(problem_id=p.id, language="python",
                     source_code="if True:\npass")  # IndentationError at compile
    s.add(sub); s.commit()

    judge_submission(sub, p, lambda *a, **k: None)
    assert sub.status == "CE"
    assert "IndentationError" in (sub.message or "")
