# -*- coding: utf-8 -*-
"""A G2 on its USB cable: its screen, its keys and its programs, with nothing
else running.

    hpprime screen -o now.png
    hpprime press 2 + 2 enter
    hpprime type SELF4 --enter
    hpprime send programs/CIRCLE/CIRCLE.txt

docs/topics/usb.md holds what this rests on and how each part of it is known.
Everything here but connect() is plain bytes, so the tests run it against a
script of reports with no calculator. Only the Windows side is written, in
hpkit/winhid.py, since that is the only one measured.
"""
from __future__ import unicode_literals
import binascii, io, os, re, struct, sys, time, zlib
from collections import OrderedDict

from hpkit import program

VENDOR, PRODUCT = 0x03F0, 0x2441            # usb.device
MEASURED_BUILD = 15515                      # the only one these were tried on
CMD_INFORMATION = 0xFA
CMD_SCREEN = 0xFC
CMD_KEY = 0xEC
CMD_FILE = 0xF7
SCREEN_FORMAT = 8
TYPE_PROGRAM = 0x06
PROTOCOL = 0x03                             # the third byte of a reply: usb.frames
REPORT_DATA = 1023                          # usb.device, less the sequence number
# A report's sequence number is one byte, and FE and FF start control frames.
MAX_REPORTS = 0xFE
MEASURED_REPORTS = 6                        # the longest message tried
# A key acts when a report starting 01 follows it, and not before: usb.keys.
RELEASE = b'\x01'
# Between one key and the next, the only gap measured. In a run of more than
# two keys the calculator sets the real pace, 2.3 to 2.9 s a key, by holding
# back the report after a key until it is ready.
GAP = 0.25
PNG = b'\x89PNG\r\n\x1a\n'

# The names of interface.key-codes, which tests/test_usb.py holds this table
# to. A digit names the key marked with it, not a code: 2 is code 43.
KEYS = OrderedDict([
    ('apps', 0), ('symb', 1), ('up', 2), ('help', 3), ('esc', 4),
    ('home', 5), ('plot', 6), ('left', 7), ('right', 8), ('view', 9),
    ('cas', 10), ('num', 11), ('down', 12), ('menu', 13),
    ('vars', 14), ('mem', 15), ('units', 16), ('xttn', 17), ('frac', 18),
    ('del', 19),
    ('pow', 20), ('sin', 21), ('cos', 22), ('tan', 23), ('ln', 24), ('log', 25),
    ('sq', 26), ('neg', 27), ('parens', 28), ('eval', 29), ('enter', 30),
    ('eex', 31), ('7', 32), ('8', 33), ('9', 34), ('div', 35),
    ('alpha', 36), ('4', 37), ('5', 38), ('6', 39), ('mul', 40),
    ('shift', 41), ('1', 42), ('2', 43), ('3', 44), ('sub', 45),
    ('on', 46), ('0', 47), ('.', 48), ('space', 49), ('add', 50),
])
# The same keys as they are marked, for the shells that let these through.
MARKED = {'+': 'add', '-': 'sub', '*': 'mul', '/': 'div'}
# The key that carries each letter, A to Z: usb.letters, which tests/test_usb.py
# holds this to.
LETTER_KEYS = ('vars', 'mem', 'units', 'xttn', 'frac', 'pow', 'sin', 'cos', 'tan',
               'ln', 'log', 'sq', 'neg', 'parens', 'eval', 'eex', '7', '8', '9',
               'div', '4', '5', '6', 'mul', '1', '2')


class UsbError(Exception):
    """Something a person can act on, said the way a person would."""


def key_code(name):
    """-> the code of a key named on the command line. code:N takes it by
    number, 0 to 50."""
    name = name.lower()
    name = MARKED.get(name, name)
    if name in KEYS:
        return KEYS[name]
    number = name[5:] if name.startswith('code:') else ''
    if number.isdigit() and int(number) <= 50:
        return int(number)
    raise UsbError('%s is not a key. `hpprime press --list` names them all.'
                   % name)


def key_frame(code):
    return bytes(bytearray([0x00, CMD_KEY, 0x03, 0, 0, 0, 1, code]))


def keys_for_text(text):
    """-> the names of the keys that type some letters and digits: usb.letters.
    A run of letters takes Alpha held only where that is fewer keys, since a
    letter costs more than two seconds, and the hold always ends with the run:
    a digit under it would be a letter."""
    keys = []
    for run in re.findall(r'[A-Z]+|[a-z]+|[0-9]+|.', text, re.S):
        if '0' <= run[0] <= '9':
            keys += list(run)
        elif not ('A' <= run[0] <= 'Z' or 'a' <= run[0] <= 'z'):
            raise UsbError('%r cannot be typed: only letters and digits have '
                           'been measured. `hpprime press` takes any key.' % run)
        else:
            small = run.islower()
            letters = [LETTER_KEYS[ord(c.upper()) - ord('A')] for c in run]
            once = ['shift', 'alpha'] if small else ['alpha']
            held = ['shift', 'alpha', 'alpha'] if small else ['alpha', 'alpha']
            if len(held) + len(run) + 1 < len(run) * (len(once) + 1):
                keys += held + letters + ['alpha']
            else:
                for letter in letters:
                    keys += once + [letter]
    return keys


def read_reply(link, command, first=8000, then=2000):
    """-> the data of the reply to a command. Control frames are skipped, and
    so is anything that is not this reply, so neither of them can stretch the
    wait past its limit."""
    data, size, sequence = None, 0, 0
    deadline = time.time() + first / 1000.0
    while True:
        left = int((deadline - time.time()) * 1000)
        report = link.read(left) if left > 0 else None
        if report is None:
            if data is None:
                raise UsbError('the calculator did not answer within %.0f s. '
                               'Is it switched on?' % (first / 1000.0))
            raise UsbError('the reply stopped after %d of %d bytes'
                           % (len(data), size))
        frame = bytearray(report[1:])
        if not frame or frame[0] in (0xFE, 0xFF):
            continue
        if data is None:
            if frame[0] != 0x00 or frame[1] != command:
                continue
            size = struct.unpack('>I', bytes(frame[3:7]))[0]
            data = bytearray(frame[7:])
        else:
            sequence = (sequence + 1) & 0xFF
            if frame[0] != sequence:
                raise UsbError('the reply came out of order: report %d where '
                               '%d was next' % (frame[0], sequence))
            data += frame[1:]
        if len(data) >= size:
            return bytes(data[:size])
        deadline = time.time() + then / 1000.0


def identify(link):
    """-> (build, version). The reply holds the serial number too, which stays
    here."""
    link.write(bytes(bytearray([0x00, CMD_INFORMATION])))
    data = bytearray(read_reply(link, CMD_INFORMATION, first=3000))
    n = len(data)
    if n < 36:
        raise UsbError('the calculator answered with %d bytes of information, '
                       'and at least 36 were expected' % n)
    version = bytes(data[n - 32:n - 22]).split(b'\x00')[0]
    return data[n - 36] | (data[n - 35] << 8), version.decode('ascii', 'replace')


def read_screen(link):
    """-> the PNG the calculator sends for its screen, as it sends it."""
    link.write(bytes(bytearray([0x00, CMD_SCREEN, SCREEN_FORMAT])))
    data = read_reply(link, CMD_SCREEN)
    start = data.find(PNG)
    if start < 0:
        raise UsbError('the reply holds no picture')
    return data[start:]


def checksum(data):
    """CRC-16, polynomial 1021, starting from 0: usb.program-message."""
    return binascii.crc_hqx(data, 0)


def program_message(name, source):
    """-> the message that installs a program: usb.program-message. The source
    travels without the container of a .hpprgm, and the calculator makes that
    itself."""
    encoded = name.encode('utf-16-le')
    inner = (bytearray([TYPE_PROGRAM, len(encoded), 0, 0]) + encoded
             + source.encode('utf-16-le') + b'\x00\x00')
    head = bytes(bytearray([CMD_FILE, PROTOCOL]))
    crc = checksum(head + struct.pack('>I', len(inner)) + bytes(inner))
    inner[2], inner[3] = crc & 0xFF, crc >> 8
    stream = zlib.compress(bytes(inner), 1)
    return (head + struct.pack('>I', len(stream) + 4)
            + struct.pack('<I', len(inner)) + stream)


def to_reports(message):
    """-> a message cut into frames, each with its sequence number."""
    pieces = [message[i:i + REPORT_DATA]
              for i in range(0, len(message), REPORT_DATA)]
    if len(pieces) > MAX_REPORTS:
        raise UsbError('this takes %d reports, and a sequence number runs out '
                       'at %d. Nothing has been tried past %d.'
                       % (len(pieces), MAX_REPORTS, MEASURED_REPORTS))
    return [bytes(bytearray([n])) + piece for n, piece in enumerate(pieces)]


def read_source(path):
    """-> the source of a program, from its text or from a built .hpprgm."""
    try:
        if path.lower().endswith('.hpprgm'):
            with open(path, 'rb') as f:
                text = program.read(f.read())[0]
        else:
            with io.open(path, encoding='utf-8') as f:
                text = f.read()
    except (IOError, OSError, UnicodeDecodeError,
            program.UnexpectedFormat) as e:
        raise UsbError('cannot read %s: %s' % (path, e))
    return program.normalize_source(text)


def read_png(data):
    """-> (width, height, rows) of a PNG holding 16-bit greys, the one kind
    the calculator was seen to send. The rows are bytes, unfiltered."""
    if data[:8] != PNG:
        raise UsbError('not a PNG')
    position, idat = 8, bytearray()
    width = height = None
    try:
        while position < len(data):
            size, kind = struct.unpack('>I4s', data[position:position + 8])
            chunk = data[position + 8:position + 8 + size]
            position += 12 + size
            if kind == b'IHDR':
                width, height, depth, colour, _, _, interlace = \
                    struct.unpack('>IIBBBBB', chunk)
                if (depth, colour, interlace) != (16, 0, 0):
                    raise UsbError('a picture of depth %d, colour type %d, '
                                   'interlace %d: only depth 16, colour type 0, '
                                   'no interlace has been seen'
                                   % (depth, colour, interlace))
            elif kind == b'IDAT':
                idat += chunk
            elif kind == b'IEND':
                break
        raw = zlib.decompress(bytes(idat))
    except (struct.error, zlib.error) as e:
        raise UsbError('the picture is damaged: %s' % e)
    if width is None:
        raise UsbError('the picture has no header')
    stride = width * 2
    if len(raw) != height * (stride + 1):
        raise UsbError('the picture is %d bytes, not the %d its header says'
                       % (len(raw), height * (stride + 1)))
    rows, previous = [], bytearray(stride)
    for y in range(height):
        start = y * (stride + 1)
        kind = bytearray(raw[start:start + 1])[0]
        row = bytearray(raw[start + 1:start + 1 + stride])
        for i in range(stride):
            a = row[i - 2] if i >= 2 else 0
            b = previous[i]
            if kind == 1:
                row[i] = (row[i] + a) & 255
            elif kind == 2:
                row[i] = (row[i] + b) & 255
            elif kind == 3:
                row[i] = (row[i] + (a + b) // 2) & 255
            elif kind == 4:
                c = previous[i - 2] if i >= 2 else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                row[i] = (row[i] + (a if pa <= pb and pa <= pc
                                    else b if pb <= pc else c)) & 255
        rows.append(bytes(row))
        previous = row
    return width, height, rows


def to_rgb(rows, width):
    """16-bit greys to the colours they hold: usb.screen. Each is
    xRRRRRGGGGGBBBBB, low byte first, the opposite of what a PNG means by 16
    bits, so white is stored FF 7F."""
    out = []
    for row in rows:
        row = bytearray(row)
        line = bytearray(width * 3)
        for x in range(width):
            v = row[2 * x] | (row[2 * x + 1] << 8)
            line[3 * x] = ((v >> 10) & 31) * 255 // 31
            line[3 * x + 1] = ((v >> 5) & 31) * 255 // 31
            line[3 * x + 2] = (v & 31) * 255 // 31
        out.append(bytes(line))
    return out


def write_png(path, width, height, rows):
    """An ordinary 8-bit RGB PNG, which anything can open."""
    def chunk(kind, body):
        return (struct.pack('>I', len(body)) + kind + body
                + struct.pack('>I', zlib.crc32(kind + body) & 0xFFFFFFFF))
    raw = b''.join(b'\x00' + row for row in rows)
    with open(path, 'wb') as f:
        f.write(PNG
                + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2,
                                             0, 0, 0))
                + chunk(b'IDAT', zlib.compress(raw, 6))
                + chunk(b'IEND', b''))


def connect():
    """-> the calculator's link, open. Nothing has been said to it yet."""
    if not sys.platform.startswith('win'):
        raise UsbError('only written for Windows so far: this is the one '
                       'platform it has been measured on')
    from hpkit import winhid
    found = winhid.paths(VENDOR, PRODUCT)
    if not found:
        raise UsbError('no HP Prime G2 on USB. Is the cable in, and the '
                       'calculator switched on?')
    try:
        return winhid.Device(found[0])
    except winhid.Busy:
        raise UsbError('the calculator is there, and another program holds '
                       'it, most likely the Connectivity Kit. Windows gives '
                       'it to one at a time: close that and run this again. '
                       '`taskkill /IM ConnectivityKit.exe` asks the Kit to '
                       'close; if somebody else is using it, ask them first.')


def _check_build(link):
    """Whether it answers at all, which is the one proof a key can't give, and
    whether anybody has tried this on what it runs."""
    build, version = identify(link)
    if build != MEASURED_BUILD:
        print('WARN: this calculator is on build %d (%s). These messages were '
              'measured on %d only, so what follows may not hold.'
              % (build, version, MEASURED_BUILD))
    return build


# ---------------------------------------------------------------------- cli

USAGE_SCREEN = """hpprime screen [-o FILE.png]

Save what a G2 on its USB cable is showing, as a picture. The Connectivity Kit
has to be closed: Windows gives the calculator to one program at a time.

  -o FILE.png   where it goes (default: screen.png)

Takes up to 3 s. See docs/topics/usb.md.
"""

USAGE_PRESS = """hpprime press KEYS...
hpprime press --list

Press keys on a G2 on its USB cable, one after another. The Connectivity Kit
has to be closed: Windows gives the calculator to one program at a time.

  KEYS     names: up, down, left, right, enter, esc, del, shift, alpha...
           A digit is the key marked with it: 2 is that key, not code 2.
           + - * / are those keys, and so are add, sub, mul, div, for a shell
           that would take them for something else.
           code:N takes a key by its number, 0 to 50.
  --list   print every name with its code

    hpprime press 2 + 2 enter
    hpprime press alpha 5         # V: a letter is alpha, then the key with it
    hpprime press shift alpha 5   # v

Allow about 3 s a key in a long run: the calculator sets the pace. It
acknowledges nothing, so a clean exit means the keys were sent and not that they
did anything: `hpprime screen` shows what they did. Few keys have been measured,
and they stop the clock being drawn for about 5 minutes. See docs/topics/usb.md.
"""


USAGE_TYPE = """hpprime type TEXT [--enter]

Type letters and digits on a G2 on its USB cable, wherever its cursor is. The
Connectivity Kit has to be closed: Windows gives the calculator to one program
at a time.

  --enter   press Enter afterwards

    hpprime type SELF4 --enter    # on Home, starts what that name names

Look at the screen first: on Home with an empty line it goes where you expect,
and a selection in the history has to go first, with `hpprime press esc`. Allow
about 3 s a key, and a letter is up to three keys. Nothing else can be typed,
since nothing else has been measured: `hpprime press` takes any key.

The calculator acknowledges nothing, so a clean exit means the keys were sent:
`hpprime screen` shows what they did. See docs/topics/usb.md.
"""


def _press_all(link, names):
    """Each key, then the report that makes it act: usb.keys."""
    for name in names:
        link.write(key_frame(KEYS[name]))
        link.write(RELEASE)
        time.sleep(GAP)


def cli_type(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE_TYPE)
        return 0
    rest = list(argv)
    enter = '--enter' in rest
    if enter:
        rest.remove('--enter')
    if len(rest) != 1 or rest[0].startswith('--'):
        print(USAGE_TYPE)
        return 2
    text = rest[0]
    try:
        names = keys_for_text(text)
    except UsbError as e:
        print('ERROR: %s' % e)
        return 2
    if enter:
        names = names + ['enter']
    if not names:
        print(USAGE_TYPE)
        return 2
    try:
        link = connect()
        try:
            _check_build(link)
            started = time.time()
            _press_all(link, names)
            took = time.time() - started
        finally:
            link.close()
    except (UsbError, OSError) as e:
        print('ERROR: %s' % e)
        return 1
    print('typed %s%s: %d key(s) in %.1f s'
          % (text, ' and Enter' if enter else '', len(names), took))
    print('(nothing acknowledges a key: `hpprime screen` shows what it did)')
    return 0


USAGE_SEND = """hpprime send FILE [--name NAME] [--any-build] [--no-lint]

Install a program on a G2 on its USB cable. The Connectivity Kit has to be
closed: Windows gives the calculator to one program at a time.

  FILE         its source, or a built .hpprgm, whose source is what travels
  --name NAME  what it is called on the calculator (default: the file's name)
  --any-build  send to a build other than 15515, the only one measured
  --no-lint    send what the linter refuses, to ask the calculator whether it
               compiles: usb.compile-check says how to read the answer

A program of that name is replaced without asking, since the calculator cannot
be asked what it holds, so ask whoever uses the calculator first. A program the
linter finds errors in is not sent. Apps are not sent either: those are still a
drag in the Connectivity Kit.

The calculator acknowledges nothing, so a clean exit means it was sent and not
that it arrived: type one of its functions on Home, or read it back through the
Connectivity Kit. See docs/topics/usb.md.
"""


def cli_send(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE_SEND)
        return 0
    rest, name = list(argv), None
    any_build = '--any-build' in rest
    if any_build:
        rest.remove('--any-build')
    no_lint = '--no-lint' in rest
    if no_lint:
        rest.remove('--no-lint')
    if '--name' in rest:
        i = rest.index('--name')
        if i + 1 >= len(rest):
            print('ERROR: --name needs a name')
            return 2
        name = rest[i + 1]
        del rest[i:i + 2]
    if len(rest) != 1 or rest[0].startswith('-'):
        print(USAGE_SEND)
        return 2
    path = rest[0]
    if name is None:
        name = os.path.splitext(os.path.basename(path))[0]
    if not name.replace('_', '').isalnum() or len(name) > 127:
        print('ERROR: "%s" is not a good name. Use letters and digits, or say '
              'which with --name.' % name)
        return 2
    from hpkit import lint
    # All of this before the calculator is touched, so that nothing goes that
    # should not.
    try:
        source = read_source(path)
        if not source.strip():
            raise UsbError('%s has no source in it' % path)
        if no_lint:
            print('WARN: --no-lint: the linter was not asked.')
        else:
            errors = [f for f in lint.check_source(path, source)[0]
                      if f.level == 'ERROR']
            for f in errors:
                print(str(f))
            if errors:
                print('not sent: %d linter error(s). To ask the calculator '
                      'itself: --no-lint' % len(errors))
                return 1
        reports = to_reports(program_message(name, source))
        link = connect()
        try:
            build, version = identify(link)
            if build != MEASURED_BUILD:
                if not any_build:
                    raise UsbError('this calculator is on build %d (%s), and '
                                   'sending was measured on %d only. Nothing '
                                   'was sent. --any-build sends anyway.'
                                   % (build, version, MEASURED_BUILD))
                print('WARN: this calculator is on build %d (%s), and sending '
                      'was measured on %d only.'
                      % (build, version, MEASURED_BUILD))
            if len(reports) > MEASURED_REPORTS:
                print('WARN: this takes %d reports, and %d is the most that has '
                      'been measured.' % (len(reports), MEASURED_REPORTS))
            for report in reports:
                link.write(report)
            time.sleep(GAP)
            link.write(RELEASE)
        finally:
            link.close()
    except (UsbError, OSError) as e:
        print('ERROR: %s' % e)
        return 1
    print('sent %s: %d characters in %d report(s)'
          % (name, len(source), len(reports)))
    names = re.findall(r'^[ \t]*EXPORT[ \t]+(\w+)[ \t]*\(', source, re.M)
    if names:
        print('it exports: %s' % ', '.join(names))
    print('(nothing acknowledges it: type a function on Home, or read it back '
          'through the Connectivity Kit)')
    return 0


def cli_screen(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE_SCREEN)
        return 0
    out, rest = 'screen.png', list(argv)
    if '-o' in rest:
        i = rest.index('-o')
        if i + 1 >= len(rest):
            print('ERROR: -o needs a file name')
            return 2
        out = rest[i + 1]
        del rest[i:i + 2]
    if rest:
        print('ERROR: did not expect %s\n' % ' '.join(rest))
        print(USAGE_SCREEN)
        return 2
    try:
        link = connect()
        try:
            _check_build(link)
            started = time.time()
            png = read_screen(link)
            took = time.time() - started
        finally:
            link.close()
        width, height, rows = read_png(png)
        write_png(out, width, height, to_rgb(rows, width))
    except (UsbError, OSError) as e:
        print('ERROR: %s' % e)
        return 1
    print('%s: %dx%d, %.1f s' % (out, width, height, took))
    return 0


def cli_press(argv):
    if '--help' in argv or '-h' in argv:
        print(USAGE_PRESS)
        return 0
    if '--list' in argv:
        for name, code in KEYS.items():
            print('%2d  %s' % (code, name))
        return 0
    if not argv:
        print(USAGE_PRESS)
        return 2
    # Every name is checked before the first key goes, so a typing mistake
    # cannot leave half of them pressed.
    try:
        codes = [key_code(name) for name in argv]
    except UsbError as e:
        print('ERROR: %s' % e)
        return 2
    try:
        link = connect()
        try:
            _check_build(link)
            started = time.time()
            for code in codes:
                link.write(key_frame(code))
                link.write(RELEASE)
                time.sleep(GAP)
            took = time.time() - started
        finally:
            link.close()
    except (UsbError, OSError) as e:
        print('ERROR: %s' % e)
        return 1
    print('sent %d key(s) in %.1f s: %s' % (len(codes), took, ' '.join(argv)))
    print('(nothing acknowledges a key: `hpprime screen` shows what it did)')
    return 0
