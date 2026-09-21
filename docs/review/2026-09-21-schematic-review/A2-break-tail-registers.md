# A2 — Adversarial review: all four 74LVC165s at the tail

**Target:** commit `7c68404`, *"All four shift registers move to the carrier at the
tail"* — ADR 0001 §"The registers live at the tail", `config/key-layout.yaml`
`chain:`, BOM rows `U-KEYS`, `R-KEY-PU`, `R-KEY-SER`, `C-KEY`, `WIRE-LOOM`,
`PCB-CARRIER`, `C-DECOUPLE-165`.
**Date:** 2026-09-21. **Brief:** break it.

---

# VERDICT: **BROKEN**

Not because the tail topology is unbuildable — it probably is buildable — but
because **every load-bearing sentence of the argument that selected it is
wrong**, and because the decision **destroyed the project's only in-service
diagnostic for the thing it was protecting**, while a document in the same
commit claims the opposite.

Five findings, in descending order of how badly they hurt:

| # | Finding | Severity |
|---|---|---|
| **B1** | The marker/error-counter diagnostic is now **structurally blind to the loom**. `ROADMAP.md` line 195, written by this commit, says it "tests the SWITCH LINES". It cannot. | **Fatal to the argument.** Unretrofittable. |
| **B2** | The "retrofittable vs not" tiebreaker is **inverted**. The chosen option's unresolved risk is only discoverable at M4/M8 — the irreversible step. The rejected option's was measurable at E4 with a drop-in fallback already in the BOM. | **Fatal to the argument.** |
| **B3** | The decisive arithmetic is wrong three independent ways: wrong aggressor, wrong circuit model, and a result that **exceeds the physical ceiling of its own mechanism**. | Conclusion survives; *reasoning* does not. |
| **B4** | Conductor count is **32–44, not "~23"**, and the BOM and ADR 0009 specify **contradictory grounding rules** differing by 2×. The stated headline is understated 1.4–1.9×. | High. Unretrofittable. |
| **B5** | `PCB-CLUSTER` was deleted and **nothing replaced it**. There is now no board in the BOM for 18 switches to solder into, against ADR 0002's explicit requirement for one. The build goes from ~4 unsupported hand joints to **~46**. | High. Unretrofittable. |

Plus two costs the decision did not book: **~1830 mm² (41 %) of a carrier whose
stated dimensions the commit did not change** (B6), and a **humidity failure
mode that can only appear after bonding** (B8).

**Evidence markers** — `[repo]` file named and read this session; `[calc]`
arithmetic shown in full; `[from memory]` recalled, unverified. **There is no
`[datasheet]` marker in this document**: vendor domains are proxy-blocked, as
`docs/research/2026-09-21-eurorack-prior-art/R10-keyscan-and-adc.md` also
records `[repo]`. Nothing below is attributed to a datasheet.

---

## B1 — The error counter is now blind to the loom, and the repo says it isn't

This is the sharpest break, and it is the one the decision inverted while
looking straight at it.

ADR 0001 states the purpose of the marker pattern in its own words `[repo]`:

> That counter is the point. It is a framing check… but it converts an
> **invisible intermittent fault into a number on the display that says whether
> the looms are good**. Without it, a marginal chain presents as occasional
> wrong notes that are indistinguishable from playing mistakes.

And the ROADMAP row, **added by this commit** `[repo] ROADMAP.md:195, git show 7c68404`:

> **Key-chain error counter over an hour, LEDs and WiFi active** | E4 | …
> **Now that the registers are all on the carrier, this tests the SWITCH LINES
> and the firmware** rather than a clocked loom

**It does not test the switch lines. It cannot.**

The marker bits are spare *parallel inputs* of the four 74LVC165s, tied to fixed
levels. With all four registers on `PCB-CARRIER`, those tie-points, those
registers, `SCK`, `SH/LD` and `QH→SER` are **all carrier-local traces**
`[repo] ADR 0001: "four devices on one PCB with millimetre traces"`. Nothing
that happens on a 265 mm switch conductor can change a marker bit. The frame
check will read correct on every single frame while any or all of the eighteen
switch lines are being corrupted.

So the decision made this trade:

| | Per-cluster loom | Tail loom |
|---|---|---|
| Failure probability | higher | lower |
| What a failure does | corrupts the 32-bit **word** | flips **one bit** |
| Marker sees it? | **Yes** — the word crosses the loom, so a disturbance breaks the framing | **No** — the word never leaves the board |
| Presentation to the player | error counter increments; a **number** | one wrong note, **silently** |
| Diagnosable at M8, pre-bond? | **Yes, by counting** | **No** — needs a golden reference the project does not have |

**The residual failure mode of the chosen option is exactly the thing ADR 0001
says the counter exists to prevent** — "occasional wrong notes that are
indistinguishable from playing mistakes" — and the chosen option is the one where
the counter cannot see it. The decision traded a *loud, countable, bench-
diagnosable* failure for a *quieter but silent* one, in a body that can never be
opened, and then kept the now-inert diagnostic in its Consequences list as a
benefit.

This is the **third** honesty marker in this project found pointing backwards.
The first two are named in ADR 0001 itself (the "hold-margin violations" claim
and the "better drive over a 14 in chain" rationale) `[repo]`. This one was
created by the commit that corrected those two.

**It is unretrofittable in both directions.** The marker bits are wiring-only and
"cannot be added later" `[repo] key-layout.yaml, ADR 0001`; so is any loom-
resident replacement.

### The fix, which is free now and impossible after M8

Restore the diagnostic *inside* the tail topology. `WIRE-LOOM` already specifies
**two spare conductors in every ribbon** `[repo]`, and `key-layout.yaml` has
`spare_bits_free: 5` plus 6 marker bits `[repo]`.

**Per cluster, spend one spare conductor and one spare chain bit on a loom
sentinel:** tie that conductor to `GND` at the *far* (cluster) end, give it its
own `R-KEY-PU` / `R-KEY-SER` / `C-KEY` set at the carrier, and route it to a
register input. It is electrically identical to a permanently-pressed key, in
the same ribbon, in the same channel, at the same length.

- Reads high → **that ribbon's ground return or that conductor is open.**
- Reads high intermittently → **that ribbon is picking up enough to cross a
  threshold**, on a bit that is never legitimately anything but low.
- Firmware increments the same visible counter.

Cost: 4 conductors already in `WIRE-LOOM`, 4 of the 5 free bits (which
`key-layout.yaml` says must be pulled anyway), 12 more 0805s. That is the
minimum condition under which this decision could be downgraded from BROKEN to
CONDITIONAL.

---

## B2 — The retrofittability tiebreaker is inverted

ADR 0001 says the tiebreaker is decisive `[repo]`:

> **The whole argument is that one option's risk is retrofittable and the
> other's is not.** A fat loom is a nuisance you can see, measure and re-route
> on the bench.

**The first clause is false, and it is the sentence the decision rests on.**

ADR 0009's own "Things that are free now and impossible later" list `[repo]`:

> **Run two spare conductors in every internal loom.** The looms are hand-built,
> once, into a stack that cannot be reopened. … discovering you need one signal
> more after bonding **costs the instrument**.

A loom is not a bench item in this build. It is built once, into a stack that
is bonded at M8 and never opened. Both options' risks are unretrofittable. So
the tiebreaker collapses to *which risk is discoverable earlier*, and there the
answer is the opposite of the one taken:

| | Rejected (per-cluster) | Chosen (tail) |
|---|---|---|
| Unresolved risk | clock/latch signal integrity | **does the loom physically fit** |
| When discoverable | **E4** — logic analyser, 32-bit words, error counter, on a bench, before any plate is cut | **M4 CAD at best, M8 dry-assembly at worst** — after the ribbons are made, the carrier is built and the plate is cut |
| Fallback if it fails | **74HC165, drop-in, same SOIC-16** — already in `U-KEYS` `[repo]` | redesign `PCB-CARRIER` — the board this decision just made the most area-constrained in the project (B6) |
| Repo's own status | measured at E4, gated | `ROADMAP.md:196` "the only part of that decision **taken on faith**" `[repo]` |

The commit message concedes this in as many words: *"What it costs is physical
and is NOT settled … the one part of this decision taken on faith."*
`[repo] git show 7c68404` — and `WIRE-LOOM`'s note repeats it.

**The decision chose the option whose open question resolves at the irreversible
step, over the option whose open question resolves at a reversible one, on the
strength of an argument that says it did the reverse.**

---

## B3 — The decisive arithmetic, checked

ADR 0001, `key-layout.yaml`, `C-KEY`'s BOM note and the commit message all carry
the same two lines `[repo]`:

```
ΔV = 180 pC / 10 nF   = 18 mV    — nothing
ΔV = 180 pC / ~40 pF  = 4.5 V    — a false key press
```

with the premise *"A 12 V LED edge at ~120 V/µs through ~15 pF of loom
coupling"*.

### B3a — Is 15 pF right? Yes, and it is conservative

Two parallel round conductors, `C' = πε₀ε_r / arccosh(d/a)` `[calc]`, at 28 AWG
(a = 0.16 mm) over 300 mm:

| Geometry | ε_eff | C over 300 mm |
|---|---|---|
| Adjacent conductors in one ribbon, d = 1.27 mm | 1.0 | **3.0 pF** |
| Same, PVC-loaded | 2.0 | **6.0 pF** |
| 5 mm separation (ribbon to LED strip) | 1.6 | **3.2 pF** |
| 10 mm separation | 1.0 | **1.7 pF** |

`arccosh(1.27/0.16) = arccosh(7.94) = ln(7.94 + √(63.0−1)) = ln(15.81) = 2.761`;
`π × 8.854e−12 / 2.761 = 10.07 pF/m` × 0.3 m = 3.02 pF. `[calc]`

**15 pF is 2.5–9× the isolated two-conductor figure**, and the real number is
lower still, because `WIRE-LOOM` puts grounds in the ribbon at 1.27 mm while the
aggressor is several millimetres away — the victim's capacitance to *ground*
dominates its capacitance to the aggressor. So 15 pF is a conservative bound.
**No objection.** But note it is the *same* bound in both columns of the
decision's table, which is fine, and it is not where the error is.

### B3b — There is no 12 V edge in this design

`[repo] ADR 0014`: the strips are **WS2815, 12 V**, with **470–1000 µF of bulk
at each feed point** (`C-STRIP-BULK`, "bulk belongs at the load") and a
**~2 kHz PWM** current modulation. A rail held up by a millifarad does not
present a 12 V voltage step. What it presents is *current* modulation, which
couples inductively and through the ground return — a mechanism the ADR's
capacitive model does not describe and the RC does not fix.

The thing in the channel with fast edges is the **data line**, and ADR 0014
specifies exactly what drives it `[repo]`: a **74AHCT125 powered from 5 V**,
"so it outputs a clean 5 V edge", at 800 kHz.

**So the aggressor amplitude in this project's own design is 5 V, not 12 V.**
`Q = 15 pF × 5 V =` **75 pC**, not 180 pC — the ADR overstates injected charge by
**2.4×**. `[calc]`

The "~120 V/µs" is 12 V in 100 ns, which belongs to neither. An AHCT125 into a
strip data line is ~2–5 ns for 5 V, i.e. ~1000–2500 V/µs `[from memory]` —
**~10–20× faster**. The figure fuses the amplitude of the slow thing with an
invented slew for the fast thing. It is also decoration: `Q = C·ΔV` has no slew
term in it.

### B3c — The circuit model double-counts, and 4.5 V is above its own ceiling

`Q/C` assumes the entire charge computed from the full aggressor swing lands on
the victim while the coupling capacitor's own voltage is unchanged. The correct
lumped model for a step faster than every RC in the network is a **capacitive
divider**:

```
ΔV_victim = ΔV_agg · C_m / (C_m + C_victim)
```

`Q/C` is the limit of that as `C_victim ≫ C_m` — true for 10 nF, **badly false
for 40 pF**, which is the column the decision rests on. `[calc]`

| C_victim | Aggressor | ADR's `Q/C` | Correct divider |
|---|---|---|---|
| 10 nF (`C-KEY`) | 12 V | 18.0 mV | 17.97 mV — identical, model valid here |
| 10 nF (`C-KEY`) | **5 V (real)** | — | **7.5 mV** |
| 40 pF (bare wire) | 12 V | **4500 mV** | **3273 mV** |
| 40 pF (bare wire) | **5 V (real)** | — | **1364 mV** |

**A passive capacitive divider cannot deliver more than the aggressor's own
swing.** The published 4.5 V is 37 % above the ceiling of the mechanism it
claims, even granting the 12 V premise. `[calc]`

### B3d — What actually appears at the register pin, with the RC in place

`R-KEY-SER` and `C-KEY` sit at the carrier `[repo] BOM`, so a ns-scale edge
lands on the 40 pF loom conductor first, then redistributes through 100 Ω into
10 nF (τ = 100 Ω × 40 pF = 4 ns). `[calc]`

```
5 V aggressor:  wire steps 1.364 V for ~ns → 54.5 pC → 54.5 pC / 10.04 nF = 5.43 mV at the pin
12 V aggressor: wire steps 3.273 V for ~ns → 130.9 pC → 13.04 mV at the pin
```

So the filtered result is **5.4 mV, not 18 mV** — the ADR is conservative by
3.3×, in the safe direction. Against `V_IL` = 0.8 V at 3.3 V `[from memory]`
that is ~150× of margin. **The filter works. That part of the claim survives.**

### B3e — Energy, which is the question that reframes the whole thing

| | Energy |
|---|---|
| Into `C-KEY` at 5.4 mV | `½ × 10 nF × (5.4 mV)² =` **0.15 fJ** |
| Into `C-KEY` at the ADR's 18 mV | **1.6 pJ** |
| Into a bare 40 pF wire at 1.36 V | **37 pJ** |

All of it is negligible, and **that is the point**: the correct question is not
energy, and it is not charge either. It is whether a disturbance can hold a line
below `V_IL` **at the instant `SH/LD` samples it**.

Two consequences the decision never reaches:

1. **A balanced pulse train injects zero net charge.** Every rising edge on the
   WS2815 data line injects +75 pC and the matching falling edge injects −75 pC.
   Over any bit period the DC term is zero. **No amount of capacitive coupling,
   at any repetition rate, can hold a key line low.** A false press needs
   sustained DC, and capacitive coupling cannot supply it. So the failure the
   63-part network was specified to prevent is **not reachable by the stated
   mechanism at all** — with or without `C-KEY`.

2. **The real asymmetry is sampling aperture, not charge.** A DC switch line is
   examined once per 250 µs for a few nanoseconds; the odds of a 3 ns glitch
   landing in that window are ~10⁻⁵. A clock line has a **100 % aperture** —
   every glitch across threshold is an extra clock, immediately, and rotates all
   32 bits. `C-KEY` trades aperture (3 ns → ~100 µs of memory) for amplitude
   (÷250), and amplitude is what crosses a threshold. **That is a correct and
   sufficient argument for the tail topology. It is not the argument the ADR
   makes.**

**Net on B3:** the conclusion "DC lines can be filtered and clock lines cannot"
is right. The arithmetic offered as *"decisive"* — and repeated verbatim in four
places `[repo] ADR 0001, key-layout.yaml, bom.csv C-KEY, commit message` — is
wrong in its aggressor (2.4×), wrong in its model (1.38× at the point that
matters), produces a number physically impossible under its own mechanism, and
answers a question that the energy check shows is the wrong one. In a project
whose honesty markers have twice been found calibrated backwards, publishing
that in four places as *the deciding arithmetic* is itself the defect.

---

## B4 — It is 32–44 conductors, not "~23", and the grounding rule contradicts itself

### The rules disagree by 2×

- **ADR 0009, Consequences** `[repo]`: *"The key chain still needs **a ground
  return per signal** (ribbon with alternating grounds, or twisted pairs) — that
  requirement is independent of what else is in the channel, and **it is the one
  thing that makes this sharing safe**."*
- **ADR 0001, item 1** `[repo]`: *"**One ground per four signals** in each
  ribbon, which a standard ribbon gives for free by alternating."*
- **`WIRE-LOOM`** `[repo]`: *"each with **a ground every ~4** and TWO SPARE
  CONDUCTORS"*

ADR 0001's sentence is **internally contradictory**: alternating gives one ground
per **one** signal, not per four. And it relaxes, without argument, the exact
requirement ADR 0009 calls "the one thing that makes this sharing safe".

### The count `[calc]`, at 1.27 mm IDC pitch `[from memory]`

**Under the BOM rule (1 gnd per 4 + 2 spares):**

| Ribbon | sig | gnd | spare | cond | width |
|---|---|---|---|---|---|
| right_hand | 6 | 2 | 2 | 10 | 12.7 mm |
| left_hand | 5 | 2 | 2 | 9 | 11.4 mm |
| left_thumb | 4 | 1 | 2 | 7 | 8.9 mm |
| right_thumb | 3 | 1 | 2 | 6 | 7.6 mm |
| **Total** | 18 | 6 | 8 | **32** | **40.6 mm** |

**Under ADR 0009's mandatory rule (1 gnd per signal + 2 spares):** 14 + 12 + 10
+ 8 = **44 conductors, 55.9 mm of flat ribbon.**

**The published figure is "~23"**, in ADR 0001's comparison table, `WIRE-LOOM`,
the commit message and `ROADMAP.md:196` `[repo]`. It matches neither rule. It
appears to be 18 + ~3 + 2, i.e. **the spares counted once for the whole
instrument instead of per ribbon, and the grounds under-counted**.

**The number the M4 CAD check is written against is wrong by 1.4× to 1.9×**, and
55.9 mm of flat ribbon is **the entire external width of the instrument**
(57 mm, ADR 0009) `[repo]`.

### Does it fit? On area, yes. On everything else, no

`[calc]`, from ADR 0009's own stack: 57 mm external − 2 × 4 mm acrylic sides
= 49 mm internal; less ~16 mm of switch column on the centreline = **33 mm,
i.e. two channels of ~16.5 mm**. Less ~3 mm per side for the WS2815 strip and
the diffusion gap that ADR 0009 says "constrains the channel depth" `[repo]` →
**~13.5 mm of usable channel width per side.**

- 40.6 mm of ribbon folded into 13.5 mm = **3.0 layers**, ~3.8 mm tall in ~20 mm
  of cavity. **Area is not the binding constraint.** The brief's hypothesis that
  it physically will not fit is **not supported**; I could not break it there.

What *is* binding is that the channels are already fully committed:

1. **Both channels carry LED strips** `[repo] ADR 0014: "one run per side"`.
2. **One carries the ~400 mm breath tube** `[repo] ADR 0009: "The tube runs the
   length of the body in one of the side channels"`. At ~6 mm OD `[from
   memory]`, that channel has **~7.5 mm left** `[calc]` — under six conductors
   laid flat.
3. **One carries the 360 mm UART** to the display board `[repo] ADR 0013`.
4. **LED power** for both runs `[repo] ADR 0009`.
5. **The U-bolt** intrudes mid-span and everything crossing it must dodge it
   `[repo] ADR 0009`. Under the per-cluster loom ~10 conductors pass it; under
   this decision **16 of 32** (left_hand 9 + left_thumb 7) do.

**And the decision destroys the one free mitigation the research identified.**
`R10-keyscan-and-adc.md` §A-4 `[repo]`: *"put the key chain in the **opposite
side channel** from the LED runs"* — listed as free and unretrofittable. With
10 conductors that is trivially available. With 32–44 it is not: they cannot fit
beside the tube in one channel, so they must split across both, i.e. **alongside
LED runs on both sides, by construction.** The decision spent the cheapest
mitigation on the table to buy the filtering it says is decisive.

---

## B5 — The switch end: 36 flying leads, and a board the BOM no longer contains

### The BOM now has nothing for the switches to attach to

`git show 7c68404 -- hardware/bom.csv` deletes `[repo]`:

```
-PCB-CLUSTER,controller,2-layer PCB - key cluster board,,Identical satellite board:
 one 74LVC165 + switches + decoupling,"small, 1.6mm",4,open,,0001,…
```

Note the description: *"one 74LVC165 **+ switches** + decoupling"*. That board
was mounting the switches, not just the register. **Nothing replaced it.**
`grep -n "^PCB" hardware/bom.csv` returns exactly two rows: `PCB-CARRIER` and
`PCB-MODULE` `[repo]`. There is **no board in the BOM for 18 key switches.**

Against ADR 0002 `[repo]`, which requires one on *mechanical* grounds, entirely
independent of the electronics:

> 3. **The plate does not flex.** A thin plate spanning several keys is a
>    trampoline; it needs ribs, a backer, or **a PCB acting as stiffener**.
> … Hand-wired on laser-cut plates during ergonomic iteration…, **moving to PCB
> once the layout is locked**. … **Switches are soldered in the final build.**

### Which makes ADR 0001's comparison table a false dichotomy

| | ADR 0001's table `[repo]` | Reality |
|---|---|---|
| Registers at the tail | **Boards: 1** | 1 carrier **+ whatever ADR 0002's stiffener PCB turns out to be** |
| One per cluster | Boards: 5 | The **same** stiffener PCBs, four of them carrying one extra SOIC-16 and eight 0805s |

**The per-cluster option's marginal board cost is zero**, because ADR 0002
already requires PCBs under the keys. The table compares against a build that
does not exist in any other document, and the "1 vs 5" row — one of four rows in
the deciding table — is not a real difference.

### Hand operations, which the brief asked me to count `[calc]`

Each switch has two pins. In the tail topology each needs its own conductor
*and* a ground, and with grounds at one-per-four the ground pins of 3–6 switches
must be daisy-chained by hand along a 96–120 mm key run.

| | Tail (as decided) | Per-cluster, switches soldered into the stiffener PCB |
|---|---|---|
| Unsupported flying-lead joints onto 0.9 mm switch pins | **36** (18 signal + 18 ground) | **0** |
| Hand-made ground daisy jumpers | ~10 | 0 |
| Machine-defined plated-hole joints | 0 | 36 |
| Mass-terminated IDC crimps | 4 | 4 |
| **Unsupported hand joints total** | **~46** | **~4** |

**The decision multiplies unsupported, hand-made, one-off, unretrofittable
joints by roughly 9×**, and the ADR's table scores this row by counting *boards*
and calling 1 better than 5.

These joints are also the ones that fail from flexing. The instrument is played
standing, on a strap, swung by the player `[repo] ADR 0009`. A stiff ribbon
conductor soldered directly to a switch pin, unsupported, is the textbook
vibration-fatigue joint. ADR 0002 accepts a failed *switch* in a bonded body as
unlikely enough to design around `[repo]`; this decision inserts 36 joints that
are more likely to fail than the switch is, and no document analyses them.

---

## B6 — Carrier area: the commit added 41 % and did not change the board size

`PCB-CARRIER` reads `"~100 x 45mm, 1.6mm"` — **identical before and after the
commit** `[repo] git show 7c68404 -- hardware/bom.csv`. Only the description
changed, to add *"63 passives and 4 ICs of extra area"*. 100 × 45 = 4500 mm².

`[calc]`, from footprint estimates at the BOM's own package policy (0805,
SOIC-16, 2.54 mm THT, **hand-assembled**, `[repo] ADR 0013`):

| | Item | mm² |
|---|---|---|
| **added** | 63 × 0805 at ~10 mm² each incl. routing corridor | **630** |
| **added** | 4 × SOIC-16 courtyard (~10.3 × 10.0) | **412** |
| **added** | 4 × 100 nF `C-DECOUPLE-165` | **40** |
| **added** | 4 loom IDC shrouded headers (2×5, 2×5, 2×4, 2×3) | **748** |
| | *subtotal added by this decision* | **1830 = 41 % of the board** |
| pre | ESP32-S3-Matrix socket footprint | ~500 |
| pre | 22 mm matrix cutout — **dead copper, must sit under that board** | 484 |
| pre | MCP3202 + REF5050 + OPA2197 (3 × SOIC-8) | 90 |
| pre | 74AHCT125 SOIC-14 | 60 |
| pre | MPXV4006DP case 1351-01 THT + tube-barb clearance | 180 |
| pre | 2 × R-78E5.0 SIP-3 | 196 |
| pre | ~15 other passives, `C-AA-ADC`, `R-ADCDIV`, bulk | 150 |
| pre | `HDR-SERVICE` 2×5 + cover clearance | 100 |
| pre | umbilical entry, `D-REVSHUNT`, backing-plate mounting | 120 |
| | **TOTAL** | **3710 = 82 % coverage** |

At **82 % component coverage on a two-layer board**, one of whose layers has to
be the ground pour that eighteen 10 kΩ-impedance nets return through, with a
22 mm hole punched in it — **this does not route.** Hand-assembled two-layer
boards are comfortable to about 40–50 % coverage `[from memory]`. The specific
per-part estimates are mine and are arguable; the conclusion is not sensitive to
them, because **the added 1830 mm² alone is 41 % of the stated board**, and the
stated board did not grow.

**And it is worse than that, because of an unresolved contradiction the decision
inherited.** `HDR-DEV` `[repo]`:

> Sockets for **both dev boards on the carrier**… 2 strips for the
> ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED

against ADR 0013 and ADR 0009, which put the display board in the 60 mm display
band at the **top** of the instrument, 360 mm away, reached by UART `[repo]`.
`U-DISP` is 60 × 25.5 mm = **1530 mm²** `[repo]`. If `HDR-DEV` is right the
carrier is at **116 % coverage** `[calc]` and the decision is arithmetically
impossible; if ADR 0013 is right, `HDR-DEV` is wrong and should be fixed. Either
way this is the second live board-partitioning contradiction of exactly the kind
this commit was written to resolve — and the commit did not look for it.

Finally, ADR 0013's justification for the whole dev-board-on-a-passive-carrier
approach was `[repo]`: *"Nothing on that board is fast, nothing is RF, and
nothing needs more than two layers. **It can be assembled by hand.**"* The
decision added ~130 hand-soldered 0805 terminations and 64 SOIC-16 pins to that
board. The premise is weaker than when it was written, and nothing recorded it.

---

## B7 — The RC filter: checked against every rule, and it survives

This is the one attack line the brief suggested that I could not land. `[calc]`

| Check | Result |
|---|---|
| Release: 10 kΩ × 10 nF | τ = 100 µs; 0 → `V_IH` 2.0 V of 3.3 V = **93.2 µs** — ADR's "~93 µs" is correct |
| Press: 100 Ω × 10 nF | τ = 1.0 µs; 3.3 → `V_IL` 0.8 V = **1.42 µs** — "press stays instant at ~1 µs" is correct |
| Against the 250 µs scan period | release filter = **37 % of one period**; never delays a release by more than one extra sample |
| Against "fire on the first closed sample" | press path is 1.42 µs against a 250 µs period — **176× of margin.** The filter does not touch the attack. |
| Against the two-agreeing-samples rule (ADR 0001) | 250–500 µs, set by the loop rate, not by the RC. Consistent with ZMK's 1 ms press-debounce recommendation `[repo] R10 §A2`. |
| Against bounce | a 50 µs open-interval mid-bounce recharges the node only to **1.30 V** (reads still-closed); 100 µs reaches 2.09 V; 200 µs reaches 2.85 V. The hardware filter is **asymmetric in the same direction as the firmware rule** — it suppresses press-bounce re-opens and does not slow the initial close. |

The hardware and firmware asymmetries are aligned, the values are conservative
(`R10 §A12`: 10 kΩ is 7× stiffer than CircuitPython's reference 68 kΩ `[repo]`),
and the loom's added series resistance (28 AWG, 265 mm ≈ 0.06 Ω `[calc]`) and
inductance (~0.2 µH, Q ≈ 0.045 into 100 Ω `[calc]`) change nothing.

**"Press is instant" is preserved. This part of the decision is correct and well
specified.** It is also the *only* part of the arithmetic in ADR 0001 that
reproduces.

---

## B8 — The failure mode that only appears once the body is bonded

Not coupling. **Leakage.**

Three repo facts that no document puts together `[repo]`:

- `MECH-COAT`: *"Conformal coating for the **in-body boards**… Breathed into for
  hours behind 18 unsealed switch cutouts, interior 10–20 K above ambient."*
- ADR 0009: the cavity is sealed oak and acrylic, the player breathes into it,
  and it runs 10–20 K hot.
- `R-KEY-PU`: 10 kΩ to 3V3, now **at the carrier**, 265 mm from the contact.

**A loom is not a board and cannot be conformal-coated.** The decision put 18 ×
265 mm of uncoated high-impedance conductor, 36 uncoated flux-residue solder
joints and 18 uncoated open switch contacts into a humid, warm, sealed cavity —
and moved the only coated part of the network to the far end.

What a leakage path does across an open switch, with a 10 kΩ pull-up `[calc]`:

| Leakage | Node | Reads as |
|---|---|---|
| 100 kΩ | 3.00 V | released |
| 20 kΩ | 2.20 V | released |
| **10 kΩ** | **1.65 V** | **forbidden band** — indeterminate |
| 5 kΩ | 1.10 V | forbidden band |
| **3 kΩ** | **0.76 V** | **FALSE PRESS — and the debounce fires on the first closed sample** |

3 kΩ of condensate-and-flux across a switch gap or between two adjacent ribbon
conductors at 1.27 mm pitch is entirely ordinary. Note it does not need to reach
0.76 V to hurt: anything between ~5 kΩ and ~20 kΩ parks a CMOS input in the
forbidden band, where it is a **metastable input whose state is set by noise** —
which is the one condition under which the coupling the ADR designed against
actually *does* become decisive, at a thousandth of the amplitude.

**This appears only after bonding, only when warm, and only after the player has
been breathing into it for an hour.** Bench testing in a dry room at E4 will
never show it, and M8's two-hour play test is pre-bond and therefore not in the
sealed condition either `[repo] ROADMAP M8`.

**The per-cluster topology is materially better here** and for a structural
reason: its high-impedance node is millimetres of *coated PCB* next to the
switch, and its loom carries low-impedance driven signals that leakage does not
move.

**The free fix, if the tail topology is kept:** **drop `R-KEY-PU` to 2.2 kΩ** and
`C-KEY` to 47 nF (τ = 103 µs, unchanged) `[calc]`. That moves the false-press
threshold from 3 kΩ of leakage to below 1 kΩ, at a cost of 18 × 1.5 mA = 27 mA
of 3V3 — affordable against the R-78E5.0's 1 A `[repo]`. 10 kΩ was chosen for a
topology where the node sat on a coated board centimetres from its switch; the
decision changed that topology and **did not revisit the value.**

---

## B9 — Is there a third option? Yes, and ADR 0001 names it and then walks past it

### The decision was taken against a strawman it identified as a strawman, in the same document

ADR 0001 writes `[repo]`:

> **74HC165 at 3.3 V has edges slow enough not to need termination at all, and
> would have been the lower-risk choice on those grounds.**

`R10 §A-5` supplies the arithmetic `[repo]`: critical length ≈ `t_r·v/2`; at
~5 ns/m a 2 ns LVC edge gives ~200 mm and a 15–25 ns HC edge gives
**1.5–2.5 m**. A 265 mm loom is a transmission line for LVC and a **lumped
load** for HC.

Every hazard the decision cites to reject the per-cluster loom — termination,
reflections, the incident half-step at intermediate receivers, double-clocking —
**is definitionally absent with 74HC165**, on the same SOIC-16 footprint that
`U-KEYS` already names as a drop-in `[repo]`.

**ADR 0001 compared (LVC, unterminated, multidrop, no Schmitt) against (tail
carrier) and picked the tail. It never compared (HC per cluster) against (tail
carrier).** It chose to move four ICs 265 mm rather than change one letter in a
part number it had already decided was the lower-risk choice.

### Four more, all from the research this ADR cites, none evaluated

| Option | What it removes | Cost | In ADR 0001? |
|---|---|---|---|
| **74HC165** instead of LVC | the entire transmission-line class, by edge rate | **0** — same footprint, already in `U-KEYS` | named, then not taken |
| **Schmitt receiver on `CLK`/`SH/LD`** at each cluster (74HC14 / SN74LVC1G17, ~0.5–1 V hysteresis `[from memory]`) | glitch-across-threshold, i.e. the #1 mechanism in `R10 §A-4` | 4 tiny parts | **absent.** `R10` calls it *"the industrial answer to a clock crossing a noisy cable"* `[repo]` |
| **74x166** (synchronous parallel load) | **the async `SH/LD` glitch** — ADR 0001's own named top-two hazard — at the part level `[repo] R10 §A9` | same footprint class | **absent** |
| **74x589 / 74x597** (input storage latch; 589 adds a **three-state output**) | the `SH/LD` hazard *and* the always-driven-`QH` problem that costs a whole SPI host and 2 GPIO. `R10 §A9`: the keyboard community's documented answer `[repo]` | same | **absent** |
| **300–500 Ω on each WS2815 data line** at the 74AHCT125 — Adafruit's standard practice `[repo] R10 §A10` | **damps the aggressor**, protecting *both* topologies | **2 resistors** | **still no BOM row** |

**The proportionality is the finding.** The project's answer to LED coupling is
**63 passives and 4 relocated ICs on 18 victims**. The documented answer is
**2 resistors on 2 aggressors**, and `R10 §A10` flagged it as *"the cheapest,
highest-leverage item on this list"* the day before this commit. It is still
absent from `hardware/bom.csv` `[repo]`.

### The option that dominates both

**74HC165 per cluster, on the stiffener PCB that ADR 0002 requires anyway**, with:
a Schmitt buffer on `CLK`/`SH/LD` at each board; `CLK INH` tied low; 100 nF
local; per-signal grounds per ADR 0009's mandatory rule; **300 Ω on each LED
data line**; and the marker bits reading back through a word that actually
crosses the loom.

| | Tail (decided) | HC-per-cluster + Schmitt + damped aggressor |
|---|---|---|
| Conductors down the body | **32–44** | ~10–14 |
| Unsupported hand joints | **~46** | ~4 |
| Carrier area consumed | **+1830 mm² (41 %)** | +0 |
| Transmission-line hazards | none | **none** — HC is lumped at 265 mm `[repo] R10 §A-5` |
| Async `SH/LD` glitch | removed | removed by Schmitt (or by 74x166) |
| **Loom fault visible to the error counter** | **No** | **Yes** |
| Can the key run use the non-LED channel? | **No** — too wide | Yes |
| Marginal BOM cost | — | 4 Schmitt buffers, 2 resistors |
| Open risk resolves at | **M4/M8, irreversible** | **E4, on a bench, with an HC→LVC swap available** |

### The two I checked and rejected

- **I²C expander (PCA9555/MCP23017)** — 4–5 conductors for the whole instrument,
  but open-drain rise times are RC-set and slow, a hung bus is a *total* key
  failure rather than a per-key one, and it does nothing about the aggressor.
  Not clearly better; I would not build a bonded instrument on it.
- **Capacitive sensing (MPR121)** — this is the project's **only real in-house
  prior art**: `R10 §A4` found the 2021 `Open-Woodwind-Project` used two MPR121s
  on I²C and *no shift register at all* `[repo, quoting src/owp/owp.ino]`. Four
  conductors for 18 keys. Correctly ruled out by ADR 0002's choice of mechanical
  switches for feel — but worth recording that of every key-sensing topology
  available, this decision selected **the single most conductor-hungry one**,
  and the author has never built the topology it selected.
- **A matrix** — 18 keys as 4 × 5 is ~9 conductors plus 18 diodes, but the row
  strobes are clocked, so it inherits the hazard the decision was avoiding.
  Correctly rejected by ADR 0001.

---

## What would have had to be true for this to survive

Stated plainly, since the brief asks for it. **The topology is defensible; the
decision as written is not.** It would have survived if:

1. **The loom carried a sentinel** so the error counter still watched it (B1).
   It does not, and the ROADMAP claims it does.
2. **The tiebreaker had been "which risk resolves earlier"** rather than "which
   is retrofittable" (B2). On the real criterion it picks the other option.
3. **The arithmetic had been right** (B3). Right conclusion, wrong aggressor,
   wrong model, impossible number, wrong question — published in four places as
   *decisive*.
4. **The conductor count had been 32–44** in the M4 gate instead of 23, and the
   grounding rule had been one rule instead of two that differ by 2× (B4).
5. **A board had replaced `PCB-CLUSTER`** for the switches to solder into (B5).
6. **`PCB-CARRIER` had grown** when 41 % more area landed on it (B6).
7. **The best per-cluster design had been the comparand** — HC edges, a Schmitt
   receiver, and 300 Ω on the aggressor — rather than the LVC strawman ADR 0001
   had itself just finished demolishing (B9).

## Minimum salvage, if the topology is kept

All five are free now and unavailable after M8. In priority order:

1. **Loom sentinels** — one spare conductor and one spare chain bit per ribbon,
   grounded at the far end, its own RC set at the carrier, feeding the existing
   error counter (B1). *Without this, the instrument has no way to know its own
   looms are good, and `ROADMAP.md:195` should be corrected today either way.*
2. **`R-KEY-PU` → 2.2 kΩ, `C-KEY` → 47 nF** — same 100 µs, 3× the leakage
   margin in a cavity that is breathed into (B8).
3. **Add the switch PCB back to the BOM**, per ADR 0002's stiffener requirement
   (B5). It also eliminates the 36 flying leads, and it makes the per-cluster
   fallback a BOM change rather than a redesign.
4. **300–500 Ω on each WS2815 data line** at the 74AHCT125 (B9). Two resistors.
   Outstanding since `R10 §A10`.
5. **Re-cost `PCB-CARRIER`** against 3710 mm² of content, and resolve
   `HDR-DEV`'s claim that the display board sockets onto it (B6).

And correct, in all four places that carry it, the arithmetic in B3 — because a
project that has now been caught three times with an honesty marker pointing
backwards cannot afford a number labelled *"the arithmetic, which is decisive"*
that is 3.3× high and above the ceiling of its own mechanism.
