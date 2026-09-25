#!/usr/bin/env python3
"""Generate progress statistics for the solutions tracked in this repository.

This script reads the on-disk layout produced by the LeetSync browser extension,
which writes exactly one directory per accepted LeetCode problem::

    solutions/<frontend-id>-<title-slug>/
        README.md              problem statement and difficulty badge
        <title-slug>.<ext>     the accepted solution
        Notes.md               optional personal notes

From that layout it regenerates two things:

* the badge and progress regions of ``README.md``
* the complete problem index in ``docs/INDEX.md``

Both are delimited by ``<!-- KEY:START -->`` / ``<!-- KEY:END -->`` markers, so
the surrounding prose is never touched.

Usage
-----
    python tools/generate_stats.py             regenerate README.md and docs/INDEX.md
    python tools/generate_stats.py --check     validate the layout, write nothing
    python tools/generate_stats.py --root DIR  operate on a different checkout

Exit codes
----------
    0   success, or --check found no violations
    1   --check found at least one violation
    2   a required file or marker region is missing
"""

from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

#: Mirrors the extension's own language table so that every file it is capable
#: of writing is attributed to the correct language here.
EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "Python",
    ".java": "Java",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".rb": "Ruby",
    ".swift": "Swift",
    ".go": "Go",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".rs": "Rust",
    ".php": "PHP",
    ".dart": "Dart",
    ".ex": "Elixir",
    ".sql": "SQL",
}

DIFFICULTIES: tuple[str, ...] = ("Easy", "Medium", "Hard")

DIFFICULTY_COLOR: dict[str, str] = {
    "Easy": "00b8a3",
    "Medium": "ffb800",
    "Hard": "ff375f",
}

DIFFICULTY_MARK: dict[str, str] = {
    "Easy": "\N{LARGE GREEN CIRCLE}",
    "Medium": "\N{LARGE YELLOW CIRCLE}",
    "Hard": "\N{LARGE RED CIRCLE}",
    "Unknown": "\N{MEDIUM WHITE CIRCLE}",
}

SOLUTIONS_DIR = "solutions"
RESERVED_FILENAMES = {"README.md", "Notes.md"}
RECENT_LIMIT = 10
BAR_WIDTH = 18

DIRECTORY_RE = re.compile(r"^(\d+)-(.+)$")
# The slug is greedy up to the first delimiter: a lazy quantifier here would match a
# single character and let the trailing wildcard swallow the rest of the slug.
TITLE_RE = re.compile(
    r"<a\s+href=[\"\']https?://leetcode\.com/problems/([^\"\'?#/]+)[^\"\']*[\"\'][^>]*>(.*?)</a>",
    re.IGNORECASE | re.DOTALL,
)
DIFFICULTY_RE = re.compile(r"Difficulty-(Easy|Medium|Hard)-", re.IGNORECASE)
TAG_RE = re.compile(r"<[^>]+>")


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Problem:
    """A single synced problem directory."""

    number: int
    slug: str
    title: str
    difficulty: str
    directory: Path
    solutions: tuple[Path, ...]
    has_notes: bool
    synced_at: datetime | None

    @property
    def languages(self) -> list[str]:
        """Distinct languages this problem has been solved in, in filename order."""
        seen: list[str] = []
        for path in self.solutions:
            language = EXTENSION_TO_LANGUAGE.get(path.suffix.lower())
            if language and language not in seen:
                seen.append(language)
        return seen

    @property
    def url(self) -> str:
        return f"https://leetcode.com/problems/{self.slug}/"


# --------------------------------------------------------------------------- #
# Parsing
# --------------------------------------------------------------------------- #


def humanize(slug: str) -> str:
    """Turn ``two-sum`` into ``Two Sum`` for directories that lack a README."""
    return " ".join(word.capitalize() for word in slug.split("-") if word)


def strip_markup(fragment: str) -> str:
    """Reduce an HTML fragment to its visible text."""
    return html.unescape(TAG_RE.sub("", fragment)).strip()


def read_problem(directory: Path, synced_at: datetime | None) -> Problem | None:
    """Build a :class:`Problem` from a directory, or ``None`` if it is not one."""
    match = DIRECTORY_RE.match(directory.name)
    if not match:
        return None

    number, slug = int(match.group(1)), match.group(2)
    title, difficulty = humanize(slug), "Unknown"

    readme = directory / "README.md"
    if readme.is_file():
        body = readme.read_text(encoding="utf-8", errors="replace")

        title_match = TITLE_RE.search(body)
        if title_match:
            slug = title_match.group(1) or slug
            parsed_title = strip_markup(title_match.group(2))
            if parsed_title:
                title = parsed_title

        difficulty_match = DIFFICULTY_RE.search(body)
        if difficulty_match:
            difficulty = difficulty_match.group(1).capitalize()

    solutions = tuple(
        sorted(
            path
            for path in directory.iterdir()
            if path.is_file()
            and path.name not in RESERVED_FILENAMES
            and path.suffix.lower() in EXTENSION_TO_LANGUAGE
        )
    )

    return Problem(
        number=number,
        slug=slug,
        title=title,
        difficulty=difficulty,
        directory=directory,
        solutions=solutions,
        has_notes=(directory / "Notes.md").is_file(),
        synced_at=synced_at,
    )


def sync_dates(root: Path) -> dict[str, datetime]:
    """Map each solution directory to the commit date that last touched it.

    The whole history is read in a single ``git log`` pass. An empty map is
    returned when git is unavailable or the checkout has no commits yet, so the
    script still works outside a repository.
    """
    prefix = f"{SOLUTIONS_DIR}/"
    try:
        completed = subprocess.run(
            ["git", "-C", str(root), "log", "--format=%x00%cI", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return {}

    dates: dict[str, datetime] = {}
    for chunk in completed.stdout.split("\x00"):
        lines = [line.strip() for line in chunk.splitlines() if line.strip()]
        if not lines:
            continue
        try:
            committed = datetime.fromisoformat(lines[0])
        except ValueError:
            continue
        for path in lines[1:]:
            if not path.startswith(prefix):
                continue
            name = path[len(prefix) :].split("/", 1)[0]
            # git log is newest-first, so the first sighting is the latest commit.
            if name:
                dates.setdefault(name, committed)
    return dates


def collect(root: Path) -> list[Problem]:
    """Discover every synced problem, ordered by problem number."""
    solutions_root = root / SOLUTIONS_DIR
    if not solutions_root.is_dir():
        return []

    dates = sync_dates(root)
    problems: list[Problem] = []
    for directory in sorted(solutions_root.iterdir()):
        if not directory.is_dir() or directory.name.startswith("."):
            continue
        problem = read_problem(directory, dates.get(directory.name))
        if problem is not None:
            problems.append(problem)
    return sorted(problems, key=lambda problem: problem.number)


# --------------------------------------------------------------------------- #
# Rendering helpers
# --------------------------------------------------------------------------- #


def escape_cell(text: str) -> str:
    """Make text safe to place inside a markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def bar(value: int, total: int, width: int = BAR_WIDTH) -> str:
    """Render a fixed-width proportional bar."""
    if total <= 0:
        return "\u2591" * width
    filled = round(width * value / total)
    return "\u2588" * filled + "\u2591" * (width - filled)


def percent(value: int, total: int) -> str:
    return f"{(value / total * 100):.1f}%" if total else "0.0%"


def badge(label: str, message: str, color: str) -> str:
    """Build a shields.io badge as an HTML image tag."""

    def quote(raw: str) -> str:
        return raw.replace("-", "--").replace("_", "__").replace(" ", "_")

    src = (
        f"https://img.shields.io/badge/{quote(label)}-{quote(message)}-{color}"
        f"?style=flat-square&labelColor=0d1117"
    )
    return f'<img src="{src}" alt="{label}: {message}" />'


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def format_date(moment: datetime | None) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d") if moment else "\u2014"


# --------------------------------------------------------------------------- #
# Renderers
# --------------------------------------------------------------------------- #


def render_badges(problems: list[Problem]) -> str:
    counts = Counter(problem.difficulty for problem in problems)
    parts = [badge("Solved", str(len(problems)), "1f6feb")]
    parts += [
        badge(level, str(counts.get(level, 0)), DIFFICULTY_COLOR[level])
        for level in DIFFICULTIES
    ]
    return "\n".join(parts)


def render_progress(problems: list[Problem]) -> str:
    total = len(problems)
    if not total:
        return (
            "> No solutions have been synced yet. These tables populate automatically "
            "the first time an accepted submission reaches this repository."
        )

    lines = [
        "| Difficulty | Solved | Share | Distribution |",
        "| :--------- | -----: | ----: | :----------- |",
    ]
    for level in DIFFICULTIES:
        count = sum(1 for problem in problems if problem.difficulty == level)
        lines.append(
            f"| {DIFFICULTY_MARK[level]} {level} | {count} | {percent(count, total)} "
            f"| `{bar(count, total)}` |"
        )

    unknown = sum(1 for problem in problems if problem.difficulty not in DIFFICULTIES)
    if unknown:
        lines.append(
            f"| {DIFFICULTY_MARK['Unknown']} Unclassified | {unknown} "
            f"| {percent(unknown, total)} | `{bar(unknown, total)}` |"
        )
    lines.append(f"| **Total** | **{total}** | **100.0%** | |")

    language_counts = Counter(
        language for problem in problems for language in problem.languages
    )
    if language_counts:
        attributed = sum(language_counts.values())
        lines += [
            "",
            "| Language | Solutions | Share |",
            "| :------- | --------: | ----: |",
        ]
        for language, count in language_counts.most_common():
            lines.append(f"| {language} | {count} | {percent(count, attributed)} |")

    dated = [problem for problem in problems if problem.synced_at is not None]
    recent = sorted(dated, key=lambda problem: problem.synced_at, reverse=True)[:RECENT_LIMIT]
    if recent:
        lines += [
            "",
            "<details>",
            f"<summary><strong>Most recently solved ({len(recent)})</strong></summary>",
            "",
            "| # | Problem | Difficulty | Synced |",
            "| ---: | :------ | :--------- | :----- |",
        ]
        for problem in recent:
            mark = DIFFICULTY_MARK.get(problem.difficulty, DIFFICULTY_MARK["Unknown"])
            lines.append(
                f"| {problem.number} | [{escape_cell(problem.title)}]({problem.url}) "
                f"| {mark} {problem.difficulty} | {format_date(problem.synced_at)} |"
            )
        lines += ["", "</details>"]

    lines += [
        "",
        f"<sub>Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} by "
        "<a href=\"tools/generate_stats.py\"><code>tools/generate_stats.py</code></a> "
        "\u00b7 <a href=\"docs/INDEX.md\">full problem index</a></sub>",
    ]
    return "\n".join(lines)


def render_index(root: Path, problems: list[Problem]) -> str:
    if not problems:
        return (
            "> No solutions have been synced yet. This index is generated from the "
            f"contents of `{SOLUTIONS_DIR}/` and fills in as problems are solved."
        )

    lines = [
        "| # | Problem | Difficulty | Solution | Notes | Synced |",
        "| ---: | :------ | :--------- | :------- | :---- | :----- |",
    ]
    for problem in problems:
        if problem.solutions:
            links = " \u00b7 ".join(
                "[{label}](../{path})".format(
                    label=EXTENSION_TO_LANGUAGE.get(
                        path.suffix.lower(), path.suffix.lstrip(".")
                    ),
                    path=relative(root, path),
                )
                for path in problem.solutions
            )
        else:
            links = "\u2014"

        notes = (
            f"[Notes](../{relative(root, problem.directory)}/Notes.md)"
            if problem.has_notes
            else "\u2014"
        )
        mark = DIFFICULTY_MARK.get(problem.difficulty, DIFFICULTY_MARK["Unknown"])
        lines.append(
            f"| {problem.number} "
            f"| [{escape_cell(problem.title)}](../{relative(root, problem.directory)}) "
            f"| {mark} {problem.difficulty} | {links} | {notes} "
            f"| {format_date(problem.synced_at)} |"
        )
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# File updates
# --------------------------------------------------------------------------- #


def replace_region(text: str, key: str, body: str, source: Path) -> str:
    """Swap the contents of a ``<!-- KEY:START -->`` / ``<!-- KEY:END -->`` block."""
    start, end = f"<!-- {key}:START -->", f"<!-- {key}:END -->"
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(text):
        sys.exit(f"error: {source} is missing the {key!r} marker region")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", text, count=1)


def write_if_changed(path: Path, content: str) -> bool:
    """Write only when the content actually differs, to avoid empty commits."""
    previous = path.read_text(encoding="utf-8") if path.is_file() else None
    if previous == content:
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #


def check(root: Path, problems: list[Problem]) -> list[str]:
    """Report every solution directory that breaks the repository conventions."""
    solutions_root = root / SOLUTIONS_DIR
    if not solutions_root.is_dir():
        return [f"{SOLUTIONS_DIR}/ does not exist"]

    violations: list[str] = []
    for entry in sorted(solutions_root.iterdir()):
        if entry.name.startswith("."):
            continue
        if entry.is_file():
            violations.append(
                f"{relative(root, entry)}: stray file outside a problem directory"
            )
        elif not DIRECTORY_RE.match(entry.name):
            violations.append(
                f"{relative(root, entry)}: directory name must be <id>-<title-slug>"
            )

    for problem in problems:
        where = relative(root, problem.directory)
        if not (problem.directory / "README.md").is_file():
            violations.append(f"{where}: missing README.md with the problem statement")
        if not problem.solutions:
            violations.append(f"{where}: no solution file with a recognized extension")
        if problem.difficulty not in DIFFICULTIES:
            violations.append(f"{where}: difficulty not determinable from README.md")

    return violations


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate the progress statistics for this repository."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="repository root (defaults to the parent of tools/)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the solutions layout and write nothing",
    )
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    problems = collect(root)

    if args.check:
        violations = check(root, problems)
        if violations:
            print(f"Found {len(violations)} convention violation(s):", file=sys.stderr)
            for violation in violations:
                print(f"  x {violation}", file=sys.stderr)
            return 1
        print(f"OK - {len(problems)} problem director(ies) match the expected layout.")
        return 0

    readme_path = root / "README.md"
    index_path = root / "docs" / "INDEX.md"
    for required in (readme_path, index_path):
        if not required.is_file():
            sys.exit(f"error: {relative(root, required)} not found")

    readme = readme_path.read_text(encoding="utf-8")
    readme = replace_region(readme, "BADGES", render_badges(problems), readme_path)
    readme = replace_region(readme, "PROGRESS", render_progress(problems), readme_path)

    index = index_path.read_text(encoding="utf-8")
    index = replace_region(index, "INDEX", render_index(root, problems), index_path)

    changed = [
        relative(root, path)
        for path, content in ((readme_path, readme), (index_path, index))
        if write_if_changed(path, content)
    ]

    counts = Counter(problem.difficulty for problem in problems)
    summary = " / ".join(f"{level} {counts.get(level, 0)}" for level in DIFFICULTIES)
    print(f"Indexed {len(problems)} problem(s) - {summary}")
    print("Updated: " + (", ".join(changed) if changed else "nothing (already current)"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
