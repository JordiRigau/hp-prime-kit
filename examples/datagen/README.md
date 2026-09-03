# Does the compiled block matter?

A program carrying large matrices is normally pasted into the Connectivity
Kit once by hand, because the calculator puts a compiled block in front of
the source and nothing here could generate one.

Decoding the block ([formats.md](../../docs/reference/formats.md#5-inside-the-block-the-symbol-entries))
turned that into a smaller question, and then into a different one:

> The calculator writes a block for **every** program it saves, code-only
> ones included. So it may be a cache it rebuilds rather than something the
> file must carry. If it is, generating one was never necessary -- and
> pasting was never necessary either.

Nobody has measured which. This is how to find out, in two steps.

## Step 1 -- make a real data program, without generating anything

`DATADEMO.txt` is an ordinary code program: two small matrices as literals,
and a function that reads them back.

```bash
hpprime write examples/datagen/DATADEMO.txt -o DATADEMO.hpprgm
```

Install it, then on **Home** type `DCHECK` (no parentheses). It must answer
**37**. Anything else, and the question changes: say what it answered.

Then bring the file back from
`Documents\HP Connectivity Kit\Calculators\<yours>\DATADEMO.hpprgm`. That
copy has been through the calculator, so it now carries a block the
calculator wrote -- a real data program, small enough to read end to end,
with contents we chose.

## Step 2 -- change the block, leave the source alone

With that file in hand, one number in the block is changed and nothing else.
Install it again and run `DCHECK`:

| It answers | What it means |
|---|---|
| the **new** number | the block is read, so a generated one would have to be right |
| **37** still | the block is a cache the calculator rebuilt: generating one is unnecessary, and so was pasting |
| an error | the calculator checks the block somehow, which is worth knowing on its own |

Either of the first two closes a line in
[README.md](../../README.md#status). The third opens a better one.

## Why the tools do not offer this yet

`numbers.symbol_entry()` builds an entry, and the tests read them back, so
the grammar is settled. What is not settled is where a new entry is spliced
into the table and which enclosing lengths that changes -- the block is the
symbol table, and the program itself is an entry in it, so an inserted global
sits inside one record and outside another.

`hpprime write` therefore refuses to add a block at all. A half-understood
container written to a calculator is how you get a file that loads and is
quietly wrong, which is the one failure this kit exists to prevent.
