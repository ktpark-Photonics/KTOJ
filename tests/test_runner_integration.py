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
