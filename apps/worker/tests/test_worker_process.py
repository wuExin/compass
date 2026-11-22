import os
import selectors
import signal
import subprocess
import sys

import pytest


# The graceful-stop semantics under test are POSIX-only: select() on pipes raises
# OSError on Windows, send_signal(SIGTERM) is a TerminateProcess hard kill there,
# and CTRL_C_EVENT would reach the whole console process group. CI keeps coverage.
@pytest.mark.skipif(
    sys.platform == "win32",
    reason=(
        "POSIX signal lifecycle: select() on pipes and graceful SIGTERM "
        "cannot be exercised on Windows."
    ),
)
@pytest.mark.parametrize("stop_signal", [signal.SIGINT, signal.SIGTERM])
def test_worker_starts_without_services_and_stops_cleanly(stop_signal: int) -> None:
    env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    process = subprocess.Popen(
        [sys.executable, "-m", "compass_worker"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env,
    )
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            assert selector.select(timeout=10), "Worker did not become ready"
            assert (
                "Worker scaffold ready; no task consumers configured" in process.stdout.readline()
            )
        process.send_signal(stop_signal)
        output, _ = process.communicate(timeout=10)
        assert process.returncode == 0, output
        assert "Worker stopped" in output
    finally:
        if process.poll() is None:
            process.kill()
        process.communicate()
