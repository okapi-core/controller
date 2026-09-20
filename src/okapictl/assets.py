"""Discovery and materialization of bundled Okapi assets."""

import json
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

from .errors import OkapiCtlError


@dataclass(frozen=True)
class BundleAssets:
    """Files belonging to one compatible Okapi bundle."""

    version: str
    compose_source: Any
    postgres_init_source: Any
    clickhouse_config_source: Any

    def materialize(self, destination: Path) -> tuple[Path, Path, Path]:
        destination.mkdir(parents=True, exist_ok=True)
        compose_file = destination / "compose.yaml"
        init_file = destination / "postgres-init.sql"
        clickhouse_config_file = destination / "clickhouse-users.xml"
        compose_file.write_bytes(self.compose_source.read_bytes())
        init_file.write_bytes(self.postgres_init_source.read_bytes())
        clickhouse_config_file.write_bytes(self.clickhouse_config_source.read_bytes())
        return compose_file, init_file, clickhouse_config_file


class BundleAssetResolver:
    """Resolve assets from the versioned bundle shipped in the package."""

    def resolve(self, version: str) -> BundleAssets:
        bundle = files("okapictl").joinpath("assets", "bundles", version)
        manifest_path = bundle.joinpath("manifest.json")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            compose_name = manifest["local_install_compose"]
            clickhouse_config_name = manifest["clickhouse_config"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            raise OkapiCtlError(f"Okapi bundle {version} was not found or is invalid.") from exc

        compose_source = bundle.joinpath(compose_name)
        init_source = bundle.joinpath("postgres-init.sql")
        clickhouse_config_source = bundle.joinpath(clickhouse_config_name)
        if (
            not compose_source.is_file()
            or not init_source.is_file()
            or not clickhouse_config_source.is_file()
        ):
            raise OkapiCtlError(f"Okapi bundle {version} is incomplete.")

        return BundleAssets(
            version=version,
            compose_source=compose_source,
            postgres_init_source=init_source,
            clickhouse_config_source=clickhouse_config_source,
        )
