# -*- coding: utf-8 -*-
"""Pruebas de mkapp.py: que la app se construye y que --check ve lo que tiene
que ver.

La prueba que de verdad importa es la del byte de la vista de arranque. Ese
fallo -la app abriendose en la consola de Python en vez de en su pantalla- no
se ve leyendo el codigo ni compilando nada: solo aparece al abrir la app en la
calculadora. Aqui se cierra desde el PC.

    python tests/test_mkapp.py
"""
from __future__ import unicode_literals
import io, os, shutil, sys, tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
import mkapp as M

PASS, FAIL = [0], [0]


def ok(cierto, msg, detalle=''):
    if cierto:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FALLO %s%s' % (msg, ('  ' + detalle) if detalle else ''))


def escribe(ruta, texto):
    with io.open(ruta, 'w', encoding='utf-8') as f:
        f.write(texto)


def main():
    tmp = tempfile.mkdtemp(prefix='mkapp_')
    try:
        # --------------------------------------------------- las plantillas
        for ext in ('hpappnote', 'hpappprgm'):
            p = os.path.join(M.PLANTILLAS, 'app.' + ext)
            ok(os.path.isfile(p), 'existe la plantilla app.%s' % ext)
        for clave, fich in sorted(M.DESCRIPTORES.items()):
            ok(os.path.isfile(os.path.join(M.PLANTILLAS, fich)),
               'existe el descriptor "%s" (%s)' % (clave, fich))

        hpapp = open(os.path.join(M.PLANTILLAS,
                                  M.DESCRIPTORES['python']), 'rb').read()
        # Los ultimos cuatro bytes son la vista de arranque: 01 es la de la
        # app, 03 es la Vista Numerica -en una app de Python, la consola-.
        ok(hpapp[-4:] == b'\x01\x00\x00\x00',
           'la plantilla arranca en la vista de la app (01), no en la consola',
           'ultimos 4 bytes: %s' % ' '.join('%02X' % b for b in hpapp[-4:]))
        ok(hpapp[:4] == b'\x7c\x61\x8a\xb2',
           'la plantilla .hpapp empieza por el magic de la Prime')

        # ------------------------------------------------------ construccion
        src = os.path.join(tmp, 'src')
        os.makedirs(src)
        escribe(os.path.join(src, 'main.py'), 'import motor\nmotor.va()\n')
        escribe(os.path.join(src, 'motor.py'),
                'from math import sqrt\n\n\ndef va():\n    return sqrt(2)\n')
        modulos = [os.path.join(src, 'main.py'), os.path.join(src, 'motor.py')]

        carpeta = M.construye('MIAPP', modulos, base=tmp, quiet=True)
        ok(os.path.isdir(carpeta), 'crea la carpeta .hpappdir')
        for f in ('MIAPP.hpapp', 'MIAPP.hpappnote', 'MIAPP.hpappprgm',
                  'main.py', 'motor.py'):
            ok(os.path.isfile(os.path.join(carpeta, f)), 'copia %s' % f)
        ok(open(os.path.join(carpeta, 'MIAPP.hpapp'), 'rb').read() == hpapp,
           'el envoltorio sale byte a byte igual que la plantilla')

        ok(M.comprueba(carpeta, modulos) == [],
           'recien construida, --check no encuentra nada')

        # ------------------------- la calculadora reescribe el envoltorio
        ruta = os.path.join(carpeta, 'MIAPP.hpapp')
        with open(ruta, 'wb') as f:
            f.write(hpapp[:-4] + b'\x03\x00\x00\x00')
        fuera = dict(M.comprueba(carpeta, modulos))
        ok('MIAPP.hpapp' in fuera,
           've el .hpapp reescrito (el fallo de la consola de Python)')
        ok('reescrito' in fuera.get('MIAPP.hpapp', ''),
           'y dice que fue la calculadora', repr(fuera.get('MIAPP.hpapp')))

        M.construye('MIAPP', modulos, base=tmp, quiet=True)
        ok(M.comprueba(carpeta, modulos) == [],
           'reconstruir lo deja como estaba')

        # --------------------------------- un modulo editado en la app
        escribe(os.path.join(carpeta, 'motor.py'), '# tocado a mano\n')
        fuera = dict(M.comprueba(carpeta, modulos))
        ok(fuera.get('motor.py', '').startswith('ha divergido'),
           've un modulo que ha divergido del original')

        # ------------------------------------------ falta un modulo
        os.remove(os.path.join(carpeta, 'main.py'))
        fuera = dict(M.comprueba(carpeta, modulos))
        ok(fuera.get('main.py') == 'no esta en la app',
           've un modulo que falta')

        # ------------------------------------------------- __pycache__
        M.construye('MIAPP', modulos, base=tmp, quiet=True)
        os.makedirs(os.path.join(carpeta, '__pycache__'))
        fuera = dict(M.comprueba(carpeta, modulos))
        ok('__pycache__' in fuera, '--check ve el __pycache__')
        M.construye('MIAPP', modulos, base=tmp, quiet=True)
        ok(not os.path.isdir(os.path.join(carpeta, '__pycache__')),
           'construir borra el __pycache__')

        # ------------------------------------------------ los imports
        escribe(os.path.join(src, 'reloj.py'),
                'import time\nimport math\n\n\ndef f():\n    import json\n')
        malos = M.revisa_imports([os.path.join(src, 'reloj.py')], [])
        nombres = [m for _, m in malos]
        ok('time' in nombres,
           'avisa de "import time": MicroPython en la Prime no lo tiene')
        ok('math' not in nombres, 'no se queja de math, que si existe')
        ok('json' not in nombres,
           'no mira los imports de dentro de una funcion')
        ok(M.revisa_imports(modulos, []) == [],
           'no da falsas alarmas con un modulo que importa a un hermano')

        # ------------------------------- el descriptor de una app en blanco
        blanca = M.construye('ENBLANCO', [], base=tmp, quiet=True,
                             descriptor='blanca')
        d = open(os.path.join(blanca, 'ENBLANCO.hpapp'), 'rb').read()
        ok(d == open(os.path.join(M.PLANTILLAS,
                                  M.DESCRIPTORES['blanca']), 'rb').read(),
           '--base blanca copia el descriptor de app en blanco')
        ok(d != hpapp, 'los dos descriptores no son el mismo fichero')

        # ------------------------------------ app de PPL con plantilla real
        tpl = _plantilla_ck()
        if tpl:
            fuente = os.path.join(tmp, 'app.txt')
            escribe(fuente, 'EXPORT START()\nBEGIN\n  RETURN 1;\nEND;')
            ruta = M.programa_ppl(carpeta, 'MIAPP', fuente, tpl)
            sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
            import hpprgm
            leido = hpprgm.leer(open(ruta, 'rb').read())[0]
            ok(leido == 'EXPORT START()\nBEGIN\n  RETURN 1;\nEND;',
               'el .hpappprgm generado devuelve el mismo fuente')
        else:
            print('  --    sin plantilla del Connectivity Kit: me salto la '
                  'app de PPL')

        # el esqueleto vacio NO sirve de plantilla, y tiene que decirlo
        vacio = os.path.join(M.PLANTILLAS, 'app.hpappprgm')
        fuente = os.path.join(tmp, 'x.txt')
        escribe(fuente, 'EXPORT F()\nBEGIN\n  RETURN 1;\nEND;')
        try:
            M.programa_ppl(carpeta, 'MIAPP', fuente, vacio)
            ok(False, 'rechaza el .hpappprgm vacio como plantilla')
        except M.ErrorApp:
            ok(True, 'rechaza el .hpappprgm vacio como plantilla')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


def _plantilla_ck():
    """Un programa SIN bloque compilado de tu Connectivity Kit, si lo hay.

    Mira tambien dentro de las .hpappdir, porque en la practica es donde
    aparecen: casi todo lo que hay en la carpeta espejo ha pasado por la
    calculadora, y la calculadora le anade su bloque compilado a todo lo que
    guarda. En la maquina donde se escribio esto, de 58 contenedores de
    programa solo 2 servian de plantilla, y los dos eran .hpappprgm.
    """
    import glob
    sys.path.insert(0, os.path.join(RAIZ, 'scripts'))
    import hpprgm
    base = os.path.join(os.path.expanduser('~'), 'Documents',
                        'HP Connectivity Kit', 'Calculators')
    if not os.path.isdir(base):
        base = os.path.join(os.path.expanduser('~'), 'Documentos',
                            'HP Connectivity Kit', 'Calculators')
    if not os.path.isdir(base):
        return None
    for calc in sorted(os.listdir(base)):
        d = os.path.join(base, calc)
        if not os.path.isdir(d):
            continue
        candidatos = [os.path.join(d, f) for f in sorted(os.listdir(d))
                      if f.endswith('.hpprgm')]
        candidatos += sorted(glob.glob(os.path.join(d, '*.hpappdir',
                                                    '*.hpappprgm')))
        for p in candidatos:
            try:
                datos = open(p, 'rb').read()
                _, _, ini, _ = hpprgm.leer(datos)
                if not hpprgm.tiene_bloque_compilado(datos, ini):
                    return p
            except Exception:
                continue
    return None


if __name__ == '__main__':
    sys.exit(main())
