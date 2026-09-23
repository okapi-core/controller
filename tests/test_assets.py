from okapictl.assets import BundleAssetResolver


def test_resolver_discovers_versioned_local_bundle():
    assets = BundleAssetResolver().resolve("0.0.5")

    assert assets.version == "0.0.5"
    assert assets.compose_source.is_file()
    assert assets.postgres_init_source.is_file()
    assert assets.clickhouse_config_source.is_file()
    assert assets.otel_compose_source.is_file()
    assert assets.otel_collector_config_source.is_file()
    assert assets.aws_source.is_dir()
