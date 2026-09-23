from pathlib import Path

from .system import run


def compose(*args: str, cwd: str | Path) -> None:
    run(["docker", "compose", *args], cwd=cwd)


def pull(cwd: str | Path) -> None:
    compose("pull", cwd=cwd)


def up(cwd: str | Path, *services: str) -> None:
    compose("up", "-d", *services, cwd=cwd)


def stop(cwd: str | Path) -> None:
    compose("stop", cwd=cwd)


def down(cwd: str | Path) -> None:
    compose("down", "--remove-orphans", cwd=cwd)
