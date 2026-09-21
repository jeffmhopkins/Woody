# Verified by hand — not agent claims

**In progress. 13 of 20 agents in.**

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
