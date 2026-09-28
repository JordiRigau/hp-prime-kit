# 1. What you are getting into

You have an HP Prime and you want it to do something of your own. This page
covers what the machine is, what the words mean and what to install. It takes
about fifteen minutes, and then you write a program.

---

## The machine

The HP Prime is a graphing calculator with a 320 × 240 touch screen
([interface.geometry](../topics/interface.md#interface.geometry)), and a small
computer you can program. There are two generations, G1 and G2, which share
firmware.

Every claim in this documentation says how it is known: measured on a G2, run
on HP's Virtual Calculator, stated in HP's built-in help, or unverified. The
four labels are explained in
[How each claim is known](../format.md#how-each-claim-is-known). The
calculator everything was measured on is a G2 with firmware 2.4.15515, so a
G1, or another firmware, is a case nobody has checked.

It is programmed in two languages, and the choice is worth making deliberately:

| | **PPL** | **Python** |
|---|---|---|
| What it is | the calculator's own language | MicroPython, a reduced Python |
| Since when | always | firmware from 2021 on |
| Looks like | Pascal / BASIC | Python, with less library |
| Good for | calculation, libraries other programs use | interfaces, long logic, reusing PC code |
| Official documentation | HP's built-in help | none |

You do not have to pick one. From Python you can run PPL and get the result
back ([micropython.eval](../topics/micropython.md#micropython.eval)), so the
usual arrangement is heavy calculation or data in PPL and the interface in
Python, or everything in PPL if it is small.

This path starts with PPL, because it is the native language and because most
of what is known here is about it. Python comes in [step 5](05-python.md).

If you come from programming on a PC, one difference matters more than the
rest: the calculator explains very little.

- When the compiler refuses a program it answers *syntax error* and a line
  number, without saying what is wrong, and the line it names is often not
  the one to fix
  ([ppl.end-semicolon](../topics/ppl.md#ppl.end-semicolon),
  [ppl.check-last-error](../topics/ppl.md#ppl.check-last-error)).
- A Python app that meets something it cannot handle closes, with no message
  ([micropython.list-with-string-closes-the-app](../topics/micropython.md#micropython.list-with-string-closes-the-app)).

That is what the tools on the PC are for: checking a program before the
calculator sees it, so that you do not depend on a paste, compile, look and
repeat loop.

## Program or app: what each one is

| | **Program** | **App** |
|---|---|---|
| What it is | a file with functions in it | a folder with its own icon |
| Where it lives | the program catalogue | the `[Apps]` key |
| How it opens | `[Shift][Program]`, navigate, `[Enter]` | `[Apps]` and touch the icon: two presses |
| The file | `MYPROG.hpprgm` | `MYAPP.hpappdir/`, a folder |

An app does not compute better. It opens faster and has somewhere to keep its
things. Start as a program and wrap it as an app at the end, once it works:
iterating on a program is faster, and converting it afterwards is packaging
rather than rewriting ([step 4](04-first-app.md)).

## What to install

| | |
|---|---|
| HP Connectivity Kit (CK) | the PC program that talks to the calculator: <https://hpcalcs.com/download/> |
| HP Prime Virtual Calculator | a Prime inside your PC, to try things without the physical one. A separate download, from the same page |
| Python 3.7 or newer | for the tools. Nothing else: no pip, no libraries |

A physical calculator is not required to start. The Virtual Calculator runs
HP's own firmware, so it is close to a G2, but it is not one: where something
was measured on only one of the two, the claim says which.

Then get the repository, <https://github.com/JordiRigau/hp-prime-kit>, either
way:

- **Download it.** On that page, **Code**, then **Download ZIP**, and unzip it.
  The folder is called `hp-prime-kit-main`.
- **Clone it**, if you use git. The folder is called `hp-prime-kit`:

  ```bash
  git clone https://github.com/JordiRigau/hp-prime-kit
  ```

Open a terminal in that folder -- on Windows 11, right-click inside it in File
Explorer and choose **Open in Terminal** -- and check the setup:

```bash
python hpprime.py doctor
```

[`doctor`](../tools.md#doctor) reports what works on your machine, where it
found the Connectivity Kit and the Virtual Calculator, and what to do about
anything missing. Its last line says whether everything is in place.

To bring it up to date later: `git pull` in a clone, and
[`hpprime update`](../tools.md#update) in a download.

Every command in these pages runs in a terminal opened in that folder, and is
written the short way, `hpprime doctor`. How you type that depends on your
shell:

| Shell | Type |
|---|---|
| Windows PowerShell | `.\hpprime doctor` — the leading `.\` is required |
| Windows cmd.exe | `hpprime doctor` |
| macOS, Linux | `./hpprime doctor` |
| anywhere, always works | `python hpprime.py doctor` |

If in doubt, use the last one. It is the same program either way.

## The vocabulary you need

The reference pages use these words without explaining them:

| Word | What it means |
|---|---|
| PPL | the Prime's own language (*Prime Programming Language*) |
| CK | the Connectivity Kit, the PC program |
| `.hpprgm` | a program's file. It is binary, with the code as text inside ([formats.container](../topics/formats.md#formats.container)) |
| `.hpappdir` | an app's folder ([apps.hpappdir-contents](../topics/apps.md#apps.hpappdir-contents)) |
| template | an existing `.hpprgm` whose header is reused to make another, because the format is not generated from nothing. One ships with the tools ([deploy.template-from-the-ck](../topics/deploy.md#deploy.template-from-the-ck)) |
| compiled block | a chunk the calculator adds to a program when it loads it, and rebuilds when it is missing ([formats.block-is-a-cache](../topics/formats.md#formats.block-is-a-cache)) |
| the mirror | the CK's folder of copies, `Documents\HP Connectivity Kit\Calculators\<your calculator>\`. It is not a drop box: the CK writes it *from* the calculator ([deploy.ck-mirror](../topics/deploy.md#deploy.ck-mirror)). `hpprime doctor` prints where it is on your machine |
| grob | an image in memory that you draw onto; `G0` is the screen |
| the labels along the bottom | the six touch targets your program draws with `DRAWMENU`. They are not keys: touching one reports nothing through `GETKEY` ([interface.soft-labels-not-keys](../topics/interface.md#interface.soft-labels-not-keys)) |
| an identifier | the name of a fact, such as `ppl.local-limit`: the page it is on and a slug. These pages link to facts by it, and it is how you cite one |

---

Next: [2. Your first program](02-first-program.md), from an empty file to
something running on the calculator.
