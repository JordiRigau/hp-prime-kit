# PPL: facts about the language

Facts about the language as a whole rather than about one command. Each has an
identifier, says how it is known, and is stated here once; the entries it
concerns link to it.

Reference firmware: G2, 2.4 revision 15515 (2025-09-15). A fact labelled `G2`
was measured on that calculator, one labelled `emulator` on HP's Virtual
Calculator, one labelled `HP help` comes from the built-in help, and one
labelled `unverified` from none of those. New to the Prime? The
[guided path](../start/01-setup.md) teaches; this page records.

## The shape of a program

```ppl
// line comment
/* block */

EXPORT VAR1, VAR2;              // globals, they persist between uses
EXPORT MYDATA:=[[1,2],[3,4]];

EXPORT FUNC(a, b)
BEGIN
  LOCAL x, y;                   // locals, until the end of this block
  x := a + b;
  RETURN x;
END;                            // the ; after END is required
```

`EXPORT` makes a function visible from other programs and from Home; without
it the function is private to its file. Everything is 1-based, which is the
most common mistake coming from Python. Equality is `==`, assignment `:=`,
not-equal `<>`, and the logicals are `AND`, `OR`, `NOT`; `AND` and `OR` stop
at the side that decides ([ppl.short-circuit](#ppl.short-circuit)).

Control flow: `IF … THEN … ELSE … END;` · `FOR i FROM 1 TO n DO … END;`
(`DOWNTO` and `STEP` too) · `WHILE … DO … END;` · `REPEAT … UNTIL c;` ·
`CASE … DEFAULT … END;` · `IFERR … THEN … END;` · `BREAK` · `CONTINUE` ·
`KILL` · `IFTE(c, a, b)` as an expression.

| What you need | PPL |
|---|---|
| size of a list or string | `SIZE(L)` |
| dimensions of a matrix | `d := DIM(M);` → `d(1)`, `d(2)` |
| append to a list | `L(SIZE(L)+1) := v;` or `L := CONCAT(L, {v});` |
| number → string / string → number | `STRING(x)` / `EXPR(s)` |
| type of a variable | `TYPE(v)` |

There is error trapping and no exceptions of your own: `IFERR statements THEN
statements [ELSE statements] END;` traps a system error and leaves its code in
`Ans`, and `STRINGFROMID` turns that into a message. What does not exist is a
way to raise an error of your own with a value inside, so an API that returns
results still needs a convention: a status code of `-1` with the reason, say,
and `{}` from functions that return lists. `IFERR` hardens one call; it does
not propagate errors.

## Where to look things up

| Source | What it is good for |
|---|---|
| **The `[Help]` key, on the calculator** | HP's own entry for the command you are on: syntax, a sentence, and worked examples. The first place to look, and the one nobody mentions |
| **Command Tree 13217** ([hpcalc.org](https://www.hpcalc.org/prime/docs/commandtree.zip)) | that same help, dumped to a 239-page PDF: how to read it without a calculator, and how an agent reads it at all |
| *HP Prime Programming Reference* (HP) | looking up one command, not for learning |
| **hpmuseum.org/forum**, HP Prime subforum | complete code and real behaviour |
| **hpcalc.org** | a program archive: read code that already works before writing any |
| **en.hpprime.club** (E. Shore / H. Klaver) | tutorials with examples that run |
| **udel.edu/~mm/hp/primePython** | the closest thing to a reference for Python on the Prime |

HP's help gets further than this repository once assumed: `LEFT`'s zero case,
`MOD` as a Euclidean remainder and the `TYPE` codes are all in it, and reading
it corrected four answers this documentation had wrong. What it does not do is cover the
edges evenly -- `RIGHT` and `MID` get no sentence about theirs -- or say
anything about the limits below that break compilation. Look it up first, and
measure the rest. Its examples are the interpreter's test data:
`tests/hp_examples.txt` holds every one that applies to a command the
interpreter implements, and `python tests/test_hpdocs.py` runs them.

Direct links:
[undocumented limits](https://www.hpmuseum.org/cgi-bin/archv021.cgi?read=254706) ·
[E. Shore's tutorial](https://literature.hpcalc.org/community/hpprime-prog-tutorial.pdf) ·
[G2 firmware 2.4.15515](https://www.hpcalc.org/details/7783) ·
[Python libraries](https://udel.edu/~mm/hp/primePython/upython.html) ·
[Python Activities Book](https://literature.hpcalc.org/community/hpprime-python-activities.pdf)

> If you are an AI agent reading this: hpmuseum.org is protected against
> automated access and answers with a challenge you cannot pass. Do not try.
> The source that does allow reading is hpcalc.org, and downloading somebody's
> program and reading it is worth more than any tutorial.

---

<a name="ppl.local-limit"></a>
## One LOCAL statement holds at most 8 variables

| | |
|---|---|
| Identifier | `ppl.local-limit` |
| Kind | rule |
| Known from | G2 |

A `LOCAL` statement with 9 or more variables does not compile, and the
compiler reports only *syntax error* on its line. Several `LOCAL` statements
in a row do work, so a longer list is split across several.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
`LOCAL za,zb,zc,zd,zf,zg,zh,zj; za := 5380; RETURN za;` answered 5380, and the
same with `zk` as well did not compile. Programs that compile on that calculator
declare 8, and three others stop at 7, and functions that failed there declared
13, 16 and 18. 9, 10, 11 and 12 also failed on the Virtual Calculator 2.4, build
2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls
coming out as they must ([results.tsv](../commands/results.tsv)). On the same
build, on 2026-11-07, the two programs above answered the same, 5380 and not
compiled, by the same command with its two controls coming out as they must, and
`Check` named the line of the `LOCAL`. `hpprime lint` catches 9 and more as an
error.

<a name="ppl.local-block-scope"></a>
## A LOCAL lasts until the end of its block

| | |
|---|---|
| Identifier | `ppl.local-block-scope` |
| Kind | rule |
| Known from | G2 |

A `LOCAL` lasts until the end of the block that declares it, and used after that,
read or assigned, it does not compile. That holds for `IF`, `FOR`, `WHILE`,
`REPEAT`, `CASE` and `IFERR`, and the parts of one statement are blocks of their
own: a `LOCAL` of a `THEN` cannot be read in its `ELSE`, one of what an `IFERR`
tries cannot be read in its `THEN`, and one of a `REPEAT` cannot be read in its own
`UNTIL`. To keep a value past the block, declare it before the block. Where a
`LOCAL` may go is [ppl.locals-at-top](#ppl.locals-at-top).

After the block the name is free again. It can be declared again; if the program
has a global of that name, the name means the global; and a `LOCAL` that repeats
an outer `LOCAL` hides it only until its block ends, when the outer one is back
with its value. A `LOCAL` that repeats a parameter was not tried (unverified).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must.
Each function declared `LOCAL zb; zb := 3;` in the block, and returned a number
nothing else would.

| The block | `zb` used where | Answered | Read inside the block |
|---|---|---|---|
| `IF` | read after its `END` | does not compile | 4735 |
| `IF` | assigned after its `END`, `zb := 4;` | does not compile | |
| `IF`, in its `ELSE` | read after its `END` | does not compile | |
| `IF`, in its `THEN` | read in its `ELSE` | does not compile | |
| `FOR` | read after its `END` | does not compile | 5213 |
| `WHILE` | read after its `END` | does not compile | 5233 |
| `REPEAT` | read after its `UNTIL` | does not compile | 5243 |
| `REPEAT` | read in its own `UNTIL` | does not compile | 5243 |
| `CASE` | read after its `END` | does not compile | 5223 |
| `IFERR` | read after its `END` | does not compile | |
| `IFERR` | read in its `THEN` | does not compile | |

After an `IF`: `LOCAL zb := 4; RETURN zb + 5180;` answered 5184. With `EXPORT
ZRVB := 2;`, a nested `LOCAL ZRVB; ZRVB := 3;` and then `RETURN ZRVB + 5190;`
answered 5192. With `zb` at 1 outside, a nested `LOCAL zb; zb := 3;` and then
`RETURN zb + 5200;` answered 5201, and in a `FOR`, `RETURN zb + 5420;` answered
5421. A `LOCAL` read inside an `IF` also compiled on the Virtual Calculator 2.4,
build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two
controls coming out as they must, and answered 3
([results.tsv](../commands/results.tsv)). The same programs, every row of the table
and the four after it, answered the same on that build on 2026-11-07, by the same
command with its two controls coming out as they must, and for each that did not
compile `Check` named the line where `zb` was used after its block. `hpprime lint`
catches a use after the block as `local-scope`, and `hpprime run` refuses to load
it.

<a name="ppl.index-call"></a>
## The result of a call cannot be indexed where it is produced

| | |
|---|---|
| Identifier | `ppl.index-call` |
| Kind | rule |
| Known from | G2 |

`SIZE(M)(1)` does not compile, and neither does the same shape on a
function a program defines, in its own file or in another program. Assign the
result to a variable and index the variable: `d := DIM(M);` and then
`d(1)`.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
with `zm := [[1,2],[3,4]];`, `RETURN SIZE(zm)(1) + 5270;` did not compile, and
`zd := DIM(zm); RETURN zd(1) + 5270;` answered 5272, and the two answered the same
on the Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples
--compile`, with its two controls coming out as they must, `Check` naming the line
of `SIZE(zm)(1)`. The programs' own functions
were measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by
`hpprime examples --compile`, with its two controls coming out as they must: a
function returning `{10,20,30}`, called and indexed with `(2)` where it is
produced, did not compile whether it was defined in the same file or in a program
compiled before it ([results.tsv](../commands/results.tsv)). `hpprime lint` catches
it as `index-call`.

<a name="ppl.export-initialised"></a>
## One EXPORT statement holds at most 8 variables

| | |
|---|---|
| Identifier | `ppl.export-initialised` |
| Kind | rule |
| Known from | G2 |

`EXPORT ZV1:=1, ZV2:=2, …;` compiles with up to 8 variables in one statement, and
with 9 it does not, and `EXPORT ZV1, ZV2, …;`, with no values, is the same. Seven is
not a limit, although one compile error was once recorded as if it were. A name that
fails whatever the count is [ppl.export-home-variable](#ppl.export-home-variable).

Some with values and some without was not measured (unverified).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must.
Each program held the variables `ZV1` onwards with their number as their value, and
a function adding the first and the last to a base: 6 answered 4747 from 4740, 7
answered 4758 from 4750, 8 answered 4769 from 4760, and 9 did not compile. With no
values, 8 and a function returning 5092 answered that, and 9 did not compile. The
same six programs answered the same on the Virtual Calculator 2.4, build 2025-09-15,
on 2026-11-07, by `hpprime examples --compile`, with its two controls coming out as
they must, and no two of those that compile in the same run, since they export the
same names. Two to
six with values also compiled on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-24 and 2026-09-25, by `hpprime examples --compile`, with its two controls
coming out as they must ([results.tsv](../commands/results.tsv)). The seven that
failed once were recorded without their program, so their names are not known.
`hpprime lint` catches 9 and more as `export-limit`, and `hpprime run` refuses to
load them.

<a name="ppl.export-home-variable"></a>
## A variable of Home's cannot be exported, though a function can be called like one

| | |
|---|---|
| Identifier | `ppl.export-home-variable` |
| Kind | rule |
| Known from | G2 |

`EXPORT Z := 1;` does not compile, and neither do `EXPORT Z;`, `EXPORT Y := 1;` and
`EXPORT A := 1;`: those are variables Home already has. The same statement with a
name of its own compiles, so it is the name that fails, and not the count. An app's
function is another matter, since a program exporting `AREA` compiles
([ppl.global-namespace](#ppl.global-namespace)).

The other letters, `θ`, and the numbered lists, matrices, graphics and complex
variables were not tried, although a report on the HP forum says the same of `B`
(unverified).

Only the exported variable is refused. A function called `F` compiles and answers,
exported or not, with an argument or with none, and in source `RETURN F;` is the
call. So do a parameter called `X` and a local called `Z`, which leaves Home's `Z` as
it was. But typed on Home, `F` answers the variable and not the function, so a
function with no arguments called like one of them cannot be started by its name
there. With an argument it fares no better: with `EXPORT F(za)`, `F(2)` typed on
Home answered *syntax error* with `Entry` at 0, and `EXPR` reads them the same way,
`EXPR("F()")` answering 0 and `EXPR("F(2)")` an error (emulator). `F(2)` was not tried
on a G2 (unverified).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must.
`EXPORT Z := 4781;` with a function returning `Z` did not compile. Each with a
function returning a number of its own, `EXPORT Y := 5060;`, `EXPORT A := 5070;` and
`EXPORT Z;` did not compile either, and `EXPORT ZV := 4781;` with a function returning
`ZV` answered 4781. `A`, `Y` and `Z` read 0 before those programs and after them.
`EXPORT F()` returning 5010 and a function returning `F() + 1` answered 5011;
`EXPORT F(za)` returning `5020 + za` and a function returning `F(1)` answered 5021; a
private `F()` returning 5030 answered it. `ZRFH(X)` returning `X + 5040`, called with
1, answered 5041, and `LOCAL Z; Z := 5050; RETURN Z;` answered 5050, with `Z` on Home
still 0. With `EXPORT F()` returning 5012, a function holding `RETURN F;` answered
5012, and `F` typed on Home answered 0. The same programs answered the same on the
Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples
--compile`, with its two controls coming out as they must, and `F` typed on its Home
answered 0; `A`, `Y` and `Z` read 0 through `EXPR` after the programs that tried to
export them. In the same runs, with `EXPORT F()` returning 5012, `EXPR("F")` and
`EXPR("F()")` answered 0, and with `EXPORT F(za)`, `EXPR("F(2)")` was an error and
`F(2)`, typed on Home with the `( )` key and `Entry` at 0, opened a dialog saying
*syntax error* ([results.tsv](../commands/results.tsv)). `hpprime lint` catches what
was refused as `export-home-variable`, and warns on the others, labelled
`unverified`, and on a function with no arguments called like one of them.
`hpprime run` refuses to load what was refused, and raises "not covered" on the
others.

<a name="ppl.no-end-keywords"></a>
## END closes everything: there is no ENDIF or ENDFOR

| | |
|---|---|
| Identifier | `ppl.no-end-keywords` |
| Kind | rule |
| Known from | G2 |

`ENDIF`, `ENDFOR`, `ENDWHILE`, `ENDCASE`, `ENDFUNC` and `ENDPROC` do not
exist in PPL.
Every block ends with `END`, and a function's `END` carries a `;`.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
an `IF` closed with `ENDIF;`, which is one of those controls, a `FOR` closed with
`ENDFOR;` and a `WHILE` closed with `ENDWHILE;` did not compile. `ENDCASE` closing a
`CASE` and `ENDFUNC` closing a function were measured on the Virtual Calculator 2.4,
build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two
controls coming out as they must, and neither compiled
([results.tsv](../commands/results.tsv)). `ENDPROC` closing a function was measured
the same way on 2026-09-25, and it did not compile
([results.tsv](../commands/results.tsv)). The `ENDFOR` and `ENDWHILE` programs did not
compile on that build either, on 2026-11-07, by the same command, whose control that
does not compile is the `ENDIF`. `hpprime lint` catches them, and the names
are not on the list of names in `docs/commands/names.tsv`.

<a name="ppl.minus-sign"></a>
## The calculator writes a negative with the mathematical minus sign

| | |
|---|---|
| Identifier | `ppl.minus-sign` |
| Kind | rule |
| Known from | emulator |

What comes back from the calculator is U+2212, the minus sign, and not the
ASCII hyphen U+002D that you type on a keyboard. Source is a different
matter: a program is written with the hyphen and the calculator accepts it.

This documentation writes results with the hyphen, because an entry is read
by people who have to type what they read, and `hpprime docs` treats the two
characters as the same sign when it compares an entry with what the emulator
answered.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15: the
`IFERR` example of [IFERR](../commands/branch/IFERR.md) answered a negative
one whose codepoints are `0x2212 0x31`, stored in
[results.tsv](../commands/results.tsv).

<a name="ppl.one-based"></a>
## Lists, strings and matrices are indexed from 1

| | |
|---|---|
| Identifier | `ppl.one-based` |
| Kind | rule |
| Known from | G2 |

Lists, strings and matrices start at 1: the first element is element 1. A 0
is never the first element, and what it is depends on where it goes:

| | |
|---|---|
| a position in a string, `MID(s, 0, 2)` | an error |
| a list read at 0, `L(0)` | its **last** element |
| a list assigned at 0, `L(0) := v` | `v` added at the end |
| an empty list read at 0 | an error |
| a string read at 0, `S(0)` | an error |
| a matrix read at 0, `M(0)` or `M(0, 1)` | an error |

The list is the trap. Coming from Python, `L(0)` means the first element,
and here it answers the last one with no error; when the index is computed,
nothing in the source shows it.

**Screen coordinates are the exception: they count from 0.** A point of the
screen or of a grob starts at `(0,0)`, and a drawing command takes it without
complaint. So a 0 is correct in a drawing call and wrong in a list, and the
two live in the same program. `hpprime lint` flags a literal 0 only where the
name is not one of the calculator's own, which is what keeps
`LINE(G1,0,0,9,4,RGB(0,0,255))` out of its way.

**Evidence.** `MID("abcdef", 0, 2)` is an error on a G2 with firmware
2.4.15515 and on the Virtual Calculator 2.4, build 2025-09-15
([results.tsv](../commands/results.tsv)), while every measured example that
indexes from 1 answers. HP's help says the same. The list and matrix rows
were measured on the same build on 2026-09-24, with the 0 held in a variable
so that the program compiled whatever the answer: `{10,20,30}` read at 0
answered 30, assigned 40 at 0 became `{10,20,30,40}`, and `[[1,2],[3,4]]`
read at 0, with one index or two, was refused; so were an empty list and
the string `"abc"` read at 0 ([results.tsv](../commands/results.tsv)). A
literal 0 written in the source, `zl(0)`, compiles too, and answered 30,
measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls coming out as they must. `hpprime lint` warns on a
literal 0 passed to a name the file does not define, which may be a list, as
`one-based`, labelled `emulator`.

The exception is measured on the same build: `C→PX(0,0)` answers `{160,109}`,
`GETPIX(G1,0,0)` answers a colour, and `LINE`, `RECT` and `TRIANGLE` all draw
with a 0 among their corners
([results.tsv](../commands/results.tsv)).

<a name="ppl.string-index-code"></a>
## A string indexed answers a character code, not a character

| | |
|---|---|
| Identifier | `ppl.string-index-code` |
| Kind | rule |
| Known from | emulator |

A string held in a variable can be indexed like a list, and what comes back
is the code of the character, a number: `"abc"` at 2 answers 98, not `"b"`.
[ASC](../commands/strings/ASC.md) answers the same codes for the whole
string, and [MID](../commands/strings/MID.md) is how to get the character as
text. A comparison against `"b"` fails, with no error, because the two are
not the same type.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-24: `LOCAL zs, zi; zs := "abc"; zi := 2; RETURN zs(zi);` answered 98,
a real ([results.tsv](../commands/results.tsv)). The index was held in a
variable so that the program compiled whatever the answer. Until then the
interpreter on the PC answered `"b"`.

<a name="ppl.names-ignore-case"></a>
## The calculator reads a command's name without regard to case

| | |
|---|---|
| Identifier | `ppl.names-ignore-case` |
| Kind | rule |
| Known from | emulator |

`alog(2)` and `Alog(2)` answer 100, as `ALOG(2)` does, and `xpon(1000)`
answers 3: a name HP writes in capitals is found in any case. It is the
assumption `hpprime lint` was built on, which never flags a spelling that
differs from the list only in case.

It does not make case irrelevant everywhere. A lower-case name can also be a
CAS command of its own, and those were kept out of the measurement: both
names tried exist on HP's list in capitals only.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-24, with each call inside `EXPR`, so through Home's reading of an
expression; a program's source compiled with the name in lower case was not
tried ([results.tsv](../commands/results.tsv)).

<a name="ppl.equality-operators"></a>
## == compares, := assigns, <> is not-equal

| | |
|---|---|
| Identifier | `ppl.equality-operators` |
| Kind | rule |
| Known from | emulator |

`==` compares, `:=` assigns and `<>` is not-equal (HP help). What was assumed
here for a long time, and is false, is that a single `=` in a condition does
not compile: **it does**. `IF a = 1 THEN … END;` passed the editor's `Check`.

And it **compares**, exactly as `==` does. Two functions asked it from
different directions and agreed: `IF a = 2` with `a` at 1 took the `ELSE`,
and the same test left `a` unchanged rather than setting it to 2. So a single
`=` inside a condition is not a trap at all: it is legal and it means what a
reader would think.

`hpprime lint` called it an error until this was measured, and the rule was
removed rather than softened: a linter that flags legal, correct code is
worse than one rule short.

**As a statement it is a trap.** `za = 2;` compiles, and assigns nothing: it
compares `za` with 2 and throws the answer away. Written where `za := 2;` was
meant, the program runs, raises nothing, and keeps the old value.
`hpprime lint` warns on it as `equality-statement`.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-12, with programs written by hand because the harness lints what it
sends and would not send this one. That it compiles: `Check` on a program
holding `IF a = 1 THEN RETURN 5; ELSE RETURN 6; END;` reported its only error
further down, in a function about
[ppl.end-semicolon](#ppl.end-semicolon), so everything above compiled. That
it compares: `IF a = 2 THEN RETURN 5; ELSE RETURN 6; END;` with `a` at 1
answered 6, and `IF a = 2 THEN a := 99; END; RETURN a;` answered 1. The
statement was measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls coming out as they must: `LOCAL za; za := 1; za = 2; RETURN za;` compiled
and answered 1 ([results.tsv](../commands/results.tsv)).

<a name="ppl.short-circuit"></a>
## AND and OR stop at the side that decides, and IFTE evaluates only the clause that wins

| | |
|---|---|
| Identifier | `ppl.short-circuit` |
| Kind | rule |
| Known from | emulator |

`a AND b` does not evaluate `b` when `a` is false, and `a OR b` does not
evaluate `b` when `a` is true: the second side is skipped whole, calls and
all (emulator). So a guard written on one line works, and the side it guards
can be something that would fail on its own: with `L := {}`,
`IF SIZE(L) > 0 AND L(1) == 3 THEN … END;` raises nothing.

`IFTE(test, a, b)` is the same: it evaluates the test and then only the
clause that wins (emulator). `IFTE(SIZE(L) == 0, 0, L(1))` is safe with an
empty list, and a clause that is slow or changes something costs nothing when
it loses.

Both were open questions until they were measured, and programs were written
around them. Putting the guarded side in an `IF` of its own is harmless, but
correctness does not need it, and a linter rule against a guard on one line
would flag correct code.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-10-25, with two programs sent by `hpprime compare` and run by hand
(`Check`, then the call from Home). The first relied on an error: with
`zl := {}`, the tests `IF SIZE(zl) > 0 AND zl(1) == 3 …`,
`IF SIZE(zl) == 0 OR zl(1) == 3 …` and `zx := IFTE(SIZE(zl) == 0, 5, zl(1));`,
each inside `IFERR`, all three ran without the error. The second relied on
none: a function that adds 1 to a global counter and answers 1, placed on the
side that should be skipped, in `IF 0 AND PRBSIDE() == 1 …`,
`IF 1 OR PRBSIDE() == 1 …` and `zx := IFTE(1 == 1, 5, PRBSIDE());`, left the
counter at 0 all three times. In the same run, `zx := zl(1);` with `zl := {}`
was an error, which is what made the first program a test at all. The PC
interpreter answered the same to every call. Not measured on a G2.

<a name="ppl.end-semicolon"></a>
## END carries a semicolon

| | |
|---|---|
| Identifier | `ppl.end-semicolon` |
| Kind | rule |
| Known from | emulator |

It is `END;`, both for a function and for a block inside one. A missing
semicolon does not compile. On a block's `END` the error is reported on the
**next** line: the compiler carries on past the `END`, swallows what follows
and fails there, so the line the calculator names is not the line to fix. On
a function's own `END` it does not compile either, even when that `END` is
the last line of the file.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-12, with a program written by hand for the question. Its second
function held `IF 1 == 1 THEN z := 2; END` on line 12 and `RETURN z;` on line
13, and the editor's `Check` answered *syntax error* on line 13. The first
function of the same program, which compiled, is the evidence for
[ppl.equality-operators](#ppl.equality-operators). A function's own `END`
without its `;` was measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls coming out as they must: last in the file, and with another function
after it, neither compiled ([results.tsv](../commands/results.tsv)). `hpprime lint` catches a line that is exactly
`END` as `end-semicolon`.

<a name="ppl.global-index-other-program"></a>
## Indexing a global from another program is not a compile error

| | |
|---|---|
| Identifier | `ppl.global-index-other-program` |
| Kind | refuted hypothesis |
| Known from | G2 |

This page used to state, as a rule, that indexing a global declared in a
different program fails, because the compiler reads `NAMES(1)` as a call to a
function called `NAMES`. That is too broad. A list declared `EXPORT
L:={"a","b",…}`, with contents, is indexed from another program and passed to
`SIZE` in an app in daily use. What did fail was a list declared `EXPORT
L:={};`, empty, indexed from another program.

What separates the two is not established. Two hypotheses, neither measured:
the declaration's contents, since an empty list may leave the compiler nothing
to infer a type from; or the order they were installed in, since a program
only sees another's functions if it was compiled afterwards, and the same may
hold for knowing a global's type. Four small programs would settle it: a
global declared empty and one declared full, each indexed from a second
program, installed in both orders.

Until somebody runs that, copying to a local first is the safe move: `zn :=
NAMES;` and then `zn(1)`. It costs one line and works in both cases. That is a
precaution, not a rule, and `hpprime lint` does not flag it: `TS1(1)` and
`AREA(3,350)` are written the same way, so one file cannot tell them apart.

**Evidence.** Both programs are on the same G2 with firmware 2.4.15515: one
indexing an empty exported list failed, one indexing a filled exported list
runs.

<a name="ppl.return-in-loop"></a>
## RETURN inside a loop is allowed

| | |
|---|---|
| Identifier | `ppl.return-in-loop` |
| Kind | refuted hypothesis |
| Known from | G2 |

The hypothesis was that `RETURN` cannot appear inside `FOR` or `REPEAT`. It is
false: `RETURN` works inside a loop, and leaves the function from there.

**Evidence.** A program that runs on a G2 has two `RETURN` statements inside
loops.

A program of its own, `RETURN 5340 + zi;` inside a `FOR` when `zi` is 2, answered
5342 on the Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime
examples --compile`, with its two controls coming out as they must
([results.tsv](../commands/results.tsv)); it was not run on a G2.

<a name="ppl.letter-digit-names"></a>
## A letter followed by a digit is a usable name

| | |
|---|---|
| Identifier | `ppl.letter-digit-names` |
| Kind | refuted hypothesis |
| Known from | G2 |

The hypothesis was that names like `r2` or `y1` are reserved, because the
calculator has variables spelled that way. It is false for locals: a program
that compiles uses `L12`, `L13`, `L14`, `L15` as local names.

**Evidence.** A program on a G2 with firmware 2.4.15515 that compiles and
runs. `LOCAL L12; L12 := 5350; RETURN L12;` answered 5350 on the Virtual Calculator
2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples --compile`, with its two
controls coming out as they must ([results.tsv](../commands/results.tsv)); it was
not run on a G2. A local called `Z` compiles too
([ppl.export-home-variable](#ppl.export-home-variable)). What was not tested is a
local named exactly like a list or a matrix in use, such as `M1` or `L1`, so the
safe habit of prefixing locals stands.

<a name="ppl.local-m-matrices"></a>
## A local called m does not clash with the M0..M9 matrices

| | |
|---|---|
| Identifier | `ppl.local-m-matrices` |
| Kind | refuted hypothesis |
| Known from | G2 |

The hypothesis was that `LOCAL m` collides with the built-in matrices. It is
false: what was failing in the program that started the hypothesis was the
number of locals in one statement, which is
[ppl.local-limit](#ppl.local-limit).

**Evidence.** The same program compiles once the `LOCAL` statement is split,
with the name unchanged, on a G2 with firmware 2.4.15515. `LOCAL m; m := 5360;
RETURN m;` answered 5360 on the Virtual Calculator 2.4, build 2025-09-15, on
2026-11-07, by `hpprime examples --compile`, with its two controls coming out as they
must ([results.tsv](../commands/results.tsv)); it was not run on a G2.

<a name="ppl.locals-initialised-one-line"></a>
## Locals can be initialised on one line

| | |
|---|---|
| Identifier | `ppl.locals-initialised-one-line` |
| Kind | refuted hypothesis |
| Known from | emulator |

The hypothesis was that a `LOCAL` statement cannot give initial values to
several variables at once, and it is false: `LOCAL za := 2, zb := 3;`
compiles, and both values are there when the function runs, and so does
three, as published tutorial code writes it. Exported globals can too, up to 8
in one statement: [ppl.export-initialised](#ppl.export-initialised).

**Evidence.** Run on the Virtual Calculator 2.4, build 2025-09-15, in the
batch stored on 2026-09-12: `LOCAL za := 2, zb := 3; RETURN za + zb;`,
compiled as the body of a function in a program that passed the editor's
`Check`, answered 5. The three-variable form, which a tutorial published by
E. Shore uses, was measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls coming out as they must: `LOCAL za := 1, zb := 2, zc := 3;` compiled
and the function answered 6 ([results.tsv](../commands/results.tsv)).

<a name="ppl.locals-at-top"></a>
## A LOCAL does not have to be at the top of the BEGIN

| | |
|---|---|
| Identifier | `ppl.locals-at-top` |
| Kind | refuted hypothesis |
| Known from | G2 |

The hypothesis was that every `LOCAL` goes at the top of the `BEGIN`, and that one
half way down a function does not compile. It is false: a `LOCAL` after other
statements compiles and works, with another before it or with none, and with an
initial value. It holds from there to the end of its block,
[ppl.local-block-scope](#ppl.local-block-scope).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and
typed as in [usb.compile-check](usb.md#usb.compile-check), with its two controls
coming out as they must. `LOCAL za; za := 4730; LOCAL zb; zb := 1; RETURN za + zb;`
answered 4731, and its pair, with `LOCAL za, zb;` at the top and `zb := 6;`,
answered 4736. `IF 1 == 1 THEN 1; END; LOCAL zb; zb := 4732; RETURN zb;`, with no
`LOCAL` before the one in it, answered 4732. `LOCAL za; za := 0; LOCAL zb := 4733;
RETURN za + zb;` answered 4733. The four answered the same on the Virtual Calculator
2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples --compile`, with its two
controls coming out as they must ([results.tsv](../commands/results.tsv)). The
hypothesis came from one compile error on a
G2, recorded without its program, so what failed there is not known. `hpprime
lint` called this an error until it was measured, and the rule was removed.

<a name="ppl.i-e-as-locals"></a>
## i and e work as local names

| | |
|---|---|
| Identifier | `ppl.i-e-as-locals` |
| Kind | rule |
| Known from | emulator |

`i` is the imaginary unit and `e` Euler's number, and a local of either name
compiles and holds what it is given: inside the function the local is the
number, not the constant. Prefixed names (`zi`, `ze`) still read better next
to arithmetic that uses the constants.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples --compile`, with its two controls coming out as they must: `LOCAL i; i := 2; RETURN i * 3;` answered 6, and
`LOCAL e; e := 2; RETURN e + 1;` answered 3 ([results.tsv](../commands/results.tsv)).

---

<a name="ppl.imaginary-unit"></a>
## The imaginary unit goes in as `i` and comes back as a private-use glyph

| | |
|---|---|
| Identifier | `ppl.imaginary-unit` |
| Kind | rule |
| Known from | emulator |

A complex number may be typed either as `3+4*i`, with the ASCII letter, or as
the pair `(3,4)`. Both are accepted. What the calculator answers is neither:
the imaginary unit comes back as U+E003, a character in Unicode's private use
area, so `CONJ(3+4*i)` reads as `3-4*` followed by that glyph.

This is the same shape as [ppl.minus-sign](#ppl.minus-sign): the calculator
takes ASCII on input and answers with a character of its own. Unlike the
minus sign, nothing here normalises it, so a program comparing an
answer against text it wrote itself will not match, and a result stored in
`results.tsv` carries the glyph literally.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15:
`RE(3+4*i)` and `RE((3,4))` both answer 3, `IM(3+4*i)` answers 4, and
`CONJ(3+4*i)` answers a `TYPE` 3 value whose text holds U+E003
([results.tsv](../commands/results.tsv)).

---

<a name="ppl.exponent-glyph"></a>
## Scientific notation comes back with a glyph of the calculator's own

| | |
|---|---|
| Identifier | `ppl.exponent-glyph` |
| Kind | rule |
| Known from | emulator |

A number in scientific notation is not written with an `E`. The exponent is
marked with U+1D07, the small capital E, and the exponent's sign is the
mathematical minus U+2212, so machine epsilon reads as `2.22044604925ᴇ−16`
rather than `2.22044604925E-16`.

This is the third character the calculator answers with that nobody can type:
the minus sign, [ppl.minus-sign](#ppl.minus-sign), the imaginary unit,
[ppl.imaginary-unit](#ppl.imaginary-unit), and this one. The pattern is worth
holding on to -- what goes in is ASCII and what comes back is the
calculator's own typography -- because a program comparing an answer against
text it wrote itself will not match, and only the minus sign is normalised
anywhere here.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15:
`LQ([[1,2],[3,4]])` and `SCHUR([[1,2],[3,4]])` both answer decompositions
holding very small numbers, and in both the exponent marker is U+1D07 and its
sign U+2212 ([results.tsv](../commands/results.tsv)).

---

<a name="ppl.exact-answers"></a>
## Some commands answer exactly, and an exact answer is not a number

| | |
|---|---|
| Identifier | `ppl.exact-answers` |
| Kind | rule |
| Known from | emulator |

A command may answer a value the calculator keeps in exact form rather than as
a decimal. `l2norm([1,2,3])` answers the square root of 14, written with
U+221A and held as `TYPE` 8 -- the same type `CAS` answers with -- while its
two siblings `l1norm` and `maxnorm` answer the plain numbers 6 and 3, of
`TYPE` 0.

So a program cannot tell from the family a command belongs to whether it will
get a number back. Arithmetic on the exact value works, but a comparison
against text, or an assumption that the answer has digits, will not.

U+221A is also the fourth character the calculator writes that nobody can
type, after [ppl.minus-sign](#ppl.minus-sign),
[ppl.imaginary-unit](#ppl.imaginary-unit) and
[ppl.exponent-glyph](#ppl.exponent-glyph).

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15:
`l2norm([1,2,3])` answers U+221A followed by 14 with `TYPE` 8, where
`l1norm([1,2,3])` answers 6 and `maxnorm([1,2,3])` answers 3, both `TYPE` 0
([results.tsv](../commands/results.tsv)).

<a name="ppl.type-codes"></a>
## What TYPE answers

| | |
|---|---|
| Identifier | `ppl.type-codes` |
| Kind | rule |
| Known from | emulator |

`TYPE(v)` answers 0 for a real, 1 for an integer, 2 for a string, 3 for a
complex, 4 for a matrix, 5 for an error, 6 for a list, 8 for a function, 9 for
a unit, and 14.x for a CAS object. Watch 3 and 4: this documentation had them the other
way round until HP's help was read, and `IF TYPE(v) == 3` then branches on
complex numbers instead of matrices.

**Evidence.** 0, 1, 2, 3, 4, 6, 8 and 9 are measured on the Virtual Calculator 2.4,
build 2025-09-15. Four by a call of their own: `TYPE(3)` is 0, `TYPE("a")` is
2, `TYPE([[1,2],[3,4]])` is 4 and `TYPE({1,2})` is 6. The fifth comes from
what other commands answer: `RGB(255,0,0)`, `SETBITS(12)` and `R→B(12)` all
come back as `#` integers of type 1, which is what HP's help calls an
integer and what an ordinary number is not. All of it is in
[results.tsv](../commands/results.tsv). Every other answer the batches bring
back carries its `TYPE` too, and none has contradicted those four. Type 8
is measured on what `CAS` answers: `CAS("1/2+1/3")` and `CAS(1/2+1/3)` both
come back as `5/6` with `TYPE` 8, 2026-09-12, and `l2norm([1,2,3])`
answers a square root of 14 with the same `TYPE` 8 and no `CAS` call
around it, 2026-09-13. That is worth reading twice,
because HP's help calls 8 a function and keeps 14.x for a CAS object, so what
the CAS hands back arrives as 8 and not as 14.x. Which of the two namings is
right is not something those two rows settle, and a program branching on
`TYPE` should follow the 8 that was measured. Type 3 is measured too: `CONJ(3+4*i)` answers a complex number and its
`TYPE` is 3, 2026-09-13, so the help's warning about 3 and 4 being easy to
swap is now settled on one side. Type 9 is measured too: `TYPE(2_m)` answers 9, 2026-09-13, which is
what HP's help calls a unit. An earlier `TEVAL` answer had come back
as 9 without settling it; a value carrying a unit settles it. The
codes still unmeasured here are 5 and 14.x, which come from HP's
built-in help. A `TEVAL` answer came back as type 9, a unit,
which agrees with the help's 9 without settling it.

<a name="ppl.function-always-answers"></a>
## A function always answers something

| | |
|---|---|
| Identifier | `ppl.function-always-answers` |
| Kind | rule |
| Known from | G2 |

There is no way to write a function that returns nothing. Without a `RETURN`,
a function answers with the value of the last statement that produced one, and
an assignment produces the value assigned. That matters because Home prints
what a program answers: you choose what the number is, not whether there is
one.

| The body ends in | It answers |
|---|---|
| `z := 1;` | 1 -- an assignment produces the value assigned |
| `FOR zi FROM 1 TO 2 DO z := zi; END;` | 2 -- the last value the body produced |
| an `IF` whose condition is false | 0 -- the value from before it, unchanged |
| a call to another function | what that function answered |
| `RETURN;`, bare and with no value | 0 -- and it does compile |

**Evidence.** Measured on a G2 with firmware 2.4.15515, one function per
ending, with no `RETURN` in any of them except the last.

<a name="ppl.home-no-parentheses"></a>
## On Home, type a function with no arguments without parentheses

| | |
|---|---|
| Identifier | `ppl.home-no-parentheses` |
| Kind | rule |
| Known from | G2 |

`MYFUNC` runs it in every entry mode measured, unless its name is one of Home's
variables ([ppl.export-home-variable](#ppl.export-home-variable)). `MYFUNC()`, typed
with the `( )` key, answers *syntax error* with [Entry](../commands/home-settings/Entry.md) at 0
or 1, and runs it with `Entry` at 2, the RPN stack. So the form to tell somebody
to type is the name alone. The calculator's own commands do the same: `TICKS()`
answers *syntax error* too, at 0, and at 1 as well on the Virtual Calculator, where at
2 it answered a number (emulator).

It is not the parentheses as such: `CIRCAREA(2)`, with an argument, answers, and
so does `EXPR("MYFUNC()")`. Nor is it a rule of PPL, since in a program's source
they are optional: [ppl.call-no-parentheses](#ppl.call-no-parentheses).

A report on the HP forum says `MYFUNC()` works on Home in general. It did not in
those two modes on this calculator, and the Virtual Calculator answered as it did in
all three, and at 0 and 1 also when the pair arrived as the two characters `(` and
`)` rather than from the key (emulator). What differs is not known, and another
firmware was not tried (unverified).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, with the
TAULES app active, keys sent as in [usb.keys](usb.md#usb.keys) and the answers
read from the screen. With `Entry` at 0: `SELF3`, from
`examples/selftest/SELFTEST.txt`, answered 1, and `SELF3()` opened a dialog saying
*syntax error*, as it did when typed by hand on 2026-09-03; `ZHOK`, returning 4703,
answered that and `ZHOK()` opened the same dialog, as did `TICKS()`; `ZHARG(2)`,
returning `4900 + za`, answered 4902, through the same key; a function holding
`RETURN EXPR("ZHOK()") + 1;` answered 4704. With `Entry` at 1: `ZHOK` answered 4703
and `ZHOK()` opened the dialog. With `Entry` at 2: both put 4703 on the stack.

The same programs answered the same on the Virtual Calculator 2.4, build 2025-09-15,
on 2026-11-07, compiled by `hpprime examples --compile` with its two controls coming
out as they must, with the Function app active. With `Entry` at 0: `ZHOK` 4703,
`SELF3` 1 and `ZHARG(2)` 4902, and the *syntax error* dialog for `ZHOK()`, `SELF3()`
and `TICKS()`. At 1: `ZHOK` 4703, and the dialog for `ZHOK()` and `TICKS()`. At 2:
4703 on the stack for both, and a number for `TICKS()`. Through `EXPR`, `ZHOK()`
answered 4703 and the function holding it 4704. The names went to the emulator's
window as typed characters and the `( )` key as a click on its picture, by messages
posted to that window, and each answer was read from a capture of its screen. Sent
as characters, `ZHOK()` and `TICKS()` opened the dialog at 0 and 1; at 2 the
characters made `ZHOK())`, which is not the call. `Entry` was set by the same
programs as on the G2, and read 0 at the end
([results.tsv](../commands/results.tsv)).

<a name="ppl.call-no-parentheses"></a>
## In source, a call with no arguments can leave out its parentheses

| | |
|---|---|
| Identifier | `ppl.call-no-parentheses` |
| Kind | rule |
| Known from | G2 |

`RETURN MYFUNC;` and `RETURN MYFUNC();` are the same call, and `MYFUNC;` as a
statement really runs the function. It makes no difference whether the function comes
earlier in the file or later, is declared ahead with `MYFUNC();` or not, or is
exported by another program sent before this one. A name that is also one of Home's
variables means the function: `RETURN F;` is the call. On Home it is another matter:
[ppl.home-no-parentheses](#ppl.home-no-parentheses).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must.
Called with no parentheses, a function defined earlier in the file answered 4710, one
declared ahead with `ZPG();` answered 4711, and one defined later and not declared
answered 4712. That last one answered 4713 with parentheses. One exported by another
program answered 4714 both ways. A function that adds 1 to a global, called as `ZPI;
ZPI;` before `RETURN ZPCNT + 4720;`, gave 4722, so both ran. With `EXPORT F()`
returning 5012, `RETURN F;` answered 5012, with Home's `F` at 0. The same programs
answered the same on the Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by
`hpprime examples --compile`, with its two controls coming out as they must
([results.tsv](../commands/results.tsv)). `hpprime lint` stays quiet on all of them,
and `hpprime run` answers the same.

<a name="ppl.getkey-no-parentheses"></a>
## GETKEY works with and without parentheses in PPL

| | |
|---|---|
| Identifier | `ppl.getkey-no-parentheses` |
| Kind | rule |
| Known from | G2 |

`zk := GETKEY;` and `zk := GETKEY();` both compile and answer the same, as any
call with no arguments does in source
([ppl.call-no-parentheses](#ppl.call-no-parentheses)). From Python, across the
bridge, it is `eval('GETKEY()')`.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and
typed as in [usb.compile-check](usb.md#usb.compile-check), with its two controls
coming out as they must: `zk := GETKEY(); RETURN zk + 4800;` answered 4799, and
`zk := GETKEY; RETURN zk + 4810;` answered 4809, so −1 both times, no key pending.
Both also answered −1 on the Virtual Calculator 2.4, build 2025-09-15, on
2026-09-25, by `hpprime examples --compile`, with its two controls coming out as
they must ([results.tsv](../commands/results.tsv)), and the two programs above
answered 4799 and 4809 there on 2026-11-07, the same way. The Python form is in programs
that run on a G2 with firmware 2.4.15515.

<a name="ppl.matrices-by-value"></a>
## Matrices are passed by value, and only a write costs more with size

| | |
|---|---|
| Identifier | `ppl.matrices-by-value` |
| Kind | rule |
| Known from | G2 |

A function that writes to a matrix it was given does not change the caller's. A
big one is not slower to hand over: reading one element of a 100x100 argument
takes as long as reading one of a 10x10, and only a write takes longer for the
bigger one. That is what copying on the first write would look like, as a report
on the HP forum says it is, although a timing cannot show the mechanism. So large
data does not have to live in a global to save the cost of passing it.

Lists were not timed (unverified).

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and
typed as in [usb.compile-check](usb.md#usb.compile-check), with its two controls
coming out as they must. `zm := [[4790,2],[3,4]]; ZMW(zm); RETURN zm(1,1);`, with
`ZMW` writing 999 to its argument at (1,1), answered 4790. One program timed 1000
calls of each kind with `TICKS`, run three times, in milliseconds:

| Run | Read 10x10 | Read 100x100 | Write 10x10 | Write 100x100 | Read a global 100x100 |
|---|---|---|---|---|---|
| 1 | 39 | 37 | 55 | 206 | 19 |
| 2 | 107 | 99 | 119 | 427 | 29 |
| 3 | 39 | 40 | 60 | 203 | 30 |

The last column is a function with no argument, so it says what an argument costs
at any size. Why the second run was slower at every step is not known.

On the Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples
--compile`, with its two controls coming out as they must, the first program answered
4790, and the timing program, run three times, answered {1, 0, 1, 4, 0}, {1, 1, 1,
3, 1} and {1, 1, 1, 3, 1} ms in the same order. The write of a 100x100 is the only
step above 1 ms, which agrees, but `TICKS` counts whole milliseconds, so on a PC
that fast the ratios cannot be read from it
([results.tsv](../commands/results.tsv)).

<a name="ppl.expr-empty"></a>
## EXPR of an empty string fails

| | |
|---|---|
| Identifier | `ppl.expr-empty` |
| Kind | rule |
| Known from | G2 |

`EXPR("")` is an error, so check `SIZE(s) > 0` before evaluating whatever came
out of a field.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
`zr := 5330; IFERR zr := EXPR(""); THEN zr := 5331; END; RETURN zr;` answered 5331. It
is an error on the Virtual Calculator 2.4, build 2025-09-15, too, where the same
program answered 5331 on 2026-11-07, by `hpprime examples --compile`, with its two
controls coming out as they must ([results.tsv](../commands/results.tsv)).

<a name="ppl.expr-dynamic-access"></a>
## EXPR is how a name is resolved at run time, and it is not free

| | |
|---|---|
| Identifier | `ppl.expr-dynamic-access` |
| Kind | rule |
| Known from | G2 |

`EXPR("NAME")` gives the variable whose name was built on the fly, and it costs more
than reading the name: 2 to 5 times, for a global holding a number. In a loop where
that matters, resolve it once, before the loop.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
one program timed 1000 `zs := ZRVA;` and then 1000 `zs := EXPR("ZRVA");` with `TICKS`,
run three times, and answered 22 and 53 ms, 21 and 114 ms, and 22 and 91 ms. On the
Virtual Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples
--compile`, with its two controls coming out as they must, the same program answered
1 and 2 ms, 0 and 3 ms, and 0 and 2 ms: `EXPR` the slower each time, though at whole
milliseconds the ratio cannot be read ([results.tsv](../commands/results.tsv)). How the
cost grows with what the name holds was not measured. A per-element loop over a data
program once had to be changed for this, in an app, and that program was not kept.
`hpprime lint` warns on it as `expr-in-loop`.

<a name="ppl.global-namespace"></a>
## Exported names share one namespace with Home

| | |
|---|---|
| Identifier | `ppl.global-namespace` |
| Kind | rule |
| Known from | G2 |

An `EXPORT`ed name is visible from Home and from every other program. **Two programs
exporting one name both compile, and nothing says so** (G2 and emulator), and a call
answers only one of them, which one depending on how they got there. Sent to the
calculator, the one that has been there longest answers, until it is sent again and
becomes the newer (G2 and emulator). Compiled with `Check` in the editor after
arriving as files, the one compiled last answers, and pressing `Check` on the other
changes it (emulator). Prefix them.

**A program's name hides an app's function of the same name.** A program
exporting `AREA`, which is the Function app's, compiled, and `AREA(2)` on
Home then answered 12.5663706144, the program's, with the Function app
active. So a program that exports an app's name takes that function away
from Home for as long as it is installed.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must:
`ZQLIB` and `ZQTEST` each exported `ZRCLH`, answering 5321 and 5322, and each exported
a function of its own, which answered, so both had compiled. Sent `ZQLIB` and then
`ZQTEST`, `ZRCLH` answered 5321. With `ZQLIB` sent again, it answered 5322. Only those
two orders were tried. Sent the same way to the Virtual Calculator 2.4, build
2025-09-15, on 2026-11-07, by the Connectivity Kit 2.4 from its content library, to a
calculator with no other program and the only one the Kit could see, the same
programs answered the same, read from captures of its screen: `ZQLIB` and then
`ZQTEST` arrived compiled, `ZRCLH` typed on Home answered 5321 and `ZRCLT` 5323, and
with `ZQLIB` sent again, `ZRCLH` answered 5322 and the new version's `ZRCLU` 5324. On
the same build and day, by `hpprime
examples --compile`, with its two controls coming out as they must, the same two
programs went on as files and were compiled with `Check`, the one answering 5321
first: `ZRCLH` answered 5322, through `EXPR` and typed on Home, and `ZRCLT` 5323. With
`Check` pressed again on the first, `ZRCLH` typed on Home answered 5321
([results.tsv](../commands/results.tsv)). `Check` on a G2 was not tried. The collision with an app's function was measured on the
Virtual Calculator 2.4, build 2025-09-15, on 2026-09-24, by `hpprime examples
--compile`, with its two controls coming out as they must, `AREA(2)` read through
`EXPR` ([results.tsv](../commands/results.tsv)). `hpprime lint --set` warns on two
files exporting one name, and `hpprime lint` on an export named like one of HP's, as
`export-clash`.

<a name="ppl.decimal-point"></a>
## The decimal point in source is always a dot

| | |
|---|---|
| Identifier | `ppl.decimal-point` |
| Kind | rule |
| Known from | unverified |

Even on a calculator that displays `,` as the decimal separator, source is
written with `.`.

**Evidence.** One line in a table of run-time traps, from work on a G2 with
firmware 2.4.15515, with no program kept. Nothing has been run with the display set
to `,`, which is what would settle it.

<a name="ppl.compilation-order"></a>
## A program only sees another's functions if it was compiled afterwards

| | |
|---|---|
| Identifier | `ppl.compilation-order` |
| Kind | rule |
| Known from | G2 |

A function that calls another program's function does not compile until that function
is on the calculator, and the other program arriving later does not rescue it. Install
each program after the programs whose functions it calls, or send it again once they
are there.

**Evidence.** Measured on a G2 with firmware 2.4.15515, on 2026-11-05, sent and typed as in [usb.compile-check](usb.md#usb.compile-check), with its
two controls coming out as they must.
`ZROCA`, returning `ZROTH()`, sent while no program held `ZROTH`, came back as
`Z*R*O*C*A`. With `ZROTH` then sent in another program, `ZROTH` answered 5310 and
`ZROCA` still came back as a product. `ZROCA` sent again answered 5310. On the Virtual
Calculator 2.4, build 2025-09-15, on 2026-11-07, by `hpprime examples --compile`, with
its two controls coming out as they must, the same programs answered the same:
`ZROCA` checked before `ZROTH` was there did not compile, `Check` naming the line of the
call, and with `ZROTH` compiled after it, `ZROCA` still came back as `Z*R*O*C*A` on Home;
in a run of its own, the same caller checked after `ZROTH` answered 5310
([results.tsv](../commands/results.tsv)). It is the same
mechanism the open question in
[ppl.global-index-other-program](#ppl.global-index-other-program) asks about for
globals.

<a name="ppl.check-last-error"></a>
## Which bad line Check names depends on what is wrong with it

| | |
|---|---|
| Identifier | `ppl.check-last-error` |
| Kind | rule |
| Known from | emulator |

When the editor's Check refuses a program with several bad lines, it names
one of them, and which one depends on the kind of error. With two plain
syntax errors far apart, it named the **first**. With calls it could not
read, it named the **last**, and fixing each moved the report backwards
through the program. So the named line is a place to start, not a promise
about the lines above or below it: a program with several bad lines takes one
round per bad line to clear, in either order.

**Evidence.** Measured on the Virtual Calculator 2.4, build 2025-09-15, with
three generated programs that differed only in a few calls. Their bad lines
were 31, 33 and 35 in the first, 31 and 33 in the second and 31 alone in the
third, and Check named 35, then 33, then 31. Which calls were bad was settled
separately by running each one inside `EXPR`, where a bad call is a value on
its row instead of a refusal of the whole program. The first-line case was
measured on the same build on 2026-09-24: a program with `za := za + ;` on
lines 4 and 12 and nothing else wrong, and Check named line 4, read off the
screen by the person pressing it.

<a name="ppl.speed-anchor"></a>
## The one speed figure there is

| | |
|---|---|
| Identifier | `ppl.speed-anchor` |
| Kind | rule |
| Known from | G2 |

PPL is interpreted and HP publishes no figure for what an operation costs. The
one measurement on physical hardware: an inverse lookup by bisection, 60
iterations, each a double interpolation over matrices, is "noticeable, but
under a second".

That is an order of magnitude to reason with. A 53x49 Gauss-Jordan is about
45,000 floating-point operations, two orders of magnitude past that bisection,
and a loop that calls it multiplies the count. If an algorithm is past that,
measure it on the calculator as soon as it compiles, not at the end. Moving
the heavy computation into Python is a real option rather than a detour: the
bridge crossing was timed once at 0.2 ms
([micropython.bridge-cost](micropython.md#micropython.bridge-cost)), which is nothing
next to this.

**Evidence.** The bisection was timed by hand on a G2 with firmware 2.4.15515.
MicroPython's own speed on the Prime has not been measured.


<a name="ppl.mu-zero-spelling"></a>
## One name on the list cannot be typed as the list spells it

| | |
|---|---|
| Identifier | `ppl.mu-zero-spelling` |
| Kind | rule |
| Known from | emulator |

The Inference app's null-hypothesis mean is on HP's list as `μ₀`,
spelled with GREEK SMALL LETTER MU, U+03BC. The calculator refuses that name
and answers to the same two glyphs spelled with MICRO SIGN, U+00B5. The two
are indistinguishable on screen.

**Evidence.** Both were read in the same app, with Inference active. U+03BC
followed by U+2080 was refused, twice, in two different batches. U+00B5
followed by U+2080 answered 0.5. Every other Greek name in the same sweep
answered as the list spells it -- `π₀`, `σ₁` and
`σ₂` among them -- so this is one name's spelling and not a rule
about Greek letters.

**In a program's source the Greek mu does not compile** (emulator):
`RETURN Inference.μ₀;` with U+03BC did not compile, and the same with U+00B5
compiled and answered 0.5. The app's name was in front, so the app rule was
not what refused it. This was measured on the Virtual Calculator 2.4, build 2025-09-15, on 2026-09-25, by `hpprime examples --compile`, with its two controls coming out as they must ([results.tsv](../commands/results.tsv)).

**What it costs.** A person reading HP's documentation, or a model trained
on it, types the refused one. `hpprime lint` makes it an error, in a
program's code though not in its strings. `docs/commands/names.tsv` is generated from
HP's Command Tree and is not edited by hand, so the list keeps HP's spelling
and this fact carries the correction.
