# -*- coding: utf-8 -*-
"""HP PPL linter: catches, before you compile, what the Prime's compiler
refuses to explain.

The Prime's compiler prints `syntax error` and points at a line. It does not
say what is wrong with it, so a mistake as small as one variable too many in
a LOCAL statement costs several compile-and-look rounds. Every rule here
comes from an error measured on a real calculator, not from reading a manual.

    hpprime lint FILE.hpprgm [more files or folders...]
    hpprime lint ppl/ --quiet      # errors only, no warnings
    hpprime lint A.txt B.txt --set # also: exported names that would clash
                                   # between files installed side by side

Output is compiler-shaped:  file:line: level: rule: message
Exit code 1 if there is any ERROR.

What this deliberately does NOT flag, because each was checked on hardware
and found legal:

  - RETURN inside a FOR or a REPEAT.
  - locals made of letter + digit (r2, y1, L12).
  - several locals given initial values on one line.

They are listed so nobody "fixes" them back in.
"""
from __future__ import unicode_literals
import io, os, re, sys

# Variables per LOCAL statement. Measured on a G2, firmware 2.4.15515,
# against programs that compile on that same calculator: 8 declared in one
# statement compiles; the functions that failed declared 13, 16 and 18.
# Above 8 is an error; 7-8 is the risky band.
LOCAL_SAFE = 6
LOCAL_MAX = 8

BAD_BLOCK_ENDS = ('ENDIF', 'ENDFOR', 'ENDWHILE', 'ENDCASE', 'ENDPROC',
                  'ENDFUNC')
KEYWORDS = set("""IF THEN ELSE END FOR FROM TO DOWNTO STEP DO WHILE REPEAT
UNTIL CASE DEFAULT BREAK CONTINUE RETURN LOCAL EXPORT BEGIN AND OR NOT
IFTE""".split())

# System functions: a 0 passed to one of these is an argument, not an index.
BUILTINS = set("""RGB MIN MAX ROUND ABS IP FP SIGN SIZE DIM LOG LN EXP SQRT
FLOOR CEILING MOD INT TRUNC RANDOM STRING EXPR TYPE WAIT MSGBOX PRINT INPUT
CHOOSE RECT RECT_P TEXTOUT TEXTOUT_P PIXON PIXOFF LINE FREEZE GETKEY ISKEYDOWN
CONCAT SUB REPLACE INSTRING LEFT RIGHT MID UPPER LOWER ASC CHAR SORT REVERSE
MAKELIST MAKEMAT TRN INVERSE DET IDENMAT ZEROS COS SIN TAN ACOS ASIN ATAN
DEGREE RADIAN SUM PRODUCT""".split())


class Finding(object):
    def __init__(self, path, line, level, rule, msg):
        self.path, self.line = path, line
        self.level, self.rule, self.msg = level, rule, msg

    def __str__(self):
        return '%s:%d: %s: %s: %s' % (self.path, self.line, self.level,
                                      self.rule, self.msg)


def _strip_noise(line):
    """Drop comments and string contents, keeping the quotes.

    This stops rules from firing on text that is only a message for the user.
    Returns the line with its string literals emptied."""
    out, i, n, in_str = [], 0, len(line), False
    while i < n:
        c = line[i]
        if in_str:
            if c == '"':
                in_str = False
                out.append('"')
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append('"')
            i += 1
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out)


def _split_top_level(s):
    """Split on commas that are not inside (), {} or [].

    Brackets and braces matter: EXPORT NAMES:={"a","b","c"}; is ONE variable,
    not three, and counting its commas used to raise a false alarm."""
    parts, depth, cur = [], 0, []
    for c in s:
        if c in '({[':
            depth += 1
        elif c in ')}]':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(c)
    parts.append(''.join(cur))
    return [p.strip() for p in parts if p.strip()]


def _call_args(line, open_idx):
    """The text between a call's parentheses, or None if they do not close on
    this line.

    Lines are judged one at a time, so a call spanning several of them is
    left alone rather than guessed at: a false alarm teaches people to
    ignore the linter."""
    depth = 0
    for i in range(open_idx, len(line)):
        c = line[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return line[open_idx + 1:i]
    return None


def check_source(path, text):
    """-> (list of Finding, list of (exported name, line))."""
    found = []
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    clean = [_strip_noise(l) for l in lines]

    exports = []
    in_body = False         # inside a function's BEGIN ... END
    seen_code = False
    depth = 0

    for k, raw in enumerate(clean):
        num = k + 1
        s = raw.strip()
        if not s:
            continue
        up = s.upper()

        # ---- ENDIF and friends -------------------------------------------
        for bad in BAD_BLOCK_ENDS:
            if re.search(r'\b%s\b' % bad, up):
                found.append(Finding(path, num, 'ERROR', 'single-end',
                                     '%s does not exist in PPL: every block '
                                     'closes with END' % bad))

        # ---- indexing the result of a call --------------------------------
        for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\([^()]*\)\s*\(', raw):
            if m.group(1).upper() not in KEYWORDS:
                found.append(Finding(path, num, 'ERROR', 'index-call',
                                     'cannot index the result of a call '
                                     '(%s(...)(...)): store it first, '
                                     'd := DIM(M); d(1)' % m.group(1)))

        # ---- index 0 into a list or matrix --------------------------------
        for m in re.finditer(r'\b([A-Za-z_]\w*)\s*\(\s*0\s*[,)]', raw):
            if m.group(1).upper() not in KEYWORDS | BUILTINS:
                found.append(Finding(path, num, 'ERROR', 'one-based',
                                     'index 0 into %s: PPL lists and matrices '
                                     'start at 1' % m.group(1)))

        # ---- LOCAL: how many variables, and where -------------------------
        if re.match(r'^LOCAL\b', up):
            body = s[5:].split(';')[0]
            nv = len(_split_top_level(body))
            if nv > LOCAL_MAX:
                found.append(Finding(path, num, 'ERROR', 'local-limit',
                                     '%d variables in one LOCAL; the most '
                                     'seen to compile is %d. Split it into '
                                     'several LOCAL statements of %d'
                                     % (nv, LOCAL_MAX, LOCAL_SAFE)))
            elif nv > LOCAL_SAFE:
                found.append(Finding(path, num, 'WARN', 'local-limit',
                                     '%d variables in one LOCAL: this is the '
                                     'limit (7-8 depending on firmware). '
                                     'Groups of %d are safe'
                                     % (nv, LOCAL_SAFE)))
            if in_body and seen_code:
                found.append(Finding(path, num, 'ERROR', 'local-first',
                                     'LOCAL after code: every local goes '
                                     'together at the top of the BEGIN'))
        elif in_body and not up.startswith('BEGIN'):
            seen_code = True

        # ---- EXPORT with several initialised variables --------------------
        if re.match(r'^EXPORT\b', up) and ':=' in s \
                and '(' not in s.split(':=')[0]:
            chunks = _split_top_level(s[6:].split(';')[0])
            valued = [t for t in chunks if ':=' in t]
            if len(chunks) > 1 and valued:
                found.append(Finding(path, num, 'ERROR', 'export-multiple',
                                     'several variables with initial values '
                                     'in one EXPORT: one declaration per '
                                     'line'))

        # ---- exported names, to cross-check between files -----------------
        m = re.match(r'^EXPORT\s+([A-Za-z_]\w*)', s, re.I)
        if m:
            exports.append((m.group(1), num))

        # ---- = where == or := belongs -------------------------------------
        no_ops = re.sub(r'(<=|>=|==|<>|:=)', '  ', raw)
        if re.search(r'\b(IF|WHILE|UNTIL)\b', up) \
                and re.search(r'[^<>=:]=[^=]', no_ops):
            found.append(Finding(path, num, 'ERROR', 'equality',
                                 'comparison with a single = : PPL compares '
                                 'with == (and assigns with :=)'))

        # ---- EXPR on a variable without checking it is not empty ----------
        for m in re.finditer(r'\bEXPR\s*\(\s*([A-Za-z_]\w*)\s*\)', raw, re.I):
            window = ' '.join(clean[max(0, k - 6):k]).upper()
            if 'SIZE(%s)' % m.group(1).upper() not in window.replace(' ', ''):
                found.append(Finding(path, num, 'WARN', 'expr-empty',
                                     'EXPR(%s) without checking SIZE(%s) > 0 '
                                     'first: EXPR("") fails at run time'
                                     % (m.group(1), m.group(1))))

        # ---- TEXTOUT_P without its width argument -------------------------
        # The trap it guards: text that does not fit raises no error. It is
        # painted over the next column and you never learn what it said.
        #
        # Both forms are judged. Measured on a G2, drawing one long string
        # three times: with no width it runs off the screen, and these two
        # clip it identically --
        #     TEXTOUT_P(txt, x, y, font, colour, width)        6 arguments
        #     TEXTOUT_P(txt, G0, x, y, font, colour, width)    7 arguments
        # so the width is the last argument of whichever form is in use.
        for m in re.finditer(r'\bTEXTOUT_P\s*\(', raw, re.I):
            args = _call_args(raw, m.end() - 1)
            if args is None:
                continue
            parts = _split_top_level(args)
            grob = len(parts) > 1 and re.match(r'^G\d$', parts[1].strip(),
                                               re.I)
            if len(parts) < (7 if grob else 6):
                found.append(Finding(path, num, 'WARN', 'textout-width',
                                     'TEXTOUT_P without its width argument: '
                                     'text that does not fit is painted over '
                                     'the next column, and raises no error'))

        # ---- block balance -------------------------------------------------
        if re.match(r'^BEGIN\b', up):
            in_body, seen_code = True, False
        opens = len(re.findall(r'\bBEGIN\b', up)) \
            + len(re.findall(r'\bTHEN\b', up)) \
            + len(re.findall(r'\bDO\b', up)) \
            + len(re.findall(r'\bCASE\b', up))
        closes = len(re.findall(r'\bEND\b', up))
        depth += opens - closes
        if in_body and depth <= 0:
            in_body = False
        # a function's END without its semicolon
        if re.match(r'^END\s*$', s):
            found.append(Finding(path, num, 'ERROR', 'end-semicolon',
                                 'END without ; at the end: in PPL it is '
                                 'END;'))

    if depth != 0:
        found.append(Finding(path, len(lines), 'ERROR', 'unbalanced',
                             'unclosed blocks: %d openings too many '
                             '(BEGIN/THEN/DO/CASE against END)' % depth))

    return found, exports


def check_files(paths, quiet=False, as_set=False):
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                for f in sorted(fs):
                    if f.endswith(('.hpprgm', '.ppl', '.txt')):
                        files.append(os.path.join(root, f))
        else:
            files.append(p)

    everything, all_exports = [], {}
    for f in files:
        try:
            txt = io.open(f, encoding='utf-8').read()
        except (IOError, UnicodeDecodeError) as e:
            print('%s: cannot read (%s)' % (f, e))
            continue
        found, exports = check_source(os.path.relpath(f), txt)
        everything.extend(found)
        for name, line in exports:
            all_exports.setdefault(name, []).append((os.path.relpath(f), line))

    # The same exported name in two files: they clash as globals. Only with
    # --set, because it is normal to keep variants of the same code that are
    # never installed together. --set is how you say "these do go together".
    for name, places in sorted(all_exports.items()) if as_set else []:
        others = set(s[0] for s in places)
        if len(others) > 1:
            f, l = places[0]
            everything.append(Finding(f, l, 'ERROR', 'export-clash',
                                      '%s is also exported by %s: exported '
                                      'names are global and collide'
                                      % (name,
                                         ', '.join(sorted(others - {f})))))

    errors = [a for a in everything if a.level == 'ERROR']
    warnings = [a for a in everything if a.level != 'ERROR']
    for a in sorted(everything, key=lambda a: (a.path, a.line)):
        if quiet and a.level != 'ERROR':
            continue
        print(str(a))
    print('\n%d file(s): %d error(s), %d warning(s)'
          % (len(files), len(errors), len(warnings)))
    return 1 if errors else 0


def cli(argv):
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    return check_files(args, quiet='--quiet' in argv, as_set='--set' in argv)


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
