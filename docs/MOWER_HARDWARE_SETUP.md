## OxChief Mower Wiring Setup

### Parts List

| # | Part | Notes |
|---:|---|---|
| 1 | [OxChief Alpha Servo Bolt-On Servo Assembly](https://shop.oxchief.com/products/oxchief-alpha-bolt-on-servo-assembly) | Plug+play servo assembly for mower |
| 2 | [12 AWG red/black wire](https://www.amazon.com/dp/B08MF7BN8H) | Main power lines for battery + - . |
| 3 | [Wire stripper tool](https://www.amazon.com/dp/B000JNNWQ2) | Wire insulation removal for terminations. |
| 4 | [Heat-shrink solder](https://www.amazon.com/dp/B0BKSJQC9Q) | For robust, insulated splices. |
| 5 | [Heat-shrink ring connector / crimper tool set](https://www.amazon.com/dp/B0B27L5TVM) | Crimp and seal ring terminals for battery/relay connections. |
| 5 | [XT60 connectors](https://www.amazon.com/dp/B0B4H5CCR3) | Power connectors — order extra; longer pigtails (e.g. https://www.amazon.com/dp/B07C5J43ZL) are useful. |
| 6 | [XT60 splitters](https://www.amazon.com/dp/B0754JKHWW) | For splitting a single XT60 feed to multiple devices (or make your own). |
| 7 | [12V → 5V 5A USB-C step-down converter](https://www.amazon.com/dp/B0CRVW7N2J) | Power Raspberry Pi; solder on XT60 pigtail for easy connect/disconnect. |
| 9 | [On/off toggle switch](https://www.amazon.com/dp/B01IYKSLCG/) | Power control for main electronics box.|
| 10 | [Cube power cable / power module](https://holybro.com/products/pm02-v3-12s-power-module) | If not included with your Cube Orange. |
| 11 | [22 AWG wire](https://www.amazon.com/dp/B07TX6BX47) | Signal wiring (telemetry, switches, etc.). |
| 12 | [10 AWG inline ATC fuse holder + 40A fuse](https://www.amazon.com/dp/B0BRPW9KJ5) | Main battery fuse — bolt to battery + terminal. |
| 13 | [Heat gun](https://www.amazon.com/dp/B004NDX7O6) | For heat-shrink application. |



### Watch: Installation Video
Check out the video for detailed instructions. The video is specifically for the OxChief R/C system, but the servo mounting process is the same.

Watch the servo linkage install video

Or view on YouTube: https://www.youtube.com/watch?v=iwFl5_PJkDQ

### Setting up for Robotics Glory

The main electronics box holds the Cube Orange Flight Controller, the Raspberry Pi, and the GNSS receiver. We want to mount this box where the battery is originally installed. We'll move a few other components around and add a few new pieces.

You may observe that we make liberal use of XT60 connectors in our installation. These connectors are robust, dependable, and user-friendly. The more XT60 connectors you add in-line between your electronic components, the easier it will be when you need to replace one. You want to make as many components plug-and-play as possible, and you can largely achive this by going crazy with XT60 connectors and heat shrink solder. You'll likely want to either make or purchase some XT60 splitters as well.

Follow these steps to get rolling:

1. Loosen the bolts holding the fuel selector valve. We will move the mounting location of this valve approximately 4 inches to the right. This makes room for the battery's new installation location.
2. Move the battery (beneath the seat) from it's original location in front of the metal crossmember bar/seat spring mount to behind the crossmember bar. We will install the autopilot electronics box in the original battery location.
2. Crimp a ring connector to one end of the inline fuse. This ring should be big enough to bolt the fuse onto the positive battery terminal. 
2. Use heat-shrink solder to connect an approximately 24" section of 12 gauge red cable to the other end of the inline fuse / ring connector. The entire fused cable should be long enough to comfortably reach from the positive battery terminal over to the 2 relays we will install on the right side of the mower.
2. Use heat-shrink solder to connect the inline fuse cable (created above) to the battery (+) VCC wires on the two relays. To be clear, we want the battery (+) wire on both of these relays wound together and then heat-shrink soldered to the fused power cable.

6. (Optional) Tap in a ground bolt to the metal pan beneath the relay plate to keep your ground wires short and clean. To be clear, we just drill a hole and tap the hole with threads -- then we attach the new ground wires to this bolt.
6. Install an on-off toggle switch for the main electronics box power. We like to install this switch behind the seat.
8. Make a 12 AWG red/black power line with XT60 ends (of course) long enough to neatly run from the 12v main electronics relay into the electronics box. Connect this wire to the main electronics relay.
8. Make a 12 AWG red/black power line with XT60 ends long enough to neatly run from the 12-24v step-up converter relay up to the Wingxine servos.
8. Install a XT60 splitter on the Wingxine servo end of the 12-24v step-up converter power line. You're probably going to want to be careful to ensure that you've got 24v positive and negative on red and black (per convention) wires up at the servo box BEFORE connecting these wires to the servos. The Wingxine servos are explicility non-tolerant of reverse polarity errors.

9. (Optional) bolt on a [NOCO permanent charging adapter](https://www.amazon.com/NOCO-GC002-Eyelet-Terminal-Connector/dp/B004LWQ35Y/) to the battery. You may find this
adapter quite conventient for hooking up a [NOCO charger](https://www.amazon.com/NOCO-GENIUS10-Fully-Automatic-Temperature-Compensation/dp/B07W3QT226/) to your mower. I
often leave the OxChief autopilot powered on when the mower is not in use -- the NOCO
charger ensures that the battery stays fully charged and ready for the next run.

Congratulations! You've now successfully installed the all electrical wiring we need to power the OxChief autopilot system.