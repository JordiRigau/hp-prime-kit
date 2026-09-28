# hp-prime-kit

## What This Is

Two layers in one repository, built in this order:

1. **The documentation.** A reference for programming the HP Prime in PPL,
   command by command, plus the platform topics a program runs into: the
   limits that break compilation, the screen and keyboard, apps, Python, the
   file formats, and getting code onto the calculator. Every entry says how it
   is known: measured on a calculator, run on the Virtual Calculator, taken
   from HP's own help, or not verified. It is written for models and people
   alike. Each entry stands on its own and has an identifier, so a model can
   load only what it needs, and the whole still reads well from start to
   finish.
2. **The agent kit**, built on that documentation. It works in the kit's own
   folder, opened in Claude Code or another agent, with nothing installed,
   and gives the agent one procedure per job, specialised roles, and checks
   it cannot skip. It cites the documentation by identifier instead of
   restating it. The Python tools (lint, run, write, install, compare) sit
   between the two layers: they make the documentation checkable, and they are
   the gates the agent works through.

In the user's words: "documentación para LLMs", "para quien no sabe, pero
también para los que saben".

## Core Value

Everything the documentation says about the Prime states how it is known, and
the agents built on it never claim more than it does.

**Done when:**

- **Milestone 1, the documentation:** every PPL command has an entry with its
  syntax, its behaviour, an example and its status; every fact measured so far
  is there with an identifier; and `hpprime lint` flags a command that does
  not exist.
- **Milestone 2, the agent kit:** with a fresh Claude Code session opened
  on the kit's folder, somebody who has never programmed a Prime has their program
  working on the calculator without reading any PPL, and an app the size of
  TermoHP (an engine, several screens, a large data set) is built from
  scratch.

## Requirements

### Validated

Inferred from the existing repository, and added phase by phase.

- ✓ `hpprime lint`: thirteen rules, each naming the fact it comes from and that fact's label, and an error only as far as the measurement reaches — existing, narrowed on 2026-09-22 (9704074) after a report of false alarms in issue #1, and its unverified cases measured in Phase 8.1
- ✓ An entry for every variable of Home and the system, and for `GET`; the open questions a program runs into measured, and `hpprime examples --compile` to ask whether a program compiles — Phase 8.1
- ✓ An entry for every name the list documents, 706 of 706: every statement, command, Home function, app function, app variable and variable, and `GET` — Phases 5 to 8.1, closed with Phase 8 on 2026-09-25
- ✓ Every fact names what catches it from a PC -- a lint rule, another command and its test -- or why nothing can; `hpprime lint` has twenty rules, eighteen tied to a fact — Phase 10
- ✓ A program reaches another app's variables and functions with the app's name in front, `Statistics_1Var.MeanX`, measured in source and through `EXPR`, and `hpprime run` calls it not covered rather than an error — Phase 8
- ✓ `hpprime run`: runs the real PPL file on the PC, and raises instead of inventing a result — existing
- ✓ `hpprime write` / `read` / `verify`: the `.hpprgm` container in both directions — existing
- ✓ `hpprime build` / `verify`: `.hpappdir` apps, PPL and Python — existing
- ✓ `hpprime install` / `pull` / `emu`: the Virtual Calculator's folder as a real mailbox, and throwaway calculators — existing
- ✓ `hpprime compare`: the same calls on the PC and on the calculator, side by side — existing
- ✓ `hpprime matrix`, `doctor`, `new`, `templates` — existing
- ✓ Measured reference for PPL, interface, libraries, apps, MicroPython, formats and deploy, every fact with its evidence or marked Unverified — existing
- ✓ HP's own help examples as test data for the interpreter (`tests/hp_examples.txt`) — existing
- ✓ Run on a real G2: a program built from the shipped template, and a PPL app built by `hpprime build --ppl` — existing
- ✓ One documented format for command entries, facts and examples, held by `hpprime docs` and `tests/test_reference.py` in both directions — Phase 1
- ✓ Examples of the commands the interpreter implements run through it in the tests; a different answer fails, an uncovered one is a note — Phase 1
- ✓ The group pages and the index are generated from the entries, and a stale one fails the tests — Phase 1
- ✓ The documentation does not refer to the kit, and a test checks it — Phase 1
- ✓ The list of every PPL name as data: 1,173 names from HP's help of 13217, the 2.1.14181 export and the release notes to 2.4.15515, each saying where it came from — Phase 2
- ✓ An index by name and one by HP's grouping, over every name that gets an entry, generated from the list — Phase 2
- ✓ `hpprime lint` flags a call to a name that is neither PPL's nor the program's (`unknown-name`): a warning alone, an error with `--set` — Phase 2
- ✓ The tools find a Connectivity Kit and a Virtual Calculator whose folders are localised, and say which folder they used — Phase 3
- ✓ The examples of a batch of entries run on the Virtual Calculator in one pass, every kind of answer comes back, and each is stored with its firmware — Phase 3
- ✓ The container reader's wrong pick between two source records ending at the same offset, reproduced in a test and fixed — Phase 3
- ✓ The platform topics carried over in the fixed format, none lost: every fact with an identifier, one statement, how it is known and its evidence, the refuted hypotheses and the unverified items included — Phase 4
- ✓ Every lint message names the fact it comes from, and the deploy page explains the send from the Connectivity Kit by hand, marked as done once — Phase 4
- ✓ An entry for every statement and program command, every Home function and every app function, each example with a Virtual Calculator result or a reason — Phases 5 to 7
- ✓ The guided path linking its facts, `docs/llms.txt` within its budget, a README that leads with the documentation, and no example left unrun — Phase 9
- ✓ `hpprime run` answers as the calculator does or says it does not cover the case, never a partial answer or a traceback; `MOD` and `NTHROOT` written between their operands — Phase 9.1
- ✓ A batch on the emulator never replaces a stored row or loses a batch to one cell without saying so, and dates its rows the day they ran — Phase 9.1

### Active: Milestone 1, the documentation

Numbered in `REQUIREMENTS.md`.

- [ ] Every example is run on the Virtual Calculator 2.4.15515, or says why it cannot be
- [ ] A person can learn from zero with a guided path and look anything up in the reference
- [ ] A model can load one entry or one topic without the rest, from an index

### Active: Milestone 2, the agent kit, built on the documentation

Defined with the user and approved on 2026-09-26, in
`milestone-2-CONTEXT.md`, and revised the same day: the kit's own folder as
the place to work, nothing installed; the beginner's path first,
checks that block, the user playing the beginner without reading the PPL,
and a new app the size of TermoHP to close it. Phases 11 to 16.

- [ ] Downloading the kit and opening its folder is the whole install, and the agent picks it up without being told
- [ ] One entry point per job (new program, port, debug, screen, app, deploy, measure), each a short procedure that loads only the entries that job needs
- [ ] Specialised agents: one writes, another verifies and assumes nothing works until a command shows it does
- [ ] Agent reports and lint messages cite the documentation's identifiers instead of paraphrasing, and a test checks that every citation resolves
- [ ] The checks run by themselves through Claude Code hooks, not only when the agent remembers them
- [ ] A fixed hand-over for what only the human can do: what was built, the exact keys to press, the values to expect, and what to report back
- [ ] A beginner can start from an idea, and the agent asks what it needs before writing any PPL
- [ ] A project too big for one session, TermoHP's size, can be built across sessions: the plan and the state live in files, and each step is checked before the next one starts
- [ ] An expert can use the tools and the documentation directly, without going through the agent's procedures
- [ ] A block to paste into a chat with no file access, generated from the documentation
- [ ] The interpreter grows to cover what the kit's programs use, each builtin measured first

### Out of Scope

- CAS commands — the choice was PPL command by command, not the whole platform. They are on the list for the linter, and can be a later milestone
- How-to guides, explanation pages and a Spanish version — not chosen for milestone 1; the guided path and the reference cover what a person needs, and a second language doubles the maintenance of every page
- Growing the interpreter in milestone 1 — the user's choice: it only learns the list of names; it grows in milestone 2. One exception, chosen on 2026-09-24: `MOD` and `NTHROOT` as operators, the forms the calculator accepts, where it had accepted the one it refuses
- Automating the keypresses on the emulator — the user's choice for Phase 3: the user presses them, a few batches in all
- Two repositories — one repository with two layers. The documentation can be split out later with `git subtree split`, history included, if it gains contributors of its own
- Rewriting the Python tools — they are validated; they change only where the new structure needs them to
- The checks enforced in agents other than Claude Code — Codex, Cursor, Copilot and the rest read the same `AGENTS.md` and procedures, but the checks that block are Claude Code hooks. Until 2026-09-26 the kit targeted Claude Code only
- Automating the send to a physical calculator — the user's decision: explain it, do not automate it. It has worked once, after five attempts
- A Node.js installer or dependency — the kit is Python 3.7+ standard library only, and this machine has no Node
- Becoming a GSD capability — it would need Node and GSD installed; the kit learns from GSD instead of depending on it. Can be revisited
- Drawing the interface on the PC, and running MicroPython on the PC — unchanged from today
- Project-specific content such as TermoHP — house rule: examples stay generic. A TermoHP-sized app is a test of the kit, built outside it

## Context

- **Origin.** The kit came out of building TermoHP, a thermodynamic-tables app
  for the G2, with an AI agent doing the coding.
- **The problem it answers.** There is little public PPL for a model to learn
  from, what exists contradicts itself across firmware versions and older HP
  calculators, and the compiler says only "syntax error" and a line number.
  Models answer with `ENDIF`, 0-based indexing and commands that do not exist.
- **The shape before the redo.** A human-oriented tutorial (a six-step guided
  path in plain prose) plus a Python CLI, with `AGENTS.md`, `SKILL.md` and
  `docs/ai/prompts.md` as the AI layer. It documented only what was measured
  and the traps, not the command set. The user's judgement on 2026-09-11: that
  shape did not capture what the kit is for, and the documentation has to come
  first.
- **The size of the command set.** `docs/commands/names.tsv` holds 1,173
  names: 706 get an entry (14 statements, 98 commands, 177 functions, 179 app
  functions, 172 app variables, 65 variables, and `GET`, of unknown kind); the
  436 CAS names, 7 keywords and 24 operators are on it for the linter and are
  not documented one by one. 1,116 come from HP's help of 13217, 50 only from
  the 2.1.14181 export, and 7 only from the release notes up to 2.4.15515.
- **Sources for the command reference.** HP's built-in help (the `[Help]` key)
  and its Command Tree dump; the 2.1.14181 export of the command tree; the
  release notes of every firmware to 2.4.15515; HP's Programming Reference and
  User Guide; and programs that already run. The help covers edges unevenly
  (`RIGHT` and `MID` say nothing about theirs) and says nothing about the
  limits that break compilation, which is why the kit measures.
- **This machine.** Connectivity Kit 2.4 with a Spanish interface: its folders
  are `Calculadoras`, `Contenido` and so on, and `hpprime doctor` has found
  them since Phase 3 taught the tools the localised names. The Virtual Calculator
  2.4 r15515, the same build as the reference G2, has been installed since
  2026-09-11; its calculators folder is `Calculators`, in English, although its
  other folders are Spanish, and the kit finds it. A program copied into that
  folder has to be compiled once, with the editor's Check, before its name
  works on Home (measured on 2026-09-06).
- **What to learn from.** GSD Core (open-gsd/gsd-core): documentation split
  into tutorials, how-to guides, reference and explanation; facts as one-line
  predicates that are cited, not paraphrased; thin entry points that load
  references only when a step needs them; specialised agents with a fresh
  context each; claim provenance tags; gates decided by external signals
  rather than the model's confidence; formal human checkpoints; questioning
  before building; state kept in files so work survives across sessions.
- **Findings not yet written into the documentation.**
  - The container reader could pick the wrong source record when two
    candidates end at the same offset (`program._source_record`), seen in
    TermoHP with a 65,515-character source. Already fixed on 2026-09-10
    (cd14080), with a test over the five sizes that used to trip it; this
    document said otherwise until Phase 3 looked.
  - What the calculator does when a program exports a name an app already
    has, such as `AREA`, has not been measured. The starter no longer does
    it: it exports `CIRCAREA` since 2026-09-23. The measurement is on Phase
    8.1's list.
- **Reference firmware.** G2, 2.4 revision 15515. There are no G1 measurements.

## Constraints

- **Direction**: the documentation never depends on the kit; the kit depends on the documentation — so the documentation stands on its own and can be split out
- **Evidence**: every entry states how it is known: measured on a G2 (what was run, on which firmware, what was seen), run on the Virtual Calculator, taken from HP's help, or unverified — the whole value is that it can be trusted
- **Own words**: entries are written in the kit's words, and HP's help is cited, not copied, with at most a short quotation — it is HP's text and the repository is MIT. HP's sources are read outside the repository
- **Tech stack**: Python 3.7+, standard library only, no install step for the tools — anybody with a fresh clone or the ZIP and a stock Python has to be able to run everything
- **Agent**: Claude Code for the kit — skills, agents and hooks in its native format
- **Language**: English in the repository (code, docs, commits); the agent answers the user in the user's language
- **Platforms**: Windows first, because that is where the emulator and the Connectivity Kit run; macOS and Linux for everything that does not need them
- **One fact, one home**: each fact is stated once and cited everywhere else
- **Git**: `main` is the published branch, and nothing is pushed to it without asking. The redo was built on a local branch, `redo`, which became `main` on 2026-09-14

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Documentation first, then the agent kit built on it | The user's correction on 2026-09-11 | ✓ Good: milestone 1 closed on 2026-09-25, and milestone 2 is built on it |
| The kit's folder is where you work: downloaded as a ZIP or cloned, opened, nothing installed; a person's programs in `programs/` | The user's choice on 2026-09-26, replacing a Claude Code plugin chosen earlier that day: the plugin tied the kit to Claude Code, installed through concepts a beginner does not know, kept its files in a cache nobody opens, and carried machinery and open points for what it gave | — Pending |
| A ZIP updates with `hpprime update`, which never writes inside `programs/`; a clone with `git pull` | The user's choice on 2026-09-26, over re-downloading by hand | — Pending |
| The beginner's path first | The user's choice on 2026-09-26: it exercises what the large project needs, on the shortest route | — Pending |
| The checks block: a lint error stops the agent, and claims no command backs are caught | The user's choice on 2026-09-26, over blocking only lint errors or only reporting | — Pending |
| Milestone 2 closes on a new app the size of TermoHP, not TermoHP | The user's choice on 2026-09-26, so that knowing TermoHP cannot flatter the kit | — Pending |
| The user plays the beginner, without reading the PPL | The user's choice on 2026-09-26, over a person who knows no PPL | — Pending |
| One repository, two layers | Chosen on 2026-09-11: a fact, its lint rule and its test change together; one clone gives everything; the documentation can be split out later | ✓ Good (Phases 1-2) |
| The documentation covers every PPL command, plus the platform topics | The user's choice on 2026-09-11; with the full list, the linter can flag invented commands | ✓ Good: the list exists and lint reads it (Phase 2) |
| The documentation is written for models and people alike | The user's choice on 2026-09-11 | — Pending |
| One Markdown file per command, with the group pages and the index generated | The user's choice for Phase 1 | ✓ Good (Phase 1) |
| The mixed entry: a summary, fixed fields, labelled examples, a short behaviour section | The user's choice for Phase 1, from three mockups | ✓ Good (Phase 1) |
| Examples are verified on the Virtual Calculator 2.4.15515 | The user's choice on 2026-09-11: closer to the hardware than the kit's own interpreter. Installed on 2026-09-11 | — Pending |
| The user presses the keys on the emulator; the kit prints them, waits and collects | The user's choice for Phase 3: the measured path, a few batches in all | — Pending |
| Examples run on a throwaway calculator, Prime_1, reset before each batch | The user's choice for Phase 3: a known state for every result, and the user's own calculator untouched. The name is the emulator's, not ours: the second window it opens is always Prime_1, and never a calculator called anything else | — Pending |
| An example the emulator confirms goes from `HP help` to `emulator`; a disagreement is flagged, never replaced | The user's choice for Phase 3 | — Pending |
| The interpreter does not grow in milestone 1; it only learns the list of names | The user's choice on 2026-09-11 | ✓ Good: lint reads the list (Phase 2) |
| For people, milestone 1 has the guided path and the reference, nothing more | The user's choice on 2026-09-11 | — Pending |
| App variables get entries, in their own phase after the app functions | The user's choice on 2026-09-11 | ✓ Good: 172 of 172, the last 42 in two unattended batches (08-05) |
| The list of names comes from HP's own sources, rebuilt by a maintainer's script; the sources stay outside the repository | Downloaded on 2026-09-11 with the user's permission | ✓ Good (Phase 2) |
| CAS names are on the list, known to the linter, not documented | CAS is out of scope, but a program may call it | ✓ Good (Phase 2) |
| `unknown-name` is a warning for a file alone and an error with `--set` | The user's choice for Phase 2: a file may call another program's export | ✓ Good (Phase 2) |
| The linter compares the calculator's names without regard to case | Never flag a spelling the calculator might accept; the calculator's own behaviour is not measured | ✓ Good: the calculator reads `alog(2)` as `ALOG(2)`, `ppl.names-ignore-case` (08.1-01) |
| Keep the measured facts and the Python tools; redo the structure, the docs and the entry points | They are validated on hardware; the problem is the shape, not the content | ✓ Good so far |
| The redo happens on a local branch `redo` | The user's choice on 2026-09-11: `main` stays intact until the redo is ready | ✓ Good: `main` moved to it by fast-forward on 2026-09-14 |
| Every agent reads the same `AGENTS.md`; Claude Code also enforces it with hooks | The user's choice on 2026-09-26, replacing "Claude Code only" (2026-09-11): being tied to one tool was one of the plugin's faults | — Pending |
| The send to a physical calculator is explained, not automated | The user's choice on 2026-09-11; one run, five attempts | — Pending |
| Done means: every PPL command documented; then a beginner succeeds end to end and a TermoHP-sized app is built from scratch | The user's choices on 2026-09-11 | — Pending |
| Learn from GSD, do not depend on it | No Node on this machine, and the kit stays standard-library only | ✓ Good so far |
| Build the redo with GSD's method: `.planning/` with PROJECT, REQUIREMENTS, ROADMAP and STATE, one phase at a time | The user asked to use GSD to capture what they want | ✓ Good: it surfaced the "documentation first" correction |
| The 65 variables and `GET` get their own phase, 8.1, inside milestone 1 | The user's choice on 2026-09-16, when Phase 9's questioning found that no phase had taken them | — Pending |
| Phase 9 runs ahead of Phases 8 and 8.1 | The user's choice on 2026-09-16: what it builds is generated from the entries or links to them | — Pending |
| The index a model loads first is one file with a link on every line | The user's choice on 2026-09-16, over the same list without links and over a map with an index per group | — Pending |
| The guided path keeps its six steps, rewritten to link rather than restate | The user's choice on 2026-09-16, over a shorter path and over a new structure | — Pending |
| Planning language comes out of the documentation, and a check keeps it out | The user's choice on 2026-09-16; harness, batch and probe are explained once instead | ✓ Good: 132 rewrites, and the check refuses "phase" and "this kit" (09-02) |
| The model index is `docs/llms.txt`, generated, with a budget of 100,000 bytes the check enforces | Approved with Phase 9's context on 2026-09-16: inside `docs/` so the documentation can still be split out, and loaded whole, so its size is watched | ✓ Good: 74,939 bytes for 598 entries and 117 facts (09-01) |
| An example nobody has run fails the check | Approved on 2026-09-16 (CHECK-02): no stored answer is allowed only for *no value*, a G2 measurement, or the interpreter | ✓ Good: it reports nothing today, and holds that (09-01) |
| The starter exports `CIRCAREA`, not `AREA` | The user's choice on 2026-09-23, over measuring what Home does with the collision first: `AREA` is the Function app's, and a reset calculator has that app active | ✓ Good: the guided path promises nothing unmeasured (09-03) |
| Phase 9.1 before any more batches: the tools stop answering wrong and losing evidence in silence | The user's choice on 2026-09-24, from a review of the plan: `hpprime run` answered 9 to `9 MOD 4 + 100` with the linter clean, and the harness could replace a stored row or lose a batch to one cell | ✓ Good: every case refused or answered as measured, and the harness keeps what it cannot settle (Phase 9.1) |
| The interpreter matches the calculator on `MOD` and `NTHROOT`, and refuses what is not measured about them | The user's choice for Phase 9.1 on 2026-09-24, over both forms raising: a deliberate exception to milestone 1's rule that the interpreter does not grow, because it corrected a form accepted wrongly | ✓ Good: `9 MOD 4 + 100` is refused until the binding is measured (Phase 9.1) |
| Phase 8.1 ahead of the rest of Phase 8 | The user's choice on 2026-09-24: the variables of Home and the system reach every program, the 42 app variables left reach six apps | ✓ Good: nothing in 8.1 waited for Phase 8 |
| Probe `App.Variable` before seven rounds with the app selected by hand | The user's choice on 2026-09-25 | ✓ Good: it works, in source and through `EXPR`, so the last 42 took two batches nobody had to prepare (08-05) |
| Statistics measured with data and their `Do` command, not only read on a reset calculator | The user's choice on 2026-09-25 | ✓ Good: every value matched the hand computation, and the quartiles showed their method (08-05) |
| The open questions a program runs into are measured in Phase 8.1's sessions | The user's choice on 2026-09-24: each one measured turns a lint warning into an error, or removes it | ✓ Good: `L(0)` is the last element, `x = 2;` assigns nothing, 9 locals do not compile, `Check` can name the first bad line (08.1) |
| Compile questions answered by small programs, two controls and `Check` | The user's choice for Phase 8.1 on 2026-09-24, over the person reading out each `Check` | ✓ Good: both controls right on the first complete run; `hpprime examples --compile` (08.1-04) |
| CHECK-04's open half gets Phase 10, which closes milestone 1 | The user's choice on 2026-09-24: no phase owned it, so the milestone could not close | ✓ Good: 122 facts each with a line, 9 checks written, and they found the guided path teaching a drawing that vanishes (10-02) |
| Any `hpprime` command counts as catching a fact, and the list lives with the linter | The user's choices for Phase 10 on 2026-09-25 | ✓ Good: 45 answers are commands, each with its test; the fact format and `docs/llms.txt` did not change |
| `--relabel` moves `unverified` to `emulator` too, never `G2` | Approved on 2026-09-16: a label weaker than the measurement understates it as surely as a stronger one overstates it | ✓ Good: 21 examples moved, and a fact measured in Phase 5 and never written down was settled with them (09-01) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? → Move to Out of Scope with the reason
2. Requirements validated? → Move to Validated with a phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update it if it has drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check: still the right priority?
3. Audit Out of Scope: are the reasons still valid?
4. Update Context with the current state

---
*Last updated: 2026-09-26, when milestone 2 was defined and approved*
