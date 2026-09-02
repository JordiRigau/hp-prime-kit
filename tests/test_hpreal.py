# -*- coding: utf-8 -*-
"""Pruebas del formato de numero interno de la Prime.

La prueba de verdad no es un round-trip: leer y escribir con el MISMO error da
un round-trip perfecto y un resultado equivocado. Lo que lo verifica es la
piedra de Rosetta -un programa de datos lleva el bloque compilado delante del
fuente, y el fuente son los mismos numeros en decimal-, asi que se comparan
decenas de miles de parejas (bytes, valor) que nadie ha elegido.

Se salta lo que no encuentre, asi que en una maquina sin calculadora no falla.

    python tests/test_hpreal.py
"""
from __future__ import unicode_literals
import glob, io, os, re, struct, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
import hpreal as R
import hpprgm

PASS, FAIL = [0], [0]


def ok(cierto, msg, detalle=''):
    if cierto:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FALLO %s%s' % (msg, ('  ' + detalle) if detalle else ''))


# Valores sueltos, con su codificacion sacada a mano del bloque de TDAT.
CONOCIDOS = [
    (0.0,      '0000000000000000'),
    (-76.0,    '9760000000000001'),
    (0.0006,   '0600000000000FFC'),
    (205.991225, '0205991225000002'),
    (2374.92,  '0237492000000003'),
    (9.1555,   '0915550000000000'),
]

# Que tienen que dar error, no un numero inventado.
IMPOSIBLES = [float('inf'), float('nan')]


def calculadoras():
    for nombre in ('Documents', 'Documentos'):
        base = os.path.join(os.path.expanduser('~'), nombre,
                            'HP Connectivity Kit', 'Calculators')
        if os.path.isdir(base):
            return [os.path.join(base, d) for d in sorted(os.listdir(base))
                    if os.path.isdir(os.path.join(base, d))]
    return []


def prueba_conocidos():
    for valor, hexa in CONOCIDOS:
        crudo = struct.pack('<Q', int(hexa, 16))
        v = R.decodifica(crudo)
        ok(abs(v - valor) <= 1e-12 * max(1.0, abs(valor)),
           'decodifica %s -> %r' % (hexa, valor), 'dio %r' % v)
        ok(R.codifica(valor) == crudo,
           'codifica %r -> %s' % (valor, hexa),
           'dio %016X' % struct.unpack('<Q', R.codifica(valor))[0])

    for x in (1.0, -1.0, 1e-300, -1e300, 0.1, 1.0 / 3.0, 123456789012.0,
              -0.0007, 9.99999999999e99):
        ok(abs(R.decodifica(R.codifica(x)) - x) <= 1e-11 * max(1.0, abs(x)),
           'ida y vuelta de %r' % x)

    for x in IMPOSIBLES:
        try:
            R.codifica(x)
            ok(False, 'rechaza %r' % x)
        except R.FormatoInesperado:
            ok(True, 'rechaza %r' % x)

    try:
        R.decodifica(struct.pack('<Q', 0x0FFF000000000000))   # mantisa no BCD
        ok(False, 'rechaza una mantisa que no es BCD')
    except R.FormatoInesperado:
        ok(True, 'rechaza una mantisa que no es BCD')


def prueba_rosetta():
    """El bloque compilado contra el fuente del mismo fichero."""
    encontrados = 0
    for calc in calculadoras():
        for p in sorted(glob.glob(os.path.join(calc, '*.hpprgm'))):
            try:
                datos = open(p, 'rb').read()
                txt, _, ini, _ = hpprgm.leer(datos)
            except Exception:
                continue
            bloque = datos[hpprgm.CABECERA:ini]
            if len(bloque) < 1000:
                continue
            mats = list(re.finditer(
                r'EXPORT\s+(\w+)\s*:=\s*\[\[(.*?)\]\]\s*;', txt, re.S))
            if not mats:
                continue
            encontrados += 1
            total = comparados = rt = 0
            perdidas = []
            for m in mats:
                filas = [[float(x) for x in re.findall(
                    r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', f)]
                    for f in m.group(2).split('],[')]
                F, C = len(filas), len(filas[0])
                plano = [x for f in filas for x in f]
                total += len(plano)
                o, hallada = 0, False
                while True:
                    o = bloque.find(struct.pack('<III', 2, F, C), o)
                    if o < 0 or o + 12 + F * C * 8 > len(bloque):
                        break
                    base = o + 12
                    try:
                        vs = [R.decodifica(bloque[base + 8 * k:base + 8 * k + 8])
                              for k in range(F * C)]
                    except R.FormatoInesperado:
                        o += 4
                        continue
                    if all(abs(v - s) <= 1e-9 * max(1.0, abs(s))
                           for v, s in zip(vs, plano)):
                        hallada = True
                        comparados += len(plano)
                        rt += sum(1 for k, s in enumerate(plano)
                                  if R.codifica(s) ==
                                  bloque[base + 8 * k:base + 8 * k + 8])
                        break
                    o += 4
                if not hallada:
                    perdidas.append(m.group(1))
            nom = os.path.basename(p)
            ok(not perdidas, '%s: las %d matrices del fuente estan en el bloque'
               % (nom, len(mats)), 'no localizadas: %s' % perdidas[:3])
            ok(comparados == total,
               '%s: %d numeros decodificados y comparados' % (nom, comparados))
            ok(rt == comparados,
               '%s: %d de %d vuelven a codificar byte a byte'
               % (nom, rt, comparados))
            negs = sum(1 for m in mats for f in m.group(2).split('],[')
                       for x in re.findall(r'-\d+\.?\d*', f))
            ok(negs > 0, '%s: la comparacion incluye %d negativos'
               % (nom, negs), 'sin negativos no se verifica el signo')
    if not encontrados:
        print('  --    ningun programa con bloque compilado y matrices en el')
        print('        fuente: me salto la prueba de la piedra de Rosetta')


def prueba_hpmat():
    vistos = 0
    for calc in calculadoras():
        for p in sorted(glob.glob(os.path.join(calc, '*.hpmat'))):
            datos = open(p, 'rb').read()
            try:
                m = R.lee_hpmat(datos)
            except R.FormatoInesperado as e:
                if 'compleja' in str(e):
                    continue                      # no esta cubierto, y lo dice
                ok(False, '%s: %s' % (os.path.basename(p), e))
                continue
            vistos += 1
            rehecho = R.escribe_hpmat(m)
            ok(rehecho == datos[:len(rehecho)],
               '%s: %dx%d, round-trip identico'
               % (os.path.basename(p), len(m), len(m[0])),
               '%d bytes contra %d' % (len(rehecho), len(datos)))
    if not vistos:
        print('  --    sin ficheros .hpmat: me salto esa parte')

    # Uno inventado, que no depende de tener calculadora.
    m = [[1.0, -2.5, 0.0], [1e-9, 3.0, 123456.789]]
    d = R.escribe_hpmat(m)
    vuelta = R.lee_hpmat(d)
    ok(len(d) == 16 + 6 * 8, 'un .hpmat de 2x3 mide 16 + 6*8 bytes')
    ok(all(abs(a - b) <= 1e-11 * max(1.0, abs(b))
           for fa, fb in zip(vuelta, m) for a, b in zip(fa, fb)),
       'una matriz escrita desde cero se relee igual')
    try:
        R.escribe_hpmat([[1.0, 2.0], [3.0]])
        ok(False, 'rechaza filas de distinta longitud')
    except R.FormatoInesperado:
        ok(True, 'rechaza filas de distinta longitud')


def main():
    print('-- el numero, contra codificaciones conocidas')
    prueba_conocidos()
    print('\n-- la piedra de Rosetta: bloque compilado contra fuente')
    prueba_rosetta()
    print('\n-- ficheros .hpmat')
    prueba_hpmat()
    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
