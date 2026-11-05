---
phase: 12-checks-the-agent-cannot-skip
plan: 01
status: complete
completed: 2026-09-29
key_files:
  - hpkit/gates.py
  - hpkit/lint.py
  - hpkit/interp.py
  - hpkit/cli.py
  - .claude/settings.json
  - .gitignore
  - tests/test_gates.py
  - tests/run_all.py
  - docs/tools.md
---

# Plan 01 summary: lint after an edit, and the ledger

## What was built

- **`hpkit/gates.py`**: what counts as a program (a `.txt` under
  `programs/` with a `BEGIN`); the ledger `.claude/hpprime-gates.json`, per
  file the SHA-1 each gate last read and whether it passed, and the files
  edited; `record()`, which writes only with `HPPRIME_GATES=1`; and
  `post_edit()`, the hook: an error goes to stderr with exit 2, warnings to
  `additionalContext`, a clean file says nothing, anything else is left
  alone. Output written as UTF-8.
- **`lint` and `run` record**: `lint` per file, by that file's own errors
  and whether it reads as UTF-8; `run` passed only when the file loaded, at
  least one `--call` was given and every one answered. `interp.cli` now
  wraps the old body, `_run`, so the record sees its exit code.
- **`hpprime hook post-edit`**, and its section in `docs/tools.md`.
- **`.claude/settings.json`**: `HPPRIME_GATES=1`, and the hook for
  `Edit|Write|MultiEdit` in exec form, `python` with
  `${CLAUDE_PROJECT_DIR}/hpprime.py hook post-edit`, 60 seconds.
  **`.gitignore`**: the ledger, its temporary file, and
  `.claude/settings.local.json`; `.claude/settings.json` ships.
- **`tests/test_gates.py`**, 24 checks, the fifteenth suite. With
  `enabled()` stubbed to always answer yes, one failed; with `is_ppl()` stubbed
  the same way, one failed.

## Settled by trying, in this session

- **Research point 3**: `env` in `.claude/settings.json`, written mid-
  session, reached the next Bash command and Python started from it.
- **Research point 2**: with the hook in place, writing
  `programs/HOOKTEST/HOOKTEST.txt` with an `ENDIF` brought back, as a
  "PostToolUse:Write hook blocking error", both findings with rule and
  fact. So `python` starts in exec form here, the Microsoft Store's alias
  included. After the fix the hook said nothing; the ledger held `lint`
  passed on the fixed content's SHA-1, and a `hpprime run ... --call
  "HKDOUBLE(3)"` typed in Bash added `run` passed on the same SHA-1. The
  trial program and the ledger were removed afterwards.

## Deviations

None.

## Results

```
test_gates.py            24 passed, 0 failed
suite                    14,928 passed, 0 failed, 15 suites
hpprime docs --check     0 problem(s)
```
