# Contributing

The point of this repository is that a newcomer can trust what it says. That
puts one requirement above all the others.

---

## A new fact about the platform needs evidence

The Prime is badly documented, which makes it tempting to write down what
seems reasonable. Do not. Everything here is either measured or marked as not
measured.

When you add a fact, say **how it is known**:

```markdown
| **`LOCAL` with too many variables** | the limit is 7-8 per statement |

**Evidence**, measured against programs that compile on that same calculator:
one that declares 8 compiles; three others stop at 7. The functions that
failed declared 13, 16 and 18.
```

The minimum is: **what was run, on what hardware, on what firmware, and what
was seen.** "G2, firmware 2.4.15515" is a fact; "on my calculator" is not.

If you cannot measure it -- it comes from a forum, from HP's reference, from
somebody else's code -- say where it came from and mark it **Unverified**.
That is genuinely useful; a confident guess is not.

Three habits that make this work:

- **An error that does not move after a fix means the hypothesis is false.**
  Do not record the fix; go back and find the real cause.
- **A round trip is not a proof.** Reading and writing with the same mistake
  gives a perfect round trip and a wrong answer. Verify against something
  that did not come from your own code.
- **Read a program that already works** on that same machine before
  concluding anything is impossible.

## If the fact can be caught from a PC, catch it

A rule that lives only in prose gets forgotten. When a mistake is detectable
without a calculator, it gets three things:

1. the fact, in the reference page it belongs to;
2. a rule in `hpkit/lint.py`;
3. **two** cases in `tests/test_lint.py`: one that it catches, and one that
   it must stay quiet about.

That second test matters as much as the first. Four hypotheses in this repo's
history looked reasonable and were false, and a linter that flags legal code
is worse than no linter -- people learn to ignore it.

The same shape applies to the interpreter: a new builtin goes into `BUILTINS`
with its case in `tests/test_interp.py`, and only after you have measured
what the calculator returns for it. An invented semantics returns a number
where the calculator returns another, which is exactly the divergence this
kit exists to catch.

## House rules

- **English**, everywhere: code, comments, messages, docs, commit messages.
- **Python 3.7+, standard library only.** No dependencies, no install step.
  Somebody with a fresh clone and a stock Python has to be able to run
  everything.
- **`python tests/run_all.py` must pass.** None of the suites needs a
  calculator; two use one if it is there and skip what they cannot find.
- **One fact, one home.** If it is in `docs/reference/`, link to it instead of
  restating it. The one deliberate exception is `docs/ai/prompts.md` §1, a
  context block for chats that cannot read files, and it says so.
- **No narrative.** State the fact and how it is known. No war stories, no
  achievement numbers, no suspense.
- **No project-specific content.** Examples are generic: a circle's area, a
  square root. Whatever you built this for stays in your own repository.

## What is worth contributing

In rough order of how much it would help:

| | Why |
|---|---|
| **The key codes below the top three rows** | those three are measured key by key; the rest of the table is read out of other people's apps. `examples/keymap/` maps a whole region in one run |
| **The string functions in the interpreter** (`LEFT`, `MID`, `INSTRING`, `SORT`) | left out on purpose: their edge behaviour is not measured. Measure one and it can go in |
| **Anything measured on a G1** | everything here is a G2. Same firmware, different hardware |
| **MicroPython speed, and an app's memory limit** | both listed as not measured, and both change what designs are possible |
| **How large a generated data program can be** | the block that avoids a compile on arrival is a cache the calculator rebuilds, so data programs generate like any other -- but nobody has timed one with hundreds of kilobytes of literals |
| **Anything the grid model would predict wrongly** | key codes are positions, five to a row. Thirteen keys fit that; a fourteenth that does not would be worth knowing |

## Sending it

Fork, branch, and open a pull request that says what you measured and how.
A PR that adds a fact with its evidence and its test is welcome even if the
prose needs work -- the evidence is the hard part.
