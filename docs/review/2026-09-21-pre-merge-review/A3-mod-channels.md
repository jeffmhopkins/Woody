# A3 — the four mod channels and the reference they share

**Wave:** 2026-09-21 pre-merge review. **Agent:** A3, cold (no prior review
directory read).

**Scope:** `hardware/module/mod-channels/`, `hardware/module/dac8568/`,
`docs/decisions/0006-cv-channel-allocation.md`, `firmware/README.md`,
`config/figures.yaml` `mod-reference`. Corroborating reads outside the slice
where a number crosses into it: `hardware/module/pitch-stage/`,
`hardware/module/power-entry/power-entry.md`, `hardware/bom.csv`,
`docs/reference/latency-budget.md`, `docs/reference/pcb-pipeline.md`.

**Provenance key:** `[repo]` path:line, `[calc]` arithmetic shown,
`[datasheet]` document + locator, `[from memory]`.

**Report only. Nothing was changed.** `python3 tools/check-staleness.py`
passes on the tree as reviewed `[repo] PASS no live stale values | corpus 121
files, 23 circuits | 5 unresolved (tracked)`.

---

## Summary

The transfer function, both endpoints, the tolerance table and both
"improved by N×" factors **all re-derive exactly**. This is the third version
of the tolerance section and it is the right one. §4 of the audit is clean.

What is wrong is around the edges of that correct core, and it clusters on the
shared reference node:

- The **schematic does not draw the circuit the algebra describes** — `R1`'s
  far end lands on the op-amp body, not on the summing node, and no sentence
  on the page says where it goes (M1).
- The **buffer-load model is wrong**, and right only by coincidence at one
  end of the range. The page, the drawing and `figures.yaml` all agree on
  1.33 mA — agreeing on a number derived from a circuit that is not this one.
  The buffer also has to **sink** 0.67 mA, which no document mentions (M2).
- The **`CLR` grade argument is attached to the wrong mechanism.** A pin
  `CLR` clears to zero scale on *every* grade; only power-on reset is
  grade-dependent `[datasheet]`. `bom.csv`'s `R-CLR-PU` row knows this and the
  two schematic pages and the ADR do not (M3).
- **`+11.45 V` has two incompatible derivations live in the corpus**, one of
  which contradicts ADR 0004's diode count and the banked OPA2197 swing spec
  (M6), and the statement it supports overstates its own failure case (M4).
- **"DAC channel 7" is never mapped to the part's `A`–`H` address field**,
  and firmware is given a voltage where it needs a code (M5).
- **`mod-reference` is restated verbatim 13 times outside its owner** — the
  exact shape CLAUDE.md §1 exists to prevent, on the figure whose own
  `escape_note` records the last escape (M7).

Severity: **M** = must fix before merge, **S** = should fix, **N** = noted,
verified, not a defect.

---

## Node `V_REF_BUF` / `R1` far end — the drawing does not close the loop  — **M1**

**`R1` is not drawn connected to the inverting input.** Column positions in
the ASCII art `[repo] hardware/module/mod-channels/mod-channels.md:36-62`:

| Element | Line | Column |
|---|---|---|
| `R1 10k` body | 42 | 21–31 |
| `R1` lower lead `│` | 43, 44 | **26** |
| op-amp box top edge `┌───┴────────┐` | 47 | 22–36, tee at **26** |
| `+` input `┤ +` | 48 | **22** |
| `−` input `┤ −` | 50 | **22** |
| left rail carrying `R2` to the `−` input | 50, 51, 53 | **19** |

`R1`'s lead terminates on the **top edge of the op-amp symbol** at column 26.
The `(−)` terminal is at column 22, fed from the column-19 rail that runs down
to `R2 30k`. **The two never meet.** `R2`'s left end is the only thing on the
summing node.

The topology is recoverable only from the algebra, because the page never
states it in prose either: the `Values` table says `R1 … To the shared
reference` `[repo] mod-channels.md:109` — the *other* end — and the Interfaces
table says `DAC ch7 … into the follower's (+) input` `[repo]
mod-channels.md:26`, which is about the buffer, not about `R1`. Searched the
whole page: no sentence puts `R1` on the inverting node.

The nearest labelled terminal below `R1`'s landing point is `+`. A reader who
resolves the ambiguity that way gets a passive summer into a non-inverting
stage, which is a **different transfer function**, not a cosmetic difference.
This page is explicitly written for "someone…while stuffing the board"
`[repo] mod-channels.md:191-192`.

`R1` must land on the column-19 rail, i.e. tie to `R2`'s left end.

**Same node, lower severity — the follower's feedback is drawn to its `(+)`
input.** `[repo] mod-channels.md:36-38`: the return wire `└───────────────┘`
runs from the tee at the op-amp output back to the tee **between `R-OPAMP-IN`
and the input**, which as drawn shorts the output to the input node. Read as
the shorthand "follower" it is harmless; read literally it is a short. Given
that the same drawing already fails to land `R1`, a reader has no basis for
assuming one line is shorthand and the other is literal.

**`R-BIAS-DAC` is missing from the drawing and from `depends_on`.** `[repo]
hardware/module/pitch-stage/bom.csv:9` carries `R-BIAS-DAC` qty 6, "AT THE DAC
PIN, not after `R-OPAMP-IN`", covering all six DAC-driven nodes. **Five of the
six** — `ch2`–`ch5` and `ch7` — are nodes `mod-channels.md` draws. It appears
in neither the drawing nor the Interfaces table, and
`[repo] hardware/module/mod-channels/circuit.yaml:46-56` does not list
`refdes:R-BIAS-DAC`. Its stated purpose is a DC path during the window when
the DAC pin is high-Z, which is precisely the power-on window this page's
park-at-0 V argument lives in.

---

## Node `V_REF_BUF` — the buffer's load is modelled as a resistor to ground, and it is not — **M2**

Three places state the shared buffer's load current, all agreeing:

- `[repo] mod-channels.md:38` — `(~1.3 mA total into 4 × 10k)`
- `[repo] mod-channels.md:196-200` — "four 10 kΩ inputs in parallel. At
  `mod-reference` into 2.5 kΩ that is **1.33 mA**"
- `[repo] config/figures.yaml:251-253` — "The real figure is 1.33 mA
  `[calc: 3.3333/2500]`"

**The far end of each `R1` is not ground.** It is the inverting node, which
negative feedback holds at `V(+) = Vdac` for that channel (`R-OPAMP-IN` carries
`I_B ≈ 5 pA` `[datasheet]` OPA2197 SBOS737C, so no drop across it). So

```
I_buf = Σ (V_ref − Vdac_i) / 10k        [calc]
```

| All four channels at | Jacks at | I_buf |
|---|---|---|
| `Vdac = 0` | −10 V | **+1.333 mA** (source) |
| `Vdac = 2.5` | **0 V — the park state** | **+0.333 mA** |
| `Vdac = 5` | +10 V | **−0.667 mA** (sink) |

`[calc] 4 × (3.3333 − 0)/10 000 = 1.3333 mA; 4 × (3.3333 − 2.5)/10 000 =
0.3333 mA; 4 × (3.3333 − 5)/10 000 = −0.6667 mA.`

1.33 mA is correct **only at the all-channels-at-−10 V extreme**, and it is
right by coincidence: at `Vdac = 0` the summing nodes happen to sit at 0 V, so
the load happens to be 2.5 kΩ to ground that one time. The stated *reason* —
"four 10 kΩ inputs in parallel", "into 2.5 kΩ" — is wrong everywhere else, and
gives 4× the true current in the resting state.

This matters more than the number does. `config/figures.yaml`'s `escape_note`
records that this same sentence was wrong once before, carried over from the
four-resistor circuit, and the fix replaced the **voltage** while keeping the
four-resistor circuit's **model** (`V_ref / 2.5 k`, a divider to ground, which
is what the difference amp actually had). The model is the survival, not the
number. **The sink case is not stated anywhere in the corpus**, and "comfortable
for the part" was concluded from a one-sided figure.

Suggested replacement, stated as a range with its worst case: `+1.33 mA
sourcing (all four jacks at −10 V) to −0.67 mA sinking (all four at +10 V),
0.33 mA at the 0 V park`. OPA2197 `I_SC = ±65 mA` typ `[datasheet] SBOS737C,
per the banked MANIFEST row`, so the conclusion survives with ~50× margin in
both directions — but it should be reached from the right circuit.

---

## Node `CLR` — the safe-state argument is attached to a mechanism that does not carry it — **M3**

The claim: `[repo] mod-channels.md:154` "On a `CLR`, the C-grade DAC8568 (the
grade is **locked** — it selects reference gain as well as reset state, ADR
0006) clears **every** channel to zero scale", and `[repo]
mod-channels.md:183-188` "**The two-resistor form also made the DAC grade
safety-critical**… a B/D part would put **+2.5 V on all four jacks**". Echoed
at `[repo] docs/decisions/0006-cv-channel-allocation.md:160-168`.

**From the banked datasheet** `[datasheet] datasheets/analog/DAC8568CIPW.pdf`,
SBAS430E, section "CLEAR CODE REGISTER and CLR PIN", verbatim:

> "Bringing the CLR pin low clears the content of all DAC registers and all DAC
> buffers, and replaces the code with **the code determined by the clear code
> register**. … **The default setting of the clear code register sets the
> output of all DAC channels** [to zero scale]."

and, separately, section "POWER-ON RESET TO ZERO SCALE OR MIDSCALE":

> "**For device grades A and C on power-up**, all DAC registers are filled with
> zeros and the output voltages of all DAC channels are set to zero scale. For
> device grades B and D all DAC registers are set to have all DAC channels
> power up midscale."

Two different mechanisms with two different selectors:

| Event | Reset state chosen by | Grade-dependent? |
|---|---|---|
| **Pin `CLR` low** (`LK-CLR`) | clear code register, default `DB1=DB0='0'` = zero scale | **No** |
| **Power-on reset** | grade letter: A/C zero, B/D midscale | **Yes** |

So a B/D part with the clear-code register at default **still parks at 0 V on a
pin `CLR`**. The `+2.5 V on all four jacks` hazard is a **power-on** hazard
only. Attaching it to `CLR`, which is what both `mod-channels.md` and ADR 0006
do, invites a reader to conclude that the grade lock protects the `LK-CLR`
bring-up path — it does not need to — and, worse, to conclude that the
**clear-code register default is not load-bearing**, when it is the only thing
standing between `LK-CLR` and midscale on any part.

`[repo] hardware/bom.csv:` `R-CLR-PU` notes has it right: *"Leave the DAC's
clear-code register at its default so a manual CLR still parks at zero scale.
Do NOT write ClearIgnore"* — confirmed against the datasheet, which lists
`DB1=DB0='1'` as *"Write to clear code register; ignore CLR pin"*
`[datasheet] SBAS430E Table 11`. **The BOM row carries the correct mechanism
and the two schematic pages and the ADR do not.** `firmware/README.md:80-82`
lists the clear-code register in the sticky set, which is the right
consequence reached from the wrong stated cause.

The argument's *conclusion* — park at 0 V — is correct on both paths. Only the
attribution is wrong. Fix is a sentence, not a redesign.

**Also on this node: the `CLR` peer is stated three different ways.**

- `[repo] mod-channels.md:28` — peer `module/digital-and-supervision`
- `[repo] hardware/module/dac8568/dac8568.md:18` — peer `module/link-supervision`,
  and in the same cell "Nothing drives it — the part that did is not fitted"
- `[repo] hardware/module/digital-and-supervision/digital-and-supervision.md:27`
  names `module/dac8568` as its DAC peer and claims no `CLR`

A peer named for a net nothing drives is at best a fiction; naming two
different ones in two pages is a reader trap on the node this whole section
turns on.

---

## Node `DAC ch7` — the mirror-image failure is overstated, and in the most load-bearing paragraph in the firmware document — **M4**

`[repo] firmware/README.md:56-58` and `[repo] mod-channels.md:177-181`:
"Firmware then rewrites the five signal channels … and `Voffset` stays at 0.
**Every mod jack pins at `4 × Vdac` ≈ +11.45 V and stays there.**"

With `V_ref = 0` the stage becomes `Vout = 4·Vdac`, i.e. **every output is its
intended value plus exactly 10 V** `[calc] 4·Vdac = (4·Vdac − 10) + 10`.
Clipping at ~+11.45 V therefore begins at an *intended* output of +1.45 V,
i.e. `Vdac > 2.8625 V` `[calc] 11.45/4`.

| Channel commanded to | Actually sits at |
|---|---|
| −10 V | **0 V** |
| 0 V (the park value) | **+10 V** |
| +1.45 V | +11.45 V, at the clip |
| anything above | +11.45 V |

So a jack commanded to −10 V does not pin at +11.45 V; it sits at 0 V. "Every
mod jack pins at +11.45 V" is true for **roughly the top 43 % of the range**
`[calc] (5 − 2.8625)/5`. The hazard is real and severe — a +10 V uncommanded
shift on four CV outputs — but the sentence as written is checkable and false,
and `firmware/README.md` itself flags this paragraph as "the most load-bearing
firmware constraint in the repo" whose "stated cause had to be one that still
exists" `[repo] firmware/README.md:65-68`. A premise that fails a five-second
check is the same failure mode as the deleted watchdog, one level down.

Accurate: *every mod output shifts +10 V; any channel commanded above +1.45 V
rails at ≈ +11.45 V, and none of it is recoverable without a power cycle.*

**Two smaller errors in the same family.**

**(a) "wrong span" is wrong.** `[repo] firmware/README.md:52-54` — writing the
superseded 2.5 V into ch7 "gives a −7.5…+12.5 V window — **wrong span**, and it
clips positive". The window is **20.0 V wide**, identical to the correct
−10…+10 V `[calc] 4 × 5 = 20 V in both cases; only the `−3·V_ref` intercept
moves, 10.0 V → 7.5 V`. It is a **wrong offset with the correct span**: every
output is +2.5 V high, and the top of the range clips. Three other statements
of the same hazard get it right by not claiming anything about the span —
`[repo] config/figures.yaml:246`, `[repo] docs/decisions/0006-…:117-118`,
`[repo] mod-channels.md:14-15`. **Only the firmware document, where a firmware
author will read it, adds the false half.** The rest of that hazard's
arithmetic verifies exactly: `4×0 − 3×2.5 = −7.5`, `4×5 − 3×2.5 = +12.5` `[calc]`.

**(b) "a hard rail … indefinitely" describes the wrong one of the two cases.**
`[repo] mod-channels.md:171-175`: had the reference come from a fixed divider,
"every mod jack would pin at `4 × 0 − 3 × 3.3333 = −10.00 V` — a hard rail on
four outputs, **indefinitely**, with no `MISO` to notice it." The arithmetic is
right; the characterisation is not, twice over. **−10.00 V is not a rail** — it
is the exact bottom of this stage's specified ±10 V range `[repo]
docs/decisions/0006-…:14`, a legal output the design is built to produce; the
rails are at ±11.45 V. And it is **not indefinite**: firmware refreshes
`ch2`–`ch5` on its next 250 µs pass `[repo] firmware/README.md:21`, restoring
correct behaviour, because in this counterfactual the offset is the thing that
*never* needed refreshing. The genuinely indefinite case is the actual
mirror-image failure in the paragraph below it, which is where "indefinitely"
belongs.

There **is** an indefinite version of the fixed-divider hazard and the page
does not state it: the module is rack-powered and the controller is on a
separate 2 m umbilical, so *module powered, controller absent* is a normal
state in which firmware never writes at all. A fixed-divider design would then
sit at −10 V on four jacks for as long as the rack is on. That is the argument
that survives; the one written down rests on a transient. The same overstatement
appears at `[repo] hardware/module/mod-channels/notes.md:95` — `Vout = 5 × 2.0 =
+10 V — a hard rail on four jacks` — where +10 V is likewise the top of the
specified range.

---

## Node `DAC ch7` — the channel is addressed by a number the part does not have — **M5**

`[datasheet] SBAS430E Table 11`: the DAC8568 addresses channels by a 4-bit
field `A3..A0`, `0000` = **DAC Channel A** through `0111` = **DAC Channel H**.
The corpus addresses them as "ch 1" … "ch 7" `[repo]
docs/decisions/0006-…:10-15`, `[repo] firmware/README.md:50`, `[repo]
mod-channels.md:26-27`, `[repo] dac8568.md:21-22`.

Grepped the whole corpus for any mapping between the two — `DAC-A`, `DAC-H`,
`channel A`, `address 0000`, a pin table, anything. **There is none.** The
`dac8568.md` drawing `[repo] dac8568.md:32-47` shows only `CLR` and `LDAC`; it
does not draw a single `VOUT` pin.

"Channel 7" is therefore ambiguous by exactly one channel: address `0111` is
DAC-**H** (the eighth), while the *seventh* channel is DAC-**G**, address
`0110`. If `ch 1` is DAC-A then `ch 7` is DAC-G and firmware must write `0110`
— but nothing says `ch 1` is DAC-A either. The numbering is also incomplete on
its own terms: ADR 0006 says "**Six of eight** channels used, two spare"
`[repo] docs/decisions/0006-…:22` and names `ch 1`–`ch 7`; the eighth channel
is never named as `ch 0` or `ch 8`, so the scheme does not even enumerate the
part.

This is the one node in the slice whose value sets the intercept of **four**
jacks. An off-by-one here puts the reference on an unpopulated, unbiased pin
and every mod output at `4·Vdac` — hazard M4, permanently, from the first boot.
It is undetectable at the SPI level: there is no `MISO` `[repo]
firmware/README.md:39-40`.

**Related, same node:** `mod-reference` is published as a voltage, `3.3333 V`.
Firmware writes a **code**, and no document gives one or gives the mapping.
`[calc]` With the C grade's 5.000 V full scale and 16 bits, LSB =
5.000/65536 = 76.294 µV; `(10/3)/76.294 µV = 43690.67`, so the nearest code is
**43691** = 3.333359 V, intercept `3 × 3.333359 = 10.000076 V`. Writing a code
derived from the literal decimal `3.3333` gives 43690 and −9.99992 V. Both are
inside 0.1 mV, so the "exactly ±10.000 V" claim survives quantisation with
~600× margin against the ±50.5 mV resistor term — but the corpus should say
which code, on the channel where it has already had one value-transcription
escape.

---

## Node `MOD 1`–`MOD 4` — `±11.45 V` has two incompatible derivations, both live — **M6**

The number appears in six corpus files and is **not** in `config/figures.yaml`.
Two derivations:

**Derivation A**, `[repo] docs/decisions/0006-cv-channel-allocation.md:136-137`:
"±12 V rails less ~0.35 V of Schottky leaves ±11.65 V, and an OPA2197 reaches
~±11.45 V — 1.45 V of margin at ±10 V." Structure: one diode drop per rail,
then 0.20 V of op-amp swing loss. **Coherent.**

**Derivation B**, `[repo] hardware/module/mod-channels/notes.md:52-54` and
`[repo] hardware/module/pitch-stage/pitch-stage.md:149-151`: "an OPA2197 on
±12 V **less two Schottky drops** reaches ~±11.45 V". Structure: 0.55 V of
diodes per rail, **zero** op-amp swing loss. **Wrong twice:**

1. `[repo] hardware/module/power-entry/power-entry.md:37-73` and its heading
   "Three diodes, not two, and the branch is before them": `D1` on module
   analog +12 V, `D2` on the separate umbilical +12 V branch, `D3` on −12 V.
   **One 1N5817 in series with each op-amp rail**, not two. `[repo]
   docs/decisions/0004-cv-interface-module.md:252` agrees: "Series Schottky
   diodes on +12 V and −12 V for reverse polarity, 1N5817".
2. An op-amp does not reach its rail. `[datasheet]` OPA2197 SBOS737C, via the
   banked `datasheets/MANIFEST.csv` row: "output swing from either rail 5 mV
   typ / 25 mV max no-load, **95 mV typ / 125 mV max at RL = 10k**, 430 mV typ
   / 500 mV max at RL = 2k".

Derivation A is also conservative on the diode, which is the safe direction but
worth knowing: `[repo] config/figures.yaml:472`, from the banked curve,
1N5817 `V_f` = 0.24 V at 245 mA. The module analog +12 V rail carries six
OPA2197 (`I_Q` 1 mA typ, 1.3 mA max each `[datasheet]`), one INA828 and the
LM317's load `[repo] power-entry.md:39-44` — tens of mA, well below 245 mA, so
`V_f` is under 0.2 V and the true clip is nearer ±11.7 V. Nothing in the slice
breaks either way; the numbers should simply agree.

Given that ±11.45 V is load-bearing for M4, for the ADR's headroom claim, for
`mod-channels/notes.md`'s ±10.05 V margin and for pitch's ±600 cents reserve,
it is a candidate for `config/figures.yaml` with its derivation in one place.

---

## Node `DAC ch7` / figure `mod-reference` — the value is restated 13 times outside its owner — **M7**

CLAUDE.md §1: "the owning document states it and every other document **cites
it by name**. Do not copy the number." Owner is
`hardware/module/mod-channels/mod-channels.md` `[repo]
config/figures.yaml:243`. `[repo] grep -rn "3\.3333"` over the corpus
(`docs/review/`, `docs/log/`, `docs/research/` excluded per §6):

| File | Copies |
|---|---|
| `docs/decisions/0006-cv-channel-allocation.md` | **8** (lines 15, 21, 92, 105, 117, 125, 127, 248) |
| `hardware/module/mod-channels/bom.csv` + the generated `hardware/bom.csv` | 2 |
| `firmware/README.md` | 1 (line 50) |
| `hardware/module/pitch-stage/notes.md` | 1 (line 33) |
| `docs/reference/pcb-pipeline.md` | 1 (line 184) |
| *(owner, permitted)* `mod-channels.md` | 5 |

**Thirteen non-owner copies.** No `forbidden` pattern can protect a *current*
value, so if `mod-reference` ever moves, step 2 of CLAUDE.md §2 has to find all
thirteen by grep before the checker can report anything — and this figure's own
`escape_note` `[repo] config/figures.yaml:248-260` records that the last time
this happened the grep was written from the owner document and missed seven
spellings. The `mod-reference` entry is *aware* of this and its
`false_positive_note` explains carefully why `2.5 V` cannot be forbidden — the
harder exposure is the un-forbiddable live value sitting in thirteen places.

Same shape, one figure out: **`±11.45 V`** (M6) and **`±10.000 V` / `k = 3` /
`gain 4`** are restated across `mod-channels.md`, both `bom.csv` layers, ADR
0006 and `pitch-stage.md` with no register entry at all.

Contrast: `[repo] mod-channels.md:20-22` and `[repo] dac8568.md:10-12` both open
their Interfaces tables with "Quantities appear **only** as a citation into
`config/figures.yaml` — this table names nodes, it does not restate values",
and both tables honour it. The rule is applied in the tables and abandoned in
the prose.

---

## §4 — the tolerance section, third version: **correct** — S1

Re-derived independently from `R1 = 10 kΩ ±1 %`, `R2 = 30 kΩ ±1 %`,
`k = R2/R1`, `Vout = (1+k)·Vdac − k·V_ref`, `V_ref = 10/3`:

`[calc]` `k ∈ [3 × 0.99/1.01, 3 × 1.01/0.99] = [2.940594, 3.060606]`.

**Zero point.** Output at `Vdac = 2.5 V`, which is where nominal `Vout = 0`
`[calc] (1+3)(2.5) − 3(10/3) = 10 − 10 = 0`:
`Vout(2.5) = 2.5(1+k) − (10/3)k`, `dVout/dk = 2.5 − 10/3 = −0.8333`,
worst case `[calc] −0.83333 × (3.060606 − 3) = −50.505 mV` and
`+0.83333 × (3 − 2.940594) = +49.505 mV`. Page says **±50.5 mV** ✓.

**Span.** `[calc] (1 + 2.940594) × 5 = 19.70297 V`, `(1 + 3.060606) × 5 =
20.30303 V`; `−1.485 %` / `+1.515 %`. Page says **19.703–20.303 V
(−1.49 %/+1.52 %)** ✓.

**"1.6× better".** Four-resistor difference amp, `b = R4/R3 = 4.02` (the 40.2 kΩ
version), common-mode error at `V_cm = 2.5 V` is
`2.5 · [b'/(1+b')·(1+b) − b]`; worst case with the two ratios skewed opposite
ways `[calc] b = 4.10121, b' = 3.94040 → −0.032551 × 2.5 = −81.38 mV`.
`81.38 / 50.505 = 1.611` ✓ **1.6×**.

**"1.33× better".** Four-resistor span error is the full ratio error,
`[calc] 1.01/0.99 − 1 = ±2.0202 %`; `2.0202 / 1.51515 = 1.3333` ✓ **1.33×**.

**"About ±18 cents per octave".** `[calc] 0.015152 × 1200 = 18.18 cents` ✓.

**The `−196 mV` trap corroborates the 40.2 kΩ.** `[repo]
mod-channels.md:98` and `[repo] notes.md:56-63`: `R-OPAMP-IN` in series with the
(+) leg makes `b' = 40.2/11 = 3.6545`; `[calc] 2.5 × [3.6545/4.6545 × 5.02 −
4.02] = −196.3 mV`, and the top endpoint `[calc] 5 × 3.6545/4.6545 × 5.02 −
4.02 × 2.5 = +9.657 V`, against the page's "+9.657 V instead of +10.05" ✓.
Two independent numbers land, which is good evidence the four-resistor baseline
is the real circuit and not a reconstruction.

**Endpoints.** `[calc]` at the published `V_ref = 3.3333 V`: `4×0 − 3×3.3333 =
−9.9999 V`, `4×5 − 3×3.3333 = +10.0001 V`. At the ideal `10/3`: exactly
∓10.000 V. **No fudge.** The 0.1 mV is an artefact of writing `10/3` as four
decimals and is 500× smaller than the resistor term.

**Two things the section should say and does not.** (i) The `±50.5 mV` zero
figure is worst case *against a resistor tolerance that does not apply to the
`V_ref` term* — `V_ref` is a DAC code, so the intercept error also carries the
DAC's own INL/gain error, which nothing in the slice quantifies. (ii) Both
worst-case columns assume independent 1 % parts; the "buy from one reel"
mitigation `[repo] mod-channels.md:141-142` is asserted without a bound and is
the only thing standing between "worst case" and "typical".

`S1` is therefore: the section is right, and should record that the answer is
resistor-only.

---

## §5 — "one matching requirement instead of two": true by count, and the concession is stronger than the page makes it — S2

**True by count.** `[repo] mod-channels.md:96`. Four-resistor form: two ratios
per channel, `R4/R3` and `R4'/R3'`. Two-resistor form: one, `R2/R1`. ✓

**And it is better on the numbers**, which the page's own table says and its
concession paragraph then contradicts in tone: `±50.5 mV` against `±81.4 mV`
zero, `±1.52 %` against `±2.02 %` span, both re-derived above. Sixteen 1 %
parts have more ways to go wrong than eight.

**What the deleted requirement was buying**, precisely: in the difference amp
the zero depends only on **leg-to-leg matching** and is exactly zero for *any*
absolute ratio `b`. In the two-resistor form the single ratio sets the gain and
the intercept **together**, so absolute ratio error lands directly on the zero.
The page states this correctly in words `[repo] mod-channels.md:132-139`. The
practical consequence it does not draw: **a matched network buys much more in
the four-resistor form than in the two-resistor form**, because matching is
exactly what a matched network specifies. With eight discrete 1 % parts — which
is what `R-MODGAIN` is `[repo] hardware/bom.csv:86` — the two-resistor form
wins. The concession is real but it is a concession about *a part that is not
fitted*.

**The formula in that paragraph is wrong as printed.** `[repo]
mod-channels.md:134-135`: "The two-resistor zero is `2.5 − (10/3)k`". At the
nominal `k = 3` that evaluates to `[calc] 2.5 − 10 = −7.5 V`, not zero, and its
slope `−10/3` would give `[calc] 3.333 × 0.060606 = 202 mV` — four times the
`±50.5 mV` the table three paragraphs above states. The correct expression is
**`2.5(1+k) − (10/3)k`**, `[calc]` zero at `k = 3`, slope `2.5 − 10/3 =
−0.8333`, worst case 50.5 mV ✓. The `(1+k)` factor is dropped. The companion
expression `2.5[b/(1+b) − b/(1+b)]` `[repo] mod-channels.md:133` is also
missing its `(1+b)` — it should be `2.5[b'/(1+b')·(1+b) − b]`; as printed it is
`0 − 0`, trivially zero for reasons that have nothing to do with the circuit.
Both conclusions are right. Both formulas a reader could check are wrong, and
the wrong one lands within 1 % of the *first* version of this section's wrong
answer (200 mV) — an easy way for the fourth version to reintroduce the first.

**One argument for the adopted topology that nobody has written down, and it is
the strongest one.** `[from memory]` E24 and E96 standard values: E24 carries
10 k and 30 k; E96 carries 10.0 k, 39.2 k, **40.2 k**, 41.2 k, and **no 40.0 k**.

| Form | Ratio needed for gain 4 | Available? |
|---|---|---|
| Two-resistor non-inverting, `k = 3` | `R2/R1 = 3` | **30 k / 10 k, both E24** ✓ |
| Four-resistor difference amp | `R4/R3 = 4` | 40.2 k / 10 k → gain **4.02**, the fudge |
| Single inverting amp | `Rf/Rin = 4` | same problem |

`gain = 1 + k` is what makes it work: a gain of 4 needs a *ratio* of 3, and 3:1
is an E24 ratio while 4:1 is not. **This is the actual reason "exactly ±10.000 V"
is reachable and ±10.05 V was not**, and the page attributes it only to the
topology. It also bears directly on M8 below.

---

## `notes.md` — a live recommendation on a past-tense-only shelf, and it is not strictly better — M8

`[repo] hardware/module/mod-channels/notes.md:3-4` opens: "**Past tense only.**
… If a number here is still true, it is in the wrong file." `[repo]
notes.md:108-112` then closes with: "Taking the reference from a **DAC
channel** instead keeps the inverting topology *and* the safe clear… **it is
strictly better than what is drawn above.** Not adopted unilaterally: it is a
redraw of a settled page and the call belongs to the author."

That is an open recommendation against the adopted topology, filed where the
file's own rule says it cannot be, and where `mod-channels.md` points readers
for "the third option… still the author's call" `[repo] mod-channels.md:101-103`.
An open decision that lives on the superseded shelf is the shape CLAUDE.md §5
describes: the checker cannot see it, and the next reader has no way to tell a
live call from a closed one.

**And "strictly better" does not hold.** `[repo] notes.md:80-83` gives
`Vout = −(Rf/Rin)·Vdac + (1 + Rf/Rin)·V+ = −4·Vdac + 5·V+` with
`V+ = 2.000 V`. The arithmetic is right `[calc] −4(0) + 10 = +10 V; −4(5) + 10
= −10 V`. But it needs `Rf/Rin = 4` **exactly** — the ratio that is not in E24
or E96 (§5 table above). The adopted form's whole claim to "exactly ±10.000 V"
is that `gain = 1 + k` turns a gain of 4 into a *ratio* of 3. The proposed
replacement gives that back and lands on the same 40.2 k fudge the redraw was
performed to escape: `[calc] 40.2/10 = 4.02 → −4.02·Vdac + 5.02 × 2.0 =
+10.04 … −10.06 V`. It also introduces a **second** reference value (2.000 V)
alongside `mod-reference`, on a channel numbering that is already ambiguous (M5).

The claimed saving — "the offset DAC channel would need **no buffer**,
returning an OPA2197 half" `[repo] notes.md:86-88` — is real: four (+) inputs
draw ~5 pA each `[datasheet] OPA2197 I_B ±5 pA typ`. `[repo]
hardware/bom.csv:67` `U-OPA-PITCH` is six packages, twelve halves, **ten used**,
two spare, so it returns a half into a spare pool that `[repo]
hardware/bom.csv:76` `U-RESP` already proposes to consume entirely. Worth
something; not "strictly better".

Recommendation: move the open call to `mod-channels.md`'s "Still open" section
with the E96 objection recorded against it, or close it. Do not leave a live
"strictly better" on the past-tense shelf.

---

## `circuit.yaml` and the Interfaces table still point at the pre-split DAC — S3

`hardware/module/dac8568/` was split out of `digital-and-supervision` on
2026-09-21 `[repo] dac8568.md:3-6`. The mod-channels side did not follow:

- `[repo] mod-channels.md:26` — `DAC ch7` peer = `module/digital-and-supervision`
- `[repo] mod-channels.md:27` — `DAC ch2`–`ch5` peer = `module/digital-and-supervision`
- `[repo] mod-channels.md:28` — `CLR` peer = `module/digital-and-supervision`
- `[repo] hardware/module/mod-channels/circuit.yaml:55` — `circuit:module/digital-and-supervision`, and **no** `circuit:module/dac8568`

while `[repo] hardware/module/dac8568/circuit.yaml:56` *does* declare
`circuit:module/mod-channels`, and `[repo]
digital-and-supervision/digital-and-supervision.md:27` hands `SCLK`/`DIN`/`SYNC`
to `module/dac8568` and claims no DAC outputs at all. The edge resolves — both
ids exist — so `check-staleness.py` passes, which is precisely the limit
`[repo] hardware/module/dac8568/circuit.yaml:23-27` documents for itself:
"every edge RESOLVES… Correctness of the edge itself is a reader's job and has
not been done."

This is **not** a §6 historical path (those are in `docs/review/`,
`docs/log/`, `docs/research/`). It is a live corpus page naming a peer that no
longer owns the net.

---

## Checked and **not** defects — N

Recorded per CLAUDE.md "Checking an agent's work", so the next reviewer does
not re-litigate them.

1. **`V_ref` is refreshed like the others — consistently, everywhere.**
   `[repo] docs/decisions/0006-…:248` "refreshed every pass, like the other
   five"; `[repo] firmware/README.md:50` same; `[repo] mod-channels.md:180`
   "refresh all six populated channels every pass". The superseded "written
   once at boot" is in `mod-reference`'s `forbidden` list `[repo]
   config/figures.yaml:245` and the checker finds no instance. Channel count
   is consistent across four documents: six populated = pitch + four mods +
   ch 7 `[repo] hardware/bom.csv:84` `R-BIAS-DAC` qty **6** "the six DAC-driven
   nodes", `[repo] hardware/bom.csv:88` `R-OPAMP-IN` qty **7** = "Pitch, mod
   1-4, the mod offset buffer, the VREFOUT follower", `[repo]
   docs/reference/latency-budget.md:146` "six DAC channels", `[repo]
   docs/decisions/0006-…:255` "already assumes six DAC channels serviced every
   250 µs pass". ✓ No slack anywhere; the sixth word is genuinely pre-paid.
2. **"Do not be tempted to split it into four buffers"** `[repo]
   mod-channels.md:206-209` is safe, though "all four channels share **exactly**
   the same offset error" is not exactly true. Because each `R1` terminates on
   a moving summing node (M2), the buffer's output current is
   channel-dependent, so a finite closed-loop output impedance does cross-couple
   the channels. Bounded: `[datasheet]` OPA2197 `Z_O` open-loop 375 Ω typ,
   GBW 10 MHz; loop gain at the 4 kHz update rate `[calc] 10 MHz/4 kHz = 2500`
   → `Z_out ≈ 375/2500 = 0.15 Ω`. A 1 mA worst-case current step moves `V_ref`
   by `[calc] 0.15 mV`, i.e. `0.45 mV` on all four outputs — **1 %** of the
   ±50.5 mV resistor term. The conclusion stands with two orders of margin; only
   the word "exactly" is wrong.
3. **`D-JACK-CLAMP` is drawn on the correct side.** `[repo]
   mod-channels.md:55-57` puts the BAV99 between the op-amp output and
   `R-OUT-PROT`, matching `[repo] hardware/bom.csv:89` "Clamp diodes on the
   DRIVER side of R-OUT-PROT". An external injection at the jack reaches the
   clamp through the 1 kΩ, which is the current limit. ✓
4. **`C-FILT-MOD` corner and side.** `[calc] 1/(2π × 1 kΩ × 82 nF) =
   1.941 kHz` ✓ against "1.94 kHz" `[repo] mod-channels.md:112`. On the jack
   side of `R-OUT-PROT`, outside the loop, consistent with `[repo]
   mod-channels.md:29` and `[repo] hardware/bom.csv:85`. ✓
5. **Resolution cost.** `[calc] 20/65536 = 305.2 µV`, `10/65536 = 152.6 µV`
   against `[repo] docs/decisions/0006-…:141` "153 µV/LSB … 305 µV/LSB" ✓.
6. **`R-OPAMP-IN` on the shared buffer costs nothing.** `[calc]` drop =
   `I_B × 1 kΩ = 5 pA × 1 kΩ = 5 nV` `[datasheet]` OPA2197 `I_B` ±5 pA typ. The
   "harmless, feeds a (+) input" row `[repo] mod-channels.md:98` is right, and
   `R-BIAS-DAC` sits at the DAC pin ahead of it, so it forms no divider ✓
   `[repo] hardware/module/pitch-stage/bom.csv:9`.
7. **Internal reference disabled at power-up does not break park-at-0 V.**
   `[datasheet] SBAS430E` p.1: "a 2.5 V, 2 ppm/°C internal reference **(disabled
   by default)**". Zero scale is 0 V with the reference off or on, so the 0 V
   park holds through the window before firmware's reference-enable write
   `[repo] hardware/module/pitch-stage/pitch-stage.md:145-147`. ✓
8. **The `LK-CLR` / power-on pair is a complete list of what asserts `CLR`.**
   `[repo] hardware/bom.csv` `R-CLR-PU`: the 74HC123 watchdog is deleted, `CLR`
   is pulled inactive and nothing drives it. `[datasheet] SBAS430E` adds a third
   path the corpus does not mention but does not need — a **software reset**
   (`C3..C0 = 0111`) is a power-on reset, which also resets the clear-code
   register to default. Harmless here, and it means `Voffset` clears on that
   path too. ✓
9. **The `−7.5…+12.5 V` hazard arithmetic.** `[calc] 4×0 − 3×2.5 = −7.5`;
   `4×5 − 3×2.5 = +12.5` ✓ in all four places it is stated. Only the added
   "wrong span" in `firmware/README.md` fails (M4a).
10. **`4X − 3X = X` and the `+2.5 V` B/D figure.** `[calc]` B/D midscale on a
    C/D-gain part is 2.5 V; `4 × 2.5 − 3 × 2.5 = +2.5 V` ✓ `[repo]
    mod-channels.md:186`. The arithmetic is right; only the mechanism it is
    attached to is wrong (M3).

---

## Fix list, ordered

| # | Node | Fix |
|---|---|---|
| M1 | `R1` / `V_REF_BUF` | Land `R1` on the column-19 rail in the drawing; add one sentence saying `R1` goes to the inverting input. Redraw the follower's feedback. Add `R-BIAS-DAC` to the drawing and to `circuit.yaml`. |
| M2 | `V_REF_BUF` | Replace "into 2.5 kΩ" with the signal-dependent range `+1.33 mA … −0.67 mA`, 0.33 mA at park. Say the buffer must sink. Correct `figures.yaml`'s `escape_note`, which fixed the value and kept the model. |
| M3 | `CLR` | Separate pin-`CLR` (clear-code register, grade-independent) from power-on reset (grade-dependent) in `mod-channels.md` and ADR 0006. Promote the clear-code-register default to a stated dependency. Settle the `CLR` peer to one circuit. |
| M4 | `MOD 1`–`MOD 4` | "shifts +10 V; rails above +1.45 V commanded", not "pins at +11.45 V". Drop "wrong span". Move "indefinitely" onto the case that is indefinite, and rest the fixed-divider argument on module-powered-controller-absent. |
| M5 | `DAC ch7` | Publish the `ch N` → `DAC-A..H` / `A3..A0` mapping once, and the 16-bit code for `mod-reference`. |
| M6 | `MOD 1`–`MOD 4` | One derivation of ±11.45 V; delete "two Schottky drops" from `mod-channels/notes.md` and `pitch-stage.md`. Consider a register entry. |
| M7 | `mod-reference` | Replace the 13 non-owner copies of `3.3333 V` with citations. |
| M8 | `V_REF_BUF` | Move the "strictly better" inverting-amp call off the past-tense shelf; record the 4:1-is-not-E96 objection against it. |
| S1 | — | Note the tolerance answer is resistor-only, and bound "one reel". |
| S2 | — | Fix `2.5 − (10/3)k` → `2.5(1+k) − (10/3)k` and the `b/(1+b)` companion. Add the E24 ratio argument. |
| S3 | — | Point the Interfaces table and `circuit.yaml` at `module/dac8568`. |
