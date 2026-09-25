<div align="center">

# LeetCode

**A continuously updated record of my algorithmic problem solving.**

Every accepted submission is captured the moment it passes — the problem statement,
the final solution, and the runtime and memory it achieved — and committed here
automatically. Nothing in this repository is written by hand after the fact.

<!-- BADGES:START -->
<img src="https://img.shields.io/badge/Solved-0-1f6feb?style=flat-square&labelColor=0d1117" alt="Solved: 0" />
<img src="https://img.shields.io/badge/Easy-0-00b8a3?style=flat-square&labelColor=0d1117" alt="Easy: 0" />
<img src="https://img.shields.io/badge/Medium-0-ffb800?style=flat-square&labelColor=0d1117" alt="Medium: 0" />
<img src="https://img.shields.io/badge/Hard-0-ff375f?style=flat-square&labelColor=0d1117" alt="Hard: 0" />
<!-- BADGES:END -->

<img src="https://img.shields.io/badge/Language-Java-e76f00?style=flat-square&labelColor=0d1117" alt="Primary language: Java" />
<img src="https://img.shields.io/github/actions/workflow/status/slazyverse/leetcode/progress.yml?branch=main&style=flat-square&labelColor=0d1117&label=CI" alt="CI status" />
<img src="https://img.shields.io/github/last-commit/slazyverse/leetcode?style=flat-square&labelColor=0d1117&color=6e7681" alt="Last commit" />
<img src="https://img.shields.io/badge/License-MIT-8957e5?style=flat-square&labelColor=0d1117" alt="License: MIT" />

<sub>
  <a href="#progress">Progress</a> &nbsp;·&nbsp;
  <a href="#repository-layout">Layout</a> &nbsp;·&nbsp;
  <a href="docs/INDEX.md">Full index</a> &nbsp;·&nbsp;
  <a href="docs/PATTERNS.md">Patterns</a> &nbsp;·&nbsp;
  <a href="docs/TEMPLATES.md">Templates</a> &nbsp;·&nbsp;
  <a href="docs/COMPLEXITY.md">Complexity</a>
</sub>

</div>

---

## Overview

This repository is the long-form version of a LeetCode profile. A profile shows a
number; this shows the work behind it — what was solved, how it was solved, what
the accepted solution cost in time and space, and what was learned in the process.

Three properties are maintained deliberately:

- **Every problem is self-contained.** One directory holds the statement, the
  solution, and any notes, so a single folder is enough to understand a problem
  without leaving the page.
- **The record is honest.** Solutions are committed automatically at the moment
  of acceptance, with the real runtime and memory percentiles in the commit
  message. Nothing is backfilled or tidied up afterwards.
- **The summary is derived, never hand-written.** Every table below is generated
  from the contents of [`solutions/`](solutions) by
  [`tools/generate_stats.py`](tools/generate_stats.py), so the statistics cannot
  drift away from the code they describe.

## Progress

<!-- PROGRESS:START -->
> No solutions have been synced yet. These tables populate automatically the first time an accepted submission reaches this repository.
<!-- PROGRESS:END -->

## Repository layout

```text
leetcode
├── solutions/                    every accepted submission lands here
│   └── 1-two-sum/                one directory per problem: <id>-<title-slug>
│       ├── README.md             the problem statement, as served by LeetCode
│       ├── two-sum.java          the accepted solution
│       └── Notes.md              optional commentary: approach, pitfalls, follow-ups
├── docs/
│   ├── INDEX.md                  generated index of every solved problem
│   ├── PATTERNS.md               the recurring shapes most problems reduce to
│   ├── TEMPLATES.md              reference implementations worth knowing cold
│   └── COMPLEXITY.md             complexity reference and a practical cost model
├── tools/
│   ├── generate_stats.py         rebuilds the progress tables and the index
│   └── test_generate_stats.py    unit tests for the generator, run on every push
├── .github/workflows/
│   └── progress.yml              test, regenerate, and validate on every synced commit
└── CONTRIBUTING.md               the conventions this repository holds itself to
```

## Anatomy of a solution

Each problem directory is named `<frontend-id>-<title-slug>` and holds up to three
files. Taking [Two Sum](https://leetcode.com/problems/two-sum/) as the example:

| File | Written by | Contents |
| :--- | :--------- | :------- |
| `README.md` | Sync | The full problem statement and a difficulty badge, preserved as LeetCode served it. |
| `two-sum.java` | Sync | The exact source that was accepted — not a cleaned-up rewrite. |
| `Notes.md` | Me | Why this approach, what the naive attempt cost, and the invariant that makes it correct. |

The commit that carries a solution records the measurement that came with it:

```text
Time: 2 ms (99.23%) | Memory: 44.8 MB (61.07%) - LeetSync
```

## How the pipeline works

```mermaid
flowchart LR
    A["Accepted submission<br/>on LeetCode"] --> B["LeetSync<br/>browser extension"]
    B -- "GitHub Contents API" --> C["solutions/&lt;id&gt;-&lt;slug&gt;/"]
    C -- "push to main" --> D["GitHub Actions<br/>progress.yml"]
    D --> E["tools/generate_stats.py"]
    E --> F["README.md<br/>docs/INDEX.md"]

    style A fill:#0d1117,stroke:#30363d,color:#e6edf3
    style B fill:#0d1117,stroke:#30363d,color:#e6edf3
    style C fill:#161b22,stroke:#30363d,color:#e6edf3
    style D fill:#0d1117,stroke:#30363d,color:#e6edf3
    style E fill:#161b22,stroke:#30363d,color:#e6edf3
    style F fill:#1f6feb,stroke:#1f6feb,color:#ffffff
```

1. A submission is accepted on LeetCode.
2. The [LeetSync](https://github.com/LeetSync/LeetSync) extension writes the
   statement, the solution, and any notes into `solutions/<id>-<slug>/` through the
   GitHub Contents API — one commit per file, straight to `main`.
3. That push triggers [`progress.yml`](.github/workflows/progress.yml), which first
   runs the generator's unit tests, then rewrites the marked regions of this README
   and of [`docs/INDEX.md`](docs/INDEX.md), committing only if something changed.
   A generator that fails its own tests is not allowed to rewrite the README.
4. A parallel job validates the layout of every problem directory, so a malformed
   or incomplete sync is surfaced rather than quietly absorbed.

The extension is configured to write into the `solutions` subdirectory, which is
what keeps the repository root readable no matter how many problems accumulate.
See [CONTRIBUTING.md](CONTRIBUTING.md) for the full configuration.

## Conventions

- **Directory names come from LeetCode, not from me.** `<frontend-id>-<title-slug>`,
  always, so a problem number is enough to find its directory.
- **Accepted source is never edited in place.** If an approach improves, the better
  solution is resubmitted on LeetCode and re-synced, so the commit history shows the
  progression instead of erasing it.
- **Notes explain reasoning, not syntax.** They record the invariant, the complexity
  argument, and the mistake that was worth remembering.
- **Generated regions are off limits to manual edits.** Anything between
  `<!-- KEY:START -->` and `<!-- KEY:END -->` markers is rewritten by the generator.

## Working with this repository locally

Because submissions are committed remotely by the extension, the remote moves without
your local checkout knowing. Pull before doing any local work:

```bash
git clone https://github.com/slazyverse/leetcode.git
cd leetcode
git pull --rebase
```

Regenerate the statistics by hand — useful after editing notes, and exactly what CI runs:

```bash
python tools/generate_stats.py
```

Validate that every problem directory is well-formed:

```bash
python tools/generate_stats.py --check
```

Run the generator's own test suite:

```bash
python -m unittest discover -s tools -p "test_*.py" --verbose
```

Everything here depends only on the Python 3.10+ standard library. There is nothing
to install, and no network access is required.

## Documentation

| Document | What it covers |
| :------- | :------------- |
| [docs/INDEX.md](docs/INDEX.md) | Generated index of every solved problem, with difficulty, language, and date. |
| [docs/PATTERNS.md](docs/PATTERNS.md) | The recurring problem shapes, how to recognize each one, and what it costs. |
| [docs/TEMPLATES.md](docs/TEMPLATES.md) | Correct, reusable Java implementations of the algorithms that keep reappearing. |
| [docs/COMPLEXITY.md](docs/COMPLEXITY.md) | Complexity reference, amortization, and how to read a constraint. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Repository conventions, sync configuration, and the review checklist. |

## License

Released under the [MIT License](LICENSE). The solutions are mine; the problem
statements reproduced under each `solutions/*/README.md` remain the property of
LeetCode and are included for context only.
