# -*- coding: utf-8 -*-
"""The HP Prime's internal number format, and the files that use it.

It shows up in two places:

  - the COMPILED BLOCK the calculator puts before the source in programs
    that declare matrices (see docs/reference/formats.md);
  - the .hpmat files of the M0..M9 matrices.

ONE NUMBER IS 8 BYTES, little-endian. Read as a 64-bit integer:

    bits  0..11   decimal exponent, 12-bit two's complement
    bits 12..59   12 BCD mantissa digits, most significant at the top
    bits 60..63   sign: 0 positive, 9 negative   (the usual BCD convention)

    value = d1.d2d3...d12 x 10^exponent          and zero is all zeros

Two real examples:

    9760000000000001  ->  sign 9, mantissa 760000000000, exp 1  ->  -76.0
    0600000000000FFC  ->  sign 0, mantissa 600000000000, exp -4 ->  0.0006

HOW IT WAS WORKED OUT, AND HOW IT IS VERIFIED

With a Rosetta stone, not by guessing: a data program carries the compiled
block BEFORE the source, and the source is the same numbers written out in
decimal. That gives thousands of (bytes, value) pairs that nobody chose.

On the sample it was decoded against -- 44,718 numbers in one program, 1,482
of them negative -- every number decoded exactly and re-encoded byte for
byte. The negatives are what pinned the sign nibble down: it is 9, not 1.
tests/test_numbers.py redoes that check against YOUR files.

WHAT THIS OPENS, AND WHAT IT DOES NOT

It opens reading and writing .hpmat, which is a whole matrix as a file: drag
it to the calculator, with nothing pasted and no program source involved.

It does NOT yet open generating a program's compiled block. That block is
not only numbers: between one matrix and the next it carries records with
the symbol name in UTF-16LE. What is known about that structure is in
docs/reference/formats.md; the hard part -- the number format -- is no
longer in the way.

Usage:
    hpprime matrix read  M1.hpmat                 # to text
    hpprime matrix write data.csv -o M1.hpmat     # from CSV to a matrix
    hpprime matrix nums  PROG.hpprgm              # the block's matrices
"""
from __future__ import unicode_literals
import io, os, struct, sys

# A .hpmat header: 16 bytes.
#   00  01 00       ?  (constant in everything observed)
#   02  14 80       type: 8014 real, 8094 complex (16 bytes per element)
#   04  u32 = 2     rank: 2 = matrix
#   08  u32         rows
#   12  u32         columns
# The TYPE IS THE LOW BYTE. Measured over 20 real .hpmat files: the high
# byte is 00, 04 or 80 for the same kind of matrix, and the compiled block
# leaves uninitialised memory there. Reading the pair as a 16-bit type
# rejects perfectly good files.
HPMAT_REAL = 0x14
HPMAT_COMPLEX = 0x94
HPMAT_WRITE_TYPE = 0x8014      # what the calculator wrote in the files that
                               # round-tripped byte for byte


class UnexpectedFormat(Exception):
    pass


def decode(b):
    """8 bytes -> float. Raises if they are not valid BCD."""
    if len(b) != 8:
        raise UnexpectedFormat('a number is 8 bytes, not %d' % len(b))
    w = struct.unpack('<Q', b)[0]
    exp = w & 0xFFF
    if exp >= 0x800:                       # 12-bit two's complement
        exp -= 0x1000
    digits = ''.join('%X' % ((w >> d) & 0xF) for d in range(56, 8, -4))
    if set(digits) - set('0123456789'):
        raise UnexpectedFormat('mantissa that is not BCD: %s' % digits)
    sign = (w >> 60) & 0xF
    if sign not in (0, 9):
        raise UnexpectedFormat('unexpected sign nibble: %X' % sign)
    if digits == '0' * 12:
        return 0.0
    # Straight from the decimal string to the float. Multiplying by 10**exp
    # introduced floating-point error: 0.0006 came out 0.0006000000000000001.
    v = float(digits[0] + '.' + digits[1:] + 'E' + str(exp))
    return -v if sign else v


def encode(x):
    """float -> 8 bytes.

    It keeps 12 significant digits, which is what fits. A number with more is
    rounded, exactly as the calculator would round it.
    """
    x = float(x)
    if x != x or x in (float('inf'), float('-inf')):
        raise UnexpectedFormat('there is no way to write %r' % x)
    if x == 0.0:
        return struct.pack('<Q', 0)
    mantissa, exp = ('%.11E' % abs(x)).split('E')
    exp = int(exp)
    digits = mantissa.replace('.', '')[:12].ljust(12, '0')
    if not -2048 <= exp <= 2047:
        raise UnexpectedFormat('exponent %d is outside the 12-bit range' % exp)
    w = ((9 if x < 0 else 0) << 60) | (exp & 0xFFF)
    for k, ch in enumerate(digits):
        w |= int(ch) << (56 - 4 * k)
    return struct.pack('<Q', w)


# --------------------------------------------------------------- .hpmat

def read_hpmat(data):
    """-> list of rows (lists of float). Complex matrices raise."""
    if len(data) < 16:
        raise UnexpectedFormat('an .hpmat is at least 16 bytes')
    kind, rank, rows, cols = struct.unpack_from('<2xHIII', data, 0)
    if rank != 2:
        raise UnexpectedFormat('rank %d: this is not a matrix' % rank)
    if kind & 0xFF == HPMAT_COMPLEX:
        raise UnexpectedFormat('complex matrix: not covered')
    if kind & 0xFF != HPMAT_REAL:
        raise UnexpectedFormat('unknown type %04X' % kind)
    needed = 16 + rows * cols * 8
    if len(data) < needed:
        raise UnexpectedFormat('bytes missing: %dx%d needs %d, there are %d'
                               % (rows, cols, needed, len(data)))
    out = []
    for i in range(rows):
        row = []
        for j in range(cols):
            o = 16 + 8 * (i * cols + j)
            row.append(decode(data[o:o + 8]))
        out.append(row)
    return out


def write_hpmat(matrix):
    """[[float]] -> the bytes of an .hpmat."""
    rows = len(matrix)
    if not rows:
        raise UnexpectedFormat('an empty matrix cannot be written')
    cols = len(matrix[0])
    if any(len(r) != cols for r in matrix):
        raise UnexpectedFormat('the rows are not all the same length')
    out = bytearray(struct.pack('<HHIII', 1, HPMAT_WRITE_TYPE, 2, rows,
                                cols))
    for row in matrix:
        for x in row:
            out += encode(x)
    return bytes(out)


# ------------------------------------------- a program's compiled block
#
# The block is a chain of SYMBOL ENTRIES, one per global the program
# declares, in the order the source declares them. Each entry is three TLV
# records, the same shape as the container around it:
#
#   [u32 total]                        everything below
#     [u32 68][u32 NAME_TAG][name UTF-16LE, zero-padded to 64 bytes]
#     [u32 8][u32 TYPE_TAG][u32 9]     9 in every entry measured
#     [u32 len][u32 VALUE_TAG][value]
#
# and a real matrix value is
#
#   [u16 flag][u16 0x0014][u32 rank=2][u32 rows][u32 cols][rows*cols numbers]
#
# Verified by walking a 367 KB block whole: 72 entries, ending exactly where
# the source record begins, recovering the same 72 names in the same order
# the source declares them.
NAME_TAG = 0x0040018B          # a variable
FUNCTION_TAG = 0x0040020B      # a function, wrapped in one more record
PROGRAM_TAG = 0x0040008B       # Main, whose value holds the source
TYPE_TAG = 0x00800185
VALUE_TAG = 0x00C0018C
NAME_RECORD = 68          # 4 for the tag + 64 for the text
MATRIX_TYPE = 0x14        # ONE byte: the one beside it is uninitialised
                          # memory (0xCD in a file measured), so reading the
                          # pair as a 16-bit type rejects real matrices


class Symbol(object):
    """One global in the compiled block."""

    __slots__ = ('name', 'offset', 'kind', 'rows', 'cols', 'value')

    def __init__(self, name, offset, kind, rows=0, cols=0, value=None):
        self.name, self.offset, self.kind = name, offset, kind
        self.rows, self.cols, self.value = rows, cols, value

    def __repr__(self):
        if self.kind == 'matrix':
            return '<%s %dx%d>' % (self.name, self.rows, self.cols)
        return '<%s %s>' % (self.name, self.kind)


def symbol_entry(name, matrix, flag=2):
    """One symbol entry, built to the grammar above. -> bytes.

    Building one is not the same as the calculator accepting it. Nothing
    here has been installed and run, so a program you assemble this way is
    an experiment, not a product. See examples/datagen/.
    """
    if len(name.encode('utf-16-le')) > 64:
        raise UnexpectedFormat('a symbol name is at most 32 characters')
    rows, cols = len(matrix), len(matrix[0])
    if any(len(r) != cols for r in matrix):
        raise UnexpectedFormat('the rows are not all the same length')
    body = b''.join(encode(x) for r in matrix for x in r)
    value = (struct.pack('<I', VALUE_TAG)
             + struct.pack('<HHIII', flag, MATRIX_TYPE, 2, rows, cols) + body)
    inner = (struct.pack('<II', NAME_RECORD, NAME_TAG)
             + name.encode('utf-16-le').ljust(64, bytes(1))
             + struct.pack('<III', 8, TYPE_TAG, 9)
             + struct.pack('<I', len(value)) + value)
    return struct.pack('<I', len(inner)) + inner


def _entry_start(data, limit):
    """Where the first symbol entry begins, or None.

    Found by shape rather than by a fixed offset: the first place whose
    name-record length and tag both match. In the file measured it is 56,
    but nothing says that is universal."""
    for o in range(12, limit - 16):
        if (struct.unpack_from('<I', data, o + 4)[0] == NAME_RECORD
                and struct.unpack_from('<I', data, o + 8)[0] == NAME_TAG):
            return o
    return None


def symbols(data, first=None, end=None):
    """The globals in a program's compiled block, in declaration order.

    Takes the whole .hpprgm: the block's end is where the source record
    begins. Pass `first` and `end` to walk a bare block instead. Returns []
    for a program with no block.

    Matrix values are decoded. Other types are reported with their type word
    and left alone: what is not measured is not guessed at.
    """
    if end is None:
        from hpkit import program
        _, _, src_start, _ = program.read(data)
        end = src_start - 8                  # the source record's own header
    o = _entry_start(data, end) if first is None else first
    if o is None:
        return []

    u32 = lambda k: struct.unpack_from('<I', data, k)[0]
    out = []
    while o + 16 <= end:
        total = u32(o)
        if not 0 < total <= end - o:
            break
        # A variable's entry starts with its name record. A function's is
        # wrapped in one more record first, so the name record is 8 bytes
        # further in. Both are followed the same way after that.
        head = o + 4
        if u32(head) != NAME_RECORD:
            head = o + 12
            if u32(head) != NAME_RECORD:
                break
        tag = u32(head + 4)
        if tag not in (NAME_TAG, FUNCTION_TAG, PROGRAM_TAG):
            break
        name = data[head + 8:head + 4 + NAME_RECORD].decode(
            'utf-16-le').rstrip(chr(0))
        if tag != NAME_TAG:
            out.append(Symbol(name, o, 'function' if tag == FUNCTION_TAG
                              else 'program'))
            o += 4 + total
            continue
        q = head + 4 + NAME_RECORD
        v = q + 4 + u32(q)                   # past the type record
        kind = data[v + 10]
        if kind == MATRIX_TYPE:
            rank, rows, cols = struct.unpack_from('<III', data, v + 12)
            body = v + 24
            try:
                value = [[decode(data[body + 8 * (i * cols + j):
                                      body + 8 * (i * cols + j) + 8])
                          for j in range(cols)] for i in range(rows)]
            except UnexpectedFormat:
                value = None
            out.append(Symbol(name, o, 'matrix', rows, cols, value))
        else:
            out.append(Symbol(name, o, 'type %02X' % kind))
        o += 4 + total
    return out


# ------------------------------------------------------------------- CLI

def _csv(path):
    rows = []
    with io.open(path, encoding='utf-8-sig') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            rows.append([float(x) for x in line.replace(';', ',').split(',')])
    return rows


def cli(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, path = argv[0], argv[1]

    def opt(flag, default=None):
        return argv[argv.index(flag) + 1] if flag in argv else default

    if cmd == 'read':
        m = read_hpmat(open(path, 'rb').read())
        print('%s: %d x %d' % (os.path.basename(path), len(m), len(m[0])))
        dest = opt('-o')
        lines = [','.join(repr(x) for x in row) for row in m]
        if dest:
            with io.open(dest, 'w', encoding='utf-8', newline='\n') as f:
                f.write('\n'.join(lines) + '\n')
            print('  wrote %s' % dest)
        else:
            for l in lines[:20]:
                print('  ' + l)
            if len(lines) > 20:
                print('  ... %d more rows' % (len(lines) - 20))
        return 0

    if cmd == 'write':
        dest = opt('-o')
        if not dest:
            print('missing -o output.hpmat')
            return 2
        m = _csv(path)
        data = write_hpmat(m)
        with open(dest, 'wb') as f:
            f.write(data)
        print('%s -> %s  (%d x %d, %d bytes)'
              % (path, dest, len(m), len(m[0]), len(data)))
        back = read_hpmat(data)
        same = all(abs(a - b) <= 1e-11 * max(1.0, abs(b))
                   for ra, rb in zip(back, m) for a, b in zip(ra, rb))
        print('  reads back correctly: %s' % same)
        print('  the file name decides which matrix: M0.hpmat .. M9.hpmat')
        return 0

    if cmd == 'nums':
        from hpkit import program
        data = open(path, 'rb').read()
        _, _, start, _ = program.read(data)
        if start <= program.HEADER_END:
            print('%s carries no compiled block' % os.path.basename(path))
            return 0
        syms = symbols(data)
        mats = [s for s in syms if s.kind == 'matrix']
        print('%s: %d-byte block, %d symbol(s), %d matrix/matrices, %d numbers'
              % (os.path.basename(path), start - program.HEADER_END, len(syms),
                 len(mats), sum(s.rows * s.cols for s in mats)))
        for s in syms[:14]:
            if s.kind == 'matrix':
                head = ', '.join(repr(x) for x in (s.value[0][:4] if s.value
                                                   else []))
                print('  %-24s %5d x %-4d  starts with %s'
                      % (s.name, s.rows, s.cols, head))
            else:
                print('  %-24s %s  (not decoded)' % (s.name, s.kind))
        if len(syms) > 14:
            print('  ... %d more' % (len(syms) - 14))
        return 0

    print('unknown command: %s' % cmd)
    return 2


if __name__ == '__main__':
    sys.exit(cli(sys.argv[1:]))
