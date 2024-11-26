"""
Author: Wayne Baswell

Serial port related functions. I.E. devices connected to Raspberry pi
via USB (or potentialy the GPIO serial pins).
"""
import asyncio
import logging
import traceback

from asyncio import StreamWriter

import serial_asyncio

import config
import robot_state

from constants import Constants

class Serial:
    """
    Represents a serial communication interface.

    This class handles serial tasks such as listing attached devices,
    finding u-blox and ArduPilot receivers, establishing serial connections,
    writing data to the serial port, and closing the serial port.

    Attributes:
        config (Config): The configuration object for serial communication.

    Methods:
        list_attached_devices: Returns a list of devices attached to the Raspberry Pi.
        ublox_serial_port_name_helper: Returns the path of the attached u-blox receiver.
        ublox_serial_port_name: Polls for the u-blox receiver until found.
        ublox_serial_port: Finds the u-blox serial port and returns the established serial connection.
        close_ublox_serial_port: Closes the u-blox serial port.
        write_to_serial: Writes the given message to the serial port.
        ardupilot_serial_port_names_helper: Returns a list of ArduPilot serial ports.
        ardupilot_serial_port_names: Polls for 2 ArduPilot ports until found.
    """
    def __init__(self, config=config.Config()):
        self.config = config

    async def list_attached_devices(self) -> list[list[str,str]]:
        """
        Returns a list of devices attached to the raspberry pi. This list is
        generated when oxchief.sh starts up and kicks off `list_usb`
        function.

        Returned list should look something like this:
        
        [
        ["/dev/ttyACM1", "u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver"],
        ["/dev/ttyUSB0", "u-blox_AG_C099__ZED-F9P_DBSP12CN"],
        ["/dev/ttyUSB1", "u-blox_AG_C099__ODIN-W2_DBSP12CT"]
        ]
        """
        devices = open(Constants.DEVICES_FILENAME, "r")
        lines = devices.readlines()
        device_list = [[s.rstrip() for s in i.split(" - ", 1)] for i in lines]
        return device_list

    async def ublox_serial_port_name_helper(self) -> str:
        """
        Returns a /dev/tty* value like this:

        "/dev/ttyACM1"

        that represents the /dev/tty* path of the attached u-blox receiver.
        If no u-blox receiver is attached, returns False.
        """
        attached_devices = await self.list_attached_devices()
        logging.info("Attached Devices:")
        logging.info(attached_devices)
        for i in attached_devices:
            device_name = i[1]
            if device_name.find(self.config.gnss_rtcm_serial_name_substring) != -1:
                return i[0]
        return False

    async def ublox_serial_port_name(self) -> str:
        """
        Polls the /dev/tty* attached devices looking for a u-blox receiver. If none 
        is found then it sleeps for a bit and tries again 'till one is finally 
        found (or not found, in which case it would loop forever).
        """
        u_blox_serial_port = await self.ublox_serial_port_name_helper()
        while u_blox_serial_port is False:
            await asyncio.sleep(1)
            logging.info("u-blox receiver not found, searching again...")
            u_blox_serial_port = await self.ublox_serial_port_name_helper()

        logging.info("u-blox serial port name: %s", u_blox_serial_port)
        return u_blox_serial_port

    async def ublox_serial_port(self) -> StreamWriter:
        """Finds u-blox serial port and returns established serial connection"""
        u_blox_serial_port = await self.ublox_serial_port_name()
        _, write_serial_port = await serial_asyncio.open_serial_connection(
            url=u_blox_serial_port,
            baudrate=self.config.gnss_rtcm_baud)
        return write_serial_port

    async def close_ublox_serial_port(self) -> None:
        """Close u-blox serial port"""
        logging.info("u-blox serial port -- attempting to close...")
        try:
            robot_state.write_serial_port_gnss_corrections.close()
            await asyncio.sleep(.2)
            logging.info("u-blox serial port --  close success!!")
        except Exception as e:
            logging.warning(f"ERROR closing u-blox serial port: {e}")
            traceback.print_exc()

    async def write_to_serial(self,message:bytes) -> None:
        """
        Write given message to serial port

        Args:
            message (bytes): RTCM correction data to write to port
        """
        message_first_n = message
        if len(message) > 20:
            message_first_n = message_first_n[:20]
        logging.info(f"inside write_to_serial.. writing message {message_first_n} ...")
        robot_state.write_serial_port_gnss_corrections.write(message)
        await robot_state.write_serial_port_gnss_corrections.drain()

    async def ardupilot_serial_port_names_helper(self) -> list[str]:
        """
        Returns a /dev/tty* list like this:

        ["/dev/ttyACM0", "/dev/ttyACM1"]

        that represents the /dev/tty* ports of the attached ArduPilot autopilot.
        If no ArduPilot autopilot is attached, returns an empty list.
        """
        attached_devices = await self.list_attached_devices()
        ardupilot_ports = []
        logging.info("Attached Devices:")
        logging.info(attached_devices)
        for i in attached_devices:
            device_name = i[1]
            if (device_name.find(self.config.ardupilot_serial_2_name_substring) != -1 or
                device_name.find(self.config.ardupilot_serial_1_name_substring) != -1):
                ardupilot_ports.append(i[0])
        return ardupilot_ports

    async def ardupilot_serial_port_names(self) -> list[str]:
        """
        Looks through /dev/tty* attached devices looking for 2 ArduPilot ports. If fewer
        than 2 are found then it sleeps for a bit and tries again 'till two are 
        finally found (or not found, in which case it would loop forever).
        """
        ardupilot_serial_ports = await self.ardupilot_serial_port_names_helper()
        while len(ardupilot_serial_ports) < 2:
            await asyncio.sleep(1)
            logging.info(f"{len(ardupilot_serial_ports)} ardupilot receivers found, "
                f"we'll sleep one second and then keep on looking 'till we find 2...")
            ardupilot_serial_ports = await self.ardupilot_serial_port_names_helper()

        logging.info("ardupilot serial port names:")
        for port in enumerate(ardupilot_serial_ports):
            logging.info(port)
        return ardupilot_serial_ports
    

    async def ardupilot_realsense_serial_port_name_helper(self) -> str:
        """
        Returns a /dev/tty* string like this:

        "/dev/ttyACM0"

        that represents the /dev/tty* port of the attached ArduPilot RealSense USB port.
        If not found, returns None.
        """
        attached_devices = await self.list_attached_devices()
        logging.info("Attached Devices:")
        logging.info(attached_devices)
        for i in attached_devices:
            device_name = i[1]
            if (device_name.find(self.config.ardupilot_realsense_serial_name_substring) != -1):
                return i[0]
        return None
    
    async def ardupilot_realsense_serial_port_name(self) -> str:
        """
        Looks through /dev/tty* attached devices looking for the ArduPilot RealSense port.
        """
        ardupilot_realsense_port = await self.ardupilot_realsense_serial_port_name_helper()
        while not ardupilot_realsense_port:
            await asyncio.sleep(1)
            logging.info("No ardupilot realsense usb port found, "
                "we'll sleep one second and then keep on looking 'till we find it.")
            ardupilot_realsense_port = await self.ardupilot_realsense_serial_port_name_helper()

        logging.info(f"ardupilot realsense serial port names {ardupilot_realsense_port}")

        return ardupilot_realsense_port