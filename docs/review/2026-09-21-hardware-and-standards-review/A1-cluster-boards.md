# A1 — Key cluster boards, cold review

**Reviewer:** cold hardware review, 2026-09-21. No prior review or research
document in this repo was read. Findings are indexed by **circuit node or BOM
reference**, not by document, because most of them appear in two or three
documents at once.

**Evidence marking.** `[repo] <file>` = read from this repository. `[calc]` =
arithmetic shown inline. `[web] <url>` = fetched or returned by search in this
session. `[from memory]` = could not verify; treat as a thing to check.

**Network.** The egress proxy blocked every datasheet host I tried —
`assets.nexperia.com`, `www.mouser.com`, `cdn.sparkfun.com`, `doc.platan.ru`,
`www.sg-micro.com`, `datasheet.octopart.com`, `www.ti.com`, `www.diodes.com`,
`www.onsemi.com`, `alldatasheet`, `lcsc`, `digikey`, `web.archive.org`,
`en.wikipedia.org`. `raw.githubusercontent.com` is reachable and that is how the
pin map got verified. `gateron.com` is still unreachable, so the mechanical
dimension that my top finding turns on is still missing.

**Headline:** the electrical design is largely right and several of the things I
was asked to attack survive the attack with numbers to spare. The serious
problems are (1) the Z-stack — this board cannot physically exist where two
documents jointly place it, (2) three floating CMOS inputs that nobody has
budgeted a part for, and (3) a connector that is roughly half the cavity tall.
The marker pattern has exactly one hole and it closes for free.

---

## Part 1 — what I verified, and what held

### `U-KEYS` pin map — **VERIFIED, the page is correct**

The page marks the whole pin map `[from memory]` and says it must be checked.
It checks out.

Source: KiCad's legacy `74xx.lib`, symbol `74LS165` with `ALIAS 74HC165`,
footprint list `DIP?16*` / `SO*16*3.9x9.9mm*P1.27mm*`
`[web] https://raw.githubusercontent.com/KiCad/kicad-symbols/master/74xx.lib`.
NXP naming in the symbol, TI naming in brackets as `cluster-boards.md` uses it:

| Pin | Symbol lib | Page's label | Agrees? |
|---|---|---|---|
| 1 | `~PL` | `SH/LD` | yes |
| 2 | `CP` | `SCK`/CLK | yes |
| 3 | `D4` | `E (D4)` | yes |
| 4 | `D5` | `F (D5)` | yes |
| 5 | `D6` | `G (D6)` | yes |
| 6 | `D7` | `H (D7)` | yes |
| 7 | `~Q7` | `QH_bar`, output, open | yes — and it **is** typed `O` (output) in the symbol, so "do NOT ground it" is right |
| 8 | `GND` | `GND` | yes |
| 9 | `Q7` | `QH` serial out | yes |
| 10 | `DS` | serial in | yes |
| 11–14 | `D0`–`D3` | `A`–`D` | yes |
| 15 | `~CE` | `CLK INH`, tied low | yes — active-low enable, so **low = clocking enabled**. Correct. |
| 16 | `VCC` | 3V3 | yes |

**Every pin on the page is right.** Remove the `[from memory]` marker from §1's
pin map and from the *Still open* list; keep it on the thresholds (see N4).

### "`H` is the first bit clocked out" — **VERIFIED**

`Q7` is the output of the last shift stage and `D7` loads into that stage, so
after the falling edge of `PL` the `H`/`D7` input is already present at `QH`
with no clock `[web]` search returned, from the TI E2E logic forum and the
NXP/TI datasheet pages: *"After a load latches the input parallel data, the
output QH represents the MSB that was latched in on the H line… DATA7 first
coming on the DOUT pin."* The symbol's `D0…D7` / `Q7` naming is consistent with
it `[web] 74xx.lib`.

The 32-bit allocation in §4 therefore stands on solid ground:
`bit 0 = H of right_thumb`, and within each device `H G F E D C B A` map to the
device's 8 bits in that order. **This was the single largest risk on the page
and it is closed.**

Consequence worth writing down for firmware, which the page does not state:
the first bit is valid *before* the first clock edge, so the chain must be read
in **SPI mode 0** (CPOL=0, CPHA=0), where the master samples MISO on the rising
edge that the '165 also shifts on. The '165's `CLK`→`QH` delay is tens of ns
`[from memory]` against an ESP32 MISO hold requirement of ~0 ns, so there is no
race at 1 MHz — but a firmware author who picks mode 1 or 3 loses bit 0 and
gets a one-position shift, which is exactly the fault the marker catches.

### The key network's asymmetric shape — **ACHIEVED, and compatible with the 250 µs scan**

Recomputed from scratch at `R-KEY-PU` 2.2 kΩ, `R-KEY-SER` 100 Ω, `C-KEY` 47 nF,
3.3 V, `V_IH` 2.31 V, `V_IL` 0.99 V. The page's figures are right to within
4 %; the small differences are because it used ideal endpoints.

```
[calc]
  pressed node level  = 3.3 × 100/(2200+100)          = 0.1435 V
  release  τ          = 2200 × 47 nF                  = 103.4 µs
  press    R_th       = 2200 ∥ 100                    = 95.65 Ω
  press    τ          = 95.65 × 47 nF                 = 4.496 µs   (page: 4.7 µs)

  release, from 0.1435 V, crosses V_IH = 2.31 V at
      t = −103.4 µs · ln[(3.3−2.31)/(3.3−0.1435)]     = 119.9 µs   (page: 125 µs, V0 = 0)
  press, from 3.3 V, crosses V_IL = 0.99 V at
      t = −4.496 µs · ln[(0.99−0.1435)/(3.3−0.1435)]  =   5.92 µs  (page: 5.66 µs)
```

**Asymmetry ratio 119.9 / 5.92 = 20×.** Instant attack, filtered release. The
shape the page claims is the shape it gets.

Now the part the page does not do — **how long the node spends in the
indeterminate band**, which is what actually decides whether the scan can be
fooled:

```
[calc]  release: leaves V_IL at 32.3 µs, reaches V_IH at 119.9 µs
        → 87.6 µs in the band. 87.6/250 = 35.0 % chance a scan lands in it.
        press:   leaves V_IH at 1.69 µs, reaches V_IL at 5.92 µs
        →  4.22 µs in the band.  4.22/250 =  1.7 % chance.
```

That asymmetry is the right way round and it is the real argument, better than
the one on the page. **A press is read as a valid level 98.3 % of the time; a
release is ambiguous 35 % of the time.** Since note-*on* is the latency-critical
and credulity-critical event and note-*off* is filtered in firmware anyway,
the network puts its uncertainty where it costs nothing. **This is fine, and it
is fine for a better reason than the page gives.**

**Against the two-agreeing-samples rule:** the rule costs 250 µs and guards
against single-sample corruption. It does not interact badly with the 120 µs
release filter, because 120 µs < 250 µs means at most one sample can land in a
release transition, and that sample can only delay a note-off by one period.

**Against contact bounce, which is the thing the release filter actually does:**

```
[calc]  minimum bounce-open interval that lets the node climb back to a valid HIGH
        = the same 119.9 µs.
```

So the network swallows every bounce-open shorter than ~120 µs outright — the
input never leaves the low state. Bounce-opens longer than 120 µs get through,
and then the two-sample rule and firmware's filtered note-off handle them.
That is a coherent two-stage scheme. **It is not validated**, because KS-33
bounce duration is unpublished and ADR 0002 correctly defers it to a scope at
M1 `[repo] 0002, ks33-geometry.md`. The number to measure is *the longest
bounce-open interval*, not "bounce duration" — that is what 120 µs has to beat.
Worth writing into M1's test plan in those words.

### Pole and static current — **page is right, with one refinement**

```
[calc] open (2.2 kΩ):   f = 1/(2π·2200·47n)  = 1539 Hz
                        20·log10(800k/1539)  = 54.3 dB   ← page's figure
       closed (95.65 Ω): f = 1/(2π·95.65·47n) = 35.4 kHz
                        20·log10(800k/35.4k) = 27.1 dB   ← page does not state this
```

The 54 dB only applies to a **released** key. A pressed key sits behind 95.65 Ω
and gets 27 dB. That is not a problem — a node clamped at 0.1435 V through
95.65 Ω is about as stiff as a logic node gets, and on this board the trace is
millimetres, not 265 mm — but the page should not imply 54 dB is the figure for
both states.

```
[calc] static: 3.3/(2200+100) = 1.4348 mA per closed key
       18 closed = 25.83 mA      15 note keys only = 21.52 mA
```

Page's 1.43 mA / 25.8 mA confirmed. And **18 closed is the right worst case,
not a fiction** — on a woodwind the lowest note covers everything.

### `LK-SER` / two-connector scheme — **WORKS, at every position including the last**

I traced every connector face in the chain. Writing `IN.n` / `OUT.n` for pin *n*
of each connector:

| Board | `IN.6` | `IN.8` | `OUT.6` | `OUT.8` | `LK-SER` |
|---|---|---|---|---|---|
| carrier | drives `SER` (IO33) | reads `QH` → IO40 | — | — | — |
| `right_thumb` | passthrough in | **its own `QH` out** | passthrough out | **`SER` source in** | A |
| `right_hand` | passthrough in | its own `QH` out | passthrough out | `SER` source in | A |
| `left_thumb` | passthrough in | its own `QH` out | passthrough out | `SER` source in | A |
| `left_hand` | **passthrough in → `LK-SER` B → `U-KEYS` pin 10** | its own `QH` out | *not fitted* | *not fitted* | B |

The invariant that makes it work: **on every board, `IN.8` is an output and
`OUT.8` is an input, always, with no exceptions.** So a 1:1 ribbon between any
`OUT` and any `IN` always joins exactly one driver to exactly one receiver.
**The page's claim that a straight-through ribbon works between any two boards
is correct**, and the last board is not a special case — it is the same board
with one connector unpopulated and one solder blob moved.

Two things the page does not say, one of which is a real hazard:

- On `left_hand` the unpopulated `OUT` footprint leaves the `LK-SER`
  position-A trace as an open stub. Harmless (it is a CMOS input stub of a few
  mm), but it should be the *short* leg in layout.
- **A mis-set `LK-SER` is caught by the marker.** If position B were set on a
  middle board, that board's `SER` would come from the pulled-up `SER` bus, and
  bits downstream of it would read all-1s. Marker bit 21 expects 0 and reads 1
  → frame fails. Good: the one hand-set option on the board is self-checking.

### `R-SER-TERM` divider — **arithmetic correct**

```
[calc] carrier IO33 driving low through R-CHAIN-SER 100 Ω against R-SER-TERM 10 kΩ:
       3.3 × 100/(100+10000) = 32.7 mV,  against V_IL = 0.99 V.  30× margin.
```

Page's "within 33 mV of the rail" confirmed. And it holds *a fortiori* if
`R-CHAIN-SER` is never fitted — it is still marked `** R PROPOSED **` on the
carrier `[repo] carrier.md §3` — because 0 Ω wins harder. Flagging the
dependency anyway since the page states the 100 Ω as though it exists.

### Chain order and the proposed swap — **both electrically safe, arithmetic confirmed**

The crossing count is right: `RT → RH → LT → LH` is bottom→top, top→bottom,
bottom→top = **3**; `RT → RH → LH → LT` is bottom→top, top→top, top→bottom =
**2** `[calc]`, against `left_hand` top / `left_thumb` bottom / `right_hand` top
/ `right_thumb` bottom `[repo] key-layout.yaml`.

And the skew argument survives the swap:

```
[calc] whole loom ≈ 265 mm [repo] 0001; ribbon propagation ≈ 5 ns/m
       → end-to-end clock skew ≈ 1.3 ns
       HC165 CLK→QH t_PD ≈ tens of ns [from memory]
       worst-case hold margin if a hop runs the "wrong" way = t_PD − 1.3 ns
       at t_PD = 30 ns → 28.7 ns of hold margin remaining
```

So the swap costs ~4 % of hold margin, matching ADR 0001's "a few percent"
`[repo] 0001`. **The proposal is sound.** See M8 for what else moves with it.

### Grounded plate above the board — **the coupling worry is a non-worry**

```
[calc] a 20 mm × 0.3 mm key-node trace, 3 mm below a grounded plate:
       C = ε0·A/d = 8.854e-12 × (20e-3 × 0.3e-3)/3e-3 = 0.018 pF
       into C-KEY = 47 nF → divider 0.018p/47n = 3.8e-7
       plate potential swing, if MECH-GNDBOND carries LED return noise, ~30 mV
       → injected at the key node ≈ 11 nV
```

**The plate is harmless as a capacitive aggressor and genuinely useful as a
shield.** Do not spend any effort here. The plate risk is entirely DC and
mechanical — see H3 and S1.

### Other things I checked that are fine

- **`CLK INH` low, permanently** — pin 15 is `~CE`, active low, so low enables
  clocking `[web] 74xx.lib`. Correct, and with SPI3 dedicated to the chain
  `[repo] 0001` there is nothing that needs to inhibit the clock.
- **`QH_bar` open** — it is an output `[web] 74xx.lib`. Correct, and the page's
  "do NOT ground it" is the right warning to leave in.
- **Chain read time** — 32 bits at 1 MHz = 32 µs = 12.8 % of 250 µs `[calc]`.
- **Loom IR drop.** 28 AWG ribbon ≈ 0.23 Ω/m `[from memory]`, hop ≈ 66 mm, IDC
  contact ≈ 15 mΩ, so `R_hop` ≈ 0.066×0.23 + 2×0.015 = 45.2 mΩ. Current per
  hop with all keys down is 25.8 / 21.5 / 12.9 / 7.2 mA, so the drop at the far
  board is 45.2 mΩ × 67.4 mA = **3.05 mV**, and the ground shift across 5
  parallel returns is **0.61 mV** `[calc]`. Against >1 V of HC noise margin
  this is nothing. The 3V3 conductor does not need to be doubled up.
- **Inrush.** 21 × 47 nF = 987 nF plus 4 × 100 nF, charging through 2.2 kΩ
  each: peak 21 × 3.3/2200 = **31.5 mA**, decaying with τ = 103 µs `[calc]`.
  No LDO cares. Key nodes are valid ~517 µs (5τ) after the rail is up.
- **Marker straps to the rails, no parts.** Correct. A '165 parallel input is an
  input only; there is nothing to current-limit. The "16 parts saved" is
  8 pull-ups + 8 caps `[calc]` — consistent.
- **Part counts.** 21 × 3 = 63 network passives ✓; 1+2+2+2 = 7 cluster
  connectors, +1 carrier = 8 ✓ matching `J-CHAIN` qty 8 `[repo] bom.csv`;
  4 ICs, 4 decoupling caps, 8 marker straps ✓.

---

## Part 2 — findings

### SHOWSTOPPER

#### S1 · `PCB-CLUSTER` (top-face boards) / `PLATE-TOP` — the Z-stack does not close, and §5 assumes the friendlier of two incompatible readings

`cluster-boards.md` §5 models the stack as **plate → switch → PCB** with an
MX-like *"~3.4 mm"* standoff `[repo] cluster-boards.md`. That is the
thumb-cluster geometry, and for `left_thumb` / `right_thumb` it is right: ADR
0009 puts the thumb plate on the **inside** face and the oak through-cut is
just the finger recess `[repo] 0009`.

For the two **top-face** boards it is not right. ADR 0009's stack is:

```
[repo] 0009
  aluminium top plate       ~2 mm   ← outermost
  oak top                   ~6 mm
  ---- cavity ----          remainder  (= 38 − 2 − 6 − 8 − 2 = 20 mm)
  oak bottom                ~8 mm
  thumb switch plate        ~2 mm
```

and its own sentence: *"Top switches pass through the plate and oak and
protrude slightly into the cavity."* So a top-face switch has to span
**2 + 6 = 8 mm** of laminate before it reaches anything a PCB could sit on
`[calc]`.

A KS-33 is **12.2 mm tall overall** `[repo] ks33-geometry.md, 0002, 0009`.
For 8 mm plus pin length to be below the plate's top surface, at most ~4 mm of
the switch is above it — less than an MX stem and top housing. The bound that
settles it without the drawing: **a KS-33 is 6.3 mm shorter than an MX (18.5 mm)
and cannot have more body below the mounting shoulder than an MX does, which is
about 5 mm** `[from memory]`. 8 mm is therefore not reachable.

ADR 0009 also contradicts itself three paragraphs later: *"even if the entire
12.2 mm sat inside it [the cavity] there would be 8 mm left"* `[repo] 0009` —
which places the whole switch *below* the oak, not through it. Both readings
cannot be true unless the switch is ~20 mm long.

**Why this is a showstopper and not a mechanical nit.** §5 says the board
outline *"cannot be drawn yet, and that is correct rather than incomplete"*
because the X/Y positions are `null` `[repo] key-layout.yaml`. That is true of
X and Y. It is **not** true of Z, and the page presents Z as a single `TBD`
waiting on one Gateron dimension. It is not waiting on one dimension; it is
waiting on a decision nobody has taken about where the aluminium plate goes on
the top face. Every downstream item is blocked by it: component height, which
side the passives go on, whether the `74HC165` can face the plate, the
connector choice in H1, the plate DXF, and the oak top's cut list.

**Resolutions, and they are not equivalent:**

1. **Move `PLATE-TOP` to the inside face of the oak top**, symmetric with the
   thumb plate. Makes §5 literally correct as written. Cost: the oak top needs
   a ≥17 mm cut per key (a 16.5 mm `CAP1-n` keycap cannot enter a 14.0 mm hole
   `[repo] bom.csv, ks33-geometry.md`), and the keys then sit in 6 mm-deep
   wells, which is an ergonomic change, not a detail.
2. **Cut the oak top away along the whole key line** and let the 2 mm plate span
   it. Preserves the feel and the stack diagram. Needs the plate to be
   structural over a long unsupported span — ADR 0002's requirement 3, *"the
   plate does not flex"*, and ADR 0009's lamination thesis stops helping where
   there is no oak.
3. Keep the stack and accept that top switches cannot reach a PCB — i.e. hand-
   wire the top clusters, which reverses ADR 0001's whole per-cluster argument.

**Also, whichever is chosen: the oak cut must be relieved, not nominal.** If
both the aluminium and the oak are cut at 14.0 mm, lateral location is shared
between a metal part and a wood part, and ADR 0002 rejected wood for exactly
this — *"repeatable cutout tolerances in wood are not achievable"* `[repo] 0002`.
The oak wants ~15.5–16 mm so the aluminium alone locates the switch, which is
what makes the cutout *"the precision feature of the entire build."*

Confidence: **high** that there is an unresolved conflict; **medium** on the
exact magnitude, because the above/below-plate split of the 12.2 mm is the one
number nobody has `[repo] 0009, ks33-geometry.md`. One dimension off Gateron's
drawing settles it, and it is the same download ADR 0002 has been asking for.

---

### HIGH

#### H1 · `J-CHAIN` — an ~8.9 mm boxed header in a 20 mm cavity, and all eight change together

`J-CHAIN` is a **2×6 2.54 mm IDC boxed header, THROUGH-HOLE, shrouded**
`[repo] bom.csv`. A standard shrouded 2.54 mm header body is **8.5–9.0 mm tall**
above the PCB `[from memory]` — it is a desktop-motherboard part.

```
[calc] thumb-cluster column, worst case:
  cavity                                    20.0 mm   [repo] 0009
  KS-33 body protruding up into it          ~8 mm     (12.2 mm less the part in
                                                       the oak bottom's recess)
  PCB-CLUSTER                                1.6 mm   [repo] bom.csv
  J-CHAIN body                               8.9 mm
                                           ─────────
  used                                      18.5 mm  → 1.5 mm left
```

and the ribbon still has to leave the header and bend, which wants another
5–10 mm. ADR 0009 says *"boards are not the constraint on depth"* `[repo] 0009`
— true of an ESP32 module at ~5 mm, not true of this connector. Both faces
carry a cluster board and `LH`/`LT` and `RH`/`RT` sit at the same longitudinal
positions `[repo] cluster-boards.md` figure, so in those regions two headers
face each other across the cavity: 2 × 8.9 = **17.8 mm of 20 mm** `[calc]`
before anything else, and the cavity also has to carry the LED channel, the
breath tube and this very loom `[repo] 0009`.

**Fix, and it is cheap only right now.** Choose a low-profile connector before
the boards are ordered: a 1.27 mm-pitch 2×6 IDC is ~5.8 mm `[from memory]`, a
right-angle header moves the height into plan, and an FFC/FPC ZIF is 1.2–2.5 mm
and would also kill the mis-mate hazard in M4. **All eight connectors and all
four ribbon assemblies change as one BOM row** `[repo] bom.csv J-CHAIN qty 8`,
so this is one decision, taken once, worth taking now. Note that a 1.27 mm
ribbon at 12 ways is also narrower, which the side channels will like.

Confidence: **high** on the conflict; **medium** on 8.9 mm, which is from
memory and is one caliper measurement away.

#### H2 · Bits 22, 23, 31 — three floating CMOS inputs, and no part budgeted for them

Three documents agree the free bits must be pulled and none of them pays for it.

- `key-layout.yaml`: *"The 5 genuinely free bits are FLOATING CMOS INPUTS and
  must be pulled"*, now 3 after the marker decision `[repo] key-layout.yaml`.
- ADR 0001 fix 6: *"pull every unused parallel input"* `[repo] 0001`.
- `cluster-boards.md` §4: *"Pull them, per ADR 0001 fix 6."*

But the component table budgets `R-KEY-PU` as **`LH` 5 · `LT` 4 · `RH` 6 ·
`RT` 6 = 21** `[repo] cluster-boards.md`, which is exactly the 21 *switch*
positions and leaves nothing for bits 22, 23 (`left_thumb` `B`, `A`) and 31
(`left_hand` `A`). `bom.csv` `R-KEY-PU` qty is 21 with the note *"One per switch
position including the 3 spare-switch bits"* `[repo] bom.csv`. The carrier
independently confirms the same 21: *"→ 21 pull-ups, 4 × VCC, 4 × 100 nF"*
`[repo] carrier.md §3`.

`left_thumb` needs 4 + 2 = 6 and `left_hand` needs 5 + 1 = 6 `[calc]`, so the
true count is 24 if these are resistors.

**They should not be resistors.** Strap them to a rail exactly like the marker
bits — zero parts, zero current, and a hard level instead of a 2.2 kΩ one. And
then the page's own argument finishes itself: §4 argues that *"'free' bits are
not free — they are useless"* because they have no plate cutout and the body
bonds shut `[repo] cluster-boards.md, 0001`. That argument does not stop at
8 bits. **All three remaining free bits are equally useless and equally
strappable, so the honest allocation is an 11-bit marker and 0 free bits**, at
exactly the same cost as pulling them. That also removes a class of confusion in
firmware, where a "free but pulled" bit reads 1 and looks like an unpressed key.

If you keep them as free-but-pulled, the BOM row has to go to 24 and the
component table to `LT` 6 / `LH` 6. Either way, **this is unretrofittable** —
it is the exact fault ADR 0001 fix 6 exists to prevent, on boards that bond
shut.

Rank High rather than Showstopper because the failure mode is a spurious bit,
not a dead instrument — but three reviewers found the same class of fault in
ADR 0001's history `[repo] 0001` and it is here again.

#### H3 · The cluster-board ground net is never named, and `MECH-GNDBOND` puts `PWR_GND` millimetres above it

`cluster-boards.md` §2 says 3V3 comes from *"pin 10 of `J-CHAIN`"*. Nothing on
the page says which ground the five `J-CHAIN` ground conductors are. It matters
twice:

1. **25.8 mA of play-rate key current returns on those five conductors**
   `[calc]` — a step, at the rate the player moves fingers. If that return lands
   on `AGND`, it is in the breath reference's ground. The carrier keeps three
   domains, `AGND` / `PWR_GND` / `DIG_GND`, ties the analog pour to `PWR_GND` at
   one point, and puts `U-TVS-CHAIN` to **`DIG_GND`** `[repo] carrier.md §1, §2,
   §3` — so `DIG_GND` is the intent, but it is inferred, not stated.
2. **`MECH-GNDBOND` bonds the aluminium plate to `PWR_GND`, never `AGND`**
   `[repo] bom.csv, carrier.md §1, 0009` — and that plate is the thing sitting
   directly above this board, at a standoff of somewhere between 2.5 mm and
   8 mm depending on how S1 resolves.

So the metal 2.5–8 mm above the cluster board is on a **different ground domain
from the board itself**, and the two meet only at the carrier's single tie,
265 mm away. §5's own bullet calls the plate *"a short waiting to happen"* but
stops at "clearance". The consequence is worth stating: **a plate-to-board short
creates a second `PWR_GND`↔`DIG_GND` tie at the far end of the body**, and
`PWR_GND` is the WS2815 return — hundreds of mA of PWM'd LED current
`[repo] carrier.md §1, 0014`. Part of that return would then come home through
the five thin ribbon grounds that exist specifically to be quiet
(ADR 0001 fix 1, *"the highest-value item on this list"* `[repo] 0001`). The
symptom is LED-rate noise in the breath reading and in the key scan, in a bonded
body.

**Three things to add to the page**, all free before layout:

- Name the net. Say `DIG_GND` and say it on the page, not by inference from the
  carrier's TVS.
- Say what a plate short *does*, so the clearance rule survives value
  engineering.
- Give the plate-facing side a keep-out, or an insulating film, or put every
  part on the far side and say so as a rule rather than an option. §5 currently
  offers "or" — make it "and". The switch pins alone are already 18 bare
  conductors pointing at a grounded plate.

---

### MEDIUM

#### M1 · §2 figure — the switch is drawn to 3V3, not to GND

Checked by column alignment, not by eye `[calc]`:

```
line 132   ├──[R-KEY-PU 2k2 1%]──┬───────► input      '├' at col 4, '┬' at col 26
line 136   │                    GND                    left rail col 4, GND col 26
line 137   │                     │                     a vertical BELOW GND, col 26
line 138   └────── SW ──[R-KEY-SER 100R 1%]────────┘   '└' at col 4, '┘' at col 48
```

The left rail at column 4 is labelled **3V3**. The bottom branch leaves that 3V3
rail, passes through `SW` and `R-KEY-SER`, crosses the `C-KEY` ground node at
column 26, and terminates at a `┘` at column 48 that has nothing above it. The
register-input node is at column 26, not 48.

Read literally, **closing a switch shorts 3V3 to GND through 100 Ω** — 33 mA
`[calc]` — and the register input never moves, because it is held at 3.3 V by
`R-KEY-PU` in both states. The intent is unambiguous from the caption
(*"shorts to GND when pressed"*) and from every number in the derivation table,
so this is a drawing defect, not a design defect.

It is Medium and not Low because **this page's stated job is to be laid out
from** — *"the boards should be laid out from one schematic with a variant
table"* — and it is the only drawing of this network anywhere in the repo. ADR
0001 gives the topology in prose only (*"2.2 kΩ to 3V3, 100 Ω in series, 47 nF
to ground"* `[repo] 0001`), and `bom.csv` in prose only. Fix the figure: the
left rail below `R-KEY-PU` should be **GND**, the switch branch should hang off
the **node** at column 26, and the stray `┘` should go.

#### M2 · The marker pattern misses a `left_thumb` load failure — and the fix is free

The pattern as specified is
`(6,7)=(1,0)`, `(14,15)=(0,1)`, `(20,21)=(1,0)`, `(29,30)=(0,1)`
`[repo] cluster-boards.md §4`. I tested it exhaustively.

**What it catches — the page's claims hold:**

| Fault | Caught? | Why `[calc]` |
|---|---|---|
| All-zeros frame | yes | bits 6, 15, 20, 30 expect 1 |
| All-ones frame / stuck bus | yes | bits 7, 14, 21, 29 expect 0 |
| Shift by +1 | yes | bit 6 expects 1, reads true bit 7 = 0 |
| Shift by −1 | yes | bit 7 expects 0, reads true bit 6 = 1 |
| Shift by ±8 (a whole device) | yes | marker-on-marker conflict |
| Broken loom at any hop | yes | downstream bits collapse to a constant, which fails a 0-expecting or 1-expecting marker whichever constant it is |
| Mis-set `LK-SER` | yes | see Part 1 |
| Device dead / unclocked / stuck | yes | its own pair fails whichever way |

Exhaustively, the shifts *guaranteed* caught by a marker-on-marker conflict
alone are ±1, ±6, ±8, ±9, ±13, ±14, ±15, ±16, ±23 `[calc]`. The rest are caught
in practice because they map a 0-expecting marker onto a key bit, which reads 1
when unpressed — but that is a statistical catch, not a guaranteed one. Worth
knowing; not worth changing for.

**The hole.** Take a device whose `SH/LD` does not reach it, so it holds the
previous frame's downstream content. Substituting each device's 8 bits with its
downstream neighbour's `[calc]`:

| Device fails to load | Shows | Verdict |
|---|---|---|
| `right_thumb` | `right_hand`'s bits | bit 6 expects 1 reads 0 → **caught** |
| `right_hand` | `left_thumb`'s bits | bit 14 expects 0 reads free-bit 22 = 1 → **caught** |
| `left_thumb` | `left_hand`'s bits | bit 20 expects 1 reads **LH5**; bit 21 expects 0 reads LH's marker = 0 → **MISSED whenever LH5 is unpressed** |
| `left_hand` | `SER` = 1 via `R-SER-TERM` | bit 29 expects 0 reads 1 → **caught** |

The root cause is that the marker **offsets** are not uniform: `RT` and `RH` put
theirs on inputs `B`,`A` (offsets 6,7); `LT` on `D`,`C` (4,5); `LH` on `C`,`B`
(5,6). Where the offsets of two neighbours differ, a device substitution maps a
marker onto a key bit instead of onto a marker.

**Fix — zero parts, zero new decisions.** Put both marker bits of every device
on inputs **`B` and `A`**, the last two bits of each byte, and keep the page's
own `1 0 · 0 1 · 1 0 · 0 1` levels:

| Device | Marker inputs | Bits | Levels | Free bits move to |
|---|---|---|---|---|
| `right_thumb` | `B`, `A` | 6, 7 | 1, 0 | — (unchanged) |
| `right_hand` | `B`, `A` | 14, 15 | 0, 1 | — (unchanged) |
| `left_thumb` | `B`, `A` | **22, 23** | 1, 0 | `D`, `C` = 20, 21 |
| `left_hand` | `B`, `A` | **30, 31** | 0, 1 | `C` = 29 |

Verified `[calc]`: **all four device load failures caught**, ±1 and ±8 shifts
caught, all-ones and all-zeros caught. Only `left_thumb` and `left_hand` change,
and only by moving two straps each. It also makes the firmware check uniform —
"bits 6 and 7 of every byte, alternating" — instead of four scattered pairs.

The one honest cost: uniform offsets reduce the *guaranteed* shift catches from
18 of 31 to 10 of 31 `[calc]`. The shifts that matter (±1, ±8) stay guaranteed,
and the rest are still caught in practice by unpressed keys reading 1.

**If H2 is taken and all three remaining bits are strapped**, bits 20, 21 and 29
become markers too and the pattern is 11 bits with no free bits at all.

**What the marker misses, and the page should say so.** It is a framing check,
and ADR 0001 says as much `[repo] 0001`, but the number is worth writing down:
**8 of 32 bits carry the check, so a random single-bit corruption is caught with
probability 8/32 = 25 %** `[calc]`. **The visible error counter therefore
undercounts the true corruption rate by 4×** — which is the number firmware
needs to interpret it, and exactly the kind of thing that gets guessed wrong on
a bench at 2 a.m. The marker also tests nothing about the 21 key networks: a
cracked switch joint, an open trace to a `D`n input, a shorted `C-KEY` are all
invisible to it. And the 8 straps are themselves 8 new failure points whose
failure mode is indistinguishable from a loom fault.

#### M3 · `R-KEY-PU` — the 2.2 kΩ / 10 kΩ trade as written is under-specified by 4.5×

§2 says going back to 10 kΩ costs *"a 100 µs τ in a humid cavity"*
`[repo] cluster-boards.md`. With the present `C-KEY`:

```
[calc]  10 kΩ × 47 nF = 470 µs τ;  V_IH crossing at 561 µs = 2.2 scan periods
        2.2 kΩ × 47 nF = 103 µs τ; V_IH crossing at 120 µs = 0.48 scan periods
```

The 100 µs figure belongs to the **old 10 kΩ / 10 nF** pair, which is what
`bom.csv` records the history of `[repo] bom.csv C-KEY`. The live option is
therefore not "swap one resistor" — it is **10 kΩ + 10 nF together**:

```
[calc]  10 kΩ ∥ 100 Ω × 10 nF = 0.99 µs τ → V_IL at ~1.2 µs (press even faster)
        10 kΩ × 10 nF = 100 µs τ → V_IH at ~121 µs (release filter unchanged)
        static: 3.3/(10000+100) = 0.327 mA per key; 18 closed = 5.88 mA
        saving: 25.83 − 5.88 = 19.95 mA, a 77 % cut
```

**So the better pair costs nothing in release filtering and gives back 20 mA.**
The only thing it loses is node stiffness against humidity, and that is
quantifiable too:

```
[calc]  leakage that would hold the node below V_IH:
        (3.3 − 2.31)/10 kΩ = 99 µA   → 33 kΩ of surface resistance across an open contact
        (3.3 − 2.31)/2.2 kΩ = 450 µA → 7.3 kΩ
        74HC input leakage is ±1 µA max [from memory] → 10 mV offset at 10 kΩ. Irrelevant.
```

**33 kΩ across an open switch contact is a very wet contact.** The humidity
argument does not carry 20 mA of cost on its own. This is the carrier's 3.2 LSB
of ADC reference movement `[repo] carrier.md §2` and it would become 0.7 LSB.

The page calls this *"a live trade, not re-opened here"* and that is a fair
scope decision — but the trade as written points at the wrong pair, so whoever
re-opens it will price it wrong. Fix the sentence.

#### M4 · `J-CHAIN` IN↔IN mis-mate puts two `QH` outputs in contention

All eight `J-CHAIN` connectors are the same part with the same pinout and the
same key `[repo] bom.csv, carrier.md §3`. The ribbons are identical. Nothing
physically prevents joining two boards' **IN** connectors, and on every board
`IN.8` is a driven `QH` output.

```
[calc]  two HC totem-pole outputs at 3.3 V, one high one low:
        I ≈ 3.3/(R_on,p + R_on,n) ≈ 3.3/(2 × 50 Ω) ≈ 33 mA  [from memory for R_on]
        74HC absolute-maximum output current is ±25 mA per pin  [from memory]
```

So the mis-mate is **over abs-max**, sustained, on two parts that are soldered
into a body that bonds shut. The page's boxing-and-keying argument protects
against connector rotation but not against this, because the two connectors are
identical in every respect including the key.

Cheap fixes, pick one: make the IN and OUT ribbons visibly different lengths (they
will be anyway); use a different shroud key or a socket/header sex difference
between IN and OUT; or fit a small series resistor in the `QH` path on each
board, which also damps the only point-to-point line in the loom. A 100 Ω in
series with `QH` limits the contention to 3.3/(100+100+50+50) = 11 mA `[calc]`,
within abs-max, and costs one 0805 per board. Given ADR 0001 already proposes
`R-CHAIN-SER` 100 Ω on the carrier's three outputs `[repo] carrier.md §3`, the
symmetric part on `QH` is consistent and near-free.

Also, for completeness: a carrier↔OUT mis-mate is **benign** (two inputs facing
each other, no damage) `[calc]`, so IN↔IN is the only one worth engineering
against.

#### M5 · `SH/LD` and `SCK` have no defined level before firmware runs

ADR 0001 fix 6 pulls the unused *parallel* inputs `[repo] 0001`. Nothing pulls
the three *control* inputs. On the ESP32-S3 the GPIOs are high-impedance inputs
through reset and the bootloader window — the carrier page says so itself, for
a different net: *"On reset GPIO1 and GPIO2 are high-impedance inputs for the
bootloader window (order 100–300 ms)"*, and fits `R-LED-PD` 10 kΩ pull-downs
because *"an AHCT input floating near its threshold does not sit still"*
`[repo] carrier.md §5`.

The identical reasoning applies to `IO7` (`SH/LD`) and `IO38` (`SCK`) and was
not applied. `SER` is covered, by `R-SER-TERM` — on the far board only.

Consequence is not data corruption (nothing is being read yet) but **through
current**: eight HC inputs — four `SH/LD` plus four `CLK` — parked near mid-rail
draw crowbar current of order 0.5–1 mA each `[from memory]`, so **4–8 mA** for
the window, and indefinitely if the board is left in download mode. Plus the
four floating inputs sit at the far end of 265 mm of ribbon next to 800 kHz LED
data, which is an efficient way to make a floating node oscillate.

Two 0805s at the carrier — 10 kΩ pull-up on `SH/LD`, 10 kΩ pull-down on `SCK` —
close it, exactly as `R-LED-PD` does for the LED lines. They are on the carrier
rather than these boards because one pair serves all four devices, and because
the cluster boards' inputs are only ever undriven when the loom is unplugged.

#### M6 · The marker allocation is stale in `carrier.md` — same node, third document

`carrier.md` §3's 32-bit table still reads **"6 | Marker pattern"** and
**"5 | Genuinely free"**, and states *"Which six bits carry the marker and to
what pattern is still undecided"* `[repo] carrier.md §3`. `key-layout.yaml` and
ADR 0001 both say 8 and 3, decided 2026-09-21 `[repo] key-layout.yaml, 0001`,
and `cluster-boards.md` §4 assigns them.

Not my file to edit, but it is the same node in a third place and it is the one
a future reader is most likely to trust, because it is the board page for the
end of the chain.

#### M7 · `IO33` may not exist — and `R-SER-TERM`'s whole rationale depends on it

`cluster-boards.md` justifies `R-SER-TERM` by *"if firmware does drive `IO33`"*,
which makes the end-to-end self-test a firmware choice `[repo] cluster-boards.md
§3, bom.csv R-SER-TERM`. The carrier drives `SER` from `IO33`
`[repo] carrier.md §3`.

`bom.csv` says the Waveshare ESP32-S3-Matrix breaks out **"16 GPIO broken out
(1-7, 34-40, 43, 44)"** `[repo] bom.csv U-MCU-RT`. That list is
7 + 7 + 2 = 16 `[calc]` and **does not contain IO33**. The carrier's own block
diagram writes the row as `IO33 … IO40` and elsewhere counts *"3 power and 17
GPIO"* `[repo] carrier.md`, which is 7 + 8 + 2 = 17 `[calc]` and *does* include
IO33. The two files contradict each other on one pin.

`bom.csv` also warns *"2MB QUAD PSRAM: confirm quad at E1, octal would eat
GPIO33-37"* `[repo] bom.csv`, so IO33 is in the range that disappears if the
part is octal.

`waveshare.com` is blocked from this sandbox, so I cannot settle it `[web]
blocked`. **Fit `R-SER-TERM` anyway** — it is one 0805, it is the tied-off case
ADR 0001 specified regardless, and it is unretrofittable. But **drop the
self-test from the justification until IO33 is confirmed**, and check it at E1
alongside the PSRAM question, since both are the same measurement on the same
board.

#### M8 · The chain-order swap moves more than the bit groups

§4 says *"if the order changes, `left_thumb` and `left_hand` swap their eight-bit
groups"* `[repo] cluster-boards.md`. Three more things move with it, and all
three are copper:

- **`LK-SER` position B** moves from `left_hand` to `left_thumb`.
- **`R-SER-TERM`** moves to `left_thumb` — the component table currently gives
  it to `LH` only `[repo] cluster-boards.md`, matching `bom.csv`
  *"Chain-end board only"* `[repo] bom.csv`.
- **`J-CHAIN` quantities swap**: `LH` goes 1 → 2 and `LT` goes 2 → 1
  `[repo] cluster-boards.md, bom.csv`.

And the groups are not the same size — bits 16–23 currently host 4 keys + 2
markers + 2 free, bits 24–31 host 5 keys + 2 markers + 1 free — so the swap is a
re-derivation of the allocation table, not a relabel. Say so in *Still open*,
because the page currently makes the swap sound cheaper than it is. (It is still
a reasonable swap — see Part 1 for why it is electrically safe.)

---

### LOW / NOTE

- **N1 · The reversed-connector fault mode is misstated, and the truth is
  worse.** §3 says boxing and keying matter *"because a reversed connector puts
  3V3 onto the `QH` net"*. A 12-way reversal maps pin *n* → pin (13 − *n*)
  `[calc]`, so **pin 10 (3V3) lands on pin 3 (GND)** — a dead short of the
  instrument's 3.3 V rail through a ribbon conductor — and pin 8 (`QH`) lands on
  pin 5 (GND). The conclusion (box and key everything) is unchanged, but the
  real hazard is a rail short, which makes `F-CHAIN` — the 100 mA fuse the
  carrier proposes and never adds to the BOM `[repo] carrier.md §3` — worth more
  than "two millimetres of board". A boxed header does not prevent this: it is
  what you get when a ribbon is pressed onto the wrong face of the cable, which
  is the commonest IDC hand-assembly error.

- **N2 · Alternating ground is a cable property, and the connector gives some of
  it back.** In a 2×6 the conductors run 1…12 across the ribbon, so the cable
  really does have ground between every signal `[repo] 0001 fix 1`. On the
  *header*, pins 1,3,5,7,9 are one row and 2,4,6,8,10 the other, so `SCK`,
  `SH/LD`, `SER`, `QH` and 3V3 sit side by side at 2.54 mm with no ground
  between them, for the ~10 mm of the connector body. 10 mm of 265 mm is
  **3.8 %** of the coupling length `[calc]`, at HC edge rates. **Not worth
  fixing** — but worth not claiming the cable's property for the whole path.
  (3V3 at pin 10 also has a ground on only one side, pin 11 being a spare. It is
  a DC rail; fine.)

- **N3 · Two derivation figures are ~4 % optimistic in the conservative
  direction.** Release is **119.9 µs**, not 125 µs, because the node starts at
  0.1435 V and not 0. Press is **5.92 µs**, not 5.66 µs, because the pressed
  time constant is 95.65 Ω × 47 nF and not 100 Ω × 47 nF `[calc]`. Neither
  changes anything. Both appear identically in ADR 0001 and in `bom.csv`
  `[repo] 0001, bom.csv C-KEY`, so correcting one means correcting three.

- **N4 · `V_IH` = 0.7 × VCC and `V_IL` = 0.3 × VCC are not a datasheet guarantee
  at 3.3 V.** 74HC is specified at VCC = 2.0, 4.5 and 6.0 V only: VIH
  1.50 / 3.15 / 4.20 V and VIL 0.50 / 1.35 / 1.80 V `[web]` search over the
  HGSemi/SGMicro/Nexperia datasheets. Note 2.0 V is 0.75/0.25, not 0.70/0.30.
  Interpolating to 3.3 V: **VIH 2.358 V, VIL 0.942 V** `[calc]` — slightly worse
  than the 2.31/0.99 used throughout. Re-running the two transitions at the
  interpolated thresholds moves release to ~123 µs and press to ~5.7 µs
  `[calc]`, so **the conclusions are unchanged**. Keep the `[from memory]` flag
  on the thresholds and drop it from the pin map.

- **N5 · The 54 dB pole figure applies to the released state only** — 27.1 dB
  when pressed `[calc]`, see Part 1. Harmless; just state both.

- **N6 · `R-SER-TERM` would be better at 2.2 kΩ than 10 kΩ.** The `SER` net is a
  265 mm conductor in the LED channel, held only by this resistor whenever IO33
  is not driving. At 800 kHz the loom's ~26 pF `[repo] 0001` has
  Z = 1/(2π·800k·26p) = **7.65 kΩ** `[calc]`, which is *comparable to* the
  10 kΩ pull, so the node is only weakly held at exactly the frequency that
  matters. At 2.2 kΩ: driven-low level becomes 3.3 × 100/2300 = **143 mV**,
  still 7× inside `V_IL`; static cost when driven low is 1.43 mA; and it is the
  **same value as `R-KEY-PU`, removing a BOM line** `[calc]`. The consequence of
  getting this wrong is nil either way — bits shifted in through `SER` are
  overwritten by the next `SH/LD` and never appear in a frame — so this is a
  tidiness argument, not a safety one. Which is itself worth saying on the page,
  because it is not obvious that `SER` noise is harmless.

- **N7 · `C-DECOUPLE-165` is right; its stated reason is weak.** ADR 0001 fix 5
  and §1 both say a '165's *"output edges brown out a local rail that has no
  reservoir"* `[repo] 0001`. The charge involved: `QH` drives ~26 pF of loom, so
  86 pC per edge, which on 100 nF is **0.86 mV** `[calc]`. The real consumer is
  the eight internal flip-flops (C_PD ≈ 45 pF `[from memory]` → ~148 µA average
  at 1 MHz, 3.3 V `[calc]`). **Fit the cap** — it is correct practice and costs
  nothing — but the justification as written invites someone to delete it after
  doing the same arithmetic I just did.

- **N8 · `SW1-n` counts do not reconcile across two files.** The component table
  sums to 5 + 4 + 6 + 3 = **18** fitted `[repo] cluster-boards.md`; `bom.csv`
  `SW1-n` qty is **21** (18 + 3 spares purchased but unfitted)
  `[repo] bom.csv`. Both are right in their own frame; the page's "Totals" line
  says *"18 fitted switches in 21 networked positions"* and resolves it. No
  action beyond not letting a future edit "fix" one to match the other.

- **N9 · KS-33 travel figures disagree between sources.** `bom.csv`,
  ADR 0002 and `ks33-geometry.md` all carry 1.70 mm pretravel / 3.00 mm total
  `[repo]`. A retailer/vendor listing surfaced in search gives **1.2 mm
  pretravel / 3.2 mm total** for KS-33 Low Profile 2.0 `[web]` search summary
  over gateron.com and Amazon listings, which I could not open to confirm. Low
  confidence, and it changes nothing electrically, but it is on the same
  download as the dimension S1 needs — check both at once.

- **N10 · `SH/LD` timing note for firmware.** `SH/LD` is asynchronous and
  level-sensitive; ADR 0001 flags that a glitch on it mid-shift reloads all four
  registers `[repo] 0001`. Firmware must return `SH/LD` high and let it settle
  *before* the SPI transaction starts, and must not let the `SH/LD` rising edge
  coincide with a clock edge `[from memory]` — the standard '165 caution. Worth
  one line on the page, since this page is where the load pin is documented.

---

## Still open, from my side

- **The one dimension that unblocks the most:** the above/below-plate split of
  the KS-33's 12.2 mm, from Gateron's drawing. It settles S1, sets the standoff,
  sets the component-height limit, and confirms or kills H1's connector
  arithmetic. ADR 0002 has been asking for this download since it was written
  `[repo] 0002`; it is now blocking three documents.
- **A `74HC165` datasheet.** I verified the pin map and the bit order from a
  KiCad symbol and two search summaries `[web]`. I could not open a single
  vendor PDF. The thresholds (N4), `t_PD`, `C_PD`, output `R_on` (M4) and the
  `SH/LD` timing caution (N10) all remain `[from memory]`. Five minutes on an
  unfiltered network.
- **I did not read** `docs/review/**` or `docs/research/**`, by instruction. If
  a prior wave already settled the Z-stack in S1 or the connector height in H1,
  those two findings are duplicates — but nothing in `hardware/`,
  `docs/decisions/` or `config/` records such a settlement, and the *Still open*
  list on this page does not mention either.

## What I would do first

1. **S1** — decide where `PLATE-TOP` sits relative to the oak top. Nothing else
   about these boards can be drawn until it is decided, and it is a
   five-sentence ADR amendment, not a redesign.
2. **H1** — change `J-CHAIN` to a low-profile connector. One BOM row, eight
   parts, before anything is ordered.
3. **H2 + M2 together** — strap bits 20, 21, 22, 23, 29, 31, move the four
   `left_thumb`/`left_hand` marker straps to inputs `B` and `A`, and record the
   result as an 11-bit marker with no free bits. Zero parts, closes a floating-
   input fault and a detection hole in one edit, and cannot be done after the
   boards are ordered.
4. **M1** — redraw the §2 figure before anyone lays out from it.

Everything else on this page I would ship.
