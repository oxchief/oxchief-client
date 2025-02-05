#!/usr/bin/env python3
#pylint: disable = logging-fstring-interpolation
"""
Author: Wayne Baswell

Functions that are designed to run forever, or more precisely, as long as the 
autopilot is on.
"""
import asyncio
import logging
import time
import traceback

import requests
import websockets

from config import Config
from constants import AutopilotMode, Constants, LastTime, MavMessageType
import flight_controller
from mavlink_util import Mavlink
from message_processor import MessageProcessor
from network_util import Network
import raspberry_pi
import robot_state
from robot_state import last_time #hash of last time we received various message types
from serial_util import Serial
import util
import waypoint_wizard

class EternalProcess:
    """
    Exposes functions that should always be running while the autopilot is on.
    """

    def __init__(self,
                message_processor: MessageProcessor = None,
                network: Network = None,
                config: Config = None,
                serial: Serial = None,
                mavlink: Mavlink = None):

        self.config = config or Config()
        self.network = network or Network(self.config)
        self.the_message_processor = message_processor or MessageProcessor(self.config)
        self.serial = serial or Serial(self.config)
        self.mavlink = mavlink or Mavlink(self.config)

    async def load_mission_data_from_autopilot(self) -> None:
        """
        Load waypoints presently in Flight Controller using the mavproxy connection.
        We do not presently use this as we've moved to using mavutil, i.e.
        `waypoint_wizard.load_waypoints_using_mavutil(..)`
        """
        #make sure we're starting with an empty list
        robot_state.waypoints_in_autopilot.clear()
        #I just want to give mavproxy one more second here
        # since I think it just finished init
        await asyncio.sleep(1)

        wp_load_string = "wp list\n"
        with robot_state.lock_mavproxy:
            robot_state.mavproxy.stdin.write(wp_load_string.encode())
            await robot_state.mavproxy.stdin.drain()

            loaded_string = "Saved"
            finished = False

            while not finished:
                line_bytes = await robot_state.mavproxy.stdout.readline()
                line = line_bytes.decode("utf-8")
                mav_dict = self.mavlink.build_lat_lng_from_mavproxy_line(line)
                if mav_dict:
                    robot_state.waypoints_in_autopilot.append(mav_dict)

                print(line)
                if line.find(loaded_string) != -1:
                    finished = True
                await asyncio.sleep(0.001)

        logging.debug(f"{len(robot_state.waypoints_in_autopilot)} waypoints loaded "
                    f"from autopilot flight controller")
        return 1

    async def get_startupdata_from_remote(self) -> None:
        """
        Pull in startup data from OxChief server
        """
        #this is how I do a reconnecting async websocket -- the official docs shows
        #using a for loop, but I just follow the this "while True" idea
        #we've been using for a good while
        while True:
            try:
                async with websockets.connect(self.config.uri_startupdata_verbose,
                                            extra_headers={"jwt":
                                                self.config.auth_token}) as websock:
                    while True:
                        #we should stay in this loop only breaking out on websocket error
                        msg = Constants.STARTUPDATA_MESSAGE_TYPE
                        time_millis = time.time_ns() // 1_000_000
                        message_json_str = (
                            '{ "messageType":"' + msg + '", '
                            '"time": ' + str(time_millis) + ', '
                            '"mType": "' + msg + '", '
                            '"message": "' + msg + '"}'
                        )
                        util.asyncio_create_task_disappear_workaround(
                            websock.send(message_json_str))
                        await asyncio.sleep(.5)
                        websocket_received_data = await asyncio.wait_for(
                            websock.recv(), timeout=10)
                        await self.the_message_processor.process_websocket_message(
                                                    websocket_received_data,
                                                    websock)
                        #sleep x seconds between pulling fresh copy of startup data
                        await asyncio.sleep(60)
            except Exception as e:
                logging.error("Caught exception in get_startupdata_from_remote. "
                            "Let's sleep for a second and then try to re-establish "
                            "the websocket connection from autopilot_client.py to "
                            "the oxchief server.")
                logging.error(e)
                traceback.print_exc()
                await asyncio.sleep(1.0)

    async def get_rtcm_corrections_from_remote(self) -> None:
        """
        Listen for gnss correction data and pass it along to the robot via
        `process_websocket_message(...)`. The user may change the correction
        provider they wish to connect to -- this code looks for
        that change and handles it.
        """
        errors = 0

        #sleep until we have a valid url to pull corrections from
        while not robot_state.uri_correction_verbose:
            await asyncio.sleep(1)

        old_uri = robot_state.uri_correction_verbose
        while True:
            try:
                async with websockets.connect(robot_state.uri_correction_verbose,
                                            extra_headers={"jwt":
                                                self.config.auth_token}) as websock:
                    while True:
                        websocket_received_data = await asyncio.wait_for(
                            websock.recv(), timeout=10)
                        await self.the_message_processor.process_websocket_message(
                                                    websocket_received_data,
                                                    websock)
                        await asyncio.sleep(.01)
                        #if correction uri has changed, break out of loop and
                        #connect to new correction URI
                        if old_uri != robot_state.uri_correction_verbose:
                            logging.info("Detected new correction uri!")
                            logging.info(f"Old: {old_uri}")
                            logging.info(f"New: {robot_state.uri_correction_verbose}")
                            old_uri = robot_state.uri_correction_verbose
                            break
            except Exception as e:
                logging.error("!!!!!!!!!!!!!!!!ERROR in get_rtcm_corrections_from_remote():")
                logging.error(e)
                traceback.print_exc()
                errors = errors + 1
                #add a slight delay here so that we don't go crazy
                #looping when, for instance, server reboots
                await asyncio.sleep(1)
                logging.debug(f"{errors} errors received so far")

    async def get_non_control_info_from_remote(self) -> None:
        """
        Keep a websocket connect open to server to listen for
        robot non-control commands from client
        """
        start_time = time.time() # for debugging
        errors = 0

        while True:
            try:
                async with websockets.connect(self.config.uri_info_verbose,
                                            extra_headers={"jwt":
                                                self.config.auth_token}) as websock:
                    while True:
                        websocket_received_data = await asyncio.wait_for(
                            websock.recv(), timeout=10)
                        await self.the_message_processor.process_websocket_message(
                                                websocket_received_data,
                                                websock)
                        await asyncio.sleep(.01)
                        #logging.debug(f"running for {time.time()-start_time} seconds"
                        #    f"\nwebsocket_received_data: {websocket_received_data}")
            except Exception as e:
                logging.error("!!!!!!!ERROR in get_non_control_info_from_remote():")
                logging.error(e)
                traceback.print_exc()
                errors = errors + 1
                #add a slight delay here so that we don't go crazy
                # looping when, for instance, server reboots
                await asyncio.sleep(1)
                logging.debug(f"{errors} errors received so far")

    async def get_control_commands_from_remote(self) -> None:
        """
        Keep a websocket connect open to server to listen for
        robot control commands from client
        """
        start_time = time.time() #for debugging
        errors = 0

        while True:
            try:
                async with websockets.connect(self.config.uri_control_verbose,
                                            extra_headers={"jwt":
                                                self.config.auth_token}) as websock:
                    while True:
                        websocket_received_data = await asyncio.wait_for(
                            websock.recv(), timeout=600)
                        await self.the_message_processor.process_websocket_message(websocket_received_data, websock)
                        await asyncio.sleep(.01)
                        #logging.debug(f"running for {time.time()-start_time} seconds"
                        #    f"\nwebsocket_received_data: {websocket_received_data}")
            except Exception as e:
                logging.error("!!!!!!!ERROR in get_control_commands_from_remote():")
                logging.error(e)
                traceback.print_exc()
                errors = errors + 1
                #add a slight delay here so that we don't go crazy
                # looping when, for instance, server reboots
                await asyncio.sleep(1)
                logging.debug(f"{errors} errors received so far")

    async def send_robot_status_out_through_websocket(self) -> None:
        """
        Send out the big `robot_json_status_string` message via websocket.
        """
        while True:
            try:
                async with websockets.connect(self.config.uri_info_silent,
                                            extra_headers={"jwt":
                                                self.config.auth_token}) as websock:
                    while True:
                        robot_status_json = await flight_controller.robot_json_status_string()
                        #we should stay in this loop only breaking out on websocket error
                        websocket_task = util.asyncio_create_task_disappear_workaround(
                            websock.send(robot_status_json))
                        #limit websocket message rate by sleeping every cycle
                        await asyncio.sleep(.5)

                        if not websocket_task.done():
                            logging.debug("websocket task is not done, so let's "
                                        "sleep half a second")
                            await asyncio.sleep(.5)

                        if not websocket_task.done():
                            logging.debug("websocket task has taken > 0.7 seconds "
                                        "to complete, let's break out of the "
                                        "inner while loop and re-establish the "
                                        "websocket connection...")
                            break

                        if websocket_task.exception() is not None:
                            logging.error("Websocket JSON data send exited with exception:")
                            websocket_task.print_stack()
                            logging.error("let's break out of the inner while loop "
                                        "and re-establish the websocket connection...")
                            break

            except Exception as e:
                logging.error("Caught exception in send_robot_status_out_through_"
                            "websocket. Let's sleep for a second and then try to "
                            "re-establish the websocket connection from "
                            "autopilot_client.py to the oxchief server.")
                logging.error(e)
                traceback.print_exc()
                await asyncio.sleep(1.0)

    async def rtcm_check_not_getting_corrections(self) -> None:
        """
        Check if we are receiving GNSS corrections. Presently we just sent a message 
        up to the OxChief Web UI indicating that it's been 
        a while since we last RTCM.
        """
        while True:
            await asyncio.sleep(5)
            if last_time[LastTime.RTCM_AS_BYTES] != -1:
                secs_since_last_rtcm = time.time() - last_time[LastTime.RTCM_AS_BYTES]
                if secs_since_last_rtcm > 30:
                    self.network.robot_log(f"{round(secs_since_last_rtcm,1)} "
                                           "seconds since last RTCM.")

    async def check_compass_variance(self) -> None:
        """
        It appears that a compass_variance >= 10 means that the autopilot
        is going to go bat poop crazy, ignoring the compass
        and weaving around wildly.
        """
        bogus_compass_time = -1
        ekf_status = robot_state.autopilot_data[MavMessageType.EKF_STATUS_REPORT]
        if ekf_status:
            if ekf_status.compass_variance >= Constants.COMPASS_VAR_LIMIT:
                logging.warning("Whoaaa! compass_variance is "
                                f"{ekf_status.compass_variance}")
                if bogus_compass_time < 0:
                    bogus_compass_time = time.time()
                    logging.debug("Setting inital bogus_compass_time to "
                                    f"{bogus_compass_time}")
            else:
                bogus_compass_time = -1

            if(bogus_compass_time > 0 and
            time.time() - bogus_compass_time > Constants.COMPASS_VAR_BOGUS_COMPASS_MAX_SECONDS):
                logging.warning(
                    f"compass_variance has been >= {Constants.COMPASS_VAR_LIMIT}"
                    f" for > {Constants.COMPASS_VAR_BOGUS_COMPASS_MAX_SECONDS} seconds, so "
                    "we're going to kill power to blades/wheels "
                    "and set autopilot to HOLD and DISARM")
                raspberry_pi.blades_and_wheels_power_off()
                await flight_controller.hold_keep_wp()
                bogus_compass_time = -1

    async def autopilot_check_gyrating_and_stop_hold_start_if_so(self) -> None:
        """
        When autopilot starts gyrating, a quick stop/start 
        often seems to fix the problem.

        Test that rover is some distance away from the prior 
        waypoint (i.e. it didn't just turn)
        """
        last_5_headings = []

        while True:
            #check headings logic While loop
            try:
                current_waypoint = -1
                mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
                if mission_current:
                    current_waypoint = mission_current.seq

                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO and
                    current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0) : #check that a mission is running
                    global_position_int = \
                        robot_state.autopilot_data[MavMessageType.GLOBAL_POSITION_INT]
                    the_heading = global_position_int.hdg / 10**2

                    prev_wp_distance = waypoint_wizard.get_prev_wp_dist_in_meters()
                    next_wp_distance = waypoint_wizard.get_wp_dist_in_meters()

                    if (prev_wp_distance < Constants.GYRATING_CHECK_MIN_DISTANCE_FROM_WAYPOINT_TO_RUN_THIS_CHECK_IN_METERS or
                        next_wp_distance < Constants.GYRATING_CHECK_MIN_DISTANCE_FROM_WAYPOINT_TO_RUN_THIS_CHECK_IN_METERS):
                        last_5_headings  = []
                        self.network.robot_log("Detected robot within "
                                f"{Constants.GYRATING_CHECK_MIN_DISTANCE_FROM_WAYPOINT_TO_RUN_THIS_CHECK_IN_METERS}"
                                " meters of waypoint -- resetting last_5_headings array")
                        await asyncio.sleep(1.0)
                        continue

                    last_5_headings.insert(0, the_heading)
                    # Keep only the last 5 elements -- i.e. the last 5 heading readings
                    last_5_headings = last_5_headings[:5]
                    #only makes sense to run if we've recorded at least 2 headings readings
                    if len(last_5_headings) >= 2:
                        wobble = util.max_heading_difference(last_5_headings)
                        if wobble > Constants.GYRATING_CHECK_MAX_ALLOWABLE_WOBBLE_IN_DEGREES:
                            #only run this logic if it's been more than
                            #MIN_TIME_BETWEEN_RESETS_IN_SECONDS
                            #seconds since last time the
                            #robot was stopped or
                            #started
                            if ((time.time() - robot_state.time_last_stop_start) >
                                Constants.GYRATING_CHECK_MIN_TIME_BETWEEN_RESETS_IN_SECONDS):
                                last_5_headings  = []
                                self.network.robot_log("Detected weaving! "
                                            "Will now stop and start robot.")
                                await flight_controller.hold_sleep_start_robot(5)
                            else:
                                self.network.robot_log(f"{wobble} degree wobble"
                                                       " over last 5 seconds")
                                self.network.robot_log("Detected weaving! However, it's been "
                                        f"fewer than {Constants.GYRATING_CHECK_MIN_TIME_BETWEEN_RESETS_IN_SECONDS}"
                                        " seconds since we last reset robot,"
                                        " so skipping reset for now.")

                await asyncio.sleep(1.0)
            except Exception as e:
                logging.error("Caught exception in "
                              "autopilot_check_gyrating_and_stop_hold_start_if_so:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in "
                    "autopilot_check_gyrating_and_stop_hold_start_if_so ...", "ERROR")
                self.network.robot_log(str(e), 'ERROR')
                await asyncio.sleep(1.0)
            #end check headings logic While loop

    async def autopilot_check_close_to_waypoint(self) -> None:
        """
        When autopilot gets close to waypoint, point it to next waypoint.
        I think the ArduPilot rover logic is supposed to do this
        via the WP_Radius parameter, but it doesn't seem to.
        """
        #DISTANCE_TO_WAYPOINT_IN_METERS = 0.3048
        DISTANCE_TO_WAYPOINT_IN_METERS = 0.7
        while True:
            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue
            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq
            try:
                wp_dist = waypoint_wizard.get_wp_dist_in_meters()
                print(f'distance to next wp: {wp_dist}')
                #only run check if in AUTO mode
                #and not sitting at last waypoint
                #(i.e. at the end of a mission run)
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO
                    and current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0):
                    if wp_dist == -1:
                        self.network.robot_log('Could not find distance to waypoint...skipping')
                    elif wp_dist < DISTANCE_TO_WAYPOINT_IN_METERS:
                        await waypoint_wizard.goto_next_wp()
                        self.network.robot_log(f'{wp_dist} meters to obstacle, goto next WP')
                await asyncio.sleep(1.0)
            except Exception as e:
                logging.error("Caught exception in autopilot_check_close_to_waypoint:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in "
                                       "autopilot_check_close_to_waypoint()...", "ERROR")
                self.network.robot_log(str(e), 'ERROR')
                await asyncio.sleep(1.0)

    async def autopilot_check_randomly_in_auto_mode_but_making_no_progress(self) -> None:
        """
        For some reason sometimes the robot just stops and, even though it's in auto
        mode, it won't go anywhere. It's like it's just paused in time. It's very
        simple to break it out of the spell: just stop then start.
        """
        #random big value because we're testing for a small value down below
        distance_traveled_lately = 99999999
        last_10_positions  = [False] * 10

        while True:
            await asyncio.sleep(2.0) #we want to sleep 2 seconds between iterations of this logic

            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue

            utm = robot_state.autopilot_data[MavMessageType.GLOBAL_POSITION_INT]
            if utm:
                present_loc = (utm.lat / 10**7, utm.lon / 10**7)  #loc = (30.5634410, -87.6780089)
                last_10_positions.pop(0)
                last_10_positions.append(present_loc)

            # test that we've recorded 10 positions
            if last_10_positions[0] and last_10_positions[9]:
                distance_traveled_lately = waypoint_wizard.total_distance_between_last_10_positions_in_meters(last_10_positions)
                print("total_distance_between_last_10_positions_in_meters: "
                      f"{distance_traveled_lately}")

            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq

            try:
                #check that a mission is running
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO
                    and current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0):
                    #robot_log("Full throttle in Auto mode for "
                    #           "{FULL_THROTTLE_STUCK_SECONDS_TO_ACTIVATE} seconds")
                    #robot_log(f"Traveled {distance_traveled_lately} meters in check window")
                    if (distance_traveled_lately <
                        Constants.DISTANCE_NO_PROGRESS_FULL_THROTTLE_STUCK_IN_METERS):
                        self.network.robot_log("Detected robot stuck in autopilot_check_"
                                "randomly_in_auto_mode_but_making_no_progress!")
                        self.network.robot_log("Will now hold / sleep for a few seconds / "
                                "attempt to start robot")
                        # 1 put robot in hold
                        self.network.robot_log("autopilot_check_randomly_in_auto_mode_but_"
                                "making_no_progress -- Attempting robot hold/start")
                        await flight_controller.hold_sleep_start_robot(1.5)
                        #reset after triggering to avoid loop
                        distance_traveled_lately = 99999999
                        #reset this array so that we don't get in a stop/start loop
                        last_10_positions  = [False] * 10

            except Exception as e:
                logging.error("Caught exception in autopilot_check_randomly_in_"
                            "auto_mode_but_making_no_progress:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in autopilot_check_randomly_in_auto_"
                        "mode_but_making_no_progress()...", "ERROR")
                self.network.robot_log(str(e), "ERROR")
                await asyncio.sleep(1.0)

    async def autopilot_check_stuck_full_throttle_no_progress(self) -> None:
        """
        If either of the motors is at max throttle and the robot hasn't moved for 10
        seconds, then we need to:
            1. Put the robot in HOLD
            2. Alert the user that the robot is stuck

        TODO
        Eventually, we'll want to put in some kind of go-around logic using
        ArduPilot Guided Mode, i.e.:
        1. Put the robot in Guided Mode
        2. Check if the line from robot to some point x feet behind the robot is 
        within the mission boundary / no exclusion zones
        3. Drive to the point behind robot from #2
        4. Calculate a point to the right-or-left of where the robot got stuck
        5. Drive to point 4
        6. Drive to a point a x feet ahead of where robot got stuck on the same line 
        it was on when it got stuck
        """

        #random big value because we're testing for a small value down below
        distance_traveled_lately = 99999999
        last_10_positions  = [False,False,False,False,False,False,False,False,False,False]
        max_throttle_now = False

        while True:
            await asyncio.sleep(2.0) #we want to sleep 2 seconds between iterations of this logic

            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue

            utm = robot_state.autopilot_data[MavMessageType.GLOBAL_POSITION_INT]
            if utm:
                present_loc = (utm.lat / 10**7, utm.lon / 10**7)  #loc = (30.5634410, -87.6780089)
                last_10_positions.pop(0)
                last_10_positions.append(present_loc)

            # test that we've recorded 10 positions
            if last_10_positions[0] and last_10_positions[9]:
                distance_traveled_lately = waypoint_wizard.total_distance_between_last_10_positions_in_meters(last_10_positions)
                print(f"total_distance_between_last_10_positions_in_meters: "
                      f"{distance_traveled_lately}")

            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq

            servo1_raw = servo3_raw = -1

            # servo1_raw and servo3_raw
            servos = robot_state.autopilot_data[MavMessageType.SERVO_OUTPUT_RAW]
            if servos:
                servo1_raw = servos.servo1_raw
                servo3_raw = servos.servo3_raw

            try:
                #check that a mission is running
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO
                    and current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0):
                    #check that at least one throttle is wide open
                    if (servo1_raw in (robot_state.servo1_min, robot_state.servo1_max) or
                        servo3_raw in (robot_state.servo3_min, robot_state.servo3_max)):
                        if not max_throttle_now:
                            max_throttle_now = time.time()
                            self.network.robot_log("Detected full throttle in Auto mode")
                        else:
                            if ((time.time() - max_throttle_now) >
                                Constants.FULL_THROTTLE_STUCK_SECONDS_TO_ACTIVATE):
                                self.network.robot_log("Full throttle in Auto mode for"
                                    f"{Constants.FULL_THROTTLE_STUCK_SECONDS_TO_ACTIVATE} seconds")
                                self.network.robot_log(f"Traveled {distance_traveled_lately} "
                                    "meters in check window")
                                if (distance_traveled_lately <
                                    Constants.DISTANCE_NO_PROGRESS_FULL_THROTTLE_STUCK_IN_METERS):
                                    await flight_controller.hold_keep_wp()
                                    self.network.robot_log("Detected robot stuck!")
                    else:
                        max_throttle_now = False
            except Exception as e:
                logging.error("Caught exception in "
                            "autopilot_check_stuck_full_throttle_no_progress:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in "
                        "autopilot_check_stuck_full_throttle_no_progress()...", 
                        "ERROR")
                self.network.robot_log(str(e), "ERROR")
                await asyncio.sleep(1.0)

    async def autopilot_check_not_making_progress_near_waypoint(self) -> None:
        """
        There's a situation where the robot stops at a waypoint and just slowly, 
        ever-so-slightly goes back and forth for, I guess, forever if you let 
        it. This code is meant to detect that and put the robot in HOLD and 
        then back in AUTO -- which seems to fix it.
        """
        waypoint_close_initial_time = 0

        while True:
            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue
            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq

            try:
                #robot_log(f"inside autopilot_check_not_making_progress_near_waypoint()"
                # "current waypoint: {current_waypoint}  len(robot_state.waypoints_in_autopilot): "
                # "{len(robot_state.waypoints_in_autopilot)}")
                wp_dist = waypoint_wizard.get_wp_dist_in_meters()
                #only run check if in AUTO mode
                #and not sitting at last waypoint
                #(i.e. at the end of a mission run)
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO
                    and current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0) :
                    #robot_log("MODE_AUTO CHECK")
                    #robot_log("LAST_WP CHECK")
                    if wp_dist == -1:
                        self.network.robot_log("Could not find distance to waypoint...skipping")
                    elif wp_dist < Constants.DISTANCE_SHUFFLE_DETECT_ACTIVE_IN_METERS:
                        self.network.robot_log("WP_DIST < 2 meters")
                        if waypoint_close_initial_time == 0:
                            self.network.robot_log("SETTING the waypoint_close_initial_time"
                                    " FLAG to now")
                            #this is how we keep track of the first time that
                            #the robot gets close to the waypoint
                            print("Detected robot close to waypoint. Recording time"
                                " to check for robot shuffling.")
                            waypoint_close_initial_time = time.time()
                        elif ((time.time() - waypoint_close_initial_time) >
                            Constants.SHUFFLE_DETECT_SECONDS_TO_ACTIVATE):
                            self.network.robot_log(
                                    "autopilot_check_not_making_progress_near_waypoint "
                                    f"More than {Constants.SHUFFLE_DETECT_SECONDS_TO_ACTIVATE}"
                                    " seconds have elapsed since we set WP close flag")
                            await flight_controller.hold_sleep_start_robot(1.5)
                            waypoint_close_initial_time = 0
                        else:
                            self.network.robot_log("Close to this waypoint for " +
                                    str(time.time() - waypoint_close_initial_time)
                                    + " seconds")
                    else:
                        waypoint_close_initial_time = 0
                else:
                    waypoint_close_initial_time = 0

                await asyncio.sleep(1.0)
            except Exception as e:
                logging.error("Caught exception in autopilot_check_not_making_"
                            "progress_near_waypoint:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in autopilot_check_not_making_progress"
                        "_near_waypoint()...", "ERROR")
                self.network.robot_log(str(e), "ERROR")
                await asyncio.sleep(1.0)

    async def autopilot_check_mission_finished(self) -> None:
        """
        If robot mission is finished, then
        1. Set status == HOLD
        2. Set next waypoint == 1 
        """

        while True:
            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue

            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq

            try:
                wp_dist = waypoint_wizard.get_wp_dist_in_meters()
                #this is a check that roughly approximates the idea:
                # "are you at the end of the mission?"
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO and
                    current_waypoint == robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 1 and wp_dist < 1.0):
                    # wait a second before disarming the vehicle -- in case the robot
                    # is a few inches away from the end of the mission, it should
                    # let it stop normally (i.e. not stop before the natural
                    # end of the mission) -- there may be some way to
                    # detect the state of "robot is at end of
                    # mission", but I don't know how
                    await asyncio.sleep(1.0)

                    #we want to check if robot_state.waypoints_in_autopilot are at the end of
                    #robot_state.waypoints_in_mission -- if not, then we load the next N
                    #waypoints from ...waypoints_in_mission into the autopilot
                    paused_in_the_middle_of_a_big_mission_waiting_to_load_more_waypoints = True

                    if (current_waypoint <
                        robot_state.end_waypoint_number_of_waypoints_in_autopilot()):
                        paused_in_the_middle_of_a_big_mission_waiting_to_load_more_waypoints = False

                    if paused_in_the_middle_of_a_big_mission_waiting_to_load_more_waypoints:
                        print("paused_in_the_middle_of_a_big_mission_"
                            "waiting_to_load_more_waypoints is TRUE")
                        print("now we'll put the autopilot in HOLD and "
                            "attempt to load the next batch of waypoints")
                        await flight_controller.hold()
                        #baswell Saturday May 27 -- prob need to let load_next_round_of_waypoints
                        # return True/False to indicate if there are more waypoints loaded
                        # (or else at the end of mission)
                        #Only run the next 5 lines of code below if more waypoints loaded
                        # i.e. not at the end of mission
                        more_waypoints_exist = await waypoint_wizard.load_next_round_of_waypoints()
                        if more_waypoints_exist:
                            await asyncio.sleep(0.1)
                            #we are already at waypoint 1 -- this should help
                            # reduce shuffling around at the outset
                            await waypoint_wizard.goto_wp(2)
                            await asyncio.sleep(0.1)
                            await flight_controller.start_robot()
                            print("now the robot should be starting back up")
                        else:
                            print("more_waypoints_exist is False -- at end of mission")
                            await flight_controller.end_of_mission_cleanup()
                    else:
                        #at the end of the mission, so disarm and cleanup
                        await flight_controller.end_of_mission_cleanup()

                await asyncio.sleep(1.0)
            except Exception as e:
                logging.error("Caught exception in autopilot_check_mission_finished:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in "
                                       "autopilot_check_mission_finished()...", "ERROR")
                self.network.robot_log(str(e), "ERROR")
                await asyncio.sleep(1.0)

    async def autopilot_check_way_off_course(self) -> None:
        """
        If ardupilot has compass confusion, it sometimes goes crazy and starts looping
        around. We want to try to detect this situation by keeping an eye on the 
        xTrack -- if it's over some threshold for some amount of time, then 
        stop / pause / start the autopilot to see if this will get it
        back to sanity
        """
        xtrack_bogus_initial_time = 0

        while True:
            if flight_controller.get_flight_mode() != AutopilotMode.MODE_AUTO:
                await asyncio.sleep(1.0)
                continue
            current_waypoint = -1
            mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
            if mission_current:
                current_waypoint = mission_current.seq

            try:
                xtrack_error = 0
                # xtrack_error
                nav = robot_state.autopilot_data[MavMessageType.NAV_CONTROLLER_OUTPUT]
                if nav:
                    xtrack_error = round(nav.xtrack_error, 2)
                # only run check if in AUTO mode
                # and not sitting at last waypoint
                # (i.e. at the end of a mission run)
                if (flight_controller.get_flight_mode() == AutopilotMode.MODE_AUTO and
                    current_waypoint != robot_state.end_waypoint_number_of_waypoints_in_autopilot()
                    and current_waypoint > 0):
                    if xtrack_error > Constants.DISTANCE_XTRACK_ERROR_ACTIVE_IN_METERS:
                        self.network.robot_log("xtrack_error > "
                            f"{Constants.DISTANCE_XTRACK_ERROR_ACTIVE_IN_METERS} meters")
                        if xtrack_bogus_initial_time == 0:
                            self.network.robot_log("SETTING the xtrack_bogus_initial_time"
                                                   " FLAG to now")
                            #this is how we keep track of the first time the robot
                            #is too far off the path (i.e. xtrack too big)
                            print("Detected xtrack too big. Recording time to check"
                                " if robot is wandering off the path.")
                            xtrack_bogus_initial_time = time.time()
                        elif ((time.time() - xtrack_bogus_initial_time) >
                                Constants.XTRACK_SECONDS_TO_ACTIVATE):
                            self.network.robot_log("More than "
                                    f"{Constants.XTRACK_SECONDS_TO_ACTIVATE} "
                                    "seconds have elapsed since we set " 
                                    "xtrack-too-big flag")
                            self.network.robot_log("Let's stop the robot, take a break, and then"
                                    " start it back to see if that fixes things.")
                            # 1 put robot in hold
                            await flight_controller.hold_sleep_start_robot(5.0)
                            xtrack_bogus_initial_time = 0
                        else:
                            self.network.robot_log("xtrack too big for "
                                    + str(time.time() - xtrack_bogus_initial_time)
                                    + " seconds")
                    else:
                        xtrack_bogus_initial_time = 0
                else:
                    xtrack_bogus_initial_time = 0

                await asyncio.sleep(1.0)
            except Exception as e:
                logging.error("Caught exception in autopilot_check_way_off_course:")
                logging.error(e)
                traceback.print_exc()
                self.network.robot_log("Exception caught in autopilot_check_way_off_course()...",
                        "ERROR")
                self.network.robot_log(str(e), "ERROR")
                await asyncio.sleep(1.0)

    async def autopilot_babysitter(self) -> None:
        """
        Sets autopilot mode == HOLD if 
        1. GPS fix is non-RTK and 
        2. autopilot mode != MANUAL 
        TODO IMPLEMENT #2 check (i.e. right now we're not checking that autopilot mode is AUTO)
        """
        while True:
            try:
                #baswell debugging
                #waypoint_1_maybe = robot_state.mutil.waypoint_request_send(1)
                #waypoint_2_maybe = robot_state.mutil.waypoint_request_send(2)
                if flight_controller.get_flight_mode() == AutopilotMode.MODE_MANUAL:
                    pass
                elif robot_state.ap_fix_type and robot_state.ap_fix_type >= 5:
                    #do nothing because we've got at least an RTK Float fix
                    logging.debug("autopilot_babysitter robot_state.ap_fix_type: "
                                  f"{robot_state.ap_fix_type}")
                else:
                    #TODO this is where we just need to add this line (I think) --
                    # elif get_flight_mode() == AutopilotMode.MODE_HOLD:
                    #send HOLD to the autopilot because the GPS
                    # fix is less than RTK Float
                    logging.warning("Sending 'mode hold' command to the autopilot "
                                    "because we don't have an RTK float or RTK fix")
                    raspberry_pi.blades_and_wheels_power_off()
                    await flight_controller.hold_keep_wp()

                await asyncio.sleep(.5)
            except Exception as e:
                logging.error("Caught exception in autopilot_babysitter:")
                logging.error(e)
                traceback.print_exc()
                await asyncio.sleep(.5)

    async def build_local_autopilot_config_data_objects(self) -> None:
            """
            Builds local autopilot configuration data objects by pulling parameters from the MAVLink connection
            and saving them to the local copy.
            
            Note about python debugging -- for some reason this method seems to often
            freeze up (and timeout, not returning usable data) when I'm 
            debugging the Python code from VSCode.
            """
            
            # pull params from mavlink connection 
            # and save them to local copy
            await asyncio.sleep(3)
            
            servo1_params_int = await self.mavlink.request_parameters_as_int(
                ['SERVO1_MAX', 'SERVO1_MIN', 'SERVO1_TRIM'])
            
            if servo1_params_int['SERVO1_MIN']:
                robot_state.servo1_min = servo1_params_int['SERVO1_MIN']
            else:
                logging.error(f"SERVO1_MIN not found in params -- leaving as {robot_state.servo1_min}")
                
            if servo1_params_int['SERVO1_TRIM']:
                robot_state.servo1_trim = servo1_params_int['SERVO1_TRIM']
            else:
                logging.error(f"SERVO1_TRIM not found in params -- leaving as {robot_state.servo1_trim}")
                
            if servo1_params_int['SERVO1_MAX']:
                robot_state.servo1_max = servo1_params_int['SERVO1_MAX']
            else:
                logging.error(f"SERVO1_MAX not found in params -- leaving as {robot_state.servo1_max}")
            
            servo3_params_int = await self.mavlink.request_parameters_as_int(
                ['SERVO3_MAX', 'SERVO3_MIN', 'SERVO3_TRIM'])
            
            if servo3_params_int['SERVO3_MIN']:
                robot_state.servo3_min = servo3_params_int['SERVO3_MIN']
            else:
                logging.error(f"SERVO3_MIN not found in params -- leaving as {robot_state.servo3_min}")

            if servo3_params_int['SERVO3_TRIM']:
                robot_state.servo3_trim = servo3_params_int['SERVO3_TRIM']
            else:
                logging.error(f"SERVO3_TRIM not found in params -- leaving as {robot_state.servo3_trim}")
            
            if servo3_params_int['SERVO3_MAX']:
                robot_state.servo3_max = servo3_params_int['SERVO3_MAX']
            else:
                logging.error(f"SERVO3_MAX not found in params -- leaving as {robot_state.servo3_max}")
    
    async def joystick_control_sanity_checks(self) -> None:
            """
            Perform sanity checks for joystick control in manual mode.
            This method checks if the joystick is connected and 
            receiving data. If no joystick data is 
            received for more than {seconds} seconds, 
            the robot is put on hold.
            """
            seconds = 3.0
            while True:
                await asyncio.sleep(1.0) #we want to sleep x seconds between iterations of this logic
                logging.debug("joystick_control_sanity_checks")
                #if we're in manual mode (brought about by web UI joystick), then we need to check that the
                #joystick is connected and that we're getting data from it
                logging.debug(f"robot_state.manual_mode_via_client_ui_joystick: {robot_state.manual_mode_via_client_ui_joystick}")
                logging.debug(f"flight_controller.get_flight_mode(): {flight_controller.get_flight_mode()}")
                if flight_controller.get_flight_mode() == AutopilotMode.MODE_MANUAL and \
                    robot_state.manual_mode_via_client_ui_joystick:
                    #if more than 1 second has passed since last joystick message, it's
                    #time to put everything on hold
                    logging.debug(f"time.time() - robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME]: "
                          f"{time.time() - robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME]}")
                    logging.debug(f"time.time(): {time.time()}")
                    logging.debug(f"robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME]: "
                          f"{robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME]}")
                    if (time.time() - robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME]) >= seconds:
                        servos = robot_state.autopilot_data[MavMessageType.SERVO_OUTPUT_RAW]
                        if servos:
                            servo1_raw = servos.servo1_raw
                            servo3_raw = servos.servo3_raw
                            
                        if servo1_raw != robot_state.servo1_trim and servo3_raw != robot_state.servo3_trim:
                            await flight_controller.hold_keep_wp()
                            logging.error(f"No joystick data received in last {seconds} seconds. Will now put robot on HOLD.")
                            self.network.robot_log(f"No joystick data received in last {seconds} seconds. "
                                    "Will now put robot on HOLD.")

    async def get_robot_config_from_remote(self) -> None:
        """
        Poll remote client for robot configuration data.
        """
        start_time = time.time() # for debugging
        errors = 0

        while True:
            try:
                robot_config_url = f"https://oxchief.com/api/robot/{self.config.robot_id}/?format=json"
                
                headers = {
                    "Authorization": "Bearer " + self.config.auth_token
                }
                print(f"robot_config_url: {robot_config_url}")
                
                robot_config_response = requests.get(robot_config_url, headers=headers)
                robot_config_json = robot_config_response.json()
                print(f"robot_config_json: {robot_config_json}")
                
                if robot_config_json["battery_multiplier"]:
                    robot_state.battery_multiplier = robot_config_json["battery_multiplier"]
                    print(f"battery_multiplier: {robot_state.battery_multiplier}")
                
                await asyncio.sleep(15)
            except Exception as e:
                logging.error("!!!!!!!ERROR in get_robot_config_from_remote():")
                logging.error(e)
                traceback.print_exc()
                errors = errors + 1
                #add a slight delay here so that we don't go crazy
                # looping when, for instance, server reboots
                await asyncio.sleep(1)
                logging.debug(f"{errors} errors received so far")

    async def build_local_autopilot_data_objects_from_mavlink_message_stream(self) -> None:
        """
        Listen to the stream of mavlink messages on the `robot_state.mutil` 
        connection and and pass them along to the parsing function
        `parse_message_to_autopilot_data_objects(..)` to
        save as a local copy of the latest robot 
        info we've received.
        """
        msg_time = time.time()
        num_msgs = 0

        while True:
            try:
                msg = robot_state.mutil.recv_match()
                if not msg:
                    await asyncio.sleep(.005)
                    #print("null message -- skipping")
                    continue
                #print(f"{msg.get_type()} {msg.to_dict()}")
                self.the_message_processor.parse_message_to_autopilot_data_objects(msg)
                num_msgs += 1
                if time.time() - msg_time > 1:
                    logging.debug("***********************************************")
                    logging.debug("number of messages in last "
                                f"{time.time() - msg_time} seconds: {num_msgs}")
                    logging.debug("***********************************************")
                    msg_time = time.time()
                    num_msgs = 0
                await asyncio.sleep(.005)
            except Exception as e:
                logging.error("error in build_local_autopilot_data_objects_"
                            "from_mavlink_message_stream():")
                logging.error(e)
