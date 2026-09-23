"""AWS OpenTelemetry demo workflow."""

from ..assets import BundleAssetResolver
from ..aws.artifacts import CodeDeployArtifacts
from ..aws.cli import AwsCli
from ..aws.codedeploy import AwsDemoOrchestrator
from ..aws.terraform import Terraform
from ..config import AwsDemoConfig
from ..runner import CommandRunner
from ..state import write_state


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
        terraform = Terraform(terraform_directory, self.runner)
        terraform.init()
        terraform.apply(
            variables_file=self.config.terraform_vars_file,
            okapi_version=self.config.bundle_version,
            auto_approve=self.config.auto_approve,
        )
        outputs = terraform.outputs()
        aws_cli = AwsCli(self.runner, outputs["aws_region"])
        artifacts = CodeDeployArtifacts(aws_directory, aws_cli)
        AwsDemoOrchestrator(aws_cli, outputs, artifacts).converge()
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
