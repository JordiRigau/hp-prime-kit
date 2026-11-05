# -*- coding: utf-8 -*-
"""Running the documentation's examples on the emulator, without it.

    python tests/test_examples_run.py

The program a batch generates, the answers it reads back, results.tsv, the
relabelling, which calculator a new window would open, and the whole run: a
temporary folder plays the calculators, lock files play the windows that are
open, and a stand-in plays the emulator, writing the matrix the way the
calculator leaves it when it closes.
"""
from __future__ import unicode_literals
import os, shutil, sys, tempfile, time
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from hpkit import docs, emulator as E, examples as X, numbers as N  # noqa

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')

PASS, FAIL = [0], [0]


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + str(detail)) if detail else ''))


def row(answered, type_=0, number=0.0, text=''):
    """One row of the matrix, the way ZENC writes it."""
    r = [1.0 if answered else 0.0, float(type_), float(number),
         float(len(text))] + [float(ord(c)) for c in text[:X.WIDTH]]
    return r + [0.0] * (X.WIDTH + X.HEAD - len(r))


def row_for(stated):
    """The row a calculator agreeing with `stated` would write."""
    if stated == X.ERROR:
        return row(False)
    if stated.startswith('"'):
        return row(True, 2, 0, stated[1:-1])
    try:
        return row(True, 0, float(stated), stated)
    except ValueError:
        return row(True, 6, 0, stated)


def lock(folder, number, pid):
    """The lock an emulator window holds on one calculator."""
    if not os.path.isdir(folder):
        os.makedirs(folder)
    name = 'HPEmuInstance%s.lock' % (number or '')
    with open(os.path.join(folder, name), 'wb') as f:
        f.write(('%d\nHPPrime\nHOST\nuuid\n\n' % pid).encode('ascii'))


VERSION = 'Software Version: 2.4.15515'


def copy_docs():
    tmp = tempfile.mkdtemp(prefix='hpex-')
    shutil.copytree(os.path.join(ROOT, 'docs'), os.path.join(tmp, 'docs'))
    return tmp


def the_program():
    batch = X.cases(ROOT, ['LEFT', 'MID', 'FOR'],
                    [('SIZE', 'TYPE(SIZE([[1,2,3],[4,5,6]]))')])
    src = X.harness(batch)
    ok(not X.lint_problems(src), 'the generated program passes the linter',
       X.lint_problems(src))
    ok(src.count('IFERR zr :=') == len(batch) + 1,
       'one IFERR per call, and one for VERSION')
    ok('ZX' in src and 'EXPORT %s()' % X.NAME in src,
       'a function body becomes a function of its own')
    try:
        X.cases(ROOT, ['NOSUCH'])
        ok(False, 'an entry that does not exist is refused')
    except X.ExamplesError:
        ok(True, 'an entry that does not exist is refused')


def the_answers():
    rows = [row(True, 2, 0, VERSION), row(True, 2, 0, 'MOM'), row(False),
            row(True, 0, 12.56636, '12.56636'),
            row(True, 6, 0, '{1,3,5,7,9}'), row(True, 2, 0, '')]
    version, answers = X.decode(rows, 5)
    ok(version == VERSION, 'the first row is the version')
    shown = [a.displayed for a in answers]
    ok(shown == ['"MOM"', X.ERROR, '12.56636', '{1,3,5,7,9}', '""'],
       'text, a refusal, a number, a list and an empty text read back', shown)
    ok(all(X.agrees(s, a.displayed, a.number if a.type == 0 else None)
           for s, a in zip(['"MOM"', X.ERROR, '12.56636', '{1,3,5,7,9}',
                            '""'], answers)),
       'each agrees with the result written the same way')
    ok(not X.agrees('"MOO"', '"MOM"') and not X.agrees('12.5', '12.56636',
                                                       12.56636),
       'and not with a different one')
    try:
        X.decode(rows[:3], 5)
        ok(False, 'a matrix of the wrong size is refused')
    except X.ExamplesError:
        ok(True, 'a matrix of the wrong size is refused')


def the_no_value_rows():
    """An example whose result is *no value* has nothing to record: the
    interpreter does not run it and it never reaches a batch."""
    tmp = copy_docs()
    try:
        left = os.path.join(tmp, 'docs', 'commands', 'strings', 'LEFT.md')
        text = open(left, encoding='utf-8').read()
        with open(left, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text.replace(
                '| `LEFT("MOMOGUMBO", 3)`',
                '| `LEFT("abc", 1)` | *no value* | unverified |\n'
                '| `LEFT("MOMOGUMBO", 3)`', 1))
        calls = [c.call for c in X.cases(tmp, ['LEFT'])]
        ok('LEFT("abc", 1)' not in calls and len(calls) > 1,
           'an example with no value to record is left out of a batch', calls)
        docs.build(tmp)         # the new row changes the pages made from it
        problems, _ = docs.check(tmp)
        ok(not problems, 'and the documentation still passes',
           '; '.join(str(p) for p in problems))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def the_firmware():
    """What VERSION answers is a block about the machine, with the serial
    number in it and the line breaks written as two characters."""
    text = ('"Calculadora grafica HP Prime\\nVersion de software: 2.4\\n'
            'Version del hardware: Emu\\nNumero de serie: XXXXXXXXXXXXXXX\\n'
            '\\nDetails\\nSoftware Build Date: 2025-09-15')
    got = X.firmware(text, 'fallback')
    ok(got == 'Virtual Calculator 2.4, build 2025-09-15',
       'the version and the build date are what is kept', got)
    ok('XXXXXXXXXXXXXXX' not in got and 'serie' not in got.lower(),
       'and the serial number is not')
    ok(X.firmware('Software Version: 2.4.15515')
       == 'Virtual Calculator 2.4.15515',
       'an English version line, with no build date')
    ok(X.firmware('', 'Virtual Calculator 2.4 r15515')
       == 'Virtual Calculator 2.4 r15515',
       'and with no version text, what the program file says')


def the_results_file():
    tmp = copy_docs()
    try:
        # The entry carries the emulator label already, so put HP help back
        # in the copy to give --relabel something to change.
        left = os.path.join(tmp, 'docs', 'commands', 'strings', 'LEFT.md')
        text = open(left, encoding='utf-8').read()
        # An unverified example with an agreeing answer is added too, and
        # one whose answer disagrees, which must keep its label.
        with open(left, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text.replace(
                '| `LEFT("MOMOGUMBO", 3)` | `"MOM"` | '
                '[emulator](../results.tsv) |',
                '| `LEFT("MOMOGUMBO", 3)` | `"MOM"` | HP help |\n'
                '| `LEFT("xyz", 2)` | `"xy"` | unverified |\n'
                '| `LEFT("uvw", 1)` | `"u"` | unverified |'))
        X.write_results(tmp, [OrderedDict([
            ('entry', 'LEFT'), ('call', 'LEFT("MOMOGUMBO", 3)'),
            ('answer', '"MOM"'), ('type', '2'), ('firmware', VERSION),
            ('date', '2026-09-11')]), OrderedDict([
            ('entry', 'LEFT'), ('call', 'LEFT("xyz", 2)'),
            ('answer', '"xy"'), ('type', '2'), ('firmware', VERSION),
            ('date', '2026-09-16')]), OrderedDict([
            ('entry', 'LEFT'), ('call', 'LEFT("uvw", 1)'),
            ('answer', '"w"'), ('type', '2'), ('firmware', VERSION),
            ('date', '2026-09-16')])])
        got = X.read_results(tmp)
        ok(got[('LEFT', 'LEFT("MOMOGUMBO", 3)')]['answer'] == '"MOM"',
           'a row written reads back')

        changed = X.relabel(tmp)
        ok(any('MOMOGUMBO' in call for _, _, call in changed),
           'relabel changes an HP help example the emulator confirms',
           changed)
        text = open(os.path.join(tmp, 'docs', 'commands', 'strings',
                                 'LEFT.md'), encoding='utf-8').read()
        ok('| `"MOM"` | [emulator](../results.tsv) |' in text,
           'and its label now points at the stored answer')
        ok('| `LEFT("xyz", 2)` | `"xy"` | [emulator](../results.tsv) |'
           in text, 'relabel changes an unverified example the emulator '
           'confirms')
        ok('| `LEFT("uvw", 1)` | `"u"` | unverified |' in text,
           'and leaves one the emulator contradicts as it was')
        ok('| `LEFT("abcdef", 3)` | `"abc"` | G2 |' in text,
           'a G2 label is left as it was')
        # The contradicted example is a problem for a person to settle, and
        # the check says so; take it out to see the rest pass.
        text = text.replace('| `LEFT("uvw", 1)` | `"u"` | unverified |\n', '')
        with open(left, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        docs.build(tmp)
        problems, _ = docs.check(tmp)
        ok(not problems, 'the documentation passes with the new labels',
           '; '.join(str(p) for p in problems))
        ok(X.relabel(tmp) == [], 'relabelling twice changes nothing more')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def the_program_measured_again():
    """A compile question's call is the program's source, line breaks and
    all, and results.tsv holds it cleaned: a line break as the two characters
    \\n, a tab as a space. The same program measured again replaces its row
    rather than adding a second one."""
    tmp = tempfile.mkdtemp(prefix='hpexagain-')
    try:
        os.makedirs(os.path.dirname(X.results_path(tmp)))
        source = 'EXPORT ZQL09()\nBEGIN\n\tRETURN 1;\nEND;\n'

        def measured(date):
            return OrderedDict([
                ('entry', 'test.compile-one'), ('call', source),
                ('answer', X.COMPILES), ('type', ''), ('firmware', VERSION),
                ('date', date)])
        X.write_results(tmp, [measured('2026-11-06')])
        X.write_results(tmp, [measured('2026-11-07')])
        mine = [r for k, r in X.read_results(tmp).items()
                if k[0] == 'test.compile-one']
        ok(len(mine) == 1 and mine[0]['date'] == '2026-11-07',
           'a program measured again reads back as one row, the newer one',
           [r['date'] for r in mine])
        with open(X.results_path(tmp), encoding='utf-8') as f:
            lines = [line for line in f
                     if line.startswith('test.compile-one\t')]
        ok(len(lines) == 1, 'and the file holds it once', lines)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def the_next_window():
    """Which calculator a window launched now would open, from the locks the
    windows already open are holding."""
    tmp = tempfile.mkdtemp(prefix='hplock-')
    try:
        calcs = os.path.join(tmp, 'Calculators')
        os.makedirs(os.path.join(calcs, 'Prime'))
        locks = os.path.join(tmp, 'Temporal')
        ok(E.next_opens(calcs, []) == 'Prime',
           'with no window open, the next one opens Prime')
        lock(locks, 0, 4242)
        ok(E.next_opens(calcs, [4242]) == 'Prime_1',
           'with Prime held, the next one opens Prime_1')
        ok(E.next_opens(calcs, []) == 'Prime',
           'a lock whose process is gone holds nothing')
        lock(locks, 1, 4343)
        ok(E.next_opens(calcs, [4343]) == 'Prime',
           'with only Prime_1 held, the next one opens Prime')
        ok(E.next_opens(calcs, [4242, 4343]) == 'Prime_2',
           'with both held, the next one opens Prime_2')
        ok(E.next_opens(calcs, [4242, 5555]) is None,
           'a running emulator whose lock cannot be found: it says so rather '
           'than guess')
        ok(E.instance_number('Prime') == 0
           and E.instance_number('Prime_12') == 12
           and E.instance_number('DOCS') is None,
           'the names a window can open, and the ones it never does')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


class Finished(object):
    def poll(self):
        return 0


def the_run():
    tmp = tempfile.mkdtemp(prefix='hpexrun-')
    saved = {k: os.environ.get(k) for k in ('HPPRIME_EMU_ROOT',
                                            'HPPRIME_KIT_STATE',
                                            'HPPRIME_EMU_EXE')}
    try:
        calcs = os.path.join(tmp, 'Calculators')
        locks = os.path.join(tmp, 'Temporal')
        prime = os.path.join(calcs, 'Prime')
        os.makedirs(prime)
        with open(os.path.join(prime, E.LIVE_FILE), 'wb') as f:
            f.write(b'saved')
        # A Prime_1 the emulator made on its own, with something in it.
        theirs = os.path.join(calcs, X.CALC)
        os.makedirs(theirs)
        with open(os.path.join(theirs, 'mine.txt'), 'w') as f:
            f.write('keep me')
        os.environ['HPPRIME_EMU_ROOT'] = calcs
        os.environ['HPPRIME_KIT_STATE'] = os.path.join(tmp, 'state')
        # No HPPrime.exe, so nothing asks Windows for its version.
        os.environ['HPPRIME_EMU_EXE'] = os.path.join(tmp, 'none.exe')
        root = copy_docs()
        batch = X.cases(root, ['LEFT', 'MID'])
        launched = []

        def must_not_launch():
            launched.append(1)
            return Finished()

        try:
            X.run(root, batch, spawn=must_not_launch, pids=[])
            ok(False, 'with no window open, it does not launch')
        except X.ExamplesError as e:
            ok('Open your own calculator' in str(e) and not launched,
               'with no window open it does not launch: that window would be '
               'your own calculator', e)
        ok(os.path.isfile(os.path.join(theirs, 'mine.txt')),
           'and it has touched nothing')

        lock(locks, 0, 4242)                    # your own calculator, open

        def emulator_that_runs_it():
            # What the calculator does on Prime_1: it runs HPKDOC, writes M9,
            # and saves its state when the window is closed.
            calc = os.path.join(calcs, X.CALC)
            ok(os.path.isfile(os.path.join(calc, X.NAME + '.hpprgm')),
               'the program is on %s before the emulator opens' % X.CALC)
            rows = [row(True, 2, 0, VERSION)] + [row_for(c.stated)
                                                 for c in batch]
            with open(os.path.join(calc, 'M%d.hpmat' % X.MAT), 'wb') as f:
                f.write(N.write_hpmat(rows))
            later = time.time() + 5
            os.utime(os.path.join(calc, E.LIVE_FILE), (later, later))
            return Finished()

        verdicts = X.run(root, batch, spawn=emulator_that_runs_it,
                         pids=[4242])
        aside = os.path.join(tmp, 'state', 'set-aside')
        kept = sorted(os.listdir(aside)) if os.path.isdir(aside) else []
        ok(len(kept) == 1
           and os.path.isfile(os.path.join(aside, kept[0], 'mine.txt')),
           'a %s the kit did not make is moved aside, not deleted' % X.CALC,
           kept)
        ok(X.CALC in E.made()
           and not os.path.exists(os.path.join(theirs, 'mine.txt')),
           '%s is now a clone of Prime, made by the kit' % X.CALC)
        ok(verdicts and all(v == 'same' for _, _, v in verdicts),
           'every answer agrees with its entry',
           [(c.call, a.displayed, v) for c, a, v in verdicts or []
            if v != 'same'])
        stored = X.read_results(root)
        mine = [stored.get((c.entry, c.call)) for c in batch]
        ok(all(r is not None
               and r['firmware'] == 'Virtual Calculator 2.4.15515'
               for r in mine),
           'results.tsv holds a row per call of the batch, with the version',
           [c.call for c, r in zip(batch, mine) if r is None
            or r['firmware'] != 'Virtual Calculator 2.4.15515'])

        lock(locks, 1, 4343)                    # and now Prime_1 is open too
        try:
            X.run(root, batch, spawn=must_not_launch, pids=[4242, 4343])
            ok(False, 'with %s already open, it does not launch' % X.CALC)
        except X.ExamplesError as e:
            ok('already open' in str(e) and not launched,
               'with %s already open, it does not launch' % X.CALC, e)

        def emulator_that_opened_another():
            return Finished()        # Prime_1's saved state never moves

        try:
            X.run(root, batch, spawn=emulator_that_opened_another,
                  pids=[4242])
            ok(False, 'an emulator that did not have %s is caught' % X.CALC)
        except X.ExamplesError as e:
            ok('did not move' in str(e),
               'an emulator that did not have %s is caught' % X.CALC, e)
        shutil.rmtree(root, ignore_errors=True)
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def the_never_stored():
    """SERIAL answers the calculator's serial number and results.tsv is
    committed and published, so that answer must reach neither the file nor
    the screen. The report reads the same object the row is built from, which
    is why one guard has to cover both."""

    class Screen(object):
        """A stand-in for stdout, to read back what the report printed."""

        def __init__(self):
            self.text = ''

        def write(self, s):
            self.text += s

        def flush(self):
            pass

    secret = 'SN-PRIME-0123456789'
    tmp = copy_docs()
    folder = tempfile.mkdtemp(prefix='hpexser-')
    try:
        with open(os.path.join(folder, 'M%d.hpmat' % X.MAT), 'wb') as f:
            f.write(N.write_hpmat([row(True, 2, 0, VERSION),
                                   row(True, 2, 0, secret)]))
        state = {'cases': [X.Case('SERIAL', 'SERIAL').as_dict()],
                 'calc': X.CALC, 'folder': folder, 'stamp': None,
                 'date': '2026-09-12'}
        verdicts = X.collect(tmp, state)

        shown = [a.displayed for _, a, _ in verdicts]
        ok(secret not in ''.join(shown),
           'what SERIAL answered is not what the collection carries', shown)

        stored = open(X.results_path(tmp), encoding='utf-8').read()
        ok(secret not in stored, 'and it is not in results.tsv')
        ok(X.NOT_STORED in stored, 'the row says so in its place')

        real, sys.stdout = sys.stdout, Screen()
        try:
            X._report(tmp, verdicts)
            printed = sys.stdout.text
        finally:
            sys.stdout = real
        ok(secret not in printed, 'and the report does not print it either')

        # VERSION carries the serial number as well. The firmware a row is
        # stamped with survives because it goes through firmware(), which
        # drops that line; a case whose entry is VERSION would not.
        folder2 = tempfile.mkdtemp(prefix='hpexver-')
        with open(os.path.join(folder2, 'M%d.hpmat' % X.MAT), 'wb') as f:
            f.write(N.write_hpmat([row(True, 2, 0, VERSION),
                                   row(True, 2, 0, secret)]))
        state2 = {'cases': [X.Case('VERSION', 'VERSION').as_dict()],
                  'calc': X.CALC, 'folder': folder2, 'stamp': None,
                  'date': '2026-09-12'}
        verdicts2 = X.collect(tmp, state2)
        shown2 = [a.displayed for _, a, _ in verdicts2]
        ok(secret not in ''.join(shown2),
           'what VERSION answered is not carried either', shown2)
        ok(secret not in open(X.results_path(tmp), encoding='utf-8').read(),
           'and VERSION did not put it in results.tsv')

        # A real VERSION answer is longer than the harness carries, so the
        # row would be marked as cut. The guard replaces the text, and a
        # placeholder that claims it was cut at 160 characters is a lie.
        long_secret = secret + 'x' * (X.WIDTH * 2)
        with open(os.path.join(folder2, 'M%d.hpmat' % X.MAT), 'wb') as f:
            f.write(N.write_hpmat([row(True, 2, 0, VERSION),
                                   row(True, 2, 0, long_secret)]))
        X.collect(tmp, state2)
        kept = [l for l in open(X.results_path(tmp), encoding='utf-8')
                if l.startswith('VERSION\tVERSION\t')]
        ok(kept and 'cut at' not in kept[0],
           'and the placeholder does not claim it was cut', kept)
        os.remove(os.path.join(folder2, 'M%d.hpmat' % X.MAT))
        os.rmdir(folder2)

        # A name that is not on the list keeps its answer, or the guard would
        # be quietly throwing away measurements.
        with open(os.path.join(folder, 'M%d.hpmat' % X.MAT), 'wb') as f:
            f.write(N.write_hpmat([row(True, 2, 0, VERSION),
                                   row(True, 2, 0, 'MOM')]))
        state['cases'] = [X.Case('LEFT', 'LEFT("MOMOGUMBO", 3)').as_dict()]
        verdicts = X.collect(tmp, state)
        ok(verdicts[0][1].displayed == '"MOM"',
           'a name that is not on the list is kept as it was',
           verdicts[0][1].displayed)
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


def the_evidence_kept():
    """A batch never loses or replaces evidence in silence: a cell it cannot
    read costs its row and no more, a different answer does not replace a
    stored row unless asked, a probe cannot reuse a stored call, and a row
    carries the day the batch ran."""
    tmp = copy_docs()
    folder = tempfile.mkdtemp(prefix='hpexkeep-')
    path = os.path.join(folder, 'M%d.hpmat' % X.MAT)
    cols = X.WIDTH + X.HEAD
    bad_cell = bytes.fromhex('F391999999999939')      # a sign nibble of 3

    def matrix(rows, spoil=()):
        data = bytearray(N.write_hpmat(rows))
        for r, c in spoil:
            o = 16 + 8 * (r * cols + c)
            data[o:o + 8] = bad_cell
        with open(path, 'wb') as f:
            f.write(bytes(data))
        ran = time.mktime((2026, 1, 2, 12, 0, 0, 0, 0, -1))
        os.utime(path, (ran, ran))

    def state(*cases):
        return {'cases': [c.as_dict() for c in cases], 'calc': X.CALC,
                'folder': folder, 'stamp': None}

    try:
        # One unreadable number, one unreadable character of text.
        matrix([row(True, 2, 0, VERSION), row(True, 0, 5.0, '5'),
                row(True, 2, 0, 'x')], spoil=[(1, 2), (2, X.HEAD)])
        verdicts = X.collect(tmp, state(X.Case('LEFT', 'ZPROBE(1)'),
                                        X.Case('LEFT', 'ZPROBE(2)')))
        stored = X.read_results(tmp)
        ok([v for _, _, v in verdicts] == ['probe', 'UNREADABLE'],
           'one bad cell costs its row, not the batch',
           [v for _, _, v in verdicts])
        first = stored.get(('LEFT', 'ZPROBE(1)'))
        ok(first is not None and first['answer'] == '5',
           'a row whose number alone is unreadable is kept from its text',
           first)
        ok(('LEFT', 'ZPROBE(2)') not in stored,
           'a row whose text is unreadable is not stored')
        ok(first is not None and first['date'] == '2026-01-02',
           'a row carries the day the matrix was written, the day it ran',
           first and first['date'])

        # A different answer does not replace the stored row.
        matrix([row(True, 2, 0, VERSION), row(True, 2, 0, 'z')])
        case = X.Case('LEFT', 'ZPROBE(1)', '"z"')
        verdicts = X.collect(tmp, state(case))
        kept = X.read_results(tmp)[('LEFT', 'ZPROBE(1)')]
        ok(verdicts[0][2].startswith('KEPT') and kept['answer'] == '5',
           'a different answer leaves the stored row, and says so',
           (verdicts[0][2], kept['answer']))
        X.collect(tmp, state(case), replace=True)
        ok(X.read_results(tmp)[('LEFT', 'ZPROBE(1)')]['answer'] == '"z"',
           'and replaces it when asked')
        verdicts = X.collect(tmp, state(case))
        ok(verdicts[0][2] == 'same',
           'the same answer again is simply written', verdicts[0][2])

        # A probe on a call that already has a row is refused before the
        # emulator opens: the guard comes before anything else is looked at.
        try:
            X.run(tmp, [X.Case('LEFT', 'ZPROBE(1)')], pids=[])
            ok(False, 'a probe reusing a stored call is refused')
        except X.ExamplesError as e:
            ok('reuse a call' in str(e),
               'a probe reusing a stored call is refused before anything '
               'launches', e)
        try:
            X.run(tmp, [X.Case('LEFT', 'ZPROBE(1)')], pids=[], replace=True,
                  spawn=lambda: None)
        except X.ExamplesError as e:
            ok('reuse a call' not in str(e),
               'and let through with --replace', e)
        else:
            ok(False, 'and let through with --replace',
               'the run went on with no emulator window open')
    finally:
        shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)


PROBES = u"""# two questions
[test.compile-one] ZQL09
EXPORT ZQL09()
BEGIN
  LOCAL a,b,c,d,e1,f,g,h,k;
  RETURN 1;
END;

# a comment between two programs belongs to neither
[test.compile-two] ZQEND
EXPORT ZQEND()
BEGIN
  IF 1 THEN RETURN 1; ENDCASE;
END;
"""


def the_compile_questions():
    """Does a program compile? Each goes on the calculator with two controls,
    and its own file says: the emulator writes a compiled block into it once
    it compiles. The controls decide whether anything is concluded."""
    import io as _io
    tmp = tempfile.mkdtemp(prefix='hpexcomp-')
    saved_env = {k: os.environ.get(k) for k in ('HPPRIME_EMU_ROOT',
                                                'HPPRIME_KIT_STATE',
                                                'HPPRIME_EMU_EXE')}
    real_compiled = X.compiled
    try:
        path = os.path.join(tmp, 'probes.txt')
        with _io.open(path, 'w', encoding='utf-8', newline='\n') as f:
            f.write(PROBES)
        programs = X.read_programs(path)
        ok([(p.entry, p.name) for p in programs]
           == [('test.compile-one', 'ZQL09'), ('test.compile-two', 'ZQEND')]
           and programs[0].source.startswith('EXPORT ZQL09()')
           and programs[0].source.endswith('END;\n')
           and '#' not in programs[0].source
           and programs[1].source.endswith('END;\n'),
           'a file of programs is read, each with its fact and its source',
           [(p.entry, p.name) for p in programs])
        for bad, what in ((u'EXPORT F()\n', 'source before any header'),
                          (u'[x] ZCOK\nEXPORT F()\n', 'a control\'s name'),
                          (PROBES + u'[x] ZQL09\nEXPORT F()\n',
                           'a name used twice')):
            with _io.open(path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(bad)
            try:
                X.read_programs(path)
                ok(False, 'a file with %s is refused' % what)
            except X.ExamplesError:
                ok(True, 'a file with %s is refused' % what)

        from hpkit import program as P
        template = open(P.default_template(), 'rb').read()
        plain = os.path.join(tmp, 'PLAIN.hpprgm')
        with open(plain, 'wb') as f:
            f.write(P.write(template, 'EXPORT F()\nBEGIN\n  RETURN 1;\nEND;'))
        ok(X.compiled(plain) is False and X.compiled(plain + 'x') is None,
           'a file with no compiled block reads as not compiled, and no file '
           'as nothing')

        # The whole run, with a stand-in for the emulator. It compiles what
        # `good` names, which is how the controls are made to come out right
        # or wrong.
        calcs = os.path.join(tmp, 'Calculators')
        prime = os.path.join(calcs, 'Prime')
        os.makedirs(prime)
        with open(os.path.join(prime, E.LIVE_FILE), 'wb') as f:
            f.write(b'saved')
        os.environ['HPPRIME_EMU_ROOT'] = calcs
        os.environ['HPPRIME_KIT_STATE'] = os.path.join(tmp, 'state')
        os.environ['HPPRIME_EMU_EXE'] = os.path.join(tmp, 'none.exe')
        lock(os.path.join(tmp, 'Temporal'), 0, 5151)
        root = copy_docs()
        marks = set()
        X.compiled = lambda p: (None if not os.path.isfile(p)
                                else os.path.basename(p) in marks)

        def emulator_that_compiles(good):
            def stand_in():
                calc = os.path.join(calcs, X.CALC)
                names = sorted(f for f in os.listdir(calc)
                               if f.endswith('.hpprgm'))
                ok(names == ['HPKDOC.hpprgm', 'ZCBAD.hpprgm', 'ZCOK.hpprgm',
                             'ZQEND.hpprgm', 'ZQL09.hpprgm'],
                   'the programs and both controls are on %s' % X.CALC,
                   names)
                marks.clear()
                marks.update(n + '.hpprgm' for n in good)
                with open(os.path.join(calc, 'M%d.hpmat' % X.MAT), 'wb') as f:
                    f.write(N.write_hpmat([row(True, 2, 0, VERSION)]))
                later = time.time() + 5
                os.utime(os.path.join(calc, E.LIVE_FILE), (later, later))
                return Finished()
            return stand_in

        verdicts = X.run(root, [], pids=[5151], programs=programs,
                         spawn=emulator_that_compiles(['ZCBAD', 'ZQL09']))
        got = dict((c.call, v) for c, _, v in verdicts)
        ok(got == {'ZCOK': 'CONTROL WRONG', 'ZCBAD': 'CONTROL WRONG',
                   'ZQL09': 'NOT CONCLUDED', 'ZQEND': 'NOT CONCLUDED'},
           'controls that come out wrong conclude nothing', got)
        stored = X.read_results(root)
        ok(not [k for k in stored if k[0] in ('test.compile-one',
                                              'test.compile-two')],
           'and nothing is stored')

        verdicts = X.run(root, [], pids=[5151], programs=programs,
                         spawn=emulator_that_compiles(['ZCOK', 'ZQL09']))
        shown = dict((c.call, a.displayed) for c, a, _ in verdicts)
        ok(shown == {'ZCOK': X.COMPILES, 'ZCBAD': X.REFUSED,
                     'ZQL09': X.COMPILES, 'ZQEND': X.REFUSED},
           'with the controls right, each program says whether it compiled',
           shown)
        stored = X.read_results(root)
        mine = [(k[0], r['answer']) for k, r in stored.items()
                if k[0] in ('test.compile-one', 'test.compile-two')]
        ok(sorted(mine) == [('test.compile-one', X.COMPILES),
                            ('test.compile-two', X.REFUSED)],
           'and each answer is stored under its fact, with the source as its '
           'call', mine)
        try:
            X.run(root, [], pids=[5151], programs=programs[:1],
                  spawn=emulator_that_compiles([]))
            ok(False, 'a program already answered is refused')
        except X.ExamplesError as e:
            ok('reuse a call' in str(e),
               'a program already answered is refused before anything '
               'launches', e)
        shutil.rmtree(root, ignore_errors=True)
    finally:
        X.compiled = real_compiled
        for k, v in saved_env.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    print('-- the program')
    the_program()
    print('\n-- the answers')
    the_answers()
    print('\n-- an example with nothing to record')
    the_no_value_rows()
    print('\n-- the firmware a result is stored with')
    the_firmware()
    print('\n-- an answer the kit must not keep')
    the_never_stored()
    print('\n-- results.tsv and relabelling')
    the_results_file()
    print('\n-- a program measured again')
    the_program_measured_again()
    print('\n-- which calculator the next window opens')
    the_next_window()
    print('\n-- the run, with a stand-in for the emulator')
    the_run()
    print('\n-- evidence is never lost or replaced in silence')
    the_evidence_kept()
    print('\n-- does a program compile')
    the_compile_questions()
    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
