---
phase: 11-the-working-folder
plan: 02
status: complete
completed: 2026-09-27
key_files:
  - hpkit/update.py
  - hpkit/cli.py
  - tests/test_update.py
  - tests/run_all.py
  - docs/tools.md
  - README.md
  - docs/start/01-setup.md
  - programs/README.md
---

# Plan 02 summary: `hpprime update`

## What was built

- **`hpkit/update.py`**: the `main` branch's ZIP from GitHub, or `--from
  FILE.zip`; the one top folder stripped; refused in a clone; nothing
  written inside `programs/` or to `.claude/settings.local.json`; an entry
  reaching outside the folder, or a ZIP without `hpprime.py`,
  `hpkit/cli.py` and `AGENTS.md` at its top, refuses the whole archive
  before anything is written; a file written only when its bytes differ;
  nothing deleted, and a file the new version lacks listed unless it is the
  person's or the new `.gitignore` marks it (a small matcher, last pattern
  wins, negation honoured); `--dry-run`; counts, the listed files, and the
  commit from the ZIP's comment.
- **`hpprime update`** in the dispatcher and `--help`; its section in
  `docs/tools.md` and the module in "Using the modules directly"; a row in
  the README's table; step 1 and `programs/README.md` say how a download is
  updated.
- **`tests/test_update.py`**, 23 checks on folders and ZIPs made in the
  test, no network: the plan's list, a second run finding nothing, a ZIP
  with no top folder and no commit, and the command's own output. With
  `is_theirs` stubbed to answer no, 3 checks failed; with the ZIP read
  without its checks, 4 failed. Added to `run_all.py`; "thirteen suites"
  became fourteen in the README and `docs/tools.md`.

## End to end

- **A download of the published version brought to this tree**: `git
  archive HEAD` (d1271bb) unzipped, a `MINE.txt` added, then updated from a
  ZIP of the working tree built through a temporary index (`git add -A`
  into a copy of the index, `git write-tree`, `git archive` of the tree), so
  the real index was not touched. Result: 16 changed, 8 added, 921
  unchanged, the same numbers as the session's modified and new files;
  `MINE.txt` and `SKILL.md` listed and kept; `programs/README.md` not
  written. Afterwards 945 of the 946 files in the ZIP matched byte for byte,
  and the one missing was `programs/README.md`.
- **From GitHub, run by accident in that copy**: `hpprime update` with no
  `--from`, in the scratch copy that had no `.git`, downloaded GitHub's ZIP
  of `main` and wrote it there. Nothing outside the scratch folder was
  touched. What it showed:
  - the download works from this machine, Python 3.9.13;
  - GitHub's ZIP carries the commit as its comment: `c8951ab`;
  - GitHub's `main` is `c8951ab` "Update LICENSE", one commit ahead of the
    local `main` (d1271bb), made on GitHub;
  - 933 changed, 5 unchanged: GitHub's ZIP holds LF, and this machine's
    `core.autocrlf=true` made the local ZIP CRLF. `file` confirmed both.
    The five unchanged are binary.

## Deviations

- The docstring and 11-03's local ZIP follow the line-ending finding: a
  local ZIP standing in for GitHub's is made with `git -c
  core.autocrlf=false -c core.eol=lf archive`. `core.autocrlf=false` alone
  was not enough: on 2026-09-27, with it, `README.md` in the archive still
  had CRLF, and with `core.eol=lf` added it had none. The blob is LF
  (`git cat-file -p HEAD:README.md`); the conversion is the checkout's,
  from `* text=auto` and `core.eol` native. `core.autocrlf=true` here comes
  from Git for Windows' own `etc/gitconfig`.

## Left as it is, and why

- **`programs/README.md` is not written by an update**, even where it is
  missing, as decision 3 has it: nothing inside `programs/`. A download from
  before `programs/` existed gets no note; `hpprime new` creates the folder
  it needs.
- **A download from before this command existed has no `hpprime update`.**
  It is downloaded again by hand once.

## Results

```
test_update.py           23 passed, 0 failed
suite                    14,904 passed, 0 failed, 14 suites
hpprime docs --check     706 entries, 122 facts: 0 problem(s)
```
