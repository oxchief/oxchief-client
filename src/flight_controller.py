"""
Author: Wayne Baswell

Flight Controller(i.e. Pixhawk) operations

This module contains functions for controlling the flight controller (Pixhawk) 
and performing various operations such as setting the autopilot mode, 
rebooting the autopilot, checking if the flight controller is 
armed, reading parameters from the autopilot, and 
controlling the RC channels.

Functions:
- set_mode(mode_string: str) -> None: Set autopilot/flight mode.
- reboot_autopilot() -> None: Disarm Flight Controller and restart it.
- is_armed() -> bool: Determine if flight controller is armed.
- get_flight_mode() -> int: Get autopilot/flight mode as an integer.
- read_single_param(name: str) -> any: Read a single parameter from the autopilot.
- get_flight_mode_as_string() -> any: Get autopilot/flight mode as a string.
- hold_keep_wp() -> None: Stop the robot but keep the current waypoint.
- hold() -> None: Stop the robot and put it in HOLD mode.
- start_robot() -> None: Start the robot and put it in AUTO mode.
- hold_sleep_start_robot(seconds) -> None: Put the robot in hold, wait for the specified number of seconds, and then start the robot.
- convert_joystick_to_pwm(speed: float) -> int: Convert joystick to PWM input value for FC.
- set_rc_channel_pwm(channel_id: int, pwm: int = 1500) -> None: Set RC channel PWM value.
- set_rc_channels_from_joystick(x: float, y: float) -> None: Set RC channel 1 and 3 PWM values from joystick x and y.
- calculate_channel_one_and_three_from_x_y(x: float, y: float) -> tuple[int, int]: Calculate channel 1 and 3 PWM values from joystick x and y.
- calculate_wheel_left_right_from_x_y(x: float, y: float) -> tuple[float, float]: Translate joystick control into left/right servo values.
- end_of_mission_cleanup() -> None: Disarm and cleanup at the end of the mission.
- robot_json_status_string() -> str: Build and return the robot JSON status string based on the latest robot data.
"""

import asyncio
import logging
import time
import traceback

from pymavlink import mavutil

from constants import MavMessageType, AutopilotMode
import robot_state
from robot_state import autopilot_data
import waypoint_wizard

def set_mode(mode_string:str) -> None:
    """Set autopilot/flight mode"""
    # Get mode ID
    mode_id = robot_state.mutil.mode_mapping()[mode_string]
    # Set new mode

    if mode_string.upper() == "MANUAL":
        robot_state.manual_mode_via_client_ui_joystick = True
    else:
        robot_state.manual_mode_via_client_ui_joystick = False
    
    robot_state.mutil.mav.set_mode_send(
        robot_state.mutil.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        mode_id)

def reboot_autopilot() -> None:
    """ Disarm Flight Controller and restart it """
    robot_state.mutil.arducopter_disarm()
    robot_state.mutil.reboot_autopilot()

def is_armed() -> bool:
    """ Determine if flight controller is armed """
    try:
        return bool(robot_state.mutil.wait_heartbeat().base_mode & 0b10000000)
    except:
        return False

def get_flight_mode() -> int:
    """Get autopilot/flight mode as int"""
    if (autopilot_data[MavMessageType.HEARTBEAT] and
        autopilot_data[MavMessageType.HEARTBEAT].system_status != 0):
        return autopilot_data[MavMessageType.HEARTBEAT].custom_mode

    return -1

def read_single_param(name: str) -> any:
    """
    Read in a single param from autopilot
    Returns None if param not found else `{"param_name": param_value}`
    """
    robot_state.mutil.param_fetch_one(name)
    # TODO: Check if this automatically updates master.params
    message = robot_state.mutil.recv_match(type="PARAM_VALUE",
                                          blocking=True,
                                          timeout=1)
    if message is None:
        return None
    return message.param_value

def get_flight_mode_as_string() -> any:
    """Get autopilot/flight mode as string"""
    mode = get_flight_mode()

    if mode == -1:
        return False
    if mode == AutopilotMode.MODE_AUTO:
        return "auto"
    if mode == AutopilotMode.MODE_MANUAL:
        return "manual"
    if mode == AutopilotMode.MODE_HOLD:
        return "hold"
    if mode == AutopilotMode.MODE_INITIALISING:
        return "initialising"

    return "unknown mode: " + str(mode)

async def hold_keep_wp() -> None:
    """Stop robot but keep current waypoint"""
    current_waypoint = 1
    mission_current = autopilot_data[MavMessageType.MISSION_CURRENT]
    if mission_current:
        current_waypoint = mission_current.seq
    await hold()
    robot_state.mutil.waypoint_set_current_send(current_waypoint)

async def hold() -> None:
    """Stop robot -- i.e. put in HOLD mode"""
    robot_state.time_last_stop_start = time.time()
    robot_state.mutil.arducopter_disarm()
    set_mode('HOLD')
    #I'm not sure if the following code makes __stop__ more likely to actually happen,
    #but that's the goal -- so what we're doing is just going to sleep
    #for .1 seconds and then sending the hold command again
    #(i.e. trying to cover on the chance that
    #the first hold command failed)
    await asyncio.sleep(.1)
    set_mode('HOLD')

async def start_robot() -> None:
    """Start robot -- i.e. put in AUTO mode"""
    robot_state.time_last_stop_start = time.time()
    #blades_and_wheels_power_on()
    robot_state.mutil.arducopter_disarm()
    set_mode('AUTO')
    robot_state.mutil.arducopter_arm()
    await asyncio.sleep(.1)
    set_mode('AUTO')
    robot_state.mutil.arducopter_arm()

async def hold_sleep_start_robot(seconds) -> None:
    """
    Three things:
    1. Put robot in hold
    2. Wait specified number of seconds
    3. Start robot

    Args:
        seconds (_type_): Seconds to wait between holding and starting robot
    """
    await hold_keep_wp()
    await asyncio.sleep(seconds)
    await start_robot()

def convert_joystick_to_pwm_dynamic(speed: float, minimum_pwm: int, midpoint_pwm: int, maximum_pwm: int) -> int:
    """
    DEPRECATED
    
    I thought we needed this, but it turns out we don't. The flight controller
    expects the pwm input values to be 1000 min, 1500 trim, and 2000 max.
    It then maps those values to the output values that the user has set in
    the flight controller, i.e. SERVO1_MIN, SERVO1_TRIM, SERVO1_MAX and
    SERVO3_MIN, SERVO3_TRIM, SERVO3_MAX. So, we don't need to do any
    mapping here. We just need to send the pwm values to the flight
    controller and it will do the mapping for us.
    
    Converts the joystick input to a corresponding PWM value based on the given parameters.

    Args:
        speed (float): The joystick value in percentage (-100 to 100).
        minimum_pwm (int): The minimum PWM value.
        midpoint_pwm (int): The PWM value at the midpoint.
        maximum_pwm (int): The maximum PWM value.

    Returns:
        int: The calculated PWM value.

    """
    # Ensure speed is within the valid range
    speed = max(min(speed, 100), -100)

    # Map speed to the corresponding PWM value
    if speed == 0:
        return midpoint_pwm
    elif speed < 0:
        return int(midpoint_pwm + (midpoint_pwm - minimum_pwm) * (speed / 100))
    else:
        return int(midpoint_pwm + (maximum_pwm - midpoint_pwm) * (speed / 100))
    

def convert_joystick_to_pwm(speed:float) -> int:
    """
    input "speed" param is -100 <= speed <= 100
    
    -100 == Full throttle reverse
    0 == Stop
    100 == Full throttle forward
    
    this assumes that the flight controller expects the PWM INPUT 
    min, trim, max values are 1000, 1500, 2000
    
    Note that this is different from the PWM OUTPUT values -- which
    are defined by the user on the Flight Controller, i.e. in 
    SERVO1_MIN, SERVO1_TRIM, SERVO1_MAX and SERVO3_MIN, 
    SERVO3_TRIM, SERVO3_MAX
    """
    return int(1500 + speed*5)

def set_rc_channel_pwm(channel_id:int, pwm=1500) -> None:
    """ 
    Set RC channel pwm value
    
    Parameters:
        channel_id (int): Channel ID
        pwm (int, optional): Channel pwm value -- generally between 1000-2000

    More information about Joystick channels
    here: https://www.ardusub.com/operators-manual/rc-input-and-output.html#rc-inputs
    """
    if channel_id < 1 or channel_id > 18:
        logging.debug("Channel does not exist.")
        return

    logging.debug(f"channel {channel_id} pwm: {pwm}")

    # Mavlink 2 supports up to 18 channels:
    # https://mavlink.io/en/messages/common.html#RC_CHANNELS_OVERRIDE
    rc_channel_values = [65535 for _ in range(18)]
    rc_channel_values[channel_id - 1] = pwm

    robot_state.mutil.mav.rc_channels_override_send(
        robot_state.mutil.target_system,                # target_system
        robot_state.mutil.target_component,             # target_component
        *rc_channel_values)                  # RC channel list, in microseconds.

def set_rc_channels_from_joystick(x:float, y:float) -> None:
    """
    Set rc channel 1,3 pwm values from joystick x,y 

    Args:
        x (float): -1 <= x <= 1 (up and down)
        y (float): -1 <= y <= 1 (left and right)
    """
    one, three = calculate_channel_one_and_three_from_x_y(x, y)
    set_rc_channel_pwm(1, one)
    set_rc_channel_pwm(3, three)
    logging.info(f"channel 1: {one}  3: {three}")

def calculate_channel_one_and_three_from_x_y(x:float, y:float) -> tuple[int, int]:
    """
    For manual driving the robot, this calculates channel 1 and channel 3 (left
    and right wheel control) from the x,y joystick values.

    Args:
        x (float): -1 <= x <= 1 (up and down)
        y (float): -1 <= y <= 1 (left and right)

    Returns:
        tuple[int, int]: tuple of pwm values for [left,right] wheel controls
    """
    x*=100
    y*=100
    
    # left_min = robot_state.servo1_min
    # left_trim = robot_state.servo1_trim
    # left_max = robot_state.servo1_max
    
    # right_min = robot_state.servo3_min
    # right_trim = robot_state.servo3_trim
    # right_max = robot_state.servo3_max
    
    # left = convert_joystick_to_pwm_dynamic(x, left_min, left_trim, left_max)
    # right = convert_joystick_to_pwm_dynamic(y, right_min, right_trim, right_max)
    left = convert_joystick_to_pwm(x)
    right = convert_joystick_to_pwm(y)
    
    return left, right

def calculate_wheel_left_right_from_x_y(x:float, y:float) -> tuple[float, float]:
    """
    Translate the joystick control into a left/right servo value.

    Parameters:
        x (float): -1 <= x <= 1 (up and down)
        y (float): -1 <= y <= 1 (left and right)

    Returns:
        tuple[float, float]: left_servo_value,right_servo_value
            where
            -100 <= left <= 100
            -100 <= right <= 100
            i.e.
            (-100, -100) --> full speed reverse!
            (100, 100)   --> full speed ahead!
            (0,0)        --> neutral
    """

    x*=100
    y*=100

    x*=-1
    y*=-1

    #Calculate R+L (Call it V): V = (100-ABS(X)) * (Y/100) + Y
    v = (100-abs(x)) * (y/100) + y

    #Calculate R-L (Call it W): W = (100-ABS(Y)) * (X/100) + X
    w = (100-abs(y)) * (x/100) + x

    #Calculate R: R = (V+W) / 2
    r = (v+w) / 2

    #Calculate L: L= (V-W) / 2
    l = (v-w) / 2

    logging.debug("left: %s right: %s", l, r)
    return l, r

async def end_of_mission_cleanup() -> None:
    """ At the end of the mission, so disarm and cleanup """
    print("end of the mission -- disarm and cleanup")
    await hold()
    await asyncio.sleep(1.0)

    #reload mission back to where it the next robot run
    #will begin at the very beginning of the mission
    print("end of mission -- refresh mission")
    wp_in_mission = robot_state.waypoints_in_mission.copy()
    load_mission_success = \
        await waypoint_wizard.load_mission_data_from_mission_waypoints(wp_in_mission)
    print(f"end of mission -- refresh mission success: {load_mission_success}")
    robot_state.mutil.waypoint_set_current_send(1)

async def robot_json_status_string()->str:
    """
    Build and return `robot_state.robot_json_status_string` based on latest robot
    data we've pulled into the `robot_state.autopilot_data[..]` dict via the
    mavutil stream.
    
    Returns:
        str: Robot json status
    """
    the_next_waypoint = -1
    the_speed = -1
    the_heading = -1
    the_lat = -1
    the_lng = -1
    the_fix_type = -1
    the_battery_voltage = -1
    the_hw_voltage = -1
    servo1_raw = -1
    servo3_raw = -1
    xtrack_error = -1

    try:
        gps_raw = robot_state.autopilot_data[MavMessageType.GPS_RAW_INT]
        global_position_int = robot_state.autopilot_data[MavMessageType.GLOBAL_POSITION_INT]

        the_heading = global_position_int.hdg / 10**2 if global_position_int else the_heading
        the_lat = global_position_int.lat / 10**7 if global_position_int else the_lat
        the_lng = global_position_int.lon / 10**7 if global_position_int else the_lng
        the_fix_type = robot_state.ap_fix_type = gps_raw.fix_type if gps_raw else the_fix_type
        the_wp_dist = waypoint_wizard.get_wp_dist_in_meters()

        mission_current = robot_state.autopilot_data[MavMessageType.MISSION_CURRENT]
        if mission_current:
            the_next_waypoint = mission_current.seq
            logging.info(f"*******  Current waypoint: {str(mission_current.seq)}")

        battery_status = robot_state.autopilot_data[MavMessageType.BATTERY_STATUS]

        if battery_status:
            if battery_status.voltages:
                the_battery_voltage = battery_status.voltages[0]*robot_state.battery_multiplier

        hwstatus = robot_state.autopilot_data[MavMessageType.HWSTATUS]
        if hwstatus:
            the_hw_voltage = hwstatus.Vcc

        vfr_hud = robot_state.autopilot_data[MavMessageType.VFR_HUD]
        if vfr_hud:
            the_speed = round(vfr_hud.groundspeed, 2)

        # servo1_raw and servo3_raw
        servos = robot_state.autopilot_data[MavMessageType.SERVO_OUTPUT_RAW]
        if servos:
            servo1_raw = servos.servo1_raw
            servo3_raw = servos.servo3_raw

        # xtrack_error
        nav = robot_state.autopilot_data[MavMessageType.NAV_CONTROLLER_OUTPUT]
        if nav:
            xtrack_error = round(nav.xtrack_error, 2)

        next_wp_lat = next_wp_lng = -1
        next_wp = waypoint_wizard.get_next_wp()
        if next_wp:
            next_wp_lat = next_wp["lat"]
            next_wp_lng = next_wp["lng"]

        mode = robot_state.mutil.flightmode.lower() # get_flight_mode_as_string()
        mode_string = ""
        if mode:
            mode_string = ', "mode": "' + mode + '"'

        robot_state.robot_json_status_string = (
            '{ "messageType":"location", "time":'+
            str(time.time()) +
            ', "lat":"'+str(the_lat)+'", "lng":"'+str(the_lng) +
            '", "heading":' + str(the_heading) +
            ', "extra_fields": {' +
            '  "battery_voltage":' + str(the_battery_voltage) + 
            ', "hw_voltage":' + str(the_hw_voltage) + 
            ', "next_wp":' + str(the_next_waypoint) +
            ', "next_wp_lat":' + str(next_wp_lat) +
            ', "next_wp_lng":' + str(next_wp_lng) +
            ', "speed":' + str(the_speed) +
            ', "wp_dist": ' + str(the_wp_dist) +
            ', "servo1": ' + str(servo1_raw) +
            ', "servo3": ' + str(servo3_raw) +
            ', "xtrack": ' + str(xtrack_error) +
            mode_string +
            '}, "fix_type":' + str(the_fix_type) + "}")

        logging.info(f"JSON data : {robot_state.robot_json_status_string}")

    except Exception as e:
        logging.error("Caught exception in flight_controller.robot_json_status_string(..):")
        logging.error(e)
        traceback.print_exc()
        await asyncio.sleep(.5)

    return robot_state.robot_json_status_string
