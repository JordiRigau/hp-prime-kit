# Prompts that work

Ready to copy. §1 is the one to paste when your assistant cannot read this
repository; the rest are task prompts that assume it can.

If your assistant *can* read files, do not paste any of this. Point it at
[`docs/llms.txt`](../llms.txt), the index of every fact and command entry, and
at [`AGENTS.md`](../../AGENTS.md) for how to work here.

---

## 1. The context block, for a chat with no file access

Paste this before asking for any PPL. It is the smallest set of facts that
stops the usual mistakes.

It restates the documentation on purpose, because a chat with no file access
cannot read it. Every rule ends with the fact or the command entry it comes
from and how that is known, the way `hpprime lint` cites them. Where this
block and the documentation differ, the documentation is right: a test holds
every identifier here to a fact or an entry that exists, with the same label,
but not the wording around it.

```
You are writing PPL for an HP Prime G2 (firmware 2.4). PPL is not Python and
not BASIC. Each rule below ends with where it comes from, [identifier, label]:
G2 means measured on a physical HP Prime G2, emulator means run on HP's
Virtual Calculator. Cite the identifier when you rely on a rule.

- Indexes start at 1. A 0 is never the first element: for MID and for a
  matrix it is an error, and a list read at 0 answers its LAST element,
  silently. Never use 0 as an index. [ppl.one-based, G2]
- A string indexed like a list answers the character's CODE, a number:
  "abc" at 2 is 98, not "b". Use MID for text. [ppl.string-index-code,
  emulator]
- Assign with :=, compare with ==, not-equal is <>. A single = inside a
  condition compiles and compares like ==, but write ==.
  [ppl.equality-operators, emulator]
- END closes every block. ENDIF, ENDFOR, ENDWHILE do not exist.
  [ppl.no-end-keywords, G2]
- END is followed by a semicolon: END; A missing one is reported on the
  line after it. [ppl.end-semicolon, emulator]
- All LOCAL declarations go together at the top of the BEGIN.
  [ppl.locals-at-top, G2]
- One LOCAL statement holds at most 8 variables; 9 does not compile. Use
  groups of 6. [ppl.local-limit, G2]
- You cannot index the result of a call: SIZE(M)(1) does not compile.
  Use d := DIM(M); then d(1). [ppl.index-call, G2]
- Indexing a global declared in another program has been seen both to fail
  and to work on the same calculator; what separates the cases is not known.
  Copying it to a local first (zn := NAMES; then zn(1)) works either way, so
  prefer that, but do not state it as a rule.
  [ppl.global-index-other-program, G2]
- EXPORT makes a function visible outside its file. Exported names are
  global and collide with each other and with HP's own names (AREA is the
  Function app's), so prefix them. [ppl.global-namespace, G2]
- Matrices are passed BY VALUE: passing a large one copies it.
  [ppl.matrices-by-value, G2]
- EXPR("") fails at run time. Check SIZE(s) > 0 first. [ppl.expr-empty, G2]
- GETKEY returns a key position, not a character. Enter is 30.
  [interface.getkey-position, G2]
- LEFT(s,0) and RIGHT(s,0) return the WHOLE string, not an empty one, and
  so does asking for more characters than there are. MID(s,start,0) returns
  an EMPTY one. MID's third argument is a length, not an end position, and
  with two arguments it runs to the end. [LEFT, G2] [RIGHT, G2] [MID, G2]
- A function with no RETURN is not silent: it answers with the value of its
  last statement that produced one. You cannot make one return nothing by
  omitting it. [ppl.function-always-answers, G2]
- On the Home screen a function with no arguments is called WITHOUT
  parentheses: MYFUNC, not MYFUNC(). Inside PPL source the parentheses
  are correct. Tell the user the right form when you tell them to test.
  [ppl.home-no-parentheses, G2]
- TEXTOUT_P's last argument is the maximum width in pixels. Without it,
  text that does not fit is painted over its neighbour with no error.
  [interface.textout-width, G2]
- The compiler says "syntax error" and a line number, and the line is often
  not the one to fix: with several bad lines Check names one of them, the
  first or the last depending on the error. [ppl.check-last-error, emulator]
- x = 2; as a statement assigns NOTHING: it compares and throws the answer
  away, with no error. Assign with :=. [ppl.equality-operators, emulator]

Do not invent commands. If you are not sure a command exists, say so instead
of guessing. If you are not sure of a limit, say you are not sure.
```

For MicroPython on the Prime, add:

```
- MicroPython on the Prime has math, hpprime, micropython. It does NOT have
  time, __future__, or os/sys as CPython has them. [micropython.modules, G2]
- hpprime.eval(ppl_string) runs PPL and returns the result.
  [micropython.eval, G2]
- Only numbers and flat lists of numbers may cross: a list with a string
  inside closes the app silently, with no traceback.
  [micropython.list-with-string-closes-the-app, G2]
- Every Python app examined has its entry point in main.py, with its code at
  module level. Whether another name works is not known, so keep that.
  [apps.main-py, unverified]
```

## 2. Task prompts

### Start something new

```
Write a PPL program for the HP Prime called <NAME> that <what it does>.
Split it in two: the functions that only compute (no screen calls), and one
function that handles the interface. Give me three calls with their expected
values so I can check the computing half with `hpprime run`.
```

The split is what makes the result testable on the PC, and asking for the
expected values turns the run into a real check.

### Port something you already have

```
Here is a Python function: <paste>
Translate it to PPL for an HP Prime. Keep the same name and the same
argument order. Remember: 1-based indexing, LOCALs at the top in groups of 6,
END; to close. Then tell me which lines of the original you could not
translate directly and why.
```

The last sentence is the one that earns its place: it surfaces the lines
where the semantics differ, instead of leaving them inside plausible code.

### Debug a `syntax error`

```
This program gives "syntax error" on line <N> on an HP Prime G2. Here is the
whole file: <paste>
Before proposing a fix, run `hpprime lint` on it and tell me what it says.
If the linter is clean, do not guess: list the hypotheses in order of
likelihood and tell me what measurement would separate them.
```

It blocks the guess-and-retry loop, which is what burns round trips here.

### Build a screen

```
Add an interface to this program: <paste>
Constraints: the screen is 320x240 and my area is y 0..212; the row of
labels is 213..239. Pass TEXTOUT_P its width, the last argument, everywhere.
Keep all the logic that decides WHAT is drawn and WHAT each key does in
functions that call nothing graphical, so I can test them with `hpprime run`.
```

### Wrap it as an app

```
Turn this into an HP Prime app with `hpprime build`. It is a PPL program, so
the app is blank-based and has no view to rest in: the Num() and View()
hooks will not fire, but [Num] and [View] arrive through GETKEY as 11 and 9.
Draw the menu on screen and read the keys. Show me the commands.
```

### Write a probe

```
I need to know <what GETKEY returns for these keys / whether this call
crosses the bridge / ...> on my actual calculator. Write me a probe app that
answers it in one pass, ordered from safest to riskiest, leaving a mark in a
PPL global after each step so I can read how far it got if the app closes.
```

On a platform with no error messages, one probe answers in a single pass
what otherwise takes several round trips.

## 3. Prompts that go wrong

| What people ask | What comes back | Ask this instead |
|---|---|---|
| "Write a program for my HP calculator" | HP 50g RPL, or TI-BASIC | say **HP Prime**, and **PPL** or **Python** |
| "Fix this" with no error text | a plausible rewrite that changes something unrelated | paste the exact linter or compiler output |
| "Is X allowed in PPL?" | a confident yes | "is X allowed? If you are not certain, say so and tell me how I would measure it" |
| "Make it faster" | micro-optimisations of the wrong thing | give it the [speed anchor](../topics/ppl.md#ppl.speed-anchor) and ask what to move to Python |
| "Write the whole app" | 400 lines, none of it tested | ask for the computing half first, check it, then the screen |

## 4. What to hand back when it fails

The platform gives you very little information, so pass all of it on:

- the exact output of `hpprime lint` (it names the rule)
- the exact output of `hpprime run` (it raises rather than inventing)
- what the calculator showed, word for word, including the line number
- what you changed since it last worked

When a fix does not move the error, say so explicitly. It means the
hypothesis is false rather than the fix being too small, and a model told that
will change tack instead of trying a fourth variation.
