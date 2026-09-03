# -*- coding: utf-8 -*-
"""Read and write HP Prime .hpprgm files from a PC.

A .hpprgm is a nested TLV container, little-endian:

    7C 61 8A B2                        magic
    FE FF FF FF  00 00 00 00           preamble
    [u32 len][len bytes of payload]    records, nested
    ...
    <trailer>

The PPL source lives inside one of those records as UTF-16LE, with LF line
endings (not CRLF) and a terminating NUL. It is stored verbatim: not
compressed, not encrypted.

The trailer is 1008 bytes in programs written by the Connectivity Kit, but
the calculator's built-in apps show that this is not always true, so nothing
here assumes it: the source record is located by its shape (see
_source_record) and everything after it is preserved untouched.

A code program is header + source + trailer, nothing else. A program that
declares large matrices also carries a COMPILED BLOCK before the source:
the numbers already in the calculator's internal format, which is what makes
such a file weigh about 3x its source and open without a compile wait.

This module cannot generate that compiled block. What it does is replace the
source inside an existing template and fix the length of every record that
contains it. So:

  - on a code program it works directly;
  - on one with a compiled block the block would no longer match the source,
    so it is refused (--force to override, on your own head).

Usage:
    hpprime read  PROG.hpprgm [-o out.txt]
    hpprime write source.txt [-t template.hpprgm] -o PROG.hpprgm
    hpprime verify PROG.hpprgm          # round-trip: read it and rebuild it
    hpprime templates <folder>          # which of your files can be templates

GETTING A TEMPLATE. The kit ships one in templates/code.hpprgm and `write`
picks it up on its own, so you only need your own if that one ever fails you.
It must be a code .hpprgm written by the Connectivity Kit, with no compiled
block, and you cannot just grab one from
Documents\\HP Connectivity Kit\\Calculators\\<your calculator>\\: that folder
is the mirror, everything in it has been through the calculator, and the
calculator adds its compiled block to whatever it stores. Measured on one
machine: of 58 containers, 2 were usable.

The `templates` command tells you which. If none are, create a program
INSIDE the Connectivity Kit itself and copy it out before sending it to the
calculator.
"""
from __future__ import unicode_literals
import io, os, struct, sys, unicodedata

MAGIC = b'\x7c\x61\x8a\xb2'


class UnexpectedFormat(Exception):
    pass


def _u32(b, off):
    return struct.unpack_from('<I', b, off)[0]


def _looks_like_source(raw):
    """A PPL source block in UTF-16LE: ends in NUL and is almost all
    printable text. Used to reject false matches.

    Printable, not ASCII. The rule used to be "90% ASCII", which rejected a
    short source with several accented characters in it -- a comment in
    Spanish or a string with units in it is enough to cross the line. What
    binary noise decoded as UTF-16LE actually looks like is control and
    unassigned code points, so that is what is counted against."""
    if len(raw) < 8 or len(raw) % 2 or raw[-2:] != b'\x00\x00':
        return False
    try:
        txt = raw[:-2].decode('utf-16-le')
    except UnicodeDecodeError:
        return False
    if not txt:
        return False
    sample = txt[:2000]
    printable = sum(1 for c in sample
                    if c in '\n\t' or unicodedata.category(c)[0] != 'C')
    return printable >= 0.9 * len(sample)


def _source_record(b):
    """Locate the source block and the records that contain it.

    The container's full grammar is not reconstructed: some records carry a
    4-byte tag before their children and some do not, and guessing wrong
    means descending into the wrong place. The trailer size is not assumed
    either -- 1008 bytes is what the Connectivity Kit writes, but the
    calculator's built-in apps prove it is not universal.

    What is firm is the shape of the source record:

        [u32 length][u32 tag][UTF-16LE text][NUL]

    So that is what is searched for, and of all the candidates the largest
    one wins: the real source. The records that wrap it are the ones ending
    exactly where it ends, and those are the lengths to fix when the text
    changes.

    Returns (length offsets to patch, start of text, end of text).
    """
    if b[:4] != MAGIC:
        raise UnexpectedFormat('does not start with the magic 7C 61 8A B2')
    n = len(b)
    best = None
    # Byte by byte, not in steps of 4: when a compiled block sits before the
    # source (the matrices of a data program) its size is not a multiple of
    # 4 and the source record ends up unaligned.
    for o in range(0x0c, n - 12):
        # cheap filter: the payload must start with an ASCII character
        # encoded as UTF-16LE (high byte zero)
        if b[o + 9] != 0:
            continue
        c = b[o + 8]
        if not (c == 0x0a or 0x20 <= c < 0x7f or c >= 0xa0):
            continue
        end = o + 4 + _u32(b, o)
        if end > n or end - (o + 8) < 8:
            continue
        if not _looks_like_source(b[o + 8:end]):
            continue
        if best is None or end - o > best[1] - best[0]:
            best = (o, end)
    if best is None:
        raise UnexpectedFormat('no source block found (empty program?)')
    off, end = best
    lens = [o for o in range(0x0c, off + 1) if o + 4 + _u32(b, o) == end]
    return lens, off + 8, end


def read(data):
    """-> (source text, length offsets, start of text, end of text)."""
    lens, start, end = _source_record(data)
    txt = data[start:end].decode('utf-16-le')
    return txt.rstrip('\0'), lens, start, end


HEADER_END = 0x98    # 152: bare header, the source starts exactly here


def has_compiled_block(data, start):
    """True if there is anything between the header and the source.

    A file freshly written by the Connectivity Kit has its source at offset
    152 exactly. Anything more is a compiled block, and then the file is no
    use as a template: change the text and the block no longer matches it.

    The threshold used to be `> 0x200` and that was wrong. Programs saved by
    the calculator carry small blocks -- 96, 184, 360 bytes -- that slipped
    under it. It showed up in cross-rebuilds, which came out exactly those
    many bytes short.
    """
    return start > HEADER_END


def normalize_source(txt):
    """Put the text in the shape the Connectivity Kit stores when you paste
    code into it: LF endings and no trailing newline, because what it stores
    is the editor's buffer.

    `write` does not apply this: the calculator's built-in apps carry CRLF
    inside and have to be rewritable as they are. The CLI applies it, since
    the CLI is what starts from a .txt on the PC."""
    t = txt.replace('\r\n', '\n').replace('\r', '\n')
    return t[:-1] if t.endswith('\n') else t


def write(template, source):
    """Put `source` into `template` (bytes), fixing the record lengths.

    The text is stored verbatim: call normalize_source() first if you want
    Connectivity-Kit-style line endings.

    This cannot add a compiled block. The block is not a slab in front of the
    source: it is the program's SYMBOL TABLE, and the program itself is one
    entry in it -- `Main`, with the source record nested inside its value. So
    adding globals means splicing entries into that table ahead of `Main`,
    and which enclosing records then have to grow is not established. See
    docs/reference/formats.md.
    """
    _old, lens, start, end = read(template)
    blob = (source + '\0').encode('utf-16-le')
    delta = len(blob) - (end - start)
    out = bytearray(template[:start]) + blob + template[end:]
    for off in lens:                       # every record that contains it
        struct.pack_into('<I', out, off, _u32(bytes(out), off) + delta)
    return bytes(out)


def default_template():
    """Path of the code template shipped with the kit, or None."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = os.path.join(root, 'templates', 'code.hpprgm')
    return p if os.path.exists(p) else None


# ------------------------------------------------------------------ CLI

def cli(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, path = argv[0], argv[1]
    args = argv[2:]

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args else default

    if cmd == 'templates':
        # Which of your binaries can act as a template for `write`. This
        # exists because intuition fails: the CK mirror folder holds
        # everything that has been through the calculator, and the
        # calculator adds its compiled block to what it saves. Measured on
        # one machine: 2 of 58.
        import glob
        if not os.path.isdir(path):
            print('usage: hpprime templates <folder>')
            return 2
        cands = []
        for pattern in ('*.hpprgm', os.path.join('*', '*.hpprgm'),
                        os.path.join('*.hpappdir', '*.hpappprgm'),
                        os.path.join('*', '*.hpappdir', '*.hpappprgm')):
            cands.extend(sorted(glob.glob(os.path.join(path, pattern))))
        good, total, unreadable = [], 0, 0
        for p in cands:
            total += 1
            try:
                d = open(p, 'rb').read()
                _, _, start, _ = read(d)
            except Exception:
                unreadable += 1
                continue
            if not has_compiled_block(d, start):
                good.append((len(d), p))
        for n, p in sorted(good):
            print('  %8d B  %s' % (n, p))
        print('\n%d container(s): %d usable as a template, %d with a compiled '
              'block, %d with no source to read'
              % (total, len(good), total - len(good) - unreadable, unreadable))
        if not good:
            print('\nNone are usable. Create a program INSIDE the Connectivity')
            print('Kit and copy it out before sending it to the calculator:')
            print('that one carries no compiled block.')
        else:
            print('\nCopy one over templates/code.hpprgm and every tool here')
            print('will pick it up on its own.')
        return 0 if good else 1

    data = open(path, 'rb').read() if cmd != 'write' else None

    if cmd == 'read':
        txt, _lens, start, _end = read(data)
        dest = opt('-o')
        print('%s: %d bytes, source %d chars at offset %d'
              % (os.path.basename(path), len(data), len(txt), start))
        if has_compiled_block(data, start):
            print('  carries %d bytes of compiled block before the source'
                  % (start - HEADER_END))
        if dest:
            with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
                f.write(txt)
            print('  wrote %s' % dest)
        else:
            sys.stdout.write(txt.encode('utf-8') if str is bytes else txt)
        return 0

    if cmd == 'verify':
        txt, _lens, _start, _end = read(data)
        rebuilt = write(data, txt)
        ok = rebuilt == data
        print('round-trip %s: %s' % (os.path.basename(path),
                                     'IDENTICAL' if ok else 'DIFFERS'))
        if not ok:
            print('  original %d bytes, rebuilt %d' % (len(data), len(rebuilt)))
            for i, (a, b) in enumerate(zip(data, rebuilt)):
                if a != b:
                    print('  first difference at offset %d' % i)
                    break
        return 0 if ok else 1

    if cmd == 'write':
        tpl_path = opt('-t') or default_template()
        dest = opt('-o')
        if not tpl_path:
            print('no template: pass -t template.hpprgm, or put one at')
            print('templates/code.hpprgm (see `hpprime templates`)')
            return 2
        if not dest:
            print('missing -o output.hpprgm')
            return 2
        template = open(tpl_path, 'rb').read()
        _, _, start, _ = read(template)
        if has_compiled_block(template, start) and '--force' not in args:
            print('ERROR: that template carries a %d-byte compiled block.'
                  % (start - HEADER_END))
            print('       Changing the source would leave it out of step.')
            print('       Use a code program (no matrices) as a template,')
            print('       or --force if you know what you are doing.')
            return 1
        source = normalize_source(io.open(path, encoding='utf-8').read())
        out = write(template, source)
        with open(dest, 'wb') as f:
            f.write(out)
        print('%s -> %s  (%d bytes)' % (path, dest, len(out)))
        # immediate check: read back what was just written
        print('  reads back correctly:', read(out)[0] == source)
        return 0

    print('unknown command: %s' % cmd)
    return 2


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
