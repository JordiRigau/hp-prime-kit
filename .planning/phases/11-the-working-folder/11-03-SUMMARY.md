---
phase: 11-the-working-folder
plan: 03
status: in progress; the GitHub leg is open
started: 2026-09-28
---

# Plan 03 summary: downloaded and tried

## The download

`C:\Users\jordi\Desktop\hp-prime-kit-main`, unzipped from tree 3607984 (the
working tree on 2026-09-27, through a temporary index), archived with
`git -c core.autocrlf=false -c core.eol=lf`: 1,020 entries, no CRLF, no
`.git`, `programs/` holding only its note, `doctor` passing. No `CLAUDE.md`
or `AGENTS.md` in any folder above it, and the Desktop is not a repository.

## The session

The user opened the folder in a new desktop-app session, "Aplicación reloj
analógico HP Prime" (`local_fa72e3c7`), on 2026-09-28, and wrote one
message, naming neither the kit nor its files: an app that draws an analog
clock showing the current time. It ran 59 turns. What was read from its
transcript, through the app's session tools, and from the folder:

| What 11-03 records | Seen | How it is known |
|---|---|---|
| `AGENTS.md` loaded by itself | yes | its first words, before any tool call: it would read the kit's documentation "como indica `AGENTS.md`" |
| `docs/llms.txt` read | yes | the transcript holds `llms.txt`'s own lines with the read tool's line numbers (`56 - [interface.two-themes]`) |
| which Python | 3.9.13 | `Python 3.9.13` in its tool output, beside a listing of the templates |
| how it started the tools | not visible | the search reaches tool output, not the commands typed; it read `docs/tools.md`'s line that `python hpprime.py` "works everywhere" |
| the program in `programs/` | yes | `programs/RELOJ/`: `RELOJ.txt`, `icon.png`, `RELOJ.hpappdir/`. Against the ZIP, no file of the kit changed, none went missing, and nothing was added outside `programs/RELOJ/` |
| `lint` | clean | its report, and here again: `1 file(s): 0 error(s), 0 warning(s)` |
| `run` | 22 calls | its report; here again `RJHORA(52507, 1) -> '14:35:07'` |
| `write` | `build` and `verify` instead, an app | its report, and here again: `programs/RELOJ/RELOJ.hpappdir: 0 difference(s)` |

It also installed the app on the emulator after checking that no `RELOJ`
was there, read the program back out of the installed app, cited facts by
identifier and label (`interface.offscreen-grob`, `deploy.ck-mirror`,
`deploy.compile-once-after-a-file-copy`), and said what nobody had
measured: that `Time` reads as decimal hours.

## For later phases, not this one

- **It asked nothing before writing.** One message from the user, then the
  whole app. Questions before PPL are KIT-07, Phase 13.
- **`hpprime pull --diff` does not reach an app's program.** The session
  said so and read the `.hpappprgm` out of the installed app by other means.
  A gap in the deploy tools, for Phase 14's deploy job.

## What the emulator showed, from the user on 2026-09-28

- **`RELOJ` opened only once its program had been compiled**, as the
  session's hand-over said to. `deploy.compile-once-after-a-file-copy` was
  measured on programs; this was an app installed with `hpprime install`.
- **Its time matched the PC's**, and the calculator's, "perfectly".
  `RELOJ` reads `Time` as decimal hours (14:30 is 14.5); read as
  hours.minutes-seconds, 14:35:07 would have shown 14:21. So, on the
  Virtual Calculator 2.4.15515, `Time` is decimal hours.
- **Every hand appeared at once**, where the program says "sincronizando
  segundos..." while it waits for a change of minute: `Time` carries the
  seconds.

The two `Time` findings and the app case of compile-once are candidates for
the reference, not written into it here: `Time.md` and `deploy.md` take a
measurement the harness can repeat, a row in `results.tsv`, and `RELOJ` is
not in the repository.

## Open

- **The GitHub leg**: once committed and pushed at the user's word, the
  ZIP from GitHub and `hpprime update` against it.
