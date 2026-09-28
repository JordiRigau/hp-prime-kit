# -*- coding: utf-8 -*-
"""Bring a downloaded copy of the kit up to the latest version.

    hpprime update                    # from GitHub
    hpprime update --from main.zip    # from a ZIP you downloaded yourself
    hpprime update --dry-run          # say what would change, write nothing

A clone updates with `git pull`, and this refuses to run in one. A download
has no git, so this does what the pull would: it fetches the `main` branch as
the ZIP GitHub builds, and writes over the kit's files the ones that changed.

**What is yours stays yours.** Nothing is written inside `programs/`, where a
person's programs go, nor to `.claude/settings.local.json`, and nothing is
ever deleted. A file on disk that the new version no longer has is listed
instead, because an update cannot tell a file the kit dropped from one the
person put there; files matching the new `.gitignore`, which is how the kit
marks what it does not ship, are not listed.

The version: `git archive`, which builds GitHub's ZIPs, writes the commit's
hash as the archive's comment, and GitHub's ZIP of `main` carried it when
this downloaded one on 2026-09-27. Where a ZIP has none, the version is
simply not reported.

Line endings: GitHub's ZIP holds text files with LF. `git archive` converts
text as a checkout would, so on Windows, with the repository's `* text=auto`
and `core.eol` native, a local ZIP holds CRLF even with `core.autocrlf=false`;
updating a download from one of those rewrites nearly every text file, with
the same content. A local ZIP like GitHub's takes
`git -c core.autocrlf=false -c core.eol=lf archive`.
"""
from __future__ import unicode_literals
import fnmatch, io, os, re, sys, zipfile

URL = 'https://github.com/JordiRigau/hp-prime-kit/archive/refs/heads/main.zip'
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# The person's: never written, never listed.
THEIRS_DIR = 'programs'
THEIRS_FILES = ('.claude/settings.local.json',)
# A ZIP without these at its top is not the kit, and nothing is written.
SIGNATURE = ('hpprime.py', 'hpkit/cli.py', 'AGENTS.md')
COMMIT = re.compile(r'^[0-9a-f]{40}$')

USAGE = """usage: hpprime update [--from FILE.zip] [--dry-run]

Brings a downloaded copy of the kit to the latest version on GitHub, or to
the ZIP given with --from. Writes the files that changed and adds the new
ones; never writes inside programs/ or to .claude/settings.local.json, and
never deletes: a file the new version no longer has is listed for you.
Refuses in a clone, which updates with `git pull`."""


class UpdateError(Exception):
    pass


def is_theirs(rel):
    return (rel == THEIRS_DIR or rel.startswith(THEIRS_DIR + '/')
            or rel in THEIRS_FILES)


def read_zip(data):
    """-> ({relative path: (bytes, unix mode)}, commit or None).

    The one folder every entry sits under, as in any ZIP GitHub builds, is
    stripped. An entry that would land outside the kit's folder refuses the
    whole archive."""
    try:
        z = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipfile as e:
        raise UpdateError('not a ZIP: %s' % e)
    infos = [i for i in z.infolist() if not i.filename.endswith('/')]
    names = [i.filename for i in infos]
    tops = set(n.split('/', 1)[0] for n in names)
    strip = len(tops) == 1 and all('/' in n for n in names)
    files = {}
    for info in infos:
        rel = info.filename.split('/', 1)[1] if strip else info.filename
        parts = rel.split('/')
        if (rel.startswith('/') or '\\' in rel or ':' in rel
                or '..' in parts or '' in parts):
            raise UpdateError('%s would land outside the kit\'s folder; '
                              'nothing was written' % info.filename)
        files[rel] = (z.read(info), (info.external_attr >> 16) & 0o777)
    missing = [s for s in SIGNATURE if s not in files]
    if missing:
        raise UpdateError('this ZIP is not the kit: it has no %s at its top'
                          % ', '.join(missing))
    comment = z.comment.decode('ascii', 'replace').strip()
    return files, (comment if COMMIT.match(comment) else None)


def ignore_rules(text):
    """The patterns of a .gitignore, in order, as (pattern, negated)."""
    rules = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        rules.append((line[1:], True) if line.startswith('!')
                     else (line, False))
    return rules


def ignored(rel, rules):
    """Whether git would ignore `rel` under these rules: the last pattern
    that matches decides. Enough for the kit's own .gitignore; not every
    corner of git's."""
    parts = rel.split('/')
    verdict = False
    for pattern, negated in rules:
        dir_only = pattern.endswith('/')
        p = pattern.strip('/')
        if '/' in pattern.rstrip('/'):
            # Anchored at the root: it matches the path or a folder on it.
            hit = any(fnmatch.fnmatchcase('/'.join(parts[:k]), p)
                      for k in range(1, len(parts) + (0 if dir_only else 1)))
        else:
            hit = any(fnmatch.fnmatchcase(part, p)
                      for part in (parts[:-1] if dir_only else parts))
        if hit:
            verdict = not negated
    return verdict


def on_disk(root):
    """Every file under the kit's folder, as relative paths, the person's
    folder left out."""
    out = []
    for folder, dirs, files in os.walk(root):
        rel_folder = os.path.relpath(folder, root).replace(os.sep, '/')
        rel_folder = '' if rel_folder == '.' else rel_folder + '/'
        dirs[:] = [d for d in dirs
                   if d != '.git' and not is_theirs(rel_folder + d)]
        out.extend(rel_folder + f for f in files)
    return out


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def plan(root, files):
    """-> what an update would do, as lists of relative paths."""
    report = {'changed': [], 'added': [], 'same': [], 'theirs': [],
              'lacking': []}
    for rel in sorted(files):
        if is_theirs(rel):
            report['theirs'].append(rel)
            continue
        path = os.path.join(root, *rel.split('/'))
        if not os.path.isfile(path):
            report['added'].append(rel)
        elif _read(path) != files[rel][0]:
            report['changed'].append(rel)
        else:
            report['same'].append(rel)
    gitignore = files.get('.gitignore', (b'', 0))[0]
    rules = ignore_rules(gitignore.decode('utf-8', 'replace'))
    report['lacking'] = sorted(
        rel for rel in on_disk(root)
        if rel not in files and not is_theirs(rel)
        and not ignored(rel, rules))
    return report


def update(root, data, dry_run=False):
    """Update the kit in `root` from a ZIP's bytes. -> (report, commit)."""
    if os.path.exists(os.path.join(root, '.git')):
        raise UpdateError('this folder is a git clone: update it with '
                          '`git pull`')
    files, commit = read_zip(data)
    report = plan(root, files)
    report['failed'] = []
    if dry_run:
        return report, commit
    for rel in report['changed'] + report['added']:
        path = os.path.join(root, *rel.split('/'))
        content, mode = files[rel]
        try:
            folder = os.path.dirname(path)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with open(path, 'wb') as f:
                f.write(content)
            if mode & 0o111 and os.name != 'nt':
                os.chmod(path, mode)
        except (IOError, OSError) as e:
            report['failed'].append('%s: %s' % (rel, e))
    return report, commit


def download(url=URL):
    from urllib.request import urlopen
    return urlopen(url, timeout=120).read()


def cli(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE)
        return 0
    dry_run = '--dry-run' in argv
    source = None
    if '--from' in argv:
        i = argv.index('--from')
        if i + 1 >= len(argv):
            print(USAGE)
            return 2
        source = argv[i + 1]

    if os.path.exists(os.path.join(ROOT, '.git')):
        print('This folder is a git clone: update it with `git pull`.')
        return 1
    try:
        if source:
            data = _read(source)
        else:
            print('downloading %s' % URL)
            data = download()
    except Exception as e:      # the network fails in more ways than one
        print('ERROR: could not read the new version: %s' % e)
        print('       Download it by hand -- on GitHub, Code, then Download')
        print('       ZIP -- and run: hpprime update --from FILE.zip')
        return 1
    try:
        report, commit = update(ROOT, data, dry_run)
    except UpdateError as e:
        print('ERROR: %s' % e)
        return 1

    verb = 'would be ' if dry_run else ''
    print('%s%s' % (source or URL,
                    (', commit %s' % commit[:7]) if commit else ''))
    print('  %d %schanged, %d %sadded, %d unchanged'
          % (len(report['changed']), verb, len(report['added']), verb,
             len(report['same'])))
    if dry_run:
        for rel in report['changed']:
            print('    changed  %s' % rel)
        for rel in report['added']:
            print('    added    %s' % rel)
    print('  programs/ and .claude/settings.local.json left as they are')
    if report['lacking']:
        print('\nNot in the new version, and left in place. Delete them if '
              'they are not yours:')
        for rel in report['lacking']:
            print('  %s' % rel)
    if report['failed']:
        print('\nCould not be written:')
        for line in report['failed']:
            print('  %s' % line)
        return 1
    if dry_run:
        print('\nNothing was written (--dry-run).')
    return 0
