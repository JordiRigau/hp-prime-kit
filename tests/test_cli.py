# -*- coding: utf-8 -*-
"""Tests for the `hpprime` command, end to end.

This is the path a newcomer actually walks: new -> lint -> run -> write ->
read. If it breaks, the first thing anybody tries breaks, so it is worth a
test of its own.

    python tests/test_cli.py
"""
from __future__ import unicode_literals
import io, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import cli, program

PASS, FAIL = [0], [0]


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


class quiet(object):
    """The commands print; the tests care about exit codes and files."""

    def __enter__(self):
        self.old = sys.stdout
        sys.stdout = io.StringIO() if str is not bytes else io.BytesIO()
        return self

    def __exit__(self, *exc):
        self.text = sys.stdout.getvalue()
        sys.stdout = self.old
        return False


def main():
    tmp = tempfile.mkdtemp(prefix='hpcli_')
    here = os.getcwd()
    try:
        os.chdir(tmp)

        with quiet() as q:
            rc = cli.main(['new', 'DEMO'])
        ok(rc == 0 and os.path.isfile('DEMO.txt'), 'new writes DEMO.txt')
        ok('hpprime lint' in q.text, 'and says what to do next')

        with quiet():
            rc = cli.main(['new', 'DEMO'])
        ok(rc == 1, 'new refuses to overwrite an existing file')

        with quiet():
            rc = cli.main(['new', 'bad name'])
        ok(rc == 2, 'new refuses a name with a space in it')

        with quiet() as q:
            rc = cli.main(['lint', 'DEMO.txt'])
        ok(rc == 0, 'the starter passes the linter')
        ok('0 error(s)' in q.text, 'with no errors reported', q.text.strip())

        with quiet() as q:
            rc = cli.main(['run', 'DEMO.txt', '--call', 'AREA(2)'])
        ok(rc == 0 and '12.56' in q.text,
           'the starter runs on the PC and AREA(2) is right', q.text.strip())

        with quiet():
            rc = cli.main(['write', 'DEMO.txt', '-o', 'DEMO.hpprgm'])
        ok(rc == 0 and os.path.isfile('DEMO.hpprgm'),
           'write builds the binary with no -t (it finds the template)')

        with quiet():
            rc = cli.main(['verify', 'DEMO.hpprgm'])
        ok(rc == 0, 'verify round-trips the binary it just built')

        with quiet():
            rc = cli.main(['read', 'DEMO.hpprgm', '-o', 'back.txt'])
        source = io.open('DEMO.txt', encoding='utf-8').read()
        back = io.open('back.txt', encoding='utf-8').read()
        ok(rc == 0 and back == program.normalize_source(source),
           'read gives back the source that was written')

        with quiet():
            rc = cli.main(['new', 'PYDEMO', '--python'])
        ok(rc == 0 and os.path.isfile(os.path.join('PYDEMO', 'main.py')),
           'new --python writes a main.py')

        with quiet():
            rc = cli.main(['build', 'PYDEMO',
                           os.path.join('PYDEMO', 'main.py'), '--quiet'])
        ok(rc == 0 and os.path.isdir('PYDEMO.hpappdir'),
           'build makes the .hpappdir')

        with quiet():
            rc = cli.main(['verify', 'PYDEMO.hpappdir',
                           os.path.join('PYDEMO', 'main.py')])
        ok(rc == 0, 'verify says the app folder is current')

        # The failure that only shows on the calculator: the wrapper rewritten
        # with the Python console as its startup view.
        path = os.path.join('PYDEMO.hpappdir', 'PYDEMO.hpapp')
        data = open(path, 'rb').read()
        with open(path, 'wb') as f:
            f.write(data[:-4] + b'\x03\x00\x00\x00')
        with quiet():
            rc = cli.main(['verify', 'PYDEMO.hpappdir',
                           os.path.join('PYDEMO', 'main.py')])
        ok(rc == 1, 'verify catches the rewritten app wrapper')

        with quiet():
            rc = cli.main(['nonsense'])
        ok(rc == 2, 'an unknown command exits 2')

        with quiet() as q:
            rc = cli.main(['--help'])
        ok(rc == 0 and 'doctor' in q.text, '--help lists the commands')

        with quiet():
            rc = cli.main(['doctor'])
        ok(rc == 0, 'doctor is happy with this checkout')
    finally:
        os.chdir(here)
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
