"""
Author: Wayne Baswell

Helper methods for mavlink communication with the autopilot via the mavutil /
mavproxy serial connection
"""
import asyncio
import logging
import time
import traceback

from typing import Dict, List, Union, Optional

import requests
from pymavlink import mavutil, mavwp

from config import Config
from constants import Constants

import robot_state

from serial_util import Serial

class Mavlink:
    """
    Mavlink class for handling MAVLink communication and commands.

    Attributes:
        config (Config): Configuration object for Mavlink.
        serial (Serial): Serial object for Mavlink communication.

    Methods:
        __init__(self, config=Config()): Initializes a Mavlink instance.
        wait_for_mavproxy_string(self, the_string:str, printstdout=True) -> None: 
            Searches for a string in the mavproxy output and returns when it finds the string.
        get_mavproxy_outs(self, robot_id:int) -> str: 
            Builds a list of hosts that the user wishes to forward a stream of mavproxy data to.
        mavproxy_command_string(self, ardupilot_port_name:str, baud:int) -> str: 
            Builds command string to start up mavproxy subprocess.
        get_param_mavproxy(self, param:str, tout=2) -> str: 
            Returns autopilot param using MavProxy to get the param value.
        init_mavutil(self, ardupilot_serial_port_name:str=None) -> None: 
            Creates mavutil connection over specified serial port.
        request_parameters_as_float(self, param_names:List[str], precision=2) -> Dict[str, float]: 
            Requests parameters as float values.
        request_parameters_as_int(self, param_names:List[str]) -> Dict[str, int]: 
            Requests parameters as integer values.
        request_parameters(self, param_names:List[str]) -> Dict[str, Union[str, float]]: 
            Requests values of a list of parameters.
        get_param_mavutil(self, param:str) -> any: 
            Gets Ardupilot parameter from Flight Controller using the mavutil connection.
        get_param_int(self, param:str) -> int: 
            Gets parameter from Ardupilot and casts it to an integer.
    """
class Mavlink:

    def __init__(self, config=Config()):
        self.config = config
        self.serial = Serial(config)
        
    async def wait_for_mavproxy_string(self, the_string:str, printstdout=True) -> None:
        """
        Searches for a string in the mavproxy output and returns when it finds the string.

        Call with asyncio.wait_for.. to put a time limit on 
        the amount of time this method may run, i.e.:

        `await asyncio.wait_for(wait_for_mavproxy_string('online system'), timeout=60)`

        Parameters:
            the_string (str): String to poll mavproxy output for.
            printstdout (bool): Print out mavproxy output as we're searching?

        """
        while True:
            line_bytes = None
            #with robot_state.lock_mavproxy:
            line_bytes = await robot_state.mavproxy.stdout.readline()
            line = line_bytes.decode("utf-8")
            if printstdout:
                print(line)
            if line.find(the_string) != -1:
                print(f'found {the_string} in {line}')
                return line
            else:
                print(f'did not find {the_string} in {line}')

            await asyncio.sleep(0.001)

    def get_mavproxy_outs(self, robot_id:int) -> str:
        """
        Build a list of hosts that the user wishes to forward a stream of mavproxy 
        data to.

        Args:
            robot_id (int): Robot ID to pull mavproxy forward info for

        Returns:
            str: Mavproxy --out string that we'll pass to the mavproxy command, 
                for exapmle:
                `--out=udp:win2:14550 --out=udp:mac1:14550 --out=udp:192.168.1.12:14550`
        
        See Also:
            - https://ardupilot.org/mavproxy/docs/getting_started/forwarding.html
        """
        mp = ""
        mav_outs_url = f"https://oxchief.com/api/{robot_id}?format=json"
        
        headers = {
            "Authorization": "Bearer " + self.config.auth_token
        }
        mav_forwards = requests.get(mav_outs_url, headers=headers)
        mav_forwards_json = mav_forwards.json()
        
        for mav in mav_forwards_json:
            mp += " --out=" + mav["ip"]
        #mp += " --out=/dev/ttyUSB3,115200"
        print("Here is the mavproxy forwarding string built from the api at " +
            mav_outs_url)
        print(mp)
        return mp

    def mavproxy_command_string(self, ardupilot_port_name:str, baud:int) -> str:
        """
        Build command string to start up mavproxy subprocess

        Args:
            ardupilot_port_name (str): Flight Controller serial port that 
            mavproxy will connect to
            baud (int): Flight Controller serial port baud rate

        Returns:
            str: mavproxy command, i.e.:
            `/root/.local/bin/mavproxy.py --master=/dev/ttyUSB0,921600 --out=udp:macpro1:14550 --out=udp:odroid:14550`
        """

        mavproxy_outs = self.get_mavproxy_outs(self.config.robot_id)
        #List of hosts to forward mavproxy telemetry data to.
        #Data looks something like this:

        #mavproxy_outs = " --out=udp:192.168.1.27:14550 --out=udp:192.168.1.12:14550"
        #mavproxy_outs = " --out=udp:192.168.1.49:14550"
        #

        # I want to send logs and params to ./temp via 
        #
        # --state-basedir=/usr/src/app/temp
        #
        # or (preferably)
        #
        # --state-basedir=temp
        #
        # but I haven't been able to make that work
        # yet -- getting various "did not find"
        # errors on mavproxy.py startup
        return Constants.MAVPROXY_SCRIPT + \
            " --master="+ardupilot_port_name+","+str(baud) + mavproxy_outs

    async def get_param_mavproxy(self, param:str, tout=2) -> str:
        """
        Return autopilot param. Uses MavProxy to get the param val.

        Parameters:
            param (str): Param whose value to find
            tout (int):  How long to wait before throwing a asyncio.TimeoutError
        
        Throws:
            asyncio.TimeoutError: If param not found in tout time
        """
        get_param_str = f"param show {param}\n"
        param_line = False

        with robot_state.lock_mavproxy:
            robot_state.mavproxy.stdin.write(get_param_str.encode())
            await robot_state.mavproxy.stdin.drain()
            param_line = await asyncio.wait_for(
                self.wait_for_mavproxy_string(param), timeout=tout)

        if param_line:
            param_line = param_line[param_line.index(param)+len(param)-len(param_line):]
            param_line = param_line.strip()

        return param_line

    async def init_mavutil(self, ardupilot_serial_port_name:str=None) -> None:
        """
        Create mavutil connection over specified serial port. We use this connection
        as the primary communication channel with the Flight Controller.

        Args:
            ardupilot_serial_port_name (str, optional): _description_. Defaults 
            to None.
        """
        while not ardupilot_serial_port_name:
            logging.info("init_mavutil() -- looking for open ardupilot ports..")
            ardupilot_port_names = await self.serial.ardupilot_serial_port_names()
            for port_name in ardupilot_port_names:
                #robot_state.mavproxy_port_name is currently in use by our mavutil,
                #so don't try to use it for mavproxy
                if robot_state.mavproxy_port_name != port_name:
                    ardupilot_serial_port_name = port_name
                    break

        #save the port name we're connecting to with mavutil
        robot_state.mavutil_port_name = ardupilot_serial_port_name
        logging.info(f"establishing mavutil connection on {ardupilot_serial_port_name}")
        robot_state.mutil = mavutil.mavlink_connection(
            ardupilot_serial_port_name,
            self.config.ardupilot_baud)
        robot_state.mutil.heartbeat_interval = 0.5  # seconds
        robot_state.mutil.wait_heartbeat()
        robot_state.wploader = mavwp.MAVWPLoader(
            robot_state.mutil.target_system,
            robot_state.mutil.target_component)
        msg = None
        #loop until weg get a message back from the pymavlink connection

        while not msg:
            logging.info("pinging mavutil...")
            robot_state.mutil.mav.ping_send(
                int(time.time() * 1e6), # Unix time in microseconds
                0, # Ping number
                0, # Request ping of all systems
                0 # Request ping of all components
            )
            msg = robot_state.mutil.recv_match()
            await asyncio.sleep(1.0)
        logging.info("mavutil setup complete")

    async def request_parameters_as_float(self, param_names: List[str], precision=2) -> Dict[str, float]:
        """
        Requests parameters as float values.

        Args:
            param_names (List[str]): A list of parameter names to request.
            precision (int): The number of decimal places to round the float values to. Default is 2.

        Returns:
            Dict[str, float]: A dictionary containing the requested parameter names as keys and their corresponding float values.
        """
        params = await self.request_parameters(param_names)
        for key, val in params.items():
            val = round(float(val), precision)
            params[key] = val
        return params
    
    async def request_parameters_as_int(self, param_names: List[str]) -> Dict[str, int]:
        """
        Requests the parameters as integers.

        Args:
            param_names (List[str]): A list of parameter names.

        Returns:
            Dict[str, int]: A dictionary mapping parameter names to their integer values.
        """
        params = await self.request_parameters(param_names)
        for key, val in params.items():
            params[key] = int(val)
        return params
        
    async def request_parameters(self, param_names:List[str]) -> Dict[str, Union[str, float]]:
        """
        Request values of a list of parameters

        Args:
            param_names (List[str]): Names of parameters to pull from Pixhawk

        Returns:
            Dict[str, Union[str, float]]: Param values
        """
        received_params = {}
        try:
            # Request parameter values for each parameter in the list
            for param_id in param_names:
                # Request parameter
                robot_state.mutil.mav.param_request_read_send(
                    robot_state.mutil.target_system,
                    robot_state.mutil.target_component,
                    param_id.encode('utf-8'),
                    -1 # -1 means request by name
                )
                print(f"Baswell requested parameter {param_id}")

            # Wait for the responses (PARAM_VALUE messages)
            timeout = time.time() + 10  # 10-second timeout
            while time.time() < timeout and len(received_params) < len(param_names):
                msg = robot_state.mutil.recv_match(type='PARAM_VALUE', blocking=True)
                if msg and msg.param_id in param_names:
                    received_params[msg.param_id] = msg.param_value
                #await asyncio.sleep(0.1)

            # Print the received parameter values
            for param_id, param_value in received_params.items():
                print(f"Parameter {param_id} value: {param_value}")

        except Exception as e:
            print(f"Error: {e}")
            
        return received_params

    async def get_param_mavutil(self, param:str) -> any:
        """
        Get Ardupilot parameter from Flight Controller using the mavutil connection

        Args:
            param (str): Name of parameter

        Returns:
            any: Parameter value
        """

        # Request parameter
        robot_state.mutil.mav.param_request_read_send(
            robot_state.mutil.target_system,
            robot_state.mutil.target_component,
            bytes(param, encoding="utf-8"),
            -1
        )

        # Print parameter value
        message = robot_state.mutil.recv_match(type="PARAM_VALUE", blocking=True).to_dict()
        param_id = message["param_id"]
        param_value = message["param_value"]
        logging.info(f"name: {param_id} \tvalue: {param_value}")
        return message["param_value"]

    async def get_param_int(self, param:str) -> int:
        """
        Get parameter from Ardupilot and cast to int. i.e.:
        
        `get_param_int("AHRS_OFFSET_E")`

        Args:
            param (str): Parameter to get from Ardupilot

        Returns:
            int: Param value cast to `int`
        """
        param_val_str =  await self.get_param_mavutil(param)
        param_val_int = int(param_val_str)
        return param_val_int

    async def get_param_float(self, param:str, precision=2) -> float:
        """
        Get parameter from Ardupilot and cast to float. i.e.:

        `get_param_float("GPS_POS1_X")`
        
        Args:
            param (str): Parameter to get from Ardupilot
            precision (int, optional): Float precision. Defaults to 2.

        Returns:
            float: Param value cast to `float`
        """
        param_val_str =  await self.get_param_mavutil(param)
        param_val_float = float(param_val_str)
        return round(param_val_float, precision)

    def parse_params_to_dictionary(self, param_string:str) -> dict:
        """
        Parse the parameter string into a dictionary object. I think this method
        was used back when we were pulling more Flight Controller data from
        the MavProxy connection. UNUSED AS OF JULY 8, 2024.

        Args:
            param_string (str): Comma-delimited key,value param string.

        Returns:
            dict: Param dictionary
        """
        param_begin = param_string.index("{")
        param_end = param_string.index("}")
        val_string = param_string[param_begin+1:param_end]
        remove_comma_array = val_string.split(",")
        param_dictionary = {}
        for i in remove_comma_array:
            key_val_array = i.split(":")
            try:
                param_dictionary[key_val_array[0].strip()] = float(key_val_array[1].strip())
            except:
                traceback.print_exc()
                param_dictionary[key_val_array[0].strip()] = key_val_array[1].strip()
        return param_dictionary

    async def init_mavproxy(self, ardupilot_serial_port_name:str=None) -> None:
        """
        Run the mavproxy subprocess

        Args:
            ardupilot_serial_port_name (str, optional): Flight Controller serial 
            port to attach mavproxy subprocess to. Defaults to None.
        """
        while not ardupilot_serial_port_name:
            logging.info("init_mavproxy() -- looking for open ardupilot ports..")
            ardupilot_port_names = await self.serial.ardupilot_serial_port_names()
            for port_name in ardupilot_port_names:
                #robot_state.mavutil_port_name is currently in use by our mavutil, so
                #don't try to use it for mavproxy
                if robot_state.mavutil_port_name != port_name:
                    ardupilot_serial_port_name = port_name
                    break

        #save this port name so we'll know which port we're using for mavproxy
        robot_state.mavproxy_port_name = ardupilot_serial_port_name
        mav_proxy_command = self.mavproxy_command_string(ardupilot_serial_port_name,
                                                self.config.ardupilot_baud)
        logging.info(f"establishing mavproxy connection on {ardupilot_serial_port_name}")
        logging.info(f"with mavproxy command: {mav_proxy_command}")

        robot_state.mavproxy = await asyncio.create_subprocess_exec(*mav_proxy_command.split(" "),
                                                        stdout=asyncio.subprocess.PIPE,
                                                        stdin=asyncio.subprocess.PIPE)
        with robot_state.lock_mavproxy:
            await asyncio.wait_for(
                self.wait_for_mavproxy_string("online system"),
                timeout=60)
            await asyncio.wait_for(
                self.wait_for_mavproxy_string("parameters to mav.parm"),
                timeout=60)

        logging.info("mavproxy setup complete")

    async def setup_ardupilot_connections(self) -> None:
        """
        Sets up the mavproxy and mavutil connections between the raspberry pi (or 
        whatever this script is running on) and the autopilot
        """
        ardupilot_port_names = await self.serial.ardupilot_serial_port_names()
        await self.init_mavproxy(ardupilot_port_names[0])
        await self.init_mavutil(ardupilot_port_names[1])

    async def mavproxy_send_command(self, command_string:str) -> None:
        """
        TODO -- Test this guy -- I don't think i've called it since rewriting with 
        mavproxy (instead of the old pexpect stuff)
        """
        try:
            with robot_state.lock_mavproxy:
                robot_state.mavproxy.stdin.write(command_string.encode())
                await robot_state.mavproxy.stdin.drain()
        except Exception as err:
            traceback.print_exc()
            return f"Error in mavproxy_send_command: {err}"

    def build_lat_lng_from_mavproxy_line(self, mavproxy_waypoint_line:str) -> any:
        """
        Mavproxy mission waypoint line will look like this:

        `16 3 30.5634909000 -87.6785348000 100.000000 p1=0.0 p2=0.0 p3=0.0 p4=0.0 cur=0 auto=1`
        """
        split_line = mavproxy_waypoint_line.split()

        #Here are our 2 hackish checks to see if this line qualifies
        #as a mavproxy mission waypoint

        #1 check if the length of items is > 7
        if len(split_line) > 7:
            # check if each of the first 5 items is numeric
            for x in range(5):
                try:
                    float(split_line[x])
                except ValueError:
                    return False
        else:
            return False

        #at this point we assume we're dealing with a waypoint
        return {"lat": float(split_line[2]), "lng": float(split_line[3])}
