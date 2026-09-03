# 6. Working with an AI

Most people picking this up will be writing PPL with an AI at their side.
That works, and it works much better with a few habits. This page is about
those.

---

## Why an AI struggles with this platform in particular

An assistant that writes excellent Python writes confident, wrong PPL. The
reason is not the language's difficulty:

- **There is very little PPL in the world**, and less of it on the open web
  than for almost any language you have used.
- **What exists is contradictory.** Forum posts about different firmware
  versions, syntax from other HP calculators, half-remembered BASIC.
- **The failure mode is silent.** `ENDIF` looks right. `M(0)` looks right.
  A `LOCAL` with twelve variables looks right. The compiler answers `syntax
  error` and points at a line, so neither you nor the AI learns anything from
  the failure.

The result is a plausible program that does not compile, and a debugging loop
where the model guesses and you carry the guesses to the calculator.

## What fixes it

**Give the model the measured facts before it writes a line.** That is what
this repository is for. Two doors into the same body of rules:

| If you use | Point it at |
|---|---|
| Claude Code | `SKILL.md` -- clone the repo into `~/.claude/skills/` and it loads itself |
| Cursor, Copilot, Codex, anything else | `AGENTS.md` -- most agent tools read it automatically |
| A chat window with no file access | paste [`docs/ai/prompts.md`](../ai/prompts.md) §1 |

With that in front of it, a model stops inventing `ENDIF` and starts asking
which firmware you are on.

## The loop that works

```
      you describe          AI writes            hpprime lint
   what it should do   →    the PPL       →    (0 errors?) ──┐
                                                              │
   you check the        hpprime write      hpprime run        │
   result on the    ←   + drag over    ←   --call "F(x)"  ←───┘
   calculator                               (right answer?)
```

Two gates before anything reaches the calculator, and both are commands you
run, not opinions:

- **`hpprime lint`** catches the errors the compiler will not explain. If the
  AI's code fails the linter, paste the linter's output back -- it names the
  rule, and the rule is measured, so the model has something real to correct
  against.
- **`hpprime run`** executes the actual file with real arguments. This is the
  gate that matters: a model can produce code that lints clean and computes
  the wrong thing.

Only then does the calculator get involved. Every round trip you avoid is
minutes saved and one less thing to remember.

## What to ask for, and how

**Ask for the pure half separately.** "Write the function that computes X,
with no screen calls" gets you something testable. Screens and key handling
come after, once the arithmetic is right.

**Say what you already know.** "This is PPL for an HP Prime G2, firmware
2.4" is worth a paragraph of correction later.

**Ask for the test with the code.** "Give me three calls to `AREA` with the
expected values" turns `hpprime run` into a real check instead of a smoke
test.

**When it fails, paste the exact output.** Not "it does not work" -- the
linter line, or the run's error, or what the calculator printed. This
platform gives you almost no information; do not throw away the little it
does.

## What not to accept

> **Any claim about the platform that comes with no evidence.**

If a model tells you that a limit is 10 variables, or that some command
exists, ask where that came from. The honest answers are "it is in
`docs/reference/`", "it is in HP's reference", or "I do not know". The
dangerous answer is a confident number with no source, because on this
platform you cannot tell the difference until it fails on the calculator --
and then it fails as `syntax error` on a line.

The same goes for the other direction: if you measure something new, write
it down with its evidence. See [CONTRIBUTING.md](../../CONTRIBUTING.md).

## Three failure modes you will recognise

**It invents a command.** `STRINGFROMID` exists; `STRINGFROM` does not. The
linter will not catch this -- it does not know every builtin -- but
`hpprime run` will, because anything it does not cover raises rather than
inventing a result.

**It writes Python in PPL's clothes.** 0-based indexing is the classic:
`L(0)` looks fine and fails at run time. The linter catches index 0
specifically, for exactly this reason.

**It fixes the same thing three times.** If the error does not move after a
fix, the hypothesis is false -- the fix was not insufficient. Say so, and
change tack: measure a program that already works instead of reasoning about
the syntax. That single rule is the difference between one round trip and
five.

## Let it use the tools

The commands are meant to be run by an agent as much as by you. A model with
shell access can lint, run, build and read binaries back without asking you
to relay output, and `AGENTS.md` tells it to do exactly that before claiming
anything works. If your assistant can run commands, let it -- and then check
the calculator yourself, because that is the part nobody can automate.

---

That is the path. From here, the [reference pages](../reference/ppl.md) are
readable in any order, and [`docs/tools.md`](../tools.md) has every command in
one place.
