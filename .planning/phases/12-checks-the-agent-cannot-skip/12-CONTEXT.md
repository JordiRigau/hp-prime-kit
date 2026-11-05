---
phase: 12-checks-the-agent-cannot-skip
created: 2026-09-29
requirements: [KIT-05, KIT-04]
status: decisions 1 to 3 from the user, proposals 4 to 9 approved by the user on 2026-09-29; for proposal 8, the third identical block lets the agent finish
---

# Phase 12 context: checks the agent cannot skip

## What this phase is

The gates of `AGENTS.md` §2 run in Claude Code without the agent having to
remember them, through hooks in the kit's own `.claude/settings.json`. Other
agents keep them as instructions (milestone 2, decision 3). How hooks behave
was read again for this phase, in `12-RESEARCH.md`.

The tried session of 11-03 went through every gate unasked. These checks are
for the session that does not.

## Decisions, from the user on 2026-09-29

1. **The end check looks at evidence, not at words.** It does not read the
   report for "it compiles" or "it works". Every PPL file the agent edited
   must have passed `lint` with no error and `run` **on its current
   content**, after its last edit. It does not depend on the language the
   agent speaks or how it phrases things.
2. **It blocks.** An agent that has not shown the evidence cannot finish:
   it is sent back with what is missing.
3. **Only PPL in `programs/`.** `tests/` holds PPL broken on purpose, and
   the kit's own examples are held by the suite; a person's programs are
   what these checks are for.

## Proposed, for approval

4. **After an edit, `lint` runs and Claude sees it.** A PostToolUse hook on
   `Edit|Write` for a `.txt` under `programs/`. An error comes back as exit
   2, which the research found does not block a PostToolUse, only puts the
   findings in front of Claude; a warning comes back as `additionalContext`.
   So "an error stops the agent until it is fixed" means: **it cannot
   finish while an edited program has an error**, since decision 1's check
   needs a clean `lint`. Blocking every other tool call as well would need a
   PreToolUse hook reading commands, which this phase does not add.
5. **What counts as `run`**: a `hpprime run` of that file on its current
   content that exited 0, so at least every `--call` answered. A run that
   stopped at something the interpreter does not cover does not count,
   since the exit code does not tell that apart from a wrong program.
6. **The evidence is a ledger the tools keep**: `hpprime lint` and
   `hpprime run` write, for each file in `programs/`, the SHA-1 of what they
   read and whether it passed, to `.claude/hpprime-gates.json`, which git
   ignores and `hpprime update` does not list. They write only when the kit's
   `.claude/settings.json` sets a variable naming that file, so an expert
   running the tools by hand writes nothing. The edit hook adds each file it
   sees edited; the end check reads the ledger and clears what it passed.
   Whether that variable reaches the agent's commands is research point 3;
   if it does not, the hooks read the agent's `hpprime` commands and their
   output instead.
7. **Every fact the report cites exists.** The end check also reads
   `last_assistant_message` for identifiers shaped like the documentation's,
   `topic.slug` with a topic the documentation has (`ppl`, `deploy`, ...),
   and blocks on one that names no fact. Identifiers are the same in every
   language. File names such as `ppl.md` are not identifiers, and tests hold
   those quiet. `AGENTS.md`'s own citations get a test (criterion 3), and so
   will the skills and agents of Phases 13 and 14.
8. **Out of a loop by itself.** The research found no limit on blocks in a
   row. If the end check blocks twice for the same missing evidence and
   nothing in the ledger has moved, the third time it lets the agent finish
   and tells the person what was never shown, rather than holding the
   session.
9. **The way out is the person's**: `"disableAllHooks": true` in their
   `.claude/settings.local.json`, Claude Code's own switch, which a project
   setting cannot override from below. The README says how; `AGENTS.md`
   says the agent never sets it.

## Plans

1. **12-01, lint after an edit, and the ledger**: `.claude/settings.json`
   with the edit hook in exec form (`python`,
   `${CLAUDE_PROJECT_DIR}/hpprime.py`, `hook`, ...); the ledger written by
   `lint` and `run`; the `.gitignore` line. Tests on hook payloads made in
   the test: an error in `programs/` reaches Claude, a warning goes as
   context, a file outside `programs/` is left alone.
2. **12-02, the end check**: evidence, identifiers, the loop guard, the
   switch in the README and `AGENTS.md`. Tests for what it must block and
   what it must let pass: a clean program lets it finish, an edit after the
   last run blocks, a cited fact that exists passes and one that does not
   blocks, a file name passes, the third identical block lets it finish.
3. **12-03, tried in a session**: a download with the hooks, opened by the
   person; research points 1 to 3 settled; a lint error planted by asking
   for it, a run left out, the switch turned on and off.

## What only the person can do

Opening the session that tries it, answering a trust prompt if one comes,
and turning the switch on in their own settings.
