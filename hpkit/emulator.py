# -*- coding: utf-8 -*-
"""The Virtual Calculator: install into it, and read back what it has.

    Documents\\HP Prime\\Calculators\\<instance>\\

is the emulator's **own file system**, not a mirror. This is the opposite of
the Connectivity Kit folder of the same shape, which is a mirror and installs
nothing -- see deploy.md. Measured on 2026-09-06 against the Virtual
Calculator 2.4.15515, by copying a `.hpprgm` that `hpprime write` had
generated into an idle instance folder:

  - it appears in the Program Catalogue on the next launch,
  - its source arrives intact, the editor's Check says "No errors",
  - it runs: the test program returned 385, the sum of squares 1..10,
  - an `.hpappdir` copied the same way appears in the Application Library.

Three rules came out of the same session, and the tool is built around them:

  - **The folder is read at launch.** A file copied in while the emulator is
    running does not appear until it is restarted. This is why `install`
    refuses to copy into a running emulator unless you pass --restart.
  - **Files it does not know are left alone.** A second program copied in
    mid-session was still there, byte for byte, after a clean exit.
  - **It writes back.** After the calculator compiled the program, the file
    on disk grew from 1,388 to 1,484 bytes: the emulator had added the
    compiled block, exactly as a G2 does. That is what makes `pull` possible.

Process control (finding, closing and launching the emulator) is written for
Windows, which is where all of the above was measured. Everywhere else the
file half still works and the tool asks you to close the emulator yourself.
"""
from __future__ import unicode_literals
import os, re, shutil, subprocess, sys, time

EXE = 'HPPrime.exe'

# Where an installer puts the emulator. Both are real: 64-bit and 32-bit.
EXE_DIRS = (
    r'C:\Program Files\HP\HP Prime Virtual Calculator',
    r'C:\Program Files (x86)\HP\HP Prime Virtual Calculator',
)

# What may be copied into a calculator. Anything else is a mistake worth
# catching here rather than on the calculator, where nothing would be said.
PROGRAM = '.hpprgm'
APPDIR = '.hpappdir'
MATRIX = '.hpmat'


class EmulatorError(Exception):
    pass


# ------------------------------------------------------------------ finding

def find_root():
    """-> the Calculators folder of the Virtual Calculator, or None.

    HPPRIME_EMU_ROOT overrides it, which is what the tests use.
    """
    env = os.environ.get('HPPRIME_EMU_ROOT')
    if env:
        return env if os.path.isdir(env) else None
    home = os.path.expanduser('~')
    for docs in ('Documents', 'Documentos'):
        found = calculators_in(os.path.join(home, docs, 'HP Prime'))
        if found:
            return found
    return None


def find_ck_root():
    """-> the Connectivity Kit's calculators folder, or None.

    It is a mirror, not a mailbox (deploy.md section 2): useful for reading
    what a connected calculator holds, never for installing. HPPRIME_CK_ROOT
    overrides it, which is what the tests use.
    """
    env = os.environ.get('HPPRIME_CK_ROOT')
    if env:
        return env if os.path.isdir(env) else None
    home = os.path.expanduser('~')
    for docs in ('Documents', 'Documentos'):
        found = calculators_in(os.path.join(home, docs, 'HP Connectivity Kit'))
        if found:
            return found
    return None


# The name the calculators folder has, in the languages it has been seen in.
# The Connectivity Kit names its folders in the language it is set to --
# Calculadoras on a Spanish install -- while the Virtual Calculator kept
# Calculators on the same machine. A name that is not here is found by what
# the folder holds.
CALCULATORS = ('Calculators', 'Calculadoras')


def calculators_in(base):
    """-> the folder inside `base` whose own folders are calculators, or
    None. A known name first; otherwise the first folder, in name order,
    holding something a calculator folder holds."""
    if not os.path.isdir(base):
        return None
    for name in CALCULATORS:
        path = os.path.join(base, name)
        if os.path.isdir(path):
            return path
    for name in sorted(os.listdir(base)):
        path = os.path.join(base, name)
        if os.path.isdir(path) and _holds_calculators(path):
            return path
    return None


def _holds_calculators(folder):
    """True if a folder inside looks like a calculator: it holds its saved
    settings, an app folder or a program."""
    for name in os.listdir(folder):
        calc = os.path.join(folder, name)
        if name.endswith(APPDIR) or not os.path.isdir(calc):
            continue
        try:
            inside = os.listdir(calc)
        except OSError:
            continue
        if any(e == LIVE_FILE or e.endswith(APPDIR) or e.endswith(PROGRAM)
               for e in inside):
            return True
    return False


def find_exe():
    """-> the path of HPPrime.exe, or None. HPPRIME_EMU_EXE overrides."""
    env = os.environ.get('HPPRIME_EMU_EXE')
    if env:
        return env if os.path.isfile(env) else None
    for folder in EXE_DIRS:
        path = os.path.join(folder, EXE)
        if os.path.isfile(path):
            return path
    return None


def instances(root):
    """-> the calculator folders inside the root, sorted."""
    if not root or not os.path.isdir(root):
        return []
    return sorted(d for d in os.listdir(root)
                  if os.path.isdir(os.path.join(root, d)))


def pick(root, name=None):
    """-> the folder of one calculator.

    With several instances and no name this raises rather than guessing:
    installing into the wrong calculator is silent, and looks exactly like
    installing into the right one and nothing happening.
    """
    if not root:
        raise EmulatorError(
            'the Virtual Calculator folder was not found under Documents/.\n'
            'Install the emulator, run it once so it creates a calculator, '
            'or set HPPRIME_EMU_ROOT.')
    found = instances(root)
    if not found:
        raise EmulatorError('%s has no calculator in it yet. Run the '
                            'emulator once.' % root)
    if name:
        if name not in found:
            raise EmulatorError('no calculator called "%s". There is: %s'
                                % (name, ', '.join(found)))
        return os.path.join(root, name)
    if len(found) > 1:
        raise EmulatorError(
            'there are %d calculators (%s). Say which one with --calc NAME.'
            % (len(found), ', '.join(found)))
    return os.path.join(root, found[0])


# ------------------------------------------------------- the process itself

def running():
    """-> the pids of the running emulators. [] if none, or if this platform
    is one where it was never measured."""
    if not sys.platform.startswith('win'):
        return []
    try:
        out = subprocess.check_output(
            ['tasklist', '/FI', 'IMAGENAME eq ' + EXE, '/FO', 'CSV', '/NH'],
            stderr=subprocess.STDOUT)
    except Exception:
        return []
    pids = []
    for line in out.decode('utf-8', 'replace').splitlines():
        m = re.match(r'"%s","(\d+)"' % re.escape(EXE), line.strip(),
                     re.IGNORECASE)
        if m:
            pids.append(int(m.group(1)))
    return pids


def close(timeout=20):
    """Ask every running emulator to close, and wait for it.

    `taskkill` without /F sends the window a close request, which is the
    same thing as clicking the X: the emulator saves its calculator on the
    way out. Never /F here -- that would lose whatever it had not written.
    """
    pids = running()
    if not pids:
        return 0
    if not sys.platform.startswith('win'):
        raise EmulatorError('closing the emulator is only implemented on '
                            'Windows. Close it yourself and run this again.')
    subprocess.call(['taskkill', '/IM', EXE],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not running():
            return len(pids)
        time.sleep(0.4)
    raise EmulatorError('the emulator did not close within %ds. It may be '
                        'showing a dialog; close it by hand.' % timeout)


def launch(exe=None):
    """Start the emulator. -> the path started."""
    exe = exe or find_exe()
    if not exe:
        raise EmulatorError('%s was not found. Pass --exe PATH, or set '
                            'HPPRIME_EMU_EXE.' % EXE)
    subprocess.Popen([exe], cwd=os.path.dirname(exe))
    return exe


# An emulator writes its calculator's `calc.hpsettings` when it closes, and
# that is the fingerprint that says which of several calculators it had.
# Measured: a launch at 17:52:23 was preceded by a write at 17:52:22, which
# was the previous emulator shutting down -- so this is a closing signature,
# not an opening one, and nothing here can tell you which calculator a
# running emulator has without closing it.
LIVE_FILE = 'calc.hpsettings'


# Which calculator a window opens is not the kit's choice. The emulator names
# its calculators Prime, Prime_1, Prime_2... (the program holds 'Prime_%1'),
# and each window holds a lock on one: a new window takes the first whose
# lock nobody holds, and makes the folder if it is not there, so no window is
# ever opened on a calculator with any other name. The locks are Qt lock
# files, HPEmuInstance.lock for Prime and HPEmuInstance1.lock for Prime_1, in
# a folder beside Calculators (Temporal, on a Spanish install), each holding
# the pid of the window that has it, and gone when that window closes.
# Measured 2026-09-11 on 2.4.15515: deploy.md section 1.
LOCK = re.compile(r'^HPEmuInstance(\d*)\.lock$')


def instance_name(n):
    """0 -> Prime, 3 -> Prime_3."""
    return 'Prime' if n == 0 else 'Prime_%d' % n


def instance_number(name):
    """Prime -> 0, Prime_3 -> 3, and None for a name no window opens."""
    if name == 'Prime':
        return 0
    m = re.match(r'^Prime_([1-9][0-9]*)$', name or '')
    return int(m.group(1)) if m else None


def held(root, pids=None):
    """-> {instance number: pid} for the locks a running emulator holds.
    `pids` are the running emulators, found when not given."""
    pids = running() if pids is None else pids
    base = os.path.dirname(os.path.abspath(root))
    out = {}
    try:
        subs = sorted(os.listdir(base))
    except OSError:
        return out
    for sub in subs:
        folder = os.path.join(base, sub)
        try:
            names = os.listdir(folder) if os.path.isdir(folder) else []
        except OSError:
            continue
        for name in names:
            m = LOCK.match(name)
            if not m:
                continue
            try:
                with open(os.path.join(folder, name), 'rb') as f:
                    pid = int(f.read().split(b'\n', 1)[0])
            except (OSError, ValueError):
                continue
            if pid in pids:
                out[int(m.group(1) or 0)] = pid
    return out


def next_opens(root, pids=None):
    """-> the calculator a window launched now would open, or None when a
    running emulator holds no lock that can be found."""
    pids = running() if pids is None else pids
    taken = held(root, pids)
    if len(set(taken.values())) != len(set(pids)):
        return None
    n = 0
    while n in taken:
        n += 1
    return instance_name(n)


def _stamps(root):
    out = {}
    for name in instances(root):
        path = os.path.join(root, name, LIVE_FILE)
        if os.path.isfile(path):
            out[name] = os.path.getmtime(path)
    return out


def _changed(root, before):
    """-> the calculator whose saved state moved since `before`, or None."""
    for name, when in sorted(_stamps(root).items()):
        if name not in before or when > before[name]:
            return name
    return None


# ----------------------------------------------------------------- contents

def contents(calc):
    """-> (programs, apps): the names the calculator has, sorted."""
    programs, apps = [], []
    for entry in sorted(os.listdir(calc)):
        if entry.endswith(PROGRAM):
            programs.append(entry[:-len(PROGRAM)])
        elif entry.endswith(APPDIR):
            # The built-in apps are stored with a leading &. They are not
            # yours and listing them as if they were is noise.
            if not entry.startswith('&'):
                apps.append(entry[:-len(APPDIR)])
    return programs, apps


def source_of(calc, name):
    """-> the PPL source of one installed program."""
    from hpkit import program
    path = os.path.join(calc, name + PROGRAM)
    if not os.path.isfile(path):
        programs = contents(calc)[0]
        raise EmulatorError('no program called "%s" on that calculator.%s'
                            % (name, ('\nIt has: ' + ', '.join(programs))
                               if programs else ''))
    return program.read(open(path, 'rb').read())[0]


# ---------------------------------------------------------------- installing

def _check_one(path):
    """Refuse now what the calculator would refuse in silence."""
    from hpkit import program
    path = path.rstrip('/\\')
    name = os.path.basename(path)
    if name.endswith(APPDIR):
        if not os.path.isdir(path):
            raise EmulatorError('%s is not a folder' % path)
        stem = name[:-len(APPDIR)]
        if not os.path.isfile(os.path.join(path, stem + '.hpapp')):
            raise EmulatorError('%s has no %s.hpapp in it: `hpprime build` '
                                'makes the whole folder' % (path, stem))
        return path, name
    if not os.path.isfile(path):
        raise EmulatorError('%s does not exist' % path)
    if name.endswith(PROGRAM):
        try:
            program.read(open(path, 'rb').read())
        except Exception as e:
            raise EmulatorError('%s is not a program the calculator would '
                                'read (%s).\nIf it is source, build it '
                                'first: hpprime write %s -o %s.hpprgm'
                                % (path, e, path,
                                   os.path.splitext(name)[0]))
        return path, name
    if name.endswith(MATRIX):
        return path, name
    raise EmulatorError(
        '%s: a calculator takes .hpprgm programs, .hpappdir apps and .hpmat '
        'matrices.\nA .txt source has to be built first: hpprime write %s '
        '-o NAME.hpprgm' % (path, path))


def install(paths, calc):
    """Copy files into a calculator folder. -> [(name, bytes)] installed.

    The emulator must not be running: it reads this folder when it starts.
    """
    checked = [_check_one(p) for p in paths]
    done = []
    for src, name in checked:
        dest = os.path.join(calc, name)
        if os.path.isdir(src):
            if os.path.isdir(dest):
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            size = sum(os.path.getsize(os.path.join(dest, f))
                       for f in os.listdir(dest)
                       if os.path.isfile(os.path.join(dest, f)))
        else:
            shutil.copyfile(src, dest)
            size = os.path.getsize(dest)
        done.append((name, size))
    return done


# ------------------------------------------------------- calculators to burn

# The `settings` file of a calculator, 164 bytes, carries its identity: for a
# physical Prime, its serial number, as a run of ASCII inside an otherwise
# empty block. Two calculators with the same one is not a state anybody has
# measured the consequences of, so a clone gets its own.
SETTINGS = 'settings'
SETTINGS_MAGIC = b'\x61\x8d\x70\xe7'

def state_dir():
    """Where the kit keeps what it has to remember between runs.

    HPPRIME_KIT_STATE overrides it, which is what the tests use so that
    running them does not leave anything in your home folder.
    """
    return (os.environ.get('HPPRIME_KIT_STATE')
            or os.path.join(os.path.expanduser('~'), '.hp-prime-kit'))


# Where `emu new` keeps a copy of each calculator it makes, so `emu reset`
# has something to go back to. Outside the Calculators folder on purpose:
# the emulator reads every directory in there as a calculator.
def snapshots():
    return os.path.join(state_dir(), 'calculators')


def _reserialize(data, serial):
    """-> the settings file with a different identity in it.

    The serial is found rather than assumed at a fixed offset: one file was
    measured, and one file is not a format.
    """
    if len(data) < 8 or data[:4] != SETTINGS_MAGIC:
        return None
    m = re.search(rb'[0-9A-Za-z]{8,}', data)
    if not m:
        return None
    old = m.group(0)
    new = serial.encode('ascii')[:len(old)].ljust(len(old), b'0')
    return data[:m.start()] + new + data[m.end():]


def _new_serial(seed):
    import hashlib
    return hashlib.sha1(seed.encode('utf-8')).hexdigest().upper()


def create(root, name, source=None, keep_content=False):
    """Clone a calculator, so experiments happen somewhere that does not
    matter. -> the new folder.

    Cloned from a configured one, because a calculator folder without a
    saved state never finishes its first run: the emulator asks for a
    language, is told, and asks again on the next unlock. Measured on an
    instance the emulator had created but never been used on.
    """
    if not name or not re.match(r'^[A-Za-z0-9_-]+$', name):
        raise EmulatorError('"%s" is not a good name for a calculator. '
                            'Letters, digits, - and _.' % name)
    dest = os.path.join(root, name)
    if os.path.exists(dest):
        raise EmulatorError('%s already exists' % dest)
    src = pick(root, source) if source else pick(root)
    if os.path.abspath(src) == os.path.abspath(dest):
        raise EmulatorError('a calculator cannot be cloned from itself')

    os.makedirs(dest)
    for entry in sorted(os.listdir(src)):
        here = os.path.join(src, entry)
        # A fresh calculator, not a copy of your work: the built-in apps
        # (stored with a leading &) come along, your programs and apps do
        # not.
        if not keep_content:
            if entry.endswith(PROGRAM):
                continue
            if entry.endswith(APPDIR) and not entry.startswith('&'):
                continue
        if os.path.isdir(here):
            shutil.copytree(here, os.path.join(dest, entry))
        else:
            shutil.copyfile(here, os.path.join(dest, entry))

    settings = os.path.join(dest, SETTINGS)
    if os.path.isfile(settings):
        data = open(settings, 'rb').read()
        fresh = _reserialize(data, _new_serial(name))
        if fresh:
            with open(settings, 'wb') as f:
                f.write(fresh)

    keep = os.path.join(snapshots(), name)
    if os.path.isdir(keep):
        shutil.rmtree(keep)
    shutil.copytree(dest, keep)
    return dest


def reset(root, name):
    """Put a cloned calculator back to how `emu new` left it."""
    keep = os.path.join(snapshots(), name)
    if not os.path.isdir(keep):
        raise EmulatorError(
            '"%s" was not made by `hpprime emu new`, so there is nothing to '
            'go back to.\nMade ones: %s'
            % (name, ', '.join(made()) or 'none'))
    dest = os.path.join(root, name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    shutil.copytree(keep, dest)
    return dest


def remove(root, name, force=False):
    """Delete a cloned calculator. Refuses one it did not make."""
    keep = os.path.join(snapshots(), name)
    if not os.path.isdir(keep) and not force:
        raise EmulatorError(
            '"%s" was not made by `hpprime emu new`. If you really mean to '
            'delete a calculator you set up yourself, --force says so.' % name)
    dest = os.path.join(root, name)
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    if os.path.isdir(keep):
        shutil.rmtree(keep)
    return dest


def which_opens(root, exe=None):
    """-> the calculator the emulator comes up on, asking it if need be.

    With one calculator there is nothing to ask. With several, the only way
    to know is to open one and see which folder it starts writing, so that
    is what this does -- and remembers, because the answer only changes when
    the set of calculators does.
    """
    found = instances(root)
    if len(found) == 1:
        return found[0]
    if not found:
        raise EmulatorError('%s has no calculator in it yet.' % root)

    name = remembered_open(root)
    if name:
        return name

    # Open one, let it settle, close it: the calculator it had is the one
    # whose saved state moved.
    close()
    before = _stamps(root)
    launch(exe)
    time.sleep(12)
    close()
    name = _changed(root, before)
    if not name:
        raise EmulatorError('could not tell which calculator the emulator '
                            'opened. Say which one with --calc.')
    if not os.path.isdir(state_dir()):
        os.makedirs(state_dir())
    with open(os.path.join(state_dir(), 'opens.txt'), 'w') as f:
        f.write('%s\n%s' % (','.join(found), name))
    return name


def remembered_open(root):
    """-> what which_opens() worked out last time, if the calculators are
    still the same ones. None rather than going and finding out."""
    path = os.path.join(state_dir(), 'opens.txt')
    if not os.path.isfile(path):
        return None
    try:
        was, name = open(path).read().split('\n', 1)
    except ValueError:
        return None
    found = instances(root)
    return name if was == ','.join(found) and name in found else None


def made():
    """-> the calculators `emu new` has made, whether or not they still
    exist."""
    keep = snapshots()
    if not os.path.isdir(keep):
        return []
    return sorted(d for d in os.listdir(keep)
                  if os.path.isdir(os.path.join(keep, d)))


# ---------------------------------------------------------------------- cli

USAGE_INSTALL = """hpprime install FILES... [--calc NAME] [--restart]

Copy programs, apps and matrices into the Virtual Calculator.

  FILES        .hpprgm programs, .hpappdir app folders, .hpmat matrices
  --calc NAME  which calculator, when there is more than one
  --restart    close the emulator first, then open it again afterwards
  --exe PATH   where HPPrime.exe is, if it is not in the usual place

The emulator reads its folder when it starts, so a file copied into a
running one changes nothing until it is restarted. Rather than let that
happen quietly, this refuses -- pass --restart and it does the whole thing.

For a real calculator, `hpprime send` installs a program on a G2 on its cable,
and an app is a drag in the Connectivity Kit: see docs/topics/deploy.md.
"""

USAGE_PULL = """hpprime pull [NAME] [--calc NAME] [-o FILE] [--diff SRC.txt]

Read back what the Virtual Calculator actually has.

  (no NAME)        list its programs and apps
  NAME             print that program's source, or write it with -o
  --diff SRC.txt   compare it with your source; exits 1 if they differ

The calculator writes each program back to disk with its compiled block, so
what comes out here is what is really installed -- which is not always what
you think you sent.
"""


USAGE_EMU = """hpprime emu list | new NAME | reset NAME | remove NAME

Calculators to experiment on, so your own is not the one you are testing on.

  list              every calculator, which one is running, which are clones
  new NAME          a clone: the machine and its built-in apps, none of your
                    programs. --from SRC to say which one to copy
  reset NAME        back to how `new` left it, whatever you have done since
  remove NAME       delete it

A clone is made from a calculator that has been used, not from nothing: a
folder the emulator has never finished setting up asks for a language on
every unlock and never gets past it. The clone gets its own identity in
`settings`, so it is not a second calculator claiming to be the first.

`reset` is the one that pays: a test that starts from a calculator in a
known state means something, and one that starts from wherever you left it
does not.
"""


def _opt(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        if i + 1 < len(argv):
            return argv[i + 1]
    return default


def cli_install(argv):
    if not argv or '--help' in argv or '-h' in argv:
        print(USAGE_INSTALL)
        return 0 if argv else 2
    calc_name = _opt(argv, '--calc')
    exe = _opt(argv, '--exe')
    restart = '--restart' in argv
    skip = {'--calc', '--exe'}
    files, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in skip:
            i += 2
            continue
        if a.startswith('-'):
            i += 1
            continue
        files.append(a)
        i += 1
    if not files:
        print(USAGE_INSTALL)
        return 2

    # Everything that can be judged without touching anything is judged
    # first. Closing somebody's emulator and only then telling them they
    # passed a .txt would be a poor trade.
    try:
        calc = pick(find_root(), calc_name)
        for path in files:
            _check_one(path)
    except EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    try:
        live = running()
        if live and not restart:
            print('The emulator is running (%d instance(s)), and it reads its'
                  % len(live))
            print('folder only when it starts. Either close it and run this')
            print('again, or let the tool do it:')
            print('')
            same = ' '.join(files)
            if calc_name:
                same += ' --calc ' + calc_name
            print('  hpprime install %s --restart' % same)
            return 1
        closed = close() if live else 0
        if closed:
            print('closed %d emulator instance(s)' % closed)
    except EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    failed = None
    try:
        done = install(files, calc)
    except (EmulatorError, EnvironmentError) as e:
        failed, done = e, []

    for name, size in done:
        print('installed %-28s %7d bytes' % (name, size))
    if done:
        print('into %s' % calc)

    if restart:
        # Even after a failed copy: the emulator was open when this started,
        # and leaving it shut is not an outcome anyone asked for.
        try:
            print('opening %s' % launch(exe))
        except EmulatorError as e:
            print('ERROR: %s' % e)
            return 1
        # Which calculator it comes up on is its own choice, and worth
        # saying when it is not the one just written to.
        root = os.path.dirname(calc)
        takes = remembered_open(root)
        wanted = os.path.basename(calc)
        if takes and takes != wanted:
            print('')
            print('note: it opens on %s, not %s. Your files are on %s.'
                  % (takes, wanted, wanted))
            print('`hpprime emu list` says which is which.')
    if failed:
        print('ERROR: %s' % failed)
        return 1
    if not restart:
        print('')
        print('Open the emulator and it will be there:')
        print('  [Shift][Program] for a program, [Apps] for an app.')
    return 0


def cli_pull(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE_PULL)
        return 0
    from hpkit import program
    calc_name = _opt(argv, '--calc')
    out = _opt(argv, '-o')
    diff = _opt(argv, '--diff')
    skip = {'--calc', '-o', '--diff'}
    names, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in skip:
            i += 2
            continue
        if a.startswith('-'):
            i += 1
            continue
        names.append(a)
        i += 1

    try:
        calc = pick(find_root(), calc_name)
    except EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    if not names:
        programs, apps = contents(calc)
        print('%s' % calc)
        print('  programs  %s' % (', '.join(programs) if programs else '-'))
        print('  apps      %s' % (', '.join(apps) if apps else '-'))
        if running():
            print('')
            print('(the emulator is running: what is on disk is what it has')
            print(' saved so far, which can be behind what is on its screen)')
        return 0

    try:
        text = source_of(calc, names[0])
    except EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    if diff:
        import io
        mine = io.open(diff, encoding='utf-8').read()
        same = program.normalize_source(mine) == program.normalize_source(text)
        print('%s %s %s' % (names[0], '==' if same else '!=', diff))
        if not same:
            print('what is installed is not what that file says. `hpprime '
                  'pull %s -o installed.txt` to look at it.' % names[0])
        return 0 if same else 1

    if out:
        import io
        with io.open(out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        print('%s -> %s  (%d characters)' % (names[0], out, len(text)))
        return 0
    sys.stdout.write(text if text.endswith('\n') else text + '\n')
    return 0


def cli_emu(argv):
    if not argv or '--help' in argv or '-h' in argv:
        print(USAGE_EMU)
        return 0 if argv else 2
    sub, rest = argv[0], argv[1:]
    names = [a for a in rest if not a.startswith('-')]
    # --from SRC takes a value, so it is not one of the names.
    source = _opt(rest, '--from')
    if source in names:
        names.remove(source)

    root = find_root()
    try:
        if sub == 'list':
            if not root:
                print('the Virtual Calculator folder was not found under '
                      'Documents/.')
                return 1
            live = running()
            clones = made()
            print('%s' % root)
            for name in instances(root):
                calc = os.path.join(root, name)
                programs, apps = contents(calc)
                print('  %-16s %2d program(s), %d app(s)%s'
                      % (name, len(programs), len(apps),
                         '   [clone]' if name in clones else ''))
            gone = [c for c in clones if c not in instances(root)]
            if gone:
                print('  (made and since deleted, `emu reset` brings back: '
                      '%s)' % ', '.join(gone))
            if live:
                print('%d emulator(s) running. Which calculator each one has '
                      'is its own choice:' % len(live))
                print('it takes the first instance not already in use.')
            return 0

        if not names:
            print('usage: hpprime emu %s NAME' % sub)
            return 2
        name = names[0]

        if sub == 'new':
            dest = create(root or '', name, source)
            print('made %s' % dest)
            print('  cloned from %s, without its programs and apps'
                  % (source or os.path.basename(pick(root))))
            print('')
            print('  hpprime install PROG.hpprgm --calc %s --restart' % name)
            print('  hpprime emu reset %s        # back to this state' % name)
            return 0
        if sub == 'reset':
            print('reset %s' % reset(root or '', name))
            return 0
        if sub == 'remove':
            print('removed %s' % remove(root or '', name, '--force' in rest))
            return 0
    except EmulatorError as e:
        print('ERROR: %s' % e)
        return 1

    print('unknown: hpprime emu %s\n' % sub)
    print(USAGE_EMU)
    return 2
