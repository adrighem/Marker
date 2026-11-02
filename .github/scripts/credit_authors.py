#!/usr/bin/env python3
"""Append "(@login)" to changelog bullets written by external contributors.

Usage: credit_authors.py FILE REPO EXCLUDED_LOGIN...

FILE is a CHANGELOG.md or a release PR body. Each bullet's commit link is
resolved to its GitHub author with `gh api`; bots and EXCLUDED_LOGINs
(the maintainers) are not credited. Bullets already crediting the author
are left alone, so the script is safe to re-run.

Stopgap for release-please 17.11.2, which accepts include-commit-authors
but drops the authors while parsing commits.
"""

import re
import subprocess
import sys
from collections.abc import Callable, Iterable
from pathlib import Path

BULLET_RE = re.compile(
    r"^(?P<head>\* .*?)(?P<links>(?: \(\[[^\]]+\]\([^)]+\)\))+)$", re.MULTILINE
)
COMMIT_RE = re.compile(r"/commit/(?P<sha>[0-9a-f]{40})\)")


def commit_shas(text: str) -> set[str]:
    """Full SHAs of all commits linked from changelog bullets."""
    return {
        sha.group("sha")
        for bullet in BULLET_RE.finditer(text)
        for sha in COMMIT_RE.finditer(bullet.group("links"))
    }


def credit(text: str, authors: dict[str, str | None], excluded: Iterable[str]) -> str:
    """Insert "(@login)" before the links of each external contributor's bullet."""
    skip = {login.lower() for login in excluded}

    def replace(bullet: re.Match[str]) -> str:
        head, links = bullet.group("head"), bullet.group("links")
        sha = COMMIT_RE.search(links)
        login = authors.get(sha.group("sha")) if sha else None
        if (
            login is None
            or login.lower() in skip
            or login.endswith("[bot]")
            or f"(@{login})" in head
        ):
            return bullet.group(0)
        return f"{head} (@{login}){links}"

    return BULLET_RE.sub(replace, text)


def gh_author(repo: str) -> Callable[[str], str | None]:
    """Return a lookup of a commit's GitHub login (None if unlinked)."""

    def lookup(sha: str) -> str | None:
        login = subprocess.run(
            ["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", ".author.login // empty"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return login or None

    return lookup


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    path, repo, excluded = Path(argv[1]), argv[2], argv[3:]
    text = path.read_text(encoding="utf-8")
    lookup = gh_author(repo)
    authors = {sha: lookup(sha) for sha in commit_shas(text)}
    path.write_text(credit(text, authors, excluded), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
