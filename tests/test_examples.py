# -*- coding: utf-8 -*-
"""The shipped examples and starters must actually work.

Everything a newcomer copies first is checked here: the starters `hpprime
new` writes, and the examples the documentation points at. If one of them
stops linting or stops computing the right answer, that is the worst kind of
rot, because it is the first thing anybody runs.

    python tests/test_examples.py
"""
from __future__ import unicode_literals
import io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import interp, lint, appdir

PASS, FAIL = [0], [0]


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


def lints_clean(path, name):
    text = io.open(path, encoding='utf-8').read()
    found, _ = lint.check_source(path, text)
    errors = [f for f in found if f.level == 'ERROR']
    ok(not errors, '%s passes the linter' % name,
       '; '.join('%s:%d %s' % (f.path, f.line, f.rule) for f in errors))


def calls(path, name, expected):
    """expected: {'F(2)': value}"""
    m = interp.Machine()
    m.load_file(path)
    for call, want in sorted(expected.items()):
        fn = call.split('(')[0]
        args = call[len(fn) + 1:-1]
        args = [float(a) for a in args.split(',')] if args else []
        try:
            got = m.call(fn, *args)
        except Exception as e:
            ok(False, '%s: %s' % (name, call), 'raised %s' % e)
            continue
        if isinstance(want, str):
            good = got == want
        else:
            good = abs(got - want) < 1e-9
        ok(good, '%s: %s -> %r' % (name, call, want), 'gave %r' % got)


def main():
    print('-- the starter `hpprime new` writes')
    starter = os.path.join(ROOT, 'templates', 'starters', 'program.txt')
    text = io.open(starter, encoding='utf-8').read().replace('__NAME__', 'X')
    tmp = os.path.join(HERE, '_starter_tmp.txt')
    with io.open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    try:
        lints_clean(tmp, 'the PPL starter')
        calls(tmp, 'starter', {'AREA(2)': 12.566370614359172})
    finally:
        os.remove(tmp)

    py_starter = os.path.join(ROOT, 'templates', 'starters', 'main.py')
    bad = appdir.check_imports([py_starter], [])
    ok(not bad, 'the Python starter imports nothing MicroPython lacks',
       str(bad))

    print('\n-- examples/selftest')
    st = os.path.join(ROOT, 'examples', 'selftest', 'SELFTEST.txt')
    lints_clean(st, 'SELFTEST.txt')
    calls(st, 'selftest', {'SELF1()': 385.0, 'SELF3()': 1.0})
    m = interp.Machine()
    m.load_file(st)
    ok(len(m.call('SELF2')) == 23,
       'SELF2 is the length SELF3 checks for (23)',
       'it is %d' % len(m.call('SELF2')))

    print('\n-- examples/conformance')
    rt = os.path.join(ROOT, 'examples', 'conformance', 'ROOT.txt')
    lints_clean(rt, 'ROOT.txt')
    calls(rt, 'conformance', {'ROOT(4)': 2.0, 'ROOT(0.25)': 0.5,
                              'ROOT(-1)': -1.0})

    print('\n-- examples/apptest')
    at = os.path.join(ROOT, 'examples', 'apptest', 'APPTEST.txt')
    lints_clean(at, 'APPTEST.txt')
    calls(at, 'apptest', {'ATSUM()': 385.0})

    print('\n-- examples/keymap')
    km = os.path.join(ROOT, 'examples', 'keymap', 'KEYMAP.txt')
    lints_clean(km, 'KEYMAP.txt')
    # Not called here on purpose: on the PC GETKEY always reports "no key",
    # so its wait loop would never end. Loading it still has to work.
    m = interp.Machine()
    m.load_file(km)
    ok('KEYMAP' in m.funcs, 'KEYMAP parses and loads')

    print('\n-- examples/strings')
    for name in ('SPROBE.txt', 'TWTEST.txt'):
        path = os.path.join(ROOT, 'examples', 'strings', name)
        lints_clean(path, name)
    # Not run here: these call the very functions the interpreter does not
    # cover. That is the point of them.

    print('\n-- examples/probe')
    probe = os.path.join(ROOT, 'examples', 'probe', 'main.py')
    bad = appdir.check_imports([probe], [])
    ok(not bad, 'the probe imports nothing MicroPython lacks', str(bad))
    ok(os.path.basename(probe) == 'main.py',
       'the probe is called main.py, which is the entry point')

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
