# A4 — Module power: rails, sequencing, and what powers up in what order

**Wave:** 2026-09-21 pre-merge review. **Agent:** A4. **Slice:** module power —
rack ±12 V through the keyed header, reverse protection, beads and bulk, the
branch, the LM317 local rail, bus +5 V for the level shifter, and the LT1641
load switch that exports +12 V up the umbilical.

**Cold:** nothing under `docs/review/**` was read. Every claim below carries
provenance. `[repo]` is a file and line in this tree, `[calc]` shows the
arithmetic, `[datasheet]` names the banked document and page.

**Report, do not fix.** Nothing in the corpus was modified.

## Method

Re-derived every number in the slice from the drawn values and the banked
datasheets, then compared against what the corpus states. PDFs were read with
`pypdf` against `datasheets/discrete-and-power/LM317LZ.pdf` (TI SLCS144E),
`datasheets/discrete-and-power/LT1641.pdf` (`164112fc`) and
`datasheets/analog/DAC8568CIPW.pdf` (SBAS430E), all verified present in
`datasheets/MANIFEST.csv` `[repo]`.

Twenty findings, indexed by circuit node or BOM reference. Four are marked
CRITICAL or near it; the two I would act on first are **A4-2** (the DAC rail
does not clear its own floor) and **A4-5** (nothing sequences the level
shifter against AVDD).

---

## Summary against the six audit questions

| # | Question | Answer |
|---|---|---|
| 1 | Does the DAC rail clear its `floor`? | **No.** Guaranteed low corner is **4.992 V** against a 5.00 V hard floor. And the `0.66 V` spread quoted in six places is the *superseded* divider's number — the real spread is 0.480 V. **A4-2, A4-3, A4-4, A4-20** |
| 2 | Anything preventing inputs being driven before AVDD is up? | **Nothing, and it is not recorded.** On power-down bus +5 V outlives AVDD by ~3 orders of magnitude and the permanently-enabled buffer drives the DAC's inputs past `AVDD + 0.3 V`. The corpus applies exactly this mitigation one stage *downstream* and omits it here. **A4-5, A4-6** |
| 3 | Does the present load switch start? SOA/hot-plug margin? | **Yes, it starts** — §5's `FB` fix is correct and the values reproduce exactly. But the **2.01× margin is 1.48×** on guaranteed silicon, the cold start takes **39.6 %** of the fault timer rather than 10.5 %, and the FET has no gate-drive criterion. **A4-9, A4-10, A4-11, A4-12, A4-19** |
| 4 | Is the three-diode split claim and its chain right? | **Conclusion yes, two numbers no.** `r_d 69 mΩ` is the ideal-diode formula and is refuted by the same entry's own digitised curve (~324 mΩ); and 392 mA is the *pre-split* current, through neither diode. **A4-13** |
| 5 | What do the jacks do at power-up/down, and does it reach a VCO? | **Yes, it reaches a VCO.** Pitch sits at **0 V — an ordinary audible note** — for ~1 s at every rack power-on, not "below −2 V, subsonic". And every power-down pulls all six jacks toward the negative rail for ~30 ms at the bulk values the page draws. **A4-7, A4-8** |
| 6 | Grounding origin consistent? Is the dispute still live? | **Origin is consistent.** The `DIG_GND` dispute is **still live** — ADR 0004 was never corrected, exactly as the register says. Verified. **A4-16** |

---

## 1. The DAC rail

### A4-2 [CRITICAL] — node `DAC AVDD`: the guaranteed low corner is below the floor, and the spread that justified "no nominal value fits" belongs to the superseded divider

**The floor.** `dac-rail.floor` is *"5.00 V, HARD … E7 selects `R-REG-SET` on the
bench across a **0.66 V** worst-case spread and must not land below 5.00 V"*
`[repo] config/figures.yaml:236`. The same 0.66 V appears in
`docs/decisions/0004-cv-interface-module.md:186`,
`docs/decisions/0006-cv-channel-allocation.md:189`, `ROADMAP.md:48`, and both
copies of the `U-REG-DAC` row (`hardware/bom.csv:110`,
`hardware/unplaced.csv:22`) `[repo]`.

**The parts actually drawn** are `LM317LZ` with `R-REG-SET` = 150 Ω / 475 Ω at
**0.1 %** `[repo] hardware/module/power-entry/power-entry.md:42-45,
hardware/bom.csv:111`.

**The datasheet terms**, read off the banked document
`[datasheet] SLCS144E p.5, datasheets/discrete-and-power/LM317LZ.pdf`:
reference voltage (output to ADJUSTMENT) **1.2 / 1.25 / 1.3 V**, specified over
the full operating junction-temperature range at `V_I−V_O` = 5–35 V and
`I_O` = 2.5–100 mA — so temperature, line and load are *already inside* that
window. ADJUSTMENT current **50 typ / 100 max µA, no minimum specified**, so the
guaranteed worst case for the low corner is `I_ADJ` = 0.

**Worst-case low corner** `[calc]`:

```
V_out(min) = V_ref(min) x (1 + R2(min)/R1(max)) + I_ADJ(min) x R2(min)
           = 1.20 x (1 + 474.525 / 150.150) + 0
           = 1.20 x 4.160340
           = 4.9924 V
```

**4.992 V — 7.6 mV BELOW the 5.00 V floor.** Crediting `I_ADJ` at its 50 µA
typical (not guaranteed) gives 5.0161 V, +16 mV. Either way the floor is not
cleared by anything the datasheet guarantees.

**Worst-case high corner** `[calc]`:
`1.30 x (1 + 475.475/149.850) + 100 µA x 475.475 = 5.4249 + 0.0475 = 5.4725 V`.

**So the real spread is 0.480 V, not 0.66 V.** The 0.66 V is the **240 Ω / 768 Ω
at 1 %** divider that ADR 0004 itself records as superseded (*"Shrink R2 —
150 Ω / 475 Ω instead of 240 Ω / 768 Ω"*, `[repo]
docs/decisions/0004-cv-interface-module.md:195-197`). Recomputing on those
values reproduces it exactly `[calc]`:

```
old 240/768 @1%:  low 4.9640   high 5.6216   spread 0.6576  ->  "0.66 V"
new 150/475 @0.1%: low 4.9924  high 5.4725   spread 0.4800
```

This is the project's named failure mode: the divider changed, and the number
derived from it did not follow into any of the six places that quote it.

**And the direction matters.** The improvement landed almost entirely at the
*top* (5.6216 → 5.4725 V). The low corner moved only +28 mV (4.9640 → 4.9924 V),
because it is dominated by `V_ref(min)` = 1.20 V and no divider tolerance
touches that. **The 0.1 % parts did not buy margin against the floor, which is
the only end that now has a hard limit** — and the corpus reads as though they
did.

**One further consequence.** ADR 0004's *"no nominal value fits on paper"*
`[repo]:186-187` was true of the 0.66 V spread against a ~0.55 V window. Against
a 0.480 V spread and the real 5.00–5.50 V window it is now *marginally* false: a
search over E96 pairs at 0.1 % finds three that fit entirely
(`R1/R2` = 107/340, 102/324, 115/365) `[calc]`, the best with **5.5 mV** of
worst-case margin. That is not a real design margin, so the bench-selection
decision survives — but the stated reason for it no longer holds as written.

### A4-3 [MAJOR] — node `DAC AVDD`: bench selection at E7 cannot hold a floor that must hold over temperature, line and life

`ROADMAP.md:48` and `config/figures.yaml:236` both discharge the floor onto a
single bench step: *"Select `R-REG-SET` here — and never below AVDD = 5.00 V"*
`[repo]`. E7 is one measurement, at one temperature, at one line and load point.

Selecting `R2` removes the *part-to-part* `V_ref` offset of that one unit. It
does not remove that unit's own subsequent drift, which the datasheet specifies
separately `[datasheet] SLCS144E p.5`:

| Term | Spec | At `V_O` = 5.21 V |
|---|---|---|
| Output voltage change with temperature, `T_J` 0–125 °C | 10 mV/V | 52 mV |
| Output voltage regulation, `V_I` 5–35 V and `I_O` 2.5–100 mA, `V_O` ≥ 5 V | 10 mV/V | 52 mV |
| Long-term drift, 1000 h | 3 typ / **10 max** mV/V | 52 mV |

`[calc]` Worst-case one-sided post-selection drift **156 mV**; RSS ≈ 90 mV.

**So a unit selected to read exactly 5.00 V on the bench at 25 °C is specified
to reach 4.84 V in the rack.** The floor needs a guard band — select for
**≥ ~5.15 V**, not ≥ 5.00 V — and nothing in the corpus says so. Headroom at the
top is fine: 5.21 + 0.156 = 5.37 V, under the 5.5 V ceiling `[calc]`.

These three terms are *not* additive to the 0.480 V paper spread of A4-2 — the
1.2–1.3 V reference window already contains them. They are the right numbers for
the post-selection case and the wrong ones to stack on the pre-selection case.

### A4-4 [MEDIUM] — node `DAC AVDD`: the "C grade is specified only for 5.0–5.5 V / out of spec" framing overstates the datasheet

Three places state it in strong terms: *"The DAC8568's C grade is specified only
for AVDD 5.0-5.5 V"* `[repo] config/figures.yaml:236`; *"a selection that lands
below 5.00V puts the DAC out of spec"* `[repo] hardware/bom.csv:94,
hardware/unplaced.csv:6`; and `ROADMAP.md:48` `[repo]`.

What the banked document says `[datasheet] SBAS430E p.3,
datasheets/analog/DAC8568CIPW.pdf`:

- Header of ELECTRICAL CHARACTERISTICS: *"At AVDD = 2.7 V to 5.5 V and over
  −40 °C to +125 °C"* — **no grade split.**
- POWER REQUIREMENTS: *"AVDD  2.7  5.5  V"* — **no grade split** `[p.5]`.
- The `AVDD ≥ 5 V` condition attaches to **one row**, Output voltage range:
  *"AVDD ≥ 5 V; grades C and D: maximum output voltage 5 V when using internal
  reference."*

**The 5.00 V number is right; "out of spec" is not.** Below AVDD = 5.0 V the
part is not uncharacterised — it simply cannot guarantee the top of its 5 V
output range, i.e. **top-code compression**. Which is exactly what ADR 0005
already argues (*"What AVDD does decide is whether the output buffer can reach
5.000 V"* `[repo] docs/decisions/0005-power-architecture.md:136`) and exactly
what ADR 0004's E7 step measures (*"raise the top codes and find where they
start compressing"* `[repo]:199-200`).

Net: **ADR 0004's E7 instruction is less wrong than the register makes it look**
— but ADR 0004 never mentions the 5.00 V floor at all (`grep` for `5.00`,
`floor`, `C grade`, `SBAS430` returns only the dismissal of a *"4.95 V floor"*
at `:201` `[repo]`). The floor landed in `figures.yaml` and `ROADMAP.md` and not
in the ADR that ADR 0005 points the reader to for this very decision
(*"see ADR 0004"*, `[repo] 0005:127`). Named failure mode.

### A4-20 [MINOR] — `dac-rail`: the nominal omits `I_ADJ`, the same omission the row criticises

`derivation: "1.25 x (1 + 475/150) = 5.208 V"` `[repo] config/figures.yaml:235`.
With `I_ADJ` at its 50 µA typical the nominal is `5.2083 + 50 µA x 475 =
5.2321 V` `[calc]`, which rounds to 5.23, not 5.21. The `R-REG-SET` row faults
the old divider for exactly this — *"whose stated '+-4% = 5.04-5.46V' ignored
both the divider tolerance and I_ADJ"* `[repo] hardware/bom.csv:111`. Harmless
numerically; worth noting because it is the same slip one revision later.

---

## 2. Sequencing

### A4-5 [CRITICAL] — nodes `SCLK` / `DIN` / `SYNC` at `U-DAC`: nothing sequences bus +5 V against AVDD, and on power-down the buffer drives the DAC's inputs past its absolute maximum

**The absolute maximum** `[datasheet] SBAS430E p.2`, verbatim:

> `Digital input voltage to GND   –0.3 to +AV_DD + 0.3   V`

**The two rails are independent and share no sequencing element.** The
74AHCT125 runs from bus +5 V through `FB4`/`C4` only — *"the one rail with no
diode"* `[repo] power-entry.md:27` — and *"Supplies the 74AHCT125 and nothing
else"* `[repo] digital-and-supervision.md:28`. AVDD comes from the LM317 off the
+12 V analog branch `[repo] power-entry.md:42`. `OE ×4` is **tied to GND,
permanently enabled** `[repo] digital-and-supervision.md:29,53`, so the buffer
outputs are never Hi-Z.

**Power-up is accidentally safe.** The cable-side `CS` pull goes to the
*instrument's* 3V3 `[repo] hardware/bom.csv:44`, which is dead until the load
switch ramps and the ESP32 boots — so all three buffer inputs are low at rack
power-on and all three outputs drive low. No violation, but nothing designed it
that way and no document claims it.

**Power-down is not.** `[calc]`, from the drawn values:

| Node | C | Load | Decay |
|---|---|---|---|
| +12 V analog (`C1`) | 47 µF | ~33 mA (6 × OPA2197, INA828, LM317 branch) | 702 V/s — reaches the LM317's 2.5 V dropout limit (`V_I−V_O` min, `[datasheet]` SLCS144E p.4) at `V_in` ≈ 7.7 V in **5.3 ms** |
| `DAC AVDD` | 1 µF | ~13 mA (`[repo] hardware/bom.csv:110`) | 13 V/ms — **collapses in well under 1 ms** after dropout |
| bus +5 V (`C4`) | 47 µF | 74AHCT125 quiescent, tens of µA | **~2 V/s — holds for seconds** |

**So AVDD is dead at t ≈ 6 ms while the buffer is still powered and still
driving, for ~3 orders of magnitude longer.** The instrument keeps its own 3V3
alive on its ~2.2 mF of far-end bulk, so `CS` stays high and the buffer holds
`SYNC` at ~5 V into a pin whose absolute maximum is then `0 + 0.3 V`.

**There is no series resistance in that path.** `R-SPI-SER` (100 Ω ×3) sits at
the *driving* end, at the instrument: *"Series termination on SCLK, MOSI and CS
at the driving end"*, `HDR-DEV IO34/35/36 → 74AHCT125` `[repo]
hardware/interfaces/spi-link/bom.csv:3, spi-link.md:35-37`. Between the
74AHCT125 output and the DAC pin there is nothing. Current into the DAC's ESD
structure is bounded only by the buffer's ±8 mA drive and its output impedance
`[repo] hardware/bom.csv:108`, and `C4` holds 235 µC at 5 V to deliver `[calc]`.

**The corpus already applies the correct mitigation one stage downstream and
misses it here.** ADR 0006 `[repo]:791-795`:

> *"**1 kΩ in series with each op-amp's non-inverting input where the DAC drives
> it.** The DAC runs from its own 5.21 V regulator and the op-amps from ±12 V,
> so the two supplies do not come up or collapse together. A driven DAC output
> into an op-amp whose rails are absent forces current through the input clamp
> structure; 1 kΩ bounds it."*

That is the only sequencing statement in the corpus (`grep` for `sequenc`,
`power.down`, `collaps` across `hardware/**`, `docs/decisions/**`,
`docs/reference/**`, `README.md`, `ROADMAP.md`). It names two rails. **There is
a third** — bus +5 V — which comes up and collapses with neither, sits on the
one branch with no reverse protection, and feeds the part that drives the DAC's
inputs. `R-OPAMP-IN` protects the DAC→op-amp direction; nothing protects the
buffer→DAC direction, where the drive is harder and the rail divergence larger.

**Not recorded as a risk anywhere.** It is absent, not accepted.

*(This also strengthens the already-open case for dropping the bus +5 V rail —
`[repo] digital-and-supervision.md:88-96`, where three reviewers want it gone.
Deriving the buffer's rail from the same protected +12 V that feeds the LM317
would make the two rails collapse together and dissolve this finding. The page
lists three reasons; this is a fourth and it is the only one that is an
absolute-maximum violation.)*

### A4-6 [MAJOR] — node `SYNC`: the DAC-side pulls were bought for a condition that no longer exists, and `SYNC` is actively held low in the declared normal resting state

The `R-SPI-PULL` row justifies three of its six resistors like this `[repo]
hardware/bom.csv:44, hardware/interfaces/spi-link/bom.csv:2`:

> *"DAC side: same, **because with OE disabled the buffer outputs are Hi-Z** and
> it is then the DAC's SCLK/DIN/SYNC that float — which is the state these were
> bought for."*

**`OE` is no longer ever disabled.** The presence-gated `OE` was deleted and
`OE` is tied to ground `[repo] docs/decisions/0004-cv-interface-module.md:398,
442-444; digital-and-supervision.md:29`. The `U-LVL-MOD` row on the *same BOM
file* says so in capitals — *"OE IS TIED ENABLED"* `[repo]
hardware/bom.csv:108`. Two rows in one generated file, one relying on a state
the other records as deleted. CLAUDE.md §5's class exactly; no grep finds it.

**Consequence at the node.** In the state ADR 0004 calls *"a designed-in
operating mode, not a fault case, and … the state the instrument spends most of
its life in"* `[repo]:380-383` — module alive, instrument off — the cable-side
`CS` pull-up goes to the instrument's **dead** 3V3 rail, so the buffer input is
low and the buffer **actively drives `SYNC` low**. The DAC-side 10 kΩ pull-up to
AVDD cannot win against a driven AHCT output `[calc]`.

So `SYNC` (active low) is asserted continuously whenever the instrument is off.
Functionally this is probably benign — with `SCLK` static no word is clocked, and
the frame aborts when `SYNC` rises. But:

- the row's stated purpose (*"a stray CS edge latches garbage into the pitch
  DAC"*) is not served: `CS` idle-high is **not achieved**, and the first thing
  that happens at instrument boot is a `SYNC` rising edge;
- the row's own objection to pulling `CS` to +5 V — *"the node sits at ~0.7V so
  'CS idle high' is not even achieved"* `[repo] hardware/bom.csv:44` — applies
  with equal force to the 3V3 pull it was changed to, since 3V3 is also dead in
  that state. Moving the pull did not fix the thing the row says it fixed.

---

## 3. The load switch

Everything in this section was re-derived from the drawn values and
`[datasheet] 164112fc, datasheets/discrete-and-power/LT1641.pdf`. **The
datasheet readings on the page are correct.** I confirmed against p.2 (DC
ELECTRICAL CHARACTERISTICS): `V_LKO` 7.5/8.3/8.8 V; `V_FBH` 1.280/1.313/1.345 V;
`V_FBL` 1.221/1.233/1.245 V; `V_SENSETRIP` 8/12/17 mV at `V_FB` = 0 V and
39/47/55 mV at `V_FB` = 1 V; `I_GATEUP` −5/−10/−20 µA; `I_TIMERUP`
−24/−80/−132 µA; `I_TIMERON` 1.5/3/5 µA; pinout `1 ON 2 FB 3 PWRGD 4 GND 5 TIMER
6 GATE 7 SENSE 8 VCC`. All nine match the page's table `[repo]
umbilical-load-switch.md:125-139`.

**The present version starts.** §5's diagnosis — `FB` unconnected holds the
limit at 12 mV/50 mΩ = 240 mA forever and the `-1` latches — is correct, and the
fitted divider fixes it. I reproduced every number in the sizing sections
exactly `[calc]`: `k` = 5.11/40.81 = 0.125214; foldback knee at `V_OUT` =
0.5/`k` = **3.993 V**; `PWRGD` release at 1.313/`k` = **10.486 V**; `V_FB` at
12 V = **1.503 V**; divider current **294 µA**; foldback slope **8.765 mV per
volt of output**, i.e. **0.1753 A/V**; the 240/415/591/766/940 mA ramp table;
`C-GATE` 82 nF → 61/122/244 V/s → 197/98/49 ms → 134/268/537 mA; `C-TIMER`
10 µF → 587/160/95.6 ms. No arithmetic defect found in any of it.

The defects are in **which corners are combined**.

### A4-9 [MAJOR] — node `TIMER`: the 2.01× hot-plug margin compares a typical-silicon start against a worst-case-silicon timer. The guaranteed margin is 1.48×

The page's claim `[repo] umbilical-load-switch.md:226,247`:

> *"**The `TIMER` must exceed 47.5 ms on worst-case silicon.**"* … *"**95.6 ms
> against a 47.5 ms hot-plug start is 2.01×.** That is the margin that matters."*

The 47.5 ms is built on the **typical** sense threshold — 12 mV foldback floor
(240 mA) and 47 mV full limit (940 mA) `[repo]:216-223`. The 95.6 ms is the
**worst-case** timer (−132 µA pull-up). Two different corners of the same die.

The page itself documents the threshold spread — *"the limit is really
0.78–1.10 A"* `[repo]:35` — and the `R-ILIM` BOM row states the binding half
explicitly: *"The foldback floor at VFB=0 is 8/12/17mV, i.e. 160/240/340 mA —
**the low corner is what a hot-plug has to climb out of**, and the worked start
in power-entry.md uses the 12mV typ"* `[repo] hardware/bom.csv:57`. **The BOM
row noticed. The margin claim never followed.**

Redone at the **minimum** sense threshold (8 mV floor = 160 mA, 39 mV full limit
= 780 mA, slope 0.1553 A/V), keeping every other assumption of the page
including its conservative "loaded throughout phase 2" convention `[calc]`:

```
phase 1  0 -> 3.99 V   t = (C/m).ln(I2/I1) = (2.2mF/0.1553).ln(780/160) = 22.4 ms
phase 2  3.99 -> 12 V at 780 mA less 360 mA load = 2.2mF x 8.01 / 420 mA = 41.9 ms
                                                             total  = 64.4 ms
```

(The page's own less-conservative variant — no load below the buck's 8 V
minimum — gives 54.7 ms `[calc]`.)

**95.6 / 64.4 = 1.48×, not 2.01×.** The same model reproduces the page's 47.5 ms
and 2.01× exactly when fed the typical thresholds, which is what validates it.

Still greater than one, so the conclusion "it does not latch on hot-plug"
survives. But the margin is **35 % smaller than stated**, and the 10 µF-over-
9.4 µF decision is argued on precisely this ratio (*"the reason for 10 µF rather
than 9.4 µF, which gives 1.89×"* `[repo]:248-249`). On guaranteed silicon those
two become 1.48× and 1.39×.

### A4-10 [MAJOR] — nodes `SENSE` / `GATE`: "never approaches the 940 mA limit thereafter" is false at the fast-gate corner, and the cold start takes 39.6 % of the fault timer, not 10.5 %

The page `[repo] umbilical-load-switch.md:269-279`:

> *"That is 10.5 % of the fault timer, and it is **the largest bite the cold
> start takes out of it** … **It never approaches the 940 mA limit thereafter**:
> the instrument's own load cannot appear below 8 V … and by then `V_FB` is
> 1.00 V and the limit has been flat at 940 mA for 4 V of output."*

The analysis stops at the foldback escape and never revisits the moment the
instrument's buck starts. At the **fast gate corner** (`I_GATE` = −20 µA, the
datasheet maximum, 244 V/s) the demand at `V_OUT` ≥ 8 V is `[calc]`:

```
charging  2.2 mF x 244 V/s = 537 mA
plus the instrument load     360 mA
                           = 897 mA
```

**897 mA is 95 % of the 940 mA typical limit — and it is above the 780 mA the
datasheet guarantees at the minimum sense threshold.** So on guaranteed silicon
the start **re-enters current limit at 8 V** and stays there to 12 V. "Never
approaches" is false even at typical, where the margin is 4.6 %.

Worse, the `TIMER` does not reset in between. `I_TIMERON` is the 1.5/3/5 µA
pull-down `[datasheet] p.2`; at 10 µF the worst-case discharge is 0.15 V/s
`[calc]`. Accumulating across the whole cold start at the fast-gate /
min-threshold corner, with the worst-case −132 µA timer:

```
A  in limit 0 -> 2.43 V           17.1 ms    TIMER +221 mV
   coast 2.43 -> 8 V              22.9 ms    TIMER   -3.4 mV   (cannot reset it)
B  buck starts, in limit 8 -> 12 V 21.0 ms   TIMER +270 mV
                                             TOTAL  488 mV of 1233 mV = 39.6 %
```
`[calc]`

**39.6 % of the fault timer, not the 10.5 % the page calls the largest bite.**
No latch — but the stated headroom is off by a factor of four, and the reason is
a corner combination (fast gate ramp × minimum sense threshold) that the page
evaluates separately and never crosses.

*(The `C-GATE-LOADSW` BOM row repeats the same conclusion — *"537mA of charging
at the fast corner … never approaches 940mA"* `[repo] hardware/bom.csv:135` — so
cross-checking the page against the BOM finds false agreement. Same shape the
`loadswitch-timer` note already records for the "12x to 300x" ratio.)*

### A4-19 [MINOR] — `C-GATE-LOADSW`: the BOM row and the page disagree on where the fast corner escapes foldback

BOM: *"537mA of charging at the fast corner still clears the 240mA foldback floor
at **0.14V** of output"* `[repo] hardware/bom.csv:135, unplaced.csv:47`.
Page: **1.69 V** `[repo] umbilical-load-switch.md:270-271`.

The page is right `[calc]`: `537 mA x 50 mΩ = 26.85 mV`; `12 + 8.765·V = 26.85`
→ `V = 1.694 V`. The row's 0.14 V also mis-states the mechanism — at 537 mA the
part *enters* current limit rather than "clearing" the floor, which is what the
page spends a paragraph correcting.

### A4-11 [MEDIUM] — node `GATE` → FET: there is no gate-drive criterion for the FET, and the part guarantees only 4.5 V

The FET is specified as *"DPAK or SO-8, chosen against the single-pulse SOA
curve — not against R_DS(on)"* with the Spirito/linear-mode caveat `[repo]
umbilical-load-switch.md:314-325`. `grep` for `logic.level`, `V_GS`, `VGS`,
`gate drive`, `enhanc` across `hardware/**` and `docs/decisions/**` returns
nothing on this point.

The datasheet does bound it `[datasheet] 164112fc p.2`:

> `ΔV_GATE  External N-Channel Gate Drive  V_GATE − V_CC, V_CC = 10.8V to 20V   4.5 min / 18 typ  V`

At Eurorack +12 V −5 % the source sits at ~11.36 V (the page's own figure
`[repo]:162`) and the gate reaches `11.4 + 4.5 = 15.9 V`, giving **`V_GS` = 4.5 V
minimum** `[calc]`. **The FET must therefore be a logic-level part fully
enhanced at 4.5 V.** A standard-threshold DPAK specified at `V_GS` = 10 V is
barely on there, and the FB-divider sizing explicitly assumes the FET's
`R_DS(on)` is *"also ~50 mΩ"* `[repo]:161` — which is only true of a logic-level
part at that drive. This is a selection criterion, not a caveat, and it is
absent.

### A4-12 [MEDIUM] — node `FB`: the divider is sized at the `PWRGD` end, and `PWRGD` is connected to nothing

> *"The divider is chosen at the `PWRGD` end, **because that is the end with a
> hard requirement**."* `[repo] umbilical-load-switch.md:156-157`, repeated in
> `config/figures.yaml:359` and `hardware/bom.csv:58`.

`grep PWRGD` across `hardware/**`, `docs/decisions/**`, `config/**` and
`firmware/**` returns only the load switch's own documents and the figure
`[repo]`. There is no consumer circuit, no pull-up resistor in any BOM fragment,
and the drawing on `power-entry.md:52-58` does not show the pin at all `[repo]`.
`PWRGD` is an open-drain output `[datasheet] p.2, V_OL / I_OH rows` — unconnected
and un-pulled-up, it is a floating pin.

**So the stated hard requirement is vacuous**, while the end that genuinely
binds — the foldback knee at `V_OUT` = 3.99 V, which sets phase 1 of the
hot-plug and therefore the entire `TIMER` margin of A4-9 — is treated as a
consequence of it. The reasoning is inverted relative to what the circuit
actually depends on.

Related: the panel-LED rework proposes taking "lit = running" from `TIMER` or
`GATE` `[repo] hardware/module/panel-led/panel-led.md:42-44`. `PWRGD` is the pin
ADI provides for exactly that, it is already sized, and it is free.

---

## 4. The three-diode split

### A4-1 [MAJOR] — node `+12V` → `U-LOADSW` `VCC` / `R-ILIM`: the interface tables say the branch is taken *before* the diodes; the drawing, the BOM and the bead figure all say it is taken *after* `D2`

Both pages state it, in nearly identical words:

- *"The branch is taken **before** the diodes; `U-LOADSW`'s `VCC` and the top of
  `R-ILIM` hang off it"* `[repo] power-entry.md:28`
- *"Taken before the entry diodes, **which is the point of the split**"*
  `[repo] umbilical-load-switch.md:15`

**Three independent sources say otherwise.**

1. **The drawing** `[repo] power-entry.md:46-51`: `+12V` branches at `┬`; the
   lower leg runs `──[D2 1N5817]──[FB2]──[C2 47µF]──┬` and that `┬` descends
   into the block containing `R-ILIM` and the LT1641.
2. **The `FB-IN` BOM row**: *"One per branch: +12V analog, **+12V umbilical**,
   -12V, +5V"* `[repo] hardware/unplaced.csv:25` — the umbilical is a bead
   branch, and a bead branch here is a *diode* branch.
3. **`ferrite-bias-impedance`**: *"**FB2 carries umbilical-current (359 mA)**"*
   `[repo] config/figures.yaml`. If the branch were taken ahead of the diodes it
   would carry no umbilical current.

**And the section title requires it.** "Three diodes, not two" counts to three
only as D1 (analog) + D2 (umbilical) + D3 (−12 V), and `D-REVPOL` is qty **3**
`[repo] hardware/bom.csv`. If the branch were ahead of the diodes, `D2` would
drive nothing and there would be two.

**Consequence if the tables are followed at layout:** the module's highest-current
branch — 359 mA to the instrument — loses its reverse-polarity protection, and
`D2`/`FB2` become dead copper. The tables were written during the 2026-09-21
split and the same wrong sentence was copied into the second page, so a reader
who checks one against the other finds agreement.

**Contributing:** the ASCII drawing is genuinely ambiguous at that junction — the
label `PWR_GND (star)` sits at the end of the `D2`/`FB2`/`C2` line, on what is
actually the +12 V umbilical feed, with only the descending `│` to say otherwise
`[repo] power-entry.md:46-48`. That is very likely how the tables came to say
what they say.

### A4-13 [MEDIUM] — `diode-split-rationale`: `r_d 69 mΩ at 392 mA` is the ideal-diode formula, and the same figure entry's own digitised curve refutes it

The tracked value is *"fault isolation and HF isolation (**r_d 69 mohm at
392 mA**)"* `[repo] config/figures.yaml`, repeated at `power-entry.md:113`.

The *same entry* carries the digitised curve: *"0.24 V at 245 mA -> 0.36 V at
612 mA"*, calibrated against the datasheet's guaranteed 0.454 V at 1.0 A and
0.746 V at 3.0 A `[repo] config/figures.yaml, derivation + provenance_note;
datasheets/discrete-and-power/1N5817.pdf`.

Fitting `V = n·V_T·ln(I) + I·R_s` to those four points `[calc]`:

```
chord 245 mA .. 612 mA   327 mohm
chord 1.0 A .. 3.0 A     146 mohm
  ->  n.V_T = 90.3 mV,  R_s = 93.9 mohm
  ->  incremental r_d at 392 mA = 90.3 mV / 0.392 A + 93.9 mohm = 324 mohm
```

**~324 mΩ, not 69 mΩ — a factor of 4.7.** Even the pure series term, 94 mΩ, is
above 69 mΩ. The 69 mΩ is reproduced exactly by the textbook ideal-diode
expression `r_d = V_T / I` at `V_T` ≈ 27 mV: `0.027 / 0.392 = 68.9 mΩ` `[calc]`
— `n` = 1, series resistance ignored. For a Schottky at 392 mA that is the wrong
model, and the entry's own data says so.

**The conclusion survives and strengthens.** A higher `r_d` makes the HF
isolation argument *better*, not worse. But the figure's `value` field is the
thing other documents cite by name, and it is wrong by ~5×.

**Second layer:** 392 mA is the *module total* on +12 V — the register says so
itself (*"392 mA is the MODULE total on +12 V (instrument + module)"*, `[repo]
config/figures.yaml`, `umbilical-current.false_positive_note`). That is the
**pre-split** current, through a single shared diode. After the split D1 carries
only the module's analog load (~33 mA) and D2 carries the 359 mA. So a figure
about *what the split buys* evaluates `r_d` at the one current that flows in
neither diode once the split exists `[calc]`.

*(The rest of the chain checks out: 120 mV → 0.52 mV/V LM317 line regulation →
62 µV → 110.5 dB PSRR → 0.00044 cents. Note the 0.52 mV/V is `0.01 %/V` × 5.21 V,
the **typ at 25 °C**; the max is 0.02 %/V at 25 °C and 0.05 %/V over temperature
and load `[datasheet] SLCS144E p.5`, i.e. up to 5× — which, at five orders of
magnitude below every other term, changes nothing, exactly as the page says.)*

---

## 5. What the jacks do during power-up and power-down

### A4-7 [MAJOR] — node `PITCH` jack: at rack power-on the jack sits at 0 V — an ordinary audible note — not "below −2 V, subsonic"

ADR 0006's power-on table `[repo] docs/decisions/0006-cv-channel-allocation.md:197-201`:

| Output | At rack power-on, before firmware writes | Why that is right |
|---|---|---|
| **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |

That row requires `V_out = 2·V_dac − 2.500` with `V_dac` = 0. **It requires the
2.500 V to exist.** It does not.

- `V_ref` is derived **entirely** from the DAC's own `VREFOUT`:
  `VREFOUT ──[TRIM-OFFSET 10k]── ½ OPA2197 ── V_ref ≈ 2.500 V` `[repo]
  hardware/module/pitch-stage/pitch-stage.md:28`. There is no independent
  reference in the pitch stage.
- **The DAC8568's internal reference is disabled by default.** ADR 0006 states
  it twenty lines below the table: *"the internal reference is disabled by
  default and needs an explicit enable write at boot … It also means the outputs
  sit at 0 V from rack power-on until firmware enables the reference, **which
  happens to reinforce the table above**"* `[repo]:219-224`. Also in the `U-DAC`
  row: *"BOTH default to reference OFF after any power cycle"* `[repo]
  hardware/bom.csv:94`.

**It does not reinforce the table — it refutes the pitch row.** `pitch-stage.md`
gives the transfer function with `VREFOUT` drifting by a fraction δ `[repo]:99`:

```
Vout = 2.Vdac(1+delta) - 2.500(1+delta) = (1+delta).(2.Vdac - 2.500)
```

Reference off is δ = −1, so `V_out = 0` **exactly** `[calc]`. Both terms die
together — which is the whole point of the page's tracking argument, applied at
its endpoint.

**So the pitch jack sits at 0 V.** On a 1 V/oct VCO 0 V is not subsonic; it is
the reference pitch, mid-range and plainly audible. **This is the one thing the
row exists to promise cannot happen.**

**Duration:** from rack power-on until firmware enables the reference and writes
channel 1. That waits on the load switch ramp (49–197 ms `[repo]
config/figures.yaml`, `loadswitch-gate-cap`), the buck start, ESP32-S3 boot and
the SPI link — order of a second `[calc, from the cited ramp plus boot]`.

**The `Mod 1–4` row is correct** and correct for the reason given: with the
reference off, both the mod channel and the ch-7 shared offset are zero, so the
difference is zero `[calc]`. The breath row is already flagged as undefined and
accepted `[repo]:203-217`. **Of the three rows, only pitch is wrong — and it is
the only one carrying a safety claim.**

### A4-8 [MAJOR] — nodes `C1`–`C4` and all six jacks: the page draws the bulk value that the BOM row exists to prevent, and it is the power-down case

`power-entry.md` draws `C1`–`C4` all at **47 µF** `[repo]:39,46,72,74` and states
it in prose: *"**Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm of
10–22 µF. Harmless except for case-wide inrush at rack power-on"* `[repo]:171-173`.

The `C-BULK-RAIL` row says the opposite, and says why `[repo]
hardware/bom.csv:122, hardware/unplaced.csv:34`:

> *"**NOT 47uF on every rail.** The +12V branch carries the LM317's divider, the
> DAC and the comparator, about 22mA against -12V's 10mA — so at 47uF each it
> collapses 2.2x faster and **every rack power-down leaves the op-amps with V+
> near 0 and V- at -6 to -8V for ~30ms, pulling all six jacks toward the
> surviving negative rail.** 100uF on +12V balances the decay."*

Part value: `100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic` `[repo]`.

**The page asserts, as a live value with a "harmless" verdict attached, exactly
the configuration the BOM row was changed to eliminate.** The fix landed in the
BOM row and did not land in the schematic page or its drawing — the named
failure mode, on the question this audit item asks about.

Two riders:

- The page's inrush bullet also computes from the wrong total: 4 × 47 µF =
  188 µF, against 241 µF as specified `[calc]`.
- The `C-BULK-RAIL` row's own load accounting still includes *"the comparator"*
  — the LM311 presence comparator, deleted `[repo]
  docs/decisions/0004-cv-interface-module.md:425-437`. CLAUDE.md §5 class; it
  makes the +12 V branch look more heavily loaded than it is, which happens to
  argue in the safe direction.

**Answer to the audit question.** At the values the page draws, **every rack
power-down pulls all six jacks toward −6 to −8 V for ~30 ms**. On pitch that is
subsonic and harmless. On the four mod channels and breath it is a large
negative excursion into whatever they are patched to, at every power-down, and
it is documented only inside a BOM `notes` field. At the values the BOM
specifies the excursion is reduced but the ordering is unchanged — the decay is
*balanced*, not *sequenced*.

---

## 6. Grounding

### A4-16 [VERIFIED — dispute still live] — node `DIG_GND`

**The origin is stated consistently.** `power-entry.md:151` — *"One origin, at
the IDC's ground pin"*; ADR 0004 — *"**The origin is the Eurorack power inlet's
ground pin.**"* `[repo] docs/decisions/0004-cv-interface-module.md:612`. Same
point, and `power-entry.md:23` agrees (*"`GND` is the star point"*). **No defect
on the origin.**

**The `DIG_GND` routing dispute is still live**, and the register's account of it
is accurate. I checked it by hand rather than repeating it:

- `power-entry.md:153-156`: *"**`DIG_GND` is not given its own path to the
  star**, which **an earlier revision of ADR 0004 asked for**"* `[repo]`.
- ADR 0004, **line 637, live text, not struck through and not marked
  superseded**: *"- **`DIG_GND` likewise** — its own path to the star."*
  `[repo]`.
- A third position at `digital-and-supervision.md:60`: *"analog star, single
  tie (ADR 0004)"* `[repo]`, cited again from `dac8568.md:23` and
  `panel-led.md:15`.

**So `power-entry.md`'s "an earlier revision of ADR 0004" is false — ADR 0004 was
never corrected.** `dig-gnd-topology`'s note says exactly this `[repo]
config/figures.yaml`; **confirmed, still true as of this review.** Three live
positions, four consumer pages.

### A4-16b [MINOR] — `dig-gnd-topology`: all three candidate line references are stale

`config/figures.yaml` is design corpus, not history, so CLAUDE.md §6's exemption
for pre-split paths does not cover it `[repo] CLAUDE.md:83-88`.

| Candidate cites | Actual |
|---|---|
| `power-entry.md:495-498` | the file is **173 lines**; the text is at **152-156** `[repo]` |
| `0004-cv-interface-module.md:627` | **637** `[repo]` |
| `digital-and-supervision.md:53` | **60** (53 is the `OE x4 → GND` line) `[repo]` |

The first points past the end of the file — a survival of the 2026-09-21 split,
in the one place a reader goes to adjudicate the dispute.

---

## 7. Register and BOM hygiene inside this slice

### A4-14 [MEDIUM] — every part in the module power-entry drawing is filed as a part nobody has drawn

`hardware/unplaced.csv` is defined as *"the 50 rows of 138 that no schematic page
names … not a dumping ground, it is a count: a part nobody has drawn"*, and the
placement rule is *"A row lives with the circuit **whose page derives its
value**"* `[repo] docs/reference/repo-maintenance.md:144-150`.

`hardware/module/power-entry/bom.csv` holds **one row**, `J-PWR-EURO` `[repo]`.
Filed in `unplaced.csv` instead, although `power-entry.md` draws *and derives*
each one `[repo] hardware/unplaced.csv`:

| Row | Drawn as | Derived in |
|---|---|---|
| `D-REVPOL` ×3 | `D1`, `D2`, `D3` | §"Three diodes, not two" |
| `FB-IN` ×4 | `FB1`–`FB4` | §"Beads, not resistors" |
| `C-BULK-RAIL` ×4 | `C1`–`C4` | §"Still open", entry bulk |
| `U-REG-DAC` | `LM317LZ` | owner of `dac-rail` |
| `R-REG-SET` ×2 | `150R/475R 0.1%` | owner of `dac-rail` |
| `C-REG-ADJ` ×2 | the `1µF` on AVDD | the LM317 network |

Plus, for the load switch: `C-TIMER-LOADSW` and `C-GATE-LOADSW`, both derived at
length in `umbilical-load-switch.md` §"The two capacitors" and both tracked
figures `[repo]`. And `U-DAC` and `U-LVL-MOD`, drawn on `dac8568.md` and
`digital-and-supervision.md` `[repo]`.

**Ten rows, and the count of undrawn parts is inflated by all ten.** The
checker's *"drawn in a schematic, no BOM row"* advisory cannot see it, because
the drawing calls them `D1`/`FB2`/`C4` and the BOM calls them
`D-REVPOL`/`FB-IN`/`C-BULK-RAIL` `[repo] .staleness/report.txt`.

**Root cause is visible in the metadata.** `power-entry/circuit.yaml` declares
`refdes:` edges for `J-PWR-EURO`, `L-BUCK-IN` and six *load-switch* parts, and
**none of its own power parts** `[repo]`. `umbilical-load-switch/circuit.yaml`
declares `fig:loadswitch-timer` but not `fig:loadswitch-gate-cap`,
`fig:loadswitch-fb-divider`, `refdes:C-TIMER-LOADSW` or
`refdes:C-GATE-LOADSW` — all four derived on that page `[repo]`. The file header
warns that `depends_on` *"fails SILENT — an undeclared edge is an unchecked
edge"* `[repo]`; these are those edges.

### A4-15 [MEDIUM] — three load-switch figures name the wrong owner after the split

`loadswitch-timer`, `loadswitch-gate-cap` and `loadswitch-fb-divider` all declare
`owner: hardware/module/power-entry/power-entry.md` `[repo]
config/figures.yaml`. **All three derivations moved to
`umbilical-load-switch.md` on 2026-09-21** `[repo]
umbilical-load-switch.md:3-5`; `power-entry.md` retains only the values inside
the ASCII drawing.

The checker already reports the consequence: *"[loadswitch-timer] value '10 uF'
has no token distinctive enough to locate — owner
hardware/module/power-entry/power-entry.md is **UNCHECKED**"* `[repo]
.staleness/report.txt`. CLAUDE.md rule 1 puts the single statement in the owner
document; for these three the owner is the page that no longer makes it.

### A4-17 [MEDIUM] — `docs/decisions/0005-power-architecture.md:74` carries the refuted sensor transfer function in an eighth spelling, and the checker passes

> *"The MPXV4006DP is a 5 V part outputting **0.2–4.7 V** (ADR 0003)."*
> `[repo] docs/decisions/0005-power-architecture.md:74`

Stated as live supporting fact, attributed to an ADR that no longer says it. The
`sensor-full-scale` register refutes it — the transfer function gives 4.86 V and
the 0.2 V pedestal is the datasheet's **cover-page** line, contradicted inside
the same document `[repo] config/figures.yaml:34-40`.

**It escapes on one character.** The dash is U+2013 with **no** surrounding
spaces `[repo, hexdump: `0.2M-bM-^@M-^S4.7 V`]`. The forbidden list has
`0.2-4.7 V` (ASCII hyphen) and `0.2 – 4.7 V` (spaced en dash) and
`0.2–4.80 V` (unspaced en dash, but 4.80) — **not** unspaced en dash with 4.7
`[calc, tested each pattern by substring match: all False]`.
`tools/check-staleness.py` reports `PASS no live stale values` `[repo]
.staleness-report.txt`.

This is the **eighth** spelling, and the register's own `escape_note` names
*"an en dash with no spaces"* as one of the seven already found `[repo]
config/figures.yaml:56-70`.

*(Also: `sensor-full-scale.false_positive_note` says 4.80 V appears legitimately
in ADR 0005 *"about an LM317 rail"* `[repo]:55`. It does not — ADR 0005's only
4.80 V is at line 102, about the superseded 5 V-umbilical option `[repo]`. The
exemption is right to exist and describes the wrong line.)*

### A4-18 [MEDIUM] — the refuted "≥1 A bead" rule is stated as live fact in two corpus documents

`ferrite-bias-impedance` refutes it in capitals: *"**THE '>=1 A' RULE DOES NOT DO
WHAT THE BOM ROW SAID IT DID.** A bead's current rating is THERMAL, not magnetic,
so it says nothing about saturation"* — with a 3000 mA part in the same package
measuring *worse* at 500 mA than the 1500 mA part `[repo] config/figures.yaml`.
The forbidden entry is the `FB-IN` row's exact sentence `[repo]`.

Two documents still assert the rule, in different words, so the literal pattern
misses both:

- `power-entry.md:143-147`: *"A ≥1 A bead is specified because the common 0805
  600 Ω part is ~300 mA and **a saturated bead is a wire**."* The paragraph then
  adds that the *series* sets the rating — a real point, but not the refutation,
  and the ≥1 A rule is left standing as the reason `[repo]`.
- `docs/decisions/0006-cv-channel-allocation.md:803-805`: *"**Ferrite beads rated
  ≥1 A, in 1206 or 1210.** The common 0805 600 Ω part is rated around 300 mA and
  both +12 V branches now exceed that. A saturated bead does not degrade
  gracefully — it loses its impedance entirely and becomes a wire."* No
  refutation wording anywhere near it `[repo]`.

Both are in the energy path this slice follows, and the figure's real finding —
that **FB2 gets ~280–310 Ω of the 600 Ω its row specifies, and no 1206 600R bead
of any rating fixes it** `[repo] config/figures.yaml` — is invisible from either
page.

---

## What I checked and found sound

Recorded so the next reviewer does not re-derive it, per CLAUDE.md's rule on
verifying before repeating.

- **Every LT1641 datasheet reading on `umbilical-load-switch.md:125-139`** —
  nine parameters, all confirmed verbatim against `[datasheet] 164112fc p.2`.
  Including the one the page marks REFUTED (`V_LKO` max is 8.8 V, not 9.8 V).
- **The `FB`-unconnected diagnosis of §5.** Correct, and ADI's Figure 9 caption
  is quoted accurately `[datasheet] p.9`.
- **Every arithmetic result in the sizing sections** — FB divider ratios and
  thresholds, the foldback slope, the 240/415/591/766/940 mA table, both
  capacitor tables, the 47.5 ms typical hot-plug, the 0.158 J ramp energy. All
  reproduce exactly `[calc]`. The defects are in corner *selection* (A4-9,
  A4-10), not in the sums.
- **`2.2 mF`** as the far-end bulk: unstated as a derivation anywhere, but it is
  `2 × C-BUCK-IN (100 µF) + 2 × C-STRIP-BULK (max 1000 µF)` = 2200 µF `[calc,
  from hardware/bom.csv]` — the **top** of the range (the floor is 1.14 mF), so
  it is the conservative choice for start time. Sound; worth stating once.
- **LM317L minimum load.** Divider current alone is `1.25 V / 150 Ω = 8.33 mA`
  `[calc]`, clearing TI's 2.5 mA max and ST/ON's ~3.5 mA even with the DAC
  absent — so the `U-REG-DAC` row's warning about manufacturer variance is
  correctly scoped to *future* divider trimming `[repo] hardware/bom.csv:110`.
- **LM317 dropout.** `V_I − V_O` ≈ 11.2 − 5.21 = 6.0 V against a 2.5 V minimum
  `[datasheet] SLCS144E p.4` `[calc]`. Ample.
- **LT1641 `V_CC` operating range** is 9–80 V `[datasheet] p.2`, above Eurorack
  +12 V −5 % = 11.4 V. Fine.
- **`ADR 0006`'s `Mod 1–4` power-on row** — correct, and correct for the stated
  reason (A4-7).
- **The `diode-split-rationale` conclusion** — 0.00044 cents, five orders below
  every other term. Survives both corrections in A4-13.
- **The grounding origin** — consistent between `power-entry.md` and ADR 0004
  (A4-16).

## Open, and outside this slice

- The `ON` pin divider is undesigned `[repo] umbilical-load-switch.md:327-343`.
  The page's guidance is sound as far as it goes, but note the LT1641's `V_CC`
  operating minimum is **9 V**, not the 8.8 V UVLO max the page reasons from
  `[datasheet] p.2` — a small correction to *"the divider only has to place the
  intended UV trip somewhere above 8.8 V"*.
- `C-TIMER-LOADSW` at 10 µF is *"an electrolytic or a large ceramic where leakage
  is a meaningful fraction of the 3 µA pull-down"* `[repo]:283-285`. A4-10 shows
  the pull-down already fails to reset the timer between current-limit episodes
  on geometry alone; leakage makes that worse, and the two interact.
- The three grounding/shield terms in `power-entry.md:116-137` (7.4 / 8–18 /
  ~7 cents, all breath-correlated) are the largest numbers in this slice by two
  orders of magnitude and are explicitly not fixed. Not mine, but nothing has
  moved on them.
