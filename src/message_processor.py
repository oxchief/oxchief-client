"""
Author: Wayne Baswell

Process client messages.
"""
import asyncio
import base64
import json
import logging
import time
import traceback

import websockets

#we need `from websockets import client` for the websockets.client.WebSocketClientProtocol
#type to work down below -- don't let the linter convince you to
#delete it
from websockets import client # <---- DO NOT DELETE ME!!!
# ^^^ DO NOT DELETE ME!!! ^^^

import flight_controller
import network_util
import mavlink_util
import util
import raspberry_pi
import robot_state
import serial_util
import waypoint_wizard

from pymavlink import mavutil

from config import Config
from constants import Constants,LastTime, MavMessageType

class MessageProcessor:
    """
    Handles mavlink tasks
    """
    def __init__(self, config=Config()):
        self.config = config
        self.network = network_util.Network(config)
        self.mavlink = mavlink_util.Mavlink(config)
        self.serial = serial_util.Serial(self.config)

    # TODO baswell -- what type is msg?
    def parse_message_to_autopilot_data_objects(self, msg:any) -> None:
        """
        Save latest mavlink message into `robot_state.autopilot_data` dict for 
        easy access throughout the app

        Args:
            msg (any): Mavlink message to save to `robot_state.autopilot_data`
        """
        msg_type = msg.get_type()
        #logging.info(f"here we go domino")
        if msg_type == MavMessageType.HEARTBEAT:
            #logging.info(f"is heartbeat message")
            # Decode the current flight mode
            current_flight_mode = mavutil.mode_string_v10(msg)
            logging.info(f"Current Flight Mode: {current_flight_mode}")
            
            if msg.autopilot == 3:
                robot_state.autopilot_data[msg_type] = msg
            #print(f'HEARTBEAT: {msg.autopilot} {msg.base_mode} {msg.crc_extra} {msg.custom_mode} {msg.system_status} {msg.type}')
        else:
            #logging.info("is NOT heartbeat message")
            robot_state.autopilot_data[msg_type] = msg

    async def process_meta_message(self, message:object) -> None:
        """
        Process "meta" JSON message type.

        Args:
            message (object): JSON message object to process.
        """
        try:
            if message["mType"] == "xy":
                if (message["time"] > robot_state.last_time[LastTime.META_X] or
                    message["time"] > robot_state.last_time[LastTime.META_Y]):
                    robot_state.last_time[LastTime.META_X] = robot_state.last_time[LastTime.META_Y] = message["time"]
                    robot_state.last_time[LastTime.META_XY_IN_LOCAL_ROBOT_TIME] = time.time()
                    x = robot_state.client_joystick_x = message["x"]
                    y = robot_state.client_joystick_y = message["y"]
                    flight_controller.set_rc_channels_from_joystick(x,y)
                    logging.info(f"xy message x:{x} y:{y}")
            elif message["mType"] == "goto_next_wp":
                if message["time"] > robot_state.last_time[LastTime.GOTO_NEXT_WP]:
                    robot_state.last_time[LastTime.GOTO_NEXT_WP] = message["time"]
                    #go to the next waypoint
                    await waypoint_wizard.goto_next_wp()
            elif message["mType"] == "goto_prev_wp":
                if message["time"] > robot_state.last_time[LastTime.GOTO_PREV_WP]:
                    robot_state.last_time[LastTime.GOTO_PREV_WP] = message["time"]
                    #go to the previous waypoint
                    await waypoint_wizard.goto_prev_wp()
            elif message["mType"] == "goto_wp_plus_50":
                if message["time"] > robot_state.last_time[LastTime.GOTO_WP_PLUS_50]:
                    robot_state.last_time[LastTime.GOTO_WP_PLUS_50] = message["time"]
                    await waypoint_wizard.goto_wp_plus_50()
            elif message["mType"] == "goto_wp_minus_50":
                if message["time"] > robot_state.last_time[LastTime.GOTO_WP_MINUS_50]:
                    robot_state.last_time[LastTime.GOTO_WP_MINUS_50] = message["time"]
                    await waypoint_wizard.goto_wp_minus_50()
            elif message["mType"] == "load_waypoints":
                # get the waypoints
                # turn them into a json string
                waypoints_json_string = json.dumps(robot_state.waypoints_in_autopilot)
                # send them back to the server
                util.asyncio_create_task_disappear_workaround(
                    self.network.simple_message_send("waypoints", waypoints_json_string, False))
            elif message["mType"] == "flight_controller_configs_request":
                # get servo1_trim and servo3_trim, servo1_max and servo3_max, and servo1_min and servo3_min
                # from robotstate and send them out via self.network.simple_message_send
                servo_configs = robot_state.build_servo_configs_as_json_string()
                util.asyncio_create_task_disappear_workaround(
                    self.network.simple_message_send("flight_controller_configs_response", servo_configs, False))
            elif message["mType"] == "load_gps_config":
                params_float = await self.mavlink.request_parameters_as_float(
                    ['GPS_POS1_X', 'GPS_POS1_Y', 'GPS_POS1_Z'])
                gps_x = params_float["GPS_POS1_X"]
                gps_y = params_float["GPS_POS1_Y"]
                gps_z = params_float["GPS_POS1_Z"]
                util.asyncio_create_task_disappear_workaround(
                    self.network.simple_message_send("config_gps_pos1",
                                    '{"x": "' + str(gps_x) + '", "y": "' + 
                                    str(gps_y)+ '", "z": "' + str(gps_z) + '"}',
                                    False))
            elif message["mType"] == "load_ahrs_config":
                params_int = await self.mavlink.request_parameters_as_int(
                        ['AHRS_OFFSET_E', 'AHRS_OFFSET_N', 'AHRS_OFFSET_S',
                         'AHRS_OFFSET_W'])
                ahrs_e = params_int['AHRS_OFFSET_E']
                ahrs_n = params_int['AHRS_OFFSET_N']
                ahrs_s = params_int['AHRS_OFFSET_S']
                ahrs_w = params_int['AHRS_OFFSET_W']
                util.asyncio_create_task_disappear_workaround(
                    self.network.simple_message_send("config_ahrs_pos", '{"e": "' + str(ahrs_e) +
                                    '", "n": "' + str(ahrs_n)+ '", "s": "' + 
                                    str(ahrs_s)+ '", "w": "' + str(ahrs_w) +
                                    '"}', False))
            elif message["mType"] == "load_etc_config":
                speed = await self.mavlink.get_param_float("WP_SPEED")
                util.asyncio_create_task_disappear_workaround(
                    self.network.simple_message_send("config_etc", 
                                    '{"speed": "' + str(speed) + '"}', False))
            elif message["mType"] == "config_save_gps_1":
                if message["time"] > robot_state.last_time[LastTime.CONFIG_GPS1_SAVE]:
                    robot_state.last_time[LastTime.CONFIG_GPS1_SAVE] = message["time"]
                    #baswell wednesday -- here we want to save the gps x,y,z offsets
                    message_json_str = message["subMessage"]
                    # {"x":"1","y":"2","z":"3"}
                    message_json = json.loads(message_json_str)
                    #message_json should look like:
                    self.network.robot_log("Received GPS_POS1 parameter save message")

                    try:
                        param = "GPS_POS1_X"
                        val_str = message_json["x"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "GPS_POS1_Y"
                        val_str = message_json["y"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "GPS_POS1_Z"
                        val_str = message_json["z"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

            elif message["mType"] == "config_save_ahrs":
                if message["time"] > robot_state.last_time[LastTime.CONFIG_AHRS_SAVE]:
                    robot_state.last_time[LastTime.CONFIG_AHRS_SAVE] = message["time"]
                    message_json_str = message["subMessage"]
                    message_json = json.loads(message_json_str)
                    self.network.robot_log("Received AHRS parameter save message")

                    try:
                        param = "AHRS_OFFSET_E"
                        val_str = message_json["e"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "AHRS_OFFSET_N"
                        val_str = message_json["n"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "AHRS_OFFSET_S"
                        val_str = message_json["s"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "AHRS_OFFSET_W"
                        val_str = message_json["w"].strip()
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting {param}: {err}"
                        self.network.robot_log(err_msg)

            elif message["mType"] == "config_save_etc":
                if message["time"] > robot_state.last_time[LastTime.CONFIG_ETC_SAVE]:
                    robot_state.last_time[LastTime.CONFIG_ETC_SAVE] = message["time"]
                    message_json_str = message["subMessage"]
                    message_json = json.loads(message_json_str)
                    self.network.robot_log("Received ETC parameter save message")
                    base_station_id = message_json["base_station_id"]
                    robot_state.set_correction_uri(self.config, base_station_id)
                    val_str = message_json["speed"].strip()
                    #baswell Saturday Dec 23 -- check base_station_id and if it's
                    #different from the base_station_id we're currently connected
                    #to, then attempt to connect to the new base_station_id
                    try:
                        param = "WP_SPEED"
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting WP_SPEED: {err}"
                        self.network.robot_log(err_msg)

                    try:
                        param = "CRUISE_SPEED"
                        if val_str:
                            self.network.robot_log(f"saving {param} {val_str}")
                            val_float = float(val_str)
                            robot_state.mutil.param_set_send(param, val_float)
                            self.network.robot_log(f"{param} sent to AutoPilot")
                    except Exception as err:
                        traceback.print_exc()
                        err_msg = f"Error setting CRUISE_SPEED: {err}"
                        self.network.robot_log(err_msg)

                    #baswell wednesday -- report back the
                    # success/failure of save via ...
                    #
                    #
                    #or
                    #
                    #robot_log("Wow everything just blew up")
                    #
                    #

            elif message["mType"] == "load_mission":
                if message["time"] > robot_state.last_time[LastTime.META_LOAD_MISSION]:
                    load_begin_time = time.time()
                    robot_state.last_time[LastTime.META_LOAD_MISSION] = message["time"]

                    #  subMessage data looks like this:
                    #
                    #  [{"lat": 30.563303425649885, "lng": -87.67828041172979},
                    #   {"lat": 30.563313844580183, "lng": -87.6782802005235}, ... ]
                    message_json_str = message["subMessage"]
                    message_json = json.loads(message_json_str)
                    #baswell update robot_state.waypoints_in_autopilot with these values
                    load_mission_success = await waypoint_wizard.load_mission_data_from_mission_waypoints(message_json)
                    if load_mission_success:
                        await self.network.simple_message_send("load_mission_reply", "1")
                    else:
                        await self.network.simple_message_send("load_mission_reply", "0")
                    print(f"load took {(time.time()-load_begin_time):.2f} seconds")
                pass
            pass
        except:
            traceback.print_exc()

    # Define WebSocket callback functions
    async def process_websocket_message(self,
                        message:str,
                        websock:websockets.client.WebSocketClientProtocol) -> None:
        """
        Process the incoming JSON message.

        Args:
            message (str): JSON message to parse
            websock (websockets.client.WebSocketClientProtocol): Websocket connection
            to potentially send replies on
        """
        message_json = json.loads(message)
        messageType = message_json["messageType"]
        message_json_first_50 = f"{message_json}"
        if len(message_json_first_50) > 50:
            message_json_first_50 = message_json_first_50[:50]
        logging.debug(f"websocket received message: {message_json_first_50}")
        if messageType == "command":
            message = message_json["message"].lower()
            #await self.process_command_message(message, websock.send)
            util.asyncio_create_task_disappear_workaround(self.process_command_message(message, websock.send))
            #asyncio.ensure_future()
        elif messageType == "meta":
            message_str = message_json["message"]
            message_json = json.loads(message_str)
            #await self.process_meta_message(message_json)
            util.asyncio_create_task_disappear_workaround(self.process_meta_message(message_json))
        elif messageType == Constants.STARTUPDATA_MESSAGE_TYPE:
            message_json = json.loads(message_json["message"])
            base_station_id = message_json["base_station_id"]
            robot_state.set_correction_uri(self.config, base_station_id)
        elif messageType == "correction":
            # we need to
            # 1 -- pull out the encoded binary rtcm message into a local variable
            # 2 -- base64decode variable from above into binary data
            # 3 -- send binary data to gps connection
            try:
                rtcm_as_string = message_json["message"]
                robot_state.rtcm_as_bytes = base64.b85decode(rtcm_as_string)
                robot_state.last_time[LastTime.RTCM_AS_BYTES] = time.time()

                logging.debug("baswell async calling write_to_serial(...)")

                #Baswell July 11, 2024 --> I would rather call the write_to_serial method
                #using the asyncio_create_task_disappear_workaround method instead of
                #directly awaiting it, but I'm wondering if, after a few hours,
                #somehow the message written to the serial port gets jacked
                #up. The issue I'm seeing is this: after a few hours,
                #the fix type on the robot goes back to 3 and when
                #we restart the autopilot script (i.e. via re.sh)
                #the fix goes back to 4/5/6. I probably need
                #to figure out a way to log what/when/if
                #serial messages are written.
                #util.asyncio_create_task_disappear_workaround(self.serial.write_to_serial(robot_state.rtcm_as_bytes))
                websocket_received_data = await asyncio.wait_for(self.serial.write_to_serial(robot_state.rtcm_as_bytes), timeout=10)
            except Exception as err:
                logging.error(f"Error in RTCM correction receiving/parsing/serial "
                            f"port writing: {err}")
                traceback.print_exc()
                logging.info("Let's try to re-establish write_serial_port_gnss_corrections")
                try:
                    await self.serial.close_ublox_serial_port()
                    #baswell March 1, 2023 -- removed line below for testing u-blox PointPerfect
                    robot_state.write_serial_port_gnss_corrections = await self.serial.ublox_serial_port()
                    logging.info("Looks like we've successfully re-established the"
                                " serial port connection")
                except Exception as e:
                    logging.error(f"Error connecting to u-blox gnss receiver: {e}")
                    traceback.print_exc()
        elif messageType == "ping":
            # reply back (pong) with original message data
            pong_message = ('{ "messageType":"pong", "origin":"'
                        + str(message_json["origin"]) + '", "time": '
                        + str(message_json["time"]) + "}")

            latency = time.time()*1000-message_json["time"]
            logging.debug("LATENCY WebSocket from client to server:")
            logging.debug(f"{latency}")
            logging.debug(f"Sending back pong_message: {pong_message}")
            util.asyncio_create_task_disappear_workaround(websock.send(pong_message))
        elif messageType == "rtc-signal":
            # this is an offer from the client -- we want to call pc.signal (or
            # whatever the method is to signal the offer to our rtc
            # connection) -- then we want to reply back on this
            # websocket with an "rtc-signal" messageType with
            # the pc.signal sdp response as the message
            received_message = message_json["message"]
            logging.debug(f"Received rtc-signal: {json.dumps(received_message)}")
            if "sender" in received_message:
                logging.debug("sender is in the received_message -- this just means "
                            "that we're getting back the message we just sent")
                logging.debug("at some point i'd like to get the websocket channel "
                            "configured so that we don't get an echo")
                logging.debug("of every message we send (both here and over in the "
                            "javascript companion code)")
                logging.debug("...but until that day, we'll just handle the echo in"
                            "code")
            else:
                await self.network.build_rtc_connection(message_json, self, websock)
                
    async def process_command_message(self,
                                      message:str, 
                                      send_respose_func:any) -> None:
        """
        Process incoming command from client.
        """
        if message == "stop":
            #stop this homie!
            #this is what that means command-wise:
            #set mode to hold
            #arm safetyon
            #mavproxy_send_command("mode hold")
            raspberry_pi.blades_and_wheels_power_off()
            await flight_controller.hold()
        elif message == "start":
            await flight_controller.start_robot()
        elif message == "blades_and_wheels_power_on":
            raspberry_pi.blades_and_wheels_power_on()
        elif message == "blades_and_wheels_power_off":
            raspberry_pi.blades_and_wheels_power_off()
        elif message == "reboot_pi":
            raspberry_pi.reboot_pi()
        elif message == "start_vpn":
            await self.network.start_vpn()
        elif message == "stop_vpn":
            await self.network.stop_vpn()
        elif message == "mode_manual":
            #ensure motor throttle is neutral before arming / putting in manual mode
            flight_controller.set_rc_channel_pwm(1, robot_state.servo1_trim)
            #ensure motor throttle is neutral before arming / putting in manual mode
            flight_controller.set_rc_channel_pwm(3, robot_state.servo3_trim)
            robot_state.mutil.arducopter_arm()
            flight_controller.set_mode("MANUAL")
            await asyncio.sleep(.1)
            flight_controller.set_mode("MANUAL")
        elif message == "mode_hold":
            await flight_controller.hold()
        elif message == "mode_hold_keep_wp":
            await flight_controller.hold_keep_wp()
        elif message == "reboot_autopilot":
            flight_controller.reboot_autopilot()
        # TODO BASWELL -- I probably need some kind of "wp list" call to the
        # autopilot ever so often to ensure that the mission that the user
        # displays on the web UI is the same as the mission loaded in the
        # autopilot. Of course, it would be nice if there was some kind
        # of hash tied to a mission to make this call really quick --
        # i.e. if the "mission hash" of the autopilot is the same
        # as the "mission hash" last time we checked
        #
        #
        # elif message == "wp-list":
        #     ##logging.debug("we're in wp-list on client.py!!")
        #     try:
        #         waypoints = []
        #         # new wp logic using "wp list" instead of "wp save"
        #         # to get more precise lat/lng data
        #         ret.sendline("wp list")
        #         ret.expect("Saved waypoints to way.txt")
        #         rawWpDataList = ret.before.splitlines()
        #         x = 0
        #         for row in rawWpDataList:
        #             rowSplit = row.split()
        #             if len(rowSplit) >= 2:
        #                 if(rowSplit[0] == "16" and rowSplit[1] == "3"):
        #                     waypoints.append({"seq": x, "lat": float(rowSplit[2]), "lng": float(rowSplit[3])})
        #                     x = x+1
        #         wp_list_reply_string = '{ "messageType":"command-reply", "message":"wp-list", "waypoints": ' + json.dumps(waypoints) + '}'
        #         await send_respose_func(wp_list_reply_string)
        #     except Exception as err:
        #         logging.warn("Error in wp-list: {0}".format(err))
        #         traceback.print_exc()

    # time_start = None

    # def current_stamp() -> int:
    #     global time_start

    #     if time_start is None:
    #         time_start = time.time()
    #         return 0
    #     else:
    #         return int((time.time() - time_start) * 1000000)

    # async def create_data_channel(rtcPC:RTCPeerConnection):
    #     channel = rtcPC.createDataChannel("somedata4")
    #     channel_log(channel, "created by local party")

    #     async def send_pings():
    #         while True:
    #             channel_send(channel, "ping %d" % current_stamp())
    #             await asyncio.sleep(1)

    #     @channel.on("open")
    #     def on_open():
    #         asyncio.ensure_future(send_pings())

    #     @channel.on("message")
    #     def on_message(message):
    #         channel_log(channel, message)

    #         if isinstance(message, str) and message.startswith("pong"):
    #             elapsed_ms = (current_stamp() - int(message[5:])) / 1000
    #             logging.debug(" RTT %.2f ms" % elapsed_ms)
