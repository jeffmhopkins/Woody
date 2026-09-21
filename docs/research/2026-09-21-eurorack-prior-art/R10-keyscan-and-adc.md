# R10 — Shift-register key scanning over a long run, and SAR ADC front ends

**Topic:** prior art outside Eurorack for (A) 74x165 key-scan chains on long cable
runs, and (B) SAR ADC front ends for a precision ratiometric sensor.
**Date:** 2026-09-21.
**Stakes:** Part A's looms are hand-built once into a body that is bonded shut.
Everything marked **UNRETROFITTABLE** below is permanent.

## Evidence markers

Used strictly. A previous review found this project's honesty markers calibrated
backwards, so the weakest marker wins whenever a claim mixes sources.

| Marker | Means |
|---|---|
| `[repo]` | I read it in this session. File named. |
| `[code]` | I read the source in this session. File named. |
| `[docs]` | I read the project's own published documentation in this session. |
| `[web]` | A web-search result summary. Not the primary document. |
| `[memory]` | Recalled. **Unverified — the vendor domain was blocked.** |
| `[BLOCKED]` | I tried to reach the primary source and the proxy refused. |

**What I could not reach.** Every component-vendor domain is blocked by the
egress proxy: `ti.com`, `ww1.microchip.com` / `microchip.com`, `nxp.com`,
`assets.nexperia.com`, `analog.com`, `onsemi.com`, `renesas.com`, `mouser.com`,
`digikey.com`, `alldatasheet.com`, `datasheet.lcsc.com`, `docs.rs-online.com`,
`diodes.com`, `cdn-shop.adafruit.com`. Also blocked: `docs.qmk.fm`,
`quinled.info`, `colinpykett.org.uk`, `sciencedirect.com`.
**So there is no `[datasheet]` marker anywhere in this document.** Every
datasheet number below is either a web-search quotation of datasheet text
(`[web]`), or recalled (`[memory]`). GitHub raw and the WebSearch tool work,
which is where the QMK, ZMK and hardware-repo evidence comes from.

---

## Findings vs Woody

| # | Practice found | Woody | Verdict |
|---|---|---|---|
| A1 | QMK ships `asym_eager_defer_pk` — press-eager, release-defer, per key. It is a named, shipped algorithm, not an invention. Default `DEBOUNCE` 5 ms. `[docs]` | Asymmetric debounce, "fire on first closed sample" | **Woody reinvented a solved thing and gave it no name.** Cite the algorithm. |
| A2 | QMK states flatly: *"Eager algorithms are not noise-resistant."* ZMK repeats it and **recommends press-debounce = 1 ms, not 0**, because it "protects against short noise spikes". `[docs]` | ADR 0001 discovered the same hazard independently and fixed it with "two consecutive agreeing samples" (250 µs) | **Right answer, arrived at the hard way.** Woody's 250 µs is tighter than ZMK's 1 ms. Fine — but the rule now has an external name and a rationale that does not depend on Woody's own reasoning holding up. |
| A3 | The 2021 predecessor `Open-Woodwind-Project` debounced the **resolved note**, not the key: `SETTINGS_NOTE_DEBOUNCE_DELAY 20` ms, symmetric, on the fingering *pattern*. Per-key debounce (10 ms, symmetric) existed only in drum-trigger mode. `[code] src/owp/owp.ino` | ROADMAP already says "apply the release filter to the note decision, not to each key independently" | **Agrees — and the brief's premise is wrong.** See A4. |
| A4 | **The predecessor did NOT use a shift-register chain.** It used two MPR121 capacitive-touch controllers on I2C. `grep -rn "165"` over `src/owp/` and `src/owp_full/` returns nothing. `[code]` | The brief supplied to this research says the 2021 project "used a similar chain" | **False premise.** There is no in-house prior art for the 165 chain. Woody has never built one. Every assumption about it is untested. |
| A5 | "Route the clock against the direction of data flow" is a **real, established rule** — it is the subject of US 6,381,719, *System and method for reducing clock skew sensitivity of a shift register*, and is standard scan-chain practice. Negative skew costs setup and buys hold. `[web]` | ADR 0001 item 3; `key-layout.yaml` chain order | **Rule is real. Woody's derivation is correct. Woody's topology satisfies it.** |
| A6 | Skew over 360 mm of loom is ~1.8 ns end to end, ~0.5 ns between adjacent clusters (≈5 ns/m). `[memory]` 74LVC165A t_PD is ~9–14 ns, t_hold ~1.5 ns. `[memory]` | `key-layout.yaml`: building the old order "would have put **hold-margin violations** into a body that cannot be reopened" | **Overstated by roughly an order of magnitude.** The old order costs ~0.5 ns of a margin dominated by a ~5–9 ns clock-to-out. It degrades hold; it does not violate it. This is an honesty marker pointing the wrong way. |
| A7 | Series (source) termination **is documented as valid only for point-to-point lines.** With distributed loads, intermediate receivers sit at the half-amplitude incident step until the far-end reflection returns, and the signal is distorted by superposition of forward and backward waves. `[web: TI SNLA034B, SiTime AN10002, and patent literature]` | `R-TERM-CHAIN`: "33–68 Ω series termination on key-chain clock and latch **at the MCU**", qty 2 — on a line that drops on **four** cluster boards `[repo] hardware/bom.csv` | **Woody applied a point-to-point technique to a multidrop line.** This is the most consequential Part A finding. See §A-5 for the arithmetic and why 68 Ω is worse than 33 Ω. |
| A8 | Reflection-induced double-clocking depends on **edge rate**, not clock rate. Slowing the clock does not fix it. `[memory, standard SI]` | ADR 0001: "Setup margin is **recoverable by clocking slower**; hold margin is not recoverable at any speed" | **The consolation is misapplied.** It is true of the skew term (which is 0.5 ns and does not matter) and false of the failure mode that actually kills 165 chains. Woody's fallback for a misbehaving chain is the one thing that will not help. |
| A9 | Function-level alternatives exist for both failure modes Woody names: **74x166** has a *synchronous* parallel load (data loads on the clock edge, so a glitch on the load pin is only sampled at an edge); **74x589 / 74x597** add an input storage latch and the 589 adds a **three-state output**. `[web]` The keyboard community's documented answer to "the 165 cannot share SPI" is the 589 — `christrotter/shift-register-spi-breakout-pcb` says so in as many words. `[repo, GitHub raw]` | ADR 0001 frames the part choice entirely as LVC-vs-HC (edge rate), and spends a whole SPI host plus 2 GPIO working around the 165's always-driven QH | **Woody solved at the wiring level a problem the catalogue solves at the part level.** The 165's async level-sensitive load is named in ADR 0001 as a top-two hazard; the 166 removes it for the same footprint. |
| A10 | Adafruit's NeoPixel Überguide — the community-standard reference — specifies a **300–500 Ω series resistor on the data line** and 500–1000 µF bulk at the strip. `[web]` | `hardware/bom.csv` has `C-STRIP-BULK` (470–1000 µF ×2) but **no series resistor on either WS2815 data line**, and drives them from a 74AHCT125 at **5 V** `[repo]` | **The single strongest aggressor in the loom is undamped.** Woody's response to LED coupling is 21 RC networks on the victims. Two resistors on the aggressor is cheaper, and it is the documented practice. |
| A11 | DodoHand (`wolfv6/keybrd_DH`) — four SN74HC165N per hand, daisy-chained, run over a **7-foot Cat6 flat patch cable**, with a tri-state buffer per row so only one row drives MISO. States the chain orientation matters — **for unused-input placement and bit numbering**, not for timing. `[repo, GitHub raw]` | ADR 0001 justifies chain order purely on setup/hold | **Practice cares about chain order for a different reason than Woody does**, and that reason (which byte lands where) is recoverable in firmware. Woody's reason is not recoverable but is also ~0.5 ns. |
| A12 | 74HC165 is preferred over CD4021 in organ builds because it "handles 3.3 V better"; keyboard-scan clock rates in these builds are set by "at what point delay becomes noticeable", i.e. by latency, not by signal integrity. `[web]` CircuitPython's `ShiftRegisterKeys` example uses **68 kΩ** external pull-ups. `[web]` | 10 kΩ pull-ups, 1 MHz clock, ~32 µs per 32-bit read `[repo]` | **Woody's values are conservative in the right direction.** 10 kΩ is 7× stiffer than the CircuitPython example; 1 MHz over 360 mm is unremarkable. No change. |
| B1 | MCP3202: internal sample cap **20 pF**, acquisition **1.5 clock cycles**, and the source "must be low impedance — well below 500 Ω with a 5 V VREF at the highest clock". `[web, quoting the datasheet]` | 6 kΩ Thevenin divider + 47 nF **at the pin** `[repo] hardware/bom.csv C-AA-ADC, R-ADCDIV` | **The 47 nF is not too large — it is what makes the 6 kΩ legal.** The reservoir is 2350× the sample cap against a textbook minimum of 10–20×. See §B-2. |
| B2 | Charge-sharing error: 20 pF drawn from 47 nF at 4 kHz through 6 kΩ gives a **DC gain error of ~0.048 % (~2 LSB of 4096)**, proportional to V_in, constant. Derived from the `[web]` sample-cap figure and `[repo]` component values. | ADR 0003 asserts the cap "fixes the source-impedance problem" without a number | **Correct conclusion, no arithmetic behind it.** The error is a constant gain term on a signal whose zero is auto-tracked and whose span is set by a panel knob. It is invisible. Put the number in the ADR so it stops being an assertion. |
| B3 | The real cost of 47 nF into 6 kΩ is **group delay: τ = 282 µs**, which is *longer than the 250 µs loop period*. | `docs/reference/latency-budget.md` and ADR 0003's latency table list "SAR ADC conversion ~50–200 µs" and **no RC term at all** `[repo]` | **An unbooked 282 µs sits on the note-gating path.** Note-on fires off a breath threshold read through this filter. The analog CV at the jack does not pass through it, so the gate lags the CV it is gating by ~282 µs. Nothing in the repo says this. |
| B4 | **MCP3201** is the same family, same SOIC-8, same speed, single channel — and has a **separate VREF pin**. MCP3202 does not: its reference *is* VDD. MCP3204/3208 also have separate VREF. `[memory, pinouts; BLOCKED on datasheets]` | `U-ADC` note: *"VDD-referenced so no separate ref chip. … One spare channel"* `[repo] hardware/bom.csv` | **The BOM states a limitation as a feature.** The 3202 buys its second channel by spending the VREF pin. Woody needs one channel and has a 5.000 V reference three centimetres away. |
| B5 | MCP3202 max sample rate: **100 ksps at 5 V, 50 ksps at 2.7 V** `[web, quoting the datasheet]`. At 18 clocks per 12-bit conversion that is **f_CLK ≈ 1.8 MHz at 5 V and ≈ 0.9 MHz at 2.7 V**; Microchip does not spec 3.3 V, so 0.9 MHz is the safe design number. | SPI2 is specified at **2 MHz** for the DAC8568 and carries the MCP3202 on the same host `[repo] ADR 0003, ADR 0004, latency-budget.md` | **2 MHz over-clocks the ADC by >2×.** Solvable — ESP-IDF sets clock per *device*, not per host — but it is written nowhere, and "SPI2 runs at 2 MHz" appears in four documents. |
| B6 | Ratiometric practice exists because in a normal design the **digital reading is the output**. | Woody's digital reading is *not* the output — the CV path is analog end to end (ADR 0003) `[repo]` | **Not a mistake, but right for a reason Woody never states.** ADR 0003 defends keeping the ADC at 3.3 V on a level-shifting argument, which is a consequence, not the analysis. See §B-3 for what the mismatch actually costs. |
| B7 | ADR 0003 spends a page on aliasing in the **signal** path. For a VDD-referenced SAR, VREF sits in the transfer function identically — and has no anti-alias filter at all. The WS2815 PWM rate is **~2 kHz** (`C-STRIP-BULK` note, `[repo]`), i.e. **exactly Nyquist for a 4 kHz sampler.** | Nothing in the repo applies the alias argument to VREF | **A hole, symmetric with the one Woody found.** Magnitude is small (regulator rejection, bulk caps, and 1 LSB = 806 µV), but the mechanism is the one the ADR calls out as a showstopper elsewhere. |
| B8 | Limiting pin current with a series resistor **is** the standard fix for an input driven above its own supply during sequencing. | `R-ADCDIV` ≥10 kΩ upper leg, sized against a **5 V** source `[repo]` | **Standard fix, stale number.** ADR 0003 moved the buffer to **+12 V**. Worst case is now (12 − 0.7)/10 k ≈ **1.1 mA**, not the ~0.4 mA a 5 V source gives. Still inside a ±2 mA clamp rating, but the margin is 1.8×, not 4×, and ADR 0003 still argues from 5 V. |
| X1 | — | **`hardware/bom.csv` says the four 74LVC165s are on the tail carrier (`PCB-CARRIER`: "dev board headers, 165 chain, ADC, reference…") *and* on four satellite boards (`PCB-CLUSTER`: "one 74LVC165 + switches + decoupling", qty 4), with `U-KEYS` qty 4 total.** `[repo]` | **These are mutually exclusive and they specify opposite looms.** This is the highest-stakes open item in the project. See §A-1. |

---

# Part A — shift-register key scanning over a long run

## A-1. The loom is not decided. Nothing else in Part A can be settled first.

`hardware/bom.csv` currently contains both of these rows `[repo]`:

```
PCB-CARRIER … "Passive carrier: dev board headers, 165 chain, ADC, reference, buffers, level shifter, power entry"
PCB-CLUSTER … qty 4 … "Identical satellite board: one 74LVC165 + switches + decoupling"
```

and `U-KEYS` is qty **4**. There are four registers and two rows claiming to host
them. ADR 0013's *Build approach* says the carrier holds "74LVC165 shift
registers"; ADR 0001 and `config/key-layout.yaml` say one register per cluster
down the body. `[repo]`

The prior cold review's `A3-bom-consistency.md` §F10 quotes both sentences
side by side and then proposes **both** PCB rows, treating them as four distinct
boards rather than as a contradiction. `[repo]` It is a contradiction, and it
decides the loom:

| | 165s on cluster boards (ADR 0001) | 165s on the tail carrier (ADR 0013) |
|---|---|---|
| Long conductors | SCK, SH/LD, SER, MISO, power, returns — ~10 with per-signal grounds | **18 switch lines + returns** — ~36, or a common return per cluster |
| Fastest thing in the loom | 1 MHz clock with ~2 ns LVC edges | **DC levels.** Nothing clocked. |
| Failure mode | reflection double-clock, SH/LD glitch → whole word corrupt | one key mis-sampled |
| Filtering possible? | **No** — you cannot RC-filter a clock | **Yes** — the 100 Ω/10 nF network sits at the register end and filters the whole run |
| What §A-5 below costs | everything in §A-5 | **all of §A-5 disappears** |

The carrier-mounted version is dramatically more robust against exactly the
hazard ADR 0001 spends its longest section on, because it puts **nothing fast in
the channel shared with the LEDs**. Its cost is conductor count. Woody has two
continuous side channels (ADR 0013) and a 265 mm worst-case run.

I am not saying which is right — conductor count in a 57 × 38 mm cross-section
with a U-bolt in it is a mechanical question I cannot answer from the repo. I am
saying **it is undecided in the live documents, and it is the decision that
everything below depends on.** Decide it before `WIRE-LOOM` is built.

## A-2. What the community actually does with 74x165 chains

Concrete builds, all read this session:

- **DodoHand** (`wolfv6/keybrd_DH`, `examples/shiftRegs/README.md`): four
  SN74HC165N per hand daisy-chained to 32 inputs; six unused inputs **grounded**,
  and deliberately placed on "the 74HC165 with unconnected SER pin" so the
  known-value bits land at a predictable end. Connected over a **7-foot Cat6
  flat patch cable**. A 74AHC1G126 tri-state buffer per row gates MISO. Scan
  budget: 63 µs per scan, target "at least every 10,000 µs". `[repo, GitHub raw]`
- **Matrix-inator** (`christrotter/shift-register-spi-breakout-pcb`): chose
  **74HC589 over 74HC165** explicitly — *"the 165 cannot share the SPI bus, and
  QMK only allows you, at present, to utilize a single SPI bus. You could use the
  165 if you also included a tri-state buffer. The 589 has that built-in."*
  Runs over a **VIK 12-pin 0.5 mm FPC** or 2.54 mm headers, in QMK with a custom
  matrix. `[repo, GitHub raw]`
- **Shiftboard** (`JamFox/Shiftboard`): 74HC165 used specifically to
  *eliminate matrix diodes* — direct-mapped switches, one input per key.
  `[repo, GitHub raw]`
- **Adafruit CircuitPython `ShiftRegisterKeys`**: 74x165 with **68 kΩ** external
  pull-ups, bit-banged or PIO or SPI. `[web]`
- **Organ/MIDI builds**: 74HC165 preferred over CD4021 for 3.3 V behaviour;
  clock rate chosen by when latency becomes audible. `[web]`

**Against that, Woody's parameters are unremarkable and mostly conservative:**
1 MHz clock (32 µs for 32 bits `[repo]`), 10 kΩ pull-ups (7× stiffer than the
Adafruit example), 4 kHz scan (2.5× faster than DodoHand's 10 ms target, and the
same order as a QMK keyboard's reported scan rate).

**Where long runs break, in this literature:** not timing. DodoHand's 7 feet of
Cat6 works at bit-bang speeds. What breaks is (a) floating inputs, (b) the
shared MISO problem, (c) ground return quality. Woody has already fixed (a) with
`R-KEY-PU` and (b) by giving the chain its own SPI host. `[repo]`

**What is absent from the community literature and present in Woody:** nobody in
these builds runs the chain **alongside a 5 V, ~2 ns-edge, 800 kHz LED data line
and a switched 12 V rail in the same channel.** That combination is Woody's own,
and §A-4 is about it.

## A-3. The chain-order rule: real, correctly applied, and ~0.5 ns

**Is it a real established rule?** Yes. Routing the clock against the direction
of data flow in a shift-register chain is standard practice and is the explicit
subject of US Patent 6,381,719, *System and method for reducing clock skew
sensitivity of a shift register* — "a clocking scheme [that] transmits a clock
signal through shift register cells in a direction which is against the
direction of the data flow". Data and clock in opposite directions produce
negative skew, which "can lead to setup violations but improves hold time".
`[web]`

**Is Woody's derivation correct?** Yes. Take a link from source device S
(further from the MCU) to destination device D (nearer). Clock reaches D at
t_D and S at t_S, with t_D < t_S. The setup check at D is

```
margin_setup = T − t_su − t_CO − t_flight − (t_S − t_D)
```

so the positive skew term subtracts from setup, and the hold check

```
t_CO,min + t_flight + (t_S − t_D) ≥ t_hold
```

gains the same term. ADR 0001's sentence — *"each device's clock arrives from
the MCU before its data source's does … late is setup, early is hold"* — is
exactly this. `[repo]`

**Is Woody's topology on the right side of it?** Yes. MCU at the tail, data
flowing toward the MCU, clock radiating away from it: that is clock counterflow.
`config/key-layout.yaml`'s `right_thumb → right_hand → left_thumb → left_hand`
with bit 0 at the device driving MISO is correct for a 74x165 chain. `[repo]`

**Now the size of it.** Loom propagation is about 5 ns/m, so 360 mm end to end
is ~1.8 ns and adjacent clusters are ~0.5 ns apart. `[memory]` 74LVC165A
clock-to-QH is roughly 9 ns typical / 14 ns max and hold on SER is around
1.5 ns. `[memory — TI datasheet BLOCKED]`

| Term | Magnitude | Share of a 1 µs clock period |
|---|---|---|
| Clock period at 1 MHz | 1000 ns | — |
| t_CO (clock → QH) | ~9–14 ns | 1.4 % |
| Setup requirement | ~3 ns | 0.3 % |
| **Inter-cluster skew** | **~0.5 ns** | **0.05 %** |

Hold margin is `t_CO,min + flight ± skew − t_hold`. With a realistic t_CO,min of
5 ns, that is ~4 ns in the good order and ~3 ns in the bad one. **The wrong
order degrades hold margin by about 12 %. It does not violate it.**

So: `config/key-layout.yaml`'s claim that the old order *"would have put
hold-margin violations into a body that cannot be reopened"* `[repo]` is
overstated by roughly an order of magnitude, and it is the kind of overstatement
this project has been told to watch for. **Keep the order. Downgrade the claim.**

**There is a better justification available, and it is the one to record.** The
two orders cost identical wire, but they differ in *which* conductor is the long
one:

- **Woody's order:** the long full-length conductor is `SER`, driven by the MCU
  into a single far-end load. That is point-to-point — the one topology where
  series termination at the driver is textbook-correct.
- **The other order:** the long full-length conductor is `QH` from the far
  cluster's 74LVC165 back to MISO. Driven by an LVC totem-pole with ~2 ns edges,
  unterminated, into an ESP32 input.

That is a signal-integrity argument with real magnitude, unlike the 0.5 ns one.
**Same conclusion, defensible reason.**

**One thing `key-layout.yaml` still does not pin down.** It defines bit 0 as the
first bit clocked out = the device nearest the MCU. It does not say **which of
that device's eight parallel inputs** is bit 0. On a 74x165 the first bit
presented is input **H** (pin 6), so bit 0 = device A input H and bit 7 = input A
(pin 11). `[memory]` This decides which switch solders to which pin — but unlike
the chain direction it is **fully recoverable in firmware**, since any bit order
is a remap. Write it down anyway; a bonded body is a bad place to be
re-deriving pinouts from a logic analyser.

## A-4. Running the chain beside WS2815 power and data

**What actually goes wrong**, in descending order of what this geometry invites:

1. **An extra clock edge.** A 74x165's CP is not a Schmitt input. `[memory]`
   Any glitch across the threshold during the 32-clock shift rotates the whole
   word. Symptom: not one wrong key — *all 32 bits offset*, i.e. a chord.
2. **A glitch on SH/LD below V_IL**, which reloads all four registers mid-shift.
   ADR 0001 already names this. `[repo]`
3. Induced levels on floating inputs — **already fixed** by `R-KEY-PU`. `[repo]`

**What people actually do.** In descending order of effect:

| Mitigation | In Woody? | Notes |
|---|---|---|
| **Series resistor on the LED data line at the driver** (Adafruit: 300–500 Ω) `[web]` | **NO ROW** | The cheapest, highest-leverage item on this list. Two resistors. |
| Bulk capacitance at the strip (Adafruit: 500–1000 µF) `[web]` | `C-STRIP-BULK` 470–1000 µF ×2 `[repo]` | Present. |
| A ground return per signal | ADR 0001 item 1, `WIRE-LOOM` `[repo]` | Present and correctly ranked highest. |
| Twisted pairs | `WIRE-LOOM` allows it `[repo]` | Present. |
| Physical separation | Two side channels exist (ADR 0013) `[repo]` | **Not stated as a rule.** Say which channel carries which. |
| **Schmitt-trigger receiver on CLK and SH/LD at each register** | **NO ROW** | The industrial answer to a clock crossing a noisy cable. ~0.5–1 V of hysteresis. |
| Slowing the clock | ADR 0001's stated fallback `[repo]` | **Does not work.** See §A-5. |
| Moving the LEDs | Not considered `[repo]` | ADR 0014 owns the LEDs; out of scope here. |

**The proportionality problem.** Woody's answer to LED coupling is 21 RC networks
(`R-KEY-SER`, `C-KEY`, `R-KEY-PU` — 63 parts) on the **key inputs**. But
`PCB-CLUSTER` puts the switches *on the cluster board with the register*
`[repo]`, so the key nodes are short board-level traces and flying leads, not
loom conductors. ADR 0001's stated mechanism — *"~15 pF of loom coupling"*
`[repo]` — describes a topology where each key has its own wire in the loom,
which `PCB-CLUSTER` does not have.

Meanwhile the three signals that **are** in the loom — SCK, SH/LD, SER — have no
filtering at all, cannot have any (you cannot RC-filter a clock), and a single
disturbance on any of them corrupts all 32 bits rather than one.

**63 parts protect the least exposed nodes; the most exposed nodes have none.**
The RCs are still worth having — they are the wetting-current and bounce fix, and
a 10 nF discharging through 100 Ω at closure gives a ~33 mA, ~1 µs, 54 nJ wetting
pulse that is good for gold contacts and far too small to weld them. Keep them.
But stop counting them as the LED-coupling defence, because for the signals that
matter they are not in the path.

**Two things belong in the loom plan and are free:** put the key chain in the
**opposite side channel** from the LED runs, and damp the aggressor with a series
resistor at the 74AHCT125 output.

## A-5. 74LVC165A vs 74HC165 — and the termination that does not terminate

**Woody's family analysis is right and the correction in ADR 0001 is right.**
Critical length — the point at which a line stops being lumped — is roughly
`t_r · v / 2`. At ~5 ns/m, a 2 ns LVC edge gives ~200 mm and a 15–25 ns HC edge
gives ~1.5–2.5 m. `[memory]` So **a 360 mm loom is a transmission line for LVC
and a lumped load for HC**, and ADR 0001's statement that the "better drive over
a long chain" justification was backwards is correct. `[repo]`

**But the termination Woody chose is the wrong kind for this topology.**

`R-TERM-CHAIN`: *"33–68 Ω 1 %, series termination on key-chain clock and latch
at the MCU"*, qty **2**. `[repo]` The clock and latch lines drop on **four**
cluster boards distributed along ~265 mm. That is multidrop.

Series termination is documented as a point-to-point technique. With a receiver
partway down the line, "the noise margin seen by the middle receiver would change
between the incident signal and the reflected signal"; an attempted multidrop
implementation "results in distortion of the signal caused by the superposition
of the forward and backward waves". `[web: TI SNLA034B; SiTime AN10002]` The
intermediate node sits at the incident step

```
V_incident = V_CC · Z0 / (Z0 + R_s + R_out)
```

until the far-end reflection returns — about 3.6 ns round trip here.

Run the numbers against 74LVC's V_IH = 2.0 V, V_IL = 0.8 V at 3.3 V `[memory]`,
taking the LVC output impedance as ~15 Ω and loom Z0 as 100–200 Ω:

| R_s | Z0 = 100 Ω | Z0 = 150 Ω | Z0 = 200 Ω |
|---|---|---|---|
| **33 Ω** | 2.48 V ✅ | 2.68 V ✅ | 2.81 V ✅ |
| **68 Ω** | **1.96 V ❌** | 2.20 V ⚠ | 2.36 V ✅ |

**At the top of Woody's own specified range, the incident wave can land below
V_IH at the intermediate cluster boards**, leaving them in the forbidden band for
~3.6 ns on every clock edge — and the falling edge is symmetric, sitting at
~1.2 V, above V_IL. A slow, threshold-region transition on a non-Schmitt clock
input, in a channel shared with a 5 V LED data line, is precisely the
double-clocking recipe.

**`R-TERM-CHAIN` currently reads "33–68 Ω". Specify 33 Ω. Do not use 68 Ω.**
This is an unretrofittable value on a carrier inside a bonded body, and the
direction is counterintuitive — more series resistance feels safer and is worse
here.

**Three other termination gaps, all unretrofittable:**

- **`R-TERM-CHAIN` is qty 2 and there are 5 more LVC outputs driving loom
  conductors**: three inter-cluster `QH → SER` hops and the final `QH → MISO`.
  Each is an unterminated LVC totem-pole into 100–150 mm — right at the critical
  length. These are *synchronous data* lines, so ringing that settles inside a
  clock period is harmless; the concern is undershoot forward-biasing the
  receiving input's clamp and injecting current back into the chain. **Four more
  33 Ω resistors, one at each 74x165 QH, on the cluster boards.** Low cost, and
  impossible afterwards.
- **`CLK INH` (pin 15) must be tied low at every device.** The cold review's
  `C1-active-parts.md` says so `[repo]`; no ADR and no BOM row does. A floating
  clock-inhibit stops the chain.
- **The eleven parallel inputs with no pull-up.** `R-KEY-PU` is qty 21 for 18
  switches + 3 spares. `config/key-layout.yaml` allocates 6 marker bits (tied) and
  leaves **`spare_bits_free: 5`** `[repo]` — five CMOS inputs with nothing on
  them. That is the exact fault `R-KEY-PU` exists to fix, reintroduced on the
  leftovers. DodoHand grounds its six unused inputs at the package. `[repo]` Do
  the same.

**And the fallback that will not work.** ADR 0001 says setup margin is
"recoverable by clocking slower". `[repo]` True of the skew term — which is
0.5 ns and irrelevant. **Reflection-induced double-clocking is set by edge rate,
not clock rate, so halving the clock does not touch it.** If the chain misbehaves
at E4, the recovery is the family swap ADR 0001 already provisions (74HC165, same
SOIC-16) — and that works precisely *because* it slows the edges, not the clock.
Say that, so the wrong knob does not get turned first.

**On 74x166 vs 74x165.** ADR 0001 names the async level-sensitive `SH/LD` as one
of two things that make a corrupt read worse than it looks. `[repo]` The 74x166
loads on the clock edge instead: *"when the parallel enable input is LOW, the
data … is loaded into the shift register on the next LOW-to-HIGH transition of
the clock"*, which "eliminates glitches because the load occurs on a clock edge".
`[web]` Same SOIC-16, same 8 bits, costs one extra clock per read and drops the
`QH̄` output nobody is using. **This is a catalogue solution to a hazard Woody
is solving with wiring discipline**, and it is worth an hour's evaluation before
`PCB-CLUSTER` is laid out. (74LVC166 may not exist; 74HC166/74HCT166 does.
`[memory]` — and given §A-5's edge-rate argument, HC is the family that wants
choosing anyway.)

## A-6. Asymmetric debounce: it has a name, and the downside is documented

**Do real instruments do this? Yes, and keyboards have shipped it for years.**

QMK's supported-algorithm table lists **`asym_eager_defer_pk`**:
*"On a key-down state change, response is immediate, followed by DEBOUNCE
milliseconds of no further input for that key. On a key-up state change, a
per-key timer is set. When DEBOUNCE milliseconds of no changes have occurred on
that key, the key-up status change is pushed."* `[docs]` That is Woody's rule,
verbatim, with a name. Default `DEBOUNCE` is **5 ms**; the source clamps at
127 ms and defaults to 5. `[code: quantum/debounce/asym_eager_defer_pk.c]`

**The documented downside is exactly the one ADR 0001 rediscovered.** QMK states
it as a property of the class: *"Eager algorithms are not noise-resistant."*
`[docs]` ZMK repeats it — *"Eager debouncing means reporting a key change
immediately and then ignoring further changes for the debounce time. This
eliminates latency but it is not noise-resistant"* — and gives the remedy:

> *"Also consider setting `CONFIG_ZMK_KSCAN_DEBOUNCE_PRESS_MS=1` instead, which
> adds one millisecond of latency but protects against short noise spikes."* `[docs]`

**Woody's "two consecutive agreeing samples" rule is that remedy**, at 250 µs
instead of ZMK's 1 ms. `[repo]` It is the right fix and it is tighter than
practice. The only change needed is citation: ADR 0001 presents it as a local
discovery, which makes it look optional. It is the documented mitigation for a
documented weakness of a named algorithm.

**Window lengths in practice:**

| Source | Press | Release | Scope |
|---|---|---|---|
| QMK default (`sym_defer_g`) | 5 ms | 5 ms | **global** — whole keyboard must be quiet `[docs]` |
| QMK `asym_eager_defer_pk` | 0 (+5 ms lockout) | 5 ms | per key `[docs]` |
| ZMK default | 5 ms | 5 ms | per key `[docs]` |
| ZMK "eager" recipe | **1 ms** | 5 ms | per key `[docs]` |
| **OWP 2021** | **20 ms, on the resolved note** | 20 ms | **the fingering pattern** `[code] src/owp/owp.ino:76,347–357` |
| OWP 2021 trigger mode | 10 ms | 10 ms | per key `[code] owp.ino:308–312` |
| **Woody** | 250 µs (2 samples) | filtered, length TBD at M1 | per key, release moved to note level `[repo]` |

**The 2021 code is the most interesting row and it is Woody's own.** It debounces
the *resolved note*, not the key:

```c
note_fingered_debounce = 60 + parseNote();
if (note_fingered_debounce != note_fingered) {
  if (note_debounce) { if (millis() > note_debounce_time + note_debounce_delay) { … } }
  else { note_debounce_time = millis(); note_debounce = true; }
}
```
`[code] src/owp/owp.ino`

That is not contact-bounce filtering. It suppresses **transient intermediate
fingerings** during a multi-finger move, which on a woodwind is the dominant
source of spurious notes and has nothing to do with switch bounce. QMK's default
`sym_defer_g` — a *global* "wait until the whole keyboard is quiet" timer — is
the same idea arrived at from the other direction. `[docs]`

Woody's ROADMAP already reaches this conclusion independently: *"apply the
release filter to the note decision, not to each key independently. A key that
opens while others close is part of a transition, not a release."* `[repo]`
**Good. Three independent sources agree.** What ROADMAP does not say, and should,
is that the *press* side needs the same treatment: a key that closes while others
open is also part of a transition. A per-key eager press means the instrument
speaks the intermediate fingering. The 2021 instrument did not have this problem
because its 20 ms window sat on the pattern, not the key.

**And the premise correction.** The brief for this research states that the 2021
project "used a similar chain". It did not. `src/owp/owp.ino` header lists
*Teensy 3.2, MPR121 (0x5A), MPR121 (0x5B), MPX2010GS, BNO055* `[code]`, and
`grep -rn "165"` over `src/owp/` and `src/owp_full/` returns nothing outside
unrelated float tables. Keys were **capacitive touch over I2C**
(`touchA.filteredData(i) < SETTINGS_TOUCH_LEVEL`) `[code]`. Breath was
`analogRead(A0)` — the Teensy's internal 10-bit ADC with software gain 3.0 and a
threshold of 225, with the exponential smoothing commented out `[code]`.

**There is therefore no in-house prior art for any of Part A.** Not the chain,
not the switches, not mechanical contacts at all. Everything ADR 0001 asserts
about bounce, coupling and chain behaviour is first-principles reasoning with no
measurement behind it, in a build that gets one attempt. That raises the value of
M1 and E4 considerably, and it means the marker-pattern error counter (ADR 0001)
is not a nicety — it is the only instrument Woody will have.

**One free refinement to the marker.** `V4-fix-conflicts.md` specifies "mixed
polarity, one per cluster board" `[repo]`. One bit per cluster alternating
1-0-1-0 detects a shift of 8 but **not a shift of 16** — cluster 0's `1` lands in
cluster 2's slot, which also expects `1`. Since a bit-shift is the characteristic
corruption of a clock glitch, spend **two bits per cluster as a 2-bit cluster ID
(00, 01, 10, 11)**. That detects every multiple-of-8 shift. It costs 8 of the 14
spare bits instead of 4–6, it is wiring-only, and it cannot be added later.

---

# Part B — SAR ADC front end

## B-1. Is the MCP3202 a sensible part?

**Yes — and MCP3201 is a better fit for the same money.**

The job is 12 bits, one channel, 4 kHz, hand-solderable. Woody's package policy
(`SOIC/SIP/TH preferred; QFN/BGA avoid`, ADR 0013 `[repo]`) rules out most modern
alternatives — TI's ADS7042/ADS7040 are X2QFN `[memory]`. Within SOIC-8 the
Microchip MCP32xx family is the obvious and correct answer, and nothing cheaper
or simpler exists for this. **The part choice is fine.**

The finer point is *which* MCP32xx. `U-ADC`'s note reads:

> *"VDD-referenced so no separate ref chip. 50ksps at 3V3 vs 4-8kHz needed. One
> spare channel"* `[repo]`

"VDD-referenced so no separate ref chip" states a **limitation as a feature**.
The MCP3202 has no VREF pin — its reference is VDD, and that is not a saving,
it is the absence of an option. `[memory]` The MCP3201 is the same package,
the same speed, single channel, **and has a separate VREF pin**; MCP3204/3208
likewise. `[memory — pinouts; datasheets BLOCKED]`

Woody needs **one** channel. The 3202 buys a spare channel by spending the
reference pin, three centimetres from a REF5050 whose whole job is to be a stable
5.000 V.

**Whether to switch is a real trade, not a slam dunk.** A SAR's VREF pin draws
charge every conversion, so driving it from a resistive divider off the REF5050
needs a buffer or a stiff low-impedance divider plus a cap `[memory]` — and both
halves of the OPA2197 are already spoken for (ADR 0003). The gain it buys is
quantified in §B-3 and is small. **My recommendation is to keep the MCP3202 and
fix the note**, not to change the part. But the note as written will mislead
whoever revisits this.

## B-2. Anti-alias filtering and the sample-and-hold

**What a SAR actually wants.** The MCP3202's internal sample capacitor is
**20 pF**, charged over **1.5 clock cycles**, and the source "must be
low-impedance — generally well below 500 Ω with a 5 V VREF to ensure good
measurements at the highest clock frequency"; an unbuffered high-impedance source
"will have to be buffered or inaccurate conversion results may occur". `[web,
quoting the datasheet]` Microchip AN246 and the general literature give the
standard structure: **a large capacitor at the ADC pin acts as a charge reservoir
so the sample cap charges by charge-sharing rather than through the source
impedance**, with the conventional sizing rule of at least 10–20× the sample
capacitance. `[web]`

**Woody's 47 nF is 2350× the sample cap.** `[repo] C-AA-ADC` So:

> **The cap is not too large. It is what makes the 6 kΩ divider legal in the
> first place.**

That is the opposite of the question's framing and it is the important point.
Without the cap, a 6 kΩ source into a 20 pF sample cap in 1.5 clocks would be a
real settling problem. With it, the ADC never sees 6 kΩ on the acquisition
timescale.

**Does the charge-sharing error matter?** Compute it. Average current drawn:

```
I_avg = C_s · V_in · f_s = 20 pF × V_in × 4 kHz = 80 nA per volt
ΔV     = I_avg × R_th   = 80 nA/V × 6 kΩ = 480 µV per volt  =  0.048 %
```

At 12 bits, 1 LSB = 1/4096 = 0.0244 %, so this is **~2 LSB at full scale**, it is
**proportional to V_in** (a pure gain term), and it is **constant**. Woody's
digital breath copy has its zero auto-tracked in firmware (ADR 0003, ADR 0006)
and its span set by a panel knob `[repo]`, so a fixed 0.048 % gain error is
invisible twice over. **It does not matter — and now there is a number behind
that, where ADR 0003 currently just asserts it.**

**The real cost of 47 nF into 6 kΩ is group delay, and it is unbooked.**

```
τ = 6 kΩ × 47 nF = 282 µs
f_c = 1/(2πτ) = 564 Hz          (matches C-AA-ADC's own note)
```

**282 µs exceeds the 250 µs loop period.** `docs/reference/latency-budget.md` and
ADR 0003's latency table list "SAR ADC conversion ~50–200 µs" and no RC term at
all. `[repo]` But note-on fires off a breath threshold read *through this
filter*, while the analog CV at the jack is taken from the buffer *before* it.
So the gate decision lags the CV it is gating by ~282 µs, and the note-on path
carries ~282 µs that nothing has budgeted. Against a 5 ms target that is ~5.6 % —
not fatal, but it belongs in the table, especially since the table is the
document that decided 4 kHz over 8 kHz.

`C-AA-ADC`'s note also says 564 Hz "matches the 500 Hz channel everywhere else"
`[repo]`. It does, but the sensor's own bandwidth is ~159 Hz (ADR 0003), so the
corner is only 3.5× above the signal — at 159 Hz that is −0.34 dB and 15.7° of
phase. Acceptable; worth knowing it is a 3.5× ratio and not the 10–20× one
usually wants ahead of a sampler.

**Note also that ADR 0003's body still says 220 nF** ("220 nF gives a ~600 Hz
corner and 58 dB at 500 kHz") while the BOM says 47 nF and explains why 220 nF
was wrong. `[repo]` The BOM is right — 220 nF into 6 kΩ is 121 Hz, not 600 Hz;
600 Hz would need a ~1.2 kΩ source. The ADR text is stale and still argues from
the superseded value.

## B-3. Ratiometric measurement with a separate reference

**Is it a mistake? No — but ADR 0003 defends it with the wrong argument.**

The usual practice exists for a specific reason: in a normal design **the digital
reading is the output**, so you make the sensor and the ADC share a reference and
the ratio cancels. ADR 0003 states this and then says the free fix "does not
apply here" because the path is analog to the jack. `[repo]` That is correct for
the *CV* — and it is also the complete answer for the *digital copy*, which
ADR 0003 never quite says. Instead it defends keeping the ADC at 3.3 V on the
grounds that a 5 V VDD would put 5 V on DOUT into a non-5 V-tolerant ESP32 pin.
`[repo]` True, but that is a consequence of one particular way of going
ratiometric, not an analysis of whether ratiometric is wanted.

**Here is what the mismatch actually costs.** The reading is

```
code = 4096 × (0.6 × V_REF5050 × f(P)) / V_DD(ADC)
```

Numerator: REF5050 at ±0.05 % and 3 ppm/°C `[repo]`. Denominator: the dev
board's onboard LDO. So **the digital reading's scale factor is 1 / V_LDO**, and
it inherits that LDO's initial accuracy (typ. ±1–2 %), load regulation
(typ. 0.1–0.5 % per 100 mA) and output noise (tens of µV RMS). `[memory]`

What survives: **only gain error**, because the zero is auto-tracked in firmware
and the span is set by a panel knob. `[repo]` A 0.1–0.5 % gain wobble on a
breath threshold, a MIDI CC (7 bits = 0.8 % per step) and four mod channels is
below anything audible. **Verdict: not a mistake, and not worth an extra part.**

**But there is a hole, and it is symmetric with one Woody already found.**
ADR 0003 spends a page establishing that unfiltered noise on the *signal* aliases
into the breath band at 4 kHz sampling, and adds `C-AA-ADC` to fix it. `[repo]`
For a VDD-referenced SAR, **VREF is in the transfer function identically and has
no anti-alias filter at all.** And the repo's own `C-STRIP-BULK` note records
that the WS2815 PWM rate is **~2 kHz** `[repo]` — *exactly Nyquist for a 4 kHz
sampler*. Any 2 kHz ripple that reaches the ADC's VDD multiplies every reading
and folds to DC or to a slow beat depending on phase.

Magnitude is small — the LEDs are on 12 V, the R-78E5.0s and the dev board LDO
are in between, and `C-STRIP-BULK` is at the strip — but the mechanism is the one
the ADR calls a showstopper elsewhere, and the right response costs a capacitor.
**Decouple the MCP3202's VDD/VREF pin hard and locally**, with bulk, and treat
that pin as an analog reference rather than a logic supply. The cold review's
`B6-instrument-power.md` already proposes giving the MCP3202 its own 3.3 V supply
on the carrier `[repo]`; this is an independent reason to do it.

**One more consequence of VDD = VREF that is written nowhere.** Sourced from the
datasheet via search: **100 ksps at 5 V, 50 ksps at 2.7 V** `[web]`. At 18 clocks
per 12-bit conversion that is **f_CLK ≈ 1.8 MHz at 5 V, ≈ 0.9 MHz at 2.7 V**.
Microchip does not spec 3.3 V, so 0.9 MHz is the number to design to. `[repo]`
ADR 0003, ADR 0004 and `latency-budget.md` all specify **SPI2 at 2 MHz** for the
DAC8568 `[repo]`, and the MCP3202 is on SPI2. **2 MHz over-clocks the ADC by more
than 2×.** ESP-IDF sets the clock per *device* on a shared host, so this is a
firmware line, not a redesign — but it is not written anywhere and "SPI2 runs at
2 MHz" appears in four documents.

**Related, and worth one check before layout:** ADR 0007 records that the
ESP32-S3-Matrix's 64 WS2812C parts are "driven over SPI2 in Zephyr's
configuration". `[repo]` Both of the S3's general-purpose SPI hosts are
allocated (SPI2 = DAC + ADC, SPI3 = key chain). **The matrix must be driven by
RMT, not SPI.** If anything ends up bit-banging WS2812 timing over SPI2, it will
share a bus with the breath converter.

## B-4. The 10 k / 15 k divider and the ESD clamp

**Is a ≥10 kΩ series element the standard fix? Yes.** Every MCU and converter
datasheet's absolute-maximum section limits input current into a pin (commonly
±2 mA to ±20 mA) and the conventional remedy is a series resistor sized to that
limit when an input can be driven above its own supply. `[memory]` Woody's upper
divider leg *is* that series resistor, and the reasoning in ADR 0003 is sound.
`[repo]`

**Two corrections.**

1. **The number is stale.** ADR 0003 computes from a **5 V** source: *"On a cold
   start the 5 V rail comes up before the real-time board's 3.3 V regulator … A
   low-impedance divider puts ~2.5 mA into that diode."* `[repo]` But ADR 0003
   itself moved the breath buffer to **+12 V** (to dissolve the fault-protection
   conflict) `[repo]`, and the divider hangs off that buffer's output. Worst case
   is now:

   ```
   I_clamp = (12 V − 0.7 V) / 10 kΩ − 0.7 V / 15 kΩ ≈ 1.08 mA
   ```

   against a family-typical ±2 mA. **10 kΩ still passes — with 1.8× of margin,
   not the ~4× the 5 V arithmetic implies.** Update the number, or the next
   person to optimise the divider downward will do it from the wrong baseline.

2. **The 47 nF helps here too and nobody says so.** It slows the rise at the ADC
   pin during sequencing, so the peak clamp current is lower than the DC
   calculation. Free, and worth recording as a third job for that capacitor.

**The alternative practice** is a Schottky or dual-diode clamp from the ADC input
to VDD (BAT54S, BAV99) rather than relying on the internal ESD structure. The
cold review's `D1-missing-protection.md` already proposes "1 kΩ + BAV99" for a
related node `[repo]`. That is the more robust idiom, and it would free the
divider to be low-impedance — which would in turn shrink the 282 µs group delay
in §B-2 and the 0.048 % gain error. **All three of Woody's ADC-branch quirks
trace to one root: a high-impedance divider chosen to do a protection job.** One
diode pair would decouple them. Whether that is worth two more parts on the
carrier is a judgement call; it is at least worth making knowingly.

---

# What Woody should change

Ordered by consequence × irreversibility. Items marked **PERMANENT** cannot be
fixed after the body is bonded.

1. **PERMANENT — Resolve where the four 74LVC165s live.** `PCB-CARRIER` and
   `PCB-CLUSTER` in `hardware/bom.csv` both claim them; ADR 0013 and ADR 0001
   say different things. The two answers specify opposite looms and different
   conductor counts, and the carrier-mounted version eliminates §A-5 entirely by
   putting nothing clocked in the LED channel. **Nothing else in Part A can be
   finalised first.** (§A-1)
2. **PERMANENT — Specify `R-TERM-CHAIN` as 33 Ω, not "33–68 Ω".** Series
   termination on a four-drop line leaves intermediate receivers at the incident
   half-step for ~3.6 ns per edge; at 68 Ω that step can land below V_IH. This is
   counterintuitive — the larger, "safer-feeling" value is the worse one. (§A-5)
3. **PERMANENT — Add a 33 Ω series resistor at every 74x165 `QH` output**
   (4 parts, on the cluster boards), not just the two at the MCU. (§A-5)
4. **PERMANENT — Add a 330–470 Ω series resistor on each WS2815 data line at the
   74AHCT125.** No such row exists. It is the Adafruit-standard practice, it damps
   the single strongest aggressor in the loom, and it costs two 0805s. Far better
   leverage than the 63 passives currently defending the victims. (§A-4)
5. **PERMANENT — Tie off the loose ends.** `CLK INH` low at all four devices;
   all eleven unused parallel inputs (including `spare_bits_free: 5`) tied hard,
   not floating. Both appear only in `docs/review/`, in no ADR and no BOM row.
   (§A-5)
6. **PERMANENT — Make the marker a 2-bit cluster ID (00/01/10/11), not an
   alternating single bit.** The characteristic corruption is a bit-shift, and an
   alternating 1-0-1-0 marker cannot detect a shift of 16. Costs 8 of the 14
   spare bits. (§A-6)
7. **PERMANENT — State the loom's channel assignment**: key chain in the opposite
   side channel from the LED runs. ADR 0013 establishes two channels; no document
   says which carries what. (§A-4)
8. **Evaluate 74HC166 before `PCB-CLUSTER` is laid out.** Its synchronous
   parallel load removes the async-`SH/LD` hazard ADR 0001 names as a top-two
   risk, for the same SOIC-16 and one extra clock. Given §A-5's edge-rate
   argument, HC is the family that wants choosing anyway. (§A-5, §A-9)
9. **Correct the chain-order claim.** `config/key-layout.yaml` says the wrong
   order "would have put hold-margin violations into a body that cannot be
   reopened". It costs ~0.5 ns of a margin dominated by a ~5–9 ns clock-to-out —
   roughly 12 % degradation, not a violation. Keep the order; replace the
   justification with the signal-integrity one (§A-3), which is real and larger.
10. **Correct ADR 0001's fallback.** "Recoverable by clocking slower" is true of
    skew and false of reflection double-clocking. The real recovery is the 74HC165
    swap, and it works because it slows *edges*. (§A-5)
11. **Cite `asym_eager_defer_pk` and ZMK's 1 ms recommendation in ADR 0001.** The
    two-consecutive-samples rule is the documented mitigation for a documented
    weakness of a named, shipped algorithm — not a local discovery. That makes it
    non-negotiable rather than a nice idea. (§A-6)
12. **Extend the transition rule to the press side.** ROADMAP correctly moves the
    *release* filter to the note decision; a key that closes during a transition
    is the same problem. The 2021 code debounced the pattern in both directions at
    20 ms. (§A-6)
13. **Delete "used a similar chain" wherever it appears.** The 2021 instrument
    used MPR121 capacitive touch on I2C. **There is no in-house prior art for any
    of Part A**, which raises what M1 and E4 are actually worth. (§A-6)
14. **Book the 282 µs.** `docs/reference/latency-budget.md` has no term for the
    ADC anti-alias RC, which is longer than the loop period and sits on the
    note-gating path. (§B-2)
15. **Reconcile ADR 0003's 220 nF text with the BOM's 47 nF.** The ADR body still
    argues from the superseded value and its "~600 Hz corner" was never right for
    a 6 kΩ source. (§B-2)
16. **Fix `U-ADC`'s note.** "VDD-referenced so no separate ref chip" is a
    limitation written as a feature. Record that MCP3201 is the single-channel
    part with a real VREF pin, that the spare channel was chosen over it, and why.
    (§B-1)
17. **Record the MCP3202 clock ceiling.** ~0.9 MHz at 3.3 V (derived from
    50 ksps × 18 clocks) against SPI2's specified 2 MHz. Per-device clock, one
    line of firmware — and currently written nowhere. (§B-3)
18. **Re-derive the ≥10 kΩ divider from +12 V, not 5 V.** ~1.08 mA, 1.8× margin.
    (§B-4)
19. **Decouple the MCP3202's VDD/VREF as a reference, not a logic supply**, with
    local bulk. The alias argument ADR 0003 makes for the signal applies to VREF,
    and the WS2815 PWM rate is ~2 kHz against a 4 kHz sampler — exactly Nyquist.
    (§B-3)
20. **Confirm the 8×8 matrix is driven by RMT, not SPI.** Both SPI hosts are
    allocated; ADR 0007 records the vendor board's Zephyr config puts the matrix
    on SPI2, which is the breath ADC's host. (§B-3)

# What Woody should keep

- **The chain order.** Right rule, right side of it, and it costs nothing. Only
  the stated magnitude is wrong. (§A-3)
- **The bit-0 definition** in `config/key-layout.yaml` — first bit out = device
  driving MISO = nearest the MCU. Correct for a 74x165 chain. Add which *pin*
  (input H) is bit 0 within the byte; unlike the chain direction that part is
  recoverable in firmware. (§A-3)
- **The asymmetric debounce, plus the two-sample rule.** QMK ships the algorithm;
  ZMK documents the exact fix Woody applied, at 1 ms where Woody uses 250 µs.
  Tighter than practice, in the right direction. (§A-6)
- **The release filter at the note level, not the key level.** Woody's own 2021
  code, QMK's default global-defer, and the ROADMAP all land here. (§A-6)
- **`R-KEY-PU` / `R-KEY-SER` / `C-KEY`.** Floating CMOS inputs are never
  acceptable; the pull-ups are mandatory. The 100 Ω also gives a ~33 mA, ~1 µs,
  54 nJ wetting pulse at closure — good for gold contacts, far below any welding
  energy — and bounds injected current. Keep all 63 parts. Just stop describing
  them as the LED-coupling defence for signals that are not in the loom. (§A-4)
- **A ground return per signal**, ranked as ADR 0001's highest-value wiring item.
  Practice agrees. (§A-4)
- **Chaining the topology rather than starring it.** (§A-4)
- **The marker pattern and its visible error counter.** With no in-house prior art
  for the chain, this is the only instrument that will distinguish a marginal
  loom from playing mistakes. Widen it to a 2-bit cluster ID. (§A-6)
- **`C-AA-ADC` at 47 nF.** Not too large — 2350× the 20 pF sample cap against a
  textbook 10–20× minimum, and it is what makes a 6 kΩ source legal. The
  charge-sharing error is 0.048 %, constant, and a gain term on a signal that is
  zeroed in firmware and spanned by a knob. (§B-2)
- **The MCP3202.** Correct class of part, correct package for a hand-built
  carrier, and nothing meaningfully better exists in SOIC-8 at this price under
  Woody's own package policy. (§B-1)
- **The ADC on 3.3 V with the sensor on REF5050.** Not a mistake. The usual
  ratiometric rule exists because the digital reading is usually the output;
  here it is not, the surviving error is gain-only, and gain is set by a panel
  knob. Only the *reason recorded* needs replacing. (§B-3)
- **The ≥10 kΩ divider leg.** Standard practice, correctly identified; only the
  source voltage in the arithmetic is stale. (§B-4)
- **LVC with series termination, and 74HC165 as the documented fallback.**
  ADR 0001's correction — that "better drive over a long chain" was backwards —
  is right, and the critical-length arithmetic supports it: 360 mm is a
  transmission line for LVC's ~2 ns edges and a lumped load for HC's ~15–25 ns.
  The termination *topology* needs fixing (§A-5), not the family reasoning.

---

## Sources

Read directly this session:

- `/home/user/Woody/docs/decisions/0001-mcu-and-board-partitioning.md`,
  `0003-breath-sensing-path.md`, `0007-imu-selection.md`, `0013-two-mcu-split.md`
- `/home/user/Woody/config/key-layout.yaml`, `/home/user/Woody/hardware/bom.csv`,
  `/home/user/Woody/ROADMAP.md`
- `/home/user/Woody/docs/review/2026-09-20-cold-review/` —
  `A1-contradictions.md`, `A3-bom-consistency.md`, `C1-active-parts.md`,
  `verification/V4-fix-conflicts.md`
- `/home/user/jeffmhopkins/open-woodwind-project/src/owp/owp.ino`,
  `README.md` (2021 predecessor, cloned this session)
- QMK `docs/feature_debounce_type.md` and
  `quantum/debounce/asym_eager_defer_pk.c` (raw.githubusercontent.com)
- ZMK `docs/docs/features/debouncing.md` and `docs/docs/config/kscan.md`
  (raw.githubusercontent.com)
- `wolfv6/keybrd_DH` `examples/shiftRegs/README.md`;
  `christrotter/shift-register-spi-breakout-pcb` `README.md`;
  `JamFox/Shiftboard` `README.md` (raw.githubusercontent.com)
- `ianmaclarty/ik` (cloned; KiCad sources use `gateron-ks27` on an RP2040-Zero
  with a diode matrix — **not** a shift-register build, so of limited value to
  this topic beyond the switch geometry ADR 0002 already cites)

Web-search summaries only (primary documents blocked): TI SNLA034B and SiTime
AN10002 on series-termination topology; US 6,381,719 on shift-register clock
counterflow; Microchip AN246 on SAR input driving; MCP3202 sample-cap,
acquisition-time, source-impedance and sample-rate figures; 74HC166 / 74HC589
functional descriptions; Adafruit NeoPixel Überguide best practices.

**Not reachable — say so rather than trusting the numbers below:** every
component-vendor domain listed at the top. The 74LVC165A timing figures
(t_PD, t_su, t_hold, V_IH, V_IL, Δt/Δv), the MCP3202 pinout and VREF behaviour,
the MCP3201 pinout, the WS2815 PWM rate and input thresholds, and the ESD clamp
current ratings are all `[memory]` or `[web]` here. **Before anything in "What
Woody should change" is committed to copper, the 74LVC165A and MCP3202
datasheets need reading on a machine that can reach them.** The conclusions are
robust to moderate error in those numbers — §A-5's margin table is the one most
sensitive, and its sensitivity is to loom Z0, which nobody has measured either.
