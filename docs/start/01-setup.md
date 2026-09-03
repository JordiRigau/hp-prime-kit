# 1. What you are getting into

You have an HP Prime and you want to make it do something of your own. This
page is the map: what the machine is, what the words mean, and what to
install. Fifteen minutes, and then you write a program.

---

## The machine

The **HP Prime** is a graphing calculator with a 320 × 240 touch screen that
is also a small computer you can program. There are two generations, **G1**
and **G2**; they share firmware, but the G2 is faster and has more memory.
Everything measured in this kit was measured on a **G2**.

It is programmed in **two languages**, and the choice is worth making
deliberately:

| | **PPL** | **Python** |
|---|---|---|
| What it is | the calculator's own language | MicroPython, a reduced Python |
| Since when | always | firmware from 2021 on |
| Looks like | Pascal / BASIC | Python, with less library |
| Good for | calculation, libraries other programs use | interfaces, long logic, reusing PC code |
| Official documentation | thin | **none** |

**You do not have to choose one.** From Python you can run PPL and get the
result back, so the usual arrangement is heavy calculation or data in PPL and
the interface in Python -- or everything in PPL, if it is small.

This path starts with **PPL**, because it is the native language and because
half of what is measured here is about it. Python comes in
[step 5](05-python.md).

If you come from programming on a PC, one difference changes everything:

> **There is no debugger, no useful error message and no console.** The PPL
> compiler says `syntax error` and points at a line, without saying what is
> wrong with it. A Python app that does something it dislikes **closes by
> itself, silently**.

That is the problem this kit exists to solve: **checking things without the
calculator**, so you do not depend on that paste-compile-look-repeat loop.

## Program or app: what each one is

| | **Program** | **App** |
|---|---|---|
| What it is | a file with functions in it | a folder with its own icon |
| Where it lives | the program catalogue | the `[Apps]` key |
| How it opens | `[Shift][Program]`, navigate, `[Enter]` | `[Apps]` and touch the icon: **two presses** |
| The file | `MYPROG.hpprgm` | `MYAPP.hpappdir/`, a folder |

An app does not compute better: it just opens faster and has somewhere to
keep its things. **Always start as a program** and wrap it as an app at the
end, once it works. Iterating on a program is much faster, and converting it
afterwards is packaging, not rewriting.

## What to install

| | |
|---|---|
| **HP Connectivity Kit** (CK) | the PC program that talks to the calculator -- <https://hpcalcs.com/download/> |
| **HP Virtual Calculator** | a Prime inside your PC, to try things without the physical one. It comes with the CK |
| **Python 3.7 or newer** | for this kit's tools. Nothing else: no pip, no libraries |

A physical calculator is not required to start: the Virtual Calculator
behaves the same for almost everything.

Then clone this repository and ask it how it is doing:

```bash
git clone https://github.com/JordiRigau/hp-prime-kit
cd hp-prime-kit
python hpprime.py doctor
```

`doctor` tells you what works on your machine and what to do about anything
that does not. It should end with *"Everything the kit needs is in place."*

On Windows you can drop the `python`: `hpprime doctor` works from the
repository folder. On macOS and Linux, `./hpprime doctor`. The rest of these
pages write it the short way.

## The vocabulary you need

The reference pages use these words without explaining them. There are seven:

| Word | What it means |
|---|---|
| **PPL** | the Prime's own language (*Prime Programming Language*) |
| **CK** | the Connectivity Kit, the PC program |
| **`.hpprgm`** | a program's file. It is **binary**, with the code as text inside |
| **`.hpappdir`** | an app's **folder** |
| **template** | an existing `.hpprgm` whose header is reused to make another. Needed because the format cannot be generated from nothing. The kit ships one |
| **compiled block** | a chunk the calculator adds before the code, with numbers already in its internal format. Makes the file bigger and the program open instantly |
| **the mirror** | the folder `Documents\HP Connectivity Kit\Calculators\<your calculator>\`. **Not a drop box**: it is a copy the CK writes *from* the calculator |

Two more you will meet in the interface pages: a **grob** is an image in
memory you draw onto (`G0` is the screen), and a **soft key** is one of the
six buttons in the bottom row, whose labels your program sets.

---

**Next:** [2. Your first program](02-first-program.md), from an empty file to
something running on the calculator.
