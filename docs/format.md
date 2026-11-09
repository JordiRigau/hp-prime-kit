# How this documentation is written

Every page under `docs/commands/` and `docs/topics/` follows the format on
this page, and a test holds each one to it. The documentation is meant to be
read by a person from start to finish and by a model one entry at a time, so
every entry stands on its own: nothing in it depends on having read the page
before.

---

## How each claim is known

Every example, and every statement about how a command behaves, carries one
of four labels, always in the same words:

| Label | What it means | What it needs |
|---|---|---|
| `G2` | measured on a physical HP Prime G2 | which program was run, on which firmware, and what the calculator showed |
| `emulator` | run on HP's Virtual Calculator | the stored result, and the firmware it came from |
| `HP help` | stated in the calculator's built-in help | the topic. Unless an entry says otherwise, this is the help dumped as Command Tree 13217 |
| `unverified` | none of the above | where it came from: a forum post, somebody's program, an inference |

A label says where a claim was seen, and the evidence says how far that
goes: a program and its pair with controls, or one program seen once, which
is weaker and says so. A claim whose evidence cannot name what was run and
what came back is not `G2`, however sure anybody is: it is `unverified`, and
says what was seen.

They are listed from strongest to weakest. The emulator runs HP's own
firmware, so it is closer to the calculator than anything written for the PC,
but it is not the calculator. What the interpreter in this repository answers
is not evidence at all: the interpreter is checked against these labels, not
the other way round.

A label can link to its evidence. Where it does not, the entry says in words
where the evidence is. The programs run to measure a fact are kept in
[evidence](evidence/README.md), listed by fact.

What the Virtual Calculator answered is kept in `docs/commands/results.tsv`,
one row per example, with the version the calculator reported. `hpprime
examples` writes it; nobody edits it by hand. An example labelled `emulator`
has its row there. Any example that has a row states the answer the emulator
gave: when the two differ, the tests fail until a person settles which is
right, and nothing is replaced on its own. When the emulator confirms an
example labelled `HP help` or `unverified`, `hpprime examples --relabel`
changes its label to `emulator`; a `G2` label is never changed.

Every example has been run somewhere, or says why it cannot be. One with no
stored answer is *no value*, with the reason in its entry; or labelled `G2`,
with the evidence in its entry; or run through `hpprime run`, because its
command runs on the PC. The tests fail on anything else: an example nobody
has run is a claim nobody has checked.

## How the examples were run

Three words recur in the evidence of entries and facts, and each means one
thing:

- **A batch** is a set of examples run together on the Virtual Calculator, as
  the calls of one generated program. The calculator is reset before every
  batch, so each answer starts from the same state, and a reset calculator
  has the Function app active:
  [apps.reset-leaves-function-active](topics/apps.md#apps.reset-leaves-function-active).
- **The harness** is that generated program. It runs each call inside
  `IFERR`, so a refusal costs its own row rather than the batch, and it brings
  back whether the call answered, what `TYPE` says, and the answer's text as
  `STRING` makes it on the calculator, cut at 160 characters with a marker
  saying so.
- **A probe** is a call made to settle a question rather than to illustrate a
  command. Its answer is stored the way an example's is. An entry that names
  a probe nobody has run is saying how an open question would be settled.

Some things a batch cannot reach, such as selecting an app or opening a view.
Those were done by pressing keys, and an entry says so where it relies on
them.

## A command entry

One file per command, `docs/commands/<group>/<NAME>.md`, and nothing about
that command is written anywhere else. This is `LEFT`, shortened:

```markdown
# LEFT

The first n characters of a string.

| | |
|---|---|
| Syntax | `LEFT(str, n)` → string |
| Group | strings |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `LEFT("abcdef", 3)` | `"abc"` | G2 |
| `LEFT("abcdef", 0)` | `"abcdef"` | G2 |
| `LEFT("MOMOGUMBO", 3)` | `"MOM"` | HP help |

## Behaviour

A count of 0 gives back the whole string, not an empty one, and so does a
count past the end (G2).
```

The parts, in this order:

1. **The name**, as the title, spelled the way PPL spells it. It is also the
   file's name and the entry's identifier.
2. **One sentence** saying what the command does. The index shows it.
3. **The fields**, in a two-column table:
   - `Syntax`: one row per form, with what it returns after `→`
   - `Group`: the folder the entry lives in
   - `Runs on the PC`: `yes` if `hpprime run` implements the command, `no` if
     it does not
4. **Examples**, in a table of three columns: the call, the result, and how
   the result is known.
   - The call and the result are PPL in backticks. The result is written the
     way the calculator displays it: `"abc"`, `{1,2}`, `[[1,2],[3,4]]`.
   - A call with a `;` in it is the body of a function, and its result is what
     that function answers. A call without one is an expression.
   - A result can be the word *error*, when the calculator refuses the call.
   - A result can be the words *no value*, when there is nothing to record:
     the command's result is the screen, or it stops the program, or it is a
     declaration rather than a call. Nothing runs such an example -- not
     `hpprime run`, not a batch on the emulator -- and the entry's behaviour
     says why there is nothing to record. It still carries a label, which says
     how the call itself is known.
   - Every example has exactly one label.
   - When the command runs on the PC, the tests run every example through
     `hpprime run` and compare the answer with the result stated.
5. **Behaviour**: short paragraphs for the edges and the errors. Every
   paragraph carries labels in parentheses, after the statements they
   support. The section can end with a paragraph that begins **Evidence.**
   and says where the labelled measurements come from; that one needs no
   label of its own.
6. **Models get wrong**, only when there is a record of it: what gets written,
   what happens, and where it was seen. An entry with no record has no such
   section, rather than a guessed one.
7. **Related**: links to other entries and to facts.

## A fact

A fact is something true about the platform rather than about one command: a
limit of the compiler, a key code, where a file has to go. It lives in the
topic page it belongs to, `docs/topics/<topic>.md`, and every command it
concerns links to it.

```markdown
<a name="ppl.local-limit"></a>
## One LOCAL statement holds at most 8 variables

| | |
|---|---|
| Identifier | `ppl.local-limit` |
| Kind | rule |
| Known from | G2 |

A `LOCAL` statement with more variables than that does not compile...

**Evidence.** Measured against programs that compile on the same
calculator...
```

- The anchor and the `Identifier` field are the same: the topic, a dot, and a
  short slug.
- `Kind` is `rule`, or `refuted hypothesis` for something that looked like a
  rule and was measured to be false. A refuted hypothesis is stated as what is
  true, and it is kept, because a model that has read only the rules will
  invent the missing ones.
- `Known from` is one label.
- Then the statement, and a paragraph that begins **Evidence.**

## Identifiers

- A command's identifier is its name: `LEFT`, `TEXTOUT_P`. A statement is
  named by its first word: `FOR`, `IF`, `IFERR`.
- A function or a variable that belongs to an app is qualified by the app, as
  in `Function.AREA`.
- A fact's identifier is its topic and a slug, as in `ppl.local-limit`.
- An identifier does not change once it is published. A rename leaves the old
  one pointing at the new.

## Where a name comes from

A name in code font is one of HP's unless the page says otherwise: it comes with
the calculator, and it is on [the list of names](#the-list-of-names) or is one
of the calculator's variables, such as `M1` or `L1`. A name that is not HP's
says whose it is:

| Origin | What it is | To use it |
|---|---|---|
| `library` | somebody's published program, such as `CHOOSE_R`: [libraries.published](topics/libraries.md#libraries.published) | install it on the calculator first |
| `hook` | a function you write, under a name HP chooses and calls, such as `START`: [apps.hooks](topics/apps.md#apps.hooks) | write it in an app's program |
| `example` | written for a page, such as `CIRCAREA` or `MYFUNC`, or written by you | write it |
| `test` | a program written to measure something, such as `ZHOK`. Those that were kept are in [evidence](evidence/README.md) | nothing: it is not meant to be used |
| `tools` | a program the tools put on a calculator to bring an answer back, such as `HPKDOC` | the tools send it |
| `python` | Python on the calculator, from MicroPython or from HP's `hpprime` module, such as `fillrect` | call it from Python, not from PPL |
| `hp` | HP's, though its list leaves it out, such as the keyword `DOWNTO` | nothing |
| `none` | nothing on the calculator: named to say so, such as `ENDIF` | it does not exist |

[not-hp.tsv](commands/not-hp.tsv) holds every such name with its origin.
`hpprime docs --check` fails on a name in capitals, or written as a call, that
is on neither list, and on a library's name in a paragraph that does not say it
is one. `hpprime lint` and `hpprime run` read it to say whose a name is.

`hpprime` names two things: the command on your PC ([tools.md](tools.md)), and
HP's Python module on the calculator
([micropython.modules](topics/micropython.md#micropython.modules)).

## The list of names

`docs/commands/names.tsv` holds every name PPL has, one per line, in six
tab-separated fields: the name, its kind, the group HP files it under, its
menu, the syntax HP's help gives for it, and where it came from. It is built
from HP's own sources: the help of firmware 13217, the command tree of
2.1.14181, and the release notes up to 2.4.15515. `tests/names_extract.py`
says how to rebuild it.

- Every entry's name is on the list, and its folder is the group the list
  gives it.
- Statements, commands, functions, app functions, app variables and
  variables each get an entry. Keywords are covered by the entry of their
  statement, operators by the topic page on the language, and CAS is not
  documented here.

## What is generated

These pages are produced, and nobody edits them by hand:

- `docs/commands/<group>.md`: every entry of a group on one page, for reading
  straight through
- `docs/commands/index.md`: every name on the list that gets an entry, with,
  for those already written, its sentence and the weakest label among its
  examples
- `docs/commands/groups.md`: the same names under the groups HP files them
  in
- `docs/llms.txt`: every fact and every entry on one line, with its link and
  its one-line summary, in the llms.txt layout, for a model to load before
  anything else. It is loaded whole, so it has a budget of 100,000 bytes, and
  the tests fail past it

`hpprime docs` regenerates them, and the tests fail when one is out of date.
