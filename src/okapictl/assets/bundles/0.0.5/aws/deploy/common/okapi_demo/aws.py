import functools
import json
import urllib.request

from .system import check_output, run


IMDS_BASE_URL = "http://169.254.169.254/latest"


@functools.cache
def imds_token() -> str:
    request = urllib.request.Request(
        f"{IMDS_BASE_URL}/api/token",
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )
    return urllib.request.urlopen(request, timeout=2).read().decode()


def imds(path: str) -> bytes:
    request = urllib.request.Request(
        f"{IMDS_BASE_URL}/{path.lstrip('/')}",
        headers={"X-aws-ec2-metadata-token": imds_token()},
    )
    return urllib.request.urlopen(request, timeout=2).read()


@functools.cache
def instance_identity() -> dict:
    return json.loads(imds("dynamic/instance-identity/document"))


@functools.cache
def region() -> str:
    return instance_identity()["region"]


def private_ip() -> str:
    return imds("meta-data/local-ipv4").decode().strip()


def get_parameter(name: str, *, decrypt: bool = False, default: str | None = None) -> str:
    cmd = [
        "aws",
        "--region",
        region(),
        "ssm",
        "get-parameter",
        "--name",
        name,
        "--query",
        "Parameter.Value",
        "--output",
        "text",
    ]
    if decrypt:
        cmd.append("--with-decryption")
    try:
        return check_output(cmd)
    except Exception:
        if default is not None:
            return default
        raise


def put_parameter(name: str, value: str, *, secure: bool = False) -> None:
    run([
        "aws",
        "--region",
        region(),
        "ssm",
        "put-parameter",
        "--name",
        name,
        "--type",
        "SecureString" if secure else "String",
        "--value",
        value,
        "--overwrite",
    ])
