"""Local Docker Compose installation workflow."""

from ..config import LocalInstallConfig
from ..assets import BundleAssetResolver
from ..health import HealthChecker, HealthEndpoint
from ..runner import CommandRunner
from ..state import write_state


class LocalInstaller:
    def __init__(
        self,
        config: LocalInstallConfig,
        runner: CommandRunner,
        health_checker: HealthChecker,
        asset_resolver: BundleAssetResolver,
    ):
        self.config = config
        self.runner = runner
        self.health_checker = health_checker
        self.asset_resolver = asset_resolver

    def run(self) -> None:
        self.runner.require("docker")
        self.runner.run(["docker", "compose", "version"])

        work_directory = (
            self.config.state_directory / "bundles" / self.config.bundle_version
        )
        bundle = self.asset_resolver.resolve(self.config.bundle_version)
        compose_file, _, _ = bundle.materialize(work_directory)

        self.runner.run(
            [
                "docker",
                "compose",
                "-p",
                self.config.project_name,
                "-f",
                str(compose_file),
                "config",
            ],
            cwd=str(work_directory),
        )
        self.runner.run(
            [
                "docker",
                "compose",
                "-p",
                self.config.project_name,
                "-f",
                str(compose_file),
                "up",
                "-d",
                "--wait",
            ],
            cwd=str(work_directory),
        )

        self.health_checker.wait_for_all(
            [
                HealthEndpoint("web", "http://127.0.0.1:9001/internal/healthcheck"),
                HealthEndpoint("ingester", "http://127.0.0.1:9009/health"),
                HealthEndpoint("oscar", "http://127.0.0.1:9002/health"),
            ],
            timeout_seconds=self.config.timeout_seconds,
            failure_hint=(
                f"Inspect with: docker compose -p {self.config.project_name} ps"
            ),
        )
        write_state(
            self.config.state_file,
            {
                "workflow": "install",
                "mode": "local",
                "bundle_version": self.config.bundle_version,
                "project_name": self.config.project_name,
                "compose_file": str(compose_file),
                "state_file": str(self.config.state_file),
            },
        )
        print("Okapi is ready: http://localhost:9001")
        print("Ingester endpoint: http://localhost:9009")
