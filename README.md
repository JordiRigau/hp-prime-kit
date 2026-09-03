# hp-prime-kit

Make your own programs and apps for the **HP Prime**, with an AI helping and
without flying blind.

The Prime is programmable and badly documented. Its compiler answers `syntax
error` and a line number; a Python app that does something it dislikes closes
without a word. So people paste, compile, look, and repeat -- and an AI
assistant, with almost no PPL to have learned from, guesses confidently and
sends you back to the calculator.

This kit removes that loop. **Write the code on your PC, lint it, run it, and
build the binary** -- all without a calculator -- and keep the measured facts
about the platform in front of both of you.

Python 3.7 or newer. No dependencies, nothing to install.

---

## Start

```bash
git clone https://github.com/JordiRigau/hp-prime-kit
cd hp-prime-kit
python hpprime.py doctor          # is this machine ready?
```

Then the whole cycle, four commands:

```bash
hpprime new CIRCLE                     # a starter that already runs
hpprime lint CIRCLE.txt                # what the compiler will not explain
hpprime run  CIRCLE.txt --call "AREA(2)"   # run the real file, here
hpprime write CIRCLE.txt -o CIRCLE.hpprgm  # build the binary
```

and drag `CIRCLE.hpprgm` onto the calculator in the Connectivity Kit window.

**Never done this before?** → **[The guided path](docs/start/01-setup.md)**.
Six steps from an empty folder to something running on the calculator,
including what will break on your first day and why.

**Using an AI?** Point it at **[`AGENTS.md`](AGENTS.md)** (Cursor, Copilot,
Codex, …) or **[`SKILL.md`](SKILL.md)** (Claude Code). Both load the same
rules, so it stops inventing syntax. If your assistant cannot read files,
paste [`docs/ai/prompts.md`](docs/ai/prompts.md) §1.

## What is here

**The path**, in order:

| | |
|---|---|
| [1. What you are getting into](docs/start/01-setup.md) | the machine, the two languages, program vs app, what to install |
| [2. Your first program](docs/start/02-first-program.md) | empty file → running on the calculator, and the eight things that break |
| [3. Asking for data and drawing](docs/start/03-input-screen.md) | `INPUT`, keys, text that fits |
| [4. Wrapping it as an app](docs/start/04-first-app.md) | the icon, and the byte that opens the wrong screen |
| [5. Moving to Python](docs/start/05-python.md) | the bridge to PPL, and the two traps that cost a day each |
| [6. Working with an AI](docs/start/06-working-with-ai.md) | the loop, and what not to accept from a model |

**The reference** -- what is measured on a G2, with the evidence beside it and
anything unconfirmed marked as such:

| | |
|---|---|
| [ppl.md](docs/reference/ppl.md) | the language: the limits that really break, and four hypotheses that look reasonable and are false |
| [interface.md](docs/reference/interface.md) | screen, keyboard, touch: `INPUT`, key codes, the touch that arrives twice |
| [apps.md](docs/reference/apps.md) | the `.hpappdir`, the hooks, the startup-view byte |
| [micropython.md](docs/reference/micropython.md) | Python on the calculator, the bridge to PPL, and the call that closes the app |
| [formats.md](docs/reference/formats.md) | the binary container and the internal number format, both decoded |
| [deploy.md](docs/reference/deploy.md) | getting it onto the calculator, which has two traps of its own |

**The tools** -- one command, [documented here](docs/tools.md):

| | |
|---|---|
| `hpprime doctor` | what works on this machine, and what to do about what does not |
| `hpprime new` | a starter that already compiles and runs |
| `hpprime lint` | nine rules, every one from an error measured on a G2 |
| `hpprime run` | **runs PPL on your PC** -- the file you install, not a copy of it |
| `hpprime write` / `read` | the `.hpprgm` binary, both directions |
| `hpprime build` / `verify` | apps: build the folder, and catch it drifting |
| `hpprime matrix` | `.hpmat` files: a whole matrix as a file, nothing pasted |

## Why running PPL on the PC matters

If you have the same calculation written twice -- in PPL for the calculator
and in Python to develop against -- no ordinary test can tell you they have
drifted apart: each one is consistent with itself and both pass their own
tests. Running the real PPL and comparing is what makes the divergence
appear, and the failures cluster around the region one side forgot.

There is a runnable example, with a mode that shows what a real divergence
looks like:

```bash
python examples/conformance/conformance.py --break
```

## What it does not do

- **It does not draw the interface.** `INPUT`, `CHOOSE`, `TEXTOUT_P` and the
  rest are recorded, not painted, so a program with a screen still runs end
  to end here. Seeing it still needs the emulator.
- **It does not run MicroPython.** The `hpprime.eval` bridge only exists on
  the calculator. What you can do is write the engine so the file that
  computes is *the same file* in both places -- see
  [micropython.md](docs/reference/micropython.md).
- **It does not generate a program's compiled block.** Programs carrying
  large matrices still get pasted once. The number format inside it *is*
  decoded, so matrices can travel as `.hpmat` files instead.
- **It does not install anything.** That last step is a drag onto the
  calculator in the CK window, and the mirror folder is not a mailbox.
- **It does not replace testing on the calculator.** It cuts the round trips
  down a lot; the last one is still a real Prime.

## Status

Reference firmware: **G2, 2.4 revision 15515 (2025-09-15)**.

A program built from the template this repository ships has been run on a
real G2: it compiles, computes and keeps its accented text
([the evidence](docs/reference/deploy.md#4-the-writer-validated-against-hardware)).

```bash
python tests/run_all.py     # eight suites, none of them needs a calculator
```

Deliberately still open, and listed so nobody leans on them:

| | |
|---|---|
| A **PPL app** built end to end by this kit | its pieces are validated separately; the combination has not been opened on hardware |
| The interpreter's **string functions** | left out: their edge behaviour is not measured, and guessing would defeat the purpose |
| **G1** | everything here is a G2. Same firmware, different hardware |
| MicroPython **speed** and an app's **memory limit** | not measured. The bridge crossing is: 0.2 ms |

Measured something new, or built something with this? See
[CONTRIBUTING.md](CONTRIBUTING.md) -- a fact with its evidence is welcome even
if the prose needs work.

## Licence

MIT -- see [LICENSE](LICENSE).
