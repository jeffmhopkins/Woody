# A8 — Interconnect: every cable in the system as one subsystem

**Reviewer:** A8, cold. **Date:** 2026-09-21.

**Scope:** the 2 m umbilical, the key chain loom, the display loom, the two LED
looms, the internal tail loom between the etherCON and the carrier, and the
grounding and shielding that ties them together. Indexed by **circuit node** and
**BOM reference**, not by document.

**Method and disclosure.** I read `docs/decisions/0003`, `0004`, `0005`, `0009`,
`0014`, `hardware/controller/carrier.md`, `hardware/controller/cluster-boards.md`,
`hardware/module/digital-and-supervision.md`, `hardware/module/power-entry.md`,
`hardware/module/breath-receive-stage.md`, `hardware/bom.csv` and `ROADMAP.md`.
I did **not** read `docs/review/**` or `docs/research/**`, by instruction, so
where I duplicate an existing finding that is coincidence and where I contradict
one, I have not seen it.

**Evidence marks.** `[repo] <file>` = read in this repo. `[calc]` = my
arithmetic, shown inline. `[web] <url>` = fetched this session. `[from memory]`
= I could not verify it; check before ordering.

**Network:** `neutrik.com`, `scpcat5e.com`, `led-stuebchen.de` and
`ledyilighting.com` were all blocked by the egress proxy (403 on CONNECT).
Search summaries got through; primary datasheets did not. Everything marked
`[web]` is a search-result summary, not a datasheet reading.

---

## Findings, ranked

| # | Node / Ref | Finding | Rank | Confidence |
|---|---|---|---|---|
| 1 | `J-UMB` pins 4,5 | `MOSI` and `CS` share one twisted pair with **no return conductor**. Intra-pair coupling is 20–40× worse than any other path in the cable, it lands on the one net whose corruption is sticky, and noise margin is 1.1–3.4:1 | **Showstopper** | High on the mechanism, Medium on the millivolts |
| 2 | `J-UMB` pin 8 `DIG_GND` | The net is named in three documents and **drawn on none of them at the instrument end**. The two possible answers give opposite failure behaviour and opposite verdicts on the module's star rule | **Showstopper** | High |
| 3 | shield / etherCON shells | No termination policy anywhere. If the module shell bonds to the panel, instrument return current takes a second path through the rack chassis — **~7 cents of breath-correlated pitch bend by a third route** | **High** | Medium (rests on a stated bus-resistance assumption) |
| 4 | `CABLE-UMB` | The project's 0.168 Ω/2 m figure is the **solid-core** number for a cable the BOM insists must be **stranded**. TIA's patch-cord limit is 14 Ω/100 m → **0.28 Ω**. Everything derived from it is 1.2–1.67× optimistic | **High** | High |
| 5 | `U-LOADSW` / `LED-SIDE` | The 1.0 A limit and ADR 0014's clamp-off worst case (1522 mA) collide. A firmware bug **latches the instrument dark** mid-performance and needs a walk to the rack. ADR 0014 calls the clamp "a comfort feature"; it is load-bearing for uptime | **High** | High |
| 6 | `J-CHAIN` ×8 | Eight identical keyed connectors and four identical cables. Swap IN/OUT on one board and two 74HC165 outputs fight at abs-max. **Keying does not prevent it.** Fix is four 100 Ω resistors on boards not yet made | **High** | High |
| 7 | `U-TVS-MODULE` | Deferred on "the module is retrofittable". The **threat originates at the player's hand** and arrives at the module as common mode. Deferring the cheap end of a two-ended problem is backwards | **High** | Medium |
| 8 | `J-UMBILICAL` | RJ45 durability is **750 mating cycles**; the instrument-end chassis jack is bonded in forever. No hot-plug rule written, and hot-plugging into 2.2 mF latches the load switch | **Medium** | Medium–High |
| 9 | `J-DISP` | No BOM row, no keying, no pinout, and `C-BULK-DISP` is `TBD` on a rail that needs **≈1000 µF** to hold a WiFi burst over 360 mm | **Medium** | Medium |
| 10 | `J-LED-L/-R` | Not keyed, not in the BOM, identical to each other, and the wire gauge for a 0.5 A conductor is unspecified. Reversed puts 19 mA into a 74AHCT125 output clamp rated ±20 mA | **Medium** | Medium |
| 11 | `J-UMBILICAL` variant | Feedthrough vs solder-tag is deferred to E12/M7, **after** E13 lays out the carrier that needs the footprint. The stated cost of feedthrough is ~46 mV and ~2 ppm — i.e. nothing | **Medium** | High |
| 12 | E11 acceptance | E11's criteria **cannot detect** the failure the pin map creates, and the umbilical is write-only so the DAC's control registers can never be read back | **Medium** | High |
| 13 | `J-UMB` pins 1,2 | **The analog pair is fine**, by ~80 dB. Crosstalk, LED ripple and IR drop are all four orders below audibility. The AGND sense-return decision is validated | **Note (positive)** | High |
| 14 | `J-CHAIN` pin 4 `SH/LD` | A `SH/LD` glitch costs far **less** than ADR 0001 claims — and the marker pattern cannot see it. The decision is still right; the justification is wrong | **Note** | Medium–High |
| 15 | ADR 0014 §"the LEDs do reach the breath channel" | The "0.4 % gain compression" figure omits the in-amp's CMRR and is **~200× pessimistic** | **Low** | High |
| 16 | `C-FILT-BREATH` | No tolerance in the BOM row. `breath-receive-stage.md` requires ±1 %; default C0G is ±5 % and costs 20 dB of CMRR at the LED PWM rate | **Low** | Medium |
| 17 | `C-STRIP-BULK` | I expected this to be in the wrong place. **It is not** — arithmetic below. Recorded so nobody else spends an afternoon on it | **Note** | High |

---

## Shared inputs used throughout

| Quantity | Value | Source |
|---|---|---|
| Cat5e DC resistance, solid horizontal | ≤ 9.38 Ω/100 m | `[web]` search summary of TIA/Cat5e spec sheets |
| Cat5e DC resistance, **patch cord** | ≤ **14 Ω/100 m** | `[web]` same |
| Cat5e mutual capacitance | 5.6 nF/100 m = **56 pF/m** | `[web]` same |
| Cat5e NVP | 0.65–0.70 → v ≈ 2.0×10⁸ m/s | `[web]` same |
| Cat5e worst-pair NEXT at 100 MHz | ≥ 35.3 dB | `[web]` |
| RJ45 contact resistance / durability | ≤ 20 mΩ, **750 cycles** | `[web]` IEC 60603-7 summaries |
| etherCON rated current per contact | 1.5 A (Neutrik); generic RJ45 often **1 A at 50 °C** | `[web]` |
| Umbilical current, typical play | 359 mA | `[repo] 0005` load table |
| Umbilical current, clamp-legal worst | 579 mA | `[repo] 0005` |
| Umbilical current, clamp fails | **~1522 mA** | `[repo] 0005` |
| Load switch limit | 1.0 A, **latching** (`-1`) | `[repo] power-entry.md` |
| SCLK | 2 MHz, edge 1–2 ns | `[repo] 0004, bom.csv` |
| Series resistors at the driving end | 220 Ω ×3 (`R-SPI-SER`) | `[repo] bom.csv` |
| In-amp gain | G = 2.185, effective 2.161; jack span 9.94 V | `[repo] breath-receive-stage.md` |
| Breath differential pole | 482 Hz, at the **module**, ahead of the in-amp | `[repo] breath-receive-stage.md` |
| WS2815 PWM rate | ~2 kHz | `[repo] 0014`, confirmed `[web]` |
| WS2815 `VIH` | 0.7 × **internal 5 V** rail, not 0.7 × 12 V | `[web]` — see node note below |

**Cable electrical length** `[calc]`:

```
v   = 2.0e8 m/s              (NVP 0.65-0.70)
T_d = 2 m / 2.0e8 = 10 ns     one-way
2·T_d = 20 ns                 round trip
```

This matches `bom.csv`'s own "a 1–2 ns edge on a 20 ns round trip" `[repo]`.
**Every crosstalk mechanism in this cable is therefore *saturated*** — the
aggressor's edge is 10× shorter than the round trip, so near-end coupling
reaches its full amplitude and does not scale with edge rate. Slowing the edges
will not help; only the pin map and the receiver will.

**Conductor resistance, corrected** `[calc]`:

```
Repo figure (ADR 0003, implied by its 8.4 µV / 50 µA row):  0.168 Ω per conductor
  → that is 8.4 Ω/100 m, i.e. the SOLID-core number.

BOM row CABLE-UMB: "Cat5e STP patch lead, STRANDED, ~2m"  [repo] bom.csv
TIA patch-cord limit:  14 Ω/100 m × 2 m = 0.280 Ω per conductor   [web]
Typical stranded 24 AWG patch:            0.20–0.23 Ω per conductor

Plus contacts: 2 mated interfaces × 20 mΩ = 0.040 Ω per conductor  [web]

Design value used below: R_cond = 0.28 + 0.02 = 0.30 Ω  (worst legal)
                         R_loop  = 0.60 Ω  (out and back)
```

**This is finding #4 and it propagates.** `0003`'s shared-ground table,
`0005`'s "122 mV cable", `carrier.md §2`'s 2.2 mV sense-error derivation and
`0004`'s whole AGND argument all rest on 0.168 Ω. **Multiply them by 1.67 for a
worst-legal stranded lead.** None of the conclusions flip — I have rechecked
each below — but the margins are smaller than written and the numbers should be
corrected before anyone else builds on them.

---

## NODE `J-UMB` pins 4 and 5 — `MOSI` / `CS`, the pair with no return

### The map contradicts its own document

ADR 0004 states, twice:

> "With real Cat5/6 each signal sits against a ground in its own twisted pair."
> `[repo] 0004`

> "`+12V / PWR_GND` … `SCLK / DIG_GND` … `MOSI / CS` … `BREATH / AGND`"
> `[repo] 0004` revised conductor budget

**These are not the same statement.** Pins 4 and 5 are the blue pair. Both
conductors are signals. `MOSI` has no return in its pair and neither does `CS`;
their return current flows in `DIG_GND` on pin 8, which is in the brown pair,
several millimetres and one different lay-length away.

The arithmetic is forced and it is worth stating so nobody argues the map:
eight conductors, and the signal set is `BREATH`, `AGND`, `+12V`, `PWR_GND`,
`MOSI`, `CS`, `SCLK`, `DIG_GND` — exactly eight. **Three digital signals and
one digital ground cannot be four pairs.** One pair must carry two signals. The
design chose `MOSI`+`CS`. That choice is never argued anywhere in the repo; the
pin-assignment section argues only about *adjacency at the connector*, which is
a different and much smaller effect (quantified below).

### What sharing a pair costs

The two conductors of a Cat5e pair are, by construction, a 100 Ω differential
transmission line — the tightest coupling in the cable. Mutual capacitance
`[calc]` from `[web]` 56 pF/m:

```
C_m(4,5) = 56 pF/m × 2 m = 112 pF     between MOSI and CS specifically
```

Backward (near-end) coupling coefficient for two coupled lines:

```
K_b = (Z_0e − Z_0o) / (2 (Z_0e + Z_0o))

Z_0o = Z_diff/2 = 50 Ω                     (the pair IS a 100 Ω diff line)
Z_0e = even mode per conductor, vs the remote returns (pins 6, 8, shield)
       — the uncertain input. UTP in a jacket with nearby grounded
         conductors: 70–120 Ω is the defensible range  [from memory]

Z_0e = 70 Ω  →  K_b = 20/240  = 0.083  →  V_NEXT = 0.083 × 3.3 V = 274 mV
Z_0e = 80 Ω  →  K_b = 30/260  = 0.115  →  V_NEXT = 0.115 × 3.3 V = 380 mV
Z_0e = 120 Ω →  K_b = 70/340  = 0.206  →  V_NEXT = 0.206 × 3.3 V = 680 mV

Saturated, because 2·T_d = 20 ns >> t_r = 2 ns.
```

At the **module** end the picture is worse, not better, because `CS` is
unterminated there `[calc]`:

```
Near-end source impedance on CS = ESP32 ~30 Ω + R-SPI-SER 220 Ω = 250 Ω
Γ_near (odd mode, 250 Ω vs 50 Ω) = (250−50)/(250+50) = +0.667
Γ_far  (10 kΩ pull-up + AHCT input ≈ open)            = +1.0

Amplitude arriving and doubling at the module node:
  0.667 × 2 × K_b × 3.3 V   →  365 mV … 907 mV for K_b = 0.083 … 0.206
```

### What it lands on

`CS` is asserted **low** for the whole 32-bit frame — which is exactly when
`MOSI` is toggling. The vulnerable state `[calc]`, 74AHCT125 on the bus +5 V
rail, `V_IL(max)` = 0.8 V `[from memory]`:

```
CS driven low:  5 V × 250 Ω / (250 Ω + R-SPI-PULL 10 kΩ) = 122 mV at the pin
Noise margin to V_IL:  800 − 122 = 678 mV

Aggressor at the module node: 365–907 mV
Margin ratio: 678/907 = 0.75×  (fails)  …  678/365 = 1.86×  (thin)
```

**So the plausible range straddles the threshold.** I cannot close this on paper
— the even-mode impedance is the uncertain input and only a measurement settles
it — but a design in which the *best* case is 1.9:1 and the worst case is a
failure, on this particular net, is not acceptable as-drawn.

### Why this net and not another

From `hardware/module/digital-and-supervision.md` `[repo]`:

> "A stray edge on `CS` re-frames the 32-bit word, and a DAC8568 frame carries
> the software reset, the clear-code register and the internal-reference
> enable — so a mis-framed word is a **sticky** failure that the 4 kHz refresh
> does not clear, unlike a corrupted data bit which self-heals in 250 µs."

So the design has put **the one net whose corruption is permanent** in a twisted
pair with **the one net that toggles hardest**, with nothing between them, and
has protected it with a pull-up resistor. A single glitch can disable the
DAC8568's internal reference — which is the pitch stage's voltage scale — and
nothing in the system notices, because **the umbilical is write-only and there
is no `MISO`** `[repo] 0004`. The symptom is "every CV output went wrong once,
in the middle of a set, and came back after a power cycle".

### For contrast: what the ADR *did* optimise

ADR 0004 spends its pin-assignment section on the 13 mm untwisted region inside
the RJ45 plug, and concludes the power pair "acts as a guard". **That claim is
true, and it is worth about 15 mV** `[calc]`, RJ45 pin pitch 1.02 mm
`[from memory]`:

```
Adjacent-pin mutual capacitance in the plug, 13 mm, d = 1.02 mm, r = 0.255 mm:
  C = π·ε0·L / ln(d/r) = π × 8.854e-12 × 0.013 / ln(4) = 0.26 pF per plug
  Both plugs: 0.52 pF

Divider against CS's node capacitance (the cable's 112 pF dominates):
  0.52 / (0.52 + 112) = 0.46 %  →  0.46 % × 3.3 V = 15 mV
```

**15 mV in the plug versus 365–907 mV in the pair.** The section reasons
carefully about the effect that is 25–60× smaller and never mentions the one
that dominates. That is the shape of the error, and it is worth naming because
the reasoning itself is sound — it is just applied to the wrong geometry.

### The options, costed

**Fix A — reassign, zero parts, unretrofittable after M7.**

```
1,2  BREATH / AGND        unchanged
3,6  +12V / PWR_GND       unchanged
4,5  SCLK / MOSI          the two synchronous nets share the pair
7,8  CS / DIG_GND         CS gets a dedicated twisted return
```

`CS` then couples only pair-to-pair. `[calc]`, Cat5e NEXT scaling
`NEXT(f) = 35.3 − 15·log10(f/100)` with `f` in MHz `[web]`:

```
At 2 MHz, 100 m:  35.3 − 15·log10(0.02) = 35.3 + 25.5 = 60.8 dB
Length: NEXT saturates near λ/4. λ(2 MHz) = 2e8/2e6 = 100 m → λ/4 = 25 m.
        2 m / 25 m = 0.08 → +21.9 dB
NEXT(2 m, 2 MHz) ≈ 82.7 dB  →  ratio 7.3e-5
SCLK fundamental: (4/π)(3.3/2) = 2.10 V pk = 1.49 V rms
Coupled onto CS:  1.49 V × 7.3e-5 = 109 µV
```

**109 µV against 678 mV of margin — a factor of 6200, versus 0.75–1.9 today.**
The cost is that `SCLK` now couples into `MOSI` at the same 365–907 mV, and it
arrives synchronously with the DAC's sampling edge. But the repo's own words
say a corrupted data bit "self-heals in 250 µs". **Trading a sticky failure for
a self-healing one is the whole trade**, and it is free.

**Fix B — delete `CS` from the cable, regenerate `SYNC` at the module.** Frees
a conductor and gives every digital signal its own return, which is what ADR
0004's prose already claims:

```
1,2 BREATH/AGND   3,6 +12V/PWR_GND   4,5 SCLK/DIG_GND   7,8 MOSI/DIG_GND2
```

ADR 0004 records that `SYNC` regeneration "was the alternative under
consideration" and rejected it because `R-MOSI-SER` made it unnecessary
`[repo] 0004` — but that reasoning is about *MOSI's* signal integrity, not
about conductor count, so it does not dispose of this. Cost: a retriggerable
gap-detector at the module (a 74AHCT14 + RC, or a 74HC123 — the module page
already knows how to size one and has deleted one). **Firmware must insert a
deliberate inter-frame gap**, which it does not today: at 2 MHz the six frames
are drawn back to back and there is no gap to detect `[repo] carrier.md §4`.
Real engineering, not free, and it puts framing on a timing constant.

**Fix C — a Schmitt receiver and an RC on `CS` at the module. This is the one
to take.** `hardware/module/digital-and-supervision.md` *already proposes the
part*, for a different reason:

> "a **74AHCT14 hex Schmitt inverter**, which two independent reviews already
> recommended adding as baseline for edge cleanup on `SCLK`, `MOSI` and `CS`
> over 2 m of Cat5. One part, three jobs. **Not adopted here because it is a
> design decision rather than a correction.**" `[repo]`

It is not a design decision. It is the thing that makes the pin map survivable.
Sizing `[calc]`:

```
Glitch width = 2·T_d = 20 ns
CS's own minimum feature at 2 MHz = one clock half-period = 250 ns
RC with τ = 40 ns:  rejects a 20 ns pulse (reaches 1 − e^(−0.5) = 39 % of a
                    375 mV glitch = 146 mV, far under the AHCT14's ~1.5 V
                    positive-going threshold at 5 V [from memory])
                    passes a 250 ns edge with 6τ of settling
  R = 1 kΩ, C = 39 pF.   Two passives and one $0.30 package.
```

**And it is at the module, which is behind four screws.** That is the single
most important scheduling fact in this finding: Fix C is retrofittable, Fix A
and Fix B are not.

**Recommendation:** take **Fix A** (free, and must be decided before M7) **and**
fit the **Fix C** footprint at E12 whether or not it is populated. Do not rely
on Fix C alone, because it defends the module's input and does nothing for the
2 m of cable that is now radiating a 907 mV common-mode transient at 2 MHz.

---

## NODE `J-UMB` pin 8 — `DIG_GND`, the net nobody drew

`grep -rn 'DIG_GND'` over the whole repo, excluding review and research
`[repo]`, returns nine hits. Every one of them is a *label*. **No drawing
anywhere connects pin 8 to anything at the instrument end.**

- `carrier.md` block diagram: lists `8 DIG_GND` in the connector pinout.
- `carrier.md §1`: shows a `PWR_GND` pour. No `DIG_GND`.
- `carrier.md §4`: `U-TVS-SPI` → **`PWR_GND`**.
- `carrier.md §3`: `U-TVS-CHAIN` → **`DIG_GND`** — a net that appears in no
  other drawing on that page.

So the carrier has three ground names, two of them used in TVS return paths,
and no statement of how any of them relate. That is not a stylistic gap; the
two possible answers give opposite behaviour in four places.

### If `DIG_GND` and `PWR_GND` are the same net at the instrument (likely)

They are also joined at the module's star point `[repo] 0004`. **Pins 6 and 8
are then shorted at both ends and are two power returns in parallel.**

```
[calc]  Return splits by resistance: 0.30 Ω ∥ 0.30 Ω = 0.15 Ω
        Loop resistance improves:  0.60 Ω → 0.45 Ω
        BUT: half the return current flows in conductor 8,
             which is SCLK's voltage reference at the module.

At 359 mA typical play:  180 mA × 0.30 Ω = 54 mV DC offset on SCLK's reference
LED PWM AC component (derived below, 34.5 mA): 17 mA × 0.30 Ω = 5.2 mV at 2 kHz
Against AHCT V_IL 0.8 V: 6.8 % of margin. Tolerable.
```

Tolerable — **but the module's entire grounding section is then defeated.**
ADR 0004 spends a page on keeping `PWR_GND` and `DIG_GND` on separate copper to
the star, and a 0.30 Ω strap through the cable shorts them anyway. The section's
mechanism (360 mA of IR drop landing under the pitch reference) is real and the
module-side rule is right; it is just not the only path.

### If they are separate nets at the instrument

Then `DIG_GND` carries only SPI return current, the module's star rule is
meaningful end to end — **and a broken `PWR_GND` conductor kills the instrument
outright**, which is the good failure. Under the shorted topology, a broken
`PWR_GND` is *silent*: the instrument keeps running on conductor 8 alone, with
all 359–579 mA in the one conductor twisted against `SCLK`, and nobody finds
out until the LEDs come up.

### The repo already contradicts itself about the module end

| Document | Says |
|---|---|
| `0004` grounding section | "**`DIG_GND` likewise** — its own path to the star." `[repo]` |
| `power-entry.md` grounding | "**`DIG_GND` is *not* given its own path to the star**, which an earlier revision of ADR 0004 asked for: a 2 MHz SPI return wants the pour directly under its trace, and routing it to a distant star point is the classic split-plane mistake." `[repo]` |
| `ROADMAP` E12 gate | "`PWR_GND` and `DIG_GND` each on their own copper" `[repo]` |

`power-entry.md` is right on the engineering and the other two were not updated.
**E12's acceptance criterion currently mandates the thing the schematic page
says is a mistake.** Two of the three have to change, and E12 is a gate.

**Required:** one sentence on `carrier.md §1` saying what pin 8 lands on, one
sentence on `carrier.md §4` saying which ground `U-TVS-SPI` and `U-TVS-CHAIN`
return to and why they differ, ADR 0004's bullet corrected to match
`power-entry.md`, and the ROADMAP E12 row corrected. My recommendation:
**tie them at the instrument (one ground in a hand-held box is the only
defensible answer), state it, and accept the parallel return** — then delete
ADR 0004's separate-copper rule for `DIG_GND` and keep it for `PWR_GND`, which
is where the 360 mA actually is.

---

## NODE: cable shield, `J-UMBILICAL` shells, and `MECH-GNDBOND` — the problem loop

### What the repo says about the shield

Everything, in one sentence:

> "**Shielded (STP/FTP) preferred.** Twisted pairs are what make the analog
> breath channel survive (ADR 0003) and any Cat5e has those, but the shield is
> free at this price and the breath pair is the one signal with no digital
> margin to spare." `[repo] 0004`

`bom.csv` `CABLE-UMB` says "Shielded preferred" `[repo]`. **There is no
statement anywhere of whether the screen is terminated at one end, both ends or
neither, what the etherCON shells connect to, or whether the instrument-end
chassis connector is isolated from its backing plate.** An STP lead with an
undefined shield topology is worse than a UTP lead, because it adds a
2 m conductor of unknown termination to a system whose grounding is otherwise
carefully reasoned.

### The loops, drawn

```
LOOP A  (intended, benign)
   module star ──[1N5817]──[FB-IN]──[LT1641 + FET]── pin 3 ──┐
                                                             │ 2 m twisted pair
   module star ◄─────────────────────────────── pin 6 ───────┘
   Differential, twisted, area ≈ 0. Carries 359–579 mA. Fine.

LOOP B  (accidental, finding #2)
   pin 6 and pin 8 shorted at both ends → return splits ~50/50
   Loop area = cable cross-section × 2 m ≈ 3 mm × 2000 mm = 6000 mm²
   Consequence: LED PWM lands on SCLK's reference. 5 mV. Survivable.

LOOP C  (the one that is a problem)
   instrument key plate ──[MECH-GNDBOND]── PWR_GND pour ── pin 6 ── module star
        │                                                              │
        └── backing plate? ── etherCON shell ── SHIELD ── etherCON shell┤
                                                     │                 │
                                            8HP aluminium PANEL        │
                                                     │                 │
                                              rack rails ── case ── PSU earth
                                                                       │
                                                        bus board ground ┘
```

**Loop C exists the moment the shield is bonded at both ends and the module's
etherCON shell touches the 8HP panel.** Neutrik D-series chassis connectors
mount through the panel with a metal flange; whether the shell is electrically
common with the panel depends on the variant and on whether isolating hardware
is used, and **the repo has not chosen a variant** (`J-UMBILICAL`: "variant
TBD", decided at E12/M7 `[repo] bom.csv`).

### What Loop C costs

The instrument's return current then has two paths home: pin 6 to the module's
star, or the shield → panel → rails → case → PSU earth → bus board → the
module's ground pin `[calc]`:

```
Path 1 (pin 6):         0.28 Ω cable + 0.02 Ω contacts          = 0.30 Ω
Path 2 (shield route):  drain wire ~0.1 Ω (24 AWG, 2 m)
                      + shell-to-panel      10 mΩ – 1 Ω  (anodising!)
                      + panel-to-rail       10 mΩ – 1 Ω  (M3 into a rail)
                      + rail/case/PSU/bus   ~50 mΩ
                                             = 0.2 Ω (good) … 2.2 Ω (bad)

Fraction diverted through the rack chassis:
   0.30 / (0.30 + 0.2)  =  60 %   at 0.2 Ω
   0.30 / (0.30 + 2.2)  =  12 %   at 2.2 Ω
   → 43–347 mA of instrument return current through the rack's chassis
     and bus ground, modulated by the LED animation, i.e. by BREATH.
```

That current re-enters the bus board at the PSU and flows along the bus ground
rail to reach our module's header. Our pitch output is referenced to our
header; the receiving VCO is referenced to **its** header. The shared segment
carries our diverted current `[calc]`, on a stated assumption:

```
ASSUMPTION [from memory]: a Eurorack bus board's ground rail is ~10 mΩ per
slot for a PCB bus (50–100 mΩ/slot for a ribbon bus). Say 3 slots shared
between our module and the VCO: 30 mΩ.

200 mA diverted × 30 mΩ = 6.0 mV between our ground and the VCO's ground
At 1 V/oct:  6.0 mV × 1200 cents/V = 7.2 cents

— and it moves with the lighting, which moves with breath.
```

**That is breath-correlated pitch bend of the same magnitude as the two the
project has already found and fixed** — the shared-Schottky term (~20 cents,
fixed with a second diode) and the shared-copper term (5.7–7.2 cents, fixed with
the star rule) `[repo] 0004`. This is a third route to the same symptom, it
arrives through a part the BOM calls "free", and nobody has written it down.

The assumption is doing real work here and I have flagged it. If the bus ground
is 1 mΩ/slot the number is 0.24 cents and this drops to a Note. **E6 can measure
it in ten minutes** — it already measures rack interaction `[repo] ROADMAP`.

### Recommendation

1. **Isolate the module's etherCON shell from the 8HP panel** (plastic shoulder
   washers, or a variant with an isolated shell), and bond the shell to the
   **module's star point** with a short wire. The shield then terminates on the
   same node as everything else in the module and Loop C never forms.
2. **At the instrument, bond the shell to `PWR_GND` at the connector**, at the
   same point where pin 6 lands — *not* to the analog pour, and not via the
   backing plate unless that plate's material and bonding are specified.
   `MECH-BACKPLATE` is currently "TBD - aluminium or ply, open" `[repo]
   bom.csv`, and **that open row silently decides the shield topology.**
3. Both ends, to the local star at each end, is then correct: there is only one
   earth in the system (the rack), so there is no mains-frequency loop to fear,
   and a both-ends shield gives the 2 MHz common-mode current a low-impedance
   path that `DIG_GND` otherwise has to carry.
4. **Add a common-mode choke or a clamp-on ferrite at the module end.** Not in
   the BOM. ~$0.50. It is the textbook part for a cable carrying a switching
   load and 2 MHz logic out of a precision analog box, and `0004` itself says
   the module "has two filtering jobs, not one" and then admits the second one
   "is not done at all" `[repo] 0004`. A common-mode choke on the umbilical is
   the component that does it.

**Unretrofittable:** item 2. Item 1, 3 and 4 are all at the module.

---

## NODE `J-UMB` pins 3 and 6 — `+12V` / `PWR_GND`

### Static IR drop, corrected for stranded

`[calc]`, using R_loop = 0.60 Ω (worst legal stranded patch + contacts):

| State | Umbilical current `[repo] 0005` | Cable drop, repo's 0.168 Ω | Cable drop, corrected |
|---|---|---|---|
| Quiescent | 212 mA | 71 mV | **127 mV** |
| Typical play | 359 mA | 121 mV | **215 mV** |
| Typical + WiFi | 414 mA | 139 mV | **248 mV** |
| Clamp-legal worst | 579 mA | 195 mV | **347 mV** |
| Load-switch limit | 1000 mA | 336 mV | **600 mV** |

ADR 0005's rail budget rebuilt `[calc]`:

```
Repo:      12.00 − 0.122 (cable) − 0.400 (Schottky) − 0.060 = 11.42 V   [repo] 0005
Corrected: 12.00 − 0.215 (cable) − 0.400 (Schottky)
                 − 0.029 (R-ILIM 50 mΩ + FET R_DS(on) ~30 mΩ at 359 mA)
                 − 0.060 (bead + entry)                     = 11.30 V
```

**Not a problem.** The R-78E5.0 needs > 6 V in `[repo] 0004`, so there is 5.3 V
of headroom. The +12 V rail is the one thing in this cable with margin to spare.
Record the corrected number anyway, because ADR 0005 presents 11.4 V as if it
were tight.

### Dynamic drop from LED switching

`[calc]`, ADR 0014's "realistic use — single hue at moderate brightness",
0.13 A average across both strips, PWM at ~2 kHz `[repo] 0014`, peak-when-on
0.34 A at ~38 % duty:

```
Fundamental of a 0→0.34 A square at duty d:
  a1 = (2 × 0.34/π) · sin(πd) = 0.2165 × sin(68°) = 0.203 A peak at 2 kHz

Current divider at 2 kHz between C-STRIP-BULK and the cable:
  Local branch : C-STRIP-BULK 470 µF → 1/(2π·2000·470e-6) = 0.169 Ω
                 + ESR ~0.2 Ω  [from memory]   ≈ 0.37 Ω
                 + LED loom 420 mm, 24 AWG, loop = 0.070 Ω → 0.44 Ω
  Source branch: LED loom 0.070 + cable 0.60 + C-BULK-RAIL 100 µF (0.80 Ω)
                 + FET/diode ~0.10                             ≈ 1.57 Ω

  Fraction reaching the umbilical = 0.44 / (0.44 + 1.57) = 0.219
  Cable AC current at 2 kHz = 0.203 × 0.219 = 44 mA
  Rail ripple at the instrument = 44 mA × 0.60 Ω = 27 mV pk at 2 kHz
```

**27 mV of 2 kHz ripple on the instrument's +12 V node.** What it reaches:

```
REF5050 line regulation ~5 ppm/V [from memory]:
  27 mV × 5 ppm/V = 0.14 ppm of 5 V = 0.7 µV on the sensor excitation.
  Ratiometric, so it divides out. Zero.

OPA2197 PSRR at 2 kHz ~90 dB (ADR 0004's own figure) [repo] 0004:
  27 mV × 10^(−90/20) = 0.85 µV at the breath buffer output.
  × in-amp 2.161 = 1.8 µV at the jack = 0.002 % of a 153 µV LSB. Zero.

Buck input: 27 mV on an 11.3 V rail, regulated out. Zero.
```

**The dynamic drop is a non-event.** Say so plainly — it is one of the few
things in this subsystem that needs no work.

### The input-LC stability question, with the cable included

`carrier.md §1` closes its Middlebrook check "for the instrument end only" and
`power-entry.md` leaves "damping the input LC … with 2 m of cable and ~2 mF at
the far end" open `[repo]`. **The cable helps** `[calc]`:

```
carrier.md §1: L = 22 µH, C = 100 µF → f0 = 3.39 kHz, Z0 = 0.469 Ω,
               ESR 0.5–1 Ω → Q ≈ 0.5–0.9, peak |Z_out| ≈ 0.42 Ω   [repo]

Adding the source impedance the cable presents at 3.39 kHz:
  R_cable 0.60 Ω  +  jωL_cable (500 nH/m × 2 m = 1 µH → j0.021 Ω)
  in series with C-BULK-RAIL 100 µF (−j0.47 Ω)
  |Z_src| = |0.60 − j0.45| = 0.75 Ω

0.60 Ω of pure series resistance is ADDED damping. Q falls, the peak falls.

Buck's negative input resistance at typical play:
  1.13 W out ÷ 0.90 = 1.26 W in at 11.3 V → R_neg = −V²/P = −101 Ω  [repo] 0005
Middlebrook margin: 101 / 0.75 = 135× (42 dB)
```

**Stable, with the cable, by 42 dB.** The `power-entry.md` open item can be
closed on paper, subject to the caveat `carrier.md` already states in bold:
`C-BUCK-IN` must be an **electrolytic with real ESR**. Substituting a low-ESR
ceramic removes the damping term and this paragraph stops being true. That
warning is currently on `carrier.md` only; it belongs in the `C-BUCK-IN` BOM
row, which says "100uF 25V electrolytic" but does not say why `[repo] bom.csv`.

### `U-LOADSW` versus `LED-SIDE` — finding #5

`power-entry.md` sets `R-ILIM` = 50 mΩ for a **1.0 A** limit, on an **`-1`
(latching)** part `[repo]`. ADR 0005's load table gives **~1522 mA** for "clamp
fails, strips latched full white" `[repo]`.

```
[calc]  1522 mA vs a 1.0 A latching limit → the LT1641-1 latches off.
        Recovery requires cycling SW-POWER at the module, in the rack,
        across the room, mid-performance.
```

ADR 0014 says `[repo] 0014`:

> "**The module's current-limited load switch** (ADR 0005) replaces a slow,
> self-heating, thermally-hysteretic protection device with a fast fixed limit
> that does not run away."
> "**The firmware clamp is a comfort feature against the electrical failure**,
> and a real one against the thermal failure."

**Both sentences are wrong about what happens.** A `-1` load switch does not
*bound* the current; it *removes* it and stays removed. The firmware lighting
clamp is therefore the only thing standing between a display bug and the
instrument going dark. That is not a comfort feature; it is a single point of
failure for uptime, implemented in software, on the board whose firmware is
being iterated.

It is also the one thing keeping the cable inside its contact rating `[calc]`:

```
etherCON contact rating: 1.5 A (Neutrik)  [web]
Generic RJ45 at 50 °C:   1.0 A            [web]
Clamp-off worst case:    1.522 A on ONE conductor (pin 3), all of it

1522 / 1500 = 101 % of Neutrik's rating
1522 / 1000 = 152 % of the generic 50 °C figure
```

ADR 0004 rejected M12 X-coded on exactly this test — *"8-contact X-code sits at
the 0.5 A end of the M12 rating range. Against an instrument drawing ~400 mA
that is 80 % of rating, on a figure that has already moved twice"* `[repo]`.
**Applied consistently, etherCON at the clamp-off case is 101 % of rating.** The
comparison table was built on the typical figure for one connector and never
re-run against ADR 0005's own worst case for the chosen one.

Thermally the cable itself is fine `[calc]` — `I²R` = 1.522² × 0.28 = 0.65 W over
2 m = 0.32 W/m in one conductor; for a 5.5 mm OD jacket, surface 0.017 m²/m at
h ≈ 8–10 W/m²K, ΔT ≈ 2 K. **The conductor is not the limit; the contact is**,
and the load switch is what protects it.

**Recommendation.** Keep the 1.0 A limit — it is the right number and it is what
makes the connector legal. Then:
- Change ADR 0014's language: the lighting clamp is **required for uptime**, not
  a comfort feature, and the failure it prevents is "the instrument goes dark and
  cannot be restarted from the player's position".
- Add a **second, hardware** bound so the firmware clamp is not alone. The
  cheapest is a series resistor in each strip's 12 V feed sized to cap
  full-white current — e.g. 1 Ω in each `J-LED` 12 V leg costs 0.5 V at 0.5 A
  (WS2815 tolerates it; the internal regulator drops from 12 V anyway) and caps
  a dead-short-to-full-white at ~0.5 A per strip `[calc]`, `12 V / (1 Ω + strip)`.
  Two 1 Ω 1 W resistors. This needs checking against WS2815 minimum supply
  before adopting `[from memory]`.
- Put the recovery procedure in the ROADMAP: **latched-off is a designed state
  and the player must know what it looks like** (panel LED out) and what to do.

---

## NODE `J-UMB` pins 1 and 2 — `BREATH` / `AGND`: the good news, quantified

I was asked to test whether a 0–5 V analog signal belongs in the same sheath as
a 2 MHz SPI clock. **It does, with about 80 dB to spare**, and the reasoning in
ADR 0003 is correct. Here is the arithmetic, because "it's fine" is not a
review finding.

### Crosstalk from `SCLK` (pins 7,8) into `BREATH` (pins 1,2)

Both aggressor and victim are differential on their own pairs, which is exactly
what NEXT/FEXT measure `[calc]`:

```
NEXT (pair-to-pair, 2 m, 2 MHz) = 82.7 dB   → derived above, from [web] 35.3 dB
Coupled: 1.49 V rms × 7.3e-5 = 109 µV rms at 2 MHz

FEXT: Cat5e ELFEXT ≥ 23.8 dB at 100 MHz/100 m [from memory]
      At 2 MHz: 23.8 + 20·log10(100/2) = 57.8 dB
      At 2 m (FEXT amplitude ∝ length): +34 dB → 91.8 dB → 39 µV rms

Receiver: 482 Hz single pole, at the module, AHEAD of the in-amp [repo]
  Attenuation at 2 MHz = 20·log10(2e6/482) = 72.4 dB → 2.4e-4
  109 µV × 2.4e-4 = 26 nV differential at the in-amp input
  × G 2.161 = 57 nV at the breath jack
```

**In the units asked for** `[calc]`:

```
As a fraction of the 9.94 V jack span:          5.7 ppb
Against the project's 153 µV LSB reference:     0.00037 LSB
In breath counts: ZERO — the instrument's MCP3202 reads BREATH *before*
  the umbilical [repo] 0004, so cable crosstalk contributes no counts at all.
In cents, if breath is patched to a 1 V/oct input (1 cent = 833 µV):
  57 nV = 0.00007 cents
```

Three design choices earn this and all three should be protected in any rework:

1. **The 482 Hz filter is at the module, ahead of the in-amp.** 72 dB of the
   margin comes from that one placement. `breath-receive-stage.md` is right that
   a filter after the in-amp cannot stop RF rectification `[repo]`, and
   `carrier.md §2` is right to refuse a cap at `R-SER-BREATH-INST`.
2. **`AGND` carries no power current.** Verified below.
3. **The differential-dominant filter** (`C_diff` 15 nF vs `C_cm` 1.5 nF) divides
   any common-mode-to-differential conversion by 10 `[repo]`.

### The power pair into the analog pair — the mechanism is conducted, not coupled

`[calc]`, at 2 kHz:

```
NEXT(2 kHz, 100 m) = 35.3 − 15·log10(0.002/100) = 35.3 + 70.5 = 105.8 dB
λ/4 at 2 kHz = (2e8/2000)/4 = 25 km. 2 m/25 km → −82 dB of length correction.
NEXT(2 m, 2 kHz) ≈ 188 dB.
```

**188 dB.** The twist annihilates the radiated path. ADR 0003 is right that the
entire mechanism is conducted — the IR drop in the shared return — and right
that giving the analog channel its own non-current-carrying return conductor
restores the Eurorack patch-cable condition. That argument survives every number
in this review.

### What the IR drop actually does to `AGND`

`AGND` is not a ground. It is the in-amp's `IN−`, terminating at two 1 MΩ bias
resistors `[repo] breath-receive-stage.md`. It ties to `PWR_GND` at exactly one
point, at the instrument's umbilical connector `[repo] carrier.md §2`. So when
`PWR_GND` at the instrument rises above the module's star by `I × R(pin 6)`,
**both** the breath buffer's output **and** `AGND` rise together. It is pure
common mode.

`[calc]`, DC / animation rate, LED step from dark to "single hue full" (0.34 A
across both strips `[repo] 0014`):

```
CM shift on AGND = 0.34 A × 0.30 Ω = 102 mV

DC CMRR of the receive stage:
  INA828 at G = 2.185: ≥100 dB [from memory]
  Source imbalance: gigaohm inputs → negligible [repo] 0003
  The 1 MΩ bias pair at 1 % against 11 kΩ legs:
     ratio error = (11k/1M) × 0.01 = 1.1e-4 → 79 dB     ← dominant
  Take 79 dB → 1.12e-4

102 mV × 1.12e-4 = 11.4 µV differential
× G 2.161 = 25 µV at the breath jack
  = 0.00025 % of 9.94 V
  = 0.030 cents, if breath is patched to a 1 V/oct input
  = 0.004 counts referred back to the instrument's 1594-count playable span
```

`[calc]`, at the 2 kHz PWM rate, where the common-mode caps set CMRR:

```
Umbilical AC at 2 kHz (derived above): 44 mA
CM on AGND = 44 mA × 0.30 Ω = 13.2 mV

CMRR from C_cm mismatch at 2 kHz, R_leg = 11 kΩ, C_cm = 1.5 nF:
  X_c(2 kHz) = 1/(2π·2000·1.5e-9) = 53.05 kΩ
  Leg transfer = Z_c/(R+Z_c): |·| = 53.05/√(11²+53.05²) = 0.9791, ∠ = +11.72°
  With 1 % spread: |·| = 0.9789, ∠ = +11.83°
  Vector difference = √((2e-4)² + (0.979 × 1.92e-3)²) = 1.89e-3 → 54.5 dB
  Divided by the C_diff/C_cm ratio of 10 [repo] → ~74 dB

13.2 mV × 10^(−74/20) = 2.6 µV → × 2.161 = 5.7 µV at the jack
  ×4 at maximum panel GAIN = 23 µV.  Inaudible by any measure.
```

**Finding #16, the one thing to fix here.** `bom.csv` row `C-FILT-BREATH` reads
"15nF C0G (diff) + 1.5nF C0G (cm x2)" with **no tolerance** `[repo]`, while
`breath-receive-stage.md` says "±1 % is needed to clear 60" `[repo]`. Default
C0G stock is ±5 %:

```
[calc]  ±5 % spread = 10 % → 1.89e-2 before the ratio → 34.5 dB
        ÷10 for C_diff dominance → 54.5 dB
        13.2 mV × 2.0e-3 = 26 µV → × 2.161 = 57 µV, ×4 at max GAIN = 228 µV
        = 0.27 cents of 2 kHz warble if breath is patched to 1 V/oct.
```

Still fine — the 10:1 `C_diff`/`C_cm` ratio is carrying the design and deserves
the credit — but **put "±1 %" in the BOM row**. It costs pennies, and the
symptom of getting it wrong is a 2 kHz buzz that appears only when the lights
are on.

### Finding #15: ADR 0014's loop-gain figure is ~200× pessimistic

ADR 0014 says `[repo] 0014`:

> "**Through the CV path it is negative feedback.** More breath → brighter LEDs
> → `AGND` rises → the CV reads lower. Loop gain is around 0.004, so the effect
> is **0.4 % of gain compression**."

`[calc]`: 0.4 % of a 9.94 V span is 40 mV. My figure above is **25 µV**. The
discrepancy is 64 dB, which is the in-amp's CMRR — ADR 0014 appears to have
treated the `AGND` rise as a **direct** subtraction rather than a common-mode
one. But rejecting that shift is the entire reason ADR 0003 bought an
instrumentation amplifier instead of a difference amp `[repo] 0003`.

The correction matters because ADR 0014 uses the figure to justify a firmware
change ("drive the LEDs from the post-gate, slew-limited breath value"). **That
change is still right** — but for the *other* loop, the positive-feedback one
through the ADC's shared reference, which is inside the instrument and has
nothing to do with the cable. Two different loops, one arithmetic error, and the
right fix adopted for the wrong reason. Rank Low because the outcome is correct.

### Is single-ended-with-sense-return the right choice at all?

Yes. Honestly costed against both alternatives:

**Alternative 1 — differential drive on pins 1,2.** ADR 0003 prices it at "about
6 dB against induced noise" `[repo]`. That is right, and there is a second 6 dB
from the doubled swing, so ~12 dB total. Cost `[calc]`: the `U-BUF` OPA2197's
two halves are both spoken for (½ reference buffer, ½ breath buffer `[repo]
bom.csv`), so a differential driver needs a **second dual package** (~$4), plus
two matched resistors, plus board area on the carrier, which is already in a
width crunch at 45 mm in 49 mm of internal body `[repo] carrier.md`. **Buying
12 dB on a channel that already has 80 dB of margin, at the cost of a part on
the board that cannot be reopened.** Declined, and ADR 0003 is right.

**Alternative 2 — digitise breath at the instrument.** This is the interesting
one, because it appears to be *negative* cost:

```
DELETE at the module: INA828 (~$9), R-SER-BREATH 10k 0.1% ×2, R-GAIN-INAMP
  42.2k 0.1%, R-BIAS-INAMP 1M ×2, C-FILT-BREATH ×3, C-OUT-BREATH 330 nF film,
  D-CLAMP-BREATH BAV99 ×2, TRIM-BREATH-ZERO + R-TRIM-RANGE
DELETE at the instrument: R-SER-BREATH-INST ×2 (1206), D-TVS-BREATH ×2
  ≈ 16 components, ≈ $20, and the project's single hardest analog problem.

ADD: nothing. The MCP3202 ALREADY digitises breath, for note gating and for
  the lights [repo] 0014. Breath becomes DAC8568 channel 7 of 8.

FREES pins 1,2 → every digital signal gets its own return, which is what
  ADR 0004's prose claims the design already has. Finding #1 evaporates.

Loop budget [calc]: 7 × 32 bits @ 2 MHz = 112 µs, + ADC 26.7 µs = 138.7 µs
  of 250 µs = 55 %. ADR 0004 records seven channels were budgeted before the
  ambient-zero was deleted [repo], so this was already carried.

Resolution [calc]: the MCP3202 is the limit, not the DAC.
  12 bits over 2.82 V = 688 µV → × 3.52 to the jack = 2.4 mV = 0.024 % of span.
  ~1594 counts of playable span. Adequate for a breath channel.

Latency: +1 loop period = 250 µs on a 5 ms budget = 5 %. [repo] latency-budget
```

**And it must still be declined, for one reason that is worth more than all of
that.** Breath being analog is the **only fail-silent path in the system**:

```
Pull the umbilical mid-note, today:
  - PITCH, MOD 1–4: the DAC8568 holds its last word. The rack drones.
    The frame watchdog that used to catch this was DELETED and the coverage
    is gone — "pull the umbilical mid-note and the rack holds that note until
    you flip the module's toggle."  [repo] digital-and-supervision.md
  - BREATH: the in-amp's inputs lose their drive. R4/R5 (2 × 1 MΩ) hold both
    inputs at module analog ground. Vout = V_REF ≈ 0 V. The VCA closes and
    the drone is SILENT.  [repo] breath-receive-stage.md
```

Digitising breath would put the VCA channel into the same latched register as
everything else and **turn a silent failure into a loud one**, on the everyday
failure the module page has already conceded is uncovered. `0004` states this
argument in fragments across three sections; it is the load-bearing one and it
should be stated once, in one place, as *the* reason breath is analog.

**Verdict: single-ended with a sense return is correct.** But the decision has a
cost the repo has never acknowledged — **it consumes the conductor that the
digital side needed** — and finding #1 is that bill arriving.

---

## NODE `J-CHAIN` — the key chain loom

**This is the best-engineered cable in the system** and the arithmetic supports
the decision that made it so. Then there are two things wrong with it that are
not about signal integrity at all.

### Coupling from the LED channel into `SCK` and `SH/LD` — quantified

Geometry: the chain ribbon shares a side channel with a WS2815 strip and the LED
loom `[repo] 0009, 0014`. Assume 5 mm separation `[from memory]` — `0009` does
not dimension the channel.

**Inductive, from the LED 12 V/GND loop** `[calc]`:

```
Aggressor: 0.5 A per strip, ~2 kHz PWM, internal MOSFET edges ~100 ns
  [from memory] → dI/dt = 0.5 A / 100 ns = 5e6 A/s
LED loom pair at 5 mm spacing:
  B at 5 mm = (µ0·I/2π)(1/d1 − 1/d2) = 2e-7 × 0.5 × (1/0.005 − 1/0.010)
            = 1e-5 T
Victim loop: SCK on pin 2, GND on pins 1 and 3 at 1.27 mm each side.
  Return splits both ways → effective loop 0.635 mm × 265 mm = 168 mm²
  Φ = 1.68e-4 m² × 1e-5 T = 1.68e-9 Wb  →  M = Φ/I = 3.36 nH
V_induced = 3.36 nH × 5e6 A/s = 17 mV
```

**Capacitive, from the WS2815 data line** `[calc]`:

```
C_mutual, two wires r = 0.4 mm at d = 5 mm over 265 mm:
  C = π·ε0·L/ln(d/r) = π × 8.854e-12 × 0.265 / ln(12.5) = 2.9 pF
  With the grounded aluminium plate above [repo] cluster-boards.md §5: call it 2 pF.
Aggressor: 5 V from the 74AHCT125 through R-LED-SER 330 Ω, edge ~20 ns
Victim SCK driven from ESP32 ~40 Ω + R-CHAIN-SER 100 Ω = 140 Ω
V_peak = C · (dV/dt) · R_src = 2e-12 × (5/20e-9) × 140 = 70 mV
```

**Total worst case ≈ 87 mV, against a 74HC165 `V_IL(max)` of 0.3 × 3.3 = 990 mV
`[from memory]` — a margin of 11:1.**

Compare against ADR 0001's own corrected figure for an **unfiltered, ungrounded**
loom conductor: **1.36 V** `[repo] 0001` — which exceeds 990 mV and is a
failure. **So the alternating-ground ribbon converts a failure into an 11:1
margin, and ADR 0001's "highest-value SI fix" claim is arithmetically correct.**
Credit it; it is the one decision in this subsystem that needs no change.

### Finding #14: what a `SH/LD` glitch actually costs

The repo's stated consequence `[repo] 0001, carrier.md §3, bom.csv`:

> "a glitch on `SH/LD` does not cost one wrong note, it reloads all four
> registers mid-shift and **corrupts the whole 32-bit word**"

**That is not what happens.** A 74HC165's `SH/LD` load is level-sensitive and
asynchronous, so a mid-shift low pulse does reload — but what comes out is a
**splice of two snapshots taken ≤32 µs apart** `[calc]`, 32 bits at 1 MHz
`[repo] carrier.md §4`. A KS-33 press takes milliseconds. So in 32 µs at most
one key changes state, and every bit in the spliced word is a *valid* reading of
its key at one of two instants 32 µs apart. **The word is almost always
correct.**

The consequence is different and more interesting:

```
Glitch on SCK   → one extra clock → all 32 bits shift by one position
                → the 8-bit marker pattern shifts too → CAUGHT.  [repo] cluster §4
Glitch on SH/LD → splice of two snapshots
                → the marker is HARD-WIRED and identical in both snapshots
                → the marker passes → NOT CAUGHT, and usually harmless.
Glitch on QH    → one wrong bit → one spurious key, self-clearing next scan.
```

So `SH/LD` is the loom's **least** consequential signal, not its most, and the
marker pattern — the chain's only integrity check — is blind to exactly the
corruption the ground-per-signal ribbon was bought to prevent. **The decision is
still right** (11:1 beats 0.7:1, the grounds are free, and a body that bonds
shut is the wrong place to be clever). But the justification in ADR 0001,
`carrier.md §3` and the `WIRE-LOOM` BOM note is wrong and should be corrected,
because someone will eventually use it to justify spending money elsewhere.

### Finding #6: eight identical connectors, four identical cables

`bom.csv` `J-CHAIN`: qty **8**, "BOXED AND KEYED because a reversed chain
connector puts 3V3 into QH. **Same pinout at all eight**" `[repo]`.
`cluster-boards.md §3`: "Boxed and keyed at all eight positions" `[repo]`.

The keying stops a **180° reversal**. It does not stop:

1. **Plugging a ribbon between the wrong two boards.** Four identical assemblies,
   eight identical sockets, one hand-built loom, inside a body that bonds shut.
2. **Swapping `IN` and `OUT` on the same board.** This is the damaging one.
   `cluster-boards.md §3` is explicit that pin 8 carries a *different net on each
   side of the board* `[repo]`: `IN` pin 8 is this board's `QH` **output**; `OUT`
   pin 8 is the next board's `QH`, an **input** to this board.

```
[calc]  IN/OUT swapped on one board:
        this board's QH output  ←→  the previous board's QH output
        Two 74HC165 totem-pole outputs, one high, one low, through 0 Ω.
        74HC output short-circuit current at 3.3 V: ~25 mA  [from memory]
        Abs-max DC output current per pin for 74HC: ±25 mA  [from memory]
        → sustained operation AT the absolute maximum rating, dissipating
          3.3 V × 25 mA = 83 mW in each output stage, indefinitely.
```

No fuse, no diagnostic, no symptom except heat and a garbage chain read.

**Fix, on boards that do not yet exist:**

- **A 100 Ω series resistor in `QH` at each cluster board's output.** Four
  0805s, ~$0.04 total. `[calc]` contention becomes
  `3.3 / (100 + 100 + 2×50) = 11 mA` — inside rating. It also fixes a real
  omission: `carrier.md §3` puts `R-CHAIN-SER` on `SCK`, `SH/LD` and `SER`
  — three of the four chain signals — and **`QH` is the one left undamped**,
  driven by an HC output with ~15 ns edges into 265 mm+ of ribbon. Same part,
  same value, same argument. It is not in the BOM at all (`R-CHAIN-SER` is
  proposed on `carrier.md` and absent from `bom.csv` `[repo]`).
- **Fit `LK-SER` and `R-SER-TERM`** — both currently `open` in the BOM `[repo]`
  — and **make the end-to-end shift test an M8 acceptance criterion.**
  `cluster-boards.md §3` describes exactly this and recommends "fitting it and
  deciding later" `[repo]`. Deciding later is the wrong call: it is the *only*
  thing that can distinguish a mis-cabled chain from a broken one, and M8 is the
  last moment it can be run. Cost: one 10 kΩ and four 3-pad links.

### `F-CHAIN` (3V3 down the body) — the fuse protects the wrong fault

`carrier.md §3` proposes a 100 mA polyfuse on the 3V3 conductor because "a short
on it browns out the dev board's LDO and takes the instrument down with no
diagnosis" `[repo]`.

```
[calc]  3V3 load: 21 × 2.2 kΩ pull-ups, 18 closed = 25.8 mA  [repo] carrier.md §3
        plus 4 × 74HC165 quiescent (µA). A 100 mA polyfuse holds it. Correct.

The likely faults, ranked:
  (a) 3V3 chafes against the grounded aluminium plate → short to GND.
      COVERED by the polyfuse. And likely: cluster-boards.md §5 warns the plate
      "is also a short waiting to happen" [repo].
  (b) 3V3 chafes against the LED loom's 12 V, 5 mm away in the same channel.
      NOT COVERED. A polyfuse limits current; it does not limit voltage.
      12 V reaches the LDO output, all four 74HC165 VCC pins, and every
      pull-up. Everything on the 3V3 net dies before the polyfuse warms up.
```

**Fit `F-CHAIN` — it covers the likelier fault and it is 2 mm of board — and add
a 3.6 V TVS or a 5.1 V zener at the carrier's 3V3 pad**, which is the part that
covers fault (b). Neither is in the BOM. Both are unretrofittable.

### Chain loom length — a number that is used and is wrong

`carrier.md §4` justifies "SPI3 at 1 MHz, and not much more" with "the chain
crosses four connectors and **~265 mm of loom**, and HC's slow edges are what
keep that a lumped load" `[repo]`.

265 mm is the carrier-to-nearest-cluster distance. The chain is
`right_thumb → right_hand → left_thumb → left_hand` and
`cluster-boards.md` shows it crossing the 38 mm body thickness **three times**
`[repo]`, in a 457 mm body. `[calc]` realistic total ribbon: 4 hops × 150–250 mm
≈ **600–1000 mm**, not 265 mm.

Does it matter? `[calc]`:

```
T_d(1 m of ribbon) = 1/2e8 = 5 ns.  HC165 edges ~15–25 ns  [from memory]
Lumped requires t_r > 6·T_d = 30 ns. At 1 m, t_r/T_d = 3 → NOT lumped.

But the load still closes easily:
  C = 60 pF/m × 1 m + 4 × 5 pF inputs + 8 connectors ≈ 85 pF
  R = ESP32 ~40 Ω + R-CHAIN-SER 100 Ω = 140 Ω
  τ = 140 × 85 pF = 12 ns, against a 500 ns half-period at 1 MHz = 2.4 %
```

**The conclusion survives; the stated reason does not.** Rank Low, but fix the
number, because `cluster-boards.md` separately proposes reordering the chain to
`RT → RH → LH → LT` to save one body crossing `[repo]` — and that proposal is
evaluated against skew, which ADR 0001 itself says is worth "a few percent of
hold margin". **The real argument for the reorder is loom length and one fewer
hand-terminated crossing inside a bonded body, and it is stronger than the
skew argument that is currently carrying it.**

### The two spare conductors

`J-CHAIN` pins 11 and 12 are spares, per ADR 0009's "run two spare conductors in
every internal loom" `[repo]`. The 2×6 IDC terminates all twelve, so they are
genuinely present — good. But `cluster-boards.md §3`'s connector drawing shows
pins 11 and 12 going nowhere on the boards `[repo]`.

**A spare conductor that reaches no pad is not a spare.** Bring 11 and 12 out to
two through-hole pads on every cluster board and on the carrier. Cost: zero
(they are already connector pins). Without it, ADR 0009's rule is satisfied in
the loom and defeated at both ends. Also note pin 11 sits next to 3V3 (pin 10)
with no ground between, so if a spare is ever used for a signal it has no return
— acceptable, but worth a silkscreen note.

---

## NODE `J-LED-L` / `J-LED-R` — the LED looms

### Finding #17: `C-STRIP-BULK` is in the right place. I checked.

ADR 0014 is emphatic that "bulk capacitance belongs where the current swings,
not at the module end of a **14-inch cable**" `[repo] 0014`, and then
`carrier.md §5` puts `C-STRIP-BULK` on the carrier `[repo]` — which is
**420 mm = 16.5 inches** of loom from the strip. That reads like the same
mistake reproduced inside the instrument. **It is not** `[calc]`:

```
At the WS2815's ~2 kHz PWM rate:
  LED loom, 420 mm of 24 AWG, loop:   R = 2 × 0.084 Ω/m × 0.42 = 0.070 Ω
                                      ωL (0.35 µH) = 0.0044 Ω
                                      |Z| = 0.070 Ω
  C-STRIP-BULK 470 µF:                1/(2π·2000·470e-6) = 0.169 Ω
                                      + ESR ~0.2 Ω [from memory] = 0.37 Ω

The LOOM is 0.070 Ω; the CAP is 0.37 Ω. The loom is 5× LOWER impedance
than the capacitor it feeds. It is not the limiting element.
```

The ADR 0004 objection does not transfer, because the module-end case had a
**ferrite bead** in the path (a wire at 2 kHz, but also no help) and 2 m of
cable at 0.60 Ω — nine times the loom's impedance. Keep `C-STRIP-BULK` on the
carrier; it is also the only place a 470–1000 µF radial can physically live
`[repo] carrier.md §5, 0009`.

**At MHz edge rates it is a different story** — `[calc]` at 1.6 MHz (the
corner of a 100 ns WS2815 switching edge), `ωL` of the 420 mm loom is 3.5 Ω and
the cap's ESL dominates, so the carrier-mounted bulk does nothing. That energy
is handled by the strip's own onboard decoupling `[from memory]` and is what
couples into the key ribbon — which I costed at 87 mV against 990 mV above.
**Both effects are covered. Nobody needs to look at this again.**

### Finding #10: the LED looms are the least specified cable in the system

| Question | Answer in the repo |
|---|---|
| BOM row? | **None.** `J-LED-L/-R` is "proposed" on `carrier.md` only `[repo]` |
| Connector type? | "4-way each" `[repo] carrier.md` |
| Keyed? | **Not stated** |
| Wire gauge? | **Not stated.** `WIRE-LOOM` package is "n/a" `[repo] bom.csv` |
| Conductor count? | 6 or 8 — depends on whether `BI` needs driving, still open `[repo]` |
| Length? | "~420 mm" `[repo] carrier.md §5` |

**Gauge matters here and nowhere else in the internal looms** `[calc]`:

```
Current per strip, full white: 1.01 A / 2 = 0.505 A  [repo] 0014
If built from the same 28 AWG ribbon as J-CHAIN (0.213 Ω/m):
   0.213 × 0.42 × 2 = 0.179 Ω loop → 90 mV drop, 45 mW per conductor
If 30 AWG (0.34 Ω/m):  0.29 Ω loop → 145 mV, 73 mW per conductor
If 24 AWG (0.084 Ω/m): 0.070 Ω loop → 35 mV, 18 mW per conductor
```

Survivable at any of them electrically, but a 30 AWG conductor carrying 0.5 A in
a sealed 20 mm channel running 10–20 K above ambient `[repo] 0009` is a
thermal-and-vibration item nobody has looked at. **Specify ≥24 AWG for the
`12 V` and `GND` conductors, explicitly and separately from `WIRE-LOOM`'s
ribbon.** `WIRE-LOOM` is one qty-1 row covering "key chain, LED power and data,
UART, power" `[repo]` — four physically different cables with four different
requirements under one part number, which is how a 30 AWG ribbon ends up
carrying half an amp.

**Reversal** `[calc]`, a 4-way at `12V / GND / DI / BI` plugged backwards:

```
12 V lands on BI → through R-LED-SER 330 Ω into the 74AHCT125's output clamp:
   (12 − 5 − 0.7)/330 = 19.1 mA
   74AHCT125 abs-max output clamp current: ±20 mA  [from memory]
   → 96 % of absolute maximum, and the current is injected INTO the 5 V rail,
     which is buck A, shared with both dev boards and the 8×8 matrix.
DI lands on GND, GND lands on DI, 12 V lands on... the strip's GND rail
   → reverse polarity across 50 WS2815 packages. Strip destroyed.
```

**Use a polarised connector** (JST-XH or PH, or a 2×3 boxed/keyed IDC with the
same alternating-ground discipline as `J-CHAIN`). It costs the same as the
unkeyed header and the project has already made this decision correctly once.

**L/R swap:** `J-LED-L` and `J-LED-R` are identical 4-ways with identical
pinouts, so they can be interchanged. Electrically harmless — ADR 0014 chose
topology **B**, two independent data lines, precisely so the sides are
independent `[repo]` — but the sides will be mirrored and it will be blamed on
firmware. **Different connector colours or a 3-way/4-way asymmetry costs
nothing.** Rank: Low.

**Pinout order is right, by luck or by judgement:** `12V, GND, DI, BI` puts GND
between the 12 V conductor and the data line. `DI` and `BI` are adjacent with no
ground between them, which is harmless because `BI` carries the same data
`[web]`. Credit it.

### The `BI` question, settled enough to act on

`carrier.md §5` and ADR 0014 both leave open whether the first pixel's `BI` must
be driven, and the answer changes the gate count and the conductor count
`[repo]`. `[web]`: the `BIN` pin receives data and the IC falls back to it only
if `DIN` fails; community practice is to **either drive it or tie it to ground
at the head of the run**, with floating "at the risk of noise causing issues".

**`bom.csv` has already decided this, and `carrier.md` has not caught up.**
`R-LED-SER` is qty **4**, 330 Ω, with the note: "FOUR not two: the WS2815's
BACKUP data line … was connected to nothing - the level shifter's two spare
gates are exactly what it needs" `[repo] bom.csv`. So: **four gates used, none
spare, 8-conductor LED loom.** `carrier.md`'s component table still lists
`R-LED-SER` as "proposed ×2–4" and the `U-LVLSHIFT` row still cites the BOM's
"Two spare gates" `[repo]` — that phrase is no longer in the BOM row. Update
`carrier.md §5` and the *Still open* list to match.

### The WS2815 threshold question, answerable now

ADR 0014 and `carrier.md §5` both flag "if its logic threshold is referenced to
12 V rather than an internal rail, 5 V shifting will not be enough and the part
choice needs revisiting" `[repo]`. `[web]`: the WS2815 regulates 12 V down to an
internal ~5 V rail and `VIH` is **0.7 × that internal rail ≈ 3.5 V**, with an
absolute-maximum input around 5.3 V.

```
[calc]  74AHCT125 on 5 V drives V_OH ≈ 4.4 V at light load  [from memory]
        Through R-LED-SER 330 Ω into a high-Z WS2815 input: ~4.4 V at the pin
        Against VIH 3.5 V: 0.9 V of margin. Against abs-max 5.3 V: safe.
```

**The 74AHCT125 is the right part and this open item can close** — subject to
one datasheet reading, which is what the item asks for. `[web]` is a search
summary, not the datasheet; the phrase to confirm is the `VIH` row and its
reference rail. Recorded here so that the *"if it needs 12 V logic, §5 is
rebuilt"* contingency can stop being carried in two documents.

---

## NODE `J-DISP` — the display loom

9 conductors, 360 mm, sharing a side channel with a WS2815 strip and its
12 V power `[repo] carrier.md §6`.

### The signal integrity is fine and the reasoning is sound

`carrier.md §6` justifies two grounds for four signals — against `J-CHAIN`'s
five grounds for four — on the grounds that everything in it is "framed,
byte-oriented and recoverable by retry" `[repo]`. **That is correct**, and the
arithmetic backs it `[calc]`:

```
UART1 at 921600 baud → bit time 1.085 µs
Coupled disturbance, same geometry as the chain loom: ~87 mV
ESP32 V_IL at 3.3 V ≈ 0.25 × 3.3 = 0.83 V  [from memory]
Margin ≈ 10:1, and a corrupted byte costs one retry.
```

Contrast this with `EN` and `IO0`, which were withdrawn from the loom `[repo]
carrier.md §6` — **those were the two lines where a glitch is unrecoverable, and
removing them is what makes the two-ground loom defensible.** Good decision,
correctly reasoned; no change needed.

### Finding #9: the power conductor is the problem, and it is `TBD`

The loom's first conductor is "5 V (or +12 V — see *Still open*)" `[repo]`. The
display is a T-Display-S3 AMOLED with a 2.4 GHz radio.

```
[calc]  Display board draw: ~150–250 mA average, with WiFi TX bursts to
        ~500 mA for ~200 µs  [from memory — E1 measures this, per ROADMAP]

360 mm loom, 26 AWG (0.133 Ω/m), loop = 2 × 0.133 × 0.36 = 0.096 Ω
  Static drop at 250 mA:  24 mV      — fine
  Burst drop at 500 mA:   48 mV      — fine

Loom inductance, 360 mm pair at ~5 mm spacing: ~0.35 µH
  TX burst step 0 → 0.5 A in ~1 µs:  V = L·dI/dt = 0.35e-6 × 5e5 = 175 mV
  → a 175 mV dip on the display board's 5 V unless local bulk holds it.

Required C-BULK-DISP to hold 500 mA for 200 µs within 100 mV:
   C = I·Δt/ΔV = 0.5 × 200e-6 / 0.1 = 1000 µF
   Within 250 mV: 400 µF.
```

`bom.csv` row `C-BULK-DISP`: part "**TBD**", package "1206 / electrolytic THT",
qty 1, status **open** `[repo]`. **A 1206 ceramic is ~10 µF. The requirement is
400–1000 µF.** Those are not the same component and the row currently permits
either.

This is the same question as `carrier.md`'s *Still open* item "**Where buck B
lives**" `[repo]`, and the two must be answered together:

| Option | Consequence |
|---|---|
| Buck B on the carrier, 5 V up the loom | Needs `C-BULK-DISP` ≈ 470–1000 µF electrolytic on the display board. ADR 0013's reason for two bucks — "so the display board's WiFi bursts are absorbed locally" `[repo] 0005` — is **defeated**: the burst travels 360 mm before it is absorbed |
| Buck B on the display board, 12 V up the loom | Satisfies ADR 0013's actual intent. Costs: 12 V now runs 360 mm adjacent to `U0RXD` in a channel that also carries 12 V LED power. A chafe puts 12 V on an ESP32 console pin |

**Recommendation: buck B on the display board, 12 V up the loom, and put a
ground conductor between the 12 V conductor and the nearest signal.** The loom
has two spares; spending one on a guard ground is the best use available for it.
ADR 0013's reasoning is the deciding input and it points one way.

### Finding #9b: no row, no connector, no keying

`J-DISP` has **no BOM row at all**. It is "proposed — 9-way" on `carrier.md`
`[repo]`. A 9-way single-row 2.54 mm header reversed puts the power conductor on
a spare and `U0TXD` on `IO6`.

**Specify a keyed connector** (JST-XH 9-way, or 2×5 boxed IDC with one pin
blanked — the latter matches `J-CHAIN`'s tooling and keying discipline, gives
the alternating-ground option for free, and lands on 10 conductors where the
loom already wants 9). And **write the pinout down as a pinout**, not as a list
of contents: `carrier.md §6` currently gives an itemised list with no pin
numbers, which is not a specification anyone can build from.

---

## NODE: the internal tail loom (etherCON chassis → `J-UMB` on the carrier)

This cable is not in the BOM, not in `carrier.md`'s loom conductor table (which
explicitly says "**excluding the umbilical**" and then lists the umbilical as
8 conductors `[repo]`), and not in `WIRE-LOOM`'s description. **It is the one
segment where the twisted pairs end**, and it is inside a body that bonds shut.

`0009` puts the etherCON on an internal backing plate, **not** on the carrier
`[repo] 0009, carrier.md` block diagram. So somewhere between 50 and 100 mm of
eight (or nine, with a shield drain) individual wires run parallel from the
chassis connector to the board.

**The electrical cost is small** `[calc]`:

```
80 mm of 8 parallel wires at 2 mm pitch, r = 0.5 mm:
  C_adjacent = π·ε0·0.08/ln(2/0.5) = 1.6 pF
MOSI → CS in the tail, bounded by the divider against CS's 112 pF cable node:
  1.6/(1.6+112) = 1.4 % × 3.3 V = 47 mV
SCLK → BREATH (six conductors apart, ~0.2 pF), into a 1 kΩ source:
  0.2e-12 × 1.65e9 × 1 kΩ = 0.33 mV, then × 2.4e-4 through the 482 Hz filter.
  Zero.
```

**The mechanical cost is not.** Eight hand-soldered joints on a chassis connector
whose latch takes the load every time the instrument moves — and `0004`'s whole
case for etherCON is that "the instrument moves constantly while being played
and the cable flexes at the connector every time" `[repo]`.

### Finding #11: the feedthrough question, costed

ADR 0004 leaves this open and states the cost `[repo] 0004`:

> "Feedthrough (NE8FDP-class) presents a plain RJ45 on the back, so the
> instrument end could take a short patch lead to a jack on the carrier instead
> of eight soldered wires inside a body that cannot be reopened — genuinely
> attractive. **The cost is two more contact interfaces in every signal,
> including the +12 V path and the analog pair.**"

`[calc]`, that stated cost:

```
On +12 V: 2 extra mated interfaces × 20 mΩ × 2 conductors = 80 mΩ  [web]
          At 579 mA (clamp-legal worst): 46 mV more drop on an 11.3 V rail.
          0.4 % of the rail. Against 5.3 V of buck headroom: irrelevant.

On the analog pair: 40 mΩ in series with 1 kΩ (instrument) + 10 kΩ (module)
          = 3.6 ppm of a leg impedance — AND it is in BOTH legs, so it is
          common-mode, which the in-amp rejects by 79 dB. Net: ~0.
```

**The stated cost is 46 mV and approximately zero.** Against it: eight
hand-soldered joints removed from the flexing path inside a body that cannot be
reopened, and a carrier that can be tested with a patch lead before it is
installed.

**Two costs the ADR does not state, and they are real:**
1. A feedthrough creates a **second chance to install a wrong lead** — this time
   *inside* the body, where it is unretrofittable. Mitigate by using a known
   straight-through lead, verifying it at M7, and securing it.
2. The internal RJ45's retention tab is now inside a bonded body. It cannot be
   re-seated. Mitigate with a cable tie or RTV over the latch at M7.

**Recommendation: feedthrough, decided at E13, not at E12/M7.** `carrier.md`'s
*Still open* already says why: the decision "decides whether this board carries
an RJ45 jack footprint (~16 × 14 mm, not in the BOM) or eight wires. ADR 0004
defers it to E12/M7, **which is after E13**" `[repo]`. **That is a genuine
ordering violation of exactly the kind the ROADMAP's own "three ordering rules a
design review found violated" section exists to catch** `[repo] ROADMAP`. Add it
as a fourth.

---

## `CABLE-UMB` and `J-UMBILICAL` — the consumable and the thing it plugs into

### Finding #8: 750 cycles, and one end of them is bonded in forever

`[web]`: IEC 60603-7 category-compliant RJ45 connectors are qualified to **750
mating cycles** with ≤20 mΩ of contact-resistance change.

The design's whole connector philosophy is *"treat cable failure as routine.
Keep spares. **Replace the lead at the first sign of intermittency** rather than
diagnosing it"* `[repo] 0004`, and `bom.csv` orders `CABLE-UMB` **qty 2** —
one spare `[repo]`.

```
[calc]  750 cycles ÷ 2 mate-demate events per session = 375 sessions.
        At 3 sessions a week: ~2.4 years of the chassis jack's life.
```

The plug-side cycles land on the consumable and do not matter. **The
chassis-side cycles land on `J-UMBILICAL`, and the instrument's copy of it is
bonded inside a body that is never reopened** `[repo] 0009`. Nothing in the repo
records that the instrument-end connector has a finite, countable life.

**Recommendations:** (a) record it; (b) the **feedthrough variant converts this
into a serviceable failure** — the internal patch lead and the external one both
plug into replaceable RJ45s, and only the feedthrough body itself is
unretrofittable; (c) qty 2 for `CABLE-UMB` is one spare for a part that is
described as a consumable — **buy four**.

### Hot-plug: an operating rule that must be written

`[calc]`, plugging a live umbilical into the instrument's bulk capacitance:

```
Instrument bulk = ~2.2 mF (2 × 100 µF buck inputs + 2 × 1000 µF strip bulk)
                                                        [repo] power-entry.md
With SW-POWER already ON, the LT1641-1's FET is enhanced and its soft-start
ramp has completed. Plugging in presents a discharged 2.2 mF as a SHORT.
  → instantaneous demand >> 1.0 A limit
  → LT1641-1 enters current limit, the 50 ms fault timer expires, it LATCHES.
  → panel LED out, instrument dark, toggle cycle required.
```

The design is *correct* — that is the load switch doing its job — but it means
**hot-plugging the umbilical always latches the module off**, every time, and
nobody has written that down. The `-1` (latching) part choice is deliberate and
right `[repo] power-entry.md`; the operating consequence is not documented.

Also: RJ45 contacts are in a single row at a common depth, so **there is no
ground-first mating sequence**. During insertion all eight contacts make within
the same few milliseconds of wipe, and contact bounce on pin 3 chatters +12 V.
The LT1641's timer absorbs it. And breaking 359 mA of DC on a gold-flashed RJ45
contact arcs; repeated hot-unplug erodes the chassis contact, which is the
unretrofittable one.

**Write the rule: switch the module off before connecting or disconnecting the
umbilical.** One line in the README, one line on the panel silkscreen if there
is room. It costs nothing and it protects the one connector that cannot be
replaced.

### Cable length is unbounded

`bom.csv` says "~2m" `[repo]`. Nothing states a maximum, and the whole point of
the etherCON decision is that any Cat5e patch lead works. `[calc]` at 5 m,
stranded worst case:

```
R_cond = 14 Ω/100 m × 5 = 0.70 Ω  →  R_loop = 1.44 Ω (with contacts)
At 579 mA: 833 mV drop. Buck still has 4.6 V of headroom. Fine.
CM on AGND: 0.34 A × 0.72 Ω = 245 mV → ÷79 dB → 60 µV at the jack. Fine.
2·T_d = 50 ns — NEXT is still saturated, so finding #1 does not get worse.
Contact current unchanged. Inrush: 1.0 A into 2.2 mF is unchanged.
```

**A 5 m lead degrades gracefully; a 25 m lead does not** (NEXT begins to
saturate against the standards limit near λ/4 = 25 m at 2 MHz). **State a
maximum of 5 m in the `CABLE-UMB` row.** It is one sentence and it stops someone
reaching for a 30 m drum in a hurry.

### The wrong-lead table, checked

ADR 0004's table `[repo]` covers rollover and 10/100 crossover. I worked both
through and **both are genuinely covered**, which is worth confirming because
the analysis is not obvious:

| Lead | What happens | Covered? |
|---|---|---|
| **Rollover** (1↔8, 2↔7, 3↔6, 4↔5) | +12 V and `PWR_GND` swap. `D-REVSHUNT` (SS34, cathode to pin 3) conducts hard, the LT1641-1 sees a short and latches, panel LED out | **Yes** `[repo] 0004, bom.csv` |
| **10/100 crossover** ((1,2)↔(3,6)) | The instrument's power pins now carry the in-amp's 10 kΩ + 1 MΩ → **no power reaches the instrument**. +12 V lands on the instrument's `BREATH` pin through `R-SER-BREATH-INST` 1 kΩ, into an *unpowered* OPA2197 output. `[calc]` (12 − 0.7)/1 kΩ = 11.3 mA through the ESD diode into a dead rail. ADR 0003's designed-safe sustained-fault case is 11.8 mA through a **1206** part rated 250 mW: `11.3 mA² × 1 kΩ = 128 mW`. Inside rating | **Yes** `[repo] 0003, bom.csv` |
| **Gigabit crossover** (also (4,5)↔(7,8)) | Power still crossed → instrument dark, as above. SPI is also crossed but nothing is powered | **Yes, by the same mechanism** |

ADR 0004's conclusion — *"A pin-map reorder was considered and declined: a
gigabit crossover swaps the other pair group as well, so no mapping is safe
against every lead. A diode is."* `[repo]` — is correct and I have nothing to
add except that **`R-SER-BREATH-INST`'s 1206 package is load-bearing for this
case**, and `bom.csv` already says so in bold `[repo]`. Protect that row.

**One case the table misses: a lead with a single broken conductor.** ADR 0004
acknowledges a broken `BREATH` or `AGND` is invisible to the instrument
`[repo]`. A broken `PWR_GND` (pin 6) is worse and is not mentioned:

```
[calc]  If DIG_GND and PWR_GND are common at both ends (finding #2), the
        instrument keeps running with its entire return in conductor 8.
          359 mA × 0.30 Ω = 108 mV DC on SCLK's reference — survivable
          At clamp-legal 579 mA: 174 mV — survivable
          At clamp-off 1522 mA: 457 mV, 57 % of the AHCT V_IL margin, and
            0.65 W in one 24 AWG conductor. Now it is not survivable.
        Nothing reports it. The instrument runs normally until the lights
        come up, then the SPI link fails intermittently.
```

**This is the strongest argument for keeping `DIG_GND` and `PWR_GND` separate at
the instrument** after all — it converts a silent, load-dependent, intermittent
failure into an instant dead instrument, which is the failure you want. It runs
against my recommendation in finding #2 and I record both honestly: **the
question is which failure mode you prefer, and nobody has posed it.**

---

## Whole-system grounding: the current-loop map

```
                    RACK PSU EARTH ── case ── rails ── 8HP PANEL
                          │                                │
                    bus board GND                    etherCON shell?
                          │                                │  (LOOP C — §shield)
   ┌──────────────────────┴────────────────────────────────┼──────────┐
   │  MODULE                                               │          │
   │   ★ STAR = the Eurorack power inlet's ground pin  [repo] 0004    │
   │     ├── PWR_GND, own copper, ~360–580 mA ──────── pin 6 ─────────┼──┐
   │     ├── DIG_GND ── (disputed: own path, or under the trace) ── pin 8 ─┤
   │     ├── module analog return (op-amps, DAC AVDD, pitch ref)      │  │
   │     └── (AGND is NOT here — it is the in-amp's IN−)              │  │
   └──────────────────────────────────────────────────────────────────┘  │
                                                                         │
   ┌─────────────────────────────────────────────────────────────────────┘
   │  INSTRUMENT (carrier)
   │   PWR_GND pour ─┬── WS2815 strip returns (0–1.01 A, 2 kHz PWM)
   │                 ├── buck A / buck B returns
   │                 ├── MECH-GNDBOND ── aluminium key plate ── THE PLAYER
   │                 ├── U-TVS-SPI return               [repo] carrier §4
   │                 └── ONE TIE ── analog star ── AGND-local ── pin 2
   │   DIG_GND ── ??? ── U-TVS-CHAIN return only        [repo] carrier §3
   │   Chain ribbon's 5 GND conductors ── ??? which pour
```

**Three unresolved joins, all at the instrument, all unretrofittable:**
`DIG_GND`↔`PWR_GND`, the chain ribbon's grounds↔which pour, and the shield.

### The loop that is a problem

Ranked by what each loop costs:

| Loop | Carries | Cost | Verdict |
|---|---|---|---|
| **A** power pair, twisted | 359–1522 mA | 215–600 mV of IR drop, all common-mode at the in-amp, rejected by 79 dB → **25 µV at the jack** | Benign. The design works |
| **B** pin 6 ∥ pin 8 | ~half the return each | 54 mV DC + 5 mV of 2 kHz on `SCLK`'s reference; defeats the module's star rule | Tolerable, undocumented |
| **C** shield → panel → rack chassis → bus ground | 43–347 mA through the rack | **~7 cents of breath-correlated pitch bend** at the assumed bus resistance | **This is the one** |
| **D** `AGND` | Tens of nA of in-amp bias `[repo] 0003` | 0.2 ppm | Correct by design |
| **E** player → key plate → `MECH-GNDBOND` → pin 6 → rack earth | ESD | 30 A into 2 µH of cable inductance; arrives at the module as common mode, and **`U-TVS-MODULE` is not fitted** | Finding #7 |

**Loop C is the problem loop.** It is the only one that carries a significant
fraction of the instrument's current outside the intended conductor, the only
one that couples into another module's ground reference, and the only one
created by a part the BOM describes as "free".

### Finding #7: `U-TVS-MODULE`, deferred backwards

`bom.csv` `[repo]`:

> "The BOM had protection at one end only. **DELIBERATELY open, not forgotten**:
> the module is behind four screws and this is retrofittable, where the
> instrument end is bonded shut. Fit at E12 if E11 gives any reason to."

The logic is "protect the end you cannot reach". **But the threat's geometry runs
the other way.** The ESD source is the player's hand on an aluminium plate
bonded to `PWR_GND` `[repo] 0009, bom.csv MECH-GNDBOND`. The instrument-side
`U-TVS-SPI` clamps `SCLK`/`MOSI`/`CS` to the instrument's **local** `PWR_GND`,
which is exactly right — it bounds the *differential* stress launched into the
cable. What it cannot do is stop the instrument's entire ground reference from
translating by hundreds of volts relative to the module for tens of nanoseconds.
That common-mode transient arrives at the module's 74AHCT125 inputs with
nothing between it and the DAC8568 but 10 kΩ pull-ups.

```
[calc]  IEC 61000-4-2, 8 kV contact: 30 A peak, ~1 ns rise  [from memory]
        Umbilical power-pair loop inductance: 500 nH/m × 2 m = 1 µH
        The current cannot rise into that inductance at 30 A/ns — what happens
        instead is that the instrument's ground floats up until the discharge
        is absorbed by its own capacitance and bled away over tens of ns.
        The SPI lines, referenced to that ground, go with it.
```

**Fit `U-TVS-MODULE` at E12 unconditionally, and add a common-mode choke or a
clamp-on ferrite at the module's cable entry.** ~$1.50 total for the retrofittable
end of a problem whose expensive end is already protected. The current
instruction — "fit at E12 *if E11 gives any reason to*" — makes it conditional on
a bench test that does not include an ESD gun `[repo] ROADMAP E11`.

---

## Finding #12: E11 cannot detect the failure the pin map creates

E11's acceptance criteria `[repo] ROADMAP`:

> "SPI **at 2 MHz** … and the analog breath pair over the real cable at length,
> **on the T568B pin mapping in ADR 0004** — the mapping is reasoned, not
> measured. Breath output clean while display, LEDs and WiFi are exercised."

Three problems:

1. **"SPI at 2 MHz" is not a criterion.** The failure mode from finding #1 is a
   mis-framed `CS` producing a sticky write into the DAC8568's control space —
   *intermittent, silent and sticky*, in `bom.csv`'s own words `[repo]`. A link
   that "works at 2 MHz" while you watch it is exactly what that failure looks
   like until it doesn't. The criterion must be a **bit-error rate over hours**,
   with the specific observable named.

2. **There is no way to read the DAC's control registers.** No `MISO`, no
   presence detect, no telemetry — the umbilical is write-only by design
   `[repo] 0004`. So the *only* observable is the six analog outputs. The test
   has to be: write a known code set, measure all six jacks with a DMM on a
   scanner or a logged meter, run for hours, log deviations. **That is
   buildable and nobody has written it.** `D2`'s request for test points and an
   LA header on the carrier is the same gap `[repo] carrier.md`.

3. **E11 runs at bench scale and M8 does not re-run it.** The ROADMAP is honest
   that "M8 exists because E11 tests a topology that does not survive to the
   finished instrument" `[repo]` — and then M8's criteria say "Full **E11
   breath-noise test** re-run on the final harness" `[repo]`. **Only the breath
   half.** The SPI-at-2 MHz half, which is the half that depends on the pin map
   and on the final grounding, is never re-run on the real loom.

**Required additions:**
- **E11:** scope `CS` at the module's 74AHCT125 input, with the real 2 m lead,
  with `MOSI` running worst-case data (alternating bits), and **measure the
  coupled glitch amplitude against the 678 mV `V_IL` margin.** That single
  measurement resolves finding #1 and settles the even-mode impedance that my
  estimate turns on.
- **E11:** add an ESD test, or explicitly state that `U-TVS-MODULE` is fitted
  without one.
- **E11:** measure the instrument return current split between pins 6 and 8
  (finding #2) and, with the shield bonded, between pin 6 and the rack chassis
  (finding #3, Loop C). Both are two-minute measurements with a current probe
  and both settle an unretrofittable decision.
- **M8:** re-run the **whole** of E11, not the breath half.

---

## What is unretrofittable, and whether each is right

Everything the body bonds over, gathered from across the repo and audited:

| # | Item | Where it is recorded | Right? |
|---|---|---|---|
| 1 | **The umbilical pin map at the instrument end** | ADR 0004 pin table `[repo]` | **No.** Finding #1. Fix A must be taken before M7 |
| 2 | **`DIG_GND`'s connection at the carrier** | Nowhere `[repo]` | **No.** Finding #2. Undrawn on a board about to be laid out |
| 3 | **Shield termination and `MECH-BACKPLATE`'s material** | `MECH-BACKPLATE` is "TBD - aluminium or ply, **open**" `[repo] bom.csv` | **No.** Finding #3. An `open` BOM row silently decides the shield topology |
| 4 | `D-REVSHUNT` SS34 | "UNRETROFITTABLE" in the BOM `[repo]` | **Yes.** Correctly flagged, correctly sized |
| 5 | `R-SER-BREATH-INST` ×2, **1206** | "Both are instrument-side and UNRETROFITTABLE" `[repo]` | **Yes.** And the 1206 package is load-bearing for the crossover case |
| 6 | `D-TVS-BREATH` ×2, `U-TVS-SPI` | `bom.csv` `[repo]` | **Yes** |
| 7 | `R-LED-PD` ×2 (10 kΩ) | "Two 0805s, and **they cannot be added later**" `[repo] carrier §5` | **Yes**, and it is **still not in the BOM.** Add it |
| 8 | `F-CHAIN` + a 3V3 clamp | `F-CHAIN` proposed, clamp not proposed | **Partly.** Fit both. Finding above |
| 9 | `R-CHAIN-SER` ×3 + `QH` series ×4 | `carrier.md` proposes 3, BOM has 0, `QH` has none anywhere | **No.** Finding #6 |
| 10 | `J-CHAIN` keying scheme | "Same pinout at all eight" `[repo]` | **No.** Finding #6 — keying stops reversal, not mis-plugging |
| 11 | Chain spare conductors reaching pads | Not specified `[repo] cluster §3` | **No.** ADR 0009's spare rule is defeated at both ends |
| 12 | `J-LED` keying and conductor gauge | Neither specified `[repo]` | **No.** Finding #10 |
| 13 | `J-DISP` keying, pinout and rail | None specified; `C-BULK-DISP` is `TBD`/`open` `[repo]` | **No.** Finding #9 |
| 14 | The etherCON variant (feedthrough vs tags) | Deferred to E12/M7, **after E13** `[repo] 0004, carrier.md` | **No.** Finding #11 — an ordering violation |
| 15 | The internal tail loom | Not in the BOM at all | **No.** Not specified, not counted, not gauged |
| 16 | `MECH-GNDBOND`'s location (the one star tie) | "This board is the only place that bond can originate" `[repo] carrier §1` | **Yes.** Correctly stated |
| 17 | Chain order `RT→RH→LT→LH` | `key-layout.yaml` `[repo]`; reorder proposed, not applied | **Open, and the argument is wrong.** Decide it on loom length and body crossings, not skew |
| 18 | The 8-bit marker pattern and `H`…`A` mapping | Moved to `cluster-boards.md` `[repo]` | Out of my scope, but **the marker cannot see a `SH/LD` splice** — finding #14 |

**Eleven of eighteen are wrong or unspecified**, and every one of them is a
connector, a keying choice, a conductor or a ground — i.e. this subsystem. That
is the predictable consequence of the review structure the project has used so
far: **every page describes its own end of every cable, and no page owns the
cable.** `WIRE-LOOM` is one qty-1 BOM row covering four physically different
harnesses; `carrier.md`'s "Loom conductor count" table counts conductors and
does not specify a single one of them.

---

## Recommended actions, in dependency order

**Before `PCB-CARRIER` is laid out (E13):**

1. **Reassign the umbilical pin map** to `1,2 BREATH/AGND · 3,6 +12V/PWR_GND ·
   4,5 SCLK/MOSI · 7,8 CS/DIG_GND` (finding #1, Fix A). Free, and it moves the
   sticky-failure net onto a real pair.
2. **Decide `DIG_GND`'s connection at the carrier and draw it** (finding #2).
   Correct ADR 0004's bullet and the ROADMAP E12 gate to agree with
   `power-entry.md`.
3. **Decide the etherCON variant** (finding #11). Recommendation: feedthrough;
   the stated cost is 46 mV.
4. **Decide `MECH-BACKPLATE`'s material and the shield topology** together
   (finding #3).
5. **Decide where buck B lives and size `C-BULK-DISP`** (finding #9).
6. Add to the BOM: `R-LED-PD` ×2, `R-CHAIN-SER` ×3, a `QH` series resistor ×4,
   `F-CHAIN`, a 3V3 clamp, `J-DISP`, `J-LED-L/-R`, the internal tail loom, and
   the umbilical common-mode choke. Add `±1 %` to `C-FILT-BREATH`. Add "real
   ESR, not ceramic" to `C-BUCK-IN`. Add a 5 m maximum and qty 4 to `CABLE-UMB`.
   Correct `CABLE-UMB`'s implied resistance from 0.168 Ω to 0.28 Ω and propagate.

**At E11:**

7. Scope `CS` at the module's AHCT input with the real lead and worst-case
   `MOSI` data. **This is the measurement the whole review turns on.**
8. Measure the pin-6/pin-8 return split, and the pin-6/chassis split with the
   shield bonded.

**At E12 (module, retrofittable):**

9. Fit `U-TVS-MODULE` unconditionally (finding #7).
10. Fit the 74AHCT14 with an RC on `CS` — `R` 1 kΩ, `C` 39 pF, τ = 40 ns
    (finding #1, Fix C). The module page already wants the part.
11. Isolate the etherCON shell from the 8HP panel; bond it to the star.

**At M8 (the pre-bond gate, last chance):**

12. Run the **whole** of E11 on the final harness, not the breath half.
13. Run the end-to-end chain shift test through `LK-SER`/`R-SER-TERM` — the only
    thing that can catch a mis-plugged `J-CHAIN` before the body closes.

**Documentation, no cost:**

14. Correct ADR 0014's "0.4 % gain compression" (finding #15) and its "the load
    switch bounds current" / "the clamp is a comfort feature" language
    (finding #5).
15. Correct ADR 0001 / `carrier.md §3` / `WIRE-LOOM` on what a `SH/LD` glitch
    costs (finding #14).
16. State the "switch the module off before plugging the umbilical" rule, and
    record the chassis connector's 750-cycle life (finding #8).
17. State **once, in one place**, that breath is analog because it is the
    system's only fail-silent path — and that the price is the conductor the
    digital side needed.

---

## What I could not check

- **The even-mode impedance of a Cat5e pair against remote returns**, which sets
  the amplitude in finding #1 to within a factor of 2.5. Only a measurement
  settles it, and E11 is the place.
- **Neutrik's actual etherCON datasheet** — `neutrik.com` was blocked. The 1.5 A
  and 750-cycle figures are search summaries `[web]`, not datasheet readings.
- **The WS2815 datasheet** — all four hosts blocked. The `VIH = 0.7 × internal
  5 V` finding is a search summary and should be confirmed before closing the
  open item in ADR 0014 and `carrier.md §5`.
- **74AHCT125 and 74HC165 absolute-maximum clamp and output currents** — used in
  findings #6 and #10, marked `[from memory]`, and both findings turn on being
  within ~20 % of the right number.
- **Eurorack bus-board ground resistance per slot**, which sets the magnitude of
  Loop C's pitch bend. I stated the assumption inline. E6 measures it.
- The channel dimensions in `0009`. I assumed 5 mm of separation between the LED
  loom and the key ribbon; the plan section that would confirm it does not exist
  until M4, and `carrier.md` says the 45 mm board and open side channels "are
  still mutually exclusive" `[repo]`. **If the real separation is 2 mm, every
  coupling figure in the `J-CHAIN` section scales by about 2.5× — to ~220 mV
  against a 990 mV margin, which is still adequate but no longer comfortable.**

---

*A8, cold review, 2026-09-21. Findings #1 and #2 are gates on `PCB-CARRIER`.*
