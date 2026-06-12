## [1.1.1] - 2026-06-12
### Fixed
- `scripts/configure_um982.py` auto-detection now matches the Holybro H-RTK
  Unicore UM982. Its USB-C config port enumerates as an FTDI device (USB `0403`),
  but the script only accepted the CH340 (`1a86`) used by generic UM982 boards, so
  it reported "could not find a UM982" on a connected Holybro unit. Both vendor
  IDs are now accepted; when more than one candidate port matches, each is probed
  at the UM982 baud rates instead of guessing. The `--port` override is unchanged.
  `docs/UM982_GPS_SETUP.md` updated to note Holybro presents as FTDI.

## [1.1.0] - 2026-05-30
### Added
- Unicore UM982 dual-antenna GNSS support (now the recommended receiver). The
  UM982 provides true GPS heading from its two antennas, so the mower no longer
  depends on a magnetic compass (unreliable on a steel zero-turn). New files:
  `cfg/OxChief_Cube_Orange_Bad_Boy_UM982.param` (GPS-yaw, compass disabled, GPS1
  at 230400) and `scripts/configure_um982.py` (one-time receiver provisioning:
  MODE ROVER, COM baud, NMEA/heading output, SAVECONFIG; optional
  `--baseline-cm` / `--heading-offset` to tune dual-antenna heading for the
  mount). New guide `docs/UM982_GPS_SETUP.md` — documents that dual-antenna
  heading is on by default, antenna placement (ANT1 forward, >=30cm / ~1m
  baseline, swapping cables flips heading 180deg), and that heading works
  without RTK. Mower-client / electronics-box / base-station docs updated to
  point at the UM982 path (F9P kept as the documented legacy option).
### Changed
- `config.ini` / `src/config.ini`: `gnss_rtcm_baud` default 115200 -> 230400 to
  match the UM982. Legacy u-blox ZED-F9P builds should set this back to 115200.
### Notes
- No client code changed: the GNSS data path is receiver-agnostic (raw RTCM3
  written over serial), so this release is parameters + config + docs + a setup
  script. A u-blox ZED-F9P base station feeds a UM982 rover fine — RTCM3 is a
  cross-vendor standard.

## [1.0.6] - 2026-05-29
### Changed
- Flight-controller startup no longer fails silently. When the FC telem ports
  (`_OxTelem1`/`_OxTelem2`) are missing/miswired, or the FC isn't responding
  (no power / wrong baud), the client now logs a loud, actionable WARNING every
  ~15s naming the exact problem instead of looping quietly forever. The MAVLink
  heartbeat wait is now bounded (10s) and self-heals when the FC starts
  responding. (The robot still requires the FC to come online; this only makes a
  stuck startup diagnosable.)
- Guard `close_ublox_serial_port()` against a None port (avoids a spurious
  AttributeError/warning during corrections-port recovery).
- Align `src/config.ini` `gnss_rtcm_serial_name_substring` to `_OxRTCM` to match
  the repo-root `config.ini` (the value used at runtime), so a run without the
  config bind-mount behaves the same.

## [1.0.5] - 2026-05-29
### Fixed
- Robot no longer fails to come online when the GNSS corrections serial device
  (gnss_rtcm_serial_name_substring, e.g. _OxRTCM) is absent. That port is now
  acquired in a background task instead of blocking client startup, so the
  cloud websocket connection (and thus "online" status) no longer depends on
  having an RTK-corrections receiver attached. RTCM messages are dropped until
  the device appears; telemetry and control are unaffected.

## [1.0.4] - 2025-04-19
### Update
- Default to OxRTCM serial USB-UART conector for sending RTCM corrections to u-blox.

## [1.0.3] - 2025-02-05
### Fixed
- Joystick control grey out bug -- read default servo trim from Flight Controller

## [1.0.0] - 2024-11-26
### Added
- Initial release