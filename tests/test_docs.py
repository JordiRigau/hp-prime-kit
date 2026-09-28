# -*- coding: utf-8 -*-
"""Every link in the documentation has to go somewhere.

A repository whose main deliverable is documentation rots through broken
links first: a file gets renamed and six pages quietly point at nothing. This
walks every relative link and anchor in every Markdown file.

    python tests/test_docs.py
"""
from __future__ import unicode_literals
import io, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
HEADING = re.compile(r'^#{1,6}\s+(.*?)\s*$', re.M)
SKIP_DIRS = {'.git', '__pycache__'}

# Where a person's programs go. The folder ships with its note and nothing
# else, and git keeps out of the rest, so an update never meets their files.
PROGRAMS = os.path.join(ROOT, 'programs')
PROGRAMS_RULES = ('programs/*', '!programs/README.md')


def markdown_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if root == PROGRAMS:
            # A person's own programs are theirs to link as they like; only
            # the note the kit ships here is checked.
            dirs[:] = []
            files = [f for f in files if f == 'README.md']
        for f in sorted(files):
            if f.endswith('.md'):
                yield os.path.join(root, f)


def anchors(path):
    """GitHub-style anchors for a file's headings."""
    text = io.open(path, encoding='utf-8').read()
    out = set()
    for h in HEADING.findall(text):
        a = h.lower()
        a = re.sub(r'`|\*|\[|\]|\(|\)|\.|,|:|;|/|\'|"', '', a)
        a = re.sub(r'[^a-z0-9\- ]', '', a)
        out.add(a.strip().replace(' ', '-'))
    # explicit <a name="..."> targets
    out |= set(re.findall(r'<a\s+name="([^"]+)"', text))
    return out

def programs_problems(gitignore, tracked):
    """-> what is wrong with programs/. `gitignore` is the text of
    .gitignore; `tracked` the files git tracks under programs/, or None
    where there is no git to ask (a download)."""
    problems = []
    lines = [l.strip() for l in gitignore.splitlines()]
    for rule in PROGRAMS_RULES:
        if rule not in lines:
            problems.append('.gitignore has no %r' % rule)
    for f in tracked or []:
        if f != 'programs/README.md':
            problems.append('%s is tracked: a person\'s program would ship'
                            % f)
    return problems


def _git(*args):
    """-> (exit code, output) of a git command here, or None with no git."""
    try:
        p = subprocess.Popen(('git',) + args, cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError:
        return None
    out = p.communicate()[0].decode('utf-8', 'replace')
    return None if p.returncode == 128 else (p.returncode, out)


def main():
    ok = bad = 0
    problems = []
    for path in markdown_files():
        rel = os.path.relpath(path, ROOT)
        text = io.open(path, encoding='utf-8').read()
        for target in LINK.findall(text):
            if target.startswith(('http://', 'https://', 'mailto:')):
                continue
            file_part, _, anchor = target.partition('#')
            if file_part:
                dest = os.path.normpath(
                    os.path.join(os.path.dirname(path), file_part))
            else:
                dest = path
            if not os.path.exists(dest):
                bad += 1
                problems.append('%s -> %s (no such file)' % (rel, target))
                continue
            if anchor and dest.endswith('.md'):
                if anchor not in anchors(dest):
                    bad += 1
                    problems.append('%s -> %s (no such heading)'
                                    % (rel, target))
                    continue
            ok += 1

    for p in problems:
        print('  FAIL  %s' % p)
    if not problems:
        print('  ok    every relative link resolves')

    # The entry points a newcomer is sent to must exist.
    required = ['README.md', 'AGENTS.md', 'CONTRIBUTING.md',
                'docs/tools.md', 'docs/ai/prompts.md',
                'docs/start/01-setup.md', 'docs/topics/ppl.md',
                'docs/format.md', 'docs/commands/index.md']
    missing = [r for r in required if not os.path.exists(os.path.join(ROOT, r))]
    if missing:
        bad += 1
        print('  FAIL  missing entry point(s): %s' % ', '.join(missing))
    else:
        ok += 1
        print('  ok    every entry point is in place')

    # programs/: its note ships, and nothing else of it can.
    gitignore = io.open(os.path.join(ROOT, '.gitignore'),
                        encoding='utf-8').read()
    listed = _git('ls-files', 'programs')
    tracked = listed[1].split() if listed else None
    problems = programs_problems(gitignore, tracked)
    if not os.path.isfile(os.path.join(PROGRAMS, 'README.md')):
        problems.append('programs/README.md is missing')
    if listed:
        if _git('check-ignore', '-q', 'programs/CIRCLE/CIRCLE.txt')[0] != 0:
            problems.append('git does not ignore a program in programs/')
        if _git('check-ignore', '-q', 'programs/README.md')[0] == 0:
            problems.append('git ignores programs/README.md, so it would '
                            'not ship')
    # And the check itself: fed no rules and a tracked program, it names
    # all three.
    fed = programs_problems('', ['programs/README.md',
                                 'programs/CIRCLE/CIRCLE.txt'])
    if len(fed) != 3:
        problems.append('the check named %d of 3 planted faults: %s'
                        % (len(fed), fed))
    if problems:
        bad += 1
        for p in problems:
            print('  FAIL  programs/: %s' % p)
    else:
        ok += 1
        print('  ok    programs/ ships its note alone, and git keeps out of '
              'the rest')

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
