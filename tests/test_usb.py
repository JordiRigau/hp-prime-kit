# -*- coding: utf-8 -*-
"""Tests for the G2 on its USB cable, with no calculator.

    python tests/test_usb.py

Nothing here opens a device. A script of reports stands in for the calculator,
shaped like what one was measured to send, and what is held is the bytes that
go out and what is made of the bytes that come back. Whether a calculator still
behaves like that is for the calculator to say: docs/topics/usb.md.
"""
from __future__ import unicode_literals
import io, os, re, shutil, struct, sys, tempfile, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import cli, usb

PASS, FAIL = [0], [0]


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
        sys.stdout = io.StringIO()
        return self

    def __exit__(self, *exc):
        self.text = sys.stdout.getvalue()
        sys.stdout = self.old
        return False


class Script(object):
    """The calculator's side: what it has to say, and what it was sent."""

    def __init__(self, *reports):
        self.reports = list(reports)
        self.sent = []
        self.closed = False

    def write(self, frame):
        self.sent.append(frame)

    def read(self, timeout_ms):
        return self.reports.pop(0) if self.reports else None

    def close(self):
        self.closed = True


def report(*frame):
    """One report as Windows hands it over: the report number, 1024 bytes."""
    return (b'\x00' + b''.join(frame)).ljust(1025, b'\x00')


def reply(command, data, extra=b''):
    """A whole reply in the framing measured: 1023 bytes to a report, less the
    header on the first. `extra` is what follows the data in the last report,
    which on the calculator is leftovers rather than zeros."""
    head = bytes(bytearray([0x00, command, 0x03])) + struct.pack('>I', len(data))
    room, out, n = 1024 - len(head), [], 1
    out.append(report(head, data[:room], extra if len(data) <= room else b''))
    data = data[room:]
    while data:
        last = len(data) <= 1023
        out.append(report(bytes(bytearray([n])), data[:1023],
                          extra if last else b''))
        data, n = data[1023:], n + 1
    return out


def information(build=15515, version=b'V2.060.650', serial=b'SERIALNUMB'):
    return (b'\x00' * 72 + struct.pack('<H', build) + b'\x00\x00'
            + version.ljust(16, b'\x00') + serial.ljust(16, b'\x00'))


def grey_png(width, values, filters=None):
    """A PNG of 16-bit greys, values given as (high byte, low byte) the way
    they lie in the file, each row under the filter asked for."""
    def chunk(kind, body):
        return (struct.pack('>I', len(body)) + kind + body
                + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF))
    height = len(values) // width
    raw, previous = bytearray(), bytearray(width * 2)
    for y in range(height):
        row = bytearray()
        for high, low in values[y * width:(y + 1) * width]:
            row += bytearray([high, low])
        kind = filters[y] if filters else 0
        filtered = bytearray(len(row))
        for i in range(len(row)):
            a = row[i - 2] if i >= 2 else 0
            b = previous[i]
            c = previous[i - 2] if i >= 2 else 0
            if kind == 0:
                guess = 0
            elif kind == 1:
                guess = a
            elif kind == 2:
                guess = b
            elif kind == 3:
                guess = (a + b) // 2
            else:
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                guess = a if pa <= pb and pa <= pc else b if pb <= pc else c
            filtered[i] = (row[i] - guess) & 255
        raw += bytearray([kind]) + filtered
        previous = row
    return (usb.PNG
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 16, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(bytes(raw)))
            + chunk(b'IEND', b''))


WHITE, BLUE, BLACK = (0xFF, 0x7F), (0x53, 0x11), (0x00, 0x00)


def keys():
    print('the names of the keys')
    ok(usb.key_code('up') == 2 and usb.key_code('down') == 12,
       'the arrows are named')
    ok(usb.key_code('enter') == 30 and usb.key_code('ENTER') == 30,
       'a name in any case')
    # The trap: 2 is what a person means by the key marked 2, and it is not
    # code 2, which is the up arrow.
    ok(usb.key_code('2') == 43, 'a digit is the key marked with it, not a code')
    ok(usb.key_code('code:2') == 2, 'code:N takes a key by its number')
    ok(usb.key_code('+') == 50 and usb.key_code('add') == 50,
       '+ and add are the same key')
    ok(usb.key_code('*') == 40 and usb.key_code('mul') == 40,
       '* and mul are the same key')
    for bad in ('nonsense', 'code:51', 'code:', 'code:-1', '43'):
        try:
            usb.key_code(bad)
            ok(False, '%s is refused' % bad)
        except usb.UsbError:
            ok(True, '%s is refused' % bad)
    ok(sorted(usb.KEYS.values()) == list(range(51)),
       'all 51 codes, each with one name')


# Names for the marks in the table of interface.key-codes that are not words.
DOC_NAMES = {'▲': 'up', '◄': 'left', '►': 'right', '▼': 'down',
             'x t θ n': 'xttn', 'a b/c': 'frac', 'x^y': 'pow', 'x²': 'sq',
             '+/-': 'neg', '( )': 'parens', '÷': 'div', '×': 'mul',
             '−': 'sub', '+': 'add'}


def keys_against_the_documentation():
    print('the table of keys against interface.key-codes')
    text = io.open(os.path.join(ROOT, 'docs', 'topics', 'interface.md'),
                   encoding='utf-8').read()
    fact = text.split('<a name="interface.key-codes"></a>')[1].split('**Evidence.**')[0]
    table = {}
    for line in fact.splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) != 2:
            continue
        for item in cells[1].split(','):
            m = re.match(r'^(.+?) (\d+)$', item.strip())
            if m:
                table[m.group(1).strip('`')] = int(m.group(2))
    ok(len(table) == 51, 'the table in the documentation has 51 keys',
       str(len(table)))
    wrong = []
    for mark, code in table.items():
        name = DOC_NAMES.get(mark, mark.lower())
        if usb.KEYS.get(name) != code:
            wrong.append('%s is %s' % (mark, code))
    ok(not wrong, 'every key here has the code the documentation gives it',
       '; '.join(wrong))


def frames():
    print('what goes out')
    ok(usb.key_frame(2) == bytes(bytearray([0, 0xEC, 3, 0, 0, 0, 1, 2])),
       'a key in the old framing, one key long')
    ok(usb.RELEASE == b'\x01', 'the report that makes it act starts 01 and '
       'holds nothing else')
    link = Script(*reply(usb.CMD_SCREEN, b'xx\x08\xff\xff\xff\xff' + grey_png(1, [WHITE])))
    usb.read_screen(link)
    ok(link.sent == [bytes(bytearray([0, 0xFC, 8]))], 'the screen is asked for '
       'as 00 FC 08')


def replies():
    print('what comes back')
    data = bytes(bytearray(range(256))) * 12
    ok(usb.read_reply(Script(*reply(0xFC, data)), 0xFC) == data,
       'a reply across several reports comes back whole')
    ok(usb.read_reply(Script(*reply(0xFA, b'abc', extra=b'leftovers')), 0xFA) == b'abc',
       'the size ends a reply, not the zeros, since what follows is leftovers')
    control = report(b'\xfe\x01\xff\x00\xf7\x03\x00\x00\x01\x00\x00\x00')
    parts = reply(0xFC, data)
    mixed = [control, parts[0], control] + parts[1:]
    ok(usb.read_reply(Script(*mixed), 0xFC) == data,
       'a control frame before or inside a reply is skipped')
    other = reply(0xFA, b'other')
    ok(usb.read_reply(Script(*(other + reply(0xFC, b'mine'))), 0xFC) == b'mine',
       'a reply to something else is not taken for this one')
    for name, script, expect in (
            ('silence', [], 'did not answer'),
            ('a reply that stops', reply(0xFC, data)[:1], 'stopped after'),
            ('reports out of order',
             reply(0xFC, data)[:1] + reply(0xFC, data)[2:], 'out of order')):
        try:
            usb.read_reply(Script(*script), 0xFC, first=50, then=50)
            ok(False, '%s is an error' % name)
        except usb.UsbError as e:
            ok(expect in str(e), '%s is an error that says so' % name, str(e))

    class Heartbeats(Script):
        def read(self, timeout_ms):
            return control

    try:
        usb.read_reply(Heartbeats(), 0xFC, first=30)
        ok(False, 'control frames forever still run out of time')
    except usb.UsbError as e:
        ok('did not answer' in str(e),
           'control frames forever still run out of time', str(e))


def identify():
    print('asking who it is')
    link = Script(*reply(usb.CMD_INFORMATION, information()))
    build, version = usb.identify(link)
    ok(build == 15515, 'the build, counted from the end of the reply', str(build))
    ok(version == 'V2.060.650', 'the version, counted from the end too', version)
    ok(link.sent == [bytes(bytearray([0, 0xFA]))], 'asked as 00 FA')
    link = Script(*reply(usb.CMD_INFORMATION, b'short'))
    try:
        usb.identify(link)
        ok(False, 'too short an answer is an error')
    except usb.UsbError:
        ok(True, 'too short an answer is an error')


def pictures():
    print('the picture')
    values = [WHITE, BLUE, BLACK, WHITE, BLACK, BLUE,
              WHITE, WHITE, WHITE, BLUE, BLUE, BLUE,
              BLACK, WHITE, BLUE, BLACK, WHITE, BLUE,
              BLUE, BLACK, WHITE, BLUE, BLACK, WHITE,
              WHITE, BLACK, BLUE, WHITE, BLACK, BLUE]
    width, height, rows = usb.read_png(grey_png(6, values, filters=[0, 1, 2, 3, 4]))
    plain = usb.read_png(grey_png(6, values))
    ok((width, height) == (6, 5) and rows == plain[2],
       'all five PNG filters give the same rows as none')
    colours = usb.to_rgb(rows, width)
    first = bytearray(colours[0])
    ok(tuple(first[0:3]) == (255, 255, 255), 'white stored as FF7F is white',
       str(tuple(first[0:3])))
    ok(tuple(first[3:6]) == (32, 82, 156),
       'the title bar stored as 5311 is the blue it is on the calculator',
       str(tuple(first[3:6])))
    ok(tuple(first[6:9]) == (0, 0, 0), 'black is black')

    tmp = tempfile.mkdtemp(prefix='hpusb_')
    try:
        path = os.path.join(tmp, 'out.png')
        usb.write_png(path, width, height, colours)
        data = open(path, 'rb').read()
        ok(data[:8] == usb.PNG and data[24:26] == b'\x08\x02',
           'what is saved is an ordinary 8-bit RGB PNG')
        raw = zlib.decompress(data[data.index(b'IDAT') + 4:data.index(b'IEND') - 8])
        ok(raw == b''.join(b'\x00' + row for row in colours),
           'and holds those colours')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    good = grey_png(2, [WHITE, BLACK])
    for name, bad, expect in (
            ('something that is not a PNG', b'not a picture', 'not a PNG'),
            ('a damaged picture', good[:-30] + b'\x00' * 30, 'damaged'),
            ('a kind never seen', good[:24] + b'\x08' + good[25:], 'depth 8')):
        try:
            usb.read_png(bad)
            ok(False, '%s is an error' % name)
        except usb.UsbError as e:
            ok(expect in str(e), '%s is an error that says so' % name, str(e))
    try:
        usb.read_screen(Script(*reply(usb.CMD_SCREEN, b'no picture here')))
        ok(False, 'a reply with no picture is an error')
    except usb.UsbError:
        ok(True, 'a reply with no picture is an error')


def commands():
    print('the commands')
    real_connect, real_gap = usb.connect, usb.GAP
    usb.GAP = 0
    tmp = tempfile.mkdtemp(prefix='hpusb_')
    here = os.getcwd()
    try:
        os.chdir(tmp)
        png = grey_png(2, [WHITE, BLUE, BLUE, WHITE])
        link = Script(*(reply(usb.CMD_INFORMATION, information())
                        + reply(usb.CMD_SCREEN, b'xx\x08\xff\xff\xff\xff' + png)))
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['screen', '-o', 'now.png'])
        ok(rc == 0 and os.path.isfile('now.png'), 'screen saves the picture',
           q.text)
        ok('now.png: 2x2' in q.text, 'and says what it saved', q.text)
        ok(link.closed, 'and lets go of the calculator')

        link = Script(*(reply(usb.CMD_INFORMATION, information())
                        + reply(usb.CMD_SCREEN, b'xx\x08\xff\xff\xff\xff' + png)))
        with quiet():
            rc = cli.main(['screen'])
        ok(rc == 0 and os.path.isfile('screen.png'),
           'screen with no -o saves screen.png')

        with quiet():
            rc = cli.main(['screen', '-o'])
        ok(rc == 2, 'screen -o with no name is a usage error')
        with quiet():
            rc = cli.main(['screen', 'stray'])
        ok(rc == 2, 'screen with a stray argument is a usage error')

        link = Script(*reply(usb.CMD_INFORMATION, information()))
        with quiet() as q:
            rc = cli.main(['press', '2', '+', '2', 'enter'])
        key = usb.key_frame
        ok(rc == 0 and link.sent[1:] == [key(43), usb.RELEASE, key(50), usb.RELEASE,
                                         key(43), usb.RELEASE, key(30), usb.RELEASE],
           'press sends each key and then the report that makes it act',
           repr(link.sent))
        ok('nothing acknowledges' in q.text,
           'and says that sending is all it knows', q.text)
        ok(link.closed, 'and lets go of the calculator')

        link = Script(*reply(usb.CMD_INFORMATION, information()))
        with quiet():
            rc = cli.main(['press', 'shift', 'alpha', '5'])
        ok(rc == 0 and link.sent[1:] == [key(41), usb.RELEASE, key(36), usb.RELEASE,
                                         key(38), usb.RELEASE],
           'a small letter goes as shift, alpha and the key that carries it',
           repr(link.sent))

        link = Script()
        with quiet() as q:
            rc = cli.main(['press', 'up', 'nonsense'])
        ok(rc == 2 and not link.sent,
           'a wrong name stops everything before the first key goes', q.text)

        with quiet():
            rc = cli.main(['press'])
        ok(rc == 2, 'press with no keys is a usage error')
        with quiet() as q:
            rc = cli.main(['press', '--list'])
        ok(rc == 0 and '43  2' in q.text and '30  enter' in q.text,
           'press --list names every key with its code', q.text[:40])

        link = Script()
        with quiet() as q:
            rc = cli.main(['press', 'up'])
        ok(rc == 1 and 'did not answer' in q.text and len(link.sent) == 1,
           'a calculator that does not answer is an error, and no key goes',
           q.text)

        link = Script(*reply(usb.CMD_INFORMATION, information(build=16000)))
        with quiet() as q:
            rc = cli.main(['press', 'up'])
        ok(rc == 0 and 'WARN' in q.text and '16000' in q.text,
           'a build nobody measured is said out loud', q.text)

        def refused():
            raise usb.UsbError('the calculator is there, and another program '
                               'holds it')
        usb.connect = refused
        with quiet() as q:
            rc = cli.main(['screen'])
        ok(rc == 1 and 'another program' in q.text,
           'a calculator held by the Connectivity Kit is an error that says so',
           q.text)
        with quiet() as q:
            rc = cli.main(['press', 'up'])
        ok(rc == 1 and 'another program' in q.text,
           'for press too', q.text)

        for name in ('screen', 'press'):
            with quiet() as q:
                rc = cli.main([name, '--help'])
            ok(rc == 0 and 'Connectivity Kit' in q.text,
               '%s --help says the Kit has to be closed' % name)
        with quiet() as q:
            cli.main(['--help'])
        ok('screen' in q.text and 'press' in q.text,
           '--help lists both commands')
    finally:
        usb.connect, usb.GAP = real_connect, real_gap
        os.chdir(here)
        shutil.rmtree(tmp, ignore_errors=True)


def letters_against_the_documentation():
    print('the table of letters against usb.letters')
    text = io.open(os.path.join(ROOT, 'docs', 'topics', 'usb.md'), encoding='utf-8').read()
    fact = text.split('<a name="usb.letters"></a>')[1].split('**Evidence.**')[0]
    table = {}
    for line in fact.splitlines():
        m = re.match(r'^\| ([A-Z]) \| `?(.+?)`? \| (\d+) \|$', line.strip())
        if m:
            table[m.group(1)] = int(m.group(3))
    ok(sorted(table) == [chr(c) for c in range(65, 91)],
       'the documentation has all 26 letters', ''.join(sorted(table)))
    wrong = ['%s is %d' % (letter, code) for letter, code in table.items()
             if usb.KEYS[usb.LETTER_KEYS[ord(letter) - 65]] != code]
    ok(not wrong, 'every letter here is on the key the documentation gives it',
       '; '.join(wrong))


def typing():
    print('what typing presses')
    k = usb.keys_for_text
    ok(k('S') == ['alpha', '9'], 'a capital is Alpha and the key that carries it')
    ok(k('v') == ['shift', 'alpha', '5'], 'a small letter is Shift, Alpha and the key')
    ok(k('ABC') == ['alpha', 'vars', 'alpha', 'mem', 'alpha', 'units'],
       'three capitals go one by one, since holding Alpha saves nothing')
    ok(k('SELF') == ['alpha', 'alpha', '9', 'frac', 'sq', 'pow', 'alpha'],
       'four capitals hold Alpha, and let go of it')
    ok(k('ab') == ['shift', 'alpha', 'vars', 'shift', 'alpha', 'mem'],
       'two small letters go one by one')
    ok(k('abc') == ['shift', 'alpha', 'alpha', 'vars', 'mem', 'units', 'alpha'],
       'three small letters hold Alpha, with the sequence that gives small ones')
    ok(k('SELF4') == ['alpha', 'alpha', '9', 'frac', 'sq', 'pow', 'alpha', '4'],
       'a digit comes after letting go, or it would be a letter')
    ok(k('Gallery') == ['alpha', 'sin', 'shift', 'alpha', 'alpha', 'vars', 'sq', 'sq',
                        'frac', '8', '1', 'alpha'],
       'a capital and then small letters')
    ok(k('A1b') == ['alpha', 'vars', '1', 'shift', 'alpha', 'mem'],
       'letters and digits in turn')
    ok(k('1234567890') == list('1234567890'), 'digits are their own keys')
    ok(k('') == [], 'nothing is no keys')
    ok(all(name in usb.KEYS for name in k('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')),
       'every key it names exists')
    # %a and ascii(), not %r: run_all reads a suite through a pipe, which on a
    # stock Windows is cp1252, and printing the last of these raises there.
    for bad in ('F(2)', 'A B', 'x+1', 'café', 'A_B', '٣'):
        try:
            k(bad)
            ok(False, '%a is refused' % bad)
        except usb.UsbError as e:
            ok('press' in str(e), '%a is refused, and says what can do it' % bad,
               ascii(str(e)))


def typing_command():
    print('the type command')
    real_connect, real_gap = usb.connect, usb.GAP
    usb.GAP = 0
    try:
        key = usb.key_frame
        link = Script(*reply(usb.CMD_INFORMATION, information()))
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['type', 'S4'])
        ok(rc == 0 and link.sent[1:] == [key(36), usb.RELEASE, key(34), usb.RELEASE,
                                         key(37), usb.RELEASE],
           'type sends each key and then the report that makes it act',
           repr(link.sent))
        ok('nothing acknowledges' in q.text and '3 key(s)' in q.text,
           'and says what it sent, and that sending is all it knows', q.text)
        ok(link.closed, 'and lets go of the calculator')

        link = Script(*reply(usb.CMD_INFORMATION, information()))
        with quiet():
            rc = cli.main(['type', 'A', '--enter'])
        ok(rc == 0 and link.sent[1:] == [key(36), usb.RELEASE, key(14), usb.RELEASE,
                                         key(30), usb.RELEASE],
           '--enter presses Enter afterwards', repr(link.sent))

        def forbidden():
            raise AssertionError('the calculator was touched')
        usb.connect = forbidden
        with quiet() as q:
            rc = cli.main(['type', 'F(2)'])
        ok(rc == 2 and 'cannot be typed' in q.text,
           'what cannot be typed stops before the calculator is touched', q.text)
        with quiet():
            rc = cli.main(['type'])
        ok(rc == 2, 'type with no text is a usage error')
        with quiet():
            rc = cli.main(['type', 'A', 'B'])
        ok(rc == 2, 'type with two texts is a usage error')
        with quiet():
            rc = cli.main(['type', ''])
        ok(rc == 2, 'type with an empty text and no --enter is a usage error')

        link = Script()
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['type', 'A'])
        ok(rc == 1 and 'did not answer' in q.text and len(link.sent) == 1,
           'a calculator that does not answer gets no keys', q.text)

        link = Script(*reply(usb.CMD_INFORMATION, information(build=16000)))
        with quiet() as q:
            rc = cli.main(['type', 'A'])
        ok(rc == 0 and 'WARN' in q.text, 'a build nobody measured is said out loud', q.text)

        def refused():
            raise usb.UsbError('the calculator is there, and another program '
                               'holds it')
        usb.connect = refused
        with quiet() as q:
            rc = cli.main(['type', 'A'])
        ok(rc == 1 and 'another program' in q.text,
           'a calculator held by the Connectivity Kit is an error for type too', q.text)

        with quiet() as q:
            rc = cli.main(['type', '--help'])
        ok(rc == 0 and 'Connectivity Kit' in q.text and 'selection' in q.text,
           'type --help says the Kit has to be closed, and to look first')
        with quiet() as q:
            cli.main(['--help'])
        ok('type TEXT' in q.text, '--help lists it')
    finally:
        usb.connect, usb.GAP = real_connect, real_gap


SMALL = 'EXPORT ZSENT()\nBEGIN\n  RETURN 7;\nEND;'


def sent_inner(message):
    """What a program message holds, uncompressed."""
    return zlib.decompress(message[10:])


def messages():
    print('the message that installs a program')
    ok(usb.checksum(b'123456789') == 0x31C3,
       'the checksum is CRC-16, polynomial 1021, from 0: its check value')
    # The only proof that does not rest on this file's own idea of the format:
    # these are what the calculator itself sent for this very program.
    source = usb.read_source(os.path.join(ROOT, 'examples', 'selftest', 'SELFTEST.txt'))
    inner = sent_inner(usb.program_message('SELFTEST', source))
    ok(len(inner) == 2304, 'SELFTEST is the 2304 bytes the G2 sent for it', str(len(inner)))
    ok(inner[:4] == b'\x06\x10\x98\xd2',
       'with the checksum the G2 itself put on SELFTEST', repr(inner[:4]))
    ok(inner[4:20] == 'SELFTEST'.encode('utf-16-le'), 'then the name, in UTF-16')
    ok(inner[20:24] == '//'.encode('utf-16-le') and inner[-4:] == ';\x00'.encode('utf-16-le'),
       'then the source and its terminator, with no container', repr(inner[-4:]))

    message = usb.program_message('ZSENT', SMALL)
    stream = message[10:]
    ok(message[:2] == b'\xf7\x03', 'it starts F7 03')
    ok(struct.unpack('>I', message[2:6])[0] == len(stream) + 4,
       'then the length of the stream plus 4, high byte first')
    ok(struct.unpack('<I', message[6:10])[0] == len(sent_inner(message)),
       'then the uncompressed length, low byte first')

    tmp = tempfile.mkdtemp(prefix='hpusb_')
    try:
        built = os.path.join(tmp, 'ZSENT.hpprgm')
        from hpkit import program
        template = open(program.default_template(), 'rb').read()
        with open(built, 'wb') as f:
            f.write(program.write(template, SMALL))
        ok(usb.read_source(built) == SMALL,
           'a built .hpprgm gives up the source that was put in it')
        text = os.path.join(tmp, 'ZSENT.txt')
        with io.open(text, 'w', encoding='utf-8', newline='\r\n') as f:
            f.write(SMALL + '\n')
        ok(usb.read_source(text) == SMALL,
           'source from a file loses CRLF and the last newline, as write does')
        for path, what in ((os.path.join(tmp, 'absent.txt'), 'a file that is not there'),
                           (text.replace('.txt', '.hpprgm.bad'), 'another file that is not there')):
            try:
                usb.read_source(path)
                ok(False, '%s is an error' % what)
            except usb.UsbError:
                ok(True, '%s is an error' % what)
        bad = os.path.join(tmp, 'bad.hpprgm')
        with open(bad, 'wb') as f:
            f.write(b'not a program')
        try:
            usb.read_source(bad)
            ok(False, 'a .hpprgm that is not one is an error')
        except usb.UsbError:
            ok(True, 'a .hpprgm that is not one is an error')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    one = usb.to_reports(b'x' * 1023)
    ok(len(one) == 1 and one[0][:1] == b'\x00' and len(one[0]) == 1024,
       '1023 bytes fit one report, after its sequence number')
    data = bytes(bytearray(range(256))) * 12
    many = usb.to_reports(data)
    ok([r[0] for r in map(bytearray, many)] == list(range(len(many))),
       'longer messages number their reports from 0')
    ok(b''.join(r[1:] for r in many) == data, 'and come back whole')
    ok(len(usb.to_reports(b'x' * (1023 * usb.MAX_REPORTS))) == usb.MAX_REPORTS,
       'as many reports as sequence numbers before the control frames')
    try:
        usb.to_reports(b'x' * (1023 * usb.MAX_REPORTS + 1))
        ok(False, 'one more report than that is refused')
    except usb.UsbError:
        ok(True, 'one more report than that is refused')


def sending():
    print('the send command')
    real_connect, real_gap = usb.connect, usb.GAP
    usb.GAP = 0
    tmp = tempfile.mkdtemp(prefix='hpusb_')
    here = os.getcwd()
    try:
        os.chdir(tmp)
        with io.open('ZSENT.txt', 'w', encoding='utf-8') as f:
            f.write(SMALL)
        calculator = reply(usb.CMD_INFORMATION, information())

        link = Script(*calculator)
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['send', 'ZSENT.txt'])
        wanted = [bytes(bytearray([0, 0xFA]))] + usb.to_reports(usb.program_message('ZSENT', SMALL)) + [usb.RELEASE]
        ok(rc == 0 and link.sent == wanted,
           'send sends the reports and then the report that lets them act',
           repr(link.sent))
        ok('nothing acknowledges' in q.text,
           'and says that sending is all it knows', q.text)
        ok('exports: ZSENT' in q.text, 'and what to type to find out', q.text)
        ok(link.closed, 'and lets go of the calculator')

        link = Script(*calculator)
        with quiet():
            rc = cli.main(['send', 'ZSENT.txt', '--name', 'OTHER'])
        ok(rc == 0 and link.sent[1:-1] == usb.to_reports(usb.program_message('OTHER', SMALL)),
           '--name says what it is called on the calculator')

        from hpkit import program
        with open('ZBUILT.hpprgm', 'wb') as f:
            f.write(program.write(open(program.default_template(), 'rb').read(), SMALL))
        link = Script(*calculator)
        with quiet():
            rc = cli.main(['send', 'ZBUILT.hpprgm'])
        ok(rc == 0 and link.sent[1:-1] == usb.to_reports(usb.program_message('ZBUILT', SMALL)),
           'a .hpprgm goes as its source, under its own name')

        with io.open('ZBROKEN.txt', 'w', encoding='utf-8') as f:
            f.write('EXPORT ZB()\nBEGIN\n  IF 1 THEN\n    RETURN 1;\n  ENDIF;\nEND;')

        def forbidden():
            raise AssertionError('the calculator was touched')
        usb.connect = forbidden
        with quiet() as q:
            rc = cli.main(['send', 'ZBROKEN.txt'])
        ok(rc == 1 and 'single-end' in q.text and 'not sent' in q.text,
           'a program with linter errors stops before the calculator is touched',
           q.text)
        ok('--no-lint' in q.text, 'and says how to ask the calculator itself', q.text)
        with quiet() as q:
            rc = cli.main(['send', 'absent.txt'])
        ok(rc == 1 and 'cannot read' in q.text,
           'a file that is not there stops before it too', q.text)
        with io.open('ZEMPTY.txt', 'w', encoding='utf-8') as f:
            f.write('\n')
        with quiet() as q:
            rc = cli.main(['send', 'ZEMPTY.txt'])
        ok(rc == 1 and 'no source' in q.text, 'and so does an empty one', q.text)
        with quiet():
            rc = cli.main(['send', 'ZSENT.txt', '--name', 'bad name'])
        ok(rc == 2, 'a name with a space in it is refused')
        with quiet():
            rc = cli.main(['send', 'ZSENT.txt', '--name'])
        ok(rc == 2, '--name with no name is a usage error')
        with quiet():
            rc = cli.main(['send'])
        ok(rc == 2, 'send with no file is a usage error')
        with quiet():
            rc = cli.main(['send', 'A.txt', 'B.txt'])
        ok(rc == 2, 'send with two files is a usage error')

        link = Script(*calculator)
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['send', 'ZBROKEN.txt', '--no-lint'])
        with io.open('ZBROKEN.txt', encoding='utf-8') as f:
            broken = usb.program.normalize_source(f.read())
        ok(rc == 0 and link.sent[1:-1] == usb.to_reports(usb.program_message('ZBROKEN', broken)),
           '--no-lint sends what the linter refuses', q.text)
        ok('linter was not asked' in q.text, 'and says the linter was not asked', q.text)

        link = Script(*reply(usb.CMD_INFORMATION, information(build=16000)))
        usb.connect = lambda: link
        with quiet() as q:
            rc = cli.main(['send', 'ZSENT.txt'])
        ok(rc == 1 and len(link.sent) == 1 and '16000' in q.text and '--any-build' in q.text,
           'a build nobody measured gets nothing, and says how to send anyway',
           q.text)
        ok(link.closed, 'and lets go of the calculator')

        link = Script(*reply(usb.CMD_INFORMATION, information(build=16000)))
        with quiet() as q:
            rc = cli.main(['send', 'ZSENT.txt', '--any-build'])
        ok(rc == 0 and len(link.sent) == 3 and 'WARN' in q.text,
           '--any-build sends, and says it is unmeasured', q.text)

        link = Script()
        with quiet() as q:
            rc = cli.main(['send', 'ZSENT.txt'])
        ok(rc == 1 and len(link.sent) == 1 and 'did not answer' in q.text,
           'a calculator that does not answer gets nothing', q.text)

        lines = ['// %064x' % (n * 0x9E3779B97F4A7C15 % (1 << 256) * 0x2545F4914F6CDD1D % (1 << 256))
                 for n in range(1, 400)]
        with io.open('ZLONG.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n' + SMALL)
        link = Script(*calculator)
        with quiet() as q:
            rc = cli.main(['send', 'ZLONG.txt'])
        ok(rc == 0 and 'WARN' in q.text and 'most that has been measured' in q.text,
           'a message longer than any measured is sent, and said out loud', q.text)

        def refused():
            raise usb.UsbError('the calculator is there, and another program '
                               'holds it')
        usb.connect = refused
        with quiet() as q:
            rc = cli.main(['send', 'ZSENT.txt'])
        ok(rc == 1 and 'another program' in q.text,
           'a calculator held by the Connectivity Kit is an error for send too',
           q.text)

        with quiet() as q:
            rc = cli.main(['send', '--help'])
        ok(rc == 0 and 'Connectivity Kit' in q.text and 'replaced' in q.text
           and 'ask whoever' in q.text,
           'send --help says the Kit has to be closed, that it replaces, and to ask')
    finally:
        usb.connect, usb.GAP = real_connect, real_gap
        os.chdir(here)
        shutil.rmtree(tmp, ignore_errors=True)


def connecting():
    print('connecting')
    real_platform = sys.platform
    try:
        sys.platform = 'linux'
        try:
            usb.connect()
            ok(False, 'another platform is refused')
        except usb.UsbError as e:
            ok('Windows' in str(e), 'another platform is refused, and says why',
               str(e))
    finally:
        sys.platform = real_platform
    if not sys.platform.startswith('win'):
        return
    from hpkit import winhid
    real_paths, real_device = winhid.paths, winhid.Device
    try:
        winhid.paths = lambda vendor, product: []
        try:
            usb.connect()
            ok(False, 'no calculator is an error')
        except usb.UsbError as e:
            ok('no HP Prime G2' in str(e), 'no calculator is an error that says so',
               str(e))

        def busy(path):
            raise winhid.Busy()
        winhid.paths = lambda vendor, product: ['a path']
        winhid.Device = busy
        try:
            usb.connect()
            ok(False, 'a calculator somebody holds is an error')
        except usb.UsbError as e:
            ok('Connectivity Kit' in str(e) and 'taskkill' in str(e),
               'a calculator somebody holds is an error that says what to do',
               str(e))
    finally:
        winhid.paths, winhid.Device = real_paths, real_device


def main():
    keys()
    keys_against_the_documentation()
    frames()
    replies()
    identify()
    pictures()
    commands()
    letters_against_the_documentation()
    typing()
    typing_command()
    messages()
    sending()
    connecting()
    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
