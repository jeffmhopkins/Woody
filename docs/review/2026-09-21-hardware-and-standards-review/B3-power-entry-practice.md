# B3 — Power entry vs. published Eurorack practice

**Reviewer stance:** cold comparative. I did not read `docs/review/**` or
`docs/research/**`. Everything below is from the four in-scope repo files plus
schematics I opened in this session.

**Scope read:** `hardware/module/power-entry.md`, `hardware/controller/carrier.md` §1,
`hardware/bom.csv`, `docs/decisions/0005-power-architecture.md`.

**Evidence marking:** `[repo] <file>` = read in this repository. `[web] <url>` =
fetched or searched in this session, URL given. `[calc]` = my arithmetic, shown.
`[from memory]` = **not verified this session; check before ordering.**

**Findings are indexed by design element, not by document.** Ranking:
Showstopper / High / Medium / Low / Note.

---

## 0. The comparison set

Fourteen published Eurorack power-entry schematics I actually opened and read
this session. This is the basis for every "the field does X" claim below.

| # | Module / design | Entry topology | Entry bulk | Local reg? | URL |
|---|---|---|---|---|---|
| 1 | **Mutable Instruments Ripples v90** (2019, cc-by-sa) | 2×5 **shrouded** hdr `M05X2SHD`; **+12 V: series Schottky D1 + bead L1** (Würth 742792664); **−12 V: PTC `P1` + bead L2 + shunt Schottky D2 (1N5819HW, anode to VEE, cathode to GND)** | 22 µF/rail + 12×100 n | no | [web] https://github.com/pichenettes/mutable-instruments-documentation/blob/main/docs/modules/ripples_2020/downloads/ripples_v90.pdf |
| 2 | **Ornament & Crime rev2e** (mxmxmx, CC BY-NC-SA) | 2×5 hdr; **D1, D2 series diodes**, one per rail. No fuse. | 22 µF/rail | LM1117-5 from +12 V, then ADP150-3v3 | [web] https://github.com/mxmxmx/O_C/blob/master/hardware/o_c_rev2e_schematic.pdf |
| 3 | **Befaco Muxlicer v1.2** | 2×5 hdr; **F1/F2 fuses in series, then D7/D8 series Schottky**, one pair per rail | 10 µF/rail | **7805L (+5 V) and 79L05 (−5 V) from ±12 V** | [web] https://github.com/Befaco/muxlicer/blob/master/hardware/muxlicer_v1_2.pdf |
| 4 | **Westlicht PER\|FORMER rev1.0** (cc-by-nc-sa) | sheet titled *"POWER INLET — Reverse protection and filtering"*: **D3/D4 1N5819HW series**, one per rail | **47 µF/rail** | R-78E5.0-1.0 (+5 V) from +12 V, then 2× LM1117-3.3 (separate digital/analog) behind beads | [web] https://github.com/westlicht/performer-hardware/blob/master/sequencer.pdf (sheet 3/8) |
| 5 | **Super Synthesis 2OPFM rev5** (2024) | J1; **D10/D11 series**, one per rail. No fuse. | 10 µF/rail | AMS1117-3.3 direct from +12 V | [web] https://github.com/supersynthesis/eurorack/blob/main/Production%20Modules/2OPFM/2OPFM_REV5_SCHEMATIC.pdf |
| 6 | **Erica Synths DIY Polivoks VCO3** (2020) | XP1 10-pin; **VD1/VD2 1N4001 — plain silicon, series**, one per rail; L1/L2 **100 µH** | **47 µF/rail** + 0.1 µF | — | [web] https://github.com/erica-synths/diy-eurorack → `VCO3 DIY.zip` → `DIYVCO3.pdf` |
| 7 | **Erica Synths DIY MIDI-CV v1.1** (2017) | **VD1/VD3 1N4001 series**, one per rail | **47 µF/rail** | **78L05 from +12 V** | [web] https://github.com/erica-synths/diy-eurorack → `Midi-CV DIY.zip` → `DIY_MIDI_CV_v1_1.pdf` |
| 8 | **KitsBlips Eurorack template** | `Conn_02x05_Europower`; D1/D2 **1N5819 series** | 10 µF | L78L05 | [web] https://github.com/Alloyed/KitsBlips/blob/main/kicad/_templates/eurorack/power.kicad_sch |
| 9 | **shmoergh/moduleur** (VCO, VCF, ADSR, brain — same sheet reused) | D6/D7 **1N5817 series** | 100 µF | — | [web] https://github.com/shmoergh/moduleur/blob/main/modules/02-vco/electronics/core/sheets/power.kicad_sch |
| 10 | **sluisbrinkie Andes** | 3× **1N5817**, L78L05 | 10 µF | L78L05 | [web] https://github.com/niektb/sluisbrinkie-eurorack-published/blob/main/Andes/Hardware/andes_12hp/power.kicad_sch |
| 11 | **moPsy eurorack-power-breakout** | 2×8 hdr; **3× 1N5817 + 3 ferrite beads — one per rail, including +5 V** | 10 µF/rail | — | [web] https://github.com/moPsy-project/eurorack-power-breakout/blob/main/eurorack-power-breakout.kicad_sch |
| 12 | **soundslikefrank/grow** | D11/D12 **1N5819 series** + beads (100 Ω @100 MHz) | 22 µF / 10 µF | R-78E5.0-0.5, LM1117-3.3 | [web] https://github.com/soundslikefrank/grow/blob/main/hardware/power_ref.sch |
| 13 | **jtommi/mmsb** | D901/D902 **1N5817 series** | 10 µF/rail | — | [web] https://github.com/jtommi/mmsb/blob/main/Common/Power.sch |
| 14 | **Winterbloom Helium** | D1/D2 **1N5819 series** + FB1/FB2 (1 kΩ @100 MHz beads) | 10 µF/rail | — | [web] https://github.com/wntrblm/Helium/blob/main/hardware/board/power.kicad_sch |

Also read but not counted (not module entries): Winterbloom Sol mainboard
(LM1117-5.0 + TPS79633) [web] https://github.com/wntrblm/Sol/blob/master/hardware/rev1/mainboard/mainboard.sch ;
Coriolis SnackBus PSU / Multibus busboards (LM317, 1N4001/1N5402 — PSU-side, not
module-side) [web] https://github.com/coriolisinstruments/EurorackModules .

A secondary summary of the same convention, naming the Moritz Klein × Erica
Synths *mki x es edu* kits as the reference design ("keyed connector + series
Schottky per rail + 10 Ω or ferrite + 47 µF + 0.1 µF + 0.1 µF at every IC"):
[web] https://github.com/hed0rah/partinfo/blob/main/src/partinfo/data/references/eurorack-power-protection.json
(treat as a note, not a schematic).

### The counts

| Feature | Count in the 14 |
|---|---|
| Series diode in each rail | **14 / 14** (+12 V); 13 / 14 (−12 V — Ripples is the exception) |
| Schottky rather than silicon | 12 / 14 (Erica uses 1N4001 twice) |
| Anti-parallel / shunt diode | **1 / 14** (Ripples, −12 V only, *with* a PTC) |
| Fuse or PTC anywhere in the entry | **2 / 14** (Ripples −12 V, Muxlicer both rails) |
| P-FET / ideal-diode reverse protection | **0 / 14** |
| Hot-swap controller or eFuse at the rack entry | **0 / 14** |
| Module that takes bus +5 V for its logic | **0 / 8** of the designs that need a sub-12 V rail; all 8 make it locally from +12 V |
| Current-limited switch on a rail sent **off-panel** | **1** found anywhere (PER\|FORMER, see §4) |

A GitHub-wide code search for `LT1641 eurorack` returns **16 hits and every one of
them is this repository** — no other published Eurorack design on GitHub mentions
the part. `eurorack TPS2553 OR TPS25940 OR TPS2592 OR LM5069 OR LTC4210` returns
**zero**. By contrast `eurorack 1N5817 power` returns **481 files**.
[web] GitHub code search API, queries as written, run 2026-09-21.

---

## 1. The reverse-protection diodes (`D-REVPOL`, 3× 1N5817)

### 1.1 Three diodes with the +12 V leg split — Medium (keep it; the stated reason does not survive checking)

**What the field does.** One series Schottky per rail, before the bead and before
the bulk cap, full stop (14/14, §0). Where a third diode appears (moPsy, Andes) it
is *one per rail including +5 V*, never two on the same rail. Splitting a rail into
two diodes has no precedent in the set, which `power-entry.md` itself says
`[repo] hardware/module/power-entry.md` ("There is no prior art for this split
because there is no prior art for the situation"). That much is fair.

**The arithmetic for the split is sound.** 1N5817 Vf rises roughly 0.26 V → 0.34 V
between ~35 mA and ~395 mA `[from memory]` — so ~80 mV of load-correlated Vf
modulation on a shared diode is real `[calc]`.

**The consequence claimed for it is not supported by the architecture as
documented.** The page says the 80 mV is "about 20 cents of breath-correlated pitch
bend" `[repo] hardware/module/power-entry.md`. 20 cents on 1 V/oct is 16.7 mV at
the jack `[calc: 20/1200 V]`. For 80 mV of +12 V movement to produce 16.7 mV at the
pitch output you need the pitch chain to be ~21 % ratiometric to +12 V `[calc]`.
But per ADR 0005 and the BOM, pitch full scale is set by the **DAC8568's internal
2.5 V reference × 2**, not by AVDD `[repo] docs/decisions/0005-power-architecture.md`,
and AVDD itself comes from the LM317, whose line regulation is ~0.01 %/V
`[from memory]` — 80 mV in gives single-digit µV out `[calc]`. The op-amps' PSRR
does the rest. **On the documented architecture the sensitivity is ~0, not 21 %.**

So: keep the second diode (it is twenty cents, it keeps 0.36–0.94 A out of the
analog rail's bead and bulk cap, and it stops an umbilical fault from collapsing
the analog rail — all good reasons), but **stop citing "20 cents of pitch bend" as
the justification**. Either the number is wrong by two orders of magnitude, or
something in the pitch chain is ratiometric to +12 V that is not written down — and
if the latter is true, §8 below is a much bigger problem than the diode ever was.

### 1.2 1N5817's 20 V reverse rating — Low

`1N5817` is 20 V / 1 A `[from memory]`. A reversed rack ribbon puts ~12 V across
it, i.e. **1.67× margin**. Five of the fourteen designs use `1N5819` (40 V,
**3.3× margin**) in the same DO-41/SOD package family at the same price
[web] refs 4, 8, 12, 14 and 1 (D2) in §0. This is a free substitution and I would
take it. The `D-USBOR` row already offers "1N5817 or SS14" `[repo] hardware/bom.csv`,
so the project is not attached to the part number.

### 1.3 D2 is the only entry diode carrying real current — Note

At 0.36 A typical, D2 dissipates ~0.12 W; at the 0.94 A limit during a fault,
~0.47 W `[calc, Vf from memory]`. Well inside a DO-41. It is nonetheless the
hottest passive in the entry and the one whose Vf sets how much of the ±5 % rail
budget the instrument actually gets. Worth a thermal sanity check at E6, nothing more.

### 1.4 Mutable deliberately avoids a series diode on −12 V — Note

Ripples v90 puts a **PTC plus a shunt Schottky** on −12 V and a series Schottky only
on +12 V [web] ref 1. Reading the schematic, D2's cathode is on GND and its anode on
VEE — it is reverse-biased in normal operation and crowbars the PTC if the rail is
reversed. The obvious motive is that a filter module wants every millivolt of
negative headroom, and the PTC costs none. Woody spends 0.35 V of −12 V headroom on
`D3` for a module whose pitch output must reach −2 V. That is almost certainly still
fine, but it is a deliberate, published counter-example to "always a series diode",
and it is the *only* fuse-based scheme in the set that a first-tier manufacturer ships.

### 1.5 The bus +5 V pin has no diode — High (see §2)

---

## 2. The +5 V bus rail — **High**, and this is the element I would change

`power-entry.md` gives bus +5 V a bead and a 47 µF cap and **no diode**, reasoning
that a reversed ribbon kills a \$0.30 buffer and nothing else
`[repo] hardware/module/power-entry.md`. ADR 0005 goes further and makes the bus
+5 V rail "a **requirement, not an option**. No jumper, no unpopulated fallback
footprint." `[repo] docs/decisions/0005-power-architecture.md`

Three problems, in increasing order of size:

1. **Nobody does this.** Of the eight designs in §0 that need a sub-12 V rail,
   **eight make it locally from +12 V** (7805L, 78L05, L78L05 ×2, LM1117-5,
   R-78E5.0 ×2, AMS1117-3.3) and **zero** take the bus +5 V. The only design in the
   set that touches the bus +5 V pin at all is a *breakout board* whose job is to
   expose it — and it still puts a 1N5817 and a bead on it
   [web] https://github.com/moPsy-project/eurorack-power-breakout/blob/main/eurorack-power-breakout.kicad_sch
2. **The Eurorack standard makes it optional and most cases omit it.** Doepfer's own
   technical page says the 10-pin bus carries only −12 V / GND / +12 V and that the
   16-pin version "has the three signals +5V, CV and Gate available"
   [web] https://doepfer.de/a100_man/a100t_e.htm (page itself **blocked** from this
   sandbox; text from search-result extract of that URL). Doepfer shipped the +5 V
   bus trace but did not put a +5 V supply in the cases, and sells a +12 V→+5 V
   adapter for the modules that need it [web] search extract citing
   https://www.modwiggler.com/forum/viewtopic.php?t=130601 and
   https://www.modwiggler.com/forum/viewtopic.php?t=248023 (both **blocked** to
   direct fetch).
3. **It is the only unprotected rail in a design that otherwise spends a lot of
   effort on protection**, and the BOM already knows it is a hazard: `R-SPI-PULL`
   carries the note "on the bus rail a reversed ribbon reaches the DAC's SYNC pin
   and turns a \$0.30 buffer failure into a DAC failure" `[repo] hardware/bom.csv`
   row 48. The rail is not as harmless as the entry page assumes.

**The change.** Delete the bus +5 V dependency. Run `U-LVL-MOD` (74AHCT125, ~10 mA)
from a local rail off the already-protected +12 V — a `78L05`/`L78L05` in TO-92, the
same part four of the fourteen designs use, is three pins and two caps. Do **not**
hang it on the LM317's 5.21 V: a 2 MHz buffer driving 2 m of cable does not belong
on the DAC's AVDD, and the existing separation is correct. This one change:

- matches 8/8 of the field,
- removes the design's only hard case-compatibility constraint,
- removes the only rail with no reverse protection,
- removes one entry bead, one 47 µF cap and one IDC rail dependency,
- and costs one TO-92, two caps, and ~70 mW `[calc: (12−5)×10 mA]`.

The counter-argument in ADR 0005 — "engineering for a case this instrument is never
in" — is a scope argument, not an engineering one, and it is buying nothing here,
because the local regulator is *cheaper and smaller* than the rail requirement it
replaces.

---

## 3. The load switch: LT1641-1CS8 + DPAK N-FET + 50 mΩ sense

### 3.1 Is a hot-swap controller normal, rare, or unheard of? — answer: unheard of at the entry, rare-but-precedented on an exported rail

**At the rack power entry: unheard of.** 0/14 in §0, and 0 hits GitHub-wide for
every hot-swap/eFuse part I searched (§0). The field's entire inrush strategy at the
rack connector is "10–22 µF and a Schottky."

**On a rail the module sends off-panel: one precedent, and it is a good one.**
Westlicht PER|FORMER's power sheet has a block literally titled *"5V SUPPLY (USB)"*
built around **U3 = STMPS2151**, an ST current-limited power-distribution switch,
with `USB_PWR_EN` from the MCU, a 10 k pulldown on EN, and `USB_PWR_FAULT` returned
to the MCU — feeding `USB_5V` out to a Molex 105057 USB-A host connector
[web] https://github.com/westlicht/performer-hardware/blob/master/sequencer.pdf
sheet 3/8. The STMPS2151 is a 2.7–5.5 V, ~500 mA-typ-limit, SOT-23-5 part with
constant-current limiting, thermal shutdown, auto-recovery and an open-drain fault
flag [web] search extract of https://www.st.com/resource/en/datasheet/stmps2141.pdf
(datasheet itself **blocked**).

**So the function is precedented and the implementation is not**, and the reason is
voltage, not taste: the cheap one-chip load switches all stop at 5.5–6.5 V. ADR
0005 already found this the hard way with the TPS2553
`[repo] docs/decisions/0005-power-architecture.md`. Exporting **12 V** instead of
5 V is what pushed this design off the shelf of SOT-23 USB switches and onto a
telecom hot-swap controller. That is a consequence of the WS2815 decision (ADR 0014),
not of over-engineering.

**Verdict: justified, not over-engineered.** 2 m of detachable cable, an etherCON
that users will hot-plug, ~2.2 mF at the far end, LED strips, and a load that can
latch at ~1.5 A. The field's alternative — see §4 — is to put raw +12 V on a header
and hope. That is not acceptable here.

### 3.2 `C-TIMER-LOADSW` is specified at 10 nF and the datasheet equation says it should be roughly 100× to 300× larger — **Showstopper**

`hardware/bom.csv` row 108 specifies `C-TIMER-LOADSW` as **"10nF C0G, 0805"**, sets
the fault timeout at ~50 ms, and notes the exact value must come off the datasheet
because `analog.com` was unreachable `[repo] hardware/bom.csv`.

I could not open the datasheet either (analog.com is blocked to this sandbox), but
the equation is quoted verbatim in search-indexed datasheet text:

> "The capacitor value for programming maximum current limit time is:
> **C(nF) = 62 • t(ms)**" — and, separately, "When the TIMER pin reaches **1.233 V**
> the internal fault latch is set … the TIMER pin is pulled back to GND by the
> **3 µA** current source … the part is not allowed to turn on again until the
> voltage at the TIMER pin falls below 0.5 V."
> [web] search extracts of https://www.analog.com/media/en/technical-documentation/data-sheets/164112fc.pdf
> and https://www.analog.com/media/en/technical-documentation/data-sheets/1641fd.pdf
> (**both blocked to direct fetch**)

Two readings, both fatal to 10 nF:

- Taking the stated formula: 50 ms → **3.1 µF** `[calc: 62 × 50]`. 10 nF gives
  **0.16 ms** `[calc: 10/62]`.
- Taking the 3 µA / 1.233 V ramp instead: C = I·t/V = 3 µA × 50 ms / 1.233 V =
  **122 nF** `[calc]`. 10 nF gives **4.1 ms** `[calc]`.

Either way the specified part is 12×–300× too small, and a 3.1 µF C0G in 0805
does not exist — so if the first reading is the right one, the **package in the BOM
row is also wrong**. A 0.16 ms or 4 ms fault timer latches the LT1641-1 off during
any start that enters current limit, which is every hot-plug (§3.4). The instrument
would appear to be dead and the only recovery would be the panel toggle.

**Action:** this is the one number in the whole entry that must come off the
datasheet before anything is ordered, and the BOM row must carry a real package.

### 3.3 Foldback and the programmed ramp are fighting each other, and nothing in the design notices — **High**

`power-entry.md` says "Program the foldback. The LT1641 family reduces its current
limit while the FET's drain voltage is high" `[repo] hardware/module/power-entry.md`.
The datasheet text describes the mechanism the other way round, keyed to the FB pin:

> "The current limit circuit will regulate the voltage across the sense resistor
> (VCC – VSENSE) to **47 mV when VFB is 0.5 V or higher**" — i.e. the limit is
> *reduced* when FB (the output-voltage divider) is **low**.
> [web] search extract of https://www.analog.com/media/en/technical-documentation/data-sheets/164112fc.pdf

That is the same physical behaviour, but it lands squarely on the start-up case,
because during the entire programmed ramp the output **is** low:

- The page's ramp analysis assumes "A normal start never enters current limit —
  0.53 A against a 1.0 A limit" `[repo] hardware/module/power-entry.md`.
- With foldback programmed, the limit at V_OUT ≈ 0 is a *fraction* of 47 mV/R.
  If that fraction is (say) ¼, the limit at the start of the ramp is **0.24 A**
  `[calc]` — **below** the 0.53 A the 50 ms ramp demands. The part enters current
  limit immediately, the timer starts, and the start becomes a folded-back
  constant-current charge that is *slower* than the 26 ms the page budgets:
  2.2 mF × 6 V / 0.24 A ≈ **55 ms just to reach half rail** `[calc]`.
- So the design can simultaneously have foldback "as ADI intends" and a fault
  timer that is too short for its own start, and the failure mode is a latched-off
  instrument that never boots.

I could not obtain the actual foldback ratio (FB-low sense threshold) — that number
is the missing input. **Take it off the datasheet and then re-derive the ramp
capacitor and the timer capacitor together, not separately.** The page's own
open-questions box already lists "the foldback network's topology" as unknown
`[repo] hardware/module/power-entry.md`; what it does not say is that the unknown
invalidates the ramp arithmetic above it.

### 3.4 The sizing case is the hot-plug, not the cold-day start — **High**

`carrier.md` §1 and ADR 0004 put a **Neutrik etherCON** on both ends
`[repo] hardware/controller/carrier.md`, `[repo] hardware/bom.csv` row 19. An
etherCON is a *connector people plug in while things are on*. That means:

- With the panel toggle already ON, the FET is fully enhanced. Plugging in the
  instrument connects 2.2 mF of discharged bulk to a hard 12 V node. The gate ramp
  does nothing here — it only runs at turn-on. **Current limiting is the only thing
  between the cable and the rack.**
- Charge time at the limit: 2.2 mF × 12 V / 0.94 A = **28 ms** `[calc]`, against a
  nominal 50 ms timer — 56 % of the budget, before foldback (§3.3) makes it worse.
- Energy in the FET is ½CV² = **158 mJ** `[calc: 0.5 × 2.2e-3 × 144]` — the same
  number the page derives, so the DPAK SOA sizing survives. The risk is nuisance
  latch-off, not FET death.

**Neither `power-entry.md` nor ADR 0005 analyses the hot-plug case at all.** Both
treat the switch-on ramp as the sizing case. Add it: the timer must clear a
foldback-limited, fully-discharged hot insert with margin, and E6 should measure
exactly that, by plugging the cable in with the module live.

Related: this is a genuine argument for the `-2` (auto-retry) suffix that ADR 0005
rejects. A hot insert that latches off and needs a toggle cycle is a bad user
experience; auto-retry into a *transient* condition is the correct behaviour, and
the thermal-runaway objection ADR 0005 raises applies to PTCs, whose hysteresis is
thermal and slow, not to a controller retrying on a fixed timer into a
correctly-SOA-sized FET. I would not overturn the `-1` decision on my own authority,
but ADR 0005's stated reason for it does not actually cover the hot-plug case.

### 3.5 The panel toggle consumes the pin that provides undervoltage lockout — **Medium**

`SW-POWER` "drives the load switch enable" `[repo] hardware/bom.csv` row 17. On the
LT1641 that pin is `ON`, and `ON` is the **programmable undervoltage lockout** input:
"The ON pin provides programmable undervoltage lockout" and "The fault latch is
cleared by pulling the ON pin low"
[web] search extract of https://www.analog.com/en/products/lt1641-1.html.

Two consequences the design does not address:

- If the toggle simply pulls `ON` high/low, **there is no UVLO**, and the part will
  attempt to start into 2.2 mF while the rack's +12 V is still coming up. Field
  practice for hot-swap parts is `ON` = resistive divider from VCC, with the enable
  switch shorting the *bottom* of that divider — you get both.
- `ON` is a ~1.2 V-threshold comparator input on a wire running to a panel toggle.
  There is no pull-down, no RC, and no debounce specified anywhere in
  `power-entry.md` or the BOM. A bouncing toggle restarts a 2.2 mF ramp several
  times in a few milliseconds. **Add a pull-down and an RC on `ON`**, and route it
  as the divider bottom so UVLO survives.

### 3.6 The current limit is 0.94 A, not 1.0 A — **Note**

`power-entry.md` computes `R_SENSE = 50 mV / 1.0 A = 50 mΩ`
`[repo] hardware/module/power-entry.md`. The datasheet number is **47 mV**
[web] as §3.3, so 50 mΩ gives **0.94 A typ** `[calc]`. That is still above the
~0.63 A clamp-legal worst case and below the etherCON's 1.5 A, so the decision
stands — but the page's headline number is 6 % optimistic and `R-ILIM`'s BOM row
already, correctly, says the value is a bench selection
`[repo] hardware/bom.csv` row 63. Just fix the arithmetic on the page.

### 3.7 The DPAK/SOA reasoning is better than anything in the comparison set — **Note (credit)**

Sizing a pass FET against its *single-pulse SOA curve* rather than R_DS(on), and
catching a SOT-23 that would have cooked, is not something any of the fourteen
designs had to do, and the reasoning as written is correct
`[repo] hardware/module/power-entry.md`. `½CV² = 158 mJ` and `12 W × 50 ms = 0.6 J`
both check out `[calc]`. Keep it.

---

## 4. Powering an external device over a cable — what the field actually does

This is the question with the least published practice, so here is everything I found.

**(a) Expander headers: raw rail, nothing else.** Befaco Muxlicer's
`EXPANSION_PORT` is a 10-pin header carrying five signals, **GND on pin 6 and raw
+12 V on pin 2 — no series element, no fuse, no limiting of any kind**
[web] https://github.com/Befaco/muxlicer/blob/master/hardware/muxlicer_v1_2.pdf.
This is the Eurorack expander convention: the parent module's protected rail goes
straight out on a header, and the expander is assumed to be short, captive, and
plugged in with the power off.

**(b) USB host ports: a current-limited load switch.** PER|FORMER, §3.1 — the one
design in the set that sends power to something detachable and treats it as a
hazard. Note what it protects: **5 V, ~500 mA, a connector the user plugs and
unplugs at will**. Structurally identical to Woody's problem, one rail down.

**(c) Expert Sleepers: no limiting, budget it and warn the user.** The FH-2's power
spec is "118 mA at +12 V, 48 mA at −12 V, **plus the power requirement of any
attached USB device**", with the manual containing "information on calculating the
current draw on the +12 V rail from the USB device"
[web] search extract of https://expert-sleepers.co.uk/fh2.html (site **blocked** to
direct fetch; also https://www.expert-sleepers.co.uk/es8usermanual.html).
The ES-8's expansion header powers an ES-5, which in turn powers further expanders
[web] same extract. The convention there is documentation, not silicon.

**Conclusion for this design.** There is no established Eurorack practice for
sending **+12 V at 360 mA down 2 m of detachable cable to a device with 2.2 mF of
bulk and addressable LEDs**, because no published module does it. The nearest
precedents are (a) do nothing, and (b) do exactly what this design does, at 5 V,
with one chip. **A current-limited, ramped, fault-timed switch is the right answer
and I would not delete it.** What the field comparison *does* say is that the
design should stop presenting the load switch as the unusual part; the unusual part
is exporting 12 V at all, and everything downstream of that decision follows.

---

## 5. The local regulator: LM317 at ~5.21 V

### 5.1 Making a sub-12 V rail locally is exactly what the field does — Note (credit)

8/8 (§0, §2). Nobody trusts the bus +5 V. The *decision* is orthodox.

### 5.2 The LM317 is an unusual choice of part, and for once the unusual choice is right — Note

Field parts for this job are **fixed**: 78L05/7805L (×4), LM1117 (×2), AMS1117,
ADP150, R-78E5.0 (×2) (§0). A GitHub search for `eurorack LM317 power supply rail`
returns PSU and busboard designs, not modules [web] GitHub code search, 2026-09-21.

But this rail must sit **above** 5.000 V (the DAC8568's full scale set by the
internal reference × 2) and **below** AVDD max, per ADR 0005
`[repo] docs/decisions/0005-power-architecture.md`. A fixed 5.0 V part at −2 % is
4.90 V and cannot do the job — the ADR's own reasoning. An adjustable regulator is
therefore correct, and the LM317L is the cheapest, most available adjustable part
in TO-92. **This is the right call and the reasoning in ADR 0005 is the good version
of it.** Two nits:

- `Vout = 1.25 × (1 + 475/150) = 5.208 V` `[calc]`, plus I_ADJ×R2 = 50 µA × 475 Ω =
  **+24 mV → ~5.23 V** `[calc]`. The BOM description says "5.25V", the note says
  5.21 V, the ADR says ~5.21 V. Pick one.
- The LM317's **minimum load current** (3.5 mA typ, 5 mA max for the L-suffix
  `[from memory]`) is satisfied by the divider alone: 1.25 V / 150 Ω = **8.3 mA**
  `[calc]`. That is a real design constraint the 240R→150R change quietly fixed;
  worth writing down so nobody "optimises" the divider back up later.
- **It is not an LDO.** `hardware/bom.csv` row 37 calls it "Adjustable LDO"; the
  LM317's dropout is ~1.7–2.5 V `[from memory]`. Irrelevant from 12 V, wrong in the
  BOM.

### 5.3 There is no reason to put the 74AHCT125 on this rail — Note

Raised only to close it off: §2 recommends a *separate* local 5 V for the buffer,
not this one. Keeping the DAC's AVDD clean of a 2 MHz cable driver is correct.

---

## 6. Beads and bulk capacitance

### 6.1 The bead current-rating argument is better than the field's — Note (credit)

"a saturated bead is a wire … Read the series, not the footprint"
`[repo] hardware/module/power-entry.md`. Of the designs that use beads, Ripples
specifies a Würth part number (742792664), Helium specifies "1 kΩ @ 100 MHz",
grow specifies "100 Ω @ 100 MHz" — **none of them state a current rating**
[web] refs 1, 12, 14. Erica sidesteps the problem entirely with 100 µH power
inductors [web] ref 6. Woody's `FB-IN` row is the only spec in the comparison set
that names the parameter that actually matters `[repo] hardware/bom.csv` row 40.
Keep this and keep the wording.

### 6.2 Entry bulk is at the very top of the field range, and the two in-scope files disagree about it — **Medium**

Field numbers per rail, from the fourteen: **10 µF ×7, 22 µF ×3, 47 µF ×3,
100 µF ×1** (§0). Median 10–22 µF; 47 µF is used by Erica (twice) and by PER|FORMER.

`power-entry.md` draws **4 × 47 µF = 188 µF total** and says entry bulk is "2–5× the
surveyed norm" `[repo] hardware/module/power-entry.md`. `hardware/bom.csv` row 76
says **100 µF on +12 V, 47 µF on the other three = 241 µF**, with a specific
argument (balancing the decay rate of ±12 V at power-down so the op-amps don't get
dragged to the surviving rail) `[repo] hardware/bom.csv`.

Two things:

- **The files disagree** and the diagram is the one people build from. Fix the page.
- 47 µF on a single rail is defensible (Erica, PER|FORMER). **241 µF across four
  rails on one 8 HP module is at the top of anything I found**, and it charges
  through three 1N5817s every time the module is plugged into a live bus. See §7.1.
- The power-down-balance argument in row 76 is good and is not in the field set at
  all; it should be *on the page*, not only in a CSV cell.

### 6.3 100 nF per supply pin — Note

`C-DECOUPLE` at 21 pieces, one per IC supply pin `[repo] hardware/bom.csv` row 42.
Universal in the field (Ripples alone has twelve 100 nF on its rails
[web] ref 1). No finding. (But see §9 — the count is stale.)

---

## 7. Will it misbehave in a real case?

### 7.1 Module inrush at hot-plug — **Medium**

241 µF (or 188 µF) charging through three Schottkys from a live bus is 10–24× the
field norm per rail `[calc]`. The 1N5817's I_FSM is ~25 A `[from memory]` so the
diodes survive; the question is whether the *bus* dips enough to reset a neighbour.
Eurorack has no standard for this because no standard module presents this much
capacitance. Two mitigations, neither expensive:

- Take the +12 V entry bulk down to 47 µF and keep row 76's decay-balance argument
  by trimming the −12 V side instead, or
- accept it and simply **write down** that this module should be plugged in with
  the case powered down — which is the normal Eurorack instruction anyway.

Note the asymmetry the design has already got right: the **2.2 mF downstream of the
load switch is ramped**, so the big capacitance is not the problem. It is the
entry bulk, which is *not* behind anything.

### 7.2 Interaction with a case's soft-start — **Low, and the design is on the right side of it**

At rack power-on with the toggle left ON, the LT1641 holds off until VCC ≥ 9 V
`[from memory: LT1641 9–80 V operating range, confirmed in the product page extract
at https://www.analog.com/en/products/lt1641-1.html]`, then ramps its own output
over 50–100 ms at 0.26–0.53 A `[repo] hardware/module/power-entry.md`. That
*defers and rate-limits* 2.2 mF of the case's total inrush. This is strictly better
than the unswitched alternative and better than anything in the comparison set.

Commercial Eurorack supplies generally use **foldback** current limiting
[web] search extract citing https://intellijel.com/shop/power/tps-power-supply-eurorack/
and https://intellijel.com/downloads/manuals/tps-power-supply-eurorack_manual_2019.09.16.pdf
(both **blocked** to direct fetch) — a supply in foldback during the case's own
start-up is exactly the condition under which an extra ramped 0.5 A is preferable to
an extra unlimited surge. No change needed.

### 7.3 Noise injected back onto the rails — **Low at the module, see §8 for the real one**

Inside the module, the split diode and the `PWR_GND` star mean the instrument's
switching and PWM currents do not share the analog rail's series elements or the
analog return `[repo] hardware/module/power-entry.md`. That part is sound, and the
refusal to give `DIG_GND` its own path to the star is the correct call (a 2 MHz
return belongs under its own trace).

### 7.4 The instrument-end protection is a coherent scheme — Note (credit)

`carrier.md` §1's `D-REVSHUNT` (SS34, cathode to +12 V, ahead of `L-BUCK-IN`) plus
the module's latching limiter is precisely the **"shunt diode + fuse"** topology
that Mutable ships on Ripples' −12 V rail (§1.4) — with the load switch playing the
fuse, at the source end, where the instrument's own faults cannot bypass it
`[repo] hardware/controller/carrier.md`. Under a rollover cable the SS34 sees
~0.94 A at ~0.5 V for one fault-timer period `[calc]` — trivial for a 3 A part. The
reasoning about putting the diode ahead of the inductor is also right. Good work.

---

## 8. The element nobody costed: 360 mA of foreign current in the rack's shared copper — **High**

This is the finding I would put first if the report were ordered by importance
rather than by design element.

The split diode (§1.1) removes ~80 mV of shared-Vf modulation **inside the module**.
It does nothing about the same 360 mA flowing through everything **outside** it.

**Supply side.** Ribbon (28 AWG ≈ 0.213 Ω/m `[from memory]`, +12 V on two
conductors, 30 cm) ≈ 32 mΩ `[calc]`; busboard trace (1 oz, 4 mm wide, 0.25 m) ≈
31 mΩ `[calc: 1.72e-8 × 0.25 / (0.004 × 35e-6)]`; plus PSU output impedance and
wiring. Call it 100 mΩ round trip. At 360 mA that is **~36 mV of breath- and
LED-correlated movement on the rack's +12 V rail, upstream of both of this module's
diodes** `[calc]`. It is ~45 % as large as the 80 mV the second diode deletes, and
it is not deletable in the module.

**Return side, and this is the one that matters.** The 360 mA returns through the
ribbon's GND conductors and the busboard ground to the PSU. A neighbouring module's
ground returns the same way. The *differential* path between this module's slot and
a neighbour's is maybe 20–40 mΩ (a few ribbon conductors plus a busboard segment)
`[calc]`, so the two modules' 0 V references move **7–15 mV apart, in time with
breath and LED activity** `[calc: 0.36 A × 0.02–0.04 Ω]`.

A CV output's sleeve *is* the module's ground. So that 7–15 mV appears directly
across the patch cable as an error at the receiving module:

> **7–15 mV on a 1 V/oct pitch output = 8–18 cents of breath-correlated pitch bend**
> `[calc: 1 cent = 1/1200 V = 0.833 mV]`

That is the *same order of magnitude as the effect the third diode exists to
delete*, it arrives by the same root cause (360 mA of foreign current in shared
copper), and it is not mentioned anywhere in `power-entry.md`, `carrier.md` §1 or
ADR 0005. It is also — cleanly — the reason no published Eurorack module pulls
hundreds of milliamps of foreign load through the bus.

**What to do about it:**

- **Acknowledge it.** It caps achievable pitch stability and it is larger than
  several of the errors this design spends parts on.
- It is only partly fixable in the module. Connect **every** GND pin on the 16-pin
  header (not one), keep the `PWR_GND` copper wide, and put the module in a slot
  electrically close to the PSU.
- The real lever is the 360 mA itself, which ADR 0005's load table says is
  dominated by lighting `[repo] docs/decisions/0005-power-architecture.md`. Every
  100 mA removed from the umbilical is ~2–4 cents.
- E6 should measure this directly: instrument on a scope between this module's
  ground and a neighbour's, LEDs cycling.

And note the interaction with §1.1: if the "80 mV → 20 cents" sensitivity claim
were true, this effect would be catastrophic rather than marginal. The two claims
cannot both stand. Resolve §1.1 first.

---

## 9. Repo-internal consistency inside my scope — **High**

`hardware/module/power-entry.md` documents a subsystem the BOM has deleted. Anyone
building from the page builds the wrong module.

| Page says `[repo] hardware/module/power-entry.md` | BOM says `[repo] hardware/bom.csv` |
|---|---|
| Panel LED and `OE ×4` share the **LM311 presence comparator's** open collector; `R-OE-PU 10k`, `R-LED 820R` to bus +5 V | row 78: "that comparator is **DELETED**"; row 79: `R-LED-PANEL` is **2k2 from the module's +12 V analog rail** — "Was 820R from bus +5V … that node is gone with the comparator" |
| "The **comparator and the watchdog** stay on the LM317's 5.21 V" | row 42: "the **watchdog is deleted**"; row 67: "THE WATCHDOG IS DELETED (U-WATCHDOG, R-WDT, C-WDT all gone)" |
| `OE` is driven, active-low, via a 10 k pull-up | row 34: "**OE IS TIED ENABLED**. The presence-gated OE is deleted along with its comparator" |
| "The **LM311 itself runs on ±12 V**" (whole paragraph justifying it over an LM393) | no LM311 line item exists; only row 42's decoupling count still references it |
| Entry bulk is **4 × 47 µF** | row 76: **100 µF (+12 V) / 47 µF (−12 V, +5 V)** |
| `PCB-MODULE` description still lists "watchdog" | row 70 — same stale word |

The page is otherwise the strongest document in the set; this section is simply a
revision that did not land. It needs deleting, not editing.

---

## 10. The two answers asked for

### The single element I would change to match field practice

**Stop requiring the bus +5 V rail. Derive the 74AHCT125's supply locally from the
protected +12 V with a 78L05-class part.** (§2.)

Zero of the eight comparison designs that need a sub-12 V rail take it from the
bus; all eight make it locally, using the same three-pin regulators. The Eurorack
+5 V bus rail is optional in the standard and absent from most cases. In this
design it is additionally the **only rail with no reverse-polarity protection**, and
the BOM already documents how a reversed ribbon on that rail reaches the DAC's
`SYNC` pin. The fix is one TO-92, two caps and ~70 mW, and it deletes a hard
case-compatibility requirement, a bead, a 47 µF cap and an unprotected rail.

(The *most urgent* change is different: §3.2, the 10 nF fault-timer capacitor. But
that is a specification bug, not a field-practice mismatch.)

### The single element where this design is genuinely better than the field

**The current-limited, ramped, fault-timed load switch on the exported +12 V rail.**
(§3, §4.)

Befaco's expander header puts raw +12 V on a pin and stops thinking about it.
Expert Sleepers passes an attached USB device's draw straight onto the rack's +12 V
rail and asks the user to do the arithmetic. Only PER|FORMER protects a rail it
sends off-panel, and only at 5 V with an auto-retry USB switch. This design is the
only one I found that treats a **detachable, 2 m, 12 V, multi-millifarad, LED-loaded
off-panel feed** as the hazard it is, with a programmed inrush ramp, a programmed
fault timer, foldback, and an SOA-sized pass device. Given the load, the field's
convention here would be actively dangerous. Keep it — and fix the timer capacitor,
the foldback/ramp interaction and the `ON`-pin network so it actually works.

---

## Sources that failed

Named as instructed. All of these are blocked by the egress proxy for this session;
where I used their content it came from search-result extracts of those exact URLs
and is marked as such in the text.

- `https://www.analog.com/…` — **all** LT1641 material, including
  `…/data-sheets/164112fc.pdf` and `…/data-sheets/1641fd.pdf`, and
  `https://www.analog.com/en/products/lt1641-1.html`
- `https://www.st.com/resource/en/datasheet/stmps2141.pdf` (STMPS2151)
- `https://doepfer.de/a100_man/a100t_e.htm` and `https://www.doepfer.de/`
- `https://expert-sleepers.co.uk/fh2.html`, `https://www.expert-sleepers.co.uk/es8usermanual.html`
- `https://www.modwiggler.com/` (all threads)
- `https://en.wikipedia.org/wiki/Eurorack`, `https://sdiy.info/wiki/Eurorack`
- `https://www.befaco.org/`, `https://intellijel.com/`, `https://tiptopaudio.com/`,
  `https://www.4mscompany.com/`, `https://www.nonlinearcircuits.com/`,
  `https://www.musicthing.co.uk/`, `https://note.com/` (HAGIWO),
  `https://division-6.com/learn/eurorack-power/`, `https://www.thonk.co.uk/`,
  `https://www.alldatasheet.com/`, `https://www.ti.com/`, `https://hackaday.io/`
- GitHub **HTML** pages via `curl` return 403 through the proxy (WebFetch and
  `git clone` and `raw.githubusercontent.com` all work). GitHub's code-search web UI
  requires sign-in; the code-search API works.

Nonlinearcircuits, HAGIWO and the Doepfer A-100 DIY pages were all unreachable, so
this comparison set is GitHub-weighted. It does still contain four commercial
manufacturers (Mutable Instruments, Befaco, Erica Synths, Super Synthesis) and two
widely-built community designs (Ornament & Crime, PER|FORMER).
