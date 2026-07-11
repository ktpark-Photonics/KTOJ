# KTOJ 온라인 저지 MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 인증 없는 단일 사용자용 온라인 저지 MVP — 문제 보기 → Python 코드 제출 → Docker 격리 채점 → 제출 결과 확인.

**Architecture:** 두 개의 Python 프로세스(FastAPI 웹 + 채점 워커)가 SQLite DB를 공유한다. 웹은 제출을 `PENDING`으로 저장만 하고, 워커가 `PENDING`을 폴링해 Docker 컨테이너에서 실행·채점 후 결과를 DB에 기록한다. 화면(Jinja+HTMX)은 상태를 폴링해 자동 갱신한다.

**Tech Stack:** Python 3.11, FastAPI, Uvicorn, SQLAlchemy 2.0, SQLite, Jinja2, HTMX, Docker Desktop(WSL2 백엔드), pytest.

## Global Constraints

- Python 버전: 3.11 이상 (`python --version`으로 확인, 개발 셸은 PowerShell)
- 모든 명령은 프로젝트 루트 `C:\Users\kyongtae\Opencode\KTOJ`의 활성화된 venv에서 실행
- DB: SQLite 파일 `ktoj.sqlite3` (프로젝트 루트). ORM은 SQLAlchemy 2.0 스타일(`Mapped`, `mapped_column`)
- 채점 격리: Docker. 러너는 `docker run --rm --network none --memory <M>m --memory-swap <M>m --pids-limit 64 --cpus 1` 옵션을 항상 사용
- 지원 언어: MVP는 `python` 하나. 단, `languages.py` 어댑터 구조로 추가 언어 대비
- 판정 코드: `PENDING | JUDGING | AC | WA | TLE | MLE | RE | CE | IE`
- 난이도: 왕초보/초보. 문제는 순수 stdin→stdout
- 개발 방식: TDD (실패하는 테스트 먼저 → 최소 구현 → 통과 → 커밋)
- 출력 비교: 각 줄의 오른쪽 공백 제거 + 끝쪽 빈 줄 제거 후 일치 비교
- 커밋: 각 Task 끝에서 커밋. 커밋 메시지는 `feat:`/`test:`/`chore:` 접두어

---

## File Structure

```
KTOJ/
├─ app/
│  ├─ __init__.py
│  ├─ config.py              # 경로/설정 상수
│  ├─ db/
│  │  ├─ __init__.py
│  │  ├─ models.py           # Problem, TestCase, Submission
│  │  └─ session.py          # engine, SessionLocal, init_db
│  ├─ judge/
│  │  ├─ __init__.py
│  │  ├─ verdicts.py         # 판정 상수
│  │  ├─ grader.py           # 순수 비교 로직
│  │  ├─ languages.py        # 언어 어댑터
│  │  ├─ runner.py           # Docker 실행 (RunResult)
│  │  └─ worker.py           # 폴링 루프 + 채점 오케스트레이션
│  ├─ problems/
│  │  ├─ __init__.py
│  │  └─ loader.py           # 문제 파일 → DB 시딩
│  └─ web/
│     ├─ __init__.py
│     ├─ main.py             # FastAPI 앱, 라우트
│     └─ templates/
│        ├─ base.html
│        ├─ problem_list.html
│        ├─ problem_detail.html
│        ├─ submission_detail.html
│        └─ _submission_status.html   # HTMX 폴링 조각
├─ problems/                 # 문제 정의 폴더 (지문 + 테스트케이스)
│  └─ <slug>/problem.md, tests/*.in, *.out
├─ docker/
│  └─ Dockerfile.python
├─ tests/
│  ├─ test_grader.py
│  ├─ test_languages.py
│  ├─ test_loader.py
│  ├─ test_worker.py
│  ├─ test_runner_integration.py   # 실제 Docker 필요
│  └─ test_web.py
├─ requirements.txt
├─ run_web.py                # uvicorn 실행 진입점
├─ run_worker.py             # 워커 실행 진입점
└─ seed.py                   # 문제 시딩 진입점
```

---

## Task 1: 프로젝트 스캐폴딩 + 의존성 + Docker 검증

**Files:**
- Create: `requirements.txt`, `app/__init__.py`, `app/config.py`, `tests/__init__.py`
- Create (빈 패키지): `app/db/__init__.py`, `app/judge/__init__.py`, `app/problems/__init__.py`, `app/web/__init__.py`

**Interfaces:**
- Consumes: 없음
- Produces: `app.config.PROJECT_ROOT`, `app.config.PROBLEMS_DIR`, `app.config.DB_PATH`, `app.config.DB_URL`

- [ ] **Step 1: Docker Desktop 설치 (사용자 수동 작업)**

Docker Desktop for Windows를 설치한다 (WSL2 백엔드 사용). 설치 페이지: https://www.docker.com/products/docker-desktop/
설치 후 Docker Desktop을 실행해 엔진이 켜진 상태로 둔다.

- [ ] **Step 2: Docker 동작 검증**

PowerShell에서 실행:
```
docker --version
docker run --rm hello-world
```
Expected: 버전이 출력되고, `hello-world`가 "Hello from Docker!" 메시지를 출력. 실패하면 Docker Desktop이 실행 중인지 확인 후 재시도.

- [ ] **Step 3: venv 생성 및 활성화**

PowerShell에서 실행:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
Expected: 프롬프트 앞에 `(.venv)` 표시. (실행 정책 오류 시: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` 후 재시도)

- [ ] **Step 4: requirements.txt 작성**

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
sqlalchemy==2.0.36
jinja2==3.1.5
python-multipart==0.0.20
markdown==3.7
pytest==8.3.4
httpx==0.28.1
```

- [ ] **Step 5: 의존성 설치**

Run: `pip install -r requirements.txt`
Expected: 에러 없이 설치 완료.

- [ ] **Step 6: 빈 패키지 파일과 config 작성**

`app/__init__.py`, `tests/__init__.py`, `app/db/__init__.py`, `app/judge/__init__.py`, `app/problems/__init__.py`, `app/web/__init__.py` — 모두 빈 파일로 생성.

`app/config.py`:
```python
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROBLEMS_DIR = PROJECT_ROOT / "problems"
DB_PATH = PROJECT_ROOT / "ktoj.sqlite3"
DB_URL = f"sqlite:///{DB_PATH}"
```

- [ ] **Step 7: 검증**

Run: `python -c "from app.config import DB_URL; print(DB_URL)"`
Expected: `sqlite:///C:\Users\kyongtae\Opencode\KTOJ\ktoj.sqlite3` 형태 출력.

- [ ] **Step 8: Commit**

```
git add -A
git commit -m "chore: project scaffolding, deps, config"
```

---

## Task 2: DB 모델 & 세션

**Files:**
- Create: `app/db/models.py`, `app/db/session.py`
- Test: `tests/test_db.py`

**Interfaces:**
- Consumes: `app.config.DB_URL`
- Produces:
  - `app.db.models.Base`
  - `Problem(id, slug, title, statement, difficulty, time_limit_ms, memory_limit_mb, testcases)`
  - `TestCase(id, problem_id, ordinal, input, expected_output, is_sample)`
  - `Submission(id, problem_id, language, source_code, status, time_ms, memory_kb, failed_case_no, message, created_at)`
  - `app.db.session.engine`, `SessionLocal`, `init_db()`, `get_session()` (contextmanager)

- [ ] **Step 1: Write the failing test**

`tests/test_db.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_db.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.db.models'` 또는 import 에러.

- [ ] **Step 3: Write minimal implementation**

`app/db/models.py`:
```python
from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import (DeclarativeBase, Mapped, mapped_column,
                            relationship)


class Base(DeclarativeBase):
    pass


class Problem(Base):
    __tablename__ = "problems"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    statement: Mapped[str] = mapped_column(Text)
    difficulty: Mapped[str] = mapped_column(String(20))
    time_limit_ms: Mapped[int] = mapped_column(default=1000)
    memory_limit_mb: Mapped[int] = mapped_column(default=128)
    testcases: Mapped[list["TestCase"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan",
        order_by="TestCase.ordinal")


class TestCase(Base):
    __tablename__ = "testcases"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    ordinal: Mapped[int] = mapped_column(default=1)
    input: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text)
    is_sample: Mapped[bool] = mapped_column(default=False)
    problem: Mapped["Problem"] = relationship(back_populates="testcases")


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"))
    language: Mapped[str] = mapped_column(String(20))
    source_code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(10), default="PENDING",
                                        index=True)
    time_ms: Mapped[int | None] = mapped_column(default=None)
    memory_kb: Mapped[int | None] = mapped_column(default=None)
    failed_case_no: Mapped[int | None] = mapped_column(default=None)
    message: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc))
```

`app/db/session.py`:
```python
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DB_URL
from app.db.models import Base

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(engine)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_db.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
git add app/db tests/test_db.py
git commit -m "feat: db models and session (Problem, TestCase, Submission)"
```

---

## Task 3: 판정 상수 + grader (순수 로직)

**Files:**
- Create: `app/judge/verdicts.py`, `app/judge/grader.py`
- Test: `tests/test_grader.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `app.judge.verdicts`: 상수 `PENDING, JUDGING, AC, WA, TLE, MLE, RE, CE, IE` (문자열)
  - `app.judge.grader.normalize(text: str) -> str`
  - `app.judge.grader.outputs_match(actual: str, expected: str) -> bool`

- [ ] **Step 1: Write the failing test**

`tests/test_grader.py`:
```python
from app.judge.grader import normalize, outputs_match


def test_exact_match():
    assert outputs_match("3\n", "3\n") is True


def test_trailing_whitespace_ignored():
    assert outputs_match("3 \n", "3\n") is True


def test_trailing_newlines_ignored():
    assert outputs_match("3\n\n\n", "3") is True


def test_wrong_answer():
    assert outputs_match("4\n", "3\n") is False


def test_multiline_match():
    assert outputs_match("1\n2\n3\n", "1\n2\n3") is True


def test_normalize_strips_line_trailing_and_end_blanks():
    assert normalize("a  \nb\t\n\n") == "a\nb"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_grader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.judge.grader'`.

- [ ] **Step 3: Write minimal implementation**

`app/judge/verdicts.py`:
```python
PENDING = "PENDING"
JUDGING = "JUDGING"
AC = "AC"
WA = "WA"
TLE = "TLE"
MLE = "MLE"
RE = "RE"
CE = "CE"
IE = "IE"
```

`app/judge/grader.py`:
```python
def normalize(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def outputs_match(actual: str, expected: str) -> bool:
    return normalize(actual) == normalize(expected)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_grader.py -v`
Expected: PASS (6 passed).

- [ ] **Step 5: Commit**

```
git add app/judge/verdicts.py app/judge/grader.py tests/test_grader.py
git commit -m "feat: verdict constants and pure output grader"
```

---

## Task 4: 언어 어댑터

**Files:**
- Create: `app/judge/languages.py`
- Test: `tests/test_languages.py`

**Interfaces:**
- Consumes: 없음
- Produces:
  - `app.judge.languages.Language` (dataclass): `name: str`, `image: str`, `source_filename: str`, `run_cmd: list[str]`, `compile_cmd: list[str] | None`
  - `app.judge.languages.get_language(name: str) -> Language` (미지원 시 `KeyError`)
  - `app.judge.languages.LANGUAGES: dict[str, Language]` (현재 `"python"` 하나)
  - python 어댑터 값: image `"ktoj-python:latest"`, source_filename `"main.py"`, run_cmd `["python", "-B", "/sandbox/main.py"]`, compile_cmd `None`

- [ ] **Step 1: Write the failing test**

`tests/test_languages.py`:
```python
import pytest

from app.judge.languages import Language, get_language


def test_python_language_adapter():
    lang = get_language("python")
    assert isinstance(lang, Language)
    assert lang.image == "ktoj-python:latest"
    assert lang.source_filename == "main.py"
    assert lang.run_cmd == ["python", "-B", "/sandbox/main.py"]
    assert lang.compile_cmd is None


def test_unknown_language_raises():
    with pytest.raises(KeyError):
        get_language("brainfuck")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_languages.py -v`
Expected: FAIL — import 에러.

- [ ] **Step 3: Write minimal implementation**

`app/judge/languages.py`:
```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Language:
    name: str
    image: str
    source_filename: str
    run_cmd: list[str]
    compile_cmd: list[str] | None = None


LANGUAGES: dict[str, Language] = {
    "python": Language(
        name="python",
        image="ktoj-python:latest",
        source_filename="main.py",
        run_cmd=["python", "-B", "/sandbox/main.py"],
        compile_cmd=None,
    ),
}


def get_language(name: str) -> Language:
    return LANGUAGES[name]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_languages.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
git add app/judge/languages.py tests/test_languages.py
git commit -m "feat: language adapter (python)"
```

---

## Task 5: 채점용 Python Docker 이미지

**Files:**
- Create: `docker/Dockerfile.python`

**Interfaces:**
- Consumes: `app.judge.languages` python 어댑터의 image 이름 `ktoj-python:latest`
- Produces: 로컬 Docker 이미지 `ktoj-python:latest` (Python 3.11 slim, 비특권 사용자 `runner`)

- [ ] **Step 1: Dockerfile 작성**

`docker/Dockerfile.python`:
```dockerfile
FROM python:3.11-slim

# 비특권 사용자로 실행 (uid 1000)
RUN useradd --create-home --uid 1000 runner
USER runner
WORKDIR /sandbox

# .pyc 쓰기 방지, 출력 버퍼링 해제
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

CMD ["python", "-B", "/sandbox/main.py"]
```

- [ ] **Step 2: 이미지 빌드**

Run: `docker build -t ktoj-python:latest -f docker/Dockerfile.python docker`
Expected: `naming to docker.io/library/ktoj-python:latest` 로 끝나며 성공.

- [ ] **Step 3: 이미지 동작 확인**

Run: `docker run --rm ktoj-python:latest python -c "print('ok')"`
Expected: `ok` 출력.

- [ ] **Step 4: Commit**

```
git add docker/Dockerfile.python
git commit -m "feat: python judge docker image"
```

---

## Task 6: Docker 러너 (실제 Docker 통합)

**Files:**
- Create: `app/judge/runner.py`
- Test: `tests/test_runner_integration.py` (실제 Docker와 `ktoj-python:latest` 이미지 필요)

**Interfaces:**
- Consumes: `app.judge.languages.Language`
- Produces:
  - `app.judge.runner.RunResult` (dataclass): `status: str` (`"OK" | "TLE" | "MLE" | "RE" | "IE"`), `stdout: str`, `stderr: str`, `exit_code: int | None`, `time_ms: int`, `memory_kb: int | None`
  - `app.judge.runner.run_code(language, source_code: str, stdin_text: str, time_limit_ms: int, memory_limit_mb: int, run_id: str) -> RunResult`
  - MVP 정책: 시간초과→`TLE`(subprocess timeout), OOM(exit 137)→`MLE`, 그 외 non-zero exit→`RE`, exit 0→`OK`, Docker/시스템 예외→`IE`. `memory_kb`는 MVP에서 항상 `None`(정밀 측정은 향후 확장).

- [ ] **Step 1: Write the failing test**

`tests/test_runner_integration.py`:
```python
import shutil

import pytest

from app.judge.languages import get_language
from app.judge.runner import run_code

pytestmark = pytest.mark.skipif(
    shutil.which("docker") is None, reason="docker not installed")

PY = get_language("python")


def test_accepts_and_returns_stdout():
    r = run_code(PY, "print(int(input()) + int(input()))", "1\n2\n",
                 time_limit_ms=2000, memory_limit_mb=128, run_id="t-ac")
    assert r.status == "OK"
    assert r.exit_code == 0
    assert r.stdout.strip() == "3"


def test_runtime_error_gives_re():
    r = run_code(PY, "raise SystemExit(1)", "",
                 time_limit_ms=2000, memory_limit_mb=128, run_id="t-re")
    assert r.status == "RE"
    assert r.exit_code != 0


def test_timeout_gives_tle():
    r = run_code(PY, "while True: pass", "",
                 time_limit_ms=1000, memory_limit_mb=128, run_id="t-tle")
    assert r.status == "TLE"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_runner_integration.py -v`
Expected: FAIL — import 에러 (`app.judge.runner` 없음).

- [ ] **Step 3: Write minimal implementation**

`app/judge/runner.py`:
```python
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from app.judge.languages import Language

# subprocess 자체가 멈추지 않도록 시간제한에 더하는 여유(초)
_KILL_GRACE_S = 5


@dataclass
class RunResult:
    status: str          # "OK" | "TLE" | "MLE" | "RE" | "IE"
    stdout: str
    stderr: str
    exit_code: int | None
    time_ms: int
    memory_kb: int | None = None


def run_code(language: Language, source_code: str, stdin_text: str,
             time_limit_ms: int, memory_limit_mb: int,
             run_id: str) -> RunResult:
    if shutil.which("docker") is None:
        return RunResult("IE", "", "docker not found", None, 0)

    container = f"ktoj-{run_id}"
    tmp = Path(tempfile.mkdtemp(prefix="ktoj-"))
    try:
        (tmp / language.source_filename).write_text(source_code,
                                                    encoding="utf-8")
        cmd = [
            "docker", "run", "--rm", "--name", container,
            "--network", "none",
            "--memory", f"{memory_limit_mb}m",
            "--memory-swap", f"{memory_limit_mb}m",
            "--pids-limit", "64",
            "--cpus", "1",
            "-i",
            "-v", f"{tmp}:/sandbox:ro",
            language.image,
            *language.run_cmd,
        ]
        timeout_s = time_limit_ms / 1000
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd, input=stdin_text.encode("utf-8"),
                capture_output=True, timeout=timeout_s + _KILL_GRACE_S)
        except subprocess.TimeoutExpired:
            subprocess.run(["docker", "kill", container],
                           capture_output=True)
            elapsed = int((time.perf_counter() - start) * 1000)
            return RunResult("TLE", "", "", None, elapsed)

        elapsed = int((time.perf_counter() - start) * 1000)
        stdout = proc.stdout.decode("utf-8", "replace")
        stderr = proc.stderr.decode("utf-8", "replace")

        if elapsed > time_limit_ms:
            return RunResult("TLE", stdout, stderr, proc.returncode, elapsed)
        if proc.returncode == 137:   # 128 + SIGKILL, Docker OOM
            return RunResult("MLE", stdout, stderr, proc.returncode, elapsed)
        if proc.returncode != 0:
            return RunResult("RE", stdout, stderr, proc.returncode, elapsed)
        return RunResult("OK", stdout, stderr, 0, elapsed)
    except Exception as exc:  # noqa: BLE001 - 어떤 시스템 오류든 IE로
        subprocess.run(["docker", "kill", container], capture_output=True)
        return RunResult("IE", "", str(exc), None, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_runner_integration.py -v`
Expected: PASS (3 passed). Docker Desktop이 실행 중이고 `ktoj-python:latest` 이미지가 빌드되어 있어야 함. 첫 실행은 컨테이너 시작 오버헤드로 다소 느릴 수 있음.

- [ ] **Step 5: Commit**

```
git add app/judge/runner.py tests/test_runner_integration.py
git commit -m "feat: docker code runner with TLE/MLE/RE detection"
```

---

## Task 7: 문제 로더 (파일 → DB)

**Files:**
- Create: `app/problems/loader.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: `app.db.models.Problem`, `TestCase`; SQLAlchemy `Session`
- Produces:
  - `app.problems.loader.parse_problem_dir(path: Path) -> tuple[dict, list[dict]]` — `(problem_meta, testcases)`. `problem_meta` 키: `slug, title, statement, difficulty, time_limit_ms, memory_limit_mb`. testcase dict 키: `ordinal, input, expected_output, is_sample`.
  - `app.problems.loader.sync_problem(session, path: Path) -> Problem` — slug 기준 upsert(기존 문제·테스트케이스 교체)
  - `app.problems.loader.sync_all(session, problems_dir: Path) -> list[Problem]`
- 파일 포맷: `<dir>/problem.md`는 YAML 유사 프론트매터(`---`로 감싼 `key: value` 줄들: `title, difficulty, time_limit_ms, memory_limit_mb`) + 이후 본문(지문). 테스트케이스는 `<dir>/tests/<n>.in` + `<n>.out`, 파일명 숫자 오름차순이 ordinal. `1`번은 샘플(`is_sample=True`).

- [ ] **Step 1: Write the failing test**

`tests/test_loader.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_loader.py -v`
Expected: FAIL — import 에러.

- [ ] **Step 3: Write minimal implementation**

`app/problems/loader.py`:
```python
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
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_loader.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```
git add app/problems/loader.py tests/test_loader.py
git commit -m "feat: problem file loader with slug upsert"
```

---

## Task 8: 초기 문제 세트 시딩

**Files:**
- Create: `problems/hello-world/problem.md` + `tests/1.in,1.out,2.in,2.out`
- Create: `problems/a-plus-b/problem.md` + `tests/*`
- Create: `problems/sum-1-to-n/problem.md` + `tests/*`
- Create: `problems/max-of-n/problem.md` + `tests/*`
- Create: `problems/fizzbuzz/problem.md` + `tests/*`
- Create: `seed.py`

**Interfaces:**
- Consumes: `app.db.session.init_db`, `get_session`; `app.problems.loader.sync_all`; `app.config.PROBLEMS_DIR`
- Produces: `seed.py` 실행 시 DB에 위 5문제 시딩

- [ ] **Step 1: hello-world 문제 작성**

`problems/hello-world/problem.md`:
```
---
title: Hello World
difficulty: 왕초보
time_limit_ms: 1000
memory_limit_mb: 128
---
# Hello World

`Hello World!` 를 출력하시오.

## 입력
없음

## 출력
`Hello World!`

## 예제 출력
```
Hello World!
```
```
`problems/hello-world/tests/1.in`: (빈 파일)
`problems/hello-world/tests/1.out`:
```
Hello World!
```

- [ ] **Step 2: a-plus-b 문제 작성**

`problems/a-plus-b/problem.md`:
```
---
title: 두 수의 합
difficulty: 왕초보
time_limit_ms: 1000
memory_limit_mb: 128
---
# 두 수의 합 (A+B)

공백으로 구분된 두 정수 A, B가 주어질 때 A+B를 출력하시오.

## 입력
첫 줄에 두 정수 A, B (−1000 ≤ A, B ≤ 1000)

## 출력
A+B
```
`tests/1.in`: `1 2\n`  → `tests/1.out`: `3\n`
`tests/2.in`: `-5 10\n` → `tests/2.out`: `5\n`

- [ ] **Step 3: sum-1-to-n 문제 작성**

`problems/sum-1-to-n/problem.md`:
```
---
title: 1부터 N까지의 합
difficulty: 초보
time_limit_ms: 1000
memory_limit_mb: 128
---
# 1부터 N까지의 합

정수 N이 주어질 때 1부터 N까지의 합을 출력하시오.

## 입력
첫 줄에 정수 N (1 ≤ N ≤ 100000)

## 출력
1부터 N까지의 합
```
`tests/1.in`: `10\n` → `tests/1.out`: `55\n`
`tests/2.in`: `100\n` → `tests/2.out`: `5050\n`

- [ ] **Step 4: max-of-n 문제 작성**

`problems/max-of-n/problem.md`:
```
---
title: N개 수 중 최댓값
difficulty: 초보
time_limit_ms: 1000
memory_limit_mb: 128
---
# N개 수 중 최댓값

첫 줄에 N, 둘째 줄에 N개의 정수가 공백으로 주어진다. 최댓값을 출력하시오.

## 입력
첫 줄에 N (1 ≤ N ≤ 1000), 둘째 줄에 N개의 정수

## 출력
가장 큰 수
```
`tests/1.in`: `5\n3 1 4 1 5\n` → `tests/1.out`: `5\n`
`tests/2.in`: `3\n-1 -5 -3\n` → `tests/2.out`: `-1\n`

- [ ] **Step 5: fizzbuzz 문제 작성**

`problems/fizzbuzz/problem.md`:
```
---
title: FizzBuzz
difficulty: 초보
time_limit_ms: 1000
memory_limit_mb: 128
---
# FizzBuzz

1부터 N까지 한 줄에 하나씩 출력하되, 3의 배수는 `Fizz`, 5의 배수는 `Buzz`, 15의 배수는 `FizzBuzz`를 출력하시오.

## 입력
첫 줄에 정수 N (1 ≤ N ≤ 100)

## 출력
규칙에 따른 N개의 줄
```
`tests/1.in`: `5\n` → `tests/1.out`: `1\n2\nFizz\n4\nBuzz\n`
`tests/2.in`: `15\n` → `tests/2.out`: `1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz\n`

- [ ] **Step 6: seed.py 작성**

`seed.py`:
```python
from app.config import PROBLEMS_DIR
from app.db.session import get_session, init_db
from app.problems.loader import sync_all


def main() -> None:
    init_db()
    with get_session() as session:
        problems = sync_all(session, PROBLEMS_DIR)
    print(f"seeded {len(problems)} problems")


if __name__ == "__main__":
    main()
```

- [ ] **Step 7: 시딩 실행 및 검증**

Run: `python seed.py`
Expected: `seeded 5 problems` 출력, 프로젝트 루트에 `ktoj.sqlite3` 생성.

Run: `python -c "from app.db.session import get_session; from app.db.models import Problem; s=get_session().__enter__(); print([p.slug for p in s.query(Problem).all()])"`
Expected: 5개 slug 목록 출력.

- [ ] **Step 8: Commit**

```
git add problems seed.py
git commit -m "feat: seed 5 beginner problems"
```

---

## Task 9: 채점 워커 (오케스트레이션 + 폴링 루프)

**Files:**
- Create: `app/judge/worker.py`, `run_worker.py`
- Test: `tests/test_worker.py` (러너를 가짜(fake)로 주입 — Docker 불필요)

**Interfaces:**
- Consumes: `app.db.models`, `app.judge.grader.outputs_match`, `app.judge.languages.get_language`, `app.judge.runner.run_code`/`RunResult`, `app.judge.verdicts`
- Produces:
  - `app.judge.worker.judge_submission(submission, problem, run_fn) -> None` — `submission.status`/`time_ms`/`memory_kb`/`failed_case_no`/`message`를 직접 갱신. `run_fn`은 `run_code`와 동일 시그니처(테스트에서 주입).
  - `app.judge.worker.claim_next(session) -> Submission | None` — 가장 오래된 `PENDING`을 `JUDGING`으로 원자적 전환 후 반환
  - `app.judge.worker.process_once(session, run_fn) -> bool` — 하나 처리하면 True
  - `app.judge.worker.run_forever(poll_interval_s: float = 2.0) -> None` — 무한 루프
  - 판정 규칙: 언어 파이썬은 `compile()`로 사전 문법 검사 → 실패 시 `CE`. 케이스 순회 중 `OK`가 아니면 즉시 해당 판정(runner status `OK/TLE/MLE/RE/IE` → verdict, `OK`+출력불일치 → `WA`, `failed_case_no=ordinal`). 전부 통과 → `AC`. `time_ms`=케이스 최댓값.

- [ ] **Step 1: Write the failing test**

`tests/test_worker.py`:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_worker.py -v`
Expected: FAIL — import 에러.

- [ ] **Step 3: Write minimal implementation**

`app/judge/worker.py`:
```python
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
```

`run_worker.py`:
```python
from app.db.session import init_db
from app.judge.worker import run_forever

if __name__ == "__main__":
    init_db()
    run_forever()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_worker.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```
git add app/judge/worker.py run_worker.py tests/test_worker.py
git commit -m "feat: judge worker with polling loop and verdict orchestration"
```

---

## Task 10: 웹 — 문제 목록 & 문제 상세

**Files:**
- Create: `app/web/main.py`, `app/web/templates/base.html`, `problem_list.html`, `problem_detail.html`
- Create: `run_web.py`
- Test: `tests/test_web.py`

**Interfaces:**
- Consumes: `app.db.session` (`SessionLocal`, `init_db`), `app.db.models`
- Produces:
  - `app.web.main.app` (FastAPI)
  - Routes: `GET /` (문제 목록), `GET /problems/{slug}` (문제 상세 + 제출 폼)
  - 템플릿은 `app/web/templates`. base는 HTMX를 `<script src="https://unpkg.com/htmx.org@2.0.4"></script>`로 로드.

- [ ] **Step 1: Write the failing test**

`tests/test_web.py`:
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, Problem, TestCase
import app.web.main as web


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite:///:memory:",
                           connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(bind=engine, expire_on_commit=False)
    with TestingSession() as s:
        p = Problem(slug="a-plus-b", title="A+B", statement="# A+B\n합을 출력",
                    difficulty="왕초보", time_limit_ms=1000, memory_limit_mb=128)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py -v`
Expected: FAIL — `app.web.main` 없음.

- [ ] **Step 3: Write minimal implementation**

`app/web/main.py`:
```python
import markdown as md
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select

from app.db.models import Problem
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
```

`app/web/templates/base.html`:
```html
<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}KTOJ{% endblock %}</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px;
           margin: 2rem auto; padding: 0 1rem; line-height: 1.6; }
    a { color: #2563eb; text-decoration: none; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
    pre { background: #f4f4f5; padding: 10px; overflow-x: auto; }
    textarea { width: 100%; font-family: monospace; }
    .verdict-AC { color: #16a34a; font-weight: bold; }
    .verdict-WA, .verdict-TLE, .verdict-MLE, .verdict-RE,
    .verdict-CE, .verdict-IE { color: #dc2626; font-weight: bold; }
    .badge { font-size: 0.8rem; background:#eef; padding:2px 6px;
             border-radius: 4px; }
  </style>
</head>
<body>
  <h1><a href="/">KTOJ</a></h1>
  {% block content %}{% endblock %}
</body>
</html>
```

`app/web/templates/problem_list.html`:
```html
{% extends "base.html" %}
{% block title %}문제 목록 - KTOJ{% endblock %}
{% block content %}
<h2>문제 목록</h2>
<table>
  <tr><th>#</th><th>제목</th><th>난이도</th></tr>
  {% for p in problems %}
  <tr>
    <td>{{ p.id }}</td>
    <td><a href="/problems/{{ p.slug }}">{{ p.title }}</a></td>
    <td><span class="badge">{{ p.difficulty }}</span></td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
```

`app/web/templates/problem_detail.html`:
```html
{% extends "base.html" %}
{% block title %}{{ problem.title }} - KTOJ{% endblock %}
{% block content %}
<p><a href="/">← 목록</a></p>
<span class="badge">{{ problem.difficulty }}</span>
<span class="badge">시간 {{ problem.time_limit_ms }}ms</span>
<span class="badge">메모리 {{ problem.memory_limit_mb }}MB</span>
<div>{{ problem.statement | markdown | safe }}</div>

{% for c in samples %}
<h4>예제 입력 {{ loop.index }}</h4><pre>{{ c.input }}</pre>
<h4>예제 출력 {{ loop.index }}</h4><pre>{{ c.expected_output }}</pre>
{% endfor %}

<h3>제출</h3>
<form method="post" action="/problems/{{ problem.slug }}/submit">
  <input type="hidden" name="language" value="python">
  <textarea name="source_code" rows="15"
            placeholder="# Python 코드를 입력하세요"></textarea>
  <p><button type="submit">제출</button></p>
</form>
{% endblock %}
```

`run_web.py`:
```python
import uvicorn

from app.db.session import init_db

if __name__ == "__main__":
    init_db()
    uvicorn.run("app.web.main:app", host="127.0.0.1", port=8000, reload=False)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```
git add app/web run_web.py tests/test_web.py
git commit -m "feat: web problem list and detail pages"
```

---

## Task 11: 웹 — 제출 접수 + 제출 상세 + HTMX 폴링

**Files:**
- Modify: `app/web/main.py` (라우트 3개 추가)
- Create: `app/web/templates/submission_detail.html`, `app/web/templates/_submission_status.html`
- Modify: `tests/test_web.py` (테스트 추가)

**Interfaces:**
- Consumes: Task 10의 `app`, `templates`, `SessionLocal`; `app.db.models.Submission`
- Produces:
  - `POST /problems/{slug}/submit` (form: `language`, `source_code`) → `Submission(PENDING)` 저장 후 `/submissions/{id}`로 303 리다이렉트
  - `GET /submissions/{id}` → 제출 상세 페이지 (상태 조각을 HTMX로 폴링)
  - `GET /submissions/{id}/status` → `_submission_status.html` 조각 (상태 확정 전에는 `hx-trigger`로 2초마다 자기 자신 재요청, 확정되면 폴링 중단)

- [ ] **Step 1: Write the failing test**

`tests/test_web.py`에 추가:
```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_web.py -v`
Expected: FAIL — `/problems/{slug}/submit` 404 (라우트 없음).

- [ ] **Step 3: Write minimal implementation**

`app/web/main.py`에 import 추가 및 라우트 추가:
```python
# 상단 import에 추가:
from fastapi import Form
from fastapi.responses import RedirectResponse
from app.db.models import Submission


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
```

`app/web/templates/_submission_status.html`:
```html
{% set pending = sub.status in ["PENDING", "JUDGING"] %}
<div id="status"
     {% if pending %}
     hx-get="/submissions/{{ sub.id }}/status"
     hx-trigger="load delay:2s"
     hx-swap="outerHTML"
     {% endif %}>
  <p>상태: <span class="verdict-{{ sub.status }}">{{ sub.status }}</span></p>
  {% if not pending %}
    {% if sub.time_ms is not none %}<p>실행시간: {{ sub.time_ms }} ms</p>{% endif %}
    {% if sub.failed_case_no %}<p>틀린 테스트케이스: {{ sub.failed_case_no }}번</p>{% endif %}
    {% if sub.message %}<pre>{{ sub.message }}</pre>{% endif %}
  {% endif %}
</div>
```

`app/web/templates/submission_detail.html`:
```html
{% extends "base.html" %}
{% block title %}제출 #{{ sub.id }} - KTOJ{% endblock %}
{% block content %}
<p><a href="/problems/{{ problem.slug }}">← {{ problem.title }}</a></p>
<h2>제출 #{{ sub.id }}</h2>
<p>문제: {{ problem.title }} / 언어: {{ sub.language }}</p>
{% include "_submission_status.html" %}
<h3>제출한 코드</h3>
<pre>{{ sub.source_code }}</pre>
{% endblock %}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_web.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```
git add app/web tests/test_web.py
git commit -m "feat: submission intake, detail page, htmx status polling"
```

---

## Task 12: 엔드투엔드 확인 + 실행 안내

**Files:**
- Create: `README.md`

**Interfaces:**
- Consumes: 전체 시스템
- Produces: `README.md` (실행 방법), 수동 E2E 확인

- [ ] **Step 1: 전체 자동 테스트 실행**

Run: `pytest -v`
Expected: 모든 테스트 통과. (Docker 미실행 시 `test_runner_integration.py`는 skip)

- [ ] **Step 2: README 작성**

`README.md`:
```markdown
# KTOJ — 온라인 저지 (학습용)

Python 코드를 제출하면 Docker 격리 환경에서 채점하는 미니 온라인 저지.

## 요구 사항
- Python 3.11+
- Docker Desktop (실행 중이어야 함)

## 준비
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
docker build -t ktoj-python:latest -f docker/Dockerfile.python docker
python seed.py
```

## 실행 (터미널 2개)
```
# 터미널 1 — 웹
python run_web.py         # http://127.0.0.1:8000

# 터미널 2 — 채점 워커
python run_worker.py
```

## 테스트
```
pytest -v
```
```

- [ ] **Step 3: 수동 E2E 확인 (Docker 실행 상태)**

1. `docker build -t ktoj-python:latest -f docker/Dockerfile.python docker`
2. `python seed.py`
3. 터미널 2개에서 `python run_web.py` 와 `python run_worker.py` 실행
4. 브라우저에서 http://127.0.0.1:8000 접속 → "두 수의 합" 선택
5. 코드 제출: `a,b=map(int,input().split());print(a+b)`
6. Expected: 제출 상세 페이지에서 상태가 `PENDING`/`JUDGING` → 몇 초 뒤 `AC`로 자동 갱신
7. 일부러 틀린 코드 `print(0)` 제출 → `WA`, 틀린 케이스 번호 표시 확인
8. 무한루프 `while True: pass` 제출 → `TLE` 확인

- [ ] **Step 4: Commit**

```
git add README.md
git commit -m "docs: add README with setup and run instructions"
```

---

## Self-Review 결과

- **스펙 커버리지:** §1 범위(문제 보기/제출/채점/기록) → Task 10·11; §3 아키텍처(웹+워커+DB 큐) → Task 2·9·10·11; §4 컴포넌트 전부 매핑(runner→T6, grader→T3, languages→T4, worker→T9, loader→T7, db→T2); §5 데이터 모델 → Task 2; §6 채점 흐름 → Task 9·11; §7 판정/에러 → Task 6·9; §8 문제 세트 → Task 8; §9 테스트 전략 → 각 Task TDD + T6 통합 + T12 E2E; §10 구조 → File Structure. 누락 없음.
- **플레이스홀더 스캔:** 모든 코드 단계에 실제 코드 포함. TBD/TODO 없음.
- **타입 일관성:** `RunResult`(status/stdout/stderr/exit_code/time_ms/memory_kb)가 runner(T6)·worker(T9)·worker 테스트에서 일치. `run_code`/`run_fn` 시그니처 일치. `Language` 필드 T4↔T6 일치. verdict 문자열 상수 일관.
