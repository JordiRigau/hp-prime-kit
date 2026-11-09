# A calculator on its USB cable

Facts about reaching a physical HP Prime G2 from a PC over its cable, with no
other software in the way: what it is showing, its keys and its programs. Each
has an identifier, says how it is known, and is stated here once.

```bash
hpprime screen -o now.png     # what it is showing, as a picture
hpprime press 2 + 2 enter     # its keys
hpprime type CIRCAREA --enter # a name, with the keys worked out
hpprime send CIRCLE.txt       # a program, installed
```

All of it was measured on one G2 on firmware 2.4.15515, from Windows. HP
documents none of it, so a firmware update can change any of it: `screen`, `press`
and `type` warn on any other build, and `send` refuses unless told otherwise.

---

<a name="usb.device"></a>
## A G2 is a HID device, with reports of 1024 bytes

| | |
|---|---|
| Identifier | `usb.device` |
| Kind | rule |
| Known from | G2 |

Its numbers are vendor `03F0`, product `2441`, version `4850`, usage page
`0081`, usage `0082`. Reports are 1024 bytes in both directions, and there are
no feature reports. On Windows each read and write is 1025 bytes, the first of
them the report number, 0, and a frame shorter than that is padded with zeros,
as Windows requires. HID needs no driver, so the standard library reaches it
through `hid.dll`.

**Evidence.** Read on 2026-11-04 with `HidD_GetAttributes` and `HidP_GetCaps`,
with the Connectivity Kit closed, from a G2 on firmware 2.4.15515. Other
product numbers are given for a G1 (`0441` and `1541`, in `BeatSkip/PrimeDev`),
and none was measured.

<a name="usb.one-program-at-a-time"></a>
## While the Connectivity Kit runs, nothing else can open the calculator

| | |
|---|---|
| Identifier | `usb.one-program-at-a-time` |
| Kind | rule |
| Known from | G2 |

The CK opens the device without sharing it, for as long as it runs, whether or
not any of its windows is using the calculator. Any other program is refused
with Windows error 32, a sharing violation, even one that asks for no access
rights, and `hpprime screen` and `hpprime press` say so and exit 1. Closing the
CK frees the device. `taskkill /IM ConnectivityKit.exe`, without `/F`, asks it
to close rather than killing it. A CK opened afterwards finds the calculator
again.

**Evidence.** Measured on 2026-11-03 and 2026-11-04 on a G2 on firmware
2.4.15515: `CreateFile` answered error 32 with the CK running and succeeded 1.5
s after it closed, each time. The CK listed the calculator again each time it
was reopened, after screen requests, keys and the protocol change of
[usb.newer-framing](#usb.newer-framing).

<a name="usb.frames"></a>
## A message is a sequence number and a command, and a reply adds a size

| | |
|---|---|
| Identifier | `usb.frames` |
| Kind | rule |
| Known from | G2 |

A request is `00`, the command, then its argument. A reply is `00`, the
command, `03`, a size of four bytes, big-endian, and the data; each later
report is the next sequence number, `01`, `02`, and more data. The size is what
ends a reply: the rest of the last report is leftover bytes, not zeros. A frame
starting `FE` or `FF` is not data, and one can be waiting when the CK closes.

`00 FA` asks for information. The reply holds 108 bytes, and it is read from
the end: at N-36 the build, two bytes, low byte first; at N-32 the version,
`V2.060.650`; at N-16 the serial number.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515: `00 FA` was
answered within 1 ms by `00 FA 03 00 00 00 6C`. The build read 15515, which is
the firmware's revision, and the serial was the one in the `settings` file of
that calculator's mirror folder
([deploy.which-calculator-is-which](deploy.md#deploy.which-calculator-is-which)).
The offsets come from `BeatSkip/PrimeDev`. `debrouxl/hplp`, written for firmware
of 2013, expects `01` where this one sends `03`.

<a name="usb.screen"></a>
## The screen comes back as a PNG whose greys are colours

| | |
|---|---|
| Identifier | `usb.screen` |
| Kind | rule |
| Known from | G2 |

`00 FC 08` asks for it. The reply's data is two bytes of checksum,
`08 FF FF FF FF`, then a PNG: 320x240, greyscale, depth 16. Those 16 bits are
not a grey. Each is a colour, `xRRRRRGGGGGBBBBB`, low byte first, which is the
opposite of what a PNG means by 16 bits, so white is stored `FF 7F`. A viewer
shows the file in false colours; `hpprime screen` converts it to an ordinary
PNG. It is 7 to 8 KB in 8 or 9 reports and takes 0.4 to 2.8 s, and asking
changes nothing on the screen. Only `08` was asked for.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515, in the
framing of [usb.frames](#usb.frames). The order was settled from what the
screen showed: the white background is stored `FF 7F` and the blue title bar
`53 11`, which is blue only with the low byte first and blue in the low bits.
Decoded that way the picture looked the same as the CK's Project window, and
its clock read the time of the request. Consecutive requests gave identical
replies. The layout comes from a decoder Cyrille de Brebisson posted on
`debrouxl/hplp` issue 6, where the false colours are reported.

<a name="usb.keys"></a>
## A key is two reports, and it acts when the second arrives

| | |
|---|---|
| Identifier | `usb.keys` |
| Kind | rule |
| Known from | G2 |

The first is `00 EC 03 00 00 00 01` and the key's code, from
[interface.key-codes](interface.md#interface.key-codes). The second is `01` and
nothing else. After the first alone the screen does not change; the key acts
when the second arrives. Keys sent without one wait: two of them, with screen
requests between them, acted together on the next frame starting `01`, and that
frame does nothing when no key is waiting. Why it does this is not known.

Nothing acknowledges either report, so only the screen says whether a key
acted. `hpprime press` asks for the information first, which is answered, so a
dead link is an error, and past that it can say only that it sent the keys.

The calculator sets the pace. Sent 0.25 s apart, one or two keys went at once,
and in a longer run a report waited while the calculator dealt with the key
before it, 2.3 to 2.9 s a key. So a command that has returned does not show that
its keys have acted, and a screen request right after a key takes up to 2.8 s
rather than 0.4 s.

Measured, on Home: ▲, ▼, the digits, `+`, `( )`, `Enter`, `Esc`, `Alpha`, `Shift`,
`Home`, `CAS` and the keys in [usb.letters](#usb.letters). Not measured: any other
key, another app, a key read by a running program, another gap, and a run of more
than 26 keys.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515, comparing
the screen pixel by pixel before and after each step. `00 EC 03 00 00 00 01 0C`
alone changed nothing, and a following `01` moved the selection in Home's
history down one stop. Two more ▼ moved it two stops and two more left the
history, as predicted, and the screen matched where it started but for
[usb.status-area](#usb.status-area). `2`, `+`, `2` put `2+2` on the entry line
and `Enter` answered `4`. `hpprime press up` selected that `4`, and `hpprime
press down` let it go. With each report timed, four arrows took 1 ms for every
first report and 0.001, 1.567, 2.677 and 2.675 s for the second; 26 keys took
71.5 s, 20 took 53.7 s, nine took 20.8 s, and two took 0.5 s. On 2026-11-05 `( )` after
a name put a pair of parentheses on the entry line, and `2` went inside it. The command
`EC` comes from `debrouxl/hplp`, written for firmware of 2013, which sends no second
report.

<a name="usb.letters"></a>
## A letter is Alpha, or Shift and Alpha, and then the key that carries it

| | |
|---|---|
| Identifier | `usb.letters` |
| Kind | rule |
| Known from | G2 |

`Alpha` and the key give the capital, and `Shift`, `Alpha` and the key give the
small letter, one letter at a time. `Alpha` twice holds capitals and `Shift`,
`Alpha`, `Alpha` holds small letters, with `↑AZ` or `↑az` at the top left, until
`Alpha` lets go. `Shift`, `Alpha`, `Shift`, `Alpha` looks as if it should hold
small letters, and holds capitals. `Esc` empties the entry line and leaves a hold
on, and a digit's key under a hold is a letter. `hpprime type` takes whichever is
fewer keys, at the pace of [usb.keys](#usb.keys), and always lets go.

| Letter | Key | Code |
|---|---|---|
| A | `Vars` | 14 |
| B | Mem | 15 |
| C | Units | 16 |
| D | `x t θ n` | 17 |
| E | `a b/c` | 18 |
| F | `x^y` | 20 |
| G | `SIN` | 21 |
| H | `COS` | 22 |
| I | `TAN` | 23 |
| J | `LN` | 24 |
| K | `LOG` | 25 |
| L | `x²` | 26 |
| M | `+/-` | 27 |
| N | `( )` | 28 |
| O | `Eval` | 29 |
| P | `EEX` | 31 |
| Q | `7` | 32 |
| R | `8` | 33 |
| S | `9` | 34 |
| T | `÷` | 35 |
| U | `4` | 37 |
| V | `5` | 38 |
| W | `6` | 39 |
| X | `×` | 40 |
| Y | `1` | 42 |
| Z | `2` | 43 |

**Evidence.** Measured on 2026-11-05 on a G2 on firmware 2.4.15515, on Home. Under
each hold these keys, in this order, gave `ABCDEFGHIJKLMNOPQRSTUVWXYZ` and
`abcdefghijklmnopqrstuvwxyz` on the entry line, read with `hpprime screen`, and
`Alpha` then `3` added a 3 after each. On 2026-11-04 the letter-at-a-time forms
gave `VERSION`, `SELF1`, `Gallery` and `Gallerx`, each read before `Enter`.
`hpprime type` gave `Gallery` and `1234567890`.

<a name="usb.start-by-name"></a>
## A name typed over USB and then Enter starts what it names

| | |
|---|---|
| Identifier | `usb.start-by-name` |
| Kind | rule |
| Known from | G2 |

On Home, a name typed with keys and `Enter`, which `hpprime type NAME --enter`
sends, does what a person's typing does. `SELF1`, a program that sums the squares
from 1 to 10, answered 385. `VERSION` answered its string. `Gallery`, the function
exported by the program of the app that was active, has an empty body and answered
0. A name takes no parentheses
([ppl.home-no-parentheses](ppl.md#ppl.home-no-parentheses)).

A name Home does not know is not always refused, so read the answer and not just
that there was one. `Gallerx` opened a syntax error dialog, which `Esc` closes, and
a second `Esc` clears the entry line. `SELF4`, once no program held it, was read as
`S*E*L*F4`, the entry changed on the screen to say so, and answered that `F4` is
not defined in Symbolic view. And Home can answer 0
([deploy.compile-once-after-a-file-copy](deploy.md#deploy.compile-once-after-a-file-copy)),
so a 0 means nothing without a control like that wrong name.

`Esc` also leaves a selection in the history, which has to go before typing.

That is as far as it was measured. Neither a program's own screen nor its
`GETKEY` under keys sent this way has been watched.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515 with the
Gallery app active, reading the screen after each `Enter`. `SELF1` comes from
`examples/selftest/SELFTEST.txt`, built with `hpprime write` and sent as in
[deploy.content-library-send](deploy.md#deploy.content-library-send), and it ran
with no key pressed by hand. The source `EXPORT Gallery() BEGIN END;` was read
from the copy of the app in the CK's content library. `S*E*L*F4` was measured on
2026-11-05 with the TAULES app active and the program gone from the CK's tree, and
`hpprime type VERSION --enter` answered the string above on the same day.

<a name="usb.program-message"></a>
## A program travels as its source, compressed, without its container

| | |
|---|---|
| Identifier | `usb.program-message` |
| Kind | rule |
| Known from | G2 |

Over the cable a program is not its `.hpprgm` file. The message is `F7 03`, a
size of four bytes big-endian, which is the length of the compressed part plus
4, the uncompressed length as four bytes low byte first, and a zlib stream.
Uncompressed, that stream is:

| Bytes | What |
|---|---|
| 1 | the type, `06` for a program |
| 1 | the name's length in bytes |
| 2 | a checksum, low byte first |
| as many as it takes | the name, UTF-16 low byte first, with no extension |
| as many as it takes | the source, UTF-16 low byte first, then `00 00` |

The checksum is a CRC-16 with polynomial `1021`, starting from 0, over `F7 03`,
the uncompressed length as four bytes big-endian, and the uncompressed part with
its checksum bytes at 0. Neither the container nor the compiled block of
[formats.container](formats.md#formats.container) travels: the calculator makes
those itself.

**Evidence.** Read on 2026-11-04 on a G2 on firmware 2.4.15515 from `SELFTEST` as
the calculator sent it, in [usb.file-request](#usb.file-request): it began
`F7 03 00 00 02 E8 00 09 00 00 78 01`, and held 2,304 bytes uncompressed. The
same layout built from `examples/selftest/SELFTEST.txt` gave those 2,304 bytes
exactly, checksum included. `debrouxl/hplp`, for firmware of 2013, describes the
same uncompressed part with no compression and `01` for `03`, and
`BeatSkip/PrimeDev` the compressed form for an app.

<a name="usb.send-program"></a>
## A program sent over USB is installed and compiled, with no sign on the screen

| | |
|---|---|
| Identifier | `usb.send-program` |
| Kind | rule |
| Known from | G2 |

With the CK closed, the message of
[usb.program-message](#usb.program-message), in the framing of
[usb.frames](#usb.frames), installs the program under the name it gives. A
program of that name is replaced. Its exported functions then answer on Home,
with no compile by hand. Nothing acknowledges the message and nothing shows on
the screen, so only running the program or reading it back says that it arrived.

Measured: a program of 310 bytes in one report, one of 256 replacing it, and one
of 16,558 replacing that, in six reports. A report `01` followed each, as it does
a key, and whether a file needs it was not separated. Not measured: an app, a
note or any other kind of file, a name that something else holds, and a longer
message. `hpprime send` does this for programs, from a source or from a built
`.hpprgm`, whose source is what travels, and it says when a message is longer
than any measured.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515. `SELF4`,
exported by a program sent this way, answered 1729, then 1730 and 1731 as each
version replaced the last, typed as in
[usb.start-by-name](#usb.start-by-name). Read back through the CK
([deploy.read-it-back](deploy.md#deploy.read-it-back)), the third was the source
sent, 8,269 characters, with a compiled block. Everything the CK had mirrored
before the first send was compared with the same after the third: the program was
new, and the source of the two other programs compared was unchanged, with bytes
changed only in the compiled block of one and the trailer of the other. `hpprime
send` itself then replaced it twice, from a source and from a built `.hpprgm`, and
`SELF4` answered 1732 and 1733.

<a name="usb.compile-check"></a>
## Whether a program compiled shows when its name is typed on Home

| | |
|---|---|
| Identifier | `usb.compile-check` |
| Kind | rule |
| Known from | G2 |

A program that does not compile is sent like any other, and nothing shows on the
screen. Its function is then unknown to Home, which reads the name as a product of
letters and answers whatever that comes to, so a program that compiled is told from
one that did not by the line Home writes: `ZCOK` and its number against `Z*C*B*A*D`
and 0. Part of the name can be a command, and then the answer is an error: `ZRLU` came
back as `Z*R*LU`. That makes a question about what compiles something a G2 can answer with no
hand on it, given a function that returns a number nothing else would and a name
not used before, and a control of each kind. A program sent after one that did
not compile compiles as usual. What a program that does not compile leaves of an
earlier one of the same name was not measured.

`hpprime send` runs the linter first and stops on an error. `hpprime send --no-lint`
sends anyway, which is how to ask the calculator about a rule of the linter.

**Evidence.** Measured on 2026-11-05 on a G2 on firmware 2.4.15515, with the TAULES
app active, sending under one name and replacing it each time. `EXPORT ZCOK() BEGIN
RETURN 4700; END;` answered 4700. `ZCBAD`, whose `IF` closes with `ENDIF;`, which
does not exist ([ppl.no-end-keywords](ppl.md#ppl.no-end-keywords)), opened no dialog,
came back as `Z*C*B*A*D` and answered 0. `ZCOKB`, sent next, answered 4702.

The test programs are in [docs/evidence](../evidence/README.md#usb.compile-check).

<a name="usb.file-request"></a>
## Asking for a file was answered once, and why not since is not known

| | |
|---|---|
| Identifier | `usb.file-request` |
| Kind | rule |
| Known from | G2 |

`F8 03`, a size of four bytes big-endian, the type, the name's length, a checksum
low byte first and the name ask for a file. The checksum leaves out the last 6
bytes. Once, with a result shown full screen, the calculator answered within
0.19 s with the message of [usb.program-message](#usb.program-message), and that
view closed, whether because of the request or not. Since then the same bytes
have had no answer: at Home, with a selection or without, followed by a report
`01` or not, and with the CK just closed. To read a program back, use the CK:
[deploy.read-it-back](deploy.md#deploy.read-it-back).

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515, with the bytes
`00 F8 03 00 00 00 14 06 10 91 6E` and the name `SELFTEST`. Requests for
information and for the screen were answered throughout, and the clock went on
moving, so the calculator was alive. The layout comes from `debrouxl/hplp`,
written for firmware of 2013.

<a name="usb.status-area"></a>
## Keys over USB stop the clock and the battery being drawn

| | |
|---|---|
| Identifier | `usb.status-area` |
| Kind | rule |
| Known from | G2 |

Once a key has acted, the top right of the title bar, x 282 to 318 and y 1 to
16, is left blank. The calculator is not hung: the entry cursor goes on
blinking and further keys act. Both come back by themselves about 5 minutes
after the last key, with the right time, and why is not known.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515, by comparing
screens: after keys that left the screen as it started, the area differed and
nothing else did. With the CK closed and the screen read every 30 s, it was
still blank 4 min 40 s after the last key and back at 5 min 10 s. Three earlier
times it was blank after the keys and back at the next reading, hours later with
the CK closed, and 11 and 15 minutes later with the CK connected, with no
readings in between.

<a name="usb.newer-framing"></a>
## The newer framing is not what makes a key act

| | |
|---|---|
| Identifier | `usb.newer-framing` |
| Kind | refuted hypothesis |
| Known from | G2 |

`FF EC 00 00 00 00 00 00`, sent after the information request, opens a session
in a newer framing: `01`, a message number and a size, each four bytes low byte
first, then the message. The calculator acknowledges each message at once with
`FE 01`, a sequence number, `00`, a position and the message number, repeats
that about every 0.5 s, and answers in the same framing, the screen included.
A key sent in that session is acknowledged and does not act until a later frame
starting `01` in the old framing. So the old framing is enough, and it is what
`hpprime screen` and `hpprime press` use.

**Evidence.** Measured on 2026-11-04 on a G2 on firmware 2.4.15515, in one
session: `EC 03 00 00 00 01 02` was acknowledged within 1 ms, and the screen
requested in the new framing afterwards was unchanged. The next `01` frame in
the old framing moved the selection three stops: that key and two more sent in
the old framing. The change frame comes from `BeatSkip/PrimeDev`; its wiki gives
another, `FF FE`, which was not tried. The old framing was still answered right
after the CK, which uses the acknowledgements above, had closed.

<a name="usb.kit-window"></a>
## The Connectivity Kit shows the screen in a window, and takes no input there

| | |
|---|---|
| Identifier | `usb.kit-window` |
| Kind | rule |
| Known from | G2 |

The CK's Monitor panel (`Supervisar` on a Spanish install) holds a thumbnail
about 110 pixels across, which changes rarely. Double-clicking it opens the
Project window (`Proyecto`), which shows the whole screen, changing about 2.2
times a second with a stall of about 1.6 s every 7.6 s. Neither window passes
anything back to the calculator. Windows can photograph the Project window with
`PrintWindow`, even covered or at the lock screen, but it needs the CK and gives
no keys; [usb.screen](#usb.screen) needs neither window nor CK.

**Evidence.** Measured on 2026-11-03 and 2026-11-04 on a G2 on firmware
2.4.15515 with the CK 2.4 in Spanish. The window was sampled every 91 ms for 127
s while the calculator's screen was changing: 208 gaps with a median of 0.45 s,
and the thumbnail changed twice. How fast the screen itself was changing was not
recorded, so the rate is not shown to be a ceiling. A person using the window by
hand got no reaction from the calculator, and neither did a click and an up
arrow sent to it. The names Monitor and Project are strings in the CK's own
program.
