# -*- coding: utf-8 -*-
"""Tests for the Prime's internal number format.

The real test is not a round trip: reading and writing with the SAME mistake
gives a perfect round trip and a wrong answer. What verifies it is the
Rosetta stone -- a data program carries the compiled block before the source,
and the source is the same numbers in decimal -- so tens of thousands of
(bytes, value) pairs that nobody chose get compared.

Whatever is not found is skipped, so on a machine with no calculator this
does not fail.

    python tests/test_numbers.py
"""
from __future__ import unicode_literals
import glob, os, re, struct, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from hpkit import numbers as N
from hpkit import program as P

PASS, FAIL = [0], [0]


def ok(cond, msg, detail=''):
    if cond:
        PASS[0] += 1
        print('  ok    %s' % msg)
    else:
        FAIL[0] += 1
        print('  FAIL  %s%s' % (msg, ('  ' + detail) if detail else ''))


# Individual values, with the encoding taken by hand out of a real block.
KNOWN = [
    (0.0,        '0000000000000000'),
    (-76.0,      '9760000000000001'),
    (0.0006,     '0600000000000FFC'),
    (205.991225, '0205991225000002'),
    (2374.92,    '0237492000000003'),
    (9.1555,     '0915550000000000'),
]

# These must raise, not produce an invented number.
IMPOSSIBLE = [float('inf'), float('nan')]


def calculators():
    for name in ('Documents', 'Documentos'):
        base = os.path.join(os.path.expanduser('~'), name,
                            'HP Connectivity Kit', 'Calculators')
        if os.path.isdir(base):
            return [os.path.join(base, d) for d in sorted(os.listdir(base))
                    if os.path.isdir(os.path.join(base, d))]
    return []


def known_values():
    for value, hexa in KNOWN:
        raw = struct.pack('<Q', int(hexa, 16))
        v = N.decode(raw)
        ok(abs(v - value) <= 1e-12 * max(1.0, abs(value)),
           'decodes %s -> %r' % (hexa, value), 'gave %r' % v)
        ok(N.encode(value) == raw,
           'encodes %r -> %s' % (value, hexa),
           'gave %016X' % struct.unpack('<Q', N.encode(value))[0])

    for x in (1.0, -1.0, 1e-300, -1e300, 0.1, 1.0 / 3.0, 123456789012.0,
              -0.0007, 9.99999999999e99):
        ok(abs(N.decode(N.encode(x)) - x) <= 1e-11 * max(1.0, abs(x)),
           'round trip of %r' % x)

    for x in IMPOSSIBLE:
        try:
            N.encode(x)
            ok(False, 'rejects %r' % x)
        except N.UnexpectedFormat:
            ok(True, 'rejects %r' % x)

    try:
        N.decode(struct.pack('<Q', 0x0FFF000000000000))   # non-BCD mantissa
        ok(False, 'rejects a mantissa that is not BCD')
    except N.UnexpectedFormat:
        ok(True, 'rejects a mantissa that is not BCD')


def rosetta():
    """The compiled block against the source of the same file."""
    found = 0
    for calc in calculators():
        for p in sorted(glob.glob(os.path.join(calc, '*.hpprgm'))):
            try:
                data = open(p, 'rb').read()
                txt, _, start, _ = P.read(data)
            except Exception:
                continue
            block = data[P.HEADER_END:start]
            if len(block) < 1000:
                continue
            mats = list(re.finditer(
                r'EXPORT\s+(\w+)\s*:=\s*\[\[(.*?)\]\]\s*;', txt, re.S))
            if not mats:
                continue
            found += 1
            total = compared = reencoded = 0
            missing = []
            for m in mats:
                rows = [[float(x) for x in re.findall(
                    r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', r)]
                    for r in m.group(2).split('],[')]
                R_, C = len(rows), len(rows[0])
                flat = [x for r in rows for x in r]
                total += len(flat)
                o, located = 0, False
                while True:
                    o = block.find(struct.pack('<III', 2, R_, C), o)
                    if o < 0 or o + 12 + R_ * C * 8 > len(block):
                        break
                    base = o + 12
                    try:
                        vs = [N.decode(block[base + 8 * k:base + 8 * k + 8])
                              for k in range(R_ * C)]
                    except N.UnexpectedFormat:
                        o += 4
                        continue
                    if all(abs(v - s) <= 1e-9 * max(1.0, abs(s))
                           for v, s in zip(vs, flat)):
                        located = True
                        compared += len(flat)
                        reencoded += sum(1 for k, s in enumerate(flat)
                                         if N.encode(s) ==
                                         block[base + 8 * k:base + 8 * k + 8])
                        break
                    o += 4
                if not located:
                    missing.append(m.group(1))
            name = os.path.basename(p)
            ok(not missing,
               '%s: all %d matrices in the source are in the block'
               % (name, len(mats)), 'not located: %s' % missing[:3])
            ok(compared == total,
               '%s: %d numbers decoded and compared' % (name, compared))
            ok(reencoded == compared,
               '%s: %d of %d re-encode byte for byte'
               % (name, reencoded, compared))
            negs = sum(1 for m in mats for r in m.group(2).split('],[')
                       for x in re.findall(r'-\d+\.?\d*', r))
            ok(negs > 0, '%s: the comparison includes %d negatives'
               % (name, negs), 'without negatives the sign is not verified')
    if not found:
        print('  --    no program with a compiled block and matrices in its')
        print('        source: skipping the Rosetta stone check')


def hpmat_files():
    seen = 0
    for calc in calculators():
        for p in sorted(glob.glob(os.path.join(calc, '*.hpmat'))):
            data = open(p, 'rb').read()
            try:
                m = N.read_hpmat(data)
            except N.UnexpectedFormat as e:
                if 'complex' in str(e):
                    continue                    # not covered, and it says so
                ok(False, '%s: %s' % (os.path.basename(p), e))
                continue
            seen += 1
            rebuilt = N.write_hpmat(m)
            ok(rebuilt == data[:len(rebuilt)],
               '%s: %dx%d, round-trip identical'
               % (os.path.basename(p), len(m), len(m[0])),
               '%d bytes against %d' % (len(rebuilt), len(data)))
    if not seen:
        print('  --    no .hpmat files: skipping that part')

    # One made up here, which needs no calculator at all.
    m = [[1.0, -2.5, 0.0], [1e-9, 3.0, 123456.789]]
    d = N.write_hpmat(m)
    back = N.read_hpmat(d)
    ok(len(d) == 16 + 6 * 8, 'a 2x3 .hpmat is 16 + 6*8 bytes')
    ok(all(abs(a - b) <= 1e-11 * max(1.0, abs(b))
           for ra, rb in zip(back, m) for a, b in zip(ra, rb)),
       'a matrix written from scratch reads back the same')
    try:
        N.write_hpmat([[1.0, 2.0], [3.0]])
        ok(False, 'rejects rows of different lengths')
    except N.UnexpectedFormat:
        ok(True, 'rejects rows of different lengths')


def build_entry(name, matrix, flag=2):
    """One symbol entry, built to the grammar in docs/reference/formats.md.

    Building one here is what lets the walker be tested with no calculator
    anywhere. It says nothing about whether a calculator would accept a
    block built this way -- that is not measured.
    """
    rows, cols = len(matrix), len(matrix[0])
    body = b''.join(N.encode(x) for r in matrix for x in r)
    value = (struct.pack('<I', N.VALUE_TAG)
             + struct.pack('<HHIII', flag, N.MATRIX_TYPE, 2, rows, cols)
             + body)
    name_rec = (struct.pack('<I', N.NAME_RECORD)
                + struct.pack('<I', N.NAME_TAG)
                + name.encode('utf-16-le').ljust(64, b'\x00'))
    type_rec = struct.pack('<III', 8, N.TYPE_TAG, 9)
    value_rec = struct.pack('<I', len(value)) + value
    inner = name_rec + type_rec + value_rec
    return struct.pack('<I', len(inner)) + inner


def synthetic_block():
    ok = bad = 0
    a = [[1.0, -2.5], [0.0006, 123456.789]]
    b = [[7.0, 8.0, 9.0]]
    block = build_entry('ALPHA', a) + build_entry('BE_TA', b, flag=1)

    syms = N.symbols(block, first=0, end=len(block))
    ok_names = [s.name for s in syms] == ['ALPHA', 'BE_TA']
    if ok_names:
        ok += 1
        print('  ok    both symbols are found, in order')
    else:
        bad += 1
        print('  FAIL  got %r' % [s.name for s in syms])

    if len(syms) == 2 and (syms[0].rows, syms[0].cols) == (2, 2) \
            and (syms[1].rows, syms[1].cols) == (1, 3):
        ok += 1
        print('  ok    their dimensions survive')
    else:
        bad += 1
        print('  FAIL  dimensions came back wrong')

    if len(syms) == 2 and syms[0].value and all(
            abs(g - w) <= 1e-11 * max(1.0, abs(w))
            for gr, wr in zip(syms[0].value, a) for g, w in zip(gr, wr)):
        ok += 1
        print('  ok    the values decode back, negatives included')
    else:
        bad += 1
        print('  FAIL  the values did not come back')

    # A name shorter than the field, and one that fills more of it, both have
    # to survive the 64-byte padding.
    long_name = 'ABCDEFGHIJKLMNOP'
    one = N.symbols(build_entry(long_name, b), first=0,
                    end=len(build_entry(long_name, b)))
    if len(one) == 1 and one[0].name == long_name:
        ok += 1
        print('  ok    a 16-character name survives the padded field')
    else:
        bad += 1
        print('  FAIL  the long name came back as %r'
              % (one[0].name if one else None))
    return ok, bad


def real_block():
    """The same walk over your own files, if any of them carry a block."""
    ok = bad = seen = 0
    for calc in calculators():
        for p in sorted(glob.glob(os.path.join(calc, '*.hpprgm'))):
            data = open(p, 'rb').read()
            try:
                syms = N.symbols(data)
            except Exception as e:
                ok_ = False
                print('  FAIL  %s: %s' % (os.path.basename(p), e))
                bad += 1
                continue
            if not syms:
                continue
            seen += 1
            src = P.read(data)[0]
            # Comments are stripped first: an EXPORT inside one is not a
            # declaration, and counting it made this check disagree with
            # itself.
            src = re.sub(r'/\*.*?\*/', '', re.sub(r'//[^\n]*', '', src),
                         flags=re.S)
            # One EXPORT can declare several names: EXPORT A, B, C; -- so the
            # whole statement is taken and split, not just its first word.
            declared = set()
            for stmt in re.findall(r'EXPORT\s+([^;]+);', src):
                for part in stmt.split(','):
                    m = re.match(r'\s*(\w+)', part)
                    if m:
                        declared.add(m.group(1))
            got = [s.name for s in syms]
            missing = [n for n in got if n not in declared]
            if not missing:
                ok += 1
                print('  ok    %s: %d symbol(s), every one of them declared '
                      'in the source' % (os.path.basename(p), len(syms)))
            else:
                bad += 1
                print('  FAIL  %s: %r are in the block but not in the source'
                      % (os.path.basename(p), missing[:3]))

            # In a program whose globals are all matrices, the block is in
            # declaration order too.
            mats = [s.name for s in syms if s.kind == 'matrix']
            if len(mats) == len(syms) and len(mats) > 1:
                order = [n for n in re.findall(r'EXPORT\s+(\w+)\s*:=', src)
                         if n in set(mats)]
                if order == mats:
                    ok += 1
                    print('  ok    %s: and in the order the source declares '
                          'them' % os.path.basename(p))
                else:
                    bad += 1
                    print('  FAIL  %s: the order differs'
                          % os.path.basename(p))
    if not seen:
        print('  --    no program with a compiled block: skipping')
    return ok, bad


def main():
    print('-- the number, against known encodings')
    known_values()
    print('\n-- the Rosetta stone: compiled block against source')
    rosetta()
    print('\n-- .hpmat files')
    hpmat_files()
    print('\n-- the compiled block, walked as symbol entries')
    a, b = synthetic_block()
    PASS[0] += a
    FAIL[0] += b
    a, b = real_block()
    PASS[0] += a
    FAIL[0] += b
    print('\nPASS: %d   FAIL: %d' % (PASS[0], FAIL[0]))
    return 1 if FAIL[0] else 0


if __name__ == '__main__':
    sys.exit(main())
