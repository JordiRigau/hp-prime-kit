---
milestone: 2
created: 2026-09-26
status: approved by the user on 2026-09-26; revised and approved again the same day, decision 1 replaced
requirements: [KIT-01, KIT-02, KIT-03, KIT-04, KIT-05, KIT-06, KIT-07, KIT-08, KIT-09, KIT-10, KIT-11]
---

# Milestone 2 context: the agent kit

## What it is

A kit that works in the folder where it is opened, on top of milestone 1's
documentation: one procedure per job, a role that writes and another that
verifies, checks the agent cannot skip, and reports that cite the
documentation by identifier instead of restating it. The Python tools are
its gates.

**Done when**, in a fresh Claude Code session opened on the kit's folder:

1. The user brings an idea, answers the agent's questions, and never reads
   the PPL it writes; the program runs on their G2.
2. A new app the size of TermoHP -- an engine, several screens, a large data
   set -- is built from scratch across sessions and runs on the G2. Not
   TermoHP itself, so that knowing it cannot flatter the kit; which app is
   chosen when that phase starts.

What exists today: `AGENTS.md` at the root, which the Claude Code desktop app
loaded by itself as the project's instructions on 2026-09-26, with no
`CLAUDE.md` in the folder; and the paste block in `docs/ai/prompts.md`. No
agents, no hooks, no job procedures.

## Decisions, from the user on 2026-09-26

1. **The kit's folder is where you work.** Nothing is installed: the
   person downloads the repository as a ZIP from GitHub, or clones it, opens
   the folder in Claude Code or any agent that reads `AGENTS.md`, and says
   what they want. Their programs go in `programs/`, which git ignores, so
   nothing the kit ships and no update touches them. The beginner takes the
   ZIP; the expert clones and runs `hpprime` directly (KIT-09). One folder
   for both.

   *Replaces* the Claude Code plugin chosen earlier the same day. The user's
   reasons: it tied the kit to Claude Code; installing went through
   concepts a beginner does not know (a marketplace, `/plugin`); its files
   lived in a cache nobody opens; and it carried machinery and four open
   points for what it gave.

2. **Updating.** A clone updates with `git pull`. A ZIP updates with
   `hpprime update`, which downloads the latest version from GitHub and
   replaces the kit's files, never `programs/`. Standard library only.
   The user's choice, over documenting a re-download by hand.

3. **Every agent reads the same contract; Claude Code also enforces it.**
   `AGENTS.md` and the procedures it links are plain Markdown any agent can
   follow. The checks that block are Claude Code hooks in the kit's
   `.claude/settings.json`, so elsewhere they are instructions, not gates,
   and the README says so. *Replaces* "the kit targets Claude Code only".

4. **The beginner's path first**: from an idea to a program running on the
   calculator. It exercises everything the larger project needs, on the
   shortest route.
5. **The checks block.** After an edit to a PPL file, `lint` runs, and an
   error stops the agent until it is fixed. When the agent finishes, its
   report is checked for claims -- "it compiles", "it works on the
   calculator", "it is installed" -- that no command's output backs.
6. **Closed by a new app**, comparable to TermoHP, built from scratch and
   tested on the G2.
7. **The user plays the beginner**, without reading the PPL. They know PPL,
   so the test is only as good as their not looking: the agent's questions
   and its hand-over are what they go by.

## What decision 1 undoes

Plan 11-01, done and never committed, undone on 2026-09-26: `.claude-plugin/`
gone; `skills/hp-prime/SKILL.md` gone, and the root `SKILL.md` it was moved
from not restored, since its one job was to point Claude Code at the contract
and Claude Code reads `AGENTS.md` itself; `plugin_problems` out of
`tests/test_docs.py`; the README and `docs/ai/prompts.md` back to their
committed text less `SKILL.md`. Phase 11 rewrites the README's install
section.
`11-RESEARCH.md` stays as the record of what was read: what it says about
hooks (exit 2 blocks, `Stop`, exec form) is what Phase 12 builds on, for
hooks in `.claude/settings.json` instead of a plugin's `hooks/hooks.json`.

## Proposed phases

Numbered after milestone 1's, in the order the decisions give.

| Phase | Goal | Requirements |
|---|---|---|
| 11. The working folder | Downloaded and opened, nothing installed: a fresh session picks up the contract, the tools run from the folder, a person's programs stay in `programs/` and survive an update; an expert uses the tools without the procedures | KIT-01, KIT-09 |
| 12. Checks the agent cannot skip | `lint` after every PPL edit, blocking on an error; the final report checked for claims no command backs; every identifier a report cites resolves | KIT-05, KIT-04 |
| 13. From an idea to the calculator | The new-program job: questions before any PPL, a writer and a verifier, the gates, and a fixed hand-over of what only the person can do. Closed by the user bringing an idea and not reading the PPL | KIT-07, KIT-03, KIT-06, KIT-02 in part |
| 14. The other jobs | Port, debug, screen, app, deploy, measure, each a short procedure loading only what it needs; the paste block generated from the documentation | KIT-02, KIT-10 |
| 15. Projects across sessions | The plan and the state in files, each step checked before the next, for a project too big for one session | KIT-08 |
| 16. A new app, from scratch | The acceptance test of decision 6, on the G2; the interpreter's growth, which each phase records, closed | KIT-11 |

**KIT-01 is reworded**: downloading the kit and opening its folder is the
whole install, and the agent picks it up without being told.

**KIT-11 runs through all of them**: the interpreter learns what the kit's
own programs use, each builtin measured first, as milestone 1 did with
`MOD` and `NTHROOT`.

## Risks, each with what would settle it

**Python on a beginner's Windows.** `python` can be the Microsoft Store
alias, which opens the Store instead of running anything; `py` and
`python3` differ by machine. The tools and the hooks both need one. Phase 11
finds how the tools start everywhere the kit claims to run, and what the
agent does first when none does.

**Hooks from a downloaded folder.** Whether Claude Code asks before running
the hooks of a folder it has just been given, and what the person sees, is
settled by trying it in Phase 11, before Phase 12 relies on them.

**`AGENTS.md` without `CLAUDE.md`.** Seen once, in the desktop app. Whether
every Claude Code the kit claims loads it the same way is settled in Phase
11; if one does not, a one-line `CLAUDE.md` that imports it, and whether
that loads it twice where both are read.

**A blocking hook can trap the agent.** A false alarm that blocks is worse
than one that warns. `lint` errors are only what a calculator refused, which
limits this; the claims check is a heuristic and needs its own quiet cases,
and a way out that the person, not the agent, controls.

**An update must not lose a program.** `hpprime update` replaces files in
the folder the person works in. A test holds that it never writes inside
`programs/`, and it refuses when the folder is a clone.

**The beginner test measures the user not looking.** Decision 7 accepts
that. The hand-over is where it shows: if they need to read the PPL to know
what to press, the test failed.

## Constraints that do not change

Everything in the repository in English; the agent speaks the user's
language. Python 3.7+, standard library only, no install step. One fact, one
home: a procedure cites the documentation, it does not restate it. Nothing
is pushed without asking, and the main email never appears in a commit.
