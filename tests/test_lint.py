# -*- coding: utf-8 -*-
"""Pruebas del linter: que caza lo que tiene que cazar y calla con lo bueno.

Los casos malos son los errores reales que costaron rondas de compilacion en
la calculadora. Los controles son codigo que SI compila en una G2 y que en su
momento se sospecho por error: si el linter los marca, esta de mas.

    python tests/test_lint.py
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import lint_ppl as L

# ---------------------------------------------------------------- casos malos
MALOS = [
    ('local-limite', """
EXPORT F(a)
BEGIN
  LOCAL zm, zn, zi, zj, zk, zp, zq, zr, zs, zt, zu, zv, zw;
  RETURN a;
END;
"""),
    ('indexar-llamada', """
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
    ('end-unico', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN a := 1; ENDIF;
  RETURN a;
END;
"""),
    ('igualdad', """
EXPORT F(a)
BEGIN
  IF a = 1 THEN RETURN 2; END;
  RETURN 0;
END;
"""),
    ('base-1', """
EXPORT F(M)
BEGIN
  RETURN M(0,1);
END;
"""),
    ('local-al-principio', """
EXPORT F(a)
BEGIN
  LOCAL x;
  x := a + 1;
  LOCAL y;
  RETURN x;
END;
"""),
    ('bloques', """
EXPORT F(a)
BEGIN
  IF a > 0 THEN
    a := 1;
  RETURN a;
END;
"""),
    ('expr-vacia', """
EXPORT F()
BEGIN
  LOCAL zs;
  zs := "";
  RETURN EXPR(zs);
END;
"""),
]

# ------------------------------------------------------- controles (bien)
# Codigo que compila en una G2 real. Ninguna regla debe dispararse.
BUENOS = [
    ('RETURN dentro de un FOR', """
EXPORT F(n)
BEGIN
  LOCAL zi;
  FOR zi FROM 1 TO n DO
    IF zi > 3 THEN RETURN zi; END;
  END;
  RETURN 0;
END;
"""),
    ('locales letra+digito', """
EXPORT F()
BEGIN
  LOCAL L12, L13, L14, r2, y1;
  L12 := 1;
  RETURN L12;
END;
"""),
    ('varios locales con valor inicial', """
EXPORT F()
BEGIN
  LOCAL x1:=160, x2:=299, x3:=21;
  RETURN x1;
END;
"""),
    ('builtin con argumento 0', """
EXPORT F()
BEGIN
  TEXTOUT_P("hola", 4, 24, 3, RGB(0,0,180));
  RETURN 1;
END;
"""),
    ('lista exportada con comas', """
EXPORT TPROP:={"P [MPa]","T [C]","T [K]","x","v","u","h","s"};
"""),
    ('EXPR con guarda previa', """
EXPORT F(zs)
BEGIN
  IF SIZE(zs) > 0 THEN
    RETURN EXPR(zs);
  END;
  RETURN 0;
END;
"""),
    ('8 locales, el maximo visto compilar', """
EXPORT F()
BEGIN
  LOCAL a, b, c, d, e2, f, g, h;
  RETURN 1;
END;
"""),
]


def main():
    ok = fallos = 0

    for regla, src in MALOS:
        av, _ = L.revisa('caso.hpprgm', src)
        reglas = set(a.regla for a in av)
        if regla in reglas:
            ok += 1
            print('  ok    caza %-20s' % regla)
        else:
            fallos += 1
            print('  FALLO no caza %-20s (dio: %s)'
                  % (regla, ', '.join(sorted(reglas)) or 'nada'))

    print('')
    for nombre, src in BUENOS:
        av, _ = L.revisa('bueno.hpprgm', src)
        errores = [a for a in av if a.nivel == 'ERROR']
        if not errores:
            ok += 1
            print('  ok    calla con %s' % nombre)
        else:
            fallos += 1
            print('  FALLO falsa alarma en %s: %s'
                  % (nombre, '; '.join(a.regla for a in errores)))

    print('\nPASS: %d   FAIL: %d' % (ok, fallos))
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
