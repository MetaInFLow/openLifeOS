#!/usr/bin/env python3
"""Print the lifecycle/source-mode status for a LifeOS repo."""

from __future__ import annotations

import argparse
from pathlib import Path


def read_flat_yaml(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    stack: list[tuple[int, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#") or ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, value = raw.strip().split(":", 1)
        while stack and stack[-1][0] >= indent:
            stack.pop()
        full_key = ".".join([item[1] for item in stack] + [key.strip()])
        value = value.strip().strip('"').strip("'")
        if value:
            values[full_key] = value
        else:
            stack.append((indent, key.strip()))
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="LifeOS repo path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.repo).expanduser().resolve()
    status_path = root / "LIFEOS_STATUS.yml"
    if not status_path.exists():
        raise SystemExit(f"Missing lifecycle status file: {status_path}")
    values = read_flat_yaml(status_path)
    mode = values.get("lifecycle.mode", "unknown")
    upload_version = values.get("versions.upload_version", "unknown")
    delivery_version = values.get("versions.delivery_version", "unknown")
    current_version = values.get("versions.current_version", "unknown")
    dev_mode = values.get("source_policy.meta_skills.development.install_mode", "submodule-or-working-source")
    delivery_mode = values.get("source_policy.meta_skills.delivery.install_mode", "github-release-archive")
    print(f"repo: {values.get('repo', root.name)}")
    print(f"lifecycle: {mode}")
    print(f"current_version: {current_version}")
    print(f"upload_version: {upload_version}")
    print(f"delivery_version: {delivery_version}")
    if mode == "development":
        print(f"meta_skill_source_mode: {dev_mode}")
        print("uploadable: true")
    elif mode == "delivery":
        print(f"meta_skill_source_mode: {delivery_mode}")
        print("uploadable: false")
    else:
        print("meta_skill_source_mode: unknown")
        print("uploadable: unknown")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
