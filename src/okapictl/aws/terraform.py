"""Terraform and output handling for the AWS demo."""

import json
from dataclasses import dataclass
from pathlib import Path

from ..errors import OkapiCtlError
from ..runner import CommandRunner


@dataclass(frozen=True)
class TerraformOutputs:
    values: dict[str, str]

    def __getitem__(self, name: str) -> str:
        return self.values[name]


class Terraform:
    def __init__(self, directory: Path, runner: CommandRunner):
        self.directory = directory
        self.runner = runner

    def init(self) -> None:
        self.runner.run(["terraform", "init", "-input=false"], cwd=str(self.directory))

    def apply(self, *, variables_file: Path | None, okapi_version: str,
              auto_approve: bool) -> None:
        args = ["terraform", "apply"]
        if auto_approve:
            args.append("-auto-approve")
        args.extend(["-var", f"okapi_image_tag={okapi_version}"])
        if variables_file is not None:
            variables_file = variables_file.expanduser().resolve()
            if not variables_file.is_file():
                raise OkapiCtlError(f"Terraform variables file was not found: {variables_file}")
            args.extend(["-var-file", str(variables_file)])
        self.runner.run(args, cwd=str(self.directory))

    def outputs(self) -> TerraformOutputs:
        result = self.runner.run(
            ["terraform", "output", "-json"], cwd=str(self.directory)
        )
        try:
            raw = json.loads(result.stdout)
            return TerraformOutputs({key: item["value"] for key, item in raw.items()})
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise OkapiCtlError("Terraform outputs were missing or invalid.") from exc
