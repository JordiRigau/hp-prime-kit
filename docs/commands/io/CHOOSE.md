# CHOOSE

Offers a short list and puts the chosen index in a variable.

| | |
|---|---|
| Syntax | `CHOOSE(var, "title", "item1", "item2", [..."item14"])` |
| Group | io |
| Runs on the PC | yes |

## Examples

| Call | Result | Known from |
|---|---|---|
| `CHOOSE(V,"title","a","b")` | *no value* | HP help |

## Behaviour

There is nothing to record: it waits for a person, and a batch has nobody to
choose (HP help). The variable receives the index of what was picked, and the
call itself answers whether something was picked, which has not been measured
here (unverified).

**Fourteen items is where HP's syntax stops** (HP help). Past that, or when
the list has to scroll, the third-party library `CHOOSE_R`, which has to be
installed first, is what people reach for,
and it has been read here rather than run (unverified),
[libraries.published](../../topics/libraries.md#libraries.published).

`hpprime run` records the call and answers a neutral value, so a program that
asks questions still runs end to end on the PC (unverified: that is what the
interpreter does, not something the calculator says)
([interface.md](../../topics/interface.md#what-the-design-of-a-screen-comes-down-to)).

## Related

[INPUT](INPUT.md) · [MSGBOX](MSGBOX.md) ·
[libraries.published](../../topics/libraries.md#libraries.published)
