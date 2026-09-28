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
# Where a person's programs go, one folder each; git ignores what is in it.
PROGRAMS = os.path.join(ROOT, 'programs')


def _shown(path):
    """A path as a person should type it: from here when it is below here,
    whole otherwise, and with forward slashes, which every shell passes on
    as they are; Git Bash eats a backslash."""
    try:
        rel = os.path.relpath(path)
    except ValueError:              # another drive, on Windows
        rel = '..'
    shown = os.path.abspath(path) if rel.startswith('..') else rel
    return shown.replace(os.sep, '/')

USAGE = """hpprime <command> [arguments]

Getting started
  doctor                  check this machine: Python, templates, the CK
  new NAME [--python]     write a starter program (or app) in programs/NAME/
  update [--from FILE.zip]      bring a downloaded kit to the latest version

Writing code
  lint FILES...           the errors the Prime's compiler will not explain
  run FILES... --call "F(3)"    run the PPL here, on the PC

Getting it onto the calculator
  write SRC.txt -o PROG.hpprgm  build the binary a calculator accepts
  read PROG.hpprgm [-o out.txt] pull the source back out of a binary
  build NAME FILES...           build an app folder (.hpappdir)
  verify TARGET                 check a .hpprgm or an app folder
  install FILES... [--restart]  put them in the Virtual Calculator
  pull [NAME] [--diff SRC.txt]  read back what it actually has
  emu new|list|reset|remove     calculators to experiment on
  compare FILES... --call "F(2)"  the same call here and on the calculator

Data
  matrix read|write|nums ...    .hpmat files and the internal number format
  templates FOLDER              which of your files can act as a template

Documentation
  docs [--check]                hold docs/ to its format, and regenerate
                                the pages made from the entries
  examples NAMES... | --all     run their examples on the Virtual
                                Calculator, and keep what it answers

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
    # except the last step works without it. Found by what it holds, since
    # the Kit names its folders in its own language.
    from hpkit import emulator
    found = emulator.find_ck_root()
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

    # The Virtual Calculator, which -- unlike the CK folder above -- has a
    # folder you really can write into. Absent is not an error either.
    from hpkit import emulator
    root = emulator.find_root()
    exe = emulator.find_exe()
    if root:
        found_calcs = emulator.instances(root)
        live = emulator.running()
        print('emulator         %s' % root)
        print('                 %d calculator(s): %s'
              % (len(found_calcs),
                 ', '.join(found_calcs) if found_calcs else 'none yet'))
        if len(found_calcs) > 1:
            print('                 more than one, so `install` and `pull`')
            print('                 want --calc NAME')
        print('                 %s'
              % ('running (%d instance(s)): close it, or `hpprime install '
                 '--restart`' % len(live) if live else 'not running'))
        if exe:
            print('                 %s' % exe)
        else:
            print('                 HPPrime.exe NOT found in the usual place')
            print('                 -> `install --exe PATH`, or set '
                  'HPPRIME_EMU_EXE')
    else:
        print('emulator         not found under Documents/')
        print('                 `hpprime install` needs it. Run the Virtual')
        print('                 Calculator once so it makes a calculator.')

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
    """Write a starter you can run today, and say what to do with it.

    It goes in programs/NAME/, a folder of its own where git keeps out, from
    wherever this runs; -o DIR puts it somewhere else instead."""
    args = [a for a in argv if not a.startswith('-')]
    if not args:
        print('usage: hpprime new NAME [--python] [-o DIR]')
        print('       NAME is what the program or app will be called on the')
        print('       calculator: letters and digits, no spaces. It goes in')
        print('       programs/NAME/, or in DIR if you give one.')
        return 2
    name = args[0]
    as_python = '--python' in argv

    if not name.replace('_', '').isalnum():
        print('ERROR: "%s" is not a good name. Use letters and digits.' % name)
        return 2

    if as_python:
        folder = os.path.join(args[1] if len(args) > 1 else PROGRAMS, name)
        if os.path.exists(folder):
            print('ERROR: %s already exists; delete it or pick another name'
                  % _shown(folder))
            return 1
        os.makedirs(folder)
        src = io.open(os.path.join(STARTERS, 'main.py'),
                      encoding='utf-8').read()
        dest = os.path.normpath(os.path.join(folder, 'main.py'))
        with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
            f.write(src.replace('__NAME__', name))
        print('wrote %s' % _shown(dest))
        print('')
        print('Next:')
        print('  hpprime build %s %s -o %s'
              % (name, _shown(dest), _shown(folder)))
        print('  then drag %s onto the calculator in the CK window'
              % _shown(os.path.join(folder, name + '.hpappdir')))
        return 0

    folder = args[1] if len(args) > 1 else os.path.join(PROGRAMS, name)
    dest = os.path.normpath(os.path.join(folder, name + '.txt'))
    if os.path.exists(dest):
        print('ERROR: %s already exists; delete it or pick another name'
              % _shown(dest))
        return 1
    if not os.path.isdir(folder):
        os.makedirs(folder)
    src = io.open(os.path.join(STARTERS, 'program.txt'),
                  encoding='utf-8').read()
    with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
        f.write(src.replace('__NAME__', name))
    built = _shown(os.path.join(folder, name + '.hpprgm'))
    print('wrote %s' % _shown(dest))
    print('')
    print('Next:')
    print('  hpprime lint %s' % _shown(dest))
    print('  hpprime run %s --call "CIRCAREA(2)"' % _shown(dest))
    print('  hpprime write %s -o %s' % (_shown(dest), built))
    print('  then drag %s onto the calculator in the CK window' % built)
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
        rest = [a for a in argv[1:] if not a.startswith('-')]
        modules = [a for a in rest if a.endswith('.py')]
        sources = [a for a in rest if not a.endswith('.py')]
        ppl = appdir.is_ppl_app(target)
        try:
            wrong = appdir.check(target, modules, None, None,
                                 sources[0] if sources else None)
        except appdir.AppError as e:
            print('ERROR: %s' % e)
            return 1
        for f, why in wrong:
            print('%s: %s' % (f, why))
        print('\n%s: %d difference(s)' % (target, len(wrong)))
        # Say what was NOT compared, so a clean result is not read as more
        # than it is.
        if ppl and not sources:
            print("(a PPL app: pass its .txt source to check the program "
                  "itself, not just the wrappers)")
        elif not ppl and not modules:
            print('(no .py files given, so only the wrappers were compared)')
        return 1 if wrong else 0
    from hpkit import program
    return program.cli(['verify'] + list(argv))


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        # A calculator folder can be named with any character, and a console
        # or a pipe on Windows may have no way to show it: print a ? for it
        # rather than stop. Found on a Connectivity Kit mirror whose
        # calculators carried Armenian and CJK characters in their names.
        sys.stdout.reconfigure(errors='replace')
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help', 'help'):
        print(USAGE)
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]

    if cmd == 'doctor':
        return _doctor()
    if cmd == 'new':
        return _new(rest)
    if cmd == 'update':
        from hpkit import update
        return update.cli(rest)
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
    if cmd == 'install':
        from hpkit import emulator
        return emulator.cli_install(rest)
    if cmd == 'pull':
        from hpkit import emulator
        return emulator.cli_pull(rest)
    if cmd == 'emu':
        from hpkit import emulator
        return emulator.cli_emu(rest)
    if cmd == 'compare':
        from hpkit import compare
        return compare.cli(rest)
    if cmd == 'docs':
        from hpkit import docs
        return docs.cli(rest)
    if cmd == 'examples':
        from hpkit import examples
        return examples.cli(rest)

    print('unknown command: %s\n' % cmd)
    print(USAGE)
    return 2


if __name__ == '__main__':
    sys.exit(main())
