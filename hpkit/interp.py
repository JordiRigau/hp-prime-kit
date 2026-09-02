# -*- coding: utf-8 -*-
"""An HP PPL interpreter in Python: run the real source, on the PC.

What it is for
--------------
Porting code to the calculator to try it there is slow, and tests that
reimplement in Python what the PPL does only catch transcription mistakes.
Here it is **the same .hpprgm file** you install that runs, so what you test
is the code that ships.

Scope
-----
It covers the subset used for computing: numbers, strings, lists, matrices,
IF/CASE/FOR/WHILE/REPEAT/IFERR, EXPORT functions, globals and locals, and
1-based indexing.

Screen and keyboard (TEXTOUT_P, RECT, INPUT, CHOOSE, WAIT, MSGBOX) are not
drawn: each call is recorded in `machine.io` and returns a neutral value, so
the calculation runs without an interface. Anything NOT covered **raises**,
never returns an invented result.

Usage
-----
    hpprime run PROG.hpprgm [more files...] --call "F(3,350)"
    hpprime run lib.hpprgm data.hpprgm --call "LOAD(1)" --call "F(3,350)"

From Python:

    from hpkit import interp
    m = interp.Machine()
    m.load_file('ppl/DATA.hpprgm')
    m.load_file('ppl/LIB.hpprgm')
    m.call('LOAD', 1)
    st = m.call('F', 3.0, 350.0)
"""
from __future__ import unicode_literals
import io, math, os, re, sys


class PPLError(Exception):
    """A run-time error, of the kind the calculator itself would raise."""


class Unsupported(Exception):
    """A construct outside the supported subset. It fails, never guesses."""


# ====================================================================== lexer

KEYWORDS = set("""BEGIN END LOCAL EXPORT IF THEN ELSE CASE DEFAULT FOR FROM TO
DOWNTO STEP DO WHILE REPEAT UNTIL BREAK CONTINUE RETURN IFERR AND OR NOT
XOR""".split())

# Operators, longest first, so that := is not read as : followed by =
OPERATORS = [':=', '==', '<>', '!=', '<=', '>=', '=>', '▶', '&&', '||',
              '+', '-', '*', '/', '^', '<', '>', '(', ')', '{', '}',
              '[', ']', ',', ';', '=']


class Tok(object):
    __slots__ = ('kind', 'val', 'line')

    def __init__(self, kind, val, line):
        self.kind, self.val, self.line = kind, val, line

    def __repr__(self):
        return '%s(%r)@%d' % (self.kind, self.val, self.line)


def lex(text):
    """-> list of Tok. Kinds: NUM STR ID KW OP EOF."""
    toks, i, n, line = [], 0, len(text), 1
    while i < n:
        c = text[i]
        if c == '\n':
            line += 1
            i += 1
            continue
        if c in ' \t\r':
            i += 1
            continue
        # comments
        if text.startswith('//', i):
            j = text.find('\n', i)
            i = n if j < 0 else j
            continue
        if text.startswith('/*', i):
            j = text.find('*/', i + 2)
            if j < 0:
                raise PPLError('line %d: unterminated /* comment' % line)
            line += text.count('\n', i, j)
            i = j + 2
            continue
        # string
        if c == '"':
            j, buf = i + 1, []
            while j < n and text[j] != '"':
                buf.append(text[j])
                j += 1
            if j >= n:
                raise PPLError('line %d: unterminated string' % line)
            toks.append(Tok('STR', ''.join(buf), line))
            i = j + 1
            continue
        # number
        if c.isdigit() or (c == '.' and i + 1 < n and text[i + 1].isdigit()):
            m = re.match(r'\d*\.?\d*(?:[eE][+-]?\d+)?', text[i:])
            raw = m.group(0)
            toks.append(Tok('NUM', float(raw), line))
            i += len(raw)
            continue
        # identifier or keyword
        if c.isalpha() or c == '_':
            m = re.match(r'[A-Za-z_]\w*', text[i:])
            word = m.group(0)
            kind = 'KW' if word.upper() in KEYWORDS else 'ID'
            toks.append(Tok(kind, word.upper() if kind == 'KW' else word,
                            line))
            i += len(word)
            continue
        # operator
        for op in OPERATORS:
            if text.startswith(op, i):
                toks.append(Tok('OP', op, line))
                i += len(op)
                break
        else:
            raise PPLError('line %d: unexpected character %r' % (line, c))
    toks.append(Tok('EOF', None, line))
    return toks


# ====================================================================== nodes
# The tree is made of tuples: (kind, ...). Simple, and enough.

# expressions: ('num',v) ('str',v) ('var',name) ('seq',[e]) ('mat',[[e]])
#              ('bin',op,a,b) ('un',op,a) ('call',name,[args])
# statements:  ('local',[(n,e)]) ('assign',target,e) ('if',c,[then],[else])
#              ('case',[(c,body)],default_) ('for',v,init,enders,step,body)
#              ('while',c,body) ('repeat',body,c) ('iferr',a,b,c)
#              ('break',) ('continue',) ('return',e|None) ('expr',e)


class Parser(object):
    def __init__(self, toks, filename='<ppl>'):
        self.t, self.i, self.filename = toks, 0, filename

    # ------------------------------------------------------------- helpers
    def peek(self, k=0):
        return self.t[min(self.i + k, len(self.t) - 1)]

    def take(self, kind=None, val=None):
        tk = self.peek()
        if kind and tk.kind != kind:
            self._error('expected %s, found %s %r' % (kind, tk.kind, tk.val))
        if val is not None and tk.val != val:
            self._error('expected %r, found %r' % (val, tk.val))
        self.i += 1
        return tk

    def at(self, kind, val=None):
        tk = self.peek()
        return tk.kind == kind and (val is None or tk.val == val)

    def accept(self, kind, val=None):
        if self.at(kind, val):
            self.i += 1
            return True
        return False

    def _error(self, msg):
        tk = self.peek()
        raise PPLError('%s:%d: %s' % (self.filename, tk.line, msg))

    def semicolon(self):
        while self.accept('OP', ';'):
            pass

    # ------------------------------------------------------------ program
    def program(self):
        """-> (functions {name: (params, body)}, globals_ [(name, expr)])"""
        funcs, globs = {}, []
        while not self.at('EOF'):
            self.semicolon()
            if self.at('EOF'):
                break
            exported = self.accept('KW', 'EXPORT')
            if not self.at('ID'):
                self._error('expected a name after EXPORT')
            name = self.take('ID').val
            if self.at('OP', '('):
                params = self.param_list()
                body = self.block()
                funcs[name] = (params, body)
            else:
                # global variable declaration(s)
                while True:
                    init = None
                    if self.accept('OP', ':='):
                        init = self.expr()
                    globs.append((name, init))
                    if not self.accept('OP', ','):
                        break
                    name = self.take('ID').val
                self.semicolon()
            del exported     # everything is visible: there is one namespace
        return funcs, globs

    def param_list(self):
        self.take('OP', '(')
        ps = []
        if not self.at('OP', ')'):
            while True:
                ps.append(self.take('ID').val)
                if not self.accept('OP', ','):
                    break
        self.take('OP', ')')
        return ps

    def block(self):
        self.take('KW', 'BEGIN')
        body = self.statements(('END',))
        self.take('KW', 'END')
        self.semicolon()
        return body

    def statements(self, enders):
        out = []
        while True:
            self.semicolon()
            tk = self.peek()
            if tk.kind == 'EOF':
                break
            if tk.kind == 'KW' and tk.val in enders:
                break
            out.append(self.statement())
        return out

    # ----------------------------------------------------------- statements
    def statement(self):
        tk = self.peek()
        if tk.kind == 'KW':
            method = getattr(self, '_s_' + tk.val.lower(), None)
            if method:
                return method()
            if tk.val in ('END', 'ELSE', 'UNTIL', 'THEN', 'DEFAULT'):
                self._error('unexpected %s' % tk.val)
            raise Unsupported('%s:%d: %s is not supported'
                              % (self.filename, tk.line, tk.val))
        # assignment, or a bare expression
        e = self.expr()
        if self.accept('OP', ':='):
            value = self.expr()
            self.semicolon()
            return ('assign', e, value)
        if self.peek().val in ('▶', '=>') and self.peek().kind == 'OP':
            self.i += 1
            target = self.expr()
            self.semicolon()
            return ('assign', target, e)
        self.semicolon()
        return ('expr', e)

    def _s_local(self):
        self.take('KW', 'LOCAL')
        decls = []
        while True:
            name = self.take('ID').val
            init = self.expr() if self.accept('OP', ':=') else None
            decls.append((name, init))
            if not self.accept('OP', ','):
                break
        self.semicolon()
        return ('local', decls)

    def _s_if(self):
        self.take('KW', 'IF')
        cond = self.expr()
        self.take('KW', 'THEN')
        then_ = self.statements(('ELSE', 'END'))
        else_ = []
        if self.accept('KW', 'ELSE'):
            else_ = self.statements(('END',))
        self.take('KW', 'END')
        self.semicolon()
        return ('if', cond, then_, else_)

    def _s_case(self):
        self.take('KW', 'CASE')
        branches, default_ = [], None
        while True:
            self.semicolon()
            if self.accept('KW', 'IF'):
                cond = self.expr()
                self.take('KW', 'THEN')
                body = self.statements(('END',))
                self.take('KW', 'END')
                self.semicolon()
                branches.append((cond, body))
            elif self.accept('KW', 'DEFAULT'):
                default_ = self.statements(('END',))
            else:
                break
        self.take('KW', 'END')
        self.semicolon()
        return ('case', branches, default_)

    def _s_for(self):
        self.take('KW', 'FOR')
        var = self.take('ID').val
        self.take('KW', 'FROM')
        init = self.expr()
        if self.accept('KW', 'TO'):
            direction = 1
        elif self.accept('KW', 'DOWNTO'):
            direction = -1
        else:
            self._error('expected TO or DOWNTO')
        enders = self.expr()
        step = self.expr() if self.accept('KW', 'STEP') else None
        self.take('KW', 'DO')
        body = self.statements(('END',))
        self.take('KW', 'END')
        self.semicolon()
        return ('for', var, init, enders, step, direction, body)

    def _s_while(self):
        self.take('KW', 'WHILE')
        cond = self.expr()
        self.take('KW', 'DO')
        body = self.statements(('END',))
        self.take('KW', 'END')
        self.semicolon()
        return ('while', cond, body)

    def _s_repeat(self):
        self.take('KW', 'REPEAT')
        body = self.statements(('UNTIL',))
        self.take('KW', 'UNTIL')
        cond = self.expr()
        self.semicolon()
        return ('repeat', body, cond)

    def _s_iferr(self):
        self.take('KW', 'IFERR')
        attempt = self.statements(('THEN',))
        self.take('KW', 'THEN')
        on_error = self.statements(('ELSE', 'END'))
        else_ = []
        if self.accept('KW', 'ELSE'):
            else_ = self.statements(('END',))
        self.take('KW', 'END')
        self.semicolon()
        return ('iferr', attempt, on_error, else_)

    def _s_break(self):
        self.take('KW', 'BREAK')
        self.semicolon()
        return ('break',)

    def _s_continue(self):
        self.take('KW', 'CONTINUE')
        self.semicolon()
        return ('continue',)

    def _s_return(self):
        self.take('KW', 'RETURN')
        e = None
        if not self.at('OP', ';') and not self.at('KW', 'END'):
            e = self.expr()
        self.semicolon()
        return ('return', e)

    def _s_begin(self):
        return ('block', self.block())

    # --------------------------------------------------------- expressions
    def expr(self):
        return self._or_expr()

    def _or_expr(self):
        n = self._and_expr()
        while self.at('KW', 'OR') or self.at('OP', '||'):
            self.i += 1
            n = ('bin', 'OR', n, self._and_expr())
        return n

    def _and_expr(self):
        n = self._not_expr()
        while self.at('KW', 'AND') or self.at('OP', '&&'):
            self.i += 1
            n = ('bin', 'AND', n, self._not_expr())
        return n

    def _not_expr(self):
        if self.accept('KW', 'NOT'):
            return ('un', 'NOT', self._not_expr())
        return self._cmp()

    def _cmp(self):
        n = self._add()
        while self.at('OP') and self.peek().val in ('==', '<>', '!=', '<',
                                                    '<=', '>', '>=', '='):
            op = self.take('OP').val
            if op == '=':
                op = '=='      # the Prime accepts it; the linter warns
            n = ('bin', op, n, self._add())
        return n

    def _add(self):
        n = self._mul()
        while self.at('OP') and self.peek().val in ('+', '-'):
            op = self.take('OP').val
            n = ('bin', op, n, self._mul())
        return n

    def _mul(self):
        n = self._unary()
        while self.at('OP') and self.peek().val in ('*', '/'):
            op = self.take('OP').val
            n = ('bin', op, n, self._unary())
        return n

    def _unary(self):
        if self.at('OP', '-'):
            self.i += 1
            return ('un', '-', self._unary())
        if self.at('OP', '+'):
            self.i += 1
            return self._unary()
        return self._power()

    def _power(self):
        n = self._postfix()
        if self.at('OP', '^'):
            self.i += 1
            return ('bin', '^', n, self._unary())   # right-associative
        return n

    def _postfix(self):
        n = self._primary()
        while self.at('OP', '('):
            self.take('OP', '(')
            args = []
            if not self.at('OP', ')'):
                while True:
                    args.append(self.expr())
                    if not self.accept('OP', ','):
                        break
            self.take('OP', ')')
            n = ('call', n, args)
        return n

    def _primary(self):
        tk = self.peek()
        if tk.kind == 'NUM':
            self.i += 1
            return ('num', tk.val)
        if tk.kind == 'STR':
            self.i += 1
            return ('str', tk.val)
        if tk.kind == 'ID':
            self.i += 1
            return ('var', tk.val)
        if self.at('OP', '('):
            self.i += 1
            e = self.expr()
            self.take('OP', ')')
            return e
        if self.at('OP', '{'):
            self.i += 1
            elems = []
            if not self.at('OP', '}'):
                while True:
                    elems.append(self.expr())
                    if not self.accept('OP', ','):
                        break
            self.take('OP', '}')
            return ('seq', elems)
        if self.at('OP', '['):
            return self._matrix_literal()
        self._error('unexpected expression: %s %r' % (tk.kind, tk.val))

    def _matrix_literal(self):
        self.take('OP', '[')
        rows = []
        if self.at('OP', '['):                 # a matrix of rows
            while True:
                self.take('OP', '[')
                row = []
                if not self.at('OP', ']'):
                    while True:
                        row.append(self.expr())
                        if not self.accept('OP', ','):
                            break
                self.take('OP', ']')
                rows.append(row)
                if not self.accept('OP', ','):
                    break
            self.take('OP', ']')
            return ('mat', rows)
        row = []                              # a plain vector
        if not self.at('OP', ']'):
            while True:
                row.append(self.expr())
                if not self.accept('OP', ','):
                    break
        self.take('OP', ']')
        return ('mat', [row])


# ===================================================================== values

class Matrix(object):
    """A PPL matrix. 1-based: M(i,j) is an element, M(i) a whole row."""
    __slots__ = ('rows',)

    def __init__(self, rows):
        self.rows = rows

    def dim(self):
        return (len(self.rows), len(self.rows[0]) if self.rows else 0)

    def copy(self):
        return Matrix([list(f) for f in self.rows])

    def __repr__(self):
        f, c = self.dim()
        return '<Matrix %dx%d>' % (f, c)


def _copy(v):
    """PPL passes matrices and lists BY VALUE: handing one to a function
    copies it. Reproducing that matters, because it is the reason an engine
    keeps large data in globals instead of passing it as arguments."""
    if isinstance(v, Matrix):
        return v.copy()
    if isinstance(v, list):
        return list(v)
    return v


def _truth(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (list, str)):
        return len(v) > 0
    return v is not None


class _Break(Exception):
    pass


class _Continue(Exception):
    pass


class _Return(Exception):
    def __init__(self, value):
        self.value = value


# ================================================================== machine

class Machine(object):
    def __init__(self):
        self.funcs = {}          # name -> (params, body)
        self.globals_ = {}
        self.io = []             # what the interface would have drawn
        self.last_line = None

    # ------------------------------------------------------------ loading
    def load(self, text, filename='<ppl>'):
        funcs, globs = Parser(lex(text), filename).program()
        self.funcs.update(funcs)
        for name, init in globs:
            self.globals_[name] = (self.evaluate(init, {}) if init is not None
                                     else 0.0)

    def load_file(self, path):
        # utf-8-sig, not utf-8: a source saved by a Windows editor can start
        # with a byte order mark, and the lexer would stop on it.
        text = io.open(path, encoding='utf-8-sig').read()
        self.load(text, os.path.basename(path))

    # ------------------------------------------------------------ calling
    def call(self, name, *args):
        if name not in self.funcs:
            raise PPLError('no such function: %s' % name)
        params, body = self.funcs[name]
        if len(args) != len(params):
            raise PPLError('%s takes %d arguments, got %d'
                           % (name, len(params), len(args)))
        frame = dict(zip(params, [_copy(a) for a in args]))
        try:
            self.run(body, frame)
        except _Return as d:
            return d.value
        return 0.0

    # ---------------------------------------------------------- execution
    def run(self, statements, frame):
        for s in statements:
            self._stmt(s, frame)

    def _stmt(self, s, frame):
        kind = s[0]
        if kind == 'local':
            for name, init in s[1]:
                frame[name] = (self.evaluate(init, frame) if init is not None
                                 else 0.0)
        elif kind == 'assign':
            self._assign(s[1], self.evaluate(s[2], frame), frame)
        elif kind == 'expr':
            self.evaluate(s[1], frame)
        elif kind == 'if':
            if _truth(self.evaluate(s[1], frame)):
                self.run(s[2], frame)
            else:
                self.run(s[3], frame)
        elif kind == 'case':
            for cond, body in s[1]:
                if _truth(self.evaluate(cond, frame)):
                    self.run(body, frame)
                    return
            if s[2]:
                self.run(s[2], frame)
        elif kind == 'for':
            _, var, init, enders, step, direction, body = s
            i = self.evaluate(init, frame)
            limit = self.evaluate(enders, frame)
            inc = self.evaluate(step, frame) if step is not None else 1.0
            inc = abs(inc) * direction
            while (inc > 0 and i <= limit) or (inc < 0 and i >= limit):
                frame[var] = i
                try:
                    self.run(body, frame)
                except _Break:
                    break
                except _Continue:
                    pass
                i = frame[var] + inc   # the body may change the variable
        elif kind == 'while':
            while _truth(self.evaluate(s[1], frame)):
                try:
                    self.run(s[2], frame)
                except _Break:
                    break
                except _Continue:
                    continue
        elif kind == 'repeat':
            while True:
                try:
                    self.run(s[1], frame)
                except _Break:
                    break
                except _Continue:
                    pass
                if _truth(self.evaluate(s[2], frame)):
                    break
        elif kind == 'iferr':
            try:
                self.run(s[1], frame)
            except (PPLError, ZeroDivisionError, ValueError, IndexError):
                self.run(s[2], frame)
            else:
                self.run(s[3], frame)
        elif kind == 'break':
            raise _Break()
        elif kind == 'continue':
            raise _Continue()
        elif kind == 'return':
            raise _Return(self.evaluate(s[1], frame) if s[1] is not None
                            else 0.0)
        elif kind == 'block':
            self.run(s[1], frame)
        else:
            raise Unsupported('statement %s' % kind)

    def _assign(self, target, value, frame):
        if target[0] == 'var':
            name = target[1]
            if name in frame:
                frame[name] = value
            else:
                self.globals_[name] = value
            return
        if target[0] == 'call':          # L(i) := v   or   M(i,j) := v
            base, args = target[1], target[2]
            if base[0] != 'var':
                raise Unsupported('assignment target too complex')
            name = base[1]
            container = frame[name] if name in frame else self.globals_.get(name)
            idx = [int(self.evaluate(a, frame)) for a in args]
            if isinstance(container, Matrix):
                if len(idx) != 2:
                    raise PPLError('a matrix is indexed with two indices')
                f, c = idx
                self._check_range(f, 1, len(container.rows), name)
                self._check_range(c, 1, len(container.rows[0]), name)
                container.rows[f - 1][c - 1] = value
                return
            if isinstance(container, list):
                i = idx[0]
                if i == len(container) + 1:   # append at the end, a PPL idiom
                    container.append(value)
                    return
                self._check_range(i, 1, len(container), name)
                container[i - 1] = value
                return
            raise PPLError('%s is neither a list nor a matrix' % name)
        raise Unsupported('assignment target %s' % target[0])

    @staticmethod
    def _check_range(i, lo, hi, name):
        if not (lo <= i <= hi):
            raise PPLError('index %d out of range in %s (1..%d)'
                           % (i, name, hi))

    # --------------------------------------------------------- evaluation
    def evaluate(self, e, frame):
        kind = e[0]
        if kind == 'num':
            return e[1]
        if kind == 'str':
            return e[1]
        if kind == 'var':
            name = e[1]
            if name in frame:
                return frame[name]
            if name in self.globals_:
                return self.globals_[name]
            if name in self.funcs:            # a call without parentheses
                return self.call(name)
            raise PPLError('undefined variable: %s' % name)
        if kind == 'seq':
            return [self.evaluate(x, frame) for x in e[1]]
        if kind == 'mat':
            return Matrix([[self.evaluate(x, frame) for x in row]
                           for row in e[1]])
        if kind == 'un':
            v = self.evaluate(e[2], frame)
            if e[1] == '-':
                return -v
            return 0.0 if _truth(v) else 1.0
        if kind == 'bin':
            return self._bin(e[1], e[2], e[3], frame)
        if kind == 'call':
            return self._call_node(e, frame)
        raise Unsupported('expression %s' % kind)

    def _bin(self, op, ia, ib, frame):
        if op == 'AND':
            return 1.0 if (_truth(self.evaluate(ia, frame)) and
                           _truth(self.evaluate(ib, frame))) else 0.0
        if op == 'OR':
            return 1.0 if (_truth(self.evaluate(ia, frame)) or
                           _truth(self.evaluate(ib, frame))) else 0.0
        a, b = self.evaluate(ia, frame), self.evaluate(ib, frame)
        if op == '+':
            if isinstance(a, str) or isinstance(b, str):
                return _as_text(a) + _as_text(b)
            if isinstance(a, list) and isinstance(b, list):
                return a + b
            return a + b
        if op == '-':
            return a - b
        if op == '*':
            return a * b
        if op == '/':
            if b == 0:
                raise PPLError('division by zero')
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
        raise Unsupported('operator %s' % op)

    def _call_node(self, e, frame):
        base, arg_nodes = e[1], e[2]
        # IFTE is lazy: only the branch that applies is evaluated
        if base[0] == 'var' and base[1].upper() == 'IFTE' and len(arg_nodes) == 3:
            cond = self.evaluate(arg_nodes[0], frame)
            return self.evaluate(arg_nodes[1] if _truth(cond) else arg_nodes[2], frame)

        # MAKEMAT and MAKELIST are lazy too: their first argument is a
        # TEMPLATE, evaluated once per element with the index variables put
        # into the frame.
        if base[0] == 'var' and base[1].upper() in ('MAKEMAT', 'MAKELIST'):
            return self._build(base[1].upper(), arg_nodes, frame)

        if base[0] == 'var':
            name = base[1]
            # 1) indexing a list or a matrix
            container = frame.get(name, self.globals_.get(name))
            if isinstance(container, (list, Matrix, str)):
                idx = [self.evaluate(a, frame) for a in arg_nodes]
                return self._index(container, idx, name)
            # 2) one of the user's functions
            if name in self.funcs:
                return self.call(name,
                                  *[self.evaluate(a, frame) for a in arg_nodes])
            # 3) a system function
            fn = BUILTINS.get(name.upper())
            if fn is not None:
                return fn(self, [self.evaluate(a, frame) for a in arg_nodes])
            raise PPLError('no such %s (not a variable, not a function, '
                           'not a supported command)' % name)

        # L(2)(1): indexing the result of ANOTHER indexing. The Prime
        # allows it -- those are nested lists -- so it is allowed here too.
        #
        # What is NOT allowed is indexing the result of a CALL, as in
        # SIZE(M)(1): the Prime rejects that at compile time, and letting it
        # through here would return a number where the calculator raises an
        # error -- exactly the kind of divergence this interpreter exists to
        # catch. The linter flags it separately, with the `index-call` rule.
        if base[0] == 'call' and self._is_container(base, frame):
            container = self.evaluate(base, frame)
            if isinstance(container, (list, Matrix, str)):
                return self._index(container, [self.evaluate(a, frame)
                                           for a in arg_nodes], '(nested)')
        raise Unsupported('a call on an expression')

    def _is_container(self, e, frame):
        """Is the base of this indexing a container variable?

        Nothing is evaluated: it walks down to the variable at the bottom
        and checks that it holds a list or a matrix, not a function.
        """
        while e[0] == 'call':
            e = e[1]
        if e[0] != 'var':
            return False
        v = frame.get(e[1], self.globals_.get(e[1]))
        return isinstance(v, (list, Matrix, str))

    def _build(self, which, arg_nodes, frame):
        """MAKEMAT(template, rows, cols) and MAKELIST(template, var,
        first, last [, step]).

        In MAKEMAT the template sees I and J, 1-based, as on the calculator.
        """
        if which == 'MAKEMAT':
            if len(arg_nodes) not in (2, 3):
                raise PPLError('MAKEMAT takes (template, rows [, cols])')
            nrows = int(round(self.evaluate(arg_nodes[1], frame)))
            ncols = int(round(self.evaluate(arg_nodes[2], frame))) if len(arg_nodes) == 3 else nrows
            if nrows < 1 or ncols < 1:
                raise PPLError('MAKEMAT with %dx%d dimensions' % (nrows, ncols))
            scope = dict(frame)
            rows = []
            for i in range(1, nrows + 1):
                row = []
                for j in range(1, ncols + 1):
                    scope['I'], scope['J'] = float(i), float(j)
                    row.append(self.evaluate(arg_nodes[0], scope))
                rows.append(row)
            return Matrix(rows)

        if len(arg_nodes) < 4:
            raise PPLError('MAKELIST takes (template, var, first, last [, step])')
        if arg_nodes[1][0] != 'var':
            raise PPLError('the 2nd argument of MAKELIST is the loop '
                           'variable name')
        name = arg_nodes[1][1]
        de = self.evaluate(arg_nodes[2], frame)
        a = self.evaluate(arg_nodes[3], frame)
        step = self.evaluate(arg_nodes[4], frame) if len(arg_nodes) > 4 else 1.0
        if step == 0:
            raise PPLError('MAKELIST with a step of 0')
        scope = dict(frame)
        out_items, x, n = [], de, 0
        while (x <= a + 1e-12) if step > 0 else (x >= a - 1e-12):
            scope[name] = x
            out_items.append(self.evaluate(arg_nodes[0], scope))
            n += 1
            if n > 1000000:
                raise PPLError('MAKELIST does not terminate')
            x = de + n * step
        return out_items

    def _index(self, container, idx, name):
        ie = [int(round(x)) for x in idx]
        if isinstance(container, Matrix):
            if len(ie) == 2:
                f, c = ie
                self._check_range(f, 1, len(container.rows), name)
                self._check_range(c, 1, len(container.rows[0]), name)
                return container.rows[f - 1][c - 1]
            if len(ie) == 1:
                self._check_range(ie[0], 1, len(container.rows), name)
                return list(container.rows[ie[0] - 1])
            raise PPLError('too many indices for %s' % name)
        if len(ie) != 1:
            raise PPLError('%s is indexed with a single index' % name)
        self._check_range(ie[0], 1, len(container), name)
        return container[ie[0] - 1]


def _as_text(v):
    if isinstance(v, str):
        return v
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return str(v)


# =================================================================== builtins
# The computing ones are really implemented. The screen and keyboard ones are
# recorded in machine.io and return a neutral value, so a calculation runs
# with no interface and tests can inspect what would have been drawn.

def _b_size(m, a):
    v = a[0]
    if isinstance(v, Matrix):
        f, c = v.dim()
        return float(f * c)
    return float(len(v))


def _b_dim(m, a):
    v = a[0]
    if isinstance(v, Matrix):
        f, c = v.dim()
        return [float(f), float(c)]
    return float(len(v))


def _b_expr(m, a):
    text = a[0]
    if not isinstance(text, str) or not text:
        raise PPLError('EXPR on an empty string')
    tree = Parser(lex(text), '<EXPR>').expr()
    return m.evaluate(tree, {})


def _b_string(m, a):
    return _as_text(a[0])


def _b_round(m, a):
    x, n = a[0], int(a[1]) if len(a) > 1 else 0
    f = 10.0 ** n
    return math.floor(abs(x) * f + 0.5) / f * (1 if x >= 0 else -1)


def _as_matrix(v, who):
    if not isinstance(v, Matrix):
        raise PPLError('%s needs a matrix' % who)
    return v


def _b_rref(m, a):
    """Gauss-Jordan with partial pivoting, the one the Prime ships.

    It is here so that leaning on the calculator's own linear algebra does
    not cost you your tests. Without it, the alternative is writing
    Gauss-Jordan by hand in PPL just to keep the core of a solver testable
    off the calculator.
    """
    M = _as_matrix(a[0], 'RREF').copy()
    rows, cols = M.dim()
    row = 0
    for col in range(cols):
        if row >= rows:
            break
        p = max(range(row, rows), key=lambda r: abs(M.rows[r][col]))
        if abs(M.rows[p][col]) < 1e-12:
            continue
        M.rows[row], M.rows[p] = M.rows[p], M.rows[row]
        pivot = M.rows[row][col]
        M.rows[row] = [x / pivot for x in M.rows[row]]
        for r in range(rows):
            if r != row and M.rows[r][col] != 0:
                f = M.rows[r][col]
                M.rows[r] = [x - f * y for x, y in zip(M.rows[r],
                                                        M.rows[row])]
        row += 1
    return M


def _b_trn(m, a):
    M = _as_matrix(a[0], 'TRN')
    f, c = M.dim()
    return Matrix([[M.rows[i][j] for i in range(f)] for j in range(c)])


def _b_idenmat(m, a):
    n = int(round(a[0]))
    if n < 1:
        raise PPLError('IDENMAT(%d)' % n)
    return Matrix([[1.0 if i == j else 0.0 for j in range(n)]
                   for i in range(n)])


def _lu(M, who):
    """Elimination with pivoting. -> (triangular copy, sign, n), or raises."""
    f, c = M.dim()
    if f != c:
        raise PPLError('%s needs a square matrix' % who)
    A = [list(x) for x in M.rows]
    sign = 1.0
    for k in range(f):
        p = max(range(k, f), key=lambda r: abs(A[r][k]))
        if abs(A[p][k]) < 1e-14:
            return A, 0.0, f
        if p != k:
            A[k], A[p] = A[p], A[k]
            sign = -sign
        for r in range(k + 1, f):
            factor = A[r][k] / A[k][k]
            A[r] = [x - factor * y for x, y in zip(A[r], A[k])]
    return A, sign, f


def _b_det(m, a):
    A, sign, n = _lu(_as_matrix(a[0], 'DET'), 'DET')
    if sign == 0.0:
        return 0.0
    d = sign
    for k in range(n):
        d *= A[k][k]
    return d


def _b_inverse(m, a):
    M = _as_matrix(a[0], 'INVERSE')
    f, c = M.dim()
    if f != c:
        raise PPLError('INVERSE needs a square matrix')
    augmented = Matrix([list(M.rows[i]) + [1.0 if i == j else 0.0
                                           for j in range(f)]
                       for i in range(f)])
    R = _b_rref(m, [augmented])
    for i in range(f):
        if abs(R.rows[i][i] - 1.0) > 1e-9:
            raise PPLError('singular matrix: it has no inverse')
    return Matrix([row[f:] for row in R.rows])


def _record(name, ret=0.0):
    def fn(m, a):
        m.io.append((name, a))
        return ret
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
    # linear algebra. MAKEMAT and MAKELIST are not here: they are lazy and
    # handled in _call_node, because their first argument is a template.
    'RREF': _b_rref,
    'TRN': _b_trn,
    'IDENMAT': _b_idenmat,
    'DET': _b_det,
    'INVERSE': _b_inverse,
    # interface: nothing is drawn, every call is recorded
    'TEXTOUT_P': _record('TEXTOUT_P'),
    'TEXTOUT': _record('TEXTOUT'),
    'RECT': _record('RECT'),
    'RECT_P': _record('RECT_P'),
    'PRINT': _record('PRINT'),
    'MSGBOX': _record('MSGBOX'),
    'FREEZE': _record('FREEZE'),
    'WAIT': _record('WAIT', 30.0),      # as if [Enter] had been pressed
    'GETKEY': _record('GETKEY', -1.0),
    'INPUT': _record('INPUT', 1.0),     # as if the form had been accepted
    'CHOOSE': _record('CHOOSE', 1.0),
}


# ======================================================================== CLI

def cli(argv):
    files, calls, skip = [], [], False
    for k, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a == '--call':
            calls.append(argv[k + 1])
            skip = True
        elif not a.startswith('--'):
            files.append(a)
    if not files:
        print(__doc__)
        return 2
    m = Machine()
    for f in files:
        m.load_file(f)
        print('loaded %s' % os.path.basename(f))
    print('  %d function(s), %d global(s)' % (len(m.funcs), len(m.globals_)))
    for expr in calls:
        tree = Parser(lex(expr), '<--call>').expr()
        try:
            r = m.evaluate(tree, {})
        except (PPLError, Unsupported) as e:
            print('%s -> ERROR: %s' % (expr, e))
            return 1
        print('%s -> %s' % (expr, _format(r)))
    return 0


def _format(v):
    if isinstance(v, list):
        return '{' + ', '.join(_format(x) for x in v) + '}'
    if isinstance(v, float):
        return repr(round(v, 10))
    return repr(v)


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
