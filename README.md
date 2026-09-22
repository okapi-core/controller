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

## Local OpenTelemetry demo

The local demo starts the pinned OpenTelemetry Astronomy Shop together with
the matching Okapi bundle and an OpenTelemetry Collector configured to export
traces, metrics, and logs to Okapi. Docker and Git are required. The demo
checkout is stored under the controller state directory and is checked out at
the revision pinned by the controller release.

```sh
okapictl demo --local
```

The command starts the demo's core/minimal Compose configuration without its
separate observability backends or Kafka-based services, then waits for the
Okapi services and demo frontend. It prints:

```text
OpenTelemetry demo is ready: http://localhost:8080
Okapi is ready: http://localhost:9001
```

Set `OPENAI_API_KEY` before running if the demo should use a real OpenAI
integration. The local workflow supplies a non-production placeholder when no
key is configured. For example:

```sh
export OPENAI_API_KEY=sk-proj-<your-key>
okapictl demo --local
```

The key is passed to Okapi Oscar through the Compose environment and is not
stored in the controller bundle. Do not commit it to `.env` or `.env.okapi`.

Kubernetes, AWS, and complete demo workflows are intentionally scaffolded but
not yet implemented.

## Kubernetes installation

The Kubernetes installer assumes that PostgreSQL and ClickHouse are already
deployed and reachable from the target cluster. Okapi does not install or
manage either database. It installs only the four version-pinned Okapi Helm
charts (`ops`, `ingester`, `oscar`, and `web`) into the current `kubectl`
context.

### Prerequisites

Select the target Kubernetes context and create the namespace:

```sh
kubectl config use-context <context-name>
kubectl create namespace okapi --dry-run=client -o yaml | kubectl apply -f -
```

PostgreSQL and ClickHouse must already be available through Kubernetes service
names. The deployment also requires the external database credentials and the
Oscar OpenAI API key to be available as Kubernetes Secrets.

Create the reserved Secrets as follows, replacing the example values. Using
an External Secrets controller is recommended for production deployments.

```sh
kubectl -n okapi create secret generic okapi-clickhouse \
  --from-literal=username=default \
  --from-literal=password="$CLICKHOUSE_PASSWORD"

kubectl -n okapi create secret generic okapi-postgres \
  --from-literal=migration-username=okapi_web_migration_user \
  --from-literal=migration-password="$POSTGRES_MIGRATION_PASSWORD" \
  --from-literal=web-username=okapi_web_user \
  --from-literal=web-password="$POSTGRES_WEB_PASSWORD" \
  --from-literal=oscar-username=okapi_oscar_user \
  --from-literal=oscar-password="$POSTGRES_OSCAR_PASSWORD"

kubectl -n okapi create secret generic okapi-openai \
  --from-literal=api-key="$OPENAI_API_KEY"
```

Do not commit real credentials to values files or shell scripts.

First copy the bundled values templates from the materialized bundle directory,
fill in the external database service names and Secret references, and create
the referenced Secret in the target namespace. Then run:

```sh
okapictl install --k8s --namespace okapi --values-dir ./okapi-values
```

The values directory must contain `ops-values.yaml`, `ingester-values.yaml`,
`oscar-values.yaml`, and `web-values.yaml`. The installer does not create or
manage PostgreSQL, ClickHouse, or the database credentials Secret.

The current controller prototype requires the values directory explicitly:

```sh
okapictl install --k8s \
  --namespace okapi \
  --values-dir ./okapi-values
```

Each values file supplies the external service endpoints and references the
reserved Secrets. The controller installs the charts in dependency order:

```text
ops → ingester → oscar → web
```

The planned higher-level interface will generate these chart overrides from a
single controller configuration file, so users will not need to manage Helm
values directly.

### Kubernetes Secret contract

The Kubernetes installation reserves three namespaced Secrets. Create or
populate these Secrets before installing Okapi, either directly or through an
External Secrets controller:

| Secret | Required keys |
| --- | --- |
| `okapi-clickhouse` | `username`, `password` |
| `okapi-postgres` | `migration-username`, `migration-password`, `web-username`, `web-password`, `oscar-username`, `oscar-password` |
| `okapi-openai` | `api-key` |

The controller and Helm values use these names and keys as a stable contract.
Secret values are not stored in the Helm values files or printed by the
controller.

To verify that all required Secrets and keys are present without displaying
their values:

```sh
kubectl -n okapi get secret okapi-clickhouse okapi-postgres okapi-openai

for item in \
  okapi-clickhouse:username \
  okapi-clickhouse:password \
  okapi-postgres:migration-username \
  okapi-postgres:migration-password \
  okapi-postgres:web-username \
  okapi-postgres:web-password \
  okapi-postgres:oscar-username \
  okapi-postgres:oscar-password \
  okapi-openai:api-key; do
  secret="${item%%:*}"
  key="${item#*:}"
  kubectl -n okapi get secret "$secret" \
    -o go-template="{{if not (index .data \"$key\")}}missing $secret/$key{{end}}"
done
```
