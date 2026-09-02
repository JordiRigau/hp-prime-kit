# -*- coding: utf-8 -*-
"""Construir y comprobar una app (.hpappdir) de la HP Prime desde el PC.

Una app es una carpeta con tres envoltorios binarios y los ficheros que la
app se lleva. Los tres envoltorios NO llevan el nombre de la app dentro: el
nombre sale del de la carpeta y del de los ficheros. Por eso un juego vale
para cualquier app, y por eso esto puede generarlos.

Los de plantillas/ salen de apps que arrancan bien en una G2: el descriptor de
Python del MarkdownViewer, y el de app en blanco -la forma de una app de PPL-
de TAULES. Ver plantillas/README.md.

    MIAPP.hpappdir/
       MIAPP.hpapp        ajustes, y LA VISTA DE ARRANQUE
       MIAPP.hpappnote    la nota
       MIAPP.hpappprgm    el programa PPL (vacio en una app de Python)
       icon.png           opcional
       *.py               los modulos

POR QUE HAY QUE REHACER LOS ENVOLTORIOS EN CADA CONSTRUCCION

Al salir de la app, la calculadora los REESCRIBE para guardar su estado,
entre otras cosas la vista en la que estabas. Si luego el Connectivity Kit
se trae la carpeta al PC, ese estado entra en el repositorio y a partir de
ahi la app arranca donde la dejaste: con un 03 en los ultimos cuatro bytes
del .hpapp, se abre en la consola de Python en vez de en su pantalla.

Paso de verdad. Por eso los envoltorios buenos viven en plantillas/ y se
copian siempre, y por eso existe --check.

    python scripts/mkapp.py MIAPP src/*.py --icon icon.png
    python scripts/mkapp.py MIAPP app.txt --ppl -t plantilla.hpprgm
    python scripts/mkapp.py --check MIAPP.hpappdir src/*.py

Opciones:
    --icon FICHERO    lo copia como icon.png (73x74 es lo que usa HP)
    --ppl FUENTE      mete un fuente PPL en el .hpappprgm; necesita -t
    -t PLANTILLA      .hpprgm de codigo escrito por el CK, para --ppl
    --base python|blanca|FICHERO.hpapp   que descriptor se copia
    -o DIR            donde crear la carpeta
    --allow a,b       modulos que se importan y que sabes que existen
    --check           no escribe: compara

--check no escribe nada: dice si la carpeta sigue siendo la que generarias.
Sale con codigo 1 si no, asi que sirve de puerta en cualquier script.
"""
from __future__ import unicode_literals
import io, os, re, shutil, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
PLANTILLAS = os.path.join(RAIZ, 'plantillas')

ENVOLTORIOS = ('hpapp', 'hpappnote', 'hpappprgm')

# Hay dos descriptores, porque no son intercambiables: uno dice "esta app se
# basa en la de Python" y el otro "esta app esta en blanco". Los dos salen de
# apps que arrancan bien en una G2.
#
#   app-python.hpapp   188 B, del MarkdownViewer. Sus ultimos cuatro bytes
#                      son la vista de arranque: 01 la de la app, 03 la
#                      consola de Python.
#   app-blanca.hpapp   124 B, de una app creada con Base App: None. Es la
#                      forma de las apps de PPL.
DESCRIPTORES = {'python': 'app-python.hpapp', 'blanca': 'app-blanca.hpapp'}

# Lo que MicroPython tiene en la Prime. Un import de fuera de aqui no da
# error al copiar: da que LA APP SE CIERRA AL ARRANCAR, sin decir nada. Por
# eso se avisa desde el PC.
#
# `time` no esta: las apps que lo necesitan se traen su propio time.py
# construido sobre eval('ticks()').
MICROPYTHON = set("""math cmath array gc micropython hpprime graphic cas
builtins""".split())


class ErrorApp(Exception):
    pass


def _lee(p, binario=True):
    if binario:
        f = open(p, 'rb')
    else:
        f = io.open(p, encoding='utf-8')
    try:
        return f.read()
    finally:
        f.close()


def imports_de_nivel_superior(texto):
    """Los modulos que un .py importa FUERA de cualquier funcion.

    Los de dentro de una funcion no cuentan: solo se ejecutan si se llama, y
    ese es el rodeo habitual para lo que solo existe en un lado.
    """
    fuera = []
    for linea in texto.replace('\r\n', '\n').split('\n'):
        if linea[:1] in (' ', '\t'):
            continue
        m = re.match(r'\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
                     linea)
        if m:
            fuera.append((m.group(1) or m.group(2)).split('.')[0])
    return fuera


def revisa_imports(modulos, permitidos):
    """-> lista de (fichero, modulo) que MicroPython no tendria."""
    conocidos = set(permitidos) | MICROPYTHON
    conocidos |= set(os.path.splitext(os.path.basename(m))[0]
                     for m in modulos)
    malos = []
    for m in modulos:
        for nombre in imports_de_nivel_superior(_lee(m, binario=False)):
            if nombre not in conocidos:
                malos.append((m, nombre))
    return malos


def destino(nombre, base='.'):
    return os.path.join(base, nombre + '.hpappdir')


def _piezas(nombre, modulos, icono, descriptor='python'):
    """-> {nombre dentro de la app: ruta de origen}."""
    if descriptor in DESCRIPTORES:
        hpapp = os.path.join(PLANTILLAS, DESCRIPTORES[descriptor])
    else:
        hpapp = descriptor           # una ruta a un .hpapp tuyo
    piezas = {'%s.hpapp' % nombre: hpapp}
    for ext in ('hpappnote', 'hpappprgm'):
        piezas['%s.%s' % (nombre, ext)] = os.path.join(PLANTILLAS,
                                                       'app.' + ext)
    for m in modulos:
        piezas[os.path.basename(m)] = m
    if icono:
        piezas['icon.png'] = icono
    return piezas


def construye(nombre, modulos, icono=None, base='.', quiet=False,
              descriptor='python'):
    """Crea o rehace la carpeta. -> ruta de la carpeta."""
    carpeta = destino(nombre, base)
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    piezas = _piezas(nombre, modulos, icono, descriptor)
    for destino_rel in sorted(piezas):
        origen = piezas[destino_rel]
        ruta = os.path.join(carpeta, destino_rel)
        cambia = (not os.path.isfile(ruta)
                  or _lee(origen) != _lee(ruta))
        shutil.copyfile(origen, ruta)
        if not quiet:
            print('%-24s %7d B%s' % (destino_rel, os.path.getsize(ruta),
                                     '   REHECHO' if cambia else ''))

    # __pycache__ lo deja el PC al probar, y en la calculadora no pinta
    # nada: son .pyc de CPython que MicroPython no leeria.
    cache = os.path.join(carpeta, '__pycache__')
    if os.path.isdir(cache):
        shutil.rmtree(cache)
        if not quiet:
            print('%-24s         borrado' % '__pycache__')

    if not quiet:
        sobran = [f for f in sorted(os.listdir(carpeta))
                  if f not in piezas and not f.startswith('.')]
        if sobran:
            print('\nen la carpeta y no en la receta (no se tocan): %s'
                  % ', '.join(sobran))
    return carpeta


def comprueba(carpeta, modulos, icono=None, descriptor='python'):
    """-> lista de (fichero, que pasa). Vacia si la carpeta esta al dia."""
    carpeta = carpeta.rstrip('/\\')
    nombre = os.path.basename(carpeta)
    if nombre.endswith('.hpappdir'):
        nombre = nombre[:-len('.hpappdir')]
    if not os.path.isdir(carpeta):
        raise ErrorApp('no existe la carpeta %s' % carpeta)

    fuera = []
    for destino_rel, origen in sorted(_piezas(nombre, modulos, icono,
                                              descriptor).items()):
        ruta = os.path.join(carpeta, destino_rel)
        if not os.path.isfile(ruta):
            fuera.append((destino_rel, 'no esta en la app'))
        elif _lee(origen) != _lee(ruta):
            if destino_rel.endswith(ENVOLTORIOS):
                fuera.append((destino_rel, 'la calculadora lo ha reescrito: '
                                           'vuelve a construir la app'))
            else:
                fuera.append((destino_rel, 'ha divergido del original'))
    if os.path.isdir(os.path.join(carpeta, '__pycache__')):
        fuera.append(('__pycache__', 'sobra: son .pyc de CPython'))
    return fuera


def programa_ppl(carpeta, nombre, fuente, plantilla):
    """Mete un fuente PPL en el .hpappprgm, usando hpprgm.py.

    La plantilla del esqueleto NO sirve aqui: es un programa vacio, no tiene
    bloque de fuente que sustituir. Hace falta un .hpprgm de codigo escrito
    por el Connectivity Kit, que es lo mismo que pide `hpprgm.py write`.
    """
    sys.path.insert(0, AQUI)
    import hpprgm
    datos_tpl = _lee(plantilla)
    try:
        _, _, ini, _ = hpprgm.leer(datos_tpl)
    except hpprgm.FormatoInesperado as e:
        raise ErrorApp('la plantilla %s no sirve: %s' % (plantilla, e))
    if hpprgm.tiene_bloque_compilado(datos_tpl, ini):
        raise ErrorApp('la plantilla %s lleva %d bytes de bloque compilado; '
                       'cambiarle el fuente lo dejaria descuadrado. Usa un '
                       'programa de codigo del Connectivity Kit'
                       % (plantilla, ini - hpprgm.CABECERA))
    texto = hpprgm.normaliza_fuente(io.open(fuente, encoding='utf-8').read())
    datos = hpprgm.escribir(datos_tpl, texto)
    if hpprgm.leer(datos)[0] != texto:
        raise ErrorApp('lo escrito no se relee igual: no lo instales')
    ruta = os.path.join(carpeta, '%s.hpappprgm' % nombre)
    f = open(ruta, 'wb')
    try:
        f.write(datos)
    finally:
        f.close()
    return ruta


def _cli(argv):
    args = [a for a in argv[1:] if not a.startswith('-')]
    if not args or '--help' in argv or '-h' in argv:
        print(__doc__)
        return 2

    def opcion(*nombres):
        for n in nombres:
            if n in argv:
                i = argv.index(n)
                if i + 1 < len(argv):
                    return argv[i + 1]
        return None

    icono = opcion('--icon')
    plantilla = opcion('-t', '--plantilla')
    base = opcion('-o', '--dir') or '.'
    permitidos = (opcion('--allow') or '').split(',')
    quiet = '--quiet' in argv
    es_ppl = '--ppl' in argv
    # Una app de PPL se hace en blanco; una de Python hereda de la de Python.
    descriptor = opcion('--base') or ('blanca' if es_ppl else 'python')
    # Los valores de las opciones no son ficheros de entrada.
    valores = set(x for x in (icono, plantilla, base, opcion('--allow'),
                              opcion('--base')) if x)
    entradas = [a for a in args if a not in valores]

    if '--check' in argv:
        carpeta, modulos = entradas[0], entradas[1:]
        try:
            fuera = comprueba(carpeta, modulos, icono, descriptor)
        except ErrorApp as e:
            print('ERROR: %s' % e)
            return 1
        for f, motivo in fuera:
            print('%s: %s' % (f, motivo))
        print('\n%s: %d diferencia(s)' % (carpeta, len(fuera)))
        return 1 if fuera else 0

    nombre, resto = entradas[0], entradas[1:]
    modulos = [m for m in resto if m.endswith('.py')]
    fuentes_ppl = [m for m in resto if not m.endswith('.py')]

    if es_ppl and not plantilla:
        # La convencion del kit: un .hpprgm de codigo escrito por el CK,
        # guardado en la raiz. Es la misma que usa tests/test_hpprgm.py.
        por_defecto = os.path.join(RAIZ, 'plantilla_codigo.hpprgm')
        if os.path.isfile(por_defecto):
            plantilla = por_defecto
    if es_ppl and (not fuentes_ppl or not plantilla):
        print('ERROR: --ppl necesita un fuente PPL y una plantilla.')
        print('       Pasala con -t, o guarda un .hpprgm de codigo escrito')
        print('       por el Connectivity Kit como plantilla_codigo.hpprgm')
        print('       en la raiz del repositorio.')
        return 2

    carpeta = construye(nombre, modulos, icono, base, quiet, descriptor)

    if es_ppl:
        try:
            ruta = programa_ppl(carpeta, nombre, fuentes_ppl[0], plantilla)
        except ErrorApp as e:
            print('ERROR: %s' % e)
            return 1
        if not quiet:
            print('%-24s %7d B   desde %s'
                  % (os.path.basename(ruta), os.path.getsize(ruta),
                     fuentes_ppl[0]))

    # El punto de entrada de una app de Python es main.py, y su codigo va a
    # nivel de modulo: es lo que hacen las tres apps que se han leido. Sin el,
    # la app arranca y no pasa nada.
    if modulos and not es_ppl and not any(
            os.path.basename(m) == 'main.py' for m in modulos):
        print('AVISO: no hay ningun main.py. El punto de entrada de una app '
              'de Python es\n       main.py, y su codigo se ejecuta al '
              'importarse.')

    malos = revisa_imports(modulos, [p for p in permitidos if p])
    for fichero, mod in malos:
        print('AVISO: %s importa "%s", que MicroPython en la Prime no tiene. '
              'La app se cerraria al arrancar, sin decir nada.'
              % (os.path.basename(fichero), mod))

    if not quiet:
        print('\n%s listo. Arrastralo ENCIMA de la calculadora en la ventana '
              'del Connectivity Kit\n(la carpeta Calculators\\ es un espejo: '
              'copiarlo ahi no instala nada).' % carpeta)
    return 0


if __name__ == '__main__':
    sys.exit(_cli(sys.argv))
