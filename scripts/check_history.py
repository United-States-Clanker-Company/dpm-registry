#!/usr/bin/env python3
"""Reject rewrites of published dpm registry versions."""

import pathlib
import subprocess
import sys
import tomllib


def git(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], stderr=subprocess.DEVNULL)


def version_paths(revision: str) -> set[str]:
    output = git("ls-tree", "-r", "--name-only", revision).decode()
    return {
        path
        for path in output.splitlines()
        if path.startswith("packages/") and "/versions/" in path and path.endswith("/dpm.toml")
    }


def without_yank(document: dict) -> dict:
    result = document.copy()
    result.pop("yanked", None)
    result.pop("yank_reason", None)
    return result


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <base-revision>", file=sys.stderr)
        return 2
    base = sys.argv[1]
    failures: list[str] = []
    for path in sorted(version_paths(base)):
        current_path = pathlib.Path(path)
        if not current_path.is_file():
            failures.append(f"published version deleted: {path}")
            continue
        old_bytes = git("show", f"{base}:{path}")
        new_bytes = current_path.read_bytes()
        if old_bytes == new_bytes:
            continue
        old = tomllib.loads(old_bytes.decode())
        new = tomllib.loads(new_bytes.decode())
        allowed_yank = (
            without_yank(old) == without_yank(new)
            and not old.get("yanked", False)
            and new.get("yanked") is True
            and bool(str(new.get("yank_reason", "")).strip())
        )
        if not allowed_yank:
            failures.append(f"published version rewritten: {path}; publish a new version or yank with a reason")
    if failures:
        print("\n".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
