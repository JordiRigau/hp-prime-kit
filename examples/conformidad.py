# -*- coding: utf-8 -*-
"""Ejemplo: comparar el PPL real contra un motor de referencia en Python.

Es el uso que de verdad rentabiliza el interprete. Si tienes el mismo calculo
escrito dos veces —en PPL para la calculadora y en Python para desarrollar—,
las pruebas normales no pueden decirte si divergen: cada implementacion es
coherente consigo misma y las dos pasan sus propios tests. Ejecutando el PPL
y comparando, las divergencias salen solas.

Este fichero esta escrito contra el proyecto TermoHP (tablas termodinamicas),
que es donde se probo. No es una libreria: es una plantilla para copiar y
adaptar. Lo que hay que cambiar esta en carga_ppl(), carga_referencia() y
casos().

Encontro un fallo real: la busqueda inversa por presion no contemplaba la
region supercritica, mientras que la de (P,T) si. Afectaba a 30 isobaras de 6
sustancias, y ninguna de las tres bancadas de pruebas del proyecto podia
verlo.

    python examples/conformidad.py /ruta/a/TermoHP
"""
from __future__ import unicode_literals
import glob, os, sys, time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'scripts'))
import pplrun

TOL = 1e-6


# --------------------------------------------------------------------- carga
def carga_ppl(raiz):
    """Todo lo que va a la calculadora, en orden de compilacion."""
    m = pplrun.Maquina()
    m.carga_fichero(os.path.join(raiz, 'ppl', 'TDAT_REG.hpprgm'))
    for f in sorted(glob.glob(os.path.join(raiz, 'ppl', 'TDAT_*.hpprgm'))):
        if not f.endswith('REG.hpprgm'):
            m.carga_fichero(f)
    m.carga_fichero(os.path.join(raiz, 'ppl', 'TERMOLIB.hpprgm'))
    return m


def carga_referencia(raiz):
    sys.path.insert(0, os.path.join(raiz, 'tools'))
    import engine
    return engine


# ---------------------------------------------------------------- comparar
def cerca(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOL * (abs(b) + 1.0)


def compara(nombre, ppl, ref, regiones, fallos):
    """ppl: la lista que devuelve la funcion PPL. ref: el dict del motor.

    Se comparan tambien los ERRORES: que los dos fallen en los mismos sitios
    es la mitad del valor. Un lado que devuelve un numero donde el otro se
    niega es justo la clase de divergencia que se busca.
    """
    if ppl[7] < 0:                                   # el PPL dice error
        if ref is None:
            return True
        fallos.append('%s: el PPL da error (%s) y el motor da resultado'
                      % (nombre, ppl[8]))
        return False
    if ref is None:
        fallos.append('%s: el PPL da resultado y el motor da error' % nombre)
        return False
    mal = []
    for i, k in enumerate(('T', 'P', 'v', 'u', 'h', 's')):
        if not cerca(ppl[i], ref[k]):
            mal.append('%s %.10g vs %.10g' % (k, ppl[i], ref[k]))
    xr = ref['x'] if ref['x'] is not None else -1.0
    if not cerca(ppl[6], xr):
        mal.append('x %.10g vs %.10g' % (ppl[6], xr))
    rr = regiones.get(ref['region'])
    if rr is None or int(ppl[7]) != rr:
        mal.append('region %d vs %s' % (int(ppl[7]), ref['region']))
    if mal:
        fallos.append('%s: %s' % (nombre, '; '.join(mal)))
        return False
    return True


def seguro(fn, *a):
    """Un error del motor de referencia es un resultado valido que comparar,
    no una excepcion que pare el barrido."""
    try:
        return fn(*a)
    except Exception:
        return None


# ------------------------------------------------------------------- casos
def casos(m, E, orden):
    """Genera (nombre, resultado_ppl, resultado_referencia).

    Los casos salen de los PROPIOS DATOS, no de una lista escrita a mano: los
    nodos tabulados, los puntos intermedios entre dos nodos y las inversas
    desde cada nodo. Asi el barrido crece con los datos y no se queda corto
    justo donde nadie miro.
    """
    subs = E.substances()
    for key in sorted(orden):
        sub = subs[key]
        m.llama('TLOAD', float(orden[key]))
        etq = key[:6]

        filas = sub['sat_by_T']
        for fila in filas[::max(1, len(filas) // 6)]:
            T = fila['T']
            for x in (0.0, 0.5, 1.0):
                yield ('%s TTX(%.4g,%.1f)' % (etq, T, x),
                       seguro(m.llama, 'TTX', T, x),
                       seguro(E.state_Tx, sub, T, x))

        filas = sub['sat_by_P']
        for fila in filas[::max(1, len(filas) // 6)]:
            P = fila['P']
            for x in (0.0, 1.0):
                yield ('%s TPX(%.4g,%.1f)' % (etq, P, x),
                       seguro(m.llama, 'TPX', P, x),
                       seguro(E.state_Px, sub, P, x))

        for b in sub['isobars'][::max(1, len(sub['isobars']) // 5)]:
            P, rows = b['P'], b['rows']
            paso = max(1, len(rows) // 5)
            for j in range(0, len(rows) - 1, paso):
                for T in (rows[j]['T'],
                          (rows[j]['T'] + rows[j + 1]['T']) / 2.0):
                    yield ('%s TPT(%.6g,%.6g)' % (etq, P, T),
                           seguro(m.llama, 'TPT', P, T),
                           seguro(E.state_PT, sub, P, T))
                for pr, k in ((3, 'h'), (4, 's')):
                    y = rows[j][k]
                    yield ('%s TPY(%.6g,%s,%.8g)' % (etq, P, k, y),
                           seguro(m.llama, 'TPY', P, float(pr), y),
                           seguro(E.state_Py, sub, P, k, y))


def main(argv):
    raiz = argv[1] if len(argv) > 1 else '.'
    if not os.path.isdir(os.path.join(raiz, 'ppl')):
        print('no encuentro %s/ppl -- pasa la raiz del proyecto' % raiz)
        return 2

    t0 = time.time()
    m = carga_ppl(raiz)
    E = carga_referencia(raiz)
    regiones = {E.LIQUID: 0, E.MIX: 1, E.VAPOR: 2, E.SUPER: 3}
    orden = {}
    for i, k6 in enumerate(m.globales['TSUBS'], 1):
        for key in E.substances():
            if key[:6] == k6:
                orden[key] = i
    print('PPL cargado: %d funciones, %d sustancias (%.1f s)'
          % (len(m.funcs), len(orden), time.time() - t0))

    ok, fallos = 0, []
    for nombre, ppl, ref in casos(m, E, orden):
        if ppl is None:
            fallos.append('%s: el interprete no ha podido ejecutarlo' % nombre)
        elif compara(nombre, ppl, ref, regiones, fallos):
            ok += 1

    print('\nPASS: %d   FAIL: %d   (%.1f s)'
          % (ok, len(fallos), time.time() - t0))
    for f in fallos[:30]:
        print('  ' + f)
    if len(fallos) > 30:
        print('  ... y %d mas' % (len(fallos) - 30))
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
