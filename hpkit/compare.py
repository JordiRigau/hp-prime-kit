# -*- coding: utf-8 -*-
"""Run the same calls here and on the calculator, and compare the numbers.

    hpprime compare lib.txt --call "CIRCAREA(2)" --call "FN(3,350)"

`hpprime run` executes PPL on the PC. It is the same file the calculator
gets, but it is not the calculator's interpreter, and the only way to know
where the two disagree is to ask both. That has always meant reading numbers
off a screen and typing them back in, which is why it was done rarely.

This does it with a file. A generated wrapper stores each result into a
global matrix; the emulator writes `M9.hpmat` into its calculator folder;
`hpkit.numbers` decodes it. Nothing is read off the screen.

    hpprime compare lib.txt --call "CIRCAREA(2)"     # installs and waits
      -> on the calculator: compile HPKCMP once, run it, close the emulator
    ... and the table appears.

Measured end to end on 2026-09-06 against the selftest example: SELF1 gave
385 on both sides and SELF3 gave 1, with nothing read off the screen. The
matrix is written when the emulator closes -- `M9.hpmat` and the
`calc.hpsettings` that marks the shutdown carried the same timestamp.

**What travels this way is numbers.** A matrix cell holds one, so a call
returning a string or a list is recorded as "it did not give a number",
which is a real answer but not the value. `--mat` picks a different matrix
if M9 is in use.

**Two keypresses are still yours.** Nothing in the Prime starts a program
on its own, so the wrapper has to be run once by hand -- and a program that
arrived as a file has to be compiled once (the editor's `Check`) before its
name is live on Home at all. Both are in deploy.md section 1. Whether an
app's START hook fires on boot, which would remove even that, is not
measured.
"""
from __future__ import unicode_literals
import io, json, os, sys, time

NAME = 'HPKCMP'


def state_file():
    """Where the calls of the last run are remembered, so --collect knows
    what it is collecting."""
    from hpkit import emulator
    return os.path.join(emulator.state_dir(), 'compare.json')


class CompareError(Exception):
    pass


# ------------------------------------------------------------- the harness

def harness(calls, mat=9, name=NAME):
    """-> the PPL wrapper that puts every result into a matrix.

    Each call is wrapped in IFERR and written straight into the cell, so a
    call that raises on the calculator -- or gives back something that is not
    a number -- is recorded rather than stopping the run. Column 1 says
    whether it gave a number, column 2 is the number.
    """
    lines = ['EXPORT %s()' % name, 'BEGIN',
             '  M%d := MAKEMAT(0,%d,2);' % (mat, len(calls))]
    for i, expr in enumerate(calls, 1):
        lines.append('  IFERR M%d(%d,2) := %s; THEN M%d(%d,1) := 0; ELSE '
                     'M%d(%d,1) := 1; END;' % (mat, i, expr, mat, i, mat, i))
    lines.append('  RETURN %d;' % len(calls))
    lines.append('END;')
    return '\n'.join(lines) + '\n'


def program_source(files, calls, mat=9, name=NAME):
    """-> the whole program: your code first, then the wrapper that
    exercises it."""
    parts = []
    for path in files:
        parts.append(io.open(path, encoding='utf-8').read().rstrip('\n'))
    return '\n\n'.join(parts) + '\n\n' + harness(calls, mat, name)


def lint_problems(source):
    """-> the linter's errors: what means this must not be sent to a
    calculator.

    The wrapper needs no exception. A 0 passed to a function your code
    defines, or to one of the calculator's, is read as an argument, so
    `CIRCAREA(0)` there is a legal call and not an index into anything; and
    `one-based` only warns wherever it cannot tell.
    """
    from hpkit import lint
    return [f for f in lint.check_source('<compare>', source)[0]
            if f.level == 'ERROR']


# ------------------------------------------------------------- the PC side

def here(files, calls):
    """-> [(expr, value or None, error or None)] from the PC interpreter."""
    from hpkit import interp
    m = interp.Machine()
    for path in files:
        m.load_file(path)
    out = []
    for expr in calls:
        try:
            tree = interp.Parser(interp.lex(expr), '<--call>').expr()
            value = m.evaluate(tree, {})
        except Exception as e:
            out.append((expr, None, '%s' % e))
            continue
        if isinstance(value, float) or isinstance(value, int):
            out.append((expr, float(value), None))
        else:
            out.append((expr, None, 'not a number: %r' % (value,)))
    return out


# ----------------------------------------------------- the calculator side

def there(calc, calls, mat=9):
    """-> [(value or None, error or None)] out of the calculator's matrix."""
    from hpkit import numbers
    path = os.path.join(calc, 'M%d.hpmat' % mat)
    if not os.path.isfile(path):
        raise CompareError('%s is not there. The calculator writes it when '
                           'it saves, so: run %s on it, then close the '
                           'emulator.' % (path, NAME))
    rows = numbers.read_hpmat(open(path, 'rb').read())
    if len(rows) != len(calls):
        raise CompareError(
            'M%d has %d row(s) and %d call(s) were sent. That matrix is from '
            'something else -- run %s on the calculator, then close the '
            'emulator, then --collect.' % (mat, len(rows), len(calls), NAME))
    out = []
    for row in rows:
        if len(row) < 2 or not row[0]:
            out.append((None, 'the calculator did not get a number'))
        else:
            out.append((float(row[1]), None))
    return out


def verdicts(pc, calc, tol=1e-9):
    """-> [(expr, pc, calculator, verdict)]. verdict is 'same', 'DIFFERENT',
    'both refused', or 'ONE REFUSED'."""
    rows = []
    for (expr, a, ea), (b, eb) in zip(pc, calc):
        if ea and eb:
            verdict = 'both refused'
        elif ea or eb:
            verdict = 'ONE REFUSED'
        elif a == b:
            verdict = 'same'
        else:
            scale = max(abs(a), abs(b), 1.0)
            verdict = 'same' if abs(a - b) <= tol * scale else 'DIFFERENT'
        rows.append((expr, ea or a, eb or b, verdict))
    return rows


# --------------------------------------------------------------- the state

def save_state(d):
    path = state_file()
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, indent=1, sort_keys=True))


def load_state():
    path = state_file()
    if not os.path.isfile(path):
        raise CompareError('there is nothing to collect: run `hpprime '
                           'compare FILE --call "..."` first.')
    with io.open(path, encoding='utf-8') as f:
        return json.loads(f.read())


# ------------------------------------------------------------------ report

def report(rows):
    width = max([len(r[0]) for r in rows] + [4])
    print('')
    print('%-*s  %-18s %-18s %s'
          % (width, 'call', 'here', 'calculator', ''))
    print('%s  %s %s %s' % ('-' * width, '-' * 18, '-' * 18, '-' * 12))
    bad = 0
    for expr, a, b, verdict in rows:
        if verdict in ('DIFFERENT', 'ONE REFUSED'):
            bad += 1
        print('%-*s  %-18s %-18s %s'
              % (width, expr, _fmt(a), _fmt(b), verdict))
    print('')
    if bad:
        print('%d of %d disagree. The PC interpreter and the Prime are not '
              'the same program;' % (bad, len(rows)))
        print('what this found is a place where that matters.')
    else:
        print('%d call(s), all agreeing.' % len(rows))
    return bad


def _fmt(v):
    if isinstance(v, float):
        return repr(v)
    return str(v)


def clean_up(calc):
    """Take the generated program off the calculator once it has answered.

    Left there it is one more name in the catalogue that nobody wrote, and
    the next run would install over it anyway.
    """
    gone = os.path.join(calc, NAME + '.hpprgm')
    if os.path.isfile(gone):
        os.remove(gone)
        return True
    return False


# --------------------------------------------------------------------- cli

USAGE = """hpprime compare FILES... --call "FN(2)" [--call ...] [options]
hpprime compare --collect

Run the same calls here and on the emulator, and compare the numbers.

  --call "FN(2)"  a call to make on both sides. Repeatable
  --calc NAME     which calculator
  --mat N         which matrix carries the results back (default 9)
  --tol X         how close counts as the same (default 1e-9, relative)
  --collect       read the results of a run you have already done
  --no-wait       install and stop, rather than waiting for the emulator
  --keep          leave the generated program on the calculator

Only numbers come back: a call whose answer is a string or a list is
recorded as "did not give a number".
"""


def cli(argv):
    from hpkit import emulator, lint, program
    if not argv or '--help' in argv or '-h' in argv:
        print(USAGE)
        return 0 if argv else 2

    def opt(flag, default=None):
        if flag in argv:
            i = argv.index(flag)
            if i + 1 < len(argv):
                return argv[i + 1]
        return default

    calls, files, skip = [], [], False
    valued = {'--call', '--calc', '--mat', '--tol'}
    for k, a in enumerate(argv):
        if skip:
            skip = False
            continue
        if a in valued:
            if a == '--call':
                calls.append(argv[k + 1])
            skip = True
        elif not a.startswith('-'):
            files.append(a)

    mat = int(opt('--mat', '9'))
    tol = float(opt('--tol', '1e-9'))
    calc_name = opt('--calc')

    # ------------------------------------------------------- collect only
    if '--collect' in argv:
        try:
            state = load_state()
            calc = emulator.pick(emulator.find_root(),
                                 calc_name or state.get('calc'))
            got = there(calc, state['calls'], state['mat'])
        except (CompareError, emulator.EmulatorError) as e:
            print('ERROR: %s' % e)
            return 1
        rows = verdicts(here(state['files'], state['calls']), got,
                        state.get('tol', tol))
        bad = report(rows)
        if '--keep' not in argv:
            clean_up(calc)
        return 1 if bad else 0

    if not files or not calls:
        print(USAGE)
        return 2

    # --------------------------------------------------------- build it
    source = program_source(files, calls, mat)
    problems = lint_problems(source)
    if problems:
        for p in problems:
            print('%s' % p)
        print('the program that would be sent does not pass the linter.')
        return 1

    # Which calculator: the one you named, or -- because you have to be able
    # to type the program's name on it -- the one the emulator actually
    # comes up on, which is not necessarily the first in the list.
    try:
        root = emulator.find_root()
        if not calc_name:
            calc_name = emulator.which_opens(root)
            if len(emulator.instances(root)) > 1:
                print('the emulator opens on %s, so that is where this goes'
                      % calc_name)
        calc = emulator.pick(root, calc_name)
    except emulator.EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    folder = os.path.dirname(state_file())
    if not os.path.isdir(folder):
        os.makedirs(folder)
    built = os.path.join(folder, NAME + '.hpprgm')
    template = program.default_template()
    with open(built, 'wb') as f:
        f.write(program.write(open(template, 'rb').read(), source))

    # The old results must not be read as the new ones.
    stale = os.path.join(calc, 'M%d.hpmat' % mat)
    if os.path.isfile(stale):
        os.remove(stale)

    save_state({'files': [os.path.abspath(f) for f in files], 'calls': calls,
                'mat': mat, 'tol': tol, 'calc': os.path.basename(calc)})

    rc = emulator.cli_install([built, '--calc', os.path.basename(calc),
                               '--restart'])
    if rc:
        return rc

    print('')
    print('On the calculator:')
    print('  [Shift][Program], pick %s, Edit, then Check -- a program that' % NAME)
    print('  arrived as a file is in the catalogue but its name is not live')
    print('  on Home until it has been compiled once.')
    print('  Then Esc to Home, type %s (no brackets) and Enter.' % NAME)
    print('Then close the emulator -- that is when it writes M%d.' % mat)
    if '--no-wait' in argv:
        print('')
        print('  hpprime compare --collect')
        return 0

    print('')
    sys.stdout.write('waiting for the emulator to close ')
    sys.stdout.flush()
    deadline = time.time() + 900
    while time.time() < deadline:
        if not emulator.running():
            break
        time.sleep(1.0)
        sys.stdout.write('.')
        sys.stdout.flush()
    else:
        print('')
        print('gave up waiting. When you have run it: hpprime compare '
              '--collect')
        return 1
    print('')

    try:
        got = there(calc, calls, mat)
    except CompareError as e:
        print('ERROR: %s' % e)
        return 1
    rows = verdicts(here(files, calls), got, tol)
    bad = report(rows)

    if '--keep' not in argv:
        clean_up(calc)
    return 1 if bad else 0
