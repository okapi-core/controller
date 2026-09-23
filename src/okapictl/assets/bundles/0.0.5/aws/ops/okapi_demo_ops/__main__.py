import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TERRAFORM_DIR = ROOT / "terraform"
DEPLOY_DIR = ROOT / "deploy"


def run(cmd: list[str], *, cwd: Path | None = None, capture: bool = False) -> str:
    print(f"+ {' '.join(cmd)}", flush=True)
    if capture:
        return subprocess.check_output(cmd, cwd=cwd, text=True).strip()
    subprocess.run(cmd, cwd=cwd, check=True)
    return ""


def outputs() -> dict:
    raw = run(["terraform", "output", "-json"], cwd=TERRAFORM_DIR, capture=True)
    data = json.loads(raw)
    return {key: item["value"] for key, item in data.items()}


def aws(region: str, *args: str, capture: bool = False) -> str:
    return run(["aws", "--region", region, *args], capture=capture)


def package_bundle(name: str, out_dir: Path) -> Path:
    src = DEPLOY_DIR / name
    if not src.exists():
        raise SystemExit(f"unknown deployment bundle: {name}")

    stage = Path(tempfile.mkdtemp(prefix=f"{name}-bundle-"))
    try:
        shutil.copytree(src, stage, dirs_exist_ok=True)
        shutil.copytree(DEPLOY_DIR / "common", stage / "common", dirs_exist_ok=True)
        zip_path = out_dir / f"{name}.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in stage.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(stage))
        return zip_path
    finally:
        shutil.rmtree(stage)


def upload_bundle(env: dict, name: str) -> tuple[str, str]:
    bucket = env["codedeploy_artifact_bucket"]
    region = env["aws_region"]
    with tempfile.TemporaryDirectory(prefix="okapi-demo-artifacts-") as tmp:
        zip_path = package_bundle(name, Path(tmp))
        key = f"codedeploy/{name}/{int(time.time())}.zip"
        aws(region, "s3", "cp", str(zip_path), f"s3://{bucket}/{key}")
    return bucket, key


def create_deployment(env: dict, target: str) -> str:
    region = env["aws_region"]
    if target == "okapi":
        bundle = "okapi-stack"
        app = env["okapi_codedeploy_app"]
        group = env["okapi_codedeploy_group"]
    elif target == "otel":
        bundle = "otel-demo"
        app = env["otel_codedeploy_app"]
        group = env["otel_codedeploy_group"]
    else:
        raise SystemExit(f"unknown deployment target: {target}")

    bucket, key = upload_bundle(env, bundle)
    return aws(
        region,
        "deploy",
        "create-deployment",
        "--application-name",
        app,
        "--deployment-group-name",
        group,
        "--s3-location",
        f"bucket={bucket},key={key},bundleType=zip",
        "--query",
        "deploymentId",
        "--output",
        "text",
        capture=True,
    )


def wait_deployment(env: dict, deployment_id: str) -> None:
    region = env["aws_region"]
    while True:
        status = aws(
            region,
            "deploy",
            "get-deployment",
            "--deployment-id",
            deployment_id,
            "--query",
            "deploymentInfo.status",
            "--output",
            "text",
            capture=True,
        )
        print(f"deployment {deployment_id}: {status}")
        if status == "Succeeded":
            return
        if status in {"Failed", "Stopped"}:
            raise SystemExit(f"deployment {deployment_id} ended with {status}")
        time.sleep(10)


def instance_id(env: dict, target: str) -> str:
    if target == "okapi":
        return env["okapi_instance_id"]
    if target == "otel":
        return env["otel_instance_id"]
    raise SystemExit(f"unknown instance target: {target}")


def start_instance(env: dict, target: str) -> None:
    region = env["aws_region"]
    iid = instance_id(env, target)
    aws(region, "ec2", "start-instances", "--instance-ids", iid)
    aws(region, "ec2", "wait", "instance-running", "--instance-ids", iid)
    aws(region, "ec2", "wait", "instance-status-ok", "--instance-ids", iid)


def stop_instance(env: dict, target: str) -> None:
    region = env["aws_region"]
    iid = instance_id(env, target)
    aws(region, "ec2", "stop-instances", "--instance-ids", iid)
    aws(region, "ec2", "wait", "instance-stopped", "--instance-ids", iid)


def deploy(env: dict, target: str) -> None:
    deployment_id = create_deployment(env, target)
    wait_deployment(env, deployment_id)


def cmd_package(args: argparse.Namespace) -> None:
    out = ROOT / "dist"
    out.mkdir(exist_ok=True)
    path = package_bundle(args.bundle, out)
    print(path)


def cmd_deploy(args: argparse.Namespace) -> None:
    env = outputs()
    targets = ["okapi", "otel"] if args.target == "all" else [args.target]
    for target in targets:
        deploy(env, target)


def cmd_start(args: argparse.Namespace) -> None:
    env = outputs()
    start_instance(env, "okapi")
    if args.redeploy:
        deploy(env, "okapi")
    start_instance(env, "otel")
    if args.redeploy:
        deploy(env, "otel")
    print(f"Okapi: {env['okapi_url']}")
    print(f"Otel:  {env['otel_url']}")


def cmd_stop(args: argparse.Namespace) -> None:
    env = outputs()
    stop_instance(env, "otel")
    stop_instance(env, "okapi")


def cmd_status(_: argparse.Namespace) -> None:
    env = outputs()
    region = env["aws_region"]
    ids = [env["okapi_instance_id"], env["otel_instance_id"]]
    aws(
        region,
        "ec2",
        "describe-instances",
        "--instance-ids",
        *ids,
        "--query",
        "Reservations[].Instances[].{Id:InstanceId,State:State.Name,PublicIp:PublicIpAddress,PrivateIp:PrivateIpAddress,Name:Tags[?Key=='Name']|[0].Value}",
        "--output",
        "table",
    )
    print(f"Okapi: {env['okapi_url']}")
    print(f"Otel:  {env['otel_url']}")


def cmd_set_openai_key(_: argparse.Namespace) -> None:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise SystemExit("OPENAI_API_KEY is required")
    env = outputs()
    region = env["aws_region"]
    name = f"{env['ssm_prefix']}/secrets/openai_api_key"
    aws(
        region,
        "ssm",
        "put-parameter",
        "--name",
        name,
        "--type",
        "SecureString",
        "--value",
        key,
        "--overwrite",
    )
    print(f"Stored OpenAI key in SSM: {name}")


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="okapi-demo")
    sub = p.add_subparsers(required=True)

    package = sub.add_parser("package")
    package.add_argument("bundle", choices=["okapi-stack", "otel-demo"])
    package.set_defaults(func=cmd_package)

    deploy_p = sub.add_parser("deploy")
    deploy_p.add_argument("target", choices=["okapi", "otel", "all"])
    deploy_p.set_defaults(func=cmd_deploy)

    start = sub.add_parser("start")
    start.add_argument("--redeploy", action="store_true")
    start.set_defaults(func=cmd_start)

    stop = sub.add_parser("stop")
    stop.set_defaults(func=cmd_stop)

    status = sub.add_parser("status")
    status.set_defaults(func=cmd_status)

    set_openai_key = sub.add_parser("set-openai-key")
    set_openai_key.set_defaults(func=cmd_set_openai_key)

    return p


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
