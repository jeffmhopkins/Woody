# 0011 — Licensing

**Status:** Open

## Context

The previous project, Open Woodwind Project, was public with **GPLv3** firmware
(the licence header appears in `src/owp/owp.ino`). This project is also public.

Hardware and CAD are not well served by software licences, so open hardware
projects typically split them.

## Options

**Firmware** — GPLv3 continues the precedent and keeps derivative firmware open.
MIT is more permissive and more likely to be reused.

**Hardware and CAD** — CERN-OHL-S is the strong-reciprocal open hardware
licence and the closest analogue to GPLv3. CC-BY-SA is commonly used and widely
understood, though not designed for hardware.

**Documentation** — CC-BY-SA or CC-BY.

## Open

Undecided. Worth settling before the repository gets meaningful external
attention, since relicensing later requires the agreement of every contributor.

A reasonable default, if no strong preference emerges: GPLv3 firmware to match
the previous project, CERN-OHL-S hardware, CC-BY-SA documentation.
