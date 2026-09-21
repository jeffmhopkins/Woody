# C4 — Module power entry: cold circuit review

**Reviewer:** cold pass, 2026-09-21. No `docs/review/` or `docs/research/` was read.
**Subject:** `hardware/module/power-entry.md`, line by line; then
`docs/decisions/0005-power-architecture.md`, the power sections of
`docs/decisions/0004-cv-interface-module.md`, and the `hardware/bom.csv` rows
that page depends on.

## Evidence markers

Every load-bearing statement below carries one of:

- `[repo]` — read out of a named file in this repository.
- `[calc]` — arithmetic done here, shown in full.
- `[datasheet]` — a device parameter. **`ti.com`, `analog.com`, `nxp.com` and
  every distributor were blocked from this sandbox.** No datasheet figure is
  stated as fact. Where a device parameter is needed, it is named, the
  conclusion is gated on it, and the gate is repeated in
  "[What is gated on a datasheet](#what-is-gated-on-a-datasheet)".
- `[from memory]` — recalled, not verified, and treated as a hypothesis that
  changes the conclusion if wrong.

The brief notes this project's confidence markers have twice been found
calibrated backwards. **Finding C4-01 is an instance of exactly that** and it
is the most important thing in this document.

## Inputs, and where each number comes from

| Quantity | Value | Source |
|---|---|---|
| Instrument bulk capacitance | 2.2 mF worst / 1.14 mF min | `power-entry.md`; `bom.csv` `C-BUCK-IN` = 100 µF ×2, `C-STRIP-BULK` = 470–1000 µF ×2 `[repo]` |
| Umbilical current, quiescent / typical / clamp-legal worst | 212 / 359 / 579 mA | ADR 0005 load table `[repo]` |
| Cable round-trip resistance, 2 m 24 AWG | 0.34 Ω | ADR 0005 `[repo]` |
| Sense resistor / limit | 50 mΩ, 1.0 A nominal | `power-entry.md`, `bom.csv` `R-ILIM` `[repo]` |
| Ramp / fault timer | ramp "50–100 ms" (ADR 0005), timer "≈50 ms" (`power-entry.md`) | `[repo]` |
| Module analog +12 V draw | ~45 mA incl. the DAC regulator | ADR 0004 `[repo]` |
| LM317 divider | 150 Ω (OUT–ADJ) / 475 Ω (ADJ–GND), 0.1 % | `bom.csv` `R-REG-SET` `[repo]` |
| Buck UVLO | R-78E5.0 needs "more than 6 V in"; 6.5 V assumed | ADR 0004 `[repo]` + `[from memory]` |

## Repo state note — the tree moved during this review

`hardware/bom.csv` was edited by a concurrent process **while this review was
being written**. Two of the rows this document cites changed under it, and the
change is recorded rather than quietly absorbed:

- **`R-OE-PU` now reads "to bus +5V" / "the 74AHCT125's OWN bus +5V rail".**
  When this review began it read "**FROM THE LM317'S 5.21V, NOT BUS +5V**".
  **C4-06 is therefore resolved in the working tree** for the BOM half. It is
  kept below in full because (a) the analysis of *why* 5.21 V is the wrong rail
  is what justifies the fix and is not written down anywhere else, and (b) the
  other half of C4-06 — `power-entry.md` L149–151 putting the **comparator** on
  5.21 V, which is C4-07 — is **unchanged and still wrong**. `power-entry.md`
  has not been modified at all during this session.
- **A `C-TIMER-LOADSW` row was added** (10 nF C0G, "value from the LT1641
  fault-timer equation"). That closes half of C4-21's missing-parts point. **No
  gate/ramp capacitor row exists**, so the other half stands and is now
  sharper: the component that sets the fault timer has been ordered, and the
  component that sets the ramp — the number C4-02 and C4-04 turn on — has not.
  The new row's own note says the timer "must outlast a current-limited start
  into the instrument", which is exactly the constraint C4-02 shows is violated
  at ~50 ms once foldback is programmed.

Everything else below was checked against the tree as of writing. Line numbers
into `bom.csv` are approximate for the same reason; the rows are named.

---

## Severity table

Scale: **S1** the circuit does not work as specified, or hardware is damaged.
**S2** a real failure mode with no mitigation, or a load-bearing claim that is
wrong. **S3** worth fixing before layout. **S4** note.

| # | Sev | Finding | Where |
|---|---|---|---|
| C4-01 | **S2** | The "20 cents of breath-correlated pitch bend" that justifies `D2` is a fossil of the **deleted** ±12 V offset divider. In the topology that is actually specified it is ~0.003 cents. Three documents cite it; it is marked "visible by inspection" and "four reviewers, four routes". | `power-entry.md` §"Three diodes"; ADR 0004 ~L296; `bom.csv` `D-REVPOL` |
| C4-02 | **S1** | **The fault timer and the foldback are mutually exclusive as specified.** A current-limited start into 2.2 mF is 29 ms with no foldback and **53 ms with 4:1 foldback** `[calc]`, against a ~50 ms timer. The page prescribes both. | `power-entry.md` L93–111 |
| C4-03 | **S1** | The specified **ramp window (50–100 ms) overlaps and exceeds the specified fault timer (~50 ms)**. A 100 ms ramp with a 50 ms timer cannot complete if it ever touches limit. | ADR 0005 L262 vs `power-entry.md` L98 |
| C4-04 | **S2** | "A normal start never enters current limit" is false at the tolerance corners: **0.74 A typical, 0.91 A at a fast ramp**, against a worst-case trip near **0.80 A** `[calc]`. The page's 0.53 A omits the instrument's own load current entirely. | `power-entry.md` L88 |
| C4-05 | **S2** | **Hot-plug of the live umbilical is unanalysed.** ~24 A first-contact surge `[calc]`, then a current-limited start that lands on the wrong side of the timer. The repo's own rebuttal ("12 V cannot arc") answers a mechanism that is not the hazard. | `power-entry.md` (absent); `docs/log/2026-09-20-review-resolution.md` L66 |
| C4-06 | **S2**, *fixed in tree mid-review* | **`R-OE-PU`'s rail was contradicted across the repo.** `bom.csv` said the LM317's 5.21 V; `power-entry.md` and `digital-and-supervision.md` both say bus +5 V; the `R-LED-PANEL` row asserted "same rail as `R-OE-PU`", which was false. Two pull-ups on one node, two rails. **Corrected in the working tree during this session** — see the repo state note. Analysis kept because the reasoning is not recorded elsewhere. | `bom.csv` `R-OE-PU` / `R-LED-PANEL` |
| C4-07 | **S2** | `power-entry.md` L149–151 puts **the comparator on the LM317's 5.21 V**, which re-creates precisely the defect `bom.csv` L99 was written to fix (a comparator that cannot see a negative input). Its own diagram and `digital-and-supervision.md` say ±12 V. | `power-entry.md` L149–151 |
| C4-08 | **S2** | **Rack power-down sequencing:** AVDD collapses at ~5 ms, the bus-+5 V buffer lives to ~14 ms, the LM311 holds `OE` low to ~8 ms `[calc]`. ~3 ms per power-down of 5 V logic driven into an unpowered DAC8568, up to three pins of clamp current. | derived from `power-entry.md` + `digital-and-supervision.md` |
| C4-09 | **S2** | **Loss of bus +5 V while the instrument plays:** the instrument's SCLK and CS drive the unpowered 74AHCT125's input clamps with **no series resistance** (`R-MOSI-SER` covers MOSI only), back-powering its VCC through a 47 µF cap to a partial rail, with `OE` unpulled. Marginal levels into a live DAC → the "sticky" mis-framed word. | `bom.csv` `R-MOSI-SER` qty 1; ADR 0005 "no fallback" |
| C4-10 | **S2** | The instrument's **2.2 mF is a local 0.16 J energy source the load switch cannot see** `[calc]`. ADR 0005's polyfuse-deletion argument ("downstream of the limiter, so it protects nothing") is inverted for a fault downstream of the bulk capacitance. | ADR 0005 L275–289 |
| C4-11 | **S3** | FET SOA is **asserted, not checked**. 12 W × 50 ms in a DPAK is at or over the line, and the *normal* start is 6.3 W × 50 ms on every power-on. With foldback deeper than 2:1 the **worst case is not a hard short** but an ~8 Ω fault at V_DS ≈ 8 V `[calc]`. | `power-entry.md` L99–105 |
| C4-12 | **S3** | **1N5817 is a 20 V part.** A +12/−12 swap presents 24 V of reverse bias. 1N5819 is the same DO-41 at the same price. | `bom.csv` `D-REVPOL` |
| C4-13 | **S3** | "A reversed ribbon kills the buffer and nothing else" is **incomplete**: `C4` on the unprotected bus +5 V entry is a 47 µF **aluminium electrolytic** with no reverse protection. | ADR 0004 L191–193; `bom.csv` `C-BULK-RAIL` |
| C4-14 | **S3** | **No `ON`-pin network at all**: no debounce RC, no pull-down, no series resistor, on a panel-wired high-impedance logic input that is also the latch reset for a latching part. | `power-entry.md` diagram L30 |
| C4-15 | **S3** | **One dark LED encodes four distinct conditions** (toggle off / instrument absent / breath front end dead / load switch latched). The LT1641's `FAULT` output is unused. `bom.csv` L82 claims the LED "says why the instrument went dark"; it says *that* it did. | `bom.csv` `LED-PANEL`; `power-entry.md` §"−1, not −2" |
| C4-16 | **S3** | **"≥1 A bead" is a thermal rating, not an impedance-at-bias rating.** `FB2` carries 0.58 A steady and 1.0 A in fault; at bias a 1 A-rated bead has little impedance left. The page's own rule ("read the series") stops one step short. | `power-entry.md` L62–66; `bom.csv` `FB-IN` |
| C4-17 | **S3** | The entry **LC is damped only by the electrolytic's ESR**, and nothing in the repo records that as a requirement. `ζ` = 1.7 with an electrolytic, **0.017 with a ceramic** `[calc]` — a Q≈30 resonance at 23 kHz on the analog rail. | `bom.csv` `C-BULK-RAIL`; `power-entry.md` |
| C4-18 | **S3** | The diagram commits to **one ground pin** for a 580 mA return. The header has several. The rack-return pitch term is 1.8–5.3 cents `[calc]` — the same size as, or larger than, the term the second diode was bought for. | `power-entry.md` L43, §Grounding |
| C4-19 | **S3** | `C-REG-ADJ` permits "**ceramic or tantalum**" for the LM317's 1 µF output cap. A 1 µF X7R at 5.2 V bias is ~0.6 µF of near-zero ESR on the rail that is the DAC's AVDD. | `bom.csv` `C-REG-ADJ` |
| C4-20 | **S3** | The cable-side `CS` pull-up **back-feeds the sleeping instrument through 10 kΩ** in what the repo calls the normal state (module alive, toggle off). | `bom.csv` `R-SPI-PULL`; ADR 0004 L346 |
| C4-21 | **S3** | **Diagram defects on the page whose thesis is "visible by inspection":** all four bulk caps drawn in series with their rails; `C2`'s node labelled `AGND`; an unmarked crossing at the FET source; no `V_CC`, no sense connections — and **no component anywhere in the repo sets the ramp rate** (the timer capacitor got a BOM row mid-review; the gate capacitor still has none). | `power-entry.md` L12–44; `bom.csv` |
| C4-22 | **S4** | Smaller points: "will not boot on a cold day" is backwards; the LM317 I_ADJ term the BOM bought 0.1 % parts for is dropped from the page's 5.21 V; the LED resistor is computed at 5.21 V and applied at 5.00 V with no colour specified; no shunt clamp on −12 V. | various |
| C4-23 | **S4** | The open item "**damping the input LC** … textbook negative-resistance instability" has **87× of margin** `[calc]` and can be closed on paper. The real thing at that node is a 2.32 kHz resonance sitting on the WS2815 PWM rate. | `power-entry.md` §Still open |

---

## C4-01 — The 20 cents is a fossil of a topology that was deleted

`power-entry.md` L48–56 `[repo]`:

> An earlier revision branched the two +12 V paths *after* a single shared
> Schottky, and four reviewers found the consequence by four different routes:
> the instrument's current then flows through the same diode as the module's
> analog rail and modulates its forward voltage by ~80 mV. That is about **20
> cents of breath-correlated pitch bend**, needing no ground path at all,
> visible by inspection of the diagram.

### The claim requires 13.6 dB of power-supply rejection

20 cents on a 1 V/oct output is `20/1200 V` = **16.67 mV** at the jack `[calc]`.
For 80 mV of +12 V rail movement to produce 16.67 mV at the jack, something in
the +12 V → jack path must have a rail-to-output transfer of
`16.67/80 = 0.208`, i.e. a power-supply rejection of

```
20·log10(0.080 / 0.01667) = 13.6 dB          [calc]
```

Nothing in the specified path is that bad. `hardware/module/pitch-stage.md`
gives the transfer function `[repo]`:

```
Vout = 2·Vdac − 2.500          with V_ref = buffered VREFOUT, R1 = R2 = 10k
```

Both terms come from the DAC's **internal 2.5 V reference at gain 2**, not from
any rail (ADR 0006, ADR 0005 L132–134 `[repo]`). The rail reaches the output
only through (a) the OPA2197's PSRR and (b) the LM317's line regulation into
AVDD, and AVDD is not the reference. Two-stage estimate `[calc]`, with each
device parameter gated:

| Path | Transfer | 80 mV becomes |
|---|---|---|
| +12 V → OPA2197 output | OPA2197 PSRR, ≥100 dB at DC `[datasheet — gated]` | ≤0.8 µV → ×2 = **1.6 µV** |
| +12 V → LM317 out → DAC ref → jack | LM317 line reg., worst-case spec ~0.07 %/V = 3.6 mV/V `[datasheet — gated]`; then DAC8568 AVDD-to-reference sensitivity | 0.080 × 3.6 mV/V = 0.29 mV on AVDD, then the DAC's own rejection |

Even assigning the DAC an implausibly bad 1 mV/V of AVDD-to-reference
sensitivity, the jack sees 0.29 µV × 2 = 0.6 µV. Total ≈ **2 µV ≈ 0.003
cents** — against a claim of 20 cents. **Four orders of magnitude.**

Note the argument does not depend on any blocked datasheet. It only requires
that no element in the chain has a PSRR as bad as 13.6 dB, and the page's own
sister document states the op-amps have "~90 dB of PSRR down there" (ADR 0004
L315 `[repo]`) — 90 dB is already 3,000× more rejection than the claim needs to
be false.

### Where the number actually came from

`pitch-stage.md` L95 `[repo]`: ADR 0006 moved the offset reference off the
±12 V rail "because a bare divider there costs **~22 cents p-p** of
LED-correlated FM".

That is a real mechanism, because a divider off the rail passes the rail
straight through. Work it backwards `[calc]`:

```
22 cents            = 22/1200 V          = 18.33 mV at the jack
∂Vout/∂V_ref        = −k = −1            (pitch-stage.md, k = R2/R1 = 1)
divider ratio       = 2.500 / 12.0       = 0.2083
rail movement       = 18.33 mV / 0.2083  = 88 mV
```

and forwards, from the quoted 80 mV `[calc]`:

```
80 mV × (2.500/12.0) × 1200 cents/V = 20.0 cents exactly
```

**The 20-cent figure is `80 mV × 2.5/12 × 1200`.** It is the shared-Schottky
ripple injected into *an offset reference divided down from the ±12 V rail* —
a component (`R-OFFINJ` and the rail divider) that ADR 0006 and
`pitch-stage.md` **deleted**. The reference now comes from buffered `VREFOUT`,
and with it the entire coupling path.

### Consequences

1. The stated justification for `D-REVPOL` qty 3 is void. It is repeated in
   `power-entry.md` L48–56, ADR 0004 ~L296, and `bom.csv` `D-REVPOL` `[repo]`,
   all three with maximum-confidence framing — "visible by inspection",
   "four reviewers … four different routes", "needs no ground path at all".
2. `power-entry.md` L504's sister claim — that the `PWR_GND` ground term "is
   the same shape as the shared-Schottky term fixed above, by a different
   path" — is **conceptually wrong and the error is instructive**. A ground
   offset adds to the output at unity gain; a rail offset is divided by the
   PSRR of whatever sits between. They are not the same shape, and that is the
   whole reason the ground term (5.7–7.2 cents, ADR 0004 L502) is real and this
   one is not. The project did this arithmetic correctly once, 200 lines later,
   in the same document.
3. **Keep `D2`. Delete the number.** The split is still right, for reasons the
   page does not give and which survive scrutiny: `D1` no longer carries
   0.58 A (it carries 45 mA, so 0.26 W of diode dissipation and ~200 mV of
   drop stay off the analog rail); the umbilical branch's fault transients —
   including `C2`'s 3.4 mJ dump through the sense resistor, C4-10 — are
   separated from the analog rail; and a single 1N5817 at 0.58 A steady plus a
   1.0 A ramp has no margin against its 1 A rating. Any one of those is worth
   twenty cents of diode. If the 20-cent figure is left standing, the next
   person to check it will find it false and may delete the diode with it.

---

## C4-02, C4-03, C4-04 — Re-deriving the load switch

### The page's own table is internally correct

`power-entry.md` L81–86 `[repo]`, reproduced `[calc]`:

```
50 ms ramp:   dV/dt = 12 V / 0.050 s              = 240 V/s          ✓ matches
              I_ch  = C·dV/dt = 2.2e-3 × 240      = 0.528 A          ✓ matches 0.53 A
              P_pk  = I_ch × 12 V (at t = 0)      = 6.34 W           ✓ matches 6.3 W
              E     = ½ × 6.34 × 0.050            = 0.1584 J         ✓ matches 0.16 J
100 ms ramp:  120 V/s, 0.264 A, 3.17 W, 0.1584 J                     ✓ matches all four
cross-check:  ½CV² = ½ × 2.2e-3 × 144             = 0.1584 J         ✓ identical
```

The "energy is the same either way" claim is **correct for a purely capacitive
load** and is a genuinely useful result. It needs one correction: with a real
load drawing `I_load` during the ramp, the FET's energy gains a
ramp-time-proportional term `≈ I_load × V̄_DS × t_active`. For the buck coming
alive at 6.5 V `[calc]`: `0.19 A × 2.75 V × 27 ms = 14 mJ` on a 50 ms ramp and
28 mJ on a 100 ms ramp — 9 % and 18 % of the total. The invariance holds to
about 15 %, not exactly.

### C4-04 — the start does not stay clear of the limit

`power-entry.md` L88 `[repo]`: "**A normal start never enters current limit** —
0.53 A against a 1.0 A limit". Two things are missing from both sides of that
comparison.

**The load side.** 0.53 A is the *capacitor charging current only*. Once the
output crosses the buck's UVLO the instrument starts drawing its own current.
ADR 0005 L157 gives 212 mA of quiescent umbilical draw `[repo]`. The FET
carries the sum `[calc]`:

```
0.528 A (charging) + 0.212 A (quiescent, once above UVLO) = 0.740 A
```

**The limit side.** `bom.csv` `R-ILIM` says it itself `[repo]`: "the stated
0.9–1.13 A window is ±11 % and is **NARROWER THAN THE LT1641'S OWN
SENSE-THRESHOLD TOLERANCE**". Take a sense-threshold tolerance of ±20 %
`[datasheet — gated; the LT1641's V_SENSE(th) spec could not be read]` on a
50 mV nominal with a 1 % resistor:

```
I_trip = 50 mV × (1 ± 0.20) / 50 mΩ = 0.80 … 1.20 A          [calc]
```

Worst case: **0.740 A of start current against a 0.80 A trip — 8 % margin.**

**And the ramp has tolerance too.** The ramp rate is `I_GATE / C_GATE`
`[from memory — this is how the LT1641 family programs dV/dt; the pin name and
the gate current are gated]`. A ±20 % gate current and a ±10 % capacitor give
up to +33 % on dV/dt:

```
0.528 × 1.33 = 0.702 A charging, + 0.212 A load = 0.914 A > 0.80 A    [calc]
```

**At the corner, a normal start enters current limit.** That is not
catastrophic by itself — it becomes one when combined with C4-02.

The fix is already in the page's own table and costs nothing: **program the
ramp at 100 ms, not 50 ms.** That gives 0.264 + 0.212 = 0.476 A against a
0.80 A worst-case trip (68 % margin), and halves the FET's peak dissipation
from 6.3 W to 3.2 W with no change in total energy.

### C4-02 — the timer and the foldback cannot both be had at ~50 ms

The page derives the timer floor from a *flat* 1.0 A limit (L95, `[repo]`):
"1.0 A into 2.2 mF to 12 V is **26 ms**". Confirmed `[calc]`:
`t = C·V/I = 2.2e-3 × 12 / 1.0 = 26.4 ms`. With the instrument's own quiescent
draw subtracted from the charging current, 29.2 ms `[calc]`.

Twelve lines later (L107–111, `[repo]`) the page says:

> **Program the foldback.** The LT1641 family reduces its current limit while
> the FET's drain voltage is high…

**Foldback keys on exactly the condition that obtains for the whole of a
current-limited start**: V_DS is at its maximum when V_OUT is at zero. The
26 ms was never redone with foldback in it. Doing it — numerical integration of
`dV/dt = (I_lim(V_DS) − I_load)/C` with a linear foldback characteristic and
the buck load appearing above 6.5 V `[calc]`:

| Foldback depth | No load | With 0.19 A load |
|---|---|---|
| none (flat 1.0 A) | 26.4 ms | **29.2 ms** |
| 2:1 | 36.6 ms | **40.4 ms** |
| 4:1 | 48.8 ms | **53.4 ms** |

**At 4:1 foldback the current-limited start is 53 ms and the timer is 50 ms.**
The instrument does not start; it latches off, and because the part is the `-1`
it stays off until somebody cycles the toggle. Two of the three columns are
inside 25 % of the timer, which is not a margin on a number derived from a
capacitance the BOM gives as a *range* (470–1000 µF ×2) and a load that ADR
0004 calls "the least trustworthy number in this document" `[repo]`.

**This is the page's central arithmetic and it is wrong in the direction that
bricks the instrument.** The two prescriptions — "timer ≈ 50 ms, comfortably
past 26 ms" and "program the foldback" — are mutually exclusive at these
values, and they are eleven lines apart.

**The resolution is better than either.** Take foldback *and* a longer timer:

```
4:1 foldback:  P(V_DS) = V_DS × 1.0 × (1 − 0.75·V_DS/12)
   V_DS = 12 V (hard short)  →  3.0 W
   V_DS =  8 V               →  4.0 W   ← worst case
   V_DS =  4 V               →  3.0 W                         [calc]
```

so the fault dissipation is genuinely "roughly flat" at 3–4 W — the page's
claim about foldback is correct — and a **120 ms timer** then costs
`4.0 W × 0.120 s = 0.48 J`, which is **less** than the page's own no-foldback
`12 W × 50 ms = 0.60 J`, while leaving 2.2× margin over the 53 ms start. That
is the coherent design: **foldback + 120 ms timer + 100 ms ramp**, in that
order of dependency.

### C4-03 — ramp ≥ timer as specified

ADR 0005 L262 specifies "a programmed **50–100 ms** ramp" `[repo]`.
`power-entry.md` L98 specifies "**Timer ≈ 50 ms**" `[repo]`.

A fault timer must be longer than the longest legitimate start. As written, the
top of the ramp window is **twice** the timer. Even at the bottom of the window
they are equal. Nothing in either document states the ordering constraint, and
the two numbers were evidently chosen independently — `power-entry.md` picks
50 ms for the timer by comparing it to 26 ms, never to the ramp it is also
specifying.

### The fault case

**Hard short at the instrument end** `[calc]`: the short sits behind 0.34 Ω of
cable, so `V_DS = 12 − 1.0×(0.34 + 0.05) = 11.6 V` → 11.6 W, essentially the
page's 12 W. **Short at the module's own output**: 12 W exactly. The page's
`12 W × 50 ms = 0.6 J` is right for its stated assumptions.

What the page does not cover:

- **`C2` discharges into the fault ahead of the controller.** 47 µF at 12 V
  into a short at the module's output: `E = ½ × 47e-6 × 144 = 3.4 mJ`, peak
  `12/0.07 ≈ 170 A`, τ ≈ 3 µs `[calc]`. Roughly 70 % of that energy lands in
  the 50 mΩ sense resistor, which `bom.csv` specifies as "0805 or 1206" with
  **no pulse rating and no tolerance** `[repo]`. At the far end of the cable it
  is milder (27 A peak, ~0.4 mJ in the sense resistor) but it is the
  module-terminal short that sizes the part. **Specify a pulse-rated sense
  resistor, 1206 or larger, and a tolerance** — noting `bom.csv` is right that
  the resistor's tolerance is dominated by the controller's threshold, which is
  an argument for measuring the trip at E6, not for leaving the part
  unspecified.
- **Repetitive faults.** The realistic fault here is a flexing or crushed
  consumable Cat5 lead (ADR 0004 §"the cable is a consumable" `[repo]`), i.e.
  an *intermittent* short. A fault that clears before the timer expires does
  not latch, and hot-swap controllers typically discharge the timer capacitor
  far more slowly than they charge it `[from memory — ratio gated]`, so
  repeated brief faults accumulate. The page analyses one hard short and stops.

### C4-11 — the FET

The page (L99–105, `[repo]`) says the FET must survive 12 W for 50 ms, that
SOT-23 cannot, and that DPAK or SO-8 "chosen against the part's single-pulse
SOA curve" can. The first two are right. The third is **asserted, not
checked**, and two things are missing:

- **The normal start is also an SOA event.** 6.3 W for 50 ms, 0.16 J, on every
  single power-on. The page treats the ramp as the benign case; it is 53 % of
  the fault energy and it happens thousands of times rather than once.
- **The worst-case fault is not the hard short.** With foldback deeper than
  2:1, `P = V_DS·I_lim(V_DS)` peaks at an intermediate drain voltage `[calc]`:
  at 4:1, at `V_DS = 6/(1−k) = 8 V`, which corresponds to a **~8 Ω fault** —
  a partially crushed conductor or a damaged strip, not a dead short. At 2:1
  the peak is at the short. **Which fault is worst depends on the foldback
  depth, and the page assumes the answer without programming the network.**

Order-of-magnitude check on the package `[from memory — single-pulse Zth is
strongly layout-dependent and the actual curve is gated]`: a DPAK's
junction-to-ambient transient thermal impedance at 50 ms is of order
10–20 °C/W on a modest pad, so 12 W gives **120–240 °C of junction rise**. That
is at or over the line, not comfortably inside it. At the recommended
4 W / 120 ms it is 40–80 °C, which is comfortable. **The foldback fix from
C4-02 is also the SOA fix.**

---

## C4-05 — Hot-plug, unplug, and a short that appears while running

### Hot-plug of the umbilical with the toggle on

This is **the default case, not an edge case**. `digital-and-supervision.md`
L90–92 `[repo]` states it directly: the umbilical +12 V node "reads 'present'
whenever the panel toggle is on, with nothing plugged in". `power-entry.md`
does not analyse it. `ROADMAP.md` L192 `[repo]` *does* call for measuring
inrush "on switch-on **and** hot-plug", so the project knows the case exists —
it is the schematic page that skips it.

**First contact.** The FET is fully enhanced, the output is a stiff 12 V, the
far end is 2.2 mF at 0 V `[calc]`:

```
R_loop = 0.05 (sense) + ~0.02 (FET) + 0.34 (cable) + ~0.04 (caps' ESR)
       + ~0.04 (contacts)                             ≈ 0.49 Ω
I_peak = 12 / 0.49                                    ≈ 24.5 A
τ      = L_cable/R ≈ 1.2 µH / 0.49 Ω                  ≈ 2.4 µs
```

The controller's fast overcurrent comparator responds in a few microseconds
`[datasheet — gated]`, so the real peak is of order 10–25 A. The repo's 30 A
estimate is the right order.

**The repo's rebuttal answers the wrong mechanism.**
`docs/log/2026-09-20-review-resolution.md` L66 `[repo]` files "30 A hot-plug
arcing" under *the findings that were wrong*: "Minimum arc voltage on gold is
~15 V, so a 12 V rail cannot arc."

**The arc claim is correct** — gold's minimum arc voltage is ~15 V and 12 V is
below it `[from memory]`. But arcing is not the failure mode for a 24 A
make-contact. At first touch the current passes through a few asperities of
microscopic area. Gold's **softening voltage is ~0.08 V and its melting voltage
~0.43 V** `[from memory — Holm contact theory]`; 24 A through even 20 mΩ of
constriction is 0.48 V across the spot. The asperity softens, melts and
micro-welds, and the RJ45's wiping insertion stroke then tears it — which is
material transfer and plating erosion, entirely below the arc threshold. **The
rebuttal disposes of the arc and leaves the erosion mechanism untouched.** On a
connector the project has already decided will be inserted often (cable as
consumable), that is the thing that matters.

**And then the electrical outcome.** After the surge the controller enters
current limit, starts the timer, and must charge 2.2 mF from zero — which is
exactly the current-limited start of C4-02, i.e. **29 ms without foldback and
53 ms with**. A hot-plug is therefore the *most likely* way to hit the timer,
and the result is a latch-off requiring a toggle cycle.

**Recommendations**, cheapest first:

1. **Document the procedure** — toggle down, plug, toggle up — in
   `power-entry.md` and on the panel legend. It costs nothing and it is the
   only mitigation that works today.
2. Size the timer per C4-02 so that a hot-plug completes rather than latches.
3. There is **no interlock available**, and the reason is worth recording: the
   presence detect senses the breath line, which requires the instrument's
   analog front end, which requires umbilical power, which requires the toggle.
   The loop cannot be closed with the specified sensor. A ninth conductor or a
   shorting contact in the connector would close it; neither is available on
   8P8C.

### Unplug mid-note

**Electrically benign, and the reason is worth stating** `[calc]`: at the
instant of break, the source side is a stiff 12 V and the load side is 2.2 mF
sitting at ~11.4 V. The voltage the contact gap has to withstand starts at
~0.6 V and only rises toward 12 V as the instrument's capacitance decays over
`2.2e-3 × 5.5 / 0.212 = 57 ms`. There is no inductive kick worth naming
(`½LI² ≈ 0.25 µJ` for 1.2 µH at 0.58 A) and the break is soft. **This is the
opposite of the plug case and the asymmetry is the point.**

**Functionally the chain is sound and should be credited.** In-amp inputs go to
`AGND` through the 1 MΩ bias pair → presence comparator drops out → `OE` high →
buffer Hi-Z → DAC pins held by the DAC-side `R-SPI-PULL` → watchdog stops being
retriggered → `CLR` at ~99 ms → pitch and mods park; breath parks on its
pull-down (ADR 0005 L318). `power-entry.md` does not claim this — it is in
`digital-and-supervision.md` — but it is the correct answer to the question and
it works.

**One gap:** the module's umbilical output node stays at 12 V with no load
after an unplug, which means the next connection is a hot-plug. There is no
automatic disable on loss of load.

### A short that appears while running

1. `C2` (47 µF) dumps 3.4 mJ through the sense resistor and FET in ~3 µs
   `[calc]` — see C4-11's sense-resistor note.
2. The controller goes to current limit, the timer runs, the FET dissipates
   3–12 W depending on the foldback, and the part latches at timer expiry.
   **This half is correct and is what the load switch is for.**
3. **The half that is not covered:** the instrument's own 2.2 mF is
   *downstream* of the fault and dumps into it with nothing in the way —
   see C4-10.

---

## C4-10 — The 2.2 mF is an energy source the load switch cannot see

ADR 0005 L275–289 `[repo]` deletes the instrument-end polyfuse with four
arguments. The second is:

> It sits **downstream of the module's limiter**, so it can never reach its
> trip current and protects nothing.

That is true for a fault *upstream of* or *in series with* the instrument's
bulk capacitance. It is **exactly inverted** for a fault downstream of it,
which is every internal fault in the instrument — a shorted strip, a solder
whisker on a buck output, a crushed internal loom `[calc]`:

```
E  = ½ × 2.2e-3 × 12²          = 0.158 J
I  = 12 V / (ESR + fault R)    = tens of amperes for the first milliseconds
```

0.16 J and tens of amps, delivered locally, inside a **bonded oak body that
cannot be reopened** (ADR 0009), with the module's limiter seeing nothing at
all until the capacitors are empty. The load switch protects **the rack** from
the instrument. It does not protect the instrument from itself, and ADR 0005
presents it as if it does ("That job is done — better, faster … by the module's
load switch", L216 `[repo]`).

The other three deletion arguments stand on their own — the derated hold
current *is* below typical play, the part *is* 6 V-rated on a 12 V rail, and
creeping polyfuses *are* the thermal-runaway shape ADR 0014 objects to. **The
conclusion may well be right; the second argument is not, and it is the one
that claims coverage rather than acceptance.** The honest wording is: *the
instrument's internal bulk capacitance is unprotected by design, and the
accepted consequence is a 0.16 J fault inside a sealed body.* Record it as
accepted risk rather than as covered.

---

## C4-06 and C4-07 — The `OE`/LED node, and two contradictions

### The node, checked in every state

```
  bus +5V ──┬──[R-OE-PU 10k]────────┬── OE ×4 (active low)
            │                       │
            └──[R-LED 820R]──▷|─────┘
                            LED      │
                                     └── LM311 collector (emitter at GND)
```

`[repo: power-entry.md L137–143]`. The LED's cathode is on the node, so the LED
lights when the comparator **sinks** — instrument present, `OE` low, buffer
enabled. That polarity is right.

| Rails | LM311 | Node | Buffer | LED | Verdict |
|---|---|---|---|---|---|
| all up, instrument present | sinking | ~0.3 V | enabled | **lit** | correct |
| all up, instrument absent | open | 5.0 V | disabled | dark | correct |
| all up, load switch latched off | open (instrument dead) | 5.0 V | disabled | dark | correct, **but see C4-15** |
| bus +5 V **absent**, ±12 V present, instrument alive | sinking | ~0.3 V | unpowered → Hi-Z | **dark** | safe; **false "absent" indication while playing**, and see C4-09 |
| bus +5 V absent, ±12 V present, instrument absent | open | floats near 0 V | unpowered | dark | harmless (buffer unpowered) |
| bus +5 V present, **±12 V absent** | unpowered → collector high-Z `[datasheet — gated: the LM311's output is a separate-emitter NPN whose collector–substrate junction returns to V−, so with V− at ground a +5 V pull-up is reverse-biased]` | 5.0 V | **disabled** | dark | **clean — and only because the pull-up is on bus +5 V** |
| −12 V feed **open** (cracked bead, broken conductor) | V− floats | — | — | — | **C4-22**: the LM311's substrate floats against a +5 V collector pull-up; add a shunt clamp |

The bottom two rows are the answer to the brief's specific question, and they
are the argument for C4-06.

### C4-06 — `bom.csv` contradicted two schematic pages

**Fixed in the working tree during this review — see the repo state note.** The
analysis is kept because it is what justifies the fix, and because the same
reasoning error survives in `power-entry.md` as C4-07.

`bom.csv` `R-OE-PU`, **as it read when this review began** `[repo]`:

> Pull-up from the LM311 open collector. **FROM THE LM317'S 5.21V, NOT BUS
> +5V** — the level shifter may sit on the bus rail … but the SUPERVISION must
> not…

`power-entry.md` L135 `[repo]`: "Both loads now pull up to the **74AHCT125's
own bus +5 V**".
`digital-and-supervision.md` L69 `[repo]`: "`OE` pull-up and the LED —
**bus +5 V**".

And `bom.csv` `R-LED-PANEL` L83 `[repo]` says the LED is "820R from **BUS
+5V**" and — in the same note — "**Same rail as `R-OE-PU`**", which is false
given L101. **As the BOM stands it puts two pull-ups on one node onto two
different rails.**

**The two schematic pages are right and `bom.csv` L101 is stale.** It is the
residue of precisely the bug `power-entry.md` L129–134 claims to have found —
a pull-up on a *higher* rail than the 74AHCT125's own VCC, driving its input
clamp. At 12 V that bug delivered 12 mA; at 5.21 V against a bus rail at 4.75 V
it delivers `(5.21 − 4.75 − 0.7)/10k` ≈ 0 in the benign case and
`5.21/10k = 0.52 mA` into the clamp whenever bus +5 V is down — same defect,
2.3× smaller.

Worse, it breaks the two clean sequencing states above `[calc]`:

- **bus +5 V present, ±12 V absent.** With the pull-up on 5.21 V (which is
  derived from +12 V, so also absent), the `OE` node has **no pull-up at all**
  and the LM311 is unpowered. `OE` floats on a powered 74AHCT125 — an
  indeterminate enable on a buffer whose outputs go to a DAC that is also
  unpowered. That is a latch-up path into the DAC8568 created purely by the
  BOM's choice of rail.
- **Rack power-down** (C4-08): the 5.21 V pull-up dies *before* the LM311 does,
  extending the floating-`OE` window by ~6 ms rather than closing it.

**Fix (now applied in the tree):** correct the `R-OE-PU` row to bus +5 V, and delete the "supervision must
not sit on the bus rail" reasoning from that row — it is a correct principle
attached to the wrong component. It belongs on the **LM311's and the 74HC123's
supply**, where `digital-and-supervision.md` L70 already has it. A pull-up is
not supervision; it is a level-setting element that must live on the rail of
the pin it drives.

### C4-07 — `power-entry.md` L149–151 puts the comparator on 5.21 V

> The **comparator and the watchdog stay on the LM317's 5.21 V** so that a bus
> rail failure cannot take the supervision with it. `[repo]`

The watchdog, yes. **The comparator, no.** `bom.csv` `U-PRESENCE` L99 `[repo]`
is emphatic about why:

> **LM311, NOT LM393** … running it on +5V/-12V … The LM311 has a SEPARATE
> EMITTER PIN … **run it on ±12 V so it can see the negative input**, tie the
> emitter to GND, pull the collector to +5 V.

`digital-and-supervision.md` L70 `[repo]` agrees: "LM311, 74HC123 — **LM317
5.21 V / ±12 V**". `power-entry.md`'s own diagram L142 says "LM311 collector
(emitter at GND)", implying a split supply.

So one sentence on the subject page contradicts its own diagram, the BOM row,
and the sister schematic page — and it contradicts them in the direction of the
**defect the project spent a whole BOM note eliminating**: a comparator that
cannot see an input below its negative rail. `bom.csv` also records that the
sensed node is at 0 V unplugged and +0.2 V alive with a +100 mV threshold, so
the comparator must resolve around **zero**, which a single 5.21 V/GND supply
cannot do.

**Fix:** L149–151 should read "the watchdog stays on the LM317's 5.21 V and the
comparator runs on ±12 V; neither depends on the bus rail."

---

## C4-08 and C4-09 — Rail sequencing, every ordering

Two of the four rails are not free. `5.21 V` is derived from +12 V through the
LM317 and lags it; **umbilical +12 V** is derived from +12 V through the toggle
and the ramp and lags it by 50–100 ms by construction. The free variables are
bus +5 V against everything, and −12 V against +12 V.

### Rise times, computed

```
+12 V analog reaches valid:   ~immediately after the rack's own rise
5.21 V:  the 10 µF ADJ bypass charges through R1∥R2 = 114 Ω
         τ = 114 × 10e-6 = 1.14 ms → ~5 ms to settle                 [calc]
         (and it ramps up rather than overshooting — the ADJ cap holds
          the output toward 1.25 V initially. This is the safe direction.)
bus +5 V: rack-dependent, independent regulator, order not guaranteed
umbilical +12 V: 50–100 ms after the toggle, whenever that is
```

### Every consequential ordering on the way **up**

| Ordering | Exposed | Verdict |
|---|---|---|
| bus +5 V first, ±12 V and 5.21 V later | Buffer alive, DAC unpowered. `OE` pulled to bus +5 V → **high → disabled → outputs Hi-Z**. LM311 unpowered, collector high-Z. | **Safe — because the pull-up is on bus +5 V.** With `bom.csv` L101's 5.21 V pull-up, `OE` floats and the buffer may drive 5 V into an unpowered DAC8568. See C4-06. |
| ±12 V first, bus +5 V later | DAC alive on 5.21 V, buffer unpowered → outputs Hi-Z, DAC pins held by the DAC-side pulls. LM311 alive. | Safe **if nothing is driving the buffer's inputs.** If the umbilical is already up, see C4-09. |
| +12 V present, **−12 V absent** | The op-amps' V− is open: all six CV outputs slam toward +11.9 V into whatever is patched, behind only `R-OUT-PROT` 1 k. The LM311's V− floats against a +5 V collector pull-up. | **No rail-presence supervision anywhere in the module.** The watchdog's `CLR` cannot help — `CLR` parks the *DAC*, and the fault is in the analog stage's rail. `[repo: pitch-stage.md gives Vout = 2·Vdac − 2.500, which requires −12 V for the −2.5 V intercept]` |
| umbilical up last (normal) | During the 50–100 ms ramp the instrument's logic is partly alive and its SPI drivers sweep through the threshold region. | **Handled well.** The cable-side `R-SPI-PULL` hold the buffer's inputs; `OE` stays disabled until the presence comparator sees the breath pedestal, which requires the instrument's REF5050 and OPA2197 to be up. This is the one sequencing case the design gets right on purpose, and it should be credited. |
| toggle already on at rack power-on | The ramp draws 0.53 A from a rack rail that is itself starting, on top of everything else in the case. The controller's UVLO should hold it off until the rail is valid `[datasheet — gated]`. | **Check the UVLO hysteresis.** If the ramp's own load pulls the rail back below UVLO, the part restarts — and a UVLO restart is *not* a latch, so this can oscillate slowly at rack power-on even on the latching `-1`. |

### C4-08 — the way **down** is where the damage is

Hold-up, from the specified capacitances and loads `[calc]`:

```
+12 V analog: 47 µF, ~45 mA.  dV/dt = 0.045/47e-6 = 957 V/s
              LM317 drops out when Vin < ~7.2 V: (11.72−7.2)/957 =  4.7 ms
              op-amps and LM311 die around 4 V total:  (11.7−4)/957 =  8.0 ms
bus +5 V:     47 µF, ~10 mA.  5 V → 2 V:  47e-6 × 3 / 0.010    = 14.1 ms
instrument:   2.2 mF, 212 mA. 12 V → 6.5 V: 2.2e-3 × 5.5/0.212 = 57.1 ms
```

**Order of death: AVDD at ~5 ms, the comparator at ~8 ms, the buffer at
~14 ms, the instrument at ~57 ms.**

From 5 ms to 8 ms the LM311 is still alive and still holding `OE` **low**
(instrument present — it is, for another 49 ms), the 74AHCT125 is still powered
from a bus rail with 9 ms left in it, and the DAC's AVDD is **gone**. For ~3 ms
on every rack power-down, three 74AHCT125 outputs drive near-5 V logic into an
unpowered DAC8568's input clamps. An AHCT gate sources ±8 mA class
`[datasheet — gated]`; three of them is up to ~24 mA into the dead AVDD rail,
against a DAC8568 per-pin input current abs-max that is typically ±10 mA
`[datasheet — gated]`.

This is the textbook CMOS latch-up condition (input above VDD + 0.3 V with VDD
at zero), it happens on **every** power-down with the instrument attached, and
nothing in the design prevents it. The `bom.csv` L101 variant makes it worse,
not better (the pull-up dies first, so from 8 ms to 14 ms `OE` floats on a
powered buffer).

**Fix, one part class, fixes C4-09 as well: 1 kΩ in series with each of the
three buffer→DAC lines and each of the three cable→buffer lines.** At 2 MHz
into a ~5 pF pin that is a 5 ns corner — irrelevant — and it caps the clamp
current at ~5 mA per pin. It is the same 1 kΩ the project already uses for
`R-OUT-PROT` and `R-OPAMP-IN`. Check the cable side at E11 against
`R-MOSI-SER`'s source termination before committing.

### C4-09 — losing bus +5 V while the instrument plays

ADR 0005 L142–145 `[repo]` makes the bus +5 V rail "a **requirement, not an
option**. No jumper, no unpopulated fallback footprint." So the behaviour when
it is absent is not a supported mode — but it is a *failure* mode, and it is
ugly.

With the umbilical up, the instrument drives SCLK, MOSI and CS at 3.3 V into
the 74AHCT125's inputs. `bom.csv` shows `R-MOSI-SER` at **qty 1** — 220 Ω, and
on MOSI only `[repo]`. **SCLK and CS have no series resistance anywhere in the
path.** With the buffer's VCC at zero, those two pins clamp to VCC through the
input protection diodes, driven straight from an ESP32 GPIO capable of tens of
milliamps.

The result is not a dead buffer, it is a **half-powered** one: `C4`'s 47 µF
charges through the clamps to roughly 3.3 − 0.7 = 2.6 V, the 74AHCT125 is now
notionally operating at 2.6 V, and `OE` has no pull-up (its rail is the one
that died). A buffer that may be enabled, running at 2.6 V, driving SCLK/SYNC
into a **live** DAC whose input threshold is 0.7 × 5.21 = 3.65 V
`[repo: ADR 0004 L188]`. Every edge lands in the indeterminate band.

`digital-and-supervision.md` L85 `[repo]` describes exactly what that costs: a
mis-framed 32-bit word is a **sticky** failure, because a DAC8568 frame carries
the software reset, the clear-code register and the internal-reference enable.
The 4 kHz refresh does not clear it.

**Fix:** the 1 kΩ series resistors above (which bound the clamp current at
~2.6 mA per line and leave a 3.0 V high against AHCT's 2.0 V VIH `[calc]`), and
either accept the failure mode explicitly in ADR 0005 or move the shifter to
the 5.21 V rail and take the switching current onto AVDD instead. The first is
cheaper and probably right.

### C4-20 — the cable-side `CS` pull-up back-feeds a sleeping instrument

`bom.csv` `R-SPI-PULL` `[repo]`: "Cable side: **CS to +5V**". In the state ADR
0004 L338 calls "the normal state" — module powered, toggle off, instrument
unpowered — that 10 kΩ sits across 2 m of cable into an unpowered ESP32 GPIO
`[calc]`: `(5.0 − 0.7)/10k = 0.43 mA` into its clamp and onto the instrument's
dead 3.3 V rail. Small, but it is a partial-power state on an MCU: above zero,
below the brownout threshold, held there indefinitely, and a known cause of
failure to reset cleanly on the next power-up.

**Fix:** 100 kΩ rather than 10 kΩ on the cable side only. The buffer's input
leakage is ≤1 µA `[datasheet — gated]`, so 100 kΩ still holds the input within
0.1 V and reduces the back-feed to 43 µA.

---

## C4-18 — Does splitting the Schottkys achieve isolation?

**No, and ADR 0004 already says so in one place while the subject page claims
the opposite in another.** ADR 0004 L317–319 `[repo]`: "'Keeping the module out
of the rack' cannot work by branching, because both branches are common
upstream at the bus header. Filtering downstream of a shared node does not
isolate that node." That is correct and it is the right frame.

### Quantifying what survives the split

The common impedance is the +12 V path from the rack PSU to the branch point:
two ribbon conductors in parallel, their IDC contacts, the bus board and the
PSU's own output impedance `[calc]`, with 28 AWG at 0.232 Ω/m and a 0.3 m
ribbon `[from memory]`:

```
ribbon:   0.232 Ω/m × 0.3 m = 0.070 Ω per conductor, ÷2 in parallel = 0.035 Ω
contacts: ~15 mΩ each, two in parallel                              = 0.007 Ω
bus board + PSU wiring + PSU Zout                                   ≈ 0.01–0.10 Ω
                                                        R_common    ≈ 0.05–0.15 Ω
```

The breath-correlated part of the umbilical current, from ADR 0005's own load
table (quiescent 212 mA → typical play 359 mA) `[repo]`, is `ΔI ≈ 147 mA`.

```
ΔV at the shared node = 0.147 A × 0.05 Ω = 7.4 mV          [calc]
                      (up to 22 mV at R_common = 0.15 Ω)
```

So the split takes the shared term from the quoted ~80 mV to ~7–22 mV — **an
improvement of 4–10×, not isolation.** The split removes the diode's dynamic
resistance from the common path; it cannot remove the ribbon.

**And then it does not matter**, for the same reason as C4-01: 7.4 mV on the
module's +12 V rail reaches the pitch jack through ≥90 dB of op-amp PSRR
`[repo: ADR 0004 L315]` and through the LM317's line regulation into a rail
that is not the reference. `[calc]` ≈ 0.2 nV–0.3 µV. Both the 80 mV and the
7.4 mV are inaudible by the same four orders of magnitude.

### The term that is real, and is 100× larger

The umbilical current returns through the **rack's shared bus ground**, which
is the module's own reference — and that offset reaches the output at **unity
gain**, not through a PSRR `[calc]`:

```
error in cents = 1200 × ΔI × R_ground

R_ground = 10 mΩ  →  1.8 cents
R_ground = 20 mΩ  →  3.5 cents
R_ground = 30 mΩ  →  5.3 cents
```

ADR 0004 L519–523 `[repo]` puts this at "~4.8 cents" and E6 is scheduled to
measure it — consistent with `R_ground ≈ 27 mΩ`, which is the right order for a
ribbon return. **That single term is larger than anything the second diode
could have bought, and it is the unavoidable cost of sourcing 360 mA out of a
Eurorack module.** It is the same physics as the 5.7–7.2 cents of internal
`PWR_GND` sharing that ADR 0004 L498–505 derives correctly.

### C4-18 proper — the diagram commits to one ground pin

`power-entry.md` L43 `[repo]`:

```
   GND └───────────────────────────────────────────── STAR POINT
```

One pin. A 16-pin Eurorack header carries **several** ground pins
`[from memory — the Doepfer bus assigns roughly six to eight of sixteen to
ground; confirm against the A-100 technical documentation, which ADR 0004
already cites as a source]`. Bonding all of them to the star divides
`R_ground` by the number bonded — the only lever this module has on the
dominant error term, it is free at layout, and it is unretrofittable
afterwards.

**This belongs on the page as a numbered layout constraint, exactly the way
ADR 0004 L479–482 argues such constraints should be recorded.** The page
currently spends its grounding section on the internal split, which is correct,
and does not mention the external term at all.

---

## C4-16, C4-17, C4-23 — Beads, 47 µF, and the LC

### Is 47 µF right?

**For the analog, −12 V and +5 V branches: yes, generously.** The page's own
caveat (L176–178, `[repo]`) that 4 × 47 µF is 2–5× the surveyed norm and adds
to case-wide inrush is worth quantifying and then dismissing `[calc]`: 188 µF
total, and a rack PSU slewing 12 V in ~5 ms draws
`188e-6 × 2400 V/s = 0.45 A` — one module's worth, for five milliseconds,
behind diodes. Not a problem.

**For the umbilical branch (`C2`): it is doing almost nothing useful and one
thing harmful.** At DC the 0.53 A ramp and the 0.58 A run current come from the
rack through `D2` and `FB2`; `C2` supplies only the HF component. What it does
do is store 3.4 mJ on the fault side of the sense resistor (C4-11). 10 µF would
serve the same HF purpose with 1/5 the fault dump.

### C4-17 — the LC, and whether it is damped

With `L ≈ 1 µH` for a 600 Ω@100 MHz bead at low frequency
`[from memory — the low-frequency inductance of a given bead series is
datasheet-gated]` and C = 47 µF `[calc]`:

```
f0 = 1/(2π√(1e-6 × 47e-6)) = 23.2 kHz
Z0 = √(1e-6/47e-6)         = 0.146 Ω
ζ  = (ESR/2)·√(C/L)
```

| Cap type | ESR | ζ | Behaviour |
|---|---|---|---|
| 47 µF aluminium electrolytic (**as specified**) | 0.5–1.5 Ω | **1.7–5.1** | overdamped, no peaking |
| 47 µF X5R ceramic (an obvious "improvement") | ~5 mΩ | **0.017** | **Q ≈ 30 at 23 kHz** |

**So the answer is: yes, it is damped — entirely by accident of the package,
and nothing in the repo records that as the reason.** `bom.csv` `C-BULK-RAIL`
says "47uF 25V electrolytic, THROUGH-HOLE radial" `[repo]` and justifies the
type nowhere. A future substitution to a 1210 ceramic — smaller, cheaper,
longer-lived, the obvious modernisation — puts a Q≈30 resonance at 23 kHz
directly on the rail feeding six op-amps and the DAC's regulator, excited by
every rack power-on step.

**Fix:** one clause in the BOM row — *"aluminium electrolytic **required**:
its 0.5–1.5 Ω ESR is what damps the LC formed with `FB-IN`. Do not substitute
ceramic without adding a series damping resistor."*

A second, smaller resonance exists between the bead and the 100 nF decouplers
(`f0 ≈ 500 kHz`, `Z0 = 3.2 Ω` `[calc]`), damped to Q ≈ 6 by the electrolytic's
HF impedance in parallel. Minor; mention it at E6 when the rail is scoped.

### C4-16 — the bead rating argument stops one step short

`power-entry.md` L62–66 `[repo]` is **right** that the rating is set by the
series and not the footprint, and right that "a saturated bead is a wire".
What it omits is that **the ≥1 A number is a thermal/DC rating, and impedance
derating with bias current is a separate curve.** A bead at its rated current
typically retains only a fraction of its zero-bias impedance `[datasheet —
gated; the derating curve is per-series]`.

`FB2` carries 0.58 A continuously at clamp-legal worst and 1.0 A during a
fault. At those currents a 1 A-rated part is contributing little but its DCR
(`0.58 A × 0.04 Ω = 23 mV`, 13 mW `[calc]`). **Specify `FB2` at ≥2 A**, which
is a different line item from the other three, and note that the page's own
sentence — "the *series* does" — is the argument for making it one.

### C4-23 — the "negative-resistance instability" open item can be closed

`power-entry.md` L168–172 `[repo]` carries `L-BUCK-IN` in front of a
constant-power load as "the textbook negative-resistance instability". The
criterion is that the source's output impedance must stay below the load's
incremental negative resistance `[calc]`:

```
CPL:  R_neg = −V²/P = −(11.4)²/1.26 W      = −103 Ω     (one R-78E5.0 at 1.26 W in)
LC:   L = 47 µH, C = 100 µF (C-BUCK-IN)
      f0 = 2.32 kHz,  Z0 = 0.686 Ω
      series R ≈ 0.4 Ω (cable + sense + FET)
      equivalent parallel damping at resonance = Z0²/R = 1.18 Ω
net parallel R = 1.18 ∥ (−103) = +1.19 Ω   → stable
instability would need |R_neg| < 1.18 Ω, i.e. P > 11.4²/1.18 = 110 W
```

**87× of margin.** The concern as stated is not a risk and should be closed on
paper rather than costing E11 bench time.

**The real item at that node is different and more specific:** `f0` is
**2.32 kHz** with `Q = Z0/R = 1.7`, and the WS2815 PWM rate that ADR 0004 L312
names is "around 2 kHz" `[repo]`. An undamped-ish LC whose resonance sits on
the dominant excitation frequency in the system is worth a damping leg (a
series R–C across `C-BUCK-IN`, e.g. 1 Ω + 100 µF) and worth measuring at E11 —
but for ringing at the strip rate, not for negative-resistance oscillation.
Rewrite the open item to say so.

---

## The LM317 branch

All four questions the brief asks come out **sound**, which is worth saying
plainly. Vout = `1.25 × (1 + 475/150)` = **5.2083 V** `[calc]`, matching both
documents.

| Check | Result | Verdict |
|---|---|---|
| **Divider / programming current** | `1.25 V / 150 Ω = 8.33 mA` `[calc]` | — |
| **Minimum load** | 8.33 mA flows through the divider whatever the DAC does. LM317L family minimum load is of order a few mA `[datasheet — gated; the LM317LZ's I_O(min) max spec must be read]`. | **Satisfied by the divider alone, even with the DAC in reset.** Add a BOM note: *do not scale these resistors up* — 1.5 k/4.75 k would give 833 µA and lose regulation at light load. |
| **Divider dissipation** | R1 `1.25²/150` = 10.4 mW; R2 `(8.33 mA + 50 µA)² × 475` = 33.4 mW `[calc]` | Fine on 0805 (125 mW). Note the 3× asymmetry self-heats R2 more than R1 in a divider whose *ratio* is the setpoint; at ~10 °C and 25 ppm/°C that is ~1.3 mV. Irrelevant for a rail, worth knowing at E7. |
| **Dissipation** | Vin = 12.0 − 0.28 (D1 at 45 mA `[datasheet — gated]`) = 11.72 V; drop 6.49 V; load ~13 mA → **84 mW** `[calc]` | Matches `bom.csv`'s "~90 mW". TO-92 at ~180 °C/W `[datasheet — gated]` → **15 °C rise**. Comfortable, and far inside the LM317LZ's 100 mA rating. |
| **Dropout** | At the rack's −5 %: `11.4 − 0.28 = 11.12 V` in, 5.23 V out → **5.9 V of headroom** against a dropout of order 1.5–1.7 V `[datasheet — gated]` `[calc]` | **Large margin**, even with the 55 mV the umbilical branch pulls out of the shared node at 1.1 A. |

Three additions:

- **C4-22a:** the page's "5.21 V" omits the `I_ADJ` term that `bom.csv`
  `R-REG-SET` says was the entire reason for choosing 150/475 over 240/768 and
  buying 0.1 % parts: `+I_ADJ × 475` = **+24 to +48 mV**, so the real target is
  **5.23–5.26 V** `[repo, calc]`. The page drops the term the BOM bought.
- **C4-19:** `C-REG-ADJ` reads "10uF / 1uF **ceramic or tantalum**" `[repo]`.
  A 1 µF X7R 0805 at 5.2 V bias is ~0.6–0.75 µF of near-zero ESR `[from
  memory — DC-bias derating]`. The LM317's compensation assumes an output
  capacitor with ESR in a window `[datasheet — gated]`; near-zero ESR is the
  classic LM317-oscillates-with-ceramics case, and this is the rail that is the
  DAC's AVDD. **Specify tantalum, or ≥10 µF aluminium, or add 0.5–1 Ω in
  series.** Delete "ceramic" from the row.
- The 10 µF ADJ bypass also makes AVDD the **last rail up and the first rail
  down** (~5 ms either way, computed above), which is what creates C4-08. Worth
  a sentence on the page, because the same cap that buys ~50 µV of noise is
  what opens the sequencing window.

---

## C4-12, C4-13, C4-14, C4-15 — Four cheap fixes

**C4-12 — 1N5817 is a 20 V part.** `[from memory: 1N5817 = 20 V, 1N5818 = 30 V,
1N5819 = 40 V; all DO-41, all the same price.]` `bom.csv` `D-REVPOL` specifies
1N5817 ×3 `[repo]`. A swap that puts −12 V where +12 V should be presents
**24 V of reverse bias** across a 20 V diode `[calc]`. The shrouded keyed
header makes that unlikely at the module end, but not at a DIY bus board's
unshrouded header. **1N5819 costs the same, adds ~40 mV of Vf at these
currents, and removes the exposure.** There is no argument for the 20 V part
other than that it is what the community copies.

**C4-13 — "kills the buffer and nothing else" is not the whole cost.** ADR 0004
L191–193 `[repo]` accepts the unprotected bus +5 V pin because "a reversed or
row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing
else". `C4` on that pin is a **47 µF aluminium electrolytic**
(`bom.csv` `C-BULK-RAIL`, 25 V `[repo]`). +12 V it survives. **−12 V reverses
it**, and a reversed radial electrolytic in a rack module vents. The accepted
cost is understated. **Fix:** either make `C4` ceramic, or add a reverse-shunt
Schottky (cathode to the +5 V rail's node, anode to ground) which protects the
buffer too for the same twenty cents the project was willing to spend on `D2`.

**C4-14 — the `ON` pin has no network.** The diagram is
`panel toggle ──── ON` `[repo]`. Missing: a pull-down so a broken panel wire
means *off*; a series resistor so a panel-accessible node is not wired straight
to an IC input (ESD, and a wire that runs past the analog section); and a
**debounce RC**, because the toggle is also the **latch reset** for a `-1`
part. A bouncing reset on a latching hot-swap controller re-arms it repeatedly
into whatever fault caused the latch — which is the auto-retry behaviour
`power-entry.md` L118–122 says this design exists to avoid, reintroduced
mechanically. 10 kΩ pull-down + 10 kΩ series + 100 nF is the whole fix.

**C4-15 — one dark LED, four conditions.** `bom.csv` `LED-PANEL` `[repo]`
claims that with the LT1641-1 latching, the LED "is also the only thing that
says **why** the instrument went dark". It is not. The LED is driven by the
presence comparator, which reports "the breath front end is alive". It goes
dark identically for:

1. toggle off,
2. instrument unplugged,
3. instrument plugged in but its analog front end / REF5050 dead,
4. **load switch latched off** — the one case that needs a distinct
   indication, because it is the one that requires a deliberate toggle cycle to
   clear.

The LT1641 has a `FAULT` output `[datasheet — gated: the pin's name and
polarity could not be checked]`. **A second LED, or a bicolour part on the same
panel hole, separates the case that needs an action from the three that do
not.** Two parts, one panel hole, and it is the difference between "the
instrument is dark" and "the instrument is dark *and here is what to do*".

---

## C4-21, C4-22 — The diagram, and smaller points

**C4-21.** `power-entry.md`'s thesis (L52–53) is that the shared-diode fault
was "**visible by inspection of the diagram**". The diagram at L12–44 cannot
be inspected `[repo]`:

- All four bulk capacitors are drawn **in series with their rails**:
  `+12V ├───┬──[D1 1N5817]──[FB1]──[C1 47µF]──┬── MODULE ANALOG +12V`. Read
  literally, no DC reaches the analog rail.
- L22 runs `──[D2]──[FB2]──[C2 47µF]──┬───────── AGND`, which labels the
  **umbilical +12 V branch node as `AGND`** — the in-amp input that this
  project's entire analog argument depends on carrying nothing.
- L35 crosses the FET's source with the `PWR_GND` rail at an unmarked `┼`, so
  the FET's source appears connected to both `PWR_GND` and the umbilical
  output.
- **There is no gate capacitor anywhere in the drawing**, although the
  programmed ramp is the page's central feature and 50 ms of dV/dt is set by
  precisely that component. Nor is there a `V_CC` connection, nor the sense
  connections across `R-ILIM`, nor a value on `C_T`.

That last point is substantive, not cosmetic: **no component in this repository
sets the ramp rate.** `bom.csv` `U-LOADSW` is a single line item reading
"LT1641-1CS8 + DPAK/SO-8 N-FET + sense R" `[repo]`. A `C-TIMER-LOADSW` row was
added during this review, so the fault timer is now ordered — **the gate
capacitor still is not**, and it is the part that sets the 50/100 ms ramp the
whole page is built around. Both values are what C4-02 turns on; both should be
BOM rows with values and tolerances, and the drawing should show which node
each sets.

**Also worth specifying while the drawing is being fixed:** the LT1641's `V_CC`
must sit **downstream of `D2`**, not on the raw bus pin, or a reverse event
applies −12 V to a pin whose absolute maximum is around −0.3 V. The diagram
does not say which.

**C4-22 — smaller points.**

- **"or the instrument will not boot on a cold day" (L96) is backwards.**
  Aluminium electrolytics *lose* capacitance when cold, which makes the start
  **faster**, not slower. If there is a cold-start mechanism here it is
  something else (higher WS2815 forward voltage, slower MCU brownout release);
  as written the sentence supplies a reason that argues the other way.
- **The LED resistor is computed on one rail and used on another.** L145
  `[repo]`: `(5.21 − 2.0)/4 mA ≈ 800 Ω → 820 Ω`, "and on the 5 V rail it is
  ~3.8 mA". Redone on the rail it is actually on, including the comparator's
  saturation voltage `[calc]`: `(5.00 − 2.0 − 0.2)/820 = 3.4 mA`. And
  `bom.csv` `LED-PANEL` specifies only "3mm LED - diffused" — **no colour, no
  Vf**. At a blue or white LED's ~3.2 V that becomes
  `(5.00 − 3.2 − 0.2)/820 = 2.0 mA` `[calc]`, about half brightness. Specify
  the colour and the Vf the resistor assumes.
- **The LED's current is also the `OE` logic low.** Total comparator sink
  `[calc]`: 3.4 mA (LED) + 0.47 mA (10 k) + ~4 µA (four OE inputs) ≈ 3.9 mA.
  The 74AHCT125's `V_IL(max)` is 0.8 V at a 5 V VCC `[datasheet — gated]`, and
  the LM311's `V_OL` at 3.9 mA must be read off its saturation curve
  `[datasheet — gated]`. The margin is probably adequate and it is **not
  quantified anywhere**, and it degrades directly if anyone makes the LED
  brighter. **The clean fix is to stop sharing the node**: drive the LED from a
  small-signal NPN off the comparator instead of hanging it on the logic node.
  That also gets the panel wiring — an antenna and an ESD target — off the
  `OE` net, which currently leaves the board and comes back.
- **No shunt clamp on the rails.** A Schottky from ground to −12 V (cathode to
  ground) and from +12 V to ground (cathode to +12 V) costs forty cents and
  removes two floating-rail states: the LM311's substrate floating against a
  +5 V collector pull-up if the −12 V feed opens, and any rail being dragged
  past ground by a reactive load.
- **`D2`'s own margin.** At clamp-legal worst it carries 0.58 A steady
  (0.26 W in a DO-41 `[calc]`) and up to ~0.83 A during a ramp and 1.0 A in a
  fault, against a 1 A part. It is inside the rating and there is not much
  spare. An SS24/SS34-class 2–3 A part in the umbilical branch only would cost
  nothing and would also make C4-12 moot for that leg.

---

## What I checked and found sound

Listed because a review that reports only defects is not calibrated either.

1. **The load-switch table's own arithmetic is exactly right.** All eight cells
   of the 50 ms / 100 ms table reproduce `[calc]`, and the `½CV²` cross-check
   agrees to four figures. The insight that ramp energy is invariant to ramp
   time is correct and well put; it needs only the +9–18 % load term.
2. **`R_SENSE = 50 mV / 1.0 A = 50 mΩ`, 18 mV and 6 mW at 360 mA** — all
   correct `[calc]`, and the 6 mW figure correctly supports the conclusion that
   R_DS(on) is irrelevant and SOA is the only specification that matters.
3. **26 ms for a flat-1.0 A current-limited start is right** for its stated
   assumptions (`2.2e-3 × 12 / 1.0` `[calc]`). The defect is what was left out
   of the assumptions, not the arithmetic.
4. **"The FET must be chosen against single-pulse SOA, not R_DS(on)" is the
   right rule**, and the SOT-23 rejection is well founded.
5. **The foldback claim is correct.** With 4:1 foldback, `P(V_DS)` varies only
   between 3.0 W and 4.0 W across the whole fault range `[calc]` — "roughly
   flat" is accurate. The page just does not follow it through to the timer.
6. **`-1` over `-2` is right**, and the reasoning (auto-retry into a persistent
   fault is the ADR 0014 thermal-runaway shape) is sound.
7. **The LM317 branch is correct on every axis asked about**: the divider gives
   5.208 V, its 8.33 mA satisfies minimum load unaided, 84 mW gives a 15 °C
   rise in TO-92, and dropout has 5.9 V of margin at the rack's −5 %. See the
   table above. The decision to select R2 on the bench rather than from a
   tolerance stack is correct for a population of one and is correctly
   reasoned in `bom.csv`.
8. **Pulling `OE` and the LED to the 74AHCT125's own bus +5 V is the right
   answer**, for exactly the reason the page gives, and it is what makes two
   of the sequencing states clean. The bug it reports finding (the +12 V
   pull-up into a 5 V part's input clamp) was a real bug and the fix is the
   right one. C4-06 is a failure to propagate that fix into `bom.csv`, not a
   defect in the fix.
9. **`OE` high = disabled = fail-safe** is the correct polarity, and
   `R-CLR-PU`'s corrected pull-*down* on `CLR` is the correct direction for
   the same reason.
10. **The unplug-mid-note chain works** — presence → `OE` → DAC-side pulls →
    watchdog → `CLR` → parked outputs — and the decision to let the umbilical
    coming up *last* gate `OE` through a sensor that requires the instrument's
    analog front end is genuinely good design.
11. **"A ferrite bead is a wire at 2 kHz" and "bulk belongs at the load" are
    both right**, and ADR 0004 records both as corrections to its own earlier
    reasoning rather than quietly editing them.
12. **"Filtering downstream of a shared node does not isolate that node"**
    (ADR 0004 L319) is the correct general statement, and my quantification
    of the residual (C4-18) agrees with it.
13. **The 5.7–7.2 cents of internal `PWR_GND` sharing and the ~4.8 cents of
    rack bus return are both physically sound**, correctly derived, and
    correctly identified as unity-gain mechanisms. My independent estimate of
    the rack term (1.8–5.3 cents for 10–30 mΩ `[calc]`) brackets the repo's
    figure.
14. **"12 V cannot arc on gold" is correct.** The rebuttal is right about
    arcing; C4-05 objects only to treating it as disposing of the hot-plug
    concern.
15. **`AGND` carries no current, and the arithmetic supporting it holds**:
    `bom.csv` `R-BIAS-INAMP`'s "~60 nA against a 350 mA power return =
    0.2 ppm" `[repo]` is the right calculation and the right conclusion.
16. **The bus +5 V rail as a stated requirement with no fallback footprint** is
    a defensible scope decision for a one-off, and ADR 0005 argues it honestly
    rather than hedging with an unpopulated jumper.
17. **The keyed shrouded IDC**, and the decision not to protect the +5 V pin
    given what is on it, are both reasonable — subject to C4-13's correction
    about what else is actually on it.

---

## What is gated on a datasheet

Every one of these is named here rather than guessed at, per the brief. None of
the conclusions above depends on a fabricated number; where one of these would
change a conclusion, the conclusion is stated conditionally.

| Part | Parameter | What it decides |
|---|---|---|
| **LT1641-1CS8** | `V_SENSE(th)` and its tolerance | The real trip window, and therefore C4-04's 8 % margin |
| **LT1641-1CS8** | Gate pin current; how `C_GATE` sets dV/dt | C4-04's ramp tolerance; the missing BOM rows in C4-21 |
| **LT1641-1CS8** | Timer charge/discharge ratio and `C_T` scaling | C4-02's timer value; repetitive-fault accumulation |
| **LT1641-1CS8** | **Foldback network topology and depth** | C4-02 (which of 29/40/53 ms applies) and C4-11 (whether the worst fault is a short or ~8 Ω). *The page flags this itself.* |
| **LT1641-1CS8** | UVLO threshold and hysteresis | Whether a toggle-on at rack power-on can oscillate |
| **LT1641-1CS8** | Whether `-1` needs an `ON` cycle to clear a latch; `FAULT` pin | C4-14's debounce; C4-15's second LED. *The page flags this itself.* |
| **N-FET (unselected)** | Single-pulse SOA at V_DS = 12 V, and transient Zth at 50–120 ms | C4-11. **No part number exists in the BOM to check.** |
| **1N5817** | V_RRM | C4-12 (20 V is `[from memory]`, and the fix is free either way) |
| **1N5817** | Vf vs I at 45 mA and 580 mA | The LM317 headroom figures, which have 5.9 V of margin and are insensitive |
| **LM317LZ** | `I_O(min)` max; dropout at 13 mA; line regulation; θJA; output-cap ESR window | The LM317 table, and C4-19 |
| **DAC8568C** | Input current abs-max per pin; AVDD current; AVDD-to-reference sensitivity | C4-08's severity; the second row of C4-01's table |
| **74AHCT125** | `V_IL(max)`, output drive, input leakage | C4-08, C4-20, C4-22's LED note |
| **LM311** | `V_OL` vs `I_sink`; collector–substrate behaviour unpowered | C4-22's `OE` low-level margin; the `±12 V absent` row |
| **OPA2197** | PSRR vs frequency | C4-01 (the conclusion holds at any PSRR better than 14 dB, so this is confirmation, not a dependency) |
| **Ferrite (unselected)** | Impedance-vs-bias-current derating; DCR; low-frequency L | C4-16, C4-17's `f0` |
| **Doepfer A-100 bus** | Ground pin count on the 16-pin header | C4-18's mitigation factor |

---

## If only five things change

1. **C4-02 / C4-03** — settle the ramp, the timer and the foldback together:
   **100 ms ramp, 120 ms timer, foldback programmed.** As specified the three
   numbers contradict each other and the instrument latches off instead of
   booting.
2. **C4-01** — delete the 20-cent claim from `power-entry.md`, ADR 0004 and
   `bom.csv`, and replace it with the reasons `D2` is actually worth keeping.
   Leaving a false load-bearing number in place invites the part to be deleted
   with it.
3. **C4-07** — fix `power-entry.md` L149–151 to put the comparator back on
   ±12 V. (C4-06, the matching `bom.csv` error, was corrected in the tree
   during this review; `power-entry.md` was not touched and still carries the
   same mistake about the same circuit.)
4. **C4-08 / C4-09** — 1 kΩ in series on all six lines through the level
   shifter. One part type, two failure modes, one of which happens on every
   power-down.
5. **C4-18** — bond every ground pin on the header to the star, and put the
   rack-return term on the page. It is free at layout and impossible
   afterwards, and it is the largest real error in the chain.
