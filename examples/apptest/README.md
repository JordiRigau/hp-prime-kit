# Verifying a PPL app on hardware

Everything else in this kit is validated: the linter's rules are measured,
the interpreter is tested against its subset, and a program built from
`templates/code.hpprgm` has been loaded onto a G2 and computed correctly.

One path is not. **A PPL app assembled end to end by `hpprime build --ppl`
has never been opened on a calculator.** Its pieces are each validated
separately -- the blank descriptor comes from an app that works, and the
program writer is proven -- but the combination is not, and this repository
says so wherever it matters.

Closing that gap takes about five minutes and a calculator. If you do it,
please report what happened.

---

## Build it

```bash
hpprime build APPTEST examples/apptest/APPTEST.txt --ppl
```

That gives you `APPTEST.hpappdir/` with four files: the two wrappers, the
empty note, and a `.hpappprgm` carrying the source. You can confirm the
source really made it in before you go near the calculator:

```bash
hpprime read APPTEST.hpappdir/APPTEST.hpappprgm | head -20
hpprime verify APPTEST.hpappdir
```

## Install it

1. Open the **Connectivity Kit** with the calculator connected. The
   **Virtual Calculator** counts for most of this, but the interesting part
   -- what the keyboard does -- is worth doing on physical hardware.
2. **Drag the whole `APPTEST.hpappdir` folder** onto the calculator in the CK
   window. Not into the `Calculators\` folder: that is a mirror, and it
   installs nothing ([why](../../docs/reference/deploy.md)).
3. On the calculator: `[Apps]`.

## The five things to look at

The app prints them in order, numbered, so you only have to read the screen.

| | What you should see | What it proves |
|---|---|---|
| **0** | `APPTEST` appears in the `[Apps]` list, and opening it draws a screen | the calculator accepts a `.hpappdir` built entirely on a PC, and `START()` is called |
| **1** | `the program is inside, and computes: 385` | the source really is inside the `.hpappprgm`, and it compiled |
| **2** | `accents: àèóç`, all four correct | UTF-16LE survived the container, the transfer and the app wrapper |
| **3-4** | press a key, and it reports a code | the keyboard reaches an app with no view of its own |
| **5** | press again: the app leaves and you land on **Home** | the documented blank-app behaviour: `START()` returning drops you to Home |

Two things worth trying while you are there, because they are documented as
traps and nobody has confirmed them for an app built this way:

- **Press `[Num]` and `[View]` at step 3.** They are expected *not* to reach
  the program: a blank app has no view to rest in. If one of them does
  something, that is a finding.
- **Leave the app and reopen it.** It should draw its own screen again, not
  something else. Then, if the CK brings the folder back to your PC, run
  `hpprime verify APPTEST.hpappdir` -- it should report that the calculator
  rewrote the wrappers, which is the failure the builder exists to prevent.

## What to report

Whichever way it goes, it is worth writing down. Open an issue or a PR
saying:

- the calculator (G1 or G2) and the firmware version;
- which of the numbered steps you saw, and where it stopped if it did;
- what `[Num]` and `[View]` did;
- if it failed: what the screen said, word for word.

A failure here is more valuable than a pass, because it is the last unproven
link in the chain. If it passes, the two places that currently say "not
tested on hardware" -- [`docs/reference/apps.md`](../../docs/reference/apps.md)
§8 and [`docs/start/04-first-app.md`](../../docs/start/04-first-app.md) -- get
to say something better.

## Note for testing on the PC

`hpprime run` will execute `ATSUM()` and give you 385. Do **not** ask it for
`START()` or `ATWAIT()`: the interpreter records `GETKEY` as "no key
pressed", so a loop waiting for one never ends. Waiting for input is exactly
the kind of thing that only means something on the calculator.
