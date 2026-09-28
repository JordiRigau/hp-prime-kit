# hp-prime-kit

A reference for programming the HP Prime in which every claim says how it is
known, and the tools to write, check and install programs from a PC. It is
written for a person learning the calculator and for an AI writing PPL beside
one.

The Prime is programmable and thinly documented. Its compiler reports `syntax
error` and a line number and nothing else; a Python app that meets something
it cannot handle closes with no message. An assistant does not make that
easier: there is little PPL in public code for a model to have learned from,
so it writes syntax that reads well and does not compile, and states limits
that nobody measured. This reference records what was measured, on a
calculator or on HP's Virtual Calculator, and says so where nothing was.

---

## The documentation

One entry per PPL name, with its syntax, examples carrying the calculator's
own answers, how it behaves and what models get wrong; and the facts about
the platform that no single command owns, from the limits that break
compilation to the screen, apps, Python, the file formats and getting a
program onto the calculator.

Every claim carries one of four labels, strongest first
([format.md](docs/format.md#how-each-claim-is-known)):

| Label | Means |
|---|---|
| `G2` | measured on a physical HP Prime G2 |
| `emulator` | run on HP's Virtual Calculator, with the answer kept in [results.tsv](docs/commands/results.tsv) |
| `HP help` | stated in the calculator's built-in help |
| `unverified` | none of those, and it says where it came from |

Where it stands:

- **Entries.** 706 of the 706 names that get an entry have one: every
  statement, command and Home function, all 179 app functions, all 172 app
  variables, all 65 variables of Home and the system, and `GET`.
- **Examples.** Of the 1149 examples, 1128 have the Virtual Calculator's answer
  on file, 4 were measured by hand on a G2, and 17 have no value to record,
  with the reason in their entry. None is unrun, and the tests fail if one
  ever is.
- **Facts.** 122 facts about the platform: 76 measured on a G2, 26 on the
  emulator, and 20 unverified, which say so.

### Where a person starts

[The guided path](docs/start/01-setup.md): six steps from an empty folder to a
program running on the calculator, linking to the facts as it uses them.

| | |
|---|---|
| [1. What you are getting into](docs/start/01-setup.md) | the machine, the two languages, program against app, what to install |
| [2. Your first program](docs/start/02-first-program.md) | empty file to running on the calculator, and what breaks on the way |
| [3. Asking for data and drawing](docs/start/03-input-screen.md) | `INPUT`, keys, text that fits |
| [4. Wrapping it as an app](docs/start/04-first-app.md) | the icon, and the byte that decides which screen opens |
| [5. Moving to Python](docs/start/05-python.md) | the bridge to PPL, and two traps that cost a day each |
| [6. Working with an AI](docs/start/06-working-with-ai.md) | the loop, and what not to accept from a model |

### Where a model starts

[`docs/llms.txt`](docs/llms.txt): every entry and every fact on one line, with
its link and a one-line summary, kept under 100,000 bytes so it can be loaded
whole. A model cites a fact by its identifier, such as `ppl.local-limit`, and a
command by its name. Whether a name exists at all is in
[`names.tsv`](docs/commands/names.tsv), HP's own list.

### The reference

| | |
|---|---|
| [commands](docs/commands/index.md) | the entries, by name and by group |
| [ppl.md](docs/topics/ppl.md) | the language: the limits that break compilation, and the restrictions that look reasonable and do not exist |
| [interface.md](docs/topics/interface.md) | screen, keyboard and touch: `INPUT`, the key map, the touch that arrives twice |
| [libraries.md](docs/topics/libraries.md) | building an interface: which level a screen needs, and what the published libraries provide |
| [apps.md](docs/topics/apps.md) | the `.hpappdir`, the hooks, the startup-view byte, and the apps whose functions need them active |
| [micropython.md](docs/topics/micropython.md) | Python on the calculator, the bridge to PPL, and the call that closes the app |
| [formats.md](docs/topics/formats.md) | the binary container and the internal number format, both decoded, and what is still not |
| [deploy.md](docs/topics/deploy.md) | getting it onto the calculator: the emulator folder you can write into, and the two traps of the one you cannot |

## The tools

One command, `hpprime`, [documented here](docs/tools.md). Python 3.7 or
newer, no dependencies, nothing to install.

```bash
git clone https://github.com/JordiRigau/hp-prime-kit
cd hp-prime-kit
python hpprime.py doctor          # is this machine ready?
```

The whole cycle is five commands, run from that folder. They are written here
the short way: `.\hpprime` in PowerShell, `./hpprime` on macOS and Linux, or
`python hpprime.py` anywhere.

```bash
hpprime new CIRCLE
hpprime lint    programs/CIRCLE/CIRCLE.txt
hpprime run     programs/CIRCLE/CIRCLE.txt --call "CIRCAREA(2)"
hpprime write   programs/CIRCLE/CIRCLE.txt -o programs/CIRCLE/CIRCLE.hpprgm
hpprime install programs/CIRCLE/CIRCLE.hpprgm --restart
```

`new` writes a starter that already runs in a folder of its own under
[`programs/`](programs/README.md), where what you make goes and git keeps out.

The last line installs into the emulator and opens it, with nothing to drag. On
a physical calculator that step is a drag onto it in the Connectivity Kit
window. [deploy.md](docs/topics/deploy.md) covers both.

| | |
|---|---|
| `hpprime doctor` | what works on this machine, and what to do about what does not |
| `hpprime new` | a starter that already compiles and runs |
| `hpprime update` | a downloaded copy brought to the latest version, your `programs/` untouched |
| `hpprime lint` | each finding names the fact it comes from and how that fact is known, and is an error only as far as the measurement reaches |
| `hpprime run` | runs PPL on your PC: the file you install, through an interpreter that raises on what it does not cover |
| `hpprime write` / `read` | the `.hpprgm` binary, both directions |
| `hpprime build` / `verify` | apps: build the folder, and catch it drifting |
| `hpprime install` / `pull` | into the emulator, and back out of it |
| `hpprime emu` | calculators to experiment on, and put back |
| `hpprime compare` | the same call here and on the calculator, side by side |
| `hpprime matrix` | `.hpmat` files: a whole matrix as a file, nothing pasted |
| `hpprime docs` / `examples` | the documentation held to its format, and its examples run on the Virtual Calculator |

If the same calculation exists twice, in PPL for the calculator and in Python
to develop against, no ordinary test will tell you the two have drifted apart.
Running the real PPL and comparing the answers is what surfaces the
difference, and there is a runnable example, with a mode that introduces a
divergence so you can see what one looks like:

```bash
python examples/conformance/conformance.py --break
```

## Working with an AI

Download this repository -- on GitHub, **Code**, then **Download ZIP**, and
unzip it -- or clone it. Open the folder in your assistant: Claude Code (the
Code tab of the Claude desktop app), Cursor, Codex or Copilot, and say what you
want the calculator to do. The only thing to install is Python 3.7 or newer.
Your programs go in [`programs/`](programs/README.md), one folder each, which
git ignores.

The assistant starts at [`docs/llms.txt`](docs/llms.txt), and at
[`AGENTS.md`](AGENTS.md), which Claude Code, Cursor, Copilot and Codex read by
themselves when this folder is open. It says what to read first, the two gates
every program goes through, what not to claim without evidence, and what only a
person can do.
A chat with no file access gets [`docs/ai/prompts.md`](docs/ai/prompts.md) §1
pasted in, where every rule names the fact it comes from.
[Step 6 of the guided path](docs/start/06-working-with-ai.md) is the version
for the person on the other side.

## What it does not do

- **Draw the interface.** `INPUT`, `CHOOSE`, `TEXTOUT_P` and the rest are
  recorded rather than painted, so a program with a screen runs end to end
  here, but seeing it needs the emulator.
- **Run MicroPython.** The `hpprime.eval` bridge exists only on the
  calculator. What you can do is write the engine so that the file which
  computes is the same file in both places; see
  [micropython.md](docs/topics/micropython.md).
- **Generate a program's compiled block**, which it does not need to. That
  block is a cache the calculator rebuilds from the source
  ([formats.block-is-a-cache](docs/topics/formats.md#formats.block-is-a-cache)),
  so a program carrying data is generated like any other. How long a large one
  takes to compile on arrival has not been measured.
- **Install on a physical calculator.** That step is a drag onto the
  calculator in the Connectivity Kit window, and the CK's mirror folder is not
  a mailbox. The emulator is different: its folder is a real one, so
  `hpprime install` does the whole job
  ([deploy.emulator-folder](docs/topics/deploy.md#deploy.emulator-folder)).
- **Replace testing on the calculator.** It cuts the number of round trips;
  the last one is still a real Prime. `hpprime compare` runs the same calls in
  both places and brings the calculator's numbers back as a file.

## Status

Reference firmware: G2, 2.4 revision 15515 (2025-09-15). The examples run on
the Virtual Calculator 2.4, build 2025-09-15.

Both paths have been run on a real G2: a program built from the template this
repository ships
([deploy.writer-on-hardware](docs/topics/deploy.md#deploy.writer-on-hardware)),
and an app built end to end by `hpprime build --ppl`
([apps.generated-and-verified](docs/topics/apps.md#apps.generated-and-verified)).

```bash
python tests/run_all.py     # fourteen suites, none of them needs a calculator
```

Open, and listed here so that nobody relies on them:

| | |
|---|---|
| G1 | everything here was measured on a G2 or its emulator. Same firmware, different hardware |
| MicroPython speed, and an app's memory limit | not measured. The bridge crossing is 0.2 ms |
| `.hplist` | lists as files are neither read nor written. Same family as `.hpmat`, with the type byte in the same slot, `0x16` against `0x14`, but every `.hplist` seen here is empty, and the format will not be guessed from those |

If you measure something new, or build something with this, see
[CONTRIBUTING.md](CONTRIBUTING.md). A fact with its evidence is welcome even if
the prose needs work.

## Licence

MIT. See [LICENSE](LICENSE).
