#! /usr/bin/env python3
"""
Author: Wayne Baswell
"""
import asyncio
import base64
import logging
import os
from pyrtcm import RTCMReader
from serial import Serial
import time
import traceback
import websockets

from config import Config
from constants import Constants

CONFIG = Config()
logging.basicConfig(level=CONFIG.log_level)

message_types = {}

if CONFIG.enable_python_debug:
    os.environ["PYTHONASYNCIODEBUG"] = "1"
    import debugpy
    debugpy.listen((CONFIG.python_debug_ip, CONFIG.python_debug_port))
    logging.info("debugging started -- now you should connect your debug client"
                 " while we sleep for 10 seconds")
    time.sleep(10)

URI_CORRECTION_SILENT = f"{CONFIG.wss_uri_prefix}/correction/{CONFIG.base_id}/none/"
RTCM_MESSAGE_END = b'\xd3\xdfd'

print("here we go 1 ...")

#
# returns an array like this:
#  [ 
#     ['/dev/ttyACM1', 'u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver'],
#     ['/dev/ttyUSB0', 'u-blox_AG_C099__ZED-F9P_DBSP12CN'],
#     ['/dev/ttyUSB1', 'u-blox_AG_C099__ODIN-W2_DBSP12CT']
#   ]
#
def list_attached_devices():
    # device_list = [
    #     ['/dev/ttyACM0','u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver'],
    #     ['/dev/ttyUSB0', 'u-blox_AG_C099__ZED-F9P_DBSP12CN'],
    #     ['/dev/ttyUSB1', 'u-blox_AG_C099__ODIN-W2_DBSP12CT'],
    #     ]
    devices = open(Constants.DEVICES_FILENAME, 'r')
    lines = devices.readlines()
    device_list = [[s.rstrip() for s in i.split(' - ', 1)] for i in lines]
    return device_list

#
# returns a /dev/tty* value like this:
#
# '/dev/ttyACM1'
#
# that represents the /dev/tty* path of the attached u-blox receiver.
# If no u-blox receiver is attached, returns
#
# False 
#
def ublox_serial_port_name_helper():
    attached_devices = list_attached_devices()
    print("Attached Devices:")
    print(attached_devices)
    # Look for a device whose name contains the substring defined in the
    # config property `gnss_rtcm_serial_name_substring` (e.g. "_GNSS_receiver").
    # This mirrors how other serial ports are discovered using their name
    # substrings in `config.ini`.
    # Prefer explicit base-station GNSS substring; fall back to gnss_rtcm setting.
    target_substring = CONFIG.base_gnss_serial_name_substring
    if target_substring:
        target_substring_lower = target_substring.lower()
        for i in attached_devices:
            device_name = i[1]
            if device_name and target_substring_lower in device_name.lower():
                return i[0]
    return False

#
# Polls the /dev/tty* attached devices looking for a u-blox receiver. If none is found
# then it sleeps for a bit and tries again 'till one is finally found (or not found, 
# in which case it would loop forever).
#
def ublox_serial_port_name():
    u_blox_serial_port = ublox_serial_port_name_helper()
    while u_blox_serial_port == False:
        print("u-blox receiver attached device not found, searching again...")
        u_blox_serial_port = ublox_serial_port_name_helper()
        time.sleep(1)
    print("u-blox serial port name: " + u_blox_serial_port)
    return u_blox_serial_port

def reboot_pi() -> None:
    #echo "sudo reboot" > /oxpipe
    os.system('echo "sudo reboot" > /oxpipe')

def restart_script() -> None:
    os.system('echo "/home/pi/src/oxchief/oxchief-client/re.sh" > /oxpipe')

async def run():
    """
    This function is responsible for running the base station client.
    It establishes a serial connection with a u-blox port, reads RTCM messages,
    encodes them in base64, and sends them to the oxchief.com server over a websocket connection.
    """
    write_count = 0
    errors = 0
    main_loop_consecutive_errors = 0
    print(f"Reading corrections from u-blox receiver at {CONFIG.gnss_rtcm_baud} baud")
    print(f"Sending corrections to {URI_CORRECTION_SILENT}")
    while True:
        try:
            with Serial(ublox_serial_port_name(), baudrate=CONFIG.gnss_rtcm_baud, timeout=1) as ser:
                reader = RTCMReader(ser)
                while True:
                    main_loop_consecutive_errors = 0
                    try:
                        async with websockets.connect(URI_CORRECTION_SILENT, extra_headers={"jwt": CONFIG.auth_token}) as websock:
                            while True:
                                if not websock.open:
                                    raise websockets.exceptions.WebSocketException("Websocket connection closed. Jump out of the send data loop and attempt to re-establish websocket connection.")

                                # Read the next message from the serial connection
                                raw_data, parsed_data = next(reader)
                                print(f"RTCM messsage type: {parsed_data.identity}")
                                print(f"raw_data length: {len(raw_data)} write_count: {write_count}\nparsed_data: {parsed_data}")

                                encodedData = base64.b85encode(raw_data).decode('utf-8')

                                #send data up to oxchief.com server over websocket connection
                                print("JSON message sent up:")
                                json_message_string = '{ "messageType":"correction", "message":"'+encodedData+'"}'
                                print("sending json_message_string: " + json_message_string)

                                #
                                # my inclination is to call the websocket.send(...) in a more aysnc-way 
                                #
                                #  i.e with something like
                                #  await asyncio.create_task(websock.send(json_message_string))
                                #  or
                                #  util.asyncio_create_task_disappear_workaround(websock.send(json_message_string))
                                #
                                # but it seems like that causes the websocket.send(...) to not actually send the message
                                #

                                await websock.send(json_message_string) 
                                #I don't actually need this response, but if we don't await it, then it
                                # appears that websocket.send(...) doesn't actually send the message
                                response = await websock.recv() 

                                print(f"Response: {response}")
                                print(f"encodedData length: {str(len(encodedData))}")
                                write_count += 1
                    except Exception as e:
                        print('!!!!!! exception on rtcm message serial read / webscocket send loop !!!!!!!!!!:')
                        print(e)
                        traceback.print_exc()
                        errors = errors + 1
                        await asyncio.sleep(1) #add a slight delay here so that we don't go crazy looping when, for instance, server reboots
                        print(f"{errors} errors received so far")          
        except Exception as e: 
            print('!!!!!!  ERROR on main loop !!!!!!!!!!:')
            print(e)
            traceback.print_exc()
            main_loop_consecutive_errors += 1
            if main_loop_consecutive_errors > 5:
                print("main loop has had too many consecutive errors")
                print("this may be some weird serial communication issue")
                print("rebooting pi to see if that fixes it")
                reboot_pi()
            await asyncio.sleep(1) #add a slight delay here so that we don't go crazy looping when, for instance, server reboots
            print(f"{errors} errors received so far")

if __name__ == '__main__':
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("Program interrupted by user.")
