#!/usr/bin/env python3
#pylint: disable = logging-fstring-interpolation
"""
Author: Wayne Baswell

Handles loading waypoints into the Flight Controller. 

Motivation:

There is a limit to the number of waypoints that many Flight Controllers will 
accept (as of 2024 this number is around 700 waypoints). However, I want to
be able to run missions that may have many thousands of waypoints. So it
was necessary to come up with a bit of logic that breaks missions up
into smaller units that we can feed into the Flight Controller.
There is some babysitting that goes along with this -- 
for example, we have to keep an eye on the waypoint 
that our robot is currenty approaching, and if
it's the last loaded waypoint, we must check
to see if there are additional "pages"
of waypoints left in the mission.
If more waypoints exist, then
of course we have to load
them and keep an eye
on where we are
in the big
mission.

There are other scenarios where we must load a new page of waypoints such as:
 - User requests a waypoint prior to the existing loaded waypoints
 - User requests a waypoint beyond the existing loaded waypoints
"""
import asyncio
import logging
import os
import random
import string
import time

import haversine
from pymavlink import mavutil
from pymavlink.dialects.v20.ardupilotmega import MAVLink_mission_item_message

import robot_state
import flight_controller

from robot_state import autopilot_data #hash of live data off the autopilot
from constants import Constants, MavMessageType

def rand_alpha_num(length: int) -> str:
    """
    Build random alphanumeric string, i.e.
    
    rand_alpha_num(10) --> "NeyFGWxtf4"

    Parameters:
        length (int): length of string to generate

    Returns:
        string: random string
    """
    x = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return x

def build_waypoint_file_first_line() -> str:
    """
    Build the standard first line of the waypoint file

    Returns:
        string: Standard waypont file first line
    """
    return "QGC WPL 110"

def build_waypoint_file_lat_lng_line(index: int, lat: float, lng: float) -> str:
    """
    Build the standard waypoint line
    
    Parameters:
        index (int): Zero-based incrementing index that is the first element 
            in the waypoint line format (i.e. the first waypoint 
            is 0, the next is 1 and so on)
        lat (float): Latitude
        lng (float): Longitude

    Returns:
        string: Standard waypoint line
    """
    return str(index) + "\t0\t3\t16\t0\t0\t0\t0\t" + str(lat) + "\t" + str(lng) + "\t100.000000\t1"

def build_waypoints_string_from_mission_waypoints(waypoints: list[dict[str, float]]) -> str:
    """
    Build a big ArduPilot mission waypoint string that we send over to the
    client for loading into the autopilot
    
    Parameters:
        waypoints (list[dict[str, float]]): list of points arranged sequentially: 
            i.e. the first item in the array is the first waypoint 
            and the last item is the last waypoint.
            Example: 
            [{"lat": 1, "lng": -87.67828041172979},..]

    Returns: 
        string: ArduPilot mission waypoint string

    See Also:
        - https://mavlink.io/en/file_formats/ For more information 
            on the waypoint file format
    """
    mission_string: str = build_waypoint_file_first_line() + "\n"
    x = 0

    for waypoint in waypoints:
        lat = round(waypoint['lat'], 8)
        lng = round(waypoint['lng'], 8)
        mission_string += build_waypoint_file_lat_lng_line(x, lat, lng) + "\n"
        x += 1

    return mission_string

def has_location(cmd_id:int) -> bool:
    """
    Helper function for wp_to_mission_item_int(..)
    
    Parameters:
        cmd_id(int): Command ID
        
    Returns:
        boolean: If command has location
    """
    if cmd_id in mavutil.mavlink.enums['MAV_CMD'].keys():
        cmd_enum = mavutil.mavlink.enums['MAV_CMD'][cmd_id]
        # default to having location for older installs of pymavlink
        # which don't have the attribute
        return getattr(cmd_enum,'has_location',True)
    return False

def wp_to_mission_item_int(wp:MAVLink_mission_item_message) -> MAVLink_mission_item_message:
    """
    Convert a MISSION_ITEM to a MISSION_ITEM_INT. We always send as 
    MISSION_ITEM_INT to give cm level accuracy

    Parameters:
        wp (MAVLink_mission_item_message): Waypoint to check and ensure it's a
            centimeter level precision object

    Returns:
        MAVLink_mission_item_message: Centimeter level precision waypoint object
    """
    if wp.get_type() == 'MISSION_ITEM_INT':
        return wp
    if has_location(wp.command):
        p5 = int(wp.x*1.0e7)
        p6 = int(wp.y*1.0e7)
    else:
        p5 = int(wp.x)
        p6 = int(wp.y)
    wp_int = mavutil.mavlink.MAVLink_mission_item_int_message(wp.target_system,
                                                                wp.target_component,
                                                                wp.seq,
                                                                wp.frame,
                                                                wp.command,
                                                                wp.current,
                                                                wp.autocontinue,
                                                                wp.param1,
                                                                wp.param2,
                                                                wp.param3,
                                                                wp.param4,
                                                                p5,
                                                                p6,
                                                                wp.z)
    return wp_int

def load_waypoints_using_mavutil(filename:str) -> int:
    '''
    Load waypoints into flight controller.

    Parameters:
        filename (str): file name to load into flight controller

    Returns: 
        int: Number of waypoints loaded
    '''
    waypoints_loaded_count = -1
    try:
        #need to remove the leading and trailing quotes in filename
        waypoints_loaded_count = robot_state.wploader.load(filename.strip('"'))
    except Exception as msg:
        logging.info(f"Unable to load {filename} - {msg}")
        return 0
    logging.info(f"Loading {robot_state.wploader.count()} waypoints from {filename}")

    upload_start = time.time()
    robot_state.mutil.waypoint_clear_all_send()
    if waypoints_loaded_count == 0:
        return 0

    robot_state.mutil.waypoint_count_send(waypoints_loaded_count)

    for _ in range(waypoints_loaded_count):
        msg = robot_state.mutil.recv_match(type=['MISSION_REQUEST'], blocking=True)
        wp_int = wp_to_mission_item_int(robot_state.wploader.wp(msg.seq))
        robot_state.mutil.mav.send(wp_int)
        logging.info(f"Sending waypoint {msg.seq}")

    logging.info("Mission uploaded")

    upload_end = time.time()
    logging.info(f"Waypoint upload took {upload_end-upload_start} seconds")

    return waypoints_loaded_count

async def load_waypoints_into_autopilot() -> bool:
    """
    Load the waypoints in the robot_state.waypoints_in_autopilot list
    into the Flight Controller.
    
    Returns:
        bool: True if any waypoints were loaded into autopilot; 
            False otherwise
    """
    big_ardupilot_waypoints_file_string = \
        build_waypoints_string_from_mission_waypoints(robot_state.waypoints_in_autopilot)

    # ensure the temp directory exists
    if not os.path.exists(os.getcwd() + "/temp"):
        print("creating temp directory")
        os.makedirs(os.getcwd() + "/temp")
        
    waypoints_filename = os.getcwd() + "/temp/waypoints_" + rand_alpha_num(20) + ".txt"
    waypoints_file = open(waypoints_filename, "w")
    waypoints_file.write(big_ardupilot_waypoints_file_string)
    waypoints_file.close()
    logging.info(f'Built waypoints file {waypoints_filename}')
    logging.info('Loading waypoints file into autopilot...')

    count = load_waypoints_using_mavutil(waypoints_filename)

    return count > 0

def more_waypoints_to_load() -> bool:
    """
    True if there are more "pages" of waypoints -- i.e. if there are
    waypoints in the currently loaded mission beyond the set of 
    loaded waypoints.

    Returns:
        bool: Whether there are more waypoints to load.
    """
    return (robot_state.last_autopilot_loaded_waypoint_number_end
            < robot_state.end_waypoint_number_of_complete_mission())

def prior_waypoints_to_load() -> bool:
    """
    True if there are prior "pages" of waypoints -- i.e. if there are
    waypoints in the currently loaded mission prior to the set of 
    loaded waypoints.

    Returns:
        bool: Whether there are prior waypoints to load.
    """
    return (robot_state.last_autopilot_loaded_waypoint_number_end
            > Constants.WAYPOINT_LOAD_COUNT_INITIAL)

async def load_prior_round_of_waypoints() -> int:
    """
    Load prior round of waypoints.
    
    Returns:
        int: last waypoint number of mission loaded into autopilot
    """
    ret_val = -1
    if prior_waypoints_to_load():
        waypoint_start_load = -1
        waypoint_end_load = -1
        if (robot_state.last_autopilot_loaded_waypoint_number_end <=
            Constants.WAYPOINT_LOAD_COUNT_INITIAL+Constants.WAYPOINT_LOAD_COUNT_SUBSEQUENT):
            #this means we've only loaded one more round of waypoints so far
            waypoint_start_load = 0
            waypoint_end_load = Constants.WAYPOINT_LOAD_COUNT_INITIAL
            ret_val = Constants.WAYPOINT_LOAD_COUNT_INITIAL
        else:
            waypoint_start_load = (robot_state.last_autopilot_loaded_waypoint_number_start
                                   - Constants.WAYPOINT_LOAD_COUNT_SUBSEQUENT - 1)
            waypoint_end_load = robot_state.last_autopilot_loaded_waypoint_number_start
            ret_val = Constants.WAYPOINT_LOAD_COUNT_SUBSEQUENT

        #Get the first N+1 items from the complete set of waypoints to load into the autopilot
        robot_state.waypoints_in_autopilot = \
            robot_state.waypoints_in_mission.copy()[waypoint_start_load:waypoint_end_load+1]
        #insert first element twice since it's passed to the autopilot as the home waypoint
        #robot_state.waypoints_in_autopilot.insert(0, robot_state.waypoints_in_autopilot[0])
        robot_state.last_autopilot_loaded_waypoint_number_start = waypoint_start_load
        robot_state.last_autopilot_loaded_waypoint_number_end = waypoint_end_load
        robot_state.local_storage.save_mission_info_to_db() #save mission data to local sqllite db
        await load_waypoints_into_autopilot()
    return ret_val

async def load_next_round_of_waypoints() -> bool:
    """
    Load next round of waypoints into Flight Controller.

    Returns:
        bool: True if more waypoints were loaded into Flight Controller; 
            False otherwise
    """
    if more_waypoints_to_load():
        next_waypoint_start = robot_state.last_autopilot_loaded_waypoint_number_end
        # in theory you would add +1 to this value (i.e. robot_state.last_autopilot_loaded_waypoint_number_end+1),
        # but by making the finishing waypoint of the previous round the first waypoint of this round,
        # I think the autopilot should try to stay on the line between those 2 waypoints.
        # Otherwise, I think the autopilot would simply want to stay on the line
        # from where the robot currently is to the next waypoint -- this could
        # leave uncut grass if the robot isn't currently really close
        # to the final waypoint. TODO test if the robot behaves OK
        # here where you're giving it the first waypoint which
        # is really close to where it already is at
        next_waypoint_end = next_waypoint_start + Constants.WAYPOINT_LOAD_COUNT_SUBSEQUENT
        if next_waypoint_end > len(robot_state.waypoints_in_mission):
            next_waypoint_end = len(robot_state.waypoints_in_mission)
        robot_state.waypoints_in_autopilot = \
            robot_state.waypoints_in_mission.copy()[next_waypoint_start:next_waypoint_end+1]
        #insert first element twice since it's passed to the autopilot as the home waypoint
        robot_state.waypoints_in_autopilot.insert(0, robot_state.waypoints_in_autopilot[0])
        robot_state.last_autopilot_loaded_waypoint_number_start = next_waypoint_start
        robot_state.last_autopilot_loaded_waypoint_number_end = next_waypoint_end
        robot_state.local_storage.save_mission_info_to_db() #save mission data to local sqllite db
        return await load_waypoints_into_autopilot()
    return False

async def load_mission_data_from_mission_waypoints(waypoints: list[dict[str, float]]) -> bool:
    """
    Load waypoints from the client into the Flight Controller.

    Parameters:
        waypoints (list[dict[str, float]]): Waypoints to load into 
            Flight Controller

    Returns:
        bool: True if load succeeds, False if it fails
    """
    robot_state.waypoints_in_mission.clear() #make sure we're starting with an empty list

    first = True
    for waypoint in waypoints:
        lat = round(waypoint['lat'], 8)
        lng = round(waypoint['lng'], 8)
        wp = {'lat': lat, 'lng': lng}
        if first:
            first = False
            #Add first line twice (i.e. to set first point as home)
            robot_state.waypoints_in_mission.append(wp)

        robot_state.waypoints_in_mission.append(wp)

    #Get the first N+1 items from the complete set of waypoints to load into the autopilot
    robot_state.waypoints_in_autopilot = \
        robot_state.waypoints_in_mission.copy()[0:Constants.WAYPOINT_LOAD_COUNT_INITIAL+1]
    robot_state.last_autopilot_loaded_waypoint_number_start = 1
    robot_state.last_autopilot_loaded_waypoint_number_end = Constants.WAYPOINT_LOAD_COUNT_INITIAL
    robot_state.local_storage.save_mission_info_to_db() #save mission data to local sqllite db

    return await load_waypoints_into_autopilot()

async def goto_wp(num:int) -> None:
    """
    Instruct Flight Controller to go to specified waypoint.

    Parameters:
        num (int): Waypoint to go to.
    """
    robot_state.mutil.waypoint_set_current_send(num)
    #await load_next_round_of_waypoints()

async def goto_next_wp() -> None:
    """
    Instruct Flight Controller to go to next waypoint.
    
    If next waypoint is beyond the waypoints presently loaded in the Flight 
    Controller, then check if there is another page of waypoints available
    (i.e. more waypoints in this mission that we haven't loaded into the 
    Flight Controler) and load that page of waypoints and then tell
    the Flight Controller to go to the desired waypoint.
    
    If next waypoint is in the presently loaded waypoints,
    tell the Flight Controller to go to it.
    """
    mission_current = autopilot_data[MavMessageType.MISSION_CURRENT]
    if mission_current:
        current_waypoint = mission_current.seq
        next_waypoint = current_waypoint+1
        #check if next_waypoint is greater than last waypoint number in autopilot
        #if so, then we need to:
        # 1. put the robot in hold (if it's in auto mode)
        # 2. load next round of waypoints
        # 3. start the robot back up (if it was in auto mode) (assume it will
        #    automatically go to waypoint #1 of the newly loaded waypoints?)
        if (next_waypoint > robot_state.end_waypoint_number_of_waypoints_in_autopilot()
            and more_waypoints_to_load()):
            was_in_auto_mode = flight_controller.get_flight_mode_as_string() == "auto"

            if was_in_auto_mode:
                await flight_controller.hold()

            await load_next_round_of_waypoints()
            await asyncio.sleep(0.1)
            #we are already at waypoint 1 -- this should help reduce shuffling around at the outset
            await goto_wp(2)
            await asyncio.sleep(0.1)

            if was_in_auto_mode:
                await flight_controller.start_robot()

        else:
            await goto_wp(next_waypoint)

async def goto_prev_wp() -> None:
    """
    Instruct Flight Controller to go to previous waypoint.
    
    If (waypoint-1)<=1, we check to see if there is a page of prior 
    waypoints to load, and if so, load that page of waypoints 
    into the autopilot before setting the new waypoint. 
    
    If (waypoint-1) > 1, we just tell the Flight Controller to go to
    waypoint-1.
    """
    mission_current = autopilot_data[MavMessageType.MISSION_CURRENT]
    if mission_current:
        current_waypoint = mission_current.seq
        next_waypoint = current_waypoint-1
        if next_waypoint <= 1:
            if prior_waypoints_to_load():
                was_in_auto_mode = flight_controller.get_flight_mode_as_string() == "auto"

                if was_in_auto_mode:
                    await flight_controller.hold()

                waypoint_end = await load_prior_round_of_waypoints()
                await asyncio.sleep(0.1)
                await goto_wp(waypoint_end)
                await asyncio.sleep(0.1)

                if was_in_auto_mode:
                    await flight_controller.start_robot()
        else:
            wp = max(mission_current.seq-1, 1)
            await goto_wp(wp)

async def goto_wp_plus_50() -> None:
    """
    Instruct Flight Controller to go to waypoint+50. 
    
    If waypoint+50 is beyond the waypoints presently loaded in the Flight 
    Controller, then check if there is another page of waypoints 
    available (i.e. more waypoints in this mission that we 
    haven't loaded into the Flight Controler) and load 
    that page of waypoints and then tell the Flight
    Controller to go to the desired waypoint.
    
    If waypoint+50 is in the presently loaded waypoints, tell the
    Flight Controller to go to it.
    """
    mission_current = autopilot_data[MavMessageType.MISSION_CURRENT]
    if mission_current:
        current_waypoint = mission_current.seq
        next_waypoint = current_waypoint+50
        if next_waypoint > robot_state.end_waypoint_number_of_waypoints_in_autopilot():
            if more_waypoints_to_load():
                was_in_auto_mode = flight_controller.get_flight_mode_as_string() == "auto"

                waypoints_left_before_end_of_currently_loaded_mission = \
                    robot_state.end_waypoint_number_of_waypoints_in_autopilot() - current_waypoint
                fifty_more_actual_waypoints = (
                    50 - waypoints_left_before_end_of_currently_loaded_mission + 1)
                if was_in_auto_mode:
                    await flight_controller.hold()

                await load_next_round_of_waypoints()
                await asyncio.sleep(0.1)
                await goto_wp(fifty_more_actual_waypoints)
                await asyncio.sleep(0.1)

                if was_in_auto_mode:
                    await flight_controller.start_robot()
            else:
                #TODO if we get here, I think we should just make the following call:
                #await goto_wp(robot_state.end_waypoint_number_of_waypoints_in_autopilot())
                pass
        else:
            await goto_wp(next_waypoint)

async def goto_wp_minus_50() -> None:
    """
    Instruct Flight Controller to go to waypoint-50. 
    
    If (waypoint-50)<=1, we check to see if there is a page of prior waypoints 
    to load, and if so, load that page of waypoints into the  
    autopilot before setting the new waypoint. 
    
    If waypoint-50 > 1, we just tell the Flight Controller to go to waypoint-50.
    """
    mission_current = autopilot_data[MavMessageType.MISSION_CURRENT]
    if mission_current:
        current_waypoint = mission_current.seq
        next_waypoint = current_waypoint-50
        if next_waypoint <= 1:
            if prior_waypoints_to_load():
                was_in_auto_mode = flight_controller.get_flight_mode_as_string() == "auto"

                if was_in_auto_mode:
                    await flight_controller.hold()

                waypoint_end = await load_prior_round_of_waypoints()
                await asyncio.sleep(0.1)
                next_wp = max(waypoint_end+next_waypoint-1,1)
                await goto_wp(next_wp)
                await asyncio.sleep(0.1)

                if was_in_auto_mode:
                    await flight_controller.start_robot()
            else:
                await goto_wp(1)
        else:
            wp = max(mission_current.seq-1, 1)
            await goto_wp(next_waypoint)

def get_prev_wp_dist_in_meters() -> float:
    """
    Get distance from robot's current location to the previous waypoint (in 
    meters).
    """
    if (robot_state.waypoints_in_autopilot and
        len(robot_state.waypoints_in_autopilot) > 0 and
        autopilot_data[MavMessageType.GLOBAL_POSITION_INT] and
        autopilot_data[MavMessageType.MISSION_CURRENT]):
        #loc1 = (30.563420913154445,-87.67828495314278)
        #loc2 = (30.563420913154445,-87.67829820257457)

        utm = autopilot_data[MavMessageType.GLOBAL_POSITION_INT]
        loc1 = (utm.lat / 10**7, utm.lon / 10**7)#loc1 = (305634410, -876780089)

        wp_number = autopilot_data[MavMessageType.MISSION_CURRENT].seq - 1

        if wp_number < 0:
            return 0

        wp_loc = robot_state.waypoints_in_autopilot[wp_number]

        loc2 = (wp_loc["lat"], wp_loc["lng"])
        dist = haversine.haversine(loc1,loc2,unit=haversine.Unit.METERS)
        return abs(round(dist, 2))
    return -1

def get_wp_dist_in_meters() -> float:
    """
    Get distance from robot's current location to the next waypoint (in meters)
    """
    if (robot_state.waypoints_in_autopilot and
        len(robot_state.waypoints_in_autopilot) > 0 and
        autopilot_data[MavMessageType.GLOBAL_POSITION_INT] and
        autopilot_data[MavMessageType.MISSION_CURRENT]):
        #loc1 = (30.563420913154445,-87.67828495314278)
        #loc2 = (30.563420913154445,-87.67829820257457)

        utm = autopilot_data[MavMessageType.GLOBAL_POSITION_INT]
        loc1 = (utm.lat / 10**7, utm.lon / 10**7)#loc1 = (305634410, -876780089)

        wp_number = autopilot_data[MavMessageType.MISSION_CURRENT].seq

        # wp_number == 0 is the "home" waypoint -- we're not really interested
        # in it -- we're interested in the first waypoint on our mission
        if wp_number == 0:
            wp_number = 1

        wp_loc = robot_state.waypoints_in_autopilot[wp_number]

        loc2 = (wp_loc["lat"], wp_loc["lng"])
        dist = haversine.haversine(loc1,loc2,unit=haversine.Unit.METERS)
        return abs(round(dist, 2))
    return -1

def get_next_wp() -> any:
    """ Get the lat/lng of the next wp """
    if (robot_state.waypoints_in_autopilot and
        len(robot_state.waypoints_in_autopilot) > 0 and
        autopilot_data[MavMessageType.GLOBAL_POSITION_INT] and
        autopilot_data[MavMessageType.MISSION_CURRENT]):

        wp_number = autopilot_data[MavMessageType.MISSION_CURRENT].seq

        # wp_number == 0 is the "home" waypoint -- we're not really interested
        # in it -- we're interested in the first waypoint on our mission
        if wp_number == 0:
            wp_number = 1

        the_wp = robot_state.waypoints_in_autopilot[wp_number]

        # #find the next waypoint and return it's
        # #lat/lng to the client
        # lat = the_wp["lat"]
        # lng = the_wp["lng"]

        return the_wp
    return None

def total_distance_between_last_10_positions_in_meters(
    last_10_positions:list[tuple[float, float]]) -> float:
    """
    Distance between each of the last 10 positions added up

    Args:
        last_10_positions (list[tuple[float, float]]): last 10 positions as a 
        list of (lat,lng) tuples, i.e.:
        `[(30.5634410, -87.6780089), ..., (30.5634410, -87.6780089)]`

    Returns:
        float: Total distance in meters
    """
    # test that we've recorded 10 positions
    if last_10_positions[0] and last_10_positions[9]:
        distance = 0
        for x in range(9):
            loc1 = last_10_positions[x]
            loc2 = last_10_positions[x+1]
            distance += haversine.haversine(loc1,loc2,unit=haversine.Unit.METERS)
        return distance
    else:
        return -1
