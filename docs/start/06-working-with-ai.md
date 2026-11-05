# 6. Working with an AI

Most people picking this up will be writing PPL with an AI at their side. That
works, and a few habits make it work much better.

---

## Why an AI struggles with this platform

An assistant that writes good Python writes confident, wrong PPL. The reason is
not the difficulty of the language:

- There is very little PPL in the world, and less of it on the open web than
  for almost any language you have used.
- What exists is contradictory: forum posts about different firmware versions,
  syntax from other HP calculators, half-remembered BASIC.
- The failure is quiet. `ENDIF` looks right. A `LOCAL` with thirteen names
  looks right. The compiler answers *syntax error* and a line, often not the
  line to fix, so neither you nor the model learns much from it.

The result is a plausible program that does not compile, and a loop in which
the model guesses and you carry the guesses to the calculator.

## What fixes it

Give the model the facts before it writes a line. The way in is one file,
[`docs/llms.txt`](../llms.txt): every entry and every fact of this
documentation on one line each, with its link and a one-line summary, kept
under 100,000 bytes so that it can be loaded whole.

| If the assistant | Give it |
|---|---|
| can read the files | `docs/llms.txt`, and let it follow the links it needs |
| is a chat window with no file access | the contents of `docs/llms.txt`, pasted in, and then the pages it asks for |

Whether a name exists at all is in
[`docs/commands/names.tsv`](../commands/names.tsv), HP's own list, with the
names that have no entry yet.

## The loop that works

```
      you describe          AI writes            hpprime lint
   what it should do   →    the PPL       →    (0 errors?) ──┐
                                                              │
   you check the        hpprime write      hpprime run        │
   result on the    ←   + drag over    ←   --call "FN(x)" ←───┘
   calculator                               (right answer?)
```

Two gates before anything reaches the calculator, and both are commands you
run rather than opinions:

- [`hpprime lint`](../tools.md#lint) catches what the compiler will not
  explain. If the model's code fails it, paste the output back: each finding
  names its rule, the fact behind it and how that fact is known, so the model
  has something real to correct against.
- [`hpprime run`](../tools.md#run) executes the actual file with real
  arguments. This is the gate that matters, because code can lint clean and
  compute the wrong thing.

Only then does the calculator get involved. When it matters that the PC and
the calculator agree on a call, [`hpprime compare`](../tools.md#compare) asks
both, with one keypress of yours on the emulator.

## What to ask for, and how

If the program computes something, ask for that part on its own first. "Write
the function that computes X, with no screen calls" gets you something
`hpprime run` can test, before screens and key handling.

Say what you already know. "This is PPL for an HP Prime G2, firmware 2.4" is
worth a paragraph of correction later.

Ask for the test with the code. "Give me three calls to `CIRCAREA` with the
expected values" turns `hpprime run` into a real check rather than a smoke
test.

When it fails, paste the exact output: the linter line, the run's error, or
what the calculator printed. This platform gives you very little information,
so do not throw away the little it does.

## What not to accept

Any claim about the platform that comes with no evidence.

If a model tells you that a limit is 10 variables, or that some command exists,
ask where that came from. The useful answers name a fact by its identifier,
such as [ppl.local-limit](../topics/ppl.md#ppl.local-limit), or a command by
its entry, together with the label that says how it is known; or they say "I
do not know". A confident number with no source is the dangerous one, because
you cannot tell the difference until it fails on the calculator, and there it
fails as *syntax error* on a line.

A label is part of the answer. A fact marked `unverified` is somebody's
reading, not a measurement, and the model should say so when it leans on one.

The same applies in the other direction. If you measure something new, write
it down with its evidence: [format.md](../format.md) says how.

## Three failure modes you will recognise

It invents a command. [STRINGFROMID](../commands/strings/STRINGFROMID.md)
exists; `STRINGFROM` does not. `hpprime lint` warns on a name that is not on
HP's list and that the file does not define, and makes it an error with
`--set`, when every file that goes to the calculator is in view; `hpprime run`
refuses it too, because it raises on anything it does not cover.

It writes Python in PPL's clothes. Zero-based indexing is the classic case:
positions count from 1, and `L(0)` does not fail: it answers the list's last
element, silently, where the model meant the first. That is why the linter
warns on it ([ppl.one-based](../topics/ppl.md#ppl.one-based)).

It fixes the same thing three times. If the error does not move after a fix,
the hypothesis is false and the fix was not merely too small. Say so, and
change tack: measure a program that already works instead of reasoning about
the syntax. The line the calculator names is one bad line among possibly
several, and not always the first
([ppl.check-last-error](../topics/ppl.md#ppl.check-last-error)).

## Let it use the tools

The commands are meant to be run by an agent as much as by you. A model with
shell access can lint, run, build and read binaries back without asking you to
relay output. Let it, and ask it to show what each command printed rather than
tell you that something works. Then check the calculator yourself, because that
is the part nobody can automate.

---

That is the path. From here, the [topic pages](../topics/ppl.md) can be
read in any order, [`docs/tools.md`](../tools.md) has every command in one
place, and [`docs/llms.txt`](../llms.txt) lists everything else.
