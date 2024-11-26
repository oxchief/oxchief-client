## Wiring the Mower for OxChief Autopilot

### Necessary Parts & Tools
Round up (or purchase) the following components/tools to aid in the installation:

1. 12 gauge red/black wire like [this](https://www.amazon.com/dp/B08MF7BN8H)
2. Wire stripper tool like [this](https://www.amazon.com/dp/B000JNNWQ2)
3. Heat shrink solder like [this](https://www.amazon.com/dp/B0BKSJQC9Q)
3. Heat shrink ring connector/crimper tool set like [this](https://www.amazon.com/dp/B0B27L5TVM)
4. XT60 connectors like [these](https://www.amazon.com/dp/B0B4H5CCR3). Order twice as many as you think you'll need. The longer pigtails like [these](https://www.amazon.com/dp/B07C5J43ZL) are quite nice for heat-shrink soldering. You may even want to spring for an extra bag of cheaper 14AWG wires like [these](https://www.ebay.com/itm/313849355086) to have laying around.
5. XT60 splitters like [these](https://www.amazon.com/dp/B0754JKHWW). Of course you can make your own with the massive load of XT60 connectors you purchased above.
5. [12v-to-5v-5amp-USB-C step-down converter](https://www.amazon.com/dp/B0CRVW7N2J) for powering the Raspberry Pi. Of course you'll want to solder on a XT60 pigtail to make it pluggable.
6. Two 12v 40a [relays](https://www.amazon.com/dp/B078T8CMF6)
7. Two on/off toggle switches like [these](https://www.amazon.com/dp/B07WW3WW3F)
8. Cube [power cable](https://www.getfpv.com/holybro-pixhawk-pm02-v3-12s-power-module.html) (if not included with your Cube Orange flight controller)
9. 22 awg wire like [this](https://www.amazon.com/dp/B07TX6BX47)
10. 12v-to-24v 20A Step Up Converter like [this](https://www.amazon.com/dp/B081K6PRX3)
11. 10 AWG inline ATC fuse holder with 40 AMP fuse (like [this](https://www.amazon.com/dp/B0BRPW9KJ5)) for main power from the battery +.
12. Heat gun like [this](https://www.amazon.com/dp/B004NDX7O6)

### Setting up for Robotics Glory

The main electronics box holds the Cube Orange Flight Controller, the Raspberry Pi, and the GNSS receiver. We want to mount this box where the battery is originally installed. We'll move a few other components around and add a few new pieces.

You may observe that we make liberal use of XT60 connectors in our installation. These connectors are robust, dependable, and user-friendly. The more XT60 connectors you add in-line between your electronic components, the easier it will be when you need to replace one. You want to make as many components plug-and-play as possible, and you can largely achive this by going crazy with XT60 connectors and heat shrink solder. You'll likely want to either make or purchase some XT60 splitters as well.

Follow these steps to get rolling:

1. Loosen the bolts holding the fuel selector valve. We will move the mounting location of this valve approximately X inches to the right. This makes room for the battery's new installation location.
2. Move the battery (beneath the seat) from it's original location in front of the metal crossmember bar/seat spring mount to behind the crossmember bar. We will install the autopilot electronics box in the original battery location.
2. Crimp a ring connector to one end of the inline fuse. This ring should be big enough to bolt the fuse onto the positive battery terminal. 
2. Use heat-shrink solder to connect an approximately 24" section of 12 gauge red cable to the other end of the inline fuse / ring connector. The entire fused cable should be long enough to comfortably reach from the positive battery terminal over to the 2 relays we will install on the right side of the mower.
2. Use heat-shrink solder to connect the inline fuse cable (created above) to the battery (+) VCC wires on the two relays. To be clear, we want the battery (+) wire on both of these relays wound together and then heat-shrink soldered to the fused power cable.
3. Locate a panel for mounting the 12v-24v power converter and the two relays. The ideal panel is Bad Boy part # 201-0020-00. If possible (this part's availablity is sketchy), you want to purchase this panel and install it on the right side of the mower, benath the right-hand fuel tank cap, bolted to the mower using the two ROPS bar support bolts on the right side of the mower. Note in the pics we just used a random plastic panel laying around the shop.
4. Attach the 12v-to-24v step-up power converter to the panel from above. You will use this 24v supply to power the Wingxine servos. We recommend soldering XT60 connectors to both the 12v supply side and the 24v output side of the step-up power converter.
5. Bolt two relays on the panel.
6. (Optional) Tap in a ground bolt to the metal pan beneath the relay plate to keep your ground wires short and clean. To be clear, we just drill a hole and tap the hole with threads -- then we attach the new ground wires to this bolt.
6. Install an on-off toggle switch for the main electronics box relay. We like to install this switch behind the seat. Run a ground wire through this switch up to one of the relays you installed on the panel.
6. Test that the 12v main electronics box relay works as expected. Should read 12v when switch is on, nothing when switched off.
7. Install another on-off switch for the 12-24v step-up converter relay. We like to install this switch on the main Bad Boy control panel. Run a ground wire through this switch up to the other relay you installed on the panel.
7. Test that the 12-24v step-up converter relay relay works as expected. Should read 12v when switch is on, nothing when switched off.
7. Connect the 12v power out from the 12-24v step-up converter relay to the 12-24v step-up converter.
7. Test that the 12-24v step-up converter works as expected. Should read 24v when switch is on, nothing when switched off.
8. Make a 12 AWG red/black power line with XT60 ends (of course) long enough to neatly run from the 12v main electronics relay into the electronics box. Connect this wire to the main electronics relay.
8. Make a 12 AWG red/black power line with XT60 ends long enough to neatly run from the 12-24v step-up converter relay up to the Wingxine servos.
8. Install a XT60 splitter on the Wingxine servo end of the 12-24v step-up converter power line. You're probably going to want to be careful to ensure that you've got 24v positive and negative on red and black (per convention) wires up at the servo box BEFORE connecting these wires to the servos. The Wingxine servos are explicility non-tolerant of reverse polarity errors.

9. (Optional) bolt on a [NOCO permanent charging adapter](https://www.amazon.com/NOCO-GC002-Eyelet-Terminal-Connector/dp/B004LWQ35Y/) to the battery. You may find this
adapter quite conventient for hooking up a [NOCO charger](https://www.amazon.com/NOCO-GENIUS10-Fully-Automatic-Temperature-Compensation/dp/B07W3QT226/) to your mower. I
often leave the OxChief autopilot powered on when the mower is not in use -- the NOCO
charger ensures that the battery stays fully charged and ready for the next run.

Congratulations! You've now successfully installed the all electrical wiring we need to power the OxChief autopilot system.