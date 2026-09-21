# Breath excitation reference — schematic

**Status:** Split out of `carrier.md` 2026-09-21 (Phase B). Every line below was
moved verbatim; nothing was reworded and no value was touched in the move.

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

| Node | Dir | Peer | Figure | Note |
|---|---|---|---|---|
| `+12V` | in | [`power-entry-instrument`](../power-entry-instrument/power-entry-instrument.md) | — | REF5050 `VIN` and the buffer half's V+ |
| REF5050 `VOUT` | internal | — | `cref-out-node` | Which side of the buffer `C-REF-OUT` sits on. Settled, and it decides the whole compensation |
| op-amp output | internal | — | `opa2197-output-impedance` | The impedance `R-ISO-REF` is sized against. Specified, not back-solved |
| `VS` | out | `U-BREATH`'s excitation pin, drawn in [`carrier.md`](../carrier.md) §2 | `riso-ref-topology` | Through `R-ISO-REF`. DC feedback is taken **here**, not at the op-amp output — which is what makes the DC error across `R-ISO-REF` zero |
| `AGND-local` | ref | the analog star point, [`carrier.md`](../carrier.md) §2 | — | `C-REF-OUT` and the sensor's 100 nF decoupler return to it |

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

- **`R-FB-REF` is 10 kΩ and not TI's 1 MΩ**, because our load draws 10 mA and
  TI's does not. The handover `1/(2π·R_F·C_F)` must sit *above* the 500 Hz
  breath channel — 15.9 kHz here, against 4.08 Hz at TI's values — or
  load-current changes appear at `VS` across `R_ISO`. `VS` **is** the
  ratiometric scale factor.
- **The network is robust, which is what makes it a design rather than a tuned
  point.** Phase margin stays above 76° across TI's whole published `Zo` range
  and across a 200× range of `C_L` `[sim, A4]`. X7R DC-bias derating cannot
  destabilise it, and if E13 finds the rail wants stiffening against strip PWM,
  **10 µF may be added at `VS` later for 2.5° of margin.** The old topology
  could not have survived that.

*(The record of the two blockers that closed here on 2026-09-21, and of the two
earlier notes they superseded, is in [`notes.md`](notes.md).)*

---

## Component table

*Rows moved verbatim from `carrier.md`'s component table. `U-BUF` is not here:
one half of it is this buffer and the other is the breath buffer, so the row
stays with the board page.*

| Ref | Value | Job | Confidence |
|---|---|---|---|
| `U-REF-BREATH` | REF5050AIDR | 5.000 V for the ratiometric sensor | `[repo]` |
| `C-REF-OUT` | 10 µF ×2 | REF5050 `VIN` bypass and REF5050 `VOUT` load cap — **not** on the buffer's output | `cref-out-node`, settled |
| **`R-FB-REF` / `R-FBX-REF` / `C-FB-REF`** | **10 kΩ / 100 Ω / 1 nF** | **The reference buffer's dual feedback. All three instrument-side and unretrofittable** | `riso-ref-topology`, settled |
