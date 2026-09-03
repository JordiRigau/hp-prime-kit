# Getting it onto the calculator

Everything else in this kit runs on your PC. This page is the one step that
does not, and it has two traps that cost an afternoon each.

---

## 1. The folder that looks like a mailbox and is not

**`Documents\HP Connectivity Kit\Calculators\<your calculator>\` is not a
drop box.** It is a **mirror** the Connectivity Kit writes *from* the
calculator. Leaving a file there with the CK closed installs nothing: on
connecting, the CK overwrites the folder with whatever is on the calculator
and your file disappears.

Verified the hard way: two corrected binaries were copied there, and the
emulator still opened the old version. The files left in the folder
afterwards were the ones the calculator had written, compiled block and all.

| Route | State |
|---|---|
| Drag the file from the file manager onto the calculator in the CK | **works** -- this is the way |
| Drag between calculators **inside** the CK | works |
| Paste the text into the CK's editor | works, but it is the slow road |
| Copy the file into `Calculators\<calculator>\` | **does not install**: it is a mirror, and the CK overwrites it on connecting |

So the procedure is:

1. Open the **Connectivity Kit** with the calculator connected (or the
   Virtual Calculator).
2. **Drag the `.hpprgm` file, or the whole `.hpappdir` folder**, from the file
   manager **onto the calculator** in the CK window.
3. On the calculator: `[Shift][Program]` for a program, `[Apps]` for an app.

## 2. If the drag is refused with the no-entry cursor

Symptom: you drag the `.hpprgm` onto the calculator, the no-entry symbol
appears and nothing happens. No dialog, no error.

**It is not the file.** The ten-second check is to drag a program the CK
itself wrote: if that is refused too, the problem is the environment.

The cause found here was that the Connectivity Kit had, in its compatibility
tab, **Windows 8 mode and "run as administrator"** enabled. Windows forbids
drag and drop between processes of different integrity levels (UIPI): the
file manager runs unelevated and cannot drop anything into an elevated
window. Clearing those two boxes makes the drag work.

Where to look: properties of the shortcut **and of the `.exe`** →
*Compatibility*. Careful when checking via the registry: the flag lives in
`HKCU\Software\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Layers`
with the executable path as the value name, but if the box is ticked on a
particular shortcut it will not appear there -- you have to look at the
`.lnk` you actually launch it from, which need not be the one on the desktop.

## 3. Do not trust that you installed it: read it back

The source can be pulled out of the installed binary, so it can be compared
with your repository:

```bash
hpprime read ".../Calculators/HP Prime/MYPROG.hpprgm" -o installed.txt
diff installed.txt ppl/MYPROG.txt
```

This is worth doing before trusting any result obtained on the calculator. It
is easy to fix something on the PC and forget to send it over -- that is how
you discover an installed app has been two commits behind the code you were
trusting.

## 4. The writer, validated against hardware

A program generated from Python -- a template's header, the source put in by
the kit, never touched by the CK or by the calculator -- was **loaded and
compiled on an HP Prime**:

| | |
|---|---|
| What was generated | 3,134 bytes, no compiled block |
| What ended up on the calculator | 3,406 bytes, with **272 of compiled block** |
| The source inside | identical to the original `.txt` |
| The accented characters | intact |
| **Run on the calculator** | the self-check function returned **1** |

The compiled block is written by the calculator when it loads the program, so
its presence alone says the program was understood. But the real proof is the
last row: the self-check verifies internally that a loop sums to 385 and that
an accented string is 26 characters long. **The program generated from Python
computes correctly on the calculator.**

The test program is in [examples/selftest/](../../examples/selftest/), so the
experiment can be repeated with one command.

## 5. Getting a template, which is not as easy as it sounds

**The kit ships one**, at `templates/code.hpprgm`, and every tool picks it up
on its own. You only need your own if that one ever fails you -- or if you
want to be sure, on your own machine, that the whole chain is yours.

A template is a code `.hpprgm` **written by the Connectivity Kit**: no
compiled block, source starting at offset 152. Copy one once and it works
forever.

What does not work is assuming there are some in
`Documents\HP Connectivity Kit\Calculators\<your calculator>\`. That folder is
the **mirror**, so everything in it has been through the calculator -- and the
calculator adds its compiled block to everything it saves. Measured on one
machine: of **58** program containers in the mirror, **2** were usable as
templates, and both were `.hpappprgm` files from apps.

```bash
hpprime templates "C:\Users\you\Documents\HP Connectivity Kit\Calculators"
```

That lists which of your files qualify. If none do:

**The reliable way to make one**: create a new program **inside the
Connectivity Kit itself** (right click → *New* on *Program*), write two lines
that compile, and **copy it out of the mirror folder before sending it to the
calculator**. That file was written by the CK and never touched by the
calculator, which is exactly what is needed.

`hpprime write` refuses a template with a compiled block on its own, so the
mistake cannot slip through silently.

## 6. Which calculator is which

When there are several folders under `Calculators\`, the `settings` file in
each one carries its identifier -- for a physical calculator, its serial
number. The folder name is whatever the CK shows in its tree.

Note that the mirror folder is only populated while the CK has actually
talked to that calculator. Finding it empty does not mean anything is broken.
