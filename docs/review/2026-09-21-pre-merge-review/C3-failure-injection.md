# C3 — Failure injection

**Agent:** C3, cold pre-merge review, 2026-09-21.
**Slice:** what the design does when things go wrong, not when they work.
**Cold rule observed:** nothing under `docs/review/**` was read. `docs/log/` and
`docs/research/` were touched only where noted, and are marked as history.

**Provenance on every claim.** `[repo] path:line` — read in this repository.
`[calc]` — arithmetic shown. `[datasheet]` — document and page, as the corpus
quotes it (I did not re-open the PDFs; where a figure is load-bearing I say so).
`[from memory]` — not verified here and must be checked.

**Findings are node-indexed** and filed against a circuit node or BOM reference.
**Nothing was fixed.** `tools/check-staleness.py` reports `PASS ... 5 unresolved
(tracked)` on the tree as I found it `[repo]`, so none of what follows is
something the checker can see — every finding below is semantic, which is the
class CLAUDE.md §5 says only a wave catches.

---

## Summary

Nineteen findings. Six are **silent** in the sense the ROADMAP means — the
instrument keeps playing, or keeps looking powered, while being wrong.

| # | Node | What | Loud or silent |
|---|---|---|---|
| **C3-01** | `+12V` raw / `D1`,`D2` / `U-LOADSW` `VCC` | Two mutually exclusive topologies stated for the module's highest-current node | latent |
| **C3-02** | `C-TIMER-LOADSW` | No minimum re-plug interval. Replug inside 2–4 s can latch off | **dark, and mislabelled** |
| **C3-03** | DAC `SYNC`/`SCLK`/`DIN` | Row-offset ribbon: the fix landed on the 10 kΩ pull and not the ~25 Ω driver on the same net | loud (dead DAC) |
| **C3-04** | DAC `AVDD` vs bus `+5V` | No power-up sequencing relationship; no series resistance | **silent (degradation)** |
| **C3-05** | `J-UMB` pin 7 `CS` | Connector break/make during a live transaction is not analysed anywhere | **silent and sticky** |
| **C3-06** | `J-UMB` pin 6 `PWR_GND` | A dirty pin-6 contact reroutes ~360 mA through `DIG_GND` into the analog star | **silent** |
| **C3-07** | etherCON contact set | No make-first/break-last on anything; mate order never stated | latent |
| **C3-08** | `C-BULK-RAIL` / `C1`–`C4` | Page says 4 × 47 µF; its own BOM row says "NOT 47uF on every rail" | latent |
| **C3-09** | all six jacks, rack power-**down** | ~30 ms toward −12 V on every power-down, analysed only in a BOM note | loud but unowned |
| **C3-10** | `PITCH` jack, rack power-on | ADR 0006 says "below −2 V"; the stage says 0.000 V | **silent (in tune-ish)** |
| **C3-11** | `BREATH` jack, instrument absent | ADR 0006's standing offset is 0.2–1.7 V; recomputes to 0.29–2.30 V | latent |
| **C3-12** | `J-CV` ×6 sleeve / `PANEL` | Which net the six jack sleeves tie to is stated nowhere | **silent** |
| **C3-13** | `C-FILT-PITCH`,`C-FILT-MOD`,`C-OUT-BREATH` | These are the ESD front line and none has a voltage rating | loud (dead cap) |
| **C3-14** | `U-TVS-MODULE` | ESD protection is fitted at the end nobody touches | loud |
| **C3-15** | `J-CHAIN` signal conductors | `F-CHAIN` fuses the supply conductor; the four signals get nothing | loud (marker) |
| **C3-16** | `SW1-n` contact material | The gold-vs-silver argument was made for `SW-POWER` and not for 21 key switches | **silent** |
| **C3-17** | `R-KEY-PU` 2.2 k vs 10 k | The recorded trade omits the leakage term humidity actually drives | latent |
| **C3-18** | `R4`/`R5` × `C_diff` | The unplug glide is accidental and written nowhere | latent |
| **C3-19** | `U-LOADSW` `ON` | Undesigned node on a front-panel lever: no divider, pull-down, debounce or ESD path | loud |

Two refuted premises found in passing, both in my slice's argument chain, are in
*Appendix A*.

---

## 1. The umbilical is unplugged mid-note

### What the corpus already says, and it says it well

This is the best-documented failure in the repository. `link-supervision.md`
carries a table of exactly what the deleted watchdog used to cover `[repo]
hardware/module/link-supervision/link-supervision.md:69-76`:

> | Cable unplugged mid-note | caught | **not caught — the DAC holds and the rack drones** |

and states the cost plainly: *"pull the umbilical mid-note and the rack holds
that note until you flip the module's toggle. That is the everyday case, not an
exotic one."* `[repo] link-supervision.md:78-80`. ADR 0004 withdraws its own
mechanism in the same terms `[repo] docs/decisions/0004-cv-interface-module.md:486-490`,
and `ROADMAP.md` E10 books the test `[repo] ROADMAP.md:51`.

Traced per jack, on the steady state after the plug leaves:

| Jack | State | Why |
|---|---|---|
| `PITCH` | **Holds its last value indefinitely** | The DAC keeps `AVDD` from the LM317 and the module keeps bus power. Nothing asserts `CLR` |
| `MOD 1`–`MOD 4` | **Hold their last values indefinitely** | Same. Channel 7 also holds, so the offset term is intact and the outputs are coherent, not railed |
| `BREATH` | Settles to `OFFSET` knob position less a fixed term | `R4`/`R5` 1 MΩ give the in-amp's inputs a DC path, so it rests at `V_REF` rather than saturating `[repo] hardware/interfaces/breath-sense-link/breath-sense-link.md:137` |

So five of six jacks are stuck and one is not — and the corpus's own framing
("a stuck CV is worse than a dead one", ADR 0004 §) applies to five of them. That
is stated and accepted. I have nothing to add to the steady state.

### C3-05 — what happens *during* the unplug is analysed nowhere

**Node: `J-UMB` pin 7 `CS`.** Every treatment of disconnection in the corpus is
of the state *after* the plug is out. I searched the whole design corpus for
`mid-note|unplug|disconnect|live insertion|insertion` and every hit is either
the steady state or the load switch's inrush arithmetic `[repo]`.

The transient is a different problem, and the corpus has already established why
it matters:

- A glitch on `CS` re-frames the 32-bit word, so every bit lands in the wrong
  field — *"including the software-reset and internal-reference-enable bits"*
  `[repo] hardware/interfaces/spi-link/spi-link.md:163-166`.
- `MISO` is deleted, so *"firmware can never read back what the DAC actually
  received"* `[repo] spi-link.md:144-146`.
- It is therefore *"the only failure in the digital path that does not self-heal
  on the next update"* — a **sticky** failure, against the 250 µs self-healing
  of everything else `[repo] spi-link.md:145-147, 163-166`.

The corpus defends `CS` against two glitch sources: intra-pair crosstalk (the
pin-map swap, ADR 0004) and floating inputs (`R-SPI-PULL` ×6). It defends it
against **neither of the two mechanical events that generate the most `CS` edges
in the instrument's life**: pulling the plug, and pushing it back in. A 4 kHz
refresh means a `CS` frame is in flight roughly 12 % of the time at 2 MHz
`[calc: 6 × 32 bits / 2 MHz = 96 µs of each 250 µs pass = 38 %`, actually — see
the loop budget's own `96.0 µs` figure `[repo] spi-link.md:117`, so **38 %**].
Contact bounce on break is a burst of edges, not one edge, and it lands inside a
word 38 % of the time.

**What a mis-framed word can write.** The DAC8568 command field is at the top of
the word, so a bit-count shift changes the command, not just data. Three of the
reachable outcomes are sticky and invisible:

- **Clear-code register.** `mod-channels.md` builds its entire safe-state
  argument on `CLR` producing zero scale `[repo]
  hardware/module/mod-channels/mod-channels.md:150-176`. The clear code is a
  writable register. A mis-framed word that rewrites it means the *next* `CLR`
  — the power-on reset, which ADR 0006 says happens on every rack power-up —
  parks four jacks somewhere else.
- **Internal-reference enable.** Disabling it takes `VREFOUT` to zero, which
  takes pitch's `V_ref` and the mod offset with it.
- **Software reset.**

`firmware/README.md` already names this exact shape: *"The same shape of bug is
latent in every other register the DAC holds that firmware writes once: the
internal-reference enable, and the clear-code register itself"* `[repo]
firmware/README.md:71-73` — and its answer is the statelessness rule, refreshing
sticky registers periodically. **That rule is what closes C3-05**, and it is
sized against a *firmware* fault, not against a mechanical one. Nothing states
the refresh interval for the sticky set ("a word every few thousand passes"
`[repo] firmware/README.md:78`), so the window between a plug event and the next
sticky-register refresh is undefined and could be seconds.

**Would it be loud?** No. A rewritten clear code does nothing at all until the
next power cycle, at which point four mod jacks come up somewhere other than 0 V
— and ADR 0006's power-on table, which is the document someone would check, says
they come up at exactly 0 V. This is the worst diagnostic shape in the project:
a fault installed by one physical act, expressed by a different one, hours later.

**Recommendation to the wave, not a fix:** the cheapest answer is a firmware
requirement, not a part — rewrite the clear-code register and the reference
enable every N passes with N small (tens of milliseconds), and say so in
`firmware/README.md` with the plug event as the stated reason. The second-
cheapest is the `74AHCT14` that `link-supervision.md` already wants for three
other jobs `[repo] link-supervision.md:105-118`; Schmitt hysteresis on `CS` is
what turns bounce into one clean edge instead of twelve.

### C3-18 — the one unplug transient that behaves, and it does so by accident

**Node: `R4`/`R5` × `C_diff`.** On break, `C_diff` (15 nF) discharges through the
two 1 MΩ bias resistors in series `[repo] breath-sense-link.md:137-142`:

```
τ = 15 nF × 2 MΩ = 30 ms          [calc]
```

So `BREATH` **glides** from mid-note to its rest position over ~30 ms rather than
stepping. That is why E10's *"breath parks quietly"* test will pass — and the
mechanism is written in no document. Anyone who later reduces `R4`/`R5` to
100 kΩ (the reflexive value for in-amp bias resistors) gets `τ` = 3 ms and turns
a glide into a click, with no line anywhere to warn them. `R4`/`R5` have their
own justification on the page (bias return, ADR 0005's withdrawn
`R-PD-BREATH` blockquote `[repo] docs/decisions/0005-power-architecture.md:358-372`)
and that justification does not mention the time constant at all.

---

## 2. The umbilical is hot-plugged

### What the corpus says

`umbilical-load-switch.md` treats hot-plug as **the** sizing case and does it
thoroughly `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:210-228`:
17.1 ms through the foldback ramp plus 30.4 ms at 940 mA less load, **47.5 ms
entirely in current limit**, against a worst-case fault timer of **95.6 ms** —
a stated **2.01×** margin. The `FB` divider is sized, `C-GATE` and `C-TIMER` are
sized, and ADI's own reference gate network is copied in. This is good work and I
found no arithmetic error in it.

It is, however, the **only** thing about hot-plug that is analysed. It answers
"how much current, for how long". It does not answer "in what order do the eight
contacts meet, and what is alive while only some of them have".

### C3-07 — no make-first/break-last on anything, and the mate order is never stated

**Node: the etherCON contact set, `J-UMBILICAL`.** An 8P8C/RJ45 contact block has
eight identical leaf contacts in one row. There is no sequenced, staggered or
early-mate contact on any of them `[from memory — the NE8FDP and NE8MC drawings
are banked at `datasheets/connectors/NE8FDP.pdf` and `NE8MC.pdf`, so this is
checkable in-repo and should be]`. The etherCON **shell** engages before the
contacts, but the shell is chassis/shield, not `PWR_GND` — and the shield policy
is, in `power-entry.md`'s own words, *"sixteen words in the whole repo"* `[repo]
hardware/module/power-entry/power-entry.md:140`.

Mate skew on a hand-inserted RJ45 comes from insertion angle and contact
tolerance and is not controlled. So during a hot-plug there is a window — short,
but real, and repeated on every insertion — in which some of these are connected
and some are not:

| Pins | Signal | What it is if it mates early or late |
|---|---|---|
| 3, 6 | `+12V` / `PWR_GND` | The supply and its only intended return |
| 1, 2 | `BREATH` / `AGND` | `AGND` is **an in-amp input, not a ground** `[repo] ADR 0004:602-640` |
| 7, 8 | `CS` / `DIG_GND` | `DIG_GND` is a ground, and where it ties is `dig-gnd-topology`, **DISPUTED** |
| 4, 5 | `SCLK` / `MOSI` | — |

**Pin 3 before pin 6 is the case that matters.** If `+12V` mates while
`PWR_GND` has not, the instrument's inrush current — current-limited at 940 mA,
not at zero — has to return through whichever ground conductor *has* mated.
There are two candidates and both are wrong:

- **Pin 8 `DIG_GND`.** At the module it ties to the analog star (per
  `digital-and-supervision.md`) or to the pour under the SPI trace (per
  `power-entry.md`) or to its own path to the star (per ADR 0004) — the figure
  records all three and is DISPUTED `[repo] config/figures.yaml:387-398`. On
  **any** of the three, up to 940 mA of inrush transits a conductor sized for
  SPI return current and lands in the module's quiet copper.
- **Pin 2 `AGND`.** Bounded, and bounded by accident: the instrument-side
  `R1b` 1 kΩ is in series, so the worst case is ~12 mA into the module-side
  `BAV99` `[calc: 12 V / 1 kΩ]`, dissipating ~144 mW in an instrument-side 1206
  during the event `[repo] breath-sense-link.md:134]`. Survivable. But `R1b`
  exists for CMRR balance `[repo] breath-sense-link.md:192-197]`, and it is the
  only thing standing between a partial mate and the INA828's input structure.
  Nothing says so.

**Nothing in the corpus states a requirement on mate order**, nor records that
none is available. That is the finding: not that the design is wrong, but that
the one connector property that governs hot-plug safety is undocumented on a
connector the design explicitly invites hot-plugging into (*"etherCON invites
live insertion"* `[repo] umbilical-load-switch.md:211`).

This is worth an E6/E11 bench item alongside the current-probe measurement the
ROADMAP already books: insert the plug slowly and at an angle, twenty times,
with a scope on `DIG_GND`-to-module-star.

### C3-02 — replug inside two to four seconds and the load switch latches off. Nobody has named this.

**Node: `C-TIMER-LOADSW`.** This is the most concrete new failure I found and it
is reachable by the single most natural human action at this connector.

A successful hot-plug spends 47.5 ms entirely in current limit, during which the
`TIMER` pin is charged by the 80 µA (−24/−80/−132 µA) pull-up `[repo, datasheet
164112fc p.2, p.8 as quoted on umbilical-load-switch.md:170-180]`. On worst-case
silicon `[calc, the page's own worst-case net ramp of 129 µA]`:

```
V_TIMER after a successful hot-plug = 129 µA × 47.5 ms / 10 µF = 0.613 V
                                    = 49.7 % of the 1.233 V fault threshold
```

which is the other face of the page's own stated 2.01× margin, and the page gets
there `[repo] umbilical-load-switch.md:226-228`.

**What the page does not do is ask how long that 0.613 V takes to go away.** The
datasheet's own figure, as the page quotes it, is a **3 µA** pull-down `[repo]
umbilical-load-switch.md:176, quoting 164112fc p.8]`, with a specified range of
1.5 / 3 / 5 µA `[repo] umbilical-load-switch.md:178`:

```
recovery at 3 µA typ :  0.613 V × 10 µF / 3 µA   = 2.04 s
recovery at 1.5 µA min: 0.613 V × 10 µF / 1.5 µA = 4.09 s      [calc]
```

**The fault timer takes 2.0 to 4.1 seconds to recover from a start that took
47.5 milliseconds — 43 to 86 times longer than the event it is recovering
from.** Plug the cable in, feel it not seat, pull it and push it again — which is
what everyone does — and the second start begins from a partly-charged `TIMER`
with less than the 47.5 ms it needs. On worst-case silicon it **latches off**,
and the `-1` suffix means it stays latched *"until you deliberately cycle the
panel toggle"* `[repo] umbilical-load-switch.md:311-313`.

**And the indication is actively misleading.** `panel-led.md` already establishes
that `LED-PANEL` runs from `+12 V analog`, which *"is live whenever the rack
is, so the LED is lit in every one of the latching faults"* `[repo]
hardware/module/panel-led/panel-led.md:33-42`. So the observed behaviour is: you
plug the instrument in, the module's power LED is lit, and the instrument is
dead with no indication anywhere that a toggle cycle is the remedy. That page
already calls the fix *"cheapest high-value fix in the review"*; C3-02 is a
second, independent, and considerably more everyday reason for it.

**Two things follow that the corpus should state and does not:**

1. **A minimum re-plug interval exists and it is seconds.** It belongs on the
   page, in ADR 0005, and on the panel if anything is ever silkscreened.
2. **`C-TIMER` at 10 µF was chosen to buy hot-plug margin** (*"the reason for
   10 µF rather than 9.4 µF"* `[repo] umbilical-load-switch.md:228`) and the
   same choice buys the longest possible recovery time, because both scale with
   `C`. The trade was taken on one side only. A smaller `C-TIMER` with the
   `-2` part, or a discharge path, or accepting 1.89× instead of 2.01×, are all
   live options that the analysis as written cannot see.

The same unaccounted `TIMER` charge applies to **toggle bounce** — see C3-19.

### C3-01 — the module's highest-current node has two mutually exclusive topologies

**Nodes: `+12V` at `J-PWR-EURO`, `D1`, `D2`, `U-LOADSW` `VCC`, `R-ILIM`.**
Two Interfaces tables and one drawing disagree about where the umbilical branch
is taken, and the answer decides the reverse-polarity and umbilical-fault
behaviour of the whole module.

**Reading A — ahead of the diodes.** Both Interfaces tables say this, and one
calls it the point of the circuit split:

> `+12V` ahead of `D1`/`D2` | out | `module/umbilical-load-switch` | — | The
> branch is taken **before** the diodes; `U-LOADSW`'s `VCC` and the top of
> `R-ILIM` hang off it
> `[repo] hardware/module/power-entry/power-entry.md:28`

> `+12V` ahead of `D1`/`D2` | in | `module/power-entry` | — | `U-LOADSW`'s
> `VCC` and the top of `R-ILIM`. Taken before the entry diodes, **which is the
> point of the split**
> `[repo] hardware/module/umbilical-load-switch/umbilical-load-switch.md:15`

**Reading B — behind `D2`.** The drawing shows `+12V` branching into two
parallel Schottkys, `D1` feeding the analog rail and `D2` → `FB2` → `C2`
feeding the node the load switch hangs on `[repo] power-entry.md:39-52`. The
prose section that owns the decision requires it: the two diodes are kept for
*"fault isolation between the exported rail and the analog rail, and HF
isolation (`r_d` is 69 mΩ at 392 mA)"* `[repo] power-entry.md:111-114`, and
`config/figures.yaml`'s `diode-split-rationale` carries the same `[repo]
config/figures.yaml:467-470`.

**They cannot both be true, and the difference is not cosmetic:**

- **Under Reading A, `D2` has no load and no function at all.** Nothing flows
  through it; the "fault isolation between the exported rail and the analog
  rail" is provided by `D1` alone, which reverse-biases when the raw node
  collapses. The project would be buying and stuffing a diode for a job that a
  different diode is already doing — and `power-entry.md` explicitly warns that
  *"Left as it was, the next reviewer who checks the arithmetic deletes the
  part"* `[repo] power-entry.md:114`. Under Reading A, that reviewer would be
  right.
- **Under Reading A, `U-LOADSW` and the pass FET sit ahead of every
  reverse-protection diode in the module.** The LT1641's `VCC` and `SENSE` pins
  and the FET's drain are connected directly to the bus `+12V` pin. On a
  reversed ribbon they see −12 V with nothing in series. That flatly refutes the
  claim, stated twice, that a reversed or row-offset ribbon *"kills the buffer
  and nothing else"* `[repo] docs/decisions/0004-cv-interface-module.md:213` and
  `[repo] power-entry.md:137` — the LT1641 is not a $0.30 part and it is the
  part on which the instrument's power depends.
- **Under Reading B**, both branches are protected, `D2` earns its place, and
  the "kills the buffer and nothing else" claim survives for the ±12 V rails.

Reading B is almost certainly the intent. That does not close it: **the
Interfaces tables are the machine-readable half of this corpus's own convention,
they are the thing a layout gets built from, and both of them say Reading A.**
`pitch-stage.md` makes precisely this point about prose in another context —
*"prose is what a layout gets built from"* `[repo] pitch-stage.md:247`.

---

## 3. A jack is shorted tip-to-sleeve

### What the corpus says, and it is the best-handled item in my slice

This is genuinely well covered. `pitch-stage.md` names the everyday case
explicitly `[repo] pitch-stage.md:268-271`:

> **With the jack shorted, DC feedback is exactly zero** and the amp rails. A
> 3.5 mm plug shorts tip to sleeve on every insertion, so every patch-in is a
> brief rail excursion recovering through the loop.

and the `R-OUT-PROT` BOM row has been through two rounds of worst-case
dissipation analysis, ending at a specified **0.66–1 W 1206 (ERJ-P08 class)**
with thick-film derating at a 50 °C rack interior accounted for `[repo]
hardware/bom.csv:87 / hardware/module/bom.csv:1`. That row explicitly identifies
itself as *"the ONLY part in the module at real risk from any jack fault"*, and
having traced all six output stages I agree with it.

Traced per stage:

| Stage | Feedback tap | On a tip-sleeve short |
|---|---|---|
| `PITCH` | **at the jack** | β = 0, op-amp rails, 1 kΩ carries ~11.5 mA, **142 mW** `[repo] bom.csv R-OUT-PROT`. Recovers through the loop when the short clears |
| `MOD 1`–`4` | op-amp output | `R-OUT-PROT` isolates. Op-amp holds its target; 1 kΩ dissipates `V²/1k` ≈ 100 mW at 10 V `[calc]` |
| `BREATH` | op-amp output | Same. `C-OUT-BREATH` 330 nF discharges into the short — a one-off 16 µJ `[calc: ½·330n·10²]`, harmless |

Pitch is the outlier and the page knows it. **The one thing I would add:** the
short clears at the instant the plug's tip reaches the jack's tip, so the
destination module is connected for the recovery. That recovery is an
audible pitch glitch on every single patch insertion, and neither its duration
nor its shape is anywhere. E9's load sweep already lists "a short" as one of
the cases `[repo] ROADMAP.md:199` — the ask is to scope the *recovery* there,
not just the steady state.

### C3-13 — the jack-side caps are the ESD front line and none has a voltage rating

**Nodes: `C-FILT-PITCH`, `C-FILT-MOD`, `C-OUT-BREATH`.** `D-JACK-CLAMP` was
deliberately moved to the **driver** side of `R-OUT-PROT`, for two good reasons
the BOM row gives in full — back-powering current (42 mA/jack at the jack
versus 7.6 mA behind the 1 kΩ) and leakage error going to zero inside the loop
`[repo] hardware/module/bom.csv:3`.

The consequence is that at the jack node itself, on the panel, with a finger and
a patch cable approaching it, **the only component is the filter capacitor.**
The clamp is 1 kΩ away. That is the right trade — but it changes which part
takes an ESD strike, and the three rows were not revisited:

```
8 kV HBM (150 pF, 330 Ω) into C-FILT-PITCH 10 nF, charge-shared:
   8000 V × 150 pF / (150 pF + 10 nF) = 118 V                 [calc]
into C-FILT-MOD 82 nF:  8000 × 150p/82.15n =  14.6 V          [calc]
into C-OUT-BREATH 330 nF: 8000 × 150p/330.15n = 3.6 V         [calc]
```

`C-FILT-PITCH` is specified **0805 C0G/NP0, no voltage rating** `[repo]
hardware/bom.csv:83`. `C-FILT-MOD` is **1210 or film — VERIFY, no voltage
rating** `[repo] hardware/bom.csv:85`. `C-OUT-BREATH` is **330 nF film, no
voltage rating** `[repo] hardware/bom.csv:69`. A 0805 C0G in the default 50 V
grade is under-rated by 2.4× for the pitch jack.

The HBM model is `[from memory]` and is the conservative one for a finger; the
arithmetic is what matters, and it says pitch is thirty times more exposed than
breath because its cap is thirty times smaller. Specify the voltage rating on
all three rows, and note that pitch's is the one that is set by ESD rather than
by the signal.

---

## 4. An output is patched to another module's output

### What the corpus says

Covered, and well, in one place: the `R-OUT-PROT` BOM row, which is where the
worst case was found and twice revised `[repo] hardware/module/bom.csv:1`:

> Pitch against a 220R output at −5V in output-to-output patching: 192mW steady
> state, because the loop **FIGHTS** the other module now that the jack is the
> feedback node. […] 2026-09-21: RATING RAISED. Two reviewers independently
> found the stated worst case understated ~2x — 322mW (output-to-output against
> a 220R source at +/-10V)

I re-derived the binding case and it stands:

```
PITCH commanded −2 V, other module driving +10 V through 220 Ω.
Pitch's loop sees the jack at +10 V, not −2 V, so it rails to −11.45 V.
I = (10 − (−11.45)) / (1 kΩ + 220 Ω) = 17.6 mA
P(R-OUT-PROT) = 17.6 mA² × 1 kΩ = 310 mW                         [calc]
```
which agrees with the row's 322 mW to within the assumed source resistance.

**The structural point the row makes is the important one and it is easy to
miss:** the jack-side feedback tap that makes pitch load-independent (`pitch-stage.md`'s
best change) is exactly what makes it *fight* another driver instead of
politely dividing against it. Load-independence and fault-passivity are the same
knob turned opposite ways, and only one page says so — the BOM row, not the
schematic page. `pitch-stage.md` lists two new E9 bounds created by the tap
(ringing into capacitive loads, and railing on a short `[repo]
pitch-stage.md:262-271`) and **does not list output-to-output**, which is the
third and the one with the thermal consequence.

No new finding here beyond that asymmetry, which is worth a cross-reference on
the page.

---

## 5. Rack power cycles, browns out, or comes up slowly

### C3-04 — bus `+5V` and DAC `AVDD` have no stated sequencing relationship, and no series resistance between them

**Node: DAC8568 `SCLK`/`DIN`/`SYNC`.** This project has the sequencing habit and
applies it twice, correctly and explicitly:

- `R-ADCDIV`: *">=10k upper leg: 5V-before-3V3 sequencing otherwise pushes
  ~2.5mA into the ADC ESD clamp on every power-up"* `[repo] hardware/bom.csv:20`
- `R-OPAMP-IN`: *"DAC on 5.21V and op-amps on +-12V do not come up together;
  bounds clamp current"* `[repo] hardware/bom.csv:2`

The third interface of the same kind is between the **74AHCT125 on bus `+5V`**
and the **DAC8568 on `AVDD` from the LM317**, and it has neither an analysis nor
a series element. The drawing shows buffer outputs going straight to the DAC
pins, with only the DAC-side `R-SPI-PULL` on the net `[repo]
hardware/module/digital-and-supervision/digital-and-supervision.md:57-72`.

These two rails are structurally guaranteed *not* to come up together:

```
bus +5V  : rack +5V through FB4/C4. Up when the rack's 5 V rail is up.
DAC AVDD : rack +12V → D1 (Vf ~0.3 V) → FB1/C1 → LM317 (dropout ~1.7 V)
           → AVDD only once +12V exceeds ~7 V                     [calc]
```

`OE` is tied permanently enabled `[repo] digital-and-supervision.md:31`, so the
buffer drives the instant its own rail is up. With the cable-side pulls holding
`CS` high, the buffer's `SYNC` output is **driven high at ~4.4 V into a DAC
whose `AVDD` is still climbing through 0 V**. Digital inputs on a single-supply
DAC are conventionally abs-max'd at `AVDD + 0.3 V` `[from memory — SBAS430E is
banked at `datasheets/analog/DAC8568CIPW.pdf` and the abs-max table should be
read before this is dismissed]`, and the only current limit is the 74AHCT125's
own output impedance.

**Why it is silent.** Injecting into a CMOS input clamp on every power-up does
not usually kill the part; it degrades it, and it can trigger latch-up. The
symptom is an instrument that works, then one day does not, with nothing in the
history to point at. The corpus's two other instances were both caught at design
time for exactly this reason; this one was not, and it is the instance with the
lowest series impedance of the three.

The `R-SPI-PULL` row shows the analysis was *started* on this net and stopped one
component short — see C3-03.

### C3-03 — the reversed/row-offset ribbon fix landed on the 10 kΩ pull and not on the driver on the same net

**Node: DAC8568 `SYNC` (and `SCLK`, `DIN`).** The `R-SPI-PULL` row contains a
genuinely good catch and its own remedy `[repo] hardware/bom.csv:44`:

> **DAC-SIDE CS PULLS TO AVDD** (the LM317's 5.21V), not bus +5V — a pull-up
> belongs on its consumer's rail, and **on the bus rail a reversed ribbon
> reaches the DAC's SYNC pin and turns a $0.30 buffer failure into a DAC
> failure**

That is exactly right, and it was acted on. But the 10 kΩ pull-up is not the
lowest-impedance thing connecting bus `+5V` to the DAC's `SYNC` pin. **The
74AHCT125's output is**, and it is still there, still powered from bus `+5V`,
still `OE`-enabled, and still connected with no series resistance.

Trace the fault the row itself names. Any mis-insertion that puts a rail above
7 V on the module's bus-`+5V` pin — reversal, or the classic row-offset
`[from memory: the Doepfer 16-pin bus pin order; the offset-by-one-row case is
named in ADR 0004 itself at line 213, so the corpus accepts it as reachable]` —
puts that voltage on the 74AHCT125's `VCC` against a 7 V absolute maximum
`[from memory; SCLS264O is banked at `datasheets/logic/SN74AHCT125.pdf` and the
corpus quotes its abs-max input range as −0.5 to 7 V `[repo]
hardware/unplaced.csv:20`]`. Before the part fails, and again after it fails
short, its **output** presents that voltage to the DAC pin.

So the module's protection against a mis-inserted ribbon reads, as built:

| Node | Protection | Adequate? |
|---|---|---|
| `+12V` analog | `D1` series Schottky | Yes — blocks for any wrong polarity |
| `+12V` umbilical | `D2` (**or not — see C3-01**) | Depends on C3-01 |
| `−12V` | `D3` series Schottky | Yes |
| bus `+5V` | **none, by decision** | The buffer dies. Accepted |
| DAC `SYNC`/`SCLK`/`DIN` | the pull moved to `AVDD` | **No — the driver was not moved and cannot be** |
| `C4` (`C-BULK-RAIL`, electrolytic, on bus `+5V`) | **none** | **No — see C3-08** |

The claim *"a reversed ribbon that kills the buffer and nothing else is an
acceptable outcome"* is stated at `[repo] power-entry.md:137` and `[repo] ADR
0004:213`, and `digital-and-supervision.md`'s own Still-open blockquote already
contradicts it from the other side `[repo] digital-and-supervision.md:87-96`:

> it is what makes a reversed 16-pin ribbon **dangerous** (module ground lands
> on bus +5 V and +12 V) […] on a branch whose **bulk capacitor vents when
> reverse-biased**

Two live pages, opposite conclusions, same fault. The third page — the BOM — has
the mechanism for the DAC half and applied it to one of the two parts on the net.

### C3-08 — the drawing says 4 × 47 µF; its own BOM row says "NOT 47uF on every rail", and says why

**Node: `C-BULK-RAIL` / `C1`–`C4`.** The schematic page draws `C1 47µF`,
`C2 47µF`, `C3 47µF`, `C4 47µF` `[repo] power-entry.md:39,46,72,74` and states
in prose *"**Entry bulk is 4 × 47 µF**, which is 2–5× the surveyed norm of
10–22 µF"* `[repo] power-entry.md:171`.

The BOM row that generates the part is emphatic in the other direction `[repo]
hardware/bom.csv:122`:

> **NOT 47uF on every rail.** The +12V branch carries the LM317's divider, the
> DAC and the comparator, about 22mA against -12V's 10mA — so at 47uF each it
> collapses 2.2x faster and **every rack power-down leaves the op-amps with V+
> near 0 and V- at -6 to -8V for ~30ms, pulling all six jacks toward the
> surviving negative rail.** 100uF on +12V balances the decay.

Value: `"100uF (+12V) / 47uF (-12V, +5V) 25V electrolytic"`, qty 4.

This is the most consequential page-versus-BOM disagreement I found, because the
page is the thing a board gets stuffed from and the row is the only place in the
corpus that reasons about power-**down** at all. The checker cannot see it:
`C-BULK-RAIL` is not a tracked figure, and `python3 tools/check-staleness.py`
passes `[repo]`.

**And the row's own premise has decayed.** Its load list is *"the LM317's
divider, the DAC and the comparator"*. The comparator is the LM311 presence
detect, which is **deleted and never had a BOM row** `[repo]
hardware/module/link-supervision/link-supervision.md:1-8`. The 22 mA figure the
100 µF choice rests on therefore includes a part that does not exist. The
conclusion probably survives — the LM317 divider alone is ~35 mA at 150 Ω/475 Ω
`[calc: 5.21 V / (150 + 475)`, and the asymmetry is real either way] — but the
number was not re-derived, and this is exactly CLAUDE.md §5's "an argument
survives its own refutation".

### C3-09 — nothing owns what the six jacks do on rack power-DOWN

**Node: all six CV jacks.** ADR 0006 has a power-**on** table, three rows, with
its reasoning `[repo] docs/decisions/0006-cv-channel-allocation.md:197-201`. There
is no power-**down** table anywhere, and the only power-down analysis in the
corpus is the BOM note quoted above — which describes **all six jacks being
pulled toward −12 V for about 30 ms on every single rack power-down**, into
whatever is patched.

That is not exotic: it happens every time the rack is switched off. Whether 30 ms
of −6 to −8 V into a VCA or a filter's CV input matters is a question the corpus
has never asked, and the one document that computed it is a CSV cell.

Three things follow:

- The behaviour belongs in ADR 0006's table as a second column, next to
  power-on, where the reader who cares about jack states looks.
- It is an M8 failure-injection item (M8 already books "failure injection"
  generically `[repo] ROADMAP.md:78`) — scope all six jacks through a rack
  power-down with the module racked.
- It interacts with C3-08: the whole point of 100 µF on `+12V` is to *reduce*
  this excursion, and the schematic page specifies the value that maximises it.

### C3-10 — `PITCH` at rack power-on is 0 V, not subsonic, and ADR 0006 still says subsonic

**Node: `PITCH` jack, before firmware's first DAC write.**

ADR 0006's table, column headed *"At rack power-on, before firmware writes"*
`[repo] docs/decisions/0006-cv-channel-allocation.md:197-201`:

> | **Pitch** | Bottom of its range, below −2 V | Subsonic. A VCO there is inaudible |

`pitch-stage.md` derives the opposite and flags the contradiction explicitly
`[repo] hardware/module/pitch-stage/pitch-stage.md:134-139`:

> **Power-on is 0.000 V, not "subsonic".** `V_ref` is the DAC's internal
> reference, which is **disabled until firmware writes an enable** — so *both*
> terms are zero and the jack sits at **0 V, a VCO's base note**, until that
> write. After it, `CLR` parks at −2.500 V. **ADR 0006's power-on table asserts
> "below −2 V" for both; they are different states, 2.5 V apart.**

The stage page is right. `Vout = 2·Vdac − 2.500` requires `V_ref` = 2.500 V,
which requires `VREFOUT`, which is disabled at reset — ADR 0006 says so **itself**,
eighteen lines below its own table `[repo] ADR 0006:227-230`:

> the internal reference is disabled by default and needs an explicit enable
> write at boot […] It also means the outputs sit at 0 V from rack power-on
> until firmware enables the reference, **which happens to reinforce the table
> above.**

It does not reinforce the table above. It refutes the pitch row of it. 0 V is
the only row of the three that the sentence contradicts, and the sentence was
written as though it confirmed all three.

**The failure this hides.** Power the rack up with the instrument absent or not
yet booted, and pitch sits at a VCO's **base note**, not below the audible
range — so a patched, self-oscillating VCO or an open VCA sounds a note at
power-on. `pitch-stage.md` calls the reference-enable-first requirement *"the
sticky-register set that gets periodically refreshed"* `[repo]
pitch-stage.md:150-152`, which means the window is bounded by firmware boot
time, not by anything in hardware. It is loud when you hear it and silent in the
document someone checks.

**The fix that is not a fix:** correcting ADR 0006's table. The stage page has
been correct since it was drawn and the ADR has been wrong the whole time; this
is the "fixes land where the editing is happening, not where the reader looks"
failure in its pure form, on a page that has *already been told* it is wrong by
the page below it.

### C3-11 — the standing breath offset with the instrument absent recomputes to 0.29–2.30 V, not 0.2–1.7 V

**Node: `BREATH` jack, instrument absent or unpowered.** ADR 0006's blockquote
`[repo] ADR 0006:208-214`:

> the two 1 MΩ bias resistors hold the in-amp's *inputs* at module `AGND`, so
> with the instrument absent the in-amp rests at `V_REF` = `breath-zero-ref` […]
> and the gain-and-offset stage then puts the jack at the **OFFSET knob's
> position less 0.2 to 1.7 V**, depending on where GAIN is set

Recomputed from the figures the owning pages now carry:

```
breath-zero-ref                    = 0.573 V   [repo] config/figures.yaml:92-96
output stage: buffered attenuator 0.125 … 1.000, then inverting × R-FB/R-IN
R-FB = 40.2 kΩ, R-IN = 10 kΩ → 4.02          [repo] breath-output-stage.md values table

min:  0.573 × 0.125 × 4.02 = 0.288 V
max:  0.573 × 1.000 × 4.02 = 2.303 V                             [calc]
```

So the jack sits at the OFFSET knob's position **less 0.29 V to 2.30 V**. The
ADR's 1.7 V upper bound is 26 % low and neither bound is reproducible from any
combination of live figures I could construct.

This is a derived-value staleness of exactly the kind CLAUDE.md §1 exists to
prevent — and it is invisible to the checker because it is a *derived* pair of
numbers in a document that cites the figure it is derived from. The register has
no entry for this quantity. If the wave wants one fix here, it is to add the
standing offset to `config/figures.yaml` with `breath-output-stage.md` as owner,
so ADR 0006 cites it instead of restating it.

### Brownout and slow ramp — traced, nothing new

- **Instrument buck drops out at 8 V while the analog holds to ~7.2 V** — ADR
  0004 names this and calls the result correct: *"the MCU dies, SPI stops, `CLR`
  fires, and breath keeps working"* `[repo] ADR 0004:521-525`. I checked the
  premise: `CLR` firing requires something to assert it, and **nothing does** —
  `R-CLR-PU` holds it inactive and the only asserter is a hand solder pad
  `[repo] hardware/module/dac8568/dac8568.md:19`. So on a sagging cable, pitch
  and the mods **hold**, they do not park. This is the same withdrawal that
  `link-supervision.md` made for the unplug case, applied consistently; ADR
  0004's sagging-cable paragraph was not updated with it. Filed in *Appendix A*
  rather than as a finding, because the downstream conclusion (breath keeps
  working) is unaffected.
- **LT1641 `VCC` UVLO at 7.5/8.3/8.8 V** holds `GATE` low below that regardless
  of `ON` `[repo] umbilical-load-switch.md:190,299-303]`, which correctly makes
  a slow rack ramp a non-event at the module.
- **Case-wide inrush** is named as an open item and correctly scoped
  `[repo] power-entry.md:170-173`.

---

## 6. A key switch fails closed, or its conductor shorts

### What the corpus says

**Stuck-closed is one of the three named silent failures** in the ROADMAP, with
the right diagnosis and a free firmware fix `[repo] ROADMAP.md:213-217`:

> Does not kill a note. Silently returns a *different* note for every fingering
> that key participates in […] Flag any key closed at boot, or held beyond N
> seconds, as suspect and report it

I have nothing to add to that; it is correct and it is the best-handled silent
failure in the project.

**A conductor shorting to a neighbour** is largely designed out by the ADR 0001
topology: the key network sits millimetres from its switch on the cluster board,
so *"There is no loom conductor between the switch and the register input for
anything to couple into"* `[repo]
hardware/interfaces/key-chain-loom/key-chain-loom.md:159-163`. A neighbour short
is then a PCB-fabrication fault, not a wiring one, and it presents as a stuck
key, caught by the boot check above.

### C3-15 — `F-CHAIN` fuses the supply conductor; the four signal conductors share the same channel with the same 12 V

**Node: `J-CHAIN` pins 2 (`SCK`), 4 (`SH/LD`), 6 (`SER`), 8 (`QH`).**
The corpus identifies the hazard precisely, for one conductor out of six
`[repo] key-chain-loom.md:142-147`:

> **`F-CHAIN`, or not.** The 3V3 conductor leaves this board, runs 265 mm
> through a bonded body next to 12 V LED power, and comes back as nothing. A
> short on it browns out the dev board's LDO and takes the instrument down with
> no diagnosis.

Everything in that sentence is equally true of the four signal conductors in the
same ribbon, in the same channel, beside the same 12 V. And the consequences are
worse, because the signals land on parts with no headroom:

```
12 V onto SCK / SH/LD / SER : reaches an ESP32-S3 GPIO through R-CHAIN-SER 100 Ω
                              → 12 V / 100 Ω ≈ 120 mA into the pad clamp   [calc]
                              and reaches four 74HC165 CLK / SH/LD pins with
                              NOTHING in series (the loom goes straight to them)
12 V onto QH                : QH is a DRIVEN 74HC165 output. Nothing in series.
```

`U-TVS-CHAIN` is the proposed answer and it is **`open`, not in the BOM as a
fitted part** `[repo] hardware/bom.csv:49`. Even fitted, it is a 5 V array at
the **carrier** end only; it does not reach the cluster-board end of any of the
four conductors, and the corpus's own reading of the sister part establishes
that this class of array has a **0.225 W** package ceiling and no pulse rating
at all `[repo] hardware/bom.csv:46, from the banked SP0504BAHT]` — 12 V into a
clamp is watts, so the array would be the first thing to die and would die
shorted.

**Loud, and that is worth saying explicitly.** A dead 74HC165 takes eight bits
with it, and the 8-bit marker pattern — one high and one low strap per device —
catches a device that is *"dead, unclocked, stuck high or stuck low […] whichever
way it failed"* `[repo]
hardware/cluster/key-marker-and-bits/key-marker-and-bits.md:58-64`. So this
failure announces itself on the error counter, which is precisely what the two
extra marker bits were bought for. **The marker pattern is doing a job nobody
credited it with**, and it is the reason this finding is a cost item and not a
disaster.

The ask is small: either extend `F-CHAIN`'s argument to say why the four
signals do *not* need equivalent treatment, or note that they do and that the
marker pattern is the mitigation. At present the page reasons about one
conductor of six and is silent about the other five.

### C3-16 — the gold-versus-silver contact argument was made for one switch and not for the twenty-one unretrofittable ones

**Nodes: `SW1-n` (21), `SW-THUMB` (4).** The `SW-POWER` BOM row contains what is,
by some distance, the best contact-reliability analysis in this repository
`[repo] hardware/bom.csv:54`:

> **THE CONTACT MATERIAL IS THE SUBTLE ONE:** W is silver-over-silver rated at
> POWER level 6A@125VAC, G is gold rated at LOGIC level 0.4VA max @ 28V […]
> This switch drives the LT1641 ON pin, whose input current is 1uA MAX — three
> orders of magnitude below any silver contact's wetting current, where silver
> oxidises and goes intermittent. NKK's own example part number in the catalogue
> is M2012SS1W01, i.e. silver — copying it would be a reliability fault that
> only shows up after months.

The identical question applies, with more force, to the twenty-one key
switches — and neither `SW1-n` nor `SW-THUMB` asks it `[repo] hardware/bom.csv:33,38]`.
`SW1-n` reads: *"KS-33 Red (linear) […] Binary. Plate cutout must be measured.
Soldered."* No contact material, no plating, no wetting-current figure.

The conditions are worse than `SW-POWER`'s in every respect except current:

- **Current is 1.43 mA per closed key** `[repo] config/figures.yaml:124-128`,
  i.e. ~4.7 mW at 3.3 V. Higher than the toggle's 1 µA, and still well inside
  dry-circuit territory `[from memory: silver wetting current is conventionally
  tens of mA]`.
- **Environment is a sealed oak box, breathed into for hours, running 10–20 K
  above ambient**, with the contacts open — the corpus's own description
  `[repo] hardware/cluster/key-switch-network/key-switch-network.md:112-120`.
- **They are soldered into boards inside the body.** `SW-POWER` is on a panel
  behind four screws. Replacing a key switch means a strip-down.
- **The failure is the project's named silent one.** An intermittent contact
  presents as *"some fingerings feel wrong"*, which the ROADMAP already
  identifies as *"unfalsifiable by ear"* `[repo] ROADMAP.md:215`.

**And the one argument that would settle it is in a file that is not the
corpus.** `docs/research/2026-09-21-eurorack-prior-art/R10-keyscan-and-adc.md`
contains the wetting-pulse derivation — *"a 10 nF discharging through 100 Ω at
closure gives a ~33 mA, ~1 µs, 54 nJ wetting pulse that is good for gold
contacts and far too small to weld them"* `[repo, historical record — read only
to establish that the argument exists and did not land]`. That is the right
analysis and it never reached a live page. Worse, the value moved: the corpus
now specifies `C-KEY` at **47 nF**, not 10 nF, which gives

```
½ × 47 nF × 3.3² = 256 nJ per closure, peak 33 mA, τ = 4.7 µs     [calc]
```

— 4.7× the energy, i.e. *better*, and nobody knows it, because
`key-switch-network.md`'s honest restatement of why the network is fitted lands
on *"The 47 nF is a bounce filter and cheap insurance. It is not what makes the
topology safe"* `[repo] key-switch-network.md:118-120`. The strongest surviving
reason for that capacitor is not in the corpus, and `docs/research/` is by rule
never to be corrected or promoted `[repo] CLAUDE.md §6`, so it is effectively
lost. The next person to cost-reduce 21 capacitors will find only "cheap
insurance" and will delete them.

**Two asks, both cheap:** put the contact-plating question on `SW1-n` with what
decides it (M1, by hand, and the Gateron drawing that is already banked), and
move the wetting-pulse arithmetic onto `key-switch-network.md` recomputed at
47 nF.

### C3-17 — the `R-KEY-PU` 2.2 k / 10 k trade omits the term humidity actually drives

**Node: key input node.** The live trade is recorded honestly and twice `[repo]
key-switch-network.md:112-124` and `[repo] hardware/carrier/carrier.md:174-186`,
and it has exactly two terms: 25.8 mA versus 5.9 mA on the MCP3202's reference
(3.2 LSB versus 0.7 LSB), against *"a 100 µs τ in a humid cavity"*.

The term that is missing is the one a humid cavity actually produces: **leakage
across an open contact, or across contaminated board surface between the input
node and ground.** It is a pure divider against the pull-up, so the pull-up value
is the whole of the design margin:

```
thresholds at 3.3 V: V_IH = 2.31 V, V_IL = 0.99 V   [repo] figures + onsemi 3.0 V row

with R-KEY-PU = 2.2 kΩ and a 10 kΩ leak to GND:
        3.3 × 10k/(10k + 2.2k) = 2.70 V   — above V_IH, reads HIGH, correct   [calc]
with R-KEY-PU = 10 kΩ and the same 10 kΩ leak:
        3.3 × 10k/(10k + 10k)  = 1.65 V   — between V_IL and V_IH:
                                            INDETERMINATE                     [calc]
```

And the corpus already carries TI's own warning that this region is where
*"double-clocking from induced ground bounce"* lives `[repo]
key-switch-network.md:95-98`.

So the 2.2 kΩ is **4.5× more tolerant of surface leakage than the 10 kΩ**, in the
one environmental condition the design cannot avoid. That is a real argument for
keeping it and it is not in the trade. The trade as written reads as "2.2 kΩ
costs us 2.5 LSB for an expired reason", which invites reverting it. `bom.csv`
says exactly that: *"that reason is gone now the register is back on the cluster
board"* `[repo] key-switch-network.md:122-127`. It is not the only reason, it is
just the only recorded one.

### Short to 12 V at the switch itself

Traced and benign: the KS-33's low side is `GND` and the aluminium plate is
bonded to `PWR_GND` `[repo] hardware/carrier/power-entry-instrument/power-entry-instrument.md:47-49`,
so a switch pin touching the plate is a short to the leg it already connects to.
The 12 V strip power runs in the side channels, not through the plate. No
finding.

---

## 7. Condensation

### What the corpus says, and it is thorough

This is the second-best-covered item in my slice. ADR 0003 has the whole
analysis: liquid versus vapour separated `[repo]
docs/decisions/0003-breath-sensing-path.md:766-820`, the datasheet objection
quoted (*"NOT compatible with water or water vapors"*, gel die coat swells when
wet), the PTFE plug doubling as the restrictor, the dead-volume trap, and — the
honest conclusion — *"Treat the sensor as a wear part […] Buy two. That last one
is the real mitigation."*

The **assembly rule** is better still, and it is the sharpest failure-mode
writing in the repository `[repo] ADR 0003:194-222`:

> **The instrument sits at 0.2 V and looks dead** — or needs implausible breath
> pressure to register anything at all. And because it tracks temperature, it
> reads correctly from cold and fails after ten minutes of playing.

with three assembly rules and an E2 test that distinguishes it from ordinary
drift (*"output that falls rather than drifts"*). That is exactly the shape a
failure-mode entry should have: mechanism, symptom, the wrong diagnosis it
invites, and the measurement that separates them. `carrier.md` carries the
masking rule forward to layout `[repo] carrier.md:145-152`.

**Detectability and recoverability, traced:**

| Failure | How you would know | Recoverable? |
|---|---|---|
| Blocked reference port | E2 cold-start sweep; output falls under warming | Yes, the body opens (ADR 0009) |
| Cavity sealing more than assumed | M8 soak watches the zero | Yes — a vent can be added |
| Liquid at the sensor | Trap, clearable "without disassembly" | **Only if the hatch exists — see below** |
| Gel swelling from vapour | Unreliable readings, no distinct signature | Replace the sensor |

### What I would add

**The "clearable without disassembly" promise has no hardware behind it yet.**
`carrier.md`'s own Still-open list says so `[repo] carrier.md:377-381`:

> ADR 0003 wants a replaceable wear part and a trap "clearable without
> disassembly"; ADR 0009 gives a 12 × 40 mm cover over a 2×5 header. **Those do
> not meet.** Either the cover becomes a real hatch with the sensor and trap
> under it, or the socket is decoration.

That is correctly flagged and I only underline it: the trap is the mitigation
for the one condensation failure with no electrical signature, and the access it
depends on is contested between two ADRs. Nothing else in my slice is blocked on
an open item this directly.

**The switch contacts are the uncoated surface in a coated design.**
`MECH-COAT` conformal-coats the boards `[repo] ADR 0009:530-533` and this is the
right call. Twenty-one mechanical switches cannot be coated, and they are the
parts with open metal contacts. That is C3-16 and C3-17 above; it is filed
there rather than repeated here.

**No finding against the condensation analysis itself.** It is correct, honest
about what it cannot fix, and it names the wear-part answer rather than
pretending to a fix.

---

## 8. Reverse polarity and the off-by-one-row insertion

Covered above as **C3-01** (the LT1641 and FET possibly ahead of all protection),
**C3-03** (the buffer's output reaching the DAC), and **C3-08** (the electrolytic
on the unprotected rail). Three points to add here rather than repeat:

**The series-Schottky scheme is right for ±12 V and handles the row-offset case
too, which nothing says.** I traced every mis-insertion outcome for the ±12 V
rails and the diodes cover all of them, not just reversal:

| What lands on the module's… | `D1`/`D2` (`+12V`) | `D3` (`−12V`) | Result |
|---|---|---|---|
| bus `−12V` on the `+12V` pin | reverse-biased, blocks | — | rail dead, no damage |
| bus `GND` on the `+12V` pin | no forward bias | — | rail dead, no damage |
| bus `+12V` on the `−12V` pin | — | reverse-biased, blocks | rail dead, no damage |

So the module is, for its ±12 V rails, safe against *any* mis-insertion and not
merely against 180° reversal. `[calc, from the drawing's diode orientations at
power-entry.md:39-72]`. ADR 0004 asserts this for reversal only and the
generalisation is worth a sentence, because it is the reason the exposure is
confined to the single unprotected pin.

**`D-REVSHUNT` at the instrument end is correctly reasoned and correctly
placed.** *"Its job is a rollover patch lead swapping pins 3 and 6; it has to
conduct immediately and let the module's LT1641-1 latch off. An inductor between
the fault and the diode is the wrong way round"* `[repo]
power-entry-instrument.md:44-48`. I checked the interaction with C3-02: a
rollover lead makes the load switch latch on **every** insertion attempt, and
the latch is cleared only by cycling the toggle — so the diagnostic experience of
a wrong patch lead is "the instrument is dead, the LED is lit, and re-seating the
cable does not help", which is indistinguishable from C3-02's symptom and from a
genuine cable fault. Three different causes, one identical presentation, and the
one indication the module has is on the wrong node. That is the strongest
argument in this report for `panel-led.md`'s proposed rework.

**The `+5V`-rail deletion proposal would close most of this.** The Still-open
blockquote's third reviewer-supported option — derive the buffer's rail locally
from the protected `+12V`, and go to a 10-pin header `[repo]
digital-and-supervision.md:87-96` — removes C3-03, C3-04 and C3-08 in one change
and removes the only unprotected pin from the module. Three separate failure
paths in this report converge on one decision that is currently deferred as
"a rail change and a connector change, not a drawing correction". I would raise
its priority on that basis: it is not one open item, it is three.

---

## 9. ESD on a jack, a key, the panel

### C3-14 — the protection is fitted at the end nobody touches

**Node: `U-TVS-MODULE`.** ESD protection on the umbilical exists at the
**instrument** end only: `U-TVS-SPI` on the three SPI lines, `D-TVS-BREATH` ×2
on the analog pair, `D-TVS-PWR` across the power pair — all at the carrier's
connector `[repo] hardware/carrier/carrier.md:288-292`. The module end is a
single BOM row with status `open` `[repo] hardware/bom.csv:131`:

> The BOM had protection at one end only. **DELIBERATELY open, not forgotten**:
> the module is behind four screws and this is retrofittable […] Fit at E12 if
> E11 gives any reason to

The retrofittability argument is sound. The exposure argument is the wrong way
round. The **module** end is the one on a front panel, in a rack, at hand
height, with a metal connector shell and a cable that gets plugged and unplugged
— and the plug is the classic ESD delivery vehicle, because the person holding
it has walked across a floor. The **instrument** end is inside a wooden body,
touched once at assembly.

I am not arguing the decision is wrong (it is retrofittable, and E11 is the
right gate). I am arguing the *stated reason* omits the exposure asymmetry
entirely, so the E11 decision will be taken on "did we see a problem" rather
than on "which end is exposed". One sentence on the row fixes it.

### C3-12 — which net the six jack sleeves tie to is stated nowhere, and the panel ties them together regardless

**Nodes: `J-CV` ×6 sleeve (PJ398SM pin 1), `PANEL`.** This is the gap I am least
comfortable about, because the sleeve is the ground the receiving VCO measures
against — it is the reference that the entire pitch-accuracy argument is *about*.

ADR 0004's grounding section enumerates *"Four returns arrive at this board"*
and names `PWR_GND`, `DIG_GND`, the module analog return and `AGND` `[repo] ADR
0004:614-621`. **The six jack sleeves are not among them**, and I could find no
statement anywhere in the corpus of which net they land on. The figure register
has `dig-gnd-topology` (DISPUTED) and nothing for the sleeves.

Worse, it may not be a PCB decision at all:

- `PANEL` is **2 mm aluminium** `[repo] hardware/bom.csv:54, in the SW-POWER
  panel-thickness analysis]`.
- The PJ398SM's bushing is **brass-nickel** and is clamped to the panel by its
  nut `[repo] hardware/bom.csv:97, from the banked Thonk drawing]`, and pin 1 is
  the sleeve, electrically the bushing.
- The etherCON `NE8FDP` flange is metal and bolts to the same panel.
- `SW-POWER`'s M6 bushing and the three pots' bodies likewise.

So **all six sleeves, the etherCON shell, the toggle bushing and the pot bodies
are shorted together through the front panel whatever the layout does**, and the
only question is whether the PCB agrees with the panel or fights it. If they
disagree, every patch cable closes a loop between the panel and whichever net
the PCB chose.

The corpus has touched the edge of this exactly once, in `power-entry.md`'s
blockquote on the three ground terms nobody had costed `[repo]
power-entry.md:120-137`:

> | The cable shield, if the etherCON shell bonds to the 10HP panel | **~7 cents** |
> […] it is a grounding and shield-bonding decision, and **the shield policy is
> sixteen words in the whole repo.**

The sleeve policy is **zero words**, and it is the larger of the two, because
six sleeves carry the signal return for every patch cable while the shield
carries nothing. On a corpus that budgets pitch error at 0.42 cents `[repo]
pitch-stage.md:299`, leaving the output reference net unspecified is the biggest
single omission I found in my slice.

**Silent.** A ground-loop-induced offset on the sleeve is a pitch offset, and a
pitch offset transposes the whole instrument equally — which `pitch-stage.md`
itself identifies as the error type that is *most* audible against a drone and
*least* like a fault `[repo] pitch-stage.md:104-110`. It will be trimmed out at
E9 against whatever the bench loop happens to be, and it will change when the
module changes slot.

### C3-19 — the `ON` node is undesigned, unprotected, and runs to a front-panel lever

**Node: `U-LOADSW` `ON`, `SW-POWER`.** The page is admirably blunt about the
state of this node `[repo] umbilical-load-switch.md:291-297`:

> There is no divider, no logic level, no supply, no pull-down, no debounce and
> no UVLO threshold specified anywhere — **four missing passives on the node
> that decides whether the instrument powers up at all.**

Three failure-injection consequences that the page does not draw:

1. **ESD path.** This is a 1.233 V comparator input with **−1 µA max input
   current** `[repo] umbilical-load-switch.md:299-301]` wired to a metal lever on
   the front panel of a rack. It is the highest-impedance node in the module and
   the most touchable. No series resistance, no clamp, no TVS is specified
   anywhere on it. Loud if it fails (the instrument goes dark), but it takes
   the LT1641 with it, and the LT1641 is the part with the 12-page banked
   datasheet and the three-reviewer history.

2. **Bounce against the unaccounted `TIMER` charge.** The `ON` pin has 80 mV of
   hysteresis and **no debounce** `[repo] umbilical-load-switch.md:293,299]`. A
   mechanical toggle bounces for milliseconds; the programmed ramp is 49–197 ms
   `[repo] config/figures.yaml:345-348]`. So every bounce interrupts a start
   that is nowhere near complete and restarts it, while the `TIMER` — which
   recovers over seconds, per C3-02 — accumulates. Flipping the toggle is the
   one operation this module has, and the interaction between its bounce and the
   fault timer is not analysed.

3. **Failing open.** With no pull-down specified, an open toggle contact leaves
   `ON` floating at −1 µA. The gold-contact choice `[repo] hardware/bom.csv:54]`
   is exactly right and is the mitigation — but it mitigates *intermittency*,
   not an open wire from the panel, and the page lists the missing pull-down
   without saying that this is what it is for.

### ESD on a key

Traced, low concern. A finger reaches the KS-33's stem, not its contacts; the
plate is aluminium bonded to `PWR_GND` `[repo] power-entry-instrument.md:47`, so
the plate is the shield and the discharge path, which is the right arrangement
and appears to be accidental — `MECH-GNDBOND`'s stated job is noise, not ESD
`[repo] ADR 0009, via power-entry-instrument.md:47-49`. Worth one sentence on the
row, since it is the second job the bond is doing.

---

## Appendix A — two refuted premises found inside my slice's argument chain

Both are the CLAUDE.md §5 shape: the conclusion survives, the stated reason does
not, and the next reader who checks the reason concludes the argument is dead.
Neither is a defect in the outcome and both should be corrected in place.

**A-1. `firmware/README.md` says the in-amp's `REF` pin is grounded.** `[repo]
firmware/README.md:80-82`:

> since the in-amp's `REF` pin is **grounded** rather than driven by a firmware
> zero (ADR 0003), no DAC register touches the breath jack at all

`REF` is **not** grounded. It carries `TRIM-BREATH-ZERO` through a buffer
`[repo] hardware/module/breath-receive-stage/breath-receive-stage.md:100-118`,
and `ROADMAP.md` E10 says so in bold with the reason — *"`REF` trimmed, not
grounded — grounding it makes the panel knobs interact"* `[repo] ROADMAP.md:51`.
The conclusion (no DAC register reaches breath) is correct and is independently
established on the stage page's own `CLR` section `[repo]
breath-receive-stage.md:213-222`. But the sentence quoted is the load-bearing one
in the **firmware** document, and it asserts the state that the roadmap
explicitly rejects. It is the same failure this file's own bolded warning about
the deleted watchdog was written to prevent, eight lines above it.

**A-2. ADR 0004's sagging-cable paragraph still has `CLR` firing.** `[repo] ADR
0004:527-531`:

> on a sagging cable the buck drops out at 8 V while the REF5050 and OPA2197
> hold regulation to ~7.2 V, so the MCU dies, SPI stops, **`CLR` fires**, and
> breath keeps working

Nothing asserts `CLR`. `R-CLR-PU` holds it inactive and the only asserter is the
`LK-CLR` hand pad `[repo] hardware/module/dac8568/dac8568.md:19`. The same ADR
withdraws the watchdog 40 lines earlier `[repo] ADR 0004:486-490`. So the correct
sentence is "the MCU dies, SPI stops, **pitch and the mods hold their last
values**, and breath keeps working" — which is the behaviour
`link-supervision.md` and `ROADMAP.md` E10 both already state for the unplug
case. The paragraph's conclusion (breath still working is designed behaviour,
not a gap) is untouched.

**A-3, noted not filed.** `firmware/README.md:88` opens its recovery section with
*"The body is bonded."* ADR 0009 supersedes this — the body closes on six
fasteners onto an RTV gasket `[repo] docs/decisions/0009-enclosure-construction.md:493-496,
653]` and `ROADMAP.md` M8 records the change `[repo] ROADMAP.md:78`. It bears on
my slice only through recoverability (C3-16's strip-down cost, and the sensor
hatch in §7), and there are enough other instances of it — `key-chain-loom.md:143`,
`breath-receive-stage.md:28`, `carrier.md:286,339`, `key-marker-and-bits.md`,
`ADR 0005:238`, `ADR 0001:244,160`, `ADR 0014:53,82`, `ROADMAP.md:207` — that it
is a sweep for another agent rather than a finding for this one.

---

## Appendix B — what I checked and found sound

Recorded because a review that only lists defects gives no information about
coverage, and because several of these took longer to verify than the findings
did.

- **`R-OUT-PROT` dissipation**, all six stages, all four fault modes (short,
  output-to-output at both polarities, back-powering when the module is off,
  ramp). The 0.66–1 W specification covers every case I could construct, with
  the derating the row already applies. `[calc]`
- **`D-JACK-CLAMP` on the driver side.** The back-powering arithmetic (42 mA per
  jack at the jack versus 7.6 mA behind the 1 kΩ, 254 mA across six into the
  rail that feeds the umbilical) is correct and is the right reason. `[repo]
  hardware/module/bom.csv:3`, `[calc]`
- **The load switch's hot-plug sizing.** 17.1 ms + 30.4 ms = 47.5 ms against
  95.6 ms worst case, and the foldback law it rests on. I could not fault the
  arithmetic; C3-02 is about what happens *after* it, not about it. `[calc]`
- **The mod channels' `CLR` safe state.** `4×0 − 3×0 = 0` requires the C grade,
  the page knows it, the grade is locked in `bom.csv`, and the firmware rule that
  prevents the `+11.45 V` mirror-image failure is stated as a rule rather than an
  optimisation. This is the best-defended failure mode in the project. `[repo]
  mod-channels.md:150-190`, `firmware/README.md:60-86`
- **`R-BIAS-DAC` ×6** covers pitch, the four mods and the offset channel, at the
  DAC pin rather than after `R-OPAMP-IN`, and closes the "op-amp output sits at a
  rail before power-on reset" window on all six. Correct and complete. `[repo]
  hardware/bom.csv:84`
- **`R-SPI-PULL` ×6 polarity and rails.** Cable-side `CS` to 3V3 (not 5 V, for
  the unpowered-ESP32 clamp reason), DAC-side to `AVDD`. Both corrections are
  right; C3-03 is that the same reasoning was not carried to the driver.
- **`R-LED-PD` ×2** closes the boot-window hole in ADR 0014's "blank at boot"
  defence, and the page states plainly that the firmware rule *"cannot run in the
  window it matters"*. That is a model piece of failure-injection writing.
  `[repo] hardware/carrier/led-strip-drive/led-strip-drive.md:40-52`
- **The polyfuse deletion.** The thermal-runaway loop ADR 0014 describes is real,
  the polyfuse was the positive-feedback term, and ADR 0005 deletes it with four
  independent reasons. The reasoning chain survives the check. `[repo] ADR
  0005:305-320`, `ADR 0014:189-223`
- **The `-1` versus `-2` suffix choice.** Auto-retry into a persistent fault is
  the same oscillating shape as the polyfuse. Correct, and C3-02 is the cost of
  that correct choice being paid at an unexpected moment, not an argument
  against it.
- **8-bit marker pattern.** Two straps per device, one high and one low, catches
  a device dead / unclocked / stuck-high / stuck-low regardless of the other
  three. It is doing more failure-detection work than any other single decision
  in the instrument, including for C3-15, and the page is honest about what it
  cannot see (single-bit flips caught 8 times in 32; the counter undercounts ~4×).
  `[repo] key-marker-and-bits.md:47-100`

---

## What I would take to the gate, in order

1. **C3-02** — a minimum re-plug interval exists, is measured in seconds, and is
   written nowhere. It converges with C3-14/§8 on `panel-led.md`'s already-costed
   one-resistor rework, which three separate failure paths in this report need.
2. **C3-01** — two topologies for the module's highest-current node. Cheap to
   settle, and everything about reverse polarity depends on the answer.
3. **C3-12** — the six jack sleeves have no stated net, on a design that budgets
   0.42 cents of pitch error.
4. **C3-10 and C3-11** — ADR 0006's jack-state table is the document a reader
   checks, and two of its three rows are wrong against the pages that own them.
5. **The bus `+5V` deletion** (§8) — one deferred decision that closes C3-03,
   C3-04 and C3-08.
6. **C3-05** — a firmware refresh interval for the DAC's sticky registers, sized
   against the plug event rather than against a firmware hang.
