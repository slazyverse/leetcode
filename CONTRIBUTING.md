# Conventions

This is a personal practice repository, so "contributing" mostly means *me, six
months from now*. These are the rules that keep it worth reading by then.

---

## 1. The sync configuration

Solutions arrive through the [LeetSync](https://github.com/LeetSync/LeetSync)
browser extension, which commits to this repository through the GitHub Contents
API. The extension must be configured exactly once:

| Setting | Value | Why |
| :------ | :---- | :-- |
| Repository | `leetcode` | This repository. |
| Subdirectory | `solutions` | Keeps hundreds of problem directories out of the repository root. **This is the setting that matters most** — without it, every problem lands at the top level and the repository becomes unreadable. |
| Notes | Enabled | LeetCode's own note field is synced to `Notes.md`, so reasoning lives next to the code. |

The extension writes to the default branch directly. There is no pull request in
the loop, so the conventions below are enforced by CI rather than by review.

## 2. The shape of a problem directory

```text
solutions/<frontend-id>-<title-slug>/
├── README.md              required — problem statement and difficulty badge
├── <title-slug>.<ext>     required — at least one accepted solution
└── Notes.md               optional — reasoning, written by me
```

Constraints, all checked by `python tools/generate_stats.py --check`:

- The directory name is `<frontend-id>-<title-slug>` — LeetCode's own numbering and
  slug, never a renamed variant. This is what makes a problem number sufficient to
  locate a directory.
- `README.md` must be present and must contain the difficulty badge, since the
  difficulty statistics are parsed from it.
- At least one file must carry a recognized source extension. Files named
  `README.md` and `Notes.md` are reserved and are never treated as solutions.
- Nothing may sit loose in `solutions/` outside a problem directory.

## 3. Rules for the source itself

**Do not edit accepted source in place.** The value of this repository is that the
code in it is the code that actually passed, with the runtime attached to the
commit. Editing it afterwards turns an honest record into a portfolio of things
that were never run.

When a better solution exists, submit it on LeetCode and let it sync. The commit
history then shows the progression — the O(n²) attempt and the O(n) replacement —
which is far more interesting than only ever seeing the final answer.

Solving a problem a second time in a different language is fine: a second file with
a different extension in the same directory is picked up automatically, and the
language statistics will show both.

## 4. Rules for notes

`Notes.md` is the only file written by hand. It is worth writing when the problem
taught something, and worth skipping when it did not. A note that restates the
problem is noise.

A note that earns its place answers at least one of:

- **Why this approach?** What made the obvious approach too slow, and what property
  of the input the accepted approach exploits.
- **What is the invariant?** The one sentence that makes the solution provably
  correct — what stays true at the top of every loop iteration.
- **What was the trap?** The off-by-one, the overflow, the empty-input case, or the
  misread constraint that cost real time.
- **What does this generalize to?** The pattern in [docs/PATTERNS.md](docs/PATTERNS.md)
  it belongs to, and the neighbouring problems it unlocks.

State complexity explicitly, in both time and space, and say what `n` refers to.

## 5. Generated content

Anything between `<!-- KEY:START -->` and `<!-- KEY:END -->` markers is owned by
[`tools/generate_stats.py`](tools/generate_stats.py) and will be overwritten on the
next sync. That currently covers:

| File | Regions |
| :--- | :------ |
| `README.md` | `BADGES`, `PROGRESS` |
| `docs/INDEX.md` | `INDEX` |

To change what those regions contain, change the generator — not the output.

## 6. Local workflow

The extension pushes to the remote, so a local checkout goes stale as soon as a
problem is solved. Always rebase before local work:

```bash
git pull --rebase
```

Before pushing anything by hand, run what CI runs:

```bash
python -m unittest discover -s tools -p "test_*.py"   # the generator still works
python tools/generate_stats.py --check                # layout matches the conventions
python tools/generate_stats.py                        # regenerate README and INDEX
```

All three require only the Python 3.10+ standard library, and none touch the network.

Changes to [`tools/generate_stats.py`](tools/generate_stats.py) belong with a test in
[`tools/test_generate_stats.py`](tools/test_generate_stats.py). The parser reads markup
produced by a third party that can change without notice, so its regression tests are
the only thing standing between a silent format change and a quietly wrong README.

## 7. Commit messages

Commits made by the extension are formatted by the extension and are left alone.
Commits made by hand follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
docs(notes): add invariant for 239-sliding-window-maximum
feat(tools): report language distribution in the progress table
chore(stats): refresh progress tables and problem index
```

The scope names the thing that changed — a problem slug, a tool, or a document.
