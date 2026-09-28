---
phase: 11-the-working-folder
plan: 01
status: complete
completed: 2026-09-26
key_files:
  - programs/README.md
  - .gitignore
  - AGENTS.md
  - README.md
  - docs/start/01-setup.md
  - tests/test_docs.py
---

# Plan 01 summary: the folder

## What was built

- **`programs/README.md`**: what goes there, one folder per program, the
  source and the `.hpprgm` built from it, and that git keeps out of it.
- **`.gitignore`**: `programs/*` and `!programs/README.md`. `git
  check-ignore -v programs/CIRCLE/CIRCLE.txt` names line 22, `programs/*`.
- **`AGENTS.md` §2**: a person's programs in `programs/NAME/`, never at the
  root, in `examples/` or `templates/`; the tools run from the root with the
  path. When `python --version` prints no version, stop and send the person
  to step 1's Python row.
- **The README's "Working with an AI"**: download the ZIP or clone, open the
  folder in the assistant, say what you want; the only install is Python.
- **`docs/start/01-setup.md`**: the ZIP beside the clone, each with the
  folder it makes, and how to open a terminal in it on Windows 11. The `cd`
  and the sentence that leaned on it are gone.
- **`programs_problems` in `tests/test_docs.py`**: both rules present, the
  note present, and, where git answers, a program ignored, the note not, and
  nothing else in `programs/` tracked. In a download, with no git, the rules
  are still read. It is fed no rules and a tracked program in the test
  itself and must name all three. With `!programs/README.md` removed by
  hand it named the missing rule and the note git would ignore; restored,
  it passed. The link walk skips a person's own files in `programs/`.

## Deviations

None. The gone `SKILL.md` needed no check of its own: the link walk found
the README's and `docs/ai/prompts.md`'s links to it when it went, and
`hpkit/docs.py` already refuses the name in `docs/`.

## Added at the user's word, 2026-09-27

`hpprime new NAME` wrote `NAME.txt` where it ran, and the guided path ran it
at the root (`11-01-PLAN.md`, "Out of this plan"). Asked, the user chose to
point it at `programs/`:

- **`hpprime new`** writes `programs/NAME/NAME.txt`, or
  `programs/NAME/main.py` with `--python`, under the kit's own folder from
  wherever it runs; `-o DIR` keeps the old placement. Its hints give the
  paths from where it ran: the `.hpprgm` and the `.hpappdir` beside the
  source, `build` with `-o`, and forward slashes on Windows too: a hint
  with backslashes, copied into Git Bash, loses them. `--help` says where
  it writes.
- **Walked in a clean copy** of the working tree: `new`, `lint`, `run`,
  `write` of step 2, `build --ppl -o` and `verify` of step 4, `new
  --python` and `build -o` of step 5 and the probe's build, each landing in
  its folder under `programs/`; `CIRCAREA(2) -> 12.5663706144`, 0
  differences. A hint copied as printed ran in Git Bash through `./hpprime`.
- **`tests/test_cli.py`** points `cli.PROGRAMS` at its temporary folder, so
  a run leaves the kit as it found it, and walks the paths the hints print:
  20 checks, three of them new (the path in the hints, the binary beside
  the source, `-o DIR`).
- **The paths in the docs**: `docs/tools.md`'s `new`; the README's cycle,
  its comments moved to the table below it; steps 2, 4 and 5 of the guided
  path, down to the read-back in step 2 and the probe in step 5. The
  generic syntax lines of `docs/tools.md` keep their own paths.

## Results

```
hpprime docs --check     706 entries, 122 facts: 0 problem(s)
suite                    14,880 passed, 0 failed
```
