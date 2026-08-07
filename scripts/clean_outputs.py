"""Remove generated project outputs while leaving directory structure intact."""

from __future__ import annotations

from pathlib import Path


PATTERNS = [
    "data/raw/*.csv",
    "data/processed/*.csv",
    "data/output/*.csv",
    "database/*.duckdb",
    "models/*.joblib",
    "models/*.json",
    "reports/*.html",
    "reports/*.csv",
    "reports/*.md",
    "reports/*.json",
    "logs/*.log",
]


def main() -> None:
    for pattern in PATTERNS:
        for path in Path(".").glob(pattern):
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()

