"""Command-line entry point for okapictl."""

import argparse
import sys

from .assets import BundleAssetResolver
from .config import LocalInstallConfig
from .errors import OkapiCtlError, UnsupportedWorkflowError
from .health import HealthChecker
from .runner import CommandRunner
from .workflows.local_install import LocalInstaller


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="okapictl")
    commands = parser.add_subparsers(dest="command", required=True)

    install = commands.add_parser("install", help="Install Okapi.")
    install_modes = install.add_mutually_exclusive_group(required=True)
    install_modes.add_argument("--local", action="store_true")
    install_modes.add_argument("--k8s", action="store_true")
    install.add_argument("--project-name", default="okapi")
    install.add_argument("--timeout", type=int, default=180)

    demo = commands.add_parser("demo", help="Run an Okapi demo.")
    demo_modes = demo.add_mutually_exclusive_group(required=True)
    demo_modes.add_argument("--local", action="store_true")
    demo_modes.add_argument("--aws", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "install" and args.local:
            LocalInstaller(
                LocalInstallConfig(
                    project_name=args.project_name,
                    timeout_seconds=args.timeout,
                ),
                runner=CommandRunner(),
                health_checker=HealthChecker(),
                asset_resolver=BundleAssetResolver(),
            ).run()
            return 0
        if args.command == "install" and args.k8s:
            raise UnsupportedWorkflowError("Kubernetes installation is not implemented yet.")
        if args.command == "demo":
            raise UnsupportedWorkflowError("Demo workflows are not implemented yet.")
        raise OkapiCtlError("No workflow selected.")
    except OkapiCtlError as exc:
        print(f"okapictl: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
