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
    hpprime run PROG.hpprgm [more files...] --call "FN(3,350)"
    hpprime run lib.hpprgm data.hpprgm --call "LOAD(1)" --call "FN(3,350)"

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
        # a name with its app's name in front, Statistics_1Var.MeanX: one
        # token, which the parser turns into a case not covered
        if c.isalpha() or c == '_':
            q = re.match(r'[^\W\d]\w*\.[^\W\d]\w*', text[i:])
            if q and q.group(0).split('.')[0].upper() not in KEYWORDS:
                toks.append(Tok('QID', q.group(0), line))
                i += len(q.group(0))
                continue
        # identifier or keyword. A name can start with a letter outside
        # ASCII: the list has ΣLIST, σX and Mean₁.
        if c.isalpha() or c == '_':
            m = re.match(r'[^\W\d]\w*', text[i:])
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
# statements:  ('local',[(n,e)],[shadowed]) ('assign',target,e) ('if',c,[then],[else])
#              ('case',[(c,body)],default_) ('for',v,init,enders,step,body)
#              ('while',c,body) ('repeat',body,c) ('iferr',a,b,c)
#              ('break',) ('continue',) ('return',e|None) ('expr',e)
#              ('scoped',statement,{names}): a statement whose block has LOCALs


# The keywords that close a block. A statement ends at its semicolon, at one of
# these, or at the end of the file; see Parser.end_statement.
CLOSERS = ('END', 'ELSE', 'UNTIL', 'THEN', 'DEFAULT')

# Operator words, written between their operands. Measured on the Virtual
# Calculator 2.4, build 2025-09-15: 9 MOD 4 answers 1 and MOD(9,4) does not
# compile; 3 NTHROOT 8 answers 2 and NTHROOT(3,8) is refused
# (docs/commands/arithmetic/MOD.md, docs/commands/catalog/NTHROOT.md).
#
# How they bind, measured on 2026-09-24. MOD sits with * and /, left to
# right: 9 MOD 4 + 100 is 101, 2 * 7 MOD 4 is 2, 8 / 2 MOD 3 is 1 and
# 9 MOD 4 / 2 is 0.5; ^ and a minus sign bind tighter (2^3 MOD 5 is 3,
# -9 MOD 4 is 3), and == looser. NTHROOT binds tighter than everything else,
# ^ and the minus sign included, left to right: 2 ^ 3 NTHROOT 8 is 4,
# -3 NTHROOT 8 is -2, 2 NTHROOT 3 NTHROOT 64 is 64 to the power 1/sqrt(3).
INFIX_WORDS = ('MOD', 'NTHROOT')
INFIX_EXAMPLE = {'MOD': '9 MOD 4', 'NTHROOT': '3 NTHROOT 8'}

# The calculator's own variables: A to Z, θ, and the numbered lists, matrices,
# graphics and complex variables. Exporting A, Y or Z did not compile on a G2, on
# 2026-11-05, and the others have not been tried (ppl.export-home-variable).
# tests/test_interp.py holds these two to hpkit/lint.py's.
HOME_VARIABLE = re.compile(r'^([A-Z]|θ|[LMGZ][0-9])$')
EXPORT_REFUSED = ('A', 'Y', 'Z')


class Parser(object):
    def __init__(self, toks, filename='<ppl>'):
        self.t, self.i, self.filename = toks, 0, filename
        self.trailing = None        # why the last statement is not covered
        self.scopes = [set()]       # the LOCALs of each block now open
        self.params = set()         # the parameters of this function
        self.gone = {}              # a nested LOCAL -> the line its block ended
        self.after_block = []       # (name, line, the line its block ended)

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

    def end_statement(self):
        """A statement ends at `;`, at the keyword that closes its block, or
        at the end of the file. Anything else after it is a word this
        interpreter cannot read there -- an operator it lacks, as MOD was --
        and reading that word as the next statement is how `9 MOD 4 + 100`
        once answered 9. It raises instead."""
        if self.at('OP', ';'):
            self.semicolon()
            return
        tk = self.peek()
        if tk.kind == 'EOF' or (tk.kind == 'KW' and tk.val in CLOSERS):
            return
        # The statement is not what it looked like, so it must not run as
        # though it were: statements() replaces it with one that raises when
        # reached, and the rest of the file still loads. Skip to its end.
        self.trailing = ('%s:%d: %r after a complete statement is not '
                         'covered: a statement ends at ; or at the keyword '
                         'that closes its block'
                         % (self.filename, tk.line, tk.val))
        depth = 0
        while not self.at('EOF'):
            t = self.peek()
            if t.kind == 'OP' and t.val in ('(', '{', '['):
                depth += 1
            elif t.kind == 'OP' and t.val in (')', '}', ']'):
                depth -= 1
            elif depth <= 0 and t.kind == 'OP' and t.val == ';':
                self.semicolon()
                return
            elif depth <= 0 and t.kind == 'KW' and t.val in CLOSERS:
                return
            self.i += 1

    def at_end(self):
        """Is the next token the end of the text, a `;`, or a closer?"""
        tk = self.peek()
        return (tk.kind == 'EOF' or (tk.kind == 'OP' and tk.val == ';')
                or (tk.kind == 'KW' and tk.val in CLOSERS))

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
                if self.at('OP', ';'):
                    # Declared ahead, and defined further down: ZPG(); answered
                    # on a G2 on 2026-11-05 (ppl.call-no-parentheses).
                    continue
                body = self.block(params)
                funcs[name] = (params, body)
            else:
                # global variable declaration(s)
                line, valued, count = self.peek().line, 0, 0
                while True:
                    if exported:
                        self.check_exported(name, line)
                    count += 1
                    init = None
                    if self.accept('OP', ':='):
                        init = self.expr()
                        valued += 1
                    globs.append((name, init))
                    if not self.accept('OP', ','):
                        break
                    name = self.take('ID').val
                if exported and count >= 9:
                    # On a G2, on 2026-11-05: 8 with values compile, and 9 do
                    # not, with values or with none (ppl.export-initialised).
                    if valued not in (0, count):
                        raise Unsupported('%s:%d: 9 or more variables in one '
                                          'EXPORT, some with values and some '
                                          'without, have not been measured'
                                          % (self.filename, line))
                    raise PPLError('%s:%d: %d variables in one EXPORT: 9 and '
                                   'more do not compile on the calculator'
                                   % (self.filename, line, count))
                self.semicolon()
            del exported     # everything is visible: there is one namespace
        return funcs, globs

    def check_exported(self, name, line):
        """What is known about exporting one of the calculator's variables."""
        if name in EXPORT_REFUSED:
            raise PPLError('%s:%d: %s is one of Home\'s variables, and exporting '
                           'it does not compile on the calculator'
                           % (self.filename, line, name))
        if HOME_VARIABLE.match(name):
            raise Unsupported('%s:%d: %s is one of the calculator\'s own '
                              'variables, and exporting one has not been '
                              'measured beyond A, Y and Z, which do not compile. '
                              'Prefix it' % (self.filename, line, name))

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

    def block(self, params=()):
        self.scopes, self.gone, self.params = [set(params)], {}, set(params)
        self.take('KW', 'BEGIN')
        body = self.statements(('END',))
        self.take('KW', 'END')
        if not self.at('OP', ';'):
            # Measured on the Virtual Calculator 2.4, build 2025-09-15, on
            # 2026-09-24: a function whose END has no ; does not compile, at
            # the end of the file or before another function
            # (ppl.end-semicolon).
            self._error("the END that closes a function needs its ';': the "
                        'calculator does not compile it without')
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
            s = self.statement()
            if self.trailing is not None:
                s, self.trailing = ('uncovered', self.trailing), None
            out.append(s)
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
            self.end_statement()
            return e if e[0] == 'uncovered' else ('assign', e, value)
        if self.peek().val in ('▶', '=>') and self.peek().kind == 'OP':
            self.i += 1
            target = self.expr()
            self.end_statement()
            return (target if target[0] == 'uncovered'
                    else ('assign', target, e))
        self.end_statement()
        return ('expr', e)

    def _s_local(self):
        line = self.take('KW', 'LOCAL').line
        decls = []
        while True:
            name = self.take('ID').val
            init = self.expr() if self.accept('OP', ':=') else None
            decls.append((name, init))
            if not self.accept('OP', ','):
                break
        if len(decls) >= 9:
            # 9 to 12 failed to compile on the emulator, 13 and more on a G2;
            # 8 compiles (ppl.local-limit).
            self._error('%d variables in one LOCAL: 9 and more do not compile '
                        'on the calculator' % len(decls))
        self.end_statement()
        shadows = []
        for name, _ in decls:
            if len(self.scopes) > 1 and name in self.params:
                return ('uncovered', '%s:%d: a LOCAL in a block that repeats the '
                        'parameter %s has not been measured'
                        % (self.filename, line, name))
            if len(self.scopes) > 1 and any(name in s for s in self.scopes[:-1]):
                shadows.append(name)    # the outer one is back when the block
            self.gone.pop(name, None)   # ends: ppl.local-block-scope
            self.scopes[-1].add(name)
        return ('local', decls, shadows)

    def open_block(self):
        self.scopes.append(set())

    def end_block(self, line):
        """-> the LOCALs of the block that ends on this line
        (ppl.local-block-scope). What uses one after that is held to the file
        as a whole when it has loaded, unless an outer LOCAL of that name is
        back in force."""
        names = self.scopes.pop()
        for name in names:
            if not any(name in s for s in self.scopes):
                self.gone[name] = line
        return names

    def close_block(self, statement):
        names = self.end_block(self.t[self.i - 1].line)
        return ('scoped', statement, names) if names else statement

    def _s_if(self):
        self.take('KW', 'IF')
        cond = self.expr()
        self.take('KW', 'THEN')
        # A THEN and its ELSE are two blocks: a LOCAL of the first read in the
        # second did not compile on a G2 (ppl.local-block-scope).
        self.open_block()
        then_ = self.statements(('ELSE', 'END'))
        names = self.end_block(self.peek().line)
        else_ = []
        if self.accept('KW', 'ELSE'):
            self.open_block()
            else_ = self.statements(('END',))
            names = names | self.end_block(self.peek().line)
        self.take('KW', 'END')
        self.end_statement()
        statement = ('if', cond, then_, else_)
        return ('scoped', statement, names) if names else statement

    def _s_case(self):
        self.take('KW', 'CASE')
        self.open_block()
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
        self.end_statement()
        return self.close_block(('case', branches, default_))

    def _s_for(self):
        self.take('KW', 'FOR')
        self.used(self.peek())
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
        self.open_block()
        body = self.statements(('END',))
        self.take('KW', 'END')
        self.end_statement()
        return self.close_block(('for', var, init, enders, step, direction,
                                 body))

    def _s_while(self):
        self.take('KW', 'WHILE')
        cond = self.expr()
        self.take('KW', 'DO')
        self.open_block()
        body = self.statements(('END',))
        self.take('KW', 'END')
        self.end_statement()
        return self.close_block(('while', cond, body))

    def _s_repeat(self):
        self.take('KW', 'REPEAT')
        self.open_block()
        body = self.statements(('UNTIL',))
        # The condition is already outside the block: a LOCAL of the REPEAT read
        # in its own UNTIL did not compile on a G2 (ppl.local-block-scope).
        names = self.end_block(self.take('KW', 'UNTIL').line)
        cond = self.expr()
        self.end_statement()
        statement = ('repeat', body, cond)
        return ('scoped', statement, names) if names else statement

    def _s_iferr(self):
        self.take('KW', 'IFERR')
        # What it tries is a block of its own: a LOCAL of it read in the THEN did
        # not compile on a G2 (ppl.local-block-scope).
        self.open_block()
        attempt = self.statements(('THEN',))
        names = self.end_block(self.take('KW', 'THEN').line)
        self.open_block()
        on_error = self.statements(('ELSE', 'END'))
        else_ = []
        if self.accept('KW', 'ELSE'):
            else_ = self.statements(('END',))
        names = names | self.end_block(self.peek().line)
        self.take('KW', 'END')
        self.end_statement()
        statement = ('iferr', attempt, on_error, else_)
        return ('scoped', statement, names) if names else statement

    def _s_break(self):
        self.take('KW', 'BREAK')
        levels = None
        if not self.at_end():
            levels = self.expr()
        self.end_statement()
        return ('break', levels)

    def _s_continue(self):
        self.take('KW', 'CONTINUE')
        self.end_statement()
        return ('continue',)

    def _s_return(self):
        self.take('KW', 'RETURN')
        e = None
        if not self.at_end():
            e = self.expr()
        self.end_statement()
        return ('return', e)

    def _s_begin(self):
        # BEGIN opens a function's body and nothing else: a block inside a
        # body does not compile on the calculator. Measured twice on the
        # Virtual Calculator 2.4, build 2025-09-15 -- once when it refused a
        # whole batch at that line, once with a program written for the
        # question -- and this accepted it until then, which is how an entry
        # came to state an example that cannot run. docs/commands/block/
        # BEGIN.md holds the evidence.
        self._error('BEGIN opens a function body; a BEGIN block inside one '
                    'does not compile on the calculator')

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
        while True:
            if self.at('OP') and self.peek().val in ('*', '/'):
                op = self.take('OP').val
            elif self.at('ID') and self.peek().val == 'MOD':
                op = self.take('ID').val
            else:
                break
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
        n = self._root()
        if self.at('OP', '^'):
            self.i += 1
            return ('bin', '^', n, self._unary())   # right-associative
        return n

    def _root(self):
        """a NTHROOT b: tighter than ^ and a minus sign, left to right
        (INFIX_WORDS)."""
        n = self._postfix()
        while self.at('ID') and self.peek().val == 'NTHROOT':
            self.take('ID')
            n = ('bin', 'NTHROOT', n, self._postfix())
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
            n = n if n[0] == 'uncovered' else ('call', n, args)
        return n

    def used(self, tk):
        """A name used: noted if it is a LOCAL whose block has ended."""
        if tk.kind == 'ID' and tk.val in self.gone:
            self.after_block.append((tk.val, tk.line, self.gone[tk.val]))

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
            self.used(tk)
            return ('var', tk.val)
        if tk.kind == 'QID':
            self.i += 1
            return ('uncovered', '%s:%d: %s, a name with its app\'s name in '
                    'front, is not covered' % (self.filename, tk.line,
                                               tk.val))
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
    """PPL passes matrices and lists BY VALUE: a function that writes to what
    it was given does not change the caller's. Copying at the call gives the
    same answers. What it does not reproduce is the cost: on a G2 only a write
    takes longer for a bigger matrix (ppl.matrices-by-value)."""
    if isinstance(v, Matrix):
        return v.copy()
    if isinstance(v, list):
        return list(v)
    return v


def _endless(word):
    return ('a %s has run %d times without finishing. If it is waiting for a '
            'key it never will here: GETKEY always reports "no key pressed" '
            'on the PC, which is what makes a wait loop endless. Run that '
            'part on the calculator.' % (word, LOOP_LIMIT))


# What Python raises when a builtin or an operator is handed something it
# was not written for. None of them is the calculator's verdict, so each
# becomes Unsupported where it is caught, never a traceback.
PYTHON_FAILURES = (TypeError, ValueError, IndexError, KeyError,
                   AttributeError, ZeroDivisionError, OverflowError)


def _kind(v):
    """How a value is named in a message: 'a number', 'a list'..."""
    if isinstance(v, bool) or isinstance(v, (int, float)):
        return 'a number'
    if isinstance(v, str):
        return 'a string'
    if isinstance(v, list):
        return 'a list'
    if isinstance(v, Matrix):
        return 'a matrix'
    return 'a %s' % type(v).__name__


def _nthroot(n, x):
    """n NTHROOT x. Measured on the Virtual Calculator 2.4, build
    2025-09-15: 3 NTHROOT 8 answers 2, 3 NTHROOT (-8) answers -2, the real
    odd root, and 2 NTHROOT (-4) is refused with HComplex at 0, as a reset
    calculator has it. A degree that is not a whole number, or not above 0,
    was not measured."""
    if not (isinstance(n, float) and isinstance(x, float)):
        raise Unsupported('NTHROOT between %s and %s is not covered'
                          % (_kind(n), _kind(x)))
    if n <= 0 or (x < 0 and n != int(n)):
        raise Unsupported('%r NTHROOT %r has not been measured' % (n, x))
    if x < 0:
        if int(n) % 2 == 0:
            raise PPLError('an even root of a negative number is refused while '
                           'HComplex is 0')
        return -((-x) ** (1.0 / n))
    return x ** (1.0 / n)


def _truth(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return v != 0
    if isinstance(v, (list, str)):
        return len(v) > 0
    return v is not None


class _Break(Exception):
    """BREAK [n]: n says how many loops to leave, and defaults to 1.

    The interpreter used to drop the number and leave one loop, so
    BREAK 2 inside two nested loops carried on with the outer body. The
    Virtual Calculator 2.4, build 2025-09-15, left both: the probe in
    docs/commands/results.tsv answers 0, where carrying on would answer 9.
    """

    def __init__(self, levels=1):
        Exception.__init__(self, levels)
        self.levels = levels


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
        self.shadowed = []       # outer LOCALs a nested LOCAL hides for now

    # ------------------------------------------------------------ loading
    def load(self, text, filename='<ppl>'):
        parser = Parser(lex(text), filename)
        funcs, globs = parser.program()
        # A LOCAL used after its block does not compile, unless the name means
        # something else by then, as a global of that name does
        # (ppl.local-block-scope).
        known = set(funcs) | set(n for n, _ in globs) | set(self.funcs) \
            | set(self.globals_)
        for name, line, ended in parser.after_block:
            if name not in known and not HOME_VARIABLE.match(name) \
                    and not _listed(name):
                raise PPLError('%s:%d: %s was declared in a block that ended on '
                               'line %d, and a LOCAL lasts until the end of its '
                               'block. Used after that, it does not compile on '
                               'the calculator'
                               % (filename, line, name, ended))
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
            last = self.run(body, frame)
        except _Return as d:
            return d.value
        # A function that falls off the end answers with the value of the
        # last statement that produced one, and nothing suppresses that.
        # Measured on a G2, one function per ending:
        #     ends in z := 1;                        -> 1
        #     ends in FOR zi FROM 1 TO 2 DO z := zi;  -> 2
        #     ends in an IF that does not run         -> 0, the value before
        #     ends in a call                          -> what the call gave
        #     ends in a bare RETURN;                  -> 0
        return last if last is not None else 0.0

    # ---------------------------------------------------------- execution
    def run(self, statements, frame):
        """-> the value of the last bare expression, or None."""
        last = None
        for s in statements:
            v = self._stmt(s, frame)
            if v is not None:
                last = v
        return last

    def _stmt(self, s, frame):
        kind = s[0]
        if kind == 'uncovered':
            raise Unsupported(s[1])
        if kind == 'scoped':
            mark = len(self.shadowed)
            try:
                return self._stmt(s[1], frame)
            finally:
                for name in s[2]:
                    frame.pop(name, None)
                while len(self.shadowed) > mark:
                    frame.update(self.shadowed.pop())
        if kind == 'local':
            if s[2]:
                self.shadowed.append(dict((n, frame[n]) for n in s[2]
                                          if n in frame))
            for name, init in s[1]:
                frame[name] = (self.evaluate(init, frame) if init is not None
                                 else 0.0)
        elif kind == 'assign':
            # An assignment produces a value: the one assigned. Measured on
            # a G2 -- a function whose body ends in `z := 1;` answers 1.
            value = self.evaluate(s[2], frame)
            self._assign(s[1], value, frame)
            return value
        elif kind == 'expr':
            return self.evaluate(s[1], frame)
        elif kind == 'if':
            if _truth(self.evaluate(s[1], frame)):
                return self.run(s[2], frame)
            return self.run(s[3], frame)
        elif kind == 'case':
            for cond, body in s[1]:
                if _truth(self.evaluate(cond, frame)):
                    return self.run(body, frame)
            if s[2]:
                return self.run(s[2], frame)
        elif kind == 'for':
            _, var, init, enders, step, direction, body = s
            turns = 0
            i = self.evaluate(init, frame)
            limit = self.evaluate(enders, frame)
            inc = self.evaluate(step, frame) if step is not None else 1.0
            inc = abs(inc) * direction
            last = None
            while (inc > 0 and i <= limit) or (inc < 0 and i >= limit):
                turns += 1
                if turns > LOOP_LIMIT:
                    raise Unsupported(_endless('FOR'))
                frame[var] = i
                try:
                    v = self.run(body, frame)
                    if v is not None:
                        last = v
                except _Break as e:
                    if e.levels > 1:        # this loop and the ones outside
                        raise _Break(e.levels - 1)
                    break
                except _Continue:
                    pass
                i = frame[var] + inc   # the body may change the variable
            return last
        elif kind == 'while':
            last, turns = None, 0
            while _truth(self.evaluate(s[1], frame)):
                turns += 1
                if turns > LOOP_LIMIT:
                    raise Unsupported(_endless('WHILE'))
                try:
                    v = self.run(s[2], frame)
                    if v is not None:
                        last = v
                except _Break as e:
                    if e.levels > 1:
                        raise _Break(e.levels - 1)
                    break
                except _Continue:
                    continue
            return last
        elif kind == 'repeat':
            last, turns = None, 0
            while True:
                turns += 1
                if turns > LOOP_LIMIT:
                    raise Unsupported(_endless('REPEAT'))
                try:
                    v = self.run(s[1], frame)
                    if v is not None:
                        last = v
                except _Break as e:
                    if e.levels > 1:
                        raise _Break(e.levels - 1)
                    break
                except _Continue:
                    pass
                if _truth(self.evaluate(s[2], frame)):
                    break
            return last
        elif kind == 'iferr':
            try:
                self.run(s[1], frame)
            except (PPLError, ZeroDivisionError, ValueError, IndexError):
                self.run(s[2], frame)
            else:
                self.run(s[3], frame)
        elif kind == 'break':
            levels = 1 if s[1] is None else int(self.evaluate(s[1], frame))
            raise _Break(max(1, levels))
        elif kind == 'continue':
            raise _Continue()
        elif kind == 'return':
            raise _Return(self.evaluate(s[1], frame) if s[1] is not None
                            else 0.0)
        elif kind == 'block':
            return self.run(s[1], frame)
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
                if 0 in idx:
                    raise Unsupported('%s(%d,%d) := ...: assigning to a matrix '
                                      'with an index of 0 has not been '
                                      'measured' % (name, f, c))
                self._check_range(f, 1, len(container.rows), name)
                self._check_range(c, 1, len(container.rows[0]), name)
                container.rows[f - 1][c - 1] = value
                return
            if isinstance(container, list):
                i = idx[0]
                # Both append. L(0) := v was measured on the Virtual
                # Calculator 2.4, build 2025-09-15: {10,20,30} became
                # {10,20,30,40}.
                if i == len(container) + 1 or i == 0:
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
            if name.upper() in BARE_BUILTINS:
                # GETKEY is written without parentheses in PPL -- it is in
                # the reference and in every example here -- so a bare name
                # has to reach the builtin, not read as a variable.
                return self._builtin(name.upper(), [])
            if _listed(name):
                raise Unsupported('%s is on HP\'s list of names and is not '
                                  'covered' % name)
            raise PPLError('undefined variable: %s' % name)
        if kind == 'seq':
            return [self.evaluate(x, frame) for x in e[1]]
        if kind == 'mat':
            return Matrix([[self.evaluate(x, frame) for x in row]
                           for row in e[1]])
        if kind == 'un':
            v = self.evaluate(e[2], frame)
            if e[1] == '-':
                try:
                    return -v
                except PYTHON_FAILURES:
                    raise Unsupported('a minus sign before %s is not covered'
                                      % _kind(v))
            return 0.0 if _truth(v) else 1.0
        if kind == 'bin':
            return self._bin(e[1], e[2], e[3], frame)
        if kind == 'uncovered':
            raise Unsupported(e[1])
        if kind == 'call':
            return self._call_node(e, frame)
        raise Unsupported('expression %s' % kind)

    def _bin(self, op, ia, ib, frame):
        # AND and OR stop at the side that decides: the other is not
        # evaluated, calls and all. Measured on the Virtual Calculator 2.4,
        # build 2025-09-15, on 2026-10-25 (ppl.short-circuit).
        if op == 'AND':
            return 1.0 if (_truth(self.evaluate(ia, frame)) and
                           _truth(self.evaluate(ib, frame))) else 0.0
        if op == 'OR':
            return 1.0 if (_truth(self.evaluate(ia, frame)) or
                           _truth(self.evaluate(ib, frame))) else 0.0
        a, b = self.evaluate(ia, frame), self.evaluate(ib, frame)
        try:
            return self._arith(op, a, b)
        except PYTHON_FAILURES:
            raise Unsupported('%s between %s and %s is not covered'
                              % (op, _kind(a), _kind(b)))

    def _arith(self, op, a, b):
        if op == 'MOD':
            return self._builtin('MOD', [a, b])
        if op == 'NTHROOT':
            return _nthroot(a, b)
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
        # IFTE is lazy: only the branch that applies is evaluated, as on the
        # Virtual Calculator (ppl.short-circuit)
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
            # 3) an operator word written as a call, which the calculator
            #    refuses at compile time (INFIX_WORDS)
            if name.upper() in INFIX_WORDS:
                if name in INFIX_WORDS:
                    raise PPLError('%s is written between its operands, as in '
                                   '%s: the calculator refuses %s(...) when '
                                   'it compiles' % (name, INFIX_EXAMPLE[name],
                                                    name))
                raise Unsupported('%s is a CAS name: not covered' % name)
            # 4) a system function
            if name.upper() in BUILTINS:
                return self._builtin(name.upper(),
                                     [self.evaluate(a, frame)
                                      for a in arg_nodes])
            if _listed(name):
                raise Unsupported('%s is on HP\'s list of names and is not '
                                  'covered' % name)
            other = _not_hp(name)
            if other is not None and other.origin == 'library':
                raise Unsupported('%s is not one of HP\'s: it belongs to the '
                                  'library %s, whose source is not loaded '
                                  'here' % (name, other.whose))
            if other is not None and other.origin == 'hp':
                raise Unsupported('%s is not on HP\'s list of names and is '
                                  'not covered: %s' % (name, other.whose))
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

    def _builtin(self, name, args):
        """Every builtin is called through here. One that fails on what it
        was given -- CONCAT handed a number, FLOOR a list -- would otherwise
        end the run with a Python traceback; it is a case not covered, and
        says so."""
        try:
            return BUILTINS[name](self, args)
        except PYTHON_FAILURES:
            raise Unsupported('%s given %s is not covered'
                              % (name, ', '.join(_kind(a) for a in args)
                                 or 'nothing'))

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
        if ie[0] == 0 and isinstance(container, list) and container:
            # Measured on the Virtual Calculator 2.4, build 2025-09-15: a
            # list read at 0 answers its LAST element, {10,20,30} gives 30.
            # An empty list, a string and a matrix read at 0 are errors,
            # which _check_range raises.
            return container[-1]
        self._check_range(ie[0], 1, len(container), name)
        if isinstance(container, str):
            # A string indexed answers the character's code, not the
            # character: "abc" at 2 gave 98 on the same build.
            return float(ord(container[ie[0] - 1]))
        return container[ie[0] - 1]


def _as_text(v):
    """A value as STRING writes it.

    A list came out as Python's own repr, [1.0, 2.0], until the Virtual
    Calculator answered {1,3,5,7,9} to the FOR examples of Phase 3
    (docs/commands/results.tsv). That is the shape of divergence this
    interpreter exists to catch, and it was the documentation that caught
    it.

    What a decimal looks like is NOT settled here: this writes Python's
    repr, and what the calculator prints for STRING(1/3) has not been
    measured. A batch will say.
    """
    if isinstance(v, str):
        return v
    if isinstance(v, float) and v == int(v) and abs(v) < 1e15:
        return str(int(v))
    if isinstance(v, list):
        return '{%s}' % ','.join(_as_text(x) for x in v)
    return str(v)


# =================================================================== builtins
# The computing ones are really implemented. The screen and keyboard ones are
# recorded in machine.io and return a neutral value, so a calculation runs
# with no interface and tests can inspect what would have been drawn.

def _b_size(m, a):
    """SIZE(list or string) -> how many; SIZE(matrix) -> its dimensions.

    HP's help: "Returns the number of elements in a list. With a matrix,
    returns the dimensions of the matrix." So a matrix answers {rows, cols},
    the same pair DIM gives -- not rows*cols, which is what this returned
    until the documented example SIZE([[1,2,3],[4,5,6]]) -> [2 3] said
    otherwise. See tests/hp_examples.txt.
    """
    v = a[0]
    if isinstance(v, Matrix):
        f, c = v.dim()
        return [float(f), float(c)]
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
    p = Parser(lex(text), '<EXPR>')
    tree = p.expr()
    if not p.at('EOF'):
        # the rest of the string would be dropped, and half an expression
        # answered as though it were the whole
        raise Unsupported('EXPR: %r after the expression is not covered'
                          % p.peek().val)
    return m.evaluate(tree, {})


def _b_string(m, a):
    """STRING(v) -> the text the calculator writes for v.

    A string comes back QUOTED. The first reading of this was thrown out as
    contaminated -- the harness brings every answer back with STRING of it,
    so STRING("abc") was measured with two of them -- and the clean probe
    settled it the other way: DIM(STRING("abc")) is 5, not 3, so the two
    quotes are part of the answer. Measured on the Virtual Calculator 2.4,
    build 2025-09-15 (docs/commands/results.tsv).

    It belongs here and not in _as_text, which concatenation also uses:
    "a" + 1 is a1, not "a"1.
    """
    v = a[0]
    if isinstance(v, str):
        return '"%s"' % v
    return _as_text(v)


def _b_round(m, a):
    """ROUND(x [, n]) -> x rounded.

    A POSITIVE n is decimal places; a NEGATIVE one is significant figures.
    HP's documented pair makes the difference plain:

        ROUND(7.8676, 2)  -> 7.87      two decimals
        ROUND(7.8676,-2)  -> 7.9       two significant figures

    Reading n as decimals in both cases returned 0.0 for the second, which
    is the shape of mistake this interpreter exists to catch: a wrong number
    rather than a refusal. See tests/hp_examples.txt.
    """
    x = a[0]
    n = int(a[1]) if len(a) > 1 else 0
    if not isinstance(x, float):
        raise Unsupported('ROUND of anything but a number is not covered')
    if n < 0:
        if x == 0.0:
            return 0.0
        # n significant figures: put the leading digit just left of the
        # point, round there, and put the magnitude back.
        digits = -n
        shift = digits - 1 - int(math.floor(math.log10(abs(x))))
        f = 10.0 ** shift
        return math.floor(abs(x) * f + 0.5) / f * (1 if x >= 0 else -1)
    f = 10.0 ** n
    return math.floor(abs(x) * f + 0.5) / f * (1 if x >= 0 else -1)


def _as_matrix(v, who):
    if not isinstance(v, Matrix):
        raise PPLError('%s needs a matrix' % who)
    return v


def _as_string(v, who):
    if not isinstance(v, str):
        raise PPLError('%s needs a string' % who)
    return v


# The string functions, measured on a G2 with examples/strings/SPROBE.txt.
# What is NOT in that measurement raises rather than being extrapolated: a
# guessed edge case would return a value where the calculator returns
# another, which is the divergence this interpreter exists to catch.

def _b_left(m, a):
    """LEFT(s, n) -> the first n characters.

    Measured: LEFT("abcdef",3) = "abc", LEFT("abcdef",99) = "abcdef", and
    -- the trap -- **LEFT("abcdef",0) = "abcdef"**, not "". A count that
    computes to zero gives you everything instead of nothing.

    HP documents that trap, which is worth knowing before treating it as
    folklore: "If n >= DIM(str) or n <= 0, returns the entire string." The
    wording covers a negative count as well, and there it is wrong: the
    Virtual Calculator 2.4, build 2025-09-15, refuses LEFT("abcdef", -1)
    instead of answering the whole string (docs/commands/results.tsv). A
    count of 0 does return everything, in both places.
    """
    s = _as_string(a[0], 'LEFT')
    n = int(round(a[1]))
    if n < 0:
        raise PPLError('LEFT with a negative count')
    if n == 0 or n >= len(s):
        return s
    return s[:n]


def _b_right(m, a):
    """RIGHT(s, n) -> the last n characters.

    Measured, and the same trap as LEFT: RIGHT("abcdef",0) and
    RIGHT("abcdef",99) both give the whole string.

    A negative count is an error, measured on the Virtual Calculator 2.4,
    build 2025-09-15 (docs/commands/results.tsv), the same as LEFT.
    """
    s = _as_string(a[0], 'RIGHT')
    n = int(round(a[1]))
    if n < 0:
        raise PPLError('RIGHT with a negative count')
    if n == 0 or n >= len(s):
        return s
    return s[-n:]


def _b_mid(m, a):
    """MID(s, start [, count]) -> count characters from start, 1-based.

    Measured, all of it:
        MID("abcdef",2,3) = "bcd"   the third argument is a LENGTH
        MID("abcdef",2)   = "bcdef" two arguments means "to the end"
        MID("abcdef",4,99)= "def"   it stops at the end
        MID("abcdef",7,2) = ""      a start past the end is empty
        MID("abcdef",2,0) = ""      a count of zero is empty
        MID("abcdef",0,2) = error   the start is 1-based and must be
        MID("abcdef",9)   = ""      with two arguments too
    Note the asymmetry with LEFT and RIGHT, where 0 means "all".
    """
    if len(a) not in (2, 3):
        raise Unsupported('MID with %d arguments is not measured' % len(a))
    s = _as_string(a[0], 'MID')
    start = int(round(a[1]))
    if start < 1:
        raise PPLError('MID with a start below 1')
    if len(a) == 2:
        return s[start - 1:]
    count = int(round(a[2]))
    if count <= 0 or start > len(s):
        return ''
    return s[start - 1:start - 1 + count]


def _b_instring(m, a):
    """INSTRING(s, sub) -> 1-based position, or 0 if it is not there.

    Measured: "cd" in "abcdef" is 3, "a" is 1, "zz" is 0, and an empty
    second argument is 1.
    """
    s = _as_string(a[0], 'INSTRING')
    sub = _as_string(a[1], 'INSTRING')
    if not sub:
        return 1.0
    return float(s.find(sub) + 1)


def _b_sort(m, a):
    """SORT(list) -> the list in ascending order.

    Measured: SORT({3,1,2}) = {1,2,3} and SORT({"b","a"}) = {"a","b"}.
    A string, and a list mixing numbers with strings, are both errors on
    the calculator. An empty list sorts to an empty list.

    HP documents a second argument -- SORT({"foo","bar","bra"},2) sorts by
    each element's 2nd part -- which is not covered here. It used to be
    accepted and then ignored, which silently gave the 1-argument answer.
    """
    if len(a) > 1:
        raise Unsupported('SORT with a second argument (sort by the nth '
                          'part of each element) is not covered')
    v = a[0]
    if isinstance(v, str):
        raise PPLError('SORT of a string')
    if not isinstance(v, list):
        raise Unsupported('SORT of anything but a list is not measured')
    if not v:
        return []
    if all(isinstance(x, str) for x in v):
        return sorted(v)
    if all(isinstance(x, float) or isinstance(x, int) for x in v):
        return sorted(v)
    raise PPLError('SORT of a list mixing numbers and strings')


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


# Builtins that PPL is written WITHOUT parentheses. Only the ones measured
# that way go here: a name that is not a call on the calculator must not
# become one here.
BARE_BUILTINS = set(['GETKEY'])

_LISTED = None
_OTHERS = None


def _names():
    """hpkit.names, whether this runs inside the kit or on its own."""
    try:
        from hpkit import names
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))))
        from hpkit import names
    return names


def _listed(name):
    """Is `name` on HP's list, docs/commands/names.tsv? A name the calculator
    has and this does not implement is a case not covered, never an
    undefined variable: Xmin answers on the calculator."""
    global _LISTED
    if _LISTED is None:
        _LISTED = _names().known()
    return name.lower() in _LISTED


def _not_hp(name):
    """The row of docs/commands/not-hp.tsv for `name`, or None."""
    global _OTHERS
    if _OTHERS is None:
        _OTHERS = _names().others()
    return _OTHERS.get(name)

# A loop that never ends would hang the tool with no message, and the usual
# way to write one here is not a mistake: a wait loop is correct PPL, and
# GETKEY on the PC always reports "no key pressed", so it can never leave.
# Stopping with a message that names the cause beats spinning.
LOOP_LIMIT = 1000000


def _record(name, ret=0.0):
    def fn(m, a):
        m.io.append((name, a))
        return ret
    return fn


def _minmax(which):
    """MIN and MAX. HP documents three shapes, and all three are here:

        MAX(210,25)          -> 210      two numbers
        MAX({1,8,2})         -> 8        the largest element of one list
        MAX({1,8,2},{2,4,6}) -> {2,8,6}  element by element

    These were `lambda m, a: max(a)`, taken over the ARGUMENT list, so a
    single list argument came back unchanged: a list where the caller
    expects a number, which then flows on without complaint. See
    tests/hp_examples.txt.
    """
    pick = max if which == 'MAX' else min

    def fn(m, a):
        if len(a) == 1:
            v = a[0]
            if not isinstance(v, list):
                raise Unsupported('%s of a single value is not covered'
                                  % which)
            if not v:
                raise PPLError('%s of an empty list' % which)
            if not all(isinstance(x, float) for x in v):
                raise Unsupported('%s over a list that is not all numbers '
                                  'is not covered' % which)
            return pick(v)
        if len(a) == 2 and all(isinstance(x, list) for x in a):
            if len(a[0]) != len(a[1]):
                raise PPLError('%s over two lists of different sizes' % which)
            if not all(isinstance(x, float) for x in a[0] + a[1]):
                raise Unsupported('%s over lists that are not all numbers '
                                  'is not covered' % which)
            return [pick(p, q) for p, q in zip(a[0], a[1])]
        if all(isinstance(x, float) for x in a):
            return pick(a)
        raise Unsupported('%s over these argument types is not covered'
                          % which)

    return fn


def _b_log(m, a):
    """LOG(x) -> base 10.  LOG(x, b) -> base b.

    HP: LOG(8) -> 0.903089986992 and LOG(8,2) -> 3. This was
    `lambda m, a: math.log10(a[0])`, which accepted the second argument and
    ignored it, answering the base-10 log for every base asked for.
    """
    if len(a) == 1:
        return math.log10(a[0])
    if len(a) == 2:
        return math.log(a[0]) / math.log(a[1])
    raise Unsupported('LOG with %d arguments is not covered' % len(a))


def _b_mod(m, a):
    """a MOD b -> the remainder, with the sign of the divisor.

    HP's help for MOD calls it the remainder of the Euclidean division, which
    is never negative. The emulator disagrees for a negative divisor: on the
    Virtual Calculator 2.4, build 2025-09-15, (-9) MOD 4 answered 3 and
    9 MOD (-4) answered -3, which is the floored remainder, the one that takes
    the divisor's sign. A Euclidean one would have given 1. This was the
    Euclidean remainder until those rows came back.
    """
    x, b = a[0], a[1]
    if b == 0:
        raise PPLError('MOD by zero')
    r = math.fmod(x, b)
    if r != 0 and (r < 0) != (b < 0):
        r += b
    return r


BUILTINS = {
    'SIZE': _b_size,
    'DIM': _b_dim,
    'EXPR': _b_expr,
    'STRING': _b_string,
    'ROUND': _b_round,
    'ABS': lambda m, a: abs(a[0]),
    'MIN': _minmax('MIN'),
    'MAX': _minmax('MAX'),
    'IP': lambda m, a: float(int(a[0])),
    'FP': lambda m, a: a[0] - float(int(a[0])),
    'FLOOR': lambda m, a: float(math.floor(a[0])),
    'CEILING': lambda m, a: float(math.ceil(a[0])),
    'SIGN': lambda m, a: float((a[0] > 0) - (a[0] < 0)),
    'SQRT': lambda m, a: math.sqrt(a[0]),
    'LOG': _b_log,
    'LN': lambda m, a: math.log(a[0]),
    'EXP': lambda m, a: math.exp(a[0]),
    'MOD': _b_mod,
    'RGB': lambda m, a: float(int(a[0]) * 65536 + int(a[1]) * 256 + int(a[2])),
    'CONCAT': lambda m, a: list(a[0]) + list(a[1]),
    # strings, measured -- see examples/strings/
    'LEFT': _b_left,
    'RIGHT': _b_right,
    'MID': _b_mid,
    'INSTRING': _b_instring,
    'SORT': _b_sort,
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
    code = _run(files, calls)
    # In a Claude Code session with the kit's settings, note whether this
    # content ran, and whether any call was made: a run with no --call shows
    # only that it loaded, and the end check says so to the person.
    from hpkit import gates
    if gates.enabled():
        for f in files:
            gates.record(f, 'run', code == 0, called=bool(calls))
    return code


def _run(files, calls):
    m = Machine()
    for f in files:
        try:
            m.load_file(f)
        except (PPLError, Unsupported) as e:
            print('%s: ERROR: %s' % (os.path.basename(f), e))
            return 1
        print('loaded %s' % os.path.basename(f))
    print('  %d function(s), %d global(s)' % (len(m.funcs), len(m.globals_)))
    for expr in calls:
        try:
            p = Parser(lex(expr), '<--call>')
            tree = p.expr()
            if not p.at('EOF'):
                # what follows the expression would be dropped, and an answer
                # for half a call is the one thing this must never print
                raise Unsupported('%r after the expression is not covered'
                                  % p.peek().val)
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
