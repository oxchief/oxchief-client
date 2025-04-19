![OxChief Experimental Image](docs/images/oxchief-experimental.png "OxChief Experimental")

Robot client for [OxChief](https://oxchief.com/) autonomous mower platform.

> :warning: **WARNING: OxChief is experimental software**: it should not be used where it could be in control of human safety. It should not be in control of the safety of anything that you don't want destroyed. It will make unepexected mistakes. It will behave in unexpected ways. Use at your own risk.

## Motivation
Everyone should own at least one autonomous zero-turn mower. OxChief's mission is to make your mower autonomous with 10x less effort.

## Overview -- 50,000 feet

In 2015 when we began working on the Autonomous Mowing problem, when you mentioned that one day every mower would have autopilot, you were usually met with skepticism. Nearly 10 years later, little skepticism remains, but often an opposite reaction: "what has taken so long?"

In 2019 we [gave an overview](https://deepsouthrobotics.com/2019/08/23/anatomy-of-a-huge-self-driving-mower/) of how to install an autopilot on a commercial zero-turn mower. After writing the article, it was clear that there were still too many hurdles to quickly get autopilot on a mower. These include:
1. Intuitive mowing control
2. Simple path planning
3. Legit servo solution
4. Robust obstacle detection
5. Clear detailed instructions

OxChief is the product of a decade's work to solve this problem. We define a specific set of [hardware](https://shop.oxchief.com)/[software](https://oxchief.com) components for 1 specific mower platform (i.e. Bad Boy [Maverick HD](https://badboycountry.com/mowers/maverick-hd) and [Maverick](https://badboycountry.com/mowers/maverick) so that anyone running OxChief will have repeatable results.

Follow this guide and you will have an autonomous zero-turn mower very soon.

## Overview -- 5,000 feet

### Intuitive Mowing Control
Autonomous mowing should be absurdly simple. The endgame is this: you click Start and your mower mows until your yard (or 100 acre sod farm) is entirely mowed without any intervention. Of course, it takes a fair bit of engineering to get to that utopia. OxChief provides intuitive software that makes autonomus mowing this simple.

### Simple Path Planing
We should be able to easily define our mowing mission. We want to be able to run routes spanning dozens (or even hundreds) of acres without interruption. OxChief makes defining (and updating) your mower's path super easy.

### Legit Servo Solution
We strongly believe that the factory control levers on an autonomous zero-turn mower should retain their original function. In other words, the left and right control arms should continue to control the left and right wheels as you would expect. This means that the servos used to control the robot should actuate the control arms back and forth. These servos should be robust and easily adjustable to get the steering precisely right. We're happy to offer an in-house designed & fabricated [servo assembly](https://shop.oxchief.com/products/oxchief-alpha-bolt-on-servo-assembly) that's engineered specifically for your Bad Boy Maverick HD mower running OxChief.

### Robust Obstacle Detection
Adding obstacle detection to your autonomous mower pays immediate dividends in safety and peace-of-mind. OxChief offers an in-house designed & fabricated [obstacle sensor enclosure](https://shop.oxchief.com/products/oxchief-realsense-mount-for-bad-boy-maverick-hd) built for the Intel RealSense D435f camera that's designed to mount on the front of your Maverick HD in less than 15 minutes. On the software side we provide everything you need to set the RealSense camera up as an obstacle sensor for your robot.

### Clear Detailed Instructions
Since your mower was not shipped with autopilot, we'll need to grab a few tools and connect a few wires to get it properly equipped. OxChief is obsessed with making the process of equipping your mower with autopilot as clear and straightforward as possible. 

## Getting Started
OxChief supports 1 mower platform: the [Bad Boy Maverick HD](https://badboycountry.com/mowers/maverick-hd) 60.

More than once I've wondered if some prescient engineer at Bad Boy built the Maverick HD with a notion of creating an ideal autopilot mower platform. The Maverick HD's autopilot friendly features include:

- ample conspicuous dead space beneath the seat platform allowing seamless install of autopilot electronics and servo linkage assembly
- category busting 13 gallon fuel capacity allowing dawn-to-dusk cross-country autonomous missions
- ideal installation point up front for obstacle sensor

Additonally, the Bad Boy Maverick HD is priced so aggressively relative to other commercial mowers, that you can effectively purchase the mower, equip it with OxChief autopilot, and you still haven't spent the cash you'd have to lay down from a comparable commercial mower from several of the legacy zero-turn manufacturers.

Don't take our word for it -- find your local Bad Boy dealer and check out their mowers. 

Pay attention to the following, in particular:

- they're equipped with Hydro-Gear hydros (and Parker motors in the split systems)
- they've got all the familiar brand engines
- the mowing deck steel is absurdly thick 
- they roll Donaldson canister filters
- the suspension seat is first-class
- they're built like a tank

We've cut thousands of acres with other brands -- the Maverick HD's cut meets or exceeds any we've seen.

Once you've secured your mower, simply follow the installation guides below to equip your mower with OxChief autopilot:

1. Follow the [Electronics Box Setup](docs/ELECTRONICS_BOX_SETUP.md) guide to build your main autopilot electronics box.
2. Follow the [Mower Wiring Setup](docs/MOWER_WIRING_SETUP.md) to prep/wire up your mower for autopilot.
3. Follow the [OxChief Servo Assembly Installation](docs/SERVO_LINKAGE_MOUNT_SETUP.md) guide to mount the servos on your mower.
4. Follow the [Obstacle Detection Setup](docs/OBSTACLE_DETECTION_SETUP.md) guide to add obstacle detection to your mower.
5. Follow the [OxChief Mower Client Setup](docs/OXCHIEF_MOWER_CLIENT_SETUP.md) guide to set up the OxChief client on your mower.
6. Follow the [OxChief Base Station Setup](docs/OXCHIEF_BASE_STATION_SETUP.md) guide to set up your GNSS base station.
7. Follow the [OxChief Mowing Planner](docs/OXCHIEF_MOWING_PLANNER.md) guide to set up your first mowing plan.

Review the [OxChief Features](docs/OXCHIEF_FEATURES.md) guide for an overview of the OxChief UI's features.

Please feel free to hit [OxChief Reddit](https://www.reddit.com/r/OxChief/) with any questions.
