# Examples

Seven things worth having, in the order you are likely to need them.

| | What it is |
|---|---|
| [`selftest/`](selftest/) | a PPL program that checks itself. Generate it, install it, type `SELF3` on Home: a `1` means the whole chain works, accents included |
| [`probe/`](probe/) | the first app to put on a calculator. Answers in one pass what cannot be answered from a PC: whether the Python bridge responds, what each key returns, whether touch arrives |
| [`conformance/`](conformance/) | compares real PPL against a Python reference over thousands of cases. This is the use that pays for the interpreter |
| [`apptest/`](apptest/) | an app that verifies, on its own screen, that a PPL app built end to end really opens and runs |
| [`keymap/`](keymap/) | prints the code of every key you press, until Esc. How any line of the key table gets measured |
| [`touch/`](touch/) | prints what a touch sends, as `WAIT(-1)` events and as `MOUSE` readings. How the touch facts get measured |
| [`glyphs/`](glyphs/) | draws eight pairs of arrows and triangles, and waits. How to find out which symbols the font draws and which come out as an empty box |
| starters | not here: `hpprime new NAME` writes one, from [`templates/starters/`](../templates/starters/) |

```bash
# prove the writer works, end to end
hpprime write examples/selftest/SELFTEST.txt -o SELFTEST.hpprgm

# find out what your calculator actually does
hpprime build PROBE examples/probe/main.py

# find where two implementations of the same thing disagree
python examples/conformance/conformance.py
python examples/conformance/conformance.py --break   # see a real divergence
```

Everything here is checked by `python tests/test_examples.py`, so an example
that stops working fails the suite rather than wasting your afternoon.
