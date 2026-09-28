# Roadmap: hp-prime-kit

## Overview

Milestone 1 builds the documentation. First comes the format, with the tests
that hold every entry to it. Then three foundations: the list of every PPL
name, a way to run examples on the Virtual Calculator, and the facts measured
so far carried over. With those in place the entries are written group by
group (statements and program commands, Home functions, app functions, app
variables, then the variables of Home and the system), every example run on
the emulator, with the guided path, the index for models and the README on
top. Reordered on 2026-09-24: before any more batches, the tools stop giving
wrong answers and losing evidence in silence; then the variables of Home and
the system, with the open questions every program runs into, come ahead of
the last app variables; and the milestone closes by holding the linter to the
facts. Milestone 2, the agent kit, builds on it: the kit's own folder as the place to
work, nothing installed; the beginner's path first, checks that block, and a new app the size of TermoHP
to close it, as defined in `milestone-2-CONTEXT.md`, approved and revised on
2026-09-26.

## Milestones

- ✅ **Milestone 1: the documentation** — Phases 1-10 (completed 2026-09-25)
- 🚧 **Milestone 2: the agent kit** — Phases 11-16 (in progress; KIT-01 to KIT-11 in `REQUIREMENTS.md`)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): planned milestone work
- Decimal phases (2.1, 2.2): urgent insertions (marked INSERTED)

- [x] **Phase 1: Entry format and checks** - One format for commands, facts and examples, and the tests that hold every entry to it (completed 2026-09-11)
- [x] **Phase 2: Command inventory** - Every PPL name as data, reconciled with 2.4.15515, and a linter that flags invented commands (completed 2026-09-11)
- [x] **Phase 3: Evidence on the Virtual Calculator** - Examples run in batches on the emulator, with any kind of answer brought back (completed 2026-09-12)
- [x] **Phase 4: Facts carried over** - Everything measured so far, in the new format, with lint messages that cite it (completed 2026-09-12)
- [x] **Phase 5: Statements and program commands** - Entries for the part of PPL every program uses (completed 2026-09-12)
- [x] **Phase 6: Home functions** - Entries for math, lists, matrices, statistics and the rest (completed 2026-09-13)
- [x] **Phase 7: App functions** - Entries for the functions of HP's apps that a program can call (completed 2026-09-14)
- [x] **Phase 8: App variables** - Entries for the app variables a program can read or set (completed 2026-09-25)
- [x] **Phase 8.1: Home and system variables, and the open questions** (INSERTED) - Entries for the 65 variables of Home, the system and the settings every app shares, and `GET`; and the open questions every program runs into, measured
- [x] **Phase 9: Guided path, index and README** - The way in, for a person and for a model (completed 2026-09-24; counted again in Phase 10)
- [x] **Phase 9.1: Tools that keep their promise** (INSERTED) - The interpreter never answers wrong in silence, and a batch never loses evidence in silence (completed 2026-09-24)
- [x] **Phase 10: What a PC can catch** - Every fact a PC could catch has a lint rule or says why not, and milestone 1 closes (completed 2026-09-25)
- [ ] **Phase 11: The working folder** - Downloaded and opened, nothing installed; a person's programs in `programs/`, kept through an update
- [ ] **Phase 12: Checks the agent cannot skip** - `lint` after every PPL edit, blocking on an error; claims no command backs caught; every citation resolves
- [ ] **Phase 13: From an idea to the calculator** - Questions before any PPL, a writer and a verifier, and a fixed hand-over
- [ ] **Phase 14: The other jobs** - Port, debug, screen, app, deploy and measure, and the paste block generated from the documentation
- [ ] **Phase 15: Projects across sessions** - The plan and the state in files, each step checked before the next
- [ ] **Phase 16: A new app, from scratch** - The size of TermoHP, on the G2, and milestone 2 closed

## Phase Details

### Phase 1: Entry format and checks
**Goal**: A fixed, documented format for a command entry, a fact and an example, and tests that reject anything that does not follow it
**Depends on**: Nothing (first phase)
**Requirements**: CMD-03, CMD-04, CMD-07, READ-02, CHECK-01, CHECK-03, CHECK-05
**Success Criteria** (what must be TRUE):
  1. One page explains the format of an entry, a fact and an example, and the four ways each can state how it is known
  2. A handful of real entries (for example `LEFT`, `SIZE` and `FOR`) and facts (for example the `LOCAL` limit) exist in the final format and pass the tests
  3. The tests fail on a duplicate identifier, a reference that does not resolve, a documentation page that mentions the kit, and a broken link
  4. For a command the interpreter implements, its entry's examples also run through `hpprime run` in the tests
**Plans**: 2 plans

Plans:
- [x] 01-01: The format, and real content in it
- [x] 01-02: The checks and the generator

### Phase 2: Command inventory
**Goal**: The complete list of PPL names lives in the repository as data, and the linter uses it
**Depends on**: Phase 1
**Requirements**: CMD-01, CMD-02, CMD-05, TOOL-01
**Success Criteria** (what must be TRUE):
  1. The list holds every statement, command, Home function, app function and app variable in HP's help, with its category and syntax; a first count of the help's titles puts the upper-case names at about 280
  2. Names added or removed after firmware 13217 are identified from a second source, and every name says where it came from
  3. An index by name and one by HP's grouping are generated from the list
  4. `hpprime lint` flags `STRLEN(s)` as a name that does not exist, and stays quiet on the program's own functions, locals and globals
**Plans**: 2 plans

Plans:
- [x] 02-01: The list of names, and the index over all of it
- [x] 02-02: The linter that reads the list

### Phase 3: Evidence on the Virtual Calculator
**Goal**: The examples of any batch of entries run on the Virtual Calculator with one keypress, and every kind of answer comes back as a file
**Depends on**: Phase 1. Checkpoint before it starts: the user installs the Virtual Calculator 2.4 and opens it once (done on 2026-09-11: 2.4 r15515)
**Requirements**: EVID-01, EVID-02, EVID-03, EVID-04, TOOL-03
**Success Criteria** (what must be TRUE):
  1. `hpprime doctor` finds the Spanish Connectivity Kit (`Calculadoras`) and the Virtual Calculator, and says which folders it used
  2. A batch of examples is sent, run with one keypress on the emulator and read back, strings, lists, matrices and errors included
  3. Each result is stored with the firmware it came from, and one that differs from HP's stated result is flagged
  4. The reader's wrong pick between two source records ending at the same offset is reproduced in a test and fixed
**Plans**: 3 plans

Plans:
- [x] 03-01: The localised folders, and what the real mirror showed
- [x] 03-02: The batch runner, and results.tsv
- [x] 03-03: The first real batch, on the emulator, with the user

### Phase 4: Facts carried over
**Goal**: Everything the current reference establishes is in the new format, stated once, and the linter points at it
**Depends on**: Phase 1
**Requirements**: FACT-01, FACT-02, FACT-03, FACT-04, FACT-05, CMD-06, TOOL-02, CHECK-04
**Success Criteria** (what must be TRUE):
  1. A migration list maps every fact in today's seven reference pages to its new home, with none left out
  2. The false hypotheses and the unverified items are entries with their own status
  3. Every lint message names the fact identifier it comes from, and a test checks that every rule has one
  4. The deploy page explains the send from the Connectivity Kit's content library, marked as done once
  5. The mistakes models are known to make appear in the entries they concern
**Plans**: 3 plans

Plans:
- [x] 04-01: The language and the formats
- [x] 04-02: The screen, the apps and Python
- [x] 04-03: Deploy, libraries, and the linter's sources

### Phase 5: Statements and program commands
**Goal**: Every statement and program command has a complete entry whose examples have been run
**Depends on**: Phases 2, 3 and 4
**Requirements**: CMD-08
**Success Criteria** (what must be TRUE):
  1. Every name the inventory files under statements and program commands has an entry in the fixed format
  2. Every example in those entries has a Virtual Calculator result on file, or says why it cannot have one
  3. The tests pass with the new entries included
**Plans**: 5 plans

Plans:
- [x] 05-01: The language itself
- [x] 05-02: Strings and integers
- [x] 05-03: Matrices, and the mixed bag under `more`
- [x] 05-04: The commands that talk to a person
- [x] 05-05: The 35 that paint

### Phase 6: Home functions
**Goal**: Every Home function has a complete entry whose examples have been run
**Depends on**: Phase 5
**Requirements**: CMD-09
**Success Criteria** (what must be TRUE):
  1. Every name the inventory files under the Home functions has an entry in the fixed format
  2. Every example in those entries has a Virtual Calculator result on file, or says why it cannot have one
  3. Where HP's stated result and the emulator's answer differ, the entry says so
**Plans**: 6 plans

Plans:
- [x] 06-01: Ten Home functions, and the guard for the one answer never kept
- [x] 06-02: Integers, bits and the rest of arithmetic
- [x] 06-03: The matrices and the lists
- [x] 06-04: The four small groups
- [x] 06-05: The mathematics of catalog
- [x] 06-06: The machine names of catalog

### Phase 7: App functions
**Goal**: Every app function a program can call has a complete entry whose examples have been run
**Depends on**: Phase 6
**Requirements**: CMD-10
**Success Criteria** (what must be TRUE):
  1. Every app function on the list has an entry in the fixed format, with the app it belongs to
  2. Every example in those entries has a Virtual Calculator result on file, or says why it cannot have one
**Plans**: 7, all complete

### Phase 8: App variables
**Goal**: Every app variable a program can read or set has an entry
**Depends on**: Phase 7. Paused after 08-04, and resumes after Phase 8.1 at the user's choice on 2026-09-24: the 42 left belong to the statistics, spreadsheet, advanced-graphing, linear-solver, sequence and solve apps, while the variables of Home and the system reach every program
**Requirements**: CMD-11
**Success Criteria** (what must be TRUE):
  1. Every app variable on the list has an entry in the fixed format, with its app, what it holds, and whether a program can set it
  2. Every example in those entries has a Virtual Calculator result on file, or says why it cannot have one
**Plans**: 5, all complete and verified on 2026-09-25. 08-01 to 08-04 one round on the emulator at a time, the person selecting the app; 08-05 took the last 42 in two batches with no app selected, through the app's name in front of each name

### Phase 8.1: Home and system variables, and the open questions (INSERTED)
**Goal**: Every variable a program reads or sets outside one app has an entry: Home's settings, the system's, and the plot and numeric settings every app shares. And the open questions every program runs into are measured, in the same sessions on the emulator
**Depends on**: Phase 9.1. Inserted on 2026-09-16: Phase 5 deferred these 65 names to Phases 6, 7 and 8, none of those phases took them, and `GET` was never assigned. Moved ahead of the rest of Phase 8, and given the open questions, at the user's choice on 2026-09-24
**Requirements**: CMD-12, FACT-06
**Success Criteria** (what must be TRUE):
  1. Every name the list files as `variable` has an entry in the fixed format, with what it holds and whether a program can set it
  2. `GET` has an entry, which says what it is, or that the sources do not say
  3. Every example in those entries has a Virtual Calculator result on file, or says why it cannot have one
  4. Every case `hpprime lint` warns on as `unverified`, and every open half of a fact in `ppl.md` that a program can run into, is measured on the emulator or says why it cannot be: at least `L(0)` on a list and on a matrix, `a = 2;` as a statement, three locals initialised on one line, `LOCAL i` and `LOCAL e`, 9 to 12 variables in one `LOCAL`, a function's `END` without its `;`, a call indexed on a name the file does not define, `WAIT(-1)`, a program exporting a name an app already has, how `MOD` and `NTHROOT` bind against `+`, `-`, `*`, `/` and `^` (`9 MOD 4 + 100` answers 101 or 9), `-9 MOD 4`, and `NTHROOT` of a negative number, the last three being what `hpprime run` refuses since Phase 9.1
  5. A lint case that is measured becomes an error with its evidence, or leaves the linter, and its test says which
**Plans**: 4, planned on 2026-09-24; all complete and verified on 2026-09-24

Plans:
- [x] 08.1-01: Home's settings, the system's, `Ans` and `GET`, with the open questions a batch can answer
- [x] 08.1-02: The app's mode and numeric view
- [x] 08.1-03: The plot view
- [x] 08.1-04: The compile questions, and the two by hand

### Phase 9: Guided path, index and README
**Goal**: A person can learn from zero and a model can find any entry, both on the finished reference
**Depends on**: Phases 5, 6, 7, 8 and 8.1. It runs ahead of 8 and 8.1, at the user's choice on 2026-09-16: what it builds is generated from the entries or links to them, and its verification is counted again when 8.1 closes
**Requirements**: READ-01, READ-03, READ-04, READ-05, READ-06, CHECK-02
**Success Criteria** (what must be TRUE):
  1. The guided path takes somebody from an empty folder to a program running on the calculator, linking to entries rather than restating them
  2. One index, within its size budget, lists every entry and topic with its identifier and a one-line summary
  3. The README presents the documentation first, and `AGENTS.md` and `SKILL.md` point at the new documentation until milestone 2 replaces them
  4. The tests confirm that every example in the documentation has been run or says why not
**Plans**: 4, approved on 2026-09-16; all complete. Verified on 2026-09-24, and counted again in Phase 10 on the finished reference

Plans:
- [x] 09-01: The model index, and the check for examples nobody ran
- [x] 09-02: Planning language out of the documentation
- [x] 09-03: The guided path
- [x] 09-04: The README, and the pages above the documentation

### Phase 9.1: Tools that keep their promise (INSERTED)
**Goal**: The interpreter never gives a wrong answer without saying so, and a batch on the emulator never loses or replaces evidence without saying so
**Depends on**: Phase 9. Inserted on 2026-09-24 at the user's choice, before any more batches: `hpprime run` answered 9 to `9 MOD 4 + 100` with the linter clean, measured that day, where the whole repository promises it raises on what it does not cover
**Requirements**: TOOL-04, TOOL-05
**Success Criteria** (what must be TRUE):
  1. `hpprime run` answers correctly, or raises with a message, on an operator word written between its operands, such as `MOD`, and on a builtin handed a type it does not handle, such as `CONCAT` given a number: never a partial answer and never a Python traceback. A test holds each case
  2. `hpprime examples` refuses a probe whose call already holds a different stored answer, unless told to replace it, and says which rows it would change
  3. An answer the decoder cannot read costs its own row, not the batch; the two infinities measured on 2026-09-13, sign nibbles 2 and 6, are read as infinities
  4. A stored row carries the date its batch ran, not the date it was prepared
**Plans**: 2, complete and verified on 2026-09-24

Plans:
- [x] 09.1-01: The interpreter answers as the calculator does, or says it does not cover the case
- [x] 09.1-02: A batch never loses or replaces evidence in silence

### Phase 10: What a PC can catch
**Goal**: Every fact a PC could catch is caught by `hpprime lint`, or says why it is not, and milestone 1 closes on the finished reference
**Depends on**: Phase 8, so that the facts have stopped moving
**Requirements**: CHECK-04
**Success Criteria** (what must be TRUE):
  1. A list covers every fact in `docs/topics/`: the lint rule that catches it, or why a PC cannot, such as a fact about the screen or the Connectivity Kit
  2. Every fact on that list that a PC can catch has a rule, with a test for a case it catches and one it must stay quiet on
  3. Phase 9's counts are taken again on the finished reference: the index within its budget, every example run or saying why not, the README's numbers current
**Plans**: 3, questioned and approved on 2026-09-25; all complete and verified on 2026-09-25

Plans:
- [x] 10-01: The compile session, and the list of every fact
- [x] 10-02: The checks the list decided on
- [x] 10-03: Phase 9's counts again, and milestone 1 closed

### Phase 11: The working folder
**Goal**: Downloading the kit and opening its folder is the whole install: a fresh session picks up the contract, the tools run from the folder, and a person's programs stay in `programs/` through an update
**Depends on**: Milestone 1
**Requirements**: KIT-01, KIT-09
**Success Criteria** (what must be TRUE):
  1. The repository downloaded as a ZIP from GitHub and opened in the Claude Code desktop app, in a folder that is not this clone, is picked up with nothing installed: the session loads `AGENTS.md` and reads `docs/llms.txt` when PPL comes up
  2. The tools run from that folder: `hpprime lint`, `run` and `write` at least, on this Windows machine; how they start on others, and what the agent does when no Python starts, is written down, and labelled where it was not run
  3. A person's programs go in `programs/`, which git ignores and the kit ships with a note in; `hpprime update` brings a ZIP to the latest version without writing inside `programs/`, refuses in a clone, and a test holds both
  4. An expert clones and uses the tools and the documentation without the kit's procedures, and the README says how, for both ways in
**Plans**: 3, replanned on 2026-09-26 when the plugin gave way to the kit's own folder. The plugin's plan 11-01 was undone before it was committed; `11-RESEARCH.md` stays as the record of what was read about hooks

Plans:
- [x] 11-01: The folder: `programs/`, and the README's two ways in
- [x] 11-02: `hpprime update`
- [ ] 11-03: Downloaded and tried

### Phase 12: Checks the agent cannot skip
**Goal**: The gates of `AGENTS.md` run without depending on the agent remembering them
**Depends on**: Phase 11
**Requirements**: KIT-05, KIT-04
**Success Criteria** (what must be TRUE):
  1. After an edit to a PPL file, `lint` runs by itself; an error stops the agent until it is fixed, and a warning is shown without stopping it
  2. A report claiming a program compiles, works on the calculator or is installed, with no command's output behind it, is caught when the agent finishes; cases it must let pass are held by tests, and the person, not the agent, can switch it off
  3. Every identifier the kit's skills and agents cite resolves, and a test fails on one that does not
**Plans**: TBD

### Phase 13: From an idea to the calculator
**Goal**: A person with an idea and no PPL gets a program running on the calculator
**Depends on**: Phase 12
**Requirements**: KIT-07, KIT-03, KIT-06, KIT-02 in part
**Success Criteria** (what must be TRUE):
  1. Given an idea, the agent asks what it needs before it writes any PPL
  2. One role writes and another verifies, and the second assumes nothing works until a command shows it does
  3. What only the person can do is handed over in one fixed form: what was built, the keys to press, the values to expect, and what to report back
  4. The user brings an idea of their own, never reads the PPL, and the program runs on their G2
**Plans**: TBD

### Phase 14: The other jobs
**Goal**: Every job the kit names has its own short procedure
**Depends on**: Phase 13
**Requirements**: KIT-02, KIT-10
**Success Criteria** (what must be TRUE):
  1. Port, debug, screen, app, deploy and measure each have an entry point that loads only the documentation that job needs
  2. The paste block for chats with no file access is generated from the documentation, and a test fails when it is stale
**Plans**: TBD

### Phase 15: Projects across sessions
**Goal**: A project too big for one session is built across several without losing its place
**Depends on**: Phase 14
**Requirements**: KIT-08
**Success Criteria** (what must be TRUE):
  1. A project's plan and state live in files in its folder under `programs/`, and a new session resumes from them
  2. Each step is checked by the kit's gates before the next one starts
**Plans**: TBD

### Phase 16: A new app, from scratch
**Goal**: The kit builds an app the size of TermoHP, and milestone 2 closes
**Depends on**: Phase 15
**Requirements**: KIT-11
**Success Criteria** (what must be TRUE):
  1. A new app with an engine, several screens and a large data set -- not TermoHP -- is built from scratch across sessions in a fresh download of the kit, and runs on the G2
  2. Every builtin the kit's programs needed from the interpreter is covered, each measured first
**Plans**: TBD

## Progress

**Execution Order:**
1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 (paused after 08-04) → 9 → 9.1 → 8.1 → 8 (the rest) → 10. Phase 4 depended only on Phase 1, so it could move ahead of Phase 3 while the emulator was not ready. Phase 9 runs ahead of 8 and 8.1 at the user's choice on 2026-09-16, since nothing it builds waits for their entries. On 2026-09-24 the user chose four changes: Phase 9.1 before any more batches, Phase 8.1 ahead of the rest of Phase 8, the open questions measured in 8.1's sessions, and Phase 10 for the half of CHECK-04 no phase owned.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Entry format and checks | 2/2 | Complete | 2026-09-11 |
| 2. Command inventory | 2/2 | Complete | 2026-09-11 |
| 3. Evidence on the Virtual Calculator | 3/3 | Complete | 2026-09-12 |
| 4. Facts carried over | 3/3 | Complete | 2026-09-12 |
| 5. Statements and program commands | 5/5 | Complete | 2026-09-12 |
| 6. Home functions | 6/6 | Complete | 2026-09-13 |
| 7. App functions | 7/7 | Complete | 2026-09-14 |
| 8. App variables | 5/5 | Complete: 172 of 172 | 2026-09-25 |
| 8.1. Home and system variables, and the open questions | 4/4 | Complete (INSERTED) | 2026-09-24 |
| 9. Guided path, index and README | 4/4 | Complete, counted again in Phase 10 on 2026-09-25 | 2026-09-24 |
| 9.1. Tools that keep their promise | 2/2 | Complete (INSERTED) | 2026-09-24 |
| 10. What a PC can catch | 3/3 | Complete: milestone 1 closed | 2026-09-25 |
| 11. The working folder | 2/3 | In progress: `programs/`, the two ways in, `hpprime update`; trying a download is next | - |
| 12. Checks the agent cannot skip | 0/TBD | Not started | - |
| 13. From an idea to the calculator | 0/TBD | Not started | - |
| 14. The other jobs | 0/TBD | Not started | - |
| 15. Projects across sessions | 0/TBD | Not started | - |
| 16. A new app, from scratch | 0/TBD | Not started | - |
