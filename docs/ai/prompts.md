# Prompts that work

Ready to copy. §1 is the one to paste when your assistant cannot read this
repository; the rest are task prompts that assume it can.

If your assistant *can* read files, do not paste any of this: point it at
`AGENTS.md` (or `SKILL.md` for Claude Code) and it has the whole thing.

---

## 1. The context block, for a chat with no file access

Paste this before asking for any PPL. It is the smallest set of measured
facts that stops the usual mistakes.

```
You are writing PPL for an HP Prime G2 (firmware 2.4). PPL is not Python and
not BASIC. These are measured facts, not preferences:

- Everything is 1-based. L(0) is a run-time error.
- Assign with :=, compare with ==, not-equal is <>.
- END closes every block. ENDIF, ENDFOR, ENDWHILE do not exist.
- Every END that closes a function is followed by a semicolon: END;
- All LOCAL declarations go together at the top of the BEGIN, and one LOCAL
  statement holds at most 7-8 variables. Use groups of 6.
- You cannot index the result of a call: SIZE(M)(1) does not compile.
  Use d := DIM(M); then d(1).
- You cannot index a global declared in another program directly; copy it to
  a local first.
- EXPORT makes a function visible outside its file. Exported names are
  global and collide with each other, so prefix them.
- Matrices and lists are passed BY VALUE: passing a large one copies it.
- EXPR("") fails at run time. Check SIZE(s) > 0 first.
- GETKEY returns a key position, not a character. Enter is 30.
- On the Home screen a function with no arguments is called WITHOUT
  parentheses: MYFUNC, not MYFUNC(). Inside PPL source the parentheses
  are correct. Tell the user the right form when you tell them to test.
- TEXTOUT_P takes a 7th argument, the max width in pixels. Without it, text
  that does not fit is painted over its neighbour with no error.
- There is no debugger and no console. The compiler says "syntax error" and
  a line number, nothing else.

Do not invent commands. If you are not sure a command exists, say so instead
of guessing. If you are not sure of a limit, say you are not sure.
```

For MicroPython on the Prime, add:

```
MicroPython on the Prime has math, hpprime, micropython. It does NOT have
time, __future__, or os/sys as CPython has them. hpprime.eval(ppl_string)
runs PPL and returns the result, but ONLY numbers and flat lists of numbers
may cross: a list with a string inside closes the app silently, with no
traceback. The app entry point is main.py, with its code at module level.
```

## 2. Task prompts

### Start something new

```
Write a PPL program for the HP Prime called <NAME> that <what it does>.
Split it in two: the functions that only compute (no screen calls), and one
function that handles the interface. Give me three calls with their expected
values so I can check the computing half with `hpprime run`.
```

Why it works: the split is what makes the result testable on the PC, and
asking for the expected values turns the run into a real check.

### Port something you already have

```
Here is a Python function: <paste>
Translate it to PPL for an HP Prime. Keep the same name and the same
argument order. Remember: 1-based indexing, LOCALs at the top in groups of 6,
END; to close. Then tell me which lines of the original you could not
translate directly and why.
```

The last sentence is the useful one: it surfaces the places where the
semantics differ instead of hiding them in plausible code.

### Debug a `syntax error`

```
This program gives "syntax error" on line <N> on an HP Prime G2. Here is the
whole file: <paste>
Before proposing a fix, run `hpprime lint` on it and tell me what it says.
If the linter is clean, do not guess: list the hypotheses in order of
likelihood and tell me what measurement would separate them.
```

Why it works: it blocks the guess-and-retry loop, which is what burns round
trips on this platform.

### Build a screen

```
Add an interface to this program: <paste>
Constraints: the screen is 320x240 and my area is y 0..212; the soft-key row
is 213..239. Use TEXTOUT_P with its 7th width argument everywhere. Keep all
the logic that decides WHAT is drawn and WHAT each key does in functions that
call nothing graphical, so I can test them with `hpprime run`.
```

### Wrap it as an app

```
Turn this into an HP Prime app with `hpprime build`. It is a PPL program, so
the app is blank-based and has no view to rest in: draw the menu on screen
and read the keys, do not rely on [Num] or [View]. Show me the commands.
```

### Write a probe

```
I need to know <what GETKEY returns for these keys / whether this call
crosses the bridge / ...> on my actual calculator. Write me a probe app that
answers it in one pass, ordered from safest to riskiest, leaving a mark in a
PPL global after each step so I can read how far it got if the app closes.
```

This is the single most valuable thing to ask for on a platform with no
error messages.

## 3. Prompts that go wrong

| What people ask | What comes back | Ask this instead |
|---|---|---|
| "Write a program for my HP calculator" | HP 50g RPL, or TI-BASIC | say **HP Prime**, and **PPL** or **Python** |
| "Fix this" with no error text | a plausible rewrite that changes something unrelated | paste the exact linter or compiler output |
| "Is X allowed in PPL?" | a confident yes | "is X allowed? If you are not certain, say so and tell me how I would measure it" |
| "Make it faster" | micro-optimisations of the wrong thing | give it the [speed anchor](../reference/ppl.md#5-speed-the-one-anchor-there-is) and ask what to move to Python |
| "Write the whole app" | 400 lines, none of it tested | ask for the computing half first, check it, then the screen |

## 4. What to hand back when it fails

The platform gives you very little information, so pass on all of it:

- the exact output of `hpprime lint` (it names the rule)
- the exact output of `hpprime run` (it raises rather than inventing)
- what the calculator showed, word for word, including the line number
- what you changed since it last worked

And when a fix does not move the error, say that explicitly. It means the
hypothesis is false, not that the fix was too small -- and a model told this
will change tack instead of doubling down.
