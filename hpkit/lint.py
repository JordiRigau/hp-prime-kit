# -*- coding: utf-8 -*-
"""HP PPL linter: catches, before you compile, what the Prime's compiler
refuses to explain.

The Prime's compiler prints `syntax error` and points at a line. It does not
say what is wrong with it, so a mistake as small as one variable too many in
a LOCAL statement costs several compile-and-look rounds. Every rule here
comes from an error measured on a real calculator, not from reading a manual,
and it is an ERROR only as far as that measurement reaches. Where a rule's
pattern goes further, to cases nobody has run, it is a warning, and the
finding says so.

    hpprime lint FILE.txt [more files or folders...]
    hpprime lint ppl/ --quiet      # errors only, no warnings
    hpprime lint A.txt B.txt --set # the files go onto the calculator
                                   # together: exported names that would
                                   # clash, and calls none of them defines

Output is compiler-shaped:  file:line: level: rule: message [fact, label]
The label is how the finding is known, in docs/format.md's words: G2 or
emulator where the case was measured, unverified where the rule reaches past
the measurement. A rule that comes from no fact ends in [no fact].
Exit code 1 if there is any ERROR.

A call to a name that is not a PPL name, from the documentation's list in
docs/commands/names.tsv, and that the program does not define is flagged as
unknown-name: a warning for a file on its own, because it may be calling a
function another program exports, and an error with --set, where all the
files that go together are in view.

What this deliberately does NOT flag, because each was checked on hardware
and found legal:

  - RETURN inside a FOR or a REPEAT.
  - locals made of letter + digit (r2, y1, L12).
  - several locals given initial values on one line.
  - a LOCAL after other statements.
  - up to 8 variables in one EXPORT.
  - a call with no arguments and no parentheses.
  - a function, a parameter or a local called like one of Home's variables.
  - a nested LOCAL that repeats an outer one, or is declared again after its
    block.

They are listed so nobody "fixes" them back in.
"""
from __future__ import unicode_literals
import io, os, re, sys
from collections import OrderedDict

# Variables per LOCAL statement. Measured on a G2, firmware 2.4.15515, on
# 2026-11-05: 8 in one statement answered and 9 did not compile. Functions that
# failed before that declared 13, 16 and 18, and on the Virtual Calculator 2.4,
# build 2025-09-15, on 2026-09-24, 9, 10, 11 and 12 failed too. So 9 and more is
# an error, and 8 and fewer, which compile, are not flagged.
LOCAL_MAX = 8                   # the most seen to compile
LOCAL_FAILS = 9                 # the fewest seen to fail

# Variables in one EXPORT. Measured on a G2, firmware 2.4.15515, on 2026-11-05,
# with prefixed names: with initial values 6, 7 and 8 compiled and 9 did not, and
# with none, 8 compiled and 9 did not. Two to six compiled on the Virtual
# Calculator, on 2026-09-24 and 2026-09-25. Some with values and some without has
# not been run.
EXPORT_MAX = 8                  # the most seen to compile
EXPORT_FAILS = 9                # the fewest seen to fail

# The calculator's own variables that were measured being exported: none
# compiled on that G2, each on its own (ppl.export-home-variable).
EXPORT_REFUSED = ('A', 'Y', 'Z')

# ENDIF, ENDFOR and ENDWHILE were measured to fail on a G2, ENDCASE and
# ENDFUNC on the Virtual Calculator on 2026-09-24, and ENDPROC on 2026-09-25.
BAD_BLOCK_ENDS = ('ENDIF', 'ENDFOR', 'ENDWHILE')
BAD_BLOCK_ENDS_EMULATOR = ('ENDCASE', 'ENDFUNC', 'ENDPROC')

# The null-hypothesis mean as HP's list spells it, with the Greek mu, which
# does not compile; with the micro sign it answers (emulator, 2026-09-25).
MU_ZERO = '\u03bc\u2080'

# Characters TEXTOUT_P drew as an empty box, in font 3, on the Virtual
# Calculator 2.4 build 2025-09-15, on 2026-09-29, each with one the same
# screen drew to write instead (interface.font-glyphs). Fonts 1 and 2, and
# the other commands that draw text, were not tried with them.
BOX_GLYPHS = OrderedDict([
    ('\u25c4', '\u25c0'),       # left pointer -> left triangle
    ('\u25c2', '\u25c0'),       # small left triangle -> left triangle
    ('\u25b8', '\u25b6'),       # small right triangle -> right triangle
    ('\u2bc7', '\u25c0'),       # left-pointing arrowhead -> left triangle
    ('\u2bc8', '\u25b6'),       # right-pointing arrowhead -> right triangle
])
BOX_FONT = '3'

# The drawing commands without _P count the plot window's units, from the
# middle of the screen: -15.9 to 15.9 across and -10.9 to 10.9 up on a reset
# calculator (interface.draw-units). A literal coordinate beyond 16, or a
# grob size beyond 32, reads as pixels written in units.
UNITS_LIMIT = 16
UNITS_SIZE_LIMIT = 32

# What draws on the screen, and what makes a program stay until somebody has
# seen it. FREEZE is among the second: what it does after a drawing has not
# been measured, and a rule leaves alone what it cannot judge.
DRAWS = ('TEXTOUT_P', 'TEXTOUT', 'RECT_P', 'RECT', 'LINE_P', 'LINE',
         'ARC_P', 'ARC', 'BLIT_P', 'BLIT', 'FILLPOLY_P', 'FILLPOLY',
         'PIXON_P', 'PIXON', 'INVERT_P', 'INVERT', 'DRAWMENU')
WAITS = ('WAIT', 'GETKEY', 'MOUSE', 'ISKEYDOWN', 'FREEZE', 'MSGBOX', 'INPUT',
         'CHOOSE')

# An app's program exports these for the app to call (apps.hooks): they
# return to the app, not to Home, and are exported on purpose.
HOOKS = ('START', 'NUM', 'PLOT', 'SYMB', 'VIEW', 'INFO', 'RESET', 'NUMSETUP',
         'PLOTSETUP', 'SYMBSETUP')
KEYWORDS = set("""IF THEN ELSE END FOR FROM TO DOWNTO STEP DO WHILE REPEAT
UNTIL CASE DEFAULT BREAK CONTINUE RETURN LOCAL EXPORT BEGIN AND OR NOT
IFTE""".split())

# The calculator's own variables: A to Z, θ, and the numbered lists,
# matrices, graphics and complex variables.
CALC_VARIABLE = re.compile(r'^([A-Z]|θ|[LMGZ][0-9])$')

# A name as the calculator writes it. Some of its own names carry an arrow --
# C→PX, PX→C, →HMS, B→R -- and the arrow is part of the name, not an operator
# (PPL assigns with :=). A rule that matches a name has to admit it: with
# [A-Za-z_]\w* the match starts after the arrow, so C→PX(0,0) reads as an
# index 0 into a variable PX and the rule fires on correct code.
NAME = r'[A-Za-z_→][\w→]*'
NOT_NAME = r'(?<![\w→])'

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The kinds of listed name that are read rather than called.
VARIABLE_KINDS = ('variable', 'app variable')

_KNOWN = None
_KINDS = None


def _kit(module):
    """hpkit.<module>, whether this runs inside the kit or as hpkit/lint.py."""
    try:
        return __import__('hpkit.' + module, fromlist=[module])
    except ImportError:
        sys.path.insert(0, ROOT)
        return __import__('hpkit.' + module, fromlist=[module])


def known_names():
    """Every name on the documentation's list, lower case, or an empty set
    if the list is not there. Compared without regard to case, so that no
    spelling the calculator might accept is flagged; whether the calculator
    itself ignores case in its names has not been measured."""
    global _KNOWN
    if _KNOWN is None:
        _KNOWN = _kit('names').known()
    return _KNOWN


def _listed_kinds():
    """-> {name in lower case: the set of kinds the list gives it}."""
    global _KINDS
    if _KINDS is None:
        _KINDS = {}
        if known_names():
            names = _kit('names')
            for n in names.read(names.PATH)[0]:
                _KINDS.setdefault(n.name.lower(), set()).add(n.kind)
    return _KINDS


def is_known(name, defined):
    """Is `name` something a call may use: the program's own, a keyword, a
    calculator variable, or a name on the list?"""
    return (name in defined or name.upper() in KEYWORDS
            or CALC_VARIABLE.match(name) is not None
            or name.lower() in known_names())


def name_kind(name, functions, variables):
    """-> 'function' if `name(...)` is a call, 'variable' if it indexes, or
    '' when neither the file nor the list says which."""
    if name in functions:
        return 'function'
    if name in variables or CALC_VARIABLE.match(name):
        return 'variable'
    kinds = _listed_kinds().get(name.lower(), set())
    if kinds - set(VARIABLE_KINDS) - {'unknown'}:
        return 'function'
    if kinds & set(VARIABLE_KINDS):
        return 'variable'
    return ''


# Every rule says which fact in docs/topics/ it comes from, so that a message
# can be checked rather than believed. A rule that comes from something else
# says what, rather than borrowing a fact that does not fit.
# tests/test_lint.py holds both halves to the topic pages.
FACTS = {
    'single-end': 'ppl.no-end-keywords',
    'index-call': 'ppl.index-call',
    'one-based': 'ppl.one-based',
    'local-limit': 'ppl.local-limit',
    'local-scope': 'ppl.local-block-scope',
    'export-limit': 'ppl.export-initialised',
    'export-home-variable': 'ppl.export-home-variable',
    'expr-empty': 'ppl.expr-empty',
    'textout-width': 'interface.textout-width',
    'end-semicolon': 'ppl.end-semicolon',
    'export-clash': 'ppl.global-namespace',
    'equality-statement': 'ppl.equality-operators',
    'mu-zero': 'ppl.mu-zero-spelling',
    'getkey-code': 'interface.getkey-position',
    'string-index': 'ppl.string-index-code',
    'draw-units': 'interface.draw-units',
    'draw-then-return': 'interface.draw-then-return',
    'wait-undrained': 'interface.drain-then-wait',
    'wait-touch': 'interface.wait-events',
    'expr-in-loop': 'ppl.expr-dynamic-access',
    'font-glyph': 'interface.font-glyphs',
}

NO_FACT = {
    'unbalanced': 'a block left open, which the compiler reports itself: no '
                  'fact about the platform is involved',
    'unknown-name': 'the list of names in docs/commands/names.tsv, which is '
                    'an inventory and not a fact about the platform',
}

# What catches each fact of docs/topics/ from a PC, or why nothing can: one
# line per fact, and `hpprime docs` writes it as a table into docs/tools.md.
# tests/test_lint.py fails if a fact has no line, a line names no fact, a
# rule is not a rule, or a test named is not where the line says. An answer
# is one of:
#   ('rule', name)                          a rule of this linter
#   ('write', name)                         a check decided on and not
#                                           written: the tests fail while
#                                           one is left
#   ('command', command, test file, words)  another hpprime command does it,
#                                           and that test holds it
#   ('quiet',)                              nothing to catch: the mistake
#                                           would be to flag it, and QUIET in
#                                           tests/test_lint.py holds that
#   ('no', why)                             nothing on a PC can see it
_ACTIVE = "which app is active is the calculator's state, not the file's"
_ANSWER = 'it is about what the calculator answers, which the source does not show'
_HANDS = "it is a person's action in the Connectivity Kit or on the calculator"
_SCREEN = 'it is about what a person sees on the screen'
_TIMING = 'it is a time, which only the calculator can take'
_OTHERS = "it is about somebody else's code, not run here"
_T_APP = 'tests/test_appdir.py'
_T_EMU = 'tests/test_emulator.py'
_T_PRG = 'tests/test_program.py'
_T_NUM = 'tests/test_numbers.py'
_T_RUN = 'tests/test_interp.py'
_T_USB = 'tests/test_usb.py'
CAUGHT = OrderedDict([
    # apps
    ('apps.hpappdir-contents',
     [('command', 'build', _T_APP, 'creates the .hpappdir folder')]),
    ('apps.startup-view-byte',
     [('command', 'verify', _T_APP,
       'sees the rewritten .hpapp (the Python-console failure)')]),
    ('apps.icon',
     [('no', 'what another size does was not measured, so none can be '
             'called wrong')]),
    ('apps.two-kinds',
     [('command', 'verify', _T_APP, 'a PPL app is recognised by its program')]),
    ('apps.hooks',
     [('no', 'a hook is an exported function like any other, so a file '
             'cannot say which ones were meant as hooks')]),
    ('apps.blank-app-hooks',
     [('no', "it is what the calculator does with an app's views while "
             'its program runs')]),
    ('apps.blank-app-keys',
     [('no', 'which keys arrive is known only while the program runs')]),
    ('apps.exports-tied',
     [('no', 'where a program is installed, in an app or in the catalogue, '
             'is not in its file')]),
    ('apps.wrappers-are-portable',
     [('command', 'build', _T_APP,
       'the wrapper comes out byte for byte like the template')]),
    ('apps.main-py',
     [('command', 'build', _T_APP, 'warns when a Python app has no main.py')]),
    ('apps.install',
     [('command', 'install', _T_EMU, 'the app lands as a folder'),
      ('no', 'on a physical calculator it is a person dragging the folder '
             'in the Connectivity Kit')]),
    ('apps.generated-and-verified',
     [('command', 'verify', _T_APP,
       'the generated .hpappprgm gives back the same source')]),
    ('apps.hpapp-not-generated',
     [('command', 'build', _T_APP,
       'the wrapper comes out byte for byte like the template')]),
    ('apps.empty-hpappprgm-not-a-template',
     [('command', 'build', _T_APP,
       'rejects the empty .hpappprgm as a template')]),
    ('apps.function-needs-active-app', [('no', _ACTIVE)]),
    ('apps.qualified-names',
     [('quiet',),
      ('command', 'run', _T_RUN, 'not_covered_is_not_an_error')]),
    ('apps.triangle-solver-degrees', [('no', _ACTIVE)]),
    ('apps.reset-leaves-function-active',
     [('no', 'it is the state a reset leaves on the calculator')]),
    ('apps.app-mode-overrides-home', [('no', _ACTIVE)]),
    ('apps.finance-shows-two-decimals', [('no', _ACTIVE)]),
    # deploy
    ('deploy.emulator-folder',
     [('command', 'install', _T_EMU,
       'the program lands in the calculator folder')]),
    ('deploy.compile-once-after-a-file-copy',
     [('no', 'Check is a key pressed on the calculator: the tools say when '
             'to press it and cannot press it')]),
    ('deploy.results-come-back-on-exit',
     [('command', 'compare', 'tests/test_compare.py',
       'a missing matrix is an error that says what to do')]),
    ('deploy.which-window-opens',
     [('command', 'examples', 'tests/test_examples_run.py',
       'with Prime held, the next one opens Prime_1')]),
    ('deploy.calc-hpsettings-moves',
     [('command', 'examples', 'tests/test_examples_run.py',
       'an emulator that did not have %s is caught')]),
    ('deploy.ck-mirror',
     [('no', 'installing on a physical calculator is a person dragging the '
             'file in the Connectivity Kit')]),
    ('deploy.content-library-send', [('no', _HANDS)]),
    ('deploy.ck-offers-firmware', [('no', _HANDS)]),
    ('deploy.usb-without-the-ck',
     [('command', 'send', _T_USB,
       'send sends the reports and then the report that lets them act')]),
    ('deploy.drag-refused-when-elevated',
     [('no', "it is Windows' settings for the Connectivity Kit")]),
    ('deploy.no-manual-compile',
     [('no', 'it is what a physical calculator does with a file it '
             'receives')]),
    ('deploy.read-it-back',
     [('command', 'pull', _T_EMU,
       'pull --diff exits 1 when the calculator has something')]),
    ('deploy.writer-on-hardware',
     [('command', 'write', 'tests/test_cli.py',
       'write builds the binary with no -t (it finds the template)'),
      ('no', 'that it runs on a G2 is for the hardware to say')]),
    ('deploy.template-from-the-ck',
     [('command', 'write', _T_PRG,
       'the shipped template has no compiled block')]),
    ('deploy.which-calculator-is-which',
     [('command', 'emu', _T_EMU,
       'a clone does not claim to be the calculator it came from')]),
    # formats
    ('formats.container',
     [('command', 'write', _T_PRG,
       'the shipped template round-trips identical')]),
    ('formats.source-record',
     [('command', 'read', _T_PRG,
       'survives being written into the template')]),
    ('formats.wrapper-trap',
     [('command', 'read', _T_PRG,
       'sizes that used to come back as the wrapper')]),
    ('formats.trailer-varies',
     [('command', 'write', _T_PRG,
       'what was written can serve as a template in turn')]),
    ('formats.header-words',
     [('no', 'what the two words mean is not known, so no value can be '
             'called wrong')]),
    ('formats.line-endings',
     [('command', 'write', 'tests/test_cli.py',
       'read gives back the source that was written')]),
    ('formats.source-offset-152',
     [('command', 'write', _T_PRG,
       'the shipped template has no compiled block')]),
    ('formats.two-producers',
     [('command', 'write', _T_PRG,
       'the shipped template has no compiled block')]),
    ('formats.block-is-a-cache',
     [('no', 'the calculator builds the block, and nothing on the PC '
             'writes one')]),
    ('formats.block-not-byte-stable',
     [('no', 'it is about two compiles on the calculator, and no tool '
             'compares blocks')]),
    ('formats.number',
     [('command', 'matrix', _T_NUM, 'round trip of %r')]),
    ('formats.number-infinity',
     [('command', 'matrix', _T_NUM,
       'decodes the positive infinity the emulator wrote')]),
    ('formats.hpmat',
     [('command', 'matrix', _T_NUM, 'a 2x3 .hpmat is 16 + 6*8 bytes')]),
    ('formats.hpmat-vector',
     [('command', 'matrix', _T_NUM, 'rank %d, the numbers survive')]),
    ('formats.symbol-table',
     [('command', 'matrix', _T_NUM,
       'all %d matrices in the source are in the block')]),
    ('formats.matrix-type-byte',
     [('command', 'matrix', _T_NUM,
       'all %d matrices in the source are in the block')]),
    ('formats.value-types-undecoded',
     [('no', 'they are not decoded, so there is nothing to check a value '
             'against')]),
    ('formats.matrix-flag',
     [('no', 'what the flag means is not known')]),
    ('formats.entry-splice',
     [('no', 'nothing on the PC writes a symbol entry into a program')]),
    ('formats.other-files',
     [('command', 'install', _T_EMU, 'a .hpprgm that is not one is refused')]),
    # interface
    ('interface.geometry',
     [('no', 'a coordinate past the edge is clipped, not refused, and a '
             'file cannot say it was meant to be seen')]),
    ('interface.draw-units', [('rule', 'draw-units')]),
    ('interface.offscreen-grob',
     [('no', 'drawing straight onto the screen is correct; the flicker is '
             'what a person sees')]),
    ('interface.two-themes', [('no', _SCREEN)]),
    ('interface.textout-width', [('rule', 'textout-width')]),
    ('interface.text-measure', [('no', _ANSWER)]),
    ('interface.font-glyphs', [('rule', 'font-glyph')]),
    ('interface.input-fields',
     [('no', 'it is how a form looks on the screen, and only two label '
             'positions were measured')]),
    ('interface.input-modal',
     [('no', 'it is what a form does while it is open')]),
    ('interface.getkey-position', [('rule', 'getkey-code')]),
    ('interface.key-codes', [('rule', 'getkey-code')]),
    ('interface.soft-labels-not-keys',
     [('no', 'which keys a program gives its labels is a choice, and no '
             'code is wrong in itself')]),
    ('interface.draw-then-return', [('rule', 'draw-then-return')]),
    ('interface.drain-then-wait', [('rule', 'wait-undrained')]),
    ('interface.wait-minus-one',
     [('no', 'it waited on the emulator and once did not on a G2, for a '
             'reason not known, so there is no form to flag')]),
    ('interface.wait-events', [('rule', 'wait-touch')]),
    ('interface.mouse-lists',
     [('command', 'build', _T_APP, 'warns about MOUSE handed to Python raw')]),
    ('interface.touch-readings',
     [('no', "it is a finger's movement, which only a running app sees")]),
    ('interface.dialog-touch-twice',
     [('no', 'it is a touch that outlives a dialog, while the app runs')]),
    ('interface.screen-capacity', [('no', _SCREEN)]),
    # libraries
    ('libraries.published', [('no', _OTHERS)]),
    ('libraries.skeletonapp-container',
     [('command', 'install', _T_EMU, 'a .hpprgm that is not one is refused')]),
    ('libraries.usb-keyboard', [('no', _OTHERS)]),
    # micropython
    ('micropython.modules',
     [('command', 'build', _T_APP,
       'warns about "import time": MicroPython on the Prime has no time')]),
    ('micropython.community-modules',
     [('no', 'nobody here has run them, so none can be called missing')]),
    ('micropython.hpprime-module',
     [('no', 'it lists calls that work, and there is nothing in it to get '
             'wrong')]),
    ('micropython.hpprime-undocumented',
     [('no', 'none of it has been run here')]),
    ('micropython.eval',
     [('no', 'it says what works across the bridge, and there is nothing '
             'in it to get wrong')]),
    ('micropython.eval-parentheses',
     [('no', 'both forms answer, so neither is a mistake to flag')]),
    ('micropython.list-with-string-closes-the-app',
     [('command', 'build', _T_APP, 'warns about MOUSE handed to Python raw'),
      ('no', 'for any other call, what it returns is known only when it '
             'runs')]),
    ('micropython.string-quotes',
     [('no', 'the quote comes from data at run time')]),
    ('micropython.number-notation',
     [('no', 'the number is written at run time, and the failure has not '
             'been reproduced here')]),
    ('micropython.bridge-cost', [('no', _TIMING)]),
    ('micropython.imports',
     [('command', 'build', _T_APP,
       'does not look at imports inside a function')]),
    ('micropython.mark-debugging',
     [('no', 'it is a way of finding a failure, not a mistake')]),
    ('micropython.ppl-calls-python',
     [('no', 'it has not been measured here')]),
    ('micropython.not-measured',
     [('no', 'it is a list of what has not been measured')]),
    # ppl
    ('ppl.local-limit',
     [('rule', 'local-limit'),
      ('command', 'run', _T_RUN,
       '9 variables in one LOCAL, which does not compile')]),
    ('ppl.local-block-scope',
     [('rule', 'local-scope'),
      ('command', 'run', _T_RUN, 'a LOCAL read after its block ends')]),
    ('ppl.index-call', [('rule', 'index-call')]),
    ('ppl.export-initialised',
     [('rule', 'export-limit'),
      ('command', 'run', _T_RUN, '9 initialised variables in one EXPORT')]),
    ('ppl.export-home-variable',
     [('rule', 'export-home-variable'),
      ('command', 'run', _T_RUN, 'Z exported, on its own')]),
    ('ppl.no-end-keywords', [('rule', 'single-end')]),
    ('ppl.minus-sign', [('no', _ANSWER)]),
    ('ppl.one-based',
     [('rule', 'one-based'),
      ('command', 'run', _T_RUN, 'a list read at 0 answers its last element')]),
    ('ppl.string-index-code',
     [('rule', 'string-index'),
      ('command', 'run', _T_RUN, 'a string indexed answers the character code')]),
    ('ppl.names-ignore-case', [('quiet',)]),
    ('ppl.equality-operators', [('rule', 'equality-statement')]),
    ('ppl.short-circuit',
     [('quiet',),
      ('command', 'run', _T_RUN, 'AND and OR skip the side that does not decide')]),
    ('ppl.end-semicolon',
     [('rule', 'end-semicolon'),
      ('command', 'run', _T_RUN, 'a function whose END has no semicolon')]),
    ('ppl.global-index-other-program', [('quiet',)]),
    ('ppl.return-in-loop', [('quiet',)]),
    ('ppl.letter-digit-names', [('quiet',)]),
    ('ppl.local-m-matrices', [('quiet',)]),
    ('ppl.locals-initialised-one-line', [('quiet',)]),
    ('ppl.locals-at-top',
     [('quiet',),
      ('command', 'run', _T_RUN, 'a LOCAL after other statements')]),
    ('ppl.i-e-as-locals',
     [('quiet',),
      ('command', 'run', _T_RUN, 'i and e can be local names')]),
    ('ppl.imaginary-unit', [('no', _ANSWER)]),
    ('ppl.exponent-glyph', [('no', _ANSWER)]),
    ('ppl.exact-answers', [('no', _ANSWER)]),
    ('ppl.type-codes', [('no', _ANSWER)]),
    ('ppl.function-always-answers',
     [('command', 'run', _T_RUN, 'no RETURN, ending in a call')]),
    ('ppl.home-no-parentheses',
     [('no', 'it is what a person types on Home, which is not in a file')]),
    ('ppl.call-no-parentheses',
     [('quiet',),
      ('command', 'run', _T_RUN, 'a call without parentheses')]),
    ('ppl.getkey-no-parentheses', [('quiet',)]),
    ('ppl.matrices-by-value',
     [('command', 'run', _T_RUN, 'matrices are passed BY VALUE')]),
    ('ppl.expr-empty', [('rule', 'expr-empty')]),
    ('ppl.expr-dynamic-access', [('rule', 'expr-in-loop')]),
    ('ppl.global-namespace',
     [('rule', 'export-clash')]),
    ('ppl.decimal-point',
     [('no', 'a comma is also the argument separator, so F(3,5) reads the '
             'same either way')]),
    ('ppl.compilation-order',
     [('no', "which program was compiled first is the calculator's state")]),
    ('ppl.check-last-error',
     [('no', "it is what the calculator's editor shows")]),
    ('ppl.speed-anchor', [('no', _TIMING)]),
    ('ppl.mu-zero-spelling', [('rule', 'mu-zero')]),
    # usb
    ('usb.device',
     [('no', 'it is what Windows reads from a calculator, and no test has '
             'one')]),
    ('usb.one-program-at-a-time',
     [('command', 'screen', _T_USB,
       'a calculator held by the Connectivity Kit is an error that says so')]),
    ('usb.frames',
     [('command', 'screen', _T_USB,
       'a reply across several reports comes back whole')]),
    ('usb.screen',
     [('command', 'screen', _T_USB, 'white stored as FF7F is white')]),
    ('usb.keys',
     [('command', 'press', _T_USB,
       'press sends each key and then the report that makes it act'),
      ('no', 'that a key acted is for the calculator to show, and it '
             'acknowledges nothing')]),
    ('usb.letters',
     [('command', 'type', _T_USB,
       'every letter here is on the key the documentation gives it')]),
    ('usb.start-by-name',
     [('no', 'what a name starts is for the calculator to show')]),
    ('usb.program-message',
     [('command', 'send', _T_USB,
       'with the checksum the G2 itself put on SELFTEST')]),
    ('usb.compile-check',
     [('no', 'whether it compiled is for the calculator to show, and no test '
             'has one')]),
    ('usb.send-program',
     [('command', 'send', _T_USB,
       'send sends the reports and then the report that lets them act'),
      ('no', 'that a program arrived is for the calculator to show, and it '
             'acknowledges nothing')]),
    ('usb.file-request',
     [('no', 'no command asks for a file, and it is not known when one is '
             'answered')]),
    ('usb.status-area', [('no', _SCREEN)]),
    ('usb.newer-framing',
     [('no', 'no command uses that framing')]),
    ('usb.kit-window', [('no', _HANDS)]),
])

# How a finding is known, in docs/format.md's words. Where a rule matches
# what was measured, its finding carries the label of the rule's fact. Where
# the rule's pattern reaches past the measurement, the finding is a warning
# and says `unverified`, so an ERROR is only ever something a calculator was
# seen to refuse. tests/test_lint.py holds every rule to that.
MEASURED = ('G2', 'emulator')
UNVERIFIED = 'unverified'
EMULATOR = 'emulator'

_LABELS = {}


def fact_label(fact):
    """The `Known from` label of a fact in docs/topics/, or '' if its page is
    not there to say. Read with the parser the documentation's tests use."""
    if fact not in _LABELS:
        path = os.path.join(ROOT, 'docs', 'topics', fact.split('.')[0] + '.md')
        if os.path.isfile(path):
            for f in _kit('docs').read_topic(ROOT, path)[0]:
                _LABELS[f.ident] = f.label or ''
        _LABELS.setdefault(fact, '')
    return _LABELS[fact]


class Finding(object):
    def __init__(self, path, line, level, rule, msg, label=None):
        self.path, self.line = path, line
        self.level, self.rule, self.msg = level, rule, msg
        self._label = label

    @property
    def fact(self):
        """The identifier of the fact the rule comes from, or '' when the
        rule comes from something else: NO_FACT says what."""
        return FACTS.get(self.rule, '')

    @property
    def label(self):
        """How this finding is known: its fact's label, `unverified` where
        the rule reaches past what was measured, '' for a rule with no fact."""
        if self._label is not None:
            return self._label
        return fact_label(self.fact) if self.fact else ''

    def __str__(self):
        if self.fact:
            where = ' [%s]' % ', '.join(x for x in (self.fact, self.label) if x)
        elif self.rule in NO_FACT:
            where = ' [no fact]'
        else:
            where = ''
        return '%s:%d: %s: %s: %s%s' % (self.path, self.line, self.level,
                                        self.rule, self.msg, where)


def _strip_noise(line):
    """Drop comments and string contents, keeping the quotes.

    This stops rules from firing on text that is only a message for the user.
    Returns the line with its string literals emptied."""
    out, i, n, in_str = [], 0, len(line), False
    while i < n:
        c = line[i]
        if in_str:
            if c == '"':
                in_str = False
                out.append('"')
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append('"')
            i += 1
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        out.append(c)
        i += 1
    return ''.join(out)


def _literals(line):
    """-> [(start, end, contents)] for the string literals on a line, before
    any // comment, with start and end the positions of their quotes. A
    string left open runs to the end of the line, as in _strip_noise."""
    out, i, n = [], 0, len(line)
    while i < n:
        c = line[i]
        if c == '"':
            j = line.find('"', i + 1)
            j = n if j < 0 else j
            out.append((i, j, line[i + 1:j]))
            i = j + 1
            continue
        if c == '/' and i + 1 < n and line[i + 1] == '/':
            break
        i += 1
    return out


def _box_glyphs(path, num, line):
    """-> a font-glyph Finding for each character on the line that TEXTOUT_P
    was seen to draw as an empty box (interface.font-glyphs). What was
    measured is a string drawn by TEXTOUT_P in font 3: a literal inside such
    a call carries the fact's label, and one anywhere else -- a constant, a
    menu, another font -- says unverified."""
    every = _literals(line)
    literals = [l for l in every if any(g in l[2] for g in BOX_GLYPHS)]
    if not literals:
        return []
    # The line with each string's contents masked, so that positions still
    # match and a comma or a parenthesis inside a string counts for nothing.
    masked = list(line)
    for start, end, _ in every:
        masked[start + 1:end] = 'x' * (end - start - 1)
    masked = ''.join(masked)
    measured = []           # the spans of TEXTOUT_P calls in font 3
    for m in re.finditer(r'\bTEXTOUT_P\s*\(', masked, re.I):
        args = _call_args(masked, m.end() - 1)
        if args is None:
            continue
        parts = _split_top_level(args)
        font = 4 if len(parts) > 1 and re.match(r'^G\d$', parts[1].strip(),
                                                re.I) else 3
        if len(parts) > font and parts[font].strip() == BOX_FONT:
            measured.append((m.end(), m.end() + len(args)))
    found, seen = [], set()
    for start, _, text in literals:
        inside = any(a <= start < b for a, b in measured)
        for g, instead in BOX_GLYPHS.items():
            if g not in text or (g, inside) in seen:
                continue
            seen.add((g, inside))
            msg = ('U+%04X has no glyph in the font: TEXTOUT_P draws an '
                   'empty box in its place, and raises no error. U+%04X is '
                   'drawn' % (ord(g), ord(instead)))
            if not inside:
                msg += '. Measured with TEXTOUT_P in font 3 only'
            found.append(Finding(path, num, 'WARN', 'font-glyph', msg,
                                 None if inside else UNVERIFIED))
    return found


def _strip_block_comments(text):
    """Blank out /* ... */ comments, keeping their line breaks so that line
    numbers stay right."""
    out, i, n, in_str = [], 0, len(text), False
    while i < n:
        c = text[i]
        if not in_str and text.startswith('/*', i):
            j = text.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append(''.join('\n' if ch == '\n' else ' '
                               for ch in text[i:j]))
            i = j
            continue
        if c == '"':
            in_str = not in_str
        elif c == '\n':
            in_str = False
        out.append(c)
        i += 1
    return ''.join(out)


def _split_top_level(s):
    """Split on commas that are not inside (), {} or [].

    Brackets and braces matter: EXPORT NAMES:={"a","b","c"}; is ONE variable,
    not three, and counting its commas used to raise a false alarm."""
    parts, depth, cur = [], 0, []
    for c in s:
        if c in '({[':
            depth += 1
        elif c in ')}]':
            depth -= 1
        if c == ',' and depth == 0:
            parts.append(''.join(cur))
            cur = []
        else:
            cur.append(c)
    parts.append(''.join(cur))
    return [p.strip() for p in parts if p.strip()]


def _call_args(line, open_idx):
    """The text between a call's parentheses, or None if they do not close on
    this line.

    Lines are judged one at a time, so a call spanning several of them is
    left alone rather than guessed at: a false alarm teaches people to
    ignore the linter."""
    depth = 0
    for i in range(open_idx, len(line)):
        c = line[i]
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth == 0:
                return line[open_idx + 1:i]
    return None


def _block_delta(up):
    """How much a line opens blocks (BEGIN THEN DO CASE) against END."""
    opens = len(re.findall(r'\b(BEGIN|THEN|DO|CASE)\b', up))
    return opens - len(re.findall(r'\bEND\b', up))


def scan_names(text):
    """-> (the names a program defines, [(name, line) for every call]).

    Defined: its functions, exported or not, with their parameters; its
    LOCAL and EXPORT variables; any other global it declares at the top.
    A call is NAME( in code, outside strings, comments and #pragma lines."""
    functions, variables, calls = _scan(text)
    return functions | variables, calls


def _scan(text):
    """-> (its functions, its variables, [(name, line) for every call]).

    The variables are the functions' parameters, the LOCAL and EXPORT
    variables and any other global declared at the top: scan_names says the
    rest."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    lines = [_strip_noise(l) for l in _strip_block_comments(text).split('\n')]
    functions, variables, calls, depth = set(), set(), [], 0
    for k, raw in enumerate(lines):
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        up = s.upper()
        header = None
        if depth <= 0:
            m = re.match(r'^(?:EXPORT\s+|KEY\s+)?([A-Za-z_]\w*)\s*\(([^()]*)\)',
                         s, re.I)
            if m and m.group(1).upper() not in KEYWORDS:
                header = m.group(1)
                functions.add(header)
                for p in _split_top_level(m.group(2)):
                    pm = re.match(r'^([A-Za-z_]\w*)', p)
                    if pm:
                        variables.add(pm.group(1))
            elif not re.match(r'^(BEGIN|LOCAL)\b', up):
                body = re.sub(r'^EXPORT\s+', '', s, flags=re.I).split(';')[0]
                for part in _split_top_level(body):
                    pm = re.match(r'^([A-Za-z_]\w*)\s*(:=|$)', part)
                    if pm:
                        variables.add(pm.group(1))
        if re.match(r'^LOCAL\b', up):
            for part in _split_top_level(s[5:].split(';')[0]):
                pm = re.match(r'^([A-Za-z_]\w*)', part)
                if pm:
                    variables.add(pm.group(1))
        for m in re.finditer(NOT_NAME + r'(%s)\s*\(' % NAME, raw):
            if m.group(1) == header and m.start() == raw.find(header):
                continue                     # the definition, not a call
            calls.append((m.group(1), k + 1))
        depth += _block_delta(up)
    return functions, variables, calls


def check_source(path, text):
    """-> (list of Finding, list of (exported name, line))."""
    found = []
    lines = text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    clean = [_strip_noise(l) for l in lines]
    code = _strip_block_comments('\n'.join(lines)).split('\n')
    functions, variables, calls = _scan(text)

    exports = []
    in_body = False         # inside a function's BEGIN ... END
    depth = 0

    for k, raw in enumerate(clean):
        num = k + 1
        s = raw.strip()
        if not s:
            continue
        up = s.upper()

        # ---- ENDIF and friends -------------------------------------------
        for bad in BAD_BLOCK_ENDS:
            if re.search(r'\b%s\b' % bad, up):
                found.append(Finding(path, num, 'ERROR', 'single-end',
                                     '%s does not exist in PPL: every block '
                                     'closes with END' % bad))
        for bad in BAD_BLOCK_ENDS_EMULATOR:
            if re.search(r'\b%s\b' % bad, up):
                found.append(Finding(path, num, 'ERROR', 'single-end',
                                     '%s does not exist in PPL: every block '
                                     'closes with END' % bad, EMULATOR))

        # ---- the null-hypothesis mean with the Greek mu -------------------
        if MU_ZERO in raw:
            found.append(Finding(path, num, 'ERROR', 'mu-zero',
                                 '\u03bc\u2080 is spelled with the Greek mu, '
                                 'U+03BC, as HP\'s list spells it, and the '
                                 'calculator refuses that name: write it with '
                                 'the micro sign, U+00B5'))

        # ---- a character the font draws as an empty box -------------------
        found += _box_glyphs(path, num, code[k])

        # ---- drawing in units, with numbers that are pixels ----------------
        for m in re.finditer(NOT_NAME + r'(LINE|RECT|TEXTOUT|ARC|PIXON|PIXOFF|'
                             r'GETPIX|INVERT|DIMGROB)\s*\(', raw):
            args = _call_args(raw, m.end() - 1)
            if args is None:
                continue
            for text, limit in _unit_args(m.group(1), _split_top_level(args)):
                if re.match(r'^-?\d+(\.\d+)?$', text) and \
                        abs(float(text)) > limit:
                    found.append(Finding(
                        path, num, 'WARN', 'draw-units',
                        '%s counts the plot window\'s units, from the middle '
                        'of the screen, not pixels: %s is beyond what a reset '
                        'calculator shows, ten pixels to the unit. For '
                        'pixels, %s_P' % (m.group(1), text, m.group(1))))
                    break

        # ---- a single = as a statement ------------------------------------
        # `a = 2;` compiles and assigns nothing: it compares and throws the
        # answer away (emulator, 2026-09-24). Inside a condition a single =
        # compares, and that is fine; a line that starts with a keyword is
        # not this case.
        m = re.match(r'^([A-Za-z_]\w*)(\s*\([^()]*\))?\s*=(?![=>])', s)
        if m and m.group(1).upper() not in KEYWORDS:
            found.append(Finding(path, num, 'WARN', 'equality-statement',
                                 '%s = ... as a statement compares and '
                                 'throws the answer away: nothing is '
                                 'assigned, and no error is raised. Assign '
                                 'with :=' % m.group(1)))

        # ---- indexing the result of a call --------------------------------
        # What was measured is a call: SIZE(M)(1) does not compile. A
        # variable indexed twice, L(2)(1), is a nested list and another
        # thing, which the interpreter runs. So the rule has to know which
        # the name is, and says so when the file does not tell it.
        for m in re.finditer(NOT_NAME + r'(%s)\s*\([^()]*\)\s*\(' % NAME, raw):
            name = m.group(1)
            if name.upper() in KEYWORDS:
                continue
            kind = name_kind(name, functions, variables)
            if kind == 'function':
                found.append(Finding(path, num, 'ERROR', 'index-call',
                                     'cannot index the result of a call '
                                     '(%s(...)(...)): store it first, '
                                     'd := DIM(M); d(1)' % name))
            elif not kind:
                found.append(Finding(path, num, 'WARN', 'index-call',
                                     '%s(...)(...): if %s is a function -- '
                                     'this file\'s or another program\'s -- '
                                     'its result cannot be indexed here, so '
                                     'store it first; if it is a list, this '
                                     'is nested indexing. This file does not '
                                     'say which' % (name, name), EMULATOR))

        # ---- index 0 into a list or matrix --------------------------------
        # A 0 passed to a function is an argument, not an index: to one of
        # the calculator's own names (RGB(0, ...)), which come from the list,
        # or to one this file defines. That is also why the name has to be
        # read with the arrow in it (NAME): a screen point is counted from 0,
        # and C→PX(0,0) is correct code.
        #
        # What was measured to fail is MID("abcdef", 0, 2), a 0 where a
        # position was expected (ppl.one-based). A list read at 0 does not
        # fail: it answers its last element, and assigning to it appends;
        # a matrix read at 0 fails (emulator, 2026-09-24). So on a list the
        # code runs and the hazard is a Python habit getting the last element
        # for the first: a warning, known from the emulator.
        for m in re.finditer(NOT_NAME + r'(%s)\s*\(\s*0\s*[,)]' % NAME, raw):
            name = m.group(1)
            if name.upper() not in KEYWORDS and name not in functions \
                    and name.lower() not in known_names():
                found.append(Finding(path, num, 'WARN', 'one-based',
                                     'index 0 into %s: positions count from '
                                     '1. A list read at 0 answers its LAST '
                                     'element and one assigned at 0 grows by '
                                     'one; a matrix read at 0 is an error'
                                     % name, EMULATOR))

        # ---- LOCAL: how many variables --------------------------------------
        if re.match(r'^LOCAL\b', up):
            body = s[5:].split(';')[0]
            nv = len(_split_top_level(body))
            if nv >= LOCAL_FAILS:
                found.append(Finding(path, num, 'ERROR', 'local-limit',
                                     '%d variables in one LOCAL; %d and more '
                                     'do not compile, and %d does. Split it '
                                     'into several LOCAL statements'
                                     % (nv, LOCAL_FAILS, LOCAL_MAX)))
            # 7 and 8 were a warning here until 8 answered on a G2: a warning
            # on code that compiles only teaches a habit.
            # A rule called `local-first` used to sit here, calling a LOCAL
            # after other statements an error. It rested on one compile error
            # recorded without its program, and on 2026-11-05 a G2 compiled
            # and answered every form of it (ppl.locals-at-top). What does not
            # compile is reading a nested LOCAL after its block: local-scope.

        # ---- EXPORT with too many variables --------------------------------
        if re.match(r'^EXPORT\b', up) and '(' not in s.split(':=')[0]:
            chunks = _split_top_level(s[6:].split(';')[0])
            valued = [t for t in chunks if ':=' in t]
            if len(chunks) >= EXPORT_FAILS:
                said = ('%d variables in one EXPORT; %d and more do not compile, '
                        'with initial values or with none, and %d does. Split it '
                        'into several EXPORT statements'
                        % (len(chunks), EXPORT_FAILS, EXPORT_MAX))
                if len(valued) in (0, len(chunks)):
                    found.append(Finding(path, num, 'ERROR', 'export-limit', said))
                else:
                    found.append(Finding(path, num, 'WARN', 'export-limit',
                                         said + '. Some with values and some '
                                         'without has not been tried',
                                         UNVERIFIED))

        # ---- EXPORT of one of the calculator's own variables ----------------
        # A function called like one is another matter, and compiles: F(), F(x)
        # and a private F() answered on a G2 on 2026-11-05. With no arguments it
        # has a trap of its own, which is below: on Home, F is the variable.
        m = re.match(r'^EXPORT\s+(\S+?)\s*\(\s*\)', s, re.I)
        if m and CALC_VARIABLE.match(m.group(1)):
            found.append(Finding(path, num, 'WARN', 'export-home-variable',
                                 '%s is one of the calculator\'s own variables. '
                                 'A function of that name compiles and answers in '
                                 'a program, but typed on Home F answered the '
                                 'variable and not the function. Prefix it'
                                 % m.group(1),
                                 None if m.group(1) == 'F' else UNVERIFIED))
        if re.match(r'^EXPORT\b', up):
            for part in _split_top_level(s[6:].split(';')[0]):
                pm = re.match(r'^([^\s:=(]+)\s*(:=|$)', part)
                if not pm or not CALC_VARIABLE.match(pm.group(1)):
                    continue
                if pm.group(1) in EXPORT_REFUSED:
                    found.append(Finding(path, num, 'ERROR',
                                         'export-home-variable',
                                         '%s is one of Home\'s variables, and '
                                         'exporting it does not compile. '
                                         'Prefix it' % pm.group(1)))
                else:
                    found.append(Finding(path, num, 'WARN',
                                         'export-home-variable',
                                         '%s is one of the calculator\'s own '
                                         'variables. Exporting A, Y or Z does '
                                         'not compile, and this one has not been '
                                         'tried. Prefix it' % pm.group(1),
                                         UNVERIFIED))

        # ---- exported names, to cross-check between files -----------------
        m = re.match(r'^EXPORT\s+([A-Za-z_]\w*)', s, re.I)
        if m:
            exports.append((m.group(1), num))
            # One of HP's names, exported: a program exporting AREA compiled,
            # and AREA(2) on Home then answered the program's, hiding the
            # Function app's (emulator, 2026-09-24). CAS names were not tried;
            # an app's hooks are exported on purpose.
            kinds = _listed_kinds().get(m.group(1).lower(), set())
            if kinds - set(['cas']) and m.group(1).upper() not in HOOKS:
                found.append(Finding(path, num, 'WARN', 'export-clash',
                                     '%s is one of HP\'s names: exporting it '
                                     'hides the calculator\'s own for as long '
                                     'as this program is installed, and '
                                     'nothing says so. Prefix it'
                                     % m.group(1), EMULATOR))

        # A rule called `equality` used to sit here, flagging a single = in
        # an IF, WHILE or UNTIL condition as an error. It was measured on
        # 2026-09-12 and it was wrong: IF a = 2 THEN compiles and compares,
        # exactly as == does, on the Virtual Calculator 2.4 build 2025-09-15
        # (ppl.equality-operators). A linter that flags legal, correct code
        # is worse than one rule short, so it went. What nobody has measured
        # is a bare = as a STATEMENT -- a = 2; where a := 2; was meant -- and
        # a rule for that has to wait for the measurement, not the other way
        # round.

        # ---- EXPR on a variable without checking it is not empty ----------
        for m in re.finditer(r'\bEXPR\s*\(\s*([A-Za-z_]\w*)\s*\)', raw, re.I):
            window = ' '.join(clean[max(0, k - 6):k]).upper()
            if 'SIZE(%s)' % m.group(1).upper() not in window.replace(' ', ''):
                found.append(Finding(path, num, 'WARN', 'expr-empty',
                                     'EXPR(%s) without checking SIZE(%s) > 0 '
                                     'first: EXPR("") fails at run time'
                                     % (m.group(1), m.group(1))))

        # ---- TEXTOUT_P without its width argument -------------------------
        # The trap it guards: text that does not fit raises no error. It is
        # painted over the next column and you never learn what it said.
        #
        # Both forms are judged. Measured on a G2, drawing one long string
        # three times: with no width it runs off the screen, and these two
        # clip it identically --
        #     TEXTOUT_P(txt, x, y, font, colour, width)        6 arguments
        #     TEXTOUT_P(txt, G0, x, y, font, colour, width)    7 arguments
        # so the width is the last argument of whichever form is in use.
        for m in re.finditer(r'\bTEXTOUT_P\s*\(', raw, re.I):
            args = _call_args(raw, m.end() - 1)
            if args is None:
                continue
            parts = _split_top_level(args)
            grob = len(parts) > 1 and re.match(r'^G\d$', parts[1].strip(),
                                               re.I)
            if len(parts) < (7 if grob else 6):
                found.append(Finding(path, num, 'WARN', 'textout-width',
                                     'TEXTOUT_P without its width argument: '
                                     'text that does not fit is painted over '
                                     'the next column, and raises no error'))

        # ---- block balance -------------------------------------------------
        was_in_body = in_body
        if re.match(r'^BEGIN\b', up):
            in_body = True
        depth += _block_delta(up)
        if in_body and depth <= 0:
            in_body = False
        # END without its semicolon, a block's or a function's own: neither
        # compiles, the function's measured at the end of the file and with
        # another function after it (emulator, 2026-09-24).
        if re.match(r'^END\s*$', s) and was_in_body and not in_body:
            found.append(Finding(path, num, 'ERROR', 'end-semicolon',
                                 'END without ; closing a function: in PPL '
                                 'it is END;, and without it the program '
                                 'does not compile'))
        elif re.match(r'^END\s*$', s):
            found.append(Finding(path, num, 'ERROR', 'end-semicolon',
                                 'END without ; at the end: in PPL it is '
                                 'END;'))

    found += _function_findings(path, clean, functions, calls)
    found += _local_scope_findings(path, text, functions)
    found += [Finding(path, n, 'WARN', 'expr-in-loop',
                      'EXPR inside a loop resolves a name on every pass: '
                      'resolve it once, before the loop')
              for n in _exprs_in_loops(clean)]

    if depth != 0:
        found.append(Finding(path, len(lines), 'ERROR', 'unbalanced',
                             'unclosed blocks: %d openings too many '
                             '(BEGIN/THEN/DO/CASE against END)' % depth))

    # ---- names that are neither PPL's nor this file's ----------------------
    # Only when the list is there to say what PPL's names are.
    if known_names():
        defined = functions | variables
        for name, num in calls:
            if not is_known(name, defined):
                found.append(Finding(path, num, 'WARN', 'unknown-name',
                                     '%s is not a PPL name, and this file '
                                     'does not define it. If another program '
                                     'exports it, lint them together with '
                                     '--set' % name))

    return found, exports


def _unit_args(name, parts):
    """-> [(argument, limit)]: the arguments of a drawing command without _P
    that are positions or sizes, read from HP's syntax for it. A form this
    cannot place gives nothing, rather than a guess."""
    def grob(p):
        return bool(re.match(r'^G\d$', p.strip(), re.I))
    if name == 'TEXTOUT':
        rest = parts[1:]
        rest = rest[1:] if rest and grob(rest[0]) else rest
        return [(p, UNITS_LIMIT) for p in rest[:2]]
    has_g = bool(parts) and grob(parts[0])
    rest = parts[1:] if has_g else parts
    if name in ('ARC', 'DIMGROB') and not has_g:
        return []
    if name == 'DIMGROB':
        return [(p, UNITS_SIZE_LIMIT) for p in rest[:2]]
    if name == 'ARC':
        return [(p, UNITS_LIMIT) for p in rest[:3]]
    if name in ('LINE', 'INVERT'):
        return [(p, UNITS_LIMIT) for p in rest[:4]]
    if name == 'RECT':
        return [(p, UNITS_LIMIT) for p in rest[:4 if len(rest) >= 4 else 2]]
    return [(p, UNITS_LIMIT) for p in rest[:2]]      # PIXON, PIXOFF, GETPIX


def _functions(clean):
    """-> [(name, exported, first line index, last line index)] for every
    function the file defines with a body. A forward declaration has none."""
    out, depth, cur, opened = [], 0, None, False
    for k, raw in enumerate(clean):
        s = raw.strip()
        if not s or s.startswith('#'):
            continue
        up = s.upper()
        if depth <= 0 and cur is None:
            m = re.match(r'^(EXPORT\s+)?([A-Za-z_]\w*)\s*\(([^()]*)\)', s,
                         re.I)
            if m and m.group(2).upper() not in KEYWORDS and \
                    not re.match(r'^[^;]*\)\s*;', s):
                cur, opened = [m.group(2), bool(m.group(1)), k], False
        depth += _block_delta(up)
        if cur is not None and re.search(r'\bBEGIN\b', up):
            opened = True
        if cur is not None and opened and depth <= 0:
            out.append((cur[0], cur[1], cur[2], k))
            cur = None
    return out


def _local_scope_findings(path, text, functions):
    """A LOCAL inside a block is gone when that block ends, and a function that
    uses it afterwards, reading or assigning, does not compile. A THEN and its
    ELSE are two blocks. All of it measured (ppl.local-block-scope).

    Lines are judged one at a time, so a LOCAL that does not start its line is
    left alone, and so is a name that means something else once the block has
    ended: a parameter, an outer LOCAL, this file's own global or function, or
    one of the calculator's names."""
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    clean = [_strip_noise(l) for l in _strip_block_comments(text).split('\n')]
    spans = _functions(clean)
    inside = set(k for f in spans for k in range(f[2], f[3] + 1))
    file_level = set(functions)
    for k, raw in enumerate(clean):
        if k not in inside:
            body = re.sub(r'^\s*EXPORT\s+', '', raw, flags=re.I).split(';')[0]
            for part in _split_top_level(body):
                pm = re.match(r'^([A-Za-z_]\w*)\s*(:=|$)', part)
                if pm:
                    file_level.add(pm.group(1))

    found = []
    for _, _, first, last in spans:
        header = re.match(r'^\s*(?:EXPORT\s+)?\w+\s*\(([^()]*)\)', clean[first],
                          re.I)
        params = set(_split_top_level(header.group(1))) if header else set()
        blocks, gone, pending_if = [], {}, 0    # each block: [kind, its LOCALs]

        def used(name, where, line):
            found.append(Finding(path, line, 'ERROR', 'local-scope',
                                 '%s was declared in a block that ended on line '
                                 '%d, and a LOCAL lasts until the end of its '
                                 'block. Used here, it does not compile. Declare '
                                 'it before the block' % (name, where)))

        def outlives(name):
            return not (name in params or name in file_level
                        or any(name in b[1] for b in blocks)
                        or CALC_VARIABLE.match(name)
                        or name.lower() in known_names())
        for k in range(first, last + 1):
            s = clean[k].strip()
            if not s:
                continue
            up = s.upper()
            declared = []
            if re.match(r'^LOCAL\b', up):
                for part in _split_top_level(s[5:].split(';')[0]):
                    pm = re.match(r'^([A-Za-z_]\w*)', part)
                    if pm:
                        declared.append(pm.group(1))
            for name in sorted(gone):
                if name in declared or not re.search(
                        NOT_NAME + re.escape(name) + r'(?![\w→])', s):
                    continue
                used(name, gone[name], k + 1)
                del gone[name]
            for name in declared:
                gone.pop(name, None)
                if blocks:
                    blocks[-1][1].append(name)
            ended = []
            for word in re.findall(r'\b(BEGIN|IFERR|IF|THEN|ELSE|DO|CASE|REPEAT|'
                                   r'UNTIL|END)\b', up):
                if word == 'IF':
                    pending_if += 1
                elif word == 'THEN':
                    if pending_if:
                        pending_if -= 1
                        blocks.append(['IF', []])
                    elif blocks:        # IFERR's own: what it tried has ended
                        ended += blocks[-1][1]
                        blocks[-1][1] = []
                elif word == 'ELSE':
                    if blocks and blocks[-1][0] == 'IF':
                        ended += blocks[-1][1]
                        blocks[-1][1] = []
                elif word == 'UNTIL':
                    if blocks:
                        finished = blocks.pop()[1]
                        ended += finished
                        # The condition is already outside the block.
                        after = re.search(r'\bUNTIL\b(.*)$', s, re.I).group(1)
                        for name in finished:
                            if outlives(name) and re.search(
                                    NOT_NAME + re.escape(name) + r'(?![\w→])',
                                    after):
                                used(name, k + 1, k + 1)
                elif word == 'END':
                    if blocks:
                        ended += blocks.pop()[1]
                else:
                    blocks.append([word, []])
            for name in ended:
                if outlives(name):
                    gone[name] = k + 1
    return found


def _key_loops(text):
    """-> [(offset, 'wait' or 'drain')]: the loops in `text` that read
    GETKEY until a key comes, or until none is left."""
    out = []
    getkey = r'GETKEY(\s*\(\s*\))?'
    for m in re.finditer(r'\bREPEAT\b(.*?)\bUNTIL\b([^;]*)', text,
                         re.I | re.S):
        body, cond = m.group(1), m.group(2)
        v = re.search(r'([A-Za-z_]\w*)\s*:=\s*' + getkey, body, re.I)
        names = [getkey] + ([re.escape(v.group(1))] if v else [])
        for n in names:
            if re.search(n + r'\s*(>=|\u2265)\s*0\b|' + n + r'\s*>\s*-\s*1\b|'
                         + n + r'\s*(<>|!=|\u2260)\s*-\s*1\b', cond, re.I):
                out.append((m.start(), 'wait'))
                break
            if re.search(n + r'\s*<\s*0\b|' + n + r'\s*(==|=)\s*-\s*1\b|'
                         + n + r'\s*(<=|\u2264)\s*-\s*1\b', cond, re.I):
                out.append((m.start(), 'drain'))
                break
    for m in re.finditer(r'\bWHILE\b([^;]*?)\bDO\b', text, re.I | re.S):
        cond = m.group(1)
        if re.search(getkey + r'\s*<\s*0\b|' + getkey + r'\s*(==|=)\s*-\s*1\b',
                     cond, re.I):
            out.append((m.start(), 'wait'))
        elif re.search(getkey + r'\s*(>=|\u2265)\s*0\b|' + getkey +
                       r'\s*(<>|!=|\u2260)\s*-\s*1\b', cond, re.I):
            out.append((m.start(), 'drain'))
    return sorted(out)


def _function_findings(path, clean, functions, calls):
    """The rules that have to read a whole function: what it draws and
    whether it waits, how it waits for a key, and what it compares a key's
    code or a string's element with."""
    found = []
    spans = _functions(clean)
    body = dict((f[0], '\n'.join(clean[f[2]:f[3] + 1])) for f in spans)
    called = dict((f[0], set(n for n, line in calls
                             if f[2] <= line - 1 <= f[3] and n != f[0]))
                  for f in spans)
    known = known_names()

    def closure(name, seen=None):
        """The file's own functions `name` reaches, itself included."""
        seen = set() if seen is None else seen
        if name in seen or name not in body:
            return seen
        seen.add(name)
        for n in called[name]:
            closure(n, seen)
        return seen

    def uses(names, words):
        return any(re.search(NOT_NAME + r'(%s)\b(?!_)' % '|'.join(words),
                             body[n]) for n in names)

    drains = set(n for n in body if any(k == 'drain'
                                        for _, k in _key_loops(body[n])))
    for name, exported, first, last in spans:
        text = body[name]
        reach = closure(name)
        strangers = set(c for n in reach for c in called[n]
                        if c not in body and c.lower() not in known)

        # ---- draws and returns, and nothing waits ---------------------------
        # Only a function Home can start by its name, one with no arguments:
        # an exported helper that draws for its caller returns to a program,
        # not to Home, and waiting there would be the caller's choice.
        header = re.match(r'^\s*(?:EXPORT\s+)?\w+\s*\(([^()]*)\)', clean[first])
        no_args = header is not None and not header.group(1).strip()
        if exported and no_args and name.upper() not in HOOKS and not strangers \
                and uses(reach, DRAWS) and not uses(reach, WAITS):
            found.append(Finding(path, first + 1, 'WARN', 'draw-then-return',
                                 '%s draws and returns without waiting: run '
                                 'from Home, the drawing is gone when it '
                                 'returns, and Home shows the value it '
                                 'answered. Wait for a key first' % name))

        # ---- waits for a key without draining the buffer --------------------
        loops = _key_loops(text)
        waits = [o for o, k in loops if k == 'wait']
        if waits:
            before = text[:waits[0]]
            drained = any(k == 'drain' and o < waits[0] for o, k in loops) or \
                any(re.search(NOT_NAME + re.escape(n) + r'\s*\(', before)
                    for n in drains)
            if not drained:
                found.append(Finding(path, first + 1 + before.count('\n'),
                                     'WARN', 'wait-undrained',
                                     'this loop waits for a key without '
                                     'draining the ones already pending: the '
                                     '[Enter] that started the program can '
                                     'end it at once. Read GETKEY until it '
                                     'answers -1 first'))

        # ---- a key's code compared with what it cannot be -------------------
        for v in set(re.findall(NOT_NAME + r'([A-Za-z_]\w*)\s*:=\s*GETKEY\b',
                                text)):
            values = re.findall(NOT_NAME + re.escape(v) + r'\s*:=\s*([^\s;]+)',
                                text)
            if any(not x.startswith('GETKEY') for x in values):
                continue
            for m in re.finditer(NOT_NAME + re.escape(v) +
                                 r'\s*(==|<>|!=|\u2260|=(?!=))\s*'
                                 r'(""|-?\d+(\.\d+)?)|(""|-?\d+(\.\d+)?)\s*'
                                 r'(==|<>|!=|\u2260|=(?!=))\s*' + re.escape(v) +
                                 r'(?![\w\u2192])', text):
                lit = m.group(2) or m.group(4)
                if lit == '""' or float(lit) != int(float(lit)) or \
                        not -1 <= float(lit) <= 50:
                    found.append(Finding(
                        path, first + 1 + text[:m.start()].count('\n'),
                        'WARN', 'getkey-code',
                        '%s holds what GETKEY answered, the position of a key '
                        'from 0 to 50, or -1 for none: it is never %s. '
                        '[Enter] is 30, not 13' % (v, 'text' if lit == '""'
                                                   else lit)))

        # ---- what WAIT(-1) answered compared with a key, TYPE unchecked -----
        wait = r'WAIT\s*\(\s*-\s*1\s*\)'
        compare = r'\s*(==|<>|!=|≠|<=|>=|≤|≥|<|>|=(?!=))\s*'
        held = set(re.findall(NOT_NAME + r'([A-Za-z_]\w*)\s*:=\s*' + wait,
                              text, re.I))
        for v in sorted(held) + [None]:
            if v and re.search(NOT_NAME + r'TYPE\s*\(\s*' + re.escape(v) +
                               r'\s*\)', text, re.I):
                continue
            what = re.escape(v) + r'(?![\w→(])' if v else wait
            m = re.search(NOT_NAME + what + compare + r'-?\d|' + NOT_NAME +
                          r'-?\d[\d.]*' + compare + NOT_NAME + what, text,
                          re.I)
            if m:
                found.append(Finding(
                    path, first + 1 + text[:m.start()].count('\n'), 'WARN',
                    'wait-touch',
                    '%s compared with a number, but a touch makes WAIT(-1) '
                    'answer a list, not a key code. Check TYPE first: only a '
                    'number is a key, a one-element list is the mouse-up, '
                    'and type 3 is the click'
                    % ('%s holds what WAIT(-1) answered and is' % v if v
                       else 'WAIT(-1) is')))

        # ---- a string's element compared with a string ----------------------
        assigned = re.findall(r'([A-Za-z_]\w*)\s*:=\s*(\S)', text)
        texts = set(v for v, c in assigned if c == '"') - \
            set(v for v, c in assigned if c != '"')
        for v in texts:
            for m in re.finditer(NOT_NAME + re.escape(v) +
                                 r'\s*\([^()]*\)\s*(==|<>|!=|\u2260|=(?!=))'
                                 r'\s*""|""\s*(==|<>|!=|\u2260|=(?!=))\s*' +
                                 re.escape(v) + r'\s*\(', text):
                found.append(Finding(
                    path, first + 1 + text[:m.start()].count('\n'), 'WARN',
                    'string-index',
                    '%s holds text, and %s(...) is the code of a character, '
                    'a number: compared with a string it is never equal. '
                    'MID(%s, i, 1) gives the character' % (v, v, v)))
    return found


def _exprs_in_loops(clean):
    """-> the line numbers of every EXPR inside a FOR, WHILE or REPEAT."""
    out, stack, loop_next = [], [], False
    for k, raw in enumerate(clean):
        for m in re.finditer(r'\b(FOR|WHILE|REPEAT|UNTIL|BEGIN|THEN|DO|CASE|'
                             r'END|EXPR)\b', raw.upper()):
            t = m.group(1)
            if t in ('FOR', 'WHILE'):
                loop_next = True
            elif t == 'DO':
                stack.append('loop' if loop_next else 'block')
                loop_next = False
            elif t in ('BEGIN', 'THEN', 'CASE'):
                stack.append('block')
            elif t == 'REPEAT':
                stack.append('loop')
            elif t in ('END', 'UNTIL') and stack:
                stack.pop()
            elif t == 'EXPR' and 'loop' in stack and \
                    (not out or out[-1] != k + 1):
                out.append(k + 1)
    return out


def lint_files(paths, as_set=False):
    """-> (the files read, every Finding), printing nothing."""
    files = []
    for p in paths:
        if os.path.isdir(p):
            for root, _, fs in os.walk(p):
                for f in sorted(fs):
                    if f.endswith(('.hpprgm', '.ppl', '.txt')):
                        files.append(os.path.join(root, f))
        else:
            files.append(p)

    everything, all_exports, texts = [], {}, []
    for f in files:
        try:
            txt = io.open(f, encoding='utf-8').read()
        except (IOError, UnicodeDecodeError) as e:
            print('%s: cannot read (%s)' % (f, e))
            continue
        found, exports = check_source(os.path.relpath(f), txt)
        if as_set:
            # With every file in view, a stranger is decided below, for the
            # whole set at once.
            found = [a for a in found if a.rule != 'unknown-name']
        everything.extend(found)
        texts.append((os.path.relpath(f), txt))
        for name, line in exports:
            all_exports.setdefault(name, []).append((os.path.relpath(f), line))

    # The same exported name in two files: they clash as globals. Only with
    # --set, because it is normal to keep variants of the same code that are
    # never installed together. --set is how you say "these do go together".
    for name, places in sorted(all_exports.items()) if as_set else []:
        others = set(s[0] for s in places)
        if len(others) > 1:
            f, l = places[0]
            # Not an error: on a G2 both compiled, and a call answered the one
            # that had been there longest (ppl.global-namespace). So a program
            # can stop answering what it says, with nothing to show for it.
            everything.append(Finding(f, l, 'WARN', 'export-clash',
                                      '%s is also exported by %s: both compile, '
                                      'and a call answers the one that has been '
                                      'on the calculator longest, with nothing '
                                      'to say so. Prefix them'
                                      % (name,
                                         ', '.join(sorted(others - {f})))))

    # A call none of the files defines, and that is not a PPL name: with the
    # whole set in view, nothing else could supply it.
    if as_set and known_names():
        scans = [(f, scan_names(t)) for f, t in texts]
        defined = set()
        for _, (d, _) in scans:
            defined |= d
        for f, (_, calls) in scans:
            for name, line in calls:
                if not is_known(name, defined):
                    everything.append(Finding(f, line, 'ERROR',
                                              'unknown-name',
                                              '%s is not a PPL name, and none '
                                              'of these files defines it'
                                              % name))

    return files, everything


def check_files(paths, quiet=False, as_set=False):
    """Lint, print compiler-shaped findings, and -> 1 if any is an error."""
    files, everything = lint_files(paths, as_set)
    errors = [a for a in everything if a.level == 'ERROR']
    warnings = [a for a in everything if a.level != 'ERROR']
    for a in sorted(everything, key=lambda a: (a.path, a.line)):
        if quiet and a.level != 'ERROR':
            continue
        print(str(a))
    print('\n%d file(s): %d error(s), %d warning(s)'
          % (len(files), len(errors), len(warnings)))
    # In a Claude Code session with the kit's settings, note what passed:
    # the end of the turn is checked against it (hpkit/gates.py).
    from hpkit import gates
    if gates.enabled():
        failed = set(a.path for a in errors)
        for f in files:
            gates.record(f, 'lint', os.path.relpath(f) not in failed
                         and _decodes(f))
    return 1 if errors else 0


def _decodes(path):
    """Whether lint could read the file at all: one it could not is not
    one it passed."""
    try:
        io.open(path, encoding='utf-8').read()
        return True
    except (IOError, OSError, UnicodeDecodeError):
        return False


def cli(argv):
    args = [a for a in argv if not a.startswith('--')]
    if not args:
        print(__doc__)
        return 2
    return check_files(args, quiet='--quiet' in argv, as_set='--set' in argv)


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
