---
name: hp-prime
description: Write, review and deploy programs, apps and interfaces for HP Prime calculators (G1/G2), in PPL or MicroPython. Use whenever .hpprgm, .hpappdir, .hpapp or .hpappprgm files appear, or PPL code (EXPORT/BEGIN/END, LOCAL, TEXTOUT_P, INPUT, CHOOSE, DRAWMENU, GETKEY), or Prime Python (import hpprime, hpprime.eval, fillrect), or the HP Connectivity Kit or Virtual Calculator, or when data, calculation or an interface has to go onto an HP Prime.
---

# HP Prime

PPL is badly documented and its compiler only says `syntax error` with a line
number. This kit removes the two things that waste the most time: **guessing
the syntax** and **the paste-and-compile ritual in the Connectivity Kit**.

## Start here

**Read [`AGENTS.md`](AGENTS.md).** It is the operating contract for this
repository: what to read before writing PPL, the two gates every program goes
through, what you must not claim, and what only the human can do. It is short,
and everything below assumes it.

Then read [`docs/reference/ppl.md`](docs/reference/ppl.md) before writing a
line -- especially §2, four hypotheses that look reasonable and are false.

## The loop, in three commands

```bash
hpprime lint FILE.txt                  # what the compiler will not explain
hpprime run  FILE.txt --call "F(2)"    # run the real file, here, no calculator
hpprime write FILE.txt -o PROG.hpprgm  # build the binary
```

Then the human drags the `.hpprgm` onto the calculator in the Connectivity Kit
window. You cannot do that step, and copying into the mirror folder does not
work -- [`docs/reference/deploy.md`](docs/reference/deploy.md).

`hpprime doctor` checks the machine, `hpprime new NAME` writes a starter that
already runs, `hpprime build` makes an app, `hpprime verify` checks one.
Every command is in [`docs/tools.md`](docs/tools.md).

## If the user has never programmed a Prime

Send them to [`docs/start/01-setup.md`](docs/start/01-setup.md) before
anything else. It is a six-step path from an empty folder to something running
on the calculator, and step 6 is about working with you.

## Installing this skill

```bash
git clone https://github.com/JordiRigau/hp-prime-kit ~/.claude/skills/hp-prime
```

The repository *is* the skill: `SKILL.md` sits at its root, so any session that
touches `.hpprgm` files or PPL code has the measured rules in front of it
instead of improvising syntax.
