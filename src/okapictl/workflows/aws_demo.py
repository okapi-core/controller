"""AWS OpenTelemetry demo workflow."""

from ..assets import BundleAssetResolver
from ..config import AwsDemoConfig
from ..errors import OkapiCtlError
from ..runner import CommandRunner
from ..state import write_state
import sys


class AwsDemoRunner:
    """Provision the AWS demo and converge both CodeDeploy applications."""

    def __init__(self, config: AwsDemoConfig, runner: CommandRunner,
                 asset_resolver: BundleAssetResolver):
        self.config = config
        self.runner = runner
        self.asset_resolver = asset_resolver

    def run(self) -> None:
        self.runner.require("terraform")
        self.runner.require("aws")
        bundle = self.asset_resolver.resolve(self.config.bundle_version)
        aws_directory = bundle.materialize_aws_assets(self.config.aws_directory)
        terraform_directory = aws_directory / "terraform"

        init_args = ["terraform", "init", "-input=false"]
        self.runner.run(init_args, cwd=str(terraform_directory))

        apply_args = ["terraform", "apply"]
        if self.config.auto_approve:
            apply_args.append("-auto-approve")
        # The controller release and the deployed Okapi images must stay in
        # lockstep. A user-provided tfvars file may configure the repository,
        # but cannot accidentally select a different Okapi image tag.
        apply_args.extend(["-var", f"okapi_image_tag={self.config.bundle_version}"])
        if self.config.terraform_vars_file is not None:
            vars_file = self.config.terraform_vars_file.expanduser().resolve()
            if not vars_file.is_file():
                raise OkapiCtlError(f"Terraform variables file was not found: {vars_file}")
            apply_args.extend(["-var-file", str(vars_file)])
        self.runner.run(apply_args, cwd=str(terraform_directory))

        # This is the copied, versioned operator from okapi-demo-tf. It packages
        # and uploads both CodeDeploy bundles, then redeploys Okapi before the
        # full OTEL demo so the collector has a live ingester endpoint.
        self.runner.run(
            [sys.executable, "-m", "ops.okapi_demo_ops", "start", "--redeploy"],
            cwd=str(aws_directory),
        )
        write_state(
            self.config.state_file,
            {
                "workflow": "demo",
                "mode": "aws",
                "bundle_version": self.config.bundle_version,
                "aws_directory": str(aws_directory),
                "terraform_directory": str(terraform_directory),
            },
        )
        print("AWS OpenTelemetry demo deployment succeeded.")
