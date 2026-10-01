# A2 - Pitch and the four mod channels

**Slice:** DAC8568 and its reference, power-on/reset output state, the pitch stage and its trims, mod-channels (incl. R-OUT-PROT outside the loop into 100 k), output protection, ADR 0006's channel allocation, and the jack allocation after the 2026-10-01 swap through J-B2B-MOD to the jacks.
**Revision measured:** 13197f8 (pinned `git archive` copy, tools/ at the same revision)
**Tools:** `tools/sim.py run` on `pitch-stage/sim` (72 runs, 0 failed), `mod-channels/sim` (42, 0 failed), `dac8568/sim` (51, 0 failed), all three `results.yaml` byte-identical to the committed ones; `check-netlist.py --strict` (0 problems); `kicad.py check` (PASS, 22 sheets, 6 boards); `check-staleness.py` (FAIL: 2 cad, see A2-15); `pdftotext -layout` on SBAS430E (`DAC8568CIPW.pdf`), LT5400 rev fa, SBOS737C.

## Summary

- **The circuits hold.** Pitch is a correct non-inverting stage, `Vout = 2·Vdac − 2.500`, DC loop closed at the jack, `C-FB-PITCH` op-amp output to (−), netlist matches the page's prose. The offset-trim arithmetic, the ±1 % bipolar gain trim, the 0.76/0.45-cent budget, the mod law `4·Vdac − 3·V_ref` with V_ref 3.3333 V, the ±50.5 mV / 19.703–20.303 V tolerance, the C-grade lock, the power-on and CLR states, and R-OUT-PROT's power rating all re-derive. The three sims reproduce exactly.
- **The jack swap is consistent end to end.** `J-B2B-MOD` carries BREATH 11, PITCH 14, MOD1 15, MOD3 16, MOD2 17, MOD4 20 on both boards' exported netlists, pin for pin. That matches `config/module.yaml`, ADR 0024 point 13, `panel.md` and the module-main README table. The DAC channel mapping is unchanged. The only miss is one stale render (A2-15).
- **Mod range at the jack does not hold as stated.** "Exactly ±10.000 V" is true at the op-amp output only. Into one 100 kΩ input the jack reads ±9.90 V nominal, and the worst-case span is −2.46 %. The page's "±18 cents/octave" leaves the load term out (A2-1).
- **One real hardware question was left behind in a history file.** The pitch jack tip reaches an LT5400 pin through at most 200 Ω and has no clamp. The LT5400 has no internal ESD diodes. The "check this at layout" item survives only in `notes.md` (A2-2).
- **The main partial-fix shape is ADR 0006 trailing the pitch page.** Its precision table and conclusions are refuted by the pitch page's corrected budget (A2-3). Its trimmer description predates the 2026-09-30 redesign (A2-4). It says the pitch jack node "carries no capacitor at all", but `C-FILT-PITCH` sits on it (A2-5). On the pitch page itself, two 1 nF-era frequencies and a gain figure did not follow their own changes (A2-6, A2-7). The pitch sim deck still models the pre-09-30 reference (A2-8).

## Findings

### A2-1 - Mod jacks: "exactly ±10.000 V" holds only at the op-amp output; at a 100 kΩ jack the range is ±9.90 V and the worst-case span error is −2.46 %, not the ±18 cents/oct stated
**Severity:** medium
**Node:** MOD1_JACK…MOD4_JACK / R-OUT-PROT-1..4 / figure `mod-reference`
- Feedback is from the op-amp output and `R-OUT-PROT` sits outside the loop. [repo] `hardware/module/mod-channels/netlist.yaml` OUT_n = R2-n.2 + R-OUT-PROT-n.1; MODn_JACK = R-OUT-PROT-n.2 + C-FILT-MOD-n + J tip.
- Into 100 kΩ the gain is 100/101 = 0.990 [calc]. [sim] `mod-channels/sim` `range`: jack nominal −9.90085 / +9.90066 V.
- Worst corner (R1+ R2−): jack_hi 9.80263 and jack_lo −9.70479 give a span of 19.507 V, which is −2.46 % of 20.000 [sim + calc]. That is −29.6 cents/oct on a pitch-like assignment [calc: 0.0246 × 1200].
- `mod-channels.md:139-142` states the 1 % load error and then, in the next sentence, "About ±18 cents per octave". ±18 is the resistor-tolerance span alone (±1.5 % × 1200 [calc]), so it reads as the load consequence and omits the load term. The tolerance table at `:133-136` carries no load row.
- ADR 0006's decision table still gives Mod 1–4 as "−10…+10V" [repo] `docs/decisions/0006-cv-channel-allocation.md:13`. Firmware scaling cannot reach ±10 V at a loaded jack, because the DAC code is already at 0 and full scale.
- `mod-channels/sim/README.md:21` and the sims.yaml `why` say "the page's tolerance section does not carry" the load error. That is now half-true: the prose has it, the table does not.

**What would settle it:** a one-line decision. Either state the range "at the op-amp output, ±9.90 V into 100 kΩ", or accept and record it.

### A2-2 - PITCH jack tip reaches an LT5400 pin through at most 200 Ω and has no clamp; the "check at layout" item is only in notes.md
**Severity:** medium
**Node:** JACK_TIP (pitch) / TRIM-GAIN / RN-PITCH.R2B / D-JACK-CLAMP
- [repo] `pitch-stage/netlist.yaml`: JACK_TIP = {C-FILT-PITCH.1, J-CV-PITCH.TIP, R-OUT-PROT.2, TRIM-GAIN.CCW}. GAIN_TRIM_MID = {RN-PITCH.R2B, TRIM-GAIN.W, TRIM-GAIN.CW}. The jack therefore reaches the LT5400 through the trimmer's CCW–W section, which is 0–200 Ω.
- `D-JACK-CLAMP` is on AMP_OUT, the op-amp side of the 1 k, by design [repo] `hardware/module/bom.csv` D-JACK-CLAMP "MOVED to the op-amp side".
- [ds LT5400.pdf p.6]: "designed without explicit ESD internal protection diodes… ±1kV… ESD beyond this voltage can damage or degrade the device including causing pin-to-pin shorts". Its Figure 1 remedy is a BAV99 at the external connector.
- `pitch-stage/notes.md:102-106` says "check the clamp actually stands between the jack and every LT5400 pin when this is laid out". It does not. The item is absent from the live page's "Still open" (`pitch-stage.md:380-384`).
- Incidental mitigation: `C-FILT-PITCH` 10 nF on the node. HBM 100 pF into 10 nF holds an 8 kV strike to about 80 V; IEC 150 pF holds it to about 118 V [calc: charge sharing, ignoring the source resistor]. But this cap is on module-main, across `J-B2B-MOD` from the jack ([repo] module-main `board-netlist.yaml` C29 = C-FILT-PITCH on /PITCH_JACK). No document claims it as the ESD defence.
- A clamp at JACK_TIP would cost no accuracy, because that node is regulated by the loop. It would bring back the back-powering the D-JACK-CLAMP move removed (42 mA/jack [repo] D-JACK-CLAMP note).

**What would settle it:** a recorded decision before layout. Either C-FILT-PITCH is the ESD defence (then place it hard at J-B2B-MOD pin 14 and say so), or add a clamp or TVS at JACK_TIP.

### A2-3 - ADR 0006's precision table and its conclusions are refuted by pitch-stage.md's corrected budget, and pitch-stage.md endorses the refuted 0.54
**Severity:** medium
**Node:** figure `pitch-cents-budget` / R-PRECISION / U-DAC reference
- [repo] `0006:366-402` table: reference 0.54 cents, discretes 5.40, matched network 0.11. Its conclusions are "Resistor tracking dominates reference drift by roughly ten to one" and "The DAC's internal reference is sufficient. At 0.54 cents… an order of magnitude inside the resistors, so a separate precision reference buys nothing measurable". It repeats 0.11 and 5.4 at `:472-473`.
- The owner page's budget (`pitch-stage.md:320-334`, figure `pitch-cents-budget`) re-derives to: reference 0.42 cents [calc: 5 ppm × 10 °C × 7 V = 350 µV × 1.2], LT5400 0.027 [calc: 10 ppm × 2.25 V], discretes 0.38. The reference is the largest term, about 15× the network. `pitch-stage.md:342-351` says attacking it with an external reference is the obvious next step. The ADR's ranking is inverted and its "buys nothing measurable" is refuted by the corrected numbers. This is shape 4.
- `pitch-stage.md:123-124` says the ADR's "sufficient, at 0.54 cents over 10 °C" survives. Twelve lines of the same page later, the same term is 0.42 (`:327`).

**What would settle it:** none needed. This is arithmetic [calc] against SBAS430E p.4 (5 ppm/°C max, C/D) and LT5400 p.3 (1 ppm/°C max).

### A2-4 - ADR 0006 describes the pre-2026-09-30 trims
**Severity:** low
**Node:** TRIM-GAIN, TRIM-OFFSET, R-GAIN-CTR, U-OPA-PITCH
- `0006:745`: "`TRIM-GAIN` shrinks to 200 Ω (0 → +2 %)… ~2 ppm/°C". It also says "At 200 Ω it contributes 2 %", and `:476-479` says "Keep the trim range small — 5 to 10 %". The built trim is ±1 % bipolar about R-GAIN-CTR, at about 1 ppm/°C at mid-travel [repo] `pitch-stage.md:132`, bom.csv TRIM-GAIN.
- `0006:487`: "The offset trimmer divides down the DAC's buffered `VREFOUT`". The built trimmer sits ahead of the buffer, across the unbuffered pin, and injects through R-VREF-INJ [repo] netlist VREFOUT = {R-VREF-SER.1, TRIM-OFFSET.CW}.
- `0006:625-627`: "Hanging a trimmer directly on VREFOUT would make the reference move… A follower breaks that". The built circuit does hang it there. The effect is negligible: the wiper-dependent load is 0–108 µA [calc: 2.5 V / 23.1 kΩ] × 30 µV/mA [ds SBAS430E p.4 load regulation], about 3 µV or 1.3 ppm. So the rationale is wrong and the outcome harmless.
- `0006:632`: "the last spare op-amp half in `U-OPA-PITCH`". Two halves are spare [repo] U-OPA-PITCH and U-RESP rows.
- ADR 0006 says the pages win (`:83-86`), so nothing builds wrong from this. It is shape 1.

### A2-5 - ADR 0006 says the pitch jack node "carries no capacitor at all"; C-FILT-PITCH 10 nF is on it
**Severity:** low
**Node:** JACK_TIP (pitch) / C-FILT-PITCH
- [repo] `0006:765-768`: "Pitch is now the exception — its feedback is tapped at the jack, so that node is the feedback node and carries no capacitor at all."
- [repo] `pitch-stage/netlist.yaml` JACK_TIP includes C-FILT-PITCH.1, and the same ADR at `:713` and `:737-742` records the deletion as reversed. The bullet is a survival of the deletion. It is shape 1 inside one document.

### A2-6 - pitch-stage.md: the shelf's frequencies are the 1 nF values; with 2.2 nF the pole/zero are about 7.2/14.4 kHz
**Severity:** low
**Node:** C-FB-PITCH / figure `pitch-compensation`
- [repo] `pitch-stage.md:224`: "Pole at 15.9 kHz, zero one octave above at 31.8 kHz". Also `:213`: "R2 + TRIM-GAIN… DC to ~16 kHz".
- For G(s) = (2+sRC)/(1+sRC) with R = 10.1 kΩ (R2 + TRIM-GAIN mid) and C = 2.2 nF: pole 1/(2π·10.1k·2.2n) = 7.16 kHz, zero 14.3 kHz [calc]. 15.9 kHz is 1/(2π·10k·1nF), the value retired 2026-09-21. `:214`'s own aside records that the neighbouring row "did not follow". `:213` and `:224` did not follow either.
- The same 15.9 kHz shelf pole is repeated in the C-AA-PITCH BOM note [repo] `pitch-stage/bom.csv` C-AA-PITCH.
- Not verified: the page's "−3 dB at 12.2 kHz" overall. No sim measures it.

### A2-7 - pitch-stage.md "exact DC solve gives gain 2.020000 for every load" matches no current configuration
**Severity:** low
**Node:** RN-PITCH / TRIM-GAIN / R-GAIN-CTR
- [repo] `pitch-stage.md:297`. The nominal gain is 2.000. The trim range is 1 + 10000/10100 = 1.990 to 1 + 10200/10100 = 2.0099 [calc].
- 2.0200 = 1 + 10200/10000, which is the pre-R-GAIN-CTR circuit with TRIM-GAIN at 200 Ω [calc]. The load-independence claim itself is right: R-OUT-PROT sits inside the DC loop, and the sims show it. Only the stated number is stale.

### A2-8 - The pitch sim deck models the pre-2026-09-30 reference, not "the stage as netlisted"
**Severity:** low
**Node:** `hardware/module/pitch-stage/sim` / R-GAIN-CTR, R-VREF-*, TRIM-OFFSET
- [repo] `pitch-step.cir:1-17`, and `pitch-loop.cir` likewise: V_ref is a unity follower of an ideal VREFOUT, R1 goes straight to it, and there is no R-GAIN-CTR, R-VREF-FB/GND, R-VREF-SER/INJ or TRIM-OFFSET. The header still says "TRIM-OFFSET is at its CW end (V_ref = VREFOUT): its CCW end is the page's open item", which was settled 2026-09-30 (`pitch-stage.md:164`).
- `sims.yaml:22` sets `r_trim_gain` 0 Ω as "the page's nominal, 'dead on 2.000' (pitch-stage.md, TRIM-GAIN row)". That phrase is no longer in the corpus [repo grep]. In the real netlist, 0 Ω is the 1.990 end.
- `dac8568/sim/poweron.cir:33` does include R-GAIN-CTR. So the trims redesign reached one deck and not the other. Because results.yaml hashes the netlist, `sim.py check` passes.
- The dynamic results (overshoot, phase margin) are unlikely to move materially: R-GAIN-CTR adds 100 Ω to 10 kΩ, and the follower is a stiff source.

**What would settle it:** rebuild the deck from the netlist's parts and re-run. Expect about the same numbers.

### A2-9 - pitch-stage.md drawing hangs R-GAIN-CTR/R1 from AGND, not from V_ref
**Severity:** low
**Node:** VREF_BUFFERED / R-GAIN-CTR
- [repo] `pitch-stage.md:34-40`, by character column: the vertical under `[R-VREF-GND 10k]── AGND` (column 69) runs down to `[R-GAIN-CTR 100R]` and `[R1 10k]`. The V_ref output column (61) stops at line 33, and `[R-VREF-FB 200R]`'s right end goes nowhere.
- The netlist has R-GAIN-CTR.2 on VREF_BUFFERED with R-VREF-FB.1 and U-PITCH.OUTA. Read literally, the drawing deletes the −2.500 V intercept.
- `check-netlist.py` passes because it checks labels, not topology. The netlist wins, so nothing builds wrong.

### A2-10 - mod-channels.md restates the four-resistor ±10.05 V as the live range
**Severity:** low
**Node:** figure `mod-reference`
- [repo] `mod-channels.md:156`: "**On the range:** ±10.05 V uses the DAC's *full* 0–5 V span." The adopted network gives ±10.000 V (`:95`, `:106`, `:119-120`). ±10.05 V was the 40.2 kΩ four-resistor version (`notes.md:48-54`). This is shape 2: the explanation restates the retired value.

### A2-11 - mod-channels.md's zero-point formula evaluates to −7.5 V
**Severity:** low
**Node:** R-MODGAIN-IN/-FB
- [repo] `mod-channels.md:147`: "The two-resistor zero is `2.5 − (10/3)k`". At k = 3 that is −7.5 V.
- The zero is 2.5(1+k) − (10/3)k = 2.5 − (5/6)k, which is 0 at k = 3 [calc]. Its ±0.0606 swing in k gives ∓50.5 mV, matching the table [calc]. The conclusion survives; the formula does not.

### A2-12 - R-MODGAIN: the BOM says buy 0.1 % thin film; the value field, page, ADR and sim say 1 %; "one reel" contradicts itself
**Severity:** low
**Node:** R-MODGAIN-IN / R-MODGAIN-FB
- [repo] `mod-channels/bom.csv` R-MODGAIN-IN: value "10k 1% metal film", notes "buy both from ONE SERIES AND TCR GRADE, Yageo RT0805BRD07 (0.1%, 25 ppm/C)… two values cannot come off one reel".
- `mod-channels.md:8`, `:118-119` and ADR 0006 `:402` say 1 %. The tolerance table (±50.5 mV, −1.49/+1.52 %) and the sim's `vary` are computed at 1 %.
- `mod-channels.md:153-154` says "Buying the four sets from one reel makes it much better than worst case". That is impossible for 10 k and 30 k, as the BOM itself says.
- If 0.1 % is what is bought, the page's tolerance figures are about 10× pessimistic. If 1 % is bought, the note is wrong.

**What would settle it:** the owner picks the part. The value field and the page follow it.

### A2-13 - R-PRECISION's "TRIM-GAIN real authority 1.86–2.16 %" is A-grade and unipolar; the ordered part is B grade and the trim is bipolar
**Severity:** low
**Node:** R-PRECISION / TRIM-GAIN
- [repo] `pitch-stage/bom.csv` R-PRECISION: "ABSOLUTE tolerance is +/-7.5% (A) / +/-15% (B), which sets TRIM-GAIN's real authority at 1.86-2.16%". The same row orders LT5400**B**IMS8E-1.
- At ±15 % absolute (R = 8.5–11.5 kΩ [ds LT5400 p.3]) with the bipolar centring, the authority is ±100/(R+100) = ±0.86 % to ±1.16 % [calc]. That is still ample against ±0.15 % FSR DAC gain error [ds SBAS430E p.3], so this is a stale figure, not a design problem. `notes.md:100` carries the same A-grade number, as history.

### A2-14 - ADR 0006 "Labelling" and ADR 0004 "Panel" still describe silkscreen plus a write-on strip in the old order
**Severity:** low
**Node:** panel legends / `art.text.jacks`
- [repo] `0006:831-832`: "Channels 1 and 2 are silkscreened. Mod 1–4 are numbered with a write-on strip".
- [repo] `0004:711-713`: "PITCH and BREATH silkscreened, MOD 1–4 numbered with a write-on strip". Its amendment note covers only point 11.
- ADR 0026 points 4 and 7 dropped the write-on strip for six word pills, and ADR 0024 point 13 reordered to BREATH, PITCH. Neither ADR 0004 nor ADR 0006 was amended.

### A2-15 - `module-photo-detail` render is stale after the jack swap
**Severity:** low
**Node:** `mechanical/module` render `module-photo-detail` / `layout.jacks`
- [test] `check-staleness.py` at 13197f8: "module-photo-detail: STALE - changed config/module.yaml, …tex-*.png, panel-art.echo, tools/render-module.py". These are the swap's inputs.
- `mechanical/module/README.md:132` captions it as the close-up of "the breath knobs and the first outputs' pills", which is the row that swapped. 13197f8 re-rendered the front photo only.

### A2-16 - ROADMAP carries two pitch items the 2026-09-30 changes closed
**Severity:** low
**Node:** R-OPAMP-IN / R-OUT-PROT (pitch)
- [repo] `ROADMAP.md:329`: "The seventh `R-OPAMP-IN` has no home — `pitch-stage.md`'s 'Still open'". The page has settled it: "R-OPAMP-IN is six… R-VREF-SER" (`pitch-stage.md:376-378`). Its Still open lists only stability.
- [repo] `ROADMAP.md:200`: "Pitch DC load sweep… Quantifies the 1 kΩ divider error against the real patch". With the jack-side tap the divider error is zero by construction (`pitch-stage.md:296-299`). The test now verifies a zero rather than quantifying an error. It is worth keeping, but reworded.

### A2-17 - ADR 0006: "Mod 1–4 … Trimmed" and the channel-number collisions
**Severity:** advisory
**Node:** ADR 0006 decision table
- `0006:13` marks Mod 1–4 Precision as "Trimmed", but `:523-526` says "Mod channels stay trimmer-free". Possibly "trimmed in firmware" is meant; it is not said.
- `:349` "breath locked to channel 2" and `:366` / `:402` "Channels 2–6" use output numbering, while the same ADR's table makes DAC ch 2 = Mod 1 and ch 6 = spare. A reader can take "Channels 2–6" to include the spare and exclude Mod 4.

### A2-18 - "Exactly 0 V" at power-on is within the DAC's zero-code error, which the sim leaves out
**Severity:** advisory
**Node:** DAC_CH1..5, DAC_CH7 / ADR 0006 power-on table
- [ds SBAS430E p.3]: zero-code error 1 mV typ, 4 mV max. It is positive, because the output is single-supply.
- Parked pitch is ≤ +8 mV [calc: 2 × 4 mV]. Parked mods are between −12 mV and +16 mV [calc: 4·e_n − 3·e_7, each 0–4 mV].
- `dac8568/sim` models the DAC as an exact 0 V plus a glitch, so its "mod parked within 2 mV" is a model property. This is harmless, but "exactly" is not what the datasheet guarantees.

### A2-19 - TRIM-OFFSET span "about ±60 cents" is −72/+60 cents
**Severity:** advisory
**Node:** TRIM-OFFSET / R-VREF-INJ
- [calc] V_ref moves −60.4 / +49.8 mV (re-derived: a = 1/23.1 = 0.0433 at the ends, (1+g) = 1.02). At 1.2 cents/mV that is 72 and 60 cents.
- [repo] `pitch-stage.md:185`, bom.csv TRIM-OFFSET: "about ±60 cents". The asymmetry is fine; the label is not.

### A2-20 - "At the jack" means module-main's side of J-B2B-MOD
**Severity:** advisory
**Node:** C-FILT-PITCH (C29), TRIM-GAIN.CCW (RV3), C-FILT-MOD (C36–C39) on module-main
- [repo] `module-jack/board-netlist.yaml`: the jack board carries only J1–J6, J7, RV1–3, R1, D1. Every jack cap and the pitch DC tap sit on module-main at the header [repo] module-main board-netlist /PITCH_JACK = {C29, J2.14, R34, RV3.CCW}.
- At DC this is immaterial: about 70 µA into a 100 kΩ VCO across header contact resistance is µV. It matters for the "low-impedance shunt at the connector" rationale (`pitch-stage.md:139`, `:231`) and for A2-2. Place C29 and C36–C39 at J-B2B-MOD.

## Checked and holds

- **Pitch transfer function.** Netlist = non-inverting stage, R1 (via R-GAIN-CTR) to VREF_BUFFERED, R2 + TRIM-GAIN from JACK_TIP, C-FB-PITCH AMP_OUT→MINUS_NODE, C-AA-PITCH on the (+) node, R-BIAS-DAC at the DAC pin [repo] netlist. `Vout = 2·Vdac − 2.500` at mid-trim [calc].
- **Offset trim table.** w = 0: 2.4396 V; w = 0.5: 2.5002 V; w = 1: 2.5500 V [calc, reproduces `pitch-stage.md:181-183`]. It touches gain not at all [calc: gain = 1 + (R2+t)/(R1+100) has no V_ref term].
- **Gain trim.** Ratio exactly 1 at mid-travel for any absolute R. CW end strapped to the wiper [repo] GAIN_TRIM_MID.
- **pitch-cents-budget.** 0.42 + 0.12 + 0.012 + 0.027 + 0.034 + 0.06 + 0.09 = 0.763 linear, 0.452 RSS [calc]. Datasheet inputs verified: 5 ppm/°C max C/D, ±1 ppm FSR/°C typ, ±0.5 µV/°C typ, ±0.15 % FSR gain error [ds SBAS430E pp.3-4]; LT5400 1 ppm/°C max, 0.2 typ [ds LT5400 p.3]; OPA2197 ±2.5 µV/°C max [ds SBOS737C p.1/p.7]. The TRIM-GAIN row's 0.034 fits (100 − 25) to (100 + 25) ppm/°C on 1 % of the ratio [calc].
- **Gain vs offset error table** (`:112-115`): 100 ppm × 2 V = 0.24 cents, × 7 V = 0.84 cents [calc].
- **Headroom.** 0–5 V maps to −2.5…+7.5 V = ±600 cents of reserve [calc]. ±11.65 V rails after the D-REVPOL drop [repo] ADR 0006:138.
- **Mod law.** k = 3, span 5(1+k) = 20 V, intercept 3 × 3.3333 = 10.000 V. Zero ±50.5 mV, span 19.703–20.303 V at 1 % [calc]. [sim] `range` agrees to 0.1 mV. Wrong-ref 2.5 V gives −7.5 V and clips [sim]. Follower load 1.333 mA at code 0 [calc, sim `ref-current`]. C-FILT-MOD 1.94 kHz [calc]. No overshoot into any mult; PM 91.6° [sim].
- **C grade and order code.** C/D are gain 2 (5 V FS); AVDD ≥ 5 V for C/D; VREFIN ≤ AVDD/2; "grades A and C… zero scale" [ds SBAS430E p.3, p.4, p.32 area]. ICPW order code is consistent across BOM, ADR and netlist note.
- **CLR, LDAC, reference.** `CLR` is pulled up by R-CLR-PU to DAC_AVDD and LK-CLR goes to AGND_MOD [repo] dac8568 netlist. `LDAC` is strapped to GND (R-LDAC 0 R) [repo]. `C-VREF-DAC` 100 nF at the pin [ds p.31]. The reference is 3-state when disabled [ds p.31], and TRIM-OFFSET's 10 k holds it at 0 V with τ = 1 ms [calc].
- **Power-on.** Pitch is 0 V, rising to −2.500 V after the reference enable. Mods are 0 V through CLR, and the pitch jack stays within 100 mV through the glitch [sim `dac8568/sim`, reproduced]. The mod ±0.12 V transient is recorded there.
- **DAC channel allocation.** ch1 = VOUTA pitch, ch2–5 = VOUTB–E mods, ch7 = VOUTG reference, F/H unconnected, consistent across ADR 0006, dac8568 netlist ports, mod-channels/pitch-stage ports and `check-netlist --strict` (0 problems). Six R-OPAMP-IN and six R-BIAS-DAC match the six DAC-driven nodes [repo].
- **Output protection.** R-OUT-PROT qty 6 and D-JACK-CLAMP qty 6 = pitch + 4 mods + breath. Output-to-output fight is 21.9 V / 1.22 kΩ = 17.95 mA, which is 322 mW in the 1 k. Dead short is 11.9²/1 k = 142 mW. Back-powering is 9.3 V / 220 Ω = 42 mA vs 9.3 V / 1220 Ω = 7.6 mA [calc]. BAV99 pins: A to −12, K to +12, common to the output [repo].
- **Pitch stability sims.** Step into a VCO overshoots 1.5 % nom / 2.4 % worst. Into a mult, `pitch-mult-overshoot` 41.8 % / 64.1 % (15.3 % / 41.8 % with the other driver). PM 69.3° at every load [sim]. This matches figures.yaml and the sim README.
- **Jack swap.** J-B2B-MOD is pin-for-pin identical on both exported board netlists. Odd = left column, BREATH 11 / MOD1 15 / MOD2 17; even = right, PITCH 14 / MOD3 16 / MOD4 20 [repo]. That matches the module-main README table, `config/module.yaml` `layout.jacks` and `art.text.jacks`, ADR 0024 point 1 and point 13, ADR 0026 point 7 and panel.md:51-53. "Fifteen signals + five AGND_MOD = 20" [repo, count]. `kicad.py check` PASS.
- **Firmware contract.** firmware/README.md states V_ref 3.3333 V refreshed every pass, the reference enable and clear-code in the refreshed set, and CLR from power-on reset plus LK-CLR. That is consistent with dac8568.md, mod-channels.md and the latency budget's six words per pass [repo].
