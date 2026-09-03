# Working in this repository

For any AI agent -- Claude Code, Cursor, Copilot, Codex or another -- writing
HP Prime code with a human, or changing this kit itself.

The person you are working with probably cannot check your PPL by reading it.
The calculator will not help either: it answers `syntax error` and a line
number. So the burden of proof is on you, and this repository exists to let
you carry it without a calculator.

---

## 1. Before you write a line of PPL

**Read [`docs/reference/ppl.md`](docs/reference/ppl.md).** Sections 1 and 2
are the ones that matter: the limits that actually break compilation, and
four hypotheses that look reasonable and are false. Writing PPL from memory
means inventing restrictions that do not exist and missing the ones that do.

Then, depending on the task:

| Task | Read |
|---|---|
| the user has never programmed a Prime | [`docs/start/01-setup.md`](docs/start/01-setup.md) -- send them there before anything else |
| anything in PPL | [`docs/reference/ppl.md`](docs/reference/ppl.md) |
| screens, keys, touch | [`docs/reference/interface.md`](docs/reference/interface.md) |
| wrapping it as an app | [`docs/reference/apps.md`](docs/reference/apps.md) |
| writing it in Python | [`docs/reference/micropython.md`](docs/reference/micropython.md) |
| the binary formats, or moving a lot of data | [`docs/reference/formats.md`](docs/reference/formats.md) |
| getting it onto the calculator | [`docs/reference/deploy.md`](docs/reference/deploy.md) |
| every command | [`docs/tools.md`](docs/tools.md) |

The non-negotiables, as a checklist -- the full list with its evidence is in
`ppl.md`:

- 1-based everywhere. `L(0)` is a run-time error.
- `:=` assigns, `==` compares, `<>` is not-equal.
- `END` closes every block. `ENDIF`/`ENDFOR`/`ENDWHILE` do not exist.
- All `LOCAL`s at the top of the `BEGIN`, at most 7-8 per statement.
- You cannot index the result of a call: `SIZE(M)(1)` does not compile.
- Exported names are global and collide. Prefix them.
- On Home, a zero-argument function is called without parentheses:
  `MYFUNC`, not `MYFUNC()`. In source, the parentheses are right. Get
  this right whenever you tell somebody how to test on the calculator.

## 2. The workflow you must follow

Never hand over PPL you have not put through both gates:

```bash
hpprime lint FILE.txt                    # 0 errors, or fix and repeat
hpprime run  FILE.txt --call "F(2)"      # the right answer, not just no error
```

Then, and only then:

```bash
hpprime write FILE.txt -o PROG.hpprgm
```

`lint` catches what the compiler will not explain. `run` executes the actual
file -- if a command is not covered it raises rather than inventing a result,
so a clean run means something.

For an app, `hpprime build` and then `hpprime verify`.

If you have shell access, run these yourself. Do not ask the user to relay
output you could have obtained.

## 3. What you must not claim

> **Nothing works until a command says it does.**

- Do not say a program compiles. Say the linter is clean, and paste what it
  printed.
- Do not say it computes correctly. Say what `hpprime run --call` returned.
- Do not say it is installed. You cannot install anything: dragging the file
  onto the calculator in the Connectivity Kit window is the human's job, and
  the mirror folder is not a mailbox. See
  [`deploy.md`](docs/reference/deploy.md).
- Do not report a platform fact without evidence. If it is in
  `docs/reference/`, cite it. If you measured it, say how. If neither, say
  you are not sure. On this platform a confident wrong number is expensive,
  because nothing contradicts it until the calculator does.

## 4. When something fails

**An error that does not move after a fix means the hypothesis is false**,
not that the fix was too small. Change tack rather than trying a fourth
variation.

The method that works here is not reasoning about syntax:

> **Measure programs that already work on that same calculator, and
> compare.**

Two practical forms of that:

- If the linter is clean and the calculator still refuses the program, it is
  a case nobody has measured. Ask the user for the exact message and line,
  compare against code known to compile, and when you find it, add the rule
  (see §6).
- If a Python app closes on startup with no message, do not guess. The
  technique is a probe that leaves a mark in a PPL global after each step, in
  order of increasing risk -- [`micropython.md`](docs/reference/micropython.md)
  §5, with one ready in `examples/probe/`.

## 5. Time you will otherwise waste

- **hpmuseum.org blocks automated access.** It answers with a challenge you
  cannot pass. Do not try. For HP Prime material the source that does allow
  reading is **hpcalc.org**.
- **Reading somebody's working app beats any tutorial.** The event loop, the
  key codes and the menu geometry documented here all came from downloading
  apps and reading them.
- **`time` does not exist in MicroPython on the Prime.** If `import time`
  fails, the bridge is fine; the module is not there.
- **The Calculators folder is a mirror**, and it is often empty. That is not
  a broken installation.

## 6. If you change this kit

- **Everything is in English**: code, comments, messages, docs, commit
  messages.
- **Tests must pass**: `python tests/run_all.py`. None of them needs a
  calculator. If you add a rule or a builtin, add its case.
- **A new platform fact needs evidence** -- which program, which firmware,
  what was seen -- and goes in the reference page it belongs to. If it can be
  caught from the PC, it also gets a linter rule and a test. Unmeasured
  things are marked `Unverified`, not stated as fact. See
  [`CONTRIBUTING.md`](CONTRIBUTING.md).
- **One fact, one home.** If it is in `docs/reference/`, link to it; do not
  restate it. (The one deliberate exception is
  [`docs/ai/prompts.md`](docs/ai/prompts.md) §1, a context block for chats
  that cannot read files. It says so.)
- **No anecdotes, no achievement numbers, no narrative.** State the fact and
  how it is known.
- **Do not add dependencies.** Python 3.7+, standard library only, no install
  step.

## 7. What only the human can do

Say so plainly when you reach these, instead of implying you have done them:

- installing anything on the calculator;
- confirming a program runs **on hardware** (the last mile: the emulator is
  close, not identical, and everything in `docs/reference/` that is marked
  `Unverified` is waiting for exactly this);
- timing anything, and judging whether an interface is usable in practice.
