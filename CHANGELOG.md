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