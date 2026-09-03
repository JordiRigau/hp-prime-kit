# -*- coding: utf-8 -*-
"""Linter tests: that it catches what it must, and stays quiet on good code.

The bad cases are real errors that cost compile rounds on the calculator.
The controls are code that DOES compile on a G2 and that was wrongly
suspected at some point: if the linter flags them, the linter is wrong.

    python tests/test_lint.py
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))
from hpkit import lint as L

# ------------------------------------------------------------- bad cases
BAD = [
    ('local-limit', """
EXPORT F(a)
BEGIN
  LOCAL zm, zn, zi, zj, zk, zp, zq, zr, zs, zt, zu, zv, zw;
  RETURN a;
END;
"""),
    ('index-call', """
EXPORT F(M)
BEGIN
  LOCAL n;
  n := SIZE(M)(1);
  RETURN n;
END;
"""),
    ('export-multiple', """
EXPORT A:=1, B:=2, C:=3, D:=4, E:=5, F:=6, G:=7;
"""),
    ('single-end', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN a := 1; ENDIF;
  RETURN a;
END;
"""),
    ('equality', """
EXPORT F(a)
BEGIN
  IF a = 1 THEN RETURN 2; END;
  RETURN 0;
END;
"""),
    ('one-based', """
EXPORT F(M)
BEGIN
  RETURN M(0,1);
END;
"""),
    ('local-first', """
EXPORT F(a)
BEGIN
  LOCAL x;
  x := a + 1;
  LOCAL y;
  RETURN x;
END;
"""),
    ('unbalanced', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    a := 1;
  RETURN a;
END;
"""),
    ('expr-empty', """
EXPORT F()
BEGIN
  LOCAL zs;
  zs := "";
  RETURN EXPR(zs);
END;
"""),
    ('textout-width', """
EXPORT F()
BEGIN
  TEXTOUT_P("a label that may not fit", G0, 4, 24, 2, RGB(0,0,0));
  RETURN 1;
END;
"""),
]

# -------------------------------------------------------------- controls
# Code that compiles on a real G2. No rule may fire on any of these.
GOOD = [
    ('RETURN inside a FOR', """
EXPORT F(n)
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO n DO
    IF zi > 3 THEN RETURN zi; END;
  END;
  RETURN 0;
END;
"""),
    ('locals of letter + digit', """
EXPORT F()
BEGIN
  LOCAL L12, L13, L14, r2, y1;
  L12 := 1;
  RETURN L12;
END;
"""),
    ('several locals with initial values', """
EXPORT F()
BEGIN
  LOCAL x1:=160, x2:=299, x3:=21;
  RETURN x1;
END;
"""),
    ('builtin called with a 0 argument', """
EXPORT F()
BEGIN
  TEXTOUT_P("hello", 4, 24, 3, RGB(0,0,180));
  RETURN 1;
END;
"""),
    ('exported list with commas in it', """
EXPORT LABELS:={"one","two","three","four","five","six","seven","eight"};
"""),
    ('EXPR behind a size guard', """
EXPORT F(zs)
BEGIN
  IF SIZE(zs) > 0 THEN
    RETURN EXPR(zs);
  END;
  RETURN 0;
END;
"""),
    ('TEXTOUT_P with its width argument', """
EXPORT F()
BEGIN
  TEXTOUT_P("a label", G0, 4, 24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
    ('TEXTOUT_P in the short form, whose width position is not measured', """
EXPORT F()
BEGIN
  TEXTOUT_P("a label", 4, 24, 2, RGB(0,0,0));
  RETURN 1;
END;
"""),
    ('a TEXTOUT_P call spanning two lines', """
EXPORT F()
BEGIN
  TEXTOUT_P("a label", G0, 4,
            24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
    ('8 locals, the most seen to compile', """
EXPORT F()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h;
  RETURN 1;
END;
"""),
]


def main():
    ok = bad = 0

    for rule, src in BAD:
        found, _ = L.check_source('case.hpprgm', src)
        rules = set(a.rule for a in found)
        if rule in rules:
            ok += 1
            print('  ok    catches %-20s' % rule)
        else:
            bad += 1
            print('  FAIL  misses %-20s (got: %s)'
                  % (rule, ', '.join(sorted(rules)) or 'nothing'))

    print('')
    for name, src in GOOD:
        found, _ = L.check_source('good.hpprgm', src)
        errors = [a for a in found if a.level == 'ERROR']
        if not errors:
            ok += 1
            print('  ok    quiet on %s' % name)
        else:
            bad += 1
            print('  FAIL  false alarm on %s: %s'
                  % (name, '; '.join(a.rule for a in errors)))

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
