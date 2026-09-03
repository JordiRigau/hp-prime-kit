# Templates

Binary skeletons the kit needs, and the starters it writes for you.

| | | |
|---|---|---|
| `code.hpprgm` | 1.8 KB | a code container written by the Connectivity Kit, with a placeholder source. `hpprime write` puts your source into a copy of it |
| `app/` | 4 files | the three wrappers an app is made of, plus the second descriptor |
| `starters/` | 2 files | what `hpprime new` writes: a PPL program and a Python app entry point |

## Why these are files and not generated

The `.hpprgm` container cannot be built from nothing: the header and trailer
carry structure this kit can read but not synthesise. So one real container
is kept, and its source is replaced. The same goes for the app wrappers.

That is not a limitation in practice, because **none of them carries a name
inside**. One code template works for every program, and one set of wrappers
for every app.

## The app wrappers

| File | | What it is |
|---|---|---|
| `app/python.hpapp` | 188 B | descriptor of an app **based on the Python app** |
| `app/blank.hpapp` | 124 B | descriptor of an app created with **Base App: None**, which is the shape a PPL app has |
| `app/note.hpappnote` | 2 B | the empty note |
| `app/program.hpappprgm` | 1152 B | the empty program, with its `Main` |

Both descriptors come from apps that start correctly on a G2, and neither
carries text inside -- that has been checked -- so they bring nothing from the
app they came from beyond its settings.

**The last four bytes of a `.hpapp` are the startup view**, and they are the
whole reason these files are here:

```
app/python.hpapp   ...  08 00 00 00   85 06 C9 00   01 00 00 00
factory &Python    ...  08 00 00 00   85 06 C9 00   03 00 00 00
                            length       tag           view
```

`01` is the app's own screen; `03` is the Python console. The calculator
**rewrites the wrappers when you leave an app**, saving the view you were in,
so a folder that has been to the calculator and back can carry `03` home with
it. `hpprime build` rebuilds them from here every time, and `hpprime verify`
tells you when a folder has drifted.

Full detail in [`docs/reference/apps.md`](../docs/reference/apps.md).

## If you need your own code template

You should not, but if the shipped one ever fails you:

```bash
hpprime templates "C:\Users\you\Documents\HP Connectivity Kit\Calculators"
```

That says which of your files qualify. If none do, create a program **inside
the Connectivity Kit** and copy it out before sending it to the calculator.
Why that is harder than it sounds:
[`docs/reference/deploy.md`](../docs/reference/deploy.md).
