# -*- coding: utf-8 -*-
"""El formato de numero interno de la HP Prime, y los ficheros que lo usan.

Es el formato que aparece en dos sitios y que hasta ahora era opaco:

  - el BLOQUE COMPILADO que la calculadora pone delante del fuente en los
    programas que declaran matrices (ver formato-hpprgm.md);
  - los ficheros .hpmat de las matrices M0..M9.

UN NUMERO SON 8 BYTES, little-endian. Leidos como un entero de 64 bits:

    bits  0..11   exponente decimal, complemento a dos de 12 bits
    bits 12..59   12 digitos BCD de mantisa, el mas significativo arriba
    bits 60..63   signo: 0 positivo, 9 negativo   (convenio BCD de siempre)

    valor = d1.d2d3...d12 x 10^exponente        y el cero es todo ceros

Ejemplo, del bloque de TDAT:

    9760000000000001  ->  signo 9, mantisa 760000000000, exp 1  ->  -76.0
    0600000000000FFC  ->  signo 0, mantisa 600000000000, exp -4 ->  0.0006

COMO SE DESCIFRO, Y COMO ESTA VERIFICADO

Con una piedra de Rosetta: un programa de datos lleva el bloque compilado
DELANTE del fuente, y el fuente son los mismos numeros escritos en decimal.
O sea que hay 44.718 parejas (bytes, valor) sin tener que adivinar nada.

    TDAT.hpprgm  ->  56 matrices, 44.718 numeros
    decodificados y comparados con el fuente:  44.718 de 44.718, exactos
    vueltos a codificar y comparados byte a byte: 44.718 de 44.718

Incluye 1.482 negativos, que es lo que fijo el nibble de signo (es 9, no 1).
La prueba esta en tests/test_hpreal.py y se rehace sobre TUS ficheros.

LO QUE ESTO ABRE, Y LO QUE NO

Abre leer y escribir .hpmat, que es una matriz entera como fichero: se
arrastra a la calculadora sin pegar nada y sin pasar por el fuente de un
programa.

NO abre todavia generar el bloque compilado de un programa. El bloque no es
solo numeros: entre matriz y matriz lleva registros con el nombre del simbolo
en UTF-16LE. Lo que se sabe de esa estructura esta en formato-hpprgm.md; la
parte dificil -el formato del numero- ya no es un obstaculo.

Uso:
    python hpreal.py read  M1.hpmat                 # a texto
    python hpreal.py write datos.csv -o M1.hpmat    # de CSV a matriz
    python hpreal.py nums  PROG.hpprgm              # las matrices del bloque
"""
from __future__ import unicode_literals
import io, os, struct, sys

# Cabecera de un .hpmat: 16 bytes.
#   00  01 00       ?  (constante en todos los observados)
#   02  14 80       tipo: 8014 real, 8094 complejo (16 bytes por elemento)
#   04  u32 = 2     rango: 2 = matriz
#   08  u32         filas
#   12  u32         columnas
HPMAT_REAL = 0x8014
HPMAT_COMPLEJO = 0x8094


class FormatoInesperado(Exception):
    pass


def decodifica(b):
    """8 bytes -> float. Da error si no son BCD validos."""
    if len(b) != 8:
        raise FormatoInesperado('un numero son 8 bytes, no %d' % len(b))
    w = struct.unpack('<Q', b)[0]
    exp = w & 0xFFF
    if exp >= 0x800:                       # complemento a dos de 12 bits
        exp -= 0x1000
    digitos = ''.join('%X' % ((w >> d) & 0xF) for d in range(56, 8, -4))
    if set(digitos) - set('0123456789'):
        raise FormatoInesperado('mantisa que no es BCD: %s' % digitos)
    signo = (w >> 60) & 0xF
    if signo not in (0, 9):
        raise FormatoInesperado('nibble de signo inesperado: %X' % signo)
    if digitos == '0' * 12:
        return 0.0
    # De la cadena decimal al float de una vez. Multiplicar por 10**exp
    # metia error de coma flotante: 0.0006 salia 0.0006000000000000001.
    v = float(digitos[0] + '.' + digitos[1:] + 'E' + str(exp))
    return -v if signo else v


def codifica(x):
    """float -> 8 bytes.

    Se queda con 12 cifras significativas, que es lo que cabe. Un numero con
    mas se redondea, igual que haria la calculadora.
    """
    x = float(x)
    if x != x or x in (float('inf'), float('-inf')):
        raise FormatoInesperado('no hay forma de escribir %r' % x)
    if x == 0.0:
        return struct.pack('<Q', 0)
    mantisa, exp = ('%.11E' % abs(x)).split('E')
    exp = int(exp)
    digitos = mantisa.replace('.', '')[:12].ljust(12, '0')
    if not -2048 <= exp <= 2047:
        raise FormatoInesperado('exponente %d fuera del rango de 12 bits' % exp)
    w = ((9 if x < 0 else 0) << 60) | (exp & 0xFFF)
    for k, ch in enumerate(digitos):
        w |= int(ch) << (56 - 4 * k)
    return struct.pack('<Q', w)


# --------------------------------------------------------------- .hpmat

def lee_hpmat(datos):
    """-> lista de filas (listas de float). Las complejas dan error."""
    if len(datos) < 16:
        raise FormatoInesperado('un .hpmat mide al menos 16 bytes')
    tipo, rango, filas, cols = struct.unpack_from('<2xHIII', datos, 0)
    if rango != 2:
        raise FormatoInesperado('rango %d: esto no es una matriz' % rango)
    if tipo == HPMAT_COMPLEJO:
        raise FormatoInesperado('matriz compleja: no esta cubierto')
    if tipo != HPMAT_REAL:
        raise FormatoInesperado('tipo %04X desconocido' % tipo)
    hacen_falta = 16 + filas * cols * 8
    if len(datos) < hacen_falta:
        raise FormatoInesperado('faltan bytes: %dx%d pide %d y hay %d'
                                % (filas, cols, hacen_falta, len(datos)))
    fuera = []
    for i in range(filas):
        fila = []
        for j in range(cols):
            o = 16 + 8 * (i * cols + j)
            fila.append(decodifica(datos[o:o + 8]))
        fuera.append(fila)
    return fuera


def escribe_hpmat(matriz):
    """[[float]] -> bytes de un .hpmat."""
    filas = len(matriz)
    if not filas:
        raise FormatoInesperado('una matriz vacia no se puede escribir')
    cols = len(matriz[0])
    if any(len(f) != cols for f in matriz):
        raise FormatoInesperado('las filas no miden todas lo mismo')
    fuera = bytearray(struct.pack('<HHIII', 1, HPMAT_REAL, 2, filas, cols))
    for fila in matriz:
        for x in fila:
            fuera += codifica(x)
    return bytes(fuera)


# ------------------------------------------------- el bloque de un programa

def matrices_de_bloque(bloque, minimo=4):
    """Las matrices que se reconocen dentro de un bloque compilado.

    Busca cabeceras [rango=2][filas][cols] cuyos datos decodifiquen enteros
    como BCD valido. Es un barrido, no una gramatica: el bloque lleva ademas
    registros de simbolo que aqui no se interpretan. Sirve para mirar lo que
    hay dentro, no para reescribirlo.

    -> lista de (offset, filas, cols, matriz)
    """
    fuera, o, n = [], 0, len(bloque)
    while o + 12 <= n:
        rango, filas, cols = struct.unpack_from('<III', bloque, o)
        cabe = o + 12 + filas * cols * 8 <= n
        if (rango == 2 and filas >= minimo and cols >= 1
                and filas < 100000 and cols < 1000 and cabe):
            try:
                m = []
                for i in range(filas):
                    m.append([decodifica(bloque[o + 12 + 8 * (i * cols + j):
                                                o + 20 + 8 * (i * cols + j)])
                              for j in range(cols)])
                fuera.append((o, filas, cols, m))
                o += 12 + filas * cols * 8
                continue
            except FormatoInesperado:
                pass
        o += 4
    return fuera


# ------------------------------------------------------------------- CLI

def _csv(path):
    filas = []
    with io.open(path, encoding='utf-8') as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith('#'):
                continue
            filas.append([float(x) for x in linea.replace(';', ',').split(',')])
    return filas


def _cli(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]

    def opt(flag, defecto=None):
        return argv[argv.index(flag) + 1] if flag in argv else defecto

    if cmd == 'read':
        m = lee_hpmat(open(path, 'rb').read())
        print('%s: %d x %d' % (os.path.basename(path), len(m), len(m[0])))
        dest = opt('-o')
        lineas = [','.join(repr(x) for x in fila) for fila in m]
        if dest:
            with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(lineas) + '\n')
            print('  escrito %s' % dest)
        else:
            for l in lineas[:20]:
                print('  ' + l)
            if len(lineas) > 20:
                print('  ... %d filas mas' % (len(lineas) - 20))
        return 0

    if cmd == 'write':
        dest = opt('-o')
        if not dest:
            print('falta -o salida.hpmat')
            return 2
        m = _csv(path)
        datos = escribe_hpmat(m)
        with open(dest, 'wb') as f:
            f.write(datos)
        print('%s -> %s  (%d x %d, %d bytes)'
              % (path, dest, len(m), len(m[0]), len(datos)))
        vuelta = lee_hpmat(datos)
        igual = all(abs(a - b) <= 1e-11 * max(1.0, abs(b))
                    for fa, fb in zip(vuelta, m) for a, b in zip(fa, fb))
        print('  releido correctamente: %s' % igual)
        print('  el nombre del fichero manda: M0.hpmat .. M9.hpmat')
        return 0

    if cmd == 'nums':
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import hpprgm
        datos = open(path, 'rb').read()
        _, _, ini, _ = hpprgm.leer(datos)
        bloque = datos[hpprgm.CABECERA:ini]
        if not bloque:
            print('%s no lleva bloque compilado' % os.path.basename(path))
            return 0
        ms = matrices_de_bloque(bloque)
        print('%s: bloque de %d bytes, %d matrices reconocidas, %d numeros'
              % (os.path.basename(path), len(bloque), len(ms),
                 sum(f * c for _, f, c, _ in ms)))
        for o, f, c, m in ms[:12]:
            print('  offset %-8d %5d x %-3d   empieza por %s'
                  % (o, f, c, ', '.join(repr(x) for x in m[0][:4])))
        if len(ms) > 12:
            print('  ... %d matrices mas' % (len(ms) - 12))
        return 0

    print('comando desconocido: %s' % cmd)
    return 2


if __name__ == '__main__':
    sys.exit(_cli(sys.argv))
