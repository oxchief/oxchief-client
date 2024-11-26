#!/usr/bin/env python3
"""
Author: Wayne Baswell

This is the main script that orchestrates all of our interaction between the 
user and their robot. The script runs in the Raspberry Pi on the robot, 
and is responsible for critical operations such as:
    -maintain websocket/webrtc connections for the OxChief Browser UI
    -monitor the fitness of the autopilot flight controller (i.e. Cube Orange)
    -monitor the mission progress to attempt to ensure it's progressing smoothly
    -create a mavproxy connection with the option to forward telemetry to Hosts
        specified by client -- one benefit of this is that users can monitor
        the robot with Mission Planner using the existing network
        connection without needing an additional
        telemetry connection
    -receive rtcm corrections from server and write to attached gnss device
    -implement effectively unlimited mission waypoint capability by paging large
        missions into the autopilot
    -implement sanity checks to ensure the robot is behaving as expected
"""
import asyncio
import logging
import os
import sys
import time

import eternal_process
import message_processor
import network_util
import robot_state
import serial_util
import util
import waypoint_wizard

from config import Config
from mavlink_util import Mavlink

config = Config()
logging.basicConfig(level=config.log_level)

#uncomment the RPi.GPIO code below if we need to use the GPIO pins for relays, etc --
#an example in the 585 hybrid mower with an electric deck -- the deck is connected
#to a relay that we want to be able to control via the rapsberry pi GPIO pins
#import RPi.GPIO as GPIO
#GPIO.setmode(GPIO.BCM)

if config.enable_python_debug:
    os.environ["PYTHONASYNCIODEBUG"] = "1"
    import debugpy
    debugpy.listen((config.python_debug_ip, config.python_debug_port))
    logging.info("debugging started -- now you should connect your debug client"
                 " while we sleep for 10 seconds")
    time.sleep(10)

network = network_util.Network(config)
serial = serial_util.Serial(config)
the_message_processor = message_processor.MessageProcessor(config)

time.sleep(1)

#Mavproxy Setup -- I'm not sure if this is still needed (as of Jan 29, 2024) but
#not really wanting to remove it atm on the chance that somehow the
# mavproxy subprocess is relying on it
if sys.version_info[0] >= 3:
    ENCODING = "ascii"
else:
    ENCODING = None

mavlink = Mavlink()

async def main():
    """ Start up the various async methods that make up the autopilot client """
    try:
        robot_state.write_serial_port_gnss_corrections = await serial.ublox_serial_port()
        await mavlink.setup_ardupilot_connections()

        robot_state.local_storage.load_mission_info_from_db()
        
        try:
            await asyncio.wait_for(
                waypoint_wizard.load_waypoints_into_autopilot(), timeout=60)
        except asyncio.exceptions.TimeoutError:
            print("Got a timeout during the waypoint_wizard."
                  "load_waypoints_into_autopilot() function!")

        ox_eternal_process = eternal_process.EternalProcess(
            the_message_processor,
            network,
            config,
            serial,
            mavlink)
        
        util.asyncio_create_task_disappear_workaround(ox_eternal_process.build_local_autopilot_config_data_objects())
        
        await asyncio.gather(
            ox_eternal_process.build_local_autopilot_data_objects_from_mavlink_message_stream(),
            ox_eternal_process.check_compass_variance(),
            ox_eternal_process.get_control_commands_from_remote(),
            ox_eternal_process.get_rtcm_corrections_from_remote(),
            ox_eternal_process.get_startupdata_from_remote(),
            ox_eternal_process.get_non_control_info_from_remote(),
            ox_eternal_process.autopilot_check_not_making_progress_near_waypoint(),
            ox_eternal_process.autopilot_check_randomly_in_auto_mode_but_making_no_progress(),
            ox_eternal_process.autopilot_check_close_to_waypoint(),
            ox_eternal_process.autopilot_check_stuck_full_throttle_no_progress(),
            ox_eternal_process.rtcm_check_not_getting_corrections(),
            ox_eternal_process.send_robot_status_out_through_websocket(),
            network.send_robot_status_out_through_webrtc(),
            ox_eternal_process.autopilot_check_mission_finished(),
            ox_eternal_process.autopilot_check_gyrating_and_stop_hold_start_if_so(),
            ox_eternal_process.joystick_control_sanity_checks(),
            ox_eternal_process.get_robot_config_from_remote(),
            )
    except KeyboardInterrupt:
        logging.error("Caught keyboard interrupt")
    finally:
        logging.debug("Cleaning up RTCPeerConnection clients")
        await network.clean_up(network.pcs)
        logging.debug("Shutting down autopilot")

if __name__ == "__main__":
    asyncio.run(main())
