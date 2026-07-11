from app.db.models import Base, Problem, TestCase, Submission
from sqlalchemy import create_engine
from sqlalchemy.orm import Session


def test_can_create_problem_with_testcases():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        p = Problem(slug="a-plus-b", title="A+B", statement="두 수의 합",
                    difficulty="왕초보", time_limit_ms=1000, memory_limit_mb=128)
        p.testcases.append(TestCase(ordinal=1, input="1 2\n",
                                    expected_output="3\n", is_sample=True))
        s.add(p)
        s.commit()
        loaded = s.query(Problem).filter_by(slug="a-plus-b").one()
        assert loaded.title == "A+B"
        assert len(loaded.testcases) == 1
        assert loaded.testcases[0].expected_output == "3\n"


def test_submission_defaults_to_pending():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        sub = Submission(problem_id=1, language="python", source_code="print(3)")
        s.add(sub)
        s.commit()
        assert sub.status == "PENDING"
        assert sub.created_at is not None
