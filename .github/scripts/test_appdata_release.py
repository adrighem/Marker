import unittest

from appdata_release import changelog_items, release_block, upsert_release

CHANGELOG = """# Changelog

## [2026.11.1](https://example.com/compare) (2026-11-02)


### Features

* render task lists ([#4](https://example.com/issues/4)) ([5bf0c62](https://example.com/c/5bf0c62))
* **ux:** polish find bar & zoom (@someone) ([bd8dbe5](https://example.com/c/bd8dbe5))


### Bug Fixes

* follow-ups from [#4](https://example.com/issues/4) review ([1d156c5](https://example.com/c/1d156c5))

## [2026.11.0](https://example.com/compare) (2026-10-17)

* older entry ([1f4246c](https://example.com/c/1f4246c))
"""

APPDATA = """<component>
  <releases>
    <release version="2026.10.0" date="2026-10-11">
      <description translate="no">
        <ul>
          <li>Old.</li>
        </ul>
      </description>
    </release>
  </releases>
</component>
"""


class ChangelogItemsTest(unittest.TestCase):
    def test_strips_links_scopes_and_trailers(self) -> None:
        self.assertEqual(
            changelog_items(CHANGELOG, "2026.11.1"),
            [
                "Render task lists.",
                "Polish find bar & zoom.",
                "Follow-ups from #4 review.",
            ],
        )

    def test_only_reads_requested_section(self) -> None:
        self.assertEqual(changelog_items(CHANGELOG, "2026.11.0"), ["Older entry."])

    def test_missing_section_fails(self) -> None:
        with self.assertRaises(ValueError):
            changelog_items(CHANGELOG, "2030.1.0")


class UpsertReleaseTest(unittest.TestCase):
    def test_inserts_newest_first_and_escapes(self) -> None:
        block = release_block("2026.11.1", "2026-11-02", ["A & B."])
        result = upsert_release(APPDATA, "2026.11.1", block)
        self.assertLess(result.index("2026.11.1"), result.index("2026.10.0"))
        self.assertIn("<li>A &amp; B.</li>", result)

    def test_replaces_existing_entry(self) -> None:
        first = upsert_release(
            APPDATA, "2026.11.1", release_block("2026.11.1", "2026-11-02", ["Old"])
        )
        second = upsert_release(
            first, "2026.11.1", release_block("2026.11.1", "2026-11-03", ["New"])
        )
        self.assertEqual(second.count('version="2026.11.1"'), 1)
        self.assertIn('date="2026-11-03"', second)
        self.assertNotIn("<li>Old</li>", second)
        self.assertIn('version="2026.10.0"', second)

    def test_missing_releases_fails(self) -> None:
        with self.assertRaises(ValueError):
            upsert_release("<component/>", "1.0.0", "")


if __name__ == "__main__":
    unittest.main()
