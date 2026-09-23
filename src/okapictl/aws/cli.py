"""Small AWS CLI adapter."""

from dataclasses import dataclass

from ..runner import CommandRunner


@dataclass(frozen=True)
class AwsCli:
    runner: CommandRunner
    region: str

    def run(self, *args: str, capture: bool = False) -> str:
        result = self.runner.run(
            ["aws", "--region", self.region, *args],
        )
        return result.stdout.strip() if capture else ""

    def get_parameter(self, name: str, *, decrypt: bool = False, default: str | None = None) -> str:
        args = ["ssm", "get-parameter", "--name", name]
        if decrypt:
            args.extend(["--with-decryption"])
        args.extend(["--query", "Parameter.Value", "--output", "text"])
        try:
            return self.run(*args, capture=True)
        except Exception:
            if default is not None:
                return default
            raise

    def put_parameter(self, name: str, value: str, *, secure: bool = False) -> None:
        parameter_type = "SecureString" if secure else "String"
        self.run(
            "ssm", "put-parameter", "--name", name, "--type", parameter_type,
            "--value", value, "--overwrite",
        )
