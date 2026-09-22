"""Local OpenTelemetry demo workflow."""

from ..assets import BundleAssetResolver
from ..config import LocalDemoConfig
from ..health import HealthChecker, HealthEndpoint
from ..errors import OkapiCtlError
from ..runner import CommandRunner
from ..state import write_state


class LocalDemoRunner:
    """Run the pinned OpenTelemetry demo with the Okapi overlay."""

    def __init__(
        self,
        config: LocalDemoConfig,
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
        self.runner.require("git")
        self.runner.run(["docker", "compose", "version"])

        bundle = self.asset_resolver.resolve(self.config.bundle_version)
        demo_directory = self.config.demo_directory
        demo_directory.parent.mkdir(parents=True, exist_ok=True)

        if not (demo_directory / ".git").is_dir():
            if demo_directory.exists():
                raise OkapiCtlError(
                    f"Demo directory exists but is not a Git checkout: {demo_directory}"
                )
            self.runner.run(["git", "clone", self.config.demo_repository, str(demo_directory)])

        self.runner.run(["git", "-C", str(demo_directory), "fetch", "origin"])
        self.runner.run(
            ["git", "-C", str(demo_directory), "checkout", "--detach", self.config.demo_commit]
        )
        bundle.materialize_otel_assets(demo_directory)
        (demo_directory / ".env.okapi").write_text(
            "OKAPI_IMAGE_REPO=ghcr.io/okapi-core\n"
            "DEMO_VERSION=3.0.0\n"
            f"TAG={self.config.bundle_version}\n",
            encoding="utf-8",
        )

        compose_args = [
            "docker",
            "compose",
            "--project-name",
            self.config.project_name,
            "--env-file",
            ".env",
            "--env-file",
            ".env.override",
            "--env-file",
            ".env.okapi",
            "-f",
            "compose.yaml",
            "-f",
            "compose.extras.yaml",
        ]
        self.runner.run(
            compose_args + ["config"],
            cwd=str(demo_directory),
        )
        self.runner.run(
            compose_args + ["up", "--detach", "--wait", "--remove-orphans"],
            cwd=str(demo_directory),
        )

        self.health_checker.wait_for_all(
            [
                HealthEndpoint("web", "http://127.0.0.1:9001/internal/healthcheck"),
                HealthEndpoint("ingester", "http://127.0.0.1:9009/health"),
                HealthEndpoint("oscar", "http://127.0.0.1:9002/health"),
                HealthEndpoint("OpenTelemetry demo", "http://127.0.0.1:8080"),
            ],
            timeout_seconds=self.config.timeout_seconds,
            failure_hint=(
                f"Inspect with: docker compose --project-name {self.config.project_name} "
                f"-f {demo_directory / 'compose.yaml'} ps"
            ),
        )
        write_state(
            self.config.state_file,
            {
                "workflow": "demo",
                "mode": "local",
                "bundle_version": self.config.bundle_version,
                "project_name": self.config.project_name,
                "demo_directory": str(demo_directory),
                "demo_commit": self.config.demo_commit,
            },
        )
        print("OpenTelemetry demo is ready: http://localhost:8080")
        print("Okapi is ready: http://localhost:9001")
