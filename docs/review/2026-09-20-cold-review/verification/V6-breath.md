# V6 — Falsification pass on the breath cluster

**Role:** adversarial. Everything below is an attempt to break eight findings from
the 2026-09-20 cold review. Nothing in the repository was modified.

**Sources read:** `docs/review/2026-09-20-cold-review/{README,B1,B2,B9,D3,D4}.md`,
`docs/decisions/{0003,0005,0006}`, `hardware/bom.csv`, plus `B6-instrument-power.md`
§"brown-out window" (reached through the register's W13).

**Method note that turned out to matter.** I read the register *and* the agent
documents it summarises. Several of the register's strongest claims are not what
the agents wrote. Two of the four "verified showstopper" claims in this cluster
were written by their originating agents with an explicit confidence caveat on
the topology assumption, and the register deleted the caveat. That is recorded
per-finding below, because it changes the verdicts.

---

## Verdicts at a glance

| # | Finding | Verdict | Confidence |
|---|---|---|---|
| 1 | Ambient-zero has the wrong polarity | **UNDERSPECIFIED-NOT-WRONG** (arithmetic survives; topology does not) | high |
| 2 | In-amp has no common-mode bias return | **SURVIVES BUT DOWNGRADED** (defect real; trigger and magnitude overstated) | high |
| 3 | Anti-alias filter is 121 Hz, not 600 Hz | **SURVIVES** (arithmetic); the "transcription error" gloss is **OVERSTATED** | very high |
| 4 | No in-amp gain resistor in the BOM | **SURVIVES BUT DOWNGRADED** to a BOM-completeness item; the *value* is uncomputable from the repo | high |
| 5 | Auto-zero conceals sensor faults | **SURVIVES BUT DOWNGRADED**; one of the three named faults is **FALSE**, the circular-breathing clause is **FALSE** | med-high |
| 6 | Zero correction open-loop across two representations | **SURVIVES BUT DOWNGRADED**; largely a restatement of #1 plus a diagnostics ask | high |
| 7 | Nothing mutes breath on watchdog / brown-out | **SURVIVES** (main clause, and the brown-out window is *wider* than claimed); the "CLR removes its zero" clause is **FALSE given #1** | high |
| 8 | Helmholtz tube model is invalid | **SURVIVES**, and is strengthened; but "no restrictor size fixes it" is **OVERSTATED** and the 214–429 Hz bracket is wrong at both ends | very high |

**The single most important result is structural and appears in the collapse
section at the end: findings 1, 2, 4, 6 and half of 7 are five symptoms of one
absent document — the module's breath stage has never been drawn.**

---

## 1. "The ambient-zero injection has the wrong polarity" — UNDERSPECIFIED-NOT-WRONG

### What I re-derived

The pedestal is real and is not offset error. ADR 0003's own transfer function
`Vout = VS × (0.1533·P + 0.04)` at VS = 5.000 V gives **0.200 V at P = 0**, by
design, on every unit.

The magnitude at the jack is cleaner than any document states, and it falls out
without needing the gain chain at all. Whatever the split between in-amp gain,
link attenuation and knob stage, the span is trimmed so that 4.5 V of sensor
signal becomes 10 V at the jack. Therefore:

```
pedestal at jack = 10 V × 0.200/4.500 = 0.444 V = 4.44 % of full scale
```

The intermediate numbers the review argues about (2.13 vs 2.39 vs 2.44, 0.909 vs
0.833) **all cancel**. This is worth stating because two agents disagreed about
them and the disagreement was irrelevant to the result.

With B2's asserted datasheet offset band (0.152 / 0.265 / 0.378 V, min/typ/max):
3.4 % / 5.9 % / 8.4 %. So the register's "4–9 %" is defensible at the band
edges; the **"4–11 %" in the brief is not sourced by anything in the repository
or in either agent document** and should be dropped.

The in-amp equation is right: `Vout = G·(V+ − V−) + V_REF`, and a DAC8568 on a
5.25 V AVDD with internal reference × 2 is 0–5 V unipolar — confirmed from ADR
0006's own "0.25–4.75 V window" language for pitch. So *if* BREATH drives IN+ and
*if* the zero is injected at REF and *if* there is no inversion downstream, REF
must be −0.426 V and cannot be.

### What I attacked, and what broke

**Three ifs, and the repository pins none of them.**

**(a) The injection point is stated twice, differently, in the same ADR.**
`docs/decisions/0003-breath-sensing-path.md:514`:

> **one channel drives a firmware-controlled DC offset into the module's analog
> summing stage.**

and ~80 lines later, the same document:

> **The zero is injected at the module, into the in-amp's `REF` pin, from DAC
> channel 6.**

ADR 0006 picks the REF pin; ADR 0003 says both. The module *has* a summing stage
— ADR 0006 puts a panel offset knob after the gain knob, and an offset summer is
conventionally inverting. **A positive 0–5 V DAC voltage into an inverting
summing node subtracts.** Under the first of ADR 0003's two stated injection
points the finding does not exist. Neither agent noticed the contradiction;
B9 looked for it (its fix (b) is exactly this) without realising the ADR already
says it.

**(b) Neither agent claimed the input polarity was established.** B9 finding 1,
verbatim: *"**Medium-high** that BREATH is the + input … If the polarity is
already the other way round, the finding evaporates and the design is fine."*
B1 finding 4: *"**Medium** on whether the author already intends an inverting
receiver arrangement."* The register promotes this to `[verified]` showstopper
status and deletes both caveats. That is the register's error, not the agents'.
An inverting receiver plus an inverting gain stage costs nothing — B9's own
preferred fix (a) is exactly that, and it needs no new parts.

**(c) The "split-brain" sub-claim is false on ADR 0006's own text.** ADR 0006
says *"the **trimmer** is the offset authority for pitch, the **DAC channel** is
the offset authority for the mod channels, and **neither channel group has
both**."* Breath is not in that sentence. Breath is *designed* to have two offset
authorities with separated roles — DAC ch 6 technical, panel knob musical — and
B9 finding 10 independently confirms the chosen order (zero before the gain knob)
is the correct one. So the "conscripted into the technical role" objection is
weak: the knob is downstream of a stage that was always going to carry a
technical null.

**(d) The "cannot correct warm-up drift in the direction it needs" clause is
unsupported and probably backwards.** B2 asserts subtract-only is *"the only
direction a warming gauge sensor drifts in a sealed body"*. Nothing in the
repository or the part's stated behaviour establishes the sign of the offset
tempco, and it is small (order ±1 % VFSS ≈ ±0.1 V at the jack against a 0.44 V
pedestal). Meanwhile the dominant thermal mechanism ADR 0003 itself identifies —
a cavity or reference port that seals as it warms — drives the reading
**negative**, which needs REF to go **positive**, which the unipolar channel can
do. So the one warm-up mechanism this design documents in detail is correctable
with the authority it has.

**(e) It cannot be a showstopper by the review's own severity logic.** Both
agents' fixes are one op-amp half that the design already spends on ch 6's
buffer, plus two resistors, on the module — the board that opens with four
screws. B2: *"This costs **no extra op-amp**."* Compare S1, which blocks a PCB
that gets bonded shut.

### Verdict

**UNDERSPECIFIED-NOT-WRONG.** The arithmetic is correct and I reproduce it. The
design defect is that *four* facts — which input BREATH drives, whether the
downstream stage inverts, which of two stated injection points is real, and
whether the gain pot can amplify — are absent, and at least two combinations of
them make the finding vanish. What must be fixed is a drawing, not a circuit.
The one thing that *is* certainly wrong is ADR 0006's power-on row (see collapse
note with #2). **Confidence: high.**

**Falsifying bench test** (both agents converge on this, correctly): power the
module and instrument, blow nothing, sweep DAC ch 6 across its code range and
watch the jack. If 0.000 V is reachable at any code, the finding is void.

---

## 2. "The in-amp has no common-mode bias return" — SURVIVES BUT DOWNGRADED

### What holds

A resistor *between* two inputs constrains only their difference. The BOM carries
`R-PD-BREATH` qty **1**, "DIFFERENTIAL across BREATH-AGND not one leg", and ADR
0003 forbids the single-leg shunt that would have provided a return. With the
umbilical unplugged, both in-amp inputs are on stray capacitance only. At
1 nA into 20 pF that is 50 V/s; the common-mode range is gone in well under a
second. **The network as specified cannot do the job ADR 0005 assigns it.** That
much survives cleanly, and the two-resistor fix (1 MΩ per leg to module analog
ground, series resistance symmetrised) is right.

ADR 0003's 19 dB figure for a single-leg shunt also re-derives: 100k/(100k+10k)
= 0.9091 → 20·log₁₀(1/0.0909) = 20.8 dB. The ADR is right about *why* it forbade
the leg shunt; it is the conclusion it drew that is incomplete.

### What I broke

**(a) "Switching the instrument off does this every time" is FALSE.** The
register says this; neither agent does. B2 says *"When the cable is unplugged"*;
B9 says *"With the umbilical out"*. Trace the off-but-plugged case: the panel
toggle drives the load switch on **+12 V only** (ADR 0005). Grounds are never
broken. AGND runs to the instrument's analog star, which is bonded to instrument
ground, which returns down PWR_GND to the module. **The bias return exists
whenever the cable is plugged, powered or not** — and in that state the
unpowered buffer's output is high-impedance, the 100 kΩ differential resistor
holds BREATH ≈ AGND, the differential input is ~0 and the output is REF ≈ 0.
**ADR 0005's stated purpose is achieved in exactly the state it names.** The
failing states are: cable unplugged with the module powered, and a broken AGND
conductor in a cable the design calls a consumable. Both are real; neither is
"every time you switch off".

**(b) "The breath jack goes to a rail" is not derivable.** Both agents assert
saturation to ~±10 V. At the specified G ≈ 2.13 the three-op-amp in-amp's output
is `(A1 − A2) + V_REF`, and when the common mode runs out of range both input
buffers slam toward the *same* rail. The deterministic part of the analysis gives
`V_REF + (mismatch between two saturated buffer outputs)` — which is
indeterminate but is not forced to a rail by any gain in the stage. The inputs
also do not run away indefinitely: the in-amp's input protection clamps them
near V+ + 0.7 V. "Output indeterminate, certainly not 0 V, plausibly a few volts,
possibly a rail" is what the physics supports; "a fully open VCA held
indefinitely" is an empirical expectation borrowed from the classic app-note
statement, not arithmetic. B9's own fix rationale does not need the rail claim.

**(c) B2 and B9 disagree about the circuit they are both reviewing.** B2 finding 5:
*"the module end of the analog pair has no series resistance and no clamp"*. B9
finding 2 proposes placing bias resistors *"on the connector side of the 10 kΩ
protection resistors"* at the module. B2 computes the pulldown attenuation as
100/110 = 9.1 %; the register's own errata section says *"against the 10 kΩ
series resistors in each leg"* → 17 %. **The repository specifies one series
resistor, at the instrument end, on the BREATH leg only** (ADR 0003: "the
instrument end needs only a buffer … with a series resistor for protection").
So 9.1 % is the supported number and the register's 17 % is unsourced. This is
another instance of the same disease as #1: two competent readers built two
different schematics from the same prose.

### Verdict

**SURVIVES BUT DOWNGRADED.** Real defect, two-resistor fix, but the trigger is
"unplugged or broken AGND", not "switched off", and the output behaviour is
indeterminate rather than rail-pinned. **Confidence: high** on the defect, **high**
on the falsification of the "switched off" trigger, **medium-high** on the
saturation-magnitude critique.

---

## 3. "The anti-alias filter is at 121 Hz, not 600 Hz" — SURVIVES (gloss OVERSTATED)

### Independent arithmetic

`R-ADCDIV` = 10 k / 15 k gives 15/25 = 0.600 ✓. The cap sits at the ADC pin, so
the pole is against the Thévenin source:

| C | R_th | f₃dB | τ | Attenuation at 500 kHz |
|---|---|---|---|---|
| **220 nF (as specified)** | 6.00 kΩ | **120.6 Hz** | 1.32 ms | **72.4 dB** |
| 47 nF | 6.00 kΩ | 564 Hz | 282 µs | 58.9 dB |
| 4.7 nF (B1's proposal) | 6.00 kΩ | 5.64 kHz | 28 µs | 38.9 dB |

The ADR asserts *two* numbers, "~600 Hz corner" and "58 dB at 500 kHz". They are
simultaneously true only at ~47 nF and **neither** is true at 220 nF. No single-leg
reading rescues it (10 kΩ → 72 Hz, 15 kΩ → 48 Hz). To get 600 Hz with 220 nF
needs R_th = 1.21 kΩ, which the same paragraph forbids on ESD-clamp grounds.
**The finding is unambiguous and I confirm it at very high confidence.**

### What I attacked

**(a) The "transcription error" framing is an inference, not a verification.** It
is a *good* inference — 47 nF makes both published figures true, which is strong
circumstantial evidence — but it is the main session's addition, not the agents'.
B1, which found this independently, proposes **4.7 nF** on performance grounds
and would reject 47 nF as still costing 282 µs of delay on the note-onset path
for stopband nobody needs. Restoring the "intended" value would restore a value
that was itself chosen against an unquantified threat. B1 quantifies the threat
and gets **~0.2 LSB of buck residue before any filtering at all** — the cap is one
to two orders of magnitude more filter than the job needs. So: fix the number,
but do not fix it *to 47 nF because that makes the ADR self-consistent*. Pick it
on merit.

**(b) "Wrong by an order of magnitude" about the settling claim is the wrong
attack.** The ADR sentence — *"Together with the divider it settles well inside
the 250 µs loop period"* — has a reading under which it is true, and B1's own
Confirmation C2 supplies it: the thing that must settle in a loop period is the
MCP3202's sample-capacitor charge redistribution, not the filter's step response.
B1 computes the bare 6.00 kΩ divider settles the sample cap with 27 % margin and
**no reservoir cap at all**. The sentence is ambiguous and conflates two
settlings; it is not simply false.

**(c) Scope containment.** `C-AA-ADC` is on the **divided ADC branch inside the
instrument**. The umbilical branch stays full scale. So the 1.32 ms buys nothing
on the analog CV path — it lands only on note gating, MIDI, the display and the
mod-channel modulation source. The register's placement of this under "Major —
things that are wrong" alongside the CV-path findings invites the reading that
breath CV is delayed. It is not.

**(d) The 1.32 ms onset penalty is a ceiling, not a typical.** A single pole
delays a *threshold crossing* by `τ·ln(A/(A−T))` for a step of amplitude A and
threshold T — 0.105τ (139 µs) at T/A = 0.1, 0.36τ at T/A = 0.3. It approaches τ
only for a ramp long compared with τ, which a 5–15 ms tongue attack roughly is.
So B1's τ estimate is fair as a worst case; the honest range is ~0.5–1.3 ms
depending on how low the note threshold sits relative to the attack's peak.

### Verdict

**SURVIVES.** Arithmetic confirmed independently, very high confidence. The
consequence is real but confined to the digital copy, is 0.5–1.3 ms rather than a
flat 1.32 ms, and the "settles inside 250 µs" sub-claim is ambiguous rather than
wrong. The "transcription error, 47 nF restores it" gloss is **OVERSTATED** — the
evidence is circumstantial and the recommended value should be 4.7 nF on B1's
quantified argument.

---

## 4. "The in-amp has no gain resistor in the BOM" — SURVIVES BUT DOWNGRADED

### What holds

There is no `R_G` row. `U-DIFFRX` says "Absorbs the ~2.13x gain stage" and an
in-amp with R_G open is G = 1. Confirmed by inspection of `hardware/bom.csv`.

### What I attacked

**(a) "So as specified it is unity gain and the 2.13× scaling stage does not
exist" is a rhetorical framing of a BOM gap.** G = 1 with R_G omitted is the
part's *defined, safe* default, not a malfunction. The originating agent (B9
finding 8) rated this **MINOR**; the register files it under "Major — things that
are simply missing". It is also one row in a class the register itself counts at
34 (M4), on a module that opens.

**(b) The interesting content is not the missing row — it is that the value
cannot be computed from the repository.** Required gain depends on three
unspecified facts:

| Assumption | Required total gain | R_G at 49.4 kΩ (INA821) |
|---|---|---|
| Pedestal nulled, no link attenuation | 10/4.50 = **2.222** | 40.4 kΩ |
| + one 10 kΩ series leg (0.909) | **2.444** | 34.2 kΩ |
| + two 10 kΩ series legs (0.833) | **2.667** | 29.6 kΩ |
| B2's figure (VFSS 4.6, 0.909) | 2.39 | 35.5 kΩ |

B9 specifies 40.2 kΩ, which is right only for the first row. And whether the
shortfall is recoverable depends on a fourth unspecified fact: B9 assumes the
panel gain pot is a divider and can only attenuate, so under-gaining is
permanent; B9's *own* finding 10 proposes putting the pot in the feedback path,
in which case it can amplify and the exact R_G stops mattering. **The stated
2.13 is wrong under every assumption** (it treats the pedestal as signal), which
is the durable part of the finding.

**(c) The "INA821 or INA828 is unresolved, which blocks it" claim overstates the
coupling.** The gain equations differ by ~1 % (49.4 kΩ vs 50 kΩ); at G ≈ 2.2 the
same resistor gives 2.229 vs 2.244. That is inside the gain knob's range and
inside the trim the channel already gets. The part choice is not what blocks the
value; the four unwritten topology facts are.

### Verdict

**SURVIVES BUT DOWNGRADED** to a BOM-completeness item whose real content is that
the value is uncomputable from the repository and the stated 2.13 is wrong.
**Confidence: high.** Collapses into the structural finding below.

---

## 5. "The continuous auto-zero conceals the sensor faults it was added to absorb" — SURVIVES BUT DOWNGRADED

### What holds, and gets stronger

The concealment argument is structurally sound and I can sharpen its best case.
ADR 0003 specifies an E2 acceptance test that depends on being able to see drift:

> **The E2 warm-up check catches it.** … watch for output that falls rather than
> drifts. A falling output under warming is a blocked reference chamber.

ADR 0006's auto-zero decays the zero toward the current reading. **Run E2 with
the auto-zero enabled and the falling output is nulled as it falls** — the
instrument presents as perfectly zeroed and unresponsive, and the diagnostic
signature ADR 0003 relies on is erased by a mechanism ADR 0006 specified three
documents later. That is a genuine cross-ADR interaction and it is the strongest
version of this finding. Neither document notices. The fix (gate the decay on
"sub-threshold AND quiet", log the correction, bound it against the commissioning
value) is firmware-only and free.

### What I broke

**(a) "A blocked restrictor" is FALSE as an item in this list.** A clogging PTFE
plug is a *bandwidth* fault: it slows the step response and changes nothing about
the zero. The auto-zero cannot conceal it because it never presents as zero
movement. Checking the source: D4 finding 3 lists *"a partially blocked
**reference port**, a cavity sealed more than assumed, a slow leak, a shifted
offset"*. The register substituted "restrictor" for "reference port". The
restrictor-clog failure is real but is a **separate** finding (D4 #9, B1 #6) with
a different detector (first-attack rise time). The register's W11 as written
names a fault its own mechanism cannot hide.

**(b) "Re-zeros during a circular-breathing catch-breath" is FALSE.** A circular
breath maintains mouth pressure with the cheeks — that is the definition of the
technique, and on a dead-ended tube cheek pressure is transmitted identically to
diaphragm pressure. The catch-breath is ~0.2–0.5 s in any case, against a rule
that requires ~2 s sub-threshold. The design scope explicitly says the player
circular-breathes; the mechanism that makes it work is the one that makes this
sub-claim not fire.

**(c) The pianissimo clause is UNDERSPECIFIED rather than true.** ADR 0006 already
guards it: *"Slow enough that it cannot chase a held note."* The decay time
constant is never given anywhere. Whether a sustained sub-threshold passage
causes a ratchet depends entirely on that unspecified τ. The *ratchet mechanism*
the finding identifies is real and worth writing down (each re-zero raises the
effective threshold, so the effect accumulates across a session) — but as stated
it assumes a number nobody has chosen.

**(d) Severity.** D4 rates this Critical. Concealment is *inherent to any
drift-correcting servo* and is the mechanism's purpose; the gap is that nothing
logs or bounds the correction. That is a diagnostics omission with a free fix on
a board that is reprogrammable forever, not a design fault.

### Verdict

**SURVIVES BUT DOWNGRADED.** Core argument holds and the E2-interlock version is
better than the one filed. One of the three named faults is false, the
circular-breathing clause is false, the pianissimo clause is contingent on an
unspecified time constant. **Confidence: medium-high.**

---

## 6. "The zero correction is open-loop across two representations" — SURVIVES BUT DOWNGRADED

### What holds

Structurally true and correctly traced: the ADC taps the divided buffer output
*inside* the instrument; the correction is injected at the module, downstream of
2 m of cable, the in-amp, the knobs and the output filter. Nothing closes the
loop. Everything past the tap is unobserved. That is a real architectural
consequence of analog-to-the-jack that no ADR states.

### What I attacked

**(a) Quantitatively it is small except in the cases that are other findings.**
The error sources between the two representations are static and calibratable: a
5 % error in the assumed in-amp gain leaves `0.200 × 2.22 × 0.05` = **22 mV at
the jack, 0.22 % FS**, after nulling. The *gross* failures D4 lists — "if the
sign is wrong", "if ch 6 was never enabled" — are finding #1 and the DAC
reference-enable trap ADR 0006 already documents. Strip those out and what
remains is sub-1 % of span.

**(b) It is the same hole as three other findings.** "Nothing observes the
module's analog output" is D4 #6 ("nothing ever learns whether the module did
what it was told"), is the register's W10 free-comparator proposal, and is what
#7's mute would also want to verify. One module-side sense point closes all of
them. As a distinct *finding* it is close to a duplicate; as a *requirement* it
is one line.

**(c) Its own "ADD" is already satisfied.** D4 #5 asks for *"one line in ADR
0003: state explicitly that the in-amp precedes the gain knob."* ADR 0006 already
orders the chain gain-then-offset downstream of the receiver, and B9 finding 10
independently confirms the order is the correct one (`gain × 0 = 0` at any knob
position, so the null survives the knob). The stated remedy is mostly already
there.

### Verdict

**SURVIVES BUT DOWNGRADED.** True and worth one sentence in ADR 0003 plus a
bounded-code check in firmware; not a showstopper, and it is one third of a
finding the review makes three times. **Confidence: high.**

---

## 7. "Nothing mutes breath when the watchdog fires / brown-out window" — SURVIVES, with one FALSE clause

### Main clause: SURVIVES

`CLR` from the 74HC123 reaches the DAC. Breath never enters the DAC. In the exact
failure the watchdog exists for — real-time board hangs, instrument still powered
— the sensor, REF5050 and both OPA2197 halves are alive and the jack carries a
live signal. Confirmed by inspection; three agents converge; there is no
alternative reading. ADR 0004's own principle ("a stuck CV is worse than a dead
one") is violated on the primary expressive channel. Fix is one FET or one
4066 gate on the same watchdog output. **Confidence: high.**

### Brown-out clause: SURVIVES and is UNDERSTATED

B6 brackets the window as 8.0 V (buck UVLO, so both MCUs die and the watchdog
parks pitch and mods) down to 7.2 V, and calls it "a 1.2 V window". Using B6's
*own* cited figures, the REF5050 holds regulation down to **5.2 V** input and the
OPA2197 runs from 4.5 V. So the window where breath is live and everything else
is parked is **8.0 → 5.2 V, ~2.8 V wide**, not 0.8–1.2 V. The finding is
conservative.

But two mitigations the review does not mention: (i) for most of that window the
LED strips are also dark, so the instrument is *visibly* dead while breath is
live — there is an annunciation channel; (ii) as a steady state it requires the
rail to *dwell* in that band, which 0.34 Ω of cable cannot produce from IR drop
alone (it would need ~12 A). The plausible routes are a foldback-limiting load
switch (which is S7's finding) and a degrading connector, not ordinary sag. As a
power-on/power-off transient it is a few milliseconds every cycle.

### "CLR simultaneously removes its zero" — FALSE, and it contradicts finding #1

This clause cannot be true at the same time as finding #1, and the register
asserts both.

- If #1 is real (REF unipolar, BREATH on IN+, no downstream inversion), then
  firmware's best achievable null **is code 0** — it wants negative and cannot
  go there. `CLR` sets code 0. **`CLR` is a no-op for breath.**
- If instead the panel offset knob has been conscripted to over-subtract and
  firmware sits at a *positive* ch 6 code to bring the floor back to zero, then
  `CLR` → 0 V **drops** the floor below zero — it closes the VCA harder. Safe
  direction.
- The clause is only true in the world where #1 is false: an inverting receiver
  with REF resting at a positive null, where `CLR` → 0 restores the pedestal.

So D3 #11's `breath floor = 2.13 × 0.20–0.26 V = 0.43–0.55 V` on watchdog fire is
computing the floor that is *already there* under #1, not an additional insult.
**Fixing #1 creates this sub-finding; it does not currently exist.** That is a
genuine "fixing one breaks another" coupling and it should be recorded as a
constraint on #1's fix: whichever injection topology is chosen must park breath
*closed*, not *open*, when ch 6 clears.

### Verdict

**SURVIVES** on the main clause and the brown-out window (which is wider than
claimed). The "CLR removes its zero" clause is **FALSE as the design stands** and
is mutually exclusive with finding #1. **Confidence: high.**

---

## 8. "The Helmholtz tube model is invalid" — SURVIVES, strengthened, with two corrections

### The cleanest test, which nobody in the review used

The lumped Helmholtz model requires the neck to be acoustically short: `kL ≪ 1`.
At the ADR's own claimed 214 Hz over its own 400 mm:

```
kL = 2π·214·0.400/343 = 1.568 rad ≈ π/2
```

**The "neck" is exactly a quarter wavelength long at the frequency the model is
being used to predict.** This is a cleaner disproof than B1's volume-ratio
argument (V_neck 2.83 mL > V_trap ≤1 mL) because **it does not depend on the
bore**, which the repository never specifies. High confidence, no assumptions.

### And the ADR's own table was already using the right model

- `c/4L` at L = 0.400 m, c = 343: **214.4 Hz** — the ADR's "214 Hz" exactly.
- `c/4L` at L = 0.030 m: **2858 Hz** — the ADR's "2858 Hz" exactly.

**Both rows of the table labelled "Helmholtz" are quarter-wave numbers.** The
only genuinely Helmholtz figure in the document is the prose's 320 Hz, and B1 is
right that it requires a ~7.2 mm bore (I reproduce 7.25 mm at c = 343). So the
error is narrower and odder than "the model is invalid": the ADR *computed*
quarter-wave, *labelled* it Helmholtz, then wrote a paragraph declaring
quarter-wave to be the wrong model and replacing it with a number from a
different tube.

### What the boundary conditions actually are, and the trap-volume lever

Solve the real problem — a tube of length L terminated at the sensor end by the
trap compliance V, with the mouth end either a low impedance (the oral cavity:
for a 3 mm bore, |Z_cavity| at 30 mL is ~3.6e6 against the tube's Z₀ = 5.8e7, so
**17× lower — the mouth end is much closer to pressure-release than to rigid**)
or rigid:

| | trap 0.2 mL | trap 1 mL | trap 3 mL |
|---|---|---|---|
| Mouth low-Z, 3 mm bore | 200 Hz | **161 Hz** | 115 Hz |
| Mouth low-Z, 6 mm bore | 211 Hz | 197 Hz | 171 Hz |
| Mouth rigid, 3 mm bore | 401 Hz | **332 Hz** | 274 Hz |
| Mouth rigid, 6 mm bore | 421 Hz | 395 Hz | 348 Hz |

Three results:

1. **`c/4L` = 214 Hz and `c/2L` = 429 Hz are ceilings approached as V → 0, not
   values.** Adding trap compliance always *lowers* the resonance. So the ADR's
   lever is not merely ineffective, **it points the right way and cannot
   reach**: shrinking the trap does raise f, asymptotically, toward a ceiling
   that is itself less than half the 500 Hz target.
2. **The bore does not change the verdict.** It moves the number by 20–40 Hz
   within the bracket (toward the ceiling as the bore grows). No bore, no trap
   volume, and no combination of the two gets a 400 mm tube above 500 Hz. The
   only lever on the *frequency* is length: `L ≤ 172 mm` for the low-Z case,
   `≤ 343 mm` for the rigid case, and less than both once the trap loads it.
   B1's 175 mm fallback is right.
3. **The review's own bracket is wrong at both ends.** B1 gives "219–437 Hz" by
   using unloaded ideal ends; the register repeats it as "214–429 Hz". With the
   trap the design actually specifies (≤1 mL, 3 mm bore), the real range is
   **161–332 Hz**, and at 161 Hz it lands essentially *on* the sensor's own
   159 Hz corner — which means the sensor rolls it off by only 3 dB and the
   500 Hz electrical filters by ~0.4 dB. The resonance passes, as claimed.

### "No restrictor size fixes it" — OVERSTATED

True of the *frequency*; false of the *problem*. A resistive restrictor between
the tube and the trap is a termination, and when its resistance approaches the
tube's characteristic impedance the reflection coefficient goes to zero and there
is no standing wave to speak of. For a 3 mm bore, Z₀ = 5.82e7 Pa·s/m³, and by
Poiseuille a **0.40 mm × 2 mm orifice gives R = 5.73e7** — matched to within 2 %.
B1's independently derived "0.34 mm × 2 mm for a 200 Hz pneumatic corner" comes
out at 1.10e8 ≈ 1.9 Z₀, reflection coefficient 0.32. **The same plug that sets
the first-order corner also terminates the tube near its characteristic
impedance.** So the restrictor absolutely can fix the resonance — by damping, at a
cost of 0.3–1.1 ms of added delay, which is the trade that belongs in the latency
budget.

### Verdict

**SURVIVES** and is strengthened. Corrections to file with it: the ADR's table was
already quarter-wave; the mouth end is closer to pressure-release than to rigid
for any realistic bore; the loaded bracket is 161–332 Hz not 214–429 Hz;
shrinking the trap is directionally right but cannot reach; the bore changes the
number and not the verdict; and "no restrictor size fixes it" should read "no
restrictor size *moves* it — damping is the only lever, and the specified PTFE
plug can supply it." **Confidence: very high** on the model invalidity and the
ceiling argument, **medium-high** on the specific loaded frequencies, which depend
on a bore and a mouthpiece the repository does not specify.

---

## Where findings collapse

### The dominant collapse: five findings, one missing drawing

**Findings 1, 2, 4, 6 and the second clause of 7 are all symptoms of the fact
that the module's breath stage has never been drawn.** The repository specifies
its parts and none of its topology. Specifically unspecified:

- which in-amp input BREATH drives (→ #1, and the sign of the whole channel)
- whether the downstream gain/offset stage inverts (→ #1)
- which of ADR 0003's **two mutually exclusive stated injection points** is real —
  "the module's analog summing stage" (line 514) or "the in-amp's REF pin" (→ #1, #6)
- how many series protection resistors there are and at which end (→ #2's
  attenuation, and B2/B9 disagree; 9.1 % vs 17 %)
- what, if anything, references the inputs to module ground (→ #2)
- whether the gain pot is a divider or sits in feedback (→ #4's recoverability)
- what R_G is (→ #4)
- whether anything can mute the stage (→ #7)

Two independent expert readers (B2, B9) built two different schematics from this
prose and disagreed about the resistor count, the attenuation, and where the
module-end network lives. **One schematic page in ADR 0003 answers all eight
questions and dissolves or re-grounds five findings.** That is the action item,
and it is cheaper and more urgent than any of the individual fixes proposed.

### #1 and #2 collapse onto one consequence, by two mechanisms

Both independently falsify **ADR 0006's power-on row "Breath | 0 V | the
receiver's differential pulldown holds it there"** and ADR 0005's "switched off —
or unplugged — presents 0 V":

- instrument **on**, before firmware writes → 0.444 V, by #1
- instrument **unplugged**, module on → indeterminate, by #2
- instrument **off but plugged** → genuinely 0 V, which is the case ADR 0005
  actually names and the one both findings get wrong when they generalise

Fixing either one leaves the row false. The row needs rewriting for three
distinct states, not one. This is a shared *consequence*, not a shared cause —
the fixes do not substitute for each other.

### #1 and #7 are mutually exclusive as stated

See §7. `CLR` can only "remove the zero" in the world where #1 is false. The
register asserts both as verified. Fixing #1 *creates* the #7 sub-finding, which
makes "park breath closed when ch 6 clears" a constraint on #1's fix rather than
a separate defect.

### #6 is one third of a finding made three times

"Nothing observes the module's analog output" = W12 = D4 #6 = W10's free
comparator. One module-side sense point closes all three.

### #5's "blocked restrictor" belongs to a different finding

The restrictor-clog failure is D4 #9 / B1 #6 (wetted plug, attack time drifts),
detected by first-attack rise time, not by zero bounds. It was pulled into W11
by a transcription slip and does not belong there.

### #3 stands alone

Nothing else in the cluster depends on it and it depends on nothing else. It is
also the only finding in the eight whose arithmetic is beyond argument.

---

## Two notes on the register rather than the design

1. **Caveat stripping.** On #1, both originating agents rated the topology
   assumption "medium" / "medium-high" and both wrote out, explicitly, the
   condition under which the finding evaporates. The register records it as
   `[verified]` and a showstopper. On #4 the agent rated it MINOR; the register
   files it as Major. On #2 the register added "switching the instrument off does
   this every time", which neither agent wrote and which is false. The register's
   own pattern note — *"a stated number in this repository is not yet a verified
   one"* — now applies to the register.

2. **`[verified]` is doing two jobs.** On #3 it means "I redid the arithmetic and
   it is unambiguous". On #1 and #2 it means "I redid the arithmetic *given the
   agent's assumed topology*". Those are different claims and the marker does not
   distinguish them. Every finding in this cluster that survived unconditionally
   (#3, #7 main clause, #8) is one where the repository states enough to make the
   reading unique. Every finding that downgraded (#1, #2, #4) is one where it does
   not.
