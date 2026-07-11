import threading

from app.judge.background import start_inprocess_worker


def test_starts_daemon_thread_and_runs_target():
    ran = threading.Event()
    t = start_inprocess_worker(target=ran.set)
    assert t is not None
    assert t.daemon is True
    assert t.name == "ktoj-inprocess-worker"
    assert ran.wait(timeout=2)  # target actually executed in the thread


def test_disabled_via_env(monkeypatch):
    monkeypatch.setenv("KTOJ_INPROCESS_WORKER", "0")
    called = []
    result = start_inprocess_worker(target=lambda: called.append(1))
    assert result is None
    assert called == []


def test_enabled_by_default(monkeypatch):
    monkeypatch.delenv("KTOJ_INPROCESS_WORKER", raising=False)
    ran = threading.Event()
    t = start_inprocess_worker(target=ran.set)
    assert t is not None
    assert ran.wait(timeout=2)
