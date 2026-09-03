# The file formats

This is the most technical page in the kit and the one you least need to
start. To write your first program you need none of it -- the
[guided path](../start/02-first-program.md) does the job in three commands.
Come here when something does not add up, when you want to move a lot of
data, or out of curiosity.

None of this is documented by HP. It was worked out by measuring real files
written by the Connectivity Kit and verified by byte-for-byte reconstruction.

**The practical conclusion**: the PPL source sits inside **verbatim**, as
UTF-16LE. Not compressed, not encrypted. It can be read and written from the
PC, so generating a program stops being "create it by hand in the
Connectivity Kit and paste the text in". Mind the last step, which has a trap
of its own -- see [deploy.md](deploy.md).

---

## 1. The `.hpprgm` container

A nested TLV container, all little-endian:

```
offset  contents
------  ----------------------------------------------------------
0       7C 61 8A B2                       magic
4       FE FF FF FF   00 00 00 00         preamble
12      [u32 length][length bytes]        records, nested
...     (optional) compiled block
...     [u32 length][u32 tag][UTF-16LE source][NUL]
...     trailer
```

Every record is a 4-byte length followed by that many bytes. Inside the
payload, some records carry a 4-byte tag before their children and some do
not -- which is why walking the tree by "take the last child" **does not
work**.

### How the source is located

The shape of the source record is firm:

```
[u32 length][u32 tag][UTF-16LE text][NUL]
```

So that is what is searched for: walk the offsets, keep those whose block
decodes as UTF-16LE, ends in NUL and is nearly all printable text, and take
the largest. The records to patch when the text changes are **the ones that
end exactly where it ends**.

Two details that look minor and are not:

- **The sweep is byte by byte, not in steps of 4.** When a compiled block
  sits before the source, its size is not a multiple of 4 and the source
  record ends up unaligned -- in one data program it starts at an odd
  offset.
- **The trailer is not constant.** It is 1008 bytes in most files, but the
  factory apps contradict even that, and it can carry **metadata inside**:
  between two files with the same source, 15 bytes of difference appeared
  there, with UTF-16 text in them. So nothing is assumed: what follows the
  source is preserved as it is when rewriting, and when **generating**, the
  template's trailer is copied. The calculator accepts the result, but it
  does mean generating is not byte-exact for an arbitrary file: it is exact
  for the header and the source, which is what the writer builds.

### Line endings

The Connectivity Kit stores **the editor's buffer**: **LF** endings and **no
trailing newline**. A normal PC text file does have a trailing newline, so
generating has to drop one to come out byte for byte like the CK would write
it. HP's factory apps, on the other hand, carry **CRLF** inside: the
container accepts both.

## 2. The compiled block

A program with only code, **as the Connectivity Kit writes it**, is header +
source + trailer, with the source starting at offset **152 exactly**.
Anything above 152 is compiled block, and that is the test for whether a file
can act as a template. (A looser threshold lets through the small blocks the
calculator adds -- 96, 184, 360 bytes -- and then what you generate comes out
exactly that many bytes short.)

A program that declares large matrices also carries a block **before** the
source with the numbers already in the calculator's internal format. It shows
in the size:

| Program | Source | File | Compiled block |
|---|---|---|---|
| a code program | 36 KB | 37 KB | — |
| a data program (43,796 numbers) | 632 KB | 1,001 KB | 367 KB |

That block is what makes a data program open **instantly** on the calculator
that receives it, with no compile wait. Generating one is not solved:
`hpprime write` refuses a template that carries one, because changing its
source would leave it out of step. In practice that does not get in the way:
data is pasted once and never changes, while code, which does change, is
generated and dragged over.

### Who writes what, and why it matters

There are **two producers** of `.hpprgm` files, and they do not write the
same thing:

| Written by | What it puts in | Same source, measured |
|---|---|---|
| The **Connectivity Kit** | the source only | 38,888 B |
| The **calculator**, on saving | source **+ its compiled block** | 42,078 B (3,190 of block) |

So the compiled block is not only in data programs. The calculator adds it to
any program it saves, code included. Both read equally well and both
round-trip exactly. But **to generate, the template has to be one from the
Connectivity Kit**: the calculator's carry a compiled block that would stop
matching the new source, and the writer rejects them for that reason.

## 3. The internal number

What is inside the compiled block is not opaque any more. **A number is 8
bytes**, little-endian; read as a 64-bit integer:

```
bits  0..11   decimal exponent, 12-bit two's complement
bits 12..59   12 BCD mantissa digits, most significant at the top
bits 60..63   sign: 0 positive, 9 negative     (the usual BCD convention)

value = d1.d2d3...d12 x 10^exponent            and zero is all zeros
```

Real words from a real block:

| Word | Sign | Mantissa | Exp | Value |
|---|---|---|---|---|
| `9760000000000001` | 9 | `760000000000` | 1 | **−76** |
| `0600000000000FFC` | 0 | `600000000000` | −4 | **0.0006** |
| `0205991225000002` | 0 | `205991225000` | 2 | **205.991225** |
| `0915550000000000` | 0 | `915550000000` | 0 | **9.1555** |

### How it was worked out, which is what makes it trustworthy

With a **Rosetta stone**, not by guessing. A data program carries the
compiled block **before the source**, and the source is *the same numbers*
written in decimal. One file therefore gives tens of thousands of
(bytes, value) pairs that nobody chose:

| | |
|---|---|
| Matrices located in the block | **56 of 56** |
| Numbers decoded and compared with the source | **44,718, exact** |
| Re-encoded and compared **byte for byte** | **44,718 of 44,718** |
| Negatives inside that comparison | **1,616** |

The negatives are the ones that mattered: a first attempt put a `1` in the
sign nibble, the round trip failed on exactly the negatives, and that is how
the `9` was established. Without negatives in the sample the mistake would
have gone through.

Redo it against your own files with `python tests/test_numbers.py`.

## 4. What that opens: `.hpmat`

The `.hpmat` files of the `M0`..`M9` matrices are **the same number format**
with a 16-byte header:

```
00  01 00      constant in everything observed
02  14 80      type: 8014 real, 8094 complex (16 bytes per element)
04  u32 = 2    rank: 2 = matrix
08  u32        rows
12  u32        columns
16  ...        the elements, row by row, 8 bytes each
```

With that, a whole matrix goes to the calculator **as a file**, with nothing
pasted and no program source involved:

```bash
hpprime matrix read  M1.hpmat -o data.csv
hpprime matrix write data.csv -o M0.hpmat
```

The file name decides: `M0.hpmat` is the matrix `M0`. Drag it over like a
program, and from PPL copy it wherever you need in one line. **Complex**
matrices are reported as an explicit error, not as invented numbers: they are
not covered.

Verified: nine real `.hpmat` files from a G2 read and rewrite **byte for byte
identical**, header included.

## 5. Inside the block: the symbol entries

**The block is the program's symbol table**, and the program itself is an
entry in it. That is the thing to hold on to, because it explains the rest:

```
[u32 len][u32 tag]                 the symbol table
   [entry]  a global               name tag 0040018B
   [entry]  a global
   ...
   [entry]  Main                   name tag 0040008B
              its value contains [u32 len][u32 tag][source UTF-16LE][NUL]
```

So the source record is nested inside the `Main` entry, a code program's
table has one entry, and what looks like "a block in front of the source" is
just the globals coming before `Main` in that table. Measured: in a code
program the source record ends exactly where the `Main` entry ends, and both
end where the table's own record does.

The entries themselves are one per exported **variable**, in the order the
source declares them. Functions other than `Main` are not in the table.

Each entry is three TLV records, the same shape as the container around them:

```
[u32 total]                                  everything below this field
  [u32 68][u32 0040018B][name UTF-16LE, zero-padded to 64 bytes]
  [u32 8][u32 00800185][u32 9]               9 in every entry measured
  [u32 len][u32 00C0018C][value]
```

and a real matrix value is

```
[u16 flag][u16 0014][u32 rank=2][u32 rows][u32 cols][rows*cols numbers]
```

with each number in the 8-byte format of §3. The name field is fixed at 64
bytes, so a name shorter than 32 characters is padded with zeros.

**How this is verified.** The walk is run over a 367 KB block from end to
end: 72 entries, finishing exactly where the source record begins, recovering
the same 72 names the source declares, in the same order. A grammar that is
wrong does not land on the last byte.

```bash
hpprime matrix nums PROG.hpprgm
```

reports every symbol, with the matrices decoded:

```
PROG.hpprgm: 367405-byte block, 72 symbol(s), 56 matrix/matrices, 44718 numbers
  ST                          51 x 11    starts with 0.0, 0.0006, 0.0006, 0.001
  IX                          44 x 4     starts with 0.01, 1.0, 35.0, 3.0
  MD                       type FF16  (not decoded)
```

### What is still not decoded

- **The other value types.** Matrices are `0014`. Lists, strings and numbers
  come out as `0012`, `001F`, `0100` and `FF16` in the files measured, and
  their payloads are reported but not read. Each is one Rosetta stone away:
  a program declaring one global of that type, installed and read back.
- **The leading `flag`** of a matrix value, which is 1 in some symbols and 2
  in others. Both are 2-D real matrices, so it is not the rank.
- **Where a new entry is spliced in, and what then has to grow.** Building
  an entry is solved -- `numbers.symbol_entry()` does it and the tests read
  them back -- but an entry inserted ahead of `Main` sits inside the table
  record and outside the `Main` one, and which enclosing lengths that changes
  is not established. `hpprime write` therefore does not offer it: a
  half-understood container written to a calculator is how you get a file
  that loads and is quietly wrong.
- **The u32 at offset 44**, which is 0 in a program with no globals and
  varies (1, 2, 4, 5, 7, 8, 9, 11, 12) in ones that have them, with no
  relation to how many. Unknown.
- **Whether the block matters at all.** The calculator writes one for every
  program it saves, so it may simply be a cache it rebuilds. If it is,
  generating one was never necessary. [examples/datagen/](../../examples/datagen/)
  is the experiment that would tell.

## 6. Other files on the calculator

The CK mirror folder holds more than programs. What this kit reads and what
it does not, so you do not waste time:

| | What it is | Read by the kit? |
|---|---|---|
| `.hpprgm` | a program | **yes** |
| `.hpappdir/` | an app | **yes**, and its `.hpappprgm` as a program |
| `.hpmat` | one of the `M0`..`M9` matrices | **yes** (the real ones) |
| `.hplist` | one of the `L0`..`L9` lists | no: a different header (`FE FF 16 00`) and variable-size elements with a type tag. An empty list is 8 bytes |
| `.hpsettings`, `settings` | settings; `settings` carries the calculator's identifier (its serial number, if physical) | no |
| `.hpexammode` | an exam mode | no |

None of these starts with the `7C 61 8A B2` magic: **they are not the TLV
container**, so the reader rejects them at once instead of inventing
anything.

## 7. How this is verified

A round trip is not enough on its own: reading and writing with the **same**
mistake gives a perfect round trip and a wrong answer. That happened here --
an early version carried 88 bytes of header along as though they were source,
and the round trip came out identical anyway.

What verifies it is rebuilding a program **from a different-sized template**
and comparing with what the Connectivity Kit wrote:

| Test | Result |
|---|---|
| Round trip of a code program (37 KB) | identical |
| Round trip of a data program (1 MB, with compiled block) | identical |
| Round trip of an `.hpappprgm` | identical |
| Round trip of the factory apps (with CRLF) | identical |
| An 11,918-character program rebuilt from an 18,007-character template | **byte for byte equal to the CK's file** |
| A 579-character factory app from the same template | **byte for byte equal** |

The last two are the ones that count: they change the size, so they exercise
the length arithmetic.

`python tests/test_program.py` repeats it against whatever binaries you have
on your machine.
