## OxChief Obstacle Detection Setup

### Parts List

| # | Part | Notes |
|---:|---|---|
| 1 | [OxChief Obstacle Sensor Mount](https://shop.oxchief.com/products/oxchief-realsense-mount-for-bad-boy-maverick-hd) | Enclosure/mount for placing the RealSense on the front of the mower. |
| 2 | [Intel RealSense D435f](https://realsenseai.com/stereo-depth-with-ir-pass-filter/d435f/) | Depth camera used for obstacle detection. |
| 3 | [Locking USB‑C → USB cable](https://www.amazon.com/dp/B088BCBNGZ) | Secure, screw-locking cable for Pi ↔ RealSense.|
| 4 | [3/4" liquid‑tight conduit kit](https://www.amazon.com/dp/B09NNDG19Z) | Conduit, 90° adapter, straight adapter — weatherproof cable tunnel from obstacle enclosure to main electronics box. |
| 5 | [PVC pipe cutter](https://www.amazon.com/dp/B09BVXZBLN/) | For cutting conduit hose to length. |
| 6 | [Thin braided rope](https://www.amazon.com/dp/B0C9N3NQNY) | Optional. Helps run cords through the conduit between the electronics enclsoures. |
| 6 | Phillips head screwdriver | For removing enclosure screws. |
| 7 | 3/8" socket / wrench | For removing front bumper on the mower. |
| 8 | 7/16" wrench | For bolting RealSense to enclosure. |

### Setting up the Obstacle Sensor
Install the OxChief Obstacle Sensor Mount to the mower:

- Remove the black rubber front bumper from your Bad Boy Maverick HD with a 3/8" socket.

- Install the obstacle sensor mount on the front of the mower, sandwiching it between the black rubber front bumper and the mower, by tightening the 3/8" screws.

Install the RealSense D435f inside the OxChief Obstacle Sensor Mount:

- Open the back of the enclosure by removing the 4 screws on the corners with a Phillips head screwdriver.

- Bolt the sensor to the enclosure, tighten with 7/16" wrench

Finalize the setup:

- Cut a 54" section of 3/4" conduit. This conduit will connect the obstacle sensor mount on the front to the main electronic box beneath the seat. 

- Install a 90 degree conduit elbow fitting on both ends of the 54" section of conduit.

- Cut a 20' (yes, 20 feet) section of the thin braided rope. Run the rope through the conduit, leaving an equal amount of extra rope on either side (approximately 7 feet). If you have trouble running the usb cable through the conduit, you can tape / zip tie it to this rope and pull the cable through the conduit by pulling the rope. You will have several feet of extra rope on other side of the conduit -- fear not, there is ample room in both enclosures for this string.

- Connect conduit to the obstacle sensor enclosure, then route it underneath the floor pan, and under the seat, finally connecting the other end to the main electronics box. 

- Run the locking usb cable from the main electronics box, through the conduit, and into the obstacle sensor enclosure. Connect the locking end to the RealSense and the other end to the Raspberry Pi.