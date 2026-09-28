---
phase: 11-the-working-folder
created: 2026-09-26
requirements: [KIT-01, KIT-09]
status: approved by the user on 2026-09-26
---

# Phase 11 context: the working folder

## What this phase is

Downloading the kit and opening its folder is the whole install. A fresh
session there picks up the contract, the tools run from the folder, and a
person's programs live in `programs/` and survive an update. Milestone 2's
decisions 1 to 3 (`../../milestone-2-CONTEXT.md`) set this; what follows is
how.

## What is already known

- **The contract loads by itself.** On 2026-09-26 the Claude Code desktop
  app, opened on this folder, loaded `AGENTS.md` as the project's
  instructions with no `CLAUDE.md` present. Seen once, in a clone; 11-03
  sees it again in a download.
- **Python here.** In the Bash tool, which is Git Bash, `python` and
  `python3` both start 3.9.13 and `py` is not found (2026-09-26).
  `hpprime.cmd` calls `python`; `hpprime`, for sh, calls `python3`.
- **The beginner's first step clones.** `docs/start/01-setup.md` says `git
  clone` and nothing else.

## Proposed decisions

1. **One folder per program in `programs/`.** `programs/NAME/` holds a
   program's source, the `.hpprgm` built from it and, for a project that
   spans sessions (Phase 15), its plan and state. Git ignores everything in
   `programs/` but its `README.md`, which says what goes there, so the
   folder exists in a ZIP.
2. **`AGENTS.md` says where a person's programs go**, in a few lines: work
   in `programs/NAME/`, never at the root or in `examples/`. The `.hpprgm`
   files lying at the root of this clone are ignored by git, so none
   ships; whether to delete them is the person's call.
3. **`hpprime update`**:
   - downloads the `main` branch as a ZIP from GitHub; `--from FILE.zip`
     does the same from a file, for tests and for a machine offline;
   - refuses when the folder has `.git`, and says to `git pull`;
   - never writes inside `programs/`, nor `.claude/settings.local.json`,
     which is the person's own;
   - overwrites and adds, and **never deletes**: a file the new version no
     longer has is listed, for the person to remove, since the update cannot
     tell it from one of theirs;
   - says what it changed, and which version it installed where the ZIP
     records one. Standard library: `urllib`, `zipfile`.
4. **The README and step 1 give two ways in.** A beginner: GitHub's **Code
   > Download ZIP**, unzip, open the folder in Claude Code's desktop app (or
   another agent), say what you want. An expert: `git clone`, and the tools
   directly. `docs/start/01-setup.md` gets the ZIP beside the clone.
5. **When no Python starts**, the agent stops and sends the person to step
   1's Python row, instead of trying commands. `AGENTS.md` says so in one
   line; which command it tries first is settled in 11-03.

## Plans

1. **11-01, the folder**: `programs/` with its `README.md` and the ignore
   rule; the lines in `AGENTS.md`; the README's and step 1's two ways in; a
   test that `programs/` ships only its note and that nothing points at the
   gone `SKILL.md`.
2. **11-02, `hpprime update`**: the command, its entry in `docs/tools.md`,
   and tests on ZIPs made in the test itself: `programs/` untouched,
   `settings.local.json` untouched, a clone refused, a removed file listed
   and kept. No test reaches the network.
3. **11-03, downloaded and tried**: a ZIP made by `git -c
   core.autocrlf=false -c core.eol=lf archive`, which is how GitHub builds
   its own (without both, a local one comes out CRLF on this machine, and
   GitHub's is LF: `11-02-SUMMARY.md`), unzipped in a folder that is not
   this clone.
   The person opens it in the desktop app and gives a first task in plain
   words, without mentioning the kit. What is recorded: whether `AGENTS.md`
   loaded, whether `docs/llms.txt` was read, which Python ran, and `lint`,
   `run` and `write` on a program in `programs/`. Then from GitHub, once
   pushed at the person's word, and `hpprime update` against it. Already
   seen in 11-02: the download works from this machine, and GitHub's ZIP
   carries its commit.

## What only the person can do

Opening a new session on the unzipped folder, and pushing. The agent says
what to do and reads what the files show afterwards.
