"""Run the judge worker inside the web process as a daemon thread.

For single-user use this avoids launching a second terminal: `run_web.py`
alone serves the site AND judges submissions. Set the environment variable
`KTOJ_INPROCESS_WORKER=0` to opt out (e.g. when running a dedicated
`run_worker.py` process instead).
"""
import os
import threading
from collections.abc import Callable

from app.judge import worker


def start_inprocess_worker(
    target: Callable[[], None] | None = None,
) -> threading.Thread | None:
    if os.environ.get("KTOJ_INPROCESS_WORKER", "1") == "0":
        return None
    thread = threading.Thread(
        target=target or worker.run_forever,
        name="ktoj-inprocess-worker",
        daemon=True,
    )
    thread.start()
    return thread
