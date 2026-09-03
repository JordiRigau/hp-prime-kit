# -*- coding: utf-8 -*-
"""Compare real PPL against a reference implementation in Python.

This is the use that pays for the interpreter. If you have the same
calculation written twice -- in PPL for the calculator, in Python to develop
against -- no ordinary test can tell you they have drifted apart: each
implementation is consistent with itself and both pass their own tests.
Running the actual PPL and comparing is what makes a divergence show up.

    python examples/conformance/conformance.py
    python examples/conformance/conformance.py --break

`--break` swaps in a reference with a deliberate bug, so you can see what a
real divergence looks like when it is found. Note how the mismatches cluster:
the cluster is what names the cause.

To adapt this to your own project, change the three marked functions.
"""
from __future__ import unicode_literals
import math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
from hpkit import interp

TOL = 1e-6


# ---------------------------------------------------------------- CHANGE ME
def load_ppl():
    """Load the PPL that runs on the calculator."""
    m = interp.Machine()
    m.load_file(os.path.join(HERE, 'ROOT.txt'))
    return m


def reference(c, broken=False):
    """The Python implementation you develop against."""
    if c < 0:
        return -1.0
    if broken and c < 1:
        # A whole region the reference does not handle. This is what a real
        # divergence looks like: not a typo, a case somebody forgot.
        return c / 2.0
    return math.sqrt(c)


def cases():
    """The inputs to sweep. Take them from your own data if you have it:
    cases you invent are the ones you already thought about."""
    out = [0.0, 1.0, 2.0, -1.0, 1e-6, 0.25, 0.5, 0.999]
    out += [i / 100.0 for i in range(1, 200)]
    out += [float(i) for i in range(1, 500)]
    return out
# ------------------------------------------------------------- END CHANGE ME


def main(argv):
    broken = '--break' in argv
    m = load_ppl()

    checked = mismatched = 0
    worst = (0.0, None)
    examples = []
    for c in cases():
        got = m.call('ROOT', c)
        want = reference(c, broken)
        checked += 1
        if want == 0:
            off = abs(got - want)
        else:
            off = abs(got - want) / abs(want)
        if off > TOL:
            mismatched += 1
            if len(examples) < 5:
                examples.append((c, got, want))
            if off > worst[0]:
                worst = (off, c)

    print('%d cases, %d mismatches' % (checked, mismatched))
    if not mismatched:
        print('The PPL and the reference agree everywhere that was swept.')
        print('(Run with --break to see what a divergence looks like.)')
        return 0

    print('worst relative difference %.3g at input %r' % worst)
    print('')
    print('  %-12s %-20s %-20s' % ('input', 'PPL', 'reference'))
    for c, got, want in examples:
        print('  %-12r %-20r %-20r' % (c, got, want))
    if mismatched > len(examples):
        print('  ... and %d more' % (mismatched - len(examples)))
    print('')
    print('Look at what the failures have in common before you look at the')
    print('code. When they all share a region of the input, the region is')
    print('the bug: some branch handles it and the other one does not.')
    return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
