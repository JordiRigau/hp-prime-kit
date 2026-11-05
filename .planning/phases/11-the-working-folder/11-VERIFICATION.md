---
phase: 11-the-working-folder
status: approved by the user on 2026-09-29
verified: 2026-09-29
requirements: [KIT-01, KIT-09]
---

# Phase 11 verification: The working folder

Taken on 2026-09-29 after plans 11-01 to 11-03, from the tests, the
download tried on 2026-09-28, GitHub's ZIP of 7581215 and git itself, not
asserted.

## Criterion 1: a download, opened with nothing installed, is picked up

| | |
|---|---|
| the download | `git -c core.autocrlf=false -c core.eol=lf archive` of the tree, unzipped on the Desktop, no `.git`, nothing above it that Claude Code reads |
| stands for GitHub's | GitHub's ZIP of 7581215 matched the same archive of that commit byte for byte, 948 of 948 files |
| the session | a new desktop-app session on that folder, one message from the user naming neither the kit nor its files |
| `AGENTS.md` loaded | **yes**: named in its first words, before any tool call |
| `docs/llms.txt` read | **yes**: its lines are in the transcript, with the read tool's line numbers |

## Criterion 2: the tools run from that folder, and how they start is written down

| | |
|---|---|
| on this Windows machine, in the tried session | `lint` clean, `run` 22 calls, `build` and `verify` 0 differences, `install` on the emulator; Python 3.9.13 |
| on this Windows machine, in a clean copy | `new`, `lint`, `run`, `write`, `build --ppl -o`, `verify`, `new --python`, `build -o`: as steps 2, 4 and 5 say (`11-01-SUMMARY.md`) |
| how the tools start elsewhere | step 1's table and `docs/tools.md`: `.\hpprime` in PowerShell, `hpprime` in cmd.exe, `./hpprime` on macOS and Linux, `python hpprime.py` anywhere |
| **exception** | `hpprime` is stored as mode `100644`, so `./hpprime` is refused on macOS and Linux; not run there, it follows from the mode. **Left as it is at the user's word on 2026-09-29.** `python hpprime.py`, which both pages give as the one to fall back on, is unaffected |
| when no Python starts | `AGENTS.md` §2: stop and send the person to step 1's Python row. Written; not exercised, since Python starts here |

## Criterion 3: `programs/`, and an update that keeps out of it

| | |
|---|---|
| `programs/` tracked | `programs/README.md` alone (`git ls-files programs`) |
| a program in it | ignored (`git check-ignore`), held by `programs_problems` in `test_docs.py` |
| `hpprime update` | 23 checks in `test_update.py`, which fail when its guards are stubbed out: `programs/` and `settings.local.json` never written, a clone refused, nothing deleted, a ZIP reaching outside refused |
| from GitHub | a copy of the tried download, `programs/RELOJ/` in it, brought to 7581215 by its own `hpprime update`: 4 changed, 1 added, `RELOJ.txt` unchanged by MD5, a second run with nothing to do |

## Criterion 4: an expert uses the tools directly

| | |
|---|---|
| the README | "Working with an AI" gives the download and the clone; "The tools" gives the clone and the five commands of the cycle, with the paths in `programs/` |
| procedures the tools need | none: every command runs on its own, and `docs/tools.md` documents each, `update` included |

## Requirements

| | |
|---|---|
| KIT-01 | complete: criterion 1 |
| KIT-09 | complete: criterion 4 |

## What only a person can confirm

That the tools start on macOS and Linux, from a clone or a download, was not
run; with the mode above, `./hpprime` would not. That the no-Python path
reads right to somebody whose Python is missing was not tried. The app the
tried session built ran on the emulator once compiled, by the user's
account; on a G2 it was not tried.

## Suite

`python tests/run_all.py`: **14,904 passed, 0 failed**, across 14 suites.
`hpprime docs --check`: 0 problems.
