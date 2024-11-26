## Hardware -- Electronics Box Setup

We will now build the entire autopilot electronics box.


### Necessary Parts & Tools

Round up the following components/tools to aid in the installation:

1. [Raspberry Pi 5](https://www.ebay.com/itm/116326708617) running [Raspberry Pi OS (64-bit) Debian 12 (bookworm)](https://www.raspberrypi.com/software/operating-systems/). Pro tip: purchase your Pi from Fun and Tech (eBay store linked) with a sweet external antenna mod.
2. [Flight Controller](https://irlock.com/products/cube-orange-plus-standard-set) -- Cube Orange officially supported
3. [OxChief Autopilot Adapter Set](https://shop.oxchief.com/products/oxchief-raspberry-pi-to-cube-autopilot-adapter-set) -- OxChief will use these adapters for communicating between the Raspberry Pi and the Cube autopilot.
4. [SD card for Pi](https://www.amazon.com/dp/B09WB1857W/) -- [endurance card](https://www.reddit.com/r/raspberry_pi/comments/xnkp71/reliability_of_microsd_endurance_cards_compared_w/) such as Samsung Pro Endurance 128 GB suggested
5. [High precision GNSS (i.e. "GPS") receiver and antenna](https://www.ardusimple.com/product/simplertk2b-basic-starter-kit-ip65/) -- u-blox ZED-F9P officially supported. Go for the ArduSimple module unless you have a compelling reason not to.
6. RM3100 external compass (available [here](https://www.getfpv.com/mateksys-ap-periph-can-magnetometer-rm3100.html) or [here](https://www.readymaderc.com/products/details/matek-ap-periph-can-magnetometer-rm3100))

7. [Enclosure](https://www.mouser.com/ProductDetail/Bud-Industries/AN-2823-A?qs=9qK3lZr%252bi0IAMON5kROY8A%3D%3D&utm_source=eciaauthorized&utm_medium=aggregator&utm_campaign=AN-2823-A&utm_term=AN-2823-A&utm_content=Bud-Industries) and [mounting plate](https://www.mouser.com/ProductDetail/Bud-Industries/ANX-91323?qs=hFSnKGZfZOZx7rEIKm0bLw%3D%3D&srsltid=AfmBOoqlWkqIRY1h3ukVxc1DUnCHEwVaUu-2IeonACblg8pWwADdTx2T) for electronics box on mower. If tempted to go with a cheap plastic enclsoure, keep in mind that aluminum dissipates heat much more effectively.

8. [4-to-1 USB Hub](https://www.amazon.com/dp/B00XMD7KPU) for extra USB devices you'll be connecting to the Raspberry Pi
9. [Heat-shrink solder](https://www.amazon.com/s?k=heat+shrink+solder) connections
10. Rubber grommets like [these](https://www.amazon.com/dp/B0B5VYYSCM/)
11. [Velcro squares](https://www.amazon.com/dp/B099RXQYFK)
12. 90 degree conduit connector like [this](https://www.amazon.com/dp/B09NNDG19Z) (may want to purchase the kit as you'll need conduit/straight adapter later)
13. Nylon standoffs like [these](https://www.amazon.com/dp/B0BN8RP7N8/)
14. [RealSense D435f](https://www.intelrealsense.com/depth-camera-d435f/)
15. 1 1/16" hole cutting [saw](https://www.amazon.com/dp/B08H78DQQ8/) or [bit](https://www.amazon.com/dp/B00AYZ3396/)
16. [Stepped drill bit](https://www.amazon.com/s?k=1+3%2F8+titanium+drill+bit+stepped)
17. [12v DC to USB-C](https://www.amazon.com/dp/B0CRVVWL4Y/) for Pi power
18. XT60 connectors like [these](https://www.amazon.com/dp/B0B4H5CCR3)
19. Heat shrink solder like [this](https://www.amazon.com/dp/B0BKSJQC9Q)
20. Drill
21. Electrical tape
22. (Optional) [Cutting fluid](https://www.amazon.com/dp/B00065VEP4/)
23. (Optional) [Pi Active Cooler](https://www.amazon.com/dp/B0CLXZBR5P/)
24. (Optional) [12v XT60 power supply](https://www.amazon.com/s?k=12v+xt60+power+supply)
25. (Optional) [XT60 splitter](https://www.amazon.com/s?k=xt60+splitter)


### Prepare Box
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
    - Power/signal cable between the compass in the obstacle enclosure and the autopilot
    in the electronics box
    - GNSS antenna cable
    - Optional: Raspberry Pi Wifi antenna cable
- The second hole is on the right side.  It should be roughly 1 3/16". We will fit it with a rubber grommet.
- The third hole is on the left side. It should be roughly 1 3/16". This hole is for the servo signal wires and the USB-C cable connecting your Raspberry Pi to your phone (for hotspot tethering). After drilling the hole, you will want to fit in a rubber grommet to protect the wires.


### Add Electronics to Box

- Start with prepped empty box
![](images/electronics_box/drilling/10-Finished-Enclosure.jpg)

- Fresh mounting plate ![Base Plate](images/electronics_box/2-Base-Plate.jpg)

- Prepped mounting plate. 35mm nylon standoffs are for your Raspberry Pi -- mount them bottom/center as shown. 15mm nylon standoffs are for the ArduSimple u-blox gnss receiver -- they are on the bottom right. Velcro squares on the left for autopilot. Velcro on upper right for USB hub. Electrical tape to ensure OxChief USB adapters don't arc on the mounting plate.  ![Prepped Base Plate](images/electronics_box/3-Base-Plate-Prepped.jpg)

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

- Locate ArduSimple GNSS receiver and a couple of nylon standoffs ![ArduSimple GNSS](images/electronics_box/12-ArduSimple-GNSS.jpg)

- Mount ArduSimple GNSS receiver in the electronics box with the nylon standoffs ![ArduSimple Mounted](images/electronics_box/13-ArduSimple-Mounted.jpg)

- Locate u-blox gnss antenna ![u-blox Antenna](images/electronics_box/14-u-blox-antenna.jpg)

- Connect u-blox antenna to ArduSimple GNSS receiver ![u-blox Antenna Connected](images/electronics_box/15-u-blox-antenna-connected.jpg)

- Locate Cube GPS1 Cable ![ArduSimple to Cube 1](images/electronics_box/16-1-ArduSimple-Cube.jpg)

- For a cleaner looking box, we tape up the 4p connector and safety switch. You won't use the 4p connector. We don't use the safety switch, but you should use it unless you understand the implications of not using it. ![ArduSimple to Cube 2](images/electronics_box/16-2-ArduSimple-Cube.jpg) ![ArduSimple to Cube 3](images/electronics_box/16-3-ArduSimple-to-Cube.jpg) ![Cube GPS1 Cable](images/electronics_box/16-4-Cube-GPS1-Cable.jpg)

- Connect GPS1 cable from the Cube autopilot to the ArduSimple GNSS receiver ![Cube GPS1 to Receiver](images/electronics_box/17-Cube-GPS1-to-Receiver.jpg)

- Locate a USB-A to Micro-USB cable ![USB-A to Micro-USB](images/electronics_box/18-USB-A-to-Micro-USB.jpg)

- Connect USB-A end to USB hub and the Micro-USB end to ArduSimple ![Micro-USB Connected](images/electronics_box/19-Micro-Connected.jpg)

- Locate Cube power module. Power cable will connect to Cube POWER1 port ![Power Module](images/electronics_box/20-Power-Module.jpg)

- Locate a 12v XT60 power supply. Alternatively, make some like these below by soldering XT60 pigtail to a 12V source. ![Power Supply XT60](images/electronics_box/21-Power-Supply-XT60.jpg)

- Connect the power supply to the power module ![Power Supply to Power Module](images/electronics_box/22-Power-Supply-Power-Module.jpg)

- Connect the power module to the Cube autopilot ![Power Module to Cube](images/electronics_box/23-Power-Module-Cube.jpg)

- Power on the system to verify connections. Cube and ArduSimple should power on. Power system back off. ![Power On](images/electronics_box/24-Power-On.jpg)

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