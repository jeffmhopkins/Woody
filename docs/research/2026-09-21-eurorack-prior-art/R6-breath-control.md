# R6 — Breath control as actually implemented

Prior art for Woody's breath channel: commercial wind controllers, DIY/academic
wind instruments, and Eurorack breath interfaces. Written 2026-09-21.

## Evidence markers

Every claim below carries one. A previous review of this project found honesty
markers calibrated backwards, so these are deliberately strict.

| Marker | Means |
|---|---|
| `[repo]` | A file in `/home/user/Woody`, opened this session |
| `[source]` | Source code I cloned and read this session — the file is named |
| `[datasheet]` | Text extracted this session from a datasheet PDF I have on disk |
| `[web-summary]` | **Weak.** A search engine's summary of a page the egress proxy would not let me open. I have not read the page. Treat as a lead, not as a fact |
| `[derived]` | My arithmetic from numbers marked above |
| `[memory]` | Model knowledge, unverified this session |

### What I could not reach

The egress proxy blocked **every** domain I tried except GitHub raw/clone.
Confirmed blocked this session: `gordophone.blogspot.com`, `www.modwiggler.com`,
`hackaday.io`, `hackaday.com`, `www.patchmanmusic.com`, `nime.org`,
`ccrma.stanford.edu`, `vcvrack.com`, `doepfer.de`, `www.nxp.com`, `www.ti.com`,
`www.manualslib.com`, `manuals.plus`, `cdn.inmusicbrands.com` (Akai EWI4000s
manual), `mybreathmymusic.com` (Yamaha WX5 manual), `yamahamusicians.com`,
`shedsynth.wordpress.com`, `en.wikipedia.org`, `usa.yamaha.com`,
`support.akaipro.com`, `electro-music.com`.

**So I never read an EWI or WX service manual, the Gordophone series, a
modwiggler thread, the KeyWI paper, or an NXP datasheet.** What I have instead
is: source code from five wind-controller projects I cloned and read in full,
one datasheet PDF that happened to be committed into one of those repos, and
search-engine summaries. Everything marked `[web-summary]` should be re-checked
by a human with an unfiltered browser before anything expensive is built on it.

### What I did read in full

- **`jeffmhopkins/open-woodwind-project`** — the author's own 2021 predecessor.
  `src/owp/owp.ino` (controller), `src/owp_synth/*` (synth). **This is the
  single most relevant prior art and it contradicts ADR 0003 on one point.**
- `Trasselfrisyr/MiniWI` — Johan Berglund's MiniWI / TeensieWI / **T.WI**, the
  most-copied DIY wind controller lineage. Includes an **MPX5010 datasheet PDF**.
- `ggood/BreathController` — Gordon Good's breath controller.
- `matthewcaren/KeyWI` — the NIME 2020 KeyWI. **Uses the MPXV4006DP, the exact
  part Woody specifies.**

---

## Findings vs Woody

| # | Prior art | Woody | Verdict |
|---|---|---|---|
| 1 | MPXV4006 / MPX5010 / MP3V5004 gauge or differential, 4–10 kPa FS, is the DIY and academic standard. **KeyWI uses the MPXV4006DP** `[source]` | MPXV4006DP, 0–6 kPa | **Right, and mainstream.** Not a reinvention |
| 2 | Real playing tops out at **2.5–2.8 kPa** in two independently-calibrated controllers `[source]`; acoustic sax is 2–3 kPa soft, 4–4.5 kPa loud `[web-summary]` | Fixed in-amp gain 2.185 puts 10 V at **6 kPa** `[repo]` | **Mis-scaled.** A hard blow reaches ~5 V, not 10. The GAIN knob must supply ~2×, not the "0.6 % shortfall" the schematic claims |
| 3 | EWI: **two knobs per sensor, "S" gain and "A" adjust**, user-set before playing `[web-summary]`. WX5: **Wind Zero + Wind Gain** trimmers `[web-summary]`. KeyWI: **`sensitivity` and `offset` knobs on ANALOG_4/5** `[source]` | Panel GAIN + OFFSET knobs | **Right, and exactly what everyone does.** Strongest validation in this report |
| 4 | WX5 manual: *"Wind Zero may change slightly when Wind Gain is adjusted, so you may have to repeat"* `[web-summary]`. KeyWI subtracts offset **before** dividing by sensitivity `[source]` | "gain first, then offset… the knobs behave independently" `[repo]` | **Wrong.** The 0.437 V sensor pedestal passes the gain pot un-nulled, so the offset needed to zero the jack is proportional to gain. The knobs are coupled. See §2 |
| 5 | EWI sets its zero against a **Breath indicator LED**; the zero is re-set per session `[web-summary]` | Zero set once at commissioning with **a meter on the jack**; display is explicitly not evidence `[repo]` | **Gap.** The one-authority rule is right; leaving the player no on-panel way to exercise it is not. A zero LED on the module fixes it |
| 6 | KeyWI's mouthpiece bleed hole exists partly to **compress dynamic range**: *"proportionally less pressure is exerted on the sensor as the user blows harder"* `[web-summary]`. DIY consensus wants an exhaust port near the sensor `[web-summary]` | Sealed dead-end; bleed rejected because the player vents round the mouth `[repo]` | **Woody answered only half the question.** The venting argument is sound; the range-compression function is a second, independent reason for the hole that ADR 0003 never addresses |
| 7 | Everyone drains: WX drain hole + swappable plugs `[web-summary]`, Aerophone drain pipe + *"lean the unit against a wall… to drain saliva"* `[web-summary]`, DIY: *"if you can't clean it out after use you have made a mould farm"* `[web-summary]` | Clearable dead-volume trap, porous PTFE plug | **Right in kind, under-specified in geometry.** A sealed tube cannot self-drain; gravity is everyone else's mechanism and Woody has not said which way its tube points at rest |
| 8 | Gore-Tex/ePTFE membrane is an established DIY moisture barrier `[web-summary]` | Porous PTFE plug, doubling as restrictor | **Right, and the dual use is good.** But see §5: a filter clogs, and Woody's chosen diagnostic will not see it |
| 9 | Melodica hose + mouthpiece, **530–570 mm**, is a commodity part; ADDAC310 uses one `[web-summary]`. KeyWI offers a long vinyl tube option `[web-summary]` | 400 mm tube, mouthpiece to be made | **400 mm is not unusual — it is short by melodica standards.** And the mouthpiece can be bought for a few pounds instead of designed |
| 10 | Nobody models the sensor tube as a resonator, anywhere I could reach | Distributed pipe, 214–429 Hz, damped by the PTFE plug `[repo]` | **Novel, and neither confirmed nor refuted.** But the prior art's tubes are all flowing or bled; Woody's is the only dead-ended one, i.e. the only undamped case. Woody is probably right to worry |
| 11 | Historic breath CV: Lyricon Wind Driver **Wind 1 ≈ +0.5 mV to +3.5 V** `[web-summary]`. Eurorack VCA unity gain is 5 V, 8 V or 10 V depending on module; many clip above 5 V `[web-summary]` | 0–10 V jack | **No standard to violate, but 10 V is the top of the range and many VCAs will hard-clip half the player's dynamics.** The GAIN knob covers it *if its range reaches low enough* — which is undrawn |
| 12 | Curves are **configurable and many**: T.WI ships **13** breath curves (9 exponential family + 4 sigmoid), 17-point LUTs, stored in EEPROM `[source]` | One `breath_gamma` power law, on the digital copy only | **Under-provisioned, and in the wrong place for the jack.** Sigmoids are not reachable by a gamma. A shaped breath copy on a mod channel costs nothing and Woody already has the machinery |
| 13 | Everyone deliberately smooths breath: T.WI **30 Hz one-pole (τ 5.3 ms)** `[source]`; KeyWI `si.smooth(0.996)` `[source]`; MiniWI IIR 0.8/0.2 `[source]`; ggood sends CC every **20 ms** `[source]`; OWP's own synth ramps amplitude over **8 ms** `[source]` | ~2.8–3.1 ms budget, 500 Hz filters, "margin not headroom" | **Woody's chain is far faster than every working instrument.** The 1.6× panic is against the wrong target. But the *unbounded* term is real — see §7 |
| 14 | OWP (2021) inserted **`breath_risetime = 5 ms`** between threshold breach and the first CC, on purpose `[source]` | 5 ms target for the whole chain `[repo]` | **The author's own last instrument deliberately spent Woody's entire budget on one delay, and played fine.** This is the most direct available refutation of the latency anxiety |
| 15 | OWP's startup zero is **a single `analogRead`** `[source]`; and the MIDI branch ignored it in favour of a fixed constant `[source]` | "Seeds the digital zero from an ADC capture at power-on, **exactly as the 2021 code did**" `[repo]` | **The precedent is weaker than cited.** One sample, no averaging, and two disagreeing zeros in the same file. Copy the idea, not the implementation |
| 16 | MPX5010 datasheet: *"Decoupling circuit shown in Figure 3 **required to meet specification**"* — 1.0 µF + 0.01 µF on VS and **470 pF on VOUT** `[datasheet]` | No sensor decoupling specified anywhere I read `[repo]` | **Missing.** And the 470 pF is the RF/anti-alias pole Woody wants, at the one place it currently has nothing |
| 17 | MPX5010 response time **tR typ 1.0 ms** (10–90 %), warm-up **20 ms** `[datasheet]` | "Pressure transducer ~1 ms" `[repo]` | **Confirmed** for the family. The 20 ms warm-up is new: the power-on zero capture must wait for it |
| 18 | MPX5010 media note: specs are *"based on use of dry air… Media other than dry air may have adverse effects"*; **fluorosilicone gel die coat** `[datasheet]` | *"NOT compatible with water or water vapors"*, gel swells when wet `[repo]` | **Directionally confirmed; the exact quote is not verified.** The wording I can see is weaker than Woody's. Someone should open the MPXV4006DP datasheet and check |
| 19 | OWP's `breath_gamma` / `lin_to_log` live in **`src/owp_synth/`, the synth**, not the controller `[source]` | "The previous firmware had `breath_gamma` and a `lin_to_log` mapping" `[repo]` | **True but misleading.** The 2021 shaping was at the *sound engine*, downstream of the wire — which is precisely the modular idiom ADR 0003 defends. Woody's analog jack is *more* faithful to the predecessor than the ADR admits |

---

## 1. The sensor, and whether 0–6 kPa is right

### What people actually use

| Project | Sensor | Range | Evidence |
|---|---|---|---|
| **KeyWI** (NIME 2020) | **MPXV4006DP** | 0–6 kPa | `[web-summary]`, repo cloned `[source]` |
| MiniWI / TeensieWI | MPX5010GP | 0–10 kPa | `MiniWI/MiniWI.ino` header `[source]` |
| T.WI | MPX5010GP header, `MP3V5004GP` in a code comment | 0–10 / 0–3.92 kPa | `T.WI/T.WI.ino` `[source]` |
| Gordon Good | **MPXV4006GP** | 0–6 kPa | `BreathController.ino` header `[source]` |
| **OWP 2021 (author's own)** | README says MPXV4006GP; `owp.ino` header says **MPX2010GS** | 0–10 kPa uncompensated | `README.md`, `src/owp/owp.ino` `[source]` |

Two things follow.

**The MPXV4006 family is not a novel choice — it is the considered choice.** The
search summary of the MiniWI/Gordophone community describes MPXV4006GP as *"even
more close to human breath pressure range"* than the MPX5010 `[web-summary]`,
and KeyWI, a peer-reviewed instrument design, landed on the **DP variant
specifically** `[web-summary]`. Woody reached the same part by a different route
(sourcing: GP is EOL, DP is not `[repo]`) and got there. Nothing to change.

**ADR 0003's account of the old repository's contradiction is accurate.** I
confirmed both halves: `README.md` says MPXV4006GP, `src/owp/owp.ino`'s header
comment says `MPX2010GS` `[source]`. ADR 0003 reports this correctly.

### Is 0–6 kPa the right range?

Three independent calibrations, all from firmware constants written by people
who tuned them against their own playing:

| Project | Constant | Pressure at "blowing as hard as you can" |
|---|---|---|
| MiniWI | `breath_max 300` of 1023, MPX5010 at 5 V | **2.81 kPa** `[derived]` |
| T.WI | `breath_max 2200` of 4095, MP3V5004 at 3.3 V | **2.49 kPa** `[derived]` |
| Acoustic alto sax | — | 2–3 kPa soft, 4–4.5 kPa loud `[web-summary]` |

MiniWI's `ON_Thr 40` works out to **−0.01 kPa** `[derived]` — i.e. exactly the
sensor's own zero-pressure offset. That the threshold lands on zero is a good
check that the transfer-function model above is right, which makes the 2.81 kPa
figure trustworthy.

**So 0–6 kPa is not too sensitive. It is roughly twice as much range as a player
uses.** That is the safe direction to be wrong in — a clipped breath channel is
unplayable and an under-used one merely wants gain — and **ADR 0003's "the
0–6 kPa range was well chosen in 2021 and stands" is correct** `[repo]`.

One caveat that cuts the other way, and it matters: **MiniWI, T.WI, KeyWI and
the EWI all bleed.** The sensor sees less than mouth pressure. Woody's tube is
sealed, so the sensor sees mouth pressure undivided, and Woody will reach a given
kPa at the sensor for *less* embouchure effort than any of these references.
That pushes Woody further into its range, not out of it — good — but it means
these numbers are a **lower bound** on what Woody will see, not a direct
prediction. E2 should measure it rather than assume it.

### The consequence Woody has not drawn: the fixed gain is scaled to the wrong thing

`hardware/module/breath-receive-stage.md` derives `R_G = 42.2 kΩ` from a
**sensor span of 0.2 → 4.8 V**, i.e. 0 → 6 kPa, and calls the residual a *"0.6 %
shortfall… absorbed by the panel gain knob"* `[repo]`.

Against real playing pressure `[derived]`:

| Mouth pressure | Signal at INA828 output | Post-stage gain for a 10 V jack | …for a 5 V jack |
|---|---|---|---|
| 2.5 kPa | 4.19 V | **2.39×** | 1.19× |
| 2.8 kPa (MiniWI max) | 4.69 V | **2.13×** | 1.07× |
| 3.0 kPa | 5.02 V | **1.99×** | 1.00× |
| 4.5 kPa (loud sax force) | 7.54 V | 1.33× | 0.66× |
| 6.0 kPa (design assumption) | 10.05 V | 1.00× | 0.50× |

The panel GAIN knob is not absorbing 0.6 %. **It is absorbing a factor of two.**

This is not a defect in the circuit — the in-amp gain is a sensible fixed value
and the knob exists precisely for this — but it is a defect in the *derivation*,
because it sets the wrong requirement on the downstream stage, which
`breath-receive-stage.md` still draws as an unvalued block `[repo]`. The
requirement that falls out of the table is:

> **The post-in-amp gain pot must span roughly 0.6× to 2.5× — about 4:1** — to
> cover "hard blow → 10 V" at one end and "hard blow → 5 V for a unipolar VCA"
> at the other. `[derived]`

Note the accident: at unity post-gain, a 3 kPa blow lands at **5.0 V**, which is
the commonest Eurorack VCA full-scale. The design as drawn is a better 0–5 V
output than a 0–10 V one.

---

## 2. Gain and offset are coupled, and the ADR says they are not

This is the most substantive electrical finding in this report.

**The claim.** ADR 0006: *"Order is gain first, then offset… The reverse ordering
makes the two controls fight each other."* `[repo]`
`breath-receive-stage.md`: the inverting summer means *"the panel knobs behave
independently, which is what 'gain first, then offset' means physically."*
`[repo]`

**Why it is wrong.** The MPXV4006DP sits at **+0.200 V at zero pressure**, and
`REF` is tied hard to module analog ground, so nothing subtracts that pedestal
before the gain stage. The INA828 output at rest is `−2.185 × 0.200 = −0.437 V`
`[derived]`. That pedestal is then multiplied by the gain pot along with the
signal:

| Post-stage gain `k` | Jack voltage at rest, before OFFSET | As % of a 10 V span |
|---|---|---|
| 1.00 | 0.437 V | 4.4 % |
| 1.33 | 0.581 V | 5.8 % |
| 2.00 | 0.874 V | 8.7 % |
| 2.39 | 1.044 V | 10.4 % |

`[derived]`

**So the OFFSET setting that zeroes the jack is a function of the GAIN setting.**
Trim the zero at unity, then turn GAIN up to put a hard blow at 10 V, and the
jack idles at about +0.44 V — into a VCA, that is audible leakage with the
instrument on a stand.

**Two independent sources say this is the known behaviour of this topology.**
The Yamaha WX5 manual, per its search summary, tells the user that *"the Wind
Zero setting may change slightly when Wind Gain is adjusted, so you may have to
repeat the Wind Zero and Wind Gain adjustments a few times"* `[web-summary]` —
Yamaha documents the iteration because their chain has the same coupling.
KeyWI, in code I read, does it the other way and avoids it:

```faust
readpressure = hslider("breath[BELA: ANALOG_0]", ...)*-1 - offset;
breath = (readpressure + pGate - .05) / (1-sensitivity) : ...
```
`code/melodica/melodica.dsp` `[source]`

**Offset is subtracted first; sensitivity divides afterwards.** With that
ordering the zero is invariant under gain, and `offset` and `sensitivity` are
genuinely orthogonal knobs.

**The fix Woody already worked out and then threw away.** Nulling the pedestal
before the gain stage means putting **+0.437 V on the INA828's `REF` pin**.
`breath-receive-stage.md` has already established both halves of this: that with
BREATH on IN−, a *positive* `REF` subtracts, and that `REF` must be driven
**hard or from a buffer**, never through a divider, because source impedance
there degrades CMRR one-for-one `[repo]`.

The reason `REF` was grounded was that **firmware** was driving it from a DAC
channel — correcting a signal it could not measure, and re-introducing a
split-brain `[repo]`. **That objection does not apply to a fixed trim.** A
multiturn trimmer buffered by an op-amp half, set once against a meter, is not
tracking anything: it subtracts a constant that is knowable from the datasheet
(0.152–0.378 V spec window, so a per-unit trim rather than a fixed resistor
`[repo]`), and it is set by a human looking at the exact node it corrects.

**Do not put this back on DAC channel 6.** `breath-receive-stage.md` notes that
the watchdog's `CLR` reaches the DAC channels, and that grounding `REF` was what
stopped `CLR` from *"yanking the zero out from under"* the breath stage `[repo]`.
A DAC-driven `REF` rebuilds that hazard. A passive trimmer plus buffer does not.

**If the trimmer is judged not worth an op-amp half in a one-off** — a defensible
call — then the honest alternative is to **delete the independence claim from
both documents and write the WX5's iterate-until-settled procedure into E10
instead.** What is not acceptable is keeping a claim of independence that the
schematic does not support.

---

## 3. Response curves

### What prior art does

**T.WI ships thirteen.** `T.WI/T.WI.ino` defines thirteen 17-point lookup tables
— `curveM4`…`curveM1`, `curveIn` (linear), `curveP1`…`curveP4`, and
`curveS1`…`curveS4` — interpolated by `multiMap`, selected by a setting stored in
EEPROM at `BREATHCURVE_ADDR`, factory default `2` (the −2 curve) `[source]`.
Four of them are **sigmoids**, which no single-exponent gamma can produce. The
output is computed at **14-bit** (`breathValHires`, 0–16383) and the MIDI
velocity is the top 7 bits of it `[source]`.

**OWP 2021 shaped at the synth, not the controller.** `breath_gamma` and
`lin_to_log` are in `src/owp_synth/` — the Teensy audio engine — not in
`src/owp/owp.ino` `[source]`:

```c
float lin_to_log(int input, int input_max, float gamma) {
  return (float)(0.5 + pow((float)input/(float)input_max, gamma) * input_max);
}
float breath_gamma = 1.85;
```
`src/owp_synth/owp_synth.ino` `[source]`

and it is applied where breath meets the VCA:

```c
breath.amplitude(lin_to_log(data2, 127, breath_gamma)/127.0, breath_ramp_rate);
```
`src/owp_synth/process_midi.ino` `[source]`

with `breath_gamma` exposed as a live CC (`CC_BREATH_GAMMA 17`) and stored per
patch `[source]`. Breath also drove pulse width (0.4), filter cutoff (0.2), LFO
rate and depth, and noise amplitude, all with per-patch depths `[source]`.

**KeyWI's curve is implicit in its physical models** — the reed and clarinet
models take `breath` as a physical pressure, so the nonlinearity comes from the
model `[source]`.

### What this means for Woody

**ADR 0003's claim that "the previous firmware had `breath_gamma`" is true of the
*synth*, and that undercuts the sense in which curve shaping is "genuinely
lost."** In 2021 the wire between the controller and the sound carried raw,
linear, threshold-mapped MIDI CC2; the shaping happened at the destination
`[source]`. **Woody's analog jack reproduces the 2021 architecture more faithfully
than the ADR gives it credit for** — and ADR 0003's own defence, that *"sending
raw breath and shaping it with the rack's own tools is the idiom"* `[repo]`, is
not a rationalisation. It is what the author already built.

Two caveats, though.

**Gamma alone is not what practice offers.** T.WI's four sigmoids exist because
players want a knee — quick onset, then a plateau — and `x^γ` cannot make one.
If Woody's firmware curve is going to be configurable at all, a small LUT with
interpolation costs the same as `pow()` and reaches the shapes people actually
select.

**The direction of the curve depends on where it sits, and Woody has three
positions to keep straight.** T.WI's default is *compressive* (more output at low
breath) because it shapes a MIDI CC before an unknown synth; OWP's gamma 1.85 is
*expansive* because it shapes a linear VCA amplitude directly. Woody's jack is
raw linear pressure into whatever the patch is. **That is only musical if the
receiving VCA is exponential** — many Eurorack VCAs have a lin/exp switch
`[memory]`, and the patch needs to be in exp. Worth one line on the panel or in
the manual, because a linear-VCA patch fed raw breath is the classic "feels like
a volume knob" complaint ADR 0003 itself warns about `[repo]`.

### The Lyricon arrangement, which Woody can have for free

The Lyricon Wind Driver — the only historical wind controller that output CV
directly to analog synths — had **two** breath CVs: *"Wind 1 (~+0.5 mVDC to
~+3.5 VDC) and Wind 2 (adjustable with Wind 2 slider and threshold knob)"*, for
the VCA and the VCF respectively `[web-summary]`.

Woody's mod channels 1–4 are generic, with *"per-channel source, scale, offset,
curve and slew set on the instrument's display"* `[repo]`. **A shaped, curved
breath copy on one mod channel is already buildable with zero design change**,
and it gives exactly the Lyricon split: raw analog breath on the dedicated jack
for the VCA, shaped digital breath on a mod jack for the filter. I would make it
the factory default assignment for Mod 1 and say so in ADR 0006 — it converts
"curve shaping on the breath output is genuinely lost" from a loss into a
routing choice.

---

## 4. Zeroing and drift

### What real instruments do — all four answers exist, and none of them is "nothing"

| Instrument | Mechanism | Evidence |
|---|---|---|
| **Akai EWI 4000s** | Two recessed knobs per sensor: **"S" (sensitivity)** and **"A" (adjust)**. Procedure: S to mid, turn A clockwise until the **Breath indicator lights**, then back off until it goes out. Manual: *"adjust them again by yourself before you play it"* | `[web-summary]` |
| **Yamaha WX5 / WX7** | **Wind Zero** and **Wind Gain** trimmers; manual documents that they interact and must be iterated | `[web-summary]` |
| **KeyWI** | Two analog knobs, `offset` (0–0.4, default 0.1) and `sensitivity` (−0.6–0.9, default 0.3), read continuously on ANALOG_5 and ANALOG_4 | `code/*/​*.dsp` `[source]` |
| **OWP 2021** | Single `analogRead` at power-on into `ambient_breath_reading` | `src/owp/owp.ino` `[source]` |
| MiniWI / T.WI / ggood | **Nothing.** A compile-time `ON_Thr` / `BREATH_THRESHOLD` constant | `[source]` |

**So Woody's panel OFFSET knob is not an oddity — it is what three of the four
serious instruments do, including both commercial ones.** The "one authority per
representation" table in ADR 0003 `[repo]` is, as far as I can tell from this
evidence, simply correct, and it is the best-argued section of the breath ADRs.

### Three specific gaps

**(a) The player has no way to set the analog zero without test gear.**
`breath-receive-stage.md` commissions the zero with *"a meter on the jack"* and
says *"E10 scopes the jack, not the display… a flat bar on the screen is no
longer evidence about the output"* `[repo]`. That reasoning is right. But the
EWI's whole zeroing procedure is possible **because there is a Breath indicator
LED that lights at the threshold** `[web-summary]` — the instrument gives the
player a null indicator for the very signal the knob controls.

> **Put a zero indicator on the module panel, driven from the post-OFFSET node.**
> A window comparator and one LED — lit when the jack is within a few tens of
> millivolts of 0 V. It measures the analog path, so it does not violate the
> one-authority rule; it *implements* it. Cost is a dual comparator and an LED.
> Without it, "a quarter turn if it ever bothers you" is not an action the player
> can actually take, because they cannot see when they have arrived.

**(b) The startup capture precedent is weaker than ADR 0003 cites.** ADR 0003 says
firmware seeds the digital zero *"exactly as the 2021 code did"* `[repo]`. What
the 2021 code did:

```c
ambient_breath_reading = SETTINGS_BREATH_GAIN * analogRead(A0);
if (ambient_breath_reading > 1023) ambient_breath_reading = 1023;
```
`src/owp/owp.ino`, `setup()` `[source]`

**One sample.** A single noise excursion, or a player already breathing into it
at power-on, biases the zero for the whole session. Worse, the same file then
*ignores* that zero in its MIDI branch and uses the fixed constant
`SETTINGS_BREATH_THRESHOLD 225` instead — two zeros, disagreeing, in one file
`[source]`. This is prior art to learn from, not to cite as validation.

> **Average the capture** (tens of milliseconds), **and gate it on a plausibility
> window.** The datasheet offset band is 0.152–0.378 V `[repo]`; a capture
> outside it is not a zero, it is a fault. ADR 0003 already warns that a reversed
> DP port *"reads zero, which is easy to mistake for a dead sensor"* `[repo]` —
> a plausibility window on the seed is the check that distinguishes the two, and
> it is free.

**(c) Wait for warm-up.** MPX5010 datasheet: **Warm-Up Time 20 ms typ**, *"the
time required for the product to meet the specified output voltage after the
Pressure has been stabilized"* `[datasheet]`. Not a latency term, but the power-on
capture must not happen inside it.

### On the drift figure itself

ADR 0003 rests the "panel knob only, touch it once" decision on the MPXV4006DP's
offset drifting *"roughly 0.5 mV/K"*, giving ~23 mV in 10 V over a 20 K rise
`[repo]`. **I could not verify that number** — nxp.com is blocked. What I *can*
see is that the MPX5010's specification does not break out an offset tempco at
all; it gives a combined accuracy of **±5 % VFSS over 0–85 °C**, with TcOffset
listed as one of five contributors folded into that budget `[datasheet]`. On a
4.5 V span that is ±225 mV of total error band. 0.5 mV/K may well be right, but
it is not obviously a published figure, and the entire "one quarter-turn, once"
conclusion depends on it. **Mark it as unverified and confirm it from the
MPXV4006DP datasheet before E10.** If it is 2 mV/K rather than 0.5, the warm-up
drift is ~90 mV at the jack and item (a) above stops being a convenience.

---

## 5. The tube, resonance, condensation, and spit

### 400 mm is not unusual

| Reference | Tube |
|---|---|
| Melodica hose + mouthpiece, commodity part | **530 mm and 570 mm** `[web-summary]` |
| ADDAC310 Pressure to CV | *"a melodica pipe connected to the front panel"* / *"melodica mouth hose"* `[web-summary]` |
| KeyWI | short tube to play at the mouth, **or a longer vinyl tube so it can rest on a table** `[web-summary]` |
| DIY guidance | Tygon, short 1/16" ID onto the sensor snout, most of the length 1/8" ID `[web-summary]` |
| **Woody** | 400 mm `[repo]` |

**Woody's tube is shorter than a stock melodica hose.** The 1.17 ms of
propagation delay `[repo]` is real, but the length itself has abundant precedent
and nothing about it needs defending.

The DIY bore guidance is worth noting against ADR 0003's open bore question
`[repo]`: the community uses **1/8" ≈ 3.2 mm** for the run and steps down to
1/16" only at the sensor stub `[web-summary]`, which is almost exactly the 3 mm
bore ADR 0003's acoustic arithmetic assumes.

### The resonance model has no prior art either way

I found **nothing**, in any project I could read or any summary I could get,
that treats the breath tube as an acoustic resonator. Not the EWI, not the WX,
not KeyWI, not MiniWI, not OWP.

Two readings of that, and I think the second is right:

- It is a non-problem, and Woody has invented a concern.
- **Every one of those tubes is either flowing or bled, and Woody's is the only
  dead-ended one.** A tube with a bleed orifice has acoustic resistance in it by
  construction; a sealed dead-end is the undamped case. So the absence of prior
  art is what you would expect if the problem is specific to the choice Woody
  made — which is exactly the situation in which you should not take silence as
  reassurance.

ADR 0003's revision — dropping the Helmholtz model, noting that no trap volume
places a pipe mode, and restating the plug's job as **damping rather than
placement** `[repo]` — is sound reasoning and I have nothing to correct in it.
**E2's ring-down measurement is the right test and it has no substitute in the
literature.**

### Condensation: right idea, missing geometry

Everyone else drains, and drains **downhill**:

- **Yamaha WX7/WX5**: a drain hole with two swappable plugs — cross-section for
  partial blocking, circular for full — which also set blowing resistance
  `[web-summary]`. Note the dual purpose: the drain *is* the resistance control.
- **Roland Aerophone**: *"There is a pipe in the Aerophone that allows for
  drainage of the saliva"*, plus a band round the mouthpiece and the instruction
  to *"lean the unit against a wall or vertical surface to drain saliva inside
  the instrument"* after each performance `[web-summary]`.
- **Akai EWI**: some air and moisture is allowed to pass through to the bottom of
  the unit `[web-summary]`; a user teardown of an EWI4000s describes *"the tubes
  that carry the breath through the instrument, and a second one to the pressure
  sensor"* `[web-summary]`.
- **DIY consensus**: *"A drain for drool/moisture build-up is highly recommended.
  All the moisture in your breath has to go somewhere, and if you can't clean it
  out after use you have made a mould farm."* `[web-summary]`

**Woody's sealed tube cannot self-drain**, so the one mechanism every other
instrument relies on — gravity, on a downhill path to an opening — is
unavailable. ADR 0003's trap plus clearable access plus porous PTFE plug is a
reasonable substitute `[repo]`, and the Gore-Tex/ePTFE membrane appearing in DIY
builds `[web-summary]` confirms the plug is established practice rather than
invention.

What is missing is the geometry:

> **Specify which way the tube slopes when the instrument is at rest, and put the
> trap at its low point.** The Aerophone's "lean it against a wall" ritual is
> the user doing by hand what a resting orientation can do by design. On a sealed
> tube with a 40 mm mouthpiece stub, it costs nothing to decide at E2.

### The failure mode Woody named but will not catch

ADR 0006 lists *"a partially blocked PTFE restrictor"* as one of three failures
the continuous auto-zero must not conceal, and instruments it by **logging the
accumulated zero correction** — *"a number that walks"* `[repo]`.

**That diagnostic cannot see a clogging restrictor.** A porous plug that is
filling with condensate and biofilm changes the pneumatic **time constant**, not
the zero. The output still settles to the same value; it just takes longer. The
zero-correction log stays flat while the instrument gets progressively vaguer to
play — which is precisely the "instrument that has gone vague" failure ADR 0006
says it is protecting against `[repo]`.

The measurement that *does* see it is already specified — E2's ring-down and
added time constant `[repo]` — but it is specified as a one-off bring-up step.

> **Make the restrictor time constant a repeatable self-test, not a bring-up
> measurement.** Firmware already has the breath ADC at 4 kHz, a threshold, and
> a display. Timing the decay of breath after a note release gives a time
> constant every time the player stops blowing. Record the value at E2 as the
> baseline and log the drift, exactly as the zero is logged. This is the same
> argument ADR 0006 makes for the zero, applied to the term that actually
> degrades — and it also bounds the one number the latency budget cannot fill in
> `[repo]`.

---

## 6. The mouthpiece, and the bleed hole Woody dismissed too quickly

### You can buy one

| Part | Notes | Evidence |
|---|---|---|
| **Melodica mouthpiece + hose**, 53 cm / 57 cm | Commodity ABS, sold as a replacement part for 32/36/37/41-key melodicas. **This is what the ADDAC310 uses.** | `[web-summary]` |
| **Akai EWM1** | Genuine EWI replacement mouthpiece, EWIUSB / 4000s / 5000. Contains the air-pressure and bite sensors, so it is a sensor assembly, not a bare mouthpiece | `[web-summary]` |
| **Roland OP-AE10MP / OP-AE10MPH** | Aerophone replacement mouthpiece, soft and hard reed. Reed not separately replaceable — replace the whole mouthpiece | `[web-summary]` |
| KeyWI | 3D-printed, `platform-files/mouthpiece.stl` in the repo | `[source]` |

ADR 0003 specifies the mouthpiece as a raw tube end with a small nib, narrow
enough that the corners of the mouth stay open for circular breathing, removable
and cleanable, with no bite sensor `[repo]`.

**A melodica mouthpiece meets every one of those requirements, is designed to be
lipped around, is sold with a tube of about the right length, and costs a few
pounds.** The EWM1 and the Roland part are sensor assemblies and are the wrong
shape of solution. **Buy a handful of melodica mouthpieces at E2 and settle the
bore by picking one**, which is exactly the "play a bare tube in two or three
sizes" experiment ADR 0003 already prescribes `[repo]` — only with parts that
already exist.

### The bleed hole does a second job Woody never considered

ADR 0003 records the sealed tube as settled, and records the reason the review's
objection failed: *"the exhale path is not the instrument… the player vents
through the corners of the mouth"* `[repo]`. **That argument is correct** and the
circular-breathing point is a genuine insight.

But it answers only the *venting* function of the bleed. KeyWI's description of
its own mouthpiece hole gives a second, independent function `[web-summary]`:

> *"A small hole in the side of the mouthpiece allows air to flow through the
> mouthpiece **as well as augmenting the dynamic range: proportionally less
> pressure is exerted on the sensor as the user blows harder, so it takes more
> pressure to reach the sensor's limit.**"*

That is a **pneumatic compressor**. The hole and the tube form a flow divider
whose division ratio worsens with flow, so the sensor sees a compressed version
of mouth pressure and the top of the player's range does not slam into full
scale. It is the pneumatic equivalent of T.WI's compressive default curve.

The Yamaha drain plugs are the same idea from the other end: *"Partially closing
the upper Drain Hole creates a tight blowing feel, while completely closing…
creates an even tighter feel, suitable for saxophone players who tend to blow
with greater force"* `[web-summary]`. **Yamaha ships a user-swappable pneumatic
range control**, and it is the same hole as the drain.

**So a bleed orifice in a commercial wind controller is doing three jobs at
once — venting, draining, and range compression — and ADR 0003 rebuts only the
first.** The section is headed *"Recorded so it is not re-raised"* and asserts
that *"the commercial designs solve a problem this playing technique does not
have"* `[repo]`. The venting problem, yes. The other two, no.

**I do not think this overturns the decision.** From §1, Woody has about 2× more
sensor range than a player uses, so it does not *need* compression to avoid
clipping — which is the specific thing KeyWI needed it for — and the panel GAIN
knob plus the firmware curve cover the feel. And the sealed tube genuinely does
buy what ADR 0003 claims: embouchure controls pressure directly, nothing to clog
as a manufacturing tolerance, and no flow through the sensor branch, which is the
property the condensation handling depends on `[repo]`.

**But the section should stop claiming the question is closed on a rebuttal that
only covers one third of it.** Rewrite the rebuttal to say: the venting function
is not needed because of how this instrument is played; the range-compression
function is not needed because the sensor has 2× headroom at realistic playing
pressure; the drain function is replaced by the trap and the resting geometry.
Three answers, because there are three questions.

---

## 7. Latency

### What the chain actually costs elsewhere

| Where | Deliberate delay | Evidence |
|---|---|---|
| **T.WI** | `FilterOnePole breathFilter(LOWPASS, 30.0)` — **30 Hz one-pole, τ = 5.31 ms** | `T.WI/T.WI.ino:173,249` `[source]` `[derived]` |
| **T.WI** | `CC_INTERVAL 5` — breath CC every 5 ms | `[source]` |
| **MiniWI** | `breathLevel = oldBreath*0.8 + breathLevel*0.2` per loop; `ON_Delay 20` ms before velocity is taken, *"wait for tounging peak"* | `MiniWI/MiniWI.ino` `[source]` |
| **ggood** | `CC_INTERVAL 20` — breath CC at **50 Hz** | `BreathController.ino` `[source]` |
| **KeyWI** | `si.smooth(0.996)` on breath, `si.smooth(0.99988)` on the slow pressure envelope | `melodica.dsp` `[source]` |
| **OWP 2021 (author's own)** | `breath_risetime = 5` ms between threshold breach and the first CC; `SETTINGS_NOTE_DEBOUNCE_DELAY 20` ms | `src/owp/owp.ino` `[source]` |
| **OWP 2021 synth** | `breath_ramp_rate = 8` ms amplitude ramp; 16 ms at note-off | `src/owp_synth/owp_synth.ino` `[source]` |
| MIDI itself | 3 bytes at 31250 baud ≈ 0.96 ms per CC | `[derived]` |

**Woody's ~2.8–3.1 ms budget is smaller than the smoothing filter of every
working wind controller I read, and smaller than the 5 ms delay the author's own
previous instrument inserted on purpose and found playable** `[source]`.

**The latency panic is calibrated against the wrong target.** The 5 ms figure in
`docs/reference/latency-budget.md` is described as *"roughly the line between an
instrument and a toy"* `[repo]`, and the page then reports 1.6× margin against it
as a near-miss. But the physically meaningful target is the one the same page
gives two paragraphs later — a tongue attack rising over **5–15 ms** `[repo]` —
and against that, 3 ms is fine, and the field's own practice of spending 5–20 ms
on smoothing is the empirical proof.

**Woody's filters are also very wide by comparison.** T.WI's 30 Hz corner implies
the musically useful bandwidth of breath is around 30 Hz. Woody's channel is
band-limited at **500 Hz** `[repo]` — sixteen times wider — which is bandwidth it
is paying for in noise susceptibility on a 2 m analog link rather than in
musical content.

I am **not** recommending narrowing it. The arithmetic goes the wrong way: a
100 Hz pole costs 1.59 ms of group delay against 0.32 ms at 500 Hz `[derived]`,
and Woody has already spent its delay budget on the tube. **500 Hz is a
defensible compromise.** But two things follow that the documents should say:

- ADR 0003's argument that *"the sensor only has ~159 Hz of real bandwidth, so a
  narrow channel costs nothing"* `[repo]` understates the case in a way that
  hides the tradeoff. The *signal* is ~30 Hz. The channel is 500 Hz. That is a
  deliberate purchase of ~24 dB of unnecessary noise bandwidth in exchange for
  ~1.3 ms of delay, and it is worth stating as such.
- **If the E2 restrictor measurement comes in badly, narrowing the electrical
  filter is not where the time can be recovered** — it is already the smallest
  term. The tube or the plug is where it would have to come from.

### What is actually at risk

The real hazard is not the total. It is that **Woody's delays are physical and
irrevocable where everyone else's are software**. T.WI can change `filterFreq`
from 30 to 100 in one line. Woody cannot shorten a 400 mm tube or loosen a
bonded-in PTFE plug. The latency budget already says this — *"the restrictor is
still unmeasured and is the term most able to break it"* `[repo]` — and it is
right to say it.

Prior art offers **no help at all** on this specific term, because nobody else
has a dead-ended long tube with a porous plug in it. That is Woody's own
territory and E2 is the only way to learn it. It also strengthens the case for
the repeatable time-constant self-test in §5: the number is unbounded *and* it
can degrade in service, and Woody currently plans to measure it once.

### Commercial latency, for what little it is worth

I could not find a measured figure for any commercial wind controller — the
searches returned only general perceptual guidance: recommended studio latency
around 5 ms, listener-preferred latencies of 2–40 ms depending on instrument,
and trigger-response pairs perceived as simultaneous within about 10 ± 5 ms
`[web-summary]`. **Nothing I found puts a working instrument's requirement below
about 10 ms.** Treat this paragraph as the weakest in the report.

---

## What Woody should change

Ordered by how much a human should care.

1. **Fix the gain/offset independence claim.** ADR 0006's *"the reverse ordering
   makes the two controls fight each other"* and `breath-receive-stage.md`'s
   *"the panel knobs behave independently"* are both wrong as the stage is drawn:
   the 0.437 V sensor pedestal passes the gain pot un-nulled, so the zero moves
   with gain by up to 0.44 V `[derived]`. **Either** null the pedestal ahead of
   the gain stage with a **buffered trimmer on the INA828 `REF` pin** — *not* a
   DAC channel, which rebuilds the watchdog-`CLR` hazard `[repo]`, and *not* a
   bare divider, which degrades CMRR `[repo]` — **or** delete the independence
   claim and write the WX5's iterate-gain-then-zero procedure into E10. §2.

2. **Re-derive the gain around playing pressure, not sensor full scale.** The
   fixed 2.185 puts 10 V at 6 kPa; a hard blow is 2.5–3 kPa `[source]`
   `[derived]`. The GAIN knob is absorbing a factor of two, not 0.6 %. **Specify
   the downstream pot range at roughly 0.6× to 2.5×** so it reaches both a 10 V
   full-scale at a real blow and a 5 V full-scale for a unipolar VCA. The
   unvalued block in `breath-receive-stage.md` is where this lands. §1, §11.

3. **Add a zero indicator on the module panel**, a window comparator and an LED
   on the post-OFFSET node. The EWI's whole zeroing procedure works because it
   has one `[web-summary]`. It measures the analog path, so it strengthens the
   one-authority rule rather than violating it. Without it, the player cannot
   exercise the only zero authority the analog path has. §4(a).

4. **Add the datasheet-required sensor decoupling.** 1.0 µF + 0.01 µF on VS and
   **470 pF on VOUT**; the family datasheet says specifications are *"required"*
   to be met with it `[datasheet]`. Nothing in ADR 0003 or the schematic
   specifies any `[repo]`. The 470 pF is also the RF/anti-alias pole nearest the
   source, which the design currently lacks. §16.

5. **Make the restrictor time constant a repeatable self-test.** The zero log
   cannot see a clogging PTFE plug — clogging changes the time constant, not the
   zero `[derived]` — and ADR 0006 names that failure as one the diagnostic is
   supposed to catch `[repo]`. Time the breath decay after every note release,
   baseline it at E2, log the drift. §5.

6. **Harden the power-on zero capture**: average over tens of milliseconds
   (after the 20 ms sensor warm-up `[datasheet]`), and reject a capture outside
   the 0.152–0.378 V offset window as a fault rather than seeding from it. The
   2021 code took **one sample** `[source]`, so ADR 0003's *"exactly as the 2021
   code did"* is a weaker precedent than it reads as. §4(b).

7. **Verify the 0.5 mV/K offset drift figure** from the MPXV4006DP datasheet
   (nxp.com was blocked this session). The whole "panel knob, touched once"
   argument rests on it, and the family datasheet I could read does not break out
   an offset tempco at all — only a combined ±5 % VFSS over 0–85 °C
   `[datasheet]`. §4.

8. **Buy the mouthpiece.** A melodica mouthpiece-and-hose is a commodity part,
   is what the ADDAC310 uses, is designed to be lipped around, and comes with
   530–570 mm of tube `[web-summary]`. Get three at E2 and settle the bore by
   picking one. §6.

9. **Rewrite the bleed rebuttal to answer all three questions.** The bleed hole
   vents, drains, **and compresses dynamic range** `[web-summary]`. ADR 0003
   rebuts only venting while declaring the matter closed `[repo]`. The decision
   survives — Woody has ~2× sensor headroom, so it does not need the
   compression — but the reasoning should cover what it claims to have settled.
   §6.

10. **Specify the resting slope of the tube** and put the trap at its low point.
    Gravity is every other instrument's drain mechanism and Woody's sealed tube
    cannot use it by accident `[web-summary]`. §5.

11. **Consider a curve LUT instead of a gamma**, and **default one mod channel to
    a shaped breath copy.** T.WI ships thirteen curves including four sigmoids
    that no `x^γ` can reach `[source]`; a shaped copy on a mod channel needs no
    design change `[repo]` and reproduces the Lyricon's Wind-1/Wind-2 split
    `[web-summary]`. §3.

12. **State the jack's linearity where the player will see it.** Raw linear
    pressure into a linear VCA is the "feels like a volume knob" failure ADR 0003
    itself names `[repo]`. One line on the panel or in the manual. §3.

---

## What Woody should keep

1. **The MPXV4006DP at 0–6 kPa.** KeyWI independently chose the same part
   `[web-summary]`, Gordon Good chose its GP sibling `[source]`, and the range is
   about 2× real playing pressure — headroom in the safe direction `[derived]`.
   ADR 0003's *"well chosen in 2021 and stands"* is correct.

2. **Panel GAIN and OFFSET knobs in the analog path.** The EWI has exactly two
   knobs per sensor, the WX5 has Wind Zero and Wind Gain, KeyWI has `offset` and
   `sensitivity` on two ADC pins `[web-summary]` `[source]`. This is what every
   serious wind instrument does, and Woody arrived at it independently.

3. **One zero authority per representation.** The clearest thinking in the breath
   ADRs. The deleted DAC-driven `REF` was correcting a signal firmware could not
   measure `[repo]`, and deleting it was right. Note that §2's fix does *not*
   reopen this: a fixed trimmer subtracts a known constant and is set by a human
   looking at the node it corrects.

4. **Continuous auto-zero on the digital copy, gated on sub-threshold *and*
   quiet, with the accumulated correction logged** `[repo]`. Nothing in the prior
   art is this careful — the field's state of the art is one `analogRead` at
   startup or a compile-time constant `[source]`. The gap in §5 is about *which*
   failures the log can see, not about the mechanism.

5. **The sealed dead-ended tube, and the circular-breathing argument for it.**
   The insight that the exhale path is the corners of the mouth, not the
   instrument, is correct and is not in any source I read `[repo]`. Keep the
   decision; widen the rebuttal.

6. **Analog end-to-end to the jack.** It matches the Lyricon, the only historical
   wind controller that drove analog synths `[web-summary]`, and — as §3 shows —
   it matches what the author's own 2021 rig actually did, since the shaping then
   lived in the *synth*, not the controller `[source]`. Sending raw breath and
   shaping it downstream is not a rationalisation of a loss.

7. **The porous PTFE plug doing two jobs.** ePTFE membranes are established DIY
   practice for this exact problem `[web-summary]`, and combining the restrictor
   with the moisture barrier is a genuinely good economy.

8. **The distributed-pipe correction, and damping rather than tuning.** No prior
   art exists either way, but the absence is explained by every other tube being
   flowed or bled. The revised reasoning in ADR 0003 is sound and E2's ring-down
   is the right test `[repo]`.

9. **Buy two sensors.** The family datasheet's dry-air qualification and
   fluorosilicone gel die coat `[datasheet]` make wear-part treatment the honest
   call, and ADR 0003 is right that spares are the only measure that makes the
   mechanism survivable rather than merely slower `[repo]`.

10. **The latency budget's honesty.** Replacing "10×" with 1.6× and naming the
    restrictor as the unbounded term `[repo]` was the right correction. The
    conclusion it now fears is wrong in Woody's favour — 3 ms is faster than
    every working instrument I read — but the *discipline* that produced the
    correction is the most valuable thing in these documents and should not be
    softened by this report.

---

## Sources

Read in full this session (cloned, GitHub):
- [jeffmhopkins/Open-Woodwind-Project](https://github.com/jeffmhopkins/Open-Woodwind-Project)
- [Trasselfrisyr/MiniWI](https://github.com/Trasselfrisyr/MiniWI) (incl. `Docs and references/MPX5010.pdf`)
- [ggood/BreathController](https://github.com/ggood/BreathController)
- [matthewcaren/KeyWI](https://github.com/matthewcaren/KeyWI)

Search-engine summaries only — **pages blocked by the egress proxy, not read**:
- [Gordophone: Basics of DIY Wind Controllers](https://gordophone.blogspot.com/2013/01/a-series-basics-of-diy-wind-controllers.html)
- [The KeyWI: An Expressive and Accessible Electronic Wind Instrument (NIME 2020)](https://nime.org/proc/nime2020_118/) · [project page](https://ccrma.stanford.edu/~mcaren/keyWI/)
- [Akai EWI 4000s Operator's Manual, sensor sensitivity adjustment](https://www.manualslib.com/manual/1399322/Akai-Ewi-4000s.html?page=22) · [reference manual PDF](https://cdn.inmusicbrands.com/akai/ewi-4000/ewi4000s_refmanual_revd_00.pdf_2b1b7872139bd77b89740a52cbb86d99.pdf)
- [Yamaha WX5 Owner's Manual, Wind Zero & Wind Gain](https://www.manualslib.com/manual/196987/Yamaha-Wx5.html?page=25) · [WX7 Owner's Manual](https://www.manualslib.com/manual/695127/Yamaha-Wx7.html)
- [Roland: Cleaning 'inside' the Aerophone](https://support.roland.com/hc/en-us/articles/4411183180315-Aerophone-Cleaning-inside-the-Aerophone) · [OP-AE10MP replacement mouthpiece](https://www.roland.com/global/products/op-ae10mp/)
- [Patchman Music Wind Controller FAQ](https://www.patchmanmusic.com/WindControllerFAQ.html)
- [ADDAC310 Pressure to CV](https://www.addacsystem.com/en/products/modules/addac300-series/addac310) · [Sound On Sound review](https://www.soundonsound.com/reviews/addac-system-addac310)
- [Pulp Logic Breath Control](https://pulplogic.com/product/breath-control-2/)
- [VCV Rack Voltage Standards](https://vcvrack.com/manual/VoltageStandards) · [What VCA CV input range is most preferred? — MOD WIGGLER](https://modwiggler.com/forum/viewtopic.php?t=264649)
- [Lyricons, EVIs and EWIs: The Evolution of the Electronic Wind Instrument — EMEAPP](https://emeapp.org/2024/12/17/lyricons-evis-and-ewis-the-evolution-of-the-electronic-wind-instrument/) · [Computone Lyricon MIDI/CV Driver listing](https://reverb.com/item/69578801-working-computone-lyricon-midi-driver-control-voltage-eurorack-ewi)
- [The Physiological Demands of Wind Instrument Performance, N. H. Fletcher](https://www.acoustics.asn.au/journal/2000/2000_28_2_Fletcher.pdf)
- [Fluid Dynamics — Building a better MIDI Breath Controller, Physics Forums](https://www.physicsforums.com/threads/fluid-dynamics-building-a-better-midi-breath-controller.1014166/)
- [Melodica mouthpiece + 57 cm hose, commodity replacement part](https://www.amazon.com/Melodica-Mouthpiece-Replacement-Instrument-Accessory/dp/B07CF46F6G)
- [Akai EWM1 replacement mouthpiece](https://www.sweetwater.com/store/detail/EWI-EWM1--akai-professional-ewm1-replacement-mouthpiece-for-ewi)
