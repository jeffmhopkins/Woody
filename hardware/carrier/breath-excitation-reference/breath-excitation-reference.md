# Breath excitation reference — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B), and edited since.
**The KiCad sheet `breath-excitation-reference.kicad_sch` is the source**
(ADR 0019); placed on the main board
([`../../boards/main-board/README.md`](../../boards/main-board/README.md)), its
datasheets banked. What the circuit used to be is in [`notes.md`](notes.md).

The REF5050 and the OPA2197 half that buffers it, driving the MPXV4006DP's `VS`
pin through `R-ISO-REF`. **`VS` is the ratiometric scale factor**, which is why
this circuit has its own page.

**The schematic is drawn in [`carrier.md`](../carrier.md) §2 and is not redrawn
here.** That drawing is one connected picture spanning this circuit, the sensor
and the ADC's reference node; dividing it would mean redrawing it, and a
redrawn schematic is not a moved one.

## Interfaces

Every net that crosses this circuit's boundary. Quantities appear **only** as a
citation into `config/figures.yaml` — this table names nodes, it does not
restate values.

The `Dir` and `Peer` columns are defined once in
[`hardware/README.md`](../../README.md#the-interfaces-table).

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `INST_POS12` | in | `carrier/power-entry-instrument` | — | The instrument's +12 V behind `Q-INRUSH`, the hot-plug inrush limiter. The buffer half's V+, and REF5050 `VIN` through `R-REF-IN` (below) |
| `REF_VIN` | — | — | — | Internal to this circuit. REF5050 `VIN` and its bypass, after `R-REF-IN`, held by `D-REF-CLAMP` |
| REF5050 `VOUT` | — | — | `cref-out-node` | Internal to this circuit. Which side of the buffer `C-REF-OUT` sits on. Settled, and it decides the whole compensation |
| op-amp output | — | — | `opa2197-output-impedance` | Internal to this circuit. The impedance `R-ISO-REF` is sized against. Specified, not back-solved |
| `VS` | out | `interfaces/breath-sense-link` | `riso-ref-topology` | `U-BREATH`'s excitation pin, drawn in `carrier.md` §2. Through `R-ISO-REF`. DC feedback is taken **here**, not at the op-amp output — which is what makes the DC error across `R-ISO-REF` zero |
| `AGND_INST` | ref | `carrier/power-entry-instrument` | — | The instrument analog star, drawn `AGND-local` in `carrier.md` §2. `C-REF-OUT`, `C-DEC-SENSOR` and `C-DEC-BUF` (`U-BUF`'s +12 V bypass) return to it |

## `R-ISO-REF` and the compensation network

*Moved verbatim from `carrier.md` §2, "Two parts this drawing was missing, both
unretrofittable". The other of the two parts, `R1b`, is in the breath chain and
stays on [`carrier.md`](../carrier.md).*

**`R-ISO-REF` — and without it the reference buffer oscillates.** As a bare
follower into the sensor's 100 nF decoupler the reference half has **1.5° of
phase margin** `[sim, A4]` against TI's specified `Zo` = 375 Ω
`[SBOS737C p.8]`. The part this page originally drew — a 10 Ω resistor with
feedback taken at `VS` — **does not fix it**: in-loop `R_ISO` buys nothing at
*any* value, 1.5° at 10 Ω and 1.5° at 37.4 Ω. It is compensated instead with
TI's own dual-feedback network, and the four parts are drawn above.

**The compensation is TI's Figure 56, adapted.** `[SBOS737C §8.2.3 p.30,
"Precision Reference Buffer"]`. See `riso-ref-topology` for the full
derivation, the adaptation, and the simulated margins; the two things worth
having on this page are *why it transfers* and *what it buys*:

```
[calc]  R_ISO is set by Zo, NOT by C_L:

          V_A / V_i = (1 + s·R_ISO·C_L) / (1 + s·(Zo + R_ISO)·C_L)

        attenuation = R_ISO/(Zo + R_ISO)    pole/zero = (Zo + R_ISO)/R_ISO

        Both depend only on R_ISO/Zo. C_L moves the two corners together and
        cancels out of the phase margin. So TI's 37.4 Ω — which is Zo/10 —
        transfers to our 100 nF unchanged, even though TI's example drives
        10 µF, 100x more.
```

**What it buys is the end of the trade this page was stuck in.** The old
argument was "unstable in-loop" against "2 % of the ratiometric scale factor
out-of-loop". Dual feedback gives **both**: at DC `C-FB-REF` blocks, so no
current flows in `R-FBX-REF`; the amplifier's input current is pA, so none
flows in `R-FB-REF`; the summing node therefore sits at `V(VS)` and the
amplifier forces `V(VS)` = 5.000 V. **The DC error across `R-ISO-REF` is
exactly zero by topology, and its value and tolerance stop mattering.**

Two consequences to keep in mind at layout:

- **`R-FB-REF` is 10 kΩ, `R-FBX-REF` 100 Ω and `C-FB-REF` 1 nF — this
  board's values, not TI's scaled.** TI's Figure 56 prints `R_F` 1 kΩ,
  `R_Fx` 10 kΩ and `C_F` 39 nF (read with TIDU026's glyph key, `ti_rf` in
  `sim/sims.yaml`). What binds here is the handover `1/(2π·R_F·C_F)`, 15.9 kHz:
  it must sit well *above* the 500 Hz breath channel, because our load draws
  10 mA and TI's does not, and above the handover a load-current change appears
  at `VS` across `R_ISO`. `VS` **is** the ratiometric scale factor.
- **The network is robust, which is what makes it a design rather than a tuned
  point.** Against TI's own OPA2197 macromodel the phase margin is
  `riso-ref-phase-margin` across a 200× range of `C_L` (47 nF to 10.1 µF) and
  every tolerance corner `[sim, sim/]`, so X7R DC-bias derating cannot
  destabilise it. **But do not add bulk capacitance at `VS` on the phase margin
  alone.** 10 µF there barely moves the margin and still rings: `|Z_out|` peaks
  near `R_ISO` at 2.5 kHz and a load step swings back through most of its own
  dip for about 3 ms (`sim/`, `step-with-10u-added`). If E13 finds the rail
  wants stiffening against strip PWM, re-run that sim with the part first.
- **As built, `VS` carries about 1.11 µF**: `C-DEC-SENSOR` here plus NXP's
  Figure 3 pair at the sensor, `C-SENSOR-VS-BULK` and `C-SENSOR-VS-HF`
  (`interfaces/breath-sense-link`, fitted 2026-10-01). The margin rises and
  `|Z_out|` at 500 Hz is unchanged; the same ~38 Ω peak moves down to about
  7.6 kHz, so a load step swings back by about 45 % and settles in under
  0.5 ms (`sim/`, `loop-as-built`, `zout-as-built`, `step-as-built`). The
  sensor's draw is steady and the peak sits well above the 500 Hz breath
  channel, so this is recorded, not a defect.

*(The record of the two blockers that closed here on 2026-09-21, and of the two
earlier notes they superseded, is in [`notes.md`](notes.md).)*

## The reference's grade

**`ref5050-grade`: REF5050IDR, the High grade: ±0.05 % initial, 3 ppm/°C**
`[ds REF5050.pdf, SBOS410O Table 4-2 p.3]`. The **A** in an order code is the
*Standard* grade — twice the initial error and 8/3 = 2.7× the drift `[calc]`
— and this reference exists for nothing but scale-factor stability, so the
order code carries no A. Both grades share the SOIC-8 pinout `[ds Table 5-1
p.4]`; a substitution that adds the A fits the footprint and silently
downgrades the breath scale factor.

## The reference's input clamp

**The rail's TVS does not protect the REF5050.** `D-TVS-PWR` on `+12V`
(`carrier/power-entry-instrument`) is sized for the rail and clamps at up to
24.4 V at its rated pulse [ds `LITTELFUSE-SMAJ-SERIES-SMAJ15A.pdf` p.2]. The
REF5050's `VIN` absolute maximum is 18 V [ds `REF5050.pdf` p.5]. The OPA2197
on the same rail has a 40 V absolute maximum [ds `OPA2197.pdf` §6.1] and is
not at risk; the reference is.

So `VIN` is fed through `R-REF-IN` (330 Ω) and held by `D-REF-CLAMP`, a 15 V
zener (onsemi MMSZ5245BT1G):

- **Clamp.** At the TVS's clamp the resistor passes (24.4 − 15.75)/330 =
  26 mA [calc]. The zener's `Vz` is at most 15.75 V and `Zzt` at most 16 Ω
  [ds `ONSEMI-MMSZ5221BT1-SERIES-MMSZ5245BT1G.pdf` p.3], so `VIN` stays at or
  under 15.75 + 0.0175 × 16 ≈ 16.1 V [calc], under 18 V.
- **Normal running.** The REF5050 draws 1.2 mA at most [ds `REF5050.pdf`
  p.8], which drops 0.40 V across the resistor [calc]. `VIN` sits at 11.6 V
  or more, well above the 5.2 V the part needs for a 5 V output [ds p.7].
  The zener is 1.65 V or more above the highest rail and draws only leakage;
  1 µA of it would move `VIN` by 0.33 mV, which the reference's line
  regulation ignores [calc].
- **Where the bypass sits.** The REF5050's `VIN` capacitors (`C-REF-OUT` #1
  and its 100 nF) sit on `REF_VIN`, after the resistor, so the resistor and
  they filter an edge before the zener sees it. Layout keeps them there.

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table. `U-BUF` is not here:
one half of it is this buffer and the other is the breath buffer, so the row
stays with the board page.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-REF-BREATH` | REF5050IDR | 5.000 V for the ratiometric sensor | `ref5050-grade`, settled |
| `R-REF-IN` | 330 Ω 1 % | Series into the REF5050's `VIN`, so the zener can clamp it | this page, `[calc]` |
| `D-REF-CLAMP` | 15 V zener (MMSZ5245BT1G) | Holds `VIN` under the REF5050's 18 V absolute maximum | this page, `[ds]` |
| `C-REF-OUT` | 10 µF ×2 | REF5050 `VIN` bypass and REF5050 `VOUT` load cap — **not** on the buffer's output | `cref-out-node`, settled |
| **`R-FB-REF` / `R-FBX-REF` / `C-FB-REF`** | **10 kΩ / 100 Ω / 1 nF** | **The reference buffer's dual feedback. All three instrument-side and unretrofittable** | `riso-ref-topology`, settled |
