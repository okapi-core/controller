import os
import subprocess
import time
from pathlib import Path


def run(cmd: list[str], *, cwd: str | Path | None = None, env: dict[str, str] | None = None) -> None:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    print(f"+ {' '.join(cmd)}", flush=True)
    subprocess.run(cmd, cwd=cwd, env=merged_env, check=True)


def check_output(cmd: list[str]) -> str:
    print(f"+ {' '.join(cmd)}", flush=True)
    return subprocess.check_output(cmd, text=True).strip()


def wait_until(name: str, fn, *, timeout_seconds: int, interval_seconds: int = 5) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            if fn():
                return
        except Exception as exc:
            last_error = exc
        time.sleep(interval_seconds)
    if last_error:
        raise TimeoutError(f"timed out waiting for {name}: {last_error}") from last_error
    raise TimeoutError(f"timed out waiting for {name}")


def ensure_dir(path: str | Path, mode: int = 0o755) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    os.chmod(p, mode)
    return p
