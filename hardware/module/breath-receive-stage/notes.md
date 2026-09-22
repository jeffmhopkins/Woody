# Breath receive stage — decision history

**Past tense only.** Every live value lives in `breath-receive-stage.md` or
`hardware/bom.csv`. If a number here is still true, it is in the wrong file.

This is the circuit's superseded shelf — the same convention
`docs/decisions/README.md` runs at project scope, one level down. Nothing is
deleted from it: a deleted superseded value stops warning the next person, and
the refutation wording is what lets `tools/check-staleness.py` tell a quoted
old value from a live one, so the two always travel together.

---

## The polarity question, dissolved twice

*Moved verbatim from `## `REF` carries a trimmer, and the polarity question
dissolved twice` in `breath-receive-stage.md`, 2026-09-21. The two paragraphs
that answer it — the buffered trimmer, and the downstream stage's inverting
topology — are live and stayed on the page, which is where "the swap" below
ends up justified.*

**The original showstopper.** The MPXV4006DP sits at **+0.2 V at zero pressure
by design** (spec range 0.152–0.378 V). An in-amp is additive at `REF`:
`Vout = G·(V+ − V−) + V_REF`. With BREATH on IN+, nulling that pedestal needs
`V_REF ≈ −0.43 V`, and the DAC channel proposed to drive `REF` is unipolar
0–5 V — it can only push the floor *up*. That left 4–9 % of full scale standing
at the jack at rest and an auto-zero with authority in one direction only.

**The first fix was to swap the inputs.** With BREATH on IN−, a *positive* `REF`
subtracts, which is what a unipolar DAC can produce.

**Then the DAC channel was deleted entirely** — it was correcting a signal
firmware cannot measure (ADR 0003, ADR 0006) — which removes the premise the
swap was argued from. So the swap needs a reason of its own, and it has one:

So the swap survives on the downstream stage's topology rather than on the DAC's
unipolarity. Recorded explicitly because a decision whose original justification
has been removed is exactly the kind of thing that survives by inertia.

---

*Moved verbatim from the page, 2026-09-21. A record of what the cold review
filed and of what drawing the topology did to each finding. Every value quoted
in it is stated live in `breath-receive-stage.md`'s own component table and
gain derivation, which is where it is maintained.*

## What this settles

| Finding | Resolution |
|---|---|
| Ambient zero has the wrong polarity | **Deleted** — there is no *firmware* injection. `REF` carries a commissioning trimmer, and polarity is a non-issue because a trimmer goes both ways |
| The zero correction is open-loop across two representations | **Deleted with it** — firmware now zeroes only the copy it measures |
| No common-mode bias return | **Fixed** — R4, R5 |
| No in-amp gain resistor | **Fixed** — R_G = 42.2 kΩ, derived above |
| The 100 kΩ differential pulldown | **Deleted.** R4/R5 do its job without its 1–17 % attenuation, and the review could not agree which figure applied |
| "Six different in-amp gains" | One gain, one derivation, shown |
| Which in-amp | **INA828** — the E96 value lands cleanly and its lower bandwidth suits a 500 Hz channel |
| Where the 500 Hz pole goes | Ahead of the in-amp, differential-dominant |

---

## Two statements in the `CLR` section that were stale until 2026-09-21

*Moved verbatim from `## What the jack does on a `CLR` — settled` in
`breath-receive-stage.md`, 2026-09-21. The conclusion it qualifies is live and
stayed there.*

> **Two things in this section were stale until 2026-09-21.** It was headed
> "when the watchdog fires", and the 74HC123 frame watchdog is deleted
> (`digital-and-supervision.md`) — the surviving sources of a `CLR` are the
> DAC's own power-on reset and the hand-asserted `LK-CLR` pad. And it said
> "now that `REF` is grounded", which is the option this page **declines** forty
> lines above, by name: grounding `REF` makes the panel knobs interact. The
> conclusion is unchanged under either correction, because it rests on breath
> never passing through the DAC.

---

*Moved verbatim from the page's `Still open` list, 2026-09-21, where it was
neither this page's circuit nor open — the compensation is decided in
`riso-ref-topology` and drawn in `hardware/carrier/carrier.md` §2.*

## The instrument-side reference buffer — settled 2026-09-21

Not this page's circuit, but it sets the number this page multiplies. ADR 0003
buffers the REF5050 with half an OPA2197 straight into the sensor's `VS` pin,
which carries a 100 nF decoupler. That load alone leaves **1.5° of phase
margin** against the OPA2197's specified 375 Ω `Zo`, so the buffer is
compensated — and **the compensation is now decided: see `riso-ref-topology`,
and `hardware/carrier/carrier.md` §2 for the drawing.**

Two things this page used to say about it are superseded, and both mattered to
the number this page multiplies:

- **The load is 100 nF, not 100 nF + 10 µF.** `C-REF-OUT` sits on the
  REF5050's own pins, not on the buffer's output — see `cref-out-node`.
- **The in-loop-versus-out-of-loop trade this page framed has been
  dissolved, not decided.** It weighed instability against *"2 % of the
  ratiometric scale factor"*. TI's dual-feedback network gives both: 85.9° of
  phase margin **and** exactly zero DC error across `R-ISO-REF`, because at DC
  the only feedback path closes at the sensor pin. In-loop `R_ISO` on its own
  was never the answer either — it buys nothing at any value.

**What this page keeps:** the buffer is instrument-side and unretrofittable,
and so are all four compensation parts.
