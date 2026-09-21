# Verified by hand — not agent claims

**In progress. 18 of 20 agents in.**

Everything below was checked directly against the repo in the main session,
independently of the agent that reported it. An agent finding is a *claim*
until it appears here. Earlier waves produced findings that were wrong, and
this wave has already produced one mis-attribution (recorded at the bottom).

Node-indexed, like the reports.

## Confirmed — two documents specify incompatible hardware

| Node | What one says | What the other says | Consequence |
|---|---|---|---|
| **`CLR`** (DAC8568) | `digital-and-supervision.md` draws `[R-CLR-PD 10k]` to `AGND` | `bom.csv` row 67 is **`R-CLR-PU`**, "holding … `CLR` **inactive**" | `CLR` is active low and the watchdog that used to drive it is deleted, so **as drawn it is asserted forever**: six dead CV outputs, no SPI write able to change them |
| **`R1b`** (`R-SER-BREATH-INST`, AGND leg) | `bom.csv` qty **2**, instrument-side, **unretrofittable**; `breath-receive-stage.md`'s 482 Hz pole depends on it | **Zero occurrences** in `carrier.md` — the schematic page for the board that must carry it, which says of itself "layout is now" | The link CMRR budget rests on a part that is not on the drawing |
| **`R-ISO-REF`** | In `bom.csv` | **Zero occurrences** in `carrier.md` §2, drawing *and* component table | A2 independently derives that without it the reference buffer **oscillates** — 100 nF of sensor decoupling on an OPA2197 output whose Ro back-solves to 75.8 Ω |
| **`C-FB-PITCH`** | **1 nF** in the `pitch-stage.md` drawing and its split-loop table | **2.2 nF** in the same page's value table and in `bom.csv` | Two different compensation networks |
| **ADR 0006 vs everything** | ADR 0006 still specifies **"1 nF across the feedback resistor"** (2 occurrences) | `pitch-stage.md` and `bom.csv` say output-to-(−), and that "across the feedback resistor" gives **18° of phase margin with 2 m of cable** | The accepted ADR still prescribes the arrangement the schematic says is unstable |
| **LM311, 74HC123** | Both **deleted** — `digital-and-supervision.md` prose, ADR 0004, `bom.csv` | Both still **drawn** in that same file's schematic, with rails allocated in its supply table, and `bom.csv` `C-DECOUPLE` qty 21 explicitly counts "LM311 on +/−12V = 2" | A board built from the drawing carries two ICs nobody wants; decoupling count should be 19 |
| **Marker allocation** | `key-layout.yaml`, ADR 0001, `cluster-boards.md`: **8 marker / 3 free** | `carrier.md` lines 454–455 still say **6 marker / 5 free** | Hard-wired copper on boards that bond shut |

## Confirmed — reference designators that do not resolve

Drawn in a schematic, absent from `bom.csv`:
`R-SCLK-SER`, `R-MOSI-SER`, `R-CS-SER`, `R-LED`, `R-OE-PU`, `F-CHAIN`,
`U-TVS-CHAIN`, `R-CHAIN-SER`.

In `bom.csv`, used by no schematic: **`R-SPI-SER`** (qty 3).

`carrier.md` §4 additionally claims *"only `R-MOSI-SER` reached the BOM,
qty 1"* — `R-MOSI-SER` is not in the BOM at all. The three series resistors
and the BOM's `R-SPI-SER` are the same three parts under two naming schemes,
and neither side knows about the other.

The last three (`F-CHAIN`, `U-TVS-CHAIN`, `R-CHAIN-SER`) were proposed in
this session's own drawings and never given BOM rows. Same defect, made
today.

## Confirmed — errors introduced in this session

- **`cluster-boards.md` §2 figure wires the switch to 3V3**, not GND,
  contradicting its own caption "shorts to GND when pressed". As drawn a
  press is a 33 mA rail short and the register input never moves.
- **Bits 22, 23 and 31 have no pull-up budgeted.** The component table,
  `bom.csv` and `carrier.md` all carry 21 pull-ups for exactly the 21
  *switch* positions; the three free bits need them too. Floating CMOS
  inputs — the precise fault ADR 0001 fix 6 exists to prevent.
- **`carrier.md` left stale on the marker count** (above), in the same
  session that fixed that pattern twice.

## Agent claims checked and NOT confirmed as stated

- **A6 F2** attributed a channel-7 refresh contradiction to ADR 0006 versus
  `firmware/README.md`. The contradiction is real but sits *inside*
  `firmware/README.md`: its line 50 says channel 7 is "written once at
  boot", while `mod-channels.md` cites that same file's statelessness rule
  as "refresh all six populated channels every pass". Right defect, wrong
  parties.
- **B2's brief was wrong, not the repo.** This session briefed B2 that the
  pitch stage gives ±5 V about a 2.500 V intercept. It gives **−2 to +7 V**.
  The agent judged against the repo rather than the brief, which is correct
  behaviour and worth recording as such.


---

# Convergence — where independent cold agents agreed

The point of running twenty agents that cannot read each other is that
agreement means something. These are conclusions reached **more than once,
from different directions, with no contact**. They carry more weight than
any single finding, including the ones I verified by hand.

## The instrument does not power up

Two agents, different scopes, no shared inputs.

**A7** (module power entry, cold design review): `C-TIMER-LOADSW` at 10 nF
is wrong by 40–400× — `t = 1.233·C/I_TIMER` needs 81 nF to 4.1 µF for
50 ms, so the module latches roughly 1 ms into every start. There is **no
gate capacitor anywhere** in the BOM or the schematic, although the FET
sizing, the boot analysis and ADR 0005's 50–100 ms specification all rest
on a "programmed ramp". And the start margin is 1 %, not the 47 % claimed,
because the page's start table has a capacitor-charging row and **no load
row at all**.

**C3** (sequencing falsification): the LT1641's real sense threshold is
**47 mV, not 50**, so `R-ILIM` at 50 mΩ limits at **0.940 A**. Foldback
regulates the sense drop to 12 mV at zero output — **240 mA**, below the
0.53 A programmed ramp — so **every start begins in current limit** and
takes ~62 ms against a ~50 ms timer. It latches at the end of every start.
Delete foldback and the margin is still 4 %, inside the part's own
threshold tolerance.

`power-entry.md` programs foldback in one section and asserts "a normal
start never enters current limit" in another. Neither agent could have seen
the other's report.

**Consequence:** the first thing that happens at E6 is that nothing
happens. This is a before-order fix, not a bring-up fix.

## The umbilical pin map is wrong — for three different reasons

Three agents, three mechanisms, one set of pins. The fixes must be
**combined**, not chosen between.

| Agent | Mechanism | Fix |
|---|---|---|
| **B5** | Published RJ45-for-other-purposes standards leave pins 4/5 empty so a misplug into PoE or telephone destroys nothing. `MOSI`/`CS` are on exactly those pins. PoE also delivers power *common-mode* through centre taps; this design puts +12 V/`PWR_GND` **differentially across pins 3-6**, straight across a switch port's transformer | Move `MOSI`/`CS` off 4/5; power onto a compact pair |
| **A4** | `MOSI` and `CS` share one twisted pair, so the signal whose glitch re-frames the DAC word (a *sticky* failure by the repo's own taxonomy) sits in the tightest coupling with its busiest aggressor, no return between them. ~2.0 V coupled step against a 0.8 V `V_IL` | `CS` pairs with `DIG_GND`; `SCLK` pairs with `MOSI` |
| **C3** | `R-SPI-PULL`'s cable-side `CS` is specified to pull up to **3V3 — a rail the module does not have**, and not one of the eight conductors | Re-specify against a rail that exists |

## The series resistor value, with a refinement

**B5** and **A4** both reject the repo's 220 Ω on transmission-line
grounds: 2 m of Cat5 is a 100 Ω line with a ~20 ns round trip against
2–5 ns edges, and at 220 Ω the far end sits at **1.83–1.86 V against a
2.0 V `V_IH`**, dwelling in the forbidden band for ~20 ns per clock edge,
into a part with no hysteresis.

They disagree on the value, and **A4 wins on a number B5 did not check**:
68 Ω is electrically ideal but draws **48 mA of fault current against a
40 mA pad spec**. 100 Ω gives a 2.75 V first step and 33 mA.

## Deleted parts are still load-bearing

**D2**, **A5**, **A7**, **B1**, **B2** and **C3** all hit this
independently. The watchdog and presence comparator are deleted in the
ADRs, the BOM and three prose sections — and still drawn, still allocated
rails, still counted in `C-DECOUPLE` qty 21, and still **depended upon**:
`mod-channels.md` justifies its whole topology on "a watchdog `CLR` parks
all four jacks at 0 V", `firmware/README.md` says "when the module watchdog
asserts `CLR`", and `bom.csv` claims the panel LED explains a latch that
nothing now indicates.

## The breath jack never rests at 0 V

**C2** and **C3** derive this separately, and **A5** and **B2** reach it by
a third route (the offset legs sum *after* the gain stage). ADR 0005 and
ADR 0006 both assert 0 V. The real value depends on the offset knob and
spans roughly **−5.9 V to +4.1 V**, with **+5.06 V at full CCW with no
instrument attached** — a patched VCA wide open at rack power-on.

## Documents defend the easy case

Not a defect but a pattern worth naming, found by **A2**, **C1**, **C2**
and **C4** independently: a claim is supported with the frequency, load or
operating point where it is comfortably true, and the case that actually
bites is not computed. Examples: the anti-alias filter defended at 330 kHz
rather than at 3.84 kHz where the aliasing is; the `SH/LD` glitch margin
argued capacitively (31× safe) when the inductive path is the one that
loads; the ADC reference costed at DC when the disturbance is a step; the
LC damping margin evaluated at typical play rather than at the clamp-legal
worst (220× becomes 56×).


## The arithmetic is sound; the bookkeeping is not

**D1** recomputed 312 numeric claims in Python from the values `bom.csv`
actually specifies. **~232 correct, ~54–61 wrong, 26 resting on inputs it
could not verify.** Its own headline is worth quoting as a result in its
own right: *"the arithmetic in this project is unusually good. Almost every
derivation that is shown is right."*

Nearly every defect is **one failure mode**: a value changed and the
numbers derived from it did not follow. They cluster on four quantities —
the breath in-amp's full-scale output, the pitch compensation capacitor,
the DAC channel count in the loop budget, and the marker-bit allocation —
**each wrong in two or three documents at once**. That is the same
staleness pattern `D2` found in prose, showing up in numbers.

Sharpest instance: the breath in-amp's full scale is stated as **−9.6 V**,
**−9.94 V**, **−10.05 V** and a "9.94 V span" across three files. Correct
is −9.94 V, and D1 notes the −9.6 V figure *"is reproducible from
nothing"*.

## A1 and D1 agree against this session's own figures

Both independently compute the key network as **119.9 µs release / 5.92 µs
press**, against the **125 µs / 5.7 µs** written into `cluster-boards.md`
and ADR 0001 today. Two agents, one from the cluster-board review and one
from a mechanical arithmetic sweep, landing on the same pair. The repo's
figures are mine and should be corrected to theirs.

D1 also confirms the part-family check passed: the crossing times use
0.7/0.3 × VCC, which is right for the 74HC part actually specified rather
than the LVC thresholds ADR 0001 retired.

## D1 and A4 do not actually conflict on the loop budget

They look contradictory and are not, and the distinction matters.

- **D1** audits the arithmetic *as written* and finds one error — the key
  chain is booked at 16 µs (32 bits at 2 MHz) where ADR 0001 and
  `carrier.md` fix the chain at 1 MHz, so **32 µs**. Corrected, the pass is
  148–155 µs of 250 µs and **4 kHz closes**.
- **A4** says the *model* omits a term: ESP-IDF's own documented
  per-transaction overhead on the ESP32-S3 (24 µs interrupt, 9 µs polling),
  which no document counts. Including it, the pass is **291 µs with driver
  defaults** — it does not close — or **196–241 µs** with polling
  transactions on an acquired bus.

So: **the repo's loop budget is arithmetically correct and structurally
incomplete.** Both agents are right about what they measured. The number
to design against is A4's, and the firmware technique it names is not
optional — it is what makes 4 kHz reachable at all.
