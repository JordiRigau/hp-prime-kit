# -*- coding: utf-8 -*-
"""Interprete de HP PPL en Python: ejecuta el fuente de verdad, en el PC.

Para que sirve
--------------
Portar codigo a la calculadora y comprobarlo alli es lento, y las pruebas que
reimplementan en Python lo que hace el PPL solo cazan errores de
transcripcion. Aqui se ejecuta **el mismo fichero .hpprgm** que se pega en la
Prime, asi que lo que se prueba es el codigo que se instala.

Alcance
-------
Cubre el subconjunto que se usa para calcular: numeros, cadenas, listas,
matrices, IF/CASE/FOR/WHILE/REPEAT/IFERR, funciones EXPORT, globales y
locales, e indexado 1-based.

Lo de pantalla y teclado (TEXTOUT_P, RECT, INPUT, CHOOSE, WAIT, MSGBOX) no se
dibuja: se registra en `maquina.io` y devuelve valores neutros, para que el
calculo pueda correr sin interfaz. Lo que NO este cubierto **da error**, nunca
un resultado inventado.

Uso
---
    python pplrun.py PROG.hpprgm [mas ficheros...] --call "TPT(3,350)"
    python pplrun.py ppl/TERMOLIB.hpprgm ppl/TDAT_AIGUA.hpprgm \\
        --call "TLOAD(1)" --call "TPT(3,350)"

Desde Python:

    import pplrun
    m = pplrun.Maquina()
    m.carga_fichero('ppl/TDAT_AIGUA.hpprgm')
    m.carga_fichero('ppl/TERMOLIB.hpprgm')
    m.llama('TLOAD', 1)
    st = m.llama('TPT', 3.0, 350.0)
"""
from __future__ import unicode_literals
import io, math, os, re, sys


class ErrorPPL(Exception):
    """Error de ejecucion, como el que daria la calculadora."""


class NoSoportado(Exception):
    """Construccion fuera del subconjunto. Falla en vez de adivinar."""


# ===================================================================== lexico

PALABRAS = set("""BEGIN END LOCAL EXPORT IF THEN ELSE CASE DEFAULT FOR FROM TO
DOWNTO STEP DO WHILE REPEAT UNTIL BREAK CONTINUE RETURN IFERR AND OR NOT
XOR""".split())

# Operadores, los mas largos primero para que := no se lea como : y =
OPERADORES = [':=', '==', '<>', '!=', '<=', '>=', '=>', '▶', '&&', '||',
              '+', '-', '*', '/', '^', '<', '>', '(', ')', '{', '}',
              '[', ']', ',', ';', '=']


class Tok(object):
    __slots__ = ('tipo', 'val', 'linea')

    def __init__(self, tipo, val, linea):
        self.tipo, self.val, self.linea = tipo, val, linea

    def __repr__(self):
        return '%s(%r)@%d' % (self.tipo, self.val, self.linea)


def lex(texto):
    """-> lista de Tok. Tipos: NUM STR ID KW OP FIN."""
    toks, i, n, linea = [], 0, len(texto), 1
    while i < n:
        c = texto[i]
        if c == '\n':
            linea += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue
        # comentarios
        if texto.startswith('//', i):
            j = texto.find('\n', i)
            i = n if j < 0 else j
            continue
        if texto.startswith('/*', i):
            j = texto.find('*/', i + 2)
            if j < 0:
                raise ErrorPPL('linea %d: comentario /* sin cerrar' % linea)
            linea += texto.count('\n', i, j)
            i = j + 2
            continue
        # cadena
        if c == '"':
            j, buf = i + 1, []
            while j < n and texto[j] != '"':
                buf.append(texto[j])
                j += 1
            if j >= n:
                raise ErrorPPL('linea %d: cadena sin cerrar' % linea)
            toks.append(Tok('STR', ''.join(buf), linea))
            i = j + 1
            continue
        # numero
        if c.isdigit() or (c == '.' and i + 1 < n and texto[i + 1].isdigit()):
            m = re.match(r'\d*\.?\d*(?:[eE][+-]?\d+)?', texto[i:])
            crudo = m.group(0)
            toks.append(Tok('NUM', float(crudo), linea))
            i += len(crudo)
            continue
        # identificador o palabra clave
        if c.isalpha() or c == '_':
            m = re.match(r'[A-Za-z_]\w*', texto[i:])
            palabra = m.group(0)
            tipo = 'KW' if palabra.upper() in PALABRAS else 'ID'
            toks.append(Tok(tipo, palabra.upper() if tipo == 'KW' else palabra,
                            linea))
            i += len(palabra)
            continue
        # operador
        for op in OPERADORES:
            if texto.startswith(op, i):
                toks.append(Tok('OP', op, linea))
                i += len(op)
                break
        else:
            raise ErrorPPL('linea %d: caracter inesperado %r' % (linea, c))
    toks.append(Tok('FIN', None, linea))
    return toks


# ====================================================================== nodos
# El arbol son tuplas: (clase, ...). Sencillo y suficiente.

# expresiones: ('num',v) ('str',v) ('var',nombre) ('lista',[e]) ('mat',[[e]])
#              ('bin',op,a,b) ('un',op,a) ('llama',nombre,[args])
# sentencias:  ('local',[(n,e)]) ('asig',destino,e) ('si',c,[then],[else])
#              ('case',[(c,cuerpo)],defecto) ('para',v,ini,fin,paso,cuerpo)
#              ('mientras',c,cuerpo) ('repite',cuerpo,c) ('iferr',a,b,c)
#              ('romper',) ('sigue',) ('devuelve',e|None) ('expr',e)


class Parser(object):
    def __init__(self, toks, fichero='<ppl>'):
        self.t, self.i, self.fichero = toks, 0, fichero

    # -------------------------------------------------------------- utiles
    def mira(self, k=0):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def come(self, tipo=None, val=None):
        tk = self.mira()
        if tipo and tk.tipo != tipo:
            self._error('se esperaba %s y hay %s %r' % (tipo, tk.tipo, tk.val))
        if val is not None and tk.val != val:
            self._error('se esperaba %r y hay %r' % (val, tk.val))
        self.i += 1
        return tk

    def es(self, tipo, val=None):
        tk = self.mira()
        return tk.tipo == tipo and (val is None or tk.val == val)

    def acepta(self, tipo, val=None):
        if self.es(tipo, val):
            self.i += 1
            return True
        return False

    def _error(self, msg):
        tk = self.mira()
        raise ErrorPPL('%s:%d: %s' % (self.fichero, tk.linea, msg))

    def punto_coma(self):
        while self.acepta('OP', ';'):
            pass

    # ------------------------------------------------------------ programa
    def programa(self):
        """-> (funciones {nombre: (params, cuerpo)}, globales [(nombre, expr)])"""
        funcs, globs = {}, []
        while not self.es('FIN'):
            self.punto_coma()
            if self.es('FIN'):
                break
            exportada = self.acepta('KW', 'EXPORT')
            if not self.es('ID'):
                self._error('se esperaba un nombre tras EXPORT')
            nombre = self.come('ID').val
            if self.es('OP', '('):
                params = self.parametros()
                cuerpo = self.bloque()
                funcs[nombre] = (params, cuerpo)
            else:
                # declaracion de variable(s) global(es)
                while True:
                    ini = None
                    if self.acepta('OP', ':='):
                        ini = self.expr()
                    globs.append((nombre, ini))
                    if not self.acepta('OP', ','):
                        break
                    nombre = self.come('ID').val
                self.punto_coma()
            del exportada        # todo es visible: aqui no hay dos espacios
        return funcs, globs

    def parametros(self):
        self.come('OP', '(')
        ps = []
        if not self.es('OP', ')'):
            while True:
                ps.append(self.come('ID').val)
                if not self.acepta('OP', ','):
                    break
        self.come('OP', ')')
        return ps

    def bloque(self):
        self.come('KW', 'BEGIN')
        cuerpo = self.sentencias(('END',))
        self.come('KW', 'END')
        self.punto_coma()
        return cuerpo

    def sentencias(self, fin):
        out = []
        while True:
            self.punto_coma()
            tk = self.mira()
            if tk.tipo == 'FIN':
                break
            if tk.tipo == 'KW' and tk.val in fin:
                break
            out.append(self.sentencia())
        return out

    # ----------------------------------------------------------- sentencias
    def sentencia(self):
        tk = self.mira()
        if tk.tipo == 'KW':
            metodo = getattr(self, '_s_' + tk.val.lower(), None)
            if metodo:
                return metodo()
            if tk.val in ('END', 'ELSE', 'UNTIL', 'THEN', 'DEFAULT'):
                self._error('%s inesperado' % tk.val)
            raise NoSoportado('%s:%d: %s no esta soportado'
                              % (self.fichero, tk.linea, tk.val))
        # asignacion o expresion suelta
        e = self.expr()
        if self.acepta('OP', ':='):
            valor = self.expr()
            self.punto_coma()
            return ('asig', e, valor)
        if self.mira().val in ('▶', '=>') and self.mira().tipo == 'OP':
            self.i += 1
            destino = self.expr()
            self.punto_coma()
            return ('asig', destino, e)
        self.punto_coma()
        return ('expr', e)

    def _s_local(self):
        self.come('KW', 'LOCAL')
        decls = []
        while True:
            nombre = self.come('ID').val
            ini = self.expr() if self.acepta('OP', ':=') else None
            decls.append((nombre, ini))
            if not self.acepta('OP', ','):
                break
        self.punto_coma()
        return ('local', decls)

    def _s_if(self):
        self.come('KW', 'IF')
        cond = self.expr()
        self.come('KW', 'THEN')
        entonces = self.sentencias(('ELSE', 'END'))
        si_no = []
        if self.acepta('KW', 'ELSE'):
            si_no = self.sentencias(('END',))
        self.come('KW', 'END')
        self.punto_coma()
        return ('si', cond, entonces, si_no)

    def _s_case(self):
        self.come('KW', 'CASE')
        ramas, defecto = [], None
        while True:
            self.punto_coma()
            if self.acepta('KW', 'IF'):
                cond = self.expr()
                self.come('KW', 'THEN')
                cuerpo = self.sentencias(('END',))
                self.come('KW', 'END')
                self.punto_coma()
                ramas.append((cond, cuerpo))
            elif self.acepta('KW', 'DEFAULT'):
                defecto = self.sentencias(('END',))
            else:
                break
        self.come('KW', 'END')
        self.punto_coma()
        return ('case', ramas, defecto)

    def _s_for(self):
        self.come('KW', 'FOR')
        var = self.come('ID').val
        self.come('KW', 'FROM')
        ini = self.expr()
        if self.acepta('KW', 'TO'):
            sentido = 1
        elif self.acepta('KW', 'DOWNTO'):
            sentido = -1
        else:
            self._error('se esperaba TO o DOWNTO')
        fin = self.expr()
        paso = self.expr() if self.acepta('KW', 'STEP') else None
        self.come('KW', 'DO')
        cuerpo = self.sentencias(('END',))
        self.come('KW', 'END')
        self.punto_coma()
        return ('para', var, ini, fin, paso, sentido, cuerpo)

    def _s_while(self):
        self.come('KW', 'WHILE')
        cond = self.expr()
        self.come('KW', 'DO')
        cuerpo = self.sentencias(('END',))
        self.come('KW', 'END')
        self.punto_coma()
        return ('mientras', cond, cuerpo)

    def _s_repeat(self):
        self.come('KW', 'REPEAT')
        cuerpo = self.sentencias(('UNTIL',))
        self.come('KW', 'UNTIL')
        cond = self.expr()
        self.punto_coma()
        return ('repite', cuerpo, cond)

    def _s_iferr(self):
        self.come('KW', 'IFERR')
        intenta = self.sentencias(('THEN',))
        self.come('KW', 'THEN')
        captura = self.sentencias(('ELSE', 'END'))
        si_no = []
        if self.acepta('KW', 'ELSE'):
            si_no = self.sentencias(('END',))
        self.come('KW', 'END')
        self.punto_coma()
        return ('iferr', intenta, captura, si_no)

    def _s_break(self):
        self.come('KW', 'BREAK')
        self.punto_coma()
        return ('romper',)

    def _s_continue(self):
        self.come('KW', 'CONTINUE')
        self.punto_coma()
        return ('sigue',)

    def _s_return(self):
        self.come('KW', 'RETURN')
        e = None
        if not self.es('OP', ';') and not self.es('KW', 'END'):
            e = self.expr()
        self.punto_coma()
        return ('devuelve', e)

    def _s_begin(self):
        return ('bloque', self.bloque())

    # ---------------------------------------------------------- expresiones
    def expr(self):
        return self._o()

    def _o(self):
        n = self._y()
        while self.es('KW', 'OR') or self.es('OP', '||'):
            self.i += 1
            n = ('bin', 'OR', n, self._y())
        return n

    def _y(self):
        n = self._no()
        while self.es('KW', 'AND') or self.es('OP', '&&'):
            self.i += 1
            n = ('bin', 'AND', n, self._no())
        return n

    def _no(self):
        if self.acepta('KW', 'NOT'):
            return ('un', 'NOT', self._no())
        return self._cmp()

    def _cmp(self):
        n = self._suma()
        while self.es('OP') and self.mira().val in ('==', '<>', '!=', '<',
                                                    '<=', '>', '>=', '='):
            op = self.come('OP').val
            if op == '=':
                op = '=='          # la Prime lo acepta; el linter ya avisa
            n = ('bin', op, n, self._suma())
        return n

    def _suma(self):
        n = self._prod()
        while self.es('OP') and self.mira().val in ('+', '-'):
            op = self.come('OP').val
            n = ('bin', op, n, self._prod())
        return n

    def _prod(self):
        n = self._unario()
        while self.es('OP') and self.mira().val in ('*', '/'):
            op = self.come('OP').val
            n = ('bin', op, n, self._unario())
        return n

    def _unario(self):
        if self.es('OP', '-'):
            self.i += 1
            return ('un', '-', self._unario())
        if self.es('OP', '+'):
            self.i += 1
            return self._unario()
        return self._pot()

    def _pot(self):
        n = self._sufijo()
        if self.es('OP', '^'):
            self.i += 1
            return ('bin', '^', n, self._unario())   # asociativo por la derecha
        return n

    def _sufijo(self):
        n = self._primario()
        while self.es('OP', '('):
            self.come('OP', '(')
            args = []
            if not self.es('OP', ')'):
                while True:
                    args.append(self.expr())
                    if not self.acepta('OP', ','):
                        break
            self.come('OP', ')')
            n = ('llama', n, args)
        return n

    def _primario(self):
        tk = self.mira()
        if tk.tipo == 'NUM':
            self.i += 1
            return ('num', tk.val)
        if tk.tipo == 'STR':
            self.i += 1
            return ('str', tk.val)
        if tk.tipo == 'ID':
            self.i += 1
            return ('var', tk.val)
        if self.es('OP', '('):
            self.i += 1
            e = self.expr()
            self.come('OP', ')')
            return e
        if self.es('OP', '{'):
            self.i += 1
            elems = []
            if not self.es('OP', '}'):
                while True:
                    elems.append(self.expr())
                    if not self.acepta('OP', ','):
                        break
            self.come('OP', '}')
            return ('lista', elems)
        if self.es('OP', '['):
            return self._matriz()
        self._error('expresion inesperada: %s %r' % (tk.tipo, tk.val))

    def _matriz(self):
        self.come('OP', '[')
        filas = []
        if self.es('OP', '['):                 # matriz de filas
            while True:
                self.come('OP', '[')
                fila = []
                if not self.es('OP', ']'):
                    while True:
                        fila.append(self.expr())
                        if not self.acepta('OP', ','):
                            break
                self.come('OP', ']')
                filas.append(fila)
                if not self.acepta('OP', ','):
                    break
            self.come('OP', ']')
            return ('mat', filas)
        fila = []                              # vector
        if not self.es('OP', ']'):
            while True:
                fila.append(self.expr())
                if not self.acepta('OP', ','):
                    break
        self.come('OP', ']')
        return ('mat', [fila])


# ==================================================================== valores

class Matriz(object):
    """Matriz de PPL. Indices 1-based: M(i,j) elemento, M(i) fila."""
    __slots__ = ('filas',)

    def __init__(self, filas):
        self.filas = filas

    def dim(self):
        return (len(self.filas), len(self.filas[0]) if self.filas else 0)

    def copia(self):
        return Matriz([list(f) for f in self.filas])

    def __repr__(self):
        f, c = self.dim()
        return '<Matriz %dx%d>' % (f, c)


def _copia(v):
    """PPL pasa matrices y listas POR VALOR: al pasarlas a una funcion se
    copian. Reproducirlo importa, porque es la razon de que el motor use
    globales en vez de argumentos para los datos grandes."""
    if isinstance(v, Matriz):
        return v.copia()
    if isinstance(v, list):
        return list(v)
    return v


def _verdad(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (list, str)):
        return len(v) > 0
    return v is not None


class _Romper(Exception):
    pass


class _Seguir(Exception):
    pass


class _Devolver(Exception):
    def __init__(self, valor):
        self.valor = valor


# ================================================================== maquina

class Maquina(object):
    def __init__(self):
        self.funcs = {}          # nombre -> (params, cuerpo)
        self.globales = {}
        self.io = []             # lo que la interfaz habria dibujado
        self.ultima_linea = None

    # ------------------------------------------------------------- cargar
    def carga(self, texto, fichero='<ppl>'):
        funcs, globs = Parser(lex(texto), fichero).programa()
        self.funcs.update(funcs)
        for nombre, ini in globs:
            self.globales[nombre] = (self.evalua(ini, {}) if ini is not None
                                     else 0.0)

    def carga_fichero(self, path):
        texto = io.open(path, encoding='utf-8').read()
        if texto[:1] != '﻿' and not texto.lstrip().startswith(('/', 'E',
                                                                   'e', 'L')):
            pass
        self.carga(texto, os.path.basename(path))

    # ------------------------------------------------------------- llamar
    def llama(self, nombre, *args):
        if nombre not in self.funcs:
            raise ErrorPPL('no existe la funcion %s' % nombre)
        params, cuerpo = self.funcs[nombre]
        if len(args) != len(params):
            raise ErrorPPL('%s espera %d argumentos y recibe %d'
                           % (nombre, len(params), len(args)))
        marco = dict(zip(params, [_copia(a) for a in args]))
        try:
            self.ejecuta(cuerpo, marco)
        except _Devolver as d:
            return d.valor
        return 0.0

    # ---------------------------------------------------------- ejecucion
    def ejecuta(self, sentencias, marco):
        for s in sentencias:
            self._sent(s, marco)

    def _sent(self, s, marco):
        clase = s[0]
        if clase == 'local':
            for nombre, ini in s[1]:
                marco[nombre] = (self.evalua(ini, marco) if ini is not None
                                 else 0.0)
        elif clase == 'asig':
            self._asigna(s[1], self.evalua(s[2], marco), marco)
        elif clase == 'expr':
            self.evalua(s[1], marco)
        elif clase == 'si':
            if _verdad(self.evalua(s[1], marco)):
                self.ejecuta(s[2], marco)
            else:
                self.ejecuta(s[3], marco)
        elif clase == 'case':
            for cond, cuerpo in s[1]:
                if _verdad(self.evalua(cond, marco)):
                    self.ejecuta(cuerpo, marco)
                    return
            if s[2]:
                self.ejecuta(s[2], marco)
        elif clase == 'para':
            _, var, ini, fin, paso, sentido, cuerpo = s
            i = self.evalua(ini, marco)
            tope = self.evalua(fin, marco)
            inc = self.evalua(paso, marco) if paso is not None else 1.0
            inc = abs(inc) * sentido
            while (inc > 0 and i <= tope) or (inc < 0 and i >= tope):
                marco[var] = i
                try:
                    self.ejecuta(cuerpo, marco)
                except _Romper:
                    break
                except _Seguir:
                    pass
                i = marco[var] + inc      # la variable es modificable dentro
        elif clase == 'mientras':
            while _verdad(self.evalua(s[1], marco)):
                try:
                    self.ejecuta(s[2], marco)
                except _Romper:
                    break
                except _Seguir:
                    continue
        elif clase == 'repite':
            while True:
                try:
                    self.ejecuta(s[1], marco)
                except _Romper:
                    break
                except _Seguir:
                    pass
                if _verdad(self.evalua(s[2], marco)):
                    break
        elif clase == 'iferr':
            try:
                self.ejecuta(s[1], marco)
            except (ErrorPPL, ZeroDivisionError, ValueError, IndexError):
                self.ejecuta(s[2], marco)
            else:
                self.ejecuta(s[3], marco)
        elif clase == 'romper':
            raise _Romper()
        elif clase == 'sigue':
            raise _Seguir()
        elif clase == 'devuelve':
            raise _Devolver(self.evalua(s[1], marco) if s[1] is not None
                            else 0.0)
        elif clase == 'bloque':
            self.ejecuta(s[1], marco)
        else:
            raise NoSoportado('sentencia %s' % clase)

    def _asigna(self, destino, valor, marco):
        if destino[0] == 'var':
            nombre = destino[1]
            if nombre in marco:
                marco[nombre] = valor
            else:
                self.globales[nombre] = valor
            return
        if destino[0] == 'llama':          # L(i) := v   o   M(i,j) := v
            base, args = destino[1], destino[2]
            if base[0] != 'var':
                raise NoSoportado('destino de asignacion demasiado complejo')
            nombre = base[1]
            cont = marco[nombre] if nombre in marco else self.globales.get(nombre)
            idx = [int(self.evalua(a, marco)) for a in args]
            if isinstance(cont, Matriz):
                if len(idx) != 2:
                    raise ErrorPPL('una matriz se indexa con dos indices')
                f, c = idx
                self._rango(f, 1, len(cont.filas), nombre)
                self._rango(c, 1, len(cont.filas[0]), nombre)
                cont.filas[f - 1][c - 1] = valor
                return
            if isinstance(cont, list):
                i = idx[0]
                if i == len(cont) + 1:      # anadir al final, idiom de PPL
                    cont.append(valor)
                    return
                self._rango(i, 1, len(cont), nombre)
                cont[i - 1] = valor
                return
            raise ErrorPPL('%s no es lista ni matriz' % nombre)
        raise NoSoportado('destino de asignacion %s' % destino[0])

    @staticmethod
    def _rango(i, lo, hi, nombre):
        if not (lo <= i <= hi):
            raise ErrorPPL('indice %d fuera de rango en %s (1..%d)'
                           % (i, nombre, hi))

    # --------------------------------------------------------- evaluacion
    def evalua(self, e, marco):
        clase = e[0]
        if clase == 'num':
            return e[1]
        if clase == 'str':
            return e[1]
        if clase == 'var':
            nombre = e[1]
            if nombre in marco:
                return marco[nombre]
            if nombre in self.globales:
                return self.globales[nombre]
            if nombre in self.funcs:            # llamada sin parentesis
                return self.llama(nombre)
            raise ErrorPPL('variable no definida: %s' % nombre)
        if clase == 'lista':
            return [self.evalua(x, marco) for x in e[1]]
        if clase == 'mat':
            return Matriz([[self.evalua(x, marco) for x in fila]
                           for fila in e[1]])
        if clase == 'un':
            v = self.evalua(e[2], marco)
            if e[1] == '-':
                return -v
            return 0.0 if _verdad(v) else 1.0
        if clase == 'bin':
            return self._bin(e[1], e[2], e[3], marco)
        if clase == 'llama':
            return self._llamada(e, marco)
        raise NoSoportado('expresion %s' % clase)

    def _bin(self, op, ia, ib, marco):
        if op == 'AND':
            return 1.0 if (_verdad(self.evalua(ia, marco)) and
                           _verdad(self.evalua(ib, marco))) else 0.0
        if op == 'OR':
            return 1.0 if (_verdad(self.evalua(ia, marco)) or
                           _verdad(self.evalua(ib, marco))) else 0.0
        a, b = self.evalua(ia, marco), self.evalua(ib, marco)
        if op == '+':
            if isinstance(a, str) or isinstance(b, str):
                return _txt(a) + _txt(b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            if b == 0:
                raise ErrorPPL('division por cero')
            return a / b
        if op == '^':
            return a ** b
        if op in ('==', '='):
            return 1.0 if a == b else 0.0
        if op in ('<>', '!='):
            return 1.0 if a != b else 0.0
        if op == '<':
            return 1.0 if a < b else 0.0
        if op == '<=':
            return 1.0 if a <= b else 0.0
        if op == '>':
            return 1.0 if a > b else 0.0
        if op == '>=':
            return 1.0 if a >= b else 0.0
        raise NoSoportado('operador %s' % op)

    def _llamada(self, e, marco):
        base, args_n = e[1], e[2]
        # IFTE es perezoso: solo se evalua la rama que toca
        if base[0] == 'var' and base[1].upper() == 'IFTE' and len(args_n) == 3:
            cond = self.evalua(args_n[0], marco)
            return self.evalua(args_n[1] if _verdad(cond) else args_n[2], marco)

        # MAKEMAT y MAKELIST tambien son perezosos: su primer argumento es una
        # PLANTILLA que se evalua una vez por elemento, con las variables del
        # indice puestas en el marco.
        if base[0] == 'var' and base[1].upper() in ('MAKEMAT', 'MAKELIST'):
            return self._construye(base[1].upper(), args_n, marco)

        if base[0] == 'var':
            nombre = base[1]
            # 1) indexar una lista o matriz
            cont = marco.get(nombre, self.globales.get(nombre))
            if isinstance(cont, (list, Matriz, str)):
                idx = [self.evalua(a, marco) for a in args_n]
                return self._indexa(cont, idx, nombre)
            # 2) funcion del usuario
            if nombre in self.funcs:
                return self.llama(nombre,
                                  *[self.evalua(a, marco) for a in args_n])
            # 3) funcion del sistema
            fn = BUILTINS.get(nombre.upper())
            if fn is not None:
                return fn(self, [self.evalua(a, marco) for a in args_n])
            raise ErrorPPL('no existe %s (ni variable, ni funcion, ni '
                           'comando soportado)' % nombre)

        # L(2)(1): indexar el resultado de OTRO indexado. En la Prime vale
        # -son listas anidadas- asi que aqui tambien.
        #
        # Lo que NO se admite es indexar el resultado de una LLAMADA, del
        # estilo SIZE(M)(1): eso la Prime lo rechaza al compilar, y dejarlo
        # pasar aqui daria un numero donde la calculadora da un error, que es
        # justo la divergencia que este interprete existe para cazar. El
        # linter lo marca aparte, con la regla `indexar-llamada`.
        if base[0] == 'llama' and self._es_contenedor(base, marco):
            cont = self.evalua(base, marco)
            if isinstance(cont, (list, Matriz, str)):
                return self._indexa(cont, [self.evalua(a, marco)
                                           for a in args_n], '(anidado)')
        raise NoSoportado('llamada sobre una expresion')

    def _es_contenedor(self, e, marco):
        """La base de este indexado, es una variable de tipo contenedor?

        Se mira sin evaluar nada: se baja hasta la variable del fondo y se
        comprueba que sea una lista o una matriz, no una funcion.
        """
        while e[0] == 'llama':
            e = e[1]
        if e[0] != 'var':
            return False
        v = marco.get(e[1], self.globales.get(e[1]))
        return isinstance(v, (list, Matriz, str))

    def _construye(self, cual, args_n, marco):
        """MAKEMAT(plantilla, filas, cols) y MAKELIST(plantilla, var, de, a
        [, paso]).

        En MAKEMAT la plantilla ve I y J, 1-based, como en la calculadora.
        """
        if cual == 'MAKEMAT':
            if len(args_n) not in (2, 3):
                raise ErrorPPL('MAKEMAT lleva (plantilla, filas [, cols])')
            nf = int(round(self.evalua(args_n[1], marco)))
            nc = int(round(self.evalua(args_n[2], marco))) if len(args_n) == 3 else nf
            if nf < 1 or nc < 1:
                raise ErrorPPL('MAKEMAT con dimensiones %dx%d' % (nf, nc))
            hijo = dict(marco)
            filas = []
            for i in range(1, nf + 1):
                fila = []
                for j in range(1, nc + 1):
                    hijo['I'], hijo['J'] = float(i), float(j)
                    fila.append(self.evalua(args_n[0], hijo))
                filas.append(fila)
            return Matriz(filas)

        if len(args_n) < 4:
            raise ErrorPPL('MAKELIST lleva (plantilla, var, de, a [, paso])')
        if args_n[1][0] != 'var':
            raise ErrorPPL('el 2o argumento de MAKELIST es el nombre de la '
                           'variable del bucle')
        nombre = args_n[1][1]
        de = self.evalua(args_n[2], marco)
        a = self.evalua(args_n[3], marco)
        paso = self.evalua(args_n[4], marco) if len(args_n) > 4 else 1.0
        if paso == 0:
            raise ErrorPPL('MAKELIST con paso 0')
        hijo = dict(marco)
        fuera, x, n = [], de, 0
        while (x <= a + 1e-12) if paso > 0 else (x >= a - 1e-12):
            hijo[nombre] = x
            fuera.append(self.evalua(args_n[0], hijo))
            n += 1
            if n > 1000000:
                raise ErrorPPL('MAKELIST no termina')
            x = de + n * paso
        return fuera

    def _indexa(self, cont, idx, nombre):
        ie = [int(round(x)) for x in idx]
        if isinstance(cont, Matriz):
            if len(ie) == 2:
                f, c = ie
                self._rango(f, 1, len(cont.filas), nombre)
                self._rango(c, 1, len(cont.filas[0]), nombre)
                return cont.filas[f - 1][c - 1]
            if len(ie) == 1:
                self._rango(ie[0], 1, len(cont.filas), nombre)
                return list(cont.filas[ie[0] - 1])
            raise ErrorPPL('indices de mas en %s' % nombre)
        if len(ie) != 1:
            raise ErrorPPL('%s se indexa con un solo indice' % nombre)
        self._rango(ie[0], 1, len(cont), nombre)
        return cont[ie[0] - 1]


def _txt(v):
    if isinstance(v, str):
        return v
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return str(v)


# =================================================================== builtins
# Lo de calculo se implementa de verdad. Lo de pantalla y teclado se registra
# en maquina.io y devuelve un valor neutro: asi el calculo corre sin interfaz
# y las pruebas pueden mirar que se habria dibujado.

def _b_size(m, a):
    v = a[0]
    if isinstance(v, Matriz):
        f, c = v.dim()
        return float(f * c)
    return float(len(v))


def _b_dim(m, a):
    v = a[0]
    if isinstance(v, Matriz):
        f, c = v.dim()
        return [float(f), float(c)]
    return float(len(v))


def _b_expr(m, a):
    texto = a[0]
    if not isinstance(texto, str) or not texto:
        raise ErrorPPL('EXPR sobre una cadena vacia')
    arbol = Parser(lex(texto), '<EXPR>').expr()
    return m.evalua(arbol, {})


def _b_string(m, a):
    return _txt(a[0])


def _b_round(m, a):
    x, n = a[0], int(a[1]) if len(a) > 1 else 0
    f = 10.0 ** n
    return math.floor(abs(x) * f + 0.5) / f * (1 if x >= 0 else -1)


def _mat(v, quien):
    if not isinstance(v, Matriz):
        raise ErrorPPL('%s necesita una matriz' % quien)
    return v


def _b_rref(m, a):
    """Gauss-Jordan con pivoteo parcial. Es la que la Prime trae de fabrica.

    Estaba sin cubrir, y su ausencia AQUI tenia consecuencias alla: en
    CiclesHP se escribio el Gauss-Jordan a mano en PPL, cuarenta lineas, para
    no dejar la pieza central del solver sin poder probarse fuera de la
    calculadora. Ahora RREF se puede usar y seguir probando.
    """
    M = _mat(a[0], 'RREF').copia()
    filas, cols = M.dim()
    fila = 0
    for col in range(cols):
        if fila >= filas:
            break
        p = max(range(fila, filas), key=lambda r: abs(M.filas[r][col]))
        if abs(M.filas[p][col]) < 1e-12:
            continue
        M.filas[fila], M.filas[p] = M.filas[p], M.filas[fila]
        piv = M.filas[fila][col]
        M.filas[fila] = [x / piv for x in M.filas[fila]]
        for r in range(filas):
            if r != fila and M.filas[r][col] != 0:
                f = M.filas[r][col]
                M.filas[r] = [x - f * y for x, y in zip(M.filas[r],
                                                        M.filas[fila])]
        fila += 1
    return M


def _b_trn(m, a):
    M = _mat(a[0], 'TRN')
    f, c = M.dim()
    return Matriz([[M.filas[i][j] for i in range(f)] for j in range(c)])


def _b_idenmat(m, a):
    n = int(round(a[0]))
    if n < 1:
        raise ErrorPPL('IDENMAT(%d)' % n)
    return Matriz([[1.0 if i == j else 0.0 for j in range(n)]
                   for i in range(n)])


def _lu(M, quien):
    """Eliminacion con pivoteo. -> (copia triangular, signo, n) o error."""
    f, c = M.dim()
    if f != c:
        raise ErrorPPL('%s necesita una matriz cuadrada' % quien)
    A = [list(x) for x in M.filas]
    signo = 1.0
    for k in range(f):
        p = max(range(k, f), key=lambda r: abs(A[r][k]))
        if abs(A[p][k]) < 1e-14:
            return A, 0.0, f
        if p != k:
            A[k], A[p] = A[p], A[k]
            signo = -signo
        for r in range(k + 1, f):
            factor = A[r][k] / A[k][k]
            A[r] = [x - factor * y for x, y in zip(A[r], A[k])]
    return A, signo, f


def _b_det(m, a):
    A, signo, n = _lu(_mat(a[0], 'DET'), 'DET')
    if signo == 0.0:
        return 0.0
    d = signo
    for k in range(n):
        d *= A[k][k]
    return d


def _b_inverse(m, a):
    M = _mat(a[0], 'INVERSE')
    f, c = M.dim()
    if f != c:
        raise ErrorPPL('INVERSE necesita una matriz cuadrada')
    ampliada = Matriz([list(M.filas[i]) + [1.0 if i == j else 0.0
                                           for j in range(f)]
                       for i in range(f)])
    R = _b_rref(m, [ampliada])
    for i in range(f):
        if abs(R.filas[i][i] - 1.0) > 1e-9:
            raise ErrorPPL('matriz singular: no tiene inversa')
    return Matriz([fila[f:] for fila in R.filas])


def _registra(nombre, retorno=0.0):
    def fn(m, a):
        m.io.append((nombre, a))
        return retorno
    return fn


BUILTINS = {
    'SIZE': _b_size,
    'DIM': _b_dim,
    'EXPR': _b_expr,
    'STRING': _b_string,
    'ROUND': _b_round,
    'ABS': lambda m, a: abs(a[0]),
    'MIN': lambda m, a: min(a),
    'MAX': lambda m, a: max(a),
    'IP': lambda m, a: float(int(a[0])),
    'FP': lambda m, a: a[0] - float(int(a[0])),
    'FLOOR': lambda m, a: float(math.floor(a[0])),
    'CEILING': lambda m, a: float(math.ceil(a[0])),
    'SIGN': lambda m, a: float((a[0] > 0) - (a[0] < 0)),
    'SQRT': lambda m, a: math.sqrt(a[0]),
    'LOG': lambda m, a: math.log10(a[0]),
    'LN': lambda m, a: math.log(a[0]),
    'EXP': lambda m, a: math.exp(a[0]),
    'MOD': lambda m, a: math.fmod(a[0], a[1]),
    'RGB': lambda m, a: float(int(a[0]) * 65536 + int(a[1]) * 256 + int(a[2])),
    'CONCAT': lambda m, a: list(a[0]) + list(a[1]),
    # algebra matricial. MAKEMAT y MAKELIST no estan aqui: son perezosas y
    # se resuelven en _llamada, porque su primer argumento es una plantilla.
    'RREF': _b_rref,
    'TRN': _b_trn,
    'IDENMAT': _b_idenmat,
    'DET': _b_det,
    'INVERSE': _b_inverse,
    # interfaz: no se dibuja, se anota
    'TEXTOUT_P': _registra('TEXTOUT_P'),
    'TEXTOUT': _registra('TEXTOUT'),
    'RECT': _registra('RECT'),
    'RECT_P': _registra('RECT_P'),
    'PRINT': _registra('PRINT'),
    'MSGBOX': _registra('MSGBOX'),
    'FREEZE': _registra('FREEZE'),
    'WAIT': _registra('WAIT', 30.0),      # como si se pulsara [Enter]
    'GETKEY': _registra('GETKEY', -1.0),
    'INPUT': _registra('INPUT', 1.0),     # como si se aceptara el formulario
    'CHOOSE': _registra('CHOOSE', 1.0),
}


# ======================================================================== CLI

def _cli(argv):
    ficheros, llamadas, saltar = [], [], False
    for k, a in enumerate(argv[1:], 1):
        if saltar:
            saltar = False
            continue
        if a == '--call':
            llamadas.append(argv[k + 1])
            saltar = True
        elif not a.startswith('--'):
            ficheros.append(a)
    if not ficheros:
        print(__doc__)
        return 2
    m = Maquina()
    for f in ficheros:
        m.carga_fichero(f)
        print('cargado %s' % os.path.basename(f))
    print('  %d funciones, %d globales' % (len(m.funcs), len(m.globales)))
    for expr in llamadas:
        arbol = Parser(lex(expr), '<--call>').expr()
        try:
            r = m.evalua(arbol, {})
        except (ErrorPPL, NoSoportado) as e:
            print('%s -> ERROR: %s' % (expr, e))
            return 1
        print('%s -> %s' % (expr, _fmt(r)))
    return 0


def _fmt(v):
    if isinstance(v, list):
        return '{' + ', '.join(_fmt(x) for x in v) + '}'
    if isinstance(v, float):
        return repr(round(v, 10))
    return repr(v)


if __name__ == '__main__':
    sys.exit(_cli(sys.argv))
