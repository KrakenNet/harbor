# SPDX-License-Identifier: Apache-2.0
"""Verify every .py under src/ starts with the SPDX-License-Identifier header.

Per FR-38, every Python source file in ``src/`` must begin with
``# SPDX-License-Identifier: Apache-2.0``. This script enforces that rule.

Usage:
    python scripts/check_spdx.py          # check only; exit 1 on any miss
    python scripts/check_spdx.py --fix    # prepend header to any missing files
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SPDX_LINE = "# SPDX-License-Identifier: Apache-2.0"
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"


def missing_header(path: Path) -> bool:
    with path.open("r", encoding="utf-8") as f:
        first = f.readline().rstrip("\n").rstrip("\r")
    return first != SPDX_LINE


def prepend_header(path: Path) -> None:
    original = path.read_text(encoding="utf-8")
    path.write_text(f"{SPDX_LINE}\n{original}", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Prepend the SPDX header to files that lack it.",
    )
    args = parser.parse_args()

    if not SRC_DIR.is_dir():
        sys.stderr.write(f"ERROR: {SRC_DIR} does not exist.\n")
        return 1

    py_files = sorted(SRC_DIR.rglob("*.py"))
    missing = [p for p in py_files if missing_header(p)]

    if not missing:
        return 0

    if args.fix:
        for path in missing:
            prepend_header(path)
            sys.stdout.write(f"fixed: {path.relative_to(REPO_ROOT)}\n")
        return 0

    sys.stderr.write(
        f"ERROR: {len(missing)} file(s) missing '{SPDX_LINE}' (FR-38):\n"
    )
    for path in missing:
        sys.stderr.write(f"  - {path.relative_to(REPO_ROOT)}\n")
    sys.stderr.write("Run with --fix to prepend the header automatically.\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
