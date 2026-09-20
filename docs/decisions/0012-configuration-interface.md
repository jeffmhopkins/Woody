# 0012 — Configuration interface

**Status:** Accepted

## Context

The instrument has a lot to configure: a custom fingering table (ADR 0010), a
four-channel routing matrix with source, scale, offset, curve and slew per
channel (ADR 0006), breath response curves (ADR 0003), IMU gating behaviour
(ADR 0007), and pitch calibration (ADR 0006).

Driving all of that through a small display and a couple of buttons is a bad
experience and a large amount of firmware — menu systems are their own project,
and they are the part of an instrument people quietly stop using.

## Decision

**Configure over WiFi from a phone, using a web app served by the instrument.**

The ESP32-S3 has 2.4 GHz WiFi and BLE 5 built in, so this costs no additional
hardware.

### SoftAP first, station mode optional

The instrument hosts its own access point. The phone joins it directly and a
captive portal opens the config page.

This is chosen over joining an existing network because **it works everywhere
with zero infrastructure** — at a gig, in a rehearsal room, in someone else's
studio, on a plane. A station-mode option (joining a known network, discovered
by mDNS at `woody.local`) is worth adding later for convenience at home, where
the phone keeps its internet connection, but it cannot be the only path.

### A web app, not a native app

Served from flash, opened in the phone's browser. No app store, no iOS/Android
split, no install, and it works identically from a laptop when that is more
convenient — which it will be for fingering table work.

BLE was considered and rejected as the primary path: Web Bluetooth is not
available in Safari on iOS, which would force a native app and an app-store
relationship for a one-person instrument project.

### Security

WPA2 with a password, not an open AP. This is not a high-security problem, but
an open access point that lets anyone reconfigure the instrument mid-set is an
avoidable annoyance at a festival.

## The radio must be off while playing

> **Substantially relaxed by [ADR 0013](0013-two-mcu-split.md).** The radio now
> lives on its own MCU, so the CPU-contention half of this reasoning no longer
> applies — WiFi cannot preempt the output loop because it is not on that
> silicon. The current-transient half still stands, but is containable with a
> separate regulator and local bulk capacitance on the display board. **Live
> configuration while playing is therefore expected to be workable**, which is
> worth real effort: adjusting a routing matrix and hearing the result
> immediately is a different instrument to one you stop playing to configure.
>
> Measure it before trusting it (see the characterisation table in the latency
> budget). The reasoning below is kept because it is why the split was worth
> making.

**This was the rule that made the rest of the design survive.**

WiFi is actively hostile to everything this project has been careful about:

- **Current transients.** Transmit bursts pull several hundred milliamps in
  spikes. Those land on the rail, propagate through the instrument's local buck
  converter, and end up as ripple on the CV outputs — and on the rack's +12V,
  where every other module gets to enjoy them (ADR 0005).
- **Latency jitter.** The WiFi stack is not a polite neighbour. If the radio
  task can preempt the 4 kHz sensor and DAC loop, the loop's timing becomes
  non-deterministic, and the entire latency budget is built on that loop being
  regular.

So:

1. **The radio is off by default and during performance.** It is enabled
   explicitly, by entering config mode — one of the spare shift-register inputs
   (ADR 0010) or a gesture. It is not a background service.
2. **WiFi is pinned to the UI core**, never the core running the sensor and
   output loop. (Under ADR 0013 this is stronger still: the radio is on a
   different chip.)
3. **The latency budget is only valid with the radio off.** Noted in
   [the budget](../reference/latency-budget.md). If config mode is ever usable
   while playing, that combination needs measuring before it is trusted.

## Consequences

### The display's job shrinks substantially


This is the biggest downstream effect. The display no longer has to host a
navigable configuration system — it becomes a **status** display: current note,
breath level, active channels, config-mode and link state.

That materially changes ADR 0008. A small OLED, previously marginal because a
four-channel routing matrix needed depth to navigate, is now comfortable and
arguably preferable.

It also reduces the button count on the instrument. Config mode needs a way in;
beyond that, physical controls are optional.

### Live monitoring is a tooling win, not just convenience

A phone on a WebSocket can show live breath pressure, IMU angles and commanded
CV values in real time. That is genuinely useful beyond configuration:

- **M2/M3 ergonomics** — watch which keys actually register while trying a
  layout, rather than inferring it by ear.
- **E9 calibration** — see commanded versus measured side by side while
  trimming, instead of alternating between a meter and a menu.
- **Breath curve tuning** — see the response curve and play against it at the
  same time.

Worth building early for that reason alone, ahead of the configuration features
it will eventually host.

### OTA updates come nearly free

Once there is a WiFi stack and a web server, over-the-air firmware update is a
small addition. Not a priority, but worth leaving room for — the instrument will
be sealed in a laminated wooden body, and reaching the USB connector may not
always be convenient.

## Open

- Whether config mode is entered by a physical input or a key gesture.
- Whether the web app's state is the authority, or the instrument's NVS is, when
  they disagree after an interrupted session.
