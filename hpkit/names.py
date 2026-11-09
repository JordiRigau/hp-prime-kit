# -*- coding: utf-8 -*-
"""The list of every PPL name, as the documentation keeps it.

docs/commands/names.tsv is built by tests/names_extract.py from HP's own
sources: the Command Tree of firmware 13217, the command tree of 2.1.14181,
and the release notes up to 2.4.15515. This module reads it. The
documentation builds its index from it, and the linter uses it to know which
names exist.

    from hpkit import names
    everything = names.load()          # OrderedDict: name -> Name
    names.known(everything)            # every name, lower case
"""
from __future__ import unicode_literals
import io, os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PATH = os.path.join(ROOT, 'docs', 'commands', 'names.tsv')

FIELDS = ('name', 'kind', 'group', 'menu', 'syntax', 'source')
KINDS = ('statement', 'keyword', 'operator', 'command', 'function',
         'app function', 'app variable', 'variable', 'cas', 'unknown')

# The kinds that get an entry of their own. Keywords belong to the entry of
# their statement, operators to the language's topic page, and CAS is out of
# scope: those are known to the linter and not documented one by one.
DOCUMENTED = ('statement', 'command', 'function', 'app function',
              'app variable', 'variable', 'unknown')


# The names the documentation writes that are not on HP's list, and whose they
# are: docs/format.md says what each origin means.
OTHERS_PATH = os.path.join(ROOT, 'docs', 'commands', 'not-hp.tsv')
OTHER_FIELDS = ('name', 'origin', 'whose')
ORIGINS = ('library', 'python', 'hook', 'tools', 'test', 'example', 'hp',
           'none')


class Name(object):
    def __init__(self, line, name, kind, group, menu, syntax, source):
        self.line = line
        self.name = name
        self.kind = kind
        self.group = group
        self.menu = menu
        self.syntax = syntax
        self.source = source

    @property
    def documented(self):
        return self.kind in DOCUMENTED


def _rows(path, fields):
    """-> ([(line, cells)], [(line, problem)]) for a tab-separated list whose
    comment lines start with #."""
    rows, problems = [], []
    if not os.path.isfile(path):
        return rows, [(0, 'there is no list of names at %s' % path)]
    for n, line in enumerate(io.open(path, encoding='utf-8'), 1):
        line = line.rstrip('\n').rstrip('\r')
        if not line.strip() or line.startswith('#'):
            continue
        cells = line.split('\t')
        if len(cells) == len(fields):
            rows.append((n, cells))
        else:
            problems.append((n, 'a row has %d fields: %s'
                             % (len(fields), ', '.join(fields))))
    return rows, problems


def read(path=PATH):
    """-> ([Name], [(line, problem)]). Comment lines start with #."""
    out, seen = [], set()
    rows, problems = _rows(path, FIELDS)
    for n, cells in rows:
        name = Name(n, *cells)
        if name.kind not in KINDS:
            problems.append((n, 'unknown kind "%s"' % name.kind))
        if name.name in seen:
            problems.append((n, '%s is listed twice' % name.name))
        seen.add(name.name)
        out.append(name)
    return out, problems


def load(path=PATH):
    """-> OrderedDict {name: Name}, the first row winning."""
    out = OrderedDict()
    for name in read(path)[0]:
        out.setdefault(name.name, name)
    return out


def known(everything=None):
    """-> the set of every listed name, lower case.

    The linter compares the calculator's names without regard to case, so
    that it never flags a spelling the calculator might accept (sin for
    SIN). Whether the calculator itself ignores case in its own names has
    not been measured. A program's own names are compared exactly."""
    if everything is None:
        everything = load()
    return set(n.lower() for n in everything)


class Other(object):
    def __init__(self, line, name, origin, whose):
        self.line = line
        self.name = name
        self.origin = origin
        self.whose = whose


def read_others(path=OTHERS_PATH):
    """-> ([Other], [(line, problem)]): the names that are not on HP's list,
    and whose they are."""
    out, seen = [], set()
    rows, problems = _rows(path, OTHER_FIELDS)
    for n, cells in rows:
        other = Other(n, *cells)
        if other.origin not in ORIGINS:
            problems.append((n, 'unknown origin "%s"' % other.origin))
        if other.name in seen:
            problems.append((n, '%s is listed twice' % other.name))
        seen.add(other.name)
        out.append(other)
    return out, problems


def others(path=OTHERS_PATH):
    """-> {name: Other}, empty if the list is not there. Compared exactly,
    unlike HP's names: `reset` is a library's and `RESET` an app's hook."""
    return dict((o.name, o) for o in read_others(path)[0])
