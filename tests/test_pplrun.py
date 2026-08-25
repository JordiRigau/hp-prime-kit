# -*- coding: utf-8 -*-
"""Pruebas del interprete de PPL, sin depender de ningun proyecto.

Cada caso es un programa PPL con un resultado conocido. Los de la seccion
ERRORES comprueban lo contrario: que **falla** donde la calculadora fallaria,
en vez de devolver un numero inventado.

    python tests/test_pplrun.py
"""
from __future__ import unicode_literals
import os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import pplrun as P

# (nombre, fuente, llamada, esperado)
CASOS = [
    ('aritmetica y precedencia', """
EXPORT F() BEGIN RETURN 2 + 3 * 4 - 6 / 3; END;
""", 'F()', 12.0),

    ('potencia asociativa por la derecha', """
EXPORT F() BEGIN RETURN 2 ^ 3 ^ 2; END;
""", 'F()', 512.0),

    ('unario y parentesis', """
EXPORT F() BEGIN RETURN -(2 + 3) * 2; END;
""", 'F()', -10.0),

    ('lista 1-based', """
EXPORT F() BEGIN LOCAL L; L := {10, 20, 30}; RETURN L(1) + L(3); END;
""", 'F()', 40.0),

    ('matriz 1-based, fila y columna', """
EXPORT F() BEGIN LOCAL M; M := [[1,2,3],[4,5,6]]; RETURN M(2,1) * 10 + M(1,3); END;
""", 'F()', 43.0),

    ('DIM de matriz', """
EXPORT F() BEGIN LOCAL M, d; M := [[1,2,3],[4,5,6]]; d := DIM(M); RETURN d(1)*100 + d(2); END;
""", 'F()', 203.0),

    ('SIZE de lista y de cadena', """
EXPORT F() BEGIN RETURN SIZE({1,2,3,4}) * 10 + SIZE("abc"); END;
""", 'F()', 43.0),

    ('asignar a un elemento', """
EXPORT F() BEGIN LOCAL L; L := {1,2,3}; L(2) := 99; RETURN L(2); END;
""", 'F()', 99.0),

    ('anadir al final, idiom de PPL', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; L(SIZE(L)+1) := 7; RETURN SIZE(L)*100 + L(3); END;
""", 'F()', 307.0),

    ('asignar en una matriz', """
EXPORT F() BEGIN LOCAL M; M := [[1,2],[3,4]]; M(2,2) := 9; RETURN M(2,2); END;
""", 'F()', 9.0),

    ('IF / ELSE', """
EXPORT F(a) BEGIN IF a > 5 THEN RETURN 1; ELSE RETURN 2; END; END;
""", 'F(3)', 2.0),

    ('CASE con DEFAULT', """
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

    ('CASE, rama que toca', """
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

    ('FOR suma', """
EXPORT F(n) BEGIN LOCAL i, s; s := 0; FOR i FROM 1 TO n DO s := s + i; END; RETURN s; END;
""", 'F(10)', 55.0),

    ('FOR DOWNTO', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 5 DOWNTO 1 DO s := s * 10 + i; END; RETURN s; END;
""", 'F()', 54321.0),

    ('FOR con STEP', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 0 TO 10 STEP 2 DO s := s + 1; END; RETURN s; END;
""", 'F()', 6.0),

    ('RETURN dentro de un FOR (es legal)', """
EXPORT F() BEGIN LOCAL i; FOR i FROM 1 TO 100 DO IF i > 4 THEN RETURN i; END; END; RETURN 0; END;
""", 'F()', 5.0),

    ('BREAK', """
EXPORT F() BEGIN LOCAL i, s; s := 0; FOR i FROM 1 TO 100 DO IF i > 3 THEN BREAK; END; s := s + i; END; RETURN s; END;
""", 'F()', 6.0),

    ('WHILE', """
EXPORT F() BEGIN LOCAL i; i := 1; WHILE i < 100 DO i := i * 2; END; RETURN i; END;
""", 'F()', 128.0),

    ('REPEAT UNTIL se ejecuta al menos una vez', """
EXPORT F() BEGIN LOCAL i; i := 50; REPEAT i := i + 1; UNTIL i > 0; RETURN i; END;
""", 'F()', 51.0),

    ('busqueda binaria, patron del motor', """
EXPORT BUSCA(M, c, x, r0, n)
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
EXPORT F() BEGIN LOCAL M; M := [[10,1],[20,2],[30,3],[40,4]]; RETURN BUSCA(M,1,25,1,4); END;
""", 'F()', 2.0),

    ('globales que persisten entre llamadas', """
EXPORT G := 5;
EXPORT SUBE() BEGIN G := G + 1; RETURN G; END;
EXPORT F() BEGIN SUBE(); SUBE(); RETURN G; END;
""", 'F()', 7.0),

    ('las matrices se pasan POR VALOR', """
EXPORT TOCA(M) BEGIN M(1,1) := 999; RETURN 0; END;
EXPORT F() BEGIN LOCAL M; M := [[1,2],[3,4]]; TOCA(M); RETURN M(1,1); END;
""", 'F()', 1.0),

    ('concatenar cadenas', """
EXPORT F() BEGIN RETURN "a" + "b" + STRING(3); END;
""", 'F()', 'ab3'),

    ('EXPR evalua una cadena', """
EXPORT DATO := [[7,8]];
EXPORT F() BEGIN LOCAL M; M := EXPR("DATO"); RETURN M(1,2); END;
""", 'F()', 8.0),

    ('IFTE solo evalua la rama que toca', """
EXPORT F(a) BEGIN RETURN IFTE(a > 0, 10, 20); END;
""", 'F(1)', 10.0),

    ('AND / OR / NOT', """
EXPORT F() BEGIN IF (1 > 0) AND NOT (2 > 3) OR (0 == 1) THEN RETURN 1; ELSE RETURN 0; END; END;
""", 'F()', 1.0),

    ('<> es distinto', """
EXPORT F() BEGIN IF 2 <> 3 THEN RETURN 1; ELSE RETURN 0; END; END;
""", 'F()', 1.0),

    ('MIN MAX ABS IP FLOOR ROUND', """
EXPORT F() BEGIN RETURN MIN(3,5) + MAX(3,5) + ABS(-2) + IP(2.9) + FLOOR(2.9) + ROUND(2.346,2)*100; END;
""", 'F()', 3 + 5 + 2 + 2 + 2 + 235.0),

    ('IFERR atrapa el error', """
EXPORT F()
BEGIN
  LOCAL L, r;
  L := {1,2};
  r := 0;
  IFERR r := L(9); THEN r := -1; END;
  RETURN r;
END;
""", 'F()', -1.0),

    ('devolver una lista', """
EXPORT F() BEGIN RETURN {1, 2, 3}; END;
""", 'F()', [1.0, 2.0, 3.0]),

    ('lista vacia como convenio de error', """
EXPORT G(a) BEGIN IF a < 0 THEN RETURN {}; END; RETURN {a}; END;
EXPORT F() BEGIN RETURN SIZE(G(-1)); END;
""", 'F()', 0.0),

    ('palabras clave en minuscula', """
export F() begin local x; x := 1; if x == 1 then return 42; end; return 0; end;
""", 'F()', 42.0),
]

# Casos donde tiene que FALLAR, no inventarse un numero
ERRORES = [
    ('indice 0', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; RETURN L(0); END;
""", 'F()'),
    ('indice fuera de rango', """
EXPORT F() BEGIN LOCAL L; L := {1,2}; RETURN L(5); END;
""", 'F()'),
    ('variable no definida', """
EXPORT F() BEGIN RETURN NOEXISTE + 1; END;
""", 'F()'),
    ('division por cero', """
EXPORT F() BEGIN RETURN 1 / 0; END;
""", 'F()'),
    ('funcion inexistente', """
EXPORT F() BEGIN RETURN CHISPUM(1); END;
""", 'F()'),
    ('EXPR de cadena vacia', """
EXPORT F() BEGIN RETURN EXPR(""); END;
""", 'F()'),
]


def evalua(fuente, llamada):
    m = P.Maquina()
    m.carga(fuente)
    return m.evalua(P.Parser(P.lex(llamada), '<test>').expr(), {})


def igual(a, b):
    if isinstance(b, list):
        return (isinstance(a, list) and len(a) == len(b)
                and all(igual(x, y) for x, y in zip(a, b)))
    if isinstance(b, str):
        return a == b
    return isinstance(a, float) and abs(a - b) < 1e-9


def main():
    ok = fallos = 0
    for nombre, fuente, llamada, esperado in CASOS:
        try:
            got = evalua(fuente, llamada)
        except Exception as e:
            fallos += 1
            print('  FALLO %-44s excepcion: %s' % (nombre, e))
            continue
        if igual(got, esperado):
            ok += 1
            print('  ok    %s' % nombre)
        else:
            fallos += 1
            print('  FALLO %-44s da %r y se esperaba %r'
                  % (nombre, got, esperado))

    print('')
    for nombre, fuente, llamada in ERRORES:
        try:
            got = evalua(fuente, llamada)
        except (P.ErrorPPL, P.NoSoportado):
            ok += 1
            print('  ok    falla como debe: %s' % nombre)
        except Exception as e:
            fallos += 1
            print('  FALLO %-44s excepcion rara: %r' % (nombre, e))
        else:
            fallos += 1
            print('  FALLO %-44s deberia fallar y da %r' % (nombre, got))

    print('\nPASS: %d   FAIL: %d' % (ok, fallos))
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
