# Mod channels 1–4 — decision history

**Past tense only.** Every live value lives in `mod-channels.md` or
`hardware/bom.csv`. If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted
old value from a live one, so the two always travel together.

---

## `A = 1 + B` was called a boundary, and the mods were said to miss it

*Moved verbatim from `## Two resistors, not four — settled`, 2026-09-21. The
identity that replaced it is live and stays on the page, as does everything
that follows from it.*

The first version of this page argued that pitch collapsed to two resistors
because `A = 1 + B` was a boundary its numbers landed on, and that the mods miss
it. **That reasoning was wrong.**

---

## A third option, from the same prior-art research

*Moved verbatim from `## Two resistors, not four — settled`, where it followed
the comparison table, 2026-09-21.*

*(A third option surfaced in the same research: four of four published designs
— Ornament & Crime, Westlicht PER|FORMER, Mutable Yarns, MTM Workshop Computer
— use a **single inverting amp** with the mid-reference on the (+) input, which
needs no buffer at all because that input draws no current. It inverts, which
is a firmware sign flip. The catch is that O&C and the PER|FORMER take that
reference from a passive divider off `VREFOUT`, which does **not** go to zero on
`CLR` — so all four jacks would slam to +10 V. The PER|FORMER avoids it by
disabling `CLR` entirely, which Woody cannot. Taking the reference from a DAC
channel keeps the inverting topology and the safe clear together.)*

---

## The four-resistor version this replaced

*Moved verbatim from `## Values`, 2026-09-21, where it opened an italic
parenthesis that was never closed. The tolerance, matching and range paragraphs
that ran on inside that same parenthesis state live values and stayed on the
page.*

The four-resistor version this replaced used 40.2 kΩ against 10 kΩ, because
E24's 39 k would have given gain 3.90 and a jack that
stops at ±9.75 V, visibly short of the specified ±10. Going slightly over costs
nothing: an OPA2197 on ±12 V less two Schottky drops reaches ~±11.45 V, so
±10.05 V has 1.4 V of margin.

**Why `R-OPAMP-IN` was wrong on the old drawing, kept because it is a good
trap.** On the four-resistor version the 10 kΩ input resistor *was* the gain
network, so a 1 kΩ in series made the DAC leg 11 kΩ against the reference leg's
10 kΩ and the stage stopped being balanced — a deterministic **−196 mV** zero
error and +9.657 V instead of +10.05, more than twice the whole tolerance
budget. On the two-resistor form the same part feeds a (+) input that draws no
current, and costs nothing. Same resistor, same reason for existing, opposite
consequence, decided entirely by the topology around it.

---

*Moved verbatim from the page, 2026-09-21 — heading included, which is why this
note sits above it rather than below. "What is drawn above" in the last
paragraph means the circuit in `mod-channels.md`, which is where it still is.
It was not adopted, and that paragraph's call was open when this moved; the
page points here rather than carrying it.*

## The alternative topology, recorded rather than adopted

Prior-art research found that **four of four published designs** (Ornament &
Crime, Westlicht PER|FORMER, Mutable Yarns, MTM Workshop Computer) build this
stage as a **single inverting amplifier** with the mid-reference on the (+)
input, not as a four-resistor difference amp. It is genuinely simpler:

```
Vout = −(Rf/Rin)·Vdac + (1 + Rf/Rin)·V+
     = −4·Vdac + 5·V+        with V+ = 2.000 V  →  +10 V … −10 V
```

Two precision resistors instead of four, no matching requirement *between* two
legs, and the offset injection is free because the (+) input draws no current —
which also means the offset DAC channel would need **no buffer**, returning an
OPA2197 half.

It inverts, which is a firmware sign flip and costs nothing.

**The one thing to be careful about, and it is the thing that matters here:**
O&C and the PER|FORMER both take that reference from a *passive divider off
`VREFOUT`*. On a `CLR` the channels go to zero and the divider does not, so
`Vout = 5 × 2.0 = +10 V` — a hard rail on four jacks. The PER|FORMER avoids
this by disabling `CLR` entirely; **Woody cannot, because `CLR` is asserted by
the DAC itself at every power-on and by `LK-CLR` at every bring-up.** A
non-clearing offset reference is therefore unsafe here regardless of what
supervises the link.

> **That last clause said "because the watchdog is the whole answer to a
> processor two metres away" until 2026-09-21** — a deleted part carrying a live
> conclusion, and the conclusion happens to be the one that rules out the
> single-inverting-amp topology four of four surveyed designs use. The
> conclusion survives the correction intact; it now rests on the DAC's own
> power-on reset, which no deletion can take away.

Taking the reference from a **DAC channel** instead keeps the inverting
topology *and* the safe clear, because `CLR` zeroes it too. That is the version
worth considering, and it is strictly better than what is drawn above. Not
adopted unilaterally: it is a redraw of a settled page and the call belongs to
the author.
