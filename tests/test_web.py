import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Problem, TestCase
import app.web.main as web


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    with TestingSession() as s:
        p = Problem(slug="a-plus-b", title="A+B", statement="# A+B\n합을 출력",
                    difficulty="왕초보", time_limit_ms=1000, memory_limit_mb=128,
                    starter_code="a, b = map(int, input().split())")
        p.testcases.append(TestCase(ordinal=1, input="1 2\n",
                                    expected_output="3\n", is_sample=True))
        s.add(p); s.commit()
    monkeypatch.setattr(web, "SessionLocal", TestingSession)
    return TestClient(web.app)


def test_problem_list_shows_title(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "A+B" in r.text


def test_problem_detail_shows_statement_and_sample(client):
    r = client.get("/problems/a-plus-b")
    assert r.status_code == 200
    assert "합을 출력" in r.text
    assert "1 2" in r.text  # 샘플 입력 노출


def test_problem_detail_prefills_starter_code(client):
    r = client.get("/problems/a-plus-b")
    assert r.status_code == 200
    # 제출 textarea에 입력 읽기 스타터 코드가 미리 채워져 있어야 한다
    assert "map(int, input().split())" in r.text


def test_submit_creates_pending_submission_and_redirects(client):
    r = client.post("/problems/a-plus-b/submit",
                    data={"language": "python",
                          "source_code": "print(3)"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"].startswith("/submissions/")


def test_submission_status_fragment_shows_verdict(client):
    r = client.post("/problems/a-plus-b/submit",
                    data={"language": "python", "source_code": "print(3)"},
                    follow_redirects=True)
    assert r.status_code == 200
    # 아직 채점 전이므로 PENDING 표시
    assert "PENDING" in r.text


def test_submit_unknown_language_rejected(client):
    r = client.post("/problems/a-plus-b/submit",
                    data={"language": "cobol", "source_code": "x"},
                    follow_redirects=False)
    assert r.status_code == 400
