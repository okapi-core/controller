"""Kubernetes Helm installation workflow."""

from pathlib import Path

from ..assets import BundleAssetResolver
from ..config import KubernetesInstallConfig
from ..errors import OkapiCtlError
from ..runner import CommandRunner
from ..state import write_state


class KubernetesInstaller:
    """Install Okapi charts into the current kubectl context."""

    def __init__(
        self,
        config: KubernetesInstallConfig,
        runner: CommandRunner,
        asset_resolver: BundleAssetResolver,
    ):
        self.config = config
        self.runner = runner
        self.asset_resolver = asset_resolver

    def run(self) -> None:
        self.runner.require("helm")

        bundle = self.asset_resolver.resolve(self.config.bundle_version)
        work_directory = (
            self.config.state_directory / "bundles" / self.config.bundle_version
        )
        bundle.materialize(work_directory)

        if self.config.values_directory is None:
            raise OkapiCtlError(
                "Kubernetes installation requires --values-dir containing filled-in "
                "ops-values.yaml, ingester-values.yaml, oscar-values.yaml, and web-values.yaml. "
                f"Templates were materialized at {work_directory / 'k8s-values'}."
            )

        values_directory = self.config.values_directory.expanduser().resolve()
        required_values = [
            "ops-values.yaml",
            "ingester-values.yaml",
            "oscar-values.yaml",
            "web-values.yaml",
        ]
        missing = [name for name in required_values if not (values_directory / name).is_file()]
        if missing:
            raise OkapiCtlError(
                f"Kubernetes values directory is missing: {', '.join(missing)}"
            )

        chart_base = "oci://ghcr.io/okapi-core/charts"
        for release, values_name in (
            ("ops", "ops-values.yaml"),
            ("ingester", "ingester-values.yaml"),
            ("oscar", "oscar-values.yaml"),
            ("web", "web-values.yaml"),
        ):
            self.runner.run(
                [
                    "helm",
                    "upgrade",
                    "--install",
                    release,
                    f"{chart_base}/{release}",
                    "--version",
                    self.config.bundle_version,
                    "--namespace",
                    self.config.namespace,
                    "--create-namespace",
                    "--values",
                    str(values_directory / values_name),
                    "--wait",
                    "--timeout",
                    f"{self.config.timeout_seconds}s",
                ],
            )

        write_state(
            self.config.state_file,
            {
                "workflow": "install",
                "mode": "k8s",
                "bundle_version": self.config.bundle_version,
                "namespace": self.config.namespace,
                "values_directory": str(values_directory),
                "state_file": str(self.config.state_file),
            },
        )
        print(f"Okapi is ready in Kubernetes namespace: {self.config.namespace}")
