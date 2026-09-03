# -*- coding: utf-8 -*-
"""Interpreter tests, tied to no particular project.

Each case is a PPL program with a known result. The ones in the ERRORS
section check the opposite: that it **fails** where the calculator would
fail, instead of returning an invented number.

    python tests/test_interp.py
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..'))
from hpkit import interp as P

# (name, source, call, expected)
CASES = [
    ('arithmetic and precedence', """
EXPORT F() BEGIN RETURN 2 + 3 * 4 - 6 / 3; END;
""", 'F()', 12.0),

    ('power is right-associative', """
EXPORT F() BEGIN RETURN 2 ^ 3 ^ 2; END;
""", 'F()', 512.0),

    ('unary minus and parentheses', """
EXPORT F() BEGIN RETURN -(2 + 3) * 2; END;
""", 'F()', -10.0),

    ('lists are 1-based', """
EXPORT F() BEGIN LOCAL L; L := {10, 20, 30}; RETURN L(1) + L(3); END;
""", 'F()', 40.0),

    ('matrices are 1-based, row and column', """
EXPORT F() BEGIN LOCAL M; M := [[1,2,3],[4,5,6]]; RETURN M(2,1) * 10 + M(1,3); END;
""", 'F()', 43.0),

    ('DIM of a matrix', """
EXPORT F() BEGIN LOCAL M, d; M := [[1,2,3],[4,5,6]]; d := DIM(M); RETURN d(1)*100 + d(2); END;
""", 'F()', 203.0),

    ('SIZE of a list and of a string', """
EXPORT F() BEGIN RETURN SIZE({1,2,3,4}) * 10 + SIZE("abc"); END;
""", 'F()', 43.0),

    ('assigning to an element', """
EXPORT F() BEGIN LOCAL L; L := {1,2,3}; L(2) := 99; RETURN L(2); END;
""", 'F()', 99.0),

    ('appending at the end, a PPL idiom', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; L(SIZE(L)+1) := 7; RETURN SIZE(L)*100 + L(3); END;
""", 'F()', 307.0),

    ('assigning into a matrix', """
EXPORT F() BEGIN LOCAL M; M := [[1,2],[3,4]]; M(2,2) := 9; RETURN M(2,2); END;
""", 'F()', 9.0),

    ('IF / ELSE', """
EXPORT F(a) BEGIN IF a > 5 THEN RETURN 1; ELSE RETURN 2; END; END;
""", 'F(3)', 2.0),

    ('CASE falling through to DEFAULT', """
EXPORT F(a)
BEGIN
  LOCAL r;
  CASE
    IF a == 1 THEN r := 10; END;
    IF a == 2 THEN r := 20; END;
    DEFAULT r := 99;
  END;
  RETURN r;
END;
""", 'F(5)', 99.0),

    ('CASE taking the matching branch', """
EXPORT F(a)
BEGIN
  LOCAL r;
  CASE
    IF a == 1 THEN r := 10; END;
    IF a == 2 THEN r := 20; END;
    DEFAULT r := 99;
  END;
  RETURN r;
END;
""", 'F(2)', 20.0),

    ('FOR, summing', """
EXPORT F(n) BEGIN LOCAL i, s; s := 0; FOR i FROM 1 TO n DO s := s + i; END; RETURN s; END;
""", 'F(10)', 55.0),

    ('FOR DOWNTO', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 5 DOWNTO 1 DO s := s * 10 + i; END; RETURN s; END;
""", 'F()', 54321.0),

    ('FOR with a STEP', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 0 TO 10 STEP 2 DO s := s + 1; END; RETURN s; END;
""", 'F()', 6.0),

    ('RETURN inside a FOR (which is legal)', """
EXPORT F() BEGIN LOCAL i; FOR i FROM 1 TO 100 DO IF i > 4 THEN RETURN i; END; END; RETURN 0; END;
""", 'F()', 5.0),

    ('BREAK', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 1 TO 100 DO IF i > 3 THEN BREAK; END; s := s + i; END; RETURN s; END;
""", 'F()', 6.0),

    ('WHILE', """
EXPORT F() BEGIN LOCAL i; i := 1; WHILE i < 100 DO i := i * 2; END; RETURN i; END;
""", 'F()', 128.0),

    ('REPEAT UNTIL runs at least once', """
EXPORT F() BEGIN LOCAL i; i := 50; REPEAT i := i + 1; UNTIL i > 0; RETURN i; END;
""", 'F()', 51.0),

    ('binary search, the shape a lookup engine has', """
EXPORT FIND(M, c, x, r0, n)
BEGIN
  LOCAL lo, hi, mid;
  IF n < 2 THEN RETURN 0; END;
  IF x < M(r0, c) THEN RETURN 0; END;
  IF x > M(r0 + n - 1, c) THEN RETURN 0; END;
  lo := r0; hi := r0 + n - 1;
  WHILE hi - lo > 1 DO
    mid := IP((lo + hi) / 2);
    IF M(mid, c) <= x THEN lo := mid; ELSE hi := mid; END;
  END;
  RETURN lo;
END;
EXPORT F() BEGIN LOCAL M; M := [[10,1],[20,2],[30,3],[40,4]]; RETURN FIND(M,1,25,1,4); END;
""", 'F()', 2.0),

    ('globals persist between calls', """
EXPORT G := 5;
EXPORT BUMP() BEGIN G := G + 1; RETURN G; END;
EXPORT F() BEGIN BUMP(); BUMP(); RETURN G; END;
""", 'F()', 7.0),

    ('matrices are passed BY VALUE', """
EXPORT TOUCH(M) BEGIN M(1,1) := 999; RETURN 0; END;
EXPORT F() BEGIN LOCAL M; M := [[1,2],[3,4]]; TOUCH(M); RETURN M(1,1); END;
""", 'F()', 1.0),

    ('concatenating strings', """
EXPORT F() BEGIN RETURN "a" + "b" + STRING(3); END;
""", 'F()', 'ab3'),

    ('EXPR evaluates a string', """
EXPORT DATA := [[7,8]];
EXPORT F() BEGIN LOCAL M; M := EXPR("DATA"); RETURN M(1,2); END;
""", 'F()', 8.0),

    ('IFTE only evaluates the branch it takes', """
EXPORT F(a) BEGIN RETURN IFTE(a > 0, 10, 20); END;
""", 'F(1)', 10.0),

    ('AND / OR / NOT', """
EXPORT F() BEGIN IF (1 > 0) AND NOT (2 > 3) OR (0 == 1) THEN RETURN 1; ELSE RETURN 0; END; END;
""", 'F()', 1.0),

    ('<> means not equal', """
EXPORT F() BEGIN IF 2 <> 3 THEN RETURN 1; ELSE RETURN 0; END; END;
""", 'F()', 1.0),

    ('MIN MAX ABS IP FLOOR ROUND', """
EXPORT F() BEGIN RETURN MIN(3,5) + MAX(3,5) + ABS(-2) + IP(2.9) + FLOOR(2.9) + ROUND(2.346,2)*100; END;
""", 'F()', 3 + 5 + 2 + 2 + 2 + 235.0),

    ('IFERR catches the error', """
EXPORT F()
BEGIN
  LOCAL L, r;
  L := {1,2};
  r := 0;
  IFERR r := L(9); THEN r := -1; END;
  RETURN r;
END;
""", 'F()', -1.0),

    ('returning a list', """
EXPORT F() BEGIN RETURN {1, 2, 3}; END;
""", 'F()', [1.0, 2.0, 3.0]),

    ('an empty list as the error convention', """
EXPORT G(a) BEGIN IF a < 0 THEN RETURN {}; END; RETURN {a}; END;
EXPORT F() BEGIN RETURN SIZE(G(-1)); END;
""", 'F()', 0.0),

    ('keywords in lower case', """
export F() begin local x; x := 1; if x == 1 then return 42; end; return 0; end;
""", 'F()', 42.0),

    # --- linear algebra and constructors ---------------------------------
    # These are covered so that leaning on the calculator's own matrix
    # commands does not cost you the ability to test off the calculator.
    ('MAKEMAT sees I and J, 1-based', """
EXPORT F() BEGIN LOCAL M; M := MAKEMAT(I*10+J, 2, 3); RETURN M(2,3); END;
""", 'F()', 23.0),

    ('MAKEMAT of zeros', """
EXPORT F() BEGIN LOCAL M, d; M := MAKEMAT(0, 4, 5); d := DIM(M);
RETURN d(1)*100 + d(2) + M(3,3); END;
""", 'F()', 405.0),

    ('MAKEMAT square, with a single size', """
EXPORT F() BEGIN LOCAL M, d; M := MAKEMAT(1, 3); d := DIM(M);
RETURN d(1)*10 + d(2); END;
""", 'F()', 33.0),

    ('MAKELIST', """
EXPORT F() BEGIN LOCAL L; L := MAKELIST(X*X, X, 1, 5); RETURN L(4); END;
""", 'F()', 16.0),

    ('MAKELIST with a step', """
EXPORT F() BEGIN LOCAL L; L := MAKELIST(X, X, 0, 10, 2.5); RETURN SIZE(L)*100 + L(3); END;
""", 'F()', 505.0),

    ('RREF solves a system', """
EXPORT F() BEGIN LOCAL R; R := RREF([[2,1,5],[1,-1,1]]);
RETURN R(1,3)*10 + R(2,3); END;
""", 'F()', 21.0),

    ('RREF leaves the identity on the left', """
EXPORT F() BEGIN LOCAL R; R := RREF([[2,1,5],[1,-1,1]]);
RETURN R(1,1)*1000 + R(1,2)*100 + R(2,1)*10 + R(2,2); END;
""", 'F()', 1001.0),

    ('RREF survives a dependent row', """
EXPORT F() BEGIN LOCAL R; R := RREF([[1,2,3],[2,4,6]]);
RETURN R(2,1)*100 + R(2,2)*10 + R(2,3); END;
""", 'F()', 0.0),

    ('TRN', """
EXPORT F() BEGIN LOCAL T, d; T := TRN([[1,2,3],[4,5,6]]); d := DIM(T);
RETURN d(1)*100 + d(2)*10 + T(3,2); END;
""", 'F()', 326.0),

    ('IDENMAT', """
EXPORT F() BEGIN LOCAL M; M := IDENMAT(3); RETURN M(2,2)*10 + M(2,3); END;
""", 'F()', 10.0),

    ('DET', """
EXPORT F() BEGIN RETURN DET([[1,2],[3,4]]); END;
""", 'F()', -2.0),

    ('DET of a singular matrix is 0', """
EXPORT F() BEGIN RETURN DET([[1,2],[2,4]]); END;
""", 'F()', 0.0),

    ('INVERSE', """
EXPORT F() BEGIN LOCAL I; I := INVERSE([[4,7],[2,6]]);
RETURN I(1,1)*1000 + I(2,2)*100; END;
""", 'F()', 640.0),

    # --- the string functions, every case measured on a G2 ---------------
    ('LEFT', """
EXPORT F() BEGIN RETURN LEFT("abcdef", 3); END;
""", 'F()', 'abc'),

    ('RIGHT', """
EXPORT F() BEGIN RETURN RIGHT("abcdef", 3); END;
""", 'F()', 'def'),

    ('MID takes a LENGTH, not an end position', """
EXPORT F() BEGIN RETURN MID("abcdef", 2, 3); END;
""", 'F()', 'bcd'),

    ('MID stops at the end instead of failing', """
EXPORT F() BEGIN RETURN MID("abcdef", 4, 99); END;
""", 'F()', 'def'),

    ('INSTRING is 1-based', """
EXPORT F() BEGIN RETURN INSTRING("abcdef", "cd"); END;
""", 'F()', 3.0),

    ('INSTRING on the first character', """
EXPORT F() BEGIN RETURN INSTRING("abcdef", "a"); END;
""", 'F()', 1.0),

    ('INSTRING not found is 0', """
EXPORT F() BEGIN RETURN INSTRING("abcdef", "zz"); END;
""", 'F()', 0.0),

    ('LEFT beyond the end gives the whole string', """
EXPORT F() BEGIN RETURN LEFT("abcdef", 99); END;
""", 'F()', 'abcdef'),

    ('LEFT(s,0) gives the WHOLE string, not an empty one', """
EXPORT F() BEGIN RETURN LEFT("abcdef", 0); END;
""", 'F()', 'abcdef'),

    ('and its size confirms it', """
EXPORT F() BEGIN RETURN SIZE(LEFT("abcdef", 99)); END;
""", 'F()', 6.0),

    ('RIGHT(s,0) gives the whole string too', """
EXPORT F() BEGIN RETURN RIGHT("abcdef", 0); END;
""", 'F()', 'abcdef'),

    ('RIGHT beyond the end gives the whole string', """
EXPORT F() BEGIN RETURN RIGHT("abcdef", 99); END;
""", 'F()', 'abcdef'),

    ('MID with two arguments runs to the end', """
EXPORT F() BEGIN RETURN MID("abcdef", 2); END;
""", 'F()', 'bcdef'),

    ('MID from past the end is empty', """
EXPORT F() BEGIN RETURN SIZE(MID("abcdef", 7, 2)); END;
""", 'F()', 0.0),

    ('MID with a count of 0 is empty, unlike LEFT and RIGHT', """
EXPORT F() BEGIN RETURN SIZE(MID("abcdef", 2, 0)); END;
""", 'F()', 0.0),

    ('INSTRING with an empty second argument is 1', """
EXPORT F() BEGIN RETURN INSTRING("abcdef", ""); END;
""", 'F()', 1.0),

    ('SORT puts numbers in ascending order', """
EXPORT F() BEGIN LOCAL L; L := SORT({3,1,2}); RETURN L(1)*100+L(2)*10+L(3); END;
""", 'F()', 123.0),

    ('SORT does the same for strings', """
EXPORT F() BEGIN LOCAL L; L := SORT({"b","a"}); RETURN L(1) + L(2); END;
""", 'F()', 'ab'),

    ('a function with no RETURN gives its last expression, not nothing', """
EXPORT G() BEGIN RETURN 43; END;
EXPORT F() BEGIN LOCAL z; z := 1; G(); END;
""", 'F()', 43.0),

    ('GETKEY without parentheses, which is how PPL writes it', """
EXPORT F() BEGIN LOCAL zk; zk := GETKEY; RETURN zk; END;
""", 'F()', -1.0),

    ('nested lists: L(2)(1)', """
EXPORT F() BEGIN LOCAL L; L := {{1,2},{3,4}}; RETURN L(2)(1); END;
""", 'F()', 3.0),

    ('a matrix row can be indexed again', """
EXPORT F() BEGIN LOCAL M; M := [[1,2,3],[4,5,6]]; RETURN M(2)(3); END;
""", 'F()', 6.0),

]

# Cases where it must FAIL rather than invent a number
ERRORS = [
    ('indexing the return of a call, which the Prime rejects', """
EXPORT F(M) BEGIN RETURN SIZE(M)(1); END;
""", 'F([[1,2],[3,4]])'),
    ('MAKELIST with a step of 0 does not hang', """
EXPORT F() BEGIN RETURN MAKELIST(X, X, 1, 5, 0); END;
""", 'F()'),
    ('INVERSE of a singular matrix', """
EXPORT F() BEGIN RETURN INVERSE([[1,2],[2,4]]); END;
""", 'F()'),
    ('RREF of something that is not a matrix', """
EXPORT F() BEGIN RETURN RREF({1,2,3}); END;
""", 'F()'),
    ('index 0', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; RETURN L(0); END;
""", 'F()'),
    ('index out of range', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; RETURN L(5); END;
""", 'F()'),
    ('undefined variable', """
EXPORT F() BEGIN RETURN NOSUCHTHING + 1; END;
""", 'F()'),
    ('division by zero', """
EXPORT F() BEGIN RETURN 1 / 0; END;
""", 'F()'),
    ('a function that does not exist', """
EXPORT F() BEGIN RETURN WHATSIT(1); END;
""", 'F()'),
    ('EXPR of an empty string', """
EXPORT F() BEGIN RETURN EXPR(""); END;
""", 'F()'),
    # Edges of the string functions that were NOT measured. They raise
    # rather than extrapolate: an invented edge case is the divergence this
    # interpreter exists to catch.
    ('MID from before the start, an error on the calculator', """
EXPORT F() BEGIN RETURN MID("abcdef", 0, 2); END;
""", 'F()'),
    ('LEFT with a negative count, an error on the calculator', """
EXPORT F() BEGIN RETURN LEFT("abcdef", -1); END;
""", 'F()'),
    ('SORT of a string, an error on the calculator', """
EXPORT F() BEGIN RETURN SORT("cba"); END;
""", 'F()'),
    ('SORT of a list mixing types, which is not measured', """
EXPORT F() BEGIN RETURN SORT({1,"a"}); END;
""", 'F()'),
    ('LEFT of something that is not a string', """
EXPORT F() BEGIN RETURN LEFT(42, 2); END;
""", 'F()'),
]


def evaluate(source, call):
    m = P.Machine()
    m.load(source)
    return m.evaluate(P.Parser(P.lex(call), '<test>').expr(), {})


def same(a, b):
    if isinstance(b, list):
        return (isinstance(a, list) and len(a) == len(b)
                and all(same(x, y) for x, y in zip(a, b)))
    if isinstance(b, str):
        return a == b
    return isinstance(a, float) and abs(a - b) < 1e-9


def bom_check():
    """A source saved by a Windows editor starts with a byte order mark, and
    the lexer has no rule for that character: load_file has to strip it."""
    import io as _io
    import tempfile
    path = os.path.join(tempfile.mkdtemp(), 'BOM.txt')
    with _io.open(path, 'w', encoding='utf-8-sig', newline='\n') as f:
        f.write('EXPORT F() BEGIN RETURN 7; END;')
    m = P.Machine()
    m.load_file(path)
    return m.call('F') == 7.0


def main():
    ok = bad = 0
    for name, source, call, expected in CASES:
        try:
            got = evaluate(source, call)
        except Exception as e:
            bad += 1
            print('  FAIL  %-44s raised: %s' % (name, e))
            continue
        if same(got, expected):
            ok += 1
            print('  ok    %s' % name)
        else:
            bad += 1
            print('  FAIL  %-44s gave %r, expected %r'
                  % (name, got, expected))

    try:
        if bom_check():
            ok += 1
            print('  ok    a file with a byte order mark still loads')
        else:
            bad += 1
            print('  FAIL  a file with a byte order mark loaded wrong')
    except Exception as e:
        bad += 1
        print('  FAIL  a file with a byte order mark raised: %s' % e)

    print('')
    for name, source, call in ERRORS:
        try:
            got = evaluate(source, call)
        except (P.PPLError, P.Unsupported):
            ok += 1
            print('  ok    fails as it should: %s' % name)
        except Exception as e:
            bad += 1
            print('  FAIL  %-44s odd exception: %r' % (name, e))
        else:
            bad += 1
            print('  FAIL  %-44s should have failed, gave %r' % (name, got))

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
