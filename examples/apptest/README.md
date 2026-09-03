# Verifying a PPL app on hardware

This app exists to check, on the calculator itself, the one thing no PC can
check: that an app assembled entirely on a PC really opens and runs.

**It has been run.** On a G2, an app built by `hpprime build --ppl` appeared
under `[Apps]`, ran `START()`, reported `385` from the program inside it and
drew `àèóç` correctly. Two key codes came out of the same run: `[View]` is
**9** and `[Num]` is **11**, and both reach the program through `GETKEY` even
in a blank-based app that has no view of its own -- which corrected what this
repository used to say.

So this is no longer a gap to close. It is still worth running if you have a
**G1**, or if you want to settle the one number that is still ambiguous: 11
is both `[Num]` and what two published apps use as soft key 6. Press the six
on-screen soft-key positions in step 3 and the app will tell you what they
return.

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
| **3-4** | press a key, and it reports a code | the keyboard reaches an app with no view of its own. Measured this way: `[View]` 9, `[Num]` 11 |
| **5** | press again: the app leaves and you land on **Home** | the documented blank-app behaviour: `START()` returning drops you to Home |

Two things worth trying while you are there:

- **Press the six on-screen soft-key positions at step 3.** That is the open
  question: `[Num]` returns 11, and 11 is also what two published apps use as
  soft key 6. One measurement settles whether they are the same key.
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

A failure is more valuable than a pass. The G2 run above says this works on
one machine and one firmware; anything that contradicts it -- a G1, a
different firmware, a different key code -- is a real finding, and
[`docs/reference/apps.md`](../../docs/reference/apps.md) §8 and
[`docs/reference/interface.md`](../../docs/reference/interface.md) §5 are
where it would go.

## Note for testing on the PC

`hpprime run` will execute `ATSUM()` and give you 385. Do **not** ask it for
`START()` or `ATWAIT()`: the interpreter records `GETKEY` as "no key
pressed", so a loop waiting for one never ends. Waiting for input is exactly
the kind of thing that only means something on the calculator.
