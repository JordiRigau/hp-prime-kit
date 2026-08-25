# -*- coding: utf-8 -*-
"""Linter de HP PPL: caza antes de compilar los fallos que el compilador de
la Prime no sabe explicar.

Cada regla viene de un error real, medido en una calculadora, no de leer el
manual. El compilador de la Prime senala una linea y dice "syntax error" sin
mas, asi que un fallo como pasarse de variables en un LOCAL cuesta varias
rondas de compilar-probar. Aqui sale en un segundo.

    python lint_ppl.py fichero.hpprgm [mas ficheros o carpetas...]
    python lint_ppl.py ppl/ --quiet      # solo errores, sin avisos
    python lint_ppl.py A.txt B.txt --set # ademas, choques de nombres entre
                                         # los ficheros que van juntos a la
                                         # calculadora

Salida estilo compilador:  fichero:linea: nivel: regla: mensaje
Codigo de salida 1 si hay algun ERROR.

Lo que NO se marca, porque se comprobo que son falsas alarmas:

  - RETURN dentro de un FOR o un REPEAT: es legal (INTERP.hpprgm lo usa).
  - locales con letra+digito (r2, y1, L12): son legales.
  - varios locales con valor inicial en una linea: es legal.

Estan aqui escritas para que nadie las vuelva a "arreglar".
"""
from __future__ import unicode_literals
import io, os, re, sys

# Limite de variables por sentencia LOCAL. Medido sobre programas que
# compilan en una G2 con firmware 2.4.15515: TRAFOS declara 8 y compila;
# otros tres se quedan en 7. Las funciones que fallaban declaraban 13, 16
# y 18. Por encima de 8 es error; 7-8 es la zona de riesgo.
LOCAL_SEGURO = 6
LOCAL_MAXIMO = 8

BLOQUE_MAL = ('ENDIF', 'ENDFOR', 'ENDWHILE', 'ENDCASE', 'ENDPROC', 'ENDFUNC')
PALABRAS = set("""IF THEN ELSE END FOR FROM TO DOWNTO STEP DO WHILE REPEAT
UNTIL CASE DEFAULT BREAK CONTINUE RETURN LOCAL EXPORT BEGIN AND OR NOT
IFTE""".split())

# Funciones del sistema: llamarlas con un 0 es un argumento, no un indice.
BUILTINS = set("""RGB MIN MAX ROUND ABS IP FP SIGN SIZE DIM LOG LN EXP SQRT
FLOOR CEILING MOD INT TRUNC RANDOM STRING EXPR TYPE WAIT MSGBOX PRINT INPUT
CHOOSE RECT RECT_P TEXTOUT TEXTOUT_P PIXON PIXOFF LINE FREEZE GETKEY ISKEYDOWN
CONCAT SUB REPLACE INSTRING LEFT RIGHT MID UPPER LOWER ASC CHAR SORT REVERSE
MAKELIST MAKEMAT TRN INVERSE DET IDENMAT ZEROS COS SIN TAN ACOS ASIN ATAN
DEGREE RADIAN SUM PRODUCT""".split())


class Aviso(object):
    def __init__(self, fich, linea, nivel, regla, msg):
        self.fich, self.linea = fich, linea
        self.nivel, self.regla, self.msg = nivel, regla, msg

    def __str__(self):
        return '%s:%d: %s: %s: %s' % (self.fich, self.linea, self.nivel,
                                      self.regla, self.msg)


def _limpia(linea):
    """Quita comentarios y contenido de cadenas, dejando las comillas.

    Asi las reglas no se disparan con texto que solo es un mensaje para el
    usuario. Devuelve la linea con los literales vaciados."""
    out, i, n, en_str = [], 0, len(linea), False
    while i < n:
        c = linea[i]
        if en_str:
            if c == '"':
                en_str = False
                out.append('"')
            i += 1
            continue
        if c == '"':
            en_str = True
            out.append('"')
            i += 1
            continue
        if c == '/' and i + 1 < n and linea[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out)


def _corta_nivel_superior(s):
    """Parte por comas que no esten dentro de (), {} ni [].

    Los corchetes y las llaves importan: EXPORT TPROP:={"a","b","c"}; es UNA
    variable, no tres, y contar sus comas daba una falsa alarma."""
    partes, prof, act = [], 0, []
    for c in s:
        if c in '({[':
            prof += 1
        elif c in ')}]':
            prof -= 1
        if c == ',' and prof == 0:
            partes.append(''.join(act))
            act = []
        else:
            act.append(c)
    partes.append(''.join(act))
    return [p.strip() for p in partes if p.strip()]


def revisa(path, texto):
    """-> lista de Aviso."""
    av = []
    fich = path
    lineas = texto.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    limpias = [_limpia(l) for l in lineas]

    exportados = []
    en_cuerpo = False       # dentro de un BEGIN ... END de funcion
    ya_hubo_codigo = False
    profundidad = 0

    for k, cru in enumerate(limpias):
        num = k + 1
        s = cru.strip()
        if not s:
            continue
        may = s.upper()

        # ---- ENDIF y compania -------------------------------------------
        for mal in BLOQUE_MAL:
            if re.search(r'\b%s\b' % mal, may):
                av.append(Aviso(fich, num, 'ERROR', 'end-unico',
                                '%s no existe en PPL: todos los bloques '
                                'cierran con END' % mal))

        # ---- indexar el retorno de una llamada ---------------------------
        for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\([^()]*\)\s*\(', cru):
            if m.group(1).upper() not in PALABRAS:
                av.append(Aviso(fich, num, 'ERROR', 'indexar-llamada',
                                'no se puede indexar el resultado de una '
                                'llamada (%s(...)(...)): guardalo en una '
                                'variable primero, d := DIM(M); d(1)'
                                % m.group(1)))

        # ---- indice 0 en lista o matriz ----------------------------------
        for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(\s*0\s*[,)]', cru):
            if m.group(1).upper() not in PALABRAS | BUILTINS:
                av.append(Aviso(fich, num, 'ERROR', 'base-1',
                                'indice 0 en %s: listas y matrices de PPL '
                                'empiezan en 1' % m.group(1)))

        # ---- LOCAL: numero de variables y posicion ------------------------
        if re.match(r'^LOCAL\b', may):
            cuerpo = s[5:].split(';')[0]
            nv = len(_corta_nivel_superior(cuerpo))
            if nv > LOCAL_MAXIMO:
                av.append(Aviso(fich, num, 'ERROR', 'local-limite',
                                '%d variables en un LOCAL; el maximo que se '
                                'ha visto compilar es %d. Partelo en varias '
                                'sentencias LOCAL de %d'
                                % (nv, LOCAL_MAXIMO, LOCAL_SEGURO)))
            elif nv > LOCAL_SEGURO:
                av.append(Aviso(fich, num, 'AVISO', 'local-limite',
                                '%d variables en un LOCAL: esta en el limite '
                                '(7-8 segun firmware). Mas seguro en grupos '
                                'de %d' % (nv, LOCAL_SEGURO)))
            if en_cuerpo and ya_hubo_codigo:
                av.append(Aviso(fich, num, 'ERROR', 'local-al-principio',
                                'LOCAL despues de codigo: todos los locales '
                                'van juntos al principio del BEGIN'))
        elif en_cuerpo and not may.startswith('BEGIN'):
            ya_hubo_codigo = True

        # ---- EXPORT con varias variables inicializadas --------------------
        if re.match(r'^EXPORT\b', may) and ':=' in s and '(' not in s.split(':=')[0]:
            trozos = _corta_nivel_superior(s[6:].split(';')[0])
            con_valor = [t for t in trozos if ':=' in t]
            if len(trozos) > 1 and con_valor:
                av.append(Aviso(fich, num, 'ERROR', 'export-multiple',
                                'varias variables con valor inicial en un '
                                'solo EXPORT: una declaracion por linea'))

        # ---- nombres exportados, para cruzarlos entre ficheros ------------
        m = re.match(r'^EXPORT\s+([A-Za-z_]\w*)', s, re.I)
        if m:
            exportados.append((m.group(1), num))

        # ---- = donde va == o := ------------------------------------------
        sin_ok = re.sub(r'(<=|>=|==|<>|:=)', '  ', cru)
        if re.search(r'\b(IF|WHILE|UNTIL)\b', may) and re.search(r'[^<>=:]=[^=]', sin_ok):
            av.append(Aviso(fich, num, 'ERROR', 'igualdad',
                            'comparacion con un solo = : en PPL se compara '
                            'con == (y se asigna con :=)'))

        # ---- EXPR sobre una variable sin comprobar que no este vacia ------
        for m in re.finditer(r'\bEXPR\s*\(\s*([A-Za-z_]\w*)\s*\)', cru, re.I):
            ventana = ' '.join(limpias[max(0, k - 6):k]).upper()
            if 'SIZE(%s)' % m.group(1).upper() not in ventana.replace(' ', ''):
                av.append(Aviso(fich, num, 'AVISO', 'expr-vacia',
                                'EXPR(%s) sin comprobar antes SIZE(%s) > 0: '
                                'EXPR("") da error en ejecucion'
                                % (m.group(1), m.group(1))))

        # ---- balance de bloques -------------------------------------------
        if re.match(r'^BEGIN\b', may):
            en_cuerpo, ya_hubo_codigo = True, False
        abre = len(re.findall(r'\bBEGIN\b', may)) \
            + len(re.findall(r'\bTHEN\b', may)) \
            + len(re.findall(r'\bDO\b', may)) \
            + len(re.findall(r'\bCASE\b', may))
        cierra = len(re.findall(r'\bEND\b', may))
        profundidad += abre - cierra
        if en_cuerpo and profundidad <= 0:
            en_cuerpo = False
        # END de funcion sin punto y coma
        if re.match(r'^END\s*$', s):
            av.append(Aviso(fich, num, 'ERROR', 'end-sin-punto-coma',
                            'END sin ; al final: en PPL el END lleva END;'))

    if profundidad != 0:
        av.append(Aviso(fich, len(lineas), 'ERROR', 'bloques',
                        'bloques sin cerrar: sobran %d aperturas '
                        '(BEGIN/THEN/DO/CASE frente a END)' % profundidad))

    return av, exportados


def revisa_ficheros(paths, quiet=False, conjunto=False):
    ficheros = []
    for p in paths:
        if os.path.isdir(p):
            for raiz, _, fs in os.walk(p):
                for f in sorted(fs):
                    if f.endswith(('.hpprgm', '.ppl', '.txt')):
                        ficheros.append(os.path.join(raiz, f))
        else:
            ficheros.append(p)

    todos, expo_global = [], {}
    for f in ficheros:
        try:
            txt = io.open(f, encoding='utf-8').read()
        except (IOError, UnicodeDecodeError) as e:
            print('%s: no se puede leer (%s)' % (f, e))
            continue
        av, expo = revisa(os.path.relpath(f), txt)
        todos.extend(av)
        for nombre, linea in expo:
            expo_global.setdefault(nombre, []).append((os.path.relpath(f), linea))

    # Nombres exportados repetidos entre ficheros: chocan como globales.
    # Solo con --set, porque lo normal es tener variantes del mismo codigo
    # (el fuente y su copia compacta) que nunca se instalan a la vez. Con
    # --set se le pasan los ficheros que SI van juntos a la calculadora.
    for nombre, sitios in sorted(expo_global.items()) if conjunto else []:
        otros = set(s[0] for s in sitios)
        if len(otros) > 1:
            f, l = sitios[0]
            todos.append(Aviso(f, l, 'ERROR', 'export-duplicado',
                               '%s tambien se exporta en %s: los nombres '
                               'exportados son globales y chocan'
                               % (nombre, ', '.join(sorted(otros - {f})))))

    errores = [a for a in todos if a.nivel == 'ERROR']
    avisos = [a for a in todos if a.nivel != 'ERROR']
    for a in sorted(todos, key=lambda a: (a.fich, a.linea)):
        if quiet and a.nivel != 'ERROR':
            continue
        print(str(a))
    print('\n%d fichero(s): %d error(es), %d aviso(s)'
          % (len(ficheros), len(errores), len(avisos)))
    return 1 if errores else 0


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(revisa_ficheros(args, quiet='--quiet' in sys.argv,
                             conjunto='--set' in sys.argv))
