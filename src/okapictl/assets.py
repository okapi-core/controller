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
    k8s_values_sources: dict[str, Any]
    otel_compose_source: Any
    otel_collector_config_source: Any

    def materialize(self, destination: Path) -> tuple[Path, Path, Path]:
        destination.mkdir(parents=True, exist_ok=True)
        compose_file = destination / "compose.yaml"
        init_file = destination / "postgres-init.sql"
        clickhouse_config_file = destination / "clickhouse-users.xml"
        compose_file.write_bytes(self.compose_source.read_bytes())
        init_file.write_bytes(self.postgres_init_source.read_bytes())
        clickhouse_config_file.write_bytes(self.clickhouse_config_source.read_bytes())
        values_directory = destination / "k8s-values"
        values_directory.mkdir(exist_ok=True)
        for name, source in self.k8s_values_sources.items():
            (values_directory / name).write_bytes(source.read_bytes())
        return compose_file, init_file, clickhouse_config_file

    def materialize_otel_assets(self, destination: Path) -> tuple[Path, Path]:
        """Materialize the controller overlays into an OTEL demo checkout."""
        collector_directory = destination / "src" / "otel-collector"
        collector_directory.mkdir(parents=True, exist_ok=True)
        compose_file = destination / "compose.extras.yaml"
        collector_file = collector_directory / "otelcol-config-extras.yml"
        compose_file.write_bytes(self.otel_compose_source.read_bytes())
        collector_file.write_bytes(self.otel_collector_config_source.read_bytes())
        (destination / "clickhouse-users.xml").write_bytes(
            self.clickhouse_config_source.read_bytes()
        )
        (destination / "postgres-init.sql").write_bytes(
            self.postgres_init_source.read_bytes()
        )
        return compose_file, collector_file


class BundleAssetResolver:
    """Resolve assets from the versioned bundle shipped in the package."""

    def resolve(self, version: str) -> BundleAssets:
        bundle = files("okapictl").joinpath("assets", "bundles", version)
        manifest_path = bundle.joinpath("manifest.json")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            compose_name = manifest["local_install_compose"]
            clickhouse_config_name = manifest["clickhouse_config"]
            k8s_values_names = manifest["k8s_values"]
            otel_compose_name = manifest["otel_compose"]
            otel_collector_config_name = manifest["otel_collector_config"]
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
            raise OkapiCtlError(f"Okapi bundle {version} was not found or is invalid.") from exc

        compose_source = bundle.joinpath(compose_name)
        init_source = bundle.joinpath("postgres-init.sql")
        clickhouse_config_source = bundle.joinpath(clickhouse_config_name)
        k8s_values_sources = {
            name: bundle.joinpath(filename)
            for name, filename in k8s_values_names.items()
        }
        otel_compose_source = bundle.joinpath(otel_compose_name)
        otel_collector_config_source = bundle.joinpath(otel_collector_config_name)
        if (
            not compose_source.is_file()
            or not init_source.is_file()
            or not clickhouse_config_source.is_file()
            or not all(source.is_file() for source in k8s_values_sources.values())
            or not otel_compose_source.is_file()
            or not otel_collector_config_source.is_file()
        ):
            raise OkapiCtlError(f"Okapi bundle {version} is incomplete.")

        return BundleAssets(
            version=version,
            compose_source=compose_source,
            postgres_init_source=init_source,
            clickhouse_config_source=clickhouse_config_source,
            k8s_values_sources=k8s_values_sources,
            otel_compose_source=otel_compose_source,
            otel_collector_config_source=otel_collector_config_source,
        )
