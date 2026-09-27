# Key switch network — decision history

**Past tense only.** Every live value lives in `key-switch-network.md`,
[`../cluster-boards.md`](../cluster-boards.md) or `hardware/bom.csv`. If a
number here is still true, it is in the wrong file.

This is the circuit's superseded shelf, on the convention
[`../../module/pitch-stage/notes.md`](../../module/pitch-stage/notes.md) sets.
Nothing is deleted from it: a deleted superseded value stops warning the next
person.

---

## Why `R-KEY-PU` became 2.2 kΩ — moved from the BOM row, 2026-09-26

*Moved out of the `R-KEY-PU` notes cell under CLAUDE.md's cut line: a BOM
cell tells a builder what to do, and this is what someone used to think.*

The pull-up started at 10 kΩ, which was fine for a register beside its
switch. It went to 2.2 kΩ when the tail-register draft ran each key node
265 mm down an **uncoated** loom to a register at the tail, and a stiffer
pull-up was wanted against what that loom could couple in. ADR 0001 then moved
the registers back beside their switches — on the cluster boards then, on the
main board and the two key boards since ADR 0017 — and that reason went with
the loom. The 2.2 kΩ was kept anyway, as cheap insurance for a humid,
breathed-into cavity with open switch contacts; the live trade it now costs is
on `key-switch-network.md`.

The row also recorded that the first cluster-board draft left the free bits
(then bits 22, 23 and 31) floating — the ADR 0001 fix-6 fault — which is why they carry a
pull-up each and the row buys more pull-ups than there are networks.

---

## 2026-09-27 — the register became the SN74HCS165; the 74HC165 derivation, retired

The page derived both crossing times against the 74HC165's thresholds
(`V_IH` 2.31 V, `V_IL` 0.99 V, bracketed by onsemi's published 3.0 V row), and
the left-hand key board's review (K1-1) found that every key edge broke that
part's input transition limit: about 280× on release and 14× on press. The
owner switched to the SN74HCS165, whose Schmitt-trigger inputs have no such
limit, and the crossing times moved to its thresholds (`key-release-time`,
`key-press-time`). What the page said until then, verbatim except that each
retired figure is marked "(retired, 74HC165)" on its own line, so the
staleness checker can see the marking beside the value:

#### The derivation as it stood on the 74HC165

`[calc]`, at 3.3 V into 74HC165 thresholds (**`V_IH` = 2.31 V, `V_IL` = 0.99 V**
— 0.70 / 0.30 × VCC `[datasheet MC74HC165A/D Rev. 13 p.4]`):

> **Corrected 2026-09-21, the same day it was changed the other way.** This
> page reasoned from TI's SCLS116E, which has no 3.3 V row, that the 0.70/0.30
> ratio "breaks at 2 V" and that the conservative 2 V ratio 0.75/0.25 was the
> defensible bound at 3.3 V. **A 3.0 V row is published, and it is 0.70/0.30.**
>
> | source | 2.0 V | **3.0 V** | 4.5 V | 6.0 V |
> |---|---|---|---|---|
> | TI SCLS116E `datasheets/logic/74HC165-ti-scls116e.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | Nexperia Rev. 8 `74HC165-nexperia.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | Toshiba TC74HC165 `74HC165-toshiba-1986-excerpt.pdf` | 1.5 / 0.5 | *(absent)* | 3.15 / 1.35 | 4.2 / 1.8 |
> | **onsemi MC74HC165A Rev. 13** `74HC165-onsemi.pdf` | 1.5 / 0.5 | **2.1 / 0.9** | 3.15 / 1.35 | 4.2 / 1.8 |
>
> All four agree digit for digit at every shared rail, so onsemi is not a
> different device — it simply prints the JEDEC HC row the other three omit.
> **3.3 V is bracketed on both sides by published 0.70/0.30 rows**, so no
> extrapolation through the 2 V point is needed at all. The 2 V entry is the
> single exception at the bottom of the family's range, not the start of a
> trend. Nexperia's front page also claims compliance with **JESD8C**
> (2.7–3.6 V) `[74HC165-nexperia.pdf p.1]`, but it prints no levels there, and
> JESD8C itself is not banked, so it is not used as evidence for any threshold
> on this page. The onsemi bracket above stands on its own.
>
> `[calc]` Interpolating in **absolute volts** between onsemi's bracketing rows,
> assuming no ratio at all:
> `V_IH`(3.3) = 2.1 + (0.3/1.5)(3.15−2.1) = **2.31 V**;
> `V_IL`(3.3) = 0.9 + (0.3/1.5)(1.35−0.9) = **0.99 V**. Both land exactly on
> 0.70/0.30, which is what makes the bracketing argument safe rather than lucky.
>
> So both crossing times go back to what they were before yesterday's move:
> (retired, 74HC165) **138.7 → 119.9 µs** and **6.89 → 5.92 µs**. Neither ever changed a
> conclusion — the release is absorbed by firmware's release window either way,
> and the press clears the scan period by 42× instead of 36×. What was not
> defensible was stating 0.75/0.25 **as the datasheet threshold** when no
> datasheet in the corpus gave a threshold at 3.3 V at all.
>
> **If a TI SN74HC165 is the part actually fitted**, its own datasheet still
> guarantees nothing at 3.3 V, and the pessimistic bound is 2.475 / 0.825 V,
> giving 138.7 µs and 6.89 µs. Those are the numbers to design margin against
> if the margin ever gets tight. It is not tight: 42× and 36× are the same
> answer.
>
> *(The press row also said `τ = 100 Ω × 47 nF = 4.7 µs` beside a crossing
> time computed from the **parallel** combination, 4.496 µs. That correction is
> independent of the threshold question and **stands** — the pull-up is still
> connected, so the parallel value is the right one.)*
>
> The TI datasheet carries a warning worth repeating: operating in the
> threshold region risks **double-clocking from induced ground bounce**.
> Another reason not to shave this margin.

**Every key edge breaks the 74HC165's input transition limit, and this is
accepted, not overlooked.** The HC165 has no Schmitt inputs, and each
datasheet caps how slowly an input may cross its thresholds: Nexperia (the
fitted part) allows 625 ns/V at 2.0 V and 139 ns/V at 4.5 V
`[datasheets/logic/74HC165-nexperia.pdf p.6, Table 5]`, about **372 ns/V at
3.3 V** interpolated `[calc: 625 − (1.3/2.5)(625 − 139)]`. `[calc]`, from the
table above:

- **Release** crosses `V_IH` at (3.3 − 2.31) V / 103.4 µs = 9.57 mV/µs, which
  is **104 000 ns/V, about 280× the limit**. The node (retired, 74HC165) spends 32.3 → 119.9 µs,
  **87.6 µs**, between `V_IL` and `V_IH`, so at the 250 µs scan about **35 %
  of releases put one sample inside the band**.
- **Press** crosses `V_IL` at 5 310 ns/V, **about 14×**, and spends 4.2 µs in
  the band.

Why it is accepted:
- These are parallel data inputs, not clocks. The register captures them
  when `SH/LD` returns high (`key-register.md` §1), so a slow input cannot
  double-clock anything. An input caught mid-band reads as 0 or 1.
- One indeterminate sample during a release is indistinguishable from
  contact bounce, which firmware's release window already rejects (above).
- The unquantified cost is extra supply current while an input dwells
  mid-rail. It is measured at bring-up: `ICC` with a key held half-pressed,
  from TP-3V3 (`hardware/boards/key-board-lh/README.md`).

**The alternative is a drop-in part, and it is the owner's choice** (Still
open, below): TI's **SN74HCS165** has Schmitt-trigger inputs and "no input
signal transition rate requirements" `[datasheets/logic/SN74HCS165-ti-scls828a.pdf
p.15]`, the same pinout and SOIC-16 `[same, p.3; p.1]`. Adopting it re-derives
`key-release-time` and `key-press-time` against its thresholds: TI publishes
them at 2 V, 4.5 V and 6 V only `[same, p.6]`, and Nexperia's 74HCS165, which
does publish a 3.0–3.6 V row, is a different die and not the one bought
`[datasheets/logic/74HCS165-nexperia.pdf p.6]`. The 74LV165A is not an
alternative: its "Schmitt-trigger action" still carries a transition-rate
limit `[datasheets/logic/74LV165A-nexperia.pdf p.5]`.

| | |
|---|---|
| Release, τ = 2.2 kΩ × 47 nF = 103.4 µs | crosses `V_IH` at **119.9 µs** (retired, 74HC165) |
| (retired, 74HC165) Press, τ = (2.2 kΩ ∥ 100 Ω) × 47 nF = 4.496 µs | crosses `V_IL` at **5.92 µs** — 42× inside the 250 µs scan |
| Pole | 1.54 kHz → **54 dB** at the WS2815's 800 kHz data rate |
| Static | **1.43 mA** per closed key; 19 closed = **27.3 mA** off the chain's 3V3 |
