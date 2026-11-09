# Evidence: the programs run to measure the facts

A fact says what was run and what came back. This folder keeps what was run, so
that it can be read and run again. What each program answered is in the evidence
of its fact, and what the Virtual Calculator answered is also in
[results.tsv](../commands/results.tsv).

These are measurements, not examples to copy. Some do not compile, on purpose:
that is what they test.

## Where each run is

| Folder | What it holds | How it was run |
|---|---|---|
| [2026-11-05](2026-11-05/) | one program per file | on a G2 with firmware 2.4.15515, sent over USB under the names `ZQTEST` and `ZQLIB`, each replacing the last, and typed on Home, as [usb.compile-check](../topics/usb.md#usb.compile-check) says. `RRL`, `RRD` and `RRM` were not run on the G2, only on the emulator |
| [2026-11-07-emulator](2026-11-07-emulator/) | the same programs, unchanged, in four files: [A](2026-11-07-emulator/BATCH-A.txt), [B](2026-11-07-emulator/BATCH-B.txt), [C](2026-11-07-emulator/BATCH-C.txt), [D](2026-11-07-emulator/BATCH-D.txt) | on the Virtual Calculator 2.4, build 2025-09-15, with `hpprime examples --compile`, as the first lines of each file say. Left out: the controls, since the tool has its own; `H2`, whose function `H5` holds; `ROAlib`, which only filled a place; and `RNBlib`, which went through the Connectivity Kit instead, as [ppl.global-namespace](../topics/ppl.md#ppl.global-namespace) says |
| [2026-10-04-emulator](2026-10-04-emulator/) | one PPL program with two screens, and the Python file of two apps | on the Virtual Calculator 2.4, build 2025-09-15, read from the screen |

To run one again: a file of the second folder goes through `hpprime examples
--compile`, and a program of the first goes to a G2 with `hpprime send --no-lint`
([tools.md](../tools.md)).

## Programs by fact

| Fact | Programs |
|---|---|
| <a name="apps.main-py"></a>[`apps.main-py`](../topics/apps.md#apps.main-py) | [ZPYENT-start.py](2026-10-04-emulator/ZPYENT-start.py) |
| <a name="interface.screen-capacity"></a>[`interface.screen-capacity`](../topics/interface.md#interface.screen-capacity) | [ZSCREEN.txt](2026-10-04-emulator/ZSCREEN.txt), `ZROWS` |
| <a name="interface.two-themes"></a>[`interface.two-themes`](../topics/interface.md#interface.two-themes) | [ZSCREEN.txt](2026-10-04-emulator/ZSCREEN.txt), `ZTHEME` |
| <a name="micropython.eval-parentheses"></a>[`micropython.eval-parentheses`](../topics/micropython.md#micropython.eval-parentheses) | [ZPYPRB-main.py](2026-10-04-emulator/ZPYPRB-main.py) |
| <a name="micropython.number-notation"></a>[`micropython.number-notation`](../topics/micropython.md#micropython.number-notation) | [ZPYPRB-main.py](2026-10-04-emulator/ZPYPRB-main.py) |
| <a name="ppl.call-no-parentheses"></a>[`ppl.call-no-parentheses`](../topics/ppl.md#ppl.call-no-parentheses) | [P1](2026-11-05/P1.txt), [P2](2026-11-05/P2.txt), [P3](2026-11-05/P3.txt), [P4](2026-11-05/P4.txt), [P5](2026-11-05/P5.txt), [P5lib](2026-11-05/P5lib.txt), [P6](2026-11-05/P6.txt) |
| <a name="ppl.compilation-order"></a>[`ppl.compilation-order`](../topics/ppl.md#ppl.compilation-order) | [ROA](2026-11-05/ROA.txt), [ROAlib](2026-11-05/ROAlib.txt), [ROBlib](2026-11-05/ROBlib.txt), [ROC](2026-11-05/ROC.txt) |
| <a name="ppl.export-home-variable"></a>[`ppl.export-home-variable`](../topics/ppl.md#ppl.export-home-variable) | [N0](2026-11-05/N0.txt), [N1](2026-11-05/N1.txt), [N2](2026-11-05/N2.txt), [RFA](2026-11-05/RFA.txt), [RFB](2026-11-05/RFB.txt), [RFC](2026-11-05/RFC.txt), [RFD](2026-11-05/RFD.txt), [RFE](2026-11-05/RFE.txt), [RFN](2026-11-05/RFN.txt), [RXA](2026-11-05/RXA.txt), [RXY](2026-11-05/RXY.txt), [RXZ](2026-11-05/RXZ.txt) |
| <a name="ppl.export-initialised"></a>[`ppl.export-initialised`](../topics/ppl.md#ppl.export-initialised) | [E6](2026-11-05/E6.txt), [E7](2026-11-05/E7.txt), [E8](2026-11-05/E8.txt), [E9](2026-11-05/E9.txt), [RXN](2026-11-05/RXN.txt), [RXO](2026-11-05/RXO.txt) |
| <a name="ppl.expr-dynamic-access"></a>[`ppl.expr-dynamic-access`](../topics/ppl.md#ppl.expr-dynamic-access) | [RZT](2026-11-05/RZT.txt) |
| <a name="ppl.expr-empty"></a>[`ppl.expr-empty`](../topics/ppl.md#ppl.expr-empty) | [RZE](2026-11-05/RZE.txt) |
| <a name="ppl.getkey-no-parentheses"></a>[`ppl.getkey-no-parentheses`](../topics/ppl.md#ppl.getkey-no-parentheses) | [G1](2026-11-05/G1.txt), [G2](2026-11-05/G2.txt) |
| <a name="ppl.global-namespace"></a>[`ppl.global-namespace`](../topics/ppl.md#ppl.global-namespace) | [RNA](2026-11-05/RNA.txt), [RNAlib](2026-11-05/RNAlib.txt), [RNBlib](2026-11-05/RNBlib.txt) |
| <a name="ppl.home-no-parentheses"></a>[`ppl.home-no-parentheses`](../topics/ppl.md#ppl.home-no-parentheses) | [H1](2026-11-05/H1.txt), [H2](2026-11-05/H2.txt), [H3](2026-11-05/H3.txt), [H5](2026-11-05/H5.txt), [H6](2026-11-05/H6.txt) |
| <a name="ppl.index-call"></a>[`ppl.index-call`](../topics/ppl.md#ppl.index-call) | [RIC](2026-11-05/RIC.txt), [RID](2026-11-05/RID.txt) |
| <a name="ppl.letter-digit-names"></a>[`ppl.letter-digit-names`](../topics/ppl.md#ppl.letter-digit-names) | [RRD](2026-11-05/RRD.txt) |
| <a name="ppl.local-block-scope"></a>[`ppl.local-block-scope`](../topics/ppl.md#ppl.local-block-scope) | [L4](2026-11-05/L4.txt), [L5](2026-11-05/L5.txt), [RLA](2026-11-05/RLA.txt), [RLC](2026-11-05/RLC.txt), [RLCP](2026-11-05/RLCP.txt), [RLD](2026-11-05/RLD.txt), [RLE](2026-11-05/RLE.txt), [RLF](2026-11-05/RLF.txt), [RLFP](2026-11-05/RLFP.txt), [RLG](2026-11-05/RLG.txt), [RLI](2026-11-05/RLI.txt), [RLJ](2026-11-05/RLJ.txt), [RLO](2026-11-05/RLO.txt), [RLR](2026-11-05/RLR.txt), [RLRP](2026-11-05/RLRP.txt), [RLS](2026-11-05/RLS.txt), [RLT](2026-11-05/RLT.txt), [RLU](2026-11-05/RLU.txt), [RLW](2026-11-05/RLW.txt), [RLWP](2026-11-05/RLWP.txt) |
| <a name="ppl.local-limit"></a>[`ppl.local-limit`](../topics/ppl.md#ppl.local-limit) | [RV8](2026-11-05/RV8.txt), [RV9](2026-11-05/RV9.txt) |
| <a name="ppl.local-m-matrices"></a>[`ppl.local-m-matrices`](../topics/ppl.md#ppl.local-m-matrices) | [RRM](2026-11-05/RRM.txt) |
| <a name="ppl.locals-at-top"></a>[`ppl.locals-at-top`](../topics/ppl.md#ppl.locals-at-top) | [L1](2026-11-05/L1.txt), [L2](2026-11-05/L2.txt), [L3](2026-11-05/L3.txt), [L6](2026-11-05/L6.txt) |
| <a name="ppl.matrices-by-value"></a>[`ppl.matrices-by-value`](../topics/ppl.md#ppl.matrices-by-value) | [M1](2026-11-05/M1.txt), [M4](2026-11-05/M4.txt) |
| <a name="ppl.no-end-keywords"></a>[`ppl.no-end-keywords`](../topics/ppl.md#ppl.no-end-keywords) | [REF](2026-11-05/REF.txt), [REW](2026-11-05/REW.txt) |
| <a name="ppl.return-in-loop"></a>[`ppl.return-in-loop`](../topics/ppl.md#ppl.return-in-loop) | [RRL](2026-11-05/RRL.txt) |
| <a name="usb.compile-check"></a>[`usb.compile-check`](../topics/usb.md#usb.compile-check) | [C1](2026-11-05/C1.txt), [C2](2026-11-05/C2.txt), [C3](2026-11-05/C3.txt), [RC1](2026-11-05/RC1.txt), [RC2](2026-11-05/RC2.txt), [RC3](2026-11-05/RC3.txt) |
| [`MAKEMAT`](../commands/matrix/MAKEMAT.md) | [M3](2026-11-05/M3.txt) |
