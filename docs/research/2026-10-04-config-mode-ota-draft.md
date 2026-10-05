# Configuration mode and OTA — a draft design (issue #37)

**DRAFT, DEFERRED.** This is not the corpus's authority. The owner decided the
hardware and deferred the firmware on 2026-10-04 (*"Let's not worry about the
firmware now. Just add the capability"*; ADR 0015, *Amendment, 2026-10-04*).
This note records the design study made for issue #37, so the firmware track
starts from it. As a research note it is a record of that day and is not
corrected. When the firmware is designed, the result goes into
`firmware/README.md`.

Evidence marks: `[ds <file> p.N]` a banked document, `[calc]` the arithmetic
shown, `[repo]` a file in this repository at 18d0b5f, `[from memory]`
unchecked.

## Entry

- **At power-up:** RT1 and RT4 held through boot, until the matrix shows the
  config glyph (about 2 s). RT1 to RT4 are `role: control` and never enter the
  fingering table `[repo config/key-layout.yaml; ADR 0010]`. RT1 and RT4 are
  the diagonal corners across the right-thumb rest (pair, rest, pair), so one
  thumb cannot press both by accident. The keys are read only at boot.
- **While idle (optional):** all four RT keys for 5 s, with breath below the
  deadband for the whole window. The matrix counts down, and a release
  cancels. Firmware then writes a flag and restarts, **so configuration mode
  is always a fresh boot**: Wi-Fi never starts in a process that has run the
  output loop.
- **Recovery without keys:** three power-cycles within 10 s each boot into
  configuration mode with defaults (a counter in RTC memory or NVS).

## What it does

- **The output loop does not run.** The DAC is written once to a safe state:
  the pitch held, the mod channels at their configured rest, and the reference
  and control registers refreshed. **The breath jack cannot be muted by
  firmware**: it is the analog buffer, not the DAC. Wi-Fi current steps reach
  `INST_POS12` through the cable, about 166 mA × 0.34 Ω ≈ 56 mV
  `[calc; 0.34 Ω from ADR 0005's table]`. E11 should measure the breath jack
  while the radio beacons. Until then, enter configuration mode with the rack's
  breath VCA closed.
- **A SoftAP:** WPA2, a fixed channel, transmit power capped well below
  21 dBm. A plain HTTP page and a WebSocket, which iOS Safari supports where
  Web Serial and Web MIDI do not `[from memory]`. The page has settings
  (including MIDI channel, controller rate and **TRS Type A/B**), a live
  breath and IMU view (diagnostic only), firmware upload and Exit. iOS's
  captive-portal sheet may not allow a file upload `[from memory]`, so the page
  says to open `http://192.168.4.1` in Safari for an update.
- **Status on the 8×8 matrix:** a Wi-Fi glyph, a client indicator, an upload
  bar, and a tick or cross for verify, at a small fixed current.
- **Exit:** reboot, from the page, the module's power toggle, or about 5
  minutes with no client.

## Security

WPA2-PSK, SSID `Woody-XXXX` from the MAC address. A per-unit random password
is made at first boot, kept in NVS, and scrolled on the matrix while RT1 is
held in configuration mode. Signed images
(`CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT`) are possible. For a one-person
instrument the recommendation is to skip them and rely on WPA2 and the image's
own SHA-256.

## OTA and rollback

- Two app slots on the Matrix's 4 MB flash `[repo ADR 0007]`, about 1.9 MB
  each `[calc]`. An ESP-IDF app with Wi-Fi and an HTTP server is about
  1.0–1.3 MB `[from memory]`, to be measured at the first build.
- `CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE`. **A new image boots first into
  configuration mode**, and is marked valid only when the phone reconnects and
  confirms within a few minutes. Otherwise it reboots unmarked and is rolled
  back. This validates the one path that can fix everything else, which
  matters more now that every wired rung needs the lid off. Play mode then runs
  its own self-test: the chain marker, the ADC rest count, and DAC frames. The
  bootloader is never updated over the air.

## Power

- ESP32-S3 TX peak: 340 mA at 802.11b, 1 Mbps, 21 dBm, and 283–291 mA in
  g and n `[ds logic/ESP32-S3-datasheet-v2.2.pdf p.66]`.
- 5 V rail: ADR 0005's quiescent row (an upper bound, display board included)
  plus 340 mA gives about 520 mA peak, against `U-BUCK`'s 1 A `[repo ADR 0005]`.
- Umbilical: +340 × 5 / (0.9 × 11.4) ≈ 166 mA `[calc]` on the quiescent row,
  about 378 mA peak, against the module's 1.0 A limit.
- The Matrix's 3V3 LDO: ME6217C33M5G, ~250–500 mA after derating
  `[repo figures.yaml matrix-led-current]`. The stock Matrix runs Wi-Fi on USB
  power `[from memory]`. Capping TX power lowers the peak.
- **Verdict:** configuration mode on umbilical power alone is fine. E6 should
  confirm it during an upload.
