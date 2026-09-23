"""CodeDeploy artifact packaging and S3 upload."""

import shutil
import tempfile
import time
import zipfile
from pathlib import Path

from .cli import AwsCli


class CodeDeployArtifacts:
    def __init__(self, aws_directory: Path, aws_cli: AwsCli):
        self.aws_directory = aws_directory
        self.aws_cli = aws_cli

    def package(self, name: str, output_directory: Path) -> Path:
        source = self.aws_directory / "deploy" / name
        if not source.is_dir():
            raise ValueError(f"Unknown deployment bundle: {name}")
        stage = Path(tempfile.mkdtemp(prefix=f"{name}-bundle-"))
        try:
            shutil.copytree(source, stage, dirs_exist_ok=True)
            shutil.copytree(
                self.aws_directory / "deploy" / "common",
                stage / "common",
                dirs_exist_ok=True,
            )
            output_directory.mkdir(parents=True, exist_ok=True)
            archive = output_directory / f"{name}.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
                for path in stage.rglob("*"):
                    if path.is_file():
                        bundle.write(path, path.relative_to(stage))
            return archive
        finally:
            shutil.rmtree(stage)

    def upload(self, name: str, bucket: str) -> str:
        with tempfile.TemporaryDirectory(prefix="okapictl-codedeploy-") as tmp:
            archive = self.package(name, Path(tmp))
            key = f"codedeploy/{name}/{int(time.time())}.zip"
            self.aws_cli.run("s3", "cp", str(archive), f"s3://{bucket}/{key}")
            return key
