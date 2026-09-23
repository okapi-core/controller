#!/usr/bin/env python3.14
import os
import sys
from pathlib import Path

from common.okapi_demo import aws
from common.okapi_demo.compose import down, pull, up
from common.okapi_demo.health import http_ok
from common.okapi_demo.render import render_template
from common.okapi_demo.system import ensure_dir, run, wait_until


APP_DIR = Path("/opt/okapi-demo/okapi-stack")
DATA_DIR = Path("/mnt/okapi-data")
DEVICE_CANDIDATES = ["/dev/nvme1n1", "/dev/xvdf", "/dev/sdf"]
PROJECT = os.getenv("OKAPI_DEMO_PROJECT", "okapi-demo")
SSM_PREFIX = f"/{PROJECT}"


def event_name() -> str:
    if len(sys.argv) > 1:
        return sys.argv[1]
    return os.getenv("LIFECYCLE_EVENT", "ApplicationStart")


# todo: why is this necessary -> is it possible to mount a EC2 volume in a specific spot.
def mount_data() -> None:
    ensure_dir(DATA_DIR)
    # todo: why do we need multiple DEVICE_CANDIDATES here
    def device() -> str | None:
        for candidate in DEVICE_CANDIDATES:
            if Path(candidate).exists():
                return candidate
        return None

    if device() is None:
        # Nitro may expose /dev/sdf as an nvme device after a short delay.
        wait_until("Okapi data volume", lambda: device() is not None, timeout_seconds=120)
    dev = device()
    if dev is None:
        raise RuntimeError("Okapi data volume device was not found")
    mounts = Path("/proc/mounts").read_text()
    if f" {DATA_DIR} " not in mounts:
        try:
            run(["blkid", dev])
        except Exception:
            run(["mkfs", "-t", "xfs", dev])
        run(["mount", dev, str(DATA_DIR)])
    for name in ["clickhouse/data", "clickhouse/logs", "postgres", "vault", "wal/metrics", "wal/logs", "wal/traces", "caddy/data", "caddy/config"]:
        ensure_dir(DATA_DIR / name)


def config_values() -> dict[str, str]:
    okapi_host = aws.get_parameter(f"{SSM_PREFIX}/config/okapi_hostname")
    image_repo = aws.get_parameter(f"{SSM_PREFIX}/config/okapi_image_repo")
    image_tag = aws.get_parameter(f"{SSM_PREFIX}/config/okapi_image_tag")
    openai = aws.get_parameter(f"{SSM_PREFIX}/secrets/openai_api_key", decrypt=True, default="")
    values = {
        "OKAPI_HOSTNAME": okapi_host,
        "OKAPI_IMAGE_REPO": image_repo,
        "OKAPI_IMAGE_TAG": image_tag,
        "POSTGRES_PASSWORD": aws.get_parameter(f"{SSM_PREFIX}/secrets/postgres_password", decrypt=True),
        "OKAPI_WEB_DB_PASSWORD": aws.get_parameter(f"{SSM_PREFIX}/secrets/okapi_web_db_password", decrypt=True),
        "OKAPI_WEB_DB_MIGRATION_PASSWORD": aws.get_parameter(f"{SSM_PREFIX}/secrets/okapi_web_migration_db_password", decrypt=True),
        "OSCAR_DB_PASSWORD": aws.get_parameter(f"{SSM_PREFIX}/secrets/oscar_db_password", decrypt=True),
        "CLICKHOUSE_PASSWORD": aws.get_parameter(f"{SSM_PREFIX}/secrets/clickhouse_password", decrypt=True),
        "VAULT_ROOT_TOKEN": aws.get_parameter(f"{SSM_PREFIX}/secrets/vault_root_token", decrypt=True),
        "OPENAI_API_KEY": openai,
    }
    values["OKAPI_PUBLIC_URL"] = f"https://{okapi_host}"
    values["OKAPI_INGESTER_URL"] = f"http://{aws.private_ip()}:9009"
    return values


def render() -> dict[str, str]:
    values = config_values()
    render_template(APP_DIR / "templates/okapi.env.tpl", APP_DIR / ".env", values)
    return values


def prepare() -> None:
    mount_data()
    ensure_dir(APP_DIR)


def install() -> None:
    prepare()
    render()
    pull(APP_DIR)


def start() -> None:
    values = render()
    up(APP_DIR)
    aws.put_parameter(f"{SSM_PREFIX}/runtime/okapi/public_url", values["OKAPI_PUBLIC_URL"])
    aws.put_parameter(f"{SSM_PREFIX}/runtime/okapi/ingester_url", values["OKAPI_INGESTER_URL"])
    aws.put_parameter(f"{SSM_PREFIX}/runtime/okapi/private_ip", aws.private_ip())


def stop() -> None:
    if APP_DIR.exists():
        down(APP_DIR)


def validate() -> None:
    wait_until("Okapi web", lambda: http_ok("http://127.0.0.1:9001"), timeout_seconds=300)
    wait_until("Okapi ingester", lambda: http_ok("http://127.0.0.1:9009"), timeout_seconds=300)


def status() -> None:
    run(["docker", "compose", "ps"], cwd=APP_DIR)


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
        "down": stop,
        "validate": validate,
        "status": status,
    }
    handler = handlers.get(event)
    if not handler:
        raise SystemExit(f"unknown deploy event: {event}")
    handler()


if __name__ == "__main__":
    main()
