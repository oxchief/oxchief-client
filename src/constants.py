"""
Author: Wayne Baswell

App-wide constants
"""

class MavMessageType:
    """
    Mavlink message types
    """
    BATTERY2 = 'BATTERY2'
    BATTERY_STATUS = 'BATTERY_STATUS'
    EKF_STATUS_REPORT = 'EKF_STATUS_REPORT'
    GPS_RAW_INT = 'GPS_RAW_INT'
    GLOBAL_POSITION_INT = 'GLOBAL_POSITION_INT'
    MISSION_CURRENT = 'MISSION_CURRENT'
    HWSTATUS = 'HWSTATUS'
    VFR_HUD = 'VFR_HUD'
    HEARTBEAT = 'HEARTBEAT'
    NAV_CONTROLLER_OUTPUT = 'NAV_CONTROLLER_OUTPUT'
    UTM_GLOBAL_POSITION = 'UTM_GLOBAL_POSITION'
    WAYPOINT_CURRENT = 'WAYPOINT_CURRENT'
    SERVO_OUTPUT_RAW = 'SERVO_OUTPUT_RAW' # servo1_raw and servo3_raw
    SYS_STATUS = "SYS_STATUS"
    NAV_CONTROLLER_OUTPUT = 'NAV_CONTROLLER_OUTPUT' # xtrack_error

class AutopilotMode:
    """
    reference: https://ardupilot.org/rover/docs/parameters.html#initial-mode-initial-driving-mode
    0  Manual
    1  Acro
    3  Steering
    4  Hold
    5  Loiter
    6  Follow
    7  Simple
    10	Auto
    11	RTL
    12	SmartRTL
    15	Guided
    """
    MODE_MANUAL = 0
    MODE_HOLD = 4
    MODE_AUTO = 10
    MODE_INITIALISING = 16

class LastTime:
    """
    We use these contants when determining the last time various kinds of 
    messages have been received
    """
    META_X = 'LAST_TIME_META_X'
    META_Y = 'LAST_TIME_META_Y'
    META_XY_IN_LOCAL_ROBOT_TIME = 'META_XY_IN_LOCAL_ROBOT_TIME'
    GOTO_PREV_WP = 'LAST_TIME_GOTO_PREV_WP'
    GOTO_NEXT_WP = 'LAST_TIME_GOTO_NEXT_WP'
    GOTO_WP_PLUS_50 = 'GOTO_WP_PLUS_50'
    GOTO_WP_MINUS_50 = 'GOTO_WP_MINUS_50'
    META_LOAD_MISSION = 'LAST_TIME_META_LOAD_MISSION'
    CONFIG_GPS1_SAVE = 'LAST_TIME_CONFIG_GPS1_SAVE'
    CONFIG_AHRS_SAVE = 'LAST_TIME_CONFIG_AHRS_SAVE'
    CONFIG_ETC_SAVE = 'LAST_TIME_CONFIG_ETC_SAVE'
    RTCM_AS_BYTES = 'LAST_TIME_RTCM_AS_BYTES'

class Constants:
    """
    Catch-all class for constants that I don't (yet) want to categorize more 
    specifically
    """
    WAYPOINT_LOAD_COUNT_INITIAL = 100
    
    #TODO maybe make this bigger once we're sure the 
    # infinite-waypoints functionality works fine
    WAYPOINT_LOAD_COUNT_SUBSEQUENT = 250
    
    DISTANCE_XTRACK_ERROR_ACTIVE_IN_METERS = 1
    XTRACK_SECONDS_TO_ACTIVATE = 5
    
    DISTANCE_SHUFFLE_DETECT_ACTIVE_IN_METERS = 2.0
    SHUFFLE_DETECT_SECONDS_TO_ACTIVATE = 10

    DISTANCE_NO_PROGRESS_FULL_THROTTLE_STUCK_IN_METERS = 0.5
    FULL_THROTTLE_STUCK_SECONDS_TO_ACTIVATE = 10

    MAVPROXY_SCRIPT = "/root/.local/bin/mavproxy.py"
    """mavproxy script path inside the running container"""
    
    STARTUPDATA_MESSAGE_TYPE = "startupdata"
    
    DEVICES_FILENAME = "temp/devices.txt"
    """File of devicepath - names created by `list_usb` in `oxchief.sh`"""
    
    DEVICES_FILENAME_REALSENSE = "temp/devices2.txt"
    
    SHUTOFF_RELAY_GPIO_PIN = 21
    
    COMPASS_VAR_LIMIT = 10
    COMPASS_VAR_BOGUS_COMPASS_MAX_SECONDS = 10

    GYRATING_CHECK_MIN_DISTANCE_FROM_WAYPOINT_TO_RUN_THIS_CHECK_IN_METERS = 10.0
    GYRATING_CHECK_MAX_ALLOWABLE_WOBBLE_IN_DEGREES = 15
    GYRATING_CHECK_MIN_TIME_BETWEEN_RESETS_IN_SECONDS = 45
