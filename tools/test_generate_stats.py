#!/usr/bin/env python3
"""Unit tests for :mod:`generate_stats`.

Run from the repository root::

    python -m unittest discover -s tools -p "test_*.py" -v

The fixtures reproduce the markup the LeetSync extension actually writes --
single-quoted badge attributes, an unpadded problem id in the directory name, and
the statement inlined after an ``<hr>`` -- so the parser is exercised against the
real format rather than an idealized one.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import generate_stats as gs  # noqa: E402

BADGE_COLOR = {"Easy": "brightgreen", "Medium": "orange", "Hard": "red"}


def write_problem(
    root: Path,
    number: int,
    slug: str,
    title: str,
    difficulty: str | None = "Easy",
    filenames: tuple[str, ...] = (),
    notes: bool = False,
    href: str | None = None,
) -> Path:
    """Create one problem directory in the layout the extension produces."""
    directory = root / gs.SOLUTIONS_DIR / f"{number}-{slug}"
    directory.mkdir(parents=True, exist_ok=True)

    link = href if href is not None else f"https://leetcode.com/problems/{slug}"
    badge = ""
    if difficulty is not None:
        badge = (
            "<img src='https://img.shields.io/badge/Difficulty-"
            f"{difficulty}-{BADGE_COLOR[difficulty]}' alt='Difficulty: {difficulty}' />"
        )
    (directory / "README.md").write_text(
        f'<h2><a href="{link}">{title}</a></h2> {badge}<hr><p>Body.</p>',
        encoding="utf-8",
    )

    for filename in filenames:
        (directory / filename).write_text("// solution\n", encoding="utf-8")
    if notes:
        (directory / "Notes.md").write_text("<h2>Notes</h2><hr>Idea.", encoding="utf-8")
    return directory


class ParsingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / gs.SOLUTIONS_DIR).mkdir()
        self.addCleanup(self._tmp.cleanup)

    def test_reads_title_slug_and_difficulty(self) -> None:
        write_problem(self.root, 1, "two-sum", "Two Sum", "Easy", ("two-sum.java",))
        (problem,) = gs.collect(self.root)

        self.assertEqual(problem.number, 1)
        self.assertEqual(problem.slug, "two-sum")
        self.assertEqual(problem.title, "Two Sum")
        self.assertEqual(problem.difficulty, "Easy")
        self.assertEqual(problem.languages, ["Java"])
        self.assertFalse(problem.has_notes)

    def test_slug_survives_trailing_slash_and_query(self) -> None:
        """A lazy quantifier here once truncated the slug to its first character."""
        for href in (
            "https://leetcode.com/problems/two-sum/",
            "https://leetcode.com/problems/two-sum/description/",
            "https://leetcode.com/problems/two-sum?envId=top-100",
            "http://leetcode.com/problems/two-sum",
        ):
            with self.subTest(href=href):
                root = Path(tempfile.mkdtemp(dir=self.root))
                (root / gs.SOLUTIONS_DIR).mkdir()
                write_problem(root, 1, "two-sum", "Two Sum", "Easy", ("two-sum.java",), href=href)
                (problem,) = gs.collect(root)
                self.assertEqual(problem.slug, "two-sum")
                self.assertEqual(problem.url, "https://leetcode.com/problems/two-sum/")

    def test_decodes_entities_and_nested_markup_in_title(self) -> None:
        write_problem(
            self.root, 8, "string-to-integer-atoi",
            "String to Integer <em>(atoi)</em> &amp; More", "Medium",
            ("string-to-integer-atoi.java",),
        )
        (problem,) = gs.collect(self.root)
        self.assertEqual(problem.title, "String to Integer (atoi) & More")

    def test_falls_back_when_readme_is_unparseable(self) -> None:
        directory = self.root / gs.SOLUTIONS_DIR / "7-reverse-integer"
        directory.mkdir(parents=True)
        (directory / "README.md").write_text("no markup here", encoding="utf-8")
        (directory / "reverse-integer.java").write_text("// x", encoding="utf-8")

        (problem,) = gs.collect(self.root)
        self.assertEqual(problem.title, "Reverse Integer")   # humanized from the slug
        self.assertEqual(problem.difficulty, "Unknown")

    def test_orders_numerically_not_lexicographically(self) -> None:
        for number, slug in ((1, "a"), (42, "b"), (1106, "c"), (9, "d")):
            write_problem(self.root, number, slug, slug.upper(), "Easy", (f"{slug}.java",))
        self.assertEqual([p.number for p in gs.collect(self.root)], [1, 9, 42, 1106])

    def test_detects_multiple_languages_and_ignores_reserved_files(self) -> None:
        write_problem(
            self.root, 1, "two-sum", "Two Sum", "Easy",
            ("two-sum.java", "two-sum.py", "two-sum.txt"), notes=True,
        )
        (problem,) = gs.collect(self.root)
        self.assertEqual(sorted(problem.languages), ["Java", "Python"])
        self.assertTrue(problem.has_notes)
        self.assertNotIn("Notes.md", [path.name for path in problem.solutions])
        self.assertNotIn("two-sum.txt", [path.name for path in problem.solutions])

    def test_skips_dotted_and_unnumbered_directories(self) -> None:
        (self.root / gs.SOLUTIONS_DIR / ".github").mkdir()
        (self.root / gs.SOLUTIONS_DIR / "scratch").mkdir()
        write_problem(self.root, 1, "two-sum", "Two Sum", "Easy", ("two-sum.java",))
        self.assertEqual(len(gs.collect(self.root)), 1)

    def test_missing_solutions_directory_yields_nothing(self) -> None:
        empty = Path(tempfile.mkdtemp(dir=self.root))
        self.assertEqual(gs.collect(empty), [])


class RenderingTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / gs.SOLUTIONS_DIR).mkdir()
        self.addCleanup(self._tmp.cleanup)

    def test_escapes_pipes_so_tables_do_not_break(self) -> None:
        write_problem(
            self.root, 1106, "parsing-a-boolean-expression",
            "Parsing A Boolean | Expression", "Hard",
            ("parsing-a-boolean-expression.java",),
        )
        rendered = gs.render_index(self.root, gs.collect(self.root))
        self.assertIn(r"Parsing A Boolean \| Expression", rendered)
        # Header, separator, and exactly one data row.
        self.assertEqual(len(rendered.splitlines()), 3)

    def test_counts_and_percentages(self) -> None:
        for number, difficulty in ((1, "Easy"), (2, "Hard"), (3, "Hard"), (4, "Medium")):
            write_problem(
                self.root, number, f"p{number}", f"P{number}", difficulty, (f"p{number}.java",)
            )
        progress = gs.render_progress(gs.collect(self.root))
        self.assertIn("| 🔴 Hard | 2 | 50.0% |", progress)
        self.assertIn("**4**", progress)
        self.assertIn("| Java | 4 | 100.0% |", progress)

    def test_empty_repository_renders_a_placeholder(self) -> None:
        self.assertIn("No solutions", gs.render_progress([]))
        self.assertIn("No solutions", gs.render_index(self.root, []))
        self.assertIn("Solved-0-", gs.render_badges([]))

    def test_badge_escaping(self) -> None:
        self.assertIn("/badge/C++-3-", gs.badge("C++", "3", "1f6feb"))
        self.assertIn("/badge/Top_K-1--2-", gs.badge("Top K", "1-2", "1f6feb"))

    def test_bar_is_fixed_width(self) -> None:
        self.assertEqual(len(gs.bar(3, 7)), gs.BAR_WIDTH)
        self.assertEqual(gs.bar(0, 0), "░" * gs.BAR_WIDTH)
        self.assertEqual(gs.bar(5, 5), "█" * gs.BAR_WIDTH)


class RegionTests(unittest.TestCase):
    def test_replaces_only_the_marked_region(self) -> None:
        text = "before\n<!-- X:START -->\nold\n<!-- X:END -->\nafter\n"
        result = gs.replace_region(text, "X", "new", Path("f.md"))
        self.assertEqual(result, "before\n<!-- X:START -->\nnew\n<!-- X:END -->\nafter\n")

    def test_body_is_inserted_literally(self) -> None:
        """Backslashes in the body must not be read as regex replacement escapes."""
        text = "<!-- X:START -->\n<!-- X:END -->"
        body = r"a \| b \1 \g<0> \\ c"
        self.assertIn(body, gs.replace_region(text, "X", body, Path("f.md")))

    def test_missing_region_exits(self) -> None:
        with self.assertRaises(SystemExit):
            gs.replace_region("no markers", "X", "body", Path("f.md"))


class ValidationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / gs.SOLUTIONS_DIR).mkdir()
        self.addCleanup(self._tmp.cleanup)

    def test_clean_layout_has_no_violations(self) -> None:
        write_problem(self.root, 1, "two-sum", "Two Sum", "Easy", ("two-sum.java",))
        self.assertEqual(gs.check(self.root, gs.collect(self.root)), [])

    def test_flags_bad_directory_name(self) -> None:
        (self.root / gs.SOLUTIONS_DIR / "two-sum").mkdir()
        violations = gs.check(self.root, gs.collect(self.root))
        self.assertTrue(any("title-slug" in v for v in violations))

    def test_flags_stray_file(self) -> None:
        (self.root / gs.SOLUTIONS_DIR / "notes.txt").write_text("x", encoding="utf-8")
        violations = gs.check(self.root, gs.collect(self.root))
        self.assertTrue(any("stray file" in v for v in violations))

    def test_flags_missing_solution_and_unknown_difficulty(self) -> None:
        write_problem(self.root, 5, "x", "X", difficulty=None, filenames=())
        violations = gs.check(self.root, gs.collect(self.root))
        self.assertTrue(any("no solution file" in v for v in violations))
        self.assertTrue(any("difficulty" in v for v in violations))

    def test_dotfiles_are_not_violations(self) -> None:
        (self.root / gs.SOLUTIONS_DIR / ".gitkeep").write_text("", encoding="utf-8")
        self.assertEqual(gs.check(self.root, gs.collect(self.root)), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
