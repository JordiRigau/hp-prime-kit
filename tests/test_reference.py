# -*- coding: utf-8 -*-
"""The documentation, held to its format in both directions.

    python tests/test_reference.py

docs/format.md states the format and hpkit/docs.py enforces it. A check that
has only ever passed proves nothing, so this suite breaks a copy of the
documentation on purpose, one way at a time, and requires every break to be
caught. The real documentation has to pass untouched: a check that flags
correct pages gets ignored, which is worse than having none.
"""
from __future__ import unicode_literals
import io, os, re, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from hpkit import docs                                        # noqa: E402

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(errors='replace')


def copy():
    tmp = tempfile.mkdtemp(prefix='hpdocs-')
    shutil.copytree(os.path.join(ROOT, 'docs'), os.path.join(tmp, 'docs'))
    return tmp


def _path(root, rel):
    return os.path.join(root, *rel.split('/'))


def edit(root, rel, old, new):
    path = _path(root, rel)
    text = io.open(path, encoding='utf-8').read()
    if old not in text:
        raise AssertionError('%s does not contain %r' % (rel, old))
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text.replace(old, new, 1))


def append(root, rel, extra):
    with io.open(_path(root, rel), 'a', encoding='utf-8', newline='\n') as f:
        f.write(extra)


def entry_named(root, name):
    """A copy of LEFT's entry under another name, in the same folder."""
    text = io.open(_path(root, 'docs/commands/strings/LEFT.md'),
                   encoding='utf-8').read().replace('# LEFT\n', '# %s\n' % name)
    with io.open(_path(root, 'docs/commands/strings/%s.md' % name), 'w',
                 encoding='utf-8', newline='\n') as f:
        f.write(text)


AGAIN = """
<a name="ppl.local-limit"></a>
## The same identifier, twice

| | |
|---|---|
| Identifier | `ppl.local-limit` |
| Kind | rule |
| Known from | G2 |

Stated again.

**Evidence.** None.
"""

# (what is broken, how, and a phrase the report has to contain)
BREAKS = [
    ('a fact identifier used twice',
     lambda r: append(r, 'docs/topics/ppl.md', AGAIN), 'already used'),
    ('a link to a fact that does not exist',
     lambda r: edit(r, 'docs/commands/list/SIZE.md', '#ppl.index-call)',
                    '#ppl.no-such-fact)'), 'names no fact'),
    ('a link to a file that does not exist',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', '(RIGHT.md)',
                    '(RIGHTS.md)'), 'goes nowhere'),
    ('a page that points at the layer built on it',
     lambda r: append(r, 'docs/commands/strings/LEFT.md', '\nSee SKILL.md.\n'),
     'layer built on it'),
    ('a generated page out of date',
     lambda r: append(r, 'docs/commands/index.md', '\nedited by hand\n'),
     'out of date'),
    ('a generated page nobody produces any more',
     lambda r: append(r, 'docs/commands/gone.md', '# Gone\n'),
     'no folder of entries produces'),
    ('an example with no label',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md',
                    '| `"MOM"` | [emulator](../results.tsv) |',
                    '| `"MOM"` |  |'), 'exactly one label'),
    ('a label that is not one of the four',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md',
                    '| [emulator](../results.tsv) |', '| HP manual |'),
     'exactly one label'),
    ('a behaviour paragraph with no label',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', 'to mix up (G2).',
                    'to mix up.'), 'says how it is known'),
    ('an example the interpreter contradicts',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', '| `"MOM"` |',
                    '| `"MOO"` |'), 'the interpreter answers'),
    ('an error the interpreter does not raise',
     lambda r: edit(r, 'docs/commands/strings/MID.md',
                    '| `MID("abcdef", 0, 2)` | *error* |',
                    '| `MID("abcdef", 1, 2)` | *error* |'),
     'where the entry says error'),
    ('a title that is not the file name',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', '# LEFT\n',
                    '# LEFTX\n'), 'the title is'),
    # The suffix belongs on the file where two names differ only in case, and
    # never in the title: a title carrying it names a command nobody has.
    ('a title wearing the file name suffix',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', '# LEFT\n',
                    '# LEFT-var\n'), 'the title is'),
    ('a group that is not the folder',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md', '| Group | strings |',
                    '| Group | list |'), 'lives in'),
    ('a field missing',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md',
                    '| Runs on the PC | yes |\n', ''), 'the fields are'),
    ('a section that is not one of the four',
     lambda r: edit(r, 'docs/commands/loop/FOR.md', '## Behaviour',
                    '## Behavior'), 'unknown section'),
    ('a fact whose Identifier is not its anchor',
     lambda r: edit(r, 'docs/topics/ppl.md', '| Identifier | `ppl.index-call` |',
                    '| Identifier | `ppl.indexcall` |'), 'repeats the anchor'),
    ('a fact with no evidence',
     lambda r: edit(r, 'docs/topics/ppl.md', '**Evidence.** A program that runs',
                    'A program that runs'), 'Evidence'),
    ('a G2 fact whose evidence says only that it was measured',
     lambda r: edit(r, 'docs/topics/ppl.md',
                    '**Evidence.** A program that runs on a G2 has two `RETURN` '
                    'statements inside\nloops.',
                    '**Evidence.** Measured on a G2 with firmware 2.4.15515.'),
     'what was run'),
    ('an entry whose name is not on the list',
     lambda r: entry_named(r, 'NOSUCH'), 'is not on the list of names'),
    ('an entry in a folder the list does not give it',
     lambda r: edit(r, 'docs/commands/names.tsv', 'LEFT\tcommand\tstrings',
                    'LEFT\tcommand\ttext'), 'the list files LEFT under'),
    ('a row of the list with a field missing',
     lambda r: append(r, 'docs/commands/names.tsv', 'BROKEN\tfunction\n'),
     'a row has'),
    ('an example labelled emulator with no stored answer',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md',
                    '| `LEFT("MOMOGUMBO", 3)`',
                    '| `LEFT("xyz", 1)` | `"x"` | [emulator](../results.tsv) |'
                    '\n| `LEFT("MOMOGUMBO", 3)`'),
     'holds no answer'),
    ('a stored answer that differs from the entry',
     lambda r: stored(r, 'LEFT', 'LEFT("abcdef", 3)', '"abd"', '2'),
     'the emulator answers'),
    # COS does not run on the PC, so an example of it with no stored answer
    # and no G2 measurement has been run nowhere.
    ('an example nobody has run',
     lambda r: edit(r, 'docs/commands/catalog/COS.md',
                    '| `COS(1)` | `0.540302305868` | [emulator](../results.tsv) |',
                    '| `COS(1)` | `0.540302305868` | [emulator](../results.tsv) |'
                    '\n| `COS(0)` | `1` | HP help |'),
     'nobody has run'),
    ('a page that speaks of the phase it was written in',
     lambda r: append(r, 'docs/commands/strings/LEFT.md',
                      '\nMeasured in Phase 7 (G2).\n'), 'how it was built'),
    ('a page that speaks of this kit',
     lambda r: append(r, 'docs/topics/ppl.md',
                      '\nThis kit measured it.\n'), 'how it was built'),
    # The guided path is held to the same rules as the pages it links to.
    ('a step of the guided path that points at the layer built on it',
     lambda r: append(r, 'docs/start/06-working-with-ai.md',
                      '\nPoint it at AGENTS.md.\n'), 'layer built on it'),
    ('a step of the guided path that speaks of this kit',
     lambda r: append(r, 'docs/start/01-setup.md',
                      '\nThis kit measured it.\n'), 'how it was built'),
    ('a step of the guided path linking to a fact that does not exist',
     lambda r: append(r, 'docs/start/02-first-program.md',
                      '\n[a fact](../topics/ppl.md#ppl.no-such-fact)\n'),
     'names no fact'),
    ('the index for models out of date',
     lambda r: append(r, 'docs/llms.txt', '\nedited by hand\n'),
     'out of date'),
    ('the index for models over its budget',
     lambda r: edit(r, 'docs/commands/strings/LEFT.md',
                    'The first n characters of a string.',
                    'The first n characters of a string'
                    + ', said at length' * 7000 + '.'),
     'over its budget'),
]


def stored(root, entry, call, answer, type_):
    """Write one row into results.tsv, as hpprime examples would."""
    from collections import OrderedDict
    from hpkit import examples
    examples.write_results(root, [OrderedDict([
        ('entry', entry), ('call', call), ('answer', answer),
        ('type', type_), ('firmware', 'test'), ('date', '2026-09-11')])])

# A call the interpreter says it does not cover: MID with four arguments
# raises Unsupported, and an entry that states a result for it has to be
# listed rather than failed.
UNCOVERED = ('| `MID("abcdef", 2, 3)` | `"bcd"` |',
             '| `MID("abcdef", 2, 3, 4)` | `"bcd"` | unverified |\n'
             '| `MID("abcdef", 2, 3)` | `"bcd"` |')


def quiet_when_uncovered():
    """An example the interpreter does not cover is listed, not failed: the
    interpreter is a subset, and says so instead of guessing. It still has to
    have been run somewhere, so the copy stores the emulator's answer."""
    root = copy()
    try:
        edit(root, 'docs/commands/strings/MID.md', *UNCOVERED)
        stored(root, 'MID', 'MID("abcdef", 2, 3, 4)', '"bcd"', '2')
        docs.build(root)
        problems, notes = docs.check(root)
        if problems:
            return False, 'it failed: %s' % '; '.join(str(p) for p in problems)
        if not notes:
            return False, 'the example was not listed as uncovered'
        return True, ''
    finally:
        shutil.rmtree(root, ignore_errors=True)


def index_for_models():
    """docs/llms.txt has one line for every entry and every fact, each with
    the link a model follows, and fits its budget."""
    entries, facts, _ = docs.load(ROOT)
    text = io.open(os.path.join(ROOT, 'docs', docs.LLMS),
                   encoding='utf-8').read()
    lines = set(text.split('\n'))
    missing = ['%s' % e.name for e in entries
               if not any(l.startswith('- [%s](commands/%s/%s.md): '
                                       % (e.name, e.folder, e.stem))
                          for l in lines)]
    for f in facts:
        page = os.path.basename(f.path)
        if '- [%s](topics/%s#%s): %s' % (f.ident, page, f.ident,
                                         f.title) not in lines:
            missing.append(f.ident)
    size = len(text.encode('utf-8'))
    if missing:
        return False, 'no line for %s' % ', '.join(missing[:5])
    if size > docs.LLMS_BUDGET:
        return False, '%d bytes, over %d' % (size, docs.LLMS_BUDGET)
    return True, '%d entries and %d facts in %d bytes of %d' % (
        len(entries), len(facts), size, docs.LLMS_BUDGET)


CITATION = re.compile(r'\[([^\],\s]+), (G2|emulator|HP help|unverified)\]')


def paste_block():
    """docs/ai/prompts.md section 1 restates the documentation for a chat that
    cannot read it. Every rule in it names where it comes from, [identifier,
    label], and each identifier is a fact with that label or an entry with an
    example so labelled. The wording is not checked; the citations are."""
    entries, facts, _ = docs.load(ROOT)
    by_fact = dict((f.ident, f.label) for f in facts)
    by_entry = dict((e.name, set(x.label for x in e.examples))
                    for e in entries)
    text = io.open(os.path.join(ROOT, 'docs', 'ai', 'prompts.md'),
                   encoding='utf-8').read().replace('\r\n', '\n')
    section = text.split('\n## 1.', 1)[1].split('\n## 2.', 1)[0]
    rules = []
    for block in re.findall(r'^```\n(.*?)^```', section, re.M | re.S):
        for chunk in re.split(r'\n(?=- )', block):
            if chunk.startswith('- '):
                rules.append(' '.join(chunk.split()))
    wrong = []
    for rule in rules:
        cites = CITATION.findall(rule)
        if not cites:
            wrong.append('no citation: %s' % rule[:60])
        for ident, label in cites:
            if '.' in ident:
                if ident not in by_fact:
                    wrong.append('%s is not a fact' % ident)
                elif by_fact[ident] != label:
                    wrong.append('%s is %s, not %s'
                                 % (ident, by_fact[ident], label))
            elif ident not in by_entry:
                wrong.append('%s has no entry' % ident)
            elif label not in by_entry[ident]:
                wrong.append('%s has no example labelled %s' % (ident, label))
    if not rules:
        return False, 'no rules found'
    if wrong:
        return False, '; '.join(wrong)
    return True, '%d rules, each citing a fact or an entry' % len(rules)


def readme_numbers():
    """What the README says about the documentation's size is computed from
    the documentation, so a batch that adds entries fails the suite until the
    README says so. Each phrase is looked for with its line breaks ignored."""
    from hpkit import examples
    from hpkit import names as namelist
    entries, facts, _ = docs.load(ROOT)
    rows = namelist.read(docs._list_path(ROOT))[0]
    written = set(e.name for e in entries)
    total, have = {}, {}
    for r in rows:
        if r.documented:
            total[r.kind] = total.get(r.kind, 0) + 1
            have[r.kind] = have.get(r.kind, 0) + (r.name in written)
    results = examples.read_results(ROOT)
    ex = [(e, x) for e in entries for x in e.examples]
    stored = sum(1 for e, x in ex if (e.name, x.call) in results)
    novalue = sum(1 for e, x in ex if x.no_value)
    by_hand = sum(1 for e, x in ex if not x.no_value
                  and (e.name, x.call) not in results and x.label == 'G2')
    labels = dict((l, sum(1 for f in facts if f.label == l))
                  for l in docs.LABELS)

    def of(kind, noun):
        if have.get(kind) == total.get(kind):
            return 'all %d %s' % (total[kind], noun)
        return '%d of the %d %s' % (have.get(kind, 0), total[kind], noun)

    phrases = [
        '%d of the %d names that get an entry have one'
        % (len(written & set(r.name for r in rows if r.documented)),
           sum(total.values())),
        of('app function', 'app functions'),
        of('app variable', 'app variables'),
        of('variable', 'variables of Home and the system'),
    ] + [
        'the other %d %s' % (total[k] - have[k], noun)
        for k, noun in (('app variable', 'app variables'),
                        ('variable', 'variables of Home and the system'))
        if have[k] < total[k]
    ] + [
        'Of the %d examples, %d have the Virtual Calculator\'s answer'
        % (len(ex), stored),
        '%d were measured by hand on a G2' % by_hand,
        '%d have no value to record' % novalue,
        '%d facts about the platform: %d measured on a G2, %d on the '
        'emulator, and %d unverified'
        % (len(facts), labels['G2'], labels['emulator'],
           labels['unverified']),
    ]
    if all(have.get(k) == total.get(k)
           for k in ('statement', 'command', 'function')):
        phrases.append('every statement, command and Home function')
    text = ' '.join(io.open(os.path.join(ROOT, 'README.md'),
                            encoding='utf-8').read().split())
    missing = [p for p in phrases if p not in text]
    if missing:
        return False, 'the README does not say: %s' % '; '.join(missing)
    return True, '%d numbers, all current' % len(phrases)


def main():
    ok = bad = 0
    problems, notes = docs.check(ROOT)
    if problems:
        bad += 1
        print('  FAIL  the documentation as it is has %d problem(s):'
              % len(problems))
        for p in problems:
            print('          %s' % p)
    else:
        ok += 1
        entries, facts, _ = docs.load(ROOT)
        print('  ok    the documentation as it is passes: %d entries, %d facts'
              % (len(entries), len(facts)))

    entries = docs.load(ROOT)[0]
    _, _, ran = docs.run_examples(ROOT, entries)
    if ran:
        ok += 1
        print('  ok    %d example(s) ran through the interpreter and agree'
              % ran)
    else:
        bad += 1
        print('  FAIL  no example ran through the interpreter')

    good, why = index_for_models()
    if good:
        ok += 1
        print('  ok    the index for models lists %s' % why)
    else:
        bad += 1
        print('  FAIL  the index for models: %s' % why)

    good, why = readme_numbers()
    if good:
        ok += 1
        print('  ok    the README states the documentation as it is: %s' % why)
    else:
        bad += 1
        print('  FAIL  the README: %s' % why)

    good, why = paste_block()
    if good:
        ok += 1
        print('  ok    the paste block for chats cites: %s' % why)
    else:
        bad += 1
        print('  FAIL  the paste block for chats: %s' % why)

    good, why = quiet_when_uncovered()
    if good:
        ok += 1
        print('  ok    an example the interpreter does not cover is listed, '
              'not failed')
    else:
        bad += 1
        print('  FAIL  an uncovered example: %s' % why)

    for name, breaker, expect in BREAKS:
        root = copy()
        try:
            breaker(root)
            found, _ = docs.check(root)
            if [p for p in found if expect in p.message]:
                ok += 1
                print('  ok    catches %s' % name)
            else:
                bad += 1
                print('  FAIL  missed %s; the report was: %s'
                      % (name, '; '.join(str(p) for p in found) or 'nothing'))
        finally:
            shutil.rmtree(root, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (ok, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
