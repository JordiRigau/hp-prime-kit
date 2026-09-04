# -*- coding: utf-8 -*-
"""Run every test suite in the kit and print one summary.

    python tests/run_all.py

Nothing here needs a calculator. The suites that CAN use one -- the .hpprgm
reader against your own binaries, and the number format against your own
data -- look for the Connectivity Kit folder and skip what they cannot find,
so a machine with no calculator gets a pass, not a failure.
"""
from __future__ import unicode_literals
import os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))

SUITES = [
    ('test_lint.py', 'the linter: what it catches, and its false alarms'),
    ('test_interp.py', 'the interpreter: the subset, and where it must fail'),
    ('test_program.py', '.hpprgm: the shipped template, and your binaries'),
    ('test_appdir.py', 'apps: building, and what --check sees'),
    ('test_numbers.py', 'the internal number format and .hpmat'),
    ('test_cli.py', 'the hpprime command, end to end'),
    ('test_examples.py', 'the starters and examples people copy first'),
    ('test_docs.py', 'every link in the documentation resolves'),
]


def main():
    total_pass = total_fail = 0
    failed_suites = []
    for name, what in SUITES:
        path = os.path.join(HERE, name)
        p = subprocess.Popen([sys.executable, path], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT)
        out = p.communicate()[0].decode('utf-8', 'replace')
        m = re.search(r'PASS: (\d+)\s+FAIL: (\d+)', out)
        ok, bad = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        total_pass += ok
        total_fail += bad
        state = 'ok  ' if p.returncode == 0 else 'FAIL'
        print('%s  %-16s %3d passed  %2d failed   %s'
              % (state, name, ok, bad, what))
        if p.returncode != 0:
            failed_suites.append((name, out))

    print('\n%d passed, %d failed, across %d suites'
          % (total_pass, total_fail, len(SUITES)))
    # Two suites walk whatever the Connectivity Kit mirror happens to hold,
    # so the total moves with what is plugged in. A smaller number than last
    # time is not a regression on its own; a failure is.
    print('(test_program and test_numbers also walk your own files, so this'
          ' total\n moves with what the Connectivity Kit has mirrored)')

    for name, out in failed_suites:
        print('\n---- %s ----' % name)
        for line in out.splitlines():
            if 'FAIL' in line or 'Error' in line or 'Traceback' in line:
                print('  ' + line.strip())

    return 1 if failed_suites else 0


if __name__ == '__main__':
    sys.exit(main())
