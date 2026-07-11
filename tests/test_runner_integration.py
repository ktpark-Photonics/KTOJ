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


def test_memory_limit_gives_mle():
    # Allocate ~640MB (80M ints) under a 128MB limit -> container OOM
    # -> exit 137 -> MLE.
    r = run_code(PY, "x = [0] * (80 * 1024 * 1024)\nprint(len(x))", "",
                 time_limit_ms=3000, memory_limit_mb=128, run_id="t-mle")
    assert r.status == "MLE"


def test_allows_tmp_scratch_under_readonly_rootfs():
    # Root FS is read-only, but /tmp is a writable tmpfs; a legitimate
    # program using scratch space must still succeed.
    src = ("open('/tmp/scratch.txt', 'w').write('hi')\n"
           "print(open('/tmp/scratch.txt').read())")
    r = run_code(PY, src, "", time_limit_ms=3000, memory_limit_mb=128,
                 run_id="t-tmp")
    assert r.status == "OK"
    assert r.stdout.strip() == "hi"
