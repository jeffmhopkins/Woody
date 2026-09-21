# X1 — Shared nodes, rails and parts across the five module pages

**Scope.** Not any one page. Every node, rail, part or signal that appears on
more than one page, or that one page creates and another consumes. Indexed by
node. Single-page faults are left to the single-page reviewers except where a
second page depends on them.

**Evidence markers.** `[repo]` = read in this repository, file and line given.
`[calc]` = arithmetic shown in full. `[from memory]` = general engineering
knowledge, unverified here. Vendor domains were proxy-blocked, so no datasheet
figure is asserted; where one is needed the gap is named as a gap and left as a
gap.

**State reviewed.** Commit `b9beb48` plus uncommitted working-tree edits. The
tree changed *during* this review — `pitch-stage.md`, `mod-channels.md`,
`bom.csv`, `ROADMAP.md`, `firmware/README.md` and three ADRs were all edited
while it was being written. Six findings were fixed under it; they are recorded
at the end under "Fixed mid-review" rather than deleted, because two of the
fixes introduced new cross-page problems and one of them is the most important
finding on this page. Everything in the main body was re-verified against the
current working tree after those edits landed.

**Sources read in full:** the five pages in `hardware/module/`, `hardware/bom.csv`,
ADRs 0003/0004/0005/0006/0014, `ROADMAP.md`, `firmware/README.md`,
`docs/review/2026-09-20-cold-review/B7-grounding.md`.

---

## Summary

Ten defects live only in the gaps between pages. In order of cost to fix later:

| # | Node | Defect | Severity |
|---|---|---|---|
| 1 | `VREFOUT` | It is a **register-controlled output, not a rail**, and pitch's reference treats it as a rail. At power-on pitch sits at 0 V, not subsonic — and ADR 0006 claims the opposite | **Showstopper** |
| 2 | `AGND` | Three pages hang returns on a conductor two ADRs say must carry nothing | **Showstopper** |
| 3 | LM311 rail | `power-entry.md` puts the comparator on 5.21 V; that re-creates the exact fault the LM393 was rejected for | **Showstopper** |
| 4 | `CS` / watchdog | The watchdog is retriggered by the one thing that keeps running during the failure its own page calls the worst one | **Major** |
| 5 | Bus +5 V | Four documents still say "only the buffer" is on it after two more loads were added | **Major** |
| 6 | `TRIM-BREATH-ZERO`, `R1b` | The BOM moved the trim to the 5.21 V rail this afternoon and the page still draws `VREFOUT`; the page then changed the range and added `R1b`, and the BOM has neither | **Major** |
| 7 | `DVDD` | The DAC's digital supply appears in one BOM cell and nowhere else, yet the level-shifter argument depends on it | **Major (gap)** |
| 8 | Output jacks | Six outputs, five clamps drawn, two more BAV99s drawn and not bought; reconstruction corners differ 33× with no stated rule | **Major** |
| 9 | `TRIM-OFFSET` | Pitch's offset trim can only move the pitch sharp — a divider cannot exceed its source | **Moderate** |
| 10 | OPA2197 halves | Pages draw 9, BOM enumerates 11, packages buy 12. Three numbers | **Minor (cost)** |

Eight shared assumptions checked out sound and are recorded in one line each.

---

## Node `VREFOUT` and its buffered/trimmed derivative

### Who drives it

The DAC8568's internal reference, grade C, reference gain 2, so
`VREFOUT = 2.500 V` and full scale `= 5.000 V` `[repo: hardware/bom.csv:12]`.
Full scale is set by the reference and not by `AVDD`
`[repo: ROADMAP.md:189; docs/decisions/0005-power-architecture.md:132-135]`.

### Defect 1 (showstopper) — `VREFOUT` is not a rail, and pitch's reference treats it as one

Four documents agree that the internal reference is a **register**:

> "Internal ref **DISABLED by default**, enable at boot" `[repo: hardware/bom.csv:12]`

> "the internal reference is disabled by default and needs an explicit enable
> write at boot … It also means **the outputs sit at 0 V from rack power-on
> until firmware enables the reference**"
> `[repo: docs/decisions/0006-cv-channel-allocation.md:163-168]`

> "a DAC8568 frame carries the software reset, the clear-code register and **the
> internal-reference enable** — so a mis-framed word is a **sticky** failure that
> the 4 kHz refresh does not clear"
> `[repo: hardware/module/digital-and-supervision.md:83-86]`

> "the same shape of bug is latent in every other register the DAC holds that
> firmware writes once: **the internal-reference enable**, and the clear-code
> register itself" `[repo: firmware/README.md:59-62]`

`hardware/bom.csv:108` used this argument, this afternoon, to move
`TRIM-BREATH-ZERO` off `VREFOUT` and onto the LM317 rail:

> "**FROM THE LM317'S 5.21V, NOT VREFOUT.** VREFOUT is the DAC's internal
> reference, which is DISABLED at power-on until firmware writes an enable — so
> deriving the breath zero from it would make the analog breath path depend on a
> DAC register"

**The identical argument applies to pitch, and nobody has applied it.**
`pitch-stage.md:14` still builds pitch's `V_ref` from `VREFOUT` through
`TRIM-OFFSET` and a follower. Work out the power-on state:

```
Vout = Vdac·(1 + k) − V_ref·k        k = 1                [repo: pitch-stage.md:57,71]

reference ENABLED, zero scale:   Vout = 0 − 2.500 = −2.500 V
reference DISABLED (power-on):   VREFOUT = 0 → V_ref = 0
                                 Vout = 0 − 0      =  0.000 V
```
`[calc]`

ADR 0006's power-on table says:

| Output | At rack power-on, before firmware writes | Why that is right |
|---|---|---|
| **Pitch** | **Bottom of its range, below −2 V** | **Subsonic. A VCO there is inaudible** |

`[repo: docs/decisions/0006-cv-channel-allocation.md:154-158]`

and then, twelve lines later, states the mechanism that breaks it and calls it
corroboration:

> "It also means the outputs sit at 0 V from rack power-on until firmware
> enables the reference, **which happens to reinforce the table above**."
> `[repo: docs/decisions/0006-cv-channel-allocation.md:167-168]`

**It does not reinforce it. It contradicts it.** Pitch's safe power-on state is
"below −2 V, subsonic" *only while the reference is enabled*. Before the enable
write — which is the window the table is explicitly about — pitch's jack sits at
**0 V**, which on a 1 V/oct input is not subsonic. It is a note in the middle of
the range, sounding, from the moment the rack is switched on until an instrument
two metres away boots and writes a register. If the instrument is not plugged
in, it sounds indefinitely.

This is the same class of defect as the four found earlier in this project —
a safe-state argument that holds for the DAC channels and silently fails for the
one output whose reference is not a DAC channel. It is invisible on every page
individually: `pitch-stage.md` never mentions the reference's power-on state,
ADR 0006's table never mentions pitch's topology, and the enable-register trap
is documented on three other pages.

**The mod channels are safe** and for a reason worth recording: their reference
*is* a DAC channel, so both terms vanish together whether the reference is
enabled or not — `4 × (0 − 0) = 0` `[calc]`, matching ADR 0006:156. **This is
the second time the "put the offset on a DAC channel" decision has paid for
itself**, and the first time was `CLR` `[repo: mod-channels.md:137-159]`.

**Fixes, in preference order.** (a) Enable the reference from hardware if the
part allows a pin-strap — **unknown, datasheet gap**. (b) Accept 0 V at power-on
and correct ADR 0006:154-168 to say so, noting that 0 V is a sounding note and
deciding whether that is acceptable. (c) Derive pitch's `V_ref` from the LM317
rail, as `TRIM-BREATH-ZERO` now does — **but this costs the ratiometric
argument** at `pitch-stage.md:99-119`, which is the best argument on that page
and converts reference drift from an offset error into a gain error. Do not take
(c) without reading that section first.

Whichever is chosen, **`pitch-stage.md` must state the power-on behaviour of its
own reference.** It currently does not mention it at all.

### Defect 4 (major) — the watchdog cannot see the failure its own page names

Following the same register across two pages:

- `digital-and-supervision.md:83-86` names a mis-framed `CS` word as a **sticky**
  failure that can hit the internal-reference enable and that "the 4 kHz refresh
  does not clear".
- The frame watchdog on the same page is **retriggered from the buffered,
  DAC-side `CS`** `[repo: digital-and-supervision.md:130-132]`.

**SPI traffic continues perfectly well while the reference is off.** `CS`
toggles at 4 kHz, the '123 is retriggered, `CLR` is never asserted, the LM311
still reports the instrument present, the panel LED stays lit — and every DAC
output is at or near zero because the reference that scales them is disabled.
The watchdog detects *absence of traffic*. The failure the page calls the worst
one is a *corruption of traffic*, and the two are orthogonal.

This is not an argument against the watchdog, which correctly solves the problem
it was built for `[repo: digital-and-supervision.md:9-14]`. It is an argument
that **the module's supervision has a named, documented blind spot and no page
says so.** The only mitigation in the design lives in `firmware/README.md:63-66`
— "refreshing the reference-enable and clear-code registers periodically" — i.e.
inside the processor the watchdog exists because nobody can trust.

**Add one line to `digital-and-supervision.md`**: the watchdog covers loss of
traffic, not corruption of traffic; the reference-enable and clear-code registers
are covered only by firmware's refresh discipline, and that is a deliberate
limit, not an oversight. It costs a sentence now and is very expensive to
rediscover at E11.

### Defect 6 (major) — the breath page and the BOM now disagree about where `TRIM-BREATH-ZERO` comes from

| Source | Says |
|---|---|
| `hardware/module/breath-receive-stage.md:53-54` | "`REF ◄── ½ OPA2197 ◄─[TRIM-BREATH-ZERO]` / buffered **from VREFOUT**" |
| `hardware/bom.csv:108` | "10k multiturn cermet + divider **from the LM317 5.21V rail**" … "**FROM THE LM317'S 5.21V, NOT VREFOUT**" |

The BOM is right and its reasoning is the same as defect 1's. **The breath page's
drawing is now wrong**, and it is the drawing a builder reads. Redraw line 54.

**And the page moved again while this was being written**, in a way that makes
the same row disagree twice more:

| | `breath-receive-stage.md` (current) | `hardware/bom.csv:108` (current) |
|---|---|---|
| Source | **`VREFOUT`** `[:56]` | **LM317 5.21 V** |
| Range | **0 → +1.0 V** `[:89,152]` | **0 to ~+0.6 V** |

The page's new range is **right, and for a good reason**: the sensor's
zero-pressure pedestal is a spec band, 0.152–0.378 V, needing `REF` anywhere
from 0.332 V to 0.826 V, so a 0.6 V trimmer leaves a sensor at the top of its
own datasheet band un-nullable `[repo: breath-receive-stage.md:86-93]`. **The
BOM row still carries the 0.6 V figure the page just retired**, in the same cell
that was edited this afternoon to change the source rail. Whoever fixes the
source must fix the range in the same edit.

Two consequences follow that nobody has written down yet:

- **The 5.21 V rail gains a new load.** With a 10 kΩ pot and a top resistor
  sized for a 0…1.0 V range from 5.21 V, the top resistor is
  `10 kΩ × (5.21 − 1.0)/1.0 = 42.1 kΩ` `[calc]` and the divider draws
  `5.21 / 52.1 kΩ = 100 µA` `[calc]` — small, but it is on the rail whose budget
  is computed in the LM317 section below, and it is not in that budget.
- **Breath's zero now tracks the LM317 rather than the DAC reference.** The
  LM317's output is explicitly *selected on the bench* and is the loosest voltage
  in the module `[repo: hardware/bom.csv:38-39: "TOLERANCE IS A BENCH TASK…
  worst case spans 0.66V"]`. That is acceptable — the trimmer nulls whatever it
  is — but the rail's **tempco** now appears directly in the breath zero, where
  previously it would have been the DAC reference's. `breath-receive-stage.md:211-214`
  gives a thermal-drift figure ("~20 mV in 10 V over a full warm-up") derived
  from the *sensor's* tempco only, and explicitly flags it unverified. That figure
  now needs an LM317 term added to it. **One line on the breath page.**

### Defect 6b — `R1b` is drawn and not bought

The breath page added a series resistor to the **`AGND` leg** at the instrument
end during this review — "`analog star ──[R1b 1k]──── AGND (pin 2)`"
`[repo: breath-receive-stage.md:28]`, with its own component row: "**`R1b`** |
1 kΩ 1 %, **1206** | **Its twin in the `AGND` leg.** Free, and it is what keeps
CMRR from collapsing" `[repo: breath-receive-stage.md:146]`. The reasoning is
right — an unbalanced source impedance across an in-amp's two legs is a CMRR
term — and it is a change to a **shared** node, the umbilical pair.

The BOM has not followed it, in two ways:

> `R-SER-BREATH-INST` … `0805` … qty **1** … "**R1** in
> `hardware/module/breath-receive-stage.md`"  `[repo: hardware/bom.csv:66]`

- **Quantity is 1; the page now draws 2.**
- **Package is 0805 in the BOM and 1206 on the page.** (1206 is the better call
  — it matches `R-OUT-PROT`'s uprating logic at `hardware/bom.csv:42` — but the
  two documents must say the same thing.)

Note also that `R1b` sits in `AGND`, the conductor ADR 0004:515-517 says
"terminates at the in-amp's IN+ and at the two 1 MΩ bias resistors, **and that
is all it does**". A 1 kΩ series element is a fourth thing. It is clearly
correct here and the rule should be widened to permit it — but the rule is
quoted verbatim on `power-entry.md:161` and in two ADRs, and it now has three
documented exceptions and no amended wording. See the `AGND` section.

### Defect 9 (moderate) — pitch's offset trim is one-sided, downward only

`pitch-stage.md:14` draws `VREFOUT ──[TRIM-OFFSET 10k]──┬── ½ OPA2197 follower`
with "+ range resistors"; `pitch-stage.md:131` says "10 kΩ multiturn cermet +
range resistors … **Before** the buffer, so it scales `V_ref`". The intended
authority is given as:

> "Range ~50mV on a 2.5V reference is ~60 cents of offset" `[repo: hardware/bom.csv:106]`

**A resistive divider cannot exceed its source.** The source is `VREFOUT` =
2.500 V and the required nominal is 2.500 V `[repo: pitch-stage.md:58,128]`, so
the achievable range is `(0, 2.500] V` `[calc]` — the trim can only *reduce*
`V_ref`, which only makes the intercept less negative, which only moves the
instrument **sharp**. It cannot correct a build that lands flat.

This is the identical error the same page catches, correctly, on its other
trimmer two rows above:

> "**0 → +2 % of ratio, one-sided** — a series trimmer can only add"
> `[repo: pitch-stage.md:130]`

**Fix:** give the "follower" a non-inverting gain of ~1.02 with the trim divider
in its feedback path, so 2.500 V sits mid-travel and the trim is two-sided. This
keeps the ratiometric property intact (the gain is a fixed resistor ratio, so
`V_ref` still scales with `VREFOUT`) and costs two resistors. Feeding the trim
divider from 5.21 V instead would also work and would forfeit the ratiometric
argument — second choice.

### Defect — the range-setting resistors have no BOM row

`pitch-stage.md:14,131` says "+ range resistors" and nowhere gives values.
`TRIM-OFFSET` in the BOM is the trimmer alone `[repo: hardware/bom.csv:106]`;
`TRIM-BREATH-ZERO` says "+ divider" with no values `[repo: hardware/bom.csv:108]`.
**Two divider networks, four to six resistors, zero part numbers.** They are the
parts that set both trims' authority — which defect 9 shows is currently wrong on
one of them, and which defect 6 has just changed the source voltage of on the
other.

### The trims do not interact — one line, and it is the good news

`TRIM-BREATH-ZERO` no longer touches `VREFOUT` at all `[repo: hardware/bom.csv:108]`,
and never tapped pitch's *buffered* node even before that change
`[repo: breath-receive-stage.md:53-54]`. **Trimming pitch's offset does not move
breath's zero, and it never did.** The two commissioning procedures
`[repo: pitch-stage.md:200-205; breath-receive-stage.md:199-209]` are correctly
independent.

### But one proposal would break that, and it is still on the page

`breath-receive-stage.md:233-235` still says of the downstream stage:

> "its **offset reference (the buffered `VREFOUT` created for pitch is the
> obvious node)** … are E10 work"

By defect 1's argument this is now doubly wrong: it couples breath's panel
offset to pitch's calibration trim, *and* it puts an analog path back on a DAC
register that `hardware/bom.csv:108` just removed it from. **Strike the
parenthetical and name the 5.21 V rail instead**, before E10 takes the "obvious
node" at its word.

One further constraint that falls out of reading two pages together, and is on
neither: the downstream stage is an **inverting** summer
`[repo: breath-receive-stage.md:60-63,88-90]`, so a **positive** offset
reference can only push the jack's rest point **down**. There is no negative
reference anywhere on the module. **The panel OFFSET knob is therefore one-sided
as currently conceived**, which contradicts "Panel OFFSET for where you want the
jack to rest" `[repo: breath-receive-stage.md:208]`. E10 work, but the constraint
belongs on the page now.

### Remaining load on `VREFOUT`

After the `TRIM-BREATH-ZERO` move, exactly one load remains: `TRIM-OFFSET`,
10 kΩ across the reference, `2.5 / 10 kΩ = 250 µA` `[calc]`. Whether the
DAC8568's `VREFOUT` pin may source that is **unverified — `ti.com` unreachable**.
It is a smaller question than it was this morning, but it is still the pin that
sets both the DAC's full scale and pitch's intercept, so it should be confirmed
before layout.

**A rule worth writing down while only one trimmer is left:** any trimmer on
`VREFOUT` must be a potentiometer wired across a fixed divider, never a rheostat.
A pot across a source draws constant current regardless of wiper position; a
rheostat modulates the load, which modulates `VREFOUT`, which modulates the DAC's
full scale and therefore pitch. `TRIM-OFFSET` is specified "across `VREFOUT`"
`[repo: pitch-stage.md:131 via hardware/bom.csv:106]` and is therefore correct as
worded — but the wording is an accident of phrasing, not a stated rule, and the
next trimmer will not inherit it.

---

## Node `AGND`

### Who creates it

The instrument. `AGND` is umbilical pin 2, leaving the analog ground pour on the
bottom cluster board and running 2 m up the Cat5
`[repo: docs/decisions/0003-breath-sensing-path.md:641-646]`.

### What the ADRs say it may do

Unambiguous, and stated twice:

> "`AGND`, from the etherCON | **Nothing.** It is an in-amp input, not a ground
> (ADR 0003)" `[repo: docs/decisions/0004-cv-interface-module.md:496]`

> "**`AGND` is not in this list.** It terminates at the in-amp's IN+ and at the
> two 1 MΩ bias resistors, and that is all it does. Anything that makes it a
> return path breaks the reason a 2 m analog run works at all."
> `[repo: docs/decisions/0004-cv-interface-module.md:515-517]`

`power-entry.md:161` restates it correctly in prose: "`AGND` is not a ground at
all — it is an in-amp input (ADR 0003)".

### Who consumes it, page by page

| Page | Use | Legal under ADR 0004? |
|---|---|---|
| `breath-receive-stage.md:27,36` | umbilical `AGND` → R3 10 kΩ → INA828 IN+ | **Yes** — the defined termination |
| `breath-receive-stage.md:44-46` | R4, R5 1 MΩ to **`AGND(module)`** | **Yes** — named explicitly at ADR 0004:516 |
| `breath-receive-stage.md:38,42` | 2 × `C_cm` 1.5 nF to **`AGND(module)`** | Yes in substance |
| `power-entry.md:15-22` | C1 47 µF, C2 47 µF **and the LM317 output cap** return to a node drawn as `AGND` | **No** |
| `mod-channels.md:37` | `C-FILT-MOD` 82 nF × 4 to `AGND` | **No** |
| `digital-and-supervision.md:41-43` | `R-CLR-PD` 10 kΩ to `AGND` | **No** |
| `digital-and-supervision.md:108-113` | proposed presence threshold "against `AGND`" | Conditional — below |

### Defect 2 (showstopper)

**`breath-receive-stage.md` is the only page that distinguishes `AGND(module)`
from the umbilical `AGND` conductor.** It writes the qualifier at lines 38, 42
and 46, against the bare `AGND (pin 2)` at line 27. The other three pages write
bare `AGND` and mean, by context, the module analog return. **No page, ADR or
BOM row states whether these are one net or two.** On a netlist they are one net
by name, and these pages will become a netlist.

If they are one net, three consequences follow, none acknowledged:

1. **The module's analog bulk capacitance returns down the sense conductor.**
   `power-entry.md:15-22` draws C1 (47 µF, module analog +12 V) and C2 (47 µF,
   the **umbilical** +12 V branch) both returning to `AGND`. C2's return is the
   inrush path for 2.2 mF of instrument bulk `[repo: power-entry.md:77]` at up to
   0.53 A `[repo: power-entry.md:83]`. **That current is the exact thing the D1/D2
   split exists to keep off the analog side** `[repo: power-entry.md:46-57]`. The
   page's central decision and the page's own drawing disagree, 140 lines apart.

2. **The mod channels' filter current lands in the breath differential input.**
   At 1 kHz, `|Z| = 1/(2π · 1000 · 82e-9) = 1.94 kΩ` `[calc]`;
   `10 V / 1.94 kΩ = 5.2 mA` per channel, `× 4 = 20.6 mA` peak into `AGND`
   `[calc]`. B7 gives the `AGND` conductor as 0.189 Ω
   `[repo: docs/review/2026-09-20-cold-review/B7-grounding.md:904]`, so
   `20.6 mA × 0.189 Ω = 3.9 mV` `[calc]` appears **differentially** at the
   in-amp, `× 2.185 = 8.5 mV` at its output `[calc]` against a 9.94 V span —
   0.09 %, i.e. mod-channel content audible on the breath CV.

3. **`R-CLR-PD` puts a standing DC current in it.** 10 kΩ from the '123's
   push-pull `Q` at 5.21 V = `521 µA` `[calc]`, flowing whenever the watchdog is
   *not* firing, which is all of normal operation. `521 µA × 0.189 Ω = 98 µV`
   `[calc]` — electrically trivial, but it is a permanent DC current in the one
   conductor specified to carry zero, and it is the precedent that makes the
   other two look normal.

If they are **two** nets, then `power-entry.md` has no drawn return for the
analog bulk caps or the LM317 output cap at all, and two other pages reference an
undefined node.

**Either reading is a defect.** Fix: rename the module analog return — ADR
0004:494 already calls it "Module analog return" — and reserve `AGND` for the
pin-2 conductor. Then redraw `power-entry.md:15-22`, `mod-channels.md:37` and
`digital-and-supervision.md:41-43` onto it.

### The presence threshold — superseded during this review, and one claim in the replacement does not hold

`digital-and-supervision.md` replaced its presence detect while this review was
being written. **The replacement is better and the finding this section
originally carried is void**; it is recorded here because the residue matters.

The current design `[repo: digital-and-supervision.md:96-122]`:

| State | In-amp output |
|---|---|
| Cable unplugged | R4/R5 pull both inputs to `AGND` → **`V_REF` ≈ +0.437 V** |
| Instrument alive | `REF` trim nulls the pedestal → **0 V** |

with the threshold at **`V_REF`/2, taken off the trim buffer itself**. Both rows
check out: unplugged, the differential input is zero so `Vout = V_REF = +0.437 V`
`[calc]`; alive, `Vout = −2.185 × 0.2 + 0.437 = 0 V` `[calc]`. **The states are
437 mV apart with the sense inverted, not collapsed** — so the claim this review
was about to make, and the claim the page itself made two revisions ago, were
both wrong. The page says so plainly and gives two arithmetic reasons the
input-node tap it briefly proposed was worse than the fault it was fixing
`[repo: digital-and-supervision.md:117-122]`. Both are stronger than the version
this review had derived and point the same way. Nothing to add.

**Two things do remain.**

- **The page's own drawing is now stale twice over.**
  `digital-and-supervision.md:52-57` still shows "in-amp output ── (0 V absent,
  **−0.44 V alive**)" into the LM311 with "threshold **−200 mV** (from −12 V)".
  That contradicts the **current** table at lines 100-101 (+0.437 V absent, 0 V
  alive) as well as the one before it, and it is the part a builder reads. It has
  now survived two corrections of the prose above it.

- **"It degrades correctly" needs one more line, because as stated it does not.**
  The page argues: "if the reference dies, the threshold goes with it and the
  detect reads 'absent'" `[repo: digital-and-supervision.md:106-107]`. Work it
  through with `V_REF = 0`:

  ```
  alive:     Vout = −2.185 × 0.2 + 0 = −0.437 V   threshold = 0 V  →  present
  unplugged: Vout = 0 V                            threshold = 0 V  →  marginal
  ```
  `[calc]`

  The absent case lands exactly **on** the threshold and is decided by hysteresis,
  not by the circuit — so a dead reference reads *present* when alive and
  *undecided* when absent, which is the opposite of the stated fail-safe. The
  self-centring claim against the 0.152–0.378 V pedestal band is correct and is
  the good part of this design; the fail-safe claim is one sentence ahead of its
  arithmetic. Either offset the threshold slightly off `V_REF`/2 toward the absent
  state, or drop the fail-safe sentence.

### The `TRIM-BREATH-ZERO` buffer now has a second consumer — checked, sound

Taking the threshold "off the trim buffer itself" makes that OPA2197 half drive
both the INA828's `REF` pin and the comparator's threshold divider. **This does
not reopen the CMRR argument** `[repo: breath-receive-stage.md:130-133]`: what
that argument forbids is source impedance *at the `REF` pin*, and an op-amp
output stays low-impedance regardless of what else hangs on it. A divider of
100 kΩ or more draws `0.437 / 100 kΩ = 4.4 µA` `[calc]`. **Sound — but it is now
a two-page shared node and neither page says so.** One line on the breath page.

### One dependency claim that is false

`breath-receive-stage.md:164-166`:

> "**But the rule as written in ADR 0003 forbids the thing that makes the
> receiver work, and must be restated** to mean 'no *power* current', which is
> what it always meant."

ADR 0003 as written already says exactly that: "Give the analog signal its own
return conductor that carries **no power current**"
`[repo: docs/decisions/0003-breath-sensing-path.md:336]`. ADR 0004:87 repeats it
verbatim, and ADR 0004:516 explicitly names "the two 1 MΩ bias resistors" as a
permitted termination. **Nothing needs restating, and the paragraph is the only
textual cover the three illegal `AGND` returns currently have.** Delete it.

---

## Node: the LM311's collector — `OE` ×4, panel LED, pull-up

### Consumers

| Consumer | Where | Assumption |
|---|---|---|
| `OE` ×4 on the 74AHCT125 | `digital-and-supervision.md:28`, `power-entry.md:138` | active low; part on bus +5 V |
| Panel LED + 820 Ω | `power-entry.md:139-141`, `digital-and-supervision.md:61`, `hardware/bom.csv:83` | bus +5 V |
| `R-OE-PU` 10 kΩ | `power-entry.md:138`, `digital-and-supervision.md:60`, `hardware/bom.csv:101` | bus +5 V |
| LM311 open collector, emitter at GND | `digital-and-supervision.md:56` | LM311 on ±12 V |

All four now agree on bus +5 V. (The BOM's `R-OE-PU` row said 5.21 V this
morning; it was corrected during this review — see "Fixed mid-review".)

### Defect 3 (showstopper) — which rail is the LM311 on?

Three statements agree, one is catastrophic:

- `digital-and-supervision.md:54-55` draws "LM311 / ±12 V"
- `power-entry.md:16` lists "LM311" among the loads on MODULE ANALOG +12 V
- `hardware/bom.csv:99`: "run it on **+-12V** so it can see the negative input,
  tie the emitter to GND, pull the collector to +5V"

against

- `power-entry.md:149-151`: "The **comparator** and the watchdog stay on the
  LM317's 5.21 V so that a bus rail failure cannot take the supervision with it."

**An LM311 on 5.21 V / GND cannot see a negative input.** That is precisely and
only why the LM393 was rejected:

> "The INA828 rests at −0.44V, **below an LM393's own V−** if it runs on
> +5V/GND" `[repo: hardware/bom.csv:99]`

`power-entry.md:149-151` re-creates the rejected fault under a new part number,
in one sentence, on the page a builder reads while choosing rails. **Delete "the
comparator and" from that sentence.** The watchdog half is correct and is
corroborated by `hardware/bom.csv:54`, and the argument the sentence is making —
supervision must outlive a bus-rail glitch — is satisfied anyway, because ±12 V
is not the bus rail.

Note this is also now corroborated *against* the BOM's newly-corrected
`R-OE-PU` note, which states the split cleanly: "that was right for the
COMPARATOR and the WATCHDOG, which do sit on 5.21V" — **and is itself wrong about
the comparator, for the same reason.** The error has propagated one document
further during this review.

### The node's behaviour, checked — sound

Comparator released: node pulled to +5 V through 10 kΩ; the LED branch needs the
node below `5.0 − 2.0 = 3.0 V` to conduct, so the LED is dark and `OE` is high →
outputs Hi-Z → **absent = disabled = LED out**. Comparator saturated: node ~0.2 V,
LED current `(5.0 − 2.0 − 0.2) / 820 = 3.4 mA` `[calc]`, `OE` low → enabled →
**LED lit**. Total LM311 sink `3.4 mA + 5.0/10 kΩ = 3.9 mA` `[calc]`. **Polarity,
fail-safe direction and current budget are all correct.** The defects on this
node are in which rail the documents claim, not in the topology.

(`power-entry.md:145` computes the LED current from 5.21 V, the rail it is no
longer on — `3.9 mA` instead of `3.4 mA` `[calc]`. Harmless, stale.)

---

## Rail: bus +5 V

### Defect 5 — "the only thing on it is a $0.30 buffer" is false in four documents

| Document | Claim |
|---|---|
| `power-entry.md:41` | "`+5V ├──[FB4]──[C4 47µF]──── 74AHCT125 **only**`" |
| `power-entry.md:58-60` | "the **only** thing on it is a $0.30 buffer, and a reversed ribbon that kills the buffer **and nothing else** is an acceptable outcome (ADR 0004)" |
| `docs/decisions/0005-power-architecture.md:122-123` | "It is used — but **only for the 74AHCT125 level shifter**, around 10 mA" |
| `docs/decisions/0004-cv-interface-module.md:189-191` | "the only thing hanging on the unprotected bus +5 V pin is a $0.30 buffer. A reversed or row-offset ribbon that puts +12 V onto that pin kills the buffer and nothing else, **which is why the +5 V entry gets no protection network of its own**" |

`power-entry.md:136-145` and `digital-and-supervision.md:60-61` add `R-OE-PU`
and the panel LED to the rail. `power-entry.md:41` was not updated in the same
commit; the word "only" survives three lines above the section that breaks it.

**This is not cosmetic.** ADR 0004:191 *derives* the no-protection decision from
the "nothing else" claim. With the two new loads, +12 V on that pin now reaches:

- the 74AHCT125's four `OE` pins (dead part, accepted);
- **the LM311's open collector**, through 10 kΩ and through the LED — an external
  rail arriving on a supervision part deliberately kept on a different supply;
- the LED at `(12 − 2) / 820 = 12 mA` `[calc]` against a 4 mA design point;
- **and possibly the DAC's `SYNC` pin** — see below.

The ADR's cost/benefit no longer describes the blast radius. Either re-derive it
against the real load list or fit the series element it declined.

### Unresolved: what rail do the DAC-side SPI pulls use?

`digital-and-supervision.md:31-32` draws the second `R-SPI-PULL ×3` between the
buffer and the DAC — "SCLK↓ MOSI↓ **CS↑**". **The pull-up's rail is stated
nowhere**; `hardware/bom.csv:49` says only "DAC side: same". The two candidates
are not equivalent:

- **Bus +5 V**: a reversed ribbon reaches the DAC8568's `SYNC` pin through 10 kΩ.
  That is a ~$10 part whose `SYNC` glitch latches the clear-code register
  `[repo: digital-and-supervision.md:83-86]`, not a $0.30 buffer.
- **5.21 V**: correct against the DAC's own thresholds and isolated from the bus
  rail. `521 µA` `[calc]` flows into the buffer's unpowered outputs if the bus
  rail dies — harmless.

**5.21 V is right. Draw it.** It is the difference between a $0.30 failure and a
DAC failure.

### Load — sound

`10 mA` buffer `[repo: ADR 0005:123]` + `3.4 mA` LED + `0.5 mA` pull-up =
**~14 mA** `[calc]`. Negligible against any rack. No action beyond deleting
"only".

---

## Rail: the LM317's 5.21 V

### Consumers

| Consumer | Where | Stated? |
|---|---|---|
| DAC8568 `AVDD` | `power-entry.md:18`, `digital-and-supervision.md:36` | yes |
| 74HC123 | `digital-and-supervision.md:47`, `hardware/bom.csv:54` | yes |
| **`TRIM-BREATH-ZERO` divider** | `hardware/bom.csv:108` | **new today, not in any budget** |
| DAC8568 `DVDD` | — | **nowhere** |
| DAC-side `CS` pull-up | — | **undrawn** |
| LM311 | `power-entry.md:149` claims it; three sources deny it | **defect 3** |

### Current budget — sound

`Vout = 1.25 × (1 + 475/150) = 1.25 × 4.1667 = 5.208 V` `[calc]` ✓ matches the
stated 5.21 V `[repo: hardware/bom.csv:39]`.

Divider current `= 1.25 V / 150 Ω = 8.33 mA` `[calc]`, which by itself exceeds an
LM317's minimum-load requirement `[from memory: 3.5–10 mA]`, so the regulator
cannot fall out of regulation on a light load.

The '123's dynamic draw is the one number nobody computed, and computing it
closes an open question. With `R·C = 1 MΩ × 220 nF = 0.22 s` and a 250 µs
retrigger interval, the timing cap charges only
`ΔV = 5.21 × (1 − e^(−250e-6/0.22)) = 5.21 × 1.136e-3 = 5.9 mV` `[calc]` between
retriggers; charge dumped per retrigger `= 220 nF × 5.9 mV = 1.30 nC` `[calc]`;
at 4 kHz that is **`5.2 µA`** `[calc]`.

Total: `8.33 mA` divider + DAC `AVDD` + ~0 for the '123 + `60 µA` for the new
breath trim divider ≈ **11–13 mA**, matching "~13mA load incl. the divider,
~90mW" `[repo: hardware/bom.csv:38]`. Dissipation
`(11.7 − 5.21) × 13 mA = 84 mW` `[calc]` in TO-92. **Sound as written — provided
the LM311 does not move onto this rail.**

### The '123 open question is answerable on paper

`hardware/bom.csv:54` and `digital-and-supervision.md:154-156` both leave open
"whether the '123 empties 220 nF in a 250 µs retrigger window". From the above the
cap is only ever 5.9 mV above ground during steady retriggering, so there is
almost nothing to empty. Worst case is the first retrigger after a full timeout,
with the cap near 5.21 V: at an internal discharge resistance of order 50 Ω
`[from memory — this single number is the gap]`, `τ = 50 Ω × 220 nF = 11 µs`
`[calc]`, `5τ = 55 µs < 250 µs` `[calc]`. **The answer is almost certainly yes and
the only unknown is one datasheet number — not a bench session.**

### Sequencing — sound both ways

- **Bus +5 V first:** the buffer powers up, `R-OE-PU` holds `OE` high, outputs
  Hi-Z, nothing is driven into an unpowered DAC. The LM311 is unpowered so its
  collector is open, which means high, which means disabled. Correct by
  construction.
- **5.21 V first:** `R-CLR-PD` holds `CLR` low = cleared = zero scale
  `[repo: digital-and-supervision.md:137-141]`, and the '123 shares the rail, so
  there is no window in which a powered '123 drives a dead DAC. Correct.

The residual is the '123's own power-on `Q` state, already on both still-open
lists `[repo: digital-and-supervision.md:152-153; hardware/bom.csv:54]`.

### Defect 7 — `DVDD` exists in exactly one cell of the repository

`grep -rn DVDD` returns two hits: "DAC8568 AVDD+DVDD = 2"
`[repo: hardware/bom.csv:43]` and one cold-review line
`[repo: docs/review/2026-09-20-cold-review/C2-passives.md:764]`. **No schematic
page assigns `DVDD` a rail.**

This is load-bearing, because the whole level-shifter argument is stated against
`AVDD`:

> "Its job is to get 3.3 V logic over the DAC's **0.7 × AVDD** input threshold —
> 3.65 V at AVDD = 5.21 V"
> `[repo: docs/decisions/0004-cv-interface-module.md:186-187]`, repeated at
> `digital-and-supervision.md:68`

On a part with a separate digital supply, the digital input threshold is normally
referenced to the **digital** supply `[from memory — the DAC8568 datasheet is the
gap]`. If `DVDD` is on bus +5 V the threshold is `0.7 × 5.0 = 3.50 V` `[calc]` and
the margin improves; if on `AVDD` the stated 3.65 V holds. **Either way the
sentence everyone relies on names a pin that is not drawn.**

Fix: put `DVDD` on 5.21 V explicitly — the same rail as `AVDD`, for the reason
already given at `digital-and-supervision.md:71` ("`CLR` levels are
unambiguous") — draw it, and re-word the threshold sentence against `DVDD`.

---

## Node: DAC channel 7 and its follower

### The `k = 3` conversion is now carried by six documents and contradicted by four sections of one page

Agreeing: ADR 0006:15,21,92 · `hardware/bom.csv:68` (`R-MODGAIN`, 10 k/30 k,
gain exactly 4, ±10.000 V, qty now 8) · `firmware/README.md:50-55`
(`Vout = 4·Vdac − 3·V_ref`, 3.3333 V) · `pitch-stage.md:83-85` ·
`docs/research/…/R1-pitch-output-stages.md:137-138` ·
`mod-channels.md:14,20,31,54-77,93-96` (diagram **and**, since this afternoon,
the Values table).

Still contradicting, all inside `mod-channels.md`:

| Line | Stale text | Should be |
|---|---|---|
| 113-121 | tolerance table, "Zero point ±81 mV", "Span **19.70–20.51 V**" | recompute — see below |
| 132-135 | "**±10.05 V** uses the DAC's *full* 0–5 V span" | ±10.000 V |
| 146 | "`Vout = 4.02 × (0 − 0) = 0 V`" | `4 ×` |
| 152 | "`4.02 × (0 − 2.5) = −10.05 V`" | `4 × (0 − 3.3333) = −13.33 V` — the *stronger* version of the same argument |
| 157 | "pins the jacks at `4.02 × Vdac` ≈ **+11.45 V**" | `4 × 5.000 = +20 V`, clipped to ~+11.45 V by the rail |
| 167 | "At **2.5 V** into 2.5 kΩ that is **1 mA**" | 3.3333 V, **1.33 mA** — and the page's own diagram at line 16 already says "~1.3 mA" |
| 171-172 | "`R-OPAMP-IN` qty 7 covers …" | see the `R-OPAMP-IN` section |

Note lines 152 and 157 get *more* forceful when corrected, not less:
`4 × (0 − 3.3333) = −13.33 V` `[calc]` and `4 × 5.000 = +20 V` `[calc]` both
exceed the ±11.45 V rail, so both failure modes now park the jacks **hard against
a rail** rather than near one. The section's argument survives and strengthens.

### A structural defect the partial fix introduced

`mod-channels.md:98` opens a parenthetical — `*(The four-resistor version this
replaced used 40.2 kΩ…` — that is **never closed**. It now swallows four
subsequent sections, including "Tolerance, done properly" and "On the range",
which are about the **live** design, not the superseded one. A reader reaches the
live tolerance numbers already told they are reading history. Close the paren
after line 102.

### Corrected tolerance for the network that is actually specified

For `R1 = 10 kΩ`, `R2 = 30 kΩ`, both 1 %, with `V_ref = 3.3333 V` exact (it is a
DAC code, not a resistor):

```
Vout = (1 + R2/R1)·Vdac − (R2/R1)·3.3333

corner A   R1 = 9.9k,  R2 = 30.3k → k = 3.0606, gain 4.0606, intercept 10.2019
           Vdac = 5 → +10.101 V    Vdac = 0 → −10.202 V    span 20.303 V
corner B   R1 = 10.1k, R2 = 29.7k → k = 2.9406, gain 3.9406, intercept  9.8019
           Vdac = 5 →  +9.901 V    Vdac = 0 →  −9.802 V    span 19.703 V

zero point at Vdac = 2.5:   A → −50.4 mV      B → +49.6 mV
```
`[calc]`

**Span 19.70–20.30 V, zero ±50 mV** — better than the stale ±81 mV / 20.51 V on
both terms. The page's conclusion survives unchanged
`[repo: mod-channels.md:123-127]`; only the numbers move. Worst case +10.20 V
still fits the ~±11.45 V headroom.

### `3.3333 V` is exactly representable — a genuinely clean result

`65535 = 3 × 21845`, so `⅔ × 65535 = 43690` **exactly**, and
`43690 / 65535 × 5.000 V = 3.333333 V` `[calc]`; `3 × 3.333333 = 10.000000`
`[calc]`. The shared offset lands on an integer code with zero quantisation
residue. The `k = 3` choice is arithmetically exact, not merely convenient —
worth one line on the page, since nobody has said it.

The `CLR` and power-on safe states also hold **exactly**, and for a subtler
reason than the page gives: any zero-scale offset the DAC has appears in both
terms and cancels, `4 × (ε − ε) = 0` `[calc]`. And per defect 1, the mod channels
are the only outputs immune to the reference-enable trap, for the same structural
reason.

### Does anything else hang on ch7? — no, and that is correct

ch7 appears only in `mod-channels.md`, ADR 0006:15,21, `firmware/README.md:50`
and `hardware/bom.csv:12`. The follower drives four 10 kΩ inputs and nothing
else. Channel allocation is consistent everywhere: pitch ch1, mods ch2–5, offset
ch7, **6 of 8 populated, ch6 and ch8 spare** `[repo: hardware/bom.csv:12]`,
matching "refresh all six populated channels" `[repo: mod-channels.md:158-159]`.
**Sound.**

One stale echo: ADR 0006:278 still says "Channels **2–6** need only to be linear
and repeatable" — the signal mods are 2–5 and 6 is free
`[repo: ADR 0006:25]`. Harmless, one edit.

### The mod channels use the full span on half of ADR 0006's reasoning

`mod-channels.md:132-135` dismisses the 0.25–4.75 V window as "a **pitch-channel
reserve** … does not apply here". ADR 0006 gives the window **two** reasons:

> "Use the DAC's 0.25–4.75 V window rather than its full 0–5 V span. That leaves
> 250 mV of headroom at both rails — **the DAC8568 at AVDD = 5 V cannot reliably
> swing to its own supply** — and the trimmer absorbs the resulting gain change."
> `[repo: docs/decisions/0006-cv-channel-allocation.md:418-421]`

The firmware-reserve reason `[repo: ADR 0006:462-463]` is indeed pitch-specific.
**The output-swing reason is a device limit and applies to every channel.** By
dismissing the window wholesale, the page puts the four mod channels at exactly
the codes whose behaviour the LM317 rail exists to protect:

> "raise the top codes and find where they start compressing against AVDD. That
> is the floor that actually matters"
> `[repo: docs/decisions/0004-cv-interface-module.md:179-181]`

> "what AVDD decides is whether the output buffer can reach it"
> `[repo: ROADMAP.md:189]`

So the mod channels, at code 65535, are the ones that will discover whether
5.21 V was enough — and they are the ones the page says need no margin. **The
page's stated reason for dismissing the window is wrong on the half that is a
hard device limit**, and it removes the only margin the design has against an E7
failure. Add a line naming E7 as the gate; if E7 finds compression, it is the mod
channels that clip.

---

## Node: the six CV outputs

| | PITCH | MOD 1–4 | BREATH |
|---|---|---|---|
| Series R | `R-OUT-PROT 1 kΩ, 1206` `[pitch:33]` | `R-OUT-PROT 1 kΩ, 1206` `[mod:35]` | **"[1k]"**, unnamed, no package `[breath:65]` |
| Clamp | `D-JACK-CLAMP BAV99`, driver side `[pitch:31]` | `D-JACK-CLAMP BAV99`, driver side `[mod:33]` | **none drawn** |
| Filter cap | none at the jack; `C-FB-PITCH` 1 nF in feedback `[pitch:29,166-171]` | `C-FILT-MOD` 82 nF, jack side `[mod:37]` | 330 nF, jack side `[breath:65,144]` |
| Corner | 15.9 kHz `[calc: 1/(2π·10k·1n) = 15.92 kHz]` | 1.94 kHz `[calc: 1/(2π·1k·82n) = 1.941 kHz]` | 482 Hz `[calc: 1/(2π·1k·330n) = 482 Hz]` |
| Feedback tap | **at the jack** `[pitch:35,143-165]` | at the op-amp output `[mod:31]` | not drawn |

### Defect 8a — the sixth clamp is bought and not drawn

`D-JACK-CLAMP` is qty **6**, "Clamp diodes on the DRIVER side of R-OUT-PROT", and
its back-powering arithmetic is computed across "**254 mA across six jacks**"
`[repo: hardware/bom.csv:52]`. Five are drawn. **The breath output has no clamp
on its page.** Either the breath page is missing one, or the quantity is wrong and
the back-powering figure is computed over a jack that has no clamp. The first
reading is almost certainly right: the breath jack is as patchable as the others
and its op-amp is on the same ±12 V.

### Defect 8b — two BAV99s are drawn that the BOM does not buy

`breath-receive-stage.md:32` draws "BAV99 to ±12 V, **both legs**" on the
*receive* pair, inside the module boundary. `D-JACK-CLAMP` qty 6 is explicitly
output-side only. `grep BAV99 hardware/bom.csv` returns that one row. ADR 0004:636
references "BAV99 bound the rest (`hardware/module/breath-receive-stage.md`)", so
the part is real and reasoned — **and has no BOM row.** Module BAV99 count should
be 6 outputs + 2 input legs = **8**. (The instrument-end ESD parts are separate
and correctly rowed: `D-TVS-BREATH` qty 2 `[repo: hardware/bom.csv:96]`.)

### Defect 8c — the BOM says pitch's reconstruction filter does not reconstruct; the pitch page says it does

The BOM states one convention twice, in identical words:

> "**ON THE JACK SIDE of R-OUT-PROT, never the op-amp side** — inside the loop it
> is a capacitive load and the stage can oscillate."
> `[repo: hardware/bom.csv:64 (C-OUT-BREATH) and :67 (C-FILT-MOD)]`

Pitch is the exception and knows it `[repo: pitch-stage.md:166-171]` — sound
engineering, well argued. But then:

> "1k x 82nF = 1.94kHz. **Real attenuation on the 3.6kHz ZOH image that a 15.9kHz
> corner ignores.**" `[repo: hardware/bom.csv:67]`

against

> "The 15.9 kHz reconstruction pole comes from `C-FB-PITCH` instead, which is the
> **same corner in a better place**" `[repo: pitch-stage.md:166-168]`

Against the 4 kHz DAC update rate `[repo: digital-and-supervision.md:85-86]`:

```
pitch, 15.92 kHz:  20·log10(1/√(1+(4/15.92)²)) = −0.27 dB    [calc]
mod,    1.941 kHz: 20·log10(1/√(1+(4/1.941)²)) = −7.20 dB    [calc]
```

**It is the same corner as the deleted part, and that corner was already
ineffective — a fact recorded in the BOM and nowhere on the pitch page.** Whether
pitch *needs* image rejection is arguable (a VCO integrates the staircase away).
What is not arguable is that two documents currently assert opposite things about
the same capacitor. **State the rule** — "1 nF is chosen for the loop, not for the
image; the image is left to the VCO" — or raise the corner. Do not leave "same
corner in a better place" standing next to the BOM line calling that corner
ineffective.

Breath's 482 Hz is **not a reconstruction pole at all** — breath never passes
through the DAC `[repo: hardware/bom.csv:67]` — it is the channel band limit.
Calling it "reconstruction" `[repo: breath-receive-stage.md:144]` makes a
three-way comparison look inconsistent when it is not.

### Defect 8d — the pitch page's own fix is half-applied, and the gap is now sharper

`pitch-stage.md`'s component table was corrected during this review (200 Ω
`TRIM-GAIN`, `R-OUT-PROT` "inside the DC feedback loop", `C-FB-PITCH` replacing
`C-FILT-PITCH`, `R-OFFINJ` deleted). **Three passages below it were not, and they
now contradict the table on the same page:**

| Line | Says | Table says |
|---|---|---|
| 203-205 | "**Trim with the real patch connected** … that error is what the gain trim's **±5 %** range exists to absorb" | `0 → +2 %`, one-sided, and the load error is now identically zero `[repo: pitch-stage.md:130,133,152-153]` |
| 212 | "**TRIM-GAIN tempco** \| **0.4–2.4 cents** … contributing ~5 % of the ratio … **have not been reconciled** … the largest line here" | 200 Ω contributes ~2 ppm/°C, "comparable to the LT5400" `[repo: pitch-stage.md:130; hardware/bom.csv:105]` — i.e. reconciled, and no longer the largest line |
| 228-230 | "Still open: **Whether `TRIM-GAIN` is 1 kΩ or 500 Ω.** ±5 % of a 10 kΩ ratio wants ~1 kΩ" | 200 Ω, decided |

**The accuracy table is ranking a term the same page has already fixed**, and the
Still Open list is asking a question the same page has already answered. This is
worse than before the fix, not better: previously the page was uniformly stale;
now it disagrees with itself.

### The E9 rationale — fixed during this review, and the neighbouring row was not

`ROADMAP.md:191` was rewritten mid-review and is now correct and forceful ("**A
GATE, not a reassurance** — and this row used to say the opposite. The pitch stage
now *is* the in-loop version"). `pitch-stage.md:173-175`'s claim that "E9 already
has the check" is now true.

**`ROADMAP.md:190` was not touched** and is still stale in the same way:
"Quantifies the **1 kΩ divider error** against the real patch, and tells you how
much a re-mult actually shifts tuning" — an error the jack-side feedback removes
by construction `[repo: pitch-stage.md:151-153]`. Keep the sweep; it now
*verifies zero* rather than quantifying a value. Rewrite its purpose.

---

## Part: OPA2197 — the half count

Counted by walking every page. Instrument-side halves excluded (`U-BUF`, a
separate qty-1 row `[repo: hardware/bom.csv:27]`).

| Page | Half | Ref |
|---|---|---|
| `pitch-stage.md` | `VREFOUT` follower | `:14` |
| `pitch-stage.md` | pitch amplifier | `:25` |
| `mod-channels.md` | DAC ch7 offset buffer | `:14` |
| `mod-channels.md` | mod channel ×4 | `:27` + "(ch3, ch4, ch5 identical)" `:20` |
| `breath-receive-stage.md` | INA828 `REF` buffer | `:53` |
| `breath-receive-stage.md` | downstream inverting **gain + offset**, one block, labelled "**½ OPA2197**" | `:60-63` |

**Drawn module total: `1 + 1 + 1 + 4 + 1 + 1 = 9` halves** `[calc]`.

The BOM enumerates eleven:

> "Twelve halves, eleven used: pitch, mod 1-4, mod offset buffer, **breath gain,
> breath offset**, VREFOUT follower, breath REF-zero buffer. One spare."
> `[repo: hardware/bom.csv:13]`

`1 + 4 + 1 + 1 + 1 + 1 + 1 = 11` `[calc]` — and **"breath gain" and "breath
offset" are the same half.** Both pages say so:

> "an inverting summer does gain and offset with two pots into **one virtual
> ground**" `[repo: breath-receive-stage.md:88-90]`

and the BOM says so itself, two rows earlier:

> "the downstream stage inverts, which is also the topology that does
> gain-then-offset with two pots in **one op-amp half**"
> `[repo: hardware/bom.csv:28]`

**`hardware/bom.csv:13` double-counts one half against `hardware/bom.csv:28`.**

Consequences, all small and all in the same direction:

- **The true count is 9, not 11.** Six packages = 12 halves gives **3 spare**, not
  one `[calc]`.
- `breath-receive-stage.md:125` — "It costs the last spare OPA2197 half, and
  `U-OPA-PITCH` goes to six packages so there is still one" — is wrong twice: it
  was not the last spare, and three remain.
- The BOM's own history line, "Was 5 packages with zero spare once the breath zero
  trimmer went in", implies **10** — a third number. At 9, five packages already
  leave one spare, so the stated reason for going to six is satisfied at five.

**Recommendation: keep six packages.** The reasoning is sound, the part is cheap,
and two open items could each consume a half ("whether the gain pot's wiper needs
a buffer" `[repo: breath-receive-stage.md:234]`; the recorded mod alternative
would *return* one `[repo: mod-channels.md:192-193]`). But **correct the
enumeration at `hardware/bom.csv:13`** — it is the only place the halves are
listed, and it currently describes a circuit that does not exist.

---

## Part: `R-OPAMP-IN` — is 7 the right quantity?

The enumeration appears twice, identically:

> "`R-OPAMP-IN` qty 7 covers pitch, the four mods, this buffer and the `VREFOUT`
> follower" `[repo: mod-channels.md:171-172]`

> "SEVEN … Pitch, mod 1-4, the mod offset buffer, the VREFOUT follower."
> `[repo: hardware/bom.csv:51]`

`1 + 4 + 1 + 1 = 7` `[calc]` ✓ internally consistent. **But the list is drawn
from two pages and omits the third**, and the stated purpose — clamp-current
protection where a DAC pin on 5.21 V meets an op-amp on ±12 V that may power up
first `[repo: pitch-stage.md:87-90; hardware/bom.csv:51]` — sorts the eight
candidate inputs differently:

| # | Input | Has one? | Actually needed? |
|---|---|---|---|
| 1 | pitch amp (+), DAC ch1 | yes `[pitch:21]` | **yes** |
| 2–5 | mod amps (+), DAC ch2–5 | yes `[mod:23]` | **yes** |
| 6 | mod offset buffer (+), DAC ch7 | yes `[mod:14]` | **yes** |
| 7 | `VREFOUT` follower (+) | yes `[bom:51]` | **redundant** — `TRIM-OFFSET`'s 10 kΩ is already in series `[repo: hardware/bom.csv:106]`, limiting clamp current to `(12 − 2.5)/10 kΩ = 0.95 mA` `[calc]` |
| 8 | breath `REF` buffer (+) | no | **no longer applicable** — it now comes from the LM317 rail, not a DAC pin `[repo: hardware/bom.csv:108]` |

So the correct statement is **"five where the DAC drives an op-amp input
directly; the `VREFOUT` follower is already protected by its own trimmer"** —
i.e. 5, or 6 for belt and braces. Seven is defensible only as over-provision.
What is not defensible is an enumeration that counts a trimmer-protected input
while the identical case on a third page went unmentioned until the BOM moved it
off the DAC this afternoon.

**Symptom of the same gap as the op-amp half count: both enumerations were built
from two pages out of three.**

---

## Part: LT5400 — the two spare sections cannot do what three documents say

> "Two of the four used at 1:1; **the other two are available for the mod
> channels, which want 1:3 (three sections against the fourth).**"
> `[repo: hardware/bom.csv:15]`

echoed at `pitch-stage.md:231-233` and `mod-channels.md:56-57`.

**A 1:3 ratio built from a quad uses three sections in series against one — all
four.** Two spare sections give 1:1 or 2:1, never 1:3 `[calc]`. And there are four
mod channels, each wanting its own pair, so even a whole spare quad serves one
channel. The mod channels are specified as ordinary 1 % discretes anyway
(`R-MODGAIN`, `[repo: hardware/bom.csv:68]`; "The discretes won"
`[repo: mod-channels.md:9]`).

**Arithmetically impossible, and the need it served was already retired.** Delete
the claim from all three places and downgrade it to what it is: two matched 10 kΩ
resistors available for anything wanting a matched pair.

---

## Part: 74AHCT125 — the spare gate's input floats

`hardware/bom.csv:35`: "Covers SCLK MOSI CS with **a spare gate**."
`hardware/bom.csv:49`: the six pulls are enumerated as three signals × two sides.
**The fourth gate is in neither list.**

The stated reason for the pulls is "so the buffer's inputs do not float **and
crowbar**" `[repo: hardware/bom.csv:49]`. An unconnected AHCT input crowbars for
the same reason whether it is spare or not `[from memory: a CMOS input biased near
mid-rail conducts both output transistors]`. **Tie the spare gate's input to
ground at the package.** No new part, one net, invisible once the board exists.

---

## Cross-page dependency claims — audit

Every "see X for Y" in the five pages, checked against X, in the current tree.

| Claim | Where | Verdict |
|---|---|---|
| "see `mod-channels.md`" for `k=3` / 3.3333 V | `pitch-stage.md:85` | **Now true** for the diagram and Values table; that page's tolerance, range and `CLR` sections still carry 40.2 k numbers |
| "ADR 0006 specifies `Vout = 4 × (Vdac − 2.5 V)`" | `mod-channels.md:6` | **True** `[repo: ADR 0006:102]` |
| "an A/C-grade DAC8568 clears every channel to zero scale (ADR 0006)" | `mod-channels.md:142` | **Stale as of this afternoon** — ADR 0006:143-147 now says "**a C grade**… Not 'A or C', which this line used to say". The page still says A/C |
| "ADR 0006 says these channels need to be 'linear and repeatable, not calibrated'" | `mod-channels.md:124` | **True** `[repo: ADR 0006:278,423]`; the ADR's "channels 2–6" is itself stale |
| "the statelessness rule in `firmware/README.md` — refresh all six populated channels every pass" | `mod-channels.md:158-159` | **True in substance, not in words.** `firmware/README.md:38` says "**Refresh everything, every pass. Never write-on-change.**" It does not say "six"; the quantity comes from `hardware/bom.csv:12`. The page quotes a specificity the file lacks |
| "ADR 0006's 0.25–4.75 V window … does not apply here" | `mod-channels.md:132-135` | **Half-false** — the ADR gives two reasons and one is a device limit `[repo: ADR 0006:418-421]` |
| "the rule as written in ADR 0003 … must be restated" | `breath-receive-stage.md:164-166` | **False.** ADR 0003:336 already says "carries no power current"; ADR 0004:516 already permits the 1 MΩ pair |
| "ADR 0004, 'The watchdog's scope is the DAC channels'" | `breath-receive-stage.md:226-227` | **True** |
| "E9 already has the check" | `pitch-stage.md:173-175` | **Now true** — `ROADMAP.md:191` was rewritten mid-review. `ROADMAP.md:190` was not |
| "Trim with the real patch connected (ADR 0006)" | `pitch-stage.md:203-205` | **True of ADR 0006, obsolete in this design**, and now contradicted by the same page's own table |
| "a reversed ribbon … kills the buffer and nothing else (ADR 0004)" | `power-entry.md:58-60` | **ADR 0004:189-191 does say it** — but the premise was invalidated 80 lines later on the same page |
| "the same shape as the polyfuse thermal runaway ADR 0014 describes" | `power-entry.md:121-122` | **True** `[repo: ADR 0014:186-191]` |
| "ADR 0005's deletion argument was about the *instrument-end* polyfuse" | `power-entry.md:173-175` | **True** `[repo: ADR 0005:275]` |
| "`AGND` is not a ground at all (ADR 0003)" | `power-entry.md:161` | **True** — and contradicted by the diagram 140 lines above it |
| "the bus rail is a stated requirement (ADR 0005)" | `digital-and-supervision.md:68` | **True** `[repo: ADR 0005:142-143]` — but the same ADR line 123 says "**only** for the 74AHCT125", which the page breaks at line 60 |
| "`CLR` … An analog path cannot latch at a level the player is not producing (ADR 0004)" | `digital-and-supervision.md:145-146` | **True** |
| "The BOM's `R-PRESENCE` note … is wrong" | `digital-and-supervision.md` (earlier revision) | **True again, for a new reason.** `hardware/bom.csv:100` was updated to the "+100 mV against `AGND`, tap the `BREATH` node" arrangement — which the page has *since* rejected as worse than the fault it fixed `[repo: digital-and-supervision.md:109-122]`. The BOM row is now one revision behind a page that has moved twice. It must be rewritten to `V_REF`/2 off the trim buffer |

### The presence detect's stale copies

`digital-and-supervision.md:103-116` correctly identifies and fixes the
trimmer-versus-comparator collision. **Three documents still carry the pre-fix
circuit:**

- **Its own drawing.** `digital-and-supervision.md:52-57` — covered above; it is
  now two revisions behind the prose on the same page.
- **ADR 0004:355-378** still presents the −437 mV / −200 mV table as the design,
  and its "**Fixed is the operative word**" paragraph rests explicitly on `REF`
  being grounded.
- **`hardware/bom.csv:28`** (`U-DIFFRX`) still reads "REF ties **HARD** to module
  AGND — no divider" and "Output is **−0.44V at rest**", against
  `hardware/bom.csv:108` on the same node.

And `breath-receive-stage.md` still says `REF` is grounded in two places:

- `:68` heading — "**`REF` ties to ground**, and the polarity question dissolved twice"
- `:223` — "now that `REF` is **grounded** it touches the breath stage in no way at all"

against `:53-55, 96-131, 143`, which all describe a buffered +0.437 V trimmer.

**`ROADMAP.md:51` was half-fixed during this review** and is now
self-contradictory within one row: "in-amp receiver with **`REF` grounded**,
gain/offset knobs. **Set `TRIM-BREATH-ZERO` first**, until the in-amp output
reads 0 V". Delete the first clause.

**This remains the most-copied stale fact in the repository — six locations
across five files describing a wire that is not there** — and it is the fact whose
change broke the presence comparator. Sweeping it is still the highest-value
editorial action available.

One arithmetic note: `breath-receive-stage.md:57` says the in-amp reaches
"−9.6 V at full", while its own derivation gives a 9.94 V span from a 0 V rest
`[repo: :155]`. `0 − 9.94 = −9.94 V` `[calc]`, not −9.6.

---

## Assumptions checked and found sound — one line each

1. **`OE` polarity and fail-safe direction.** Active low; comparator released →
   pulled high → buffer disabled → LED out → "instrument absent". Consistent
   across `power-entry.md:138,147-150`, `digital-and-supervision.md:69`,
   `hardware/bom.csv:101`. Correct.
2. **DAC channel allocation.** pitch ch1, mods ch2–5, offset ch7, ch6 and ch8
   spare — consistent across ADR 0006:15,25, `hardware/bom.csv:12`,
   `firmware/README.md:50`, `mod-channels.md`. Six populated, six refreshed.
3. **`CLR` rail alignment.** The '123 and the DAC share the LM317's 5.21 V, so
   `CLR` levels are unambiguous and neither can drive the other while unpowered
   `[repo: digital-and-supervision.md:70-71]`. The reason given is the right one.
4. **`R-CLR-PD` direction.** Pull-**down** = cleared = zero scale = safe, and the
   pull-up it replaced is correctly retired `[repo: digital-and-supervision.md:137-141;
   hardware/bom.csv:71]`. (The BOM's `ref` is still spelled `R-CLR-PU` — a naming
   nuisance, not a defect.)
5. **`R-SPI-PULL` count and polarity.** Six, both sides, `CS` up / `SCLK` and
   `MOSI` down on each — `digital-and-supervision.md:24-32,82` matches
   `hardware/bom.csv:49` exactly, including the reasoning about Hi-Z outputs
   leaving the *DAC's* pins floating. The best-argued shared node on the five pages.
6. **Watchdog retrigger source.** DAC-side buffered `CS`, never cable-side —
   `digital-and-supervision.md:130-132` matches `hardware/bom.csv:54`, and the
   failure mode it avoids is stated accurately on both. (Its blind spot is
   defect 4, which is a different question.)
7. **D1/D2 split.** Three diodes, branch before them, instrument current kept off
   the analog rail `[repo: power-entry.md:46-57; hardware/bom.csv:37]`. Correct
   and consistently stated — and it is the principle defect 2 violates by another
   route.
8. **The mod channels' immunity to both zero-scale traps.** `CLR` and the
   reference-enable trap both cancel exactly, because the offset is a DAC channel
   `[calc: 4 × (ε − ε) = 0]`. The decision has now paid for itself twice.

---

## What to fix, in order

1. **Decide what pitch's jack does at rack power-on** (defect 1) and correct
   ADR 0006:154-168, which currently claims the mechanism reinforces a table it
   contradicts. Say it on `pitch-stage.md`, which does not mention it at all.
2. **Resolve `AGND`** (defect 2). Rename the module analog return; redraw
   `power-entry.md:15-22`, `mod-channels.md:37`, `digital-and-supervision.md:41-43`.
   Delete `breath-receive-stage.md:164-166`.
3. **Delete "the comparator and" from `power-entry.md:149`** (defect 3), and
   correct the same error where it has just propagated into `hardware/bom.csv:101`.
4. **Redraw `breath-receive-stage.md:56`** to the 5.21 V rail (defect 6), add the
   rail's tempco to the drift figure, and in the same edit carry the page's new
   0 → +1.0 V range and `R1b` into `hardware/bom.csv:108` and `:66` (defect 6b).
5. **Add the watchdog's blind spot** to `digital-and-supervision.md` (defect 4).
6. **Delete "only" from `power-entry.md:41,58-60` and ADR 0005:123**, and
   re-derive ADR 0004:189-191 against the real load list (defect 5).
7. **State the DAC-side `CS` pull-up rail (5.21 V) and `DVDD`'s rail** (defect 7).
8. **Finish `mod-channels.md`** — lines 98 (unclosed paren), 113-121, 132-135,
   142, 146, 152, 157, 167, 171-172.
9. **Finish `pitch-stage.md`** — lines 203-205, 212, 228-230, now that the table
   above them has been fixed; and fix the one-sided `TRIM-OFFSET` (defect 9).
10. **Sweep the "`REF` is grounded" copies**, including the first clause of
    `ROADMAP.md:51`; rewrite `ROADMAP.md:190`.
11. **Redraw `digital-and-supervision.md:52-57`** to the presence detect the same
    page now describes, rewrite `hardware/bom.csv:100` to match, and either fix or
    drop the "degrades correctly" sentence.
12. **Correct the counts**: OPA2197 halves 11 → 9; BAV99 6 → 8; `R-OPAMP-IN`
    enumeration; LT5400 spare-section claim deleted in three places; spare AHCT
    gate input tied.

---

## Fixed mid-review — recorded, not claimed as findings

These were live defects when this review began and were corrected in the working
tree while it was being written. Recorded so the count above is not inflated, and
because three of them changed the analysis.

| Was | Now | Effect on this review |
|---|---|---|
| `R-OE-PU` pulled to 5.21 V while the LED pulled to bus +5 V — two rails on one node | Both bus +5 V `[repo: hardware/bom.csv:101]` | Defect removed. **But the new note repeats the LM311-on-5.21 V error** — defect 3 has propagated one document further |
| `TRIM-BREATH-ZERO` derived from `VREFOUT` | Derived from the LM317 5.21 V rail, because `VREFOUT` depends on a DAC register `[repo: hardware/bom.csv:108]` | **This is the best cross-page catch in the tree today, and it is incomplete: the identical argument applies to pitch and was not applied.** It became defect 1 |
| `R-MODGAIN` qty 16 against a note saying 8 | qty 8 | Removed |
| `C-DECOUPLE` qty 19, enumerated against 5 op-amps and an LM393 | qty 22, enumerated against 6 op-amps and the LM311 | Removed. Independently recomputed here as 22 `[calc]` |
| `mod-channels.md` Values table at 40.2 kΩ / 2.500 V | 30 kΩ / 3.3333 V | Partly removed — four sections below it are still stale, and the fix left an unclosed parenthesis |
| `pitch-stage.md` component table at 1 kΩ `TRIM-GAIN`, `C-FILT-PITCH`, `R-OFFINJ` | 200 Ω, `C-FB-PITCH`, `R-OFFINJ` deleted | Partly removed — **and the page now contradicts itself**, because three passages below the table still assume ±5 % and 1 kΩ |
| `ROADMAP.md:191` E9 rationale inverted | Rewritten correctly | Removed. `ROADMAP.md:190` untouched |
| ADR 0006 "A or C grade" | "a C grade", with the gain/grade reasoning | Removed — but `mod-channels.md:142` still says "A/C-grade" |
| `breath-receive-stage.md` trim range 0 → +0.6 V | 0 → **+1.0 V**, ranged against the sensor's 0.152–0.378 V spec band | **New divergence** — `hardware/bom.csv:108` still says 0.6 V |
| Breath umbilical legs asymmetric (1 kΩ on `BREATH` only) | **`R1b` 1 kΩ added in the `AGND` leg** for CMRR | **New divergence** — `R-SER-BREATH-INST` is still qty 1, package 0805 vs the page's 1206 (defect 6b) |
| Presence detect: "both states sit at 0 V, so move the tap to the `BREATH` node" | **States are 437 mV apart with the sense inverted**; threshold is `V_REF`/2 off the trim buffer `[repo: digital-and-supervision.md:96-122]` | **Supersedes a finding this review was carrying.** The page's own arithmetic is stronger than mine. Residue: its ASCII is now two revisions stale, `hardware/bom.csv:100` is one revision stale, and the "degrades correctly" claim does not survive its own arithmetic |

**Two patterns are worth naming.** First, **every one of these fixes was applied
to one document and left stale in another** — the same failure mode this review
exists to catch, reproduced in the act of fixing it. Second, the two most
valuable fixes (`TRIM-BREATH-ZERO`'s rail, the `R-OE-PU` rail) were each derived
from an argument that **applies to a second node nobody checked**: the reference
is a register (pitch also depends on it), and a pull-up must sit on its consumer's
rail (the DAC-side `CS` pull-up has no stated rail at all).

---

## What this review could not determine

No vendor domain was reachable. These are **gaps, not findings**, and no figure
has been invented for any of them:

- **Whether the DAC8568's internal-reference enable can be strapped in hardware.**
  This decides whether defect 1 has a clean fix or only a documented compromise.
- **`VREFOUT`'s permitted DC load and load regulation.** 250 µA is drawn from it
  `[calc]`.
- **Whether the DAC8568's digital input thresholds reference `AVDD` or `DVDD`.**
  Decides whether ADR 0004:186 is correctly worded (defect 7).
- **The 74HC123's internal `C_ext` discharge resistance.** One number closes the
  "does it empty 220 nF in 250 µs" open item on paper.
- **The LT1641's pin names, foldback topology, and whether `-1` needs an `ON`
  cycle after latch-off** — already correctly flagged at `power-entry.md:113-116`.
- **The LT5400 option suffix** — already flagged at `pitch-stage.md:225-227`.
- **Whether 82 nF exists in C0G below 1210** — already flagged at
  `hardware/bom.csv:67`.
