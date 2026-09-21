# C3 — Break the sequencing

**Brief:** find the power-up, power-down or fault sequence that damages something,
latches badly, or produces a dangerous output. Cold: `docs/review/**` and
`docs/research/**` unread.

**Verdict: the design has four latching faults, one of which prevents the
instrument from ever starting, and one hazard that reaches the user's other
modules.** They are listed in severity order in §0 and then developed against
the ten scenarios.

Evidence marking: `[repo] <file>` = read in this repo this session. `[calc]` =
arithmetic shown inline. `[web] <url>` = fetched or returned by search this
session. `[from memory]` = **not verified, check before building.**
`analog.com`, `ti.com`, `recom-power.com`, `waveshare.com`, `digikey.com`,
`sparkfun.com` and three datasheet mirrors were all blocked by the egress proxy;
what survived came through search-result summaries and is marked `[web]` with
the query's source URL.

---

## §0 — The findings, by circuit node

| # | Node / BOM ref | Fault | Outcome |
|---|---|---|---|
| **C3-1** | `U-LOADSW` FB / `R-ILIM` / `C-TIMER-LOADSW` | Foldback and the 50 ms timer are mutually exclusive as specified | **Every start latches off. The instrument never powers on.** |
| **C3-2** | `U-LOADSW` FET, `J-UMBILICAL` | The load switch is *upstream* of the connector, so the programmed ramp does nothing for a hot-plug | ~20–30 A for µs into the etherCON contacts; current limit → timer → **latch**. ADR 0005's stated reason for the part is wrong. |
| **C3-3** | `R-LED-PD` (**not in `bom.csv`**), `U-LVLSHIFT`, `LED-SIDE` | Strips get random data for 100–300 ms before firmware runs; mean random draw ~0.5 A on top of the ramp | Exceeds the 0.94 A limit → **latch off**. Intermittent, unretrofittable, inside a bonded body. |
| **C3-4** | `PITCH` jack / `R-OUT-PROT` / `C-FB-PITCH` | Pitch's protection resistor is inside the feedback loop, and no watchdog parks the DAC | A garbage DAC word holds **up to 13.5 mA and 182 mW** into a neighbouring module, indefinitely. **This is the one that can hurt the synth.** |
| **C3-5** | `R-SPI-PULL` cable-side `CS` | Specified to pull up to **"3V3", a rail the module does not have** | `CS`/`SYNC` state is undefined by construction in the design's own normal resting state. |
| **C3-6** | `BREATH` jack, `POT-OFFSET`, `R-OFFNEG` | Breath's rest voltage is analog and knob-set; it is **not 0 V** in any fault state | ADR 0005 and ADR 0006 both assert 0 V. Real value −0.93 V ± the offset knob, i.e. anywhere in **−5.9 … +4.1 V**. |
| **C3-7** | `MOD 1–4` jacks / `R-LDAC` / DAC ch7 | 80 µs full-rail excursion at every boot and every `CLR` exit | **Write order does change it** (−10.0 V vs +11.45 V), contrary to `digital-and-supervision.md`. |
| **C3-8** | `U-LVL-MOD` outputs → `U-DAC` inputs | **No series resistance** between the 74AHCT125 and the DAC | Rack +5 V up before LM317 5.21 V → up to ±50 mA into an unpowered DAC8568 input clamp. |
| **C3-9** | `C-BULK-RAIL` +12 V | Its decay-balancing calculation omits the 360 mA umbilical load on the same node | +12 V falls ~16× faster than the row assumes for the first ~1 ms of every power-down. |
| **C3-10** | 5 V and 3V3 rails, `U-BUCK`, `F-CHAIN` (**not in `bom.csv`**) | `U-LOADSW` cannot see a 5 V or 3V3 short at all | Hiccup or thermal-cycle indefinitely inside a sealed oak body. Nothing indicates it. |
| **C3-11** | `LED-PANEL` | The panel LED cannot indicate a latch-off since the comparator was deleted | `bom.csv` still claims it does. Every latching fault above is **silent**. |

---

## §1 — `U-LOADSW` / `R-ILIM` / FB: the start never completes

This is the finding that makes everything else academic, so it goes first.

### The threshold is 47 mV, not 50 mV

`hardware/module/power-entry.md` sizes `R-ILIM` as `50 mV / 1.0 A = 50 mΩ`
`[repo] power-entry.md`. The LT1641's current-limit amplifier regulates
`V_CC − V_SENSE` to **47 mV**, not 50 `[web]` (ADI's LT1641/-1/-2 datasheet text,
via search of
`https://www.analog.com/media/en/technical-documentation/data-sheets/164112fc.pdf`;
the PDF itself is proxy-blocked).

```
[calc]  I_limit = 47 mV / 50 mΩ = 0.940 A     not 1.000 A
```

6 % low. On its own, harmless — `bom.csv`'s own `R-ILIM` note already says the
±11 % window is narrower than the part's threshold tolerance `[repo] bom.csv`.
It matters because every margin below is computed against 0.94 A, not 1.0 A.

### Foldback is 12 mV at the bottom, and it is 5× tighter than the ramp

The same source gives the foldback law `[web]`: with `V_FB = 0 V` the part
regulates the sense drop to **12 mV**; the limit rises linearly with `V_FB` and
reaches the full 47 mV at `V_FB = 0.5 V`.

```
[calc]  I_limit(V_out = 0) = 12 mV / 50 mΩ = 0.240 A
```

`power-entry.md` says two things that cannot both be true `[repo]`:

> **A normal start never enters current limit** — 0.53 A against a 1.0 A limit

> **Program the foldback.** The LT1641 family reduces its current limit while the
> FET's drain voltage is high…

The programmed gate ramp is sized for `dV/dt = 240 V/s` into 2.2 mF = 0.53 A.
At `V_out = 0` the foldback limit is **0.240 A**. 0.53 > 0.24, so **the part is
in current limit from the first microsecond of every start**, and the fault
timer starts with it.

### The current-limited start is longer than the timer

With the FB divider set so `V_FB = 0.5 V` at `V_out = 12 V` — the only sensible
choice — the limit is `I(V) = 0.240 + 0.0583·V` amps.

```
[calc]  Charging 2.2 mF alone:
        t = ∫₀¹² C dV / I(V) = (0.0022/0.0583)·ln(0.940/0.240)
          = 0.03771 × 1.3654 = 51.5 ms
```

Already past the specified **"Timer ≈ 50 ms"** `[repo] power-entry.md`. And that
ignores the load, which the page's whole start analysis ignores: its table has a
"Charging current" row and no load row, while ADR 0005's own load table puts
**212 mA quiescent / 359 mA typical** on the umbilical `[repo] 0005`.

Adding the loads as they switch on — WS2815 quiescent ~120 mA at 12 V direct
`[repo] 0005`, the two `U-BUCK` R-78E5.0s starting once their input clears their
**8 V minimum** `[web]` (Recom R-78E-1.0 series datasheet summary; the PDF and
three mirrors are proxy-blocked) and then behaving as a ~2.2 W constant-power
load:

```
[calc]  0 → 6 V   I = 0.240 + 0.0583V           t = 0.0377·ln(0.590/0.240) = 33.9 ms
        6 → 8 V   less 0.12 A of strip Iq       t = 0.0377·ln(0.587/0.470) =  8.4 ms
        8 → 12 V  less 0.12 A + ~0.25 A bucks   t = 0.0377·ln(0.570/0.336) = 19.9 ms
                                          TOTAL ≈ 62 ms
```

**62 ms against a 50 ms timer. The LT1641-1 latches off at the end of every
single start.** The user sees: rack on, module LED lit, instrument dark. Flip
the toggle: same. There is no indication of what happened (see §11).

### What to do

Pick one, not both:

- **Delete the foldback network** and take the 100 ms ramp, not the 50 ms one.
  At 100 ms the ramp is 0.26 A, plus 0.37 A of load = 0.63 A against a 0.940 A
  limit — 1.49× margin, enough to absorb the LT1641's own threshold tolerance.
  At 50 ms it is 0.53 + 0.37 = **0.90 A against 0.940 A, a 4 % margin**, which is
  inside the part's tolerance: *even without foldback the 50 ms ramp is not
  buildable.* `power-entry.md`'s table presents 50 ms and 100 ms as equivalent
  choices differing only in peak FET power. They are not: one boots and one does
  not.
- **Or keep the foldback and set the timer from the foldback arithmetic above**
  — ≥100 ms, with `C-TIMER-LOADSW` sized to it and the FET's single-pulse SOA
  re-checked at `12 V × 0.24 A × 100 ms = 0.29 J` (which is *easier* than the
  0.6 J the page sizes the DPAK against, because foldback holds the fault
  current at 0.24 A, not 1.0 A — the page's "A hard short holds 12 V across it
  at the 1.0 A limit — **12 W**" is the no-foldback number and contradicts the
  foldback paragraph three lines below it).

`C-TIMER-LOADSW` is BOM status **`open`** with the note "Exact value from the
datasheet equation; analog.com was unreachable" `[repo] bom.csv`. It is the part
that decides whether the instrument works at all.

---

## §2 — Scenario 1: case powers up with the umbilical connected

### Rail order

| t | Event | `[evidence]` |
|---|---|---|
| 0 | Rack ±12 V and +5 V ramp | |
| +µs | `D1`/`D2`/`D3` conduct; `C1`–`C4`, `C-BULK-RAIL` charge | `[repo] power-entry.md` |
| ~1 ms | Module `±12 V` valid. **OPA2197s live. `R-OFFNEG` is already pulling from −12 V.** | `[repo] breath-output-stage.md` |
| ~2–5 ms | `LM317LZ` 5.21 V rises — *slowly*, because `C-REG-ADJ` is a 10 µF ADJ bypass | `[repo] bom.csv C-REG-ADJ` |
| ~5 ms | DAC `AVDD` valid → POR → all channels zero scale, **internal reference disabled** | `[repo] 0006` |
| concurrent | `U-LOADSW` VCC clears UVLO (~9 V `[from memory]`, the part is spec'd 9–80 V `[web]`) and, if the toggle is on, **starts immediately** | |
| +50–100 ms | Umbilical ramp; see §1 | |
| +~1 s | ESP32-S3 boot: bootloader window 100–300 ms, then app | `[repo] carrier.md §5` |

Two things follow from that order that nobody has written down.

### The BREATH jack fires a +5 V spike at every rack power-on

`breath-output-stage.md`'s summer takes a fixed negative current from −12 V
through `R-OFFNEG` 95.3 kΩ and a variable positive current from the LM317's
5.21 V through `R-OFF` 21.0 kΩ `[repo]`. The −12 V rail is up milliseconds
before the LM317, and `C-REG-ADJ` 10 µF deliberately slows the LM317 further.
During that window the positive leg is at 0 V:

```
[calc]  I = −12 V / 95.3 kΩ = −125.9 µA
        V_jack = −(−125.9 µA × 40.2 kΩ) = +5.06 V
```

**The BREATH jack sits at +5.06 V for the first few milliseconds of every rack
power-on**, before any digital anything. Into a VCA CV input that is a full-open
click; into a 1 V/oct input it is five octaves; into a module expecting 0–5 V it
is at the top of its range. It is short, but it is at *every* power-on and it is
not in any power-on table in the repo.

Fix: nothing in hardware if you accept the click; otherwise take `R-OFFNEG` from
the LM317-derived rail's *negative* counterpart, or add a small RC so the
negative leg lags. Cheapest: shrink `C-REG-ADJ` so the LM317 leads −12 V, which
also loses the 50 µV noise benefit — a trade, not a free fix.

### PITCH sits at 0.000 V — a sounding note — for the whole boot

`pitch-stage.md` states it and ADR 0006's own power-on table contradicts it
`[repo]`:

- DAC zero-scale reset **and** internal reference disabled → `V_dac = 0`,
  `VREFOUT = 0`, buffered `V_ref = 0`.
- `V_pitch = 2·0 − 0 = **0.000 V**` `[calc]`.
- ADR 0006's table says "Bottom of its range, below −2 V | Subsonic. A VCO there
  is inaudible" `[repo] 0006`. That is the `CLR`-with-reference-enabled state,
  which is −2.500 V. They are 2.5 V apart and **the ADR is the document someone
  will read.**

Concretely: rack on, and any VCO patched to PITCH sounds its 0 V note at full
amplitude for ~1–3 s until firmware's first write. If the instrument latches off
(§1), **forever**.

Mods 1–4 are genuinely safe here: `4·0 − 3·0 = 0.000 V` `[calc]`, and that is
the one place the two-resistor redraw earned its keep `[repo] mod-channels.md`.

### BREATH's settled power-on value is a knob position, not 0 V

Once the LM317 is up, the in-amp sees the instrument's BREATH conductor at ~0 V
(the instrument has no power yet; its OPA2197 breath buffer's output is clamped
near its own dead rails through `R-SER-BREATH-INST` 1 kΩ). The in-amp is
additive at `REF`:

```
[calc]  V_inamp = −2.185 × (0 − 0) + 0.437 = +0.437 V
        (rest is 0 V only when BREATH carries the sensor's +0.200 V pedestal)
        Output stage inverts, ×4 fixed, attenuator 0.125…1.000:
        at the commissioned ~2.13× working point  → −0.93 V
        at full gain 4×                           → −1.75 V
        plus POT-OFFSET, −4.89 … +5.04 V          → −5.9 … +4.1 V
```

So **the BREATH jack's power-on and fault-state voltage is whatever the player
left the OFFSET knob at, minus about a volt.** ADR 0005's "Pull down the module's
breath receive input, so that an instrument which is switched off — or unplugged
— presents 0 V rather than a floating buffer output" `[repo] 0005` is wrong by
the pedestal *and* by the whole offset knob. `R-BIAS-INAMP` does hold the inputs
(good), but holding them at 0 V is not the same as holding the *jack* at 0 V,
because `TRIM-BREATH-ZERO` deliberately puts +0.437 V at `REF` to null a
pedestal that is not there when the instrument is not there.

This is not fixable by a resistor. It needs either the module to hold `REF` at
0 V when the instrument is absent (which needs the deleted presence detect), or
the acknowledgement written into ADR 0005/0006 that **breath's absent-state
voltage is −0.9 V ± the offset knob and the player must centre the knob before
unplugging.**

### The LED strips: `R-LED-PD` is proposed and not in the BOM

`carrier.md` §5 marks `R-LED-PD` `** PROPOSED **` and the component table marks
it `proposed`; `grep '^R-LED-PD,' hardware/bom.csv` returns nothing `[repo]`.

The window `carrier.md` describes is real and its current consequence is not
written down `[repo] carrier.md §5`:

- The instrument's `U-LVLSHIFT` 74AHCT125 is on the 5 V rail, which comes up
  when the umbilical crosses ~8 V — about two-thirds of the way up the ramp.
- `OE ×4` is tied **low** (enabled) `[repo] carrier.md §5`.
- ESP32-S3 `IO1`/`IO2` are high-Z inputs for the bootloader window, 100–300 ms
  `[repo] carrier.md, from memory`.
- An AHCT input floating near threshold oscillates; the buffer squares that into
  clean 5 V edges at 25 LEDs per strip.

Random 24-bit pixel values average 50 % duty on each channel:

```
[calc]  ADR 0014: both strips, 60/m, full white = 1.01 A
        random data, mean ≈ 0.5 × 1.01 A       = 0.505 A
        plus the programmed 50 ms ramp          = 0.53 A
        plus buck/strip quiescent               = 0.12 A
                                          total ≈ 1.16 A  vs 0.940 A limit
```

**The missing pull-downs alone push the start over the current limit**, and with
the timer already marginal (§1) that is a latch. The symptom is an instrument
that sometimes starts and sometimes does not, with a flash of random colour, and
the strips lose their state on power removal so it is different every time. Two
0805s, and `carrier.md` is right that they cannot be added later.

This also re-creates ADR 0014's runaway loop in a new shape. ADR 0014 says the
load switch "replaces a slow, self-heating, thermally-hysteretic protection
device with a fast fixed limit that does not run away" `[repo] 0014`. True of
the thermal loop. But *reset → random strip data → over the limit → latch* is
the same loop with a digital drive term, and it terminates in a permanent dark
instrument rather than an oscillation. Better, still bad, still undocumented.

---

## §3 — Scenario 2: hot-plugging the umbilical into a live module

### The load switch is on the wrong side of the connector

ADR 0005 justifies the part with `[repo] 0005`:

> **Inrush limiting.** The instrument's bulk capacitance is a near-short at the
> instant of connection. A toggle takes that surge across its contacts every
> time; a load switch ramps the output instead.

**It cannot.** The FET is fully enhanced before the plug is inserted. The
programmed gate ramp is a gate-charging rate; it is irrelevant when the load
appears downstream of an already-on switch. `power-entry.md` inherits the claim
and sizes the whole ramp table against "the instant of connection" `[repo]`.

What actually happens `[calc]`, with ADR 0005's own 0.34 Ω round-trip cable
figure `[repo] 0005` and ~1 µH/m of Cat5 pair inductance `[from memory]`:

```
L_loop ≈ 2 µH, R_loop ≈ 0.34 Ω cable + 0.05 Ω sense + ~0.02 Ω FET
                     + ~0.04 Ω contacts ≈ 0.45 Ω,  C = 2.2 mF
Q = (1/R)·√(L/C) = 2.22 × 0.0302 = 0.067   → heavily overdamped, R-limited
I_peak → 12 V / 0.45 Ω = 26.7 A,  rising with τ = L/R = 4.4 µs
Total resistive loss = ½CV² = 0.158 J, split by resistance:
  contacts' share ≈ 0.04/0.45 = 9 %  → 14 mJ dumped in the contact interface
  FET's share     ≈ 0.02/0.45 = 4.4 % →  7 mJ  (trivial)
```

So the FET is fine and **the etherCON contacts take ~14 mJ of arc energy in a
few microseconds, on contacts rated 1.5 A** `[repo] 0005`, every hot-plug.
Whether the LT1641 pulls the gate down fast enough to shorten this depends on
its current-limit amplifier response, which is on the blocked datasheet
`[from memory: hot-swap controllers are typically 1–3 µs, i.e. comparable to
τ = 4.4 µs — so it helps but does not prevent the first peak]`.

Then the part sees current limit, starts the timer, and has to charge 2.2 mF
from 0 — which is exactly the §1 calculation. **Every hot-plug latches the
module off.** The user's mental model will be "the cable is faulty".

### etherCON pin-order permutations

An RJ45's eight contacts lie in a line perpendicular to insertion, so they mate
within a rock of each other — microseconds to a couple of milliseconds, in
arbitrary order. Against the T568B map `[repo] 0004`:

| Pins | Signal |
|---|---|
| 1, 2 | BREATH / AGND |
| 3, 6 | **+12 V / PWR_GND** |
| 4, 5 | MOSI / CS |
| 7, 8 | SCLK / DIG_GND |

**Permutation A — grounds first (6 and/or 8 before 3).** Benign. This is the
only safe order and nothing enforces it.

**Permutation B — pin 3 (+12 V) before pin 6 (PWR_GND), with 4/5/7 already
mated.** The instrument's 2.2 mF is uncharged, so its PWR_GND rises with its
+12 V node — the whole instrument floats up toward +12 V relative to the module.
Its SPI pins go with it. At the module end they enter the 74AHCT125's inputs:

```
[calc]  Instrument-end series R is R-SPI-SER 220 Ω ×3 (in bom.csv, qty 3 —
        carrier.md §4 is stale when it says only R-MOSI-SER reached the BOM)
        I per line = (12 − 5.0 − 0.7) / 220 Ω = 28.6 mA
        three lines                          = 86 mA into the module's bus +5 V
```

The 74AHCT125's input clamp-current absolute maximum is **±20 mA per pin**
`[from memory — AHCT family; verify on the TI datasheet]`. 28.6 mA is 1.4× over
it, on all three inputs at once, into a 5 V rail that is the **rack's** +5 V bus
(`FB4` has no diode, by decision `[repo] power-entry.md`). Outcome: degraded or
destroyed 74AHCT125 inputs, possible CMOS latch-up on a part whose VCC is behind
a rack supply that will happily deliver an amp into a latched die.

Without `R-SPI-SER` this is unbounded and immediately fatal. **The three 220 Ω
resistors are the only thing standing between a rocked plug and a dead level
shifter, and `carrier.md` still lists two of the three as `** PROPOSED **`
against a `bom.csv` that already has qty 3.** Reconcile the pages; do not let
the proposal be dropped as "already covered".

**Permutation C — pin 6 (PWR_GND) mates but pin 3 does not, briefly.** Harmless.

**Permutation D — pin 8 (DIG_GND) mates before pin 6.** The whole start current
— up to 0.94 A — returns through the DIG_GND conductor and the instrument's
internal DIG_GND↔PWR_GND tie. 24 AWG carries it; the RJ45 contact is at 63 % of
its 1.5 A rating; the real cost is that `digital-and-supervision.md`'s careful
"a 2 MHz SPI return wants the pour directly under its trace" grounding argument
`[repo]` is briefly violated by an amp of power return. Transient only.

**Permutation E — pin 2 (AGND) mates alone.** Safe, and worth stating because it
looks unsafe: `AGND` at the module is **not a ground** — it is an INA828 input
behind `R-SER-BREATH` 10 kΩ with only `R-BIAS-INAMP` 1 MΩ to module analog
ground `[repo] breath-receive-stage.md`. No return current can flow through it.
The `AGND`-is-not-a-ground rule is load-bearing here and it holds.

**Permutation F — the analog pair mates and the power pair does not.** BREATH
sits at ~0 V, in-amp outputs +0.437 V, jack at −0.93 V + offset (§2). No damage.

---

## §4 — Scenario 3: umbilical unplugged live, mid-note

`digital-and-supervision.md` already owns the headline and states it honestly:
"pull the umbilical mid-note and the rack holds that note until you flip the
module's toggle" `[repo]`. Three things it does not say:

**1. The four MOD jacks hold too, and one of them may be driving something that
does not like being held.** A mod channel assigned to a filter cutoff or a VCA
CV holds at up to ±10.05 V indefinitely. ADR 0006's own "anything pitch-like
belongs on channel 1" advice `[repo] mod-channels.md` does not bound this.

**2. BREATH does not go to 0 V, it goes negative.** §2's arithmetic: the jack
**steps to −0.93 V** (typical gain) or −1.75 V (full gain), plus the offset knob.
Into a linear VCA that closes it (fine). Into an inverting VCA, a bipolar filter
CV, or anything expecting 0 V at rest, that is a **step in the wrong direction
at the moment the player is trying to stop playing.** ADR 0004's E10 check —
"verifies it by pulling the umbilical mid-note with the mouthpiece at rest"
`[repo] breath-receive-stage.md` — will show this immediately, and the document
predicting "nothing, and that is correct" will be wrong.

**3. The break-order permutations are the mirror of §3, and one of them matters.**
PWR_GND (pin 6) breaking *first*, with +12 V and SPI still mated: the
instrument's 2.2 mF is charged and now has no return. Its ground floats up; the
return current finds the SPI lines and the 74AHCT125 input clamps at the module:

```
[calc]  three lines × 220 Ω in parallel = 73 Ω
        the instrument's ground rises until the clamps conduct:
        I_total ≈ 3 × (0.7 V / 220 Ω) ≈ 9.5 mA   — survivable
```

The 220 Ω resistors bound it. Fine. But the **aluminium key plate** is bonded to
PWR_GND by `MECH-GNDBOND` `[repo] carrier.md §1`, so during that window the
plate the player is holding floats up to ~12 V above rack ground, carrying
2.2 mF:

```
[calc]  E = ½ × 2.2 mF × 12² = 0.158 J
        into a patch-cable sleeve or a jack ring: I_peak = 12 V / ~0.1 Ω = ~120 A
```

Not a safety hazard to a person (0.16 J, 12 V), but it is a **spark at the
connector and an audible pop through anything the instrument's plate can touch a
grounded surface with**, and it is 0.16 J into the etherCON shell contact. Add a
bleeder across the instrument's 12 V rail — 10 kΩ discharges 2.2 mF to 1 % in
0.1 s, costs 14 mW, and is one 0805.

**What the module does:** nothing. No fault, no trip, the FET stays on with 12 V
on open panel-connector contacts (shielded by the etherCON shell, so acceptable).
`R-SPI-PULL` cable-side takes over — see §7, because that state is not the clean
one the BOM claims.

---

## §5 — Scenario 4: USB-C connected while the module is also powering

### The OR is not where the BOM says it is

`bom.csv` `D-USBOR`: *"One diode per source into the shared 5V node"* `[repo]`.
`carrier.md` §1 draws both diodes on the **outputs of the two R-78E5.0s**, and
its component table says outright: *"One per regulator output, not 'one per
source' — the OR node is a dev-board pin. `[repo]` note is wrong"* `[repo]`.

`carrier.md` is right and the BOM row is not merely wrong, it is **unbuildable**:
VBUS enters at the dev board's own USB-C connector, so a diode "in the USB leg"
would have to be cut into a trace on a socketed dev board — which ends its life
as a swappable module, the thing `HDR-DEV` exists to preserve `[repo] bom.csv`.
Correct the BOM row; there is no reverse blocking on the USB side and there
cannot be one without a different dev board.

### What wins

Assuming the Waveshare ESP32-S3-Matrix ties VBUS to its `5V` pad directly, which
is the usual arrangement on that family `[from memory — `waveshare.com`,
`docs.waveshare.com` and the Zephyr board page were all proxy-blocked; the board
carries an **ME6217C33M5G**, a plain 800 mA fixed 3.3 V LDO with no
reverse-blocking `[web]`]`:

```
[calc]  Umbilical leg: R-78E5.0 out 5.00 V − SS14 Vf ~0.35 V at 0.5 A = 4.65 V
        USB leg:       VBUS 5.00–5.25 V, no diode
        → USB wins by 0.35–0.60 V
```

**USB wins.** `D-USBOR` A goes reverse-biased and buck A idles into an open
circuit (the R-78E has no minimum-load requirement `[from memory]` — confirm).
The 74AHCT125 `U-LVLSHIFT`, the 8×8 matrix and the ESP32-S3 are all now powered
from the host's port.

That is a real hazard by itself: ADR 0014's own figure for a full-field matrix
is **960 mA at 5 V** `[repo] 0014`, and the firmware thermal clamp that keeps it
below that is a firmware rule that does not run in the boot window. Plugging the
instrument into a laptop can drag the port into over-current shutdown. It
recovers gracefully — buck A picks the load back up at 4.65 V through `D-USBOR`
— so the OR does work in that direction.

### Can the USB host be backfed 5 V? Yes.

With the umbilical powering and the USB cable *not* in, the 5 V node sits at
4.65 V and, on the assumed dev-board topology, **that 4.65 V is presented on the
USB-C receptacle's VBUS pin**, from a source good for 1 A (the R-78E's
over-current trip is 200 % of max = ~2 A `[web]`).

Concretely:

- A USB-C source performs `vSafe0V` detection before applying VBUS. A device
  presenting Rd *and* sourcing 4.65 V on VBUS is an illegal state; most chargers
  and hubs simply refuse to attach. Symptom: **"the USB port doesn't work when
  the rack is on."** That is exactly the bench affordance `D-USBOR` was bought
  for (`E5`), defeated.
- A host that is *off* or asleep gets 4.65 V pushed into its VBUS switch. Port
  controllers with reverse-current protection trip at a few hundred milliamps
  and latch; ones without it backfeed the laptop's 5 V rail.
- Firmware's recovery ladder — "USB-Serial-JTAG through the tail USB-C slot"
  `[repo] firmware/README.md` — runs through this port. A bricked instrument is
  recovered with the rack *on*, because the rack is what powers it. That is the
  worst combination of the two states above.

**Recommendation:** put the OR where it can be built — a P-FET ideal-diode or an
`SS14` in series with the carrier's 5 V node *before* the dev-board socket's
`5V` pin, so the dev board's VBUS tie is isolated from the carrier's rail — and
verify the Waveshare board's VBUS→5V connection with a multimeter at E1 before
anything is laid out. If it turns out there *is* a diode on the dev board, most
of this section evaporates; if there is not, the E5 bench workflow does not work
as designed.

### What the dev board's regulator is doing

Nothing unusual: the ME6217 sees 4.65 V (umbilical) or 5.0 V (USB), both
comfortably above its dropout at the ~250 mA the S3 draws `[web, from memory]`.
The interesting part is that **the display board's buck B has no USB source at
all** — `carrier.md` draws `D-USBOR` on buck B's output feeding `J-DISP 5V`
`[repo]`. So USB-only means the real-time board boots and the display board does
not, the framed UART times out, and the one path for flashing the display board
("flashed over its UART, by the real-time board" `[repo] firmware/README.md`)
is unavailable exactly when you are on the bench.

---

## §6 — Scenario 5: USB-C connected, umbilical NOT connected

### It half-powers, and the half that is missing is all of the analog

ADR 0003/ADR 0005 put the **whole** instrument analog section on raw +12 V
`[repo] 0005, carrier.md §2`: `REF5050` → `OPA2197` buffer → `MPXV4006DP` `VS`,
and the breath output buffer's `V+`. With no umbilical there is no +12 V, so:

| Block | Rail | State on USB-only |
|---|---|---|
| `U-REF-BREATH` REF5050 | +12 V | dead |
| `U-BUF` OPA2197 ×2 halves | +12 V | dead, output clamped near 0 V |
| `U-BREATH` MPXV4006DP | REF5050 5.000 V | dead, `Vout` = 0 |
| `U-ADC` MCP3202 | **3V3 from the dev board LDO** | **alive** |
| `U-LVLSHIFT` 74AHCT125 | **5 V node = VBUS** | **alive, `OE` tied low** |
| `LED-SIDE` WS2815 ×50 | +12 V | dead |
| `U-MCU-RT` ESP32-S3 | 3V3 | alive |

### The power-on zero capture is poisoned, and the poison is sticky

`firmware/README.md` and ADR 0014 both make the breath zero **"the power-on ADC
capture"** `[repo]`. On a USB-only boot the ADC's input is the 0.6× divider from
a dead buffer:

```
[calc]  Correct rest reading, sensor pedestal 0.200 V:
          0.200 × 0.6 = 0.120 V → 0.120/3.3 × 4096 = 149 counts
        USB-only rest reading:  0 V → 0 counts
        Captured zero is therefore 149 counts LOW.
```

Hot-plug the umbilical afterwards and the sensor comes alive at 149 counts,
which is now **149 counts above the stored zero**. The deadband is "zero plus a
*measured* noise margin… a few times the standard deviation" `[repo] 0014` —
tens of counts at most. So the instrument reads a sustained hard blow with
nobody blowing: **a held note at the CV jacks, the strips and matrix lit to full
breath, and the thermal clamp scaling a field that should be dark.** It persists
until a clean reboot, and nothing in the UI says why.

Fix is one line of firmware: reject a zero capture that is implausibly low, or
re-capture when the analog rail appears. The instrument cannot detect the analog
rail because there is no presence detect and nothing samples +12 V — but
`MCP3202 CH1` is documented as spare in two places `[repo] bom.csv, carrier.md`.
**Wire a divider from the instrument's +12 V node to `CH1`.** Two resistors,
retrofittable only until the body is bonded, and it gives the instrument back
the "am I actually powered?" knowledge that `digital-and-supervision.md` says
"moved to the instrument" `[repo]` without giving it a way to know.

### The 74AHCT125 drives 5 V logic into unpowered WS2815s

`OE ×4` is tied low and the buffer is on the USB-powered 5 V node, so the moment
firmware writes LED data it drives 5 V into WS2815 `DI`/`BI` pins whose `VDD` is
0 V:

```
[calc]  through R-LED-SER 330 Ω: I = (5.0 − 0.7) / 330 = 13.0 mA per line
        four lines (DI + BI × 2 strips)          = 52 mA
        into the instrument's dead +12 V node (C-BUCK-IN 2×100 µF +
        C-STRIP-BULK 2×470–1000 µF ≈ 2.2 mF) → it charges to ~0.7 V and stops
```

So a **sustained 13 mA per WS2815 input clamp** for as long as firmware animates
the strips with no umbilical — which is the design's own bench scenario. The
WS2815's absolute-maximum logic input is quoted as **3.7–5.3 V** `[web]` (search
summary of the WS2815 datasheet; three mirrors proxy-blocked) — that is an
abs-max on a *powered* part and says nothing about clamp current into an
unpowered one `[from memory: WS281x input clamps are not characterised and are
a known way to kill the first pixel]`. Firmware must not drive LED data without
+12 V, and it has no way to know (see the `CH1` recommendation above).

### And the same `[web]` result reopens ADR 0014's biggest open question

`VIH = 0.7 × VDD` with `VDD = 12 V` gives **8.4 V** `[web]`, while the same
document's abs-max row implies a 5 V-class input. ADR 0014 flags this exact
ambiguity and says "Most 12 V addressable strips accept 5 V logic, but 'most' is
not a basis for a sealed build" `[repo] 0014`. It is still open, and `carrier.md`
§5 says the whole section is rebuilt if the answer is 8.4 V. **This blocks the
carrier layout, not just the BOM.** Buy a reel and scope it.

### What appears on the BREATH conductor

`U-BUF`'s OPA2197 breath-buffer half is unpowered with `V+` and `V−` both at
0 V. Its output presents the output stage's body diodes to those rails, i.e.
roughly 0 V ± 0.6 V through `R-SER-BREATH-INST` 1 kΩ. **The BREATH conductor
sits at ~0 V**, which is the same state as "unplugged" and produces the same
−0.93 V ± offset at the module's jack (§2, §4). No damage. `D-TVS-BREATH` is a
12 V standoff part so it does nothing here — which is correct and is the reason
`bom.csv` rejected the 5 V array `[repo]`.

---

## §7 — Scenario 6: module power removed while USB-C is still connected

### `R-SPI-PULL` cable-side `CS` names a rail that does not exist

`bom.csv` `R-SPI-PULL` `[repo]`:

> **CABLE-SIDE CS PULLS TO 3V3, NOT +5V**: pulled to 5V it drives 430 µA
> continuously through the unpowered ESP32's input clamp in the design's NORMAL
> resting state, and the node sits at ~0.7 V so 'CS idle high' is not even
> achieved.

**The module has no 3V3 rail.** Its rails are +12 V, −12 V, bus +5 V and the
LM317's 5.21 V (`power-entry.md`'s four-rail diagram `[repo]`), and 3V3 is not
one of the eight umbilical conductors (`BREATH, AGND, +12V, PWR_GND, MOSI, CS,
SCLK, DIG_GND` `[repo] 0004`). `grep -n "3V3" hardware/module/` returns nothing
relevant. So the instruction cannot be followed, and the board will be built with
`CS` pulled to bus +5 V — i.e. **into the fault the row was written to prevent.**

Where it settles is undefined, and both ends are bad:

```
[calc]  Path: bus +5 V → 10 kΩ → CS conductor → R-SPI-SER 220 Ω →
        ESP32 IO34 → clamp diode → the instrument's dead 3V3 rail.

  If the instrument's 3V3 leakage is low (~240 Ω equivalent):
        V_CS ≈ 0.7 V.  AHCT V_IL(max) = 0.8 V at VCC = 5 V.
        → CS is 0.1 V from its own threshold: INDETERMINATE, and an AHCT input
          biased at threshold oscillates. The buffer then drives the DAC's
          SYNC at MHz rates while SCLK floats near threshold too.

  If the instrument's 3V3 leakage is high (~20 kΩ, an unpowered S3 module plus
  flash, PSRAM, MCP3202, four 74HC165 and the LDO divider):
        (5 − V3 − 0.6)/10.22k = V3/20k  →  V3 = 88/30.22 = 2.91 V
        → the instrument's 3V3 rail is back-powered to ~2.9 V through ONE
          GPIO clamp diode, which is above the ESP32-S3's POR threshold and
          below its 3.0 V minimum: a zombie-boot oscillation on 420 µA.
```

**The DAC-side pull-up does not save it.** `bom.csv` specifies `DAC-SIDE CS
PULLS TO AVDD` `[repo]` — but the 74AHCT125's output is *actively driving*
`SYNC`, and an active AHCT output beats a 10 kΩ pull-up every time.

Consequence, in the state the design calls normal (module on, toggle off or
load switch latched, instrument connected and dark): the DAC's `SYNC` is held
low or oscillating, its shift register is open, and `SCLK` is a 2 m unterminated
pair running beside two WS2815 strips and the LED data lines. Thirty-two
crosstalk-clocked bits is a latched DAC8568 command — and
`digital-and-supervision.md` already names that class: *"a DAC8568 frame carries
the software reset, the clear-code register and the internal-reference enable —
so a mis-framed word is a **sticky** failure that the 4 kHz refresh does not
clear"* `[repo]`.

**Fix (pick one):**
- Add a 3V3 LDO to the module for the cable-side pulls alone. Ugly, one part.
- Pull cable-side `CS` to bus +5 V and **accept the 430 µA**, then add a
  100 kΩ pull-up on `CS` at the *instrument* end to its own 3V3, so that
  whenever the instrument has power `CS` is unambiguously high through the
  ESP32's reset window. Does not cover module-on/instrument-off.
- **Gate `OE` after all**, from the link rather than from breath — which is
  exactly the option `digital-and-supervision.md` parks under "demote this
  comparator to LED and health duty and gate `OE` from the link itself"
  `[repo]`. This finding is the argument for taking that option.

### Back-powering the rack's +5 V through `FB4`

With the rack off and USB alive, the instrument keeps driving SPI at 3.3 V into
an unpowered 74AHCT125:

```
[calc]  per line: (3.3 − 0.7) / 220 Ω = 11.8 mA
        three lines = 35 mA, through the AHCT input clamps into bus +5 V,
        which reaches the rack's +5 V bus through FB4 with NO diode
        (a stated design decision — ADR 0004 / power-entry.md)
```

Per-pin 11.8 mA is inside the ±20 mA input-clamp rating `[from memory]`; 35 mA
total through `V_CC` approaches the family's package limit `[from memory ±50 mA]`.
It is continuous, not transient, and it partially powers a 74AHCT125 to ~2.6 V
whose outputs drive an unpowered DAC8568. No single number here is fatal; the
combination is not a state anyone designed.

### The reconnect is the dangerous half

When the rack comes back on, the module's rails rise while the ESP32 is mid-frame.

- **If the DAC8568 aborts a short frame** — i.e. `SYNC` rising before 32 clocks
  discards the word `[from memory; SBAS430 was unreachable, `ti.com` is
  proxy-blocked]` — then a partial frame is harmless and the next `SYNC` low
  resynchronises. That behaviour is what saves this case and **it is unverified.**
- If it does not, or if the buffer's power-up puts glitches on `SCLK` while
  `SYNC` is low, the DAC latches a mis-framed word. Sticky, per above.

**Confirm the DAC8568's short-frame behaviour before trusting any of this.** It
is the single most load-bearing unverified fact in the digital path.

### `U-LVL-MOD` → `U-DAC`: no series resistance at all

Separate and simpler. The module's bus +5 V (from the rack) and the LM317's
5.21 V (from +12 V through `D1`) come up on different schedules, and nothing
sequences them. If bus +5 V leads, the 74AHCT125 is live and driving 5 V logic
into a DAC8568 whose `AVDD` is still 0 V. There is **no series resistor between
the buffer's outputs and the DAC's `SCLK`/`DIN`/`SYNC`** — `R-SPI-PULL` are
pull-ups/downs, not series elements `[repo] digital-and-supervision.md,
bom.csv`.

```
[calc]  74AHCT125 output drive into a clamp: ±50 mA short-circuit [from memory]
        DAC8568 input clamp abs max: ±10 mA typical for a TI CMOS input
                                     [from memory]
        → 5× over, on three pins, at every rack power-on where +5 V leads +12 V
```

`bom.csv`'s own `R-SPI-PULL` note worries about precisely this class of fault on
the *cable* side ("a reversed ribbon reaches the DAC's SYNC pin and turns a
$0.30 buffer failure into a DAC failure" `[repo]`) and leaves the buffer→DAC side
open. **Add 100–220 Ω in series on all three buffer outputs.** Three 0805s, no
signal-integrity cost at 2 MHz, and it closes the only unbounded clamp path in
the module.

---

## §8 — Scenario 7: a short on the instrument's 5 V, 3V3 or 12 V rail, 2 m away

### A 12 V short: yes, it trips, easily

```
[calc]  Fault loop, dead short at the instrument end:
          cable round trip           0.34 Ω   [repo] 0005
          R-ILIM                     0.05 Ω
          FET R_DS(on)             ~0.02 Ω
          FB2 bead DCR             ~0.05 Ω
          two etherCON contacts    ~0.04 Ω
                             total ≈ 0.50 Ω
        Prospective current = 12 V / 0.50 Ω = 24 A
        Trip threshold                      = 0.940 A
        → 26× over. The cable resistance is nowhere near enough to hide it.
```

**The trip resistance ceiling is the number worth writing down:**

```
[calc]  R_total_trip = 12 V / 0.940 A = 12.8 Ω
        less the 0.50 Ω of fixed path → any fault ABOVE ~12.3 Ω never trips.
        At 12.3 Ω the fault itself dissipates 0.94² × 12.3 = 10.9 W  (it trips)
        At 13 Ω it draws 0.92 A, dissipates 11 W, and NEVER TRIPS.
```

So a partial short — a pinched conductor, a crushed strain relief, a screw
through the loom — between about 13 Ω and 30 Ω sits **just under the limit,
dissipating 5–11 W inside a bonded oak and acrylic body** whose entire
thermal budget is ~3 K/W with 5 W already spent `[repo] 0014`. That is a 15–35 K
rise from the fault alone, on top of everything else, with no trip, no
indication, and no way in. The load switch protects the *rack*, which is what
ADR 0005 asked of it; it does not protect the instrument.

With foldback programmed it is worse, not better: foldback lowers the limit only
when the output is *low*, and a 13 Ω fault holds the output near 11 V, so
foldback is fully released and the limit is the full 0.94 A.

### A 5 V short: the LT1641 never sees it

The 5 V rail is behind `U-BUCK`, whose over-current trip is **200 % of max load
with auto-recovery** `[web]` — a hiccup. In hiccup the average input current is a
small fraction of nominal:

```
[calc]  R-78E5.0 in short-circuit hiccup: output ~2 A in short bursts at a low
        duty cycle; reflected input power is a few hundred milliwatts,
        i.e. tens of mA on the 12 V side.
        Against a 0.940 A trip: invisible. Against the 359 mA typical draw:
        the umbilical current actually goes DOWN.
```

**Outcome:** the instrument goes dead, the module's LED stays lit, the load
switch does not trip, and 2 A flows in bursts through a shorted trace inside a
sealed body indefinitely. If USB-C happens to be connected at the same time,
the host's port supplies the short *without* the R-78E's hiccup in the path —
there is no fuse anywhere on the carrier's 5 V node `[repo] carrier.md §1: "There
is no fuse and no power switch on this board"`.

### A 3V3 short: two regulators invisible

Behind the dev board's **ME6217C33M5G, 800 mA** `[web]`. A short pulls its
current limit and puts `(5 − 0) × 0.8 = 4 W` `[calc]` into a SOT-23-5 on a
socketed dev board — thermal shutdown, cycling, indefinitely. Upstream, the 5 V
rail sees 800 mA, the R-78E5.0 (1 A) is at 80 % and does not trip, and the
umbilical current rises by `0.8 × 5 / (11.4 × 0.90) = 390 mA` `[calc]` — taking
the umbilical from 359 mA to ~750 mA, which is **still below the 0.94 A trip.**

`carrier.md` proposes `F-CHAIN`, a 100 mA polyfuse on the 3V3 conductor that
"runs 265 mm beside 12 V LED power in a bonded body" `[repo]`. It is **not in
`bom.csv`** (`grep '^F-CHAIN,'` → nothing) and its own *Still open* entry calls
it "unretrofittable". The failure it covers — "the instrument is dead and there
is no way to look inside" — is exactly the one this section has just found three
routes to. **Fit it.**

### Summary of protection coverage

| Rail | Protected by | Detects a short? | Indicates? |
|---|---|---|---|
| Umbilical +12 V | `U-LOADSW` | **Yes, below ~12.3 Ω** | No (§11) |
| Umbilical +12 V, 13–30 Ω partial | nothing | **No** | No |
| Instrument 5 V | `U-BUCK` hiccup | Locally, invisibly | No |
| Instrument 5 V, with USB-C in | **nothing** | **No** | No |
| Instrument 3V3 | dev-board LDO | Locally, invisibly | No |
| Instrument 3V3 conductor down the body | `F-CHAIN` (**not in BOM**) | — | — |
| Module analog ±12 V | **nothing** — `power-entry.md` "Still open" | No | No |

---

## §9 — Scenario 8: reverse polarity and the rollover lead

### Reversed Eurorack header

`J-PWR-EURO` is a **16-pin shrouded keyed IDC** `[repo] power-entry.md`, so a
true 180° reversal is mechanically blocked. The realistic versions are a
home-made or miskeyed cable, or the very common 10-pin-into-16-pin offset.

`D1`/`D2`/`D3` (1N5817) block reversed ±12 V and the module is simply dead —
that part works. **The bus +5 V pin has no diode, by explicit decision**
`[repo] power-entry.md, 0004`:

> a reversed ribbon that kills the buffer and nothing else is an acceptable
> outcome (ADR 0004)

**It is not "the buffer and nothing else."** On the +5 V branch sits `FB4` and
then `C-BULK-RAIL`, a **47 µF 25 V through-hole radial electrolytic**
`[repo] bom.csv`. If the reversal lands −12 V on the +5 V pin — which it does
in the offset-by-one-pair case on most bus-board maps `[from memory: the exact
Doepfer 16-pin map could not be verified this session; confirm before relying on
which mirror pin lands where]` — that capacitor is reverse-biased at 12 V with
only a ferrite bead in series.

**A reverse-biased aluminium electrolytic vents.** That is a through-hole radial
part on an 8HP module a few centimetres behind a panel, at the user's eye level
in a rack. It is a different class of outcome from "a $0.30 buffer" and the ADR
should say so. Two fixes, both trivial: a fourth 1N5817 on the +5 V branch
(twenty cents, and the argument for omitting it evaporates once the failing part
is an electrolytic rather than a buffer), or make `C-BULK-RAIL`'s +5 V position a
ceramic or a bipolar part.

**What the CV outputs do:** with `D1`/`D3` blocking, the OPA2197s are unpowered
and all six outputs sit near 0 V. `D-JACK-CLAMP` BAV99 is on the **driver** side
of `R-OUT-PROT`, so a neighbouring module driving 10 V back into a jack is
limited to `(10 − 0.7)/1 kΩ = 7.6 mA` per jack `[calc, and bom.csv's own
figure]`, 46 mA across six. That decision holds up and is the one place in this
review where a prior fix does exactly what it claims.

### The rollover lead, pins 3↔6

This one is **genuinely covered**, and it is worth saying so plainly.

```
[calc]  Reversed, D-REVSHUNT SS34 conducts (cathode to the +12 V pin):
        I_available = (12 − 0.35 D2 − 0.5 SS34) / (0.34 cable + 0.05 sense
                      + 0.02 FET) ≈ 11.15 / 0.41 ≈ 27 A
        → far above the 0.940 A limit: instant current limit.
        With foldback: the output is held at the SS34's −0.5 V, so V_FB ≈ 0
        and the limit folds to 0.240 A.
        FET dissipation = (12 − 0.5) × 0.24 = 2.76 W for the timer duration
                        = 0.14 J at 50 ms — well inside a DPAK's single-pulse SOA.
        SS34 (3 A) carries 0.24–0.94 A for 50 ms. Fine.
        Timer expires → LATCH OFF. Correct behaviour.
```

Everything downstream sees −0.5 V, which both `C-BUCK-IN` and `C-STRIP-BULK`
electrolytics tolerate transiently. `D-TVS-PWR` SMAJ15A is **unidirectional**
`[repo] bom.csv`, so it forward-conducts in parallel with the SS34 at ~1 V and
shares the current — harmless and worth knowing.

**The residual problem is indication, not electrical.** The user sees an
instrument that will not power up and a module LED that is still lit (§11). They
will suspect the instrument, not the lead — which is the exact reverse of the
truth and the exact reverse of what ADR 0004 promised ("the panel LED says so"
`[repo] 0004`).

### The crossover lead, (1,2)↔(3,6) — **not covered, and not detected**

ADR 0004 says this case "is covered *by design*" `[repo] 0004`. It is covered
against *damage*; it is not covered against anything else, and the instrument
does something nobody has described.

+12 V now lands on the instrument's **BREATH** pin, and the instrument's +12 V
pin lands on the module's in-amp input (which sources nothing).

```
[calc]  Instrument side: 12 V (less D2) through R-SER-BREATH-INST 1 kΩ into
        the unpowered OPA2197's output stage, whose upper body diode conducts
        into the instrument's dead +12 V rail:
          I = (11.65 − 0.7) / 1 kΩ = 10.95 mA
          P in R-SER-BREATH-INST = I²R = 120 mW
        → the 1206 ≥250 mW spec that breath-receive-stage.md fought for is
          exactly what keeps this from being a fire. It is at 48 % of rating,
          CONTINUOUSLY, inside a bonded body.

        That 11 mA is the instrument's ENTIRE supply. It charges ~2.2 mF:
          to 5 V takes 2.2 mF × 5 V / 11 mA = 1.0 s
        The R-78E5.0s then try to start below their 8 V minimum and hiccup;
        the WS2815s brown out and display garbage; the node oscillates.

        The ADC divider is also driven: node ~11 V through R-ADCDIV-U 10 kΩ
        into an MCP3202 whose VDD is 0:
          I = (11 − 0.6) / 10 kΩ = 1.04 mA into its ESD clamp, sustained,
        back-powering the 3V3 rail. bom.csv's R-ADCDIV row worries about
        2.5 mA of this on a power-up TRANSIENT; here it is steady state.

        Module side: the load switch is sourcing 11 mA into a ~1 kΩ load.
        Against a 0.940 A limit: NO TRIP, no timer, no latch, forever.
```

**Outcome:** module LED lit, instrument's strips flickering garbage, 120 mW
cooking one 1206 and 1 mA flowing through an ADC's ESD structure, indefinitely,
with no protection device anywhere in the system aware that anything is wrong.
`D-TVS-BREATH`'s 12 V standoff sits right at `V_RWM` on an 11 V node, leaking and
warm — and the 12 V standoff was chosen `[repo] bom.csv]` precisely so this case
*would* be survivable. It is survivable. It is not detectable, and it is not
self-limiting.

The honest statement for ADR 0004 is: **a crossover lead is electrically
survivable and operationally invisible**, and the only thing that would catch it
is the presence detect that was deleted.

---

## §10 — Scenario 9: brownout, in order

### Nothing degrades gracefully; it is a cliff at ~9 V

| Rack +12 V | What happens | `[evidence]` |
|---|---|---|
| 12.0 → 10.6 V | Nothing visible | |
| **~10.55 V** | Module analog rail 10.2 V; OPA2197 swing ~10.05 V → **MOD channels at full scale begin to clip.** Pitch (+7.5 V max) is unaffected | `[calc]`, `[repo] 0006` |
| ~10.2 V | Umbilical arrives at 9.6 V; both R-78E5.0 still in regulation (8 V min); WS2815s begin to dim | `[web]`, `[repo] 0005` |
| **~9.0 V** | **`U-LOADSW` VCC UVLO. FET off. The instrument is disconnected, hard, with no ramp-down and no warning.** The LT1641 is spec'd 9–80 V | `[web]`, `[from memory]` for the exact UVLO |
| +0 ms | Instrument coasts on 2.2 mF from 8.6 V | |
| **+3.0 ms** | Bucks drop out at their 8 V minimum | `[calc]` below |
| +3.2 ms | 5 V node falls below the ME6217's dropout; 3V3 begins to fall | `[calc]` |
| **+3.3 ms** | **ESP32-S3 brownout detector fires at ≈2.43 V** (ESP-IDF default level 7) | `[web]` |

```
[calc]  Holdup between the LT1641 cut and buck dropout:
          E = ½ × 2.2 mF × (8.6² − 8.0²) = ½ × 2.2e-3 × 9.96 = 11.0 mJ
          Load at that point: 2 bucks ≈ 2.2 W in + strips ≈ 1.5 W = 3.7 W
          t = 11.0 mJ / 3.7 W = 3.0 ms
        At 4 kHz that is 13 loop passes × 6 DAC words = ~78 DAC words written
        while the instrument's 3V3 rail falls from 3.3 V to 2.43 V.
```

### The answer to the question asked: the detector fires *after*, always

**The ESP32-S3's brownout detector cannot fire before the DAC gets garbage, for
three structural reasons:**

1. **It is two regulators and 3 ms of holdup downstream of the event.** The
   thing that sags is the rack's +12 V; the thing the detector watches is
   `VDD3P3` after a buck *and* an LDO *and* 2.2 mF. Every one of those is a
   low-pass between the fault and the sensor.
2. **Its default trip is below the chip's own minimum.** The ESP-IDF default on
   ESP32-S3 is level 7, ≈2.43 V `[web]`; the ESP32-S3's minimum operating supply
   is 3.0 V `[from memory]`. **There is a guaranteed ~0.57 V band in which the
   part is out of specification and still executing code**, and the DAC service
   routine runs in that band.
3. **Nothing downstream discards the garbage.** The module's `U-LVL-MOD`
   74AHCT125 is on the *rack's* +5 V and the DAC is on the LM317's 5.21 V — both
   perfectly healthy while the instrument is dying. The buffer faithfully squares
   up whatever a sub-spec ESP32-S3 emits into clean 5 V TTL edges at the DAC's
   inputs. The 3.3 V I/O of an S3 at 2.9 V still clears the AHCT's 2.0 V
   threshold, so the *levels* stay valid long after the *data* stops being.

And when it does fire: the ESP32 resets, the SPI stops — **and the DAC keeps its
last word.** The frame watchdog is deleted and `CLR` is pulled inactive by
`R-CLR-PU` `[repo] digital-and-supervision.md, bom.csv`. So the garbage is
latched, at the jacks, until someone flips the toggle.

`digital-and-supervision.md`'s own table lists "Instrument loses power mid-note |
caught | **not caught**" `[repo]`. This section is that row's arithmetic: it is
not merely "not caught", it is *~78 words of out-of-spec output, then frozen*.

### Two free mitigations

- **Raise `CONFIG_ESP_BROWNOUT_DET_LVL_SEL`** from the default to the highest
  level (≈3.19 V `[from memory — the S3 levels run roughly 2.43 V to 3.19 V;
  check the Kconfig reference]`), so the detector fires *before* the chip leaves
  its specified range rather than 0.57 V after. One sdkconfig line. It is the
  only thing in the system that shortens the garbage window.
- **Put the DAC service routine in IRAM** — already recommended in
  `digital-and-supervision.md` for a different reason (NVS/OTA cache stalls)
  `[repo]` — and have it write a known-safe parking value if the loop detects a
  missed deadline. Costs nothing and turns "78 garbage words" into "a few".

### And the recovery latches

When the rack recovers above the LT1641's UVLO, the part restarts with a ramp
into 2.2 mF. That is §1's calculation, which does not complete inside the timer.
**A single rack brownout — caused by, say, someone plugging another module in —
permanently latches the instrument off.** The DAC still holds the garbage word.
The user sees a drone at a wrong pitch and an instrument that will not come back,
with a lit module LED telling them nothing.

### `C-BULK-RAIL`'s balancing argument omits the umbilical

`bom.csv` `[repo]`:

> The +12V branch carries the LM317's divider, the DAC and the comparator, about
> 22mA against -12V's 10mA — so at 47uF each it collapses 2.2x faster … 100uF on
> +12V balances the decay.

That balances the module's *own* consumption. It omits the **360 mA** the
umbilical draws from the same +12 V node `[repo] 0005`:

```
[calc]  With the umbilical loading it, from rack-off until the LT1641 UVLO cuts
        at ~9 V:
          dV/dt = 0.360 A / 100 µF = 3600 V/s   → 12 V to 9 V in 0.83 ms
        Without it (the row's assumption):
          dV/dt = 0.022 A / 100 µF = 220 V/s    → 12 V to 9 V in 13.6 ms
        → 16× faster, for the first ~1 ms of every power-down.
```

During that 0.83 ms the +12 V rail drops 3 V while −12 V has barely moved. The
op-amps do not rail (they still have 8.65 V of headroom), so the consequence is
bounded — but the row's claim that the decay is *balanced* is only true after the
LT1641 has already cut the umbilical, and the row does not say so. Re-derive it,
or state that the balance applies only below 9 V.

---

## §11 — `LED-PANEL`: every latching fault in this document is silent

`bom.csv` `LED-PANEL` `[repo]`:

> A PLAIN POWER LED off the module's own rail … **With LT1641-1 latching off on
> a fault, this still says why the instrument went dark**

It does not. A plain power LED on the module's own rail is lit whenever the
module has power, which is *always* — including during every one of:

- the load switch latching at the end of every start (§1)
- the load switch latching after every hot-plug (§3)
- the load switch latching on a random-LED-data overcurrent (§2)
- the load switch latching on a rollover lead (§9)
- the load switch latching after a rack brownout (§10)
- a 5 V or 3V3 short in the instrument (§8)
- a crossover lead half-powering the instrument (§9)

`power-entry.md` still draws the LED on the LM311's open collector
`[repo] power-entry.md`, and `bom.csv` says that comparator is deleted
`[repo]`. The two pages disagree about what is on the board. **Whichever wins,
neither arrangement indicates a latch-off**, because in the surviving design
nothing in the module knows the instrument's state.

**This is the cheapest high-value fix in the review.** The LT1641 has a `FAULT`/
`TIMER` state that is already a node on the board; `C-TIMER-LOADSW` sits at
1.233 V when latched `[web]`. One transistor and a second LED — or, better,
drive the existing LED from the `TIMER` node so that **lit = running, out =
latched**, which is the fail-safe sense and costs nothing extra. ADR 0004's
promise that "the panel LED says so" then becomes true.

---

## §12 — Scenario 10: what the CV outputs do, in every case

`R-OUT-PROT` 1 kΩ is on all six outputs, and `D-JACK-CLAMP` is on the **driver**
side of it, so in every state below the current into a neighbouring module's
input is bounded by that 1 kΩ — **except on PITCH**, where `R-OUT-PROT` is
*inside* the feedback loop `[repo] pitch-stage.md`.

### The one that can hurt the synthesizer: PITCH

```
[calc]  Mod channel at +11.45 V (rail) into a victim clamping at 5.1 V:
          I = (11.45 − 5.1) / 1 kΩ = 6.35 mA,  P in R-OUT-PROT = 40 mW
        → bounded, benign, R-OUT-PROT does its job.

        PITCH, feedback tapped at the jack, commanded high by a garbage word,
        into another module's OUTPUT sitting at −5 V behind its own 220 Ω:
          the loop FIGHTS it; the op-amp saturates at +11.45 V
          I = (11.45 − (−5)) / (1 kΩ + 220 Ω) = 13.5 mA
          P in R-OUT-PROT = 13.5 mA² × 1 kΩ = 182 mW
        → bom.csv's own figure, and it is why R-OUT-PROT is ≥500 mW [repo].
```

`bom.csv` frames that 182 mW as an *output-to-output patching mistake*. **Every
sequencing fault in this document can command exactly that condition**, without
anyone mis-patching: a brownout garbage word (§10), a mis-framed SPI word (§7), a
crosstalk-clocked DAC command while `SYNC` is stuck low (§7). And because the
frame watchdog is deleted and `CLR` is tied inactive, it is held **indefinitely**
— not for a note, for as long as the rack is on.

13.5 mA into a neighbouring module's input protection is not instantly
destructive, but sustained for hours it is exactly how small-signal clamp diodes
and op-amp input stages die. **This is the answer to "can the instrument hurt the
synthesizer it is plugged into": yes, through PITCH, because PITCH is the one
output whose protection resistor was moved inside the feedback loop to buy
load-independent gain.** That trade was made on accuracy grounds
`[repo] pitch-stage.md`, against four published designs, and it is a good trade —
but it converts PITCH from a current-limited output into one that actively
fights, and nothing in the design bounds *how long* it fights for. That is what
the deleted watchdog was buying.

### The table

| Scenario | PITCH | MOD 1–4 | BREATH |
|---|---|---|---|
| Rack power-on, first ms | 0 V | 0 V | **+5.06 V spike** (`R-OFFNEG` before the LM317) |
| Rack power-on, before firmware | **0.000 V — a sounding VCO note**, held ~1–3 s (or forever if the start latches) | 0.000 V | **−0.93 V + offset knob**, i.e. −5.9…+4.1 V |
| Firmware's reference-enable write, before ch1 | **−2.500 V** for ≥16 µs | 0 V | unchanged |
| First pass, ch7 written **last** | tracking | **+11.45 V on all four, ~80 µs** | unchanged |
| First pass, ch7 written **first** | tracking | **−10.000 V on all four, ~80 µs** (legal, in range) | unchanged |
| Hot-plug, start latches | stays at 0 V | stays at 0 V | −0.93 V + offset |
| Umbilical unplugged mid-note | **holds the last note forever** | **hold forever** | **steps to −0.93 V + offset** |
| USB-C only, no umbilical | (module sees no instrument) 0 V or held | 0 V or held | −0.93 V + offset |
| Module power removed | all rails down, all jacks ~0 V, back-feed bounded to 7.6 mA/jack by `D-JACK-CLAMP` | | |
| 12 V short at the instrument | load switch latches; jacks hold last value | hold | −0.93 V + offset |
| 5 V / 3V3 short | **no trip**; instrument dies; jacks hold last value | hold | −0.93 V + offset |
| Reversed rack header | ±12 V blocked; all jacks ~0 V | ~0 V | ~0 V |
| Rollover lead 3↔6 | latch; jacks at power-on state (0 V) | 0 V | −0.93 V + offset |
| Crossover lead (1,2)↔(3,6) | 0 V, no trip, indefinitely | 0 V | −0.93 V + offset |
| Brownout, during the 3 ms window | **up to 78 garbage words, then frozen** | same | −0.93 V + offset once the instrument dies |
| Brownout recovery | **latched off; garbage word still held** | same | same |

### The LDAC finding, which contradicts the repo

`digital-and-supervision.md` says `[repo]`:

> every exit from `CLR` — hot-plug, watchdog recovery, reboot, an OTA stall —
> throws intermediate values at the mod jacks for 100–200 µs, and **no write
> order avoids it**.

The excursion is unavoidable; **its polarity is not.** `R-LDAC` ties `LDAC`
inactive, so each channel updates on its own write, 16 µs apart at 2 MHz
`[repo] bom.csv, carrier.md §4`.

```
[calc]  Mods: Vout = 4·Vdac − 3·Vref, Vref from DAC ch7.
        ch7 written LAST:  for 5 × 16 µs = 80 µs the four jacks sit at
                           4·Vdac with Vref = 0 → up to 4 × 5 V = 20 V,
                           clipped by the rails at +11.45 V.
        ch7 written FIRST: for 80 µs the four jacks sit at
                           4 × 0 − 3 × 3.3333 = −10.000 V exactly.
```

−10.000 V is the channel's own specified endpoint — a legal level that every
downstream module is already expected to survive. +11.45 V is a rail excursion
1.4 V above the specified range. **Write channel 7 first.** One line of firmware,
free, and `firmware/README.md`'s statelessness rule already fixes the *ordering*
of the refresh without fixing the *sequence within a pass*. Add it to the rule.

---

## §13 — What to change, in order

**Blocking — the instrument does not start without these:**

1. **`C-TIMER-LOADSW` / foldback / ramp.** Either delete the foldback network and
   take the 100 ms ramp, or keep foldback and set the timer ≥100 ms from §1's
   arithmetic. `power-entry.md`'s start analysis must gain a load row; today it
   charges 2.2 mF and ignores the 359 mA the instrument draws while it does.
2. **`R-LED-PD` ×2 into `bom.csv`.** Proposed in `carrier.md`, absent from the
   BOM, unretrofittable, and on its own enough to push every start over the
   current limit.

**Unretrofittable — decide before the body is bonded:**

3. **A +12 V sense divider to `MCP3202 CH1`.** Gives the instrument back the
   knowledge the deleted presence detect took away: it fixes the poisoned
   power-on zero capture (§6), stops firmware driving LED data into unpowered
   WS2815s (§6), and makes a 12 V-rail fault reportable on the instrument's own
   display.
4. **`F-CHAIN`** into the BOM (§8).
5. **A 10 kΩ bleeder across the instrument's 12 V rail** (§4).

**Module-side, all cheap, all retrofittable but all better done now:**

6. **100–220 Ω in series on the three 74AHCT125 outputs into the DAC** (§7).
7. **Resolve `R-SPI-PULL` cable-side `CS`** — it names a rail that does not
   exist (§7). This is the argument for gating `OE` from the link, which
   `digital-and-supervision.md` already parks as the better answer.
8. **A fourth 1N5817 on the bus +5 V branch**, or a non-electrolytic
   `C-BULK-RAIL` there (§9).
9. **Drive `LED-PANEL` from the LT1641's `TIMER` node** so a latch-off is
   visible (§11).

**Firmware, free:**

10. **Write DAC channel 7 first** in every pass (§12).
11. **Raise the ESP32-S3 brownout level** to fire before the chip leaves spec
    (§10).
12. **Reject an implausible power-on zero capture** (§6).

**Document corrections:**

13. ADR 0006's power-on table: PITCH is **0.000 V**, not "below −2 V".
14. ADR 0005 and ADR 0006: BREATH's absent state is **−0.93 V ± the offset
    knob**, not 0 V.
15. ADR 0005: the load switch **cannot** limit hot-plug inrush; it is upstream
    of the connector.
16. ADR 0004: a crossover lead is survivable but **undetectable and not
    self-limiting**.
17. `carrier.md` §4 is stale — `R-SPI-SER` qty 3 is already in `bom.csv`.
18. `bom.csv` `D-USBOR`: "one per source" is unbuildable; package is DO-214AC
    for an SS14, not DO-41.

## §14 — Unverified facts this report depends on

Every one of these was blocked by the egress proxy. They are load-bearing.

| Fact | Where it matters | Source attempted |
|---|---|---|
| LT1641 sense threshold 47 mV, foldback 12 mV at `V_FB` = 0 | §1 — the whole finding | `analog.com` PDF blocked; taken from the search engine's summary of it `[web]` |
| LT1641 `V_CC` UVLO value and whether `-1` needs an `ON` toggle to clear the latch | §1, §10 | `analog.com` blocked |
| LT1641 current-limit amplifier response time | §3 | `analog.com` blocked |
| DAC8568 short-frame abort behaviour on `SYNC` rising before 32 clocks | §7 — it is what saves the reconnect case | `ti.com` blocked |
| DAC8568 input clamp current rating | §7 | `ti.com` blocked |
| 74AHCT125 input clamp current rating (±20 mA assumed) | §3, §7 | `ti.com` blocked |
| Waveshare ESP32-S3-Matrix: is VBUS tied to the `5V` pad without a diode? | §5 — decides the whole backfeed section | `waveshare.com`, `docs.waveshare.com`, `docs.zephyrproject.org` all blocked. **Measure it with a meter at E1.** |
| R-78E5.0-1.0 minimum input: 7 V or 8 V | §1, §10 | `recom-power.com`, `digikey.com`, `sparkfun.com` all blocked; 8 V taken from a search summary `[web]` |
| WS2815 `VIH` — 0.7 × 12 V = 8.4 V, or 5 V-referenced? | §6, and it blocks the carrier layout | three datasheet mirrors blocked; the search summary gives **both** answers `[web]` |
| ESP32-S3 brownout level table (2.43 V default, ~3.19 V maximum) | §10 | ESP-IDF Kconfig reference not fetched; default 2.43 V from a search summary `[web]` |
| The Doepfer 16-pin bus map — which pin mirrors +5 V | §9 | not verified |
