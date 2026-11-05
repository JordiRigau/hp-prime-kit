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
EXPORT ZG := 5;
EXPORT BUMP() BEGIN ZG := ZG + 1; RETURN ZG; END;
EXPORT F() BEGIN BUMP(); BUMP(); RETURN ZG; END;
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

    # ppl.short-circuit, measured on the emulator: the side that does not
    # decide is skipped whole, so BUMP never runs and the counter stays at 0
    ('AND and OR skip the side that does not decide', """
EXPORT ZN := 0;
EXPORT BUMP() BEGIN ZN := ZN + 1; RETURN 1; END;
EXPORT F() BEGIN ZN := 0; IF 0 AND BUMP() == 1 THEN ZN := ZN + 10; END; IF 1 OR BUMP() == 1 THEN ZN := ZN + 0; END; RETURN ZN; END;
""", 'F()', 0.0),

    ('IFTE does not evaluate the clause that loses', """
EXPORT ZN := 0;
EXPORT BUMP() BEGIN ZN := ZN + 1; RETURN 1; END;
EXPORT F() BEGIN LOCAL zx; ZN := 0; zx := IFTE(1 == 1, 5, BUMP()); zx := IFTE(0 == 1, BUMP(), 6); RETURN ZN; END;
""", 'F()', 0.0),

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

    # --- the four HP's own documented examples corrected -------------------
    # Each of these answered a different number until tests/hp_examples.txt
    # was run against the interpreter. The full set lives there; these are
    # here so a regression shows up in the suite that people run first.
    ('ROUND with a NEGATIVE n is significant figures, not decimals', """
EXPORT F() BEGIN RETURN ROUND(7.8676, -2); END;
""", 'F()', 7.9),

    ('MIN over one list is its smallest element, not the list', """
EXPORT F() BEGIN RETURN MIN({1,8,2}); END;
""", 'F()', 1.0),

    ('MAX over two lists goes element by element', """
EXPORT F() BEGIN RETURN MAX({1,8,2},{2,4,6}); END;
""", 'F()', [2.0, 8.0, 6.0]),

    ('LOG takes a base as its second argument', """
EXPORT F() BEGIN RETURN LOG(8, 2); END;
""", 'F()', 3.0),

    ('MOD of a negative number, as on the emulator', """
EXPORT F() BEGIN RETURN (-9) MOD 4; END;
""", 'F()', 3.0),

    # The remainder takes the divisor's sign: floored, not Euclidean, as the
    # emulator answered on 2026-09-24 where HP's help says Euclidean.
    ('MOD by a negative number takes its sign', """
EXPORT F() BEGIN RETURN 9 MOD (-4); END;
""", 'F()', -3.0),

    # Measured on the Virtual Calculator 2.4, build 2025-09-15: the operator
    # words are written between their operands (docs/commands/arithmetic/
    # MOD.md, docs/commands/catalog/NTHROOT.md).
    ('9 MOD 4 answers 1, as on the emulator', """
EXPORT F() BEGIN RETURN 9 MOD 4; END;
""", 'F()', 1.0),

    ('MOD in parentheses can be added to', """
EXPORT F() BEGIN RETURN (9 MOD 4) + 100; END;
""", 'F()', 101.0),

    ('MOD binds looser than ==, as on the emulator', """
EXPORT F() BEGIN LOCAL n; n := 4; IF n MOD 2 == 0 THEN RETURN 1; END; RETURN 0; END;
""", 'F()', 1.0),

    ('3 NTHROOT 8 answers 2, as on the emulator', """
EXPORT F() BEGIN RETURN 3 NTHROOT 8; END;
""", 'F()', 2.0),

    # How they bind, measured on the Virtual Calculator on 2026-09-24.
    ('MOD sits with *, and before +', """
EXPORT F() BEGIN RETURN 9 MOD 4 + 100; END;
""", 'F()', 101.0),
    ('MOD and * go left to right', """
EXPORT F() BEGIN RETURN 2 * 7 MOD 4 + 9 MOD 4 * 2; END;
""", 'F()', 4.0),
    ('^ and a minus sign bind tighter than MOD', """
EXPORT F() BEGIN RETURN 2^3 MOD 5 + -9 MOD 4; END;
""", 'F()', 6.0),
    ('NTHROOT binds tighter than * and +', """
EXPORT F() BEGIN RETURN 2 * 3 NTHROOT 8 + 19; END;
""", 'F()', 23.0),
    ('MOD sits with / too, left to right', """
EXPORT F() BEGIN RETURN 8 / 2 MOD 3 + 9 MOD 4 / 2; END;
""", 'F()', 1.5),
    ('NTHROOT binds tighter than ^', """
EXPORT F() BEGIN RETURN 2 ^ 3 NTHROOT 8; END;
""", 'F()', 4.0),
    ('NTHROOT binds tighter than a minus sign', """
EXPORT F() BEGIN RETURN -3 NTHROOT 8; END;
""", 'F()', -2.0),
    ('8 variables in one LOCAL compile', """
EXPORT F() BEGIN LOCAL a,b,c,d,f,g,h,j; a := 8; RETURN a; END;
""", 'F()', 8.0),
    ('6 initialised variables in one EXPORT compile', """
EXPORT ZA:=1, ZB:=2, ZC:=3, ZD:=4, ZE:=5, ZF:=6;
EXPORT F() BEGIN RETURN ZA + ZF; END;
""", 'F()', 7.0),

    # All of these answered on a G2, with firmware 2.4.15515, on 2026-11-05.
    ('7 initialised variables in one EXPORT compile', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7;
EXPORT F() BEGIN RETURN 4750 + ZV1 + ZV7; END;
""", 'F()', 4758.0),
    ('8 initialised variables in one EXPORT compile', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8;
EXPORT F() BEGIN RETURN 4760 + ZV1 + ZV8; END;
""", 'F()', 4769.0),
    ('a prefixed name exported on its own', """
EXPORT ZV := 4781;
EXPORT F() BEGIN RETURN ZV; END;
""", 'F()', 4781.0),
    ('a LOCAL after other statements', """
EXPORT F() BEGIN LOCAL za; za := 4730; LOCAL zb; zb := 1; RETURN za + zb; END;
""", 'F()', 4731.0),
    ('a LOCAL after other statements, with none before it', """
EXPORT F() BEGIN IF 1 == 1 THEN 1; END; LOCAL zb; zb := 4732; RETURN zb; END;
""", 'F()', 4732.0),
    ('a LOCAL after other statements, with a value', """
EXPORT F() BEGIN LOCAL za; za := 0; LOCAL zb := 4733; RETURN za + zb; END;
""", 'F()', 4733.0),
    ('a LOCAL in a nested block, used inside it', """
EXPORT F()
BEGIN
  LOCAL za;
  za := 4734;
  IF za == 4734 THEN
    LOCAL zb;
    zb := 1;
    za := za + zb;
  END;
  RETURN za;
END;
""", 'F()', 4735.0),
    ('a call without parentheses, defined earlier', """
ZPF() BEGIN RETURN 4710; END;
EXPORT F() BEGIN RETURN ZPF; END;
""", 'F()', 4710.0),
    ('a call without parentheses, declared ahead', """
ZPG();
EXPORT F() BEGIN RETURN ZPG; END;
ZPG() BEGIN RETURN 4711; END;
""", 'F()', 4711.0),
    ('a call without parentheses, defined later', """
EXPORT F() BEGIN RETURN ZPH; END;
ZPH() BEGIN RETURN 4712; END;
""", 'F()', 4712.0),
    ('a call with parentheses, defined later', """
EXPORT F() BEGIN RETURN ZPH(); END;
ZPH() BEGIN RETURN 4713; END;
""", 'F()', 4713.0),
    ('a call without parentheses as a statement really calls', """
EXPORT ZPCNT := 0;
ZPI() BEGIN ZPCNT := ZPCNT + 1; END;
EXPORT F() BEGIN ZPCNT := 0; ZPI; ZPI; RETURN ZPCNT + 4720; END;
""", 'F()', 4722.0),

    # What a nested LOCAL leaves behind: all of these answered on a G2, on
    # 2026-11-05 (ppl.local-block-scope).
    ('a global read after a LOCAL of its name has ended', """
EXPORT zb := 2;
EXPORT F()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb;
END;
""", 'F()', 2.0),
    ('a LOCAL declared again after its block', """
EXPORT F()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  LOCAL zb := 4;
  RETURN zb;
END;
""", 'F()', 4.0),
    ('a nested LOCAL hides an outer one until its block ends', """
EXPORT F()
BEGIN
  LOCAL zb;
  zb := 1;
  IF zb == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5200;
END;
""", 'F()', 5201.0),
    ('and what it holds inside the block is its own', """
EXPORT F()
BEGIN
  LOCAL zb, zs;
  zb := 1;
  IF zb == 1 THEN
    zb := 5;
    LOCAL zb;
    zb := 3;
    zs := zb;
  END;
  RETURN zb * 10 + zs;
END;
""", 'F()', 53.0),
    ('a LOCAL of a FOR, read inside it', """
EXPORT F()
BEGIN
  LOCAL zi, zs;
  zs := 0;
  FOR zi FROM 1 TO 2 DO
    LOCAL zb;
    zb := zi;
    zs := zs + zb;
  END;
  RETURN zs + 5210;
END;
""", 'F()', 5213.0),
    ('and in a FOR too', """
EXPORT F()
BEGIN
  LOCAL zi, zb;
  zb := 1;
  FOR zi FROM 1 TO 2 DO
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5420;
END;
""", 'F()', 5421.0),
    ('a LOCAL of a WHILE, read inside it', """
EXPORT F()
BEGIN
  LOCAL zi, zs;
  zi := 0;
  WHILE zi < 1 DO
    LOCAL zb;
    zb := 3;
    zs := zb;
    zi := 1;
  END;
  RETURN zs + 5230;
END;
""", 'F()', 5233.0),
    ('a LOCAL of a REPEAT, read inside it', """
EXPORT F()
BEGIN
  LOCAL zs;
  REPEAT
    LOCAL zb;
    zb := 3;
    zs := zb;
  UNTIL 1;
  RETURN zs + 5240;
END;
""", 'F()', 5243.0),
    ('a LOCAL of a CASE, read inside it', """
EXPORT F()
BEGIN
  CASE
    IF 1 == 1 THEN
      LOCAL zb;
      zb := 3;
      RETURN zb + 5220;
    END;
  END;
  RETURN 5221;
END;
""", 'F()', 5223.0),

    # Called like one of Home's variables: all compiled and answered on a G2, on
    # 2026-11-05 (ppl.export-home-variable).
    ('a function called F, with an argument', """
EXPORT F(za) BEGIN RETURN 5020 + za; END;
EXPORT ZRFB() BEGIN RETURN F(1); END;
""", 'ZRFB()', 5021.0),
    ('a call with no parentheses is the function and not the variable', """
EXPORT F() BEGIN RETURN 5012; END;
EXPORT ZRFN() BEGIN RETURN F; END;
""", 'ZRFN()', 5012.0),
    ('a parameter called X', """
ZRFH(X) BEGIN RETURN X + 5040; END;
EXPORT ZRFD() BEGIN RETURN ZRFH(1); END;
""", 'ZRFD()', 5041.0),
    ('a local called Z', """
EXPORT ZRFE() BEGIN LOCAL Z; Z := 5050; RETURN Z; END;
""", 'ZRFE()', 5050.0),
    ('a single = as a statement compares, and assigns nothing', """
EXPORT F() BEGIN LOCAL za; za := 1; za = 2; RETURN za; END;
""", 'F()', 1.0),
    ('i and e can be local names', """
EXPORT F() BEGIN LOCAL i, e; i := 2; e := 2; RETURN i * 3 + e + 1; END;
""", 'F()', 9.0),
    ('two NTHROOT go left to right', """
EXPORT F() BEGIN RETURN 2 NTHROOT 3 NTHROOT 64; END;
""", 'F()', 64 ** (1 / 3 ** 0.5)),
    ('a string indexed answers the character code', """
EXPORT F() BEGIN LOCAL zs, zi; zs := "abc"; zi := 2; RETURN zs(zi); END;
""", 'F()', 98.0),
    ('an odd root of a negative is real', """
EXPORT F() BEGIN RETURN 3 NTHROOT (-8); END;
""", 'F()', -2.0),

    # An index of 0 into a list, measured on the emulator on 2026-09-24.
    ('a list read at 0 answers its last element', """
EXPORT F() BEGIN LOCAL L, zi; L := {10,20,30}; zi := 0; RETURN L(zi); END;
""", 'F()', 30.0),
    ('a list assigned at 0 grows by one', """
EXPORT F() BEGIN LOCAL L, zi; L := {10,20,30}; zi := 0; L(zi) := 40; RETURN L; END;
""", 'F()', [10.0, 20.0, 30.0, 40.0]),

    ('SIZE of a MATRIX is its dimensions, not its element count', """
EXPORT F() BEGIN RETURN SIZE([[1,2,3],[4,5,6]]); END;
""", 'F()', [2.0, 3.0]),

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

    ('SORT of an empty list is an empty list', """
EXPORT F() BEGIN RETURN SIZE(SORT({})); END;
""", 'F()', 0.0),

    ('MID with two arguments past the end is empty', """
EXPORT F() BEGIN RETURN SIZE(MID("abcdef", 9)); END;
""", 'F()', 0.0),

    # A function that falls off the end answers with the last statement
    # that produced a value. One case per ending, all measured on a G2.
    ('no RETURN, ending in a call', """
EXPORT G() BEGIN RETURN 43; END;
EXPORT F() BEGIN LOCAL z; z := 1; G(); END;
""", 'F()', 43.0),

    ('no RETURN, ending in an assignment', """
EXPORT F() BEGIN LOCAL z; z := 1; END;
""", 'F()', 1.0),

    ('no RETURN, ending in a FOR: the last value the body produced', """
EXPORT F() BEGIN LOCAL z, zi; z := 0; FOR zi FROM 1 TO 2 DO z := zi; END; END;
""", 'F()', 2.0),

    ('no RETURN, ending in an IF that does not run', """
EXPORT F() BEGIN LOCAL z; z := 0; IF z == 1 THEN z := 2; END; END;
""", 'F()', 0.0),

    ('a bare RETURN compiles, and answers 0', """
EXPORT F() BEGIN LOCAL z; z := 5; RETURN; END;
""", 'F()', 0.0),

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
    ('a matrix read at 0, an error on the emulator', """
EXPORT F() BEGIN LOCAL M, zi; M := [[1,2],[3,4]]; zi := 0; RETURN M(zi, 1); END;
""", 'F()'),
    ('an empty list read at 0, an error on the emulator', """
EXPORT F() BEGIN LOCAL L, zi; L := {}; zi := 0; RETURN L(zi); END;
""", 'F()'),
    ('a string read at 0, an error on the emulator', """
EXPORT F() BEGIN LOCAL zs, zi; zs := "abc"; zi := 0; RETURN zs(zi); END;
""", 'F()'),
    ('an even root of a negative, refused on the emulator', """
EXPORT F() BEGIN RETURN 2 NTHROOT (-4); END;
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
    ('MID with two arguments and a start below 1, also an error', """
EXPORT F() BEGIN RETURN MID("abcdef", 0); END;
""", 'F()'),
    ('SORT of a string, an error on the calculator', """
EXPORT F() BEGIN RETURN SORT("cba"); END;
""", 'F()'),
    ('SORT of a list mixing types, an error on the calculator', """
EXPORT F() BEGIN RETURN SORT({1,"a"}); END;
""", 'F()'),
    ('LEFT of something that is not a string', """
EXPORT F() BEGIN RETURN LEFT(42, 2); END;
""", 'F()'),

    # Measured on the Virtual Calculator 2.4, build 2025-09-15, in
    # docs/commands/results.tsv. HP's help says a count of 0 or less returns
    # the whole string: 0 does, -1 does not, and the entries say so.
    ('LEFT with a negative count', """
EXPORT F() BEGIN RETURN LEFT("abcdef", -1); END;
""", 'F()'),

    ('RIGHT with a negative count', """
EXPORT F() BEGIN RETURN RIGHT("abcdef", -1); END;
""", 'F()'),

    # What the calculator refuses to compile, this refuses to load.
    ('9 variables in one LOCAL, which does not compile', """
EXPORT F() BEGIN LOCAL a,b,c,d,f,g,h,j,k; RETURN 1; END;
""", 'F()'),
    ('a function whose END has no semicolon', """
EXPORT F() BEGIN RETURN 1; END
""", 'F()'),
    ('9 initialised variables in one EXPORT', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8, ZV9:=9;
EXPORT F() BEGIN RETURN ZV1; END;
""", 'F()'),
    ('9 variables with no values in one EXPORT', """
EXPORT ZV1, ZV2, ZV3, ZV4, ZV5, ZV6, ZV7, ZV8, ZV9;
EXPORT F() BEGIN RETURN 5091; END;
""", 'F()'),
    ("Z exported, on its own", """
EXPORT Z := 4781;
EXPORT F() BEGIN RETURN Z; END;
""", 'F()'),
    ("Z exported with no value", """
EXPORT Z;
EXPORT F() BEGIN RETURN 5081; END;
""", 'F()'),
    ("Y exported, on its own", """
EXPORT Y := 5060;
EXPORT F() BEGIN RETURN 5061; END;
""", 'F()'),
    ("A exported, on its own", """
EXPORT A := 5070;
EXPORT F() BEGIN RETURN 5071; END;
""", 'F()'),
    ("Y and Z exported together", """
EXPORT Y := 1, Z := 4782;
EXPORT F() BEGIN RETURN Z + Y; END;
""", 'F()'),
    ('a LOCAL read after its block ends', """
EXPORT F()
BEGIN
  LOCAL za;
  za := 4734;
  IF za == 4734 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN za + zb;
END;
""", 'F()'),
    ('a LOCAL of a FOR read after it', """
EXPORT F()
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO 2 DO
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5100;
END;
""", 'F()'),
    ('a LOCAL of a WHILE read after it', """
EXPORT F()
BEGIN
  LOCAL zi;
  zi := 0;
  WHILE zi < 1 DO
    LOCAL zb;
    zb := 3;
    zi := 1;
  END;
  RETURN zb + 5110;
END;
""", 'F()'),
    ('a LOCAL of a REPEAT read after it', """
EXPORT F()
BEGIN
  REPEAT
    LOCAL zb;
    zb := 3;
  UNTIL 1;
  RETURN zb + 5120;
END;
""", 'F()'),
    ('a LOCAL of a CASE read after it', """
EXPORT F()
BEGIN
  CASE
    IF 1 == 1 THEN
      LOCAL zb;
      zb := 3;
    END;
  END;
  RETURN zb + 5130;
END;
""", 'F()'),
    ('a LOCAL of an ELSE read after it', """
EXPORT F()
BEGIN
  IF 0 == 1 THEN
    1;
  ELSE
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5140;
END;
""", 'F()'),
    ('a LOCAL of a THEN read in its ELSE', """
EXPORT F()
BEGIN
  IF 0 == 1 THEN
    LOCAL zb;
    zb := 3;
  ELSE
    RETURN zb + 5150;
  END;
  RETURN 5151;
END;
""", 'F()'),
    ('a LOCAL of an IFERR read after it', """
EXPORT F()
BEGIN
  IFERR
    LOCAL zb;
    zb := 3;
  THEN
    1;
  END;
  RETURN zb + 5160;
END;
""", 'F()'),
    ('a LOCAL of a REPEAT read in its own UNTIL', """
EXPORT F()
BEGIN
  LOCAL zs;
  zs := 0;
  REPEAT
    LOCAL zb;
    zb := 3;
    zs := zb;
  UNTIL zb == 3;
  RETURN zs + 5410;
END;
""", 'F()'),
    ('a LOCAL of what an IFERR tries, read in its THEN', """
EXPORT F()
BEGIN
  IFERR
    LOCAL zb;
    zb := 3;
  THEN
    RETURN zb + 5400;
  END;
  RETURN 5401;
END;
""", 'F()'),
    ('a LOCAL assigned after its block ends', """
EXPORT F()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  zb := 4;
  RETURN 5170;
END;
""", 'F()'),

    # Not measured, so not answered.
    ('another of the calculator\'s variables exported', """
EXPORT B := 1;
EXPORT F() BEGIN RETURN B; END;
""", 'F()'),
    ('9 in one EXPORT, some with values and some without', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8, ZV9;
EXPORT F() BEGIN RETURN 1; END;
""", 'F()'),
    ('a LOCAL in a block that repeats a parameter', """
EXPORT F(zb)
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb;
END;
""", 'F(1)'),

    # The calculator refuses the call forms of its operator words when it
    # compiles (emulator), so they must not answer here.
    ('MOD written as a call', """
EXPORT F() BEGIN RETURN MOD(9, 4); END;
""", 'F()'),
    ('NTHROOT written as a call', """
EXPORT F() BEGIN RETURN NTHROOT(3, 8); END;
""", 'F()'),

    ('a word it does not know, after an expression', """
EXPORT F() BEGIN RETURN 9 FOO 4; END;
""", 'F()'),
    ('the same word after an assignment', """
EXPORT F() BEGIN LOCAL z; z := 9 FOO 4; RETURN z; END;
""", 'F()'),

    # A builtin handed what it was not written for: a Python TypeError here
    # used to end `hpprime run` with a traceback. HP's own examples hit it.
    ('CONCAT handed a number', """
EXPORT F() BEGIN RETURN CONCAT({1,2,3}, 4); END;
""", 'F()'),
    ('FLOOR handed a list', """
EXPORT F() BEGIN RETURN FLOOR({3.2, -3.2}); END;
""", 'F()'),
    ('a minus sign before a string', """
EXPORT F() BEGIN RETURN -"abc"; END;
""", 'F()'),
]


def uncovered_stays_local():
    """A function the interpreter cannot cover must not stop the rest of the
    file from loading and running: it raises when it is called, and only
    then."""
    m = P.Machine()
    m.load('EXPORT GOOD() BEGIN RETURN 9 MOD 4; END;\n'
           'EXPORT BAD() BEGIN RETURN 2.5 NTHROOT (-8); END;\n'
           'EXPORT ODD() BEGIN RETURN 9 FOO 4; END;')
    if m.call('GOOD') != 1.0:
        return False, 'GOOD did not answer 1'
    for name in ('BAD', 'ODD'):
        try:
            got = m.call(name)
            return False, '%s answered %r' % (name, got)
        except P.Unsupported:
            pass
    return True, ''


def not_covered_is_not_an_error():
    """What the calculator has and this does not implement is a case not
    covered, never a refusal the calculator would make: a name with its
    app's name in front, which compiles and runs on the calculator
    (apps.qualified-names), a name on HP's list, and one that starts with a
    letter outside ASCII. A name nobody has stays undefined."""
    m = P.Machine()
    m.load('EXPORT GOOD() BEGIN RETURN 7; END;\n'
           'EXPORT QREAD() BEGIN RETURN Statistics_1Var.MeanX; END;\n'
           'EXPORT QSET() BEGIN Statistics_1Var.D1 := {1,2}; RETURN 1; END;\n'
           'EXPORT QCALL() BEGIN RETURN Spreadsheet.SUM({1,2,3}); END;\n'
           'EXPORT QSTORE() BEGIN 3 \u25b6 Finance.PV; RETURN 1; END;\n'
           'EXPORT LISTED() BEGIN RETURN Xmin; END;\n'
           'EXPORT LCALL() BEGIN RETURN SSS(3,4,5); END;\n'
           'EXPORT GREEK() BEGIN RETURN \u03a3LIST({1,2,3}); END;\n'
           'EXPORT NOBODY() BEGIN RETURN ZQNOSUCH; END;')
    if m.call('GOOD') != 7.0:
        return False, 'GOOD did not answer 7'
    for name in ('QREAD', 'QSET', 'QCALL', 'QSTORE', 'LISTED', 'LCALL',
                 'GREEK'):
        try:
            got = m.call(name)
            return False, '%s answered %r' % (name, got)
        except P.Unsupported:
            pass
        except P.PPLError as e:
            return False, '%s was called an error: %s' % (name, e)
    try:
        m.call('NOBODY')
        return False, 'NOBODY answered'
    except P.PPLError:
        pass
    except P.Unsupported as e:
        return False, 'NOBODY was called not covered: %s' % e
    return True, ''


def cli_never_tracebacks():
    """hpprime run prints one line and exits 1 on what it does not cover,
    at load time and at run time, and on a --call with something after the
    expression: never a Python traceback."""
    import io as _io
    import tempfile
    folder = tempfile.mkdtemp()
    cases = [('EXPORT F() BEGIN RETURN CONCAT({1}, 2); END;', 'F()'),
             ('EXPORT F() BEGIN RETURN "unterminated; END;', 'F()'),
             ('EXPORT F() BEGIN RETURN 1; END;', 'F() F()'),
             ('EXPORT F() BEGIN RETURN \u03c3X; END;', 'F()'),
             ('EXPORT F() BEGIN RETURN Solve.SOLVE(X^2-4=0,X,1); END;',
              'F()')]
    for k, (source, call) in enumerate(cases):
        path = os.path.join(folder, 'C%d.txt' % k)
        with _io.open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(source)
        out = _io.StringIO()
        saved, sys.stdout = sys.stdout, out
        try:
            rc = P.cli([path, '--call', call])
        except Exception as e:
            sys.stdout = saved
            return False, '%r raised %r' % (source, e)
        finally:
            sys.stdout = saved
        if rc != 1 or 'ERROR' not in out.getvalue():
            return False, '%r gave %r' % (source, out.getvalue())
    return True, ''



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


def endless_loop_check():
    """A wait loop is correct PPL and can never finish here, because GETKEY
    reports "no key pressed". It has to stop with a message, not spin."""
    limit = P.LOOP_LIMIT
    P.LOOP_LIMIT = 2000                  # the mechanism, not the patience
    try:
        m = P.Machine()
        m.load('EXPORT F() BEGIN LOCAL zk; '
               'REPEAT zk := GETKEY; UNTIL zk >= 0; RETURN zk; END;')
        try:
            m.call('F')
            return False, 'it returned instead of stopping'
        except P.Unsupported as e:
            if 'GETKEY' not in str(e):
                return False, 'the message does not name the cause: %s' % e
            return True, ''
    finally:
        P.LOOP_LIMIT = limit


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

    # What the calculator refuses is one list, kept in the linter.
    from hpkit import interp as I, lint as L
    if I.EXPORT_REFUSED == L.EXPORT_REFUSED and \
            I.HOME_VARIABLE.pattern == L.CALC_VARIABLE.pattern:
        ok += 1
        print('  ok    the interpreter and the linter refuse the same exports')
    else:
        bad += 1
        print('  FAIL  the interpreter and the linter disagree on what cannot '
              'be exported')

    good, why = endless_loop_check()
    if good:
        ok += 1
        print('  ok    a loop that waits for a key stops, and says why')
    else:
        bad += 1
        print('  FAIL  the endless-loop guard: %s' % why)

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

    for check, what in ((uncovered_stays_local,
                         'a function not covered leaves the rest of the file '
                         'running'),
                        (not_covered_is_not_an_error,
                         'what the calculator has and this does not cover is '
                         'not called an error'),
                        (cli_never_tracebacks,
                         'hpprime run answers in one line, never a traceback')):
        good, why = check()
        if good:
            ok += 1
            print('  ok    %s' % what)
        else:
            bad += 1
            print('  FAIL  %s: %s' % (what, why))

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
