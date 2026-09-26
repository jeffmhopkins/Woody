# N1 — feedback topology: every net that closes a loop

**Slice:** N1, cold. Claim type: for every op-amp, in-amp, regulator and
hot-swap controller in the 22 netlists, establish from the owning page's own
derivations where feedback is taken **from** and delivered **to**, then check
whether `netlist.yaml` says exactly that — and recompute every stated gain,
intercept and threshold from the netlist's own resistors.

**Measured against** `d1f0cb7`. `tools/` treated as frozen; nothing under
`hardware/`, `config/`, `tools/`, `docs/`, `firmware/` was modified by this
slice. `[test] git diff --stat d1f0cb7..HEAD -- hardware config tools ROADMAP.md README.md CLAUDE.md docs/decisions docs/reference firmware` → empty, so the
corpus at the session HEAD (`5c39a4e`) is byte-identical to the named revision.

**Baseline** `[test] python3 tools/check-netlist.py` →
`netlist: 22 circuit(s), 197 components, 254 nets, 55 master net(s) | 0 problem(s) | 0 drawing page(s) still without a netlist | 0 master endpoint(s) awaiting one`.
So everything below is invisible to that checker by construction: it compares
values and endpoints, never arithmetic, and never asks whether a net is the
*right* node.

**Cold discipline:** nothing under `docs/review/` was read, including this
wave's own directory.

---

## Scope actually covered

Every active device in the corpus that closes a loop, and the loop-closing
nets of each:

| Device | Circuit | Loop nets checked | Verdict |
|---|---|---|---|
| `U-REFBUF` (OPA2197) | `carrier/breath-excitation-reference` | `REF_MINUS`, `BUF_OUT`, `VS`, `AC_FB_MID` | **correct** |
| `U-BREATHBUF` (OPA2197) | `carrier/breath-excitation-reference` | `SENSOR_BUFFERED_OUT` | **correct** |
| `U-DIFFRX` (INA828) | `module/breath-receive-stage` | `GAIN_SET`, `GAIN_SET_B`, `REF_DRIVE` | **correct** |
| `U-REF-BUF` (OPA2197) | `module/breath-receive-stage` | `REF_DRIVE` | correct; see N1-7 |
| `U-BREATH-BUF` (OPA2197) | `module/breath-output-stage` | `BUF_OUT` | **correct** |
| `U-BREATH-SUM` (OPA2197) | `module/breath-output-stage` | `SUM_NODE`, `BREATH_OUT` | correct; see N1-2, N1-5 |
| `U-RESP-A` (OPA2197) | `module/breath-response-shaper` | `VIRTUAL_GND`, `V_SHAPED`, `V_IN_HALF` | **correct** |
| `U-MOD-REFBUF` (OPA2197) | `module/mod-channels` | `VREF_MOD` | **correct** |
| `U-MOD-1…4` (OPA2197) | `module/mod-channels` | `MINUS_1…4`, `OUT_1…4` | **correct**, all four identically |
| `U-PITCH-REFBUF` (OPA2197) | `module/pitch-stage` | `VREF_BUFFERED` | **correct** |
| `U-PITCH-AMP` (OPA2197) | `module/pitch-stage` | `MINUS_NODE`, `AMP_OUT`, `GAIN_TRIM_MID`, `JACK_TIP` | **correct**; see N1-3, N1-4 |
| `U-REG-DAC` (LM317LZ) | `module/power-entry` | `REG_ADJ`, `DAC_AVDD` | **WRONG — N1-1** |
| `U-LOADSW` (LT1641-1) | `module/umbilical-load-switch` | `FB`, `UMBILICAL_POS12`, `GATE_DRIVE`, `GATE_COMP_MID` | **correct** |
| `U-BUCK-A/B` (R-78E5.0-1.0) | `carrier/power-entry-instrument` | — | no external loop to check (3-pin module); netlist correctly has none |

`module/panel-led`, `module/dac8568`, `module/digital-and-supervision`,
`carrier/breath-adc`, `carrier/led-strip-drive`,
`carrier/display-and-service-uart`, `carrier/netlist.yaml`, the three
`cluster/` circuits and the three `interfaces/` circuits contain no feedback
network. I checked each for an amplifier, regulator or controller and found
none `[repo, per-netlist scan of every `part:`/`value:` field across all 22
netlist.yaml]`. That is a deliberate statement of a clean area, not a gap.

---

## N1-1 — `module/power-entry`.`REG_ADJ` / `DAC_AVDD`: the LM317's two divider legs are on the wrong pins, and the rail is 1.65 V, not 5.21 V

**Severity: High.**

**Claim.** The netlist puts `R-REG-SET-HI` (475 Ω) between the LM317's `OUT`
and `ADJ` and `R-REG-SET-LO` (150 Ω) between `ADJ` and ground, which sets
`DAC_AVDD` to **1.65 V** — the two legs are swapped relative to the register's
own derivation of the 5.21 V figure, and 1.65 V is below the DAC8568 C grade's
absolute minimum, never mind the tracked hard floor of 5.00 V.

**Evidence.**

`[repo hardware/module/power-entry/netlist.yaml]` the two nets, verbatim:

```
  REG_ADJ:
    - U-REG-DAC.ADJ
    - R-REG-SET-HI.2
    - R-REG-SET-LO.1
    - C-REG-ADJ.1

  DAC_AVDD:
    - U-REG-DAC.OUT
    - R-REG-SET-HI.1
    - C-REG-OUT.1
    - port: DAC_AVDD
```

and `R-REG-SET-LO.2` appears on `AGND_MOD`. Values in the same file:
`R-REG-SET-HI: "475R 0.1%"`, `R-REG-SET-LO: "150R 0.1%"`. So the netlist says
**475 Ω spans OUT↔ADJ and 150 Ω spans ADJ↔GND**.

`[datasheet datasheets/discrete-and-power/LM317LZ.pdf, SLCS144E §9.2.2.3 "Feedback Resistors", Equation 2]` — extracted from the banked PDF's content
streams: *"The feedback resistor set the output voltage using Equation 2.
`V REF × (1 + R 2 / R 1) + I ADJ × R 2`"*. The same document's §7.5 table gives
*"Reference voltage (output to ADJUSTMENT) … 1.2 / 1.25 / 1.3 V"*, and §8.4
says *"clamping ADJUSTMENT to ground, programming the output to 1.25 V"* — both
of which fix `R1` as the **OUT-to-ADJ** resistor and `R2` as the **ADJ-to-GND**
resistor. Its block-diagram labelling reads `R1 OUTPUT … ADJ/GND R2`.

`[calc]` with the netlist's assignment (`R1` = 475, `R2` = 150):

```
V_O = 1.25 × (1 + 150/475) + 50 µA × 150
    = 1.25 × 1.315789 + 0.0075
    = 1.6447 + 0.0075 = 1.652 V
```

`[repo config/figures.yaml, id: dac-rail]` `value: "5.21 V"`, `status: settled`,
`derivation: "1.25 x (1 + 475/150) = 5.208 V"`. Put beside the datasheet's
equation, that derivation requires **`R2` = 475 Ω (ADJ→GND)** and **`R1` = 150 Ω
(OUT→ADJ)** — the opposite of the netlist. `[calc]` the intended arrangement:
`1.25 × (1 + 475/150) + 50 µA × 475 = 5.2083 + 0.0238 = 5.232 V`, i.e. the
figure.

**The same figure entry carries the consequence:** `floor: "5.00 V, HARD. The
DAC8568's C grade is specified only for AVDD 5.0-5.5 V"`. `[repo hardware/bom.csv, U-DAC]` *"THE C GRADE REQUIRES AVDD 5.0V TO 5.5V"*.

**A second, independent corroboration that 150 Ω is meant to be the OUT→ADJ
leg.** `[repo hardware/bom.csv, U-REG-DAC]` *"~13mA load including the
divider"*. `[calc]` divider current is `V_REF / R1`: with `R1` = 150 Ω it is
`1.25/150 = 8.33 mA`, which plus the DAC's few mA is ~13 mA; with the netlist's
`R1` = 475 Ω it is `1.25/475 = 2.63 mA`, and no plausible DAC load reaches
13 mA. The minimum-load argument in that row — *"A BLEEDER SIZED FOR TI'S
2.5mA UNDER-LOADS A 3.5mA PART … The ~13mA load clears every reading"* — is
only true of the 150 Ω-on-top arrangement. Under the netlist's arrangement the
divider alone supplies 2.63 mA, which is *below* the 3.5 mA that row names as
the worst-case candidate minimum.

**The BOM agrees with the netlist and therefore also contradicts the figure.**
`[repo hardware/module/power-entry/bom.csv:6-7]` and `[repo hardware/bom.csv:64-65]`:
`R-REG-SET-HI … "LM317 divider, ADJ to OUT"` and `R-REG-SET-LO … "LM317 divider, ADJ to GND"`. So this is one fact wrong in three files
(netlist, fragment, generated master) and right in two (`figures.yaml`, and the
drawing's `DAC AVDD 5.21V` label `[repo hardware/module/power-entry/power-entry.md:49]`).
That is the repository's named failure shape, arriving through the *newest*
file.

**Downstream, because `DAC_AVDD` is not only the DAC's rail.** `[repo hardware/nets.yaml, DAC_AVDD]` lists `module/dac8568`,
`module/breath-output-stage`, `module/breath-receive-stage` and
`module/digital-and-supervision` as receivers.

- `[repo hardware/module/breath-output-stage/netlist.yaml]` `POT-OFFSET.CW` is
  on `DAC_AVDD`. `[calc]` at 1.652 V the offset knob's range collapses from
  the page's `+5.06 V … −4.91 V` to `+5.06 V … +1.90 V`
  (`−40.2k × (1.652/21.0k − 12/95.3k) = +1.90 V`), i.e. **the OFFSET knob can
  no longer reach zero, let alone −5 V**, and every number in that page's
  offset table is void.
- `[repo hardware/module/breath-receive-stage/netlist.yaml]`
  `TRIM-BREATH-ZERO.CW` is on `DAC_AVDD`; its required span is 0 → +1.0 V
  `[repo .../breath-receive-stage.md]`, which 1.65 V still just covers, so this
  one survives — worth saying because it is the one consumer that does.

**What would have to be true for this finding to be wrong.** Either (a) the
LM317's 1.25 V reference appears across the ADJ-to-GND resistor rather than
across the OUT-to-ADJ resistor — refuted verbatim by the banked datasheet's own
parameter name *"Reference voltage (output to ADJUSTMENT)"*; or (b) `.1`/`.2`
on these two resistors are not interchangeable terminals and I have the
orientation backwards — but the finding is about which **net** each resistor
spans, not which terminal, and each resistor spans exactly one pair of nets
here; or (c) `figures.yaml`'s derivation string is itself the defect and the
rail is genuinely meant to be 1.65 V — refuted by the DAC8568 C grade's
5.0–5.5 V window, the figure's `status: settled`, the hard 5.00 V floor, and
the drawing's own `5.21V` label.

**Smallest fix.** In `hardware/module/power-entry/netlist.yaml`, move
`R-REG-SET-LO.1` to the `DAC_AVDD` net and `R-REG-SET-HI.1` to `REG_ADJ` (i.e.
swap which resistor bridges `OUT`→`ADJ`), then correct the two
`LM317 divider, ADJ to …` description fields in
`hardware/module/power-entry/bom.csv` and re-run `tools/merge-bom.py`. While
there, the names invite the error: `HI`/`LO` reads as position but was assigned
by magnitude. `R-REG-SET-TOP` / `R-REG-SET-BOT`, or naming them after the pins
they bridge, costs nothing and closes the class. Note also that
`R-REG-SET-LO`'s row carries *"E7 SELECTS THIS ONE"* while `U-REG-DAC`'s row
says E7 *"selects R2"* — after the fix those point at different parts, so one
of the two has to move.

---

## N1-2 — `module/breath-output-stage`.`RAIL_NEG` / `RAIL_POS`: the output clamp's rail terminals are on nets that exist nowhere, while the rail itself is a port of the same circuit

**Severity: High.**

**Claim.** `D-JACK-CLAMP`'s two rail terminals are netted to `RAIL_POS` and
`RAIL_NEG`, which are single-endpoint nets excused by `external_endpoints` —
yet `MODULE_ANALOG_NEG12` is a **declared port of this very circuit**, already
carrying `R-BREATH-OFFNEG.1`. Transcribed as written, the breath jack's
protection diode has both ends unconnected and the only clamped CV output on
the module is unclamped.

**Evidence.** `[repo hardware/module/breath-output-stage/netlist.yaml]`:

```
  RAIL_POS:                      # clamp to +12 V
    - D-JACK-CLAMP.K
  RAIL_NEG:                      # clamp to -12 V
    - D-JACK-CLAMP.A
...
external_endpoints: [RAIL_POS, RAIL_NEG]
```

and, in the same file, `ports: … MODULE_ANALOG_NEG12: {dir: in, from: module/power-entry}` with
`MODULE_ANALOG_NEG12: [port: …, R-BREATH-OFFNEG.1]`.

The file's justification is false on its face `[repo, same file, comment above external_endpoints]`: *"the clamp rails, which terminate on the module's supply
rather than inside this circuit"* — the module's −12 V supply **is** inside this
circuit, as a port, two dozen lines above.

**The two sibling circuits do it the other way, with the identical part.**
`[repo hardware/module/pitch-stage/netlist.yaml]`
`MODULE_ANALOG_POS12: [port: …, D-JACK-CLAMP.K]` and
`MODULE_ANALOG_NEG12: [port: …, D-JACK-CLAMP.A]`.
`[repo hardware/module/mod-channels/netlist.yaml]` the same, for all four
channels. `[repo hardware/module/breath-receive-stage/netlist.yaml]` the same
for `D-CLAMP-IN+/-`. So four of five circuits that carry a BAV99 net it to the
rail ports and one invents two dangling nets.

**Why the checker is silent.** `[repo tools/check-netlist.py:435-447]`
`rails:` on a component *synthesises an implicit port*, and implicit ports are
exempt from the "port is declared and used by no net" rule. `U-BREATH-BUF` and
`U-BREATH-SUM` both declare `rails: [MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12]`,
which satisfies `nets.yaml`'s forward check — `[repo hardware/nets.yaml, MODULE_ANALOG_POS12]` names `module/breath-output-stage` as a receiver — without
`MODULE_ANALOG_POS12` ever appearing in `ports:` or in any net. The clamp then
rides on the exemption.

`[repo hardware/module/breath-output-stage/breath-output-stage.md, ## Interfaces]`
states the intent plainly: *"`MODULE ANALOG +12V`, `MODULE ANALOG −12V` | in |
… Op-amp supplies, **and `D-JACK-CLAMP` returns to both rails**"*. The page
says the connection exists; the authoritative file does not make it.

**Contrast, as evidence that the distinction is understood elsewhere.**
`[repo hardware/module/breath-response-shaper/netlist.yaml, ports:]` *"The two
rails arrive through U-RESP-A's `rails:` — **there is no clamp or divider on
them here, so there is no net to declare them in**."* That is exactly the right
test, and `breath-output-stage` fails it: it *does* have a part on the rails.

**What would have to be true for this finding to be wrong.** That `RAIL_POS`
and `RAIL_NEG` are intended as *distinct physical nodes* from
`MODULE_ANALOG_POS12`/`NEG12` — a separate, pre-bead or pre-diode clamp return.
Nothing in the page, in `nets.yaml` or in the file's own comments proposes such
a node, and the comment says the opposite ("the module's supply"). Also wrong
if `external_endpoints` is understood by downstream transcription as "merge
this into the identically-described rail by name", which no file states and
which `RAIL_NEG` ≠ `MODULE_ANALOG_NEG12` would defeat anyway.

**Smallest fix.** Delete the `RAIL_POS`/`RAIL_NEG` nets and the
`external_endpoints` line; add `MODULE_ANALOG_POS12` to `ports:` (`dir: in`,
`from: module/power-entry`) and put `D-JACK-CLAMP.K` on it and
`D-JACK-CLAMP.A` on the existing `MODULE_ANALOG_NEG12` net — i.e. make this
circuit look like `pitch-stage`.

---

## N1-3 — `module/pitch-stage`.`GAIN_TRIM_MID` / `TRIM-GAIN`: the page states two different nominal gains for the same network, and the netlist cannot say which

**Severity: Medium.**

**Claim.** `pitch-stage.md` states the stage's gain as **2.000** in its value
table and as **2.020000** in its trimming section; the netlist's
`TRIM_GAIN_STRAP` is deliberately unasserted, so nothing in the corpus fixes
where "nominal" sits. The two figures differ by ±54 cents at the ends of the
range, on the one output where cents are the unit.

**Evidence.** `[repo hardware/module/pitch-stage/pitch-stage.md, Component values, TRIM-GAIN]` *"0 → +2 % of ratio, one-sided … **Nominal is dead on
2.000** and the trimmer has no downward authority"*. `[repo same page, "The trims still interact one way"]` *"**the exact DC solve gives gain 2.020000 for
every load** from open circuit to 2 kΩ, with about 1 ppm of residual"*.

`[repo hardware/module/pitch-stage/netlist.yaml]` `R1: "10k"`, `R2: "10k"`,
`TRIM-GAIN: "200R multiturn cermet"`, note *"IN SERIES with R2, between R2 and
the jack"*, and the series path is `GAIN_TRIM_MID: [R2.2, TRIM-GAIN.W]` with
`TRIM-GAIN.CCW` on `JACK_TIP` — so the inserted resistance is the W↔CCW
section, 0 → 200 Ω.

`[calc]` the feedback ratio and the two endpoints of the trimmer:

```
k = (R2 + R_trim)/R1
wiper at CCW:  k = 10000/10000  = 1.000  →  gain 1+k = 2.000, intercept -k·2.500 = -2.500 V
wiper at CW:   k = 10200/10000  = 1.020  →  gain 1+k = 2.020, intercept          = -2.550 V
```

So 2.020000 is the **end-stop** value, reachable only with the full 200 Ω in
circuit, and 2.000 is the other end stop. `[calc]` the difference at the window
edges: `V_out(k=1.02) − V_out(k=1.00) = 0.02·V_dac − 0.05`, which is −45 mV at
`V_dac` = 0.25 V and +45 mV at 4.75 V — **∓54 cents** on 1 V/oct
(`0.045 V / 1 V per octave × 1200`).

The load-independence claim the 2.020000 sentence is making is **correct and I
verified it from the netlist**: with the tap at `JACK_TIP` and no current into
`MINUS_NODE`, `V_jack = V_dac(1+k) − k·V_ref` for any load, exactly. `[calc]`
That is the page's real point; the defect is that it carries a specific gain
number that its own value table contradicts, and that "about 1 ppm of residual"
is reported for a relation that is algebraically exact — i.e. the sentence is
reporting a numerical solve rather than the topology, and the solve was run
with the trimmer at one particular setting that the sentence does not name.

**What would have to be true for this finding to be wrong.** That "nominal"
for this stage is defined as the trimmer fully inserted (200 Ω in circuit), in
which case 2.020000 is the nominal and *"Nominal is dead on 2.000"* is the
error rather than the other way round. Either way the two live sentences cannot
both stand. Also wrong if `TRIM-GAIN.W`↔`CCW` at rest is 200 Ω rather than 0 Ω,
which is a wiper-position convention no file states — and which is itself the
point: `TRIM_GAIN_STRAP` (the `CW` terminal) is listed in
`external_endpoints` as undecided, so the file cannot answer it.

**Smallest fix.** Name the setting in the 2.020000 sentence ("with the trimmer
at its `+2 %` end stop, the exact DC solve gives 2.020000 for every load"), so
the two numbers stop competing. The physical question — whether `TRIM-GAIN`
should bracket 2.000 instead of sitting above it — is already the page's own
E9 open item and is not this finding.

---

## N1-4 — `module/pitch-stage`.`MINUS_NODE` / `C-FB-PITCH`: the shelf's stated pole and zero are the 1 nF pair, not the netlist's 2.2 nF pair

**Severity: Low.**

**Claim.** The paragraph that establishes *why* a capacitor across `R2` cannot
filter — the page's most load-bearing stability argument, and the one it says
three other places got wrong — quotes a pole at 15.9 kHz and a zero at
31.8 kHz. Those follow from `C` = 1 nF, the superseded value. From the
netlist's 2.2 nF they are 7.23 kHz and 14.5 kHz.

**Evidence.** `[repo hardware/module/pitch-stage/pitch-stage.md]`:

```
G(s) = 1 + (R2/R1)/(1 + sR2C) = (2 + sRC)/(1 + sRC)
```
*"Pole at 15.9 kHz, **zero one octave above at 31.8 kHz**, flattening at gain 1."*

`[repo hardware/module/pitch-stage/netlist.yaml]` `C-FB-PITCH: value: "2.2nF"`,
`R2: "10k"`. `[calc]`

```
1/(2π·10 kΩ·1.0 nF) = 15 915 Hz   ← the stated pole
1/(2π·10 kΩ·2.2 nF) =  7 234 Hz   ← the netlist's pole
zero = 2× pole:  31.8 kHz  vs  14.5 kHz
```

The page itself records the move `[repo same page]`: *"This row said **1 nF /
~16 kHz** until 2026-09-21; the value went to 2.2 nF … and this row did not
follow"* — the row was fixed and this derivation, two sections away, was not.
The transferable conclusions in the same paragraph — *"Maximum attenuation
6.02 dB, at any frequency, for any capacitor value"* and *"It is a shelf, not a
pole"* — are value-independent and `[calc]` correct (`20·log10(2) = 6.021 dB`),
so the argument survives; only the two frequencies are stale.

**What would have to be true for this finding to be wrong.** That the
paragraph is deliberately narrating the superseded 1 nF part rather than the
fitted one. It does not say so, and it is written in the present tense about
the live topology decision.

**Smallest fix.** Replace "15.9 kHz" with 7.23 kHz and "31.8 kHz" with
14.5 kHz, or drop both numbers and keep the ratio, since the paragraph's point
is that the shelf is 6.02 dB *whatever* the capacitor is.

---

## N1-5 — `module/breath-output-stage`.`SUM_NODE` / `R-BREATH-FB`: the summer's fixed gain is 4.02 from the netlist, not 4

**Severity: Low.**

**Claim.** The page and the netlist both call `U-BREATH-SUM` a "fixed ×4"; the
netlist's own resistors give 4.020, so the stage's range is 0.5025–4.020, not
the stated 0.5–4.0.

**Evidence.** `[repo hardware/module/breath-output-stage/netlist.yaml]`
`R-BREATH-FB: "40.2k 1%"` (note: *"40.2k, NOT 40k — 40k is not an E96 value"*),
`R-BREATH-IN: "10k 1%"`, and `U-BREATH-SUM` note *"Inverting summer, fixed x4 =
R-FB/R-IN"*. `[repo .../breath-output-stage.md]` *"attenuation = 0.125 … 1.000
× fixed gain R-FB/R-IN = 4 = 0.5 … 4.0"*.

`[calc]` `40.2k/10k = 4.020`; `R-GAIN-FLOOR` floor is `7.15/(50 + 7.15) =
0.125109`; product `0.125109 × 4.020 = 0.50294`. So 0.503–4.020.

This is a stated rounding rather than a wrong netlist — and the same page's
offset table uses **40.2 k exactly** and reproduces `[calc]` to three figures
(`−40.2k × (2.605/(21.0k + 2.5k) − 12/95.3k) = +0.6057 V` against the page's
`+0.606 V`; full CCW `+5.062 V` vs `+5.06`; full CW `−4.9115 V` vs `−4.91`;
zero crossing `p = 0.56689` → `+20.07°` vs `+20.1°`). So the page is precise
where it matters and loose only in the headline. Filed because the 0.5×
**floor** is a specification ("Without it the knob reaches zero gain") and
0.5025 vs 0.5000 is the kind of 0.5 % that gets propagated as exact.

**What would have to be true for this finding to be wrong.** That "×4" is
openly nominal shorthand. It reads that way, which is why this is Low and not
Medium — but `R-FB/R-IN = 4` is written as an equation, and it is not one.

**Smallest fix.** Write `R-FB/R-IN = 4.02` in the two places (page value table
and the netlist note), or state "×4 nominal (4.02 as built)".

---

## N1-6 — `carrier/breath-excitation-reference`.`U-REFBUF` / `U-BREATHBUF`: the negative rail of both halves is asserted only in prose

**Severity: Low.**

**Claim.** Both OPA2197 halves declare `rails: [UMBILICAL_POS12]` and nothing
else, so the authoritative file does not say where `V−` goes. The only
statement is a `note:` field.

**Evidence.** `[repo hardware/carrier/breath-excitation-reference/netlist.yaml]`
`U-REFBUF: … rails: [UMBILICAL_POS12] … note: "Single supply from +12 V, **V-
on the analog star**. …"`; `U-BREATHBUF` the same, with no rails statement about
the star at all. `AGND_INST` is a declared port here (`dir: ref`) and carries
seven capacitor and reference returns, but neither op-amp. Every module
OPA2197 half by contrast declares both rails `[repo hardware/module/{pitch-stage,mod-channels,breath-output-stage,breath-response-shaper}/netlist.yaml]`.
`[repo hardware/carrier/carrier.md §2]` the drawing annotates `(V+ = +12V)` and
says nothing about `V−` either.

**What would have to be true for this finding to be wrong.** That `rails:` is
understood to mean "the supplies that are not the reference net", with the
reference implied by the circuit's `ref` port. Nothing states that, and the
module circuits list a negative rail explicitly, so the convention is not
uniform.

**Smallest fix.** `rails: [UMBILICAL_POS12, AGND_INST]` on both halves, and add
the op-amps to the page's `AGND_INST` Interfaces row.

---

## N1-7 — `module/breath-receive-stage`.`U-REF-BUF`: the only OPA2197 half on the module with no `rails:` at all

**Severity: Low.**

**Claim.** `U-REF-BUF` — the buffer whose whole justification is that the
INA828's `REF` pin needs a low source impedance — declares no supplies.

**Evidence.** `[repo hardware/module/breath-receive-stage/netlist.yaml]`
`U-REF-BUF: {part: OPA2197, section: A, of: U-OPA-PITCH, pins: [IN+, IN-, OUT], note: "Buffers the trimmer wiper into the in-amp REF pin…"}` — no `rails:` key.
The circuit's `MODULE_ANALOG_POS12`/`NEG12` nets carry `U-DIFFRX.V+`/`V-` and
the two BAV99 legs, and no op-amp. `[repo .../breath-receive-stage.md, ## Interfaces]` says the rails feed *"The INA828, **both OPA2197 halves**, and the
BAV99 legs on the input pair and at the jack"* — a row that also still counts
two halves and a jack clamp this circuit no longer owns, so the page's claim is
not usable as the assertion either.

**What would have to be true for this finding to be wrong.** That an omitted
`rails:` is read as "supplied, unstated". Every other OPA2197 half on the
module states it, so the omission is a difference, not a convention.

**Smallest fix.** `rails: [MODULE_ANALOG_POS12, MODULE_ANALOG_NEG12]` on
`U-REF-BUF`. (Separately, that Interfaces row's "both OPA2197 halves … and at
the jack" is stale against the output-stage split — outside my claim type, but
it is the reason the page cannot stand in for the netlist here.)

---

## N1-8 — `module/breath-receive-stage`.`AGND_SENSE` / `D-CLAMP-IN+`: the clamp's note names a node the net is not

**Severity: Low.**

**Claim.** `D-CLAMP-IN+`'s note says *"Clamps IN+ to the rails"*, but its
common terminal is on `AGND_SENSE` — the far side of `R2`, not `IN_POS`. Same
for `D-CLAMP-IN-` on `BREATH_SENSE` vs `IN_NEG`.

**Evidence.** `[repo hardware/module/breath-receive-stage/netlist.yaml]`
`AGND_SENSE: [port: …, R2.1, D-CLAMP-IN+.C]` and
`BREATH_SENSE: [port: …, R3.1, D-CLAMP-IN-.C]`, against
`IN_POS: [R2.2, R4.1, C-CM-IN+.1, C-DIFF-BREATH.1, U-DIFFRX.IN+]`.
The drawing agrees with the **nets** `[repo hardware/module/breath-receive-stage/breath-receive-stage.md]` — the
`[D-CLAMP-BREATH] BAV99 to ±12 V, both legs` arrow lands on the two incoming
conductors above `R2`/`R3` — so the netlist is right and only the note is
loose. That ordering is also the correct one electrically: the diode takes the
fault and `R2`/`R3` further limit what reaches the pin.

**What would have to be true for this finding to be wrong.** That "IN+" in the
note means "the IN+ *leg*" rather than the in-amp pin. `R2`'s own note in the
same file uses it that way (*"Module-side series protection, IN+ leg"*), which
is why this is Low. On a page whose whole subject is which side of a series
element a node sits on, the ambiguity is still worth closing.

**Smallest fix.** *"Clamps the IN+ leg at the connector side of `R2`"*.

---

## N1-9 — `module/breath-response-shaper`.`V_SHAPED`: an Interfaces row that no netlist and no master net backs

**Severity: Low.**

**Claim.** The page's `## Interfaces` table declares `V_shaped` as `out` with
peer `module/breath-output-stage`. There is no such port in either netlist and
no such net in `hardware/nets.yaml`.

**Evidence.** `[repo hardware/module/breath-response-shaper/breath-response-shaper.md]`
`| `V_shaped` | out | `module/breath-output-stage` | — | Drawn feeding the gain
attenuator. *Where it inserts* is argued below and is open |`.
`[repo hardware/module/breath-response-shaper/netlist.yaml]` `V_SHAPED` is a
local net (`U-RESP-A.OUT`, `R-RESP-FB.2`, `POT-RESP.CCW`) with no `port:`
entry, and the file says why: *"WHERE THIS INSERTS IS OPEN and the x2 restoring
stage … is not drawn, so this file stops here rather than asserting a path"*.
`[test] grep -n "V_SHAPED\|proposed:" hardware/nets.yaml` → four `proposed:`
lines, all `module/breath-response-shaper`, on `MODULE_ANALOG_POS12`,
`MODULE_ANALOG_NEG12`, `AGND_MOD` and `BREATH_INAMP_OUT`; no `V_SHAPED` entry
at all.

The netlist's position is the honest one — the restoring ×2 half is costed and
undrawn, so asserting the path would invent it. The defect is that the
Interfaces table, which `hardware/README.md` defines as *"a wiring instruction"*
with *"Exactly one page sources a net"*, asserts an `out` that nothing else in
the corpus knows about.

**What would have to be true for this finding to be wrong.** That a `—`-class
context row and an `out` row are interchangeable while a circuit is `proposed`.
`hardware/README.md` distinguishes them explicitly (`—` = "no connection here
— the row is context").

**Smallest fix.** Change that row's `Dir` to `—` and its note to "proposed
insertion point; not asserted in `netlist.yaml` or `nets.yaml` until the ×2
restoring half is drawn" — the same treatment `breath-receive-stage.md` gives
`CLR`.

---

## Areas checked and clean, with what was checked

Stated explicitly because a silent gap reads like a pass.

**1. Compensation capacitor: output vs across the feedback resistor.** The
corpus's own warning case is right in the netlist.
`[repo hardware/module/pitch-stage/netlist.yaml]` `C-FB-PITCH.1` is on
`AMP_OUT` (with `U-PITCH-AMP.OUT`) and `C-FB-PITCH.2` is on `MINUS_NODE` — the
op-amp **output** to the inverting input, not across `R2`, which spans
`MINUS_NODE`→`GAIN_TRIM_MID`→`JACK_TIP`. That is exactly what the page's boxed
warning demands, and the netlist's component note repeats the reason. The mod
channels, which the same page says are unaffected, carry no compensation
capacitor at all and take feedback from `OUT_n` — `[repo hardware/module/mod-channels/netlist.yaml]`, all four identically.

**2. Split DC/AC feedback, both instances.**
- `pitch-stage`: DC through `R2` + `TRIM-GAIN` from `JACK_TIP`; AC through
  `C-FB-PITCH` from `AMP_OUT`. Both land on `MINUS_NODE`. Matches the page's
  handover table.
- `carrier/breath-excitation-reference`: DC through `R-FB-REF` (10 k) from
  `VS` — the **far** side of `R-ISO-REF`; AC through `R-FBX-REF` (100 Ω) +
  `C-FB-REF` (1 nF) in series from `BUF_OUT` — **before** `R-ISO-REF`. Both
  land on `REF_MINUS`. `[calc]` handover `1/(2π·10 kΩ·1 nF) = 15 915 Hz`,
  which is the page's 15.9 kHz and is above the 500 Hz breath channel as
  required. `[repo config/figures.yaml, id: riso-ref-topology]` specifies
  *"R_ISO 37.4 ohm, R_F 10 kohm taken at VS, R_Fx 100 ohm + C_F 1 nF at the
  op-amp output"* — the netlist is that, element for element and node for node.
  Also verified: neither 10 µF `C-REF-OUT` is on `BUF_OUT` (they are on
  `UMBILICAL_POS12` and `REF_5V`), which is `cref-out-node` settled and,
  per that entry, the difference between a 1 nF load limit and 10 000× it.

**3. Unity followers, output tied to inverting input — all six.**
`U-BREATHBUF` (`SENSOR_BUFFERED_OUT`), `U-BREATH-BUF` (`BUF_OUT`),
`U-REF-BUF` (`REF_DRIVE`), `U-MOD-REFBUF` (`VREF_MOD`), `U-PITCH-REFBUF`
(`VREF_BUFFERED`) each have `.OUT` and `.IN-` on one net. `U-REFBUF` is the
deliberate exception — its `IN-` is on `REF_MINUS` because its feedback is the
dual network of item 2, not a strap. `[repo, per-pin net dump across all 22 netlists]`

**4. Virtual grounds, asserted and denied.**
- Asserted and correct: `breath-output-stage.SUM_NODE` (`U-BREATH-SUM.IN-`,
  `R-BREATH-IN.2`, `R-BREATH-OFF.2`, `R-BREATH-OFFNEG.2`, `R-BREATH-FB.1`) with
  `U-BREATH-SUM.IN+` on `AGND_MOD` — the offset is injected at the summing node
  exactly as the receive page requires, and the gain pot is a **buffered
  attenuator ahead of it**, not a rheostat in the loop.
  `breath-response-shaper.VIRTUAL_GND` likewise, with `U-RESP-A.IN+` on
  `AGND_MOD` and the antiparallel diode branch injecting into the node
  (`D-RESP-A.A` / `D-RESP-B.K`), which is what the page's shaping argument
  needs.
- Denied and correct: `pitch-stage.MINUS_NODE` and `mod-channels.MINUS_n` are
  non-inverting nodes sitting at `V_dac`, and the page says so in as many
  words. The deleted `R-OFFINJ` — the part that used to inject into that node
  on the false premise that it was a virtual ground — appears in **no** netlist
  and in **no** `bom.csv` row `[test] grep -rn "R-OFFINJ" hardware/ config/` →
  only prose in `pitch-stage.md` and `bom.csv` notes recording the deletion.

**5. Series elements inside vs outside the loop.**
- `pitch-stage`: `R-OUT-PROT` spans `AMP_OUT`→`JACK_TIP` and the DC tap is on
  `JACK_TIP`, so it is **inside** the DC loop. `[calc]` with no current into
  `MINUS_NODE`, `V_jack = V_dac(1+k) − k·V_ref` for any load — exactly
  load-independent, which is the page's entire case for moving the tap.
  `C-FILT-PITCH` (10 nF) is on `JACK_TIP` and therefore outside the AC loop,
  which `C-FB-PITCH` from `AMP_OUT` makes safe (β(∞) = 1).
- `mod-channels`: `R-OUT-PROT-n` spans `OUT_n`→`MODn_JACK` and feedback is
  taken at `OUT_n`, so it is **outside** the loop and `C-FILT-MOD-n` (82 nF) is
  isolated. The netlist note says exactly this, per channel.
- `breath-output-stage`: same as mod — `R-BREATH-FB` from `BREATH_OUT`,
  `C-OUT-BREATH` on `JACK_TIP`.
- `breath-excitation-reference`: `R-ISO-REF` is inside the DC loop and outside
  the AC loop, which is the whole content of `riso-ref-topology`.

**6. Every stated gain and intercept, recomputed from the netlist's resistors.**

| Stage | Page/register says | `[calc]` from netlist | Agrees? |
|---|---|---|---|
| `pitch-stage` | slope 2.000, intercept −2.500 V | `1 + 10k/10k = 2.000`; `−(10k/10k)·2.500 = −2.500 V` | yes (trimmer at 0 Ω — see N1-3) |
| `mod-channels` | `V = 4·V_dac − 3·V_ref`, ±10.000 V | `1 + 30k/10k = 4.000`; `k = 3.000`; `3 × 3.3333 = 9.9999 V` | yes |
| `breath-receive-stage` raw | `G = 1 + 50k/42.2k = 2.185` | `1 + 50000/42200 = 2.184834` | yes — and the 50 kΩ is confirmed `[datasheet datasheets/analog/INA828IDR.pdf §6.x: "Gain equation 1 + (50 k / R_G) V/V"]` |
| `breath-receive-stage` effective | 2.16106 (raw × 1M/(1M+11k)) | `2.184834 × 1e6/1.011e6 = 2.161063`; the 11 kΩ is `R1` 1 k + `R2`/`R3` 10 k per leg, and `R4`/`R5` 1 M to `AGND_MOD` are the dividers | yes |
| `breath-receive-stage` polarity | `V = −2.16106·(V_BREATH − V_AGND) + V_REF` | `BREATH_SENSE`→`R3`→`IN−`, `AGND_SENSE`→`R2`→`IN+`, so `G·(V_IN+ − V_IN−)` is `−G·(V_BREATH − V_AGND)` | yes |
| `breath-output-stage` gain | ×4, range 0.5–4.0 | `40.2k/10k = 4.020`, floor `7.15/57.15 = 0.12511` → 0.503–4.020 | N1-5 |
| `breath-output-stage` offset | +5.06 / +0.606 / −4.91 V, zero at +20.1° | reproduces to 3 figures from 21.0k / 95.3k / 40.2k / 10k pot (`p = 0.56689`) | yes |
| `breath-response-shaper` | ÷2 inverting; wiper 0 V at centre for any input | `−10k/20k = −0.500`; ends at `+V_in/2` (matched 10k/10k divider) and `−V_in/2` (the stage's own output), so the midpoint is 0 V by construction, not by tolerance | yes |
| reference buffer handover | 15.9 kHz | `1/(2π·10 kΩ·1 nF) = 15 915 Hz` | yes |
| `umbilical-load-switch` FB divider | `k = 0.1250`, ratio 6.986 | `5.11/(35.7+5.11) = 0.125214`; `35.7/5.11 = 6.9863` | yes |
| `umbilical-load-switch` thresholds | PWRGD 10.49 V, full limit 3.99 V, re-assert 9.85 V, `V_FB` 1.503 V at 12 V, 294 µA | `1.313/0.125214 = 10.486`; `0.5/0.125214 = 3.993`; `1.233/0.125214 = 9.847`; `12 × 0.125214 = 1.5026`; `12/40.81k = 294.0 µA` | yes, all five |
| `umbilical-load-switch` foldback slope | 8.77 mV/V, `m` = 0.1753 A/V, limits 415/591/766/940 mA | `70 mV per V_FB × 0.125214 = 8.765 mV/V`; `/50 mΩ = 175.3 mA/V`; `(12 + 8.765·V)/50 mΩ` gives 415.3 / 590.6 / 765.9 / 939.4 mA | yes |
| `umbilical-load-switch` start | phase 1 17.1 ms, phase 2 30.4 ms, 47.5 ms total; escape at 0.16 V / 1.3 ms; fast corner 1.69 V / 10.1 ms | `(2.2m/0.1753)·ln(940/240) = 17.14 ms`; `2.2m×8.01/0.580 = 30.38 ms`; `(268×0.05−12)/8.765 = 0.160 V`; `(537×0.05−12)/8.765 = 1.695 V`, `0.01255·ln(537/240) = 10.11 ms` | yes |
| `umbilical-load-switch` timer/gate | 587 / 160 / 95.6 ms; 61 / 122 / 244 V/s; 2.01× | `1.233×10µ/21µ = 587 ms`, `/77µ = 160.1`, `/129µ = 95.6`; `5µ/82n = 61.0`, `10µ/82n = 122.0`, `20µ/82n = 243.9`; `95.6/47.5 = 2.013` | yes |
| `power-entry` DAC rail | 5.21 V | **1.65 V** | **N1-1** |

**7. The LT1641 gate network, which is a compensation loop and not a divider.**
`[repo hardware/module/umbilical-load-switch/netlist.yaml]`
`GATE_DRIVE: [U-LOADSW.GATE, R-GATE-SER.1, R-GATE-COMP.1]`,
`GATE_NODE: [R-GATE-SER.2, Q-LOADSW.G]`,
`GATE_COMP_MID: [R-GATE-COMP.2, C-GATE-LOADSW.1]`, `C-GATE-LOADSW.2` on
`PWR_GND`. So `R-GATE-COMP` is **in series with** `C-GATE`, from the `GATE`
pin side of `R-GATE-SER` to ground — which is the page's own ASCII detail and
ADI's Figure 5, and *not* the "capacitor straight to ground" that removes the
compensation zero. `R-ILIM` spans `BUS_POS12_RAW`→`SENSE_NODE` with
`U-LOADSW.SENSE` and `Q-LOADSW.D` on `SENSE_NODE`, and the FB divider hangs off
the FET **source** (`UMBILICAL_POS12`), which is the output — the exact node
the page's §5 correction is about. Clean.

**8. Boundary-net hygiene of the loops themselves.** Each feedback net checked
is internal to its circuit; no feedback path crosses a circuit boundary
anywhere in the corpus, so no loop depends on `nets.yaml` being right. The one
place a loop *reaches* a boundary is `pitch-stage.JACK_TIP` → `J-CV-PITCH`,
and the jack is declared as this circuit's own part with `module/panel` owning
only the hole.

---

## One note on why the checker passes all of this

`tools/check-netlist.py` proves refdes, values, pin uniqueness, both halves of
each master net, and drawing labels. It does not, and does not claim to,
evaluate a transfer function or ask whether a net is the right node. N1-1 is a
value-correct, endpoint-correct, drawing-consistent netlist that delivers a
third of the intended rail voltage, and N1-2 rides on the `rails:` implicit-port
exemption at `[repo tools/check-netlist.py:435-447]`. Both are the semantic half
`CLAUDE.md` §5 says a grep cannot reach — with the twist that the netlists are
now the authoritative artefact, so the semantic gap has moved into the file the
build is transcribed from.

A cheap mechanical guard for the N1-1 class, offered rather than proposed:
`figures.yaml` already carries `derivation:` strings containing the arithmetic
(`"1.25 x (1 + 475/150) = 5.208 V"`). Nothing checks that the resistors named
in a derivation sit on the nets that derivation implies. That is a narrower
check than "evaluate the circuit" and would have caught this one.
