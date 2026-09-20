# A3 — BOM ↔ ADR consistency audit

**Scope.** `hardware/bom.csv` (62 data rows, header + rows 2–63) reconciled against all
14 ADRs in `docs/decisions/`, in both directions.

**Headline numbers.**

| Measure | Count |
|---|---|
| BOM rows examined | 62 |
| ADRs examined | 14 (0010, 0011, 0012 specify no hardware) |
| Rows whose `adr` citation is wrong or too weak | 4 |
| Rows with a demonstrably wrong quantity | 6 |
| Rows that are un-orderable as written (two parts in one row, `TBD`/non-numeric qty, no full P/N) | 5 |
| Rows proposed for addition (parts named or directly implied by an ADR, absent from the BOM) | 34 |
| Package-policy violations found | 0 confirmed, 2 unverifiable as written |
| Status values outside the implied vocabulary | 1 (`available`) |
| Rows whose status understates a decision already Accepted | 10 |

**The single biggest class of defect is direction 2: the BOM carries the ICs and forgets
the circuits around them.** Thirty-four rows are proposed below, for parts an ADR states
in prose and the BOM does not carry: the in-amp gain resistor, the breath protection
resistors, the band-limit caps, the reconstruction-filter caps, the mod-channel gain
network, the watchdog timing pair, the load-switch ILIM resistor, the OE-gating network,
the panel LED, every PCB in the project, and the entire mechanical fastening set. The
board-level ones are exactly what makes a fabbed board
unbuildable at stuffing time; the mechanical ones are what makes an 18-inch laminated
stack un-closable.

---

## A. Parts specified by an ADR and missing from the BOM

### F1. **The instrumentation amplifier has no gain-setting resistor, and the value depends on an unresolved part choice.**

Severity: **Critical** (the breath channel has no defined gain without it).

BOM row 28:

```
U-DIFFRX,module,INA821 or INA828,TI,"Instrumentation amp - breath receiver, senses against AGND",SOIC-8 (1.27mm pitch),1,candidate,,0003,Buffered GOhm inputs make source impedance irrelevant. Absorbs the ~2.13x gain stage. REF pin takes the ambient-zero injection
```

ADR 0003: "it **absorbs the ~2.13× scaling stage** so net part count is flat or lower".

An INA821/INA828 sets its gain with one external resistor and is a unity-gain follower
without one. The row claims a 2.13× stage and provides no resistor for it. Worse, the
required value differs between the two candidates — INA821 is `G = 1 + 49.4k/R_G`
(R_G ≈ 43.7 kΩ for 2.13×), INA828 is `G = 1 + 50k/R_G` (R_G ≈ 44.2 kΩ) — so the
unresolved "INA821 or INA828" propagates into a resistor that cannot be ordered until
the IC is chosen. This is also a precision resistor: it is in the gain of a DC-accurate
0–10 V output, so it wants 0.1 % / 25 ppm, not 1 %.

Add (after choosing INA821):

```
R-INAGAIN,module,43.7k 0.1% 25ppm metal film,,Gain-set resistor for U-DIFFRX - sets the ~2.13x breath scaling,0805 (2.0 x 1.25mm),1,open,,0003,"INA821: G = 1 + 49.4k/RG. INA828 would need 44.2k - value is not portable between the two candidates, so U-DIFFRX must be resolved first"
```

### F2. **The breath link's protection resistors are absent, at both ends.**

Severity: **High**.

ADR 0003: "the instrument end needs **only a buffer** — an op-amp follower, band-limited,
with a series resistor for protection"; and "gigaohm inputs make source impedance
irrelevant, so **protection resistors can be 10 kΩ and unmatched** with no CMRR penalty."

The BOM carries the buffer (`U-BUF`), the receiver (`U-DIFFRX`) and the pulldown
(`R-PD-BREATH`), but no series resistors. Three are implied: one at the instrument
buffer output, two at the in-amp inputs (BREATH and AGND legs). Without them the
fault-tolerance argument that ADR 0003 spends two pages constructing is not built.

Add:

```
R-BREATH-SER,controller,10k 1% metal film,,Series protection on the breath buffer output into the umbilical,0805 (2.0 x 1.25mm),1,candidate,,0003,"+12V-rail buffer means no clamp current, so the value is free to be what the 500Hz band-limit wants"
R-BREATH-IN,module,10k 1% metal film,,Series protection at the in-amp inputs - BREATH and AGND legs,0805 (2.0 x 1.25mm),2,candidate,,0003,"Unmatched is fine - the in-amp's GOhm inputs remove the source-impedance/CMRR coupling that would have capped a difference amp at ~24dB"
```

### F3. **"Band-limit at both ends, around 500 Hz" has no capacitors in the BOM.**

Severity: **High**.

ADR 0003: "**Band-limit at both ends, around 500 Hz.** The sensor only has ~159 Hz of
real bandwidth, so a narrow channel costs nothing and rejects almost everything that
could couple in — SPI edges, LED PWM, WiFi bursts and switching-supply hash all live far
above it."

The BOM has `C-AA-ADC` (the ADC branch anti-alias cap) and nothing for the umbilical
branch. This is the filter that makes the 2 m analog run survivable, and it is the
cheapest part in the chain. With the 10 kΩ series resistors of F2, 33 nF gives 482 Hz.

Add:

```
C-BREATH-BL,controller,33nF C0G/NP0 50V,,500Hz band-limit at the breath buffer output,0805 (2.0 x 1.25mm),1,candidate,,0003,"10k x 33nF = 482Hz. C0G not X7R - X7R's voltage coefficient is a distortion term in a DC-accurate path"
C-BREATH-BLRX,module,33nF C0G/NP0 50V,,500Hz band-limit at the in-amp inputs - differential across BREATH-AGND,0805 (2.0 x 1.25mm),1,candidate,,0003,"Differential, matching R-PD-BREATH's placement. Two smaller common-mode caps would need matching to avoid converting CM to DM"
```

### F4. **None of the six CV outputs has a reconstruction-filter capacitor.**

Severity: **High**.

ADR 0006 specifies three distinct corners — "Corner it around 10–20 kHz" for pitch,
"~2 kHz" for breath, "**Mod 1–4** get a uniform **~2 kHz** filter" — and the consequence
section fixes the topology: "**The pitch output filter stays an ordinary series RC.**
With no in-loop compensation capacitor, the filter's corner is set by its own R and C and
nothing else."

`R-OUT-PROT` (1 kΩ × 6) is the R of those RCs. The C does not exist anywhere in the BOM.
Without it the DAC's zero-order-hold image reaches the jacks unattenuated, which is the
exact failure ADR 0006 quantifies at −19.2 dB.

Add:

```
C-FILT-PITCH,module,10nF C0G/NP0,,Reconstruction filter cap on the pitch output,0805 (2.0 x 1.25mm),1,candidate,,0006,"1k x 10nF = 15.9kHz, inside ADR 0006's 10-20kHz window. Fast so note changes land instantly"
C-FILT-SLOW,module,82nF C0G/NP0,,Reconstruction filter cap on breath and mod 1-4 outputs,0805 (2.0 x 1.25mm),5,candidate,,0006,"1k x 82nF = 1.94kHz. Puts real attenuation on the 3.6kHz ZOH image that a 15kHz corner ignores"
```

### F5. **The mod channels' gain-of-4 resistors do not exist in the BOM, and ADR 0006 contradicts itself about what they should be.**

Severity: **High**.

ADR 0006, mod-channel topology: "**Gain of 4 is a 1:4 ratio**, which the LT5400 family
offers directly — no external resistor, so no absolute tempco leaks into the gain."

ADR 0006, calibration section: "Channels 2–6 run on ordinary 1% discretes; nobody's ear
cares whether a modulation CV moves a few cents' equivalent with temperature."

These cannot both be built. `Vout = 4 × (Vdac − 2.5 V)` is a difference amplifier and
needs four resistors per channel — 16 discretes for mod 1–4, or four more matched
networks. The BOM carries **neither**: `R-PRECISION` is a single `TBD`-quantity row
scoped to "pitch scaling", and there is no discrete-resistor row for the module's gain
network at all. The pitch stage's own fixed resistors (the ones the trimmer trims
*around* — "Small trim range around a fixed precision resistor") are likewise absent.

Resolve in favour of the cheaper reading (discretes on 2–6), which is what the
calibration section concludes and what "the precision parts concentrate on channel 1"
means, and add:

```
R-MODGAIN,module,10k / 40k 1% 25ppm metal film,,Difference-amp network for each mod channel - Vout = 4 x (Vdac - 2.5V),0805 (2.0 x 1.25mm),16,candidate,,0006,"4 per channel x 4 channels. ADR 0006 is self-contradictory here - the topology section offers an LT5400 1:4, the calibration section says ordinary 1% discretes on channels 2-6. Taking the latter; if the former is wanted this becomes 4 x LT5400 and this row is deleted"
```

### F6. **The watchdog monostable has no timing resistor or capacitor.**

Severity: **High** (the part does nothing without them).

BOM row 59:

```
U-WATCHDOG,module,74HC123 or equivalent retriggerable monostable,,Frame watchdog: asserts DAC CLR when SPI traffic stops,SOIC-16 (1.27mm pitch),1,candidate,,0004,A stuck CV drones the rack forever and nothing notices...
```

ADR 0004: "**Assert `CLR` at the module when no valid frame has arrived for N
milliseconds.** … Size N so a busy loop cannot trip it but a hang is caught in well under
a second."

A 74HC123's pulse width is `t ≈ 0.45 · R_ext · C_ext`. N is the whole specification of
this part and there is nothing in the BOM that sets it. A pull-up on the DAC's active-low
`CLR` is also implied and missing.

Add:

```
R-WDT,module,1M 1% metal film,,74HC123 timing resistor - sets the frame timeout,0805 (2.0 x 1.25mm),1,candidate,,0004,"t = 0.45 x R x C. 1M with 220nF is ~99ms - well under a second, far above a 250us loop period"
C-WDT,module,220nF X7R,,74HC123 timing capacitor,0805 (2.0 x 1.25mm),1,candidate,,0004,Pairs with R-WDT for a ~99ms frame timeout
R-CLR-PU,module,10k 1%,,Pull-up on the DAC8568 CLR line,0805 (2.0 x 1.25mm),1,candidate,,0004,"Active-low CLR must not float while the monostable is being retriggered"
```

### F7. **The current-limited load switch has no ILIM resistor.**

Severity: **High**.

BOM row 19 notes: "Adjustable limit set ~500mA." ADR 0005: "the load switch's current
limit is set from that measurement" (E6).

A TPS2553DBV sets its limit with one resistor from ILIM to GND. It is the one component
that makes the row's own note true, and it is not in the BOM. A FAULT pull-up is also
required if the flag is used.

Add:

```
R-ILIM,module,1% metal film - value set at E6,,Current-limit programming resistor for U-LOADSW,0805 (2.0 x 1.25mm),1,open,,0005,"TPS2553 ILIM to GND. Value deliberately open - ADR 0004 says the instrument current figure is the least trustworthy number in the project and E6 measures it with a current probe"
```

### F8. **The level shifter's output-enable gating network is missing.**

Severity: **High**.

ADR 0004: "**Gate the 74AHCT125's output enable from umbilical +12 V presence**, so
'instrument absent' is a state the hardware knows about rather than one it stumbles into."
The same paragraph calls this the reason the power switch had to move to the module — it
is load-bearing for ADR 0005's whole switching architecture.

The BOM has `U-LVL-MOD` and `R-SPI-PULL`, and nothing that senses +12 V presence. A
divider plus clamp is the minimum; the AHCT125's four OE pins are active-low and must be
driven, not left floating.

Add:

```
R-OEGATE,module,100k / 47k 1%,,Divider sensing umbilical +12V presence to drive the 74AHCT125 OE pins,0805 (2.0 x 1.25mm),2,candidate,,0004,"12V x 47/147 = 3.84V - a valid AHCT high off the 5V rail; 0V when the load switch is off. Gates all four OE pins together"
D-OEGATE,module,BAT54 or BAV99,,Clamp on the OE divider node to the 5V rail,SOT-23,1,candidate,,0004,Bounds the divider node if the 5V rail is absent while +12V is present
```

### F9. **The USB/umbilical power-OR diode is specified in ADR 0005 and absent.**

Severity: **Medium**.

ADR 0005: "**OR the umbilical power with USB power** — it costs a diode, and it means the
instrument runs on the bench during development without a rack attached. That is worth a
diode."

Milestone E5 (USB MIDI bring-up before any analog hardware exists) depends on it. No row.

```
D-USBOR,controller,1N5817 or SS14,,ORs USB VBUS with the umbilical-derived 5V rail for bench use,DO-41 THROUGH-HOLE,2,candidate,,0005,"One diode per source into the shared 5V node. Bench-only affordance - explicitly not a standalone mode (ADR 0005)"
```

### F10. **No PCB appears anywhere in the BOM — not the carrier, not the cluster boards, not the module.**

Severity: **High**.

ADR 0013: "**Instead: keep both dev boards as modules, on a carrier that has no MCU on it
at all.** The carrier holds only: Headers the dev boards plug into, 74LVC165 shift
registers, MCP3202 ADC, REF5050 … Passives."
ADR 0001: "one register per cluster … makes every satellite board identical".
ADR 0004: "**Brace the connector to the module PCB** … Free on a board being designed
anyway".
ADR 0014: "**The carrier needs a ~22 mm cutout** under the board".

Four distinct fabricated boards are specified across the ADRs and none has a row. The
carrier's 22 mm matrix cutout in particular is called "impossible to add later".

```
PCB-CARRIER,controller,2-layer PCB - real-time carrier,,Passive carrier: dev board headers, 165 chain, ADC, ref, buffers, level shifter, power entry,"~100 x 45mm, 1.6mm",1,open,,0013,"Must carry the ~22mm cutout under the 8x8 matrix (ADR 0014) and the umbilical backing-plate mounting. Nothing on it is fast or RF - 2 layers, hand-assembled"
PCB-CLUSTER,controller,2-layer PCB - key cluster board,,Identical satellite board: one 74LVC165 + switches + decoupling,"small, 1.6mm",4,open,,0001,"One per cluster - left hand, left thumb, right hand, right thumb. Identical by design so the 14 spare chain bits are free expansion"
PCB-MODULE,module,2-layer PCB - 6HP CV interface,,DAC, scaling, jacks, power entry, watchdog,"~28 x 110mm, 1.6mm",1,open,,0004,"Must brace the etherCON mechanically - the 23.8mm hole leaves 3.19mm of panel each side"
```

### F11. **The dev boards have nowhere to plug in: no headers or sockets in the BOM.**

Severity: **High**.

ADR 0013 lists "Headers the dev boards plug into" as the *first* item the carrier holds.
The ESP32-S3-Matrix breaks out 16 GPIO plus power; the T-Display-S3 AMOLED breaks out 28
pins. Neither is soldered down — ADR 0008 even says "some ship with pins pre-soldered,
which may or may not be wanted inside a sealed body."

```
HDR-DEV,controller,2.54mm female header strip - machined or dual-wipe,,Sockets for both dev boards on the carrier,THROUGH-HOLE,6,open,,0013,"Cut to length: 2 strips for the ESP32-S3-Matrix, 2 for the T-Display-S3 AMOLED, 2 spare. Sockets not solder-down - a dead dev board in a bonded body is otherwise terminal"
```

### F12. **ADR 0013 requires a regulator per board; the BOM has one buck and only the display board's capacitor.**

Severity: **Medium**.

ADR 0013: "give each board its own regulator from the umbilical +12 V, with local bulk
capacitance on the display board, so WiFi bursts are absorbed locally rather than reaching
the analog section." ADR 0012 repeats it: "containable with a separate regulator and local
bulk capacitance on the display board."

The BOM took half the prescription — `C-BULK-DISP` cites 0013 — and left the other half
out. ADR 0005's power tree still shows one buck feeding both boards, so the two ADRs
disagree and the BOM silently follows 0005. This matters beyond tidiness: ADR 0014
computes that a full-field matrix plus both dev boards asks 1.36 A of a 1 A part.

Either change `U-BUCK` qty to 2, or record in ADR 0005/0013 that the per-board regulator
was declined. Proposed:

```
U-BUCK,controller,R-78E5.0-1.0,Recom,12V to 5V switching regulator module,SIP-3 THROUGH-HOLE,2,candidate,,0005,"One per dev board (ADR 0013): splitting the rail keeps the display board's WiFi bursts off the real-time board and off the matrix. 1A each instead of 1A shared, which also relieves the 1.36A worst case in ADR 0014"
```

### F13. **The LC filter at the buck input has an L and no C, and the instrument has no bulk capacitance at the umbilical entry.**

Severity: **Medium**.

BOM row 53: `L-BUCK-IN … "A real inductor, not a bead. This is the part the bead was
wrongly credited for"`, citing ADR 0004's "**A real LC between the umbilical node and the
buck input** — 10–47 µH of inductance, not a bead."

An LC needs a C. Separately, ADR 0005 says the load switch exists partly for "**Inrush
limiting.** The instrument's bulk capacitance is a near-short at the instant of
connection" — a bulk capacitance the BOM does not contain (the only electrolytics are the
two strip caps and the display cap).

```
C-BUCK-IN,controller,100uF 25V electrolytic + 100nF ceramic,,Bulk and HF cap at the umbilical entry / buck input - the C of L-BUCK-IN's LC,THROUGH-HOLE radial / 0805,2,candidate,,0004,"Completes the LC. Also the capacitance TPS2553's inrush ramp is sized against (ADR 0005). 25V part on a 12V rail for derating"
```

### F14. **No decoupling for any controller-side IC except the shift registers.**

Severity: **High**.

ADR 0001 fixes only the registers: "**100 nF at every register**, on its own board. There
is no controller-side decoupling in the design at all". `C-DECOUPLE-165` (qty 4) satisfies
exactly that sentence and stops there. But ADR 0013 lists five more ICs on the carrier —
MCP3202, REF5050, OPA2197, 74AHCT125, R-78E5.0 — plus the MPXV4006DP, and none of them has
a cap. The REF5050 in particular is the part whose stability and noise the whole
ratiometric argument rests on.

```
C-DECOUPLE-CARRIER,controller,100nF X7R,,HF decoupling at every carrier IC - ADC, reference, buffer, level shifter, sensor,0805 (2.0 x 1.25mm),6,candidate,,0013,"One per supply pin: MCP3202, REF5050 in, OPA2197 +12V, 74AHCT125, MPXV4006DP, R-78E5 in. ADR 0001 fixed only the shift registers"
C-REF-OUT,controller,10uF X7R + 100nF,,Output capacitor on the REF5050,1206 / 0805,2,candidate,,0003,"Per the REF50xx datasheet's recommended output capacitance. This is the rail that IS the breath scale factor"
```

### F15. **The breath sensor is specified as a replaceable wear part; nothing in the BOM makes it replaceable.**

Severity: **Medium**.

ADR 0003: "**Treat the sensor as a wear part.** It is socketed or otherwise replaceable,
and the trap is clearable without disassembly. **Buy two**."

The BOM buys two (`U-BREATH` qty 2) and provides no socket. In a bonded body the spare is
only usable if the first one comes out.

```
SKT-BREATH,controller,Machined SIP socket strip 2.54mm,,Socket for the MPXV4006DP so the sensor is replaceable,THROUGH-HOLE,1,candidate,,0003,"The spare in U-BREATH is only reachable if the first part is removable. Case 1351-01 THT leads on 2.54mm"
```

### F16. **The module panel's power LED and its series resistor are specified and missing.**

Severity: **Medium**.

ADR 0004, "Panel, top to bottom": "Connector, power switch and **LED** — the system's only
power switch, since the instrument has none — two breath knobs, then six jacks".

```
LED-PANEL,module,3mm LED - diffused,,Panel power indicator,THROUGH-HOLE,1,candidate,,0004,Downstream of the load switch so it indicates umbilical power actually present
R-LED-PANEL,module,2k2 1%,,Series resistor for LED-PANEL,0805 (2.0 x 1.25mm),1,candidate,,0004,~4mA from +12V
```

### F17. **The panel pots have no knobs.**

Severity: **Low**.

ADR 0004: "**two breath knobs**". `POT-BREATH` is the potentiometer; a 9 mm Alpha
vertical pot ships as a bare shaft.

```
KNOB-BREATH,module,Knob for 6mm D-shaft or 9mm Alpha shaft,,Knobs for the breath gain and offset pots,n/a,2,candidate,,0004,Match the shaft type of the POT-BREATH variant ordered - D-shaft and knurled are not interchangeable
```

### F18. **The mechanical fastening set specified across ADR 0009 is entirely absent: U-bolt, backing plate, thumb plate, adhesive, loom wire.**

Severity: **High** (these are the "free now, impossible later" items ADR 0009 names).

ADR 0009: "A U-bolt near the middle of the instrument, **slightly above the centre of
gravity**, carries a neck strap. … **It must anchor to the structural plate stack, not to
the oak.**"; "**Mount the connector to an internal backing plate** — aluminium or ply,
tied into the same stack that carries the keys"; "thumb switch plate ~2 mm" in the
thickness stack; "**Run two spare conductors in every internal loom.** The looms are
hand-built, once, into a stack that cannot be reopened."; "The thumb switches mount to a
plate on the **inside** face"; and the whole design is "A laminated stack" — i.e. bonded,
with an adhesive nobody has chosen.

Six rows, none of which exists:

```
MECH-UBOLT,mechanical,U-bolt + backing washer plate + nylocs,,Strap anchor through the full laminated stack,THROUGH-HOLE,1,open,,0009,"Position settled empirically at the M8 pre-bond dry-assembly, not adjustable afterwards. Anchors to the plate stack, never to oak"
MECH-BACKPLATE,mechanical,TBD - aluminium or ply,,Internal backing plate for the etherCON and the U-bolt,n/a,1,open,,0009,"The tail face leaves ~3.5mm of oak above and below the 26x31mm etherCON flange. The oak is the face the screws pass through, not the thing they hold"
PLATE-THUMB,mechanical,TBD - ~2mm,,Thumb switch plate, mounted to the inside face of the oak bottom,n/a,1,candidate,,0009,"Carries the 4 left-thumb and 3 right-thumb switches. Same cutout geometry and same vendor order as PLATE-TOP"
MECH-THUMBREST,mechanical,TBD,,Laminated thumb rest lip on the bottom panel,n/a,1,open,,0009,"A 2D part added by lamination - there is no pocketing anywhere in this design"
MECH-ADHESIVE,mechanical,Structural adhesive for oak/acrylic/aluminium,,Lamination adhesive for the stack,n/a,1,open,,0009,"Keep it away from the breath sensor during lamination - a glue line across the reference port is the 5.2kPa failure in ADR 0003"
WIRE-LOOM,controller,Ribbon with alternating grounds and/or twisted pair,,Internal looms: key chain, LED power and data, UART, power,n/a,1,open,,0009,"A ground return per signal on the key chain is mandatory (ADR 0001 item 1). Two SPARE conductors in every loom - a few cents now, the instrument later"
```

### F19. **ADR 0002 leaves four lighter switches as an M1 decision and the BOM has no line for them.**

Severity: **Low**.

ADR 0002: "**the four left-thumb keys may want a lighter spring than the eleven finger
keys.** … Since this is settled before the build, mixed weights cost nothing but ordering
four of something different."

`SW1-n` is 18 of one part, `purchased`. If M1 says lighter thumb springs, that is a second
order. Carry the placeholder so it is not forgotten:

```
SW-THUMB,controller,KS-33 lighter variant - TBD at M1,Gateron,Optional lighter-spring switches for the four left-thumb keys,"switch, plate mount",4,open,,0002,"Decided by hand at M1 before anything is built. If taken, SW1-n drops to 14"
```

---

## B. Quantity errors

### F20. **`C-DECOUPLE` qty 10 is roughly half the module's supply-pin count.**

Severity: **High**.

BOM row 46:

```
C-DECOUPLE,module,100nF ceramic,,HF decoupling at every IC,0805 (2.0 x 1.25mm),10,candidate,,0004,"One per supply pin, close to the pin"
```

ADR 0004: "**100 nF ceramics** at every IC". The row's own note says "one per supply pin",
which is the correct rule and is not what qty 10 buys. Counting the module as the ADRs
specify it:

| IC | Supply pins needing a cap |
|---|---|
| OPA2197 × 5 (±12 V) | 10 |
| INA821 (±12 V) | 2 |
| DAC8568 (AVDD + digital) | 2 |
| 74AHCT125 | 1 |
| 74HC123 | 1 |
| TPS2553 (VIN) | 1 |
| LM317LZ (input) | 1 |
| **Total** | **18** |

Change to:

```
C-DECOUPLE,module,100nF X7R 50V,,HF decoupling at every IC supply pin,0805 (2.0 x 1.25mm),18,candidate,,0004,"One per supply pin, close to the pin. 5 duals + in-amp on +/-12V is 12 on its own, plus DAC 2, AHCT125, HC123, TPS2553 VIN, LM317 in"
```

### F21. **`R-OPAMP-IN` qty 5 undercounts the DAC-driven op-amp inputs by two.**

Severity: **Medium**.

BOM row 56:

```
R-OPAMP-IN,module,1k 1%,,Series resistor on each op-amp + input driven by the DAC,0805 (2.0 x 1.25mm),5,candidate,,0006,DAC on 5.25V and op-amps on +-12V do not come up together...
```

ADR 0006: "**1 kΩ in series with each op-amp's non-inverting input where the DAC drives
it.**" ADR 0006's channel table populates seven DAC channels, and every one of them drives
an op-amp input: pitch (ch 1), mod 1–4 (ch 2–5), the breath ambient-zero buffer (ch 6 —
ADR 0003: "driven from a low-impedance buffer rather than a divider"), and the shared
2.5 V mod offset buffer (ch 7 — ADR 0006: "**The 2.5 V reference point comes from a
buffered DAC channel**").

Seven, not five. This also cross-checks `U-OPA-PITCH` qty 5: 7 DAC-driven halves + breath
gain + breath offset = 9 halves = 4.5 duals, so five packages with one half spare is
right — which means the op-amp count and the resistor count are inconsistent with each
other in the current BOM.

```
R-OPAMP-IN,module,1k 1%,,Series resistor on each op-amp + input driven by the DAC,0805 (2.0 x 1.25mm),7,candidate,,0006,"Seven populated DAC channels, all driving op-amp inputs: pitch, mod 1-4, breath ambient-zero buffer (ch6), mod offset buffer (ch7)"
```

### F22. **`F-POLY` at 500 mA hold is below the instrument's own budgeted draw.**

Severity: **High** — and ADR 0014 documents this exact failure in detail.

BOM row 37:

```
F-POLY,controller,PPTC 1206 500mA hold,multiple,Resettable fuse at umbilical entry,1206 (3.2 x 1.6mm),1,candidate,,0005,1206 not 0603 - larger package is easier to place and inspect
```

ADR 0004: "+12 V | ~320 mA (45 module incl. the DAC regulator, ~275 instrument) —
**estimated, and a review put it nearer 410–430 mA**". ADR 0014 adds a ~3 W lighting
budget on the same rail — another ~250 mA at 12 V — and then describes what a PPTC does
when it is near its hold current:

> "LED current ↑ → umbilical current ↑ → the polyfuse self-heats and its resistance rises
> → the rail sags → the buck draws more input current → the polyfuse heats further →
> brownout → **the MCU resets** → the WS2815s **hold their last latched colour** → the
> load does not fall."

A 500 mA hold device under a ~430–470 mA load, derated for an interior running 10–20 K
above ambient (PPTC hold falls roughly 0.6 %/°C), is inside that loop by construction. The
hold current must sit well above the maximum legal draw, and the trip current is what
protects the rack.

```
F-POLY,controller,PPTC 1.1A hold / 2.2A trip 16V,multiple,Resettable fuse at umbilical entry,1206 (3.2 x 1.6mm),1,candidate,,0005,"1.1A hold, not 500mA: the instrument budget is 410-430mA plus ~250mA of lighting at 12V, and PPTC hold derates ~0.6%/degC in a body running 10-20K above ambient. Size finally from the E6 current-probe measurement; the module load switch is the fast limit, this is the backstop"
```

### F23. **`FB-IN` qty 4 is two different components on one line, and the capacitor half duplicates `C-STRIP-BULK`.**

Severity: **Medium** (un-orderable as written; see also F26).

BOM row 44:

```
FB-IN,module,Ferrite bead >=1A + 470uF at the load per branch,,"Input filtering, branched per rail",1206/1210 bead / THT electrolytic,4,candidate,,0004,"NOT a series resistor - we pass 295mA so even 2.2ohm costs 0.64V..."
```

ADR 0004's power tree needs four beads (+12 V analog branch, +12 V umbilical branch,
−12 V, +5 V) and four entry bulk capacitors. But the "470 µF at the load" text in this row
is ADR 0004's *correction*, which relocated that capacitance to the strips — "Bulk belongs
at the load, not at the entry. **470–1000 µF at each WS2815 feed point**" — and that is
already row 52, `C-STRIP-BULK`. The module's entry bulk is the ordinary "10–100 µF per
rail" of the same ADR. As written, one row orders an unknown mixture and double-books the
strip capacitors.

Replace with two rows:

```
FB-IN,module,Ferrite bead >=1A 600R@100MHz,,Series bead per supply branch,1206 or 1210,4,candidate,,0004,"One per branch: +12V analog, +12V umbilical, -12V, +5V. Rated >=1A - the common 0805 600R part is ~300mA and a saturated bead is a wire"
C-BULK-RAIL,module,47uF 25V electrolytic,,Entry bulk capacitance downstream of each bead,THROUGH-HOLE radial,4,candidate,,0004,"10-100uF per rail per ADR 0004. NOT the 470uF strip capacitance - that moved to the load and is C-STRIP-BULK"
```

### F24. **`R-PRECISION` has quantity `TBD` for a part the design needs exactly one of, and no orderable P/N.**

Severity: **Medium**.

BOM row 15:

```
R-PRECISION,module,LT5400-class matched network,ADI / Vishay,Matched resistor network for pitch scaling,MSOP-8 (0.65mm pitch),TBD,candidate,,0006,Highest-value precision part in the design. Ratio tracking is what matters not absolute tempco
```

ADR 0006: "**Use a matched resistor network for the pitch scaling stage** (LT5400 class,
MSOP-8) … This is the single highest-value precision component in the design." One pitch
stage, one network. `TBD` in a quantity column is an order-time hole in the most important
precision part in the project. The LT5400 also ships in DFN as well as MSOP, and its ratio
is set by the option suffix, so "LT5400-class" is not orderable either (see F30).

```
R-PRECISION,module,LT5400BCMS8-x (MSOP option, ratio per pitch stage design),ADI,Matched resistor network for pitch scaling,MSOP-8 (0.65mm pitch),1,candidate,,0006,"One pitch stage, one network. MUST be the MS8 (MSOP) option, not the DFN - the DFN is leadless and banned by the ADR 0013 package policy. Ratio suffix follows the final gain/offset topology"
```

### F25. **`LED-SIDE` quantity is written as a length, not as an orderable unit, and contradicts ADR 0014's purchasing instruction.**

Severity: **Low**.

BOM row 11 carries `qty = 2 x 420mm`. ADR 0014: "**Buy one 1 m strip and cut two 420 mm
runs from it.**"

```
LED-SIDE,controller,"WS2815 (12V addressable), 60/m, 1m reel",multiple,Addressable LED strip - one 1m reel cut into two 420mm side runs,flexible strip,1,candidate,,0014,"0.84m used of 1m. TWO independent data lines, no crossover wire - both ends of the cavity are the congested ones. 60/m settled on appearance; M6 can downgrade on looks"
```

---

## C. Wrong or weak ADR citations

### F26. **`U-LVL-MOD` cites ADR 0006, which never mentions a level shifter.**

Severity: **Medium**.

BOM row 38:

```
U-LVL-MOD,module,74AHCT125,,"Level shifter, 3V3 SPI up to 5V for the DAC",SOIC-14 (1.27mm pitch),1,candidate,,0006,"SAME part as the instrument LED shifter. Covers SCLK MOSI CS with a spare gate. Runs from bus +5V; the DAC runs from U-REG-DAC"
```

The part, its rail, its threshold arithmetic and its OE gating are all in ADR 0004 ("**A
local 5.25 V regulator … 74AHCT125** for the shifter, running from the **bus +5 V rail**"),
reinforced by ADR 0005 ("It is used — but **only for the 74AHCT125 level shifter**, around
10 mA"). ADR 0006 is about channel allocation and calibration and says nothing about it.
The citation sends a reader to the wrong document for the part's entire justification —
including the OE gating requirement missing in F8.

```
U-LVL-MOD,module,74AHCT125,,"Level shifter, 3V3 SPI up to 5V for the DAC",SOIC-14 (1.27mm pitch),1,selected,,0004,"SAME part as the instrument LED shifter. Covers SCLK MOSI CS with a spare gate. Runs from bus +5V; the DAC runs from U-REG-DAC. OE gated from umbilical +12V presence (ADR 0004) - see R-OEGATE"
```

### F27. **`R-MOSI-SER` is categorised `module`; ADR 0004 puts it at the driving end, which is the instrument.**

Severity: **Medium** (it lands on the wrong PCB).

BOM row 55:

```
R-MOSI-SER,module,220R 1%,,Series termination on MOSI at the driving end,0805 (2.0 x 1.25mm),1,candidate,,0004,Also removes the need for SYNC regeneration at the module end
```

ADR 0004: "**220 Ω in series on MOSI at the driving end.** Source termination on the one
line that runs the full umbilical carrying data." MOSI is driven by the real-time board
(ADR 0013: "SPI2: SCK, MOSI, MISO — DAC8568 + MCP3202" on the instrument). Source
termination at the far end of the cable is not source termination. The row's own
description says "at the driving end" while its category says `module`.

```
R-MOSI-SER,controller,220R 1%,,Series termination on MOSI at the driving end,0805 (2.0 x 1.25mm),1,candidate,,0004,"Driving end is the real-time carrier, not the module - source termination at the receiver is not source termination. Also removes the need for SYNC regeneration at the module end"
```

### F28. **`U-TVS-UMB` cites ADR 0004, which never specifies ESD protection on the umbilical.**

Severity: **Medium**.

BOM row 32:

```
U-TVS-UMB,controller,SP3012-06UTG or similar array,multiple,TVS array on umbilical entry,SOT-23-6 (0.95mm pitch),1,candidate,,0004,Multi-line array beats discretes for placement. 8 conductors from outside
```

ADR 0004 covers the connector, the conductor budget, the pin mapping and the power entry,
and specifies no TVS anywhere. ADR 0005's protection discussion is the polyfuse and the
load switch. So this row is justified by no ADR — it is sensible engineering, but it is
unrecorded, which is precisely what the ADR process exists to prevent. Two sub-problems:
the qty is 1 for a two-ended cable (only the instrument end is protected), and a 6-channel
array against the 8 conductors the note cites (6 signals + 2 grounds — arithmetic that
works but is not stated).

Either write the decision into ADR 0004/0005 and cite it, or mark the row accordingly:

```
U-TVS-UMB,controller,SP3012-06UTG or similar 6-line array,multiple,TVS array on umbilical entry,SOT-23-6 (0.95mm pitch),1,open,,0005,"NOT SPECIFIED BY ANY ADR - added in the BOM only. 6 channels covers the 6 non-ground conductors (+12V, SCLK, MOSI, CS, BREATH plus one spare); the module end is currently unprotected. Needs an ADR paragraph or a deletion"
```

### F29. **`CAP1-n`'s note contains a logic-family argument that belongs to `U-KEYS` and contradicts ADR 0001.**

Severity: **Low** (documentation), but it is a live contradiction inside one CSV.

BOM row 3, keycaps, notes field: "Sold in 5-packs - 18 keys needs 4 packs. Smaller than
18mm MX spacing. **74HC preferred over LVC for ~2x input noise margin, not for speed** -
over an unterminated loom LVC's faster edges are worse".

ADR 0001: "**On family choice: the part stays 74LVC165A** … LVC is kept because it is
specified natively at 3.3 V and is already selected — but it is kept **with item 4 above**,
the series termination". BOM row 8 (`U-KEYS`) says the same: "Kept for its native 3V3 spec,
WITH 33-68R series termination."

So the keycap row asserts a part choice that is (a) not about keycaps, (b) opposite to the
accepted ADR, and (c) opposite to the row that actually carries the part. Also note row 2
(`SW1-n`) still contains "Plate cutout must be measured", which ADR 0002 explicitly
retracts — "**That was wrong.** … And a caliper is the worse instrument for this" — in the
same note that then says to use the datasheet.

```
CAP1-n,controller,MT165-MX,Tai-Hao,Keycap 16.5x16.5mm blank black MX stem,keycap,18,purchased,Beekeeb,0002,"Sold in 5-packs - 18 keys needs 4 packs. 16.5mm caps allow ~18-20mm pitch before collision, tighter than standard 18mm MX spacing"
SW1-n,controller,KS-33 Red (linear),Gateron,Low-profile mechanical switch MX stem,"switch, plate mount",18,purchased,Amazon,0002,"Binary. Cutout is 14.0 x 14.0mm, same as MX - from the published geometry, NOT from a caliper (ADR 0002). Soldered. Thumb keys may want a lighter spring - decide at M1. 12.2mm tall, 1.70mm pretravel, 3.00mm total travel, 3-pin. Use Gateron's datasheet and STEP model"
```

---

## D. Un-orderable rows, statuses and package policy

### F30. **`U-DAC` violates the one instruction ADR 0006 gives the BOM by name.**

Severity: **High**.

BOM row 12: `U-DAC,module,DAC8568C (or A grade) - full orderable P/N required,TI,…`

ADR 0006: "**Specify the full orderable part number in the BOM**, not 'DAC8568'. The grade
letter is the whole decision and it is invisible in the generic name."

The BOM restates the requirement instead of satisfying it, and "DAC8568C (or A grade)"
leaves both the grade and the package suffix open — the family is sold in a TSSOP (`PW`)
body and in leadless bodies that the ADR 0013 package policy bans outright. This is also
the row where a wrong grade silently parks the pitch output octaves high (B/D reset to
midscale).

```
U-DAC,module,DAC8568CAPW,TI,"Octal 16-bit DAC SPI, internal reference",TSSOP-16 (0.65mm pitch),1,selected,,0006,"C grade = ZERO-scale reset, which with the DAC-sourced 2.5V offset parks pitch subsonic and mods at exactly 0V. A grade is the alternative; B/D reset to midscale and are WRONG here. PW = TSSOP - do not order a leadless body (ADR 0013). Populate 7 of 8. Internal ref is DISABLED by default, enable at boot. AVDD from U-REG-DAC"
```

### F31. **`BENCH` uses a status value that does not exist in the BOM's vocabulary, and is not a bill-of-materials item.**

Severity: **Low**.

BOM row 25:

```
BENCH,tooling,n/a,,"Scopes, logic analysers, DMMs, signal generators, RF",n/a,1,available,,0006,Full bench available - E9 not gated on tooling
```

Every other row uses `purchased` / `selected` / `candidate` / `open` / `not-needed`;
`available` is a sixth value invented for one row. The underlying fact is real and is
already recorded in ADR 0006 ("Resolved — a full bench is available"). A BOM is what gets
ordered. Delete the row:

```
DELETE: BENCH,tooling,n/a,,"Scopes, logic analysers, DMMs, signal generators, RF",n/a,1,available,,0006,Full bench available - E9 not gated on tooling
```

...and, since nothing in the repository defines the status vocabulary, add the five values
to `docs/decisions/README.md` beside the ADR status table, or to a header comment in the
BOM.

### F32. **Ten rows carry `candidate` for parts that an Accepted ADR names outright.**

Severity: **Medium** (it makes the status column uninformative exactly where it should be
driving orders).

ADR 0013 enumerates the carrier's contents as settled: "**74LVC165** shift registers,
**MCP3202** ADC, **REF5050** 5.000 V reference, **OPA2197** dual …, **74AHCT125** level
shifter, **R-78E5.0** regulator module, polyfuse, umbilical connector". ADR 0001 says of
the shift register: "LVC is kept because it is specified natively at 3.3 V and **is already
selected**". ADR 0005 states the LM317LZ, the 1N5817s and the 16-pin header as decisions.

Yet `U-ADC`, `U-KEYS`, `U-BUCK`, `U-REF-BREATH`, `U-BUF`, `U-LVLSHIFT`, `U-LVL-MOD`,
`U-REG-DAC`, `D-REVPOL` and `J-PWR-EURO` are all `candidate` — the same word carried by
`R-PRECISION` ("LT5400-class"), `U-DIFFRX` ("INA821 or INA828") and `J-UMBILICAL`
("variant TBD"), which are genuinely undecided. Two different meanings share one value.

Proposed: move those ten to `selected`, reserving `candidate` for rows where the ADR
itself leaves a choice open. Example:

```
U-KEYS,controller,74LVC165A,multiple,8-bit parallel-in shift register,SOIC-16 (1.27mm pitch),4,selected,,0001,"SOIC-16. Kept for its native 3V3 spec, WITH 33-68R series termination (R-TERM-CHAIN). 74HC165 is a drop-in on the same footprint if E4 says otherwise"
```

### F33. **`U-IMU` is a phantom line that can be double-ordered; the BOM's own convention says it should be qty 0 / `not-needed`.**

Severity: **Low**.

BOM row 7 lists the QMI8658C at qty 1, status `selected`, with package "on dev board".
`U-OPA-GEN` (row 14) sets the convention for a part that exists in the design but is not
separately bought: qty 0, `not-needed`, with the explanation in the notes. `J-USB`,
`U-ESD-USB` and `SW-BOOT` follow it correctly for exactly this reason ("Dev boards carry
these"). The IMU is the same case and is recorded differently.

```
U-IMU,controller,QMI8658C (onboard U-MCU-RT),multiple,6-axis IMU - accel + gyro no fusion,on dev board,0,not-needed,,0007,"Not separately ordered - it is on U-MCU-RT and the carrier is passive, so this IS the final IMU. SDA=GPIO11 SCL=GPIO12 INT1=GPIO10 INT2=GPIO13. Fusion not wanted: raw accel is the signal and capture-on-press makes drift irrelevant"
```

### F34. **Package policy: no confirmed violation, but two rows assert a package that cannot be checked as written.**

Severity: **Low–Medium**.

Against the ADR 0013 table (SOIC/SIP/through-hole preferred, TSSOP/MSOP at 0.65 mm
acceptable, QFN/BGA/leadless avoided, passives 0805/1206), every row complies on its face:
SOIC-8/14/16 at 1.27 mm, TSSOP-16 and MSOP-8 at 0.65 mm, SOT-23-6 at 0.95 mm (which ADR
0005 pre-emptively defends: "at 0.95 mm pitch it is *coarser* than the TSSOP-16 DAC already
accepted"), SOT-23, TO-92, DO-41, SIP-3, case 1351-01, and 0805/1206 passives.

Two rows cannot be verified from the BOM as written:

- `U-TVS-UMB` — "SP3012-06UTG": the row asserts SOT-23-6, but `-UTG`-style suffixes on
  Semtech arrays commonly denote a leadless µDFN body, which the policy bans. Confirm
  against the datasheet before ordering, or pick an array whose SOT-23-6 body is certain.
- `R-PRECISION` — "LT5400-class" is offered in both MSOP-8 and a leadless DFN; the row
  names MSOP-8 but the part field does not pin the option (F24 fixes this).

Three rows give two packages in one field and should be resolved before fab:
`R-REG-SET` ("0805 or through-hole"), `L-BUCK-IN` ("SMD shielded or THT"), `C-BULK-DISP`
("1206 / electrolytic THT"). `FB-IN` gives two packages because it is two parts (F23).

### F35. **`PANEL` states a 6HP width that disagrees with ADR 0004's own arithmetic.**

Severity: **Low**.

BOM row 21: `PANEL,module,"2mm aluminium, 6HP x 3U (30.0 x 128.5mm)"`.

ADR 0004: "A 6HP panel is **30.18 mm** wide — `(6 × 5.08) − 0.3`, +0/−0.2." 30.0 mm sits at
the very bottom of that tolerance band, and the panel is also the part whose remaining
material either side of the 23.8 mm etherCON hole the ADR computes at 3.19 mm — a figure
that only holds at 30.18.

```
PANEL,module,"2mm aluminium, 6HP x 3U (30.18 x 128.5mm)",,Eurorack front panel,n/a,1,candidate,,0004,"30.18mm = (6 x 5.08) - 0.3, +0/-0.2 (ADR 0004). Laser or waterjet from DXF - SAME vendor and order as PLATE-TOP and PLATE-THUMB. Brace the etherCON to the PCB: 3.19mm of aluminium each side passes fit and fails stiffness"
```

---

## E. Defects found on the ADR side while walking backwards

These are not BOM rows, but they are why two BOM rows look wrong and should be fixed so
the next audit does not re-derive them.

### F36. **ADR 0004 still specifies the INA134, which ADR 0003 replaced.**

Severity: **Medium** (documentation; the BOM is right and the ADR is stale).

ADR 0004, "Module parts, chosen for build ease": "**INA134 for the breath difference amp.**
On-chip matched resistors give ~90 dB CMRR against the 60 dB needed (ADR 0003), with no
external matching network to place or match."

ADR 0003 explicitly overturns this: "**But the receiver is a true instrumentation amplifier
(INA821 / INA828), not a difference amplifier.** A difference amp's CMRR is set by
**source-impedance balance, not by the chip** … this design's own protection resistor and
pulldown would have left roughly **19–34 dB against the 60 dB the scheme needs.**" The BOM
follows 0003 correctly; ADR 0004's paragraph should be struck through with a pointer, per
the repo's own rule ("do not edit the old ADR" applies to *decisions*, not to a sentence
that now names the wrong part in an Accepted ADR).

### F37. **ADR 0013's zone table still places the breath sensor and ADC at the top of the instrument.**

Severity: **Low** (documentation).

ADR 0013: "| **Top** | Display board (AMOLED + WiFi), **breath sensor + ADC on a short
tube**, upper key cluster |".

ADR 0003 reverses this at length — "**Sensor placement: at the bottom, with the real-time
board.** Decided after review. This reverses an earlier placement whose justification
turned out to be false" — and ADR 0009 and ADR 0014 both depend on the new position (the
side channels are only safe to share with LED current because no analog run traverses the
body). The BOM's `U-BREATH` and `TUBE` notes follow 0003. ADR 0013's table is the last
place the old placement survives, and it is the table someone will lay the boards out from.

### F38. **ADR 0006 says both "populate six" and "seven of eight".**

Severity: **Low** (documentation; the BOM picked the right one).

ADR 0006: "Use an **octal** 16-bit DAC (DAC8568 or AD5676) and **populate six**", against
its own channel table three paragraphs earlier: "**Seven of eight channels used, one
spare**" — pitch, mod 1–4, ch 6 ambient zero, ch 7 mod offset. `U-DAC`'s note ("Populate 7
of 8") is correct; the ADR sentence is a leftover from before the mod-offset channel
existed, and it is the sentence that would make someone size F21's resistor count at five.

---

## Summary table — ADR → parts specified → parts present → gaps

| ADR | Hardware it specifies | In BOM | Missing / wrong |
|---|---|---|---|
| **0001** MCU & partitioning | 74LVC165A ×4; 100 nF per register ×4; 33–68 Ω termination ×2; per-signal ground return in the loom; 4 identical cluster boards | 3 of 6 (`U-KEYS`, `C-DECOUPLE-165`, `R-TERM-CHAIN`) | **`PCB-CLUSTER` ×4** (F10); **`WIRE-LOOM`** (F18); status `candidate` though ADR says "already selected" (F32) |
| **0002** Key switches | 18 × KS-33 Red; 18 × MT165-MX caps; optional 4 lighter thumb switches; plate at 1.5/2 mm | 2 of 4 | **`SW-THUMB`** placeholder (F19); stale "must be measured" note (F29); plate thickness still open (tracked on `PLATE-TOP`) |
| **0003** Breath path | MPXV4006DP ×2; MCP3202; REF5050; OPA2197 dual; INA821/828 + **gain resistor**; 0.6× divider ×2; 220 nF AA cap; **series protection R ×3**; **500 Hz band-limit C ×2**; PTFE plug; tube + trap; **sensor socket**; **REF output cap** | 9 of 15 | **`R-INAGAIN`** (F1); **`R-BREATH-SER`, `R-BREATH-IN`** (F2); **`C-BREATH-BL`, `C-BREATH-BLRX`** (F3); **`SKT-BREATH`** (F15); **`C-REF-OUT`** (F14) |
| **0004** Module & umbilical | etherCON ×2; 6HP panel; jacks; pots; toggle; IDC header; 1N5817 ×2; ferrite ×4 + **entry bulk ×4**; LM317LZ + 2R + 2C; 74AHCT125 + **OE gating**; SPI pulls ×3; 220 Ω MOSI; watchdog + **R/C**; LC inductor + **C**; **panel LED + R**; **knobs**; **module PCB**; **connector bracing** | 14 of 22 | **`R-OEGATE`/`D-OEGATE`** (F8); **`R-WDT`/`C-WDT`/`R-CLR-PU`** (F6); **`C-BULK-RAIL`** (F23); **`C-BUCK-IN`** (F13); **`LED-PANEL`/`R-LED-PANEL`** (F16); **`KNOB-BREATH`** (F17); **`PCB-MODULE`** (F10); `C-DECOUPLE` qty 10→18 (F20); `R-MOSI-SER` on the wrong board (F27); panel width 30.0→30.18 (F35); ADR itself still names INA134 (F36) |
| **0005** Power | R-78E5.0 (×1 or ×2); polyfuse; TPS2553 + **ILIM R**; 1N5817 ×2; LM317LZ; breath pulldown; **USB-OR diode** | 6 of 9 | **`R-ILIM`** (F7); **`D-USBOR`** (F9); polyfuse hold current too low (F22); regulator count vs ADR 0013 (F12) |
| **0006** CV channels | DAC8568 **full P/N**; OPA2197 ×5; LT5400 ×1; 6 jacks; 2 pots; 2 trimmers; 1 kΩ out ×6; 1 kΩ op-amp in ×**7**; BAV99 ×6; ferrites; **6 filter caps**; **mod gain network**; **pitch fixed resistors** | 10 of 14 | **`C-FILT-PITCH`/`C-FILT-SLOW`** (F4); **`R-MODGAIN`** ×16 (F5); `R-OPAMP-IN` 5→7 (F21); `R-PRECISION` qty TBD→1 (F24); `U-DAC` P/N unresolved (F30); ADR self-contradiction on six vs seven channels (F38) and on matched-vs-discrete for mod (F5) |
| **0007** IMU | ESP32-S3-Matrix ×1 (IMU onboard) | 2 of 2 | `U-IMU` should be qty 0 / `not-needed` per the BOM's own convention (F33) |
| **0008** Display | T-Display-S3 AMOLED base ×1 | 1 of 1 | none |
| **0009** Enclosure | Key plate; oak ×2; acrylic ×2; **thumb plate**; **thumb rest**; **U-bolt**; **internal backing plate**; **adhesive**; conformal coat; ground bond; tail window; **spare loom conductors** | 5 of 12 | **`PLATE-THUMB`, `MECH-THUMBREST`, `MECH-UBOLT`, `MECH-BACKPLATE`, `MECH-ADHESIVE`, `WIRE-LOOM`** (F18) |
| **0010** Key layout | none (data only) — fixes 18 switches, 15 note + 3 control | n/a | none |
| **0011** Licensing | none | n/a | none |
| **0012** Config interface | none (radio is onboard); wants display-board local bulk + regulator | `C-BULK-DISP` only | regulator half missing (F12) |
| **0013** Two-MCU split | **Carrier PCB**; **dev-board headers**; 74LVC165; MCP3202; REF5050; OPA2197; 74AHCT125; R-78E5.0; polyfuse; connector; passives; **per-board regulator + display bulk**; package policy | 8 of 12 | **`PCB-CARRIER`** (F10); **`HDR-DEV`** (F11); **`C-DECOUPLE-CARRIER`** (F14); second regulator (F12); ADR's zone table still puts the sensor at the top (F37) |
| **0014** Lighting | WS2815 1 m reel; 74AHCT125; 470–1000 µF ×2 at the feeds; window + diffuser; 22 mm carrier cutout | 4 of 5 | qty expressed as a length (F25); the 22 mm cutout lives on the missing `PCB-CARRIER` (F10) |

---

## Consolidated change set

**Delete (1):** `BENCH`.

**Change (16):** `SW1-n` (note), `CAP1-n` (note), `U-IMU` (qty/status), `U-KEYS` (status),
`U-BUCK` (qty), `LED-SIDE` (qty/units), `U-DAC` (P/N, status), `R-PRECISION` (qty, P/N),
`PANEL` (width), `U-TVS-UMB` (status, ADR), `F-POLY` (rating), `FB-IN` (split),
`C-DECOUPLE` (10→18), `R-OPAMP-IN` (5→7), `R-MOSI-SER` (category), `U-LVL-MOD` (ADR),
plus the nine further `candidate`→`selected` status moves in F32.

**Add (34 rows):** `R-INAGAIN`, `R-BREATH-SER`, `R-BREATH-IN`, `C-BREATH-BL`,
`C-BREATH-BLRX`, `C-FILT-PITCH`, `C-FILT-SLOW`, `R-MODGAIN`, `R-WDT`, `C-WDT`, `R-CLR-PU`,
`R-ILIM`, `R-OEGATE`, `D-OEGATE`, `D-USBOR`, `PCB-CARRIER`, `PCB-CLUSTER`, `PCB-MODULE`,
`HDR-DEV`, `C-BULK-RAIL`, `C-BUCK-IN`, `C-DECOUPLE-CARRIER`, `C-REF-OUT`, `SKT-BREATH`,
`LED-PANEL`, `R-LED-PANEL`, `KNOB-BREATH`, `MECH-UBOLT`, `MECH-BACKPLATE`, `PLATE-THUMB`,
`MECH-THUMBREST`, `MECH-ADHESIVE`, `WIRE-LOOM`, `SW-THUMB`.

**ADR edits (3):** strike the INA134 paragraph in ADR 0004 (F36); correct ADR 0013's zone
table (F37); reconcile "populate six" with the seven-channel table in ADR 0006 (F38), and
resolve its matched-network-vs-discretes contradiction for mod 1–4 (F5).

**Nothing in the current BOM violates the package policy outright.** Two rows need a
datasheet check before they can be said to comply (F34).

*No repository file was modified in producing this audit.*
