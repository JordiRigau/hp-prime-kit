# Examples

Four things worth having, in the order you are likely to need them.

| | What it is |
|---|---|
| [`selftest/`](selftest/) | a PPL program that checks itself. Generate it, install it, run `SELF3()`: a `1` means the whole chain works, accents included |
| [`probe/`](probe/) | the first app to put on a calculator. Answers in one pass what cannot be answered from a PC: does the Python bridge respond, what does each key return, does touch arrive |
| [`conformance/`](conformance/) | compares real PPL against a Python reference over thousands of cases. This is the use that pays for the interpreter |
| [`apptest/`](apptest/) | an app that verifies, on its own screen, that a PPL app built end to end really opens and runs |
| [`keymap/`](keymap/) | prints the code of every key you press, until Esc. How any line of the key table gets measured |
| [`strings/`](strings/) | the two probes that measured what the string functions return, and where the TEXTOUT_P width goes. Kept for the edges still open |
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
