# -*- coding: utf-8 -*-
"""Pruebas del lector/escritor de .hpprgm.

Necesitan ficheros que haya escrito el Connectivity Kit. Si no se encuentran,
la prueba se salta en vez de fallar: son especificos de cada maquina.

    python tests/test_hpprgm.py [carpeta_de_la_calculadora]

La carpeta por defecto es
    %USERPROFILE%\\Documents\\HP Connectivity Kit\\Calculators\\<la primera>
"""
from __future__ import unicode_literals
import io, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', 'scripts'))
import hpprgm as H


def busca_calculadora(dado=None):
    if dado:
        return dado
    base = os.path.join(os.path.expanduser('~'), 'Documents',
                        'HP Connectivity Kit', 'Calculators')
    if not os.path.isdir(base):
        return None
    for d in sorted(os.listdir(base)):
        p = os.path.join(base, d)
        if os.path.isdir(p) and any(f.endswith('.hpprgm')
                                    for f in os.listdir(p)):
            return p
    return None


def main(argv):
    carpeta = busca_calculadora(argv[1] if len(argv) > 1 else None)
    if not carpeta:
        print('SALTADA: no se encuentra ninguna carpeta del Connectivity Kit')
        return 0

    binarios = []
    for raiz, _, fs in os.walk(carpeta):
        for f in sorted(fs):
            if f.endswith(('.hpprgm', '.hpappprgm')):
                binarios.append(os.path.join(raiz, f))
    if not binarios:
        print('SALTADA: no hay programas en %s' % carpeta)
        return 0

    ok = fallos = saltados = cruzados = 0
    plantilla = None
    for path in binarios:
        datos = open(path, 'rb').read()
        nombre = os.path.basename(path)
        try:
            txt, lens, ini, _fin = H.leer(datos)
        except H.FormatoInesperado as e:
            # un programa sin bloque de fuente es un programa vacio: las apps
            # de fabrica de la calculadora lo son. No es un fallo.
            saltados += 1
            continue

        # 1) round-trip: reescribir lo mismo debe dar el fichero identico
        if H.escribir(datos, txt) == datos:
            ok += 1
            print('  ok    %-24s round-trip identico (%d chars)'
                  % (nombre, len(txt)))
        else:
            fallos += 1
            print('  FALLO %-24s round-trip distinto' % nombre)

        if not H.tiene_bloque_compilado(datos, ini) and plantilla is None:
            plantilla = (nombre, datos)

    # Una plantilla guardada a mano gana a lo que haya en la carpeta del CK:
    # esos ficheros dejan de servir en cuanto la calculadora reescribe el
    # programa, porque entonces llevan su propio bloque compilado.
    fija = os.environ.get('HP_PRIME_PLANTILLA') or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'plantilla_codigo.hpprgm')
    if os.path.isfile(fija):
        d = open(fija, 'rb').read()
        try:
            if not H.tiene_bloque_compilado(d, H.leer(d)[2]):
                plantilla = (os.path.basename(fija), d)
        except H.FormatoInesperado:
            pass

    # 2) cruzado: meter el fuente de un programa en la plantilla de otro.
    #    Es la prueba que de verdad valida la aritmetica de longitudes,
    #    porque el tamano cambia.
    if plantilla:
        pn, pd = plantilla
        for path in binarios:
            datos = open(path, 'rb').read()
            nombre = os.path.basename(path)
            if nombre == pn:
                continue
            try:
                txt, _, ini, _fin = H.leer(datos)
            except H.FormatoInesperado:
                continue
            if H.tiene_bloque_compilado(datos, ini):
                continue
            gen = H.escribir(pd, txt)
            cruzados += 1
            # Lo que el escritor construye es cabecera + fuente; la cola la
            # copia de la plantilla. Y la cola NO siempre es la misma: puede
            # llevar metadatos. Asi que se comprueba lo que de verdad
            # construye, y la cola se informa aparte en vez de fallar.
            if gen[:_fin] == datos[:_fin]:
                ok += 1
                igual_cola = gen[_fin:] == datos[_fin:]
                print('  ok    %-24s reconstruido desde %s%s'
                      % (nombre, pn,
                         '' if igual_cola else '  (cola distinta, se copia'
                                               ' la de la plantilla)'))
            else:
                fallos += 1
                print('  FALLO %-24s cabecera o fuente distintos (%d vs %d)'
                      % (nombre, len(gen), len(datos)))

    print('\nPASS: %d   FAIL: %d   saltados (programas vacios): %d'
          % (ok, fallos, saltados))
    if cruzados:
        print('reconstrucciones cruzadas: %d' % cruzados)
    else:
        # La prueba fuerte es reconstruir un programa desde la plantilla de
        # OTRO de distinto tamano: es lo unico que ejercita la aritmetica de
        # longitudes. Sin plantilla esto son solo round-trips, que valen
        # bastante menos. Mejor decirlo que encogerse en silencio.
        print('')
        print('AVISO: ninguna reconstruccion cruzada, que es la comprobacion')
        print('  que de verdad valida el escritor. Hace falta un .hpprgm de')
        print('  codigo SIN bloque compilado, o sea escrito por el')
        print('  Connectivity Kit y no por la calculadora: en cuanto la')
        print('  calculadora reescribe un programa, deja de servir.')
        print('  Guarda uno como plantilla_codigo.hpprgm en la raiz del')
        print('  repositorio, o apuntalo con HP_PRIME_PLANTILLA.')
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
