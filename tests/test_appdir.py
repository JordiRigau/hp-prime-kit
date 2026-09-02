# -*- coding: utf-8 -*-
"""Tests for the app builder: that the app is built, and that --check sees
what it has to see.

The one that really matters is the startup-view byte. That failure -- the app
opening in the Python console instead of its own screen -- cannot be seen by
reading the code or by compiling anything: it only shows when you open the
app on the calculator. Here it is caught from the PC.

    python tests/test_appdir.py
"""
from __future__ import unicode_literals
import io, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import appdir as A
from hpkit import program as P

PASS, FAIL = [0], [0]


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


def put(path, text):
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def main():
    tmp = tempfile.mkdtemp(prefix='hpapp_')
    try:
        # ------------------------------------------------- the templates
        for f in ('note.hpappnote', 'program.hpappprgm'):
            ok(os.path.isfile(os.path.join(A.TEMPLATES, f)),
               'the %s template is there' % f)
        for key, f in sorted(A.DESCRIPTORS.items()):
            ok(os.path.isfile(os.path.join(A.TEMPLATES, f)),
               'the "%s" descriptor is there (%s)' % (key, f))

        hpapp = open(os.path.join(A.TEMPLATES,
                                  A.DESCRIPTORS['python']), 'rb').read()
        # The last four bytes are the startup view: 01 is the app's own, 03
        # is the Numeric view -- in a Python app, the console.
        ok(hpapp[-4:] == b'\x01\x00\x00\x00',
           "the template starts in the app's view (01), not the console",
           'last 4 bytes: %s' % ' '.join('%02X' % b for b in hpapp[-4:]))
        ok(hpapp[:4] == b'\x7c\x61\x8a\xb2',
           'the .hpapp template starts with the Prime magic')

        # ------------------------------------------------------ building
        src = os.path.join(tmp, 'src')
        os.makedirs(src)
        put(os.path.join(src, 'main.py'), 'import engine\nengine.go()\n')
        put(os.path.join(src, 'engine.py'),
            'from math import sqrt\n\n\ndef go():\n    return sqrt(2)\n')
        modules = [os.path.join(src, 'main.py'), os.path.join(src, 'engine.py')]

        folder = A.build('MYAPP', modules, base=tmp, quiet=True)
        ok(os.path.isdir(folder), 'creates the .hpappdir folder')
        for f in ('MYAPP.hpapp', 'MYAPP.hpappnote', 'MYAPP.hpappprgm',
                  'main.py', 'engine.py'):
            ok(os.path.isfile(os.path.join(folder, f)), 'copies %s' % f)
        ok(open(os.path.join(folder, 'MYAPP.hpapp'), 'rb').read() == hpapp,
           'the wrapper comes out byte for byte like the template')

        ok(A.check(folder, modules) == [],
           'freshly built, --check finds nothing')

        # ------------------------ the calculator rewrites the wrapper
        path = os.path.join(folder, 'MYAPP.hpapp')
        with open(path, 'wb') as f:
            f.write(hpapp[:-4] + b'\x03\x00\x00\x00')
        wrong = dict(A.check(folder, modules))
        ok('MYAPP.hpapp' in wrong,
           'sees the rewritten .hpapp (the Python-console failure)')
        ok('rewrote' in wrong.get('MYAPP.hpapp', ''),
           'and says it was the calculator', repr(wrong.get('MYAPP.hpapp')))

        A.build('MYAPP', modules, base=tmp, quiet=True)
        ok(A.check(folder, modules) == [],
           'rebuilding puts it back')

        # ----------------------------------- a module edited inside the app
        put(os.path.join(folder, 'engine.py'), '# touched by hand\n')
        wrong = dict(A.check(folder, modules))
        ok(wrong.get('engine.py', '').startswith('has diverged'),
           'sees a module that diverged from the original')

        # ---------------------------------------------- a missing module
        os.remove(os.path.join(folder, 'main.py'))
        wrong = dict(A.check(folder, modules))
        ok(wrong.get('main.py') == 'not in the app', 'sees a missing module')

        # ------------------------------------------------- __pycache__
        A.build('MYAPP', modules, base=tmp, quiet=True)
        os.makedirs(os.path.join(folder, '__pycache__'))
        wrong = dict(A.check(folder, modules))
        ok('__pycache__' in wrong, '--check sees the __pycache__')
        A.build('MYAPP', modules, base=tmp, quiet=True)
        ok(not os.path.isdir(os.path.join(folder, '__pycache__')),
           'building removes the __pycache__')

        # ------------------------------------------------- the imports
        put(os.path.join(src, 'clock.py'),
            'import time\nimport math\n\n\ndef f():\n    import json\n')
        bad = A.check_imports([os.path.join(src, 'clock.py')], [])
        names = [m for _, m in bad]
        ok('time' in names,
           'warns about "import time": MicroPython on the Prime has no time')
        ok('math' not in names, 'does not complain about math, which is there')
        ok('json' not in names,
           'does not look at imports inside a function')
        ok(A.check_imports(modules, []) == [],
           'no false alarm for a module importing a sibling')

        # ------------------------------- the blank app descriptor
        blank = A.build('BLANKAPP', [], base=tmp, quiet=True,
                        descriptor='blank')
        d = open(os.path.join(blank, 'BLANKAPP.hpapp'), 'rb').read()
        ok(d == open(os.path.join(A.TEMPLATES,
                                  A.DESCRIPTORS['blank']), 'rb').read(),
           '--base blank copies the blank app descriptor')
        ok(d != hpapp, 'the two descriptors are not the same file')

        # ------------------------------------ a PPL app, with the shipped
        # template: no calculator and no Connectivity Kit needed
        tpl = P.default_template()
        ok(bool(tpl), 'the kit ships a code template')
        if tpl:
            source = os.path.join(tmp, 'app.txt')
            code = 'EXPORT START()\nBEGIN\n  RETURN 1;\nEND;'
            put(source, code)
            path = A.put_ppl_program(folder, 'MYAPP', source, tpl)
            back = P.read(open(path, 'rb').read())[0]
            ok(back == code,
               'the generated .hpappprgm gives back the same source')

        # the empty skeleton is NOT a usable template, and it must say so
        empty = os.path.join(A.TEMPLATES, 'program.hpappprgm')
        source = os.path.join(tmp, 'x.txt')
        put(source, 'EXPORT F()\nBEGIN\n  RETURN 1;\nEND;')
        try:
            A.put_ppl_program(folder, 'MYAPP', source, empty)
            ok(False, 'rejects the empty .hpappprgm as a template')
        except A.AppError:
            ok(True, 'rejects the empty .hpappprgm as a template')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
