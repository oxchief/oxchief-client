## OxChief Electronics Box Setup

> **GNSS receiver:** this build uses the **Holybro H-RTK Unicore UM982** — a dual-antenna RTK receiver with true GPS heading and no compass. Receiver wiring and the one-time configuration are in [UM982 GNSS Setup](UM982_GPS_SETUP.md). A few photos in the GNSS step below still show the older single-antenna u-blox ZED-F9P (ArduSimple), which remains a legacy alternative; everything else in the box build (Pi, Cube, power, RealSense) is identical either way.

### Parts List

| # | Part | Description / Notes |
|---:|---|---|
| 1 | [Raspberry Pi 5](https://www.ebay.com/itm/116326708617) | Raspberry Pi OS (64-bit). The linked part is from Fun and Tech (eBay) with external antenna mod. |
| 2 | [Flight Controller — Cube Orange](https://irlock.com/products/cube-orange-plus-standard-set) | Officially supported. |
| 3 | [OxChief Autopilot Adapter Set](https://shop.oxchief.com/products/oxchief-raspberry-pi-to-cube-autopilot-adapter-set) | Adapter for Pi ↔ Cube communication. |
| 4 | [SD card for Pi — Samsung Pro Endurance 128GB](https://www.amazon.com/dp/B09WB1857W/) | Endurance microSD recommended. |
| 5 | [Holybro H-RTK Unicore UM982](https://holybro.com/products/h-rtk-unicore-um982) | **Recommended GNSS receiver** — dual-antenna RTK with true GPS heading, no compass. Includes 2 helical antennas + cables. Setup: [UM982 GNSS Setup](UM982_GPS_SETUP.md). Legacy alternative: single-antenna [ArduSimple SimpleRTK2B / u-blox ZED-F9P](https://www.ardusimple.com/product/simplertk2b-basic-starter-kit-ip65/). |
| 6 | [RM3100 magnetometer](https://www.getfpv.com/mateksys-ap-periph-can-magnetometer-rm3100.html) | External compass — **only for the legacy ZED-F9P build**. Not used with the UM982 (heading comes from the dual GPS antennas; the compass is disabled). |
| 7 | [Aluminum enclosure — Bud AN-2823-A](https://www.mouser.com/ProductDetail/Bud-Industries/AN-2823-A?qs=9qK3lZr%252bi0IAMON5kROY8A%3D%3D) and [mounting plate — Bud ANX-91323](https://www.mouser.com/ProductDetail/Bud-Industries/ANX-91323?qs=hFSnKGZfZOZx7rEIKm0bLw%3D%3D) | Aluminum recommended for heat dissipation. |
| 8 | [4-to-1 USB Hub](https://www.amazon.com/dp/B00XMD7KPU) | For extra devices. |
| 9 | [Heat-shrink solder](https://www.amazon.com/dp/B0BKSJQC9Q) | Heat-shrink solder connections. |
| 10 | [Rubber grommets](https://www.amazon.com/dp/B0B5VYYSCM/) | Protect cable entries. |
| 11 | [Velcro squares](https://www.amazon.com/dp/B099RXQYFK) | Mounting/padding. |
| 12 | [Conduit & connectors](https://www.amazon.com/dp/B09NNDG19Z) | Liquid-tight connection from main electronics box to obstacle sensor box. |
| 13 | [Nylon standoffs](https://www.amazon.com/dp/B0BN8RP7N8/) | For mounting PCBs. |
| 14 | [Intel RealSense D435f](https://store.realsenseai.com/buy-intel-realsense-depth-camera-d435f.html) | Depth camera. |
| 15 | [1 1/16" hole saw / bit](https://www.amazon.com/dp/B08H78DQQ8/) | For conduit connector. |
| 16 | [Stepped drill bit](https://www.amazon.com/s?k=1+3%2F8+titanium+drill+bit+stepped) | For cable holes. |
| 17 | [12V → USB-C converter](https://www.amazon.com/dp/B0CRVVWL4Y/) | Power Raspberry Pi. |
| 18 | [XT60 connectors](https://www.amazon.com/dp/B0B4H5CCR3) | Power connectors. |
| 19 | [Cutting fluid (optional)](https://www.amazon.com/dp/B00065VEP4/) | Helps when drilling metals. |
| 20 | [Pi active cooler (optional)](https://www.amazon.com/dp/B0CLXZBR5P/) | For Raspberry Pi thermal management. |
| 21 | [12V XT60 power supply (optional)](https://www.amazon.com/s?k=12v+xt60+power+supply) | Packaged supply. |
| 22 | [XT60 splitter (optional)](https://www.amazon.com/s?k=xt60+splitter) | For powering multiple XT60 devices. |
| 23 | [Electrical tape](https://www.amazon.com/dp/B001AXD0EY/) | General wiring protection. |
| 24 | Drill | General tooling. |

### Prepare Box

We will now build the entire autopilot electronics box.

We need to drill 3 holes into the short sides of the electronics box.

- Start with your empty electronics enclosure
![Empty Electronics Box](images/electronics_box/1-Empty-Box.jpg)

- Gather a drill, some cutting fluid, and a stepped drill bit.

![](images/electronics_box/1-Drilling-Tools.jpg)

- We want to drill 3 holes: 
    - one exactly 1 1/16" hole on the right side (for conduit connector)
    - one roughly 1 3/16" hole on the right side (for rubber grommet)
    - one roughly 1 3/16" hole on the left side (for rubber grommet)

![](images/electronics_box/drilling/1-Drill-Prep.jpg)
![](images/electronics_box/drilling/2-Punched-Drill-Spots.jpg)
![](images/electronics_box/drilling/3-Drill-Prep.jpg)
![](images/electronics_box/drilling/4-Drill-Prep.jpg)
![](images/electronics_box/drilling/5-32_5mm-From-Top.jpg)
![](images/electronics_box/drilling/6-58mm-From-Side.jpg)
![](images/electronics_box/drilling/7-Bits-Finished-1.jpg)
![](images/electronics_box/drilling/8-Bits-Finished-2.jpg)
![](images/electronics_box/drilling/9-Tools-Finished.jpg)
![](images/electronics_box/drilling/10-Finished-Enclosure.jpg)

- The first hole should be exactly 1 1/16" for the 90 degree 3/4" liquid tight connector. We use 3/4" electrical conduit to connect the OxChief Obstacle Enclosure in the front of the mower to the autopilot electronics box under the operator seat. We send the following wires in this conduit tunnel: 
    - USB cable connecting the RealSense obstacle sensor in the front of the mower to the Raspberry Pi in the electronics box
    - GNSS antenna cable(s) — the UM982 uses two antennas for heading; see [UM982 GNSS Setup](UM982_GPS_SETUP.md) for placement
    - Legacy ZED-F9P build only: power/signal cable between the external compass in the obstacle enclosure and the autopilot (the UM982 needs no compass)
    - Optional: Raspberry Pi Wifi antenna cable
- The second hole is on the right side.  It should be roughly 1 3/16". We will fit it with a rubber grommet.
- The third hole is on the left side. It should be roughly 1 3/16". This hole is for the servo signal wires and the USB-C cable connecting your Raspberry Pi to your phone (for hotspot tethering). After drilling the hole, you will want to fit in a rubber grommet to protect the wires.


### Add Electronics to Box

- Start with prepped empty box
![](images/electronics_box/drilling/10-Finished-Enclosure.jpg)

- Fresh mounting plate ![Base Plate](images/electronics_box/2-Base-Plate.jpg)

- Prepped mounting plate. 35mm nylon standoffs are for your Raspberry Pi -- mount them bottom/center as shown. 15mm nylon standoffs are for the GNSS receiver (the Holybro UM982; the legacy ArduSimple mounts the same way) -- they are on the bottom right. Velcro squares on the left for autopilot. Velcro on upper right for USB hub. Electrical tape to ensure OxChief USB adapters don't arc on the mounting plate.  ![Prepped Base Plate](images/electronics_box/3-Base-Plate-Prepped.jpg)

- Mounting plate in electronics box. Go ahead and attach plate to box with a couple of the included screws (not pictured). ![Box With Plate](images/electronics_box/4-Box-With-Plate.jpg)

- Find your Cube Orange autopilot ![Autopilot](images/electronics_box/5a-Autopilot.jpg)

- Remove Velcro backing exposing sticky side on the 4 Velcro squares on the left side of the plate. Mount autopilot on Velcro sqares, ensuring that the arrow in the orange Cube is pointing forward. ![Autopilot](images/electronics_box/5c-Autopilot-Mounted.jpg)

- Push the Cube autopilot down with a fair amount of force so that the Velcro sticky side sticks to your Cube. If you'd like, pull up the Cube and notice Velcro is now affixed to back of Cube. ![Autopilot](images/electronics_box/5b-Autopilot-Velcro.jpg)

- Remove backing from two USB hub Velcro pads on the mounting plate, exposing sticky side. Mount USB hub in electronics box. ![USB Hub](images/electronics_box/6a-USB-Hub.jpg)
- Push the USB hub down with a fair amount of force so that the Velcro sticky side sticks to the hub. If you'd like, pull up the hub and notice Velcro is now affixed to the back of the hub. ![USB Hub Velcro](images/electronics_box/6b-USB-Hub-Velcro.jpg)
- USB Hub mounted in electronics box ![USB Hub Mounted](images/electronics_box/7-USB-Hub-Mounted.jpg)

- Gather the OxChief Raspberry-Pi-to-Cube connectors ![OxChief Raspberry Pi to Cube Adapters](images/electronics_box/8-OxChief-Pi-To-Cube-Adapters.jpg)

- Connect OxChief OxTelem1 connector to Cube TELEM 1 port and USB hub ![Telem 1 to USB](images/electronics_box/9-Telem-1-to-USB.jpg)

- Connect OxChief OxTelem2 connector to Cube TELEM 2 port and USB hub ![Telem 2 to USB](images/electronics_box/10-Telem-2-to-USB.jpg)

- Connect OxChief OxGPS2 connector to Cube GPS 2 port and USB hub ![GPS 2 to USB](images/electronics_box/11-GPS-2-to-USB.jpg)

#### GNSS receiver — Holybro Unicore UM982

OxChief uses the **Holybro H-RTK Unicore UM982** (dual-antenna, GPS heading, no compass). Mount it on the 15mm nylon standoffs (bottom-right of the plate, where the legacy ArduSimple went), then wire and configure it per [UM982 GNSS Setup](UM982_GPS_SETUP.md). In short:

- **UM982 COM1 → Cube GPS1 port** — sends position + heading (NMEA) to the autopilot.
- **OxChief `_OxRTCM` USB-serial adapter → UM982 RX** (via the USB hub) — RTK corrections from the Pi.
- **UM982 USB → USB hub** — used once to run `python3 scripts/configure_um982.py` (MODE ROVER, baud, NMEA/heading output, SAVECONFIG); also powers the module.
- **Two antennas** on a fixed baseline — ANT1 forward (master), ANT2 behind (slave). See [UM982 GNSS Setup](UM982_GPS_SETUP.md) for placement, baseline length, and the 180° heading-flip gotcha.

> **Legacy ZED-F9P build:** the original single-antenna ArduSimple / u-blox install (mount the ArduSimple on the standoffs, connect the u-blox antenna, run the Cube GPS1 cable to it, and a USB-A → Micro-USB to the hub) is no longer the recommended path. The [ArduSimple starter kit](https://www.ardusimple.com/product/simplertk2b-basic-starter-kit-ip65/) connects to Cube GPS1 the same way; load the legacy `.param` file per the [mower-client guide](OXCHIEF_MOWER_CLIENT_SETUP.md). (The original step-by-step photos for this variant were removed when the UM982 became the default.)

- Locate Cube power module. Power cable will connect to Cube POWER1 port ![Power Module](images/electronics_box/20-Power-Module.jpg)

- Locate a 12v XT60 power supply. Alternatively, make some like these below by soldering XT60 pigtail to a 12V source. ![Power Supply XT60](images/electronics_box/21-Power-Supply-XT60.jpg)

- Connect the power supply to the power module ![Power Supply to Power Module](images/electronics_box/22-Power-Supply-Power-Module.jpg)

- Connect the power module to the Cube autopilot ![Power Module to Cube](images/electronics_box/23-Power-Module-Cube.jpg)

- Power on the system to verify connections. Cube and GNSS receiver should power on. Power system back off. ![Power On](images/electronics_box/24-Power-On.jpg)

- Locate your Raspberry Pi 5. Active cooler adorns this one. ![Raspberry Pi with Fan](images/electronics_box/25-Raspberry-Pi-5-With-Fan.jpg)

- Locate a DC power converter (12v to 5v) ![DC Power Converter](images/electronics_box/26-DC-Power-Converter-12v-to-5v.jpg)

- Connect the DC power converter to the Raspberry Pi power adapter ![Pi Power Adapter](images/electronics_box/27-Pi-Power-Adapter.jpg)

- Locate  aXT60 splitter to power 2 XT60 connections from 1 source. Alternatively, make your own, as below. ![XT60 Splitter](images/electronics_box/28-XT60-Splitter.jpg)

- Connect the XT60 splitter to the power supply and the DC power converter. Cube pictured below to be clear about how everything is connected. ![AutoPilot Pi Power Supply 1](images/electronics_box/29-AutoPilot-Pi-Power-Supply-1.jpg)

- Verify all connections and power on the system ![Autopilot Pi Power Supply 2](images/electronics_box/30-AutoPilot-Pi-Power-Supply-2.jpg)

- Mount Raspberry Pi in enclosure. USB hub and RealSense are connected to Pi USB below. ![Raspberry Pi Mounted](images/electronics_box/31-Pi-Mounted.jpg)

- Locate Intel RealSense D435f ![alt text](images/electronics_box/32-RealSense-D435f-1.jpg) ![alt text](images/electronics_box/33-RealSense-D435f-2.jpg) ![alt text](images/electronics_box/34-RealSense-Tripod-USB-3.jpg) 
- Connect Tripod and USB cable. ![alt text](images/electronics_box/35-RealSense-Tripod-USB-Connected-4.jpg)

- Connect RealSense USB to Pi. Ensure RealSense in connected to Pi's blue USB port (USB 3). Connect USB hub to Pi black USB port (USB 2). We want to leave one Pi blue/USB3 port open for tethered cellular data connection later. ![alt text](images/electronics_box/36-Electronics-Box-Complete.jpg)