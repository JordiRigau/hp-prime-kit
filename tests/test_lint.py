# -*- coding: utf-8 -*-
"""Linter tests: that it catches what it must, and stays quiet on good code.

The bad cases are real errors that cost compile rounds on the calculator.
The controls are code that DOES compile on a G2 and that was wrongly
suspected at some point: if the linter flags them, the linter is wrong.

    python tests/test_lint.py
"""
from __future__ import unicode_literals
import io, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import lint as L                                   # noqa: E402

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
    ('export-limit', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8, ZV9:=9;
"""),
    ('export-home-variable', """
EXPORT Z := 1;
"""),
    ('single-end', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN a := 1; ENDIF;
  RETURN a;
END;
"""),
    ('one-based', """
EXPORT F(M)
BEGIN
  RETURN M(0,1);
END;
"""),
    ('local-scope', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    LOCAL y;
    y := a + 1;
  END;
  RETURN y;
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
EXPORT ZF()
BEGIN
  LOCAL zs;
  zs := "";
  RETURN EXPR(zs);
END;
"""),
    ('textout-width', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label that may not fit", G0, 4, 24, 2, RGB(0,0,0));
  RETURN 1;
END;
"""),
    ('textout-width', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label that may not fit", 4, 24, 2, RGB(0,0,0));
  RETURN 1;
END;
"""),
    # The command a model invents: there is no STRLEN in PPL.
    ('unknown-name', """
EXPORT F(zs)
BEGIN
  RETURN STRLEN(zs);
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
EXPORT ZF()
BEGIN
  LOCAL L12, L13, L14, r2, y1;
  L12 := 1;
  RETURN L12;
END;
"""),
    ('several locals with initial values', """
EXPORT ZF()
BEGIN
  LOCAL x1:=160, x2:=299, x3:=21;
  RETURN x1;
END;
"""),
    # Each of these three was an error here until a G2 compiled it, on
    # 2026-11-05: ppl.locals-at-top, ppl.export-initialised.
    ('a LOCAL after other statements', """
EXPORT ZF()
BEGIN
  LOCAL za;
  za := 4730;
  LOCAL zb;
  zb := 1;
  RETURN za + zb;
END;
"""),
    ('a LOCAL after other statements, with none before it', """
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN 1; END;
  LOCAL zb;
  zb := 4732;
  RETURN zb;
END;
"""),
    ('8 initialised variables in one EXPORT', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8;
"""),
    ('builtin called with a 0 argument', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("hello", 4, 24, 3, RGB(0,0,180));
  RETURN 1;
END;
"""),
    # The arrow is part of the name. Read without it, C→PX(0,0) looks like an
    # index 0 into a variable PX, and one-based fired on correct code.
    ('a name with an arrow in it, called with 0', """
EXPORT ZF()
BEGIN
  LOCAL zp;
  zp := C→PX(0,0);
  RETURN zp;
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
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label", G0, 4, 24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
    ('TEXTOUT_P in the short form, with its width', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label", 4, 24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
    ('a TEXTOUT_P call spanning two lines', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label", G0, 4,
            24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
    ('8 locals, the most seen to compile', """
EXPORT ZF()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h;
  RETURN 1;
END;
"""),
]

# ------------------------------------------------ names that are not strangers
# Every call in these is to a name PPL has or the program defines, so
# unknown-name must not appear at all, not even as a warning.
KNOWN_NAMES = [
    ('its own functions, exported or not, defined before or after', """
F2(za)
BEGIN
  RETURN za;
END;

EXPORT F(za)
BEGIN
  RETURN F2(za) + F3(za);
END;

F3(zb)
BEGIN
  RETURN zb;
END;
"""),
    ('a parameter and a local, indexed', """
EXPORT F(zl)
BEGIN
  LOCAL zm;
  zm := {1,2};
  RETURN zl(1) + zm(2);
END;
"""),
    ('an exported variable, indexed', """
EXPORT ZDATA:={1,2,3};
EXPORT ZF()
BEGIN
  RETURN ZDATA(2);
END;
"""),
    ("the calculator's own variables", """
EXPORT ZF()
BEGIN
  L1 := {1,2};
  M1 := [[1,2],[3,4]];
  RETURN L1(2) + M1(1,2) + A;
END;
"""),
    ('an app function, with and without its app', """
EXPORT ZF()
BEGIN
  RETURN AREA(1,2) + Function.AREA(1,2);
END;
"""),
    ('a CAS name', """
EXPORT F(zx)
BEGIN
  RETURN simplify(zx) + expand(zx);
END;
"""),
    ("the calculator's names in lower case", """
EXPORT F(zx)
BEGIN
  RETURN sin(zx) + size({1,2});
END;
"""),
    ('a forward declaration', """
F2();
EXPORT ZF()
BEGIN
  RETURN F2();
END;
F2()
BEGIN
  RETURN 1;
END;
"""),
    ('a #pragma line', """
#pragma mode( separator(.,;) integer(h32) )
EXPORT ZF()
BEGIN
  RETURN 1;
END;
"""),
    ('a call inside a block comment', """
/* STRLEN(s) would be wrong,
   but this is a comment */
EXPORT ZF()
BEGIN
  RETURN 1;
END;
"""),
    ('a call inside a string', """
EXPORT ZF()
BEGIN
  MSGBOX("STRLEN(s) is not a command");
  RETURN 1;
END;
"""),
]

# ---------------------------------------------------------------- evidence
# (what, rule, level, label, source). A rule is an ERROR where it matches
# what was measured, with its fact's label, and a warning labelled
# unverified where its pattern reaches further. A level of None means the
# rule must not fire at all: the case is not what the rule is about.
EVIDENCE = [
    ('a call indexed where it is produced', 'index-call', 'ERROR', 'G2', """
EXPORT F(M)
BEGIN
  RETURN SIZE(M)(1);
END;
"""),
    ("the file's own function, indexed", 'index-call', 'ERROR', 'G2', """
F2(n)
BEGIN
  RETURN {n};
END;
EXPORT ZF()
BEGIN
  RETURN F2(1)(1);
END;
"""),
    ('a nested list, indexed twice', 'index-call', None, None, """
EXPORT ZF()
BEGIN
  LOCAL zr;
  zr := {{1,2,3},{4,5,6}};
  RETURN zr(2)(3);
END;
"""),
    ("the calculator's own list, indexed twice", 'index-call', None, None, """
EXPORT ZF()
BEGIN
  RETURN L1(2)(1);
END;
"""),
    ('a name the file does not define, indexed twice', 'index-call', 'WARN',
     'emulator', """
EXPORT ZF()
BEGIN
  RETURN ZSTRANGE(1)(2);
END;
"""),
    ('index 0 into a list', 'one-based', 'WARN', 'emulator', """
EXPORT ZF()
BEGIN
  LOCAL zl;
  zl := {1,2,3};
  RETURN zl(0);
END;
"""),
    ("0 passed to the file's own function", 'one-based', None, None, """
ZHELP(flag, n)
BEGIN
  RETURN n;
END;
EXPORT ZF()
BEGIN
  RETURN ZHELP(0, 5);
END;
"""),
    ('13 locals in one LOCAL', 'local-limit', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h, i, j, k, l, m;
  RETURN 1;
END;
"""),
    ('9 locals in one LOCAL', 'local-limit', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h, j;
  RETURN 1;
END;
"""),
    ('10 locals in one LOCAL', 'local-limit', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h, i, j;
  RETURN 1;
END;
"""),
    ('8 locals in one LOCAL, which compile', 'local-limit', None, None, """
EXPORT ZF()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h;
  RETURN 1;
END;
"""),
    ('9 initialised variables in one EXPORT', 'export-limit', 'ERROR', 'G2',
     """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8, ZV9:=9;
"""),
    ('9 variables with no values in one EXPORT', 'export-limit', 'ERROR', 'G2',
     """
EXPORT ZV1, ZV2, ZV3, ZV4, ZV5, ZV6, ZV7, ZV8, ZV9;
"""),
    ('9 in one EXPORT, some with values, which nobody has tried', 'export-limit',
     'WARN', 'unverified', """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8, ZV9;
"""),
    ('8 initialised variables in one EXPORT, which compile',
     'export-limit', None, None, """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7, ZV8:=8;
"""),
    ('7 initialised variables in one EXPORT, which compile',
     'export-limit', None, None, """
EXPORT ZV1:=1, ZV2:=2, ZV3:=3, ZV4:=4, ZV5:=5, ZV6:=6, ZV7:=7;
"""),
    ('Z exported, which does not compile', 'export-home-variable', 'ERROR',
     'G2', """
EXPORT Z := 4781;
"""),
    ('Y exported, which does not compile', 'export-home-variable', 'ERROR', 'G2',
     """
EXPORT Y := 5060;
"""),
    ('A exported, which does not compile', 'export-home-variable', 'ERROR', 'G2',
     """
EXPORT A := 5070;
"""),
    ('Z exported with no value, which does not compile', 'export-home-variable',
     'ERROR', 'G2', """
EXPORT Z;
"""),
    ('B exported, which nobody has tried', 'export-home-variable', 'WARN',
     'unverified', """
EXPORT B := 1;
"""),
    ('a prefixed name exported, the pair of Z', 'export-home-variable', None,
     None, """
EXPORT ZV := 4781;
"""),
    ('a lower-case name exported, which is not the calculator\'s variable',
     'export-home-variable', None, None, """
EXPORT z := 1;
"""),
    ('a function called like a variable, with an argument, which compiles',
     'export-home-variable', None, None, """
EXPORT F(za)
BEGIN
  RETURN za;
END;
"""),
    ('F with no arguments, which on Home answers the variable',
     'export-home-variable', 'WARN', 'G2', """
EXPORT F()
BEGIN
  RETURN 5010;
END;
"""),
    ('another letter with no arguments, which nobody has tried',
     'export-home-variable', 'WARN', 'unverified', """
EXPORT B()
BEGIN
  RETURN 5010;
END;
"""),
    ('a list of initial values with a Home variable inside it',
     'export-home-variable', None, None, """
EXPORT ZV := {A, B};
"""),
    ('a nested LOCAL read after its block', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL za;
  za := 4734;
  IF za == 4734 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN za + zb;
END;
"""),
    ('a nested LOCAL read inside its block', 'local-scope', None, None, """
EXPORT ZF()
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
"""),
    ('a LOCAL of a FOR read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO 2 DO
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5100;
END;
"""),
    ('a LOCAL of a FOR read inside it', 'local-scope', None, None, """
EXPORT ZF()
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
"""),
    ('a LOCAL of a WHILE read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
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
"""),
    ('a LOCAL of a REPEAT read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  REPEAT
    LOCAL zb;
    zb := 3;
  UNTIL 1;
  RETURN zb + 5120;
END;
"""),
    ('a LOCAL of a REPEAT read inside it', 'local-scope', None, None, """
EXPORT ZF()
BEGIN
  LOCAL zs;
  REPEAT
    LOCAL zb;
    zb := 3;
    zs := zb;
  UNTIL 1;
  RETURN zs + 5240;
END;
"""),
    ('a LOCAL of a CASE read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  CASE
    IF 1 == 1 THEN
      LOCAL zb;
      zb := 3;
    END;
  END;
  RETURN zb + 5130;
END;
"""),
    ('a LOCAL of an ELSE read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  IF 0 == 1 THEN
    1;
  ELSE
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5140;
END;
"""),
    ('a LOCAL of a THEN read in its ELSE', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  IF 0 == 1 THEN
    LOCAL zb;
    zb := 3;
  ELSE
    RETURN zb + 5150;
  END;
  RETURN 5151;
END;
"""),
    ('a LOCAL of an IFERR read after it', 'local-scope', 'ERROR', 'G2', """
EXPORT ZF()
BEGIN
  IFERR
    LOCAL zb;
    zb := 3;
  THEN
    1;
  END;
  RETURN zb + 5160;
END;
"""),
    ('a LOCAL of a REPEAT read in its own UNTIL', 'local-scope', 'ERROR', 'G2',
     """
EXPORT ZF()
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
"""),
    ('a LOCAL of what an IFERR tries, read in its THEN', 'local-scope', 'ERROR',
     'G2', """
EXPORT ZF()
BEGIN
  IFERR
    LOCAL zb;
    zb := 3;
  THEN
    RETURN zb + 5400;
  END;
  RETURN 5401;
END;
"""),
    ('a nested LOCAL that repeats an outer one, read after', 'local-scope', None,
     None, """
EXPORT ZF()
BEGIN
  LOCAL zb;
  zb := 1;
  IF zb == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb + 5200;
END;
"""),
    ('a nested LOCAL only assigned after its block', 'local-scope', 'ERROR',
     'G2', """
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  zb := 4;
  RETURN 1;
END;
"""),
    ('a nested LOCAL declared again after its block', 'local-scope', None,
     None, """
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  LOCAL zb;
  zb := 4;
  RETURN zb;
END;
"""),
    ('two blocks each with a LOCAL of that name', 'local-scope', None, None, """
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  IF 2 == 2 THEN
    LOCAL zb;
    zb := 4;
  END;
  RETURN 1;
END;
"""),
    ('a parameter of that name, after the block', 'local-scope', None, None, """
EXPORT F(zb)
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb;
END;
"""),
    ('a global of that name, after the block', 'local-scope', None, None, """
EXPORT zb := 2;
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  RETURN zb;
END;
"""),
    ('that name only in a string or a comment, after the block', 'local-scope',
     None, None, """
EXPORT ZF()
BEGIN
  IF 1 == 1 THEN
    LOCAL zb;
    zb := 3;
  END;
  // zb is gone by here
  /* and zb is gone here too */
  RETURN "zb";
END;
"""),
    ("a block's END without ;", 'end-semicolon', 'ERROR', 'emulator', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    a := 1;
  END
  RETURN a;
END;
"""),
    ("a function's END without ;", 'end-semicolon', 'ERROR', 'emulator', """
EXPORT F(a)
BEGIN
  RETURN a;
END
"""),
    ('ENDIF', 'single-end', 'ERROR', 'G2', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN a := 1; ENDIF;
  RETURN a;
END;
"""),
    ('ENDCASE', 'single-end', 'ERROR', 'emulator', """
EXPORT F(a)
BEGIN
  CASE IF a > 0 THEN a := 1; END; ENDCASE;
  RETURN a;
END;
"""),
    ('ENDPROC', 'single-end', 'ERROR', 'emulator', """
EXPORT F(a)
BEGIN
  RETURN a;
ENDPROC;
"""),
    ('a single = as a statement', 'equality-statement', 'WARN', 'emulator',
     """
EXPORT ZF()
BEGIN
  LOCAL za;
  za := 1;
  za = 2;
  RETURN za;
END;
"""),
    ('a single = in a condition, which compares', 'equality-statement', None,
     None, """
EXPORT F(a)
BEGIN
  IF a = 2 THEN RETURN 5; END;
  RETURN a == 3;
END;
"""),
    ('6 locals in one LOCAL', 'local-limit', None, None, """
EXPORT ZF()
BEGIN
  LOCAL za, zb, zc, zd, zf, zg;
  RETURN 1;
END;
"""),
    ("a block's END and a function's, each with its ;", 'end-semicolon', None,
     None, """
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    a := 1;
  END;
  RETURN a;
END;
"""),
    ('END closing an IF and a FOR', 'single-end', None, None, """
EXPORT F(a)
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO 3 DO
    IF a > zi THEN a := zi; END;
  END;
  RETURN a;
END;
"""),
    ('EXPR behind a size guard', 'expr-empty', None, None, """
EXPORT F(zs)
BEGIN
  IF SIZE(zs) > 0 THEN
    RETURN EXPR(zs);
  END;
  RETURN 0;
END;
"""),
    ('TEXTOUT_P with its width argument', 'textout-width', None, None, """
EXPORT ZF()
BEGIN
  TEXTOUT_P("a label", G0, 4, 24, 2, RGB(0,0,0), 70);
  RETURN 1;
END;
"""),
]

EVIDENCE += [
    ('the null-hypothesis mean with the Greek mu', 'mu-zero', 'ERROR',
     'emulator', """
EXPORT ZF()
BEGIN
  RETURN Inference.\u03bc\u2080;
END;
"""),
    ('the same with the micro sign, and the Greek one in a message', 'mu-zero',
     None, None, """
EXPORT ZF()
BEGIN
  MSGBOX("\u03bc\u2080");
  RETURN Inference.\u00b5\u2080;
END;
"""),
    ("a key's code compared with 65", 'getkey-code', 'WARN', 'G2', """
EXPORT ZF()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;
  REPEAT zk := GETKEY; UNTIL zk >= 0;
  IF zk == 65 THEN RETURN 1; END;
  RETURN 0;
END;
"""),
    ("a key's code compared with codes a key has", 'getkey-code', None, None,
     """
EXPORT ZF()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;
  REPEAT zk := GETKEY; UNTIL zk >= 0;
  IF zk == 30 THEN RETURN 1; END;
  IF zk <> 4 AND zk <> -1 THEN RETURN 2; END;
  RETURN 0;
END;
"""),
    ("a string's element compared with a string", 'string-index', 'WARN',
     'emulator', """
EXPORT ZF()
BEGIN
  LOCAL zs;
  zs := "abc";
  IF zs(2) == "b" THEN RETURN 1; END;
  RETURN 0;
END;
"""),
    ("a list of strings' element compared with a string", 'string-index', None,
     None, """
EXPORT ZF()
BEGIN
  LOCAL zl;
  zl := {"a", "b"};
  IF zl(2) == "b" THEN RETURN 1; END;
  RETURN 0;
END;
"""),
    ('LINE and DIMGROB given pixels', 'draw-units', 'WARN', 'emulator', """
EXPORT ZF()
BEGIN
  DIMGROB(G1, 320, 240);
  LINE(0, 0, 320, 240);
  RETURN 1;
END;
"""),
    ('the _P forms given pixels, and LINE given units', 'draw-units', None,
     None, """
EXPORT ZF()
BEGIN
  DIMGROB_P(G1, 320, 240);
  LINE_P(0, 0, 319, 239);
  LINE(-5, -5, 5, 5);
  RETURN 1;
END;
"""),
    ('a program that draws and returns', 'draw-then-return', 'WARN', 'G2',
     """
EXPORT SHOW()
BEGIN
  TEXTOUT_P("done", G0, 10, 10, 2, RGB(0,0,0), 100);
  RETURN 1;
END;
"""),
    ('a program that draws and waits, through a function of its own',
     'draw-then-return', None, None, """
ZPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;
  REPEAT zk := GETKEY; UNTIL zk >= 0;
  RETURN zk;
END;

EXPORT SHOW()
BEGIN
  TEXTOUT_P("done", G0, 10, 10, 2, RGB(0,0,0), 100);
  ZPAUSE();
  RETURN 1;
END;
"""),
    ('a loop that waits for a key, nothing drained', 'wait-undrained', 'WARN',
     'G2', """
EXPORT ZF()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk >= 0;
  RETURN zk;
END;
"""),
    ('drained, then waited for', 'wait-undrained', None, None, """
EXPORT TPAUSE()
BEGIN
  LOCAL zk;
  REPEAT zk := GETKEY; UNTIL zk < 0;
  REPEAT zk := GETKEY; UNTIL zk >= 0;
  RETURN zk;
END;
"""),
    ("WAIT(-1)'s answer compared with a key, its TYPE unchecked",
     'wait-touch', 'WARN', 'emulator', """
EXPORT ZF()
BEGIN
  LOCAL ze;
  REPEAT
    ze := WAIT(-1);
  UNTIL ze == 4;
  RETURN 1;
END;
"""),
    ('a key told from a touch by its TYPE, and the click acted on',
     'wait-touch', None, None, """
EXPORT ZF()
BEGIN
  LOCAL ze;
  REPEAT
    ze := WAIT(-1);
    IF TYPE(ze) == 6 THEN
      IF B→R(ze(1)) == 3 THEN RETURN 2; END;
    END;
  UNTIL TYPE(ze) == 0 AND ze == 4;
  RETURN 1;
END;
"""),
    ('EXPR inside a FOR', 'expr-in-loop', 'WARN', 'G2', """
EXPORT F(zn)
BEGIN
  LOCAL zi, zs;
  zs := 0;
  FOR zi FROM 1 TO zn DO
    zs := zs + EXPR("ZDATA(" + zi + ")");
  END;
  RETURN zs;
END;
"""),
    ('EXPR once, before the loop', 'expr-in-loop', None, None, """
EXPORT F(zn)
BEGIN
  LOCAL zi, zs, zv;
  zs := 0;
  zv := EXPR("ZDATA");
  FOR zi FROM 1 TO zn DO
    zs := zs + zv(zi);
  END;
  RETURN zs;
END;
"""),
    ('a program exporting AREA', 'export-clash', 'WARN', 'emulator', """
EXPORT AREA(zr)
BEGIN
  RETURN 3.14159265359 * zr * zr;
END;
"""),
    ('an exported helper with arguments that draws for its caller',
     'draw-then-return', None, None, """
EXPORT ZBOX(zx, zy)
BEGIN
  RECT_P(zx, zy, zx + 10, zy + 10, RGB(0,0,0));
  RETURN 1;
END;
"""),
    ('a prefixed export, and an app hook', 'export-clash', None, None, """
EXPORT CIRCAREA(zr)
BEGIN
  RETURN 3.14159265359 * zr * zr;
END;

EXPORT View()
BEGIN
  RETURN 1;
END;
"""),
    ('box characters drawn by TEXTOUT_P in font 3', 'font-glyph', 'WARN',
     'emulator', """
EXPORT ZF()
BEGIN
  TEXTOUT_P("◄ back", 4, 24, 3, RGB(0,0,0), 100);
  TEXTOUT_P("next, ⯈", G0, 4, 48, 3, RGB(0,0,0), 100);
  RETURN 1;
END;
"""),
    ('the same kept in a constant, and drawn in font 2', 'font-glyph', 'WARN',
     'unverified', """
EXPORT ZF()
BEGIN
  LOCAL zs;
  zs := "◂";
  TEXTOUT_P("▸", 4, 24, 2, RGB(0,0,0), 100);
  RETURN zs;
END;
"""),
    ('the characters that were drawn, and a box one in comments',
     'font-glyph', None, None, """
EXPORT ZF()
BEGIN
  // ◄ is a box: write ◀
  /* "◄" */
  TEXTOUT_P("◀ ▶ ← → ► ⇐ ⇒ « » < >",
            4, 24, 3, RGB(0,0,0), 300);
  TEXTOUT_P("▲ ▼ ° ω", 4, 48, 2, RGB(0,0,0), 300);
  RETURN 1;
END;
"""),
]

# Rules that need several files in view: (what, rule, level, label, files).
MULTI = [
    ('two files exporting one name', 'export-clash', 'WARN', 'G2',
     [('A.txt', 'EXPORT ZSAME(zx)\nBEGIN\n  RETURN zx;\nEND;\n'),
      ('B.txt', 'EXPORT ZSAME(zx)\nBEGIN\n  RETURN 2 * zx;\nEND;\n')]),
    ('two files exporting a name each', 'export-clash', None, None,
     [('A.txt', 'EXPORT ZONE(zx)\nBEGIN\n  RETURN zx;\nEND;\n'),
      ('B.txt', 'EXPORT ZTWO(zx)\nBEGIN\n  RETURN 2 * zx;\nEND;\n')]),
]

# The facts with nothing to catch, where the mistake would be to flag them:
# each program here compiles and does what its fact says, so no rule may say
# anything about it, not even a warning. A list of files is linted together.
QUIET = {
    'ppl.return-in-loop': """
EXPORT F(n)
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO n DO
    IF zi > 3 THEN RETURN zi; END;
  END;
  REPEAT
    RETURN n;
  UNTIL 1;
END;
""",
    'ppl.letter-digit-names': """
EXPORT ZF()
BEGIN
  LOCAL L12, L13, r2, y1;
  L12 := 1;
  RETURN L12;
END;
""",
    'ppl.local-m-matrices': """
EXPORT ZF()
BEGIN
  LOCAL m;
  m := 2;
  RETURN m;
END;
""",
    'ppl.locals-initialised-one-line': """
EXPORT ZF()
BEGIN
  LOCAL za := 1, zb := 2, zc := 3;
  RETURN za + zb + zc;
END;
""",
    'ppl.locals-at-top': """
EXPORT ZF()
BEGIN
  LOCAL za;
  za := 0;
  LOCAL zb := 4733;
  RETURN za + zb;
END;
""",
    'ppl.call-no-parentheses': """
ZPG();

ZPF()
BEGIN
  RETURN 1;
END;

EXPORT ZF()
BEGIN
  ZPF;
  RETURN ZPF + ZPF() + ZPG + ZPG();
END;

ZPG()
BEGIN
  RETURN 2;
END;
""",
    'ppl.i-e-as-locals': """
EXPORT ZF()
BEGIN
  LOCAL i, e;
  i := 2;
  e := 1;
  RETURN i * 3 + e;
END;
""",
    'ppl.short-circuit': """
EXPORT ZF()
BEGIN
  LOCAL zl;
  zl := {};
  IF SIZE(zl) > 0 AND zl(1) == 3 THEN RETURN 1; END;
  RETURN IFTE(SIZE(zl) == 0, 0, zl(1));
END;
""",
    'ppl.names-ignore-case': """
EXPORT F(zx)
BEGIN
  RETURN sin(zx) + alog(2) + xpon(1000);
END;
""",
    'ppl.getkey-no-parentheses': """
EXPORT ZF()
BEGIN
  LOCAL zk, zj;
  zk := GETKEY;
  zj := GETKEY();
  RETURN zk + zj;
END;
""",
    'apps.qualified-names': """
EXPORT ZF()
BEGIN
  Statistics_1Var.D1 := {1,2,2,3,7};
  Statistics_1Var.Do1VStats(Statistics_1Var.H1);
  RETURN Statistics_1Var.MeanX + Spreadsheet.SUM({1,2,3});
END;
""",
    'ppl.global-index-other-program': [
        ('DATA.txt', 'EXPORT ZNAMES:={"a","b","c"};\n'),
        ('USE.txt', 'EXPORT ZF()\nBEGIN\n  RETURN ZNAMES(1);\nEND;\n')],
}


def quiet_findings(case):
    """Every finding on a QUIET case: one source, or files linted as a
    set."""
    if isinstance(case, list):
        return lint_files(case, True)
    return L.check_source('quiet.txt', case)[0]


def caught_list():
    """CAUGHT against the facts, the rules and the tests it names. -> the
    problems, and how many checks are decided and not written."""
    from hpkit import docs
    facts = set(f.ident for f in docs.load(ROOT)[1])
    problems, to_write = [], 0
    for ident in sorted(facts - set(L.CAUGHT)):
        problems.append('%s has no line' % ident)
    for ident in sorted(set(L.CAUGHT) - facts):
        problems.append('%s is not a fact' % ident)
    for ident, answers in L.CAUGHT.items():
        if not answers:
            problems.append('%s has no answer' % ident)
        for a in answers:
            kind = a[0]
            if kind == 'rule' and a[1] not in L.FACTS:
                problems.append('%s: %s is not a rule tied to a fact'
                                % (ident, a[1]))
            elif kind == 'command':
                path = os.path.join(ROOT, a[2])
                text = (io.open(path, encoding='utf-8').read()
                        if os.path.isfile(path) else '')
                if a[3] not in text:
                    problems.append('%s: %s has no test "%s"'
                                    % (ident, a[2], a[3]))
            elif kind == 'quiet' and ident not in QUIET:
                problems.append('%s: no QUIET case' % ident)
            elif kind == 'no' and not a[1].strip():
                problems.append('%s: no reason' % ident)
            elif kind == 'write':
                to_write += 1
                problems.append('%s: %s is decided on and not written'
                                % (ident, a[1]))
            elif kind not in ('rule', 'command', 'quiet', 'no', 'write'):
                problems.append('%s: unknown answer %r' % (ident, kind))
    for rule, fact in sorted(L.FACTS.items()):
        if ('rule', rule) not in L.CAUGHT.get(fact, []):
            problems.append('%s is tied to %s, whose line does not name it'
                            % (rule, fact))
    for ident in sorted(QUIET):
        if ('quiet',) not in L.CAUGHT.get(ident, []):
            problems.append('QUIET has %s, whose line is not quiet' % ident)
    return problems, to_write


def rules_have_both_cases():
    """Every rule tied to a fact has a case it catches and one it must
    stay quiet on. -> the rules missing one."""
    catches, quiet = set(r for r, _ in BAD), set()
    for case in EVIDENCE + MULTI:
        (catches if case[2] else quiet).add(case[1])
    return ['%s has no case it %s' % (r, what)
            for r in sorted(L.FACTS)
            for what, seen in (('catches', catches), ('stays quiet on', quiet))
            if r not in seen]

# What a finding looks like: (source, rule, how its line ends).
SHAPES = [
    (EVIDENCE[0][4], 'index-call', '[ppl.index-call, G2]'),
    (EVIDENCE[5][4], 'one-based', '[ppl.one-based, emulator]'),
    ("""
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    a := 1;
  RETURN a;
END;
""", 'unbalanced', '[no fact]'),
]

# ------------------------------------------------------------ files together
LIBRARY = """
EXPORT ZLIB(zx)
BEGIN
  RETURN zx * 2;
END;
"""
CALLER = """
EXPORT ZF()
BEGIN
  RETURN ZLIB(21);
END;
"""
STRANGER = """
EXPORT F(zs)
BEGIN
  RETURN STRLEN(zs);
END;
"""


def lint_files(sources, as_set):
    """Lint (name, source) pairs as files. -> every Finding."""
    tmp = tempfile.mkdtemp(prefix='hplint-')
    try:
        paths = []
        for name, src in sources:
            path = os.path.join(tmp, name)
            with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(src)
            paths.append(path)
        return L.lint_files(paths, as_set=as_set)[1]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def levels(found, rule):
    return sorted(set(a.level for a in found if a.rule == rule))


SETS = [
    ('a stranger in a file on its own is a warning',
     lambda: levels(lint_files([('A.txt', STRANGER)], False),
                    'unknown-name') == ['WARN']),
    ('a stranger with --set is an error',
     lambda: levels(lint_files([('A.txt', STRANGER)], True),
                    'unknown-name') == ['ERROR']),
    ('a call to another file\'s export warns when the file is alone',
     lambda: levels(lint_files([('B.txt', CALLER)], False),
                    'unknown-name') == ['WARN']),
    ('and is quiet with --set, when that file is in view',
     lambda: levels(lint_files([('A.txt', LIBRARY), ('B.txt', CALLER)],
                               True), 'unknown-name') == []),
]


def kit_sources():
    """The PPL this repository ships for people to copy."""
    out = []
    for base in ('examples', 'templates'):
        for folder, _, files in os.walk(os.path.join(ROOT, base)):
            out += [os.path.join(folder, f) for f in sorted(files)
                    if f.endswith('.txt')]
    return out


def rules_cite_facts():
    """-> the problems with what each rule says it comes from.

    Every rule the linter can emit either names a fact that a topic page
    defines, or says in NO_FACT what it comes from instead. A rule that does
    neither is a message nobody can check.
    """
    import re
    from hpkit import docs as D
    src = io.open(os.path.join(ROOT, 'hpkit', 'lint.py'),
                  encoding='utf-8').read()
    rules = set(re.findall(r"'(?:ERROR|WARN)',\s*'([a-z-]+)'", src))
    facts = set(f.ident for f in D.load(ROOT)[1])
    problems = []
    for rule in sorted(rules):
        if rule in L.FACTS and rule in L.NO_FACT:
            problems.append('%s is in both FACTS and NO_FACT' % rule)
        elif rule in L.FACTS:
            if L.FACTS[rule] not in facts:
                problems.append('%s names %s, which no topic page defines'
                                % (rule, L.FACTS[rule]))
        elif rule in L.NO_FACT:
            if not L.NO_FACT[rule].strip():
                problems.append('%s gives no reason for having no fact' % rule)
        else:
            problems.append('%s names no fact and gives no reason' % rule)
    for rule in sorted(set(L.FACTS) | set(L.NO_FACT)):
        if rule not in rules:
            problems.append('%s is mapped, and the linter never emits it'
                            % rule)
    return problems


def finding_problem(a):
    """-> what is wrong with how finding `a` says it is known, or ''.

    Its label is one of docs/format.md's four, or none for a rule with no
    fact; and an ERROR is only what a calculator was seen to refuse, so a
    rule with a fact raises one only with a G2 or emulator label."""
    from hpkit import docs as D
    if a.rule in L.NO_FACT:
        return '%s has no fact and says %s' % (a.rule, a.label) if a.label \
            else ''
    if a.label not in D.LABELS:
        return '%s says it is known from %r' % (a.rule, a.label)
    if a.level == 'ERROR' and a.label not in L.MEASURED:
        return '%s raises an ERROR known only from %s' % (a.rule, a.label)
    return ''


def errors_have_evidence():
    """-> the problems with how findings are known, checked two ways: every
    rule that can raise an ERROR has a measured fact, and every finding on
    every case in this file passes finding_problem."""
    import re
    src = io.open(os.path.join(ROOT, 'hpkit', 'lint.py'),
                  encoding='utf-8').read()
    problems = []
    for rule in sorted(set(re.findall(r"'ERROR',\s*'([a-z-]+)'", src))):
        label = L.fact_label(L.FACTS[rule]) if rule in L.FACTS else None
        if label is not None and label not in L.MEASURED:
            problems.append('%s can raise an ERROR, and %s is known from %s'
                            % (rule, L.FACTS[rule], label or 'nothing'))
    sources = ([s for _, s in BAD + GOOD + KNOWN_NAMES]
               + [e[4] for e in EVIDENCE] + [s[0] for s in SHAPES])
    found = []
    for s in sources:
        found += L.check_source('case.txt', s)[0]
    found += lint_files([('A.txt', LIBRARY), ('B.txt', LIBRARY),
                         ('C.txt', STRANGER)], True)
    problems += [finding_problem(a) for a in found if finding_problem(a)]
    return sorted(set(problems))


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

    print('')
    for name, src in KNOWN_NAMES:
        found, _ = L.check_source('names.hpprgm', src)
        strangers = [a for a in found if a.rule == 'unknown-name']
        if not strangers:
            ok += 1
            print('  ok    no unknown-name on %s' % name)
        else:
            bad += 1
            print('  FAIL  unknown-name on %s: %s'
                  % (name, '; '.join(a.msg.split(' ')[0] for a in strangers)))

    print('')
    for what, rule, level, label, src in EVIDENCE:
        found, _ = L.check_source('evidence.txt', src)
        got = sorted(set((a.level, a.label) for a in found if a.rule == rule))
        want = [(level, label)] if level else []
        said = ', '.join('%s %s' % g for g in got) or 'nothing'
        if got == want:
            ok += 1
            print('  ok    %s on %s: %s' % (rule, what, said))
        else:
            bad += 1
            print('  FAIL  %s on %s: %s, and should be %s'
                  % (rule, what, said,
                     '%s %s' % (level, label) if level else 'nothing'))

    print('')
    for src, rule, tail in SHAPES:
        shown = [str(a) for a in L.check_source('shape.txt', src)[0]
                 if a.rule == rule]
        if shown and all(s.endswith(tail) for s in shown):
            ok += 1
            print('  ok    %s ends in %s' % (rule, tail))
        else:
            bad += 1
            print('  FAIL  %s should end in %s: %s'
                  % (rule, tail, '; '.join(shown) or 'nothing'))

    print('')
    problems = errors_have_evidence()
    if problems:
        bad += 1
        print('  FAIL  findings against their evidence: %s'
              % '; '.join(problems))
    else:
        ok += 1
        print('  ok    every ERROR is known from a G2 or the emulator, and '
              'every label is one of four')
    wrong = L.Finding('x.txt', 1, 'ERROR', 'one-based', '', L.UNVERIFIED)
    if finding_problem(wrong):
        ok += 1
        print('  ok    and the check refuses an ERROR labelled unverified')
    else:
        bad += 1
        print('  FAIL  the check lets an ERROR labelled unverified through')

    print('')
    for name, test in SETS:
        if test():
            ok += 1
            print('  ok    %s' % name)
        else:
            bad += 1
            print('  FAIL  %s' % name)

    print('')
    flagged = []
    for path in kit_sources():
        text = io.open(path, encoding='utf-8').read()
        flagged += ['%s:%d %s' % (os.path.relpath(path, ROOT), a.line,
                                  a.msg.split(' ')[0])
                    for a in L.check_source(path, text)[0]
                    if a.rule == 'unknown-name']
    if flagged:
        bad += 1
        print('  FAIL  unknown-name in the PPL this repository ships: %s'
              % '; '.join(flagged))
    else:
        ok += 1
        print('  ok    no unknown-name in the PPL this repository ships')

    print('')
    for what, rule, level, label, files in MULTI:
        found = lint_files(files, True)
        got = sorted(set((a.level, a.label) for a in found if a.rule == rule))
        want = [(level, label)] if level else []
        if got == want:
            ok += 1
            print('  ok    %s on %s' % (rule, what))
        else:
            bad += 1
            print('  FAIL  %s on %s: %s, and should be %s'
                  % (rule, what, got or 'nothing', want or 'nothing'))

    print('')
    for ident in sorted(QUIET):
        found = quiet_findings(QUIET[ident])
        if not found:
            ok += 1
            print('  ok    nothing flagged on %s' % ident)
        else:
            bad += 1
            print('  FAIL  %s is flagged: %s'
                  % (ident, '; '.join('%s %s' % (a.rule, a.level)
                                      for a in found)))

    print('')
    problems, to_write = caught_list()
    if problems:
        bad += 1
        print('  FAIL  the list of what catches each fact: %s'
              % '; '.join(problems))
    else:
        ok += 1
        print('  ok    every fact has a line, and every line holds')
    missing = rules_have_both_cases()
    if missing:
        bad += 1
        print('  FAIL  %s' % '; '.join(missing))
    else:
        ok += 1
        print('  ok    every rule tied to a fact has a case it catches and '
              'one it stays quiet on')

    print('')
    problems = rules_cite_facts()
    if problems:
        bad += 1
        print('  FAIL  rules against facts: %s' % '; '.join(problems))
    else:
        ok += 1
        print('  ok    every rule names its fact, or says what it comes from')

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
