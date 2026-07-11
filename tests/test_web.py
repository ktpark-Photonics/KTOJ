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


def test_problem_detail_sets_last_problem_cookie(client):
    r = client.get("/problems/a-plus-b")
    assert r.status_code == 200
    assert r.cookies.get("last_problem") == "a-plus-b"


def test_solve_redirects_to_last_problem_when_cookie_set(client):
    client.cookies.set("last_problem", "a-plus-b")
    r = client.get("/solve", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/problems/a-plus-b"


def test_solve_shows_empty_state_without_cookie(client):
    client.cookies.clear()
    r = client.get("/solve", follow_redirects=False)
    assert r.status_code == 200
    assert "아직 풀던 문제가 없어요" in r.text


def test_submission_history_lists_submissions(client):
    # 제출 두 건 생성
    client.post("/problems/a-plus-b/submit",
                data={"language": "python", "source_code": "print(3)"})
    client.post("/problems/a-plus-b/submit",
                data={"language": "python", "source_code": "print(4)"})
    r = client.get("/submissions")
    assert r.status_code == 200
    assert "내 제출 이력" in r.text
    assert "A+B" in r.text          # 문제 제목 노출
    assert "#1" in r.text and "#2" in r.text


def test_submission_history_empty_state(client):
    r = client.get("/submissions")
    assert r.status_code == 200
    assert "아직 제출이 없어요" in r.text
