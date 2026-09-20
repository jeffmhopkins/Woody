# B4 — The four modulation CV channels, and the shared DAC

Independent review. Sources read: `README.md`, `ROADMAP.md`, `docs/decisions/0001`–`0014`,
`docs/reference/latency-budget.md`, `docs/reference/ks33-geometry.md`, `hardware/bom.csv`,
`firmware/README.md`, `config/key-layout.yaml`. `docs/review/` and `docs/log/` deliberately
not read.

## Datasheet provenance

Network egress to ti.com was blocked, so no datasheet PDF was read directly. Every
datasheet claim below is marked **[VERIFIED]** (corroborated from TI product/forum/driver
sources reachable through the proxy, named at the point of use), or **[MEMORY]** (working
from recollection; the falsification test is given).

Verified this session:

- DAC8568 grade letters: **gain = 1 for A/B grades, gain = 2 for C/D grades**; **power-on
  and software reset to zero scale for A and C, midscale for B and D**. Internal reference
  is 2.5 V and is **disabled by default**; full-scale output is therefore 2.5 V (A/B) or
  5 V (C/D). Source: TI DAC8568 product page and DAC7568/8168/8568 datasheet text surfaced
  in search, plus the TI E2E thread on DAC8568C/D bipolar operation. **[VERIFIED]**
- DAC8568 has a **clear-code register** that determines what the `CLR` pin does, and it
  must be written after power-up. Source: TI E2E "dac8568 : CLR Pin & Software Reset".
  **[VERIFIED]**
- DAC8568 command set includes `WriteToInputRegister` (no output change),
  `UpdateRegister` (software LDAC), `WriteToChannelAndUpdateAllRegisters`,
  `WriteToLDACRegister` (LDAC mask), `WriteToClearCodeRegister`, `SoftwareReset`.
  Source: the `dac8568` Rust driver's control-nibble table, which mirrors the datasheet's
  command table. **[VERIFIED]** — the 32-bit frame length is **[MEMORY]**.
- OPA2197: 36 V, RRIO, GBW 10 MHz, slew 20 V/µs, e_n 5.5 nV/√Hz at 1 kHz, V_OS ±25 µV typ,
  output ±65 mA. Source: TI OPA2197 product page. **[VERIFIED]**. Its output-swing-from-rail
  figure (I use ~200 mV at light load) is **[MEMORY]**.

---

# Findings

## 1. The mod offset is written once at boot, so any `CLR` event parks all four mod outputs near +11.4 V, indefinitely and undetectably

**Severity: SHOWSTOPPER** (as written; the fix is firmware-only and free)

**Where.** ADR 0006, "Channels do not share an update rate":

> | Mod offset | **written once at boot** | The shared 2.5 V reference point |

against ADR 0004, "A stuck CV is worse than a dead one":

> **Assert `CLR` at the module when no valid frame has arrived for N milliseconds.**
> … an A/C grade part clears to zero scale, which parks pitch subsonic and the mod
> channels at 0 V

and ADR 0004, on the deleted return path:

> MISO goes, and with it the planned module-ID line.

**Why.** `CLR` is a global asynchronous clear: it clears *all eight* DAC registers,
including channel 7, the shared mod offset. While `CLR` is asserted the identity the ADR
relies on holds and the mods sit at 0 V:

```
Vout = 4 × (Vdac − Voffset) = 4 × (0 − 0) = 0 V        ✓ correct
```

The problem is the *release*. Firmware resumes writing mod codes at 4 kHz and never
rewrites channel 7, because the design says it is written once. With `Voffset = 0`:

```
Vout = 4 × Vdac
```

Take the ADR's own stated default range, 0–8 V. That range occupies `Vdac = 2.5 … 4.5 V`.
With the offset gone:

```
Vout = 4 × 2.5 = 10.0 V  …  4 × 4.5 = 18.0 V
```

clipped by the output stage at

```
+12 V rail − 0.35 V (1N5817 at ~400 mA) = +11.65 V
                   − ~0.20 V (OPA2197 swing from rail, light load)  = +11.45 V
```

so **all four mod jacks sit at a hard +11.45 V DC** (11.34 V after the 1 kΩ into a 100 kΩ
input). Into a VCA that is fully open; into a 1 V/oct input that is 9.4 octaves up. It is
loud, indefinite, and unresponsive — precisely the failure ADR 0004 names as the worst one
available, and the watchdog that exists to prevent it is the thing that causes it.

Two things make this worse than a one-off:

- **The trigger is routine.** `CLR` fires on N milliseconds of frame loss with N well under
  a second. The umbilical is a **consumable** by explicit decision ("replace the lead at the
  first sign of intermittency"), so momentary frame loss is a designed-for event, not an
  exotic one. Each occurrence leaves the instrument in the stuck-at-rail state until someone
  power-cycles the module.
- **Nothing can detect it.** MISO is deleted; there is no conductor from module to
  instrument at all. The instrument — the only thing in the system with a display — cannot
  observe a single bit of module state. So "notice and re-init" is not available; only
  unconditional periodic refresh is.

There is a second member of the same class: the **clear-code register** is itself volatile,
firmware-written state (**[VERIFIED]** — TI E2E: "put the desired value into the clear code
register after power up"), as is the **internal-reference enable**, which ADR 0006 already
flags as disabled by default. If a software reset or a glitched write disturbs the
reference-enable bit, every output goes to 0 V and firmware keeps writing codes into a dead
DAC — the "board that looks dead" failure ADR 0006 warns about, arriving mid-session
instead of at bring-up.

**Proposal.**

1. Make it a stated rule: **the module holds no state that firmware does not refresh.**
   Rewrite, on a slow cycle, all four pieces of module-side state: internal-reference
   enable, clear-code register, LDAC mask, and the channel-7 offset.
2. Cost check against the published loop budget. The latency budget already books
   *six* DAC channels per 250 µs pass at 16 µs each = 96 µs, but only **five** are actually
   written per pass (pitch + 4 mods). Adding the offset refresh to every pass brings the
   real count to exactly the six already budgeted. **The fix is free against a number the
   project has already published.** A 40 Hz refresh (once per 100 passes) is free twice over.
3. Refresh the offset *atomically* with the mod codes — see finding 2.

**Confidence: high** that the failure exists as documented; **high** that no detection path
exists; **[VERIFIED]** that `CLR` is global and that the clear-code register is volatile.

**What would falsify it.** At E7, with the module on the bench: write the offset and a set
of mod codes, confirm the outputs; pulse `CLR` low and release it; continue writing only mod
codes. If the outputs return to their commanded values, the DAC is retaining channel 7
through `CLR` and this finding collapses to the reference-enable half. (I expect them to pin
high.) Second test: hold `CLR` low and attempt the reference-enable write, then release —
if the write is swallowed, the boot-time race in the proposal is real too.

---

## 2. The offset and the four mod codes must move together, and nothing in the design makes them; `LDAC` is unmentioned in every document

**Severity: MAJOR**

**Where.** ADR 0006:

> **The 2.5 V reference point comes from a buffered DAC channel** … One buffered channel
> serves all four mod channels

and ADR 0006's power-on table, which claims:

> | **Mod 1–4** | **Exactly 0 V** | Both terms of the difference are zero |

The `LDAC` pin appears in no ADR and in no BOM line. `hardware/bom.csv` lists `U-DAC` with
notes on grade, populated channels and AVDD, and nothing about `LDAC`.

**Why.** Putting the offset inside the signal path makes `Vout` a function of *two* DAC
registers. Any interval in which one has been updated and the other has not is an interval
of full-scale error on four outputs at once. The power-on table is true only for the window
*before firmware acts*, which is the least interesting window. Once firmware starts, there
are exactly two orderings and both are bad:

| Boot order | Output during the gap |
|---|---|
| offset (ch 7) first, then mod codes | `4 × (0 − 2.5)` = **−10 V** on all four |
| mod codes first, then offset | `4 × (2.5…4.5 − 0)` = **+10…+18 V**, clipped at **+11.45 V** |

Duration of the gap: 32-bit DAC frames **[MEMORY]**, four mod writes plus overhead. At
2 MHz that is 4 × 16 µs = 64 µs; at the 0.6 MHz figure ADR 0004 quotes, 4 × 53 µs = 212 µs.
Through the specified single-pole 2 kHz reconstruction filter (τ = 1/(2π·2000) = 79.6 µs)
a −10 V pulse of width T reaches the jack at `10 × (1 − e^(−T/τ))`:

```
T =  64 µs →  10 × (1 − e^−0.80) = 5.5 V
T = 212 µs →  10 × (1 − e^−2.66) = 9.3 V
```

So **every power-on and every watchdog recovery puts a 5.5–9.3 V, ~0.1–0.2 ms spike on four
modulation outputs into a live rack.** Not damaging; audible as a thump through every
destination, every time.

**Proposal.** Use the mechanism the part already has, at zero hardware cost:

- Tie `LDAC` **high** and drive updates from the software LDAC path: `WriteToInputRegister`
  (command 0) for the offset and each mod channel, then one `UpdateRegister` (command 1)
  to move them together. Alternatively set the LDAC mask register (command 6) so those five
  channels are held, and let a final `WriteToChannelAndUpdateAllRegisters` (command 2) commit.
  All four commands are **[VERIFIED]** present in the part's command set.
- Decide the `LDAC` pin's state explicitly in the schematic and put it in the BOM notes.
  A 16-pin part with two control pins where the documents discuss only one is a pin that
  gets left floating on a hand-assembled board.
- Same mechanism makes finding 1's periodic offset refresh glitch-free.
- One consequence to absorb: five output buffers now settle simultaneously rather than
  staggered across the pass. Order-of-magnitude: five buffers slewing ~5 V in ~7 µs
  **[MEMORY: DAC8568 settling ≈ 7 µs]** at a few mA each ≈ 10 mA for 7 µs; into the LM317's
  1 µF output cap that is ΔV = I·Δt/C = 10 mA × 7 µs / 1 µF = **70 mV of AVDD dip**.
  Raise `C-REG-ADJ`'s output member from 1 µF to 10 µF and it is 7 mV. Cheap insurance;
  the staggered-update scheme currently gets this benefit by accident.

**Confidence: high** on the two orderings and the arithmetic; **high** that `LDAC` is
undocumented; **medium** on the exact spike duration, which depends on the SPI clock
(see finding 5).

**What would falsify it.** Scope all four mod jacks through a power-on at E7/E10 with the
real boot sequence. No visible transient means firmware happened to use input-register
writes already, and the finding becomes a documentation fix rather than a behaviour fix.

---

## 3. "A or C grade" is not a choice — the A grade has gain 1, and the whole 0–5 V DAC span the analog design is built on disappears

**Severity: MAJOR**

**Where.** ADR 0006:

> So specify an **A or C grade** part — zero-scale reset

`hardware/bom.csv`:

> `U-DAC … DAC8568C (or A grade) - full orderable P/N required … A/C grade resets to ZERO
> scale`

against ADR 0004:

> **DAC8568 at internal reference × 2 spans 0–5 V**

> | DAC VDD | Output span | Gain the scaling stage must supply |
> | **5 V** | **0–5 V (ref × 2)** | **1.8×** |

**Why.** The grade letter carries **two** independent properties, not one. **[VERIFIED]**:

| Grade | Reference gain | Full scale (internal 2.5 V ref) | Reset value |
|---|---|---|---|
| A | **1** | **2.5 V** | zero scale |
| B | 1 | 2.5 V | midscale |
| **C** | **2** | **5.0 V** | **zero scale** |
| D | 2 | 5.0 V | midscale |

ADR 0006 read the reset column and treated the letter as though that were all it encoded.
It is not: **only the C grade satisfies both constraints.** An A-grade part would reset to
zero scale as wanted and then deliver a 0–2.5 V span, which breaks both output stages:

- **Pitch** would need gain 3.6× instead of 1.8× for the −2…+7 V span — exactly the
  penalty ADR 0004 spent a table rejecting ("everything the scaling stage amplifies … is
  amplified by that factor. **5 V halves it**"). Op-amp offset, drift and noise all double
  in the one channel where they are audible.
- **Mod 1–4** would need `Vout = 8 × (Vdac − 1.25)` for ±10 V. Gain 8, and the ×8 applies
  to the DAC's noise and INL and to the offset channel's error as well.

It also explains a number the ADR quotes without sourcing: its drift table uses "DAC
internal reference, 5 ppm/°C", which matches the C/D grade; a search summary (not the
datasheet itself) suggests A/B carry a looser full-scale drift figure. So the ADR's own
precision arithmetic is already C-grade arithmetic.

Separately, ADR 0006's instruction — "**Specify the full orderable part number in the
BOM**, not 'DAC8568'. The grade letter is the whole decision and it is invisible in the
generic name" — is correct, is the single best line in that ADR, and **is still unfulfilled
in the BOM**, which says "full orderable P/N required" as a note to self.

**Proposal.** Strike "(or A grade)" everywhere. Specify **`DAC8568ICPW`** (TSSOP-16, tube)
or `DAC8568ICPWR` (tape) — confirm the exact suffix against TI's ordering table, which I
could not reach; the `C` is the load-bearing character. Add a one-line note in the BOM
stating *why*: "C = internal reference gain 2 (0–5 V FS) **and** zero-scale reset. A grade
is gain 1 and halves every output span."

**Confidence: high.** The grade/gain and grade/reset mappings are **[VERIFIED]** from two
independent sources this session.

**What would falsify it.** Read TI's DAC8568 ordering-information table. If A and C differ
only in reset value and the gain is set by a register rather than the grade, the finding
falls. (The E2E thread title — "Bipolar operation with DAC8568**C/D**" — is itself evidence
the gain lives in the letter.)

---

## 4. The reconstruction filter exists only in prose, and the single pole specified puts just 6.3 dB on the image the ADR sized the update rate around

**Severity: MAJOR**

**Where.** ADR 0006:

> **Give the mod channels a lower reconstruction corner than pitch — around 2 kHz.** Their
> sources top out near 400 Hz, so the corner costs nothing in signal and puts real
> attenuation on the image.

`hardware/bom.csv` contains `R-OUT-PROT` (1 kΩ × 6), `C-DECOUPLE` (100 nF × 10, "one per
supply pin"), and **no capacitor of any kind for any CV output filter** — not for the four
mod channels, not for breath, not for pitch. No R or C value for any filter appears in any
document in the repository.

**Why — the arithmetic the ADR stopped one step short of.** Zero-order hold at
f_s = 4 kHz puts the first image at `f_s − f_in`, shaped by `sinc(f/f_s)`. Relative to the
reproduced fundamental:

```
image/fundamental = [ sin(π·f_img/f_s)/(π·f_img/f_s) ] / [ sin(π·f_in/f_s)/(π·f_in/f_s) ]

f_in = 400 Hz, f_img = 3600 Hz:
   sin(0.31416)/2.8274 = 0.10930        (−19.23 dB absolute — the ADR's own number ✓)
   sin(0.31416)/0.31416 = 0.98363       (−0.14 dB)
   ratio = 0.11112                      → −19.08 dB
```

A **single** real pole at 2 kHz then contributes:

```
at 3600 Hz: 1/√(1 + (3.6/2)²) = 1/2.0591 = 0.4856  → −6.27 dB
at  400 Hz: 1/√(1 + (0.4/2)²) = 0.9806            → −0.17 dB
```

Net image at the jack: **−19.08 − 6.27 + 0.17 = −25.2 dB, i.e. 5.5 % of the modulation
depth.** "Real attenuation" is 6.3 dB. The ADR rejected the 2 kHz update rate because
−12.6 dB was unacceptable and then accepted −25.2 dB without computing it.

**Is it audible?** It depends entirely on the source's real bandwidth, and the ADR's
400 Hz is an assumption no source in this instrument justifies:

| Source content | Image freq | ZOH, rel. | 1 pole @2 kHz | Net | As % of depth |
|---|---|---|---|---|---|
| 400 Hz (ADR's assumption) | 3600 Hz | −19.1 dB | −6.3 dB | **−25.2 dB** | 5.5 % |
| 160 Hz (digitised breath — the fastest real source; sensor corner ~159 Hz) | 3840 Hz | −27.6 dB | −6.7 dB | **−34.3 dB** | 1.9 % |
| 50 Hz (IMU tilt/roll gesture) | 3950 Hz | −37.9 dB | −6.3 dB | **−44.2 dB** | 0.6 % |
| 20 Hz | 3980 Hz | −46.0 dB | −6.3 dB | −52.3 dB | 0.2 % |

Verdict, stated plainly because the brief asks for it:

- **Into a VCA at ±5 V depth from a breath-derived mod channel:** 1.9 % amplitude ripple at
  3.84 kHz is amplitude modulation of index m = 0.019, giving sidebands at m/2 = **−40 dB**
  either side of every partial, at an *inharmonic* 3.84 kHz offset and near the ear's
  most sensitive region. Audible as a faint metallic ring on sustained quiet material.
  At the ADR's assumed 400 Hz the same figure is **−31 dB**, which is plainly audible.
- **Into an exponential FM or 1 V/oct input:** 0.28 V of image at 3.6 kHz on a 440 Hz
  carrier gives peak deviation ≈ 94 Hz at f_m = 3600 Hz, modulation index β = 0.026,
  first sidebands at β/2 = **−38 dB**. Audible but not gross.
- **From gesture sources below ~50 Hz:** inaudible by a wide margin. The mod channels are
  safe for the thing they will mostly do, and the ADR's *conclusion* for those sources is
  right.

So the honest summary is: the update rate was chosen correctly, and the filter that is
supposed to finish the job is (a) not on the parts list and (b) one pole where two are
needed if the 400 Hz assumption is ever true.

**Proposal.** Second order, using parts already in the BOM, for four capacitors:

1. **Pole 1, at the DAC-side summing node.** `R-OPAMP-IN` (1 kΩ, already specified for
   supply-sequencing clamp current) plus the gain network's input resistor already form a
   source impedance at the op-amp's non-inverting node. For a 10 k/40 k network that is
   (1 k + 10 k) ∥ 40 k = 8.63 kΩ; **10 nF C0G to AGND gives 1.84 kHz** and costs nothing
   in DC accuracy because it sits outside the feedback path. It also swallows DAC
   code-change glitch energy *before* the ×4 gain, which the present single-pole scheme
   amplifies first and filters second.
2. **Pole 2, at the jack**, formed with `R-OUT-PROT`: 1 kΩ + **82 nF → 1.94 kHz**.
   **Specify C0G/NP0 or film, not X7R.** This capacitor carries the full ±10 V output
   swing, and an 0805 X7R's DC-bias coefficient can lose 20–40 % of its capacitance at
   10 V, moving the corner 30 % and making it signal-dependent. 82 nF C0G does not exist
   in 0805; use a film part — through-hole is explicitly acceptable in this project's
   package policy and the module is not space-constrained on the PCB, only on the panel.
3. Two poles at ~1.9 kHz give **−12.5 dB** at 3.6 kHz → net image **−31.3 dB** (2.7 %),
   and **−41 dB** (0.9 %) against the realistic 160 Hz source.
4. **The corner should be argued from the real source bandwidth, not from 2 kHz.** Two
   poles at 800 Hz give net **−55 dB** at 3.84 kHz and cost 2/(2π·800) = **398 µs** of
   group delay. **There is no latency budget entry for the mod path at all** — every table
   in `latency-budget.md` covers breath, keys or pitch — so that delay costs nothing that
   has been written down. If a gate assignment is wanted with a crisp edge, ~1.5 kHz
   two-pole is the compromise: net −35 dB, 10–90 % rise ≈ 0.29 ms, still well inside any
   Schmitt-triggered Eurorack input.
5. Regardless of corner: **put six capacitors in the BOM with values.** A project that
   specifies the LM317 divider to 240 R / 768 R should not leave the component that
   implements its own headline noise argument as the phrase "~2 kHz".

**Confidence: high** on the arithmetic (self-contained); **high** that the parts are absent
from the BOM; **medium** on the audibility verdicts, which depend on the destination.

**What would falsify it.** At E10, drive a mod channel with a 400 Hz (and a 160 Hz) sine
from the firmware source path at full depth and take an FFT at the jack. If the component
at f_s − f_in is below −40 dBc with the as-built filter, the single pole is sufficient and
this reduces to the BOM omission.

---

## 5. The SPI clock the 4 kHz loop actually requires is ~1.3–2 MHz; ADR 0004 still says 0.6–1 MHz, and E11 is written to validate the wrong number

**Severity: MAJOR**

**Where.** ADR 0004 gives three different clocks in one document:

> ```
> SCLK, MOSI, CS      SPI to the DAC, ~2 MHz
> ```
> ```
> SCLK      / DIG_GND     SPI to the DAC, ~1 MHz
> ```
> | **Breath analog, 5 channels at 2 kHz** | **0.32 Mbit/s** | **~0.6 MHz** |

ROADMAP E11:

> Umbilical link | SPI (**~0.6 MHz**) and the analog breath pair over the real cable at length

**Why.** ADR 0004's bandwidth table was computed at **2 kHz** per channel. ADR 0006 then
doubled it and said so explicitly — "The table used to say 2 kHz and it was wrong twice
over" — and **ADR 0004's arithmetic was never updated.** Redo it at 4 kHz, with 32-bit DAC
frames **[MEMORY]**:

```
5 channels × 32 bits × 4 kHz = 0.64 Mbit/s     (not 0.32)
at ADR 0004's own "50 % bus use" rule          → 1.28 MHz
with the finding-1 offset refresh, 6 channels  → 0.77 Mbit/s → 1.54 MHz
```

And the loop budget only closes at the top of that range. One pass at 250 µs:

| SCLK | 5 DAC words | + ADC 24 µs + keys 16 µs | Duty |
|---|---|---|---|
| 0.6 MHz | 267 µs | 307 µs | **123 % — does not close** |
| 1 MHz | 160 µs | 200 µs | 80 % |
| 2 MHz | 80 µs | 120 µs | 48 % |

The latency budget's own figures — "six DAC channels 96 µs", "**136 µs** … 54 % duty" —
are 16 µs per 32-bit word, i.e. **2.0 MHz**. So the design has already silently committed
to 2 MHz in the one document that does the timing, while the connector ADR advertises
0.6 MHz and the milestone that proves the cable tests 0.6 MHz.

The consequence is not academic. ADR 0004 retires RS-485 on the strength of:

> Plain single-ended SPI at well under 1 MHz over twisted pair is unremarkable.
> **RS-485 returns to contingency status.**

At 2 MHz over 2 m that is probably still true, but the stated reason no longer holds, and
E11 as written would pass at 0.6 MHz and tell you nothing about the clock the firmware
will use. Setup/hold margin scales directly with the period: 833 ns of half-cycle at
0.6 MHz versus 250 ns at 2 MHz.

**Proposal.** Fix one number, 2 MHz, in ADR 0004's conductor table, ADR 0004's bandwidth
table, and E11. Rerun E11 at 2 MHz **and at 4 MHz** to find the margin rather than merely
confirming the operating point. Re-state the RS-485 retirement against 2 MHz. If the
bandwidth table is kept, correct 0.32 → 0.64 Mbit/s.

**Confidence: high** on the internal inconsistency and on the 0.6 MHz case not closing;
**medium** on 32-bit frames (**[MEMORY]** — but the latency budget's 16 µs/channel figure
is only consistent with 32 bits at 2 MHz, which is corroboration from inside the project).

**What would falsify it.** Logic analyser at the module end during a real 4 kHz loop at
E11: measure the actual bits per pass and the actual clock. If the firmware sends 24-bit
frames or updates the mods at 2 kHz after all, the numbers change.

---

## 6. Series termination is fitted on the one umbilical line where ringing is harmless and omitted from the two where it corrupts a DAC word

**Severity: MAJOR**

**Where.** ADR 0004:

> **220 Ω in series on MOSI at the driving end.** Source termination on **the one line that
> runs the full umbilical carrying data.**

`hardware/bom.csv`: `R-MOSI-SER`, 220 Ω, **qty 1**.

Meanwhile the same project, for the key chain, gets it right:

> `R-TERM-CHAIN … 33-68R … Source termination at the driving end` — and the ADR 0001 note
> "faster edges into an unterminated loom ring."

**Why.** The premise is factually wrong: **SCLK and CS run the full umbilical too**, on
pins 7/8 and 4/5 of the same T568B mapping ADR 0004 specifies. And of the three, MOSI is
the line where a reflection matters *least* — it is sampled once per bit at the clock edge,
long after the line has settled. SCLK is the line where a reflection matters **most**: a
double-clocked edge shifts the entire 32-bit word by one bit, which does not corrupt one
channel's LSB, it writes a **different command nibble to a different channel address**.
With the mod offset living in channel 7, a single double-clock can write a garbage value
into the offset and produce finding 1's stuck-at-rail state without any `CLR` involvement.
CS is the framing line, and ADR 0004's own stated fear is "a stray edge on CS latches a
garbage word into the pitch DAC."

Is the cable a transmission line here? Yes: 2 m at ~0.65 c is t_prop = 10.3 ns one way,
so the transmission-line threshold (edge rate < 2·t_prop = 20.6 ns) is met by any ESP32-S3
GPIO, whose rise time is a few nanoseconds. The far end is effectively open — a 74AHCT125
input plus a 10 kΩ pull — so reflection is total.

The 220 Ω value is also wrong for the line it *is* on. With Z0 ≈ 100 Ω and an ESP32-S3
output impedance of ~30 Ω:

```
first incident step at the far end (doubled at the open end):
   2 × 3.3 V × 100/(100 + 220 + 30) = 2 × 0.94 V = 1.89 V
```

against the 74AHCT125's TTL V_IH of 2.0 V. The line sits **110 mV below threshold for a
full round trip (20.6 ns)** and staircases to ~2.7 V, ~3.05 V, ~3.16 V over the next three
trips. ADR 0004 itself notes the part is "a plain buffer, not a Schmitt trigger". On MOSI
this is survivable; on SCLK it would be a double-clock generator.

**Proposal.**

- Put source termination on **SCLK and CS as well** — two more 0805 resistors, ~$0.02.
- Size it properly: **68–82 Ω**, not 220 Ω, so that R_s + Z_driver ≈ Z0 and the far end
  reaches full level in one round trip rather than staircasing through the threshold.
  Change the MOSI part to match.
- Free belt-and-braces: reduce the ESP32-S3's GPIO drive strength on these three pins
  (it is configurable) to slow the edges below the transmission-line threshold.
- Keep ADR 0004's note that a 74AHCT14 is the escalation if E11 says so, but note that
  correct source termination is the cheaper fix to try first.

**Confidence: high** that SCLK and CS traverse the cable and are unterminated;
**high** on the transmission-line threshold; **medium** on the exact staircase levels,
which depend on the real GPIO output impedance and the cable's Z0.

**What would falsify it.** E11, already scheduled: scope SCLK at the **module end**, at
full cable length, at 2 MHz, and look for a second threshold crossing on any edge. Count
DAC frame errors over an hour with a known test pattern — the project already knows this
technique, it is the key-chain marker pattern from ADR 0001, and the same idea should be
applied to the DAC link (which, with no MISO, is the only way to catch it at all).

---

## 7. `R-SPI-PULL` qty 3 defines only one side of the level shifter; the DAC's own control inputs float in the state the design calls normal

**Severity: MAJOR**

**Where.** ADR 0004, "The module's normal 'off' state has the SPI bus floating":

> the ordinary powered-down state is: **module alive, DAC alive, and SCLK / MOSI / CS
> floating** at the level shifter's inputs … Floating CMOS inputs oscillate and draw
> crowbar current — inside the precision analog box
>
> - **CS pulled to +5 V; SCLK and MOSI pulled to ground**, at the module end.
> - **Gate the 74AHCT125's output enable from umbilical +12 V presence**

`hardware/bom.csv`: `R-SPI-PULL … 10k … qty 3`.

**Why.** Three resistors can sit on only one side of the buffer, and the design needs both:

- **Buffer inputs (umbilical side)** need defining, or the AHCT125's own inputs float and
  it oscillates and draws crowbar current — the stated reason for the pulls.
- **Buffer outputs (DAC side)** need defining *independently*, because the OE gating puts
  those outputs into **Hi-Z** in exactly the same state. A tri-stated buffer does not pass
  its input pulls through. So in the normal off state — which ADR 0004 correctly identifies
  as "the state the instrument spends most of its life in" — the DAC8568's `SYNC`, `SCLK`
  and `DIN` are floating on their own, with the DAC powered from its LM317, inside the
  precision box, continuously, for years.

The two stated harms both land on the DAC, not the buffer: crowbar current in the DAC's
input structures (self-heating and die-level noise injection next to a 2 ppm/°C reference),
and the framing hazard — though I will be honest about the second: with the umbilical
unplugged, the floating node is ~1 cm of PCB trace, not a 2 m antenna, and latching a word
requires 32 clean clock edges between two `SYNC` transitions. The probability is low; the
crowbar argument is the solid one, and it is the project's own argument.

**Proposal.** Six resistors, not three: 10 kΩ on both sides of all three lines. Mark the
BOM line accordingly. If a gate has to be saved, the DAC side is the one that matters —
that is where the precision analog and the reference live.

**Confidence: high** that qty 3 covers one side only and that OE gating tri-states the
outputs; **medium** on how much the crowbar current actually costs.

**What would falsify it.** At E6/E7, with the panel switch off and the umbilical
unplugged: scope the DAC's `SYNC`, `SCLK` and `DIN` pins and measure the LM317's output
current. Clean rails and quiet pins mean the DAC's inputs are being held somewhere by
leakage and the finding is cosmetic.

---

## 8. The module's internal ground topology is unspecified, and the umbilical lands 320–430 mA of pulsed instrument return current on the same connector as the analog reference

**Severity: MAJOR**

**Where.** ADR 0003 spends several pages on exactly this problem *in the cable*:

> **`AGND` carries no power current** — it is a sense reference only, which is the whole
> reason the analog channel survives the cable

> | Instrument draw | Offset on a shared ground |
> | 350 mA | **58.9 mV** |
> It moves with display brightness, LED animation and WiFi bursts

and then no document says where `PWR_GND`, `DIG_GND`, `AGND`, the jack sleeves, the DAC's
GND and the bus header's ground meet **inside the module**. ADR 0004's power tree shows
only the positive rails.

**Why.** Every CV output in this module is measured by its destination against the **jack
sleeve**. Any voltage developed between the jack sleeve node and the node the DAC and the
gain stages reference appears 1:1 on all six outputs, gain and calibration notwithstanding.

The module carries a current the ADRs elsewhere describe vividly: the whole instrument's
return — "~320 mA (estimated, and a review put it nearer 410–430 mA)" — with, per ADR 0014,
a 200–400 mA component switching at the WS2815's ~2 kHz PWM rate, plus WiFi bursts. That
current enters on the etherCON's `PWR_GND` pair and must reach the bus header's ground.
Whatever copper it shares with the analog reference becomes a signal source:

```
1 cm of 10-mil, 1 oz trace:  R = 1.7e-8 × 0.01 / (0.254e-3 × 35e-6) = 19 mΩ
300 mA pp × 20 mΩ = 6 mV pp at ~2 kHz, on every output
```

On the mod channels 6 mV is 0.03 % of span — irrelevant. On **pitch** it is
6 mV / 83.3 mV per semitone = **7.2 cents of 2 kHz warble**, inside the pitch channel's
deliberately fast 15 kHz filter, audible as a buzz on the VCO rather than as a tuning
error. And it is exactly the artefact — light show on the CV — that the entire umbilical
grounding scheme was designed to prevent, arriving on the other side of the connector.

On a solid ground pour with the etherCON's `PWR_GND` landing near the bus header, the
shared impedance is more like 1 mΩ and the figure falls to 0.3 mV / 0.36 cents, which is
fine. **The point is that this is a layout decision nobody has written down, the good
outcome and the bad outcome differ by 20×, and it is not retrofittable.**

**Proposal.** State the topology in ADR 0004 alongside the power tree:

- `PWR_GND` runs from the etherCON to the bus header's ground pins as a dedicated wide
  pour that **no analog reference shares**, so the instrument's return current never
  traverses analog copper.
- `AGND`, `DIG_GND`, the analog ground and the jack sleeve ground join at **one point**,
  at that same bus-header node, with the jack sleeves on the analog side of the join.
- The mod offset buffer's output stars to the four difference amplifiers rather than
  daisy-chaining: 1.6 mA of code-dependent current (see "correct", below) through 20 mΩ
  of chained trace is 32 µV × gain 4 = 128 µV of channel-to-channel crosstalk, comparable
  to the 305 µV LSB. A star makes it disappear.
- Add the measurement below to E11 and M8.

**Confidence: high** that the topology is unspecified; **medium-high** that it matters at
the stated currents; **high** on the arithmetic.

**What would falsify it.** ROADMAP already schedules "Breath channel noise — scope the
breath jack while sweeping display brightness, LED animation and a WiFi burst". **Extend
that test to the pitch jack and all four mod jacks, with the outputs commanded static.**
If nothing appears on pitch at the µV level, the ground layout is fine and this is a
documentation gap only. This is also the one test that should be repeated at M8, because
the LED strips do not exist at E11.

---

## 9. ±10 V is not reachable; the mod range is bounded by the DAC's inability to reach its own rails, not by the op-amp headroom the ADR checked

**Severity: MINOR**

**Where.** ADR 0006 states both of these, three sections apart:

> ```
> Vout = 4 × (Vdac − 2.5 V)
>   Vdac 0.00 V  →  −10 V
>   Vdac 5.00 V  →  +10 V
> ```
> **Headroom is ample.** ±12 V rails less ~0.35 V of Schottky leaves ±11.65 V, and an
> OPA2197 reaches ~±11.45 V — 1.45 V of margin at ±10 V.

> - **Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span.** That leaves
>   250 mV of headroom at both rails — the DAC8568 at AVDD = 5 V cannot reliably swing to
>   its own supply

**Why.** The second rule is a property of the part, not a choice about pitch, and there is
only one part. Apply it to the mod topology:

```
Vdac 0.25 V → 4 × (0.25 − 2.5) = −9.0 V
Vdac 4.75 V → 4 × (4.75 − 2.5) = +9.0 V
```

**The stage spans ±9 V, not ±10 V**, and two of the five advertised range presets —
"0–10 V" and "±10 V" — are unreachable. (0–8 V needs `Vdac` 2.5–4.5 V and ±5 V needs
1.25–3.75 V; both are comfortably inside the window, so the presets that matter are fine.)

The interesting part is that the ADR checks the headroom that is *not* binding. Verifying
its numbers: at ~430 mA the 1N5817 drops ~0.35–0.40 V **[MEMORY]** giving +11.6 V; the
−12 V rail at only ~40 mA drops ~0.2 V giving −11.8 V; OPA2197 swing from rail at light
load ~0.2 V **[MEMORY]** → ±11.4 V available against a worst case of 10 V plus ±2 % of
resistor gain error = 10.2 V. **1.2 V of margin. The rail headroom is genuinely fine and
the ADR is right about it.** What actually limits the range is 250 mV at the DAC, multiplied
by four.

**Proposal.** Either (a) accept ±9 V, delete "0–10 V" and "±10 V" from the preset list,
and say so — nothing in the design needs more, since the ADR itself calls ±10 V "headroom,
not a default"; or (b) set the gain to 40/9 = 4.44 (e.g. 44.2 k / 10 k, 1 %) so that the
0.25–4.75 V window maps exactly to ±10 V. Option (b) is free — the mod channels use
ordinary discretes, not the 1:4 matched network, so the convenient ratio buys nothing here.
Either way, **state the DAC window rule once, globally, rather than inside the pitch
section**, because it silently governs every channel.

**Confidence: high** on the contradiction; **medium** on the exact usable window, which is
a datasheet/measurement question the project has already scheduled.

**What would falsify it.** ROADMAP already lists "**DAC saturation vs AVDD** — record the
actual saturation code at the actual rail" at E7. If the DAC8568C at AVDD = 5.25 V is
linear to within 50 mV of 0 V and 5.0 V, the window is 0.05–4.95 V and the range is ±9.8 V.
Run that measurement at both ends, not just the top.

---

## 10. "Four mod channels trimmed" (E10) has neither trimmers nor a calibration path

**Severity: MINOR**

**Where.** ROADMAP E10:

> Analog breath stage … Four mod channels **trimmed**

against ADR 0006:

> **Mod channels stay trimmer-free.** They need to be linear and repeatable, not musically
> accurate; firmware scaling is sufficient there

and the BOM, where `TRIM-PITCH` is qty **2** (pitch only), and where no resistor line item
exists for the mod gain networks at all — "ordinary 1 % discretes" appears only in prose.

**Why.** There is nothing to turn, and no stated firmware mechanism either: ADR 0006 gives
the mod channels "source, scale, offset, curve and slew" as *routing* parameters, not as
per-channel hardware corrections, and the NVS calibration blob is described only for pitch.
So "trimmed" at E10 is not an executable milestone.

What the uncorrected hardware delivers, from 1 % discretes:

- **Gain:** a ratio of two 1 % parts → **±2 % worst case**, ±1.4 % RSS. On a 0–8 V preset
  that is ±160 mV of scale error, and up to **320 mV of spread between two mod channels**
  commanded identically.
- **Zero:** a difference amplifier's common-mode rejection with gain G and tolerance ε is
  CMRR ≈ (1 + G)/(4ε) = 5/0.04 = 125 → **41.9 dB**. (Sanity check: the same formula gives
  the textbook 34 dB for a unity-gain difference amp with 1 % resistors.) The common-mode
  here is the 2.5 V offset, so the zero error is **2.5 V / 125 = 20 mV** at the output.

For "a VCA gets a bit more or less" that is all fine, and ADR 0006 is right that nobody's
ear cares. It stops being fine in two named cases the design explicitly permits: two mod
channels expected to match (a stereo pair, or two VCAs), and a mod channel assigned to a
1 V/oct destination, where 20 mV is 24 cents of fixed detune and 2 % of gain is 24 cents
per octave.

**Proposal.** Eight floats. At E10, measure each mod channel's actual gain and zero with
the bench DMM (two points per channel) and store them in the same NVS blob as the pitch
calibration, behind the same CRC. Firmware already has to scale these channels; folding a
per-channel `a` and `b` into that multiply is free at runtime. Then rewrite E10's "trimmed"
as "measured and stored", which is a thing someone can actually do and check.

**Confidence: high.** The gap is between two documents and the arithmetic is standard.

**What would falsify it.** Measure four as-built channels at E10. If the spread is under
0.5 %, the resistors happened to come from one reel and the practical case for correction
weakens — though the 20 mV zero error is systematic per channel and will still be there.

---

## 11. "Step size is bounded by slew rate, not full scale" is the wrong mechanism, and it is what let the 400 Hz assumption go unchallenged in the same ADR

**Severity: MINOR**

**Where.** ADR 0006, two sections apart:

> Stepping artefacts on the generic channels are not a concern: **step size is bounded by
> slew rate, not full scale.** A signal moving over ~10 ms sampled at 4 kHz changes by a
> fortieth of its excursion per sample

> It also conflated amplitude quantisation with time quantisation. **Software smoothing
> band-limits the content; it cannot remove the images the DAC creates after it.**

**Why.** The second statement is the right one and is the reason the update rate went to
4 kHz. The first is a different, incompatible model of the same artefact, and it is wrong:
**image amplitude is set by the sinc envelope evaluated at the image frequency, which
depends on the content's bandwidth, not on the step size.** Two signals with identical
500 mV steps — a 10 ms ramp and a 400 Hz sine of 1.6 V p-p — put very different energy at
3.6 kHz. The arithmetic quoted is correct (10 ms / 250 µs = 40 samples; on a 20 V span,
500 mV per step) and its conclusion is correct, but by luck: slow signals are safe because
their images sit near the sinc **null** at f_s, not because their steps are small. The
correct version of the same argument is the table in finding 4 — content under 50 Hz gives
an image at −38 dB *before* any filtering.

That matters because the wrong mechanism is load-bearing: it is what allows a "sources top
out near 400 Hz" assumption to sit in the same document as "stepping artefacts are not a
concern" without the contradiction being visible.

**On whether firmware smoothing can do what the design claims for it** — the brief asks
directly, so, precisely:

- **It can** reduce image *level*, because smoothing is band-limiting and the images are
  replicas of the content: halving the content bandwidth moves the image up the sinc
  skirt. The blanket statement "it cannot remove the images the DAC creates after it" is
  too strong as written. It is true in the sense that matters — you cannot smooth your way
  out of an image when the content is *already* near f_s/2 — and false as a general claim.
  The distinction should be written down, because the loose version would justify leaving
  the hardware filter out entirely, and finding 4 shows the hardware filter is the part
  that is already missing.
- **It cannot** move the image frequency, flatten the sinc envelope, or help a deliberately
  full-bandwidth event. ADR 0006 explicitly allows a **gate** on a mod channel ("a gate can
  be assigned to one if wanted"). A gate is a step: firmware smoothing is the wrong tool
  and the hardware filter is the only thing shaping it. Budget for it honestly —
  250 µs of update quantisation plus 175 µs (one pole at 2 kHz) or ~290 µs (two poles at
  1.5 kHz) of 10–90 % rise. Both are inaudible as gate timing and are fine into any
  Schmitt-triggered trigger input; neither is a fast edge, and no Eurorack input needs one.
- **Per-channel smoothing is the right place for it**, as `firmware/README.md` says, because
  firmware knows the destination and the analog filter does not. The design's division of
  labour is correct; only the justification needs repairing.

**Confidence: high.** This is a reasoning defect, not a behaviour defect.

**What would falsify it.** Nothing measurable — it is an argument, and the fix is to
rewrite one paragraph of ADR 0006 in the language of the other.

---

## 12. Two small errors of statement that change what a measurement should look for

**Severity: NIT**

**(a) "The DAC's full-scale output is its supply."** ADR 0004:

> **The DAC's full-scale output is its supply.** DAC8568 at internal reference × 2 spans
> 0–5 V, so full scale *equals* AVDD.

Full scale is **2 × the internal 2.5 V reference = 5.000 V** and is set by the bandgap, not
by AVDD **[VERIFIED: internal 2.5 V reference, gain 2 on C/D grades]**. It merely *coincides*
with a nominal 5 V rail. The real constraint is `AVDD ≥ FS + output-stage headroom`, which
is why TI wants ~5.5 V, and it is why the LM317 at 5.25 V is the right call — for a
different reason than the one given. The practical consequence: AVDD sag does **not**
proportionally scale the output (that would be a reference problem), it **compresses the
top of the transfer function** and couples in only through PSRR. So E7's scheduled
"DAC saturation vs AVDD" measurement should look for a *knee* — the code above which the
output stops tracking — not for a proportional slope. Same measurement, different
expected shape, and the difference decides whether a rail problem or a reference problem is
being diagnosed.

**(b) The LM317's dissipation figure.** BOM `U-REG-DAC`: "~5 mA load, **135 mW**".
`(12 − 5.25) V × 5 mA = 34 mW`; even adding the 5.2 mA the 240 Ω divider draws
(`1.25 / 240`) gives `6.75 V × 10.2 mA = 69 mW`. 135 mW implies 20 mA. Nothing downstream
is sized from it, so it is harmless — but it is the sort of number that gets reused. While
there: 5.2 mA of divider current is comfortably above the LM317L's ~3.5 mA minimum load
**[MEMORY]**, which is a real requirement and is being met by accident rather than by
statement.

**Confidence: high** on both arithmetic points.

**What would falsify it.** (a) Read TI's DAC8568 "Internal Reference" section. (b) Measure
AVDD current at E6 with the DAC idle and with all eight channels slewing.

---

# Where the design is right

Said explicitly, because most of it is, and several of these are better than they look.

1. **The DAC-sourced offset makes the reset state exact, and the reference-tracking
   argument is correct.** Substituting `Vdac = 2·Vref·N/65536`:

   ```
   Vout = 4 × (Vdac_sig − Vdac_off) = (8 · Vref / 65536) × (N_sig − N_off)
   ```

   Reference drift is therefore **pure gain**, and at `N_sig = N_off` the output is
   **exactly 0 V regardless of Vref** — the mod channels' zero is reference-independent by
   construction, not by trimming. That is genuinely elegant, and the ADR's argument that
   "the drift argument is a wash" is right for a better reason than it gives.

2. **The reference/offset error budget is negligible and stays negligible through the ×4.**
   The offset channel's own INL, ±4 LSB typ **[MEMORY]** = ±305 µV at the DAC, becomes
   ±1.22 mV common to all four outputs — 0.006 % of a 20 V span. The offset buffer's
   V_OS (±25 µV typ **[VERIFIED]**) × 4 = 100 µV. Each difference amp's own V_OS × noise
   gain 5 = 125 µV. All well under one 305 µV LSB.

3. **Crosstalk through the shared offset node is a non-problem, and here is the number.**
   Each difference amp draws code-dependent current from the offset node:
   `I = (2.5 − 0.8·Vdac)/R1`, which over a full 0–5 V DAC swing is `4 V / R1` =
   **400 µA per channel** at R1 = 10 k, 1.6 mA for all four. An OPA2197 buffer
   (GBW 10 MHz **[VERIFIED]**) has closed-loop Z_out ≈ Z_OL/(GBW/f); at 400 Hz that is
   ~4 mΩ, giving 1.6 µV × gain 4 = **6.4 µV of channel-to-channel crosstalk, −124 dB**.
   Even at a code-step's ~50 kHz content it is 800 µV for ~7 µs, which the output filter
   integrates to ~70 µV. **Keep the buffer** (driving four difference amps straight from
   the DAC pin would put the DAC's own load regulation into this path) and star its output
   — see finding 8 — and this stays where it is.

4. **The resolution question is answered correctly, and the analog stage does not spoil
   it.** 305 µV/LSB on a 20 V span; the narrowest preset (±2.5 V) still resolves
   5 V / 305 µV = 16,393 steps ≈ 14 bits. Stage noise, at R1/R2 = 10 k/40 k: R2 contributes
   25.7 nV/√Hz, R1 × 4 = 51.4, the + divider × 5 = 57.5, the op-amp (5.5 nV/√Hz
   **[VERIFIED]**) × 5 = 27.5 → RSS **85.8 nV/√Hz**; over a 2 kHz single-pole ENBW
   (1.57 × 2000 = 3140 Hz) that is **4.8 µV RMS**, a sixtieth of an LSB. The 16 bits are
   real rather than nominal, and would still be with 100 kΩ resistors.

5. **The output filter is a plain series RC with feedback taken at the op-amp output, and
   declining the in-loop version was right.** At a step the filter capacitor is a short, so
   the op-amp sees only the 1 kΩ — 10 mA at 10 V, nowhere near its ±65 mA
   **[VERIFIED]** — and the stage is unconditionally stable into any patch-cable
   capacitance. ADR 0006's observation that the in-loop `Cf` and the output filter are
   physically the same part and cannot both exist is exactly right, and resolving it now
   rather than deferring it was the correct call.

6. **The 1 kΩ series resistors into each op-amp's non-inverting input**, for the case where
   the DAC's 5.25 V rail and the ±12 V rails do not come up together, are the right part in
   the right place, and being outside the feedback path they cost nothing. This also covers
   the reverse case: with the DAC unpowered and its output high-Z, the difference amp's
   own divider pulls the + node to ground and the mod outputs sit at 0 V. Both sequencing
   directions land safe.

7. **BAV99 over BAT54S, and the arithmetic behind it.** 2 µA × 1 kΩ = 2 mV;
   2 mV / 83.3 mV per semitone = 2.4 cents, temperature-dependent. Correct, and correctly
   identified as reintroducing the exact error the matched network was bought to remove.

8. **The ZOH arithmetic that is present is right.** −12.6 dB at a 2 kHz update and
   −19.2 dB at 4 kHz both reproduce exactly (sinc at 1600/2000 = 0.2339; sinc at
   3600/4000 = 0.10930). The decision to reject 2 kHz updates when the loop already pays
   for 4 kHz is correct and well argued. Finding 4 is about the step after this one, not
   about this one.

9. **0 V is the right disconnect state, for every preset.** Unipolar 0–5/0–8 V → minimum;
   ±5/±2.5 V → centre; gate → off. There is no configuration in which the safe state is
   wrong, which is not automatic and is worth noticing.

10. **One op-amp part throughout**, and the reasoning that a cheaper part on the
    non-precision channels buys a class of assembly error for a few dollars, is correct for
    a one-off — and, in a module whose four mod channels share a reference and a supply
    with a precision channel, it also removes a whole category of "why is channel 3
    different" debugging.

---

# The sharing question, answered directly

**What pitch imposes on the mod channels**

- **The grade letter.** The zero-scale reset that pitch wants is also what makes
  `4 × (0 − 0) = 0` work for the mods, so this one is free — but it comes bundled with the
  reference gain (finding 3), and getting the bundle wrong halves every mod span.
- **The 0.25–4.75 V DAC window**, decided in the pitch section, costs the mods 10 % of
  their range: ±9 V, not ±10 V (finding 9).
- **AVDD from a dedicated 5.25 V LM317**, a part the mod channels alone would never have
  justified. Harmless, and they get quieter supply for free.
- **Out-of-turn pitch writes.** "Immediate update on note change" inserts a word into the
  round-robin, deferring a mod channel's update by one word (16–53 µs depending on the
  clock). Against a 250 µs period and sources under 200 Hz, that is nothing: uniform jitter
  of 8.7 µs RMS on a 20 Hz signal is −59 dB. Correct decision, no cost.
- **The requirement not to disturb the pitch reference** is what makes the offset buffer,
  the AVDD bulk capacitance and the ground star non-optional rather than nice-to-have.

**What the mod channels impose on pitch**

- **Four fifths of the SPI budget per pass.** They are the reason the link needs ~1.3–2 MHz
  rather than the 0.6 MHz ADR 0004 still advertises (finding 5). The RS-485 retirement
  rests on a number the mod channels invalidated.
- **DAC-to-DAC crosstalk and AVDD transients at every update.** Order of magnitude: even a
  pessimistic 2 LSB of DC crosstalk from four full-scale neighbours is 2 × 76 µV = 152 µV
  at the DAC, × 1.8 pitch gain = 274 µV = **0.33 cents**. Inaudible — but that is true only
  if the AVDD bulk (finding 2) and the ground topology (finding 8) are right, and neither
  is currently specified. **[MEMORY: DAC8568 crosstalk specs; verify at E9 by sweeping all
  four mod channels full-scale while a frequency counter watches the VCO.]**
- **The shared `CLR`.** This is the real coupling, and it runs the wrong way:
  **the watchdog that exists to park pitch safely is also what clears the mod channels'
  offset, and the mod channels are the ones that come back wrong** (finding 1). A feature
  added for the precision channel becomes the non-precision channels' worst failure mode,
  because only the mod channels have a second DAC register inside their transfer function.
  That is the single strongest argument for the "refresh everything, always" rule: the
  module has no readback, so shared state can only be made safe by being made stateless.

**Is one DAC, one reference and one supply the right call for five channels of two
different precisions?** Yes. The noise, INL and crosstalk arithmetic above all come out one
to two orders of magnitude inside what either class of channel needs, the reference-drift
term cancels in the mod topology and is an order of magnitude inside the resistor drift on
pitch, and the alternative — a second DAC — would add a part, a second reference to
disagree with the first, and another chip select down a cable that has no conductors left.
The sharing is sound. What is not sound is that two of the three coupling mechanisms it
creates — the shared `CLR` and the shared ground — are undocumented.
