# -*- coding: utf-8 -*-
"""Tests for `hpprime update`, on kit folders and ZIPs made here.

An update writes into the folder a person works in, so what it must never
do is tested as hard as what it does: it never writes inside programs/ or
to .claude/settings.local.json, never deletes, never runs in a clone, and
never writes anything from a ZIP that reaches outside the folder. Nothing
here touches the network.

    python tests/test_update.py
"""
from __future__ import unicode_literals
import io, os, shutil, sys, tempfile, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import update

PASS, FAIL = [0], [0]
COMMIT = 'd1271bb200ac2e90ed8dfa10456fa64a6d0882ea'
GITIGNORE = (b'__pycache__/\n*.hpprgm\n!templates/code.hpprgm\n'
             b'programs/*\n!programs/README.md\n')


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


def make_zip(files, prefix='hp-prime-kit-main/', comment=None):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        for rel, content in sorted(files.items()):
            z.writestr(prefix + rel, content)
        if comment:
            z.comment = comment.encode('ascii')
    return buf.getvalue()


def make_kit(folder, files):
    for rel, content in files.items():
        path = os.path.join(folder, *rel.split('/'))
        if not os.path.isdir(os.path.dirname(path)):
            os.makedirs(os.path.dirname(path))
        with open(path, 'wb') as f:
            f.write(content)


def read(folder, rel):
    path = os.path.join(folder, *rel.split('/'))
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return f.read()


# The version on disk, as a download left it and a person then used it.
OLD = {
    'hpprime.py': b'old',
    'hpkit/cli.py': b'same',
    'AGENTS.md': b'same',
    '.gitignore': GITIGNORE,
    'docs/gone.md': b'the kit dropped this',
    'programs/README.md': b'the note as it was',
    'programs/CIRCLE/CIRCLE.txt': b'mine',
    '.claude/settings.local.json': b'mine',
    'STRAY.hpprgm': b'built and left lying',
    'hpkit/__pycache__/cli.pyc': b'cache',
}
# The new version. It carries the person's paths too, to prove that an
# update leaves them alone even then.
NEW = {
    'hpprime.py': b'new',
    'hpkit/cli.py': b'same',
    'AGENTS.md': b'same',
    '.gitignore': GITIGNORE,
    'docs/new.md': b'the kit added this',
    'programs/README.md': b'the note, rewritten',
    'programs/CIRCLE/CIRCLE.txt': b'not yours',
    '.claude/settings.local.json': b'not yours',
}


def main():
    tmp = tempfile.mkdtemp(prefix='hpupdate_')
    try:
        print('-- which paths the new .gitignore marks as not shipped')
        rules = update.ignore_rules(GITIGNORE.decode('ascii'))
        for rel, want in [('hpkit/__pycache__/cli.pyc', True),
                          ('STRAY.hpprgm', True),
                          ('templates/code.hpprgm', False),
                          ('programs/CIRCLE/CIRCLE.txt', True),
                          ('programs/README.md', False),
                          ('docs/gone.md', False)]:
            ok(update.ignored(rel, rules) == want,
               '%s is %s' % (rel, 'ignored' if want else 'not ignored'))

        print('\n-- a dry run')
        kit = os.path.join(tmp, 'kit')
        make_kit(kit, OLD)
        data = make_zip(NEW, comment=COMMIT)
        report, commit = update.update(kit, data, dry_run=True)
        ok(report['changed'] == ['hpprime.py'], 'finds the changed file',
           repr(report['changed']))
        ok(report['added'] == ['docs/new.md'], 'finds the added file',
           repr(report['added']))
        ok(read(kit, 'hpprime.py') == b'old' and
           read(kit, 'docs/new.md') is None, 'and writes nothing')

        print('\n-- the update')
        cli_path = os.path.join(kit, 'hpkit', 'cli.py')
        os.utime(cli_path, (1000000000, 1000000000))
        report, commit = update.update(kit, data)
        ok(read(kit, 'hpprime.py') == b'new', 'a changed file is rewritten')
        ok(os.path.getmtime(cli_path) == 1000000000,
           'an unchanged one is not touched')
        ok(read(kit, 'docs/new.md') == b'the kit added this',
           'a new file is added')
        ok(read(kit, 'programs/README.md') == b'the note as it was' and
           read(kit, 'programs/CIRCLE/CIRCLE.txt') == b'mine',
           'nothing inside programs/ is written, though the ZIP carries it')
        ok(read(kit, '.claude/settings.local.json') == b'mine',
           '.claude/settings.local.json is not written either')
        ok(read(kit, 'docs/gone.md') == b'the kit dropped this',
           'a file the new version lacks is kept')
        ok(report['lacking'] == ['docs/gone.md'],
           'and listed, alone: not the person\'s, not what .gitignore marks',
           repr(report['lacking']))
        ok(commit == COMMIT, 'the commit is read from the ZIP\'s comment')
        again, _ = update.update(kit, data)
        ok(not again['changed'] and not again['added'],
           'a second run finds nothing to do')

        print('\n-- what it refuses')
        clone = os.path.join(tmp, 'clone')
        make_kit(clone, OLD)
        os.mkdir(os.path.join(clone, '.git'))
        try:
            update.update(clone, data)
            ok(False, 'a clone is refused')
        except update.UpdateError as e:
            ok('git pull' in str(e) and read(clone, 'hpprime.py') == b'old',
               'a clone is refused, and nothing written', str(e))

        evil = dict(NEW)
        evil['../outside.txt'] = b'escaped'
        try:
            update.update(kit, make_zip(evil))
            ok(False, 'a ZIP reaching outside is refused')
        except update.UpdateError:
            ok(not os.path.exists(os.path.join(tmp, 'outside.txt')) and
               read(kit, 'hpprime.py') == b'new',
               'a ZIP reaching outside is refused, and nothing written')

        stranger = {'README.md': b'something else'}
        try:
            update.update(kit, make_zip(stranger))
            ok(False, 'a ZIP that is not the kit is refused')
        except update.UpdateError as e:
            ok('not the kit' in str(e), 'a ZIP that is not the kit is refused')

        print('\n-- other shapes of ZIP')
        flat = os.path.join(tmp, 'flat')
        make_kit(flat, OLD)
        report, commit = update.update(flat, make_zip(NEW, prefix=''))
        ok(read(flat, 'hpprime.py') == b'new' and commit is None,
           'a ZIP with no top folder, and no commit, works too')

        print('\n-- the command')
        zpath = os.path.join(tmp, 'main.zip')
        with open(zpath, 'wb') as f:
            f.write(data)
        cmd = os.path.join(tmp, 'cmd')
        make_kit(cmd, OLD)
        saved, out = update.ROOT, sys.stdout
        update.ROOT = cmd
        sys.stdout = io.StringIO() if str is not bytes else io.BytesIO()
        try:
            rc = update.cli(['--from', zpath])
            text = sys.stdout.getvalue()
        finally:
            update.ROOT, sys.stdout = saved, out
        ok(rc == 0 and 'commit d1271bb' in text and 'docs/gone.md' in text,
           'hpprime update --from says the commit and lists what it kept',
           text)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
