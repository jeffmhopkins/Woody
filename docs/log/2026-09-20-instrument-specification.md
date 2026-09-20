# 2026-09-20 — Instrument specification

Second session entry. Following the kickoff, the instrument itself got
specified: key count and roles, how the hands hold it, the strap, the envelope,
and how it gets configured.

## Decided

**18 keys.** Left hand 5, right hand 6, left thumb 4, right thumb 3 — but not
all of them are note keys. The right thumb's three are **control** inputs for
modulation and IMU gating, so the fingering table covers 15, not 18. That
distinction now lives in the layout data as a `role` field, because getting it
wrong in either direction is a quiet, ear-only bug.

**Chain:** 4× 74HC165, one per cluster, 32 bits for 18 switches, 14 spare. The
spares are worth spending on dedicated octave, mode and hold inputs rather than
repeating the 2021 firmware's key-combination mode switching.

**Envelope:** 18 inches long, 1.5 inches thick, width still open. The
longitudinal budget closes with three inches of slack, so the layout wants
designing but is not cramped.

**Strap:** U-bolt on the bottom face in the inter-hand gap, slightly above CG,
through-bolting the whole laminated stack.

**Configuration over WiFi from a phone**, not through the display.

## How the hands hold it

The most design-relevant thing learned this session, and it constrains the
layout more than the key count does.

The left thumb **sandwiches** — opposing the fingers to grip — and actuates with
the **tip**, extending from that grip. The right thumb **rests**, with its three
control switches offset from the rest position.

Three consequences, all now recorded in ADR 0010:

- Grip patch and key cluster must be physically separate on both thumbs, or
  holding the instrument triggers keys.
- The left thumb's four keys lie on the **arc the tip sweeps**, not in a line.
  This stopped being a preference and became the mechanism — a line makes four
  keys unreachable.
- A thumb tip extending from a grip has little force. Light linear switches
  almost certainly; KS-33 weight variant is unconfirmed and goes on the M1 list.

Since the underside keys are operated entirely by feel, the inset recess rim is
a **tactile locator**, not a side effect. Worth designing.

## Corrections made

- **The left thumb concern was overstated.** Four keys were flagged as ambitious
  for a thumb also carrying the instrument's weight. With the right thumb as the
  primary rest, the left thumb is largely freed, and four register keys under it
  is conventional — a saxophone's octave key works the same way.

- **The long-run signal risk was overstated.** ADR 0001 assumed roughly two feet
  between the MCU at the top and the IMU and connector at the bottom. At 18
  inches overall the longest run is nearer 14–16 inches. The topology is
  unchanged; RS-485 transceivers drop from likely to contingency.

- **The display's job shrank.** With configuration on a phone, it no longer has
  to host a navigable routing matrix. ADR 0008 now leans OLED, which the earlier
  UI depth requirement had been arguing against.

## The WiFi rule

The radio is off by default and during performance. Transmit bursts pull
hundreds of milliamps in spikes that land on the CV outputs and on the rack's
rail, and the WiFi stack can preempt the 4 kHz loop the entire latency budget
assumes is regular. Radio pinned to the UI core, enabled only in config mode,
and the budget now states the assumption explicitly.

## Worth pulling forward

**Live telemetry to the phone is a test instrument, not a convenience.** A
WebSocket streaming breath pressure, IMU angles and commanded CV would make M2
and M3 layout work observable rather than inferred by ear, and would make E9
calibration a side-by-side comparison instead of alternating between a meter and
a menu. It depends only on E1, so it should be built long before its phase.

## Still open

Instrument width — a grip question, to be answered with the paper mockup at M2
rather than from a number. Breath sensor identity, IMU part, display, connector,
licence. None of them block work.

## Next

Unchanged: M1 the day the switches arrive. Measure the plate cutout, scope the
contact bounce, confirm the switch weight, and measure the body height below the
plate — that last one decides how much cavity survives in the thumb regions.
