"""Small subprocess boundary used by workflow adapters."""

from shutil import which
from subprocess import CompletedProcess, run
import sys

from .errors import OkapiCtlError


class CommandRunner:
    """Run external deployment tools without hiding their output."""

    def require(self, executable: str) -> None:
        if which(executable) is None:
            raise OkapiCtlError(
                f"Required executable '{executable}' was not found on PATH."
            )

    def run(
        self,
        args: list[str],
        *,
        cwd: str | None = None,
        input: str | None = None,
    ) -> CompletedProcess[str]:
        try:
            result = run(
                args,
                cwd=cwd,
                check=True,
                text=True,
                input=input,
                capture_output=True,
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=sys.stderr)
            return result
        except FileNotFoundError as exc:
            raise OkapiCtlError(f"Required executable '{args[0]}' was not found.") from exc
        except Exception as exc:
            raise OkapiCtlError(f"Command failed: {' '.join(args)}") from exc
