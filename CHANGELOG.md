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