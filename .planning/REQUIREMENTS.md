# Requirements: hp-prime-kit

**Defined:** 2026-09-11
**Core Value:** Everything the documentation says about the Prime states how it is known, and the agents built on it never claim more than it does.

## Milestone 1 requirements: the documentation

### Command reference (CMD)

- [x] **CMD-01**: The repository holds, as data, the list of every PPL statement, command, Home function, app function and app variable in HP's help, with the category the help files it under and its syntax. Names and syntax only: HP's prose stays HP's
- [x] **CMD-02**: That list is reconciled with firmware 2.4.15515: what was added or removed after the help dump (13217) is identified from a second source, and every name says where it came from
- [x] **CMD-03**: A command entry has one fixed, documented format: identifier, every form of its syntax, what it does in the kit's own words, its arguments and what it returns, at least one example with its result, the known edge cases and errors, and related entries
- [x] **CMD-04**: Every entry and every example states how it is known, as exactly one of: measured on a G2, run on the Virtual Calculator 2.4.15515, taken from HP's help, or unverified, with the evidence beside it
- [x] **CMD-05**: Entries are grouped the way HP's help groups them, and there is an index by name, both generated from the list
- [x] **CMD-06**: When a model is known to get a command wrong (`SIZE` of a matrix, `LEFT(s,0)`), its entry says what gets written instead and where that was seen
- [x] **CMD-07**: An entry says whether `hpprime run` implements the command, and where it does, the entry's examples also run through the interpreter in the tests
- [x] **CMD-08**: Every statement and program command has an entry (blocks, branches, loops, variables, functions, strings, drawing, matrices, input and output, app control)
- [x] **CMD-09**: Every Home function has an entry (math, lists, matrices, probability, statistics, integers and bits, finance and the rest HP files there)
- [x] **CMD-10**: Every app function a program can call has an entry
- [x] **CMD-11**: Every app variable a program can read or set has an entry, with the app it belongs to
- [x] **CMD-12**: Every name the list files as `variable` has an entry, 65 of them: Home's settings, the system's, and the plot and numeric settings every app shares. So does `GET`, whose kind the sources do not give

### Evidence on the Virtual Calculator (EVID)

- [x] **EVID-01**: `hpprime doctor`, `install`, `pull` and `compare` find the Connectivity Kit and the Virtual Calculator when their folders are localised (`Calculadoras` on a Spanish Connectivity Kit), and say which folder they used
- [x] **EVID-02**: The examples of a batch of entries run on the Virtual Calculator in one pass: one generated program, one keypress, and the results come back as a file
- [x] **EVID-03**: Answers that are not numbers come back too: strings, lists, matrices and errors
- [x] **EVID-04**: Each example keeps what the Virtual Calculator answered and the firmware it answered on; an answer that differs from HP's stated result is flagged, never silently replaced

### Platform facts (FACT)

- [x] **FACT-01**: Every fact in today's reference (ppl, interface, libraries, apps, micropython, formats, deploy) is carried over with its evidence, and a migration list says where each one went
- [x] **FACT-02**: Every fact has a stable identifier, one statement, how it is known, its firmware and its evidence, and it is stated in one place only
- [x] **FACT-03**: The hypotheses found false and the unverified items are entries too, with their own status, so "this is not a rule" is as easy to find as a rule
- [x] **FACT-04**: A fact about one command lives in that command's entry; a platform fact lives in its topic page (limits, screen, keyboard and touch, apps, Python, formats, deploy); each links to the other
- [x] **FACT-05**: The deploy page explains how to send a file to a physical calculator from the Connectivity Kit's content library, by hand, marked as done once, on 2026-09-09
- [x] **FACT-06**: The open questions a program runs into are measured on the Virtual Calculator, or say why they cannot be: every case `hpprime lint` warns on as `unverified`, and every open half of a fact in `ppl.md` that a program can meet. A case that is measured becomes a lint error with its evidence, or leaves the linter

### Reading, for people and models (READ)

- [x] **READ-01**: A guided path from zero: today's six steps rewritten on the new reference, linking to entries instead of restating them
- [x] **READ-02**: Every entry and topic page can be read on its own, without the rest loaded
- [x] **READ-03**: One index a model can load first, listing every entry and topic with its identifier and a one-line summary, within a size budget
- [x] **READ-04**: The documentation reads well from start to finish for a person: one format throughout, plain prose, no internal jargon
- [x] **READ-05**: The README presents the documentation first and the tools second
- [x] **READ-06**: Until milestone 2 replaces them, `AGENTS.md`, `SKILL.md` and the paste block point at the new documentation

### Tools that follow the documentation (TOOL)

- [x] **TOOL-01**: `hpprime lint` flags a call to a name that is neither on the list nor defined in the program, reading the list from the documentation's data rather than a copy. Two tests: a case it catches, and one it must stay quiet on
- [x] **TOOL-02**: Every lint message names the fact identifier its rule comes from, or says what it comes from instead
- [x] **TOOL-03**: The container reader's wrong pick, two candidate source records ending at the same offset, is reproduced in a test and fixed
- [x] **TOOL-04**: `hpprime run` never answers wrong in silence: an operator word it does not implement, such as `MOD` between its operands, and a builtin handed a type it does not handle either answer correctly or raise with a message, never a partial answer and never a Python traceback
- [x] **TOOL-05**: A batch on the Virtual Calculator never loses or replaces evidence in silence: a probe whose call already holds a different stored answer is refused unless replacing it is asked for; an answer the decoder cannot read costs its own row, not the batch, and the two measured infinities are read; a stored row carries the date its batch ran

### Checks that keep it honest (CHECK)

- [x] **CHECK-01**: Every identifier is unique, and every reference to one resolves
- [x] **CHECK-02**: Every example has been run, with a Virtual Calculator result on file or through the interpreter, or says why it cannot be
- [x] **CHECK-03**: The documentation never refers to the kit layer
- [x] **CHECK-04**: Every lint rule is tied to a fact, and every fact that can be caught from a PC has a rule or says why not
- [x] **CHECK-05**: Every relative link resolves

## Milestone 2 requirements: the agent kit

Defined with the user on 2026-09-26, in `milestone-2-CONTEXT.md`, and mapped
to Phases 11 to 16. KIT-01 reworded the same day, when the plugin gave way to
the kit's own folder.

- **KIT-01**: Downloading the kit and opening its folder is the whole install, and the agent picks it up without being told
- **KIT-02**: One entry point per job (new program, port, debug, screen, app, deploy, measure), each loading only the entries that job needs
- **KIT-03**: Specialised agents: one writes, another verifies and assumes nothing works until a command shows it does
- **KIT-04**: Agent reports cite the documentation's identifiers instead of paraphrasing, and a test checks that every citation resolves
- **KIT-05**: The checks run by themselves through Claude Code hooks
- **KIT-06**: A fixed hand-over for what only the human can do: what was built, the keys to press, the values to expect, what to report back
- **KIT-07**: A beginner can start from an idea, and the agent asks what it needs before writing any PPL
- **KIT-08**: A TermoHP-sized project can be built across sessions, with the plan and the state in files and each step checked before the next
- **KIT-09**: An expert can use the tools and the documentation directly, without the agent's procedures
- **KIT-10**: A block to paste into a chat with no file access, generated from the documentation
- **KIT-11**: The interpreter grows to cover what the kit's programs use, each builtin measured first

## Out of Scope

| Feature | Reason |
|---------|--------|
| CAS commands (436 lower-case names on the list) | The choice was PPL command by command, not the whole platform. They are on the list for the linter, not documented |
| How-to guides, explanation pages | Not chosen for milestone 1; the guided path and the reference cover it |
| A Spanish version | Not chosen; it doubles the maintenance of every page |
| Growing the interpreter in milestone 1 | The user's choice: it only learns the list of names, and grows in milestone 2 |
| Automating the send to a physical calculator | The user's choice: explain it, do not automate it |
| The checks enforced in agents other than Claude Code | They read the same `AGENTS.md`; the checks that block are Claude Code hooks |
| Copying HP's help text | It is HP's text; entries are written in the kit's words and cite it |
| Node.js, or becoming a GSD capability | The kit stays standard-library Python |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CMD-03 | Phase 1 | Complete |
| CMD-04 | Phase 1 | Complete |
| CMD-07 | Phase 1 | Complete |
| READ-02 | Phase 1 | Complete |
| CHECK-01 | Phase 1 | Complete |
| CHECK-03 | Phase 1 | Complete |
| CHECK-05 | Phase 1 | Complete |
| CMD-01 | Phase 2 | Complete |
| CMD-02 | Phase 2 | Complete |
| CMD-05 | Phase 2 | Complete |
| TOOL-01 | Phase 2 | Complete |
| EVID-01 | Phase 3 | Complete |
| EVID-02 | Phase 3 | Complete |
| EVID-03 | Phase 3 | Complete |
| EVID-04 | Phase 3 | Complete |
| TOOL-03 | Phase 3 | Complete |
| FACT-01 | Phase 4 | Complete |
| FACT-02 | Phase 4 | Complete |
| FACT-03 | Phase 4 | Complete |
| FACT-04 | Phase 4 | Complete |
| FACT-05 | Phase 4 | Complete |
| CMD-06 | Phase 4 | Complete |
| TOOL-02 | Phase 4 | Complete |
| CHECK-04 | Phases 4 and 10 | Complete: every rule is tied to a fact or says what it comes from (Phase 4); every fact names what catches it or why nothing on a PC can, and the nine checks that list decided on are written (10-01, 10-02) |
| CMD-08 | Phase 5 | Complete |
| CMD-09 | Phase 6 | Complete |
| CMD-10 | Phase 7 | Complete |
| CMD-11 | Phase 8 | Complete |
| CMD-12 | Phase 8.1 | Complete |
| FACT-06 | Phase 8.1 | Complete; ENDPROC and EXPORT with 3 and 5 measured in Phase 10, another app's settings left open and saying so |
| TOOL-04 | Phase 9.1 | Complete |
| TOOL-05 | Phase 9.1 | Complete |
| READ-01 | Phase 9 | Complete |
| READ-03 | Phase 9 | Complete |
| READ-04 | Phase 9 | Complete as far as a check holds it; whether it reads well is a reader's judgement |
| READ-05 | Phase 9 | Complete |
| READ-06 | Phase 9 | Complete |
| CHECK-02 | Phase 9 | Complete |

**Coverage:**
- Milestone 1 requirements: 38 total
- Mapped to phases: 38
- Complete: 38
- Unmapped: 0

| Requirement | Phase | Status |
|-------------|-------|--------|
| KIT-01 | Phase 11 | Pending |
| KIT-09 | Phase 11 | Pending |
| KIT-05 | Phase 12 | Pending |
| KIT-04 | Phase 12 | Pending |
| KIT-07 | Phase 13 | Pending |
| KIT-03 | Phase 13 | Pending |
| KIT-06 | Phase 13 | Pending |
| KIT-02 | Phases 13 and 14 | Pending |
| KIT-10 | Phase 14 | Pending |
| KIT-08 | Phase 15 | Pending |
| KIT-11 | Phases 13 to 16 | Pending |

**Coverage, milestone 2:**
- Requirements: 11 total
- Mapped to phases: 11
- Complete: 0

---
*Requirements defined: 2026-09-11*
*Last updated: 2026-09-24, when the roadmap was reordered: FACT-06 for Phase 8.1, TOOL-04 and TOOL-05 for the inserted Phase 9.1, and CHECK-04's open half given to Phase 10*
