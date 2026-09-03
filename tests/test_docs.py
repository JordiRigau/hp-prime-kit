# -*- coding: utf-8 -*-
"""Every link in the documentation has to go somewhere.

A repository whose main deliverable is documentation rots through broken
links first: a file gets renamed and six pages quietly point at nothing. This
walks every relative link and anchor in every Markdown file.

    python tests/test_docs.py
"""
from __future__ import unicode_literals
import io, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

LINK = re.compile(r'\[[^\]]*\]\(([^)]+)\)')
HEADING = re.compile(r'^#{1,6}\s+(.*?)\s*$', re.M)
SKIP_DIRS = {'.git', '__pycache__'}


def markdown_files():
    for root, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
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
    required = ['README.md', 'AGENTS.md', 'SKILL.md', 'CONTRIBUTING.md',
                'docs/tools.md', 'docs/ai/prompts.md',
                'docs/start/01-setup.md', 'docs/reference/ppl.md']
    missing = [r for r in required if not os.path.exists(os.path.join(ROOT, r))]
    if missing:
        bad += 1
        print('  FAIL  missing entry point(s): %s' % ', '.join(missing))
    else:
        ok += 1
        print('  ok    every entry point is in place')

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
