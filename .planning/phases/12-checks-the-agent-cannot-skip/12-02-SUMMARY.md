---
phase: 12-checks-the-agent-cannot-skip
plan: 02
status: complete
completed: 2026-09-29
key_files:
  - hpkit/gates.py
  - .claude/settings.json
  - tests/test_gates.py
  - AGENTS.md
  - README.md
  - docs/tools.md
---

# Plan 02 summary: the end check

## What was built

- **`stop(event)` in `hpkit/gates.py`**, with `missing()`, `cited()`,
  `facts()` and `unknown_citations()`:
  - each program edited since the check last passed needs, on its current
    SHA-1, a passed `lint` and a passed `run`; what is missing is named with
    the command that supplies it; a program that is gone, or no longer PPL,
    leaves the list;
  - identifiers in the last message, in backticks or as a link's text,
    shaped `topic.slug` with one of the seven topics of `docs/topics/` and a
    slug that is neither a file's extension nor a domain's (`ppl.md`,
    `micropython.org`), must be one of the 122 anchors there;
  - nothing missing: the list and the guard are cleared, exit 0, silent;
  - something missing: exit 2 with the list, the commands, a line for a
    program the interpreter cannot run (say so in the report), and that
    switching off is the person's;
  - the guard: the problems and the ledger entries behind them are hashed;
    the same hash a third time running exits 0 with a `systemMessage` to the
    person naming what was never shown, and clears the list.
- **`hpprime hook stop`**, and the `Stop` hook in `.claude/settings.json`,
  exec form like the edit hook.
- **The switch**, `"disableAllHooks": true` in `.claude/settings.local.json`,
  in the README's "Working with an AI"; `AGENTS.md` §2 says what the hooks
  hold the agent to and that switching them off is never its decision;
  `docs/tools.md`'s `hook` gives both hooks.
- **17 new checks in `tests/test_gates.py`**, 41 in all: the plan's list,
  plus the lint the edit hook ran counting as the lint, and every fact
  `AGENTS.md` cites existing (10 of 10). With `GUARD` raised to 99, 3
  failed; with `unknown_citations` answering nothing, 1; with `digest`
  answering the same for every content, 2.

## Tried by hand

`hpprime hook stop` fed a message citing `ppl.one-based` and
`ppl.inventado`: exit 2, naming only `ppl.inventado`. Fed `{}` with no
ledger: exit 0, and no ledger written.

## Seen live, in this session

The first turn to end with the `Stop` hook in place was sent back by it:
its report to the user quoted, in backticks, the invented identifier of the
trial above, and the hook named it as no fact, with exit 2 and the text in
front of the agent. So Claude Code honours the kit's `Stop` hook here. It
also shows the check's reach: a report that quotes a non-fact as an example
is sent back like one that cites it. That stays as built; a report can name
such an example without backticks.

## Deviations

- `micropython.org` would have read as a citation of a fact that does not
  exist; domains joined the extensions that make a slug no slug, and a test
  holds it.

## Results

```
test_gates.py            41 passed, 0 failed
suite                    14,947 passed, 0 failed, 15 suites
hpprime docs --check     0 problem(s)
```
