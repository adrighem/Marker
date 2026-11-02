import unittest

from credit_authors import commit_shas, credit

EXT = "a" * 40
OWN = "b" * 40
BOT = "c" * 40
NONE = "d" * 40

TEXT = f"""## [2026.11.1](https://example.com/compare) (2026-11-02)

### Features

* task lists ([#4](https://example.com/issues/4)) ([aaaaaaa](https://example.com/commit/{EXT}))
* **ux:** find bar ([bbbbbbb](https://example.com/commit/{OWN}))
* deps ([ccccccc](https://example.com/commit/{BOT}))
* unlinked author ([ddddddd](https://example.com/commit/{NONE}))
"""

AUTHORS: dict[str, str | None] = {
    EXT: "Contributor",
    OWN: "Maintainer",
    BOT: "renovate[bot]",
    NONE: None,
}


class CommitShasTest(unittest.TestCase):
    def test_collects_full_shas(self) -> None:
        self.assertEqual(commit_shas(TEXT), {EXT, OWN, BOT, NONE})


class CreditTest(unittest.TestCase):
    def test_credits_external_contributor_only(self) -> None:
        result = credit(TEXT, AUTHORS, ["maintainer"])
        self.assertIn(
            "* task lists (@Contributor) ([#4](https://example.com/issues/4))", result
        )
        self.assertEqual(result.count("(@"), 1)

    def test_is_idempotent(self) -> None:
        once = credit(TEXT, AUTHORS, ["Maintainer"])
        self.assertEqual(credit(once, AUTHORS, ["Maintainer"]), once)

    def test_leaves_other_lines_alone(self) -> None:
        result = credit(TEXT, AUTHORS, ["Maintainer"])
        self.assertTrue(result.startswith("## [2026.11.1](https://example.com/compare)"))


if __name__ == "__main__":
    unittest.main()
