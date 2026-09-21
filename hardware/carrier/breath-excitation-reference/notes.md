# Breath excitation reference — decision history

**Past tense only.** Every live value lives in
[`breath-excitation-reference.md`](breath-excitation-reference.md),
`config/figures.yaml` or `hardware/bom.csv`. If a number here is still true, it
is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted old
value from a live one, so the two always travel together.

---

## Both datasheet blockers closed, and the two notes they superseded

*Moved verbatim from `carrier.md` §2, 2026-09-21. "This page" throughout means
`carrier.md` as it stood before the split; the live circuit is now in
[`breath-excitation-reference.md`](breath-excitation-reference.md) and the
drawing it refers to is still in [`carrier.md`](../carrier.md) §2.*

> **✅ BOTH BLOCKERS CLOSED 2026-09-21, AND THE HEDGES THAT USED TO LIVE HERE
> ARE GONE WITH THEM.** `datasheets/texas-instruments/OPA2197.pdf` (SBOS737C,
> 56 pp) and `datasheets/texas-instruments/REF5050.pdf` (SBOS410O, 52 pp) are
> both banked. Two earlier notes on this page are superseded rather than
> amended, and are recorded here because each was a *correct* finding filed the
> wrong way:
>
> **1. The "1 nF" IS an OPA2197 figure**, and this page had filed it as refuted
> on the strength of the INA828 carrying the same headline number by
> coincidence. It is on the OPA2197's own front page — *"High Capacitive Load
> Drive Capability: 1 nF"* — and in §7.3.5 p.22. **Per `CLAUDE.md` that is the
> more dangerous error**: a wrong finding gets caught by the next reviewer; one
> filed as handled does not.
>
> **2. `Ro` is specified, and it is 375 Ω, not the 75.8 Ω this page
> back-solved.** Figure 26 reads ~3.26 kΩ at 0.1 Hz, 482 Ω at 10 Hz, a **375 Ω
> plateau from 100 Hz to 300 kHz**, 301 Ω at 1 MHz and ~73 Ω at 10 MHz — so
> 75.8 Ω is about the *10 MHz* value. Every number this page derived from it
> has been recomputed against 375 Ω, and the published **2.6° / 458 kHz is
> dead**; the real hazard is ~1.5° at ~206 kHz. Both mean "oscillator".
>
> **3. `C-REF-OUT`'s node is settled and this page's drawing was right.** See
> `cref-out-node`. The 10 µF parts are the REF5050's own `VIN` bypass and
> `VOUT` load capacitor — **neither is on the buffer's output**, where 10 µF
> would have been 10 000× the OPA2197's rated capacitive load. A consequence
> nobody had written down: the REF5050's only load is now the buffer's input
> bias current, ±20 pA max, so its load regulation contributes **zero** to the
> breath scale factor. On the other topology, 10 mA through 30 ppm/mA would
> have been 300 ppm — a whole LSB.

---

## `C-REF-OUT` qty 2 — closed 2026-09-21

*Moved verbatim from `carrier.md`'s `Still open` list, 2026-09-21, where it was
already struck through as closed.*

- ~~**`C-REF-OUT` qty 2** for one REF5050 — parallel, or input and output?~~
  **Closed 2026-09-21: input and output, see `cref-out-node`.** The datasheet
  forces a `C_L` onto the REF5050's own `VOUT`, which accounts for one of the
  two and leaves nothing for the buffer's output.
