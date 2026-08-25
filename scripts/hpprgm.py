# -*- coding: utf-8 -*-
"""Leer y escribir ficheros .hpprgm de la HP Prime desde el PC.

El .hpprgm es un contenedor TLV anidado, little-endian:

    7C 61 8A B2                        magic
    FE FF FF FF  00 00 00 00           preambulo
    [u32 len][len bytes de payload]    registros, anidados
    ...
    <cola>

El fuente PPL vive dentro de uno de esos registros, en UTF-16LE, con saltos
de linea LF (no CRLF) y terminado en NUL. Va literal: no esta comprimido ni
cifrado.

La cola mide 1008 bytes en los programas escritos por el Connectivity Kit,
pero las apps de fabrica de la calculadora demuestran que no siempre, asi
que aqui no se da por supuesto: el bloque de fuente se localiza por su forma
(ver _rec_chain) y todo lo que va detras se conserva tal cual.

Un programa de codigo (TERMOLIB) es cabecera + fuente + trailer, nada mas.
Un programa que declara matrices grandes (TDAT) lleva ademas un bloque
compilado ANTES del fuente: son los numeros ya en formato interno, que es lo
que hace que el fichero pese ~3x el fuente y que al recibirlo no haya que
esperar ninguna compilacion.

Este modulo NO sabe generar ese bloque compilado. Lo que hace es reemplazar
el fuente dentro de una plantilla existente y ajustar las longitudes de todos
los registros que lo contienen. Para eso:

  - en un programa de codigo funciona directamente;
  - en uno con bloque compilado, el bloque dejaria de corresponder al fuente,
    asi que se rechaza (--force para saltarselo bajo tu responsabilidad).

Uso:
    python hpprgm.py read  PROG.hpprgm [-o salida.txt]
    python hpprgm.py write fuente.txt -t plantilla.hpprgm -o PROG.hpprgm
    python hpprgm.py check PROG.hpprgm          # round-trip: leer y reescribir

La plantilla es cualquier .hpprgm de codigo que haya escrito el Connectivity
Kit; esta en Documentos\\HP Connectivity Kit\\Calculators\\<tu calculadora>\\.
Se copia una vez y sirve para siempre.
"""
from __future__ import unicode_literals
import io, os, struct, sys

MAGIC = b'\x7c\x61\x8a\xb2'


class FormatoInesperado(Exception):
    pass


def _u32(b, off):
    return struct.unpack_from('<I', b, off)[0]


def _texto_plausible(crudo):
    """Un bloque de fuente PPL en UTF-16LE: acaba en NUL y es casi todo
    ASCII imprimible. Sirve para descartar coincidencias falsas."""
    if len(crudo) < 8 or len(crudo) % 2 or crudo[-2:] != b'\x00\x00':
        return False
    try:
        txt = crudo[:-2].decode('utf-16-le')
    except UnicodeDecodeError:
        return False
    if not txt:
        return False
    ascii_ok = sum(1 for c in txt[:2000] if c == '\n' or 0x20 <= ord(c) < 0x7f)
    return ascii_ok >= 0.9 * len(txt[:2000])


def _rec_chain(b):
    """Localiza el bloque de fuente y los registros que lo contienen.

    No se reconstruye la gramatica entera del contenedor: unos registros
    llevan etiqueta de 4 bytes antes de los hijos y otros no, y adivinarla
    lleva a descender mal. Tampoco se da por hecho el tamano del trailer: en
    los tres ficheros de este proyecto son 1008 bytes, pero las apps de
    fabrica de la calculadora demuestran que no siempre.

    Lo que si es firme es la forma del registro del fuente:

        [u32 longitud][u32 etiqueta][texto UTF-16LE][NUL]

    Asi que se busca por ahi, y de todos los candidatos se coge el mayor: el
    fuente de verdad. Los registros que lo envuelven son los que terminan
    exactamente donde el, y son los que hay que reajustar al cambiar el texto.

    Devuelve (offsets de longitud a corregir, inicio del texto, fin del texto).
    """
    if b[:4] != MAGIC:
        raise FormatoInesperado('no empieza por el magic 7C 61 8A B2')
    n = len(b)
    mejor = None
    # Byte a byte, no de 4 en 4: cuando delante del fuente hay un bloque
    # compilado (las matrices de un programa de datos) su tamano no es
    # multiplo de 4 y el registro del fuente queda desalineado.
    for o in range(0x0c, n - 12):
        # filtro barato: el payload ha de empezar por un caracter ASCII
        # codificado en UTF-16LE (byte alto a cero)
        if b[o + 9] != 0:
            continue
        c = b[o + 8]
        if not (c == 0x0a or 0x20 <= c < 0x7f):
            continue
        fin = o + 4 + _u32(b, o)
        if fin > n or fin - (o + 8) < 8:
            continue
        if not _texto_plausible(b[o + 8:fin]):
            continue
        if mejor is None or fin - o > mejor[1] - mejor[0]:
            mejor = (o, fin)
    if mejor is None:
        raise FormatoInesperado('no se encuentra ningun bloque de fuente '
                                '(programa vacio?)')
    off, fin = mejor
    lens = [o for o in range(0x0c, off + 1) if o + 4 + _u32(b, o) == fin]
    return lens, off + 8, fin


def leer(datos):
    """-> (fuente unicode, offsets de longitud, inicio y fin del texto)."""
    lens, ini, fin = _rec_chain(datos)
    txt = datos[ini:fin].decode('utf-16-le')
    return txt.rstrip('\0'), lens, ini, fin


CABECERA = 0x98      # 152: cabecera pelada, el fuente empieza justo aqui


def tiene_bloque_compilado(datos, ini):
    """True si hay algo entre la cabecera y el fuente.

    Un fichero recien escrito por el Connectivity Kit tiene el fuente en el
    offset 152 exacto. Cualquier cosa mas es bloque compilado, y entonces no
    sirve de plantilla: al cambiarle el texto, el bloque dejaria de
    corresponderle.

    El umbral era `> 0x200` y estaba mal. Los programas que guarda la
    calculadora llevan bloques pequenos -- 96, 184, 360 bytes -- que se
    colaban por debajo. Se veia en las reconstrucciones cruzadas, que salian
    exactamente esos bytes mas cortas.
    """
    return ini > CABECERA


def normaliza_fuente(txt):
    """Deja el texto como lo guarda el Connectivity Kit al pegar codigo:
    saltos LF y sin salto final, porque lo que guarda es el buffer del editor.

    No lo aplica `escribir`: las apps de fabrica de la calculadora llevan CRLF
    dentro y hay que poder reescribirlas tal cual. Lo aplica el CLI, que es
    quien parte de un .txt del PC."""
    t = txt.replace('\r\n', '\n').replace('\r', '\n')
    return t[:-1] if t.endswith('\n') else t


def escribir(plantilla, fuente):
    """Mete `fuente` en `plantilla` (bytes) ajustando las longitudes.

    El texto se guarda tal cual: quien quiera los saltos de linea al estilo
    del CK que pase antes por normaliza_fuente()."""
    viejo, lens, ini, fin = leer(plantilla)
    blob = (fuente + '\0').encode('utf-16-le')
    delta = len(blob) - (fin - ini)
    out = bytearray(plantilla[:ini]) + blob + plantilla[fin:]
    for off in lens:                       # cada registro que lo contiene
        struct.pack_into('<I', out, off, _u32(bytes(out), off) + delta)
    return bytes(out)


# ------------------------------------------------------------------ CLI

def _cli(argv):
    if len(argv) < 3:
        print(__doc__)
        return 2
    cmd, path = argv[1], argv[2]
    args = argv[3:]

    def opt(flag, defecto=None):
        return args[args.index(flag) + 1] if flag in args else defecto

    datos = open(path, 'rb').read()

    if cmd == 'read':
        txt, lens, ini, fin = leer(datos)
        dest = opt('-o')
        print('%s: %d bytes, fuente %d chars en offset %d'
              % (os.path.basename(path), len(datos), len(txt), ini))
        if tiene_bloque_compilado(datos, ini):
            print('  lleva %d bytes de bloque compilado antes del fuente'
                  % (ini - 0x98))
        if dest:
            with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
                f.write(txt)
            print('  escrito %s' % dest)
        else:
            sys.stdout.write(txt.encode('utf-8') if str is bytes else txt)
        return 0

    if cmd == 'check':
        txt, lens, ini, fin = leer(datos)
        rehecho = escribir(datos, txt)
        ok = rehecho == datos
        print('round-trip %s: %s' % (os.path.basename(path),
                                     'IDENTICO' if ok else 'DIFIERE'))
        if not ok:
            print('  original %d bytes, rehecho %d' % (len(datos), len(rehecho)))
            for i, (a, b) in enumerate(zip(datos, rehecho)):
                if a != b:
                    print('  primera diferencia en offset %d' % i)
                    break
        return 0 if ok else 1

    if cmd == 'write':
        tpl_path = opt('-t')
        dest = opt('-o')
        if not tpl_path or not dest:
            print('faltan -t plantilla.hpprgm y/o -o salida.hpprgm')
            return 2
        plantilla = open(tpl_path, 'rb').read()
        _, _, ini, _ = leer(plantilla)
        if tiene_bloque_compilado(plantilla, ini) and '--force' not in args:
            print('ERROR: la plantilla lleva un bloque compilado de %d bytes.'
                  % (ini - 0x98))
            print('       Cambiar el fuente lo dejaria descuadrado. Usa como')
            print('       plantilla un programa de codigo (sin matrices), o')
            print('       --force si sabes lo que haces.')
            return 1
        fuente = normaliza_fuente(io.open(path, encoding='utf-8').read())
        out = escribir(plantilla, fuente)
        with open(dest, 'wb') as f:
            f.write(out)
        print('%s -> %s  (%d bytes)' % (path, dest, len(out)))
        # comprobacion inmediata: releer lo escrito
        print('  releido correctamente:', leer(out)[0] == fuente)
        return 0

    print('comando desconocido: %s' % cmd)
    return 2


if __name__ == '__main__':
    sys.exit(_cli(sys.argv))
