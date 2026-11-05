# -*- coding: utf-8 -*-
"""Run the documentation's examples on the Virtual Calculator, and keep what
it answers.

    hpprime examples LEFT RIGHT          these entries' examples, one batch
    hpprime examples --all               every entry's examples
    hpprime examples ... --probe E=CALL  also a call no entry states yet
    hpprime examples --collect           read a batch not waited for
    hpprime examples ... --replace       let a different answer replace the
                                         row results.tsv already holds
    hpprime examples --relabel           HP help and unverified become
                                         emulator where the stored answer
                                         agrees
    hpprime examples --compile FILE      does each program in FILE compile?

A question a batch cannot ask -- does this compile? -- goes in a file of small
programs, each headed `[fact-or-entry] NAME`. They are put on the same
throwaway calculator with two controls, one that compiles and one that does
not; you press Check on each, run HPKDOC and close the window, and each
program's file says whether it compiled: the calculator writes a compiled
block into it when it does. If the controls do not come out as they must,
nothing is concluded and nothing is stored.

The interpreter is checked against the documentation; this checks the
documentation against the calculator's own firmware. Each example becomes
one call in a generated program, HPKDOC, which runs on a throwaway
calculator, Prime_1, cloned from the one you use and reset before every
batch. Every answer comes back through the matrix M9 -- numbers, text,
lists, matrices, and a refusal -- together with what the calculator reports
as its version.

Two things are yours to do, because nothing on the Prime starts a program on
its own: in the emulator that opens, compile HPKDOC once (a program copied
as a file is not live on Home until it has been checked: deploy.md section
1), run it, and close that window. The command prints the keys and waits.

Which calculator an emulator opens is the emulator's choice, not the kit's:
the first window opens Prime, the second Prime_1, and no window opens a
calculator with any other name (deploy.md section 1). So this launches only
when the next window will be Prime_1, which means your own calculator open
in another, and when that window closes, the saved state of Prime_1 has to
have moved, or nothing is read. A Prime_1 the kit did not make is moved
into the kit's own folder, never deleted.
"""
from __future__ import unicode_literals
import io, json, os, re, shutil, subprocess, sys, time
from collections import OrderedDict

NAME = 'HPKDOC'         # the generated program
# The throwaway calculator. Its name is the emulator's choice: with your own
# calculator open in one window, a second window opens Prime_1 and nothing
# else (deploy.md section 1).
CALC = 'Prime_1'
MAT = 9                 # the matrix that carries the answers back
WIDTH = 160             # characters of an answer's text brought back
HEAD = 4                # answered, TYPE, the number, the text's length
RESULTS = ('docs', 'commands', 'results.tsv')
FIELDS = ('entry', 'call', 'answer', 'type', 'firmware', 'date')
ERROR = '*error*'
# An answer whose cells the decoder could not read. It is reported and never
# stored: what it was is not known.
UNREADABLE = '*unreadable*'

# What a compile question can answer, and its two controls. ZCBAD fails with
# ENDIF, measured to fail on a G2 (ppl.no-end-keywords); ZCOK is the smallest
# function there is.
COMPILES = '*compiles*'
REFUSED = '*does not compile*'
CONTROL = 'control'
CONTROLS = (('ZCOK', 'EXPORT ZCOK()\nBEGIN\n  RETURN 1;\nEND;\n', True),
            ('ZCBAD', 'EXPORT ZCBAD()\nBEGIN\n  IF 1 THEN RETURN 1; ENDIF;'
                      '\n  RETURN 0;\nEND;\n', False))

# Names whose answer belongs to the machine and is not kept. SERIAL answers
# the calculator's serial number, and results.tsv is committed and published.
# The answer is discarded where the row is built, which is also where the
# report takes its copy from, so one line closes both. A name here still gets
# an entry: what the command answers is documented, what it answered is not.
# Names whose answer is never kept. SERIAL is the obvious one. VERSION is
# here because its answer carries the serial number too: the firmware a row
# is stamped with goes through firmware(), which drops that line, but a case
# whose entry is VERSION would take the ordinary path straight into the file.
NEVER_STORED = ('SERIAL', 'VERSION')
NOT_STORED = '(not stored)'

# What TYPE answers, from HP's help. Unverified against 2.4.15515 until a
# batch has read it back; results.tsv keeps the number, not this name.
TYPES = {0: 'real', 1: 'integer', 2: 'string', 3: 'complex', 4: 'matrix',
         5: 'error', 6: 'list', 8: 'function', 9: 'unit'}


class ExamplesError(Exception):
    pass


class Case(object):
    """One call to run: an entry's example, or a probe no entry states."""

    def __init__(self, entry, call, stated=None, label=None):
        self.entry = entry
        self.call = call
        self.stated = stated        # as the entry writes it; ERROR; None
        self.label = label

    def as_dict(self):
        return {'entry': self.entry, 'call': self.call,
                'stated': self.stated, 'label': self.label}


class Program(object):
    """A small program put on the calculator to see whether it compiles.
    `entry` is the fact or entry its answer belongs to; `name` is the
    program's own, and what the person picks in the catalogue."""

    def __init__(self, entry, name, source):
        self.entry, self.name, self.source = entry, name, source

    def as_dict(self):
        return {'entry': self.entry, 'name': self.name,
                'source': self.source}


def read_programs(path):
    """-> [Program] from a file of programs, each headed `[entry] NAME`.
    A line that is `#` alone or starts with `# ` is the file's comment and
    belongs to no program, wherever it is: PPL has no such comment, so one
    left in a program would make it fail to compile for a reason that is not
    the question. Anything else before the first header is refused."""
    out, cur = [], None
    for n, line in enumerate(io.open(path, encoding='utf-8'), 1):
        line = line.rstrip('\r\n')
        if line == '#' or line.startswith('# '):
            continue
        m = re.match(r'^\[([^\]]+)\]\s+([A-Z][A-Z0-9_]*)\s*$', line)
        if m:
            cur = Program(m.group(1).strip(), m.group(2), '')
            out.append(cur)
        elif cur is not None:
            cur.source += line + '\n'
        elif line.strip() and not line.startswith('#'):
            raise ExamplesError('%s:%d: a program starts with [entry] NAME'
                                % (path, n))
    names = [p.name for p in out]
    taken = set([NAME] + [c[0] for c in CONTROLS])
    bad = sorted(set(n for n in names if names.count(n) > 1 or n in taken))
    if bad:
        raise ExamplesError('%s: a name used twice, or one the tool uses: %s'
                            % (path, ', '.join(bad)))
    for p in out:
        p.source = p.source.strip('\n') + '\n'
    return out


def compiled(path):
    """Did the calculator compile the program in this file? True when the
    file carries a compiled block, which the emulator writes into it once the
    program compiles; None when there is no readable program."""
    from hpkit import program as P
    if not os.path.isfile(path):
        return None
    data = open(path, 'rb').read()
    try:
        start = P.read(data)[2]
    except P.UnexpectedFormat:
        return None
    return P.has_compiled_block(data, start)


class Answer(object):
    def __init__(self, answered, type_=None, number=None, text='', cut=False):
        self.answered = answered
        self.type = type_
        self.number = number
        self.text = text
        self.cut = cut

    @property
    def displayed(self):
        """The answer the way an entry writes a result."""
        if self.answered is None:
            return UNREADABLE
        if not self.answered:
            return ERROR
        if self.type == -1:
            return '(answered, but could not be written back)'
        if self.type == 2 and not (len(self.text) > 1
                                   and self.text[0] == self.text[-1] == '"'):
            return '"%s"' % self.text
        return self.text


# ------------------------------------------------------------ the batch

def cases(root, names=None, probes=()):
    """-> [Case]: the examples of the named entries, every entry's when
    names is None, and then the probes, as (entry, call) pairs."""
    from hpkit import docs
    entries = docs.load(root)[0]
    out = []
    for e in entries:
        if names is not None and e.name not in names:
            continue
        for ex in e.examples:
            if ex.no_value:
                continue        # nothing to record, so nothing to run
            out.append(Case(e.name, ex.call,
                            ERROR if ex.result is None else ex.result,
                            ex.label))
    if names is not None:
        missing = sorted(set(names) - set(c.entry for c in out))
        if missing:
            raise ExamplesError('no entry with examples for: %s'
                                % ', '.join(missing))
    for entry, call in probes:
        out.append(Case(entry, call))
    return out


def harness(batch, mat=MAT, width=WIDTH, name=NAME):
    """-> the PPL program that runs every call and writes its answer into a
    row of the matrix. Row 1 is the calculator's VERSION."""
    m = 'M%d' % mat
    out = []
    for k, c in enumerate(batch, 1):
        if ';' in c.call:
            out += ['ZX%d()' % k, 'BEGIN', '  ' + c.call, 'END;', '']
    out += ['ZENC(zk, zv)',
            'BEGIN',
            '  LOCAL zt, zs, zl, zi, zn;',
            '  zt := TYPE(zv);',
            '  %s(zk, 2) := zt;' % m,
            '  IF zt == 0 THEN %s(zk, 3) := zv; END;' % m,
            '  zs := STRING(zv);',
            '  zn := SIZE(zs);',
            '  %s(zk, 4) := zn;' % m,
            '  IF zn > 0 THEN',
            '    zl := ASC(zs);',
            '    FOR zi FROM 1 TO MIN(zn, %d) DO' % width,
            '      %s(zk, %d + zi) := zl(zi);' % (m, HEAD),
            '    END;',
            '  END;',
            '  RETURN zn;',
            'END;',
            '',
            'EXPORT %s()' % name,
            'BEGIN',
            '  LOCAL zr;',
            '  %s := MAKEMAT(0, %d, %d);' % (m, len(batch) + 1, width + HEAD)]
    calls = ['VERSION'] + ['ZX%d()' % k if ';' in c.call else c.call
                           for k, c in enumerate(batch, 1)]
    for row, expr in enumerate(calls, 1):
        out += ['  IFERR zr := %s; THEN %s(%d, 1) := 0; ELSE %s(%d, 1) := 1; '
                'END;' % (expr, m, row, m, row),
                '  IF %s(%d, 1) == 1 THEN IFERR ZENC(%d, zr); THEN '
                '%s(%d, 2) := -1; END; END;' % (m, row, row, m, row)]
    out += ['  RETURN %d;' % len(batch), 'END;']
    return '\n'.join(out) + '\n'


def lint_problems(source):
    """-> the linter's errors on a generated program, which then must not be
    sent."""
    from hpkit import lint
    return [f for f in lint.check_source('<%s>' % NAME, source)[0]
            if f.level == 'ERROR']


# ------------------------------------------------------------ the answers

def _text(row, width):
    """-> (text, cut), or (None, False) when a cell of it is unreadable."""
    if len(row) > 3 and row[3] is None:
        return None, False
    length = int(row[3]) if len(row) > 3 else 0
    codes = row[HEAD:HEAD + min(length, width)]
    if None in codes:
        return None, False
    return ''.join(chr(int(c)) for c in codes), length > width


def decode(rows, count, width=WIDTH):
    """-> (the version text, [Answer]) from the matrix the calculator left.
    Raises if the matrix is not the batch's."""
    if len(rows) != count + 1 or (rows and len(rows[0]) != width + HEAD):
        raise ExamplesError(
            'M%d is %dx%d, and this batch writes %dx%d: it is not the '
            "batch's matrix. Was %s run before the emulator was closed?"
            % (MAT, len(rows), len(rows[0]) if rows else 0, count + 1,
               width + HEAD, NAME))
    version = (_text(rows[0], width)[0] or '') if rows[0][0] == 1 else ''
    answers = []
    for row in rows[1:]:
        # A cell nobody has measured decodes as None (numbers.read_hpmat with
        # strict=False). The number alone can go: the text is the answer as
        # an entry writes it. Anything else leaves the answer unknown.
        if row[0] is None or row[1] is None:
            answers.append(Answer(None))
            continue
        if row[0] != 1:
            answers.append(Answer(False))
            continue
        text, cut = _text(row, width)
        if text is None:
            answers.append(Answer(None))
            continue
        answers.append(Answer(True, int(row[1]), row[2], text, cut))
    return version, answers


def agrees(stated, answer, number=None):
    """Does an answer, as displayed (and its number, when it is one), match
    what an entry states?"""
    from hpkit import docs
    if stated == ERROR or answer == ERROR:
        return stated == answer
    if number is not None:
        return docs.same(float(number), docs.parse_result(stated))
    return docs.same(docs.parse_result(answer), docs.parse_result(stated))


# ------------------------------------------------------------ results.tsv

def results_path(root):
    return os.path.join(root, *RESULTS)


def _clean(s):
    return s.replace('\t', ' ').replace('\r', '').replace('\n', '\\n')


def read_results(root):
    """-> OrderedDict {(entry, call): {field: value}}."""
    out = OrderedDict()
    path = results_path(root)
    if not os.path.isfile(path):
        return out
    for line in io.open(path, encoding='utf-8'):
        line = line.rstrip('\r\n')
        if not line or line.startswith('#'):
            continue
        cells = line.split('\t')
        if len(cells) != len(FIELDS):
            continue
        row = OrderedDict(zip(FIELDS, cells))
        out[(row['entry'], row['call'])] = row
    return out


def write_results(root, rows):
    """Replace the rows for the same (entry, call), keep the rest, and write
    the file sorted by entry. A new row is keyed as the file will hold it,
    cleaned, which is how read_results keys the rows already there: a compile
    question's call is a program's source, line breaks and all."""
    table = read_results(root)
    for row in rows:
        table[(_clean(row['entry']), _clean(row['call']))] = row
    lines = ['# What the Virtual Calculator answered to the documentation\'s '
             'examples.',
             '# Written by `hpprime examples`; not edited by hand. One row per '
             'call.',
             '# ' + '\t'.join(FIELDS)]
    for key in sorted(table, key=lambda k: (k[0].lower(), k[0], k[1])):
        lines.append('\t'.join(_clean(table[key][f]) for f in FIELDS))
    with io.open(results_path(root), 'w', encoding='utf-8',
                 newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


# VERSION answers a block of text about the machine, and on a Spanish install
# it reads "Calculadora grafica HP Prime / Version de software: 2.4 / Version
# del hardware: Emu / Numero de serie: ... / Software Build Date: ...". The
# serial is the calculator's own and results.tsv is committed, so only the
# version and the build date are kept, never the block itself.
VERSION_NUMBER = re.compile(r'(\d+\.\d+(?:\.\d+)*)')
BUILD_DATE = re.compile(r'Build Date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})')


def firmware(version_text, fallback=''):
    """-> a short firmware string with nothing of the calculator's own in it.

    The version number and the build date, in whatever language the
    calculator answers in, and never the text VERSION gave: that carries the
    serial number.
    """
    # STRING(VERSION) brings the line breaks back as the two characters \ and
    # n rather than as line breaks, and the accented letters do not survive
    # ASC, so the lines are rebuilt here and nothing below leans on anything
    # but ASCII.
    text = (version_text or '').replace('\\n', '\n')
    number = ''
    for line in text.split('\n'):
        low = line.lower()
        if 'serial' in low or 'serie' in low:
            continue
        if 'software' in low or 'versi' in low:
            m = VERSION_NUMBER.search(line)
            if m:
                number = m.group(1)
                break
    build = BUILD_DATE.search(text)
    if number and build:
        return 'Virtual Calculator %s, build %s' % (number, build.group(1))
    if number:
        return 'Virtual Calculator %s' % number
    return fallback or 'unknown'


def exe_version(exe):
    """-> the file version of HPPrime.exe ('2.4 r15515'), or ''."""
    if not exe or not sys.platform.startswith('win'):
        return ''
    try:
        out = subprocess.check_output(
            ['powershell', '-NoProfile', '-Command',
             '(Get-Item -LiteralPath "%s").VersionInfo.FileVersion' % exe],
            stderr=subprocess.STDOUT)
        return out.decode('utf-8', 'replace').strip()
    except Exception:
        return ''


# ------------------------------------------------------------ the run

def _state_file():
    from hpkit import emulator
    return os.path.join(emulator.state_dir(), 'examples.json')


def prepare(root, batch, calc=CALC, programs=()):
    """Put the batch's program, and any programs to compile, on a freshly
    reset `calc`. -> its folder."""
    from hpkit import emulator as E, program as P
    source = harness(batch)
    problems = lint_problems(source)
    if problems:
        raise ExamplesError('the generated program does not pass the '
                            'linter:\n  %s'
                            % '\n  '.join(str(p) for p in problems))
    emu = E.find_root()
    if not emu:
        raise ExamplesError('the Virtual Calculator folder was not found: '
                            'install it and open it once')
    found = E.instances(emu)
    try:
        if calc in found and calc not in E.made():
            print('%s was not made by the kit: moved, not deleted, to %s'
                  % (calc, set_aside(emu, calc)))
            found.remove(calc)
        if calc in found:
            E.reset(emu, calc)
        else:
            others = [n for n in found if n != calc]
            if not others:
                raise ExamplesError('%s has no calculator to clone %s from'
                                    % (emu, calc))
            E.create(emu, calc, 'Prime' if 'Prime' in others else others[0])
    except E.EmulatorError as e:
        raise ExamplesError('%s' % e)
    folder = os.path.join(emu, calc)
    stale = os.path.join(folder, 'M%d.hpmat' % MAT)
    if os.path.isfile(stale):
        os.remove(stale)
    template = open(P.default_template(), 'rb').read()
    with open(os.path.join(folder, NAME + '.hpprgm'), 'wb') as f:
        f.write(P.write(template, source))
    # Not linted: whether they compile is the question.
    for p in programs:
        with open(os.path.join(folder, p.name + '.hpprgm'), 'wb') as f:
            f.write(P.write(template, p.source))
    return folder


def set_aside(root, name):
    """Move a calculator out of the emulator's folder into the kit's own,
    rather than delete it. -> where it went."""
    from hpkit import emulator as E
    dest = os.path.join(E.state_dir(), 'set-aside',
                        '%s-%s' % (name, time.strftime('%Y%m%d-%H%M%S')))
    if not os.path.isdir(os.path.dirname(dest)):
        os.makedirs(os.path.dirname(dest))
    shutil.move(os.path.join(root, name), dest)
    return dest


def check_opens(emu, calc=CALC, pids=None):
    """Raise unless a window launched now opens `calc`. `pids` are the
    running emulators, found when not given."""
    from hpkit import emulator as E
    if not emu:
        raise ExamplesError('the Virtual Calculator folder was not found: '
                            'install it and open it once')
    if E.instance_number(calc) is None:
        raise ExamplesError('no emulator window opens a calculator called %s:'
                            ' they are Prime, Prime_1, Prime_2...' % calc)
    opens = E.next_opens(emu, pids)
    if opens == calc:
        return
    if opens is None:
        why = ('an emulator is running and no lock file says which '
               'calculator it has. Close every emulator window, open your '
               'own calculator in one, and run this again.')
    elif E.instance_number(opens) < E.instance_number(calc):
        why = ('a window launched now would open %s, not %s. Open your own '
               'calculator in the emulator first, so that the next window '
               'is %s.' % (opens, calc, calc))
    else:
        why = ('%s is already open in an emulator window. Close that window,'
               ' keep your own open, and run this again.' % calc)
    raise ExamplesError(why)


def _stamp(folder):
    from hpkit import emulator as E
    path = os.path.join(folder, E.LIVE_FILE)
    return os.path.getmtime(path) if os.path.isfile(path) else None


def keys(calc=CALC, programs=()):
    first = ''
    if programs:
        first = ('\n  first, for each of these, in this order: [Shift]'
                 '[Program], pick it, Edit, Check, then Esc, whatever Check '
                 'says:\n    %s' % ' '.join(p.name for p in programs))
    return ('In the emulator window that has just opened, which should be %s:'
            '%s'
            '\n  [Shift][Program], pick %s, Edit, then Check, then Esc'
            '\n  on Home, type %s (no brackets) and Enter'
            '\n  then close that window. That is when it writes M%d.'
            % (calc, first, NAME, NAME, MAT))


def collect(root, state, answers_from=None, replace=False):
    """Read the batch back, write results.tsv. -> [(Case, Answer, verdict)].

    `answers_from` is the calculator folder; by default the one in state. A
    row results.tsv already holds is replaced by a different answer only
    with `replace`, given here or to the run that made the batch; otherwise
    the stored row stays and the verdict says so."""
    from hpkit import numbers
    folder = answers_from or state['folder']
    if state.get('stamp') is not None and _stamp(folder) == state['stamp']:
        raise ExamplesError(
            'the saved state of %s did not move, so the emulator that closed '
            'was not %s and nothing was run there. Open the emulator while '
            'your own calculator is open in another one, then run %s on %s.'
            % (state['calc'], state['calc'], NAME, state['calc']))
    path = os.path.join(folder, 'M%d.hpmat' % MAT)
    if not os.path.isfile(path):
        raise ExamplesError('%s is not there: %s was not run, or the emulator '
                            'was not closed' % (path, NAME))
    batch = [Case(**c) for c in state['cases']]
    version, answers = decode(numbers.read_hpmat(open(path, 'rb').read(),
                                                 strict=False), len(batch))
    stamp = firmware(version, 'Virtual Calculator %s'
                     % (state.get('exe_version') or '?'))
    # The day the batch ran: the emulator writes the matrix when it closes
    # after running it. The day it was prepared can be the day before.
    date = time.strftime('%Y-%m-%d', time.localtime(os.path.getmtime(path)))
    replace = replace or state.get('replace', False)
    stored = read_results(root)
    rows, out = [], []
    for c, a in zip(batch, answers):
        if a.answered is None:
            out.append((c, a, 'UNREADABLE'))
            continue
        if c.entry.upper() in NEVER_STORED:
            # displayed is derived from these, and both the row below and
            # _report read this same object, so replacing it here is what
            # keeps the answer off the file and off the screen at once.
            a.text, a.number, a.cut = NOT_STORED, None, False
        shown = a.displayed
        if c.stated is None:
            verdict = 'probe'
        elif a.type == -1:
            verdict = 'not comparable'
        else:
            verdict = ('same' if agrees(c.stated, shown,
                                        a.number if a.type == 0 else None)
                       else 'DIFFERENT')
        row = OrderedDict([
            ('entry', c.entry), ('call', c.call),
            ('answer', shown + (' (cut at %d characters)' % WIDTH
                                if a.cut else '')),
            ('type', '' if a.type is None else '%d' % a.type),
            ('firmware', stamp), ('date', date)])
        old = stored.get((c.entry, c.call))
        if (old is not None and not replace
                and (old['answer'], old['type']) != (row['answer'],
                                                     row['type'])):
            # The evidence on file and this batch disagree. Which is right is
            # a person's call -- an app active in one run and not the other
            # has done this -- so the stored row stays until asked.
            verdict = 'KEPT %s' % old['answer']
        else:
            rows.append(row)
        out.append((c, a, verdict))
    programs = [Program(**p) for p in state.get('programs', [])]
    if programs:
        _collect_compiled(folder, programs, stored, replace, stamp, date,
                          rows, out)
    write_results(root, rows)
    return out


def _collect_compiled(folder, programs, stored, replace, stamp, date, rows,
                      out):
    """Whether each program compiled, read from its file. The controls
    decide whether anything is concluded: ZCOK has to have compiled and
    ZCBAD not, or the method did not work -- a program not checked, a
    failed Check that writes a block after all -- and no row is stored."""
    seen = dict((p.name, compiled(os.path.join(folder, p.name + '.hpprgm')))
                for p in programs)
    trusted = all(seen.get(name) is want for name, _, want in CONTROLS)
    for p in programs:
        got = seen[p.name]
        shown = (UNREADABLE if got is None else COMPILES if got else REFUSED)
        case = Case(p.entry, p.name)
        answer = Answer(True, None, None, shown)
        if p.entry == CONTROL:
            want = dict((n, w) for n, _, w in CONTROLS)[p.name]
            out.append((case, answer, 'control' if got is want
                        else 'CONTROL WRONG'))
            continue
        if not trusted:
            out.append((case, answer, 'NOT CONCLUDED'))
            continue
        if got is None:
            out.append((case, answer, 'UNREADABLE'))
            continue
        row = OrderedDict([
            ('entry', p.entry), ('call', p.source), ('answer', shown),
            ('type', ''), ('firmware', stamp), ('date', date)])
        old = stored.get((p.entry, _clean(p.source)))
        if old is not None and not replace and old['answer'] != shown:
            out.append((case, answer, 'KEPT %s' % old['answer']))
            continue
        rows.append(row)
        out.append((case, answer, 'compile'))


def run(root, batch, calc=CALC, wait=True, spawn=None, timeout=1800,
        pids=None, replace=False, programs=()):
    """Prepare the batch, launch an emulator, wait for it, collect.
    `pids` are the running emulators, found when not given."""
    from hpkit import emulator as E
    if not replace:
        # A probe reusing a call that already has a row would replace that
        # row when it is collected. Refused before any keypress is spent.
        stored = read_results(root)
        clash = [c for c in batch
                 if c.stated is None and (c.entry, c.call) in stored]
        clash += [Case(p.entry, p.name) for p in programs
                  if (p.entry, _clean(p.source)) in stored]
        if clash:
            raise ExamplesError(
                '%d probe(s) reuse a call results.tsv already holds, and '
                'would replace its row: %s. Give each a call text of its own, '
                'or pass --replace to measure it again on purpose.'
                % (len(clash), '; '.join('%s %s' % (c.entry, c.call)
                                         for c in clash)))
    if programs:
        programs = [Program(CONTROL, n, s) for n, s, _ in CONTROLS] \
            + list(programs)
    check_opens(E.find_root(), calc, pids)
    folder = prepare(root, batch, calc, programs)
    exe = E.find_exe()
    state = {'cases': [c.as_dict() for c in batch], 'calc': calc,
             'folder': folder, 'stamp': _stamp(folder),
             'exe_version': exe_version(exe), 'replace': replace,
             'programs': [p.as_dict() for p in programs]}
    target = _state_file()
    if not os.path.isdir(os.path.dirname(target)):
        os.makedirs(os.path.dirname(target))
    with io.open(target, 'w', encoding='utf-8') as f:
        f.write(json.dumps(state, indent=1, ensure_ascii=False))
    if spawn is None:
        if not exe:
            raise ExamplesError('HPPrime.exe was not found')

        def spawn():
            return subprocess.Popen([exe], cwd=os.path.dirname(exe))
    proc = spawn()
    print('%d call(s) on %s, in %s.' % (len(batch), calc, NAME))
    if programs:
        print('%d program(s) to compile, two of them controls.'
              % len(programs))
    print(keys(calc, programs))
    if not wait:
        print('\nWhen it is closed: hpprime examples --collect')
        return None
    sys.stdout.write('waiting for that emulator to close ')
    sys.stdout.flush()
    deadline = time.time() + timeout
    while proc.poll() is None:
        if time.time() > deadline:
            print('\ngave up waiting. When you have run it: hpprime examples '
                  '--collect')
            return None
        time.sleep(1.0)
        sys.stdout.write('.')
        sys.stdout.flush()
    print('')
    return collect(root, state)


def relabel(root):
    """HP help or unverified -> emulator for every example whose stored
    answer agrees: a label weaker than what was measured understates the
    evidence as surely as a stronger one overstates it.
    -> [(path, line, call)] changed. G2 is never touched."""
    from hpkit import docs
    results = read_results(root)
    changed = []
    for e in docs.load(root)[0]:
        lines = e.text.split('\n')
        touched = False
        for ex in e.examples:
            r = results.get((e.name, ex.call))
            if not r or ex.label not in ('HP help', 'unverified'):
                continue
            stated = ERROR if ex.result is None else ex.result
            number = None
            if r['type'] == '0':
                try:
                    number = float(r['answer'])
                except ValueError:
                    number = None
            if not agrees(stated, r['answer'], number):
                continue
            i = ex.line - 1
            new = re.sub(r'\|\s*(HP help|unverified)\s*\|\s*$',
                         '| [emulator](../results.tsv) |', lines[i])
            if new != lines[i]:
                lines[i] = new
                touched = True
                changed.append((e.path, ex.line, ex.call))
        if touched:
            with io.open(e.path, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(lines))
    return changed


# ---------------------------------------------------------------------- cli

def _report(root, verdicts):
    width = max([len(c.call) for c, _, _ in verdicts] + [4])
    width = min(width, 48)
    print('\n%-10s %-*s  %-22s %-22s %s' % ('entry', width, 'call',
                                           'the entry says', 'the emulator',
                                           ''))
    bad = kept = lost = 0
    for c, a, verdict in verdicts:
        if verdict == 'DIFFERENT':
            bad += 1
        elif verdict.startswith('KEPT'):
            kept += 1
        elif verdict in ('UNREADABLE', 'NOT CONCLUDED', 'CONTROL WRONG'):
            lost += 1
        print('%-10s %-*s  %-22s %-22s %s'
              % (c.entry, width, c.call[:width], (c.stated or '-')[:22],
                 a.displayed[:22], verdict))
    print('\n%d call(s); %d disagree with their entry. The rows are in %s.'
          % (len(verdicts), bad, '/'.join(RESULTS)))
    if kept:
        print('%d answer(s) differ from the row results.tsv already holds, '
              'which was KEPT. To replace them: hpprime examples --collect '
              '--replace' % kept)
    if lost:
        print('%d answer(s) could not be read back, or were not concluded '
              'because a control came out wrong, and were not stored.' % lost)
    refused = [c.call for c, a, v in verdicts
               if v == 'compile' and a.text == REFUSED]
    if refused:
        print('Did not compile: %s. If Check was not pressed on one of '
              'them, that one is not a result: say so, and it is run again.'
              % ', '.join(refused))
    return bad + kept + lost


def cli(argv):
    from hpkit import docs
    if not argv or '--help' in argv or '-h' in argv:
        print(__doc__)
        return 0 if argv else 2
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    root = docs.ROOT
    try:
        if '--relabel' in argv:
            changed = relabel(root)
            for path, line, call in changed:
                print('%s:%d: now emulator  %s'
                      % (os.path.relpath(path, root), line, call))
            print('%d label(s) changed. Run hpprime docs to regenerate the '
                  'pages.' % len(changed))
            return 0
        if '--collect' in argv:
            with io.open(_state_file(), encoding='utf-8') as f:
                state = json.loads(f.read())
            return 1 if _report(root, collect(
                root, state, replace='--replace' in argv)) else 0
        programs = []
        if '--compile' in argv:
            programs = read_programs(argv[argv.index('--compile') + 1])
        probes, names, skip = [], [], False
        for k, a in enumerate(argv):
            if skip:
                skip = False
                continue
            if a == '--probe':
                entry, _, call = argv[k + 1].partition('=')
                probes.append((entry.strip(), call.strip()))
                skip = True
            elif a == '--compile':
                skip = True
            elif not a.startswith('-'):
                names.append(a)
        batch = cases(root, None if '--all' in argv else names, probes)
        if not batch and not programs:
            print('nothing to run')
            return 2
        verdicts = run(root, batch, wait='--no-wait' not in argv,
                       replace='--replace' in argv, programs=programs)
        if verdicts is None:
            return 0
        return 1 if _report(root, verdicts) else 0
    except ExamplesError as e:
        print('ERROR: %s' % e)
        return 1
