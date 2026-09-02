# -*- coding: utf-8 -*-
"""The `hpprime` command: one entry point for every tool in the kit.

    hpprime <command> [arguments]

Each command is a thin front for a module in hpkit/, and every module can
still be imported and used directly from Python.
"""
from __future__ import unicode_literals
import io, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
STARTERS = os.path.join(ROOT, 'templates', 'starters')

USAGE = """hpprime <command> [arguments]

Getting started
  doctor                  check this machine: Python, templates, the CK
  new NAME [--python]     write a starter program (or a starter app)

Writing code
  lint FILES...           the errors the Prime's compiler will not explain
  run FILES... --call "F(3)"    run the PPL here, on the PC

Getting it onto the calculator
  write SRC.txt -o PROG.hpprgm  build the binary a calculator accepts
  read PROG.hpprgm [-o out.txt] pull the source back out of a binary
  build NAME FILES...           build an app folder (.hpappdir)
  verify TARGET                 check a .hpprgm or an app folder

Data
  matrix read|write|nums ...    .hpmat files and the internal number format
  templates FOLDER              which of your files can act as a template

`hpprime <command> --help` prints the detail for one command.
"""


def _doctor():
    """Say what works on this machine, and what to do about what does not."""
    from hpkit import program
    problems = 0

    print('Python           %d.%d.%d' % sys.version_info[:3])
    if sys.version_info < (3, 7):
        print('                 WARNING: 3.7 or newer is what this is tested on')

    tpl = program.default_template()
    if tpl:
        try:
            data = open(tpl, 'rb').read()
            src, _, start, _ = program.read(data)
            if program.has_compiled_block(data, start):
                print('code template    templates/code.hpprgm HAS A COMPILED '
                      'BLOCK: unusable')
                problems += 1
            else:
                print('code template    templates/code.hpprgm  (%d bytes, ok)'
                      % len(data))
        except Exception as e:
            print('code template    templates/code.hpprgm is broken: %s' % e)
            problems += 1
    else:
        print('code template    MISSING (templates/code.hpprgm)')
        print('                 -> `hpprime templates <CK folder>` finds one')
        problems += 1

    app_dir = os.path.join(ROOT, 'templates', 'app')
    missing = [f for f in ('python.hpapp', 'blank.hpapp', 'note.hpappnote',
                           'program.hpappprgm')
               if not os.path.isfile(os.path.join(app_dir, f))]
    if missing:
        print('app templates    MISSING: %s' % ', '.join(missing))
        problems += 1
    else:
        print('app templates    templates/app/  (4 files, ok)')

    # The Connectivity Kit mirror. Its absence is not an error: everything
    # except the last step works without it.
    found = None
    for name in ('Documents', 'Documentos'):
        base = os.path.join(os.path.expanduser('~'), name,
                            'HP Connectivity Kit', 'Calculators')
        if os.path.isdir(base):
            found = base
            break
    if found:
        calcs = [d for d in sorted(os.listdir(found))
                 if os.path.isdir(os.path.join(found, d))]
        print('Connectivity Kit %s' % found)
        print('                 %d calculator folder(s): %s'
              % (len(calcs), ', '.join(calcs) if calcs else 'none right now'))
        print('                 (that folder is a MIRROR: copying files into')
        print('                  it installs nothing. Drag onto the')
        print('                  calculator in the CK window instead)')
    else:
        print('Connectivity Kit not found under Documents/')
        print('                 Everything here works without it except the')
        print('                 last step, installing. https://hpcalcs.com')

    # End to end, with no calculator: source -> binary -> source.
    if tpl:
        code = 'EXPORT F()\nBEGIN\n  RETURN 42;\nEND;'
        try:
            out = program.write(open(tpl, 'rb').read(), code)
            assert program.read(out)[0] == code
            from hpkit import interp
            m = interp.Machine()
            m.load(code)
            assert m.call('F') == 42.0
            print('self test        source -> .hpprgm -> source, and the PPL '
                  'runs: ok')
        except Exception as e:
            print('self test        FAILED: %s' % e)
            problems += 1

    print('')
    if problems:
        print('%d problem(s). The lines above say what to do.' % problems)
    else:
        print('Everything the kit needs is in place.')
    return 1 if problems else 0


def _new(argv):
    """Write a starter you can run today, and say what to do with it."""
    args = [a for a in argv if not a.startswith('-')]
    if not args:
        print('usage: hpprime new NAME [--python] [-o DIR]')
        print('       NAME is what the program or app will be called on the')
        print('       calculator: letters and digits, no spaces.')
        return 2
    name = args[0]
    base = args[1] if len(args) > 1 else '.'
    as_python = '--python' in argv

    if not name.replace('_', '').isalnum():
        print('ERROR: "%s" is not a good name. Use letters and digits.' % name)
        return 2

    if as_python:
        folder = os.path.join(base, name)
        if os.path.exists(folder):
            print('ERROR: %s already exists; delete it or pick another name'
                  % folder)
            return 1
        os.makedirs(folder)
        src = io.open(os.path.join(STARTERS, 'main.py'),
                      encoding='utf-8').read()
        dest = os.path.normpath(os.path.join(folder, 'main.py'))
        with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.replace('__NAME__', name))
        print('wrote %s' % dest)
        print('')
        print('Next:')
        print('  hpprime build %s %s' % (name, dest))
        print('  then drag %s.hpappdir onto the calculator in the CK window'
              % name)
        return 0

    dest = os.path.normpath(os.path.join(base, name + '.txt'))
    if os.path.exists(dest):
        print('ERROR: %s already exists; delete it or pick another name'
              % dest)
        return 1
    src = io.open(os.path.join(STARTERS, 'program.txt'),
                  encoding='utf-8').read()
    with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src.replace('__NAME__', name))
    print('wrote %s' % dest)
    print('')
    print('Next:')
    print('  hpprime lint %s' % dest)
    print('  hpprime run %s --call "AREA(2)"' % dest)
    print('  hpprime write %s -o %s.hpprgm' % (dest, name))
    print('  then drag %s.hpprgm onto the calculator in the CK window' % name)
    return 0


def _verify(argv):
    """One verb for two things, because a beginner does not yet know which
    kind of thing they are holding."""
    if not argv:
        print('usage: hpprime verify PROG.hpprgm | MYAPP.hpappdir')
        return 2
    target = argv[0].rstrip('/\\')
    if os.path.isdir(target) or target.endswith('.hpappdir'):
        from hpkit import appdir
        modules = [a for a in argv[1:] if not a.startswith('-')]
        try:
            wrong = appdir.check(target, modules)
        except appdir.AppError as e:
            print('ERROR: %s' % e)
            return 1
        for f, why in wrong:
            print('%s: %s' % (f, why))
        print('\n%s: %d difference(s)' % (target, len(wrong)))
        if not modules:
            print('(no .py files given, so only the wrappers were compared)')
        return 1 if wrong else 0
    from hpkit import program
    return program.cli(['verify'] + list(argv))


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help', 'help'):
        print(USAGE)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]

    if cmd == 'doctor':
        return _doctor()
    if cmd == 'new':
        return _new(rest)
    if cmd == 'verify':
        return _verify(rest)
    if cmd == 'lint':
        from hpkit import lint
        return lint.cli(rest)
    if cmd == 'run':
        from hpkit import interp
        return interp.cli(rest)
    if cmd in ('read', 'write', 'templates'):
        from hpkit import program
        return program.cli([cmd] + rest)
    if cmd == 'build':
        from hpkit import appdir
        return appdir.cli(rest)
    if cmd == 'matrix':
        from hpkit import numbers
        return numbers.cli(rest)

    print('unknown command: %s\n' % cmd)
    print(USAGE)
    return 2


if __name__ == '__main__':
    sys.exit(main())
