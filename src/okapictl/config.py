"""Version and local workflow configuration."""

from dataclasses import dataclass
from pathlib import Path

from .constants import OKAPI_VERSION


@dataclass(frozen=True)
class LocalInstallConfig:
    """Configuration for a local Okapi Compose installation."""

    bundle_version: str = OKAPI_VERSION
    project_name: str = "okapi"
    state_directory: Path = Path.home() / ".local" / "state" / "okapictl"
    timeout_seconds: int = 180

    @property
    def state_file(self) -> Path:
        return self.state_directory / "local-install.json"


@dataclass(frozen=True)
class KubernetesInstallConfig:
    """Configuration for installing Okapi into an existing Kubernetes cluster."""

    bundle_version: str = OKAPI_VERSION
    namespace: str = "okapi"
    values_directory: Path | None = None
    state_directory: Path = Path.home() / ".local" / "state" / "okapictl"
    timeout_seconds: int = 900

    @property
    def state_file(self) -> Path:
        return self.state_directory / "k8s-install.json"
