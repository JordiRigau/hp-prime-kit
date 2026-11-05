# -*- coding: utf-8 -*-
"""Tests for the gates' ledger and the hook that lints after an edit.

In Claude Code the kit's hooks put `lint` in front of the agent after every
edit of a program in programs/, and `lint` and `run` note what content they
passed. This holds what the hook must say, what it must leave alone, and
when the tools may write the ledger, on a kit folder made in a temporary
directory and hook events made here.

    python tests/test_gates.py
"""
from __future__ import unicode_literals
import io, json, os, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import gates, interp, lint

PASS, FAIL = [0], [0]

ERROR = 'EXPORT F(x)\nBEGIN\n IF x>1 THEN RETURN 1; ENDIF;\n RETURN 0;\nEND;\n'
WARNING = 'EXPORT G(x)\nBEGIN\n RETURN FOOBARZ(x);\nEND;\n'
CLEAN = 'EXPORT H(x)\nBEGIN\n RETURN x*2;\nEND;\n'


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


class quiet(object):
    def __enter__(self):
        self.old = sys.stdout
        sys.stdout = io.StringIO() if str is not bytes else io.BytesIO()
        return self

    def __exit__(self, *exc):
        sys.stdout = self.old
        return False


def put(kit, rel, text):
    path = os.path.join(kit, *rel.split('/'))
    if not os.path.isdir(os.path.dirname(path)):
        os.makedirs(os.path.dirname(path))
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return path


def edited(path):
    return {'hook_event_name': 'PostToolUse', 'tool_name': 'Edit',
            'tool_input': {'file_path': path}}


def main():
    tmp = tempfile.mkdtemp(prefix='hpgates_')
    saved = (gates.ROOT, gates.PROGRAMS, gates.LEDGER,
             os.environ.get(gates.FLAG))
    gates.ROOT = tmp
    gates.PROGRAMS = os.path.join(tmp, 'programs')
    gates.LEDGER = os.path.join(tmp, '.claude', 'hpprime-gates.json')
    os.environ.pop(gates.FLAG, None)
    try:
        err = put(tmp, 'programs/F/F.txt', ERROR)
        warn = put(tmp, 'programs/G/G.txt', WARNING)
        clean = put(tmp, 'programs/H/H.txt', CLEAN)
        outside = put(tmp, 'examples/X/X.txt', ERROR)
        pyfile = put(tmp, 'programs/APP/main.py', 'x = 1\n')
        note = put(tmp, 'programs/H/notes.txt', 'ideas for later\n')

        print('-- what counts as a program')
        ok(gates.program_rel(err) == 'programs/F/F.txt',
           'a .txt in programs/ is one, named from the kit')
        ok(gates.program_rel(outside) is None, 'one outside programs/ is not')
        ok(gates.program_rel(pyfile) is None, 'a .py in programs/ is not')

        print('\n-- the hook after an edit')
        code, out, errtext = gates.post_edit(edited(err))
        ok(code == 2, 'an error comes back with exit 2')
        ok('programs/F/F.txt' in errtext and 'single-end' in errtext and
           'ppl.no-end-keywords' in errtext,
           'naming the file, the rule and its fact', errtext)
        ledger = gates.load()
        ok(ledger['edited'] == ['programs/F/F.txt'],
           'the file joins the edited ones')
        ok(ledger['files']['programs/F/F.txt']['lint']['ok'] is False,
           'and its lint is recorded failed, without the variable')

        code, out, errtext = gates.post_edit(edited(warn))
        context = json.loads(out)['hookSpecificOutput'] if out else {}
        ok(code == 0 and not errtext, 'a warning does not stop the agent')
        ok(context.get('hookEventName') == 'PostToolUse' and
           'FOOBARZ' in context.get('additionalContext', ''),
           'and reaches it as context', out)
        ok(gates.load()['files']['programs/G/G.txt']['lint']['ok'] is True,
           'a warning is a lint that passed')

        code, out, errtext = gates.post_edit(edited(clean))
        ok((code, out, errtext) == (0, '', ''), 'a clean program is silent')

        before = gates.load()
        for path, what in [(outside, 'a file outside programs/'),
                           (pyfile, 'a .py'),
                           (note, 'a .txt with no BEGIN'),
                           (os.path.join(tmp, 'programs', 'gone.txt'),
                            'a file that is not there')]:
            ok(gates.post_edit(edited(path)) == (0, '', ''),
               '%s is left alone' % what)
        ok(gates.load() == before, 'and none of them reaches the ledger')
        ok(gates.post_edit({}) == (0, '', ''), 'an event with no file too')

        print('\n-- what lint and run record, and when')
        shutil.rmtree(os.path.join(tmp, '.claude'))
        with quiet():
            lint.check_files([clean])
            interp.cli([clean, '--call', 'H(2)'])
        ok(not os.path.exists(gates.LEDGER),
           'without the variable, lint and run write nothing')

        os.environ[gates.FLAG] = '1'
        with quiet():
            lint.check_files([clean, err])
        files = gates.load()['files']
        ok(files['programs/H/H.txt']['lint']['ok'] is True and
           files['programs/F/F.txt']['lint']['ok'] is False,
           'with it, lint records each file by its own findings')
        ok(files['programs/H/H.txt']['lint']['sha1'] == gates.digest(clean),
           'against the content it read')

        with quiet():
            interp.cli([clean, '--call', 'H(2)'])
        ok(gates.load()['files']['programs/H/H.txt']['run']['ok'] is True,
           'a run whose calls all answered is recorded passed')
        with quiet():
            interp.cli([clean, '--call', 'NOSUCH(2)'])
        ok(gates.load()['files']['programs/H/H.txt']['run']['ok'] is False,
           'one whose call raised, failed')
        with quiet():
            interp.cli([clean])
        run_ = gates.load()['files']['programs/H/H.txt']['run']
        ok(run_['ok'] is True and run_['called'] is False,
           'one with no --call is recorded as loaded, and as calling nothing')
        with quiet():
            lint.check_files([outside])
        ok('examples/X/X.txt' not in gates.load()['files'],
           'a file outside programs/ is never recorded')

        print('\n-- the end check: evidence')
        fresh = lambda: shutil.rmtree(os.path.join(tmp, '.claude'),
                                      ignore_errors=True)
        fresh()
        ok(gates.stop({}) == (0, '', '') and not os.path.exists(gates.LEDGER),
           'no edit and no citation: silent, and nothing written')

        gates.post_edit(edited(clean))
        code, out, errtext = gates.stop({})
        ok(code == 2 and 'programs/H/H.txt: no run of its current content'
           in errtext and 'hpprime run programs/H/H.txt' in errtext,
           'an edited program with no run sends the agent back, naming run',
           errtext)
        ok('no lint' not in errtext, 'the lint the hook ran counts')
        with quiet():
            interp.cli([clean, '--call', 'H(2)'])
        ok(gates.stop({}) == (0, '', ''),
           'with lint and run on its current content, the agent finishes')
        ok(gates.load()['edited'] == [] and 'guard' not in gates.load(),
           'and the edited list is cleared')

        gates.post_edit(edited(clean))
        with quiet():
            interp.cli([clean])
        code, out, errtext = gates.stop({})
        message = json.loads(out).get('systemMessage', '') if out else ''
        ok(code == 0 and 'programs/H/H.txt' in message and 'never called' in message,
           'a program only loaded lets the agent finish, and the person is told',
           out + errtext)
        ok(gates.stop({}) == (0, '', ''), 'and is told once')

        put(tmp, 'programs/H/H.txt', CLEAN.replace('x*2', 'x*3'))
        gates.post_edit(edited(clean))
        code, _, errtext = gates.stop({})
        ok(code == 2 and 'no run of its current content' in errtext,
           'an edit after the run sends it back again')

        gates.post_edit(edited(err))
        code, _, errtext = gates.stop({})
        ok(code == 2 and 'programs/F/F.txt: lint finds errors' in errtext,
           'a program with a lint error sends it back, naming lint', errtext)
        os.remove(err)
        code, _, errtext = gates.stop({})
        ok('programs/F/F.txt' not in errtext and
           gates.load()['edited'] == ['programs/H/H.txt'],
           'a program that was deleted leaves the list')

        print('\n-- the end check: out of a loop')
        fresh()
        gates.post_edit(edited(clean))
        first, second = gates.stop({}), gates.stop({})
        code, out, errtext = gates.stop({})
        message = json.loads(out).get('systemMessage', '') if out else ''
        ok(first[0] == 2 and second[0] == 2,
           'the same problems send the agent back twice')
        ok(code == 0 and 'programs/H/H.txt' in message and not errtext,
           'the third time it finishes, and the person is told what was '
           'never shown', out)
        ok(gates.load()['edited'] == [] and 'guard' not in gates.load(),
           'and the list starts again')

        fresh()
        gates.post_edit(edited(clean))
        gates.stop({})
        with quiet():
            interp.cli([clean, '--call', 'NOSUCH(1)'])
        codes = [gates.stop({})[0] for _ in range(3)]
        ok(codes == [2, 2, 0],
           'a change in the ledger starts the count again', repr(codes))

        print('\n-- the end check: citations')
        fresh()
        good = ('Known from (`ppl.one-based`, G2) and '
                '[ppl.local-limit](docs/topics/ppl.md#ppl.local-limit).')
        ok(gates.cited(good) == ['ppl.one-based', 'ppl.local-limit'],
           'identifiers are read in backticks and as a link\'s text')
        ok(gates.stop({'last_assistant_message': good}) == (0, '', ''),
           'facts that exist let the agent finish')
        code, _, errtext = gates.stop(
            {'last_assistant_message': 'as `ppl.no-such-fact` says'})
        ok(code == 2 and '`ppl.no-such-fact` names no fact' in errtext,
           'one that does not exist sends it back', errtext)
        ok(gates.cited('`ppl.md`, `deploy.md`, `hpkit.gates`, '
                       '`micropython.org`, `RELOJ.txt`, ppl.one-based') == [],
           'file names, modules, sites and bare words are not citations')

        print('\n-- the citations the kit makes itself')
        agents = io.open(os.path.join(ROOT, 'AGENTS.md'),
                         encoding='utf-8').read()
        ids = gates.cited(agents)
        ok(len(ids) >= 10 and not gates.unknown_citations(agents),
           'every fact AGENTS.md cites exists (%d)' % len(ids),
           repr(gates.unknown_citations(agents)))

        print('\n-- a session in a worktree')
        # A desktop-app session on a clone can run in a copy of the kit under
        # .claude/worktrees/, while the hook runs from the folder it started
        # in. Seen on 2026-10-02: the hook read the main folder's facts and
        # did not watch the copy's programs/.
        fresh()
        copy = os.path.join(tmp, '.claude', 'worktrees', 'copy')
        put(copy, 'hpprime.py', '')
        put(copy, 'docs/topics/ppl.md', '<a name="ppl.only-in-the-copy"></a>\n')
        there = put(copy, 'programs/W/W.txt', ERROR)
        inside = os.path.join(copy, 'programs', 'W')
        ok(gates.kit_of(inside) == copy,
           'the kit is the nearest folder holding hpprime.py and docs/topics/')
        ok(gates.program_rel(there) is None,
           'seen from the main folder, the copy\'s program is not watched')
        topics_before = gates.TOPICS
        try:
            gates.use_kit(copy)
            ok(gates.program_rel(there) == 'programs/W/W.txt',
               'seen from its own kit, it is')
            code, _, errtext = gates.post_edit(edited(there))
            ok(code == 2 and 'single-end' in errtext,
               'and the hook after an edit lints it', errtext)
            ok(os.path.isfile(os.path.join(copy, '.claude', 'hpprime-gates.json')),
               'with the ledger in the copy, not the main folder')
            ok(gates.unknown_citations('`ppl.only-in-the-copy`') == [],
               'and a fact added in the copy is a fact')
        finally:
            gates.use_kit(tmp)
            gates.TOPICS = topics_before
    finally:
        gates.ROOT, gates.PROGRAMS, gates.LEDGER, flag = saved
        if flag is None:
            os.environ.pop(gates.FLAG, None)
        else:
            os.environ[gates.FLAG] = flag
        shutil.rmtree(tmp, ignore_errors=True)

    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
