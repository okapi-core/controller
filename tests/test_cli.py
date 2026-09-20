from okapictl.cli import build_parser
from okapictl.constants import OKAPI_VERSION


def test_version_and_modes_are_declared():
    args = build_parser().parse_args(["install", "--local"])
    assert args.local is True
    assert args.k8s is False
    assert OKAPI_VERSION == "0.0.5"


def test_demo_modes_are_declared():
    args = build_parser().parse_args(["demo", "--aws"])
    assert args.aws is True
    assert args.local is False
