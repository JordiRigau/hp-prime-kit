# PPL: what is measured

Reference firmware: **G2, 2.4 revision 15515 (2025-09-15)**. Everything here
was checked on a real calculator. Anything that was not is marked
**Unverified**.

New to the Prime? Start with [the guided path](../start/01-setup.md). This
page is reference, not a tutorial.

---

## 1. The limits that actually break

| What will not compile | Why | The way that works |
|---|---|---|
| **`LOCAL` with too many variables** | the limit is **7-8 per statement**. It reports *syntax error* on the `LOCAL` line, without saying what is wrong with it | several `LOCAL` statements in a row, in groups of 6 |
| `n := SIZE(M)(1);` | you cannot index the result of a call | `d := DIM(M);` and then `d(1)` |
| `EXPORT A:=1, B:=2, …;` | failed with 7 initialised variables on one line | one declaration per line |
| `LOCAL` half way down a function | every local goes together at the top of the `BEGIN` | declare them all first |
| `ENDIF`, `ENDFOR`, `ENDWHILE` | they do not exist | `END` closes everything |
| **Indexing a global declared in ANOTHER program** | the compiler does not know it is a list, so it reads `NAMES(1)` as **a call to a function** called `NAMES` | copy it to a local first: `zn := NAMES;` then `zn(1)` |

That last one is easy to miss, because the same code compiles when the
declaration is in the same file.

**Evidence for the `LOCAL` limit**, measured against programs that compile on
that same calculator: one that declares **8** compiles; three others stop at
**7**. The functions that failed declared **13, 16 and 18**.

`hpprime lint` catches all of these except the last one, which cannot be
decided by looking at one file: `TS1(1)` and `AREA(3,350)` are written the
same way.

## 2. Hypotheses that turned out FALSE

Do not repeat them. Each one cost a compile round.

| Hypothesis | Why it is false |
|---|---|
| "`RETURN` inside a `FOR`/`REPEAT` is not allowed" | a program that works has two of them |
| "letter + digit is reserved (`r2`, `y1`)" | a program that compiles uses `L12, L13, L14, L15…` as locals |
| "`LOCAL m` clashes with the `M0..M9` matrices" | coincidence: what was failing was the number of locals |
| "several locals with initial values on one line" | published tutorial code uses `local x1:=160, x2:=299, x3:=21` |

**Unverified**: `i` (the imaginary unit) and `e` (Euler's number) as local
names. Prefixing locals (`zm`, `zres`…) costs nothing and settles the
question.

## 3. The syntax, briefly

```ppl
// line comment
/* block */

EXPORT VAR1, VAR2;              // globals, they persist between uses
EXPORT MYDATA:=[[1,2],[3,4]];

EXPORT FUNC(a, b)
BEGIN
  LOCAL x, y;                   // ALL the locals, at the top
  x := a + b;
  RETURN x;
END;                            // the ; after END is required
```

- `EXPORT` makes a function visible from other programs and from Home;
  without it the function is private to its file.
- **Everything is 1-based.** This is the most common mistake coming from
  Python.
- Equality `==`, assignment `:=`, not-equal `<>`. Logicals `AND`, `OR`, `NOT`.
- **There is error trapping, but no exceptions of your own.**
  `IFERR statements THEN statements [ELSE statements] END;` traps a system
  error and leaves its code in `Ans` (`STRINGFROMID` turns it into a
  message). What does **not** exist is a way to raise your own error with a
  value inside, so an API that returns results still needs a convention: a
  region code of `-1` with the reason, say, and `{}` from functions that
  return lists. `IFERR` is for hardening one call, not for propagating
  errors.

| What you need | PPL |
|---|---|
| size of a list or string | `SIZE(L)` |
| dimensions of a matrix | `d := DIM(M);` → `d(1)`, `d(2)` |
| append to a list | `L(SIZE(L)+1) := v;` or `L := CONCAT(L, {v});` |
| number → string / string → number | `STRING(x)` / `EXPR(s)` |
| type of a variable | `TYPE(v)` (0 real, 2 string, 3 matrix, 6 list) |

Control flow: `IF … THEN … ELSE … END;` · `FOR i FROM 1 TO n DO … END;`
(`DOWNTO` and `STEP` too) · `WHILE … DO … END;` · `REPEAT … UNTIL c;` ·
`CASE … DEFAULT … END;` · `IFERR … THEN … END;` · `BREAK` · `CONTINUE` ·
`KILL` · `IFTE(c, a, b)` as an expression.

Keywords are **case-insensitive** (`local x := 1;` is fine); variable names
are not.

Input and output:

```ppl
INPUT({v1,v2}, "Title", {"Label1:","Label2:"}, {"help1","help2"});  // 1 = OK
CHOOSE(var, "Title", "opt1", "opt2");    // var receives the index
MSGBOX("message");
RECT();                                  // clears the screen (320x240)
TEXTOUT_P("text", x, y, font, RGB(r,g,b));
WAIT(-1);                                // waits for a key, returns its code
```

## 4. Run-time traps

| Trap | Detail |
|---|---|
| **Matrices are passed by value** | handing a big matrix to a function **copies** it. With large data, reach for a global instead of passing an argument |
| **`EXPR("")` fails** | always check `SIZE(s) > 0` before evaluating what came out of a field |
| **`LEFT(s, 0)` and `RIGHT(s, 0)` return the WHOLE string** | measured on a G2. A count that computes to zero gives you everything instead of nothing, silently |
| **`MID(s, start, 0)` returns the EMPTY string** | the same zero, the opposite answer. `MID` also takes a **length**, not an end position, and with two arguments it runs to the end |
| **`INSTRING` answers 0 when it finds nothing** | and **1** when the second argument is empty |
| **Global names** | exported names share one namespace with Home: prefix them so they do not collide |
| **Decimal point in source** | always `.`, even on a calculator that displays `,` |
| **Dynamic access** | `EXPR("NAME")` gives the variable whose name you built on the fly; do it once at load time, never per element |
| **`INPUT` builds its labels once** | it is modal, so a label that depends on another field of the same form cannot be refreshed. Offer fixed variants instead |
| **`WAIT(-1)`** | returns a key *position* identifier, **not ASCII**. Confirm with a probe: `[Enter]` is 30 |
| **A blank app** | has no view to rest in, so `[View]`/`[Num]` never reach the program: draw the menu yourself and read the keys yourself |
| **Compilation order** | a program only sees another's functions **if it was compiled afterwards**. Send data → engine → app |
| **What an app's program exports** | is tied to that app. If the engine has to be reusable, put it in a catalogue program |
| **Global state in a library** | if your library has an "active substance" or similar, a calculation mixing two has to reload before each query. Keep a global saying what is loaded and reload only on change |
| **A function with no `RETURN` is not silent** | it answers with the value of its last bare expression. Measured: a function ending in a call to another came back with that function's value. So you cannot make a program return nothing by leaving `RETURN` out |
| **`GETKEY` takes no parentheses in PPL** | `zk := GETKEY;`. From Python, across the bridge, it does: `eval('GETKEY()')` |
| **On Home, a function with no arguments is called without parentheses** | `MYFUNC` runs it; `MYFUNC()` answers *syntax error*. Inside PPL source the parentheses are correct and required -- see below |

### Calling a function from Home

The empty argument list is the one place where Home and PPL source disagree,
and it bites on the very first thing you do after installing a program.

| Where | With no arguments | With arguments |
|---|---|---|
| **Home** | `MYFUNC` — `MYFUNC()` is a *syntax error* | `AREA(2)` |
| **Inside PPL source** | `MYFUNC()` | `AREA(2)` |

**Evidence**, measured on a G2 (firmware 2.4.15515): typing `SELF3()` on Home
answers *syntax error*; `SELF3` returns 1. That same program's source
contains `IF SELF1() == 385 AND SIZE(SELF2()) == 23`, and it compiled and
returned 1 -- so the parentheses are right in source and wrong on Home, not
wrong everywhere.

It is the same convention the built-in `GETKEY` follows in PPL, generalised
to your own functions: an empty pair of parentheses is not how the Home
parser reads a call.

The screen and keyboard traps -- `WAIT(-1)`, touch, key codes, text that
overflows -- have their own page: [interface.md](interface.md).

## 5. Speed: the one anchor there is

PPL is **interpreted**, and there is no published figure for what an
operation costs. The only thing measured on physical hardware:

> An inverse lookup by bisection -- **60 iterations**, each one a double
> interpolation over matrices -- is "noticeable, but under a second". (G2.)

That is enough for an order of magnitude, and it is worth doing the sum
**before** committing to a design: a 53×49 Gauss-Jordan is about **45,000**
floating-point operations, two orders of magnitude more than that bisection,
and if a loop calls it repeatedly the count multiplies.

Rule of thumb: if your algorithm is past that, **measure it on the
calculator as soon as it compiles**, not at the end. And remember that the
bridge to Python costs **0.2 ms per crossing** (measured), which is nothing
next to this -- so moving the heavy computation into Python is a real
option, not a detour.

**Unverified**: MicroPython's own speed on the Prime. Only the bridge
crossing has been measured.

## 6. Where to look things up

| Source | What it is good for |
|---|---|
| *HP Prime Programming Reference* (HP) | looking up one command, not for learning |
| **hpmuseum.org/forum**, HP Prime subforum | the best one: complete code and real behaviour |
| **hpcalc.org** | a program archive: **read code that already works before writing any** |
| **en.hpprime.club** (E. Shore / H. Klaver) | tutorials with examples that run |
| **udel.edu/~mm/hp/primePython** | the closest thing to a reference for Python on the Prime |

Direct links:
[undocumented limits](https://www.hpmuseum.org/cgi-bin/archv021.cgi?read=254706) ·
[E. Shore's tutorial](https://literature.hpcalc.org/community/hpprime-prog-tutorial.pdf) ·
[G2 firmware 2.4.15515](https://www.hpcalc.org/details/7783) ·
[Python libraries](https://udel.edu/~mm/hp/primePython/upython.html) ·
[Python Activities Book](https://literature.hpcalc.org/community/hpprime-python-activities.pdf)

> **If you are an AI agent reading this**: hpmuseum.org is protected against
> automated access and answers with a challenge you cannot pass. Do not try.
> The source that does allow reading is **hpcalc.org** -- and downloading
> somebody's program and **reading it** is worth more than any tutorial.
