from pathlib import Path


def render_template(src: str | Path, dst: str | Path, values: dict[str, str], *, mode: int = 0o600) -> None:
    text = Path(src).read_text()
    for key, value in values.items():
        text = text.replace("${" + key + "}", value)
    out = Path(dst)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    out.chmod(mode)
