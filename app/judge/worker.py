import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Problem, Submission
from app.db.session import SessionLocal
from app.judge import verdicts
from app.judge.grader import outputs_match
from app.judge.languages import get_language
from app.judge.runner import run_code

# runner status → 최종 verdict (OK는 별도 처리)
_STATUS_TO_VERDICT = {
    "TLE": verdicts.TLE,
    "MLE": verdicts.MLE,
    "RE": verdicts.RE,
    "IE": verdicts.IE,
}


def _syntax_ok(language_name: str, source_code: str) -> tuple[bool, str]:
    if language_name == "python":
        try:
            compile(source_code, "<submission>", "exec")
        except SyntaxError as exc:
            return False, f"SyntaxError: {exc}"
    return True, ""


def judge_submission(submission: Submission, problem: Problem,
                     run_fn=run_code) -> None:
    ok, msg = _syntax_ok(submission.language, submission.source_code)
    if not ok:
        submission.status = verdicts.CE
        submission.message = msg
        return

    language = get_language(submission.language)
    max_time = 0
    for case in problem.testcases:
        result = run_fn(language, submission.source_code, case.input,
                        problem.time_limit_ms, problem.memory_limit_mb,
                        run_id=f"{submission.id}-{case.ordinal}")
        max_time = max(max_time, result.time_ms or 0)
        if result.status != "OK":
            submission.status = _STATUS_TO_VERDICT.get(result.status,
                                                       verdicts.IE)
            submission.failed_case_no = case.ordinal
            submission.time_ms = max_time
            submission.message = (result.stderr or "")[:2000]
            return
        if not outputs_match(result.stdout, case.expected_output):
            submission.status = verdicts.WA
            submission.failed_case_no = case.ordinal
            submission.time_ms = max_time
            return

    submission.status = verdicts.AC
    submission.time_ms = max_time
    submission.failed_case_no = None


def claim_next(session: Session) -> Submission | None:
    sub = session.scalar(
        select(Submission).where(Submission.status == verdicts.PENDING)
        .order_by(Submission.id).limit(1))
    if sub is None:
        return None
    sub.status = verdicts.JUDGING
    session.commit()
    return sub


def process_once(session: Session, run_fn=run_code) -> bool:
    sub = claim_next(session)
    if sub is None:
        return False
    problem = session.get(Problem, sub.problem_id)
    try:
        judge_submission(sub, problem, run_fn)
    except Exception as exc:  # noqa: BLE001
        sub.status = verdicts.IE
        sub.message = str(exc)[:2000]
    session.commit()
    return True


def run_forever(poll_interval_s: float = 2.0) -> None:
    print("KTOJ judge worker started. polling for submissions...")
    while True:
        session = SessionLocal()
        try:
            worked = process_once(session)
        finally:
            session.close()
        if not worked:
            time.sleep(poll_interval_s)
