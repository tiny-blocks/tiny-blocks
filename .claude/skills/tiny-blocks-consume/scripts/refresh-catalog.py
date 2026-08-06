#!/usr/bin/env python3
"""Rebuild references/catalog.md from the tiny-blocks vendor on Packagist.

Usage:
    python3 scripts/refresh-catalog.py

Depends only on the Python standard library. No curl, no jq, no shell.
"""

from __future__ import annotations

import json
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

VENDOR = "tiny-blocks"
LIST_URL = f"https://packagist.org/packages/list.json?vendor={VENDOR}"
CATALOG_PATH = Path(__file__).resolve().parent.parent / "references" / "catalog.md"
LINE_WIDTH = 120
REQUEST_TIMEOUT_SECONDS = 30

CATALOG_HEADER = """\
# tiny-blocks catalog

Index of published tiny-blocks packages and their one-line purpose. Generated from Packagist by
scripts/refresh-catalog.py, not hand-maintained. For the full API of a package, read its README
and public PHPDoc under vendor/tiny-blocks/<name>/.

"""


def report(message: str) -> None:
    print(message, file=sys.stderr)


def fetch_json(url: str) -> dict:
    request = urllib.request.Request(url=url, headers={"User-Agent": "tiny-blocks-catalog"})

    with urllib.request.urlopen(url=request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
        payload = json.load(fp=response)
    return payload


def sanitize(description: str) -> str:
    collapsed = " ".join(description.split())

    for character in (";", "—", "–"):
        collapsed = collapsed.replace(character, ",")
    return collapsed


def catalog_line(name: str) -> Optional[str]:
    try:
        metadata = fetch_json(url=f"https://packagist.org/packages/{name}.json").get("package", {})
    except (urllib.error.URLError, json.JSONDecodeError):
        report(message=f"Skipping {name}, metadata fetch failed.")
        return None

    if metadata.get("abandoned"):
        return None

    description = sanitize(description=metadata.get("description") or "")

    return textwrap.fill(
        text=f"- `{name}`: {description}",
        width=LINE_WIDTH,
        subsequent_indent="  ",
        break_long_words=False,
        break_on_hyphens=False,
    )


def build_catalog() -> str:
    names = sorted(fetch_json(url=LIST_URL).get("packageNames", []))
    lines: List[str] = []

    for name in names:
        line = catalog_line(name=name)

        if line is not None:
            lines.append(line)
    return CATALOG_HEADER + "\n".join(lines) + "\n"


def main() -> int:
    try:
        catalog = build_catalog()
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        report(message=f"Failed to build the catalog: {error}")
        return 1

    CATALOG_PATH.write_text(data=catalog, encoding="utf-8")
    print(f"Wrote {CATALOG_PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
