#!/usr/bin/env python3.14
import os
import sys
from pathlib import Path

from common.okapi_demo import aws
from common.okapi_demo.health import http_ok
from common.okapi_demo.render import render_template
from common.okapi_demo.system import ensure_dir, run, wait_until


APP_DIR = Path("/opt/okapi-demo/otel-demo")
REPO_DIR = Path("/opt/okapi-demo/opentelemetry-demo")
PROJECT = os.getenv("OKAPI_DEMO_PROJECT", "okapi-demo")
SSM_PREFIX = f"/{PROJECT}"
OTEL_REPO = os.getenv("OTEL_DEMO_REPO", "https://github.com/open-telemetry/opentelemetry-demo.git")
OTEL_COMMIT = os.getenv("OTEL_DEMO_COMMIT", "1755859a9de82c2e5e225be68abc401a5ebf2b4f")

def event_name() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.getenv("LIFECYCLE_EVENT", "ApplicationStart")


def compose_cmd(*args: str) -> list[str]:
    return [
        "docker",
        "compose",
        "-f",
        "compose.yaml",
        "-f",
        "compose.full.yaml",
        "-f",
        "compose.okapi.yaml",
        *args,
    ]


def clone_or_update() -> None:
    ensure_dir(REPO_DIR.parent)
    if not (REPO_DIR / ".git").exists():
        run(["git", "clone", OTEL_REPO, str(REPO_DIR)])
    run(["git", "fetch", "--depth", "1", "origin", OTEL_COMMIT], cwd=REPO_DIR)
    run(["git", "checkout", "--detach", OTEL_COMMIT], cwd=REPO_DIR)


def values() -> dict[str, str]:
    otel_host = aws.get_parameter(f"{SSM_PREFIX}/config/otel_hostname")
    return {
        "OTEL_HOSTNAME": otel_host,
        "OKAPI_INGESTER_URL": aws.get_parameter(f"{SSM_PREFIX}/runtime/okapi/ingester_url"),
        "OTEL_PUBLIC_URL": f"https://{otel_host}",
    }


def render() -> None:
    vals = values()
    render_template(APP_DIR / "templates/otel.env.override.tpl", REPO_DIR / ".env.override", vals)
    render_template(APP_DIR / "templates/otelcol-config-extras.yml.tpl", REPO_DIR / "src/otel-collector/otelcol-config-extras.yml", vals)
    render_template(APP_DIR / "templates/compose.okapi.yaml.tpl", REPO_DIR / "compose.okapi.yaml", vals, mode=0o644)
    render_template(APP_DIR / "templates/Caddyfile.tpl", REPO_DIR / "Caddyfile", vals, mode=0o644)


def prepare() -> None:
    ensure_dir(APP_DIR)
    ensure_dir("/opt/okapi-demo/caddy-otel/data")
    ensure_dir("/opt/okapi-demo/caddy-otel/config")

def install() -> None:
    prepare()
    clone_or_update()
    render()
    run(compose_cmd("pull"), cwd=REPO_DIR)


def start() -> None:
    clone_or_update()
    wait_until(
        "Okapi ingester",
        lambda: http_ok(values()["OKAPI_INGESTER_URL"]),
        timeout_seconds=300,
    )
    render()
    run(compose_cmd("up", "-d"), cwd=REPO_DIR)


def stop() -> None:
    if (REPO_DIR / "compose.yaml").exists() and (REPO_DIR / "compose.okapi.yaml").exists():
        run(compose_cmd("down", "--remove-orphans"), cwd=REPO_DIR)


def validate() -> None:
    wait_until("Otel demo frontend", lambda: http_ok("http://127.0.0.1:8080"), timeout_seconds=420)
    wait_until("Otel demo public proxy", lambda: http_ok("http://127.0.0.1"), timeout_seconds=120)


def status() -> None:
    run(compose_cmd("ps"), cwd=REPO_DIR)


def main() -> None:
    event = event_name()
    handlers = {
        "ApplicationStop": stop,
        "BeforeInstall": prepare,
        "AfterInstall": install,
        "ApplicationStart": start,
        "ValidateService": validate,
        "prepare": prepare,
        "install": install,
        "start": start,
        "stop": stop,
        "validate": validate,
        "status": status,
    }
    handler = handlers.get(event)
    if not handler:
        raise SystemExit(f"unknown deploy event: {event}")
    handler()


if __name__ == "__main__":
    main()
