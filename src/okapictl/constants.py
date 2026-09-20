"""Controller and Okapi bundle constants."""

from pathlib import Path


_VERSION_FILE = Path(__file__).resolve().parents[2] / "OKAPI_VERSION"
OKAPI_VERSION = _VERSION_FILE.read_text(encoding="utf-8").strip()

