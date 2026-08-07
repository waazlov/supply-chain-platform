"""Shared configuration, path, logging, and serialization helpers."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


def load_config(config_path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML configuration and return a mutable dictionary."""
    path = Path(config_path or DEFAULT_CONFIG_PATH)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    if not isinstance(config, dict):
        raise TypeError(f"Configuration file must contain a mapping: {path}")
    return config


def project_path(*parts: str | Path) -> Path:
    """Return an absolute path inside the project root."""
    return PROJECT_ROOT.joinpath(*map(Path, parts))


def configured_path(config: dict[str, Any], key: str) -> Path:
    """Return a configured project path."""
    return project_path(config["paths"][key])


def ensure_directories(config: dict[str, Any]) -> None:
    """Create configured output directories."""
    for key in ["raw_data", "processed_data", "output_data", "models", "reports", "logs"]:
        configured_path(config, key).mkdir(parents=True, exist_ok=True)
    configured_path(config, "database").parent.mkdir(parents=True, exist_ok=True)


def setup_logging(config: dict[str, Any], stage: str = "pipeline") -> Path:
    """Configure timestamped file logging and console logging."""
    log_dir = configured_path(config, "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{stage}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[logging.FileHandler(log_file, encoding="utf-8"), logging.StreamHandler()],
        force=True,
    )
    return log_file


def write_json(data: dict[str, Any] | list[dict[str, Any]], path: str | Path) -> None:
    """Write JSON using stable formatting."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, default=str)


def read_json(path: str | Path) -> Any:
    """Read JSON from disk."""
    with Path(path).open("r", encoding="utf-8") as file:
        return json.load(file)


def write_html_table(df, path: str | Path, title: str) -> None:
    """Save a simple standalone HTML table report."""
    html = (
        "<html><head><meta charset='utf-8'>"
        f"<title>{title}</title>"
        "<style>body{font-family:Arial,sans-serif;margin:32px;}"
        "table{border-collapse:collapse;width:100%;font-size:13px;}"
        "th,td{border:1px solid #ddd;padding:6px;text-align:left;}"
        "th{background:#f4f6f8;}</style></head><body>"
        f"<h1>{title}</h1>{df.to_html(index=False)}</body></html>"
    )
    Path(path).write_text(html, encoding="utf-8")
