---
status: executing
progress:
  total_phases: 18
  completed_phases: 12
  total_plans: 49
  completed_plans: 48
  percent: 67
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-09-24)

**Core value:** Everything the documentation says about the Prime states how it is known, and the agents built on it never claim more than it does.
**Current focus:** Milestone 2, the agent kit. Phase 11: the working folder

## Current Position

Milestone: 2 of 2 (the agent kit), defined and approved on 2026-09-26, revised the same day
Phase: 11, the working folder: 11-01 and 11-02 done; 11-03, a download tried in a fresh session, next
Plan: every phase of milestone 1 complete and verified. Everything up to Phase 8 is committed and pushed in d9f1c16; Phase 10 is uncommitted. 706 entries, 122 facts, 20 lint rules, 1252 lines in results.tsv
Status: milestone 1 closed on 2026-09-25: 38 of 38 requirements, every name on HP's list with an entry, every example run or saying why not, every fact naming what catches it
Last activity: 2026-09-28 — Plan 11-03 tried: the user opened the download in a new session and asked for an analog clock without naming the kit; the session loaded `AGENTS.md` by itself, read `docs/llms.txt`, ran on Python 3.9.13, built `programs/RELOJ/` through lint, run, build and verify, cited facts by label, and changed no file of the kit. It asked nothing first (Phase 13) and found `pull --diff` does not reach an app (Phase 14). On the emulator the app opened once compiled, its time matched the PC's, and the seconds came at once: `Time` reads as decimal hours with seconds, a candidate for `Time.md` once the harness measures it. Before that, 2026-09-27, plan 11-02 done: `hpprime update` in `hpkit/update.py`, 23 checks in `tests/test_update.py` that fail when its guards are stubbed out, the fourteenth suite; a download of d1271bb brought to this tree end to end, 945 of 946 files matching and `programs/README.md` left unwritten as decided. Run by accident against GitHub in a scratch copy: the download works here, GitHub's ZIP carries its commit, GitHub's `main` is `c8951ab` "Update LICENSE", one ahead of the local `main`, and its ZIP is LF where a local `git archive` with `core.autocrlf=true` is CRLF. Suite 14,904 passed. Before that, `hpprime new` pointed at `programs/NAME/` at the user's word, with `test_cli` kept out of the kit's own `programs/` and the paths of the docs, the README and steps 2, 4 and 5 following; recorded in `11-01-SUMMARY.md`. Suite 14,880 passed. Before that, 2026-09-26, plan 11-01 done, at the user's approval of `11-CONTEXT.md`: `programs/` with its note and the ignore rules, `AGENTS.md` saying where a person's programs go and what to do when no Python starts, the README and step 1 giving the ZIP beside the clone, and `programs_problems` in `tests/test_docs.py`, which named both faults when the note's rule was removed by hand. Left for the user: `hpprime new` still writes at the root, as step 2 does. Suite 14,876 passed. Before that, milestone 2 revised at the user's word: the plugin gave way to the kit's own folder, downloaded as a ZIP or cloned and opened, nothing installed; a person's programs in `programs/`; `hpprime update` for a ZIP; every agent reads `AGENTS.md` and Claude Code also enforces it. The user's reasons: tied to Claude Code, installed through concepts a beginner does not know, files in a cache nobody opens, machinery and open points for what it gave. The plugin's plan 11-01 undone before it was committed: `.claude-plugin/` and `skills/` gone, and the root `SKILL.md` not restored, since the desktop app loaded `AGENTS.md` by itself with no `CLAUDE.md` in the folder; the README, `docs/ai/prompts.md` and `tests/test_docs.py` back to the committed text less `SKILL.md`. Phase 11 replanned as the working folder, three plans. Before that, Phase 11 researched and questioned, plan 11-01 done. How plugins work read from Claude Code's documentation into `11-RESEARCH.md`, with four points left to try. The user chose: the repository's root as the plugin, the skill running the tools by their full path, a local marketplace for trying it. `.claude-plugin/plugin.json` and `marketplace.json` written, `SKILL.md` moved to `skills/hp-prime/` and rewritten as an adapter to `AGENTS.md`, the README's install section, and `plugin_problems` holding the files to the documented rules. Suite 14,874 passed. Before that, milestone 2 questioned and defined in `milestone-2-CONTEXT.md`, approved by the user: a Claude Code plugin; the beginner's path first; checks that block a lint error and catch claims no command backs; the user playing the beginner without reading the PPL; closed by a new app the size of TermoHP. Phases 11 to 16. Phase 10's commit d1271bb pushed once GitHub answered again. Before that, 2026-09-25, plan 10-03, Phase 10 verified and milestone 1 closed. Phase 9's counts taken again on the finished reference: `docs/llms.txt` 91,335 bytes of 100,000 with 706 entries and 122 facts; 1,149 examples, 1,128 on the emulator, 4 on a G2, 17 with no value, none unrun; the guided path linking 79 facts, its commands run in a clean folder; the README's 9 numbers current. Nothing the count found wrong. Before that, plan 10-02, at the user's approval of the list, with Check confirmed on `ZQMU1` and `ZQEP`. Seven lint rules and one grown: `mu-zero` (error), `getkey-code`, `string-index`, `draw-units`, `draw-then-return`, `wait-undrained`, `expr-in-loop`, and `export-clash` on an export named like one of HP's; `build` warns on `MOUSE` handed to Python raw. Twenty rules. They found step 3's `TDRAW` drawing and returning, now fixed, and the conformance example exporting `ROOT`, now `BISROOT`; on the user's 29 installed programs, no false alarm. CHECK-04 complete. Suite 14,879 passed. Before that, Phase 10 questioned (any hpprime command counts; the list lives with the linter; one compile session) and plan 10-01 done. The session: `GETKEY()` compiles and answers, so no rule and the fact corrected; `Inference.μ₀` with the Greek mu does not compile and with the micro sign answers 0.5; `ENDPROC` does not compile, now an error; `EXPORT` with 3 and 5 compiles, closing 8.1's open questions. `CAUGHT` in `hpkit/lint.py` gives each of the 122 facts its answer, written into `docs/tools.md` by `hpprime docs` and held by `caught_list`, `QUIET` and `rules_have_both_cases` in `tests/test_lint.py`. It found `export-clash` with no test, and a tenth-listed check, an export named like one of HP's. Suite 14,860 passed. Before that, plan 08-05 and Phase 8 closed, at the user's word to go on with Phase 8. Questioned first, two choices: probe `App.Variable` before seven rounds with the app selected by hand, and measure the statistics with data. Two batches with no app selected, 165 rows, both compile controls right: a program reaches another app's variables and functions with the app's name in front, in source and through `EXPR`, now `apps.qualified-names`. 42 entries, the last app variables: 706 of 706 names. Every statistic matched the hand computation; `Statistics_1Var.MeanX` and `Statistics_2Var.MeanX` are two values; `Triangle_Solver.SSS` from the Function app answers radians; `Solve.SOLVE(X^2-4=0,X,1)` answers 2 and `Solve.Solve` is still refused. `hpprime run` fixed three ways: a qualified name was a syntax error, a Greek initial a traceback, and a name on HP's list "undefined"; now "not covered", with a test. I told the user 39 of 42 answered qualified at once; it was 28, corrected. Suite 14,713 passed. Before that, plan 08.1-04 and Phase 8.1 closed. `hpprime examples --compile` built and tested, then 22 programs and 2 controls on the emulator, both controls right. 9 locals do not compile (the limit is 8); a function's `END` without `;` does not compile; `ENDCASE`, `ENDFUNC` do not; a `LOCAL` in a nested block, `EXPORT` with 2 to 6 initialised, three initialised locals, `LOCAL i` and `e`, and a literal `L(0)` all compile; `x = 2;` compiles and assigns nothing; a program exporting `AREA` hides the Function app's; `Check` named the first of two syntax errors, contradicting `ppl.check-last-error`'s old title; `WAIT(-1)` waited both times. The linter has 13 rules, the interpreter refuses what does not compile. Suite 13,550 passed. Before that, plan 08.1-03: 69 calls, the harness waiting three hours through its own `timeout`. 30 entries for the plot view, and with them all 65 variables of Home and the system and `GET`: CMD-12 complete, 664 of 706 names. The app's mode settings are shifted by one against Home's and override them once not 0 -- angle, complex numbers, number format -- so `apps.app-angle-overrides-home` became `apps.app-mode-overrides-home` before it was ever published. Drawing units follow the plot window: `C→PX(0,0)` moves with `Xmin` and `Ymax`. The parameter, polar and sequence ranges refuse with the Function app active. `HAngle` 2 is gradians. Suite 13,513 passed. Before that, plan 08.1-02: 46 calls, collected by a watcher after the harness gave up waiting at 30 minutes. 16 entries for the app's mode and numeric view. The active app's `AAngle` overrides Home's `HAngle` for a program's trigonometry, now `apps.app-angle-overrides-home`; a string indexed answers a character code, now `ppl.string-index-code`; `MOD` sits with `/`, `NTHROOT` binds tighter than `^` and a minus sign; `Base` 0 to 3 are binary, octal, decimal, hexadecimal. The interpreter follows every row. 634 entries, 121 facts, suite 12,970 passed. Before that, plan 08.1-01: Phase 8.1 questioned (four decisions from the user, all sixteen open questions taken) and its first batch run, 71 calls, all read back. 20 entries, Home's settings, the system's, `Ans` and `GET`. A list read at 0 answers its LAST element and one assigned at 0 appends, a matrix at 0 is an error; `MOD` binds like `*` and its remainder takes the divisor's sign, against HP's help; `NTHROOT` binds tighter than `*`; the calculator ignores case in command names, now `ppl.names-ignore-case`; `STRING` follows `HFormat` and `HDigits`. The interpreter and the linter follow. 618 entries, 119 facts, suite 12,689 passed. Before that, Phase 9.1 complete and verified, questioned first with four decisions from the user. `hpprime run` answers `9 MOD 4` and `3 NTHROOT 8` as the emulator did, refuses the call forms as the calculator does, refuses `9 MOD 4 + 100` because how `MOD` binds was never measured, and never prints a traceback: 114 interpreter tests. `hpprime examples` keeps a stored row a different answer would replace, refuses a probe on a stored call, loses one row and not a batch to a cell it cannot read, reads the two infinities, and dates a row the day `M9.hpmat` was written: 56 tests. One new fact, `formats.number-infinity`. Suite 12,344 passed, 0 failed. Before that, the README approved by the user and Phase 9 closed: 09-04's summary, and a verification that counts 598 entries and 117 facts in 74,929 bytes of `docs/llms.txt`, 779 of 800 examples stored, 4 by hand on a G2, 17 *no value*, none unrun. Before that, the plan reviewed at the user's request, and four changes applied at their choice: Phase 9.1 inserted before any more batches, for `hpprime run` answering 9 to `9 MOD 4 + 100` and the harness able to replace a stored row or lose a batch to one cell; Phase 8.1 moved ahead of the rest of Phase 8; the open questions every program runs into measured in 8.1's sessions (FACT-06), a list of about a dozen rather than the 22 `unverified` facts, most of which are about formats, libraries and Python; and Phase 10 for CHECK-04's open half. Before that, plan 09-04: the README leads with the documentation and a test holds its numbers; `AGENTS.md`, `SKILL.md` and the paste block send a model to `docs/llms.txt` first; every rule of the paste block cites its fact with its label, and a test holds each citation; the apptest README's settled question closed. Before that, 2026-09-23, plan 09-03: the six steps of the guided path rewritten to link 51 facts, `docs/start/` under the same checks as the entries, 19 errors on the path corrected (the context's three and sixteen more found by reading), the starter's `AREA` renamed `CIRCAREA` at the user's choice, and `ppl.one-based` narrowed to what was measured. Before that, 2026-09-22, commit 9704074, made outside the plan in answer to issue #1 on GitHub: every lint finding carries its fact's label, and a rule is an error only as far as its measurement reaches. Before that, 2026-09-16, plan 09-02: planning language and "this kit" out of 100 pages, a check that refuses "phase" and "this kit", and a glossary of batch, harness and probe in `format.md`. Before that, plan 09-01: `docs/llms.txt` generated at 74,939 bytes of a 100,000 budget, the check for examples nobody ran, and 21 `unverified` examples relabelled, which settled `ppl.locals-initialised-one-line` from a row Phase 5 had stored for it and never written down. Before that, Phase 9 questioned: four decisions from the user, 66 names found that no phase had taken, now Phase 8.1, and eight decisions proposed in `09-CONTEXT.md`. Before that, the Finance round: 50 of 68 variables answer from any app, 9 need Finance selected, 9 refuse either way; with Finance active every number becomes text with two decimals; and `Xlist` turned out not to be alone. Before that, 2026-09-15, the Inference round: 49 of 50 variables answer with the app active, the app ships with a worked example loaded, `DoInference` answers and writes its results where Phase 7 recorded a refusal, and the one name that refused is spelled on HP’s list with a codepoint the calculator does not accept. Before that, the Function app round. `F1:='X^2-4'` stores the expression where `F1:=X^2-4` stored a number, so a batch fills `F1` unaided and the whole group answered with no keypresses; and the function commands turn out **not** to write their own variables, where `DoSolve` did. Before that, the Phase 8 probe, two batches and 48 rows. A reset calculator turns out to have the Function app active, so "no app open" is not a condition the Prime has and seven entries said it was. The app rule reaches variables as well as functions, a program can set one and the value stays, and `DoSolve` answers once something has put a triangle in the app — where Phase 7 recorded a refusal

Progress: [███████░░░] 67%

## Accumulated Context

### Decisions

Decisions are logged in the Key Decisions table of PROJECT.md. Recent ones:

- Phase 2: CAS names are on the list, known to the linter and not documented
- Phase 2: unknown-name is a warning for a file alone, an error with `--set`
- Phase 2: the linter compares the calculator's names without regard to case; whether the calculator does is not measured
- Phase 3: the user presses the keys on the emulator; the batch runs on a throwaway calculator, Prime_1 — the name the emulator's second window always opens, measured 2026-09-11 — reset before each batch; HP help becomes emulator where the emulator agrees, and a disagreement is flagged, never replaced
- Phase 3: what a result is stored with is the version number and the build date, never what `VERSION` answers, which carries the calculator's serial number
- 2026-09-24, from a review of the plan: Phase 9.1 before any more batches; Phase 8.1 ahead of the rest of Phase 8, with the open questions every program runs into; Phase 10 for CHECK-04's open half. Commits are held and made larger, at the user's request
- 2026-09-23: the starter exports `CIRCAREA`, not `AREA`, which is the Function app's; the rename was chosen over measuring what Home does with the collision
- 2026-09-22, 9704074: a lint rule is an error only as far as its measurement reaches, a warning labelled `unverified` beyond it; `tests/test_lint.py` fails on an error whose label is not `G2` or `emulator`
- Phase 9, questioned 2026-09-16: the 65 variables and `GET` become Phase 8.1, inside milestone 1; Phase 9 runs ahead of 8 and 8.1; the index a model loads first is one file with a link on every line; the guided path keeps its six steps, rewritten to link; planning language leaves the documentation, with a check to keep it out

### Pending Todos

- **Owned by a phase since 2026-09-24.** The tool problems below are
  fixed by Phase 9.1 (2026-09-24): the interpreter's silent answer to
  `9 MOD 4 + 100` and its tracebacks on `CONCAT` and the list forms of
  `FLOOR`; a probe overwriting a stored row; a batch lost to one infinity; a
  row dated the day its batch was prepared. Phase 8.1 takes the open
  questions, and 9.1 added three: how `MOD` and `NTHROOT` bind against the
  arithmetic operators, `-9 MOD 4`, and `NTHROOT` of a negative number. Also
  `L(0)` on a list: the interpreter raises it as the calculator's error
  (`PPLError`), which nothing measured. The others: `a = 2;` as a statement,
  three locals initialised on one line, `L(0)` on a list, `LOCAL i` and `e`,
  `WAIT(-1)`, the export that meets an app's name, and the cases the linter
  warns on as `unverified`. Phase 10 takes CHECK-04's open half. The bullets
  stay below as the record of what was measured
- **Done in plan 09-04, found by 09-03** (2026-09-23). `AGENTS.md` and
  `docs/ai/prompts.md` §1 no longer say `L(0)` is a run-time error, and
  `examples/apptest/README.md` no longer asks for the labels along the bottom
  to be pressed to settle a code `interface.soft-labels-not-keys` settled

- **Finance splits three ways** (measured 2026-09-15). With the Function
  app active, 50 of its 68 variables answered. Nine refused and then
  answered with Finance selected -- `NbPmt`, `IPYR`, `PV`, `PMT`, `FV`,
  `PPYR`, `CPYR`, `BEG`, `GSize`, the time-value-of-money names. Nine refused
  either way: the eight cash-flow results and `BSPut`. No name of either side
  collides with another on HP's list, so a clash does not explain it. The
  likeliest reason for the eight is that `CFData` is empty -- a sum of
  nothing answers 0 (`TotalCF`), a present value of nothing has none -- and
  their twin functions, `CashFlowNPV` and the rest, answered in Phase 7 given
  the flows as arguments. `BSPut` refusing while `BSCall` answers 0, with
  every input at 0, is unexplained
- **With the Finance app active a number becomes text with two decimals**
  (measured 2026-09-15): `CFPYR`, `BSCall` and `TotalCF` came back `12`,
  `0`, `0` with the Function app active and `12.00`, `0.00`, `0.00` with
  Finance. The harness makes every answer's text with `STRING` on the
  calculator, so a program doing the same gets a string that depends on
  which app is active. Rows taken with Finance active carry the decimals.
  Now `apps.finance-shows-two-decimals`
- **A `:=` form appears in an entry's Syntax only where an assignment was
  measured** (decided 2026-09-15). Four Triangle Solver entries had declared
  one without evidence -- `TriType`'s own text said it was never tried -- and
  lost it; `Alpha` and `Ylist`, which were measured, gained it. Eight
  Inference entries had also labelled a name's meaning `(HP help)` where HP's
  list gives none; they say `(unverified)` now

- **Other agents work in this repository between sessions, and nothing is
  committed with `git add -A` any more** (2026-09-15). While a session was
  interrupted, another agent left twelve files changed and uncommitted; the
  next commit swept them in under this session's message. Audited file by
  file: its fix of a fact kind was right and is kept, its unlinking of nine
  entries is undone now their targets exist, its CI workflow is out at the
  user's word, and its rewrite of `tests/test_lint.py` to `unittest` is
  reverted -- `tests/run_all.py` reads each suite's `PASS: N FAIL: M` line, so
  the rewrite had made the linter's 39 checks count as zero with nothing
  failing. After any break: list what changed since the last own commit,
  attribute each file, stage by name

- **A probe can overwrite a stored row without a word** (2026-09-15, my
  mistake). `results.tsv` keys on the exact call text, so a probe reusing
  one replaces the row -- the documented trap. Round 5 of Phase 8 reused
  `(Alpha)` and turned a refusal measured with the Function app active into
  0.01 measured with Inference active. The loss is a redundant row: two
  others still carry that refusal, and no entry lost its evidence. Round 4
  had avoided it by generating each call text against the stored keys;
  round 5 was typed by hand. **Worth a decision about the tool**: the
  harness could refuse a probe whose key already holds a different answer.
  That is a change to `hpkit/examples.py` and goes through its own decision,
  like the date stamp above; until then every probe list is generated
  against the stored keys, never typed

- **One name on HP's list cannot be typed as the list spells it** (measured
  2026-09-14). `μ₀` uses GREEK SMALL LETTER MU, U+03BC, and is refused;
  the same glyphs with MICRO SIGN, U+00B5, answer 0.5. Eleven other Greek and
  subscripted names in the same app answer as listed, so it is this name and
  not a rule. The extractor was checked first and does not normalise: the
  Command Tree 13217 spells it that way. **The linter will accept the broken
  spelling and flag the working one as invented.** Now `ppl.mu-zero-spelling`;
  worth a decision in Milestone 2 about whether the linter should know
- **The Inference app ships with a worked example loaded** (measured
  2026-09-14): `n₁` and `n₂` 50, `Mean₁` 0.461368, `Alpha` 0.05,
  `Conf` 0.99 on a calculator the harness had just reset. So a program
  reading before writing gets HP's data, and `DoInference` answered with
  nothing supplied at all. Three apps, three conventions for an unwritten
  value: −1, 0, and somebody else's example
- **`Xlist` is not alone** (measured 2026-09-14, settled 2026-09-15). It
  answered `{}` under three apps and was recorded as the one variable that
  ignores the app rule. All five of the Inference app's other lists then
  answered `{}` with the Function app active, and so did 50 Finance
  variables. Its entry is corrected
- **Lists and matrices come back differently empty** (measured 2026-09-14):
  a list as `{}`, a matrix as `[[0]]`, a one-by-one table holding zero. A
  program cannot test the two the same way

- **The `Do` commands write their app's variables; the functions do not**
  (measured 2026-09-14, refined the same day). First read as one app's habit,
  then `DoInference` wrote `TestScore`, `Prob`, `CritVal1` and `Result` the
  way `DoSolve` had written the angles -- two apps, both `Do` commands, both
  writing. A `Do` command runs over state the app already holds and puts its
  answer back there; a function takes arguments and returns. Two apps are not
  every app. `DoSolve` writes `AngleA`, `AngleB` and `AngleC`;
  `ROOT`, `SLOPE`, `ISECT` and `AREA` write nothing -- each answered while
  the variable of the same name stayed at 0, read in the same batch one call
  later. `Extremum` is the trap: it reads 0 and `EXTREMUM(F1,0)` answers 0,
  so a single row would have read as a write. The paired before-and-after is
  what separates them
- **There is no shared marker for "not computed" across apps** (measured
  2026-09-14). The Triangle Solver uses −1, which a program can test for;
  the Function app uses 0, which is indistinguishable from a real answer.
  One test cannot cover both

- **A reset calculator has the Function app active** (measured
  2026-09-14), so "with no app open" is not a condition any measurement can
  have. Proved by a reversal: with nothing selected the Function app's
  variables answered and the Triangle Solver's refused; with the Triangle
  Solver selected, exactly the other way round. Every `emulator` row taken
  from an untouched batch was therefore measured with the Function app
  active. For names outside that app that is the same as the app not being
  active, so those readings stand; for the five Function app commands and
  the five Function app variables it is not. Now
  `apps.reset-leaves-function-active`, and seven entries that had written
  "from Home, with no app open" are corrected
- **The app rule reaches some variables, not all** (measured 2026-09-14,
  narrowed 2026-09-15). `AngleA` refused both reading and assignment with
  another app active and did both with the Triangle Solver active, and the
  Function app's variables behave the same. But 50 of Finance's 68 answer
  from any app, and so do the Inference app's six lists while its `Alpha`
  does not. **Whether a variable needs its app is a fact about that variable**,
  and an entry states it only where it was measured. The phase is still one
  of rounds, but fewer than feared: an untouched batch reads a good part of
  it
- **A program can set an app variable and the value stays** (measured
  2026-09-14): `SideA:=3` answered 3 and a later read in the same pass
  answered 3. That is the phase's success criterion answered with rows
- **The working shape of an app from a program, measured end to end**
  (2026-09-14): set `SideA`, `SideB`, `SideC` to 3, 4, 5; call `DoSolve`;
  read `AngleA`, `AngleB`, `AngleC` and get 36.8698976458, 53.1301023542 and
  90. **`DoSolve` answers where Phase 7 recorded a refusal** -- the
  difference is that the app now has a triangle. Its entry had named this
  exact probe as unverified. Expect `DoInference` and `Do1VStats` to behave
  the same and do not write it down until they have
- **An unset side or angle reads −1, not 0** (measured 2026-09-14). A
  program testing for 0 to find out whether a value is known is wrong on
  every fresh app. `TriType` is the exception at 0, and it is also the only
  variable `DoSolve` did not write
- **`SOLVE` is not the callable form `Solve` lacked** (measured
  2026-09-14). All four forms refused, the bare read included. Phase 7's one
  silent group stays silent and the likeliest explanation is gone
- **`Xlist` answers under both app conditions and nothing explains it**
  (measured 2026-09-14): `{}` with the Function app active and `{}` with the
  Triangle Solver active, while every other variable of another app refused.
  Whether other variables ignore the rule the same way is untested

- **Ask before pushing to GitHub.** `redo` became `main` on 2026-09-14 at the user's word: `main` was an ancestor of `redo`, so it moved by fast-forward with nothing discarded and no force, 104 commits landed on `origin/main`, and `redo` was deleted locally and on the remote. `main` is now the published default branch, so the caution that applied to `redo` applies to it -- and more, because this is the branch people see
- **Commands that receive their data answer; commands that read their app's
  state do not** (measured 2026-09-14). `DoInference`, `DoSolve` and
  `Do1VStats` take nothing or an empty data set and all three refuse, while
  every `inference` command handed two lists answers. It holds across every
  group of phase 7 and explains four groups that answered nothing at all.
  **Overturned 2026-09-14 in Phase 8 for two of the three**: `DoSolve` and
  `DoInference` both answer once their own app is active. The refusals were
  the wrong app -- every untouched batch has the Function app active -- and
  not the shape of the command. `Do1VStats` is untested that way
- **An app's functions answer only while its app is active** (measured
  2026-09-14 on the user's G2, firmware 2.4.15515). Selecting the app is
  enough; the call need not be typed inside it. `SSS(3,4,5)`,
  `SUM({1,2,3})` and `ROOT(F1,1)` all answer on Home with their own app
  active and are refused otherwise. That turns 31 phase 7 refusals from a
  defect into a condition, and explains why no batch could measure them: the
  harness resets the calculator before each run and cannot select an app.
  Now `apps.function-needs-active-app`. Three names are recorded with it as
  exceptions: `Solve`, `Solve2×2` and `Solve3×3` refuse with their own app
  active, and `Solve2×2` is a syntax error rather than a refusal. The rule is
  also necessary but not sufficient -- 18 of the 22 `spreadsheet` names still
  refuse with the app open
- **The Triangle Solver answers in degrees** (measured 2026-09-14), while
  everything else measured here is in radians. `SSS(3,4,5)` gives
  `{36.8698976458,53.1301023542,90}`, matching degrees to ten figures and
  summing to 180. A program chaining that into a trigonometric function is
  wrong by a factor near 57 with nothing raised. Now
  `apps.triangle-solver-degrees`
- **Still untried with their app active: 27 of the 49 silent names**, in
  `geometry` 13, `finance` 4, `inference` 3, `statistics-1var` 3 and
  `statistics-2var` 4. Their entries record the batch refusal and point at
  the rule rather than assuming it would not have helped. The other 22 silent
  names were retried with the app active and refused anyway, which makes them
  measured negatives: 18 in `spreadsheet`, plus `DoSolve`, `Solve2×2`,
  `Solve3×3` and `Solve`. `solve` is the one group left answering nothing at
  all, and it has one name
- **`S1` cannot be assigned from a batch and `F1` can** (measured
  2026-09-14), though `F1` stores the evaluated value rather than the
  expression: `F1:=X^2-4` leaves `F1` holding -4. **Settled 2026-09-14: the
  quote is the whole difference.** `F1:='X^2-4'` stores the expression
  itself, type 8, and so does `F1:="X"` as a string -- both come back as
  expression objects rather than numbers. With that, a batch fills `F1`
  unaided, the Function app is already active on a reset calculator, and
  `ROOT`, `EXTREMUM`, `ISECT`, `SLOPE` and `AREA` all answered from one
  batch with no keypresses at all. `S1` has had no such round, so
  `statistics-2var` is still blocked, and the same quoting is the obvious
  first thing to try there
- **Three families have their plainest constructor broken** (measured
  2026-09-14): `line` while `segment` and `half_line` answer, `triangle`
  while its eight polygon neighbours answer, and `plotparam` while
  `plotfunc` and `plotpolar` answer by building one. Three gaps, each at the
  name a reader reaches for first. Worth carrying into Phase 8 as something
  to expect rather than to rediscover
- **The calculator corrects HP's published syntax in words** (measured
  2026-09-14): `translation` replies that its first argument must not be a
  point, and `perpendicular` that it expects three points. Both times the
  machine was more precise than the list, and both replies arrived as text
  rather than as refusals
- **`Apps` answers the calculator's app names in its own language**
  (measured 2026-09-14), as a list of strings cut at 160 characters. A
  program comparing them against English names matches nothing
- **Two families have their plainest constructor broken** (measured
  2026-09-14): `line` is refused while `segment` and `half_line` answer, and
  `triangle` is refused while its eight polygon neighbours answer. Both cost
  other entries their evidence -- four commands were refused on arguments
  `line` had built, and `perimeter` on a `triangle` that was never made.
  Three of those four recovered when rebuilt with `segment`
- **Two geometry tests answer a code rather than a truth** (measured
  2026-09-14): `is_isosceles` answers 3 and `is_parallelogram` answers 4,
  while `is_equilateral` answers 0 for a false case. A comparison against 1
  never fires; testing the answer for truth works
- **Every polygon closes its ring** (measured 2026-09-14): the first vertex
  is repeated at the end, so a triangle answers four points and a square
  five. Counting vertices as given overstates every figure by one
- **A Result cell holding U+E003 has to be written by a script, not typed**
  (measured 2026-09-14). Editing `affix.md` by hand to add the imaginary unit
  produced a no-op: the replacement came back byte-identical to the original,
  because the private-use codepoint does not survive the editing channel. The
  accented U+00E1 in the geometry error strings does survive, and matched its
  stored row first time, so the limit is private-use characters rather than
  non-ASCII in general. The working method is to read the row from
  `results.tsv` and substitute it programmatically, which is what the entry
  format already required -- build such a cell from the stored row, never type
  it. The same applies to U+03C0, U+2212, U+221A and U+1D07 wherever they
  appear in a Result column
- **A stored row carries the date the batch was prepared, not the date it
  ran** (noticed 2026-09-14). `collect()` writes `state['date']`, which
  `prepare()` stamped when the program was sent, so a batch prepared before
  midnight and run after it gives rows dated the day before the keypresses.
  The first geometry batch is the case: its 25 rows say 2026-09-13 and the
  measurements were made on the 14th. Nothing is wrong with the data and the
  dates here say the truth about when each fact was measured, so a reader
  comparing the two will find them one day apart. Worth deciding later
  whether `collect()` should stamp its own date instead, which is a change to
  the tool and goes through its own decision
- **The seven-group probe: two groups answer, four are unresolved, and none
  is shown unreachable** (measured 2026-09-13). `inference` answers --
  `Chi2TwoWay` of a two-by-two matrix gives a list of three and
  `AnovaOneWay` of two lists gives a list of eight, both type 6 -- and
  `statistics-1var` answers, `ISCHECK(1)` giving 0. Refused were
  `Do2VStats(S1)`, `ROOT(F1)`, `SSS(3,4,5)`, `LinSolve` of an augmented
  matrix and the bare `Solve`. **Those five are not evidence about their
  groups**: two of them name app variables that a reset calculator leaves
  empty, and three have argument shapes nobody has confirmed. Unlike
  `spreadsheet`, where 22 of 22 fell including plain lists, nothing here
  rules a group out, and the entries must not say it does
- **A command can report its failure as text rather than raising**
  (measured 2026-09-13): `residue(1/X,X,0)` answers the string
  `"residue(1/X,X,0) 
 Error: valor de argumento incorrecto"`, type 2, 58
  characters, in the calculator's own language. It is not an `*error*` row --
  the call was accepted and handed back a description of the failure. If other
  commands do the same, it changes how every stored `*error*` row should be
  read, and whether a program can tell a failure from a value at all. Worth
  one probe: the same shape of bad argument on two or three other names
- **The 160-character width was already measured in Phase 6, and three
  documents said otherwise until 2026-09-13.** `SVD([[1,2],[3,4]])` comes back
  truncated with its row marked, 184 characters stored once the marker is
  counted, and `matrix/SVD.md` and `matrix/SVL.md` write it up. `QR`, `LQ`,
  `SCHUR` and `EIGENVV` sit just under at 152, 139, 124 and 107. The narrow
  truth, which is what the summaries now say, is that no phase 7 batch has
  produced an answer long enough to reach the limit. `AnovaOneWay` cannot
  force one: it answers eight numbers for two lists and eight for four, so its
  length is fixed by the statistic and not by the input
- **Reporting a failure as text is common, and a claim of mine said the
  opposite** (measured 2026-09-14, correcting 2026-09-13). The first geometry
  batch returned seven answers carrying an error message as data, in three
  different types: `equation`, `parameq`, `perimeter`, `single_inter` and
  `perpendicular` as strings of type 2, `inter` as a list of type 6 holding
  one, and `parallel` as a type 8 object with the message **inside** it --
  `line\(y="Error: entrada no válida"\)`. So `residue` was not a
  special case. The earlier bullet, which closed this question in the
  negative on the strength of `Chi2GOF` and `LinRegrTTest` answering a plain
  `*error*`, was wrong: those two refuse, and plenty of others do not. **A
  program cannot assume a failure arrives as a refusal**, and a caller
  checking only for an error will take a string or a list as a value
- **The error text is in the calculator's language** (measured 2026-09-14).
  Six of those answers carry U+00E1, the accented letter of `válida`.
  The message is Spanish because this machine is, so the text is not a stable
  property of the command and no entry should quote it as though it were
- **`arcLen(X^2,0,1)` answers 1, and the arc is about 1.4789**
  (measured 2026-09-14). A plausible wrong number from a call that succeeded,
  which is the same shape of trap as `LineTan` collapsing its expression. The
  probe is an arc whose length is a whole number by construction
- **`line` is refused where `segment` and `half_line` are not**
  (measured 2026-09-14): all three were given `point(0,0)` and `point(3,4)`,
  and the other two answered with an object naming themselves
- **`perpendicular` says it expects three points** (measured 2026-09-14),
  answering `"se esperan 3 puntos ..."`, while HP's published syntax is
  `perpendicular(Point, Line)`. The machine and the help disagree, and the
  machine is the one that runs
- **Four groups are now refused on two argument shapes each** (measured
  2026-09-13): `SSS(3,4,5)` and `AAS(30,60,10)`; `LinSolve` of an augmented
  matrix and of a square one; `Solve` bare and as `Solve(X^2-4=0,X)`. Two
  shapes is evidence about `triangle-solver`, `linear-solver` and `solve`
  rather than about the calls, which one shape was not. **Two of the three
  were overturned on 2026-09-14** once the app was active: five of six
  `triangle-solver` names answer, and `LinSolve` answers `{2,1}`. What two
  shapes established was that the calls were not the problem, and they were
  not -- the missing app was. `solve` held: five forms, all refused
- **The probe meant to free `ROOT` and `Do2VStats` did not do its job**
  (2026-09-13). Both were called after a setup expression meant to fill `F1`
  and `S1`, and both were still refused -- but the batch never measured
  whether the setup itself worked, so an empty variable and an unreachable
  group are still not separated. The fix costs one row each: return the
  variable's own value alongside, so the setup is measured rather than assumed
- **A whole group can be unreachable from Home, and `spreadsheet` is one**
  (measured 2026-09-13). All 22 of its names were refused, including
  `AVERAGE` and `SUM` given a plain list, which need no cell, no range and no
  app state. The obvious explanation was refuted in the same batch: HP files
  these under `Toolbox App Spreadsheet`, but it files the four `explorer`
  names under `Toolbox App Explorer` the same way and those four answered. So
  the menu does not separate them and the cause is not established. Two
  probes, one batch each: the call written straight into a program rather
  than inside `EXPR`, and the call made from inside the app with a sheet open.
  **Settled 2026-09-14 by the second probe**: with the Spreadsheet active,
  `SUM`, `AVERAGE`, `CellHasData` and `ClearCell` answer and the other 18
  still refuse. So the group was never unreachable, and the remaining 18 are
  mostly statistics names wanting data an empty sheet does not hold
- **Plan the remaining groups with a short probe first.** `spreadsheet` cost
  a full 26-call batch to learn one fact that eight calls would have shown.
  119 names are left in phase 7 -- 84 `geometry`, 9 `inference`, 6 and 5 in
  the two statistics groups, 6 `triangle-solver`, 5 `function`, 3
  `linear-solver`, 1 `solve` -- and only `geometry` has been probed
- **The harness's 160-character width is still untested in phase 7**, after
  two batches. `STAT1`, `STAT2`, `REGRS` and `AMORT` were the candidates and
  all four are in the refused group; the longest answer so far is 7
  characters. `inference` returns matrices and is the next chance
- **`PercentMargin` and `PercentMarkup` are swapped** against the usual
  accounting meanings (measured 2026-09-13): cost 60 and price 100 give 66.67
  from the one called Margin and 40 from the one called Markup, where over the
  price is 40 and over the cost is 66.67. Both entries carry a
  `Models get wrong` table, because the plausible wrong number is the danger
- **The three finance commands taking dates are the three that were refused**
  (measured 2026-09-13): `DateDays`, `BondPrice` and `BondYield`, with dates
  written the way the Prime displays them, while all 31 plain-number commands
  answered. The probe is one call whose date the machine produces rather than
  this kit
- **`CashFlowMIRR` and `CashFlowFMRR` answer identically**, character for
  character, on the list tried (measured 2026-09-13). The probe that would
  separate them is a list turning negative again after the outlay
- **`ChangeNew` and `ChangeOld` answer what no simple reading explains**
  (measured 2026-09-13): 100 at ten per cent gives 10 rather than 110, and 110
  gives 1100. Their siblings `ChangePrice` and `ChangeCost` are proper
  inverses. The suspect is the undocumented third argument, and the probe is
  the same calls with other values for it
- **`BlackScholes` answers a list of two whose second element is exactly
  zero** (measured 2026-09-13), and HP's syntax row for it is truncated in
  `names.tsv` part way through the sixth argument, so the full argument list
  is not published in the data this kit holds
- **Nothing has yet tested a long structured answer against the harness's
  160-character width in phase 7.** The finance batch's longest answer was 17
  characters. `STAT1`, `REGRS` and the `inference` matrices are where it will
  matter
- **Geometry is measurable from Home, and the phase 7 risk is closed**
  (measured 2026-09-13). A probe of 9 calls settled it: `distance` of two
  points answers 5, so the functions that receive their arguments compute
  rather than echo, with no Geometry app open and on a calculator reset before
  the run. `slope` answers `1/2`, exact rather than decimal; `is_collinear`
  answers 1; `midpoint` of a segment answers `point(1,1)`, so nested objects
  work. Three kinds separate cleanly: argument-taking functions answer values,
  the view commands do not -- `zoomin` is an error -- and the plot commands
  answer a symbolic object rather than painting: `plotfunc(X^2)` comes back as
  `plotparam` over the default range, carrying both the imaginary unit U+E003
  and the real minus U+2212
- **`circle` takes its two points as a diameter, not centre and rim**
  (measured 2026-09-13): the area of the circle through the origin and 1,0 is
  a quarter of pi, so the radius is a half
- **`QUOTE` does not stop `LineTan` collapsing** (measured 2026-09-13). The
  probe phase 6 named is answered and the answer is no: both
  `LineTan\(X^2,X,1\)` and the same call with `QUOTE` around the expression
  answer `line\(y=diff\(0,0\)*x-diff\(0,0\)\)`. Whatever evaluates the
  argument does it before `QUOTE` can hold it back, so the working form is
  still unknown
- **`NEG` and `INVERSE` refuse every form tried, and both probes failed**
  (measured 2026-09-13). `NEG(5)` and `NEG 5` are both refused, so the call
  shape and the prefix shape are gone and the working one is unknown.
  `INVERSE(4)` and `INVERSE([[1,2],[3,4]])` are both refused, which kills the
  interpreter's lead that the argument merely wanted to be a matrix. `NTHROOT`
  is settled by contrast: `3 NTHROOT 8` answers 2, so it is infix like `MOD`
- **The four upper-tail commands are refused**, `UTPC`, `UTPF`, `UTPN` and
  `UTPT`, each written with HP's own published argument list. All four were
  reached through `EXPR` on Home, which is what they share; the probe is one
  direct call inside a program, and `UTPN` carries the explanation
- **`LineTan` answers a collapsed expression** rather than a tangent, because
  what it is handed is evaluated before it sees it. The probe is `QUOTE`
  around the expression, or a variable holding nothing
- **The compiler names the last bad line, not the first**, which is why three
  rounds of the user's keypresses each accused a call that an earlier round
  had appeared to clear. Now a fact,
  `ppl.check-last-error` in docs/topics/ppl.md, labelled emulator. The
  direct confirmation -- one program carrying two deliberate errors far apart
  -- has not been run and would cost a single round
- **A batch is refused whole, so a doubtful call goes inside `EXPR("...")`**
  (2026-09-13): the compiler stops at the first line it cannot read and the
  other calls die with it, which cost two rounds of the user's keypresses for
  nothing. `EXPR` takes a string, so it compiles whatever it holds and fails,
  if it fails, at run time -- where the harness's `IFERR` already catches it
  and marks that row alone. Probing an unknown form belongs in a string; a
  direct call is for a form already proven
- **One undecodable cell loses a whole batch** (measured 2026-09-13):
  `valuation(X^2+X)` answered negative infinity -- bytes
  `F3 91 99 99 99 99 99 29`, exponent 499, a mantissa of nines, sign nibble
  2. Measured 2026-09-13 by asking for it as text and as a type instead:
  `STRING(...)` answers `"-Inf"` and `TYPE(...)` answers 0, an ordinary
  real. So nibble 2 marks an infinity where 9 marks an ordinary
  negative, and `decode` knows neither. Measured again 2026-09-13 from the
  other side: `Dirac(0)`, which is positive infinity, answers the same
  exponent 499 and mantissa of nines with sign nibble **6**, and it killed a
  24-call batch the same way. In the same batch `MAXREAL` decoded cleanly at
  9.99999999999E499 -- the same exponent and mantissa with an ordinary sign
  nibble -- which is what says 2 and 6 mark infinity itself rather than
  magnitude. 23 of the 24 rows were recovered from M9.hpmat afterwards. `numbers.decode`
  accepts only 0 and 9 as the sign nibble, so it raised, and `collect()`
  raised with it before writing a single row: 17 calls and a round of the
  user's keypresses lost to one cell. The 16 good rows were recovered
  afterwards by reading M9.hpmat directly, which is what says the data was
  there all along. Two things to decide, both changes to the tool: whether
  `decode` should learn sign nibble 2, and whether `collect()` should keep
  the rows it can read and mark the ones it cannot instead of abandoning the
  batch. The second matters more -- it is the difference between losing one
  answer and losing seventeen
- **The interpreter drops the rest of an expression after an unknown infix
  operator** (measured 2026-09-13): `9 MOD 4` answers 9, and `9 MOD 4 + 100`
  answers 9 as well, with no error. `MOD` is the case that found it -- the
  builtin `_b_mod` is correct and answers `MOD(9,4)` as 1, but the parser has
  no infix `MOD`, so it evaluates the left operand and discards what follows.
  That is a silently wrong answer rather than a refusal, which is worse than
  the traceback above it, and it is the only form the calculator compiles.
  Whether other unknown infix words behave the same has not been checked.
  Fixing it is a change to the parser and goes through its own decision
- **`hpprime run` leaks a Python traceback on legal PPL** (measured
  2026-09-13): `CONCAT({1,2,3},4)` and `FLOOR({3.2,-3.2})` exit 1 with
  `TypeError: 'float' object is not iterable` and `must be real number, not
  list`. The builtins at `hpkit/interp.py:1418` and `:1427` are lambdas that
  do not check their arguments. The interpreter's own `--help` promises that
  anything not covered *raises* rather than inventing a result, and raising is
  right -- a Python stack trace is not. `docs.evaluate` classifies these as
  `uncovered`, which is a note and not a problem, so the documentation
  pipeline tolerates what the command line crashes on. Eight of HP's own
  worked examples for Phase 6 names hit it: CONCAT x3, the list forms of
  CEILING, FLOOR, FP and IP, and ROUND with a list of places. Fixing it is a
  change to the tool and goes through its own decision rather than riding
  along with a page
- `GETPIX`, `PIXON` and `PIXOFF` without `_P` answered `#FF000000h` all three
  times, including a read of a grob filled red (2026-09-12). The write and the
  read disagree, or both land off the picture; nothing measured separates them.
  The probe: paint with `PIXON` and read back with `GETPIX_P`, which does not
  share the mistake
- `SUBGROB` without `_P` is refused where `SUBGROB_P` cuts and allocates
  (2026-09-12). Either the rectangle falls outside the grob, or this form does
  not create its target. Creating `G3` first separates them
- `HMS→(1.3)` answers `1.3`, its argument unchanged, while `→HMS(1.5)` answers
  `1°30′00″` and converts (2026-09-12). The round trip `HMS→(→HMS(1.5))` is
  the probe
- `ADDCOL` and `ADDROW` now refuse nine forms. The explanation both entries
  named as likeliest -- that they change a variable rather than answering a
  copy -- was tested on `M1` and is refuted (2026-09-12). Untried: a vector
  rather than a list, and a position inside the matrix
- `TEXTOUT` answers 182 where `TEXTOUT_P` answers 19 for the same string. The
  factor of ten measured for the drawing units does **not** explain it: 182/19
  is about 9.6, not 10. Both are measured; neither is explained
- What a bare `=` does as a **statement** is the one case left where it could bite: `a = 2;` where `a := 2;` was meant might compare and throw the answer away, doing nothing at all. Inside a condition it is measured harmless (2026-09-12): it compiles and it compares. One hand-written program answers it, since the harness lints what it sends
- `ppl.locals-initialised-one-line` is settled (2026-09-16, plan 09-01): the row plan 05-01 stored for it on 2026-09-12 answered 5, and nobody had written it into the fact. It is `emulator` for two locals initialised on one line; three has not been run. `ppl.equality-operators` and `ppl.end-semicolon` are now `emulator` -- the first of them cost the `equality` rule, which flagged legal code -- and `BREAK 2` was measured, with the interpreter changed to follow it
- CHECK-04's open half: which of the 108 facts a PC could catch and no lint rule does. Wants the entries of Phases 5 to 8 first
- What the header words at 20 and 44 of an `.hpprgm` mean
- `TYPE` answers 0 for a number, 2 for a string, 4 for a matrix and 6 for a list, measured by the two batches; the interpreter has no `TYPE`, and does not grow in Milestone 1, so `SIZE`'s entry keeps that in a paragraph instead of an example
- Whether `agrees()` should treat `[2 3]` and `{2,3}` as the same value, which it does today

### Blockers/Concerns

- A program copied into the emulator's folder has to be compiled once, with the editor's Check, before its name works on Home (measured 2026-09-06): each batch of examples costs some keypresses on the emulator
- HP's sources live in the session scratchpad, outside the repository; `tests/hp_examples_extract.py` and `tests/names_extract.py` say how to get them again

## Session Continuity

Last session: 2026-09-27
Stopped at: plan 11-02 complete, and 11-03's download prepared. Local `main` fast-forwarded on 2026-09-27 to GitHub's c8951ab "Update LICENSE". Milestone 2's definition, the replanning, 11-01 and 11-02 are uncommitted. Suite 14,904 passed, 0 failed
Resume with: plan 11-03's GitHub leg. The download was tried on 2026-09-28 (`11-03-SUMMARY.md`): a fresh session loaded `AGENTS.md`, read `docs/llms.txt`, built `RELOJ` in `programs/RELOJ/` through the gates and touched nothing else, and the app ran on the emulator once compiled. Waiting for the user's word to commit and push; then GitHub's ZIP and `hpprime update` against it, and Phase 11 closes.
