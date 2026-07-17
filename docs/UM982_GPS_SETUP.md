## OxChief GNSS Setup — Unicore UM982 (recommended)

The UM982 is the **recommended GNSS receiver** for OxChief. It is a single
dual-antenna RTK receiver that computes a true **GPS heading** from its two
antennas — so the mower does not depend on a magnetic compass.

> Why this matters: a zero-turn mower is a large steel machine surrounded by
> motors and current. A magnetometer on that frame is unreliable, and bad
> heading is the most common cause of a mower that wanders or won't track a
> straight line. The UM982 gets heading from the two GPS antennas instead, so
> there is **no compass to calibrate and nothing magnetic to fool it**.

This guide is the GNSS section of the build. The legacy single-antenna u-blox
ZED-F9P path still works and is documented in the photo walkthrough in
[Electronics Box Setup](ELECTRONICS_BOX_SETUP.md); new builds should use the
UM982.

### Parts

| Part | Notes |
|---|---|
| Unicore UM982 dual-antenna RTK receiver + 2 antennas | A UM982 board with two antenna connectors (ANT1 = position, ANT2 = heading). Most UM982 kits ship with both antennas. The UM980 does position but not heading — get the UM982. |
| OxChief `_OxRTCM` USB-to-serial adapter | Carries RTK corrections from the Pi into the UM982 (RX2 pin on the UART2/COM2 connector — see Wiring below). |

**Where to buy:** the [Holybro H-RTK Unicore UM982 (Dual Antenna Heading)](https://holybro.com/products/h-rtk-unicore-um982) (~$250, includes both helical antennas and cables) is a turnkey, ArduPilot-ready option. On a budget, a generic "UM982 + 2-antenna kit" on AliExpress runs ~$130 (search *"UM982 dual antenna RTK kit"*) — same receiver, lower-grade antennas. Either way, mount the two antennas with a fixed separation (the "baseline"); a longer baseline gives more precise heading (~0.5 m+ is typical on a mower).

### Wiring

Three connections. The table below uses the connector names printed on the
Holybro unit; the UM982 datasheet calls these same ports COM1/COM2/COM3, so
both names are listed. (On a generic UM982 board, match by COM number.)

| Connector on the receiver | UM982 port name | Connects to | Carries |
|---|---|---|---|
| **UART1** (10-pin) | COM1 | Cube **GPS1** port | Position + heading to the Cube; 5V power back to the receiver |
| **UART2** (6-pin) | COM2 | `_OxRTCM` USB-serial adapter | RTK corrections in from the Pi |
| **USB-C** | COM3 | Pi USB | Setup script only (one time) |

In detail:

1. **Navigation (UM982 → flight controller):** plug the 10-pin **UART1** cable
   into the Cube's **GPS1** port (ArduPilot `SERIAL3`). The UM982 sends NMEA —
   including the dual-antenna heading — to the Cube here. This is the full
   cable that ships with the Holybro unit; use it as-is.
2. **Corrections (Pi → UM982):** the `_OxRTCM` USB-serial adapter's signal
   wire (the adapter's TX) goes to the **RX2 pin** on the 6-pin **UART2**
   connector, and its ground wire to the **GND pin** on that same connector.
   **Leave UART2's 5V pin unconnected** — the adapter is powered by the Pi
   over USB. No receiver configuration is needed for this link: the UM982
   accepts RTCM3 corrections on any port automatically, and the setup script
   below sets the port baud to match the client (230400).
3. **Configuration (UM982 → Pi, one time):** connect the **USB-C** port to the
   Pi while you run the setup step below, then unplug it. Generic UM982 boards
   show up as a CH340 (USB `1a86`); the Holybro H-RTK Unicore UM982 presents
   its USB-C config port as an FTDI device (USB `0403`). The setup script
   auto-detects both.

**How everything gets power:** the PM02 power module powers the *Cube* — mower
battery → PM02 → Cube **POWER1** port (this is also how the Cube measures
battery voltage/current; see [Electronics Box Setup](ELECTRONICS_BOX_SETUP.md)).
The UM982 then draws its 5V *from the Cube* through the UART1/GPS1 cable. The
receiver is only USB-powered while it's plugged into the Pi for the one-time
setup step — on the mower it runs off the Cube, and the USB-C port stays
unplugged.

Mount the two antennas with a clear sky view on a **rigid, fixed baseline**. ANT1
is the master (position) antenna and ANT2 is the slave (heading) antenna — heading
is the bearing from ANT1 → ANT2, so mount ANT1 forward and ANT2 directly behind it
along the mower's centerline. Keep them at least 30 cm apart; ~1 m gives
sub-degree heading (0.5 m is decent, 0.3 m is noisy), so spread them as far as the
frame allows. **Swapping the two antenna cables flips the heading 180°.** If you
can't mount them front-to-back, use the `--heading-offset` option below.

### 1. Configure the UM982 receiver

With the UM982's USB connected to the Pi (and the OxChief client **not** running,
so the GPS port is free), from the cloned repo on the Pi:

```
pip3 install pyserial   # if not already present
python3 scripts/configure_um982.py
```

This puts the receiver in **MODE ROVER**, sets the COM ports to 230400 baud,
enables the NMEA sentences ArduPilot needs on COM1 (including the
`UNIHEADINGA`/`GPHDT` heading sentences), and `SAVECONFIG`s so it sticks. Run
`python3 scripts/configure_um982.py --verify-only` to check it afterward.

> **About heading:** dual-antenna heading is **on by default** on the UM982 — the
> command above (MODE ROVER + enabling `UNIHEADINGA`/`GPHDT` + `SAVECONFIG`) is all
> that's required to get heading out; there is no separate "enable heading" step.
> Heading also works **without** RTK corrections (RTK is only for cm-level
> position). Two optional tweaks for your specific mount:
> - `--baseline-cm <cm>`: your measured ANT1↔ANT2 spacing (e.g. `--baseline-cm 100`
>   for 1 m) — speeds up and stabilizes the first heading fix.
> - `--heading-offset <deg>`: use if the antenna line isn't along the mower's
>   forward axis, e.g. `--heading-offset 90` for antennas mounted left-right with
>   ANT1 on the right.
>
> Example: `python3 scripts/configure_um982.py --baseline-cm 100`

### 2. Load the UM982 ArduPilot parameters

In Mission Planner: **Config → Full Parameter Tree → Load from file → Write
Params**, using:

```
cfg/OxChief_Cube_Orange_Bad_Boy_UM982.param
```

Versus the legacy F9P param file, this set: takes GPS heading instead of compass
(`EK3_SRC1_YAW=2`), **disables the compass** (`COMPASS_ENABLE=0`, `COMPASS_USE=0`,
`COMPASS_DISBLMSK=65535`), and runs GPS1 at 230400 (`SERIAL3_BAUD=230`).

Then calibrate the accelerometers ([guide](https://ardupilot.org/rover/docs/common-accelerometer-calibration.html)).
**Skip the Large-Vehicle MagCal compass step** — there is no compass in this setup.

> The GPS antenna lever-arm offsets (`GPS_POS1_*`, `GPS_POS2_*`) in the param file
> are example values. Measure your own antenna positions (body frame, meters from
> the autopilot: X forward, Y right, Z down) and set them for best accuracy.

### 3. Set the corrections baud

The repo `config.ini` already ships `gnss_rtcm_baud=230400` for the UM982. If you
are upgrading from an F9P build, confirm it reads 230400 (not 115200).

### Base station — you can reuse a u-blox ZED-F9P

RTK corrections are a standard format (RTCM3), so your base station does **not**
have to match the rover. If you already own a u-blox ZED-F9P / ArduSimple kit, it
makes a perfectly good base for a UM982 rover — see
[Base Station Setup](OXCHIEF_BASE_STATION_SETUP.md). Configure the F9P base to
emit the standard set — `1005` (base position), MSM4 `1074/1084/1094/1124`, and
`1230` (GLONASS biases, which matter in a mixed-vendor base/rover pair) — and
survey-in its position. A UM982 base works too.
