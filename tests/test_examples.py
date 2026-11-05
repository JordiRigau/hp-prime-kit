# -*- coding: utf-8 -*-
"""The shipped examples and starters must actually work.

Everything a newcomer copies first is checked here: the starters `hpprime
new` writes, and the examples the documentation points at. If one of them
stops linting or stops computing the right answer, that is the worst kind of
rot, because it is the first thing anybody runs.

    python tests/test_examples.py
"""
from __future__ import unicode_literals
import io, os, re, sys

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
        calls(tmp, 'starter', {'CIRCAREA(2)': 12.566370614359172})
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
    rt = os.path.join(ROOT, 'examples', 'conformance', 'BISROOT.txt')
    lints_clean(rt, 'BISROOT.txt')
    calls(rt, 'conformance', {'BISROOT(4)': 2.0, 'BISROOT(0.25)': 0.5,
                              'BISROOT(-1)': -1.0})

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

    print('\n-- examples/touch')
    th = os.path.join(ROOT, 'examples', 'touch', 'TOUCH.txt')
    lints_clean(th, 'TOUCH.txt')
    # Not loaded here: the interpreter does not read the arrow in B→R,
    # and on the PC no key would end its loops. What it can check is that
    # both programs are exported, and that the linter has no warning.
    text = io.open(th, encoding='utf-8').read()
    found, _ = lint.check_source(th, text)
    ok(not found, 'TOUCH.txt has no warning either',
       '; '.join('%d %s' % (f.line, f.rule) for f in found))
    ok('EXPORT TOUCHEV()' in text and 'EXPORT TOUCHMS()' in text,
       'TOUCH.txt exports TOUCHEV and TOUCHMS')

    print('\n-- examples/glyphs')
    gl = os.path.join(ROOT, 'examples', 'glyphs', 'GLYPHS.txt')
    lints_clean(gl, 'GLYPHS.txt')
    # Not called either: it waits for a key the same way.
    m = interp.Machine()
    m.load_file(gl)
    ok('GLYPHS' in m.funcs, 'GLYPHS parses and loads')

    print('\n-- examples/probe')
    probe = os.path.join(ROOT, 'examples', 'probe', 'main.py')
    bad = appdir.check_imports([probe], [])
    ok(not bad, 'the probe imports nothing MicroPython lacks', str(bad))
    ok(os.path.basename(probe) == 'main.py',
       'the probe is called main.py, which is the entry point')

    guided_path(io.open(starter, encoding='utf-8').read()
                .replace('__NAME__', 'CIRCLE'))

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


PPL_BLOCK = re.compile(r'^```ppl\n(.*?)^```', re.M | re.S)


def _code(text):
    """A program without its comment lines, to compare what a page shows
    with what the starter is."""
    lines = [l.rstrip() for l in text.replace('\r\n', '\n').split('\n')
             if not l.lstrip().startswith('//')]
    return '\n'.join(lines).strip()


def guided_path(starter):
    """Every program on the guided path lints with no error and no warning,
    and loads: the starter together with every block of a step that exports
    something, and a fragment inside a function of its own. The program step 2
    shows is the one `hpprime new` writes."""
    print('\n-- the guided path, docs/start/')
    folder = os.path.join(ROOT, 'docs', 'start')
    for name in sorted(os.listdir(folder)):
        if not name.endswith('.md'):
            continue
        page = io.open(os.path.join(folder, name), encoding='utf-8').read()
        blocks = PPL_BLOCK.findall(page.replace('\r\n', '\n'))
        if name == '02-first-program.md':
            ok(any(_code(b) == _code(starter) for b in blocks),
               '%s shows the program `hpprime new` writes' % name)
        if not blocks:
            continue
        parts = [starter]
        for n, b in enumerate(blocks, 1):
            if _code(b) == _code(starter):
                continue
            if 'EXPORT' in b:
                parts.append(b)
            else:
                parts.append('EXPORT ZFRAG%d()\nBEGIN\n%s\nEND;\n' % (n, b))
        source = '\n'.join(parts)
        found, _ = lint.check_source(name, source)
        ok(not found, '%s: its programs lint with no error and no warning'
           % name, '; '.join('%d %s %s' % (f.line, f.level, f.rule)
                             for f in found))
        try:
            interp.Machine().load(source, name)
            ok(True, '%s: its programs load in the interpreter' % name)
        except Exception as e:
            ok(False, '%s: its programs load in the interpreter' % name,
               str(e))


if __name__ == '__main__':
    sys.exit(main())
