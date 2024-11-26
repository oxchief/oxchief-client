"""
Author: Wayne Baswell

Holds the entire state of the robot.
"""
import threading
import time

from asyncio import StreamWriter
from collections import defaultdict
from local_storage import LocalStorage

from config import Config

autopilot_data = defaultdict(lambda:False)
"""latest data pulled in via MavLink messages"""

last_time = defaultdict(lambda:-1)
"""holds the last time various kinds of messages were received"""

client_joystick_x = 0.0
"""last x axis reading we received from client joystick: -1 < val <= 1"""

client_joystick_y = 0.0
"""last y axis reading we received from client joystick: -1 < val <= 1"""

mutil = None
"""mutil is the mavutil.mavlink_connection(...) variable"""

mavproxy = None
"""mavproxy serial connection object -- set up in autopilot_client.py"""

wploader = None
"""mavproxy waypoint loader, i.e. mavwp.MAVWPLoader"""

waypoints_in_autopilot = []
"""Holds the waypoints for the mission currently loaded in the autopilot"""

waypoints_in_mission = []
"""
Holds the waypoints for the complete mission -- i.e. maybe 
more than those currently in the autopilot
"""

last_autopilot_loaded_waypoint_number_end = -1
"""
waypoint number of the last waypoint loaded into the autopilot flight controller
this number is also the index of the waypoint in waypoints_in_mission -- even
though waypoints_in_mission is a zero-based list, the first element in
waypoints_in_mission is the home element
"""

last_autopilot_loaded_waypoint_number_start = -1


lock_mavproxy = threading.RLock()
"""
Lock to keep different threads from colliding while 
accessing the mavproxy serial connection
"""

local_storage = LocalStorage()

robot_json_status_string = ""
"""
Status overview/summary that the client UI uses to display the most important
robot data on the robot main screen. This is the most recent value
calculated at `flight_controller.robot_json_status_string(..)`.
"""

time_last_stop_start = time.time()
"""
Time most recently started or stopped Flight Controller. This data should
probably be saved as 2 pieces of data (i.e. time_last_stop and 
time_last_start) and then just OR those to find this value.
"""

write_serial_port_gnss_corrections:StreamWriter = None
"""serial port connected to u-blox gnss receiver where we write RTCM data"""

uri_correction_verbose = False
"""
RTCM Correction URI. We pull this in initially from startupdata. Note
that this uri is stored in the `robot_state` module where several 
other uris are stored in the `config.Config` class -- the 
reason for this is that this uri may be changed by
the user in the app, but the other URIs are
constant after app startup.
"""

mavproxy_port_name = ""
"""holds the name of the tty we're using for Mavproxy, i.e. /dev/ttyACM0"""

mavutil_port_name = ""
"""holds the name of the tty we're using for mavutil, i.e. /dev/ttyACM1"""

rtcm_as_bytes = None
"""most recent binary gnss correction data received """

ap_fix_type = None
"""Autopilot GNNS Fix Type"""

servo1_min = 1000 #default
"""Servo 1 min value"""

servo1_trim = 1500 #default
"""Servo 1 trim value"""

servo1_max = 2000 #default
"""Servo 1 max value"""

servo3_min = 1000 #default
"""Servo 3 min value"""

servo3_trim = 1500 #default
"""Servo 3 trim value"""

servo3_max = 2000 #default
"""Servo 3 max value"""

manual_mode_via_client_ui_joystick = False

battery_multiplier = 1.0

def end_waypoint_number_of_waypoints_in_autopilot()->int:
    return len(waypoints_in_autopilot)-1

def end_waypoint_number_of_complete_mission()->int:
    return len(waypoints_in_mission)-1

def set_correction_uri(config:Config, base_station_id):
    """
    Set gnss correction URI

    Args:
        base_station_id (_type_): Base station ID to get corrections from
    """
    global uri_correction_verbose
    if not isinstance(base_station_id, int):
        base_station_id = -1
    uri_correction_verbose = f"{config.wss_uri_prefix}/correction/{base_station_id}/all/"
    
def build_servo_configs_as_json_string():
    """
    Build servo config JSON

    Returns:
        str: JSON string
    """
    return f'{{"servo1_min":{servo1_min},"servo1_trim":{servo1_trim},"servo1_max":{servo1_max},'\
        f'"servo3_min":{servo3_min},"servo3_trim":{servo3_trim},"servo3_max":{servo3_max}}}'
