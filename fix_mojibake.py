#!/usr/bin/env python3
"""Repair Cyrillic (and other) mojibake in Claude export files.

Some third-party Claude exporters save conversation files as UTF-8 text that
has already been mis-decoded as Windows-1251 (CP1251). The result is "mojibake"
such as ``Р’С‹Р±РѕСЂ`` instead of ``Выбор`` — the corruption is baked into the
bytes, so simply re-opening the file with a different encoding does not help.

This utility reverses that specific corruption by re-encoding the text back to
CP1251 bytes and decoding them as UTF-8. It writes a new ``*_fixed`` file next
to each input rather than overwriting the original.

Usage:
    python fix_mojibake.py                 # fix every *.json / *.md in the cwd
    python fix_mojibake.py file1.json ...  # fix only the named files
"""

import glob
import os
import sys
from typing import List


def repair_text(text: str) -> str:
    """Reverse a UTF-8-decoded-as-CP1251 round trip.

    Args:
        text: The corrupted (mojibake) text read from the file.

    Returns:
        The recovered text. Characters that cannot be represented in CP1251
        (e.g. emoji that were themselves corrupted) are replaced rather than
        raising, so a best-effort result is always produced.
    """
    return text.encode("cp1251", errors="replace").decode("utf-8", errors="replace")


def fix_file(path: str) -> str:
    """Repair a single file and write the result alongside it.

    Args:
        path: Path to the corrupted file.

    Returns:
        The path of the written ``*_fixed`` file.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()

    base, ext = os.path.splitext(path)
    out_path = f"{base}_fixed{ext}"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(repair_text(data))
    return out_path


def collect_targets(args: List[str]) -> List[str]:
    """Determine which files to repair.

    Args:
        args: Command-line file arguments (may be empty).

    Returns:
        Explicit arguments when provided, otherwise every ``*.json`` and
        ``*.md`` file in the current directory, excluding files this tool has
        already produced.
    """
    if args:
        return args
    candidates = glob.glob("*.json") + glob.glob("*.md")
    return [f for f in candidates if not f.endswith(("_fixed.json", "_fixed.md"))]


def main() -> None:
    """Repair every targeted file, reporting progress per file."""
    targets = collect_targets(sys.argv[1:])
    if not targets:
        print("No .json/.md files found to repair in the current directory.")
        return

    for path in targets:
        try:
            out_path = fix_file(path)
            print(f"OK: {path}  ->  {out_path}")
        except FileNotFoundError:
            print(f"Skipped {path}: file not found")
        except OSError as e:
            print(f"Skipped {path}: {e}")


if __name__ == "__main__":
    main()
