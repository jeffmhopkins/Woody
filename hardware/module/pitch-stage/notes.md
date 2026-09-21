# Pitch stage — decision history

**Past tense only.** Every live value lives in `pitch-stage.md` or
`hardware/bom.csv`. If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted
old value from a live one, so the two always travel together.

---

## `A = 1 + B` was called a boundary, and it is an identity

**A correction, because the first version of this page got the reason wrong.**
It said `A = 1 + B` is a *boundary* that pitch's numbers happened to land on,
and that the mod channels miss it and therefore need four resistors.

`A = 1 + B` is not a boundary. It is the **defining identity** of this
topology — with `k = R2/R1`, gain is `1 + k` and the intercept is `k·V_ref`,
for every `k`. The free parameter is not the ratio, it is **`V_ref`**:

```
k = A − 1        V_ref = offset / (A − 1)
```

Winterbloom's Sol ships this exact circuit and divides its 2.5 V reference
down to **1.190 V** to land on the gain and offset it wants. Pitch is not a
lucky case; it is the ordinary case with `V_ref` left at 2.500 V.

The consequence matters: **the mod channels can use two resistors too**, at
`k = 3` with the offset channel writing **3.3333 V** instead of 2.500 V — and
the power-on-and-`CLR`-at-0 V property survives, because both terms still go
to zero. See `mod-channels.md`.

*(Kept because the wrong version made the mod channels look as though they
needed four resistors, which they do not — and that reading survived into
three other documents before it was caught.)*

---

## The superseded accuracy table

*Moved verbatim from the page, 2026-09-21. "The section above" and "the live
table twelve lines up" refer to `## What limits accuracy, in order` in
`pitch-stage.md`, which is where they still are.*

> **Superseded, and left here rather than deleted. 2026-09-21.** The four rows
> below are the remains of the accuracy table the section above replaced. They
> lost their header when the replacement landed, so they read as a continuation
> of the prose, and **two of them contradict the live table twelve lines up**:
> LT5400 ratio tracking is **0.027 cents**, not `~0.1`, and the DAC internal
> reference is **0.42 cents**, not `~0.5`. Neither figure is tracked in
> `config/figures.yaml`, so `check-staleness.py` is structurally blind to this
> — it was found by reading, which is what `CLAUDE.md` §5 says a grep cannot
> replace. They belong in this circuit's `notes.md` once the restructure gives
> it one; until then they stay marked rather than removed, because a deleted
> superseded value stops warning the next person.
>
> | LT5400 ratio tracking | ~0.1 cents | The reason it is not two discrete 0.1 % parts, which would be ~1.2 cents |
> | DAC internal reference | ~0.5 cents | A gain term, per above |
> | OPA2197 offset drift | <0.1 cents | An offset term, but a tiny one |
> | DAC INL, ±4 LSB typical | ~0.4 cents | Curvature; firmware's multi-point correction, not a trimmer's job |

---

## The LT5400 option suffix — closed 2026-09-21

*Moved verbatim from the page's `Still open` list, 2026-09-21. The exposed-pad
question inside it is **still open** and is carried forward in
`pitch-stage.md`; everything else here closed.*

- ~~**The LT5400 option suffix.**~~ **CLOSED 2026-09-21.** `5400fa.pdf` is
  banked at `datasheets/other-semi/LT5400.pdf`. The option table (p.2) is
  `-1` 10k 1:1, `-2` 100k 1:1, `-3` 1:10, `-4` 1k 1:1, `-5` 1M 1:1, `-6` 1:5 —
  so **`-1` is the four-equal-10k 1:1 quad** and **there is no 1:3 option at
  all**, which the arithmetic below had already concluded from the other
  direction. Grade A is 0.01 % matching and B is 0.025 %, and ratio tracking is
  **1 ppm/°C max** (0.2 typ), so the 0.027 cents line in the budget above is
  conservatively sourced rather than optimistic. The claim that two spare
  sections can build the mod channels' 1:3 is **arithmetically impossible** —
  three sections against the fourth is all four.
  > **But the package was wrong, and it is layout-blocking.** p.2: *"MS8E
  > PACKAGE / 8-LEAD PLASTIC MSOP / EXPOSED PAD (PIN 9) IS FLOATING"*, and p.8
  > is headed *"8-Lead Plastic MSOP, Exposed Die Pad"*. `bom.csv` said plain
  > MSOP-8 with no pad. **The pad is 1.88 × 1.68 mm**, it is not DC-connected to
  > any resistor, and p.6 says *"do not tie the exposed pad to noisy signals or
  > noisy grounds"* and that *"connecting the exposed pad to a quiet AC ground
  > is recommended"*.
  >
  > **New, and it lands on this stage's own node:** pad-to-resistor coupling is
  > **5.5 pF** against only 1.4 pF resistor-to-resistor. The pad is therefore
  > the dominant stray on the 1 V/oct network, and nothing in this corpus says
  > where it goes — because the BOM did not know it had one. **Decide it with
  > the layout, not after.**
  >
  > Two more from the same document. **Absolute tolerance is ±7.5 % (A) /
  > ±15 % (B)** — nobody had written that down, and it means `TRIM-GAIN`'s
  > "0 → +2 %" is nominal-only; the real authority is 1.86–2.16 % on an A part,
  > which sharpens the "no downward authority" worry two items below. And the
  > **LT5400 has no internal ESD diodes, only ±1 kV HBM** (p.6), with Figure 1's
  > named remedy being a **BAV99** — which `D-JACK-CLAMP` already is. Pitch
  > feedback is tapped *at the jack*, i.e. exactly the datasheet's "external
  > connector" case, so check the clamp actually stands between the jack and
  > every LT5400 pin when this is laid out.
  >
  > **Caveat on the revision.** This is rev **fa**, not the **fc** `bom.csv`
  > names canonical — `analog.com` is still unreachable and this came from an
  > RS mirror. Rev fa's option table predates the `-7`, so `LT5400-7` is
  > **not-in-document**, not refuted. Do not "correct" ADR 0006 by citing rev
  > fa's silence.
