# X2 — What the six jacks do, instant by instant

**Woody**, cross-cutting review. Scope: **the state of every jack at every
moment of every power, connect and fault sequence.** Nothing here is about
steady-state accuracy; it is about the transitions between states, which no
existing document walks end to end.

Sources read in full: `hardware/module/power-entry.md`,
`digital-and-supervision.md`, `pitch-stage.md`, `mod-channels.md`,
`breath-receive-stage.md`; `docs/decisions/0004`, `0005`, `0006`;
`firmware/README.md`; `hardware/bom.csv` (rows quoted where load-bearing).

No repository file outside this directory was modified. Nothing committed.

## Evidence marking

Every figure carries one of:

- **[repo]** — read out of a file named above, quoted back at it.
- **[calc]** — arithmetic on **[repo]** figures, shown inline.
- **[datasheet-gated]** — a part parameter I could **not** verify. The proxy
  blocked ti.com, analog.com and nxp.com throughout. **No datasheet number
  appears in this document.** Where a conclusion needs one, the part and the
  exact parameter are named and the conclusion is stated conditionally.
- **[from memory]** — a general engineering fact, not a number, from recall.

The brief warns that this project's honesty markers have twice been found
calibrated backwards. So: **the markers below are deliberately pessimistic.**
Anything I could not trace to a file is marked `[from memory]` even where I am
confident, and every arithmetic step is shown so it can be checked rather than
trusted. Where I found the design *right*, §7 says so — a sequencing review
that only lists faults misrepresents what is already closed.

---

## 1. The three transfer functions, and the states they can be in

Everything in the tables below comes from these. **[repo]**

```
PITCH    Vout = 2·Vdac1 − V_refP           V_refP = TRIM-OFFSET × VREFOUT ≈ 2.500 V
MOD n    Vout = 4·Vdac(n) − 3·V_ch7        V_ch7  = DAC ch7 ≈ 3.3333 V
BREATH   V_ia = −2.185·(V_BREATH − V_AGND) + V_REFB
         Vjack = −G_d · V_ia + V_knob      V_REFB = TRIM-BREATH-ZERO, 0 → +1.0 V,
                                                    set to 0.332…0.826 V at commissioning
                                           G_d ≈ 0.6 … 2.5  (panel GAIN)
```

`pitch-stage.md` gives the pitch form and `V_refP` from `VREFOUT`;
`mod-channels.md` gives `k = 3`, `R1 10 k / R2 30 k`, `V_ref = 3.3333 V` from
ch7; `breath-receive-stage.md` gives `G = 2.185`, `REF` from a buffered
`TRIM-BREATH-ZERO`, and `G_d ≈ 0.6–2.5`. **[repo]**

**The `REF` trimmer's supply is being edited as I write, and the repo currently
says both things at once** — the schematic on that page still draws it *"from
VREFOUT"*, `bom.csv` `TRIM-BREATH-ZERO` still says *"Range 0 to ~+0.6 V from
VREFOUT"*, and the page's own values table now says *"From the LM317 rail, never
`VREFOUT`"*. **[repo, all three, as of this writing]** §4.1 is written to cover
both, because which one gets built changes the failure from *dynamic* to
*static* and decides whether the breath-immunity claim is true. The pedestal is
also now a band rather than a number — **0.152–0.378 V**, needing `REF` anywhere
from **0.332 V to 0.826 V** **[repo]** — so every breath figure below is a range,
not a point.

Two facts do most of the damage in this document, and both are already written
down in the repo — just never carried through to a jack voltage:

1. **`DAC full scale = 2 × VREFOUT`, and `VREFOUT` is off until firmware turns
   it on.** ADR 0006: *"the internal reference is disabled by default and needs
   an explicit enable write at boot … the outputs sit at 0 V from rack power-on
   until firmware enables the reference."* **[repo]**
2. **`VREFOUT` feeds pitch's offset, and — depending on which of the three
   contradictory statements above is built — breath's zero too.** **[repo]**

So `VREFOUT` is a single node, controlled by one sticky bit in a **write-only,
unreadable** register, that sets the scale of five jacks and the offset of a
sixth, and may also set the zero of the one jack the design claims is immune to
it. Nothing anywhere can observe it.

### Jack voltages for each reachable DAC state **[calc]**

| DAC state | VREFOUT | PITCH | MOD 1–4 |
|---|---|---|---|
| POR / `CLR`, **reference not yet enabled** | 0 V | **0.000 V** | 0.000 V |
| POR / `CLR`, reference enabled | 2.500 V | **−2.500 V** | 0.000 V |
| All six channels at midscale | 2.500 V | **+2.500 V** | **+2.500 V** |
| All six channels at full scale | 2.500 V | **+7.500 V** | **+5.000 V** |
| Signal ch at full, ch7 still 0 | 2.500 V | — | `4(5) − 0` = +20 V → **clips ≈ +11.45 V** |
| Signal ch at 0, ch7 at 3.3333 | 2.500 V | — | **−10.000 V** |
| Reference disabled while playing | 0 V | **0.000 V** | 0.000 V |

Clip limit +11.45 V is the repo's own OPA2197-on-±12 V figure. **[repo]**

### Breath jack, knob at zero **[calc]**

| Condition | In-amp out | Jack at G_d = 0.6 | at G_d = 2.5 |
|---|---|---|---|
| Alive, no breath, `REF` trimmed | 0 V | 0 V | 0 V |
| Alive, full blow | −9.94 V | +5.96 V | +10 V (knob fits) |
| **Unplugged**, `REF` trimmed | **+0.332 to +0.826 V** | −0.20 V | **−2.07 V** |
| **Alive, no breath, `REF` collapsed to 0** | **−0.332 to −0.826 V** | +0.20 V | **+2.07 V** |
| Unplugged, `REF` collapsed to 0 | 0 V | 0 V | 0 V |
| Unplugged, **with the proposed presence tap** (§4.2) | −0.6 to −5.0 V | +0.36 V | **+1.5 to +11.45 V** |

Row 3 is the **normal idle state of the whole system** and row 4 is what
`VREFOUT` failing does to it. Both are derived from the pedestal band and the
trim range the page now specifies **[calc]**; the earlier single-point figures
(±0.437 V → ∓0.26…1.09 V) were computed against the typical pedestal only and
understate both by about 2×.

---

## 2. The scenario table

`t` is measured from the event. "Startling" = an audible artefact into a normal
patch. "Damaging" = outside a normal Eurorack input's rating, or a sustained
level that can damage a speaker or a listener's expectations of silence.

Abbreviations: **LS** = LT1641 load switch, **WD** = 74HC123 watchdog,
**OE** = 74AHCT125 output enable, **ref** = DAC internal reference.

| # | Scenario | Rail order | DAC | OE | WD | PITCH | BREATH | MOD 1–4 | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **1** | Rack on, instrument attached, toggle ON | bus +5 V first (no diode); ±12 V behind Schottky; AVDD last (LM317 needs +12 V > ≈ 6.9 V) **[calc]** | POR zero scale, **ref off** | Hi-Z until presence; **then §4.1** | untriggered | §4.1a: **0.000 V permanently** (the ref-enable write never gets through). §4.1b: 0.000 V → −2.500 V at that write → parked | knob value; **+0.20…+2.07 V** while the sensor is alive and `REF` is still 0 (§4.1b) | 0 V | **Dead** — §4.1a; **startling then dead** if §4.1b |
| **2** | Rack on, toggle OFF; toggle ON later | as #1 but umbilical branch dead | POR zero, ref off | Hi-Z | untriggered | **0.000 V** held indefinitely | knob value | 0 V | Same trap as #1 at the toggle, plus §4.3 |
| **3** | Rack on, nothing plugged in | as #1 | POR zero, **ref never enabled** | **never asserted** | never triggered | **0.000 V — permanently** | **knob value, unbounded** | 0 V | **Startling** — §5.1, §5.2 |
| **4** | Umbilical hot-plugged into a running module | umbilical node steps 0 → 12 V **un-ramped** | zero scale | asserts mid-frame | starts on first buffered CS | 0 → −2.5 V step; then §4.3 transient | 30 ms rise to rest | **±10 V transient, ~100–200 µs** | **Startling; §4.3, §5.3** |
| **5** | Umbilical unplugged mid-note | umbilical only | holds last value 99 ms, then `CLR` | drops ~30 ms after unplug | fires at t ≈ 99 ms | held note for 99 ms, then **−2.500 V** | decays τ ≈ 30 ms to **−0.20…−2.07 V** | held, then 0 V | **Safe** (but see §5.2 on the negative rest) |
| **6** | MCU hangs mid-note (WD fires) | none | holds, then `CLR` | stays asserted | fires at 99 ms | note held 99 ms, then **−2.500 V** | **follows the player** | 0 V | **Safe if the player stops blowing; startling if not** — §5.4 |
| **7** | MCU resets and reboots mid-note | none | `CLR`, then §4.3 | **stays asserted throughout** | fires at 99 ms | −2.500 V for the whole boot (0.3–1 s), then §4.3's transient | unaffected | 0 V, then **±10 V transient** | **Startling** — §4.3, §5.5 |
| **8** | LS latches off on a fault mid-note | umbilical node decays 163 V/s **[calc]**; MCU alive ~21 ms | keeps being written for ~21 ms by a **browning-out** MCU | still asserted (sensor alive) | fires ~120 ms after latch-off | note held ≈ 120 ms then −2.500 V | decays to −0.20…−2.07 V | held then 0 V | **Safe, except §5.6** (garbage SPI on the way down) |
| **9** | Rack powers OFF while playing | **module +12 V dies first (~26 ms), −12 V last (~56 ms)** **[calc]** | AVDD collapses with +12 V | released when LM311 dies | dies with its rail | all six jacks pulled toward the **surviving −12 V rail** | same | same | **Startling, possibly damaging** — §4.4 |
| **10** | Flash / OTA / NVS stall > 99 ms | none | `CLR` then §4.3 | asserted | fires | note → **−2.500 V** for the stall, then recovery transient | unaffected | 0 V, then **±10 V transient** | **Startling** — §5.7 |
| **11** | Bus +5 V fails, ±12 V survives | bus +5 V only | undriven, then `CLR` | **unpowered but OE held low by a live LM311** | fires at 99 ms | −2.500 V | unaffected | 0 V | **Probably safe, by an unverified mechanism** — §4.5 |
| **12** | Instrument browns out but does not reset | umbilical sags | **keeps being written with possibly-corrupt data** | asserted | **kept fed by CS edges** | **whatever garbage is written — up to +7.5 V** | follows the sensor | **up to ±11.45 V** | **The watchdog's blind spot** — §4.6 |

### The three claims, tested

| Claim | Verdict |
|---|---|
| *"Zero-scale reset equals 0 V on the mods"* (`mod-channels.md`, ADR 0006) | **True only for an exact, simultaneous zero on all six channels.** False at midscale (+2.500 V), false at full scale (+5.000 V), and false during **every** exit from `CLR`, which cannot be simultaneous. §4.3, §5.8 |
| *"`CLR` parks pitch subsonic"* (ADR 0004, `bom.csv` `U-WATCHDOG`) | **False as stated.** Before the ref-enable write it parks at **0.000 V** — a VCO's base note. After it, −2.500 V, which is a tritone below the lowest *playable* note, not subsonic; whether it is audible is a property of the patch, not of the module. §5.1 |
| *"An analog breath path cannot latch"* (ADR 0004, `breath-receive-stage.md`, `firmware/README.md`) | **False as currently drawn and BOM'd** — the breath zero is derived from `VREFOUT`, a DAC node set by a sticky, unreadable register, so losing it puts **+0.20 to +2.07 V** of standing breath on the jack with nobody blowing and no watchdog able to see it. **Becomes true** if the page's new *"From the LM317 rail"* line is landed everywhere. Independently, the proposed presence tap can put **+11.45 V** on the same jack. §4.1, §4.2, §4.6 |

---

## 3. Rail ordering, derived once

Used by scenarios 1, 3, 9 and 11. **All currents are estimates and must be
measured at E7 before any of the timing below is trusted** — the *ordering*
conclusions are robust to a factor of two, the millisecond figures are not.

**Module analog +12 V**, behind `D1` / `FB1` / `C1 47 µF`: **[repo]** for the
topology and part values.

| Load | mA | Basis |
|---|---|---|
| LM317 set divider, 150 Ω | **8.3** | `1.25 V / 150 Ω` **[calc]** from `bom.csv` `R-REG-SET` **[repo]** |
| DAC AVDD via the LM317 | ~1.5 | **[datasheet-gated]** — DAC8568C AVDD supply current |
| 5 × OPA2197 (10 halves) V+ | ~6 | **[datasheet-gated]** — OPA2197 I_Q per channel |
| INA828 | ~1 | **[datasheet-gated]** |
| LM311 V+ | ~5 | **[datasheet-gated]** |
| **Total** | **≈ 22 mA** | |

**Module −12 V**, behind `D3` / `C3 47 µF`: the same op-amp halves and the
INA828 and the LM311's V− — **≈ 10 mA**, because the LM317 divider, the DAC and
the LM317 itself are all on +12 V only.

```
+12 V decay:  22 mA / 47 µF = 468 V/s   →  12 V to LM317 dropout (≈6.9 V) in 10.9 ms; to 0 in 25.6 ms
−12 V decay:  10 mA / 47 µF = 213 V/s   →  −12 V to 0 in 56 ms
Ratio:        2.2 : 1                                                                 [calc]
```

**Bus +5 V**, behind `FB4` / `C4 47 µF`, no diode: load is the 74AHCT125 plus —
per `power-entry.md` and `digital-and-supervision.md` — the `OE` pull-up
(0.5 mA) and the panel LED (3.8 mA). **[repo]** ≈ 6 mA → **128 V/s**.

**Umbilical / instrument node**, `C = 2.2 mF` at the far end **[repo]**, load
359 mA in typical play **[repo]**:

```
359 mA / 2.25 mF = 160 V/s
11.4 V → 8.0 V (buck dropout, ADR 0005)  =  3.4 / 160  =  21 ms          [calc]
8.0 V → 7.2 V (REF5050 dropout, ADR 0004) =  0.8 / 160  =  a further 5 ms
```

**Order of death on a rack power-down [calc]:**

```
  module analog +12 V   ≈ 26 ms   ← first
  instrument MCU        ≈ 21 ms   (comparable; which wins depends on E7)
  bus +5 V              ≈ 39 ms
  module analog −12 V   ≈ 56 ms   ← last
```

**This is the single most important ordering result in the document**, and
nothing in the repo states it. Every op-amp in the module spends roughly
**30 ms with `V+` at or near zero and `V−` between −6 V and −8 V.** §4.4.

**Order of birth on a rack power-up [calc]:** bus +5 V first (no diode, no
regulator), ±12 V behind one Schottky drop, **AVDD last** — the LM317 cannot
regulate until +12 V exceeds about 6.9 V. The op-amps are alive before the DAC
is. §5.9.

---

## 4. The dangerous sequences

### 4.1 — SHOWSTOPPER: the trim inverts the presence detect, and the presence detect gates every DAC jack

There are two failures here, one unconditional and one that depends on an
unresolved question. Both end with the module refusing to pass SPI.

#### 4.1a — Unconditional: the detect is backwards

`TRIM-BREATH-ZERO` nulls the sensor pedestal at the in-amp's `REF` pin. That is
its entire job **[repo]**. The consequence for the comparator **[calc]**:

| State | In-amp output, `REF` **grounded** (old) | In-amp output, `REF` **trimmed** (now) |
|---|---|---|
| Cable unplugged | 0 V | **+0.332 to +0.826 V** |
| Instrument alive, at rest | −0.332 to −0.826 V | **0 V** |

The split did not collapse — it **inverted**. A threshold of −200 mV, sitting
below both of the new values, reads **"absent" in both states**. `OE` is never
asserted, the 74AHCT125's outputs stay Hi-Z, the DAC never receives a word, the
'123 is never triggered, `CLR` stays asserted, and **all five DAC jacks sit in
their park state forever**. The panel LED never lights.

`digital-and-supervision.md` half-found this — *"both states sit at 0 V and the
detect stops working"* **[repo]** — and the diagnosis is wrong in a way that
matters: they are not both 0 V, and the failure is not a loss of sensitivity but
a reversal. A reviewer who believes the states are degenerate looks for a more
sensitive comparator. The circuit needs a **different sign**, and §4.2 shows the
proposed replacement does not work either.

`bom.csv` `U-PRESENCE` and `R-PRESENCE` still carry the corrected description
**[repo]**, so the intent is recorded — but `R-PRESENCE`'s own resistor values
still implement the old arrangement (§4.2a). Nothing in the repo currently
describes a presence detect that works.

#### 4.1b — Conditional: if `REF` comes from `VREFOUT`, the failure becomes dynamic

If the trimmer is supplied from `VREFOUT` (the schematic on that page and
`bom.csv` still say it is **[repo]**), scenario 1 runs like this:

1. Rack up. DAC at POR zero scale, **reference off**, so `VREFOUT = 0` and
   therefore `V_REFB = 0` **[repo]** + **[calc]**.
2. LS ramps. The instrument's REF5050 and MPXV4006DP come alive **within the
   50–100 ms ramp and before the MCU has booted**, because they hang straight
   off umbilical +12 V with no MCU in the path **[repo]** (ADR 0005 power tree).
3. The pedestal reaches the module. In-amp output = `−2.185 × (0.152…0.378) =
   −0.332 to −0.826 V` **[calc]** — always below −200 mV. **Presence asserts,
   `OE` enables, the LED lights, the module works.**
4. The MCU finishes booting (0.3–1 s **[from memory]** for ESP-IDF with OTA
   rollback and NVS) and issues the write ADR 0006 insists it must issue:
   *"Enable the DAC's internal reference explicitly at boot"* **[repo]**.
5. `VREFOUT` steps 0 → 2.500 V. The trimmer delivers its set voltage to `REF`.
   The in-amp output moves to **0 V** — *exactly as designed* **[repo]**.
6. 0 V is above the −200 mV threshold. **Presence deasserts. `OE` goes high.
   SPI stops reaching the DAC.** The 1 MΩ hysteresis latches it.
7. 99 ms later the watchdog asserts `CLR`. Pitch → −2.500 V, mods → 0 V, LED
   out. Permanently.

**The module disables itself with its own first command**, through a loop that
runs DAC register → `VREFOUT` → breath `REF` → in-amp output → comparator →
`OE` → SPI to that same DAC. On the bench at E7 this presents as *"it worked for
a second and then stopped"*, which points at firmware. It is not firmware.

And on the same conditional, **the third design claim fails**: the breath jack's
zero is a DAC-derived node, so any loss of `VREFOUT` (§4.6) shifts the jack by
**+0.20 to +2.07 V** with nobody blowing **[calc]** — a latched level the player
is not producing, which is precisely what ADR 0004 says an analog path cannot
do **[repo]**.

#### The fix

**Source `TRIM-BREATH-ZERO` from the LM317's 5.21 V rail, not `VREFOUT`.** The
breath page's values table now says exactly this **[repo]**; the schematic on
the same page and the `bom.csv` row do not. **Land it in all three.** It breaks
the loop, deletes 4.1b, and makes *"no DAC register touches the breath jack"*
true for the first time. Cost is tempco on a channel ADR 0006 classes as
**Trimmed**, not **Calibrated** **[repo]**: a 1 % shift in the LM317 output
moves the null by ~6 mV → ~13 mV at the in-amp output → **0.13 % of breath full
scale** **[calc]**. Irrelevant.

That leaves 4.1a, which is independent and needs §4.2.

**Severity: SHOWSTOPPER either way.** Nothing is destroyed; the module simply
cannot complete a boot with the instrument attached.

### 4.2 — SHOWSTOPPER: the proposed fix cannot work with an LM311

`digital-and-supervision.md` and `bom.csv` `R-PRESENCE` both propose the same
repair: *"sense the module end of `BREATH` against `AGND` through the existing
10 k protection resistors: unplugged that node is at 0 V (held by the 1 M bias
pair), alive it is at the sensor's +0.2 V pedestal. Threshold ~+100 mV …
1 M from output to IN+ for hysteresis."* **[repo]**

Three independent reasons it does not work as written.

**(a) The threshold divider does not produce the threshold, and the threshold
itself has no margin.** `R-PRESENCE` is
specified as `100 k / 10 k / 1 M` **[repo]**. From either 5 V rail:

```
5.21 V × 10 k / (100 k + 10 k) = 0.474 V                                   [calc]
```

474 mV, against a pedestal whose **worst case is 152 mV** **[repo]**. The
comparator reads "absent" in both states. The values are left over from the
−200 mV arrangement. And the proposed +100 mV threshold has only **52 mV** of
margin against a sensor at the bottom of its own spec band **[calc]** — before
any of (b) or (c).

**(b) A bipolar comparator cannot sense 200 mV across a 1 MΩ source.** The
proposed node is the in-amp's `IN−` pin. Its source impedance is **11 kΩ when
plugged** (instrument buffer + `R1 1 k` + `R2 10 k`) and **1 MΩ when unplugged**
(`R4` alone). **[repo]** The LM311 is a bipolar-input part **[from memory]**;
its input bias current is **[datasheet-gated]** — *name it: LM311 `I_IB`, typ
and max, and its direction*. For any bias current in the hundreds-of-nanoamps
class:

```
I_IB × R4 = 100 nA × 1 MΩ = 100 mV        (250 nA → 250 mV)               [calc]
```

The error the comparator injects into the unplugged state is **larger than the
entire signal it is trying to detect** — the pedestal's worst case is
**152 mV** **[repo]**, against a bias error of 100–250 mV. There is no threshold
that works.
*Gate:* if `I_IB` is below ~10 nA the objection vanishes — but that is not what
a bipolar comparator does, which is why this needs the datasheet before any
threshold is chosen.

**(c) The hysteresis is applied to the signal node, whose impedance changes
100×.** `R-PRESENCE` puts 1 MΩ *from the output to `IN+`* **[repo]**, i.e. onto
the sense node itself. The LM311's open collector idles at ~5 V (pulled up by
`R-OE-PU 10 k`; the LED stops conducting above ~3.2 V and the node reaches the
rail) **[calc]**.

```
Plugged   (source 11 kΩ):  hysteresis ≈ 5 V × 11 k / 1 M   = 55 mV        [calc]  ← correct
Unplugged (source 1 MΩ):   node = 5 V × 1 M / (1 M + 1 M)  = +2.5 V       [calc]  ← the feedback
                                                                              owns the node
```

Unplugged, **the detect's own feedback drives the node harder than the cable
state does.** Two outcomes, and which one occurs depends on the final network
(*"Final values at E10"* **[repo]**):

- If it settles "absent" (output high), the node sits at **+2.5 V**, the in-amp
  sees it as breath, `V_ia = −2.185(2.5) + 0.437 = −5.02 V` **[calc]**, and the
  **BREATH jack sits at +3.0 V to +12.6 V, clipping at ≈ +11.45 V** **[calc]**.
  **A rail on a jack, in the system's most common idle state.**
- If it chatters at the threshold, the node sits near +0.47 V and the jack sits
  at **+0.36 to +1.5 V** **[calc]**, with `OE` toggling at the chatter rate.

Expert Sleepers ships 1 MΩ of hysteresis on this comparator **[repo]** — around
a **low-impedance** node. The value does not transfer to a node biased by 1 MΩ.

**Fixes:** hysteresis to the *threshold* input, never the signal input; buffer
the tap with the one spare OPA2197 half `bom.csv` `U-OPA-PITCH` records
**[repo]**; and/or use a CMOS-input comparator whose bias current is picoamps,
which removes (b) and (c) together. **Re-derive the threshold divider.**

### 4.3 — HIGH: every exit from `CLR` throws ±10 V at the four mod jacks

**Six channels cannot be updated simultaneously.** No `LDAC` line appears in
`digital-and-supervision.md`'s schematic — the umbilical carries `SCLK`, `MOSI`,
`CS` only **[repo]**, and only `SCLK / DIN / SYNC / CLR` reach the DAC. So each
channel updates as its own 32-bit word lands.

`CLR` clears every channel, **including ch7**, and firmware then refreshes all
six *in some order* (`firmware/README.md`'s statelessness rule **[repo]**). For
the whole of that pass the offset and the signals disagree:

```
ch7 written last :  4·Vdac − 3(0)      = up to +20 V  → clips ≈ +11.45 V   [calc]
ch7 written first:  4(0)  − 3(3.3333)  =      −10.000 V                    [calc]
```

**No ordering avoids it.** Duration: six words × 32 bits at 2 MHz **[repo]** =
96 µs of clocking, so **≈ 100–200 µs** with inter-frame gaps **[calc]**.

Into a VCA: a click. Into a trigger or gate input: **a spurious trigger.** Into
a quantiser: a spurious note. And it happens on **every** hot-plug (#4), **every**
watchdog recovery (#6, #10), and **every** instrument reboot (#7) — the exact
events after which a player is most likely to be listening.

`firmware/README.md` documents the *permanent* version of this bug (ch7 never
refreshed → jacks pinned at +11.45 V) and closes it with the statelessness rule
**[repo]**. The per-pass transient is the same arithmetic one loop iteration
wide and is **not** closed by that rule.

**Fixes:** use the DAC8568's software-`LDAC` register so the six channels update
on one command — **[datasheet-gated]**, *name it: DAC8568 `LDAC` register and
the "write to input register" vs "write and update" command encodings*; or wire
the physical `LDAC` pin, which the schematic currently leaves unaccounted for
and which should be resolved before layout either way.

### 4.4 — HIGH: on rack power-down all six jacks are pulled to the negative rail

Scenario 9, which the repo does not address anywhere. From §3 **[calc]**:
**+12 V dies at 2.2× the rate of −12 V**, because +12 V carries the LM317's
8.3 mA divider, the DAC, and the LM311's positive supply while −12 V carries
none of them.

```
t = 11 ms   V+ = 6.9 V   V− = −9.7 V    AVDD leaves regulation
t = 20 ms   V+ = 2.6 V   V− = −7.7 V    DAC below any usable supply
t = 26 ms   V+ = 0 V     V− = −6.5 V    op-amps have a negative supply only
t = 56 ms   V+ = 0 V     V− = 0 V
```

An op-amp whose input sits above its own `V+` does not hold its output
mid-scale; it saturates, usually to the surviving rail, and some parts invert
phase on the way **[from memory]**. **[datasheet-gated]** — *name it: OPA2197
behaviour with `V+` below the input common-mode range; output state and phase
inversion.* The `D-JACK-CLAMP` BAV99s clamp to the rails **[repo]**, so they do
not oppose an excursion *toward* a rail.

**Expected: all six jacks swing to somewhere between −5 V and −8 V for roughly
30 ms on every rack power-down**, through `R-OUT-PROT 1 k`. A 1 kΩ source at
−8 V is 8 mA into a shorted input — not damaging to a normal Eurorack input
**[from memory]** — but it is a substantial thump through any VCA that is open,
and it is the last thing the rack does before going quiet. It is also the one
sequence where the module actively drives a jack somewhere no firmware, no
watchdog and no `CLR` chose.

**Fix, one part:** make the two rails decay together by matching `C / I`.

```
For equal dV/dt:   C₊ / C₋ = I₊ / I₋ = 2.2                                 [calc]
C1 = 100 µF against C3 = 47 µF  →  220 V/s vs 213 V/s                      [calc]
```

`power-entry.md` already notes the entry bulk is 2–5× the surveyed norm
**[repo]**, so raising `C1` is free in intent if not in board area; dropping
`C3` to 22 µF works identically (455 vs 468 V/s **[calc]**) and is cheaper.
**Measure the two rail currents at E7 first** — the ratio is the whole design
input.

### 4.5 — MEDIUM: the bus +5 V fail-safe rests on an unverified part property

`power-entry.md`: *"if bus +5 V dies, the buffer is unpowered and its outputs
are off anyway."* **[repo]** That is the claim scenario 11 rests on, and it is
not established.

With bus +5 V at 0 V and ±12 V alive, the instrument keeps driving three 3.3 V
logic lines into the 74AHCT125's inputs. Whether those inputs clamp to a dead
`VCC` — and therefore whether the part parasitically powers itself to roughly
`3.3 − V_diode ≈ 2.6 V` **[calc]** — is exactly **[datasheet-gated]**: *name it:
74AHCT125 `I_off` / partial-power-down specification, and whether the input
structure includes a clamp diode to `VCC`.* The AHC/AHCT families are generally
**not** specified for partial power-down **[from memory]**, which is why this
needs checking rather than asserting.

If it does parasitically power:

- `OE` is **pulled low by the LM311**, which is on ±12 V and still alive, so the
  buffer is *enabled* on a ~2.6 V rail.
- The DAC's logic-high threshold is `0.7 × AVDD = 0.7 × 5.21 = 3.65 V`
  **[calc]** (**[datasheet-gated]** — *name it: DAC8568 `V_IH` as a fraction of
  AVDD*). A 2.6 V "high" **never clears it**.
- So the DAC sees every line as low or indeterminate. Framing is lost, and a
  mis-framed DAC8568 word is the sticky class `digital-and-supervision.md`
  already names: software reset, clear-code register, internal-reference enable.
  **[repo]**

The watchdog probably saves the outputs (no valid `CS` edges → `CLR` at 99 ms),
so the *jacks* land safe. What does not land safe is the **DAC's configuration**,
and §4.6 is what that costs.

The page's stated design goal — *"a rack +5 V glitch must not be able to clear
the outputs mid-phrase"* **[repo]** — is met. But a +5 V glitch can do something
strictly worse than clearing them: it can **write** them, and write registers
nothing can read back.

**There is also a live contradiction about which rail `OE` and the LED sit on.**

| Source | `R-OE-PU` and the panel LED |
|---|---|
| `power-entry.md`, `digital-and-supervision.md` | **bus +5 V** — *"pulling them to a higher rail would push the AHCT125's input clamps"* **[repo]** |
| `bom.csv` `R-OE-PU` | **"FROM THE LM317'S 5.21 V, NOT BUS +5 V — the supervision must not [sit on the bus rail]"** **[repo]** |

Both arguments are correct and they are **mutually exclusive as long as the
'125 sits on the bus rail**. Pulling `OE` to 5.21 V against a 5.00 V `VCC` is
the smaller version of the +12 V bug `power-entry.md` congratulates itself for
finding; leaving supervision on the bus rail is the failure `bom.csv` objects
to. The contradiction is evidence for the resolution:

**Recommendation: move the 74AHCT125 onto the LM317's 5.21 V rail, and drop the
bus +5 V dependency entirely.**

- Satisfies both arguments at once: one rail, no skew, no cross-clamping.
- Deletes scenario 11 outright and with it §4.5 and the `I_off` question.
- Deletes the undiode'd bus +5 V pin that ADR 0004 accepts as an acceptable loss
  on a reversed ribbon **[repo]** — there would be nothing on it.
- The '125 still clears the DAC's `0.7 × AVDD` threshold, because it would be
  driving from *the same rail that sets that threshold* — a better guarantee
  than the present arrangement, not a worse one.
- Cost: LM317LZ load goes from the BOM's *"~13 mA, ~90 mW"* **[repo]** to
  roughly 27 mA, i.e. `(12 − 5.21) × 27 mA = 183 mW` in a TO-92 **[calc]**.
  **[datasheet-gated]** — *name it: LM317LZ `θ_JA` in TO-92 and its 100 mA
  rating.* If that is tight, a TO-252 part or a small LDO solves it.
- It contradicts ADR 0005's *"the level shifter's rail is a requirement, not an
  option"* **[repo]** — but that passage justifies the bus rail as *free and
  convenient*, not as necessary. This is a decision to revisit, not physics to
  overturn.

### 4.6 — HIGH: the one drone the watchdog cannot see

The watchdog is retriggered from **`CS` edges**, not from valid frames
**[repo]**. ADR 0004 specifies the intent as *"when no **valid frame** has
arrived for N milliseconds"* **[repo]**; the implementation counts activity.
The gap between those two sentences is where scenario 12 lives.

**A browning-out but un-reset MCU keeps toggling `CS`.** The watchdog is fed.
Whatever the DAC receives is latched. Reachable end states **[calc]**, all held
**indefinitely**:

| Corruption | PITCH | MOD 1–4 |
|---|---|---|
| Internal reference disabled | **0.000 V** — a VCO's base note | 0 V |
| Clear-code register set to full scale, then `CLR` | **+7.500 V** | **+5.000 V** |
| Clear-code register set to "ignore `CLR`" | **the watchdog stops working entirely** | ditto |
| Channels power-down commanded | §5.9 — op-amp inputs undefined | ditto |

**[datasheet-gated]** for all four — *name them: DAC8568 clear-code register,
its power-on default and its full option set; the internal-reference enable
command; the power-down command and its output-termination options (1 kΩ /
100 kΩ / Hi-Z); and whether a 32-bit frame with an unrecognised command field is
ignored or acted on.* I will not guess the encodings. But the **structure** of
the hazard is established from the repo alone: `digital-and-supervision.md`
states that a DAC8568 frame carries the software reset, the clear-code register
and the internal-reference enable, and that a mis-framed word is a **sticky**
failure the 4 kHz refresh does not clear **[repo]**.

Three things make this worse than it looks:

1. **Reference-disable is the worst case and is completely silent.** It puts
   pitch at 0.000 V *and* — while `REF` still hangs off `VREFOUT` — simultaneously
   shifts the breath jack up by **+0.20 to +2.07 V** (§1) — **a VCA held open with
   a VCO sitting on a note.** Every other
   failure in this design ends in silence. This one ends in a drone, which is
   precisely the failure ADR 0004 declares unacceptable **[repo]**. And the
   watchdog cannot see it, because `CS` is still toggling.
2. **The corruption outlives the instrument.** The DAC is powered by the rack;
   the instrument is powered through the load switch. Unplugging, rebooting or
   power-cycling the **instrument** does not clear a sticky DAC register. **Only
   a rack power cycle does.** Nothing in the repo says this.
3. **The mitigation is already written down but is not sized for it.**
   `firmware/README.md`: *"refreshing the reference-enable and clear-code
   registers periodically costs a word every few thousand passes"* **[repo]**.
   A few thousand passes at 250 µs is **~1 second** **[calc]** — a second of
   drone per event. Recommend refreshing both registers **every pass** (the
   latency budget books six words and five are written **[repo]**; there is room
   for one, not three) or at minimum every 10 ms.

**The structural fix is a readback, and the cable no longer has room for one.**
ADR 0004 deleted `MISO` and the statelessness rule is the compensation
**[repo]**. Statelessness closes *"firmware forgot to write it"*; it does not
close *"the module received something firmware never sent."* A single line
reporting `CLR` state and reference-enable would close scenario 12, §4.1b and
§4.5 at once — but the revised conductor budget is *"Eight of eight"* with the
spare consumed **[repo]**, so it would have to displace something or run
half-duplex on `MOSI`. **Decide this before the umbilical is terminated**, not
after; it is the one thing on this list that cannot be retrofitted.

**And `CS` is twisted with `MOSI`.** ADR 0004's earlier section promises *"each
signal sits against a ground in its own twisted pair"*; its revised budget pairs
`MOSI / CS` **[repo, same ADR]**. So the one conductor whose stray edges cause
**sticky, unrecoverable** DAC corruption is capacitively coupled, over 2 m, to
the fastest-switching line in the cable, with no ground between them. The 220 Ω
source termination on `MOSI` **[repo]** limits the aggressor's edge rate and is
the right instinct, but the pairing choice itself should be revisited at E11
with a logic analyser: `CS` wants a ground partner more than `MOSI` does.

---

## 5. The rest, in less detail

### 5.1 — `CLR` does not park pitch subsonic

Two separate failures of the claim.

**Before the ref-enable write, pitch is at 0.000 V, not −2.500 V.** ADR 0006's
own power-on table says *"Pitch: bottom of its range, below −2 V. Subsonic. A
VCO there is inaudible"* **[repo]** — and eleven lines below it, the same
section says *"the outputs sit at 0 V from rack power-on until firmware enables
the reference"* **[repo]**. Both cannot be true. The arithmetic settles it: with
`VREFOUT = 0`, `Vout = 2(0) − 0 = 0.000 V` **[calc]**. **0 V is a VCO's base
note** — the single most audible place on the whole −2…+7 V range. In scenario 3
this is permanent.

**After the ref-enable write, −2.500 V is not subsonic either.** It is 0.5 V
below the specified bottom of the range **[calc]** — a tritone below the lowest
note the instrument can play. Whether that is inaudible depends entirely on how
the player tuned the VCO, which is not a property the module controls. The claim
should be restated as what it actually is: *"`CLR` parks pitch at the bottom of
its range, half an octave below the lowest playable note. Audibility depends on
the patch; the thing that makes it silent is breath falling to rest, not pitch
falling low."*

That restatement matters because the real silencer is breath — and §4.1, §4.2
and §4.6 are all ways breath fails to fall to rest.

### 5.2 — Breath's power-on state is a knob, not 0 V

ADR 0006's power-on table says *"Breath: 0 V. The receiver's differential
pulldown holds it there"* **[repo]**. The pulldown (`R4`/`R5`) holds the
**in-amp's inputs** at `AGND` **[repo]**. The **jack** is two stages later,
downstream of the panel OFFSET knob, which is a performance control that does
not reset **[repo]**. So at every power-on with no instrument, the breath jack
sits at whatever the player last left OFFSET at — anywhere in the downstream
stage's range.

Harmless in most patches; but the table states a guarantee the circuit does not
provide, and a reviewer reading that table would not go looking for §4.2's +3 V
to +11.45 V, which arrives at the same jack by the same route.

Separately: unplugged, with the trim active, the jack rests at **−0.20 to
−2.07 V** **[calc]** — *negative*, on a jack specified 0–10 V **[repo]**, and up
to a fifth of full scale.
Harmless into a VCA; wrong into anything expecting a unipolar source; and it
contradicts ADR 0005's *"an instrument which is switched off — or unplugged —
presents 0 V"* **[repo]**, which was written when `REF` was grounded.

### 5.3 — Hot-plug is the un-ramped case, and it is not analysed

`power-entry.md` sizes the load switch against a **ramped** start: 0.53 A at
50 ms, *"a normal start never enters current limit"* **[repo]**. That analysis
applies to *toggle-on-after-plug*. **It does not apply to hot-plug**, which the
brief states is a requirement and which `digital-and-supervision.md` confirms is
a normal operating mode (*"module alive, DAC alive, and SCLK/MOSI/CS floating …
is the state the instrument spends most of its life in"* **[repo]**).

Plugging into a module whose toggle is already on connects 12 V to a discharged
2.2 mF through a **fully enhanced** FET. Current is limited only by the LT1641
sense loop:

```
1.0 A into 2.2 mF to 12 V  =  26 ms                     [repo, power-entry.md]
12 V × 1.0 A × 26 ms       =  0.31 J into the FET       [calc]
Timer 50 ms > 26 ms → the part does not latch off       [repo]
```

So it survives — but **the FET meets its worst single pulse on every ordinary
connection**, not only on faults, and the 0.6 J SOA sizing **[repo]** is being
spent as routine duty rather than as margin. Additionally, the initial di/dt
before the sense loop responds is limited only by layout inductance **[from
memory]**, and that spike is drawn from the shared rack +12 V pin — `D1` and
`C1` protect *this* module's analog rail **[repo]**, but not the other modules
in the case.

**[datasheet-gated]** — *name them: LT1641-1 UVLO threshold, current-limit loop
response time, foldback characteristic, and whether a latch-off requires an `ON`
pin cycle to reset* (the last is already flagged as unknown in `power-entry.md`
**[repo]**).

Also unstated anywhere: **etherCON/RJ45 contacts are not sequenced.** There is
no first-make/last-break ground. If `+12 V` mates before `PWR_GND`, the
instrument's local ground is dragged up and the return path is whatever else is
connected — `AGND` (a precision sense conductor behind 10 kΩ), and the three SPI
conductors into the 74AHCT125's input clamps. **[datasheet-gated]** — *name it:
the etherCON insert's contact make/break sequencing, if any.* The mitigation is
cheap and should be decided before layout: series resistance and clamps sized
for the SPI conductors, or a documented "toggle off before plugging" procedure
with the panel legend to match.

### 5.4 — The watchdog is a 99 ms glissando, not an instant mute

Scenarios 5, 6, 8, 10 all end the same way: the note is **held for up to 99 ms**
and then pitch jumps to −2.500 V while the mods jump to 0 V. If the player has
stopped blowing, breath has already closed the VCA and none of it is heard —
that is the designed behaviour and it works.

If the player has *not* stopped blowing — an MCU hang mid-phrase is exactly the
case where they have not — the jump is fully audible: a held note, then a drop
of up to 9.5 V on the pitch jack in one step, through a 15.9 kHz reconstruction
pole **[repo]**, i.e. instantaneous. Plus every mod channel stepping to 0 V
together.

Not a defect — it is the right trade against a permanent drone — but it should
be *stated*, because §4.3's ±10 V recovery transient lands on top of it when the
instrument comes back, and the two together are what E10 will actually hear.

### 5.5 — MCU reset passes a glitch straight through an enabled buffer

Scenario 7. During an MCU reset the instrument's SPI pins go high-Z **[from
memory]** and the module-side pulls take over: `CS` high, `SCLK`/`MOSI` low
**[repo]**. No edges → watchdog fires at 99 ms → safe park. That part works.

But **the buffer is still enabled throughout**, because the REF5050 and the
sensor are powered from umbilical +12 V and never noticed the MCU resetting
**[repo]**. So any glitch the ESP32-S3 produces on `CS` during reset or during
strapping-pin evaluation reaches the DAC's `SYNC` directly. `bom.csv`
`R-SPI-PULL` states the hazard precisely — *"a stray CS edge latches garbage
into the pitch DAC"* **[repo]** — but the pulls and the OE gating were both
designed for the *instrument absent* case, and neither covers *instrument
present, MCU resetting*.

### 5.6 — A browning-out instrument writes to the DAC for ~21 ms

Scenario 8. After the load switch latches off, the instrument's 2.2 mF keeps the
MCU alive for **21 ms** (§3) while the umbilical node falls from 11.4 V to the
buck's 8 V dropout **[calc, repo]**. Throughout that window the buffer is still
enabled (the sensor is still alive — ADR 0004 makes exactly this point, that the
REF5050 outlives the buck **[repo]**), and the MCU is writing SPI from a
collapsing rail. Every word in that window is a candidate for §4.6's sticky
corruption, and unlike every other path into §4.6, this one **leaves the
corruption behind after the instrument has gone dark** — so the next connection
starts from a poisoned DAC.

### 5.7 — A config save is a mid-phrase pitch drop

Scenario 10 is already identified in `digital-and-supervision.md` (*"An ESP32-S3
NVS commit or OTA write disables the instruction cache … A config save that
overruns 99 ms would assert `CLR` mid-note"* **[repo]**). What is not stated is
that ADR 0005's load table contains a row for **"Typical + live config over
WiFi"** **[repo]** — live configuration *while playing* is a designed operating
mode, not an edge case, and the real-time board owns both NVS and the DAC loop
**[repo]**. So this is a scheduled collision, not a hypothetical. Jack
consequence: pitch → −2.500 V, mods → 0 V for the stall, then §4.3's ±10 V
transient on recovery.

The prescribed fix (DAC service routine in IRAM **[repo]**) is right and should
be promoted out of "Still open".

### 5.8 — The two-resistor mod stage traded away a safety property

`mod-channels.md` claims *"Crucially the safe-state property survives. On `CLR`
both `Vdac` and `V_ref` go to zero, so `Vout = 0`."* **[repo]** True, but
narrower than the property it replaced.

```
Four-resistor difference amp:   Vout = 4·(Vdac − V_ref)     → 0 V for ANY uniform state
Two-resistor, k = 3:            Vout = 4·Vdac − 3·V_ref     → Vout = X for a uniform X   [calc]
```

The old topology parked the mods at 0 V whether the DAC reset to zero scale,
midscale, or anything else, because it subtracted. The new one only parks them
at 0 V for an **exact zero**. At midscale all four jacks sit at **+2.500 V**
**[calc]**; at full scale, **+5.000 V**.

That matters because ADR 0006's grade argument was built on the old topology:
*"Taking the offset from a DAC channel dissolves it"* — dissolves the
zero-scale-vs-midscale choice **[repo]**. Under `k = 3` **it does not dissolve;
grade selection is load-bearing again.** `bom.csv` is locked to `DAC8568CIPW`
and states C clears to zero scale where B/D clear to midscale **[repo]**, with
the honest caveat *"CONFIRM the gain/grade mapping against SBAS430 — ti.com was
unreachable"* **[repo]**. **[datasheet-gated]** — *name it: DAC8568 grade-letter
mapping to reference gain AND to power-on-reset level, per SBAS430.*

Not a reason to revert. It **is** a reason to (a) re-mark the grade letter as
safety-critical rather than range-critical, and (b) stop describing the mod
safe-state as a structural property — it is a property of one specific DAC
state, and §4.3 shows the DAC passes through non-uniform states routinely.

### 5.9 — Nothing defines the op-amp inputs while the DAC is unpowered

From §3, the op-amps are alive before AVDD on the way up and after AVDD on the
way down. In both windows the five signal op-amps and the two reference buffers
have their `(+)` inputs connected, through `R-OPAMP-IN 1 k` **[repo]**, to DAC
output pins that are not being driven. **There is no resistor from any DAC
output node to ground anywhere in the design** — I looked for one on all three
schematic pages and in `bom.csv`.

If the DAC8568's outputs are high-impedance below its POR threshold (and again
in commanded power-down), those op-amp inputs are undefined, and a stage with a
gain of 2 or 4 and ±12 V rails will take its output wherever leakage sends it.
**[datasheet-gated]** — *name it: DAC8568 `VOUT` state below the power-on-reset
threshold, and the output termination options in power-down mode (1 kΩ / 100 kΩ
/ Hi-Z).* If the answer is "actively held at zero scale from the moment AVDD is
valid, and terminated in power-down", this is a non-issue. If it is "Hi-Z", then
every rack power-on and power-off produces an unspecified excursion on five
jacks.

`pitch-stage.md` says `R-OPAMP-IN` is *"pure clamp-current protection for the
power-up window where the DAC is on 5.21 V and the op-amp is on ±12 V"*
**[repo]** — which shows the power-up window *was* considered, for current, but
not for the node's **voltage**.

**Cheap insurance if the datasheet says Hi-Z:** 1 MΩ from each DAC output node
to `AGND`. Against a 1 kΩ source that is a 0.1 % divider **[calc]** — absorbed by
the pitch gain trim, and 0.1 % of the mods' 20 V span is 20 mV, inside the
±81 mV zero budget `mod-channels.md` already accepts **[repo]**.

### 5.10 — Two drawing errors worth catching before layout

**(a) The entry bulk returns to `AGND`.** `power-entry.md`'s schematic draws
`C1` and `C2` (both 47 µF, on both +12 V branches) returning to a node labelled
**`AGND`** **[repo]**. The same page states *"`AGND` is not a ground at all — it
is an in-amp input"* **[repo]**, and it is a conductor that runs 2 m up the
umbilical to the instrument's analog star. If that label is literal, the
module's entire +12 V ripple current — including the 360 mA umbilical branch —
returns through the breath measurement's reference conductor, and breath becomes
a readout of the LED strips' PWM. Almost certainly a labelling slip for the
analog ground region, but it is the kind of slip that survives into a netlist.
**Resolve the label before layout.**

**(b) `digital-and-supervision.md`'s presence annotation is stale.** Its
schematic still annotates the in-amp output as *"0 V absent, −0.44 V alive"*
**[repo]**, the pre-trim polarity, while the same page's prose explains why that
is no longer true. Anyone reading the drawing rather than the prose builds
§4.1 without noticing.

**(c) `breath-receive-stage.md` and `firmware/README.md` both still say `REF` is
grounded.** *"now that `REF` is grounded it touches the breath stage in no way
at all"* (breath page, "What the jack does when the watchdog fires — settled")
and *"the in-amp's `REF` pin is grounded rather than driven by a firmware zero …
no DAC register touches the breath jack at all"* (`firmware/README.md`)
**[repo]** — both contradicted by the same breath page's own schematic and
values table, which feed `REF` from `VREFOUT` through a buffered trimmer
**[repo]**. `bom.csv` contradicts itself on the same pin: `U-DIFFRX` says *"REF
ties HARD to module AGND — no divider"* while `TRIM-BREATH-ZERO` says
*"Range 0 to ~+0.6 V from VREFOUT"* **[repo]**.

**The project does not currently know which circuit it is building**, and the
answer decides whether the breath-immunity claim is true (grounded: true, and
§4.1 does not exist) or false (trimmed from `VREFOUT`: false, and §4.1 is a
showstopper). This is the single highest-value thing to settle on this page.

---

## 6. Retired: one open question the arithmetic closes

`digital-and-supervision.md` and `bom.csv` `U-WATCHDOG` both leave open
*"Whether the '123 empties 220 nF in a 250 µs retrigger window … It is
retriggered ~400 times per timeout period."* **[repo]**

It is retriggered more often than that — six channels at 4 kHz is one `CS`
assertion every **41.7 µs** **[calc]** — and that makes the concern
*quantitatively* unfounded rather than more worrying. Between retriggers the
timing capacitor charges for 41.7 µs out of a 99 ms period:

```
41.7 µs / 99 ms = 0.042 %  of the timing ramp per interval                 [calc]
```

Any discharge better than 0.042 % per trigger holds the node down in steady
state; there is no ratcheting mechanism. The residual question is not discharge
capability but **minimum trigger pulse width** — `CS` is low for
`32 bits / 2 MHz = 16 µs` **[calc]**, which is enormous by HC-family standards
**[from memory]**. **[datasheet-gated]** — *name it: 74HC123 minimum trigger
pulse width and minimum retrigger period at `VCC` = 5 V*, but this should be
downgraded from "bench-check before build" to "confirm on the datasheet".

**The '123's power-up state is the open item that should replace it.** A
74HC123's `Q` state at power-up, and whether an untriggered part ever times out,
are both unspecified from the repo. The consequence is not at power-on (the DAC
is at POR zero anyway) but later: **a glitch on the 5.21 V rail that resets the
'123 while the DAC holds a played value could leave the watchdog disarmed with a
note standing — the exact drone the watchdog exists to prevent.** The
power-on-reset RC already listed as "Still open" **[repo]** closes it and should
be promoted.

---

## 7. What is right, and why it is right

Stated because five of the twelve scenarios land safe and it is not by accident.

- **`OE`'s fail-safe polarity works for a structural reason.** `OE` is active
  low and pulled **up**; it is asserted only by a comparator on ±12 V. Its
  default lives on a long-lived rail and its assertion depends on a short-lived
  one, so every rail failure and every power-down defaults to "instrument
  absent". `bom.csv` `R-OE-PU` states this **[repo]** and the structure holds
  under every sequence I walked.
- **`R-CLR-PD` as a pull-down is correct** and the reasoning given for it (the
  window before the '123 powers up) is the right reasoning **[repo]**.
- **Six pulls, not three.** The observation that with `OE` disabled it is the
  **DAC's** pins that float, not the buffer's, is exactly right and is the kind
  of thing that is normally found on a bench **[repo]**.
- **`D1`/`D2` split before the diode.** Confirmed useful in a way the page does
  not claim: on power-down, `D1` isolates the module's analog rail from the
  instrument's 360 mA discharge, so the module's precision section is not dragged
  down by the load **[calc]**.
- **`R4`/`R5` bias return.** Covers every contact-break order on unplug: whatever
  mates or breaks last, the in-amp's inputs are defined. This is the one part of
  the hot-plug story that is properly closed **[repo]**.
- **Retriggering from the buffered, DAC-side `CS`.** The cable-side alternative
  would be defeated in exactly the state the watchdog exists for **[repo]**.
  Correct, and it is what makes scenarios 5, 6, 7 and 11 land safe.
- **`-1` over `-2` on the load switch** and the foldback requirement **[repo]**.
  Correct for a fault that will be persistent (a crushed cable, a latched-white
  strip set) rather than transient.

---

## 8. What to do, in order

| # | Action | Severity | Closes |
|---|---|---|---|
| 1 | **Settle the in-amp `REF` pin.** Six places in the repo give three different circuits; the values table's *"From the LM317 rail"* is the right one | **Showstopper** | §5.10(c), deletes §4.1b, makes the breath claim true |
| 2 | **Fix the presence detect's *polarity*** — independent of item 1, the trim inverted it and no threshold in the repo works | **Showstopper** | §4.1a |
| 3 | **Redesign the presence detect**: hysteresis to the threshold input, buffer the tap or use a CMOS comparator, re-derive the divider | **Showstopper** | §4.2 |
| 4 | **Make the six DAC channels update atomically** (software `LDAC`, or wire the pin) | High | §4.3 |
| 5 | **Refresh the reference-enable and clear-code registers every pass**, not every few thousand | High | §4.6 (partially) |
| 6 | **Move the 74AHCT125 onto the LM317 rail**; delete the bus +5 V dependency | High | §4.5, scenario 11, the `bom.csv`/schematic contradiction |
| 7 | **Match the ±12 V decay rates** (`C1 = 100 µF` or `C3 = 22 µF`) after measuring both rail currents at E7 | High | §4.4 |
| 8 | **Gate `OE` on a frame boundary** — one 74HC74 clocked by cable-side `CS` | Medium | §4.3's trigger source, §5.5 |
| 9 | **Resolve the `AGND` label on the entry bulk** before layout | Medium (or showstopper if literal) | §5.10(a) |
| 10 | **Add the '123 power-on reset RC**; promote the DAC service routine to IRAM | Medium | §6, §5.7 |
| 11 | **Correct ADR 0006's power-on table** — pitch is 0 V, not subsonic; breath is a knob, not 0 V | Medium (documentation, but it is the table people will trust) | §5.1, §5.2 |
| 12 | **Decide the hot-plug contact-order story**, or document "toggle off before plugging" | Medium | §5.3 |
| 13 | **Decide the readback conductor and the `MOSI`/`CS` pairing before the umbilical is terminated.** The budget is eight of eight; there is no spare | Medium, but **unretrofittable** | §4.6 structurally, §5.5 |

## 9. The datasheet questions, collected

None of these were answerable: the proxy blocked ti.com, analog.com and nxp.com
throughout. **No figure from any of them appears above.**

| Part | Parameter | Gates |
|---|---|---|
| **DAC8568C** (SBAS430) | Grade-letter → reference gain **and** POR level | §5.8 |
| | Internal-reference default state at POR | §4.1, §5.1 — *stated as "disabled" in ADR 0006 **[repo]**; confirm* |
| | Clear-code register: power-on default and full option set | §4.6 |
| | `V_OUT` state below the POR threshold; power-down termination options | §5.9, §4.6 |
| | `V_IH` as a fraction of AVDD; digital-input abs-max relative to AVDD | §4.5 |
| | `LDAC` pin and software-`LDAC` register encoding | §4.3 |
| | Behaviour of a 32-bit frame with an unrecognised command field | §4.6 |
| **74AHCT125** | `I_off` / partial-power-down; input clamp structure to `VCC`; `VCC` range | §4.5 |
| **74HC123** | Min trigger pulse width, min retrigger period; `Q` state at power-up | §6 |
| **LM311** | `I_IB` typ/max **and direction**; input common-mode range vs supplies | §4.2 |
| **LT1641-1** | UVLO threshold; current-limit loop response; foldback shape; whether latch-off needs an `ON` cycle | §5.3 |
| **OPA2197** | Behaviour with `V+` below the input common-mode range: output state, phase inversion | §4.4 |
| **LM317LZ** | `θ_JA` in TO-92 at ~180 mW | §4.5 fix |
| **etherCON insert** | Contact make/break sequencing, if any | §5.3 |
| **MPXV4006DP** | Offset tempco (already flagged unverified in `breath-receive-stage.md` **[repo]**) | — |
