#!/usr/bin/env python3
"""Add or refresh an AppStream <release> entry from a CHANGELOG.md section.

Usage: appdata_release.py APPDATA CHANGELOG VERSION DATE

Runs on the release-please PR branch: release-please writes CHANGELOG.md,
this script mirrors the matching section into the AppStream metadata so
software centers show the release notes.
"""

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

SECTION_RE = r"^## \[?{version}\]?.*?$\n(?P<body>.*?)(?=^## |\Z)"
BULLET_RE = re.compile(r"^\* (?P<text>.+)$", re.MULTILINE)
LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
TRAILER_RE = re.compile(r"(\s+\((?:\[[^\]]+\]\([^)]+\)|@[\w-]+|[^()]*)\))+$")
SCOPE_RE = re.compile(r"^\*\*[^*]+:\*\*\s*")
RELEASES_TAG = "  <releases>\n"


def changelog_items(changelog: str, version: str) -> list[str]:
    """Return the plain-text bullets of the CHANGELOG section for version."""
    pattern = SECTION_RE.format(version=re.escape(version))
    match = re.search(pattern, changelog, re.MULTILINE | re.DOTALL)
    if match is None:
        raise ValueError(f"no CHANGELOG section for {version}")
    items = []
    for bullet in BULLET_RE.finditer(match.group("body")):
        text = TRAILER_RE.sub("", bullet.group("text"))
        text = LINK_RE.sub(r"\1", SCOPE_RE.sub("", text)).strip()
        if text:
            items.append(text[0].upper() + text[1:].rstrip(".") + ".")
    if not items:
        raise ValueError(f"CHANGELOG section for {version} has no entries")
    return items


def release_block(version: str, date: str, items: list[str]) -> str:
    """Render one <release> element in the file's indentation style."""
    lines = [
        f'    <release version="{escape(version)}" date="{escape(date)}">',
        '      <description translate="no">',
        "        <ul>",
        *(f"          <li>{escape(item)}</li>" for item in items),
        "        </ul>",
        "      </description>",
        "    </release>",
    ]
    return "\n".join(lines) + "\n"


def upsert_release(appdata: str, version: str, block: str) -> str:
    """Replace the entry for version, or insert it as the newest release."""
    existing = re.compile(
        rf'^    <release version="{re.escape(version)}".*?^    </release>\n',
        re.MULTILINE | re.DOTALL,
    )
    if existing.search(appdata):
        return existing.sub(lambda _: block, appdata, count=1)
    if RELEASES_TAG not in appdata:
        raise ValueError("appdata has no <releases> element")
    return appdata.replace(RELEASES_TAG, RELEASES_TAG + block, 1)


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__, file=sys.stderr)
        return 2
    appdata_path, changelog_path = Path(argv[1]), Path(argv[2])
    version, date = argv[3], argv[4]
    items = changelog_items(changelog_path.read_text(encoding="utf-8"), version)
    appdata = appdata_path.read_text(encoding="utf-8")
    block = release_block(version, date, items)
    appdata_path.write_text(upsert_release(appdata, version, block), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
