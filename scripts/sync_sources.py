#!/usr/bin/env python3
"""Synchronize source registry storage formats."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import source_store


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-yaml",
        action="store_true",
        help="Initialize or refresh sources/source-registry.sqlite from sources/source-registry.yaml",
    )
    parser.add_argument("--db", type=Path, default=source_store.DEFAULT_DB_FILE)
    parser.add_argument("--yaml", type=Path, default=source_store.DEFAULT_YAML_FILE)
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if not args.from_yaml:
        print("ERROR: choose --from-yaml", file=sys.stderr)
        return 2
    try:
        source_store.initialize_sqlite_from_yaml(db_path=args.db, yaml_path=args.yaml)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Wrote {args.db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

