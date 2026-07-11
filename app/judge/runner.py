import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

from app.judge.languages import Language

# subprocess 자체가 멈추지 않도록 시간제한에 더하는 여유(초)
_KILL_GRACE_S = 5
_DOCKER_KILL_TIMEOUT_S = 10


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
            # Hardening: drop all Linux capabilities, forbid privilege
            # escalation, and make the root FS read-only. A small writable
            # tmpfs at /tmp lets legitimate programs use scratch space
            # without persisting anything or touching the host.
            "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges",
            "--read-only",
            "--tmpfs", "/tmp:size=16m,mode=1777",
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
            try:
                subprocess.run(["docker", "kill", container],
                               capture_output=True,
                               timeout=_DOCKER_KILL_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                pass
            elapsed = int((time.perf_counter() - start) * 1000)
            return RunResult("TLE", "", "", None, elapsed)

        elapsed = int((time.perf_counter() - start) * 1000)
        stdout = proc.stdout.decode("utf-8", "replace")
        stderr = proc.stderr.decode("utf-8", "replace")

        # NOTE: TLE is enforced solely by the subprocess timeout above.
        # time_ms is wall-clock (includes container/interpreter startup);
        # accurate in-container timing is a future improvement.
        if proc.returncode == 137:   # 128 + SIGKILL, Docker OOM
            return RunResult("MLE", stdout, stderr, proc.returncode, elapsed)
        if proc.returncode != 0:
            return RunResult("RE", stdout, stderr, proc.returncode, elapsed)
        return RunResult("OK", stdout, stderr, 0, elapsed)
    except Exception as exc:  # noqa: BLE001 - 어떤 시스템 오류든 IE로
        try:
            subprocess.run(["docker", "kill", container], capture_output=True,
                           timeout=_DOCKER_KILL_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            pass
        return RunResult("IE", "", str(exc), None, 0)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
