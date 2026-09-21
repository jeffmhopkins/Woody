# C1 — Break the key chain

**Falsification pass, 2026-09-21.** Written cold: `docs/review/**` and
`docs/research/**` were not read. Sources are `hardware/controller/cluster-boards.md`,
`hardware/controller/carrier.md` §3–§4, `config/key-layout.yaml`,
`docs/decisions/0001-mcu-and-board-partitioning.md`, `hardware/bom.csv`, plus
`0009` and `0014` for channel geometry and LED current.

Marking: `[repo] <file>`, `[calc]` with the arithmetic inline, `[web] <url>`,
`[from memory]`. Findings are indexed by **circuit node** or **BOM ref**.

Every enumeration below was run as an exhaustive symbolic solve, not reasoned by
hand: for each corrupted frame the eight marker positions become constraints on
the key bits, and a case "passes" only if those constraints are simultaneously
satisfiable by some real hand position. The scripts are reproducible from the
tables here; the marker map used is exactly §4's.

---

## Verdicts

| # | Claim | Verdict |
|---|---|---|
| 1 | The 8-bit marker catches dead / unclocked / stuck / all-zeros / all-ones / stuck bus / shift-by-one | **BROKEN** — three undetected families, one of them the chain reorder this very page proposes |
| 2 | A `SH/LD` glitch corrupts the whole word, and ground-per-signal prevents it | **SURVIVES, but the stated mechanism is the wrong one** — 31× margin capacitively, 6.2× inductively, and it is the inductive path that ground-per-signal actually rescues. One measurement outstanding |
| 3 | Two agreeing samples remove the single-sample credulity | **BROKEN** — the dominant aggressor is a 750 µs burst against a 250 µs scan, so consecutive samples are not independent |
| 4 | `LK-SER` + `R-SER-TERM` make the self-test a firmware choice at zero hardware cost | **BROKEN** both ways — a named healthy chain it calls broken, a named broken chain it calls healthy, and the cost is not zero |
| 5 | 125 µs release / 5.7 µs press is an asymmetric debounce | **BROKEN** — 125 µs is 1/12 to 1/50 of a real bounce train; a single press can be read as multiple presses |

---

## Claim 1 — the marker pattern. **BROKEN.**

### What it does catch — confirmed, not assumed

Node `N-QH` (`J-CHAIN` pin 8 → `IO40`), `N-SCK` (pin 2 → `IO38`), `N-SHLD`
(pin 4 → `IO7`), `N-SER` (pin 6 → `IO33`), device `U-KEYS` ×4.

Exhaustive over all four devices and both stuck polarities, **24 of 24 hard
faults fail the marker**: device stuck high, stuck low, dead (`VCC` open),
unclocked, loads-but-does-not-shift, shifts-but-does-not-load (both with
`R-SER-TERM` high and with `IO33` driven low), `SCK` open at each of the four
hops, `SH/LD` open at each of the four hops, serial link open mid-chain
(floating either way), serial link shorted to either flanking ground,
all-zeros, all-ones, stuck bus, shift by ±1. `[calc]`

The two-bits-per-device argument is sound and the eight bits earn their place.
Everything below is about what the page then *infers* from that.

### BREAK 1 — `chain:` order. The one swap that passes is the one the page proposes.

`[repo] cluster-boards.md` §*The four boards* proposes reordering the chain to
`RT → RH → LH → LT` to save a body-thickness crossing, and warns "**If the order
changes, the bit allocation in §4 changes with it**". It is listed first under
*Still open*.

Run all 23 non-identity permutations of the four devices against §4's marker
map. **Exactly one passes: `RT → RH → LH → LT`.** `[calc]` It passes whenever
`LH5` is not pressed — one key, released most of the time.

Why, in copper: under that order the absolute marker positions land on

```
  bit 20  = left_hand  byte-position 4 = LH5      (needs 1 → LH5 released)
  bit 21  = left_hand  byte-position 5 = strap 0  ✓
  bit 29  = left_thumb byte-position 5 = strap 0  ✓
  bit 30  = left_thumb byte-position 6 = free bit, pulled UP = 1  ✓
```

Three of the four are satisfied by straps and a pull-up that happen to sit in
the right places. `[repo] cluster-boards.md` §4 tables.

What the player hears: bits 16–19 now carry `LH1..LH4` while firmware reads them
as `LT1..LT4`, and bits 24–27 carry `LT1..LT4` read as `LH1..LH4`. **Left-hand
fingering operates the octave/register keys and the left thumb operates the
fingering.** `LH5` becomes a dead key — bit 28 reads `left_thumb`'s hard-wired
`C1`, permanently "released" — and the *only* symptom of pressing `LH5` is that
the error counter ticks. The instrument therefore reports "the loom is bad"
precisely when the player touches the one key that would have revealed the real
fault. `[calc]`

This is not a hypothetical build error. Three things make it live:

- The reorder is an open decision in the same document `[repo] cluster-boards.md`.
- The marker levels are **not in `config/key-layout.yaml`**. That file is ADR
  0010's single source of truth and generates the firmware bit mapping
  `[repo] key-layout.yaml` lines 1–8, but it carries only `spare_bits_marker: 8`
  and a comment pointing at prose in another file. The levels live in a Markdown
  table. Nothing regenerates when `chain:` changes.
- `LK-SER` exists specifically so all four boards are one schematic
  `[repo] bom.csv` row `LK-SER`. Identical boards, identical `J-CHAIN` pinout at
  all eight positions `[repo] bom.csv` row `J-CHAIN`, four identical ribbon
  assemblies. Interchangeability was bought on purpose.

**Root cause, and it is structural.** The rule "one bit high and one bit low per
device" admits only two signatures, `(1,0)` and `(0,1)`. Four devices, two
signatures — at least two devices must share one. Device *identity* is therefore
outside the reach of an 8-bit marker built to this rule, whatever levels are
chosen. The marker checks each device's *direction*, never its *place in the
chain*. The page's "every device fails it on its own whichever way it failed" is
true and is not the same claim as the one the reader takes away.

**Fix, tested.** Flip `left_thumb`'s pair: bit 20 → **0**, bit 21 → **1**. The
pattern becomes `1 0 · 0 1 · 0 1 · 0 1`. Re-running the full enumeration:
**all 23 permutations fail**, all 24 hard faults still fail, and the
leading-clock-shift hole (BREAK 3) closes too. Cost: one extra mid-shift reload
point, 12 instead of 11. `[calc]` It is two characters in §4 and two straps on
one board. The page's own "not a repeating byte" test is what missed it — the
pattern *is* a repeating nibble, `1001 1001`, and that is exactly the symmetry
the swap exploits.

### BREAK 2 — the mid-shift `SH/LD` reload passes 11 times out of 31.

This is the fault ADR 0001 names as the chain's worst case — "a glitch on
`SH/LD` reloads every register mid-shift and corrupts the whole word"
`[repo] 0001` fix 1, and again `carrier.md` §3. The 32-stage chain is reset to
its parallel state, so a reload after `n` clocks gives

```
  received[i] = P[i]      for i < n
  received[i] = P[i-n]    for i >= n
```

Exhaustive over `n = 1..31`, with the three reserved spare-switch positions
treated as permanently released (they are `network fitted, pad unloaded`
`[repo] bom.csv` row `SW1-n`, so their inputs sit at `R-KEY-PU`):

| `n` | marker needs | key bits reported wrong |
|---|---|---|
| 5 | `RT2`↑ `RT3`↓ `RH2`↓ `RH3`↑ `LT1`↓ `LH1`↓ `LH2`↑ | **16** |
| 12 | `RT3`↓ `RH1`↑ `RH2`↓ `LT2`↓ `LT3`↑ | **11** |
| 19 | `RT2`↑ `RT3`↓ `RH3`↓ `RH4`↑ | **6** |
| 20 | `RT1`↑ `RT2`↓ `RH2`↓ `RH3`↑ | **5** |
| 21 | `RT1`↓ `RH1`↓ `RH2`↑ | **5** |
| **22** | **`RH1` released — that is all** | **5** |
| 27 | `RT3`↓ | 2 |
| 28 | `RT2`↓ `RT3`↑ | 1 |
| 29, 30, 31 | weak or none | 0 (only free bits) |

`[calc]` (↑ = released, ↓ = pressed.)

**11 of 31 reload points produce a marker-clean frame; 8 of those carry wrong
key data.** If the three spare switches are ever fitted, it is **21 of 31**, and
`n = 2,3,4` corrupt 17–19 bits each.

The worst is `n = 22`, whose entire precondition is that `RH1` is not pressed.
Its effect: `bit24 ← RT3`, and `bit25..28 ← ` the three unloaded spare positions
and a marker strap — all hard 1. **Every left-hand key reads released**, no
matter what the player's left hand is doing, and the error counter stays at
zero. On a woodwind that is not a wrong note, it is the wrong *register* — the
fingering collapses to all-LH-open. `[calc]`

Two mitigations the page might reach for, and why they are weaker than they look:

- *"It needs a specific chord."* `n = 22` needs one key released. `n = 27..31`
  need one or two. And the chain is scanned 4 000 times a second — a chronically
  noisy `SH/LD` re-rolls this lottery 720 000 times in a three-minute piece.
- *"The two-sample rule catches it."* Only if `n` is random per scan. See
  Claim 3: the dominant aggressor is periodic and bursty, so `n` is not random.

### BREAK 3 — "a frame shifted by one position" is true, and does not generalise.

Shift by ±1 both fail — correct. But run all shifts `−31..+31`: **`s = −5`
passes** (five extra leading clocks, or `SH/LD` still low for the first five
clocks, filling from `R-SER-TERM`), under a seven-key chord, with **21 of 21
networked positions reported wrong**. `[calc]` With the spare switches fitted,
`s = −2, −3, −4, −5` all pass.

`s = −5` is not exotic. It is what a `SH/LD` release that lags the first SPI
clock produces, which is a firmware-ordering bug, and it is also what five
`SCK` runt pulses produce. The sentence in §4 is literally true and reads as a
general statement about framing. It is not one.

### BREAK 4 — 24 of 32 positions have no coverage at all, ever.

A single-bit flip is detected at bits 6, 7, 14, 15, 20, 21, 29, 30 and nowhere
else: **8/32 = 25 %**. The 21 networked positions and 3 free bits are never
covered. `[calc]` Burst coverage by burst length `L`, over all start positions:
L=1 25 %, L=2 39 %, L=3 50 %, L=4 62 %, L=5 75 %, L=6 85 %, L=7 96 %, L=8 100 %.
`[calc]` The page says this ("it is a framing check, not an error-detecting
code" `[repo] 0001`) and then lists eight things it catches without listing the
one it does not: **a single wrong key bit, which is the only corruption that
produces a wrong note rather than a held frame.**

There is a sharper version of this. `[repo] cluster-boards.md` §4: *"Marker bits
strap straight to the rails — no resistor, no capacitor."* The eight marker
nodes are therefore the only eight register inputs in the instrument that do
**not** share a component type with the 21 that carry the music. An open
`R-KEY-SER`, a cracked `C-KEY`, a lifted `R-KEY-PU` pad, a switch pin that did
not wet — none of them can move a marker bit, by construction. The 16 parts
saved are real; so is the fact that the check now validates a population it was
never drawn from. Worth 16 parts either way, but the page should say which 24
nodes it is not speaking for.

### Which undetected cases give a wrong note rather than silence

Ranked by what a player hears:

1. **Chain order `RT→RH→LH→LT`** — permanent, systematic wrong notes, counter
   clean, and the counter ticks only on the one key that would explain it.
2. **`SH/LD` reload at `n = 19..22`** — the left hand goes dead or transposes,
   intermittently, counter clean.
3. **Single-bit flip on any of 24 positions** — one spurious note-on at full
   velocity `[repo] 0001` §Key-line signal integrity, counter clean.
4. **`s = −5` frame shift** — everything wrong at once, which at least sounds
   broken rather than like a playing mistake.

Silence (held previous frame + counter) is what all 24 hard faults give. The
marker's design centre is exactly right; its blind spot is exactly the class
that sounds like the player's fault.

---

## Claim 2 — the `SH/LD` glitch and the alternating-ground ribbon. **SURVIVES — on a mechanism the page does not name.**

Node `N-SHLD`: `IO7` → `R-CHAIN-SER` 100 Ω → `J-CHAIN` pin 4, 265 mm of 12-way
1.27 mm ribbon with `GND` on pins 3 and 5, into four `U-KEYS` pin 1 inputs.

Nobody had computed this. Here it is.

### Inputs

- Required excursion: `SH/LD` sits at 3.3 V during the shift; a guaranteed load
  needs it below `V_IL` = 0.99 V → **2.31 V** of droop. `[repo] 0001` §, and
  `[web]` 74HC165 DC table gives `V_IL` 0.5 V @ 2.0 V, 1.35 V @ 4.5 V, i.e.
  0.3·VCC, confirming the page's `[from memory]` figure —
  https://assets.nexperia.com/documents/data-sheet/74HC_HCT165.pdf (blocked by
  the egress proxy; values via search result summary, so still treat as
  unconfirmed against a vendor PDF).
- Minimum load pulse width `t_W(PL)`: **50 ns @ 2.0 V, 22 ns @ 4.5 V, 20 ns @
  5.5 V** `[web]` same source. Interpolating, **≈30 ns at 3.3 V**. A glitch must
  be both deep *and* 30 ns wide.
- Victim capacitance `C_v` ≈ **26 pF** — ADR 0001's own loom figure `[repo] 0001`.
- Source impedance: `R-CHAIN-SER` 100 Ω + ESP32-S3 GPIO ≈ 40 Ω = **140 Ω**.
- The key ribbon and the LED strips **share the same side channel**
  `[repo] 0009` §Consequences: *"The two side channels are shared: LED strips on
  both sides, looms alongside."* So take separations of 3–10 mm, not "a
  different part of the instrument".

### Capacitive, from the WS2815 data line — nowhere near

Aggressor: 5 V from `U-LVLSHIFT` through `R-LED-SER` 330 Ω into ~40 pF of strip
input plus lead → τ = 13.2 ns, t_r(10–90) = 29 ns, **dV/dt = 0.172 V/ns** `[calc]`.

Two round conductors, 0.32 mm diameter, length 265 mm, εr ≈ 1.5 for a mostly-air
channel: `C = πε₀ε_r·l / arccosh(d/a)` `[calc]`

| geometry | `C_m` | undriven step | **driven peak** = `R_s·C_m·dV/dt` |
|---|---|---|---|
| strip 3 mm away | 3.05 pF | 525 mV | **74 mV** |
| strip 5 mm away | 2.67 pF | 466 mV | **65 mV** |
| *in the same ribbon, no ground between* | 8.01 pF | 1 178 mV | **193 mV** |

The driven column is the right one: τ_victim = 140 Ω × 26 pF = 3.6 ns is seven
times shorter than the 29 ns aggressor edge, so the driver tracks the
disturbance out and the node never reaches the open-circuit step. `[calc]`

**Margin: 2.31 V / 74 mV = 31×** at the worst realistic spacing. To reach `V_IL`
on the driven line you would need `C_m` = 96 pF over 265 mm = **362 pF/m**,
which is roughly seven times the total capacitance of ribbon cable to *all* its
neighbours. `[calc]` No geometry inside this instrument produces it. And the
glitch would still be ~29 ns wide against a ~30 ns `t_W(PL)`.

**So the claim's own named aggressor fails by 31× on amplitude and again on
pulse width — and the alternating ground is not what saves it.** Delete the five
grounds, keep everything else, and the capacitive number changes only through
`C_m` (guarding), a factor of two or three. The 31× comes from HC's 2.31 V noise
margin and a 140 Ω-driven line.

### Inductive, from the 12 V LED PWM current — this is the real one, and it is the one ADR 0001 argued away

ADR 0001 fix 1's correction says *"There is no 12 V edge"* `[repo] 0001`. True of
the *voltage*. ADR 0014 says of the same rail: *"modulates its draw by hundreds
of milliamps at the ~2 kHz PWM rate"* `[repo] 0014` line 115, and gives 1.01 A
at 60/m full white `[repo] 0014` line 124. **There is a 12 V current edge**, and
current edges couple through loop area, which is precisely what ground-per-signal
controls. Killing the capacitive model took the inductive one with it.

Loop area: 1.27 mm × 265 mm = 3.36e-4 m² with a ground beside `SH/LD`;
14 mm × 265 mm = 3.71e-3 m² with one shared return at the far end of a 12-way
ribbon — **11× larger**. Field from the strip's +12 V/GND pair (s ≈ 5 mm):
`B = µ₀·I·s / (2π d²)`. `[calc]`

| separation | return scheme | `M` | at 1 A/100 ns | at 1 A/1 µs |
|---|---|---|---|---|
| 3 mm | **ground-per-signal** | 37.4 nH | 374 mV — **6.2×** | 37 mV — 62× |
| 3 mm | one shared return | 412 nH | 4 122 mV — **0.6× — LOADS** | 412 mV — 5.6× |
| 5 mm | **ground-per-signal** | 13.5 nH | 135 mV — 17× | 14 mV — 172× |
| 5 mm | one shared return | 148 nH | 1 484 mV — **1.6×** | 148 mV — 16× |
| 10 mm | **ground-per-signal** | 3.4 nH | 34 mV — 69× | 3 mV — 686× |
| 10 mm | one shared return | 37 nH | 371 mV — 6.2× | 37 mV — 62× |

`[calc]` And this spike, unlike the capacitive one, is **~100 ns wide — wider
than `t_W(PL)`**, so amplitude is the only thing standing between it and a load.

**Verdict: the margin is real (6.2× worst case) and the alternating-ground
ribbon is what makes it real — for the 12 V PWM current, not for the 800 kHz
data line the page cites.** A single shared return in the same channel at 3 mm
sits at 0.6× and *would* glitch. ADR 0001 calling fix 1 "the highest-value item
on this list" is correct; the reason given for it is not the reason it is true.

### UNDECIDABLE — one number

`di/dt` at the WS2815's internal PWM edge is `[from memory]` at 1 A/100 ns and
nothing in the repo measures it. The whole inductive column scales linearly with
it. Break-even at 3 mm with ground-per-signal is **6.2 A/µs**; 1 A/µs is safe at
62×.

**Measurement that settles it:** current probe (or a 0.1 Ω shunt) on the
`LED-SIDE` +12 V feed downstream of `C-STRIP-BULK`, scope at 20 MHz bandwidth,
strip driven full white, trigger on a PWM edge, read `di/dt`. Ten minutes at E4.
`C-STRIP-BULK` 470–1000 µF at each feed point `[repo] bom.csv` row
`C-STRIP-BULK` should localise the fast loop to the strip itself, which is the
reason to expect the answer to be comfortable — but it is an expectation, not a
measurement, and "bulk belongs at the load" is the whole justification for that
row.

### Two `N-SHLD` items that fall out of this and are not in the BOM

- **`U-TVS-CHAIN`** is drawn on `carrier.md` §3 as `** PROPOSED **` and has
  **no `bom.csv` row** `[repo] bom.csv` — grep finds `D-TVS-BREATH` and
  `D-TVS-PWR` only. `R-CHAIN-SER` likewise has no row. Both are on the four
  signals whose blast radius is the whole word.
- **An open `SH/LD` is worse than a glitch and is not discussed anywhere.** A
  disconnected HC input has no pull and sits in its own linear region, where the
  input inverter is a high-gain amplifier with 100 nF of local decoupling
  (`C-DECOUPLE-165`) as its supply — i.e. an oscillator. That produces
  *continuous* mid-shift reloads at random `n`, which is BREAK 2 fired 4 000
  times a second. A 100 kΩ pull-up to 3V3 on `SH/LD` at each `U-KEYS` — four
  0805s, one per cluster board — fails the loom safe instead of noisy, and lets
  the marker see it (all four devices reload constantly → `n` random → ~65 % of
  frames fail the marker → the counter runs away, which is the right symptom).

---

## Claim 3 — two consecutive agreeing samples. **BROKEN.**

`[repo] 0001` §Two firmware rules: *"Require two consecutive agreeing samples
before a note-on… This keeps the asymmetric debounce's fast attack while
removing its single-sample credulity."*

### The failure it does not remove: the aggressor is a burst, not an impulse

The rule's entire force rests on consecutive scans being independent. The
dominant aggressor in the channel is not.

`LED-SIDE` is one 1 m reel cut into two 420 mm runs, 60/m → **25 pixels per
run** `[repo] 0014` lines 29/124. A WS2815 refresh is 24 bits per pixel at
800 kHz: `25 × 24 / 800 kHz = ` **750 µs** `[calc]` — **three consecutive 250 µs
scans**. If both runs ever share one data line, 1 500 µs = **six**. `[calc]`

So whatever the 800 kHz data line can do to the chain, it does for three to six
scans in a row. "Two consecutive agreeing samples" is satisfied by construction
during an LED refresh. The rule filters single-scan events; the instrument's
loudest neighbour does not produce single-scan events.

The same argument applies to the 2 kHz PWM: 50 pixels × 3 channels = 150
independent PWM channels inside a 500 µs period, so current edges arrive roughly
every 3.3 µs `[calc]` — dense on the 32 µs scale of a 32-bit read at 1 MHz
`[repo] 0001` §Consequences. There is no quiet window to sample in.

### Can two consecutive samples agree on a WRONG value? Yes, four ways

1. **Any marker-passing corruption that is static** — Claim 1 BREAK 1. The chain
   order is wrong forever; every sample agrees with the last one.
2. **Any physical fault slower than 500 µs** — a cracked `R-KEY-SER` joint, a
   switch pin that did not wet, an IDC contact gone resistive under strap
   movement, a whisker across `C-KEY`. The rule's stated scope ("single-sample
   credulity") already concedes this; the page does not say that this is the
   entire population of real faults in a bonded body, because a bonded body has
   no transient-handling problem — it has a permanent-fault problem.
3. **A `SH/LD` reload at a stable `n`** — BREAK 2. If the disturbance is
   phase-locked to anything (the SPI transaction itself, a PWM harmonic, the
   scan's own 4 kHz), `n` repeats and so does the wrong frame.
4. **Bounce aliasing.** The press path's pole is `1/(2π·100 Ω·47 nF)` =
   **33.9 kHz**, 17× above the 2 kHz Nyquist of the 4 kHz scan `[calc]`. The
   release path's pole is 1.54 kHz, below Nyquist `[repo] cluster-boards.md` §2.
   **The network anti-aliases the edge that is not the problem and passes the one
   that is.** Broadband bounce energy near 4 kHz and its multiples folds down to
   near-DC in the sample stream, which is exactly a run of consecutive identical
   samples. The 54 dB figure quoted at 800 kHz is real and is about the wrong
   frequency: nothing in the design attenuates 3.5–4.5 kHz on the press edge.

### Interaction with the 125 µs filter and the 250 µs scan

`[calc]`, τ = 2.2 kΩ × 47 nF = 103 µs, from 0 V toward 3.3 V:

| level | reached at |
|---|---|
| `V_IL` 0.99 V (guaranteed low ends) | 36.9 µs |
| VCC/2 = 1.65 V (where a real HC input actually trips) | **71.7 µs** |
| `V_IH` 2.31 V (guaranteed high begins) | 124.5 µs |

The node sits **inside the indeterminate band for 88 µs of every release**, and
the scan period is 250 µs, so **35 % of releases are sampled while the input is
neither a guaranteed 1 nor a guaranteed 0** `[calc]`. 88 µs < 250 µs, so two
*consecutive* samples cannot both land in the band — the rule does cover this
one, for note-on. Note-*off* is not two-sample gated ("Note-off stays filtered as
before" `[repo] 0001`), and the firmware filter that is doing that work is
unwritten: `firmware/` contains a README and nothing else `[repo] firmware/`.

**Net: the rule costs 250 µs and buys protection against the one class of fault
a bonded, unopenable instrument is least likely to have.** It should be kept —
it is free — but it should not be counted as an answer to anything in Claim 1.

---

## Claim 4 — `LK-SER` + `R-SER-TERM`. **BROKEN both ways.**

BOM refs `LK-SER` (3-pad solder link, qty 4, status `open`) and `R-SER-TERM`
(10 kΩ 0805, qty 1, status `open`) `[repo] bom.csv` rows 104–105. Node `N-SER`:
`IO33` → `R-CHAIN-SER` 100 Ω → `J-CHAIN` pin 6, passed through all four hops to
the chain-end `U-KEYS` pin 10.

### The healthy chain the self-test reports as broken

**`LK-SER` in position A on the chain-end board.** `[repo] cluster-boards.md` §3
drawing:

```
   IN pin 6 (SER passthrough) ──┬──[LK-SER position B]──► 74HC165 SER (pin 10)
                                │
                        [R-SER-TERM 10k]
                                │
                               3V3
```

Position A instead connects pin 10 to `OUT` pin 8 — and the chain-end board has
no `OUT` connector fitted (`J-CHAIN` qty 1 for `LH` `[repo] cluster-boards.md`
component table). So pin 10 goes to an unpopulated pad.

**Normal play is completely unaffected.** In a 32-clock read the chain-end
device's serial input occupies stage 31 and never reaches `QH`. All 32 bits are
correct, the marker passes, the instrument plays. **The self-test fails.** A
build error on a 3-pad link — the kind of thing that is set once, by hand, on a
board that then bonds into the body — produces a permanent "the loom is broken"
report on a loom that is fine. Since the self-test's advertised job is to
distinguish a broken loom from a stuck bit `[repo] carrier.md` §3, its first
false positive is unfalsifiable from inside the instrument.

**And `R-SER-TERM` does not cover it.** As drawn, the 10 kΩ pulls the
*passthrough node*, on the upstream side of the link. With `LK-SER` in position
A, `U-KEYS` pin 10 is a **floating CMOS input** — the exact fault ADR 0001 fix 6
exists to eliminate `[repo] 0001` — and `R-SER-TERM` is not on it. The BOM row
says the part *"Holds the far serial input high when nothing drives it, which is
the tied-off case ADR 0001 specified"* `[repo] bom.csv` row `R-SER-TERM`. That is
true only in position B. **Move `R-SER-TERM` to the common pin of `LK-SER`**
(the `U-KEYS` pin 10 side) and it holds the input in both positions, which is
what the row already claims and costs nothing to correct before layout.

### The broken chain the self-test reports as healthy

The self-test walks a pattern from the chain-end `SER` to `QH` at the carrier.
It exercises the 32 shift stages, `SCK`, and the pin-6 conductor. It **does not
touch `SH/LD`, does not touch any parallel input, and does not touch any of the
63 network passives.**

- **`SH/LD` open anywhere.** The chain shifts perfectly; the self-test passes;
  the frame is garbage. The marker does catch the frame — but the operator is
  now holding a green self-test and a red marker counter, which the design says
  means *"one bit is stuck"*. The diagnosis is inverted on the one fault whose
  blast radius is the whole word.
- **Every parallel-input fault, permanently.** Open `R-KEY-SER`, lifted
  `R-KEY-PU`, shorted `C-KEY`, an unwetted switch pin, a `U-KEYS` input pin with
  a solder void. Invisible to the self-test by construction, and invisible to
  the marker because the marker straps bypass the network entirely (Claim 1
  BREAK 4). **24 of 32 register inputs have no test in the instrument, at any
  time, by any mechanism.**
- **Intermittent joints.** The self-test is a point-in-time check; a joint that
  opens when the strap moves is the fault the loom design exists to survive.
  Running the self-test every scan would cost 32 more clocks — SPI3 goes from
  32 µs to 64 µs of 250 µs, 13 % → 26 % `[calc]`, still comfortable against
  `carrier.md` §4's loop budget — and *that* is the version worth having. As a
  boot-time check it adds little the marker does not already provide.

### "Zero hardware cost" is not zero

- `R-SER-TERM` is a part with a BOM row `[repo] bom.csv` row 105. The page's own
  text says "at the cost of one resistor"; the summary sentence says zero.
- `LK-SER` is four solder links `[repo] bom.csv` row 104 — four build steps, one
  of which has a wrong setting that is undetectable in play (above) and one of
  which (**position B on a middle board**) truncates the chain. That one *is*
  caught: with `LK-SER` = B on `left_thumb`, bits 24–31 fill from
  `R-SER-TERM` high, bit 29 reads 1 against a required 0 → marker fails `[calc]`.
- **It spends `J-CHAIN` pin 6 on all four hops.** ADR 0009's two-spares rule and
  the "spares now buy repair" argument `[repo] 0001` fix 1 both assume the loom
  has slack. Pin 6 does nothing in normal operation and everything in the
  self-test, so the honest count is 2 spares plus 1 conductor that is
  load-bearing only for its own test.
- **It makes `IO33` a driven 265 mm line one ground away from `SH/LD`** (pin 4 /
  GND pin 5 / pin 6). Quantified so it is not left hanging: ESP32 edge through
  100 Ω into 26 pF → t_r ≈ 6 ns, dV/dt = 0.55 V/ns; guarded `C_m` ≈ 0.64 pF;
  driven peak = 140 Ω × 0.64 pF × 0.55 V/ns = **49 mV**, 47× margin `[calc]`.
  Safe — but it is the nearest aggressor in the instrument to the one line whose
  blast radius is the whole word, and nobody had costed it.

**Verdict: `LK-SER` is worth fitting** — one schematic for four boards is a real
win and the link is the cheapest way to get it. The *self-test* justification is
the part that breaks. Fit the link for the schematic-unification reason, move
`R-SER-TERM` to the link's common pin, and describe the self-test as what it is:
a localiser for the shift path, adding no detection the marker does not already
have, and covering none of the 24 parallel inputs.

---

## Claim 5 — the asymmetric debounce. **BROKEN.**

Node: `SW1-n` (Gateron KS-33) → `R-KEY-SER` 100 Ω → `U-KEYS` parallel input,
with `R-KEY-PU` 2.2 kΩ and `C-KEY` 47 nF.

### What the network actually rejects

Press: τ = 100 Ω × 47 nF = 4.7 µs, crosses `V_IL` at **5.7 µs**.
Contact-open hold: **71.7 µs** to the real VCC/2 trip, **124.5 µs** to guaranteed
`V_IH` `[calc]`. So the network's entire debounce authority is: *it ignores
contact openings shorter than about 72–125 µs.* That is all it does.

### Real bounce, published

- Ganssle's bench study, 18 switch types × 300 actuations: **average bounce
  1 557 µs, maximum 6 200 µs**; recommends a 20–50 ms debounce period
  `[web]` https://www.eejournal.com/article/ultimate-guide-to-switch-debounce-part-4/
  and https://www.ganssle.com/debouncing-pt2.htm (both blocked by the egress
  proxy; figures via search-result summaries).
- Individual intervals within a bounce train run **"as short as just a few
  microseconds, or as long as 400 microseconds"** `[web]` same search.
- Cherry MX: **< 1 ms** from the Nov-2019 leaf-spring change; the industry
  guarantee that datasheets carry is **≤ 5 ms**
  `[web]` https://www.cherry.de/en-gb/company/news/cherry-blog/article/100-mio
  and https://deskthority.net/wiki/Cherry_MX.
- **Gateron publishes no bounce figure for the KS-33.** The official datasheet
  (`GATERON_KS-33-Low_Profile_2.0_Mechanical_Switch_Set.pdf`, mirrored at
  https://github.com/keyboardio/keyswitch_documentation) downloaded fine but is a
  **scanned image PDF with no text layer** — it lists 1.7 ± 0.5 mm pre-travel,
  3.0 ± 0.2 mm total travel, 60 ± 15 gf, 12.2 mm height, and no electrical
  bounce spec `[web]`. `bom.csv` row `SW1-n` quotes the same four mechanical
  numbers and no bounce figure `[repo]`. **The design has no bounce number for
  the switch it bought.**

### The arithmetic

- 125 µs of hold against a 1 557 µs average train = **1/12**. Against 6 200 µs =
  **1/50**. `[calc]`
- 125 µs of hold against a 400 µs individual open interval = **3.2× too short**.
  A single long interval inside the train fully discharges the hold and presents
  a clean "released" at the register input. `[calc]`
- A 1 557 µs train spans **6.2** scan periods; a 6 200 µs train spans **24.8**.
  `[calc]`
- To debounce in hardware you would need the hold to outlast the train:
  `t = τ·ln(3.3/(3.3−2.31))` → 5 ms needs τ = 4.15 ms → **`R-KEY-PU` = 88 kΩ**
  at 47 nF, or `C-KEY` = 1.9 µF at 2.2 kΩ. For 6.2 ms: 110 kΩ or 2.3 µF.
  `[calc]` Neither is acceptable — 88 kΩ is the opposite direction from ADR
  0001's humidity argument, and 1.9 µF is not an 0805.

**So the 125 µs is not a debounce. It is a 1.54 kHz low-pass that removes the
shortest bounce intervals and passes the rest.** The page calling it "a free
hardware debounce" (`bom.csv` row `R-KEY-SER` still says so `[repo]`) and "the
asymmetric-debounce shape ADR 0001 wants" credits hardware for work that is
entirely done by the unwritten firmware note-off filter.

### Can one fast press be read as multiple presses? Yes. Worked example

`[calc]`, scan at 250 µs, two-sample note-on, hold = 71.7 µs (typical trip):

```
 t=0      first contact closure         input low by 5.7 us
 t=250    scan  -> pressed
 t=500    scan  -> pressed              TWO AGREE -> NOTE ON, full velocity
 t=700    bounce opens for 400 us       node ramps, passes trip at 771 us
 t=750    scan  -> still low (50 us in, node at 3.3(1-e^-50/103) = 1.27 V)
 t=1000   scan  -> RELEASED (300 us in, node at 3.12 V)
 t=1100   contact re-closes             input low by 1106 us
 t=1250   scan  -> pressed
 t=1500   scan  -> pressed              TWO AGREE -> SECOND NOTE ON
```

**A double attack 1 ms apart, from one finger.** The minimum bounce-open needed
is about 400 µs — one sample to see it released plus the 72 µs hold — and that
is the documented upper end of a *single interval* inside a train whose average
length is four times longer. On an instrument where note-on is at full velocity
with no velocity filtering `[repo] 0001` §Key-line signal integrity, a retrigger
is not a soft artefact: it is a second full-amplitude attack. At the 6.2 ms
extreme, several.

Whether this actually happens depends entirely on the firmware note-off filter,
which does not exist yet.

### What settles it, and what to write down

**Measurement (E4/M1, one afternoon):** one KS-33 on a 2.2 kΩ/100 Ω/47 nF
network at 3.3 V, scope on the register input at 1 µs/div, 300 actuations at
playing speed including fast repeated notes, logging (a) total train length, (b)
the longest single open interval, (c) how many intervals exceed 72 µs. (b) is
the number the design needs and does not have.

**The number to write into firmware now, before that measurement:** a note-off
hold of **8–10 ms**, which clears the 6.2 ms published maximum with margin. It
costs note-off latency only, and note-off timing on a wind instrument is far less
critical than attack. Against ADR 0001's 5 ms budget, note-*on* latency is
untouched — the two-sample rule's 250 µs is the only thing on the attack path,
which is what "instant attack, filtered release" was always supposed to mean.
The page's asymmetry is right in principle; the asymmetry is just in the wrong
component, by a factor of fifty.

---

## What to change, in order of what bonds shut first

1. **`left_thumb` marker levels: bit 20 → 0, bit 21 → 1.** Kills all 23 chain
   permutations and the `s = −5` shift hole, verified by exhaustive re-run;
   costs one extra reload point out of 31. Two straps. *(Claim 1 BREAK 1, 3.)*
2. **Put the marker bit map into `config/key-layout.yaml`**, beside `chain:`, and
   generate both from it. ADR 0010 already makes that file the single source of
   truth for the firmware bit mapping; the eight levels are the one part of the
   mapping that is only in prose. *(Root cause of BREAK 1.)*
3. **Move `R-SER-TERM` to the common pin of `LK-SER`**, so the chain-end serial
   input is pulled in both link positions. *(Claim 4; also ADR 0001 fix 6.)*
4. **Add a 100 kΩ pull-up to 3V3 on `SH/LD` at each `U-KEYS`** — four 0805s, one
   per cluster board. Fails an open latch conductor safe rather than into a
   linear-region oscillator. *(Claim 2.)*
5. **Give `U-TVS-CHAIN` and `R-CHAIN-SER` BOM rows** or delete them from
   `carrier.md` §3. They are drawn and not budgeted. *(Claim 2.)*
6. **Measure `di/dt` on the `LED-SIDE` +12 V feed** at a PWM edge. It is the one
   number the `SH/LD` immunity case rests on and it is `[from memory]`.
   *(Claim 2, UNDECIDABLE.)*
7. **Measure KS-33 bounce** — train length and longest single open interval —
   and write a note-off hold of 8–10 ms into firmware in the meantime.
   *(Claim 5.)*
8. **Say in `cluster-boards.md` §4 which 24 positions the marker does not speak
   for**, and that a single wrong key bit is undetectable by design. The page is
   unusually honest everywhere else; this is the one place the list of what is
   caught reads as a list of what is covered. *(Claim 1 BREAK 4.)*
