# -*- coding: utf-8 -*-
"""Build and check an HP Prime app (.hpappdir) from a PC.

An app is a folder holding three binary wrappers plus the files the app
carries. None of the three wrappers has the app's name inside them: the name
comes from the folder and from the file names. That is why one set of
wrappers works for any app, and why this can generate them.

The ones in templates/app/ come from apps that start correctly on a G2.

    MYAPP.hpappdir/
       MYAPP.hpapp        settings, and THE STARTUP VIEW
       MYAPP.hpappnote    the note
       MYAPP.hpappprgm    the PPL program (empty in a Python app)
       icon.png           optional
       *.py               the modules

WHY THE WRAPPERS ARE REBUILT ON EVERY BUILD

On the way out of an app, the calculator REWRITES them to save its state,
including the view you were last in. If the Connectivity Kit then brings that
folder back to the PC, that state enters your repository, and from then on
the app opens where you left it: with an 03 in the last four bytes of the
.hpapp it opens the Python console instead of its own screen.

That is why the good wrappers live in templates/app/ and are always copied,
and why --check exists.

    hpprime build MYAPP src/*.py --icon icon.png
    hpprime build MYAPP app.txt --ppl
    hpprime build --check MYAPP.hpappdir src/*.py

Options:
    --icon FILE       copied in as icon.png (73x74 is what HP uses)
    --ppl SOURCE      puts a PPL source into the .hpappprgm
    -t TEMPLATE       code .hpprgm for --ppl (defaults to the shipped one)
    --base python|blank|FILE.hpapp   which descriptor is copied
    -o DIR            where to create the folder
    --allow a,b       modules you import and know are there
    --check           writes nothing: compares

--check writes nothing: it says whether the folder is still the one you would
generate. It exits 1 when it is not, so it works as a gate in any script.
"""
from __future__ import unicode_literals
import io, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TEMPLATES = os.path.join(ROOT, 'templates', 'app')

WRAPPERS = ('hpapp', 'hpappnote', 'hpappprgm')

# There are two descriptors, and they are not interchangeable: one says "this
# app is based on the Python app" and the other "this app is blank". Both come
# from apps that start correctly on a G2.
#
#   python.hpapp   188 B. Its last four bytes are the startup view: 01 the
#                  app's own, 03 the Python console.
#   blank.hpapp    124 B, from an app created with Base App: None. That is
#                  the shape a PPL app has.
DESCRIPTORS = {'python': 'python.hpapp', 'blank': 'blank.hpapp'}

# What MicroPython has on the Prime. An import from outside this set does not
# fail when you copy it over: it makes THE APP CLOSE ON STARTUP, silently.
# That is why it is flagged here, on the PC.
#
# `time` is not there: apps that need it bring their own time.py built on
# eval('ticks()').
MICROPYTHON = set("""math cmath array gc micropython hpprime graphic cas
builtins""".split())


class AppError(Exception):
    pass


def _read(p, binary=True):
    if binary:
        f = open(p, 'rb')
    else:
        f = io.open(p, encoding='utf-8')
    try:
        return f.read()
    finally:
        f.close()


def top_level_imports(text):
    """The modules a .py imports OUTSIDE any function.

    Imports inside a function do not count: they only run if it is called,
    and that is the usual way around something that exists on one side only.
    """
    out = []
    for line in text.replace('\r\n', '\n').split('\n'):
        if line[:1] in (' ', '\t'):
            continue
        m = re.match(r'\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))',
                     line)
        if m:
            out.append((m.group(1) or m.group(2)).split('.')[0])
    return out


def check_imports(modules, allowed):
    """-> list of (file, module) that MicroPython would not have."""
    known = set(allowed) | MICROPYTHON
    known |= set(os.path.splitext(os.path.basename(m))[0] for m in modules)
    bad = []
    for m in modules:
        for name in top_level_imports(_read(m, binary=False)):
            if name not in known:
                bad.append((m, name))
    return bad


def app_path(name, base='.'):
    return os.path.join(base, name + '.hpappdir')


def _parts(name, modules, icon, descriptor='python'):
    """-> {name inside the app: source path}."""
    if descriptor in DESCRIPTORS:
        hpapp = os.path.join(TEMPLATES, DESCRIPTORS[descriptor])
    else:
        hpapp = descriptor           # a path to a .hpapp of your own
    parts = {'%s.hpapp' % name: hpapp}
    parts['%s.hpappnote' % name] = os.path.join(TEMPLATES, 'note.hpappnote')
    parts['%s.hpappprgm' % name] = os.path.join(TEMPLATES,
                                                'program.hpappprgm')
    for m in modules:
        parts[os.path.basename(m)] = m
    if icon:
        parts['icon.png'] = icon
    return parts


def build(name, modules, icon=None, base='.', quiet=False,
          descriptor='python'):
    """Create or rebuild the folder. -> path of the folder."""
    folder = app_path(name, base)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    parts = _parts(name, modules, icon, descriptor)
    for rel in sorted(parts):
        src = parts[rel]
        path = os.path.join(folder, rel)
        changed = not os.path.isfile(path) or _read(src) != _read(path)
        shutil.copyfile(src, path)
        if not quiet:
            print('%-24s %7d B%s' % (rel, os.path.getsize(path),
                                     '   REBUILT' if changed else ''))

    # __pycache__ is left by the PC while testing, and means nothing on the
    # calculator: those are CPython .pyc files MicroPython would not read.
    cache = os.path.join(folder, '__pycache__')
    if os.path.isdir(cache):
        shutil.rmtree(cache)
        if not quiet:
            print('%-24s         removed' % '__pycache__')

    if not quiet:
        extra = [f for f in sorted(os.listdir(folder))
                 if f not in parts and not f.startswith('.')]
        if extra:
            print('\nin the folder but not in the recipe (left alone): %s'
                  % ', '.join(extra))
    return folder


def app_name(folder):
    """The app's name, which is its folder's name without the suffix."""
    name = os.path.basename(folder.rstrip('/\\'))
    if name.endswith('.hpappdir'):
        name = name[:-len('.hpappdir')]
    return name


def is_ppl_app(folder, name=None):
    """True if the app's program carries a source, rather than being the
    empty 1152-byte skeleton a Python app has.

    This is how the kind of app is told apart without being told, and it
    matters: a PPL app is built from the blank descriptor and its
    .hpappprgm is expected to differ from the empty template. Checking it
    against a Python app's parts reports two differences that are not
    there.
    """
    from hpkit import program
    path = os.path.join(folder.rstrip('/\\'),
                        '%s.hpappprgm' % (name or app_name(folder)))
    if not os.path.isfile(path):
        return False
    try:
        program.read(_read(path))
        return True
    except Exception:
        return False


def check(folder, modules, icon=None, descriptor=None, ppl_source=None):
    """-> list of (file, what is wrong). Empty if the folder is current.

    `descriptor` defaults to the one the app's own shape implies. Pass
    `ppl_source` to check a PPL app's program against the source it should
    have been built from; without it that file is left alone, because the
    only other thing to compare it with is the empty skeleton, which it is
    correctly not equal to.
    """
    folder = folder.rstrip('/\\')
    name = app_name(folder)
    if not os.path.isdir(folder):
        raise AppError('no such folder: %s' % folder)

    ppl = is_ppl_app(folder, name)
    if descriptor is None:
        descriptor = 'blank' if ppl else 'python'
    program_rel = '%s.hpappprgm' % name

    out = []
    for rel, src in sorted(_parts(name, modules, icon, descriptor).items()):
        path = os.path.join(folder, rel)
        if not os.path.isfile(path):
            out.append((rel, 'not in the app'))
            continue
        if rel == program_rel and ppl:
            problem = _check_ppl_program(path, ppl_source)
            if problem:
                out.append((rel, problem))
            continue
        if _read(src) != _read(path):
            if rel.endswith(WRAPPERS):
                out.append((rel, 'the calculator rewrote it: build the app '
                                 'again'))
            else:
                out.append((rel, 'has diverged from the original'))
    if os.path.isdir(os.path.join(folder, '__pycache__')):
        out.append(('__pycache__', 'does not belong: CPython .pyc files'))
    return out


def _check_ppl_program(path, ppl_source):
    """-> what is wrong with an app's PPL program, or None."""
    from hpkit import program
    if not ppl_source:
        return None
    want = program.normalize_source(
        io.open(ppl_source, encoding='utf-8-sig').read())
    try:
        got = program.read(_read(path))[0]
    except program.UnexpectedFormat as e:
        return 'is not readable as a program: %s' % e
    if got != want:
        return 'holds a different source from %s' % ppl_source
    return None


def put_ppl_program(folder, name, source, template):
    """Put a PPL source into the .hpappprgm, using program.py.

    The skeleton's own .hpappprgm is no use as a template here: it is an
    empty program, with no source block to replace. What is needed is a code
    .hpprgm written by the Connectivity Kit, the same thing `hpprime write`
    asks for -- and the kit ships one.
    """
    from hpkit import program
    tpl = _read(template)
    try:
        _, _, start, _ = program.read(tpl)
    except program.UnexpectedFormat as e:
        raise AppError('template %s is no use: %s' % (template, e))
    if program.has_compiled_block(tpl, start):
        raise AppError('template %s carries %d bytes of compiled block; '
                       'changing its source would leave it out of step. Use '
                       'a code program from the Connectivity Kit'
                       % (template, start - program.HEADER_END))
    text = program.normalize_source(io.open(source, encoding='utf-8').read())
    data = program.write(tpl, text)
    if program.read(data)[0] != text:
        raise AppError('what was written does not read back: do not install it')
    path = os.path.join(folder, '%s.hpappprgm' % name)
    f = open(path, 'wb')
    try:
        f.write(data)
    finally:
        f.close()
    return path


def cli(argv):
    args = [a for a in argv if not a.startswith('-')]
    if not args or '--help' in argv or '-h' in argv:
        print(__doc__)
        return 2

    def opt(*names):
        for n in names:
            if n in argv:
                i = argv.index(n)
                if i + 1 < len(argv):
                    return argv[i + 1]
        return None

    icon = opt('--icon')
    template = opt('-t', '--template')
    base = opt('-o', '--dir') or '.'
    allowed = (opt('--allow') or '').split(',')
    quiet = '--quiet' in argv
    is_ppl = '--ppl' in argv
    # A PPL app is built blank; a Python one inherits from the Python app.
    descriptor = opt('--base') or ('blank' if is_ppl else 'python')
    # Option values are not input files.
    values = set(x for x in (icon, template, base, opt('--allow'),
                             opt('--base')) if x)
    inputs = [a for a in args if a not in values]

    if '--check' in argv:
        folder, rest = inputs[0], inputs[1:]
        # A PPL source among the arguments is what the app's program should
        # hold; .py files are modules. Without --base, the app's own shape
        # says which descriptor to expect.
        try:
            wrong = check(folder,
                          [m for m in rest if m.endswith('.py')],
                          icon, opt('--base'),
                          ([m for m in rest if not m.endswith('.py')] or
                           [None])[0])
        except AppError as e:
            print('ERROR: %s' % e)
            return 1
        for f, why in wrong:
            print('%s: %s' % (f, why))
        print('\n%s: %d difference(s)' % (folder, len(wrong)))
        return 1 if wrong else 0

    name, rest = inputs[0], inputs[1:]
    modules = [m for m in rest if m.endswith('.py')]
    ppl_sources = [m for m in rest if not m.endswith('.py')]

    if is_ppl and not template:
        from hpkit import program
        template = program.default_template()
    if is_ppl and (not ppl_sources or not template):
        print('ERROR: --ppl needs a PPL source and a template.')
        print('       Pass one with -t, or put a code .hpprgm written by the')
        print('       Connectivity Kit at templates/code.hpprgm.')
        return 2

    folder = build(name, modules, icon, base, quiet, descriptor)

    if is_ppl:
        try:
            path = put_ppl_program(folder, name, ppl_sources[0], template)
        except AppError as e:
            print('ERROR: %s' % e)
            return 1
        if not quiet:
            print('%-24s %7d B   from %s'
                  % (os.path.basename(path), os.path.getsize(path),
                     ppl_sources[0]))

    # The entry point of a Python app is main.py, and its code sits at module
    # level: that is what the apps that work do. Without it the app starts
    # and nothing happens.
    if modules and not is_ppl and not any(
            os.path.basename(m) == 'main.py' for m in modules):
        print('WARNING: there is no main.py. The entry point of a Python app '
              'is\n         main.py, and its code runs on import.')

    for path, mod in check_imports(modules, [p for p in allowed if p]):
        print('WARNING: %s imports "%s", which MicroPython on the Prime does '
              'not have.\n         The app would close on startup, silently.'
              % (os.path.basename(path), mod))

    if not quiet:
        print('\n%s is ready. Drag it ONTO the calculator in the Connectivity '
              'Kit window\n(the Calculators\\ folder is a mirror: copying it '
              'there installs nothing).' % folder)
    return 0


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
