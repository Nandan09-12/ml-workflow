from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MIGRATIONS_DIR = Path("apps/api/alembic/versions")
IGNORED_FILE_NAMES = {".gitkeep"}


def _run_git(*args: str, repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _repo_root() -> Path:
    return Path(_run_git("rev-parse", "--show-toplevel", repo_root=Path.cwd()))


def _resolve_base(repo_root: Path) -> str:
    base_sha = os.environ.get("MIGRATION_GUARD_BASE_SHA", "").strip()
    if base_sha and set(base_sha) != {"0"}:
        return base_sha

    default_branch = os.environ.get("MIGRATION_GUARD_DEFAULT_BRANCH", "").strip()
    if default_branch:
        return _run_git("merge-base", "HEAD", f"origin/{default_branch}", repo_root=repo_root)

    return "HEAD"


def _is_relevant(path_value: str) -> bool:
    path = Path(path_value)
    if "__pycache__" in path.parts:
        return False
    if path.name in IGNORED_FILE_NAMES:
        return False
    return path.suffix == ".py"


def main() -> int:
    repo_root = _repo_root()
    base_ref = _resolve_base(repo_root)
    diff_output = _run_git(
        "diff",
        "--name-status",
        "--find-renames",
        f"{base_ref}..HEAD",
        "--",
        str(MIGRATIONS_DIR),
        repo_root=repo_root,
    )

    if not diff_output:
        print("Alembic guard: no migration file changes detected.")
        return 0

    disallowed: list[str] = []
    allowed_new_files: list[str] = []

    for line in diff_output.splitlines():
        parts = line.split("\t")
        status = parts[0]

        if status.startswith("R"):
            old_path, new_path = parts[1], parts[2]
            if _is_relevant(old_path) or _is_relevant(new_path):
                disallowed.append(f"{status}: {old_path} -> {new_path}")
            continue

        path = parts[1]
        if not _is_relevant(path):
            continue

        if status == "A":
            allowed_new_files.append(path)
            continue

        disallowed.append(f"{status}: {path}")

    for path in allowed_new_files:
        print(f"Alembic guard: allowing new migration file {path}")

    if disallowed:
        print("Alembic guard: immutable migration files were changed.", file=sys.stderr)
        for item in disallowed:
            print(f" - {item}", file=sys.stderr)
        print(
            "Existing Alembic revisions are immutable once applied. "
            "Create a new revision instead of editing an existing one.",
            file=sys.stderr,
        )
        return 1

    print("Alembic guard: only new migration files were added.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
