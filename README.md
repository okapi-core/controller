# okapi-ctl

`okapi-ctl` is the supported command-line interface for installing Okapi and
running Okapi demos. A controller release is tied to the same Okapi bundle
version: `okapictl==0.0.4` selects the bundled `0.0.4` Compose/Okapi artifacts
by default.

## Development

```sh
poetry install
poetry run okapictl --help
poetry run okapictl install --local
```

The local installer requires Docker with the Compose v2 plugin. It starts the
versioned, package-bundled Compose project and waits for the Okapi health
endpoints before returning.

Kubernetes, AWS, and complete demo workflows are intentionally scaffolded but
not yet implemented.
