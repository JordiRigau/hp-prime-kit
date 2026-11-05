# Contributing

The point of this repository is that a newcomer can trust what it says. That
puts one requirement above the others.

---

## A new fact about the platform needs evidence

The Prime is thinly documented, which makes it tempting to write down what
seems reasonable. Do not. Everything here is either measured or marked as not
measured.

When you add a fact, say how it is known:

```markdown
| **`LOCAL` with too many variables** | the limit is 8 per statement |

**Evidence**, measured against programs that compile on that same calculator:
one that declares 8 compiles; three others stop at 7. The functions that
failed declared 13, 16 and 18.
```

The minimum is what was run, on what hardware, on what firmware, and what was
seen. "G2, firmware 2.4.15515" is a fact; "on my calculator" is not.

If you cannot measure it, because it comes from a forum, from HP's reference or
from somebody else's code, say where it came from and mark it `Unverified`.
That is useful. A confident guess is not.

Four habits make this work:

- An error that does not move after a fix means the hypothesis is false. Do not
  record the fix; go back and find the real cause.
- One failure is not a rule. A thing that broke once and a thing that cannot
  work are different claims, and this kit has already written the first as the
  second. If you have one observation, say what you saw; a rule needs the case
  that fails and a case that does not.
- A round trip is not a proof. Reading and writing with the same mistake gives
  a perfect round trip and a wrong answer. Verify against something that did
  not come from your own code.
- Read a program that already works on that same machine before concluding
  that anything is impossible.

Whether something compiles can be asked without a hand on the calculator: on the
emulator with `hpprime examples --compile`, and on a G2 with `hpprime send
--no-lint` and a control of each kind
([usb.compile-check](docs/topics/usb.md#usb.compile-check)).

## If the fact can be caught from a PC, catch it

A rule that lives only in prose gets forgotten. When a mistake is detectable
without a calculator, it gets three things:

1. the fact, in the reference page it belongs to;
2. a rule in `hpkit/lint.py`;
3. two cases in `tests/test_lint.py`: one that it catches, and one that it must
   stay quiet about.

The second test matters as much as the first. Several hypotheses in this repo's
history looked reasonable and were false, and a linter that flags legal code is
worse than no linter, because people learn to ignore it.

A rule is an error only as far as the measurement behind it reaches. Where its
pattern goes further, to a case nobody has run, it warns, and the finding says
`unverified`; that case becomes an error when somebody measures it.
`tests/test_lint.py` fails on an error whose label is not `G2` or `emulator`.

The same shape applies to the interpreter. A new builtin goes into `BUILTINS`
with its case in `tests/test_interp.py`, and only after you have measured what
the calculator returns for it. Measuring one is a short program that prints
each case and its result on screen, run from Home and read off the display;
include the edges, which is where the surprises are. An invented semantics
returns a number where the calculator returns another, which is exactly the
divergence this kit exists to catch.

## House rules

- English everywhere: code, comments, messages, docs, commit messages.
- Python 3.7+, standard library only. No dependencies, no install step.
  Somebody with a fresh clone and a stock Python has to be able to run
  everything.
- `python tests/run_all.py` must pass. None of the suites needs a calculator;
  two use one if it is there and skip what they cannot find.
- One fact, one home. If it is in `docs/topics/`, link to it instead of
  restating it. The one deliberate exception is `docs/ai/prompts.md` §1, a
  context block for chats that cannot read files, and it says so.
- No narrative. State the fact and how it is known. No war stories, no
  achievement numbers, no suspense.
- No project-specific content. Examples are generic: a circle's area, a square
  root. Whatever you built this for stays in your own repository.
- A way to build an app goes in `docs/patterns.md`, as an option with what it
  solves and what it costs. A topic page states what the calculator does, and
  the guided path teaches the facts, not one app's design.

## What is worth contributing

In rough order of how much it would help:

| | Why |
|---|---|
| **The interpreter's remaining gaps** | `M := GZ` aliases here -- assign a global matrix to a local, change one element, and the global changes with it -- where the Prime copies. What is measured on the calculator is the copy on a **call**; the assignment has not been run there |
| **Anything measured on a G1** | everything here is a G2. Same firmware, different hardware |
| **MicroPython speed, and an app's memory limit** | both are listed as not measured, and both change which designs are possible |
| **How large a generated data program can be** | the block that avoids a compile on arrival is a cache the calculator rebuilds, so data programs generate like any other, but nobody has timed one with hundreds of kilobytes of literals |
| **Anything the grid model would predict wrongly** | key codes are positions, five to a row. Thirteen keys fit that; a fourteenth that does not would be worth knowing |

## Sending it

Fork, branch, and open a pull request that says what you measured and how. A PR
that adds a fact with its evidence and its test is welcome even if the prose
needs work: the evidence is the hard part.
