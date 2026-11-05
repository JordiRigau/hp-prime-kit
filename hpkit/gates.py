# -*- coding: utf-8 -*-
"""The evidence the gates leave, and the hooks that read it.

`AGENTS.md` asks an agent to put every program through `lint` and `run`
before it says anything about it. In Claude Code the kit's
`.claude/settings.json` makes that more than a request:

- after every edit of a PPL file in `programs/`, `post-edit` lints it and
  puts the answer in front of the agent: errors as a hook error, warnings as
  context;
- `lint` and `run` note, in a ledger, what content of which file they
  passed or failed, as the SHA-1 of the bytes they read;
- when the agent finishes, `stop` checks the ledger: every program edited
  since the last check passed must have passed `lint` on its current content
  and been loaded by `run`, and every fact the report cites must exist.
  Otherwise the agent is sent back with what is missing. A program that was
  only loaded, with no call that answered, lets the agent finish, and the
  person is told: one that is all screen and keys may have nothing the PC
  can answer, and the check is not there to make its author build it
  otherwise.

The ledger is `.claude/hpprime-gates.json`, which git ignores. The tools
write it only when `HPPRIME_GATES` is `1`, which the kit's settings set for
the session, so somebody running the tools by hand writes nothing.

    hpprime hook post-edit      # what .claude/settings.json runs; not typed
    hpprime hook stop

Only `programs/` is watched, where a person's programs go: the kit's own
tests hold PPL broken on purpose. A `.txt` there counts as PPL when it has a
`BEGIN`, which every program does.

The end check reads evidence, not the report's words, so the language the
agent speaks does not matter; the one thing it reads in the report is fact
identifiers, which are the same in every language. Claude Code documents no
limit on how often a Stop hook may send the agent back, so this keeps itself
out of a loop: the same problems a third time running, with nothing moved,
let the agent finish and tell the person what was never shown. Turning the
checks off is the person's: `"disableAllHooks": true` in their
`.claude/settings.local.json`.

A session in a git worktree works in a copy of the kit, while Claude Code runs
the hook from the folder the session started in, so the folder is taken from
the event's `cwd` and not from where this file is.
"""
from __future__ import unicode_literals
import hashlib, io, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROGRAMS = os.path.join(ROOT, 'programs')
LEDGER = os.path.join(ROOT, '.claude', 'hpprime-gates.json')
FLAG = 'HPPRIME_GATES'
BEGIN = re.compile(r'\bBEGIN\b', re.I)

# The facts are the anchors of docs/topics/, and a page's name is its topic.
TOPICS = os.path.join(ROOT, 'docs', 'topics')
ANCHOR = re.compile(r'<a name="([^"]+)"')
# Cited in backticks or as a link's text, shaped topic.slug.
CITED = re.compile(r'`([^`\n]+)`|\[([^\]\n]+)\]')
IDENT = re.compile(r'^([a-z][a-z0-9]*)\.([a-z0-9][a-z0-9-]*)$')
# A slug that is a file's extension makes a file name, `ppl.md`, and one that
# is a domain's makes a site, `micropython.org`: neither is a fact.
EXTENSIONS = set('md txt py json tsv csv html png zip cmd sh hpprgm hpappdir '
                 'hpapp hpappnote hpappprgm hpmat hplist org com net io'
                 .split())
# The same problems this many times running let the agent finish.
GUARD = 3

USAGE = """usage: hpprime hook post-edit|stop < event.json

What the kit's .claude/settings.json runs in Claude Code; not typed by hand.
It reads the hook's event on stdin."""


def enabled():
    return os.environ.get(FLAG) == '1'


def kit_of(folder):
    """-> the kit a session works in: the nearest folder at or above `folder`
    that holds hpprime.py and docs/topics/, or None."""
    path = os.path.abspath(folder)
    while True:
        if (os.path.isfile(os.path.join(path, 'hpprime.py'))
                and os.path.isdir(os.path.join(path, 'docs', 'topics'))):
            return path
        parent = os.path.dirname(path)
        if parent == path:
            return None
        path = parent


def use_kit(root):
    """Read programs, the ledger and the facts from this kit. A session in a
    git worktree works in a copy of the kit, while Claude Code runs the hook
    from the folder the session started in, so the code's own place is not
    where the work is: a hook's event says it, in `cwd`."""
    global ROOT, PROGRAMS, LEDGER, TOPICS
    ROOT = root
    PROGRAMS = os.path.join(root, 'programs')
    LEDGER = os.path.join(root, '.claude', 'hpprime-gates.json')
    TOPICS = os.path.join(root, 'docs', 'topics')


def program_rel(path):
    """-> 'programs/.../X.txt', relative to the kit with forward slashes,
    when `path` is a source in programs/; None otherwise."""
    try:
        rel = os.path.relpath(os.path.abspath(path), ROOT)
    except ValueError:              # another drive, on Windows
        return None
    rel = rel.replace(os.sep, '/')
    if rel.startswith('../') or not rel.endswith('.txt'):
        return None
    top = os.path.relpath(PROGRAMS, ROOT).replace(os.sep, '/') + '/'
    return rel if rel.startswith(top) else None


def _full(rel):
    return os.path.join(ROOT, *rel.split('/'))


def _read(path):
    with open(path, 'rb') as f:
        return f.read()


def digest(path):
    return hashlib.sha1(_read(path)).hexdigest()


def is_ppl(path):
    try:
        text = _read(path).decode('utf-8-sig')
    except (IOError, OSError, UnicodeDecodeError):
        return False
    return bool(BEGIN.search(text))


def load():
    try:
        with io.open(LEDGER, encoding='utf-8') as f:
            ledger = json.load(f)
    except (IOError, OSError, ValueError):
        ledger = {}
    ledger.setdefault('files', {})
    ledger.setdefault('edited', [])
    return ledger


def save(ledger):
    folder = os.path.dirname(LEDGER)
    if not os.path.isdir(folder):
        os.makedirs(folder)
    tmp = LEDGER + '.tmp'
    with io.open(tmp, 'w', encoding='utf-8') as f:
        f.write(json.dumps(ledger, indent=1, sort_keys=True))
    os.replace(tmp, LEDGER)


def _note(ledger, rel, gate, ok, called=None):
    entry = {'sha1': digest(_full(rel)), 'ok': bool(ok)}
    if called is not None:
        entry['called'] = bool(called)
    ledger['files'].setdefault(rel, {})[gate] = entry


def record(path, gate, ok, called=None):
    """What `lint` and `run` call: `gate` passed or failed on the content of
    `path` as it is now. Writes nothing outside a Claude Code session with
    the kit's settings, nor for a file outside programs/."""
    rel = program_rel(path)
    if not enabled() or rel is None or not os.path.isfile(_full(rel)):
        return
    ledger = load()
    _note(ledger, rel, gate, ok, called)
    save(ledger)


def post_edit(event):
    """The hook after Edit, Write and MultiEdit. -> (exit code, stdout,
    stderr). Exit 2 puts stderr in front of the agent; it does not undo the
    edit, which has already been made."""
    from hpkit import lint
    path = (event.get('tool_input') or {}).get('file_path') or ''
    rel = program_rel(path) if path else None
    if rel is None or not os.path.isfile(_full(rel)) or not is_ppl(_full(rel)):
        return 0, '', ''
    text = _read(_full(rel)).decode('utf-8-sig')
    found, _ = lint.check_source(rel, text)
    errors = [a for a in found if a.level == 'ERROR']
    warnings = [a for a in found if a.level != 'ERROR']

    ledger = load()
    if rel not in ledger['edited']:
        ledger['edited'].append(rel)
    _note(ledger, rel, 'lint', not errors)
    save(ledger)

    if errors:
        lines = '\n'.join(str(a) for a in errors + warnings)
        return 2, '', ('hpprime lint: %s has %d error(s). The calculator '
                       'would refuse it; fix them before anything else, '
                       'since the turn cannot end with them:\n%s\n'
                       % (rel, len(errors), lines))
    if warnings:
        context = ('hpprime lint: %s has no error and %d warning(s):\n%s'
                   % (rel, len(warnings),
                      '\n'.join(str(a) for a in warnings)))
        return 0, json.dumps({'hookSpecificOutput': {
            'hookEventName': 'PostToolUse',
            'additionalContext': context}}), ''
    return 0, '', ''


def cited(text):
    """-> the fact identifiers `text` cites, in backticks or as a link's
    text, shaped topic.slug with one of the documentation's topics; file
    names such as `ppl.md` left out."""
    topics = set(f[:-3] for f in os.listdir(TOPICS) if f.endswith('.md'))
    out = []
    for a, b in CITED.findall(text or ''):
        m = IDENT.match((a or b).strip())
        if (m and m.group(1) in topics and m.group(2) not in EXTENSIONS
                and m.group(0) not in out):
            out.append(m.group(0))
    return out


def facts():
    out = set()
    for f in os.listdir(TOPICS):
        if f.endswith('.md'):
            with io.open(os.path.join(TOPICS, f), encoding='utf-8') as fh:
                out.update(ANCHOR.findall(fh.read()))
    return out


def unknown_citations(text):
    """-> the identifiers `text` cites that name no fact."""
    ids = cited(text)
    have = facts() if ids else set()
    return [i for i in ids if i not in have]


def missing(ledger):
    """-> what the programs edited since the last passed check still lack,
    as lines naming the command that would supply each. Programs that are
    gone, or are no longer PPL, leave the edited list."""
    problems, keep = [], []
    for rel in ledger['edited']:
        full = _full(rel)
        if not os.path.isfile(full) or not is_ppl(full):
            continue
        keep.append(rel)
        sha = digest(full)
        entry = ledger['files'].get(rel, {})
        lint_, run_ = entry.get('lint', {}), entry.get('run', {})
        if lint_.get('sha1') != sha:
            problems.append('%s: no lint of its current content. Run: '
                            'hpprime lint %s' % (rel, rel))
        elif not lint_.get('ok'):
            problems.append('%s: lint finds errors in it. Fix them and run '
                            'hpprime lint %s again' % (rel, rel))
        if run_.get('sha1') != sha:
            problems.append('%s: no run of its current content. Run: '
                            'hpprime run %s --call "NAME(...)", with calls whose '
                            'answers you know, or with no --call if nothing in '
                            'it can answer on the PC' % (rel, rel))
        elif not run_.get('ok'):
            problems.append('%s: its run on this content raised: it did not '
                            'load, or a call failed' % rel)
    ledger['edited'] = keep
    return problems


def only_loaded(ledger):
    """-> the edited programs whose run on their current content loaded them
    and called nothing."""
    out = []
    for rel in ledger['edited']:
        full = _full(rel)
        if not os.path.isfile(full):
            continue
        run_ = ledger['files'].get(rel, {}).get('run', {})
        if (run_.get('sha1') == digest(full) and run_.get('ok')
                and run_.get('called') is False):
            out.append(rel)
    return out


def stop(event):
    """The hook when the agent finishes. -> (exit code, stdout, stderr).
    Exit 2 sends the agent back with stderr; exit 0 with a systemMessage
    lets it finish and tells the person."""
    ledger = load()
    problems = missing(ledger)
    for ident in unknown_citations(event.get('last_assistant_message')):
        problems.append('`%s` names no fact in docs/topics/. Cite one that '
                        'exists, or drop it' % ident)
    if not problems:
        loaded = only_loaded(ledger)
        if ledger['edited'] or 'guard' in ledger:
            ledger['edited'] = []
            ledger.pop('guard', None)
            save(ledger)
        if loaded:
            return 0, json.dumps({'systemMessage': (
                'hpprime: loaded on the PC and never called, so nothing they '
                'do was checked there: %s. What they do is for the calculator '
                'to show.' % ', '.join(loaded))}), ''
        return 0, '', ''

    behind = dict((rel, ledger['files'].get(rel)) for rel in ledger['edited'])
    signature = hashlib.sha1(json.dumps([problems, behind], sort_keys=True)
                             .encode('utf-8')).hexdigest()
    guard = ledger.get('guard') or {}
    count = guard.get('count', 0) + 1 if guard.get('sig') == signature else 1
    listed = '\n'.join('- ' + p for p in problems)
    if count >= GUARD:
        ledger['edited'] = []
        ledger.pop('guard', None)
        save(ledger)
        return 0, json.dumps({'systemMessage': (
            'hpprime: the agent finished without showing this, after being '
            'sent back for it %d times:\n%s' % (GUARD - 1, listed))}), ''
    ledger['guard'] = {'sig': signature, 'count': count}
    save(ledger)
    return 2, '', (
        'hpprime: before finishing, show the evidence AGENTS.md section 2 '
        'asks for:\n%s\nIf a program cannot be run here, because the '
        'interpreter does not cover what it uses, say so plainly in your '
        'report. Switching these checks off is the person\'s decision, not '
        'yours.\n' % listed)


def _write(stream, text):
    if text:
        stream.buffer.write(text.encode('utf-8'))
        stream.buffer.flush()


def cli(argv):
    hooks = {'post-edit': post_edit, 'stop': stop}
    if not argv or argv[0] not in hooks:
        print(USAGE)
        return 2
    try:
        event = json.loads(sys.stdin.buffer.read().decode('utf-8-sig') or '{}')
    except ValueError as e:
        _write(sys.stderr, 'hpprime hook: the event is not JSON: %s\n' % e)
        return 1
    kit = kit_of(event['cwd']) if event.get('cwd') else None
    if kit:
        use_kit(kit)
    code, out, err = hooks[argv[0]](event)
    _write(sys.stdout, out)
    _write(sys.stderr, err)
    return code
