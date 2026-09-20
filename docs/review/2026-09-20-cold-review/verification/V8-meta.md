# V8 — Meta-falsification of the cold-review register

Target: `docs/review/2026-09-20-cold-review/README.md` (the register) and the
synthesis in it. Not the design. No repository file was modified.

Everything below is cited to `docs/review/2026-09-20-cold-review/<file>:<line>`
(abbreviated to the agent tag, e.g. `B3:99`) or to the design file and line.
Register lines are `REG:<line>`.

---

## 0. The one-paragraph verdict

The register's *findings* are mostly right. Its *epistemology* is not. Three
structural defects run through it:

1. **Convergence is being counted, not tested.** Every high-count finding in the
   register is N readers of one sentence performing the same one-step
   derivation. The register's stated method — "a finding that two blind agents
   reach by *different routes* is evidence" (REG:6) — is never actually applied
   to any of the counts it reports.
2. **The most-converged finding is double-counted.** W4's four "independent
   mechanisms" are two mechanisms, and its two largest rows are the same
   calculation performed by two agents through the same transfer function.
3. **"What the review confirmed as right" contains at least four claims that the
   underlying agent documents explicitly contradict or condition**, including one
   (`0.03 cents` on pitch) that the register's own W3 and W4 falsify two pages
   earlier. Two of the four come from documents whose *conclusion was a failure*,
   with only the confirming sentence lifted out.

And one class of finding was dropped wholesale: **every amplifier-stability
finding in the review**. B9 raised three MAJOR items (findings 5, 6, 7) about
oscillation in circuits that end up inside a bonded body. None appears anywhere
in the register, and one of them (B9's finding 5) had its *conditional good case*
promoted into the confirmations list as an unconditional result.

---

## 1. Are the convergence counts real?

The counts are arithmetically honest — I checked them — but almost none of them
are evidence in the sense the register claims.

### The counts, audited

| Register item | Claimed | Agents I can find | Is the count evidence? |
|---|---|---|---|
| S1 TPS2553 on 12 V | 5 | B5:52, B6:120, C1:61, C4:34, B10:116 | **Echo.** One BOM row + one datasheet number. |
| S2 zero-injection polarity | 4 | B1:356, B2:159, B9:75, C1:461 | **Partly real** (two routes, see below). |
| S3 no bias return | 5 | B2:90, B7:320, B9:145, C2:207, B8 (victim table) | **Echo**, but of a textbook rule — the strongest kind of echo. |
| S5 LM317 | 2 | B5:365, C2:251 | **Real**, and *contradicted* by a third agent (B9:830). Register does not say so. |
| S6 SP3012 | 3 | B6:717, B10:701, C1:129, C2:817 (=4) | **Echo of one remembered number.** See §4. |
| S7 current limits | 5 | A1:339, B5, B6, B10, C2:357 | **Real** — the load tables were rebuilt independently and land 390–650 mA. |
| W1 121 Hz filter | 5 | B1:22, B8, B9:317, C1:526, C2:86 | **Pure echo.** One division: `10k‖15k = 6k`. |
| W4 pitch bend | "4 independent mechanisms" | see below | **Inflated. Two mechanisms, one double-counted.** |
| W5 SPI clock | 5 | A1:134, B4:374, B8, C5:130, B1 | **Echo**, and misdiagnosed (see below). |
| Zone table | 5 | A1:14, A2:101, A3, B1, B6, C5:280 (=6) | **Echo** of the most visible table in the repo. |
| IMU die-temperature | 3 | D1:551, D2:595, D4:936 | **Correct count.** But all three were *assigned* the same gap and the search space has one element. |

### S1 is right and the "5 agents" adds nothing

All five agents read `bom.csv:19` and recalled the same TI product-description
sentence. C4 is explicit that it could not reach ti.com and worked from a search
summary (C4:63–65). B5:12 says the same. Five agents recalling one number is one
datasheet lookup with five witnesses — useful against hallucination, useless as
independent derivation. The register should say "five agents, one source, still
needs the absolute-maximum table read on an unblocked network" — which C4:331
says and the register drops.

### W1 is pure echo, and the register's "exactly" is not exact

R_th = 10 k ‖ 15 k = 6.00 kΩ is one line of arithmetic from `bom.csv:51`. Every
agent who opened the BOM row did it. There is no second route. The finding is
correct (I re-derived: 220 nF → 120.6 Hz; 47 nF → 564.4 Hz, 58.9 dB at 500 kHz).

But the register's claim that 47 nF gives "*exactly* the two numbers ADR 0003
asserts" (REG:182) overstates. ADR 0003:494 says "~600 Hz corner and **58 dB**".
564 Hz is not 600 Hz; it is 6 % low. The transcription hypothesis is *plausible*,
not proven — a 10 kΩ single leg with 26.5 nF also lands at 600 Hz. Nothing turns
on it, but a register that flags "precise-looking numbers that were never
computed" (REG:558) should not manufacture a precise-looking provenance either.

### W4 is the register's headline convergence claim and it is wrong

REG:223–241 presents four rows that "add". They do not.

**Rows 1 and 2 are the same finding.**

- Row 1 ("Offset reference rail + WS2815 ripple (W3), ~22 cents p-p") is B3's
  finding 1 (B3:99–110): the pitch offset trimmer divides the module's +12 V
  node at 0.2083 V/V; a 300 mA square wave across the shared 1N5817's ~0.3 Ω
  dynamic resistance puts ~90 mV p-p on that node → 22.5 cents.
- Row 2 ("A shared 1N5817 … modulates V_f by ~80 mV … ~20 cents") is D3's
  finding 2 (D3:160–170): `ΔVf ≈ 80 mV → 0.67 % of 12 V → 16.7 mV of offset
  error → 20 cents`.

**Same diode, same rail node, same 0.2083 V/V divider, same missing reference.**
D3 and B3 found the same defect; the register split one defect into two rows of a
table and then wrote "and they add". It also presents row 2 as needing "no ground
path at all" as though that made it a distinct mechanism — it is distinct from
rows 3 and 4, not from row 1.

The consequence is not cosmetic: fixing W3 (give the offset a real reference)
deletes rows 1 **and** 2 at once. The register's table implies two fixes are
needed.

**Rows 3 and 4 are real and independent of each other**, and genuinely
convergent: the module's internal ground was found by B4:556 (7.2 cents) and
B5:233 (5.7 cents) by different arithmetic; the rack bus ground by B7:110
(4.8 cents). That is two mechanisms found four times, not four mechanisms.

**Row 3 is also presented at its worst case only.** B5:227 gives 19 cents if the
analog reference is tapped at the etherCON and **7.3 cents if Kelvin'd to the
header**, and the breath-correlated swing is 5.7 cents vs **2.2 cents**. B4:597
gives 7.2 cents for a 10-mil trace and **0.36 cents on a solid pour** — a 20×
spread that B4 explicitly says is the point. The register reports "5.7–7.2 cents"
as if it were the design's value. Both agents' actual finding is *"this is an
unwritten layout decision with a free good answer"*, which is a different and
more actionable statement.

**The agents also disagree about which term is largest**, and the register hides
it: B7:166 says its 4.8-cent term "is the largest in the system and it is the
only dynamic one" — written by an agent who had not seen B3's 22 cents. The
register merges them without noting that one agent's superlative is falsified by
another's number.

### Verdict on §1

- **Evidence (genuinely multi-route):** S7, W4 rows 3+4, S2 (B9 reached the
  polarity from amplifier-topology reasoning, B1 from the sensor's pedestal).
- **Echo (N readers, one source sentence, one derivation step):** S1, S3, W1,
  W5, the zone table, S6.
- **Double-counted:** W4 rows 1+2.
- **Convergence that is an artefact of assignment:** the IMU die-temperature
  register (three "missing-X" agents pointed at the same hole).

Echo is not worthless — it is good protection against a single agent
hallucinating — but the register presents it as corroboration of *reasoning*, and
it is corroboration of *reading*. The two should be labelled differently.

---

## 2. Are the "errors of my own" actually errors?

Nine are listed (REG:455–479). Audit:

### 2.1 The 496.1 kHz buck frequency — **right to confess, wrong about the crime**

ADR 0003:490–494 reads as an *illustrative sequence* ("at 500 kHz … at 498 kHz …
at 496.1 kHz"), which is legitimate rhetoric. `bom.csv:50` is where it becomes a
falsehood: "Without it a **496kHz** buck folds to 100Hz". So it is one BOM
assertion, not two.

More important: **the register confesses the number and never re-runs the
argument.** At the R-78E5.0's real rate the aliasing case is still live —
330 kHz mod 4 kHz = 2.000 kHz, i.e. it folds exactly onto Nyquist and any
load-dependent frequency pull walks it down into the audio band. The register
retires the number as "theatre" and leaves the reader with no replacement figure.

And **the agents' figure disagrees with the register's.** B8:31 lists the buck as
"~500 kHz *(assumed by ADR 0003; unverified)*" and B8:818 puts "R-78E5.0
switching ≈ 500 kHz" under "taken from the project and not independently
checked". No agent verified 330 kHz. The register asserts it flatly. That is the
same defect as the original, in the opposite direction.

### 2.2 "17 usable GPIO, not 16" — **an over-correction that is less safe than the error**

`bom.csv:4` says "16 GPIO broken out (1-7, 34-40, 43, 44)" — the list has exactly
16 entries, so the *stated* count matches its own list. C5:171 is the source.

But the same BOM row and `ROADMAP.md:188` both say **"octal [PSRAM] would eat
GPIO33-37"** and that this is unresolved until E1. GPIO33 is only usable if E1
confirms quad PSRAM. The register records "17" as a flat correction with no
condition, in a document whose whole purpose is to catch unconditional numbers.
The safe restatement is: *17 if quad, 12 if octal, and E1 decides* — which is
what the ROADMAP already says and the correction erases.

### 2.3 `U-DAC` "full orderable P/N required" and "(or A grade)" — **correct, and understated**

Both confirmed at `bom.csv:12`. The A-grade point is right and well sourced:
B4:203 gives the grade table (A/B = reference gain 1, C/D = gain 2; A/C = zero-
scale reset) as **[VERIFIED]** from two sources. An A-grade part halves every
span exactly as the register says.

What the register drops is that this also makes **`ADR 0004:99–107`'s "gain the
scaling stage must supply" table wrong twice over** — once because it assumes
3.6× for a 3.3 V DAC that was never chosen, and once because the 0.25–4.75 V
window (ADR 0006:314) makes the real pitch gain 2.000, not 1.8×. Nobody
reconciles those three numbers.

### 2.4 `U-BREATH` "THT leads" — **right, and the consequence is overstated**

`bom.csv:5` package field says "case 1351-01, dual side ports, THT leads". Case
1351-01 is an 8-lead SOP. So the field is wrong.

"It therefore **cannot be socketed**, which breaks ADR 0003's wear-part plan"
(REG:467) overstates. ADR 0003:642 says "**socketed or otherwise replaceable**".
An SOP on a small daughter-board with pin headers satisfies the ADR as written.
A3 already proposes exactly that as a new BOM row (`SKT-BREATH`, A3:826). The
register turned a solved problem into a broken decision.

The register also misses the more consequential sourcing item on the same row:
**qty is 2 and C4:234 wants 4**, with a reason (the E2 restrictor-sizing work
risks one, a coating accident risks one, M8 re-test needs one), and **spares only
help pre-bond** (C4:36).

### 2.5 The 74HC-vs-LVC note on the keycap row — **mischaracterised as a transcription slip when it is an unresolved reversal**

`bom.csv:3` (`CAP1-n`, keycaps) carries "74HC preferred over LVC for ~2x input
noise margin". `bom.csv:8` (`U-KEYS`) specifies **74LVC165A** and defends it:
"Kept for its native 3V3 spec". Moving the note to the right row does not fix
anything — it produces a part row that argues against its own part.

The register files this as a tooling accident ("my edit matched `"165" in part`").
It is a live contradiction: A1:400 lists it as finding 12 ("The key chain is
74LVC165A and 74HC165"), and C4:34 (#13) adds that TI's stocked 74LVC165A is
TSSOP, not the SOIC-16 the BOM claims, so the part may not be orderable as
written. Three problems on one row, confessed as one formatting slip.

### 2.6 README's two licensing sections — **correct, and the wrong README error was confessed**

`README.md:77–85` and `README.md:108–112` both exist; the second says "Not yet
decided". Real.

But the register omits the README error that the project itself identified as
causally responsible for a bad review finding. `README.md:28` still says *"The
controller is purely digital and carries no analog signal path"* — the exact
sentence that **ADR 0004:25–29** retracts ("That claim was already false when
written and it let a review finding through unchallenged") and that
**ADR 0003:593–596** says must be corrected explicitly. Two agents flagged it
(A1:371, A2:69). It appears **nowhere** in the register.

That is the single clearest framing tell in the document: the harmless duplicate
heading is confessed; the sentence that previously broke a review is not.

### 2.7 `U-REG-DAC` "135 mW" → "34 mW" — **the correction is also wrong, by 2×**

`bom.csv:41` says 135 mW. The register says 34 mW (6.75 V × 5 mA). B5:795 says
69 mW and C1:345 says ~88 mW.

The register forgot the LM317's own set divider. `R-REG-SET` is 240 Ω / 768 Ω
(`bom.csv:42`), so the divider draws 1.25 V / 240 Ω = **5.2 mA** — as much again
as the DAC. Input is ~11.65 V after the 1N5817, so:

```
(11.65 − 5.25) × (5 mA load + 5.2 mA divider) ≈ 65 mW
```

Roughly double the confessed figure. The register corrected a number that was
never computed with another number that was not computed either — inside the
section whose own Pattern 4 (REG:558) names that as the project's failure mode.

### 2.8 R48's decoupling line applied to the wrong part — **right, and much worse than described**

Confirmed: `bom.csv:48` gives the shift registers decoupling; there is no
decoupling row for the MCP3202, the MPXV4006DP, the REF5050, the OPA2197 or the
level shifter. A3:295 (F14) states it as "no decoupling for any controller-side
IC except the shift registers".

"100 mV on VREF is 124 LSB" verifies (3.3 V / 4096 = 806 µV/LSB). But this is not
a decoupling defect — it is an architecture defect, and B6:665 (finding 10) works
it out: the MCP3202's VREF **is** the real-time board's 3.3 V LDO output, on the
board that also carries the 8×8 WS2812C matrix drawing up to 600 mA of PWM'd
current through the same ground pour. 20 mΩ of shared pour = 12 mV = 15 LSB of
*brightness-correlated* noise sitting on the note-gate threshold — a path "you
cannot Kelvin away, because the matrix is on the same board as the LDO".

A capacitor does not fix that. B6's proposal is a dedicated LDO for the ADC,
which directly contradicts ADR 0005:149 ("3.3 V does not need its own
converter"). The register reduced a topology finding to a missing capacitor.

**Related and entirely absent:** the anti-alias RC (`C-AA-ADC`) protects the ADC
*input*. Ripple that arrives on **VREF = VDD** is not attenuated by it at all,
and it aliases by exactly the same mechanism the ADR uses to justify the cap. The
review's own aliasing argument does not cover its own reference.

### 2.9 The "17 % attenuator" — **placement-dependent, and it contradicts its own source**

REG:478 states flatly that the 100 kΩ differential pulldown "**is** silently a
17 % attenuator against the 10 kΩ series resistors in each leg".

- **The agent it came from says 9.1 %, not 17 %.** B2:400 (finding 6):
  `100 k/(100 k + 10 k) = 0.9091`, one leg, "the fixed gain is 2.39, not 2.13".
  The register's 17 % assumes 10 kΩ in **both** legs. Both are defensible (the
  register's own S3 fix demands "series resistance symmetrised"), but the
  register silently doubled an agent's number without saying it had.
- **The placement is unspecified, and it decides the answer.** `bom.csv:35` says
  only "DIFFERENTIAL across BREATH-AGND". Put the 100 kΩ at the connector,
  upstream of the series resistors, and there is **no attenuation at all** — the
  source is a low-impedance buffer and the in-amp inputs are gigaohms. Put it at
  the in-amp pins and you get 9.1 % or 16.7 % depending on leg count. The real
  finding is *"the placement of R-PD-BREATH is unwritten and determines both the
  gain and whether the ADR 0005 unplugged-0 V behaviour survives"*, not a number.
- **The resistors it attenuates against are not in the BOM.** `R-BREATH-IN` is
  one of A3's 34 proposed additions (A3:826). The register is confessing an error
  in a circuit that does not yet have a parts list.
- **And the arithmetic is incomplete anyway.** B9:573 (finding 8) points out that
  once the 0.2 V pedestal is removed the real span is 4.5 V, so 2.13× cannot
  reach 10 V regardless of any pulldown; the required gain is 2.22 clean, ~2.4
  with B2's divider, ~2.67 with the register's. None of this is in the register.

### §2 summary

| Confessed error | Verdict |
|---|---|
| 496 kHz buck | Real, but the replacement number is itself unsourced and the aliasing argument was never re-run |
| 16 → 17 GPIO | **Over-correction.** True only if E1 confirms quad PSRAM; stated unconditionally |
| `U-DAC` P/N + A grade | Correct, understated |
| `U-BREATH` "THT leads" | Correct; "cannot be socketed" is wrong (ADR says "or otherwise replaceable") |
| 74HC/LVC note misplaced | **Mischaracterised.** Not a transcription slip — a live part contradiction plus a package/stock problem |
| Two licensing sections | Correct — and the *load-bearing* README error (`README.md:28`) is omitted |
| "135 mW" → 34 mW | **The correction is wrong.** ~65 mW; the set divider was forgotten |
| R48 decoupling | Correct but **much worse than described**: it is a VREF-architecture problem (B6 f10), not a capacitor |
| "17 % attenuator" | **Over-confident.** Source agent says 9.1 %; placement unspecified; resistors not in the BOM |

---

## 3. Is anything in "What the review confirmed as right" actually wrong?

This is the weakest section of the register and the most dangerous. Six of its
claims are wrong, conditional, or lifted out of documents that concluded the
opposite.

### 3.1 "Nothing the instrument does reaches pitch above 0.03 cents" — **falsified by the register itself**

REG:502. The source is B8:14. B8 derives it **only through the op-amp's supply
pins**: B8:761 computes 62 mV of 2 kHz on the module's +12 V through OPA2197
PSRR ≈ 74 dB → 22 µV → 0.027 cents.

The register carries, thirty lines earlier, W3 and W4 saying that the *same*
62–90 mV on the *same* node reaches pitch through the offset divider at
**0.2083 V/V — no rejection at all — for ~20–22 cents**. B3:120 puts it exactly:
"the design is protecting a node that is 86 dB quieter than the one it left
unspecified."

B8 itself knew: its own headline (B8:17) names "**one DC reference that is never
defined**" as a problem. The register lifted B8's PSRR-path sentence out of a
paragraph whose neighbour says the opposite, and printed it in the section
nobody will re-read.

**A reader of the register who fixes W3 and then trusts "0.03 cents" will
conclude the pitch channel is clean. It is not — rows 3 and 4 of W4 (the two
ground paths) survive W3's fix entirely, at 2–7 cents.**

### 3.2 "~60 µV at the breath jack (−104 dB)" — **one agent, one chain, three remembered numbers**

REG:501. B8:743–752 is the whole basis. The chain is:

```
206 mA @ 2 kHz × 160 mΩ = 33 mV on +12 V
→ REF5050 PSRR ~55 dB @ 2 kHz → 58 µV on the sensor supply
→ ratiometric at 2.5 V out → 29 µV → × 2.13 → 62 µV
```

B8:812 lists **"REF5050 AC PSRR ~55 dB at 2 kHz"** under "from memory, not
verified". B8:818 lists the 0.34 A strip current, the 2 kHz PWM rate and the
2.13× gain as "taken from the project and not independently checked". So the
headline confirmation of the analog architecture rests on one unverified PSRR
figure, one project-supplied current and one gain that B9:573 says is wrong.

It is also **one agent**, presented in a register that everywhere else counts
agents. No second route exists for it.

### 3.3 "The AGND sense return holds at every frequency tried" — **true in steady state, false in the two cases other agents examined**

REG:508. B8's table (B8:730) is DC, LED PWM and WiFi burst — all steady-state,
cable connected, both ends alive. Two other agents found the cases B8 did not run:

- **B2:339 (finding 5):** at hot-plug, AGND can briefly be the instrument's only
  current return. The module end of the analog pair has no series resistance and
  no clamp.
- **B7:320 (F3) / REG's own S3:** unplugged, the same node is not a reference at
  all — the in-amp walks to a rail.
- **B7:743 (F8) / B2:552:** the cable shield, bonded at both ends as the natural
  build does, becomes a *third* parallel power return in parallel with AGND. That
  is not in the register.

"Holds at every frequency tried" is accurate and misleading. The failures are not
at a frequency; they are at a transition.

### 3.4 "The 500 Hz band-limit is the most valuable noise decision" — **true of the intended filter; two agents say the natural build destroys it**

REG:509–511. The arithmetic checks (943 µV × 500/500 000 = 0.94 µV). But:

- **B2:281 (finding 4):** *"a single-ended filter capacitor at the module throws
  away the entire CMRR the in-amp was bought for"* — 14 dB instead of 90.
- **B1:649 (finding 7):** *"The 500 Hz band-limiting capacitor must sit on the far
  side of the 10 kΩ series resistor, and nothing says so."*
- **B8:747** itself: *"My finding 7 is only about **where** the pole sits."*
- **A3:80 (F3):** the capacitors are in prose and **not in the BOM at all**.

So the register confirms as the project's best decision a filter that (a) has no
parts, (b) has no specified placement, and (c) loses its value in the obvious
implementation. All three caveats are in the same documents the confirmation was
taken from.

### 3.5 "An independent thermal model gives 2.89 K/W" — **a confirming sentence lifted from a document whose finding is a failure**

REG:516. B6:100–104 does give 2.89 K/W. B6:601 says so in terms: *"I am not
disputing the coefficient. I am disputing what it is multiplied by."*

B6's actual finding (B6:610–640) is that ADR 0014 compares the lighting increment
against the tolerance instead of adding it to the baseline, so the real interior
rise is **20 K by B6's model, 24 K by ADR 0014's own 3 K/W, and 29 K with the
player's hands over 31 % of the escape path** — against the 9 K the ADR quotes.
Interior reaches 42–51 °C.

Two further B6 findings fall out and appear nowhere in the register:

- **`C-STRIP-BULK` has no temperature or hours grade** (`bom.csv:52`: "470-1000uF
  electrolytic, 16V"). At a 50 °C interior an 85 °C/1000 h part gives
  **≈1.3 years of continuous operation** (B6:632). These are the only wear-out
  parts in a body that cannot be reopened. Specifying 105 °C/2000 h costs nothing
  and gives 90 000 h.
- **16 V electrolytics on a 12 V rail with no overvoltage clamp** (B6:640, B6:738)
  is 75 % derating with no transient margin.

A 1.3-year electrolytic inside a permanently bonded instrument is arguably a
showstopper. It was compressed out of the register into a one-line confirmation
of the coefficient.

### 3.6 "The pitch gain is exactly 2.000 … and the ADR never noticed" — **arithmetic right, attribution wrong, and it is a correction filed as a confirmation**

The arithmetic holds: (4.75 − 0.25) = 4.5 V into 9 V is exactly 2.000, and 2:1 is
a standard matched-quad ratio.

But **ADR 0006:314–317 did notice.** It says the 0.25–4.75 window "achieves the
same benefit as respeccing the output range, **without needing an
exactly-constructible resistor ratio**". The register's "the ADR never noticed"
is false as written.

More seriously, this is **not a confirmation of the design — it is a partial
refutation of the trimmer decision**, filed in the section reserved for things
that verified. ADR 0006:260–272 gives **two** reasons for the trimmer: no offset
authority (`b`), and the 9/5 ratio. Dissolving the second does not touch the
first, and the first is the one ADR 0006 calls decisive. A reader taking REG:517
at face value may drop the trimmer and lose all offset authority — which is also
W3's and W2's fix path.

It also **contradicts the very next bullet** (REG:530, the LT5400 drop), which is
justified *"now that the trimmer sits in the gain ratio"*. The register cannot
simultaneously hold that the ratio is exactly constructible without a trimmer and
that the trimmer dominates the ratio's tempco.

### 3.7 "RSS to ~0.8 cents over 10 K" — **only with a trimmer figure the register elsewhere rejects**

REG:527, from B3:664. I reproduced B3's table (B3:620–637). The critical row:

| Trimmer tempco used | Source | Cents/10 K | RSS of the "worked hardest for" set |
|---|---|---|---|
| 22 ppm/°C | **ADR 0006:282**, the design's own table | 2.4 (B3 says 1.32) | **≈2.5 cents** |
| 4.6 ppm/°C | B3's own recomputation (±5 % on an LT5400 leg) | 0.28 | **≈0.5–0.8 cents** |

B3 lists the ADR's own figure as an italicised alternative it is overriding. The
register quotes the result and not the override. So **"RSS to ~0.8 cents" is a
silent 5× correction of ADR 0006's trimmer table, presented as a confirmation of
it.** Using the ADR's own number the same RSS is ~2.5 cents, which is not
"comfortably inside the 3.5 cents the VCO does by itself" — it is most of it.

### 3.8 "The out-of-loop RC … no cable capacitance can destabilise it" — **the conditional half of a MAJOR finding, promoted to unconditional**

REG:520. The "71 µs" is B3:560. But the stability claim is B9's finding 5
(B9:379), and B9's verdict is the opposite of a confirmation:

> *"the six output reconstruction filters exist in the ADRs and in no BOM line,
> and their placement relative to the 1 kΩ is never stated — **on the wrong side
> of it every output stage oscillates**"* (B9:379)

B9's good case holds **only** with the capacitor on the jack side and feedback at
the op-amp pin. With it on the op-amp side — which B9:441 says "nothing in the
repository says not to" — the mod stages sit at **~0° phase margin** driving 82 nF
against a part rated for 1 nF in unity gain.

The register took B9's conditional, dropped the condition, and put it under
confirmations. Its M1 mentions the same capacitors but only for **dielectric**
(REG:141–143), which is the *less* serious of B9's two problems.

### 3.9 Not wrong, but conditional

- **"The T568B pin mapping is genuinely good work"** (REG:522). B2:510 (finding 9)
  agrees about pin 1 and then says **pin 3 should be `PWR_GND`, not `+12 V`** —
  the (3,6) pair is T568B's split pair with the longest untwisted run in the plug,
  and the register's blanket praise erases a free one-line improvement that costs
  nothing and does not conflict with W8's fix.
- **"The BAV99-over-BAT54S re-derives exactly"** — verified independently
  (B9:826, C2:872). This one is solid.
- **"The dedicated SPI host for the 74x165 chain is the best single piece of work
  in the repository"** — but C5:539 (F13) shows the *consequence* of sharing SPI2
  between the DAC and the MCP3202 breaks the frame watchdog (see §5).

### 3.10 The "resolved" agent-versus-agent conflict is not resolved — it is reversed

REG:485–491 is the register's only listed conflict, and it resolves in the
design's favour. Reading the source (C3:469):

C3 **already knew** the internal-regulation argument. It wrote:

> *"In practice a great many builds drive WS2815 from 5 V logic and work, because
> each pixel regulates 12 V down to an internal 5 V logic rail … But ADR 0014
> already wrote the right rule: **'most' is not a basis for a sealed build.**"*

C3's recommendation was never "fit a 12 V gate driver". It was **"treat 5 V as
plan A and lay out plan B's footprint on the same board"** — two DNP resistors,
free at layout, impossible after bonding.

The register presents C3's own caveat as the refutation of C3, declares "an
ADR 0014 open item closes in the design's favour", and discards the actual
recommendation. This is the clearest instance of the register arguing against an
agent using that agent's own text.

### §3 summary

| Confirmation | Verdict |
|---|---|
| ~60 µV at the breath jack | One agent; rests on an unverified PSRR figure and a gain B9 says is wrong |
| Nothing reaches pitch above 0.03 cents | **Wrong as stated** — falsified by the register's own W3/W4 |
| AGND holds at every frequency | True in steady state; false at hot-plug, unplug, and with a both-ends shield |
| 500 Hz band-limit most valuable | True of the intended filter; no parts, no placement, destroyed by the natural build |
| Pitch gain exactly 2.000, quad-buildable | Arithmetic right; "the ADR never noticed" false; it is a *correction*, not a confirmation; conflicts with the LT5400 bullet |
| Independent thermal model 2.89 K/W | Correct, and **lifted out of a finding that says the rise is 20–29 K, not 9 K**, discarding a 1.3-year electrolytic |
| Precision terms RSS to ~0.8 cents | **Only with a trimmer figure 5× below ADR 0006's own**; with the ADR's number it is ~2.5 cents |
| Out-of-loop RC unconditionally stable | **Conditional half of a MAJOR oscillation finding**, promoted to unconditional |

---

## 4. Are the severity assignments right?

### Filed as showstopper, is not

**S6 (`U-TVS-UMB`).** Both agents who examined the mechanism rated it **MINOR**
(B6:715, B10:737). C1:131 rated it High and datasheet-verified. The register
marks it **[agent]** — i.e. unverified in the main session — and then states
"V_RWM 5.0 V" as bare fact, when B6:731 flags it as `[memory, not verified]`,
B10:1674 lists it among "the three to check first", and B6:752 says *"if it
happens to be a 12 V-rated array, the +12 V line is covered"*.

And the part is not decided by anything: A3:599 notes it is **"NOT SPECIFIED BY
ANY ADR — added in the BOM only … needs an ADR paragraph or a deletion"**, and
C4:34 says it is discontinued and in the wrong package anyway. A showstopper that
resolves by deleting a row nobody decided to add, on a number nobody verified, is
not a showstopper.

### Filed below showstopper, should stop the build

1. **W14 — key switches have no pull-ups.** A 74x165 parallel input with an open
   switch and no pull-up has **no defined logic level**. This is not a noise
   margin issue; the key scanner does not function as specified. It sits under
   "Major — things that are wrong", below a TVS array. It also gates the cluster
   boards and the loom, which M3/M5 lock — earlier than the bond.

2. **B9 findings 5, 6 and 7 — oscillation, three MAJORs, entirely absent.**
   - **f5** (B9:379): reconstruction capacitors on the op-amp side of the 1 kΩ →
     ~0° phase margin on four mod channels.
   - **f6** (B9:450): the REF5050→OPA2197 follower drives the MPXV4006DP's **supply
     pin**, which by the BOM's own rule takes 100 nF. A unity-gain OPA2197 into
     100 nF against a part rated for 1 nF is an oscillator. It is on a
     **ratiometric** supply (so it multiplies straight into the breath scale
     factor), it shares a package and a supply pin with the breath buffer, and it
     lives **400 mm inside a body that cannot be reopened**. Fix is one 10 Ω
     resistor, free now, impossible later.
   - **f7** (B9:511): no compensation capacitors anywhere, at unspecified feedback
     resistor values.

   A register that identifies "unobservable things belong in the module, never in
   the instrument" (REG:439) dropped the one finding that puts a marginal control
   loop in the instrument.

3. **`C-STRIP-BULK` grade (B6:632).** ~1.3 years of continuous operation for an
   85 °C/1000 h part at a 50 °C interior, in two permanently entombed capacitors.
   Absent from the register.

4. **C5 F13 (C5:539) — the frame watchdog can be masked.** The DAC and the
   MCP3202 share SPI2, so `SCLK` and `MOSI` run down the umbilical on **every ADC
   read at 4 kHz**. Retrigger the 74HC123 from `SCLK` — the obvious build — and a
   firmware fault that stops updating the DAC while breath sampling continues
   **retriggers the watchdog forever**. The register makes S4 a showstopper for a
   *side effect* of the watchdog firing, and omits the finding that says it may
   never fire. Fix: retrigger from the DAC's `CS` only. One line on a schematic
   that does not exist yet.

5. **C1 F5 Problem 1 (C1:300) — a clamp event on every power-on.** The module's
   74AHCT125 runs from bus +5 V while the DAC's AVDD comes up behind a Schottky
   and the LM317's soft-start. For milliseconds the buffer drives ~5 V into DAC
   inputs whose supply is near zero; ~100 mA into a ±20 mA clamp, **every time
   the rack is switched on**. The design already fits `R-OPAMP-IN` for exactly
   this hazard on the analog side (ADR 0006:410) and fits nothing on the digital
   side. Absent from the register.

6. **C4's entombment list (C4:33–40).** `U-MCU-RT`, `U-DISP` and `U-BREATH` are
   single-source consumer parts, silently revised, that get bonded into the body.
   C4's action — *buy two of each, same order, same batch, and recognise spares
   only help pre-bond* — has a hard deadline at M6 and appears nowhere in the
   register.

### Where the register's severities are right

S1, S5, S7, W2, W3, W13 and W14 (modulo the filing) are correctly reasoned, and
S7's "the polyfuse is downstream of the load switch, so the load switch does not
break the runaway loop ADR 0014 believes it deleted" is the sharpest single
sentence in the register.

### One severity the register got right and then under-argued

**S7's "the limiter may prevent boot" has an unacknowledged agent conflict.**
B5:281 (finding 4) says a 500 mA limit "cannot start the load at all" and
predicts motorboating. B10:927–938 says *"the TPS2553 does not re-ramp on
hot-plug, it current-limits. **This is exactly what the load switch is for and it
works.**"* The register adopts B5 and never mentions B10. Given that S7 is one of
the three items in the "first block", that omission matters.

**And the register introduced its own uncomputed number here.** S7 and W13 both
cite an **8 V** buck UVLO. B6:407 says 8 V `[verified — R-78E-1.0 input range is
8–28 V]`; **B5:314 says 7 V `(datasheet-verified)`**; **ADR 0005:214 says "a buck
that needs more than 6 V in"**. Three figures, two marked verified, and the
register picked one silently — in an item it marks `[verified]`. W13's brown-out
window is 2.8 V wide (8.0 → 5.2 V, the REF5050's real dropout per B6:409), not
the 0.8 V the register's "~7.2 V" implies; the register transcribed a scenario
voltage from B6:408 as if it were a limit, and thereby *understated* a hazard it
was reporting.

---

## 5. What did twenty-three agents all miss?

The register is right that subsystem assignment cannot see composition. It is
right about the mechanism and wrong that nothing else fell through. Specific gaps
in the review's own coverage:

### 5.1 Nobody re-summed the 250 µs loop with the accepted fixes in it

C5:677 is the only first-principles loop budget, and it closes at 161 µs (64 %)
**at 2 MHz with five jack channels**. Its own sensitivity table (C5:712) says:

> *"Two internal DAC channels (ambient zero, mod offset) added every loop:
> +38 µs → 199 µs, 80 % — **closes, but don't.** Update them at ~10 Hz."*

The register's S4 fix is *"refresh the offset every pass"*, and its structural
rule (REG:441) is *"with no readback, refresh **everything**, every pass"* —
which, taken literally, adds the reference-enable and clear-code registers on top.
**The register's headline structural rule is the thing the only agent who costed
it says not to do**, and the register cites the latency budget's six-word booking
as though the fix were free. It is affordable; it is not free, and nobody added it
up with W5's clock, C5's IMU cadence and the frame-watchdog refresh together.

Related, and also missed by the register: **C1:1123 and C5:380 both find the IMU
read does not fit** (315–342 µs against a 250 µs period). C5's sensitivity table
calls it "201 % — fails catastrophically". Neither the register nor the latency
budget has a row for it.

### 5.2 The op-amp inventory was never taken

`bom.csv:13` buys five OPA2197 (ten halves) for the module plus one
(`U-BUF`, two halves) for the instrument. B9:34 is the only document that counts
them, and B9:637 (finding 10) finds the breath knob chain "consumes the last spare
amplifier half" — while B3:126 and D3:190 both propose a **buffered 2.5 V
reference** using "the spare OPA2197 half", and B4/B9 propose a follower for the
mod offset. **Three register-endorsed fixes each claim the same spare half.**
Nothing in the register notices, and it is exactly the composition failure
Pattern 3 names.

### 5.3 Nobody asked what the accepted fixes do to each other

The register's Pattern 3 is about the *design's* fixes composing badly. It never
applies the test to its own register. At minimum:

- **W3's fix (offset from the DAC's VREFOUT) breaks ADR 0006's power-on table.**
  B3:141 says so explicitly: the internal reference is disabled at reset, so
  pitch parks at **0 V — an audible note — not subsonic**. The register carries
  W3 and the power-on table and never connects them.
- **W2's fix ("±600 cents of firmware offset authority") spends headroom reserved
  for something else.** The 0.25 V of DAC margin exists because "the DAC8568 at
  AVDD = 5 V cannot reliably swing to its own supply" (ADR 0006:314) and because
  ADR 0004:131 warns the top calibration point must not land in the nonlinear
  region. Shifting codes to implement `b` consumes exactly that margin. The
  register calls the resolution "better than the original" (REG:203).
- **S3's fix (1 MΩ to AGND on each input) interacts with the pulldown value.**
  B2:426 proposes deleting the 100 kΩ in favour of the 2 × 1 MΩ pair. The register
  keeps both, which changes the attenuator it confesses in §2.9 and the unplugged
  behaviour ADR 0005:213 requires.
- **The register's own "delete the polyfuse" (S7) and "add protection at the
  module end" (S6) and W8's "shunt SS34 in the footprint the polyfuse vacates"
  all land on the same node** and were never drawn as one circuit.

### 5.4 Whole-system questions nobody was assigned

- **A commissioning-to-bond sequence.** The register names M3 as the real
  deadline (REG:416) and then lists S1/S7/zone-table as the first block
  (REG:573) — which are E-track items. There is no single ordered list of "what
  must be true before the plate is cut / before the body closes", and the
  constraints are scattered across ROADMAP ordering rules, C4's procurement
  deadlines, C3's pre-cut measurements and D5's M3 gates.
- **What the *instrument* does when the module is absent or off.** Covered
  piecemeal (ADR 0004:277, C2:610, B7:810) and never as one state table.
- **Rework and failure recovery after bonding.** C5 F1/F2 (neither board can be
  forced into bootloader mode; the display board has no external access) and
  C4:36 ("spares only help pre-bond") are the same problem; the register splits
  them across W10 and drops C4 entirely.
- **Nobody costed the review's own fixes.** No agent, and not the register, adds
  up parts, board area or pin count for the accepted changes.
- **Nobody attacked the 0–6 kPa range choice** except B1:846, which observes that
  a closed tube presents an adult's full occlusion pressure (15–20 kPa) to a 6 kPa
  part and that the range "is asserted rather than measured". Register-absent.
- **Nobody attacked the PTFE plug's dual role.** B1:556 finds the two jobs fight:
  *succeeding as a water barrier changes its flow resistance*, so the breath
  attack time drifts with wetting. The register discusses the restrictor in W7
  and omits this. ADR 0003:638 celebrates the dual role as a saving.

### 5.5 Things the register drops that agents did find

Listed because "twenty-three agents missed it" and "the register dropped it" are
different failures and the second is larger here:

| Finding | Source | Register |
|---|---|---|
| Three amplifier-stability MAJORs | B9:379, B9:450, B9:511 | absent |
| Watchdog masked by ADC traffic on shared SPI2 | C5:539 | absent |
| Clamp event into the DAC on every rack power-on | C1:300 | absent |
| MCP3202 VREF = matrix-modulated dev-board LDO | B6:665 | reduced to "a decoupling cap" |
| Electrolytic grade → ~1.3 years | B6:632 | absent |
| 16 V caps on 12 V, no clamp | B6:640 | absent |
| Pin 3 should be PWR_GND | B2:510 | contradicted by a confirmation |
| Single-ended 500 Hz cap → 14 dB CMRR | B2:281 | absent |
| Shield bonded both ends = third power return | B7:743, B2:552 | absent |
| `README.md:28` "purely digital" | A1:371, A2:69 | absent |
| etherCON flange is 26 mm, not the 23.8 mm bore → 2.09 mm of panel | C3:95 | absent |
| WS2815 plan-B footprint | C3:469 | **reversed** |
| ADR 0004's "+5 V reversal kills the buffer and nothing else" is false | B5:460 | absent |
| `L-BUCK-IN` LC resonance lands on the 2 kHz aggressor | C2:464 | absent |
| `R-OUT-PROT` over its power rating in the fault it exists for | C2:319 | absent |
| `R-SPI-PULL` backfeeds the instrument through an ESD diode when off | C2:610 | absent |
| IMU read does not fit the loop | C1:1123, C5:380 | absent |
| Flash-cache / PSRAM / fingering-LUT determinism rules | C5:569 | absent |
| Strap hardware — highest-stress point, no part number | C3:816 | absent |
| Entombed dev boards, buy-two-same-batch, pre-bond only | C4:33–40 | absent |
| D5 findings 6–13 (tuning ritual, gate/retrigger, register changes at M3, embouchure axis) | D5:30 | absent |

---

## 6. Is the register's framing distorting anything?

Yes, in both directions, and the directions are not symmetric: the register is
**penitent about cosmetics and protective about architecture**.

### 6.1 Penitence is spent on cheap items

The "errors of my own" list is dominated by things that cost nothing to admit: a
duplicate heading, a note on the wrong row, a power figure, a frequency used
rhetorically. The two README errors are instructive: the harmless duplicate
licence section is confessed; **`README.md:28`, the sentence that ADR 0004 says
"let a review finding through unchallenged", is not** — even though two agents
flagged it (A1:371, A2:69).

The same pattern in the B6 thermal material: the *confirmation* (2.89 K/W) is
quoted; the *finding* (20–29 K rise, a 1.3-year electrolytic, no overvoltage
clamp) is not. And in B9: nothing from it survives except a promoted conditional.

### 6.2 The one conflict resolution goes the design's way, using the agent's own caveat

Covered in §3.10. The register's "Agent-versus-agent conflicts" section contains
exactly one entry, resolved in the design's favour. At least four other conflicts
exist and are not listed:

- **LM317 tolerance:** B9:830 *confirms* the ±4 % figure S5 destroys.
- **Buck UVLO:** B5:314 says 7 V verified, B6:407 says 8 V verified.
- **Inrush:** B5:281 says a 500 mA limit cannot start the load; B10:938 says the
  load switch "works".
- **Largest pitch term:** B7:166 claims its 4.8 cents is "the largest in the
  system"; B3:622 has 22.5 cents.

A section that exists to surface disagreement and contains one entry, resolved
favourably, is doing the opposite of its stated job.

### 6.3 Over-correction: a fix adopted because it sounds rigorous

**The LT5400 drop (REG:530).** The register endorses replacing a matched network
with "two 0.1 % / 10 ppm thin-film 0805s" that "do better". They do not:

- Two independent 10 ppm/°C parts give **√2 × 10 = 14.1 ppm/°C of *ratio* drift**
  (C1:1148 says this itself), which over 10 K on a 9 V span is **≈1.5 cents**.
- The LT5400's 1 ppm/°C *tracking* gives **0.11 cents** — 14× better.
- ADR 0006:230–232 is explicit and correct: *"what matters is not each resistor's
  absolute tempco but how well the two track each other — and two discrete parts
  do not track at all."* B8:772 calls that "the best piece of analysis in the
  repository".

So the register accepts a substitution that reverses the one analysis it
separately calls the design's best, by quoting **absolute** tolerance figures at
an argument about **tracking**. It is defensible only if the trimmer really does
contribute 2.4 cents — and the register's *other* endorsement (§3.7, the 0.8-cent
RSS) requires the trimmer to contribute 0.28 cents, in which case the two
discretes at ~1.5 cents become the **dominant term in the whole budget**, 5× the
trimmer and ~half the VCO.

**The register holds both numbers, eight lines apart, and the fix it adopts is
only safe under the one it elsewhere rejects.**

The same over-correction reaches the confirmations: "the pitch gain is exactly
2.000 … so the objection that drove the trimmer decision is dissolved"
(REG:517–519) reads as permission to remove the trimmer, which would remove the
offset authority ADR 0006 calls the primary reason for it *and* the authority W3
and W2 both depend on.

### 6.4 Other framing effects

- **"Four independent mechanisms" and "the most-converged finding in the review"**
  (REG:224) — the register's rhetoric is strongest exactly where its evidence is
  weakest (§1).
- **Pessimising on layout-dependent numbers.** W4 row 3 reports 5.7–7.2 cents when
  both sources give 0.36–2.2 cents for the good layout, and both say the point is
  that the decision is unwritten. Accepting the worse number is penitent and
  unhelpful: it obscures that the fix is a routing rule, not a part.
- **"34 further line items"** (REG:158) double-counts: M1 (`C-FILT-PITCH`/
  `C-FILT-SLOW`), M2 (`R-MODGAIN`) and M3 (`R-INAGAIN`) are all inside A3's 34
  (A3:826). It is 34 total, of which three are already register items.
- **"~19,500 lines"** (REG:9) — the twenty-three agent documents are 22 169 lines.
  A small thing, but it is an uncomputed number in a register whose Pattern 4
  warns about exactly that.
- **The first block (REG:573) contradicts the register's own deadline finding.**
  REG:416 says "the deadline is earlier than the rest of this register assumes:
  **M3, layout lock**", then the closing section names S1, S7 and the zone table —
  two E-track items and one geometry item. W14 (key pull-ups), D5's #5 and #9
  (spare keys and register changes), C3's pre-cut measurements and C4's
  buy-before-bond list are the M3-gated block, and none of them is named.
- **One thing the framing gets right and deserves saying:** the register does not
  soften S1, S5, S7, W2, W3 or W13, all of which are directly critical of
  decisions the author defended at length. The defensiveness is not in what it
  admits — it is in the confirmations section and the conflicts section.

---

## 7. The shortest list of things to change in the register

1. **Delete or merge W4 rows 1 and 2**, and restate W4 as *two* mechanisms (an
   unreferenced offset divider; shared ground impedance), with row 3 given as
   "0.36–7.2 cents, set by a layout decision nobody has written down".
2. **Strike "nothing the instrument does reaches pitch above 0.03 cents"** or
   scope it to "through the op-amp supply pins, once the offset reference is
   fixed; the two ground paths survive at 2–7 cents".
3. **Add a stability section** carrying B9 findings 5, 6 and 7. B9 f6 (follower
   into the sensor's decoupling capacitor) is a one-resistor fix inside a body
   that cannot be reopened and should be in the first block.
4. **Add C5 F13** (watchdog retriggered by ADC traffic) next to S4 — the watchdog
   that may never fire outranks the watchdog's side effect.
5. **Re-price the RSS and the LT5400 bullet against one trimmer figure.** Pick
   4.6 or 22 ppm/°C, state which, and note that the LT5400 substitution flips
   verdict between them.
6. **Add B6's thermal finding** (20–29 K, electrolytic grade, 16 V derating) and
   demote the 2.89 K/W bullet to a sub-clause of it.
7. **Restore C3's WS2815 plan-B footprint** and re-open the ADR 0014 item; the
   agent's own caveat is not a refutation of the agent.
8. **Add `README.md:28`** to the errors-of-my-own list, above the duplicate
   licence section.
9. **Correct 34 mW to ~65 mW**, make "17 GPIO" conditional on E1, and mark the
   buck's UVLO and switching frequency as unresolved between agents.
10. **Recompute the loop** with W5's clock, S4's refresh, the stateless rule, the
    IMU cadence and the watchdog refresh all applied at once, and add the result
    to the latency budget. C5:712 is the only place this has been costed and it
    says "closes, but don't".
