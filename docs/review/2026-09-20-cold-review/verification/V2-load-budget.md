# V2 — The instrument's +12 V load budget, built from first principles

**Falsification agent. Task: settle four conflicting answers to "what does the
instrument draw on +12 V".** Everything below is re-derived from component
figures, not from any of the four existing tables. Where I reach the same number
as an existing agent, I say so; where I do not, I say why.

**Provenance marks used throughout:**

| Mark | Means |
|---|---|
| `[ds-v]` | Datasheet figure **retrieved this session** (search summary; vendor PDFs are blocked by the egress proxy — source named at each use) |
| `[ds-m]` | Datasheet figure **from memory**, treat as a claim to check |
| `[repo]` | The project's own stated figure |
| `[est]` | My engineering estimate, reasoning given |
| `[calc]` | My arithmetic from the above |

---

## 1. The answer, first

### 1.1 The load table

All currents are at the **instrument's +12 V node**, i.e. what flows in the
umbilical and through the module's load switch. The node voltage is solved
self-consistently against the series drop (§4), so the conversion of 5 V loads
uses the voltage that actually arrives, not 12.00 V.

| State | 5 V rail | 12 V direct | **Umbilical total** | V at instrument | Power in the body | Interior rise @2.89 K/W (hands on plate) |
|---|---|---|---|---|---|---|
| **A — Quiescent** (both MCUs booted, radio off, screen dark, LEDs blanked) | 180 mA | 123 mA | **212 mA** | 11.52 V | 2.44 W | 7 K (10 K) |
| **B — Typical play** (radio off, status screen, single-hue strips tracking breath, breath bar on the matrix) | 226 mA | 248 mA | **359 mA** | 11.40 V | 4.10 W | 12 K (17 K) |
| **B′ — Typical play + a live config/telemetry session** (SoftAP, WebSocket) | 336 mA | 248 mA | **414 mA** | 11.36 V | 4.70 W | 14 K (20 K) |
| **C — Worst case the firmware clamp permits** (3 W of commanded light, allocated where it costs most — all on the matrix — plus WiFi) | 928 mA | 119 mA | **579 mA** | 11.22 V | 6.49 W | 19 K (27 K) |
| **C′ — same, display board at its own worst** (full-field bright screen + WiFi) | 1028 mA | 119 mA | **630 mA** | 11.18 V | 7.04 W | 20 K (30 K) |
| **D — Absolute worst if the clamp fails**, first seconds: everything full white | 1338 mA | 1024 mA | **1795 mA** | 10.21 V | 18.3 W | 53 K (77 K) |
| **D′ — the *sustained* clamp-failure state**: buck has shut down on its own protection, logic dead, strips latched full white | ~0 | 1023 mA | **1132 mA** | 10.76 V | 12.2 W | 35 K (51 K) |

**Headline numbers to quote: 212 mA quiescent, 360 mA typical, 580–630 mA
clamp-legal worst, 1.8 A peak / 1.13 A sustained if the clamp fails.**

Two secondary allocations of the same 3 W clamp, for completeness — the clamp
does not say *where* the light is spent, and it matters:

| Clamp-legal variant | 5 V rail | Umbilical total |
|---|---|---|
| 3 W all on the **strips** (12 V direct, no conversion) | 328 mA | **531 mA** |
| 3 W split 50/50 | 628 mA | **554 mA** |
| 3 W all on the **matrix** (through the buck) | 928 mA | **579 mA** |

The spread is only ±5 % on the umbilical, but it is **3× on the 5 V rail**
(328 → 928 mA), and the 5 V rail is where the 1 A regulator lives. That is the
single most important structural fact in this budget and §7.5 returns to it.

### 1.2 Adjudication

| Answer | Verdict |
|---|---|
| **ADR 0005 — 250 mA** | **Wrong by 1.4× on typical, 2.3–2.5× on the clamp-legal worst.** It is not a bad estimate of a *different instrument*: one with no 8×8 matrix, no WS2815 quiescent term, and no lighting clamp. All three arrived after it was written. |
| **ADR 0004 — ~275 mA** | Same composition, same omissions, +25 mA. ADR 0004 is right that it is "the least trustworthy number in this document" and right to forbid sizing anything from it — and then the BOM sized two protection devices from it anyway. |
| **Previous review — 410–430 mA "typical"** | **Right diagnosis, wrong label.** It found the two loads that were actually missing (WS2815 quiescent, the onboard matrix) and its total is close to my **B′ = 414 mA**, i.e. it is a *radio-active* typical, not a typical. It never produced a clamp-legal worst case, which is the number the hardware has to be sized from, so everything downstream that used 410–430 mA as the design maximum is still 40 % low. |
| **B6 — 392 typical / 555–589 clamp-legal** | **Closest, and its worst case is confirmed.** Same decomposition and the same two clamp allocations as mine, independently. My 579/531 against its 589/555: **within 2 %.** Its typical is 9 % above mine, entirely from a higher display-board estimate (150 mA vs my 90 mA at 5 V, radio off). **This is the table the project should adopt.** |
| **B5 — ≈440 mA** | **Not a typical and not a worst case — an inconsistent hybrid.** It converts the entire 3 W clamp at 12 V (`3 W / 12 V = 250 mA`) no matter which device spends it, while its 5 V line item ("400 mA of 5 V load") excludes the matrix's commanded light. So the same 3 W is counted once at 12 V and never at 5 V. Under the matrix-heavy allocation the correct figure is 579 mA, and B5's own parenthetical alternative (545 / 590 mA) is right — its headline is not. |
| **B10 — 356 mA idle / 606–650 mA normal worst** | **Structurally correct, ~10 % high, and its "idle" is not idle.** It takes the top of ADR 0014's "dev boards 330–400 mA" for a state it calls idle — 400 mA at 5 V implies WiFi and a bright screen — and uses 120 mA of strip quiescent (above the datasheet's 2.1 mA/px max) and 85 % buck efficiency (§3.3 says ~90 %). Its worst-case *range endpoints* are derived exactly right: 250 mA if the light goes to the strips, 294 mA if it goes through the buck to the matrix. |

**The convergence is the finding.** Four independent builds — mine, B6's, B5's
alternative reading, B10's — put the clamp-legal worst case in a
**530–650 mA** band. Nobody who actually enumerates the loads gets near 250 mA.
Both protection devices in the BOM are set at **500 mA**, i.e. **below a state
the firmware is explicitly permitted to command**, and one of them is inside a
body that cannot be reopened.

---

## 2. Why the four answers differ — the reconciliation

Not opinion: each gap is one specific term.

| From | To | Δ | Cause |
|---|---|---|---|
| ADR 0005, 250 mA | ADR 0004, 275 mA | +25 | The module's DAC regulator was added to the *module* line, and the instrument line drifted upward without a derivation. |
| ADR 0004, 275 mA | my typical, 359 mA | +105 | **WS2815 driver quiescent, 50 px × 2.1 mA = 105 mA `[ds-v]`.** Every pixel carries a second always-powered backup driver — the exact feature ADR 0014 bought the part for. ADR 0014's density table is emission-only and never adds it back. |
| " | " | +25 | **The 8×8 matrix's idle drivers**, ~50 mA at 5 V `[repo, ADR 0007]` = 25 mA at 12 V. The matrix arrived in ADR 0014, after both power figures were written. |
| " | " | −46 | Offsetting: my display-board and real-time-board estimates are *lower* than the 330–400 mA the ADRs assume for the pair with the radio off. |
| my typical 359 | my clamp-legal 579 | +220 | **The 3 W lighting clamp**, which no ADR power figure includes at all. |
| B10's 650 | my 579 | −71 | Its dev-board figure (400 mA at 5 V) and 85 % efficiency vs my 310 mA / 90 %. |
| B5's 440 | my 579 | +139 | Its double-miss on matrix light (§1.2). |

**Two arithmetic/method errors worth recording, both mine to call:**

- **Converting at 12.00 V is wrong by ~4 %.** The 5 V branch is a
  constant-*power* load. Lower arriving voltage ⇒ *more* input current, and the
  arriving voltage is 11.2–11.5 V, not 12.0 V (§4). Every existing table
  converts at 12 V. At state C this understates by 21 mA.
- **ADR 0014's `×0.49` conversion factor is right by coincidence.** It embeds
  85 % efficiency at 12.0 V (`5/(12×0.85) = 0.490`). The correct pair is 90 %
  efficiency at 11.2 V (`5/(11.22×0.90) = 0.495`). Two errors of ~6 % in
  opposite directions. The factor survives; neither input does.

---

## 3. Every load, enumerated, with provenance

### 3.1 On +12 V directly (no conversion)

| Load | Figure | Provenance | Qty | 12 V current |
|---|---|---|---|---|
| **WS2815 strip quiescent** | < 2.1 mA per pixel, at 12 V | `[ds-v]` — WS2815 spec, "quiescent current less than 2.1 mA", retrieved this session via the Worldsemi/Normand datasheet mirrors | 2 × 420 mm @ 60/m = **50 px** | **105 mA** (max). ~50 mA if the commonly-measured ~1 mA/px `[ds-m]` holds |
| **WS2815 commanded light** | **13 mA/px** measured (9.4 W/m at 60/m = 0.78 A/m at 12 V) `[ds-v]`; **15 mA/px** datasheet ceiling `[ds-v]`; **20 mA/px** as assumed by ADR 0014 `[repo]` | LED Lab / Hanron WS2815 specification summaries, retrieved this session | 50 px full white | **650 / 750 / 1010 mA** — I carry **1010 mA** for sizing, but note ADR 0014's strip figures are **~30–55 % conservative** |
| — realistic use | single hue at ~40 % | `[repo]` ADR 0014's own table | both runs | 130 mA |
| — at the 3 W clamp, strips only | 3 W / 12 V | `[calc]` | both runs | 250 mA |
| **REF5050 quiescent** | 0.8 mA typ, 1.2 mA max | `[ds-m]` TI REF50xx (B6 reports this `[verified]`) | 1 | 0.8 mA |
| **MPXV4006DP supply** | 10 mA max | `[repo]` ADR 0003 / NXP `[ds-m]` | 1 | 10 mA — drawn **from +12 V through the OPA2197 buffer**, so it lands on the 12 V rail, not on a 5 V rail |
| **OPA2197, both channels** | ~1 mA/ch | `[ds-m]` TI | 2 ch | 2 mA |
| **R-78E5.0 no-load quiescent** | ~5 mA at 12 V in | `[ds-m]` Recom | 1 | 5 mA (only visible in state A; absorbed into efficiency under load) |
| TVS array leakage, electrolytic leakage, 100 k pulldown | µA each | `[est]` | — | < 0.5 mA, ignored |
| **Analog subtotal on +12 V** | | | | **13–14 mA** |

Cross-check against B6 (13 mA) and B10 (15 mA): agreement.

### 3.2 On the 5 V rail (through the buck)

| Load | Figure | Provenance | 5 V current |
|---|---|---|---|
| **Real-time board** — ESP32-S3-Matrix, radio off | ESP32-S3 at 240 MHz dual core, RF off: **30–50 mA at 3.3 V** `[ds-v]` (Espressif ESP32-S3 datasheet / forum measurements, retrieved this session); + QMI8658C ~1.5 mA `[ds-m]`; + the board's own LDO quiescent. The LDO is a series device, so 5 V current ≈ 3.3 V current | `[est]` from `[ds-v]` parts | **55 mA** typ, **70 mA** max |
| **8×8 matrix, idle drivers** | 64 × WS2812C-2020 controller idle, 0.6–1 mA each | `[repo]` ADR 0007's own estimate; **ROADMAP already requires this measured at E1** | **38–64 mA**, use **50 mA** |
| **8×8 matrix, commanded** | 5 mA per channel, 15 mA/px full white, 960 mA full field | `[repo]` ADR 0014 / WS2812C-2020 `[ds-m]` | 0 → **960 mA** |
| — at the 3 W clamp, matrix only | 3 W / 5 V | `[calc]` | **600 mA** |
| **Display board** — T-Display-S3 AMOLED (base) | **No board-level figure is published** `[ds-v]` — I checked LilyGO's wiki and product pages this session and none exists. Built up: ESP32-S3 radio off 30–50 mA `[ds-v]`; WiFi TX peak 180–240 mA `[ds-v]`, association/serving average ~100 mA at 3.3 V `[est]`; RM67162 AMOLED panel, power follows lit pixels `[repo]` ADR 0008 — a dark status layout is tens of mA, a bright field is 100 mA+ `[est]` | `[est]`, flagged | **70 mA** dark/idle, **90 mA** typical, **200 mA** with a live config session, **300 mA** worst (bright + WiFi), bursts +150–250 mA for 1–2 ms |
| **74AHCT125 level shifter** | static µA; dynamic `C·V·f` = 50 pF × 5 V × 0.8 MHz × 2 data lines = 0.4 mA | `[calc]` | **< 2 mA** |
| **3.3 V loads**, via the real-time board's onboard LDO (the LDO passes the current from 5 V) | 4 × 74LVC165A static µA + ~0.5 mA dynamic `[calc]`; MCP3202 550 µA typ / 750 µA max `[ds-m]`; I²C pull-ups ~0.4 mA avg; ADC divider 4.7 V / 25 k = 188 µA | `[calc]` | **2–3 mA** |
| *(not in the BOM)* key-chain pull-ups | The 74LVC165 has no internal pull-ups and the BOM carries no pull-up line. At 10 k: 0.33 mA per closed key, ≤8 closed = 2.6 mA. At B10's proposed 2.2 k: **12 mA** | `[calc]` | **+3 to +12 mA when fitted** |

**5 V rail totals** — 180 mA quiescent, 226 mA typical, 928–1028 mA at the
clamp-legal worst, 1338 mA if the clamp fails.

### 3.3 The conversion, and the efficiency number

**Recom R-78E5.0-1.0** `[ds-v]`, retrieved this session (Recom R-78E-1.0
datasheet via Arrow/Digi-Key/LCSC summaries):

- Input **8–28 V** (some summaries say 7–28 V), output 5.0 V / 1.0 A
- Switching frequency **330 kHz** for the 3.3 V and 5 V variants
- **Efficiency: 93 % max at minimum input, 85 % at maximum input, 91 % headline**
- Short-circuit protection with **continuous automatic recovery**;
  overcurrent trip point at **200 % of maximum load**

12 V input sits near the *bottom* of the input range, which is the
high-efficiency end. **I use η = 0.90 (±0.02) at 0.2–1.0 A output, 0.87–0.88 at
≤0.2 A.** This settles the spread between the four tables: B5's 0.91 is right,
B6's 0.88 is slightly pessimistic, ADR 0014's and B10's 0.85 is the figure for
28 V input and is wrong here by ~6 %.

Conversion used everywhere below:

```
I_12V  =  P_5V  /  ( η × V_node )          not  P_5V / (η × 12.0)
```

Worked, for state C: `928 mA × 5.00 V = 4.64 W`; `4.64 / (0.90 × 11.22 V) =
459 mA`. Add 105 mA strip quiescent + 14 mA analog = **578 mA**.

---

## 4. What voltage actually arrives — and what ADR 0005's table gets wrong

### 4.1 The real series path

ADR 0005's drop table counts **the cable and nothing else**. The full path from
the rack bus to the instrument's 12 V node:

| Element | Value | Provenance | Drop at 579 mA |
|---|---|---|---|
| 1N5817 Schottky (`D-REVPOL`) | V_f 0.30–0.40 V | `[ds-m]` onsemi curve | **0.40 V** |
| Ferrite bead ≥ 1 A, 1206/1210 | DCR 50–100 mΩ | `[ds-m]` | 0.035 V |
| Load switch FET + sense resistor | ~0.10 Ω assumed | `[est]` (TPS2553 is 85 mΩ `[ds-m]`; a hot-swap FET + 25 mΩ shunt is ~60 mΩ) | 0.058 V |
| Module PCB + IDC header | ~30 mΩ | `[est]` | 0.017 V |
| 2 × mated RJ45 pairs, both conductors | ≤ 20 mΩ per contact | `[ds-m]` | 0.046 V |
| 2 m Cat5e, 24 AWG **stranded**, out and back (4 m of copper) | 0.095 Ω/m | `[ds-m]` wire tables + stranding allowance | **0.220 V** |
| *(polyfuse, if fitted)* | R_initial ≈ 0.15 Ω `[ds-v]` | Littelfuse 1206L050/15YR distributor data, retrieved this session | *(0.087 V)* |
| **Total series R** | **0.65 Ω** (0.80 Ω with the polyfuse) | | **0.78 V** (0.86 V) |

So: **11.22 V arrives at the clamp-legal worst case, 11.40 V in typical play,
11.52 V at quiescent** — from a 12.00 V bus, and ~0.2 V lower from a realistic
loaded 11.8 V bus.

Cable-gauge sensitivity at state C (this is real: the project designates the
lead a consumable to be replaced from a drawer):

| Lead | Round-trip R | Umbilical current | V at instrument |
|---|---|---|---|
| 24 AWG solid (ADR 0005's implicit assumption) | 0.337 Ω | 577 mA | 11.25 V |
| **24 AWG stranded (what the BOM requires)** | 0.380 Ω | 579 mA | **11.22 V** |
| 26 AWG stranded (common in slim patch leads) | 0.580 Ω | 584 mA | 11.10 V |
| 28 AWG stranded (common in "snagless" leads) | 0.920 Ω | 592 mA | 10.89 V |

### 4.2 Verdict on ADR 0005's table

> | Delivered at | Current | Drop | Arrives as | Error |
> | **12 V** | 250 mA | 84 mV | **11.92 V** | **0.7 %** |
> | 5 V | 600 mA | 202 mV | 4.80 V | 4.0 % |

**The arithmetic is right and every input is wrong.**

- `250 mA × 0.337 Ω = 84.3 mV` ✓ and `600 mA × 0.337 Ω = 202 mV` ✓.
- **The current is wrong**: 360 mA typical, 579–630 mA clamp-legal.
- **The scope is wrong**: it counts the cable only. The Schottky alone is 0.40 V
  — five times the cable drop it presents as the whole story.
- **"Arrives as 11.92 V" is wrong by 0.7 V.** The real figure is **11.2–11.4 V**.
- **The 5 V row understates its own case.** Its 600 mA comes from "the
  instrument's load is roughly 3 W". The load is 4.1 W typical and 6.5 W at the
  clamp — so a 5 V umbilical would carry **0.9–1.4 A**, dropping 0.31–0.48 V,
  i.e. **6–10 % error, not 4 %**. And a 5 V umbilical forces 5 V LED strips
  (ADR 0014), roughly doubling the strip current on top of that.
- **"The instrument's load is roughly 3 W" is itself wrong** — it is 2.4 W with
  nothing happening and 6.5–7.0 W at the clamp.

**The decision survives and is strengthened; the table should be rewritten.**
And the framing should change with it: at 12 V delivery the arriving voltage is
**not an accuracy question at all** — nothing is referenced to it (the
ratiometric sensor runs from the REF5050, ADR 0003). It is purely a headroom
question, and the headroom is:

| Floor | Value | Margin at the clamp-legal worst (11.22 V) |
|---|---|---|
| R-78E5.0 minimum input | 8 V `[ds-v]` | **3.2 V** |
| WS2815 minimum supply | 9.5 V `[ds-m]` | **1.7 V** |

Even at state D (1.8 A, 10.21 V) both floors hold. **That** is the argument for
12 V distribution, and it is much stronger than the 0.7 %-error argument
currently written down — which is an accuracy claim about a rail whose accuracy
does not matter.

---

## 5. The load switch's current limit

### 5.1 The four constraints, as numbers

| Constraint | Requires |
|---|---|
| **Must never trip in a firmware-legal state** | > 630 mA steady (state C′), plus ~+40 mA of WiFi TX burst → **≥ 0.75 A** with tolerance |
| **Must start into the instrument's bulk capacitance** | See §6: **≥ 0.9 A** with a 50 ms programmed ramp, or **≥ 0.7 A** with 100 ms |
| **Should arrest a gross clamp failure** before the body bakes | < 1.13 A (state D′, strips latched full white) |
| **Must keep the etherCON power contact inside rating** | etherCON/RJ45 is **~1.5 A per contact** `[repo, ADR 0004's own comparison table]` → **≤ 1.5 A**, and ≤ 1.0 A for a 1.5× margin |

The window is **0.9 A to 1.13 A**. It is narrow because the clamp-legal worst
case and the clamp-failure case are only 1.8× apart.

### 5.2 Recommendation

> **Set the limit at 1.0 A nominal** (0.85–1.15 A over a ±15 % programming
> tolerance), **latch-off rather than auto-retry**, with a **programmed
> dV/dt ramp of 50–100 ms** and a **fault timer longer than the ramp**
> (150–250 ms), and `/FAULT` brought to the module's panel LED.

Why each part:

- **1.0 A**, not 500 mA: 500 mA is *below* the legal steady load (§1.1) in a
  state the firmware is permitted to command, and below it by enough that a
  −15 % unit (425 mA) sits under **typical play**. The instrument would
  current-limit while being played normally. This is the single most consequential
  error in the current design and five agents plus this one have now reached it
  independently.
- **1.0 A, not 1.5 A**: 1.0 A is below the latched strips-full-white state
  (1.13 A), so a gross clamp failure trips the limiter rather than cooking the
  body at 12 W with no firmware left to intervene. At 1.5 A that state is
  permitted indefinitely. It also keeps the connector contact at 2/3 of rating.
- **Latch-off**, not auto-retry: auto-retry into a latched full-white strip
  state motorboats — buck drops out, load falls, retry, collapse, repeat — which
  is a rediscovery of exactly the oscillating-protection failure ADR 0014
  analyses. Latch-off makes it one visible event and one toggle cycle.
  (This matches the register's S1 proposal, LT1641-2 + N-FET + sense resistor.)
- **Programmed ramp**, not "let the current limit do it": §6.

**Honest limitation, which should be written down:** a 1.0 A limiter **cannot**
be the thermal guard. A *partial* clamp failure — strips and matrix both at
60 % — draws about 1.1 A and 11 W, which sits right at the edge and may not
trip, while still driving a 32 K interior rise. Only firmware bounds a sustained
bright state that is electrically legal and thermally not, exactly as ADR 0014
already says. The limiter catches gross failures and shorts; that is its job.

**Coupled recommendation:** restating the firmware clamp (§7.5) so the legal
worst case lands at ~0.55 A widens the margin from 1.35× to 1.55× at the
worst-case-low limit, which is what makes 1.0 A comfortable rather than tight.

---

## 6. Can it start through a current limit?

### 6.1 The capacitance

| Element | Value | Source |
|---|---|---|
| `C-STRIP-BULK`, 2 off | 470–1000 µF each → **0.94–2.0 mF** | `[repo]` BOM / ADR 0014 |
| Buck input capacitor | Recom specifies 10 µF `[ds-m]` — **absent from the BOM** (B6 finding 4 is correct) | |
| Decoupling, TVS, etc. | < 10 µF | `[est]` |
| **Total on the 12 V node** | **≈ 1.0–2.1 mF** | |

`C-BULK-DISP` sits on the 5 V side and is charged through the buck's own
soft-start; 220 µF to 5 V is 2.75 mJ and does not affect the 12 V ramp.

### 6.2 Uncontrolled inrush — the reason a switch is needed at all

`[calc]`: E = ½CV² = **72–148 mJ**; peak current = 12 V / 0.65 Ω = **18.5 A**;
τ = RC = 0.65–1.34 ms. A bare toggle takes that on its contacts every time.
ADR 0005 is right that this needs a load switch.

### 6.3 Starting at 500 mA — it does not

At the instant of switch-on the firmware has blanked nothing yet, but the strips
are unpowered and therefore dark, so the load during the ramp is the quiescent
state: strips' quiescent (from ~9.5 V) + buck input (from ~8 V) ≈ **210 mA**.

At a 500 mA limit the switch is in **constant-current regulation for the whole
ramp**, and the charge current available is 500 − 210 = 290 mA:

`t = C·ΔV / I = 2.06 mF × 11.4 V / 0.29 A = 81 ms`

81 ms of continuous constant-current operation. Two things kill it:

- Any fault timer shorter than 81 ms **latches off on every normal switch-on**.
- The regulation point is unstable: the buck is a constant-power load, so as the
  node sags the buck demands *more* current, and the operating point runs
  downward to the buck's UVLO. B5 calls this motorboating and is right.
- A −15 % unit at 425 mA nominal has 215 mA of charge current against a 210 mA
  load: **it may never finish charging at all.**

### 6.4 Starting at 1.0 A with a programmed ramp — it does, comfortably

| Ramp | C = 1.0 mF | C = 1.5 mF | C = 2.06 mF | Peak incl. 210 mA load (2.06 mF) |
|---|---|---|---|---|
| 10 ms | 1140 mA | 1710 mA | 2348 mA | 2558 mA — **exceeds any sane limit** |
| 20 ms | 570 | 855 | 1174 | 1384 mA — **exceeds 1.0 A** |
| **50 ms** | 228 | 342 | **470** | **680 mA** ✓ |
| **100 ms** | 114 | 171 | **235** | **445 mA** ✓ |

`I_charge = C · dV/dt` `[calc]`.

**Specify a 100 ms ramp** (`dV/dt ≈ 114 V/s`): peak 445 mA against a
worst-case-low limit of 850 mA is **1.9×**. FET stress during the ramp:
average V_ds ≈ 5.7 V × ~0.45 A ≈ **2.6 W for 100 ms = 0.26 J** — trivially
inside the single-pulse SOA of any DPAK or SO-8 FET `[est]`.

**Also specify `C-STRIP-BULK` = 470 µF, not 1000 µF.** ADR 0014's own transient
arithmetic (and B6's confirmation of it) shows 470 µF is sufficient at the
strips; the difference is entirely startup burden.

### 6.5 The case the ramp does not cover: hot-plug

The load switch is **upstream of the connector**. Mating the etherCON with the
module powered bypasses the ramp entirely and puts the full 18.5 A, 72–148 mJ
into the contacts as they wipe. The ramp protects switch-on and nothing else.

**Write the operating rule down: mate and unmate with the module toggle off.**
It costs nothing, and it is now the only thing standing between the connector
and a pitted power contact. ROADMAP E6 already schedules the hot-plug inrush
measurement — keep it, and use it to decide whether an NTC or a small series
resistance at the instrument entry is worth the drop.

---

## 7. The remaining dependent questions

### 7.1 The polyfuse: **delete it**

Three independent reasons, in order of force.

**(a) Its hold current is below the load.** `F-POLY` is a 500 mA-hold PPTC. PPTC
hold current is specified at ~23 °C and derates in a warm ambient by roughly
×0.7–0.8 at 45–50 °C `[ds-m]`. The interior reaches **34 °C in typical play and
41–49 °C at the clamp** (§1.1, at a 22 °C room), so the effective hold is
**350–400 mA**:

| State | Umbilical current | vs derated hold (≈375 mA) |
|---|---|---|
| Quiescent | 212 mA | 0.57× — safe |
| **Typical play** | **359 mA** | **0.96× — at the threshold** |
| **Clamp-legal worst** | **579–630 mA** | **1.5–1.7× — trips, or creeps** |

A PPTC above hold does not open cleanly; it walks up its R–T curve, the rail
sags, the buck (constant power) draws more, the device heats further. **That is
precisely the runaway loop ADR 0014 describes and believes it has deleted.**
The load switch was added; the thermally-hysteretic series element was never
removed.

**(b) It is redundant, and in the wrong place.** It sits at the *instrument's*
entry, downstream of the module limiter. Every fault it could see, the limiter
sees first and faster. It protects nothing upstream of itself — and upstream of
itself is 2 m of constantly-flexed consumable cable and two connectors, which is
where the faults actually are.

**(c) It has a voltage-rating trap.** `[ds-v]`, retrieved this session: the
default **1206L050YR is a 6 VDC part** (0.5 A hold, 1.0 A trip, ~0.15 Ω). On a
12 V rail that is a destructive failure. The correct variant is
**1206L050/15YR** (15 VDC). The BOM line says only "PPTC 1206 500mA hold" — the
voltage rating is unspecified, and the part you get by ordering the obvious part
number is wrong.

**One correction to the other agents while deleting it:** B6 and B5 both
overstate its resistance. B6 uses R_min = 0.75 Ω and derives **0.44 V of drop
and 0.26 W inside the body**; B5 uses 0.35 Ω. The distributor data for the
1206L050/15YR gives **0.15 Ω** `[ds-v]`, so the real figures are **87 mV and
50 mW** at state C — about **5× smaller than B6 claims**. It is *not* "the
largest resistance in the 12 V path"; the cable (0.38 Ω) is, and the Schottky's
0.40 V dwarfs both. **The case for deletion is (a) and (b), not the drop.**

**If a belt-and-braces device inside the body is still wanted**, it must be
sized above the clamp-legal worst *with derating*, i.e. **≥ 1.5 A hold** — at
which point it can never trip before the 1.0 A module limiter, which is the
proof that it is dead weight. Delete it, and use the vacated footprint for the
reverse-polarity/negative-transient shunt the register already wants there.

*(On B10's alternative — a 500 mA fast-blow fuse in each strip's feed: too
small. A single strip at full white is 505 mA and the clamp permits 250 mA per
strip today. If per-strip fusing is wanted it should be 1 A.)*

### 7.2 ADR 0005's umbilical drop and arriving voltage: **wrong, decision unaffected**

Settled in §4.2. Rewrite the table with 360 / 579 mA, include the diode and
connectors, state 11.2–11.4 V as the arriving voltage, and re-cast the argument
as headroom (3.2 V above the buck's floor, 1.7 V above the strips' floor) rather
than as a 0.7 % accuracy claim about a rail nothing is referenced to.

### 7.3 Starting through a current limit: **yes at 1.0 A with a 100 ms programmed ramp; no at 500 mA**

Settled in §6.

### 7.4 The 1 A regulator: the clamp permits **93–103 %** of it

At state C the 5 V rail carries **928 mA**; at C′, **1028 mA**. Both are
firmware-legal. The R-78E5.0-1.0 is a 1 A part, and its rating derates with
ambient — inside a body at 41–49 °C it is not a 1 A part.

This confirms B6 finding 7 independently, with one addition in the design's
favour and one against:

- *In favour:* the R-78E has **short-circuit protection with continuous
  automatic recovery** and a **200 % overcurrent trip point** `[ds-v]`. It will
  not latch. And because the matrix is *on* the rail that collapses, the load
  falls, the rail recovers, the MCU boots and ADR 0014's blank-at-boot rule
  clears the state. That loop genuinely closes.
- *Against:* the 200 % trip point means the part does **not** protect itself at
  1.0 A — it will happily pass 1.33 A (state D) until its own thermal shutdown
  intervenes. That is why state D peaks at 1.8 A rather than being capped at the
  nameplate.

ADR 0013 and `docs/reference/latency-budget.md` both specify **one regulator per
board**; ADR 0005's power tree quietly reduced it to one for both and did not
argue the reduction. Three documents describe two different power trees. Fitting
the second R-78E5.0 — a 3-pin SIP on a 7805 footprint — resolves the
contradiction *and* the headroom problem at once.

### 7.5 The thermal clamp: **right idea, wrong quantity, three ways**

**(a) It is denominated in emitted LED watts; the body is heated by umbilical
watts.** Decomposing my state C (6.49 W at the instrument):

| | W | Clamp sees it? |
|---|---|---|
| Commanded LED light | 3.00 | **yes** |
| WS2815 driver quiescent, 50 px × 2.1 mA × 11.2 V | 1.18 | no |
| 8×8 matrix idle drivers | 0.28 | no |
| Display board (200 mA at 5 V, reflected) | 1.11 | no |
| Real-time board core | 0.39 | no |
| Level shifter + 3.3 V loads | 0.05 | no |
| REF5050 + OPA2197 + sensor | 0.16 | no |
| Buck conversion loss at 90 % | 0.33 | no |
| **Unclamped subtotal** | **3.49** | |

**The clamp bounds 46 % of the thermal load.** ADR 0014 quotes the clamp's cost
as "roughly 9 K of interior rise" — that is 3 W × 3 K/W, the *increment*. The
total is 6.5 W → **19 K**, or **27 K** with the player's hands over the plate.
ADR 0014 has the baseline written down ("the existing electronics dissipate
roughly 5 W") and then compares the increment to the tolerance instead of adding
it to the baseline.

**(b) Two equal clamp-legal states stress the hardware completely
differently.** 3 W on the strips is 0 mA on the buck; 3 W on the matrix is
600 mA on a 1 A part, and costs 3.33 W of body heat rather than 3.00 W because
it arrives through a 90 %-efficient converter. **One scalar cannot express
both.**

**(c) Quiescent lighting is outside the clamp.** 1.46 W of strips-and-matrix
idle that the clamp, by construction, cannot see — because firmware clamps
*commanded* values and nothing commands quiescent. "Lighting costs at most 3 W"
is really "lighting costs 4.5 W".

**Proposed restatement — two terms, both computable in firmware before the
write:**

```
1.  Thermal term, in umbilical watts, the quantity that actually heats the body:
        P_fixed(measured at E1/E6)  +  P_strip_cmd  +  P_matrix_cmd / 0.90   ≤  6.0 W
    With P_fixed ≈ 3.5 W that leaves ~2.5 W of commanded light — still twice
    ADR 0014's "realistic use" figure of 1.5 W.

2.  Regulator term, which the thermal term cannot see:
        I_matrix_cmd  ≤  350 mA at 5 V
    Keeping the 5 V rail under 800 mA (80 % of the part) even with the display
    board at its own worst.
```

Checked: that pair lands at **554 mA / 6.23 W / 18 K**, and — the point — it
makes the legal worst case a *designed* number instead of a discovered one,
which is what lets the 1.0 A load switch have 1.55× of margin instead of 1.35×.

**Keep the M8 soak** as ROADMAP already requires, and instrument it with three
thermocouples (breath sensor, R-78E case, an acrylic side channel) rather than
one. My own quick check of the coefficient agrees with ADR 0014 and with B6: the
2.89–3 K/W figure is sound. It is what it gets multiplied by that is wrong.

---

## 8. Corrections to the other agents, for the record

| Claim | Status |
|---|---|
| B6: the polyfuse is "the largest resistance in the 12 V path", 0.44 V, 0.26 W | **Overstated ~5×.** R_initial is 0.15 Ω `[ds-v]`, giving 87 mV and 50 mW. The cable (0.38 Ω) is the largest resistance and the Schottky (0.40 V) the largest drop. Deletion is still right, on hold current and redundancy. |
| B6: "the two spare conductors are currently idle — parallel them onto +12 V" | **Based on a superseded conductor budget.** ADR 0004's revised budget uses **eight of eight** (BREATH/AGND, +12 V/PWR_GND, MOSI/CS, SCLK/DIG_GND). There are no spares to parallel. |
| B6 / B10 / ADR 0014: buck efficiency 85–88 % | **~90 %** at 12 V in `[ds-v]`. 85 % is the figure at 28 V input. |
| B10: "356 mA idle" | Not idle — it embeds a WiFi-active dev-board figure. True quiescent is **212 mA**. |
| B5: "≈440 mA umbilical steady" | Internally inconsistent about where the clamp's 3 W is spent (§1.2). Its own alternative figures, 545/590 mA, are the right ones. |
| ADR 0014: strips full white = 1.01 A for 0.84 m (20 mA/px) | **Conservative by 30–55 %.** Measured is ~13 mA/px (0.78 A/m at 60/m) and the datasheet ceiling ~15 mA/px `[ds-v]`. Conservative is the right direction for sizing — but the "12.1 W / ~36 K" pathological figure in ADR 0014 is correspondingly about a third high. |
| BOM `F-POLY`: "PPTC 1206 500mA hold" | Voltage rating unspecified; the obvious part number (1206L050YR) is a **6 V** part `[ds-v]`. Moot if deleted. |
| BOM `D-REVPOL` 1N5817 | 1 A part `[ds-m]` carrying instrument + module current. Fine at 630 mA; **1.8× over rating in state D**. A 1N5822/SS34 (3 A) costs the same and removes the question — and reduces the V_f modulation the register already flags as a pitch-accuracy route. |

---

## 9. What to measure, and what would falsify this

The table's uncertainty is concentrated in **two** numbers, and ROADMAP already
schedules both:

| Measurement | At | Falsifies |
|---|---|---|
| **Each dev board's 5 V current**, separately: idle, display at full brightness, WiFi associating and serving | E1 | The largest term in my uncertainty. My display board is 70/90/200/300 mA; B6's is 150/250/400. **±100 mA at 5 V = ±50 mA at 12 V.** If the pair stays under 200 mA at 5 V with WiFi active, my typical drops to ~320 mA; if it reaches 400 mA, it rises to ~440 mA and B5's headline becomes right for the wrong reason. |
| **8×8 matrix idle current** | E1 | ADR 0007's ~50 mA is an estimate. ±25 mA at 5 V = ±12 mA at 12 V. |
| **Umbilical current with a probe**, at the 3 W clamp with the light on the matrix, WiFi active, soaked at M8 temperature, for 30 min | E6 | The whole table. **If it stays under 450 mA, I am wrong and 500 mA survives.** I expect 560–640 mA. |
| **Inrush on switch-on and on hot-plug** | E6 | §6. If the node reaches 11 V monotonically in under 50 ms with charge current under 300 mA, my capacitance estimate is high. |
| **PPTC hold current at 45 °C interior**, if anyone argues for keeping it | E6/M8 | §7.1(a). |
| **Total umbilical power and interior air temperature at the clamp** | M8 | §7.5. If measured K/W is under 2, the thermal restatement relaxes. |

**The one-line summary for the register:** the instrument draws **360 mA
typical and 580–630 mA in a state the firmware is explicitly allowed to
command**; both 500 mA protection devices are set below that; **B6's table is
the one to adopt**; the load switch wants **1.0 A with a 100 ms programmed ramp
and latch-off**; the polyfuse should be **deleted**; ADR 0005's arriving-voltage
table should be **rewritten as a headroom argument at 11.2 V**; and the thermal
clamp should be **denominated in umbilical watts with a separate matrix-current
cap**, because 3 W on the matrix and 3 W on the strips are not the same 3 W.
