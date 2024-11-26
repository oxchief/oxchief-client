"""
Author: Wayne Baswell

Class for interacting with Sabertooth motor driver.
"""
import asyncio
from asyncio import StreamReader,StreamWriter
from typing import Callable, Optional

import serial_asyncio

import serial_util

SABERTOOTH_BAUD=115_200
SABERTOOTH_PORT_NAME_SUBSTRING = 'Dimension_Engineering_Sabertooth'

sabertooth_read_serial_port:StreamReader = None
sabertooth_write_serial_port:StreamWriter = None

class Sabertooth:
    """
    Holds Sabertooth data
    """
    m1_current:int = -1
    m1_temp:int = -1
    m1_volt:int = -1

    m2_current:int = -1
    m2_temp:int = -1
    m2_volt:int = -1

async def sabertooth_serial_port_name_helper() -> str:
    """
    returns a /dev/tty* value like this:

    '/dev/ttyACM1'

    that represents the /dev/tty* path of the attached sabertooth motor controller.
    If no u-blox receiver is attached, returns False.
    """
    attached_devices = await serial_util.list_attached_devices()
    print("Attached Devices:")
    print(attached_devices)
    for i in attached_devices:
        device_name = i[1]
        if device_name.find(SABERTOOTH_PORT_NAME_SUBSTRING) != -1:
            return i[0]
    return False

async def sabertooth_serial_port_name() -> str:
    """
    Polls the /dev/tty* attached devices looking for sabertooth. If none is found
    then it sleeps for a bit and tries again 'till one is finally found
    (or not found, in which case it would loop forever).
    """
    sabertooth_serial_port = await sabertooth_serial_port_name_helper()
    while sabertooth_serial_port is False:
        await asyncio.sleep(1)
        print("sabertooth not found, searching again...")
        sabertooth_serial_port = await sabertooth_serial_port_name_helper()
    print(f"sabertooth serial port name: {sabertooth_serial_port}")
    return sabertooth_serial_port

async def sabertooth_write(msg: str) -> None:
    """
    Write in the serial port.
    Automatically transform to bytes and insert \r\n at the end.
    """
    if sabertooth_write_serial_port:
        sabertooth_write_serial_port.write(str('{}\r\n'.format(msg)).encode())
        await sabertooth_write_serial_port.drain()
    else:
        print(f"Could not send this message to robot: {msg}")

async def connect_to_sabertooth_serial_port() -> None:
    """
    Finds sabertooth serial port and returns established serial connection
    """
    global sabertooth_read_serial_port, sabertooth_write_serial_port
    sabertooth_port_name = await sabertooth_serial_port_name()
    print(f'Found sabertooth at {sabertooth_port_name}')
    sabertooth_read_serial_port, sabertooth_write_serial_port = await serial_asyncio.open_serial_connection(url=sabertooth_port_name, baudrate=SABERTOOTH_BAUD)
    print('Connected to sabertooth serial')

async def read_sabertooth_data() -> None:
    """
    read data from sabertooth
    """
    while True:
        await sabertooth_write('m1:getc')
        m1c = await sabertooth_read_serial_port.readline()
        m1c = m1c.decode().strip()
        Sabertooth.m1_current = int(m1c[4:])

        await sabertooth_write('m2:getc')
        m2c = await sabertooth_read_serial_port.readline()
        m2c = m2c.decode().strip()
        Sabertooth.m2_current = int(m2c[4:])

        await sabertooth_write('m1:gett')
        m1t = await sabertooth_read_serial_port.readline()
        m1t = m1t.decode().strip()
        Sabertooth.m1_temp = int(m1t[4:])

        await sabertooth_write('m2:gett')
        m2t = await sabertooth_read_serial_port.readline()
        m2t = m2t.decode().strip()
        Sabertooth.m2_temp = int(m2t[4:])

        await sabertooth_write('m1:getb')
        m1b = await sabertooth_read_serial_port.readline()
        m1b = m1b.decode().strip()
        Sabertooth.m1_volt = int(m1b[4:])

        await sabertooth_write('m2:getb')
        m2b = await sabertooth_read_serial_port.readline()
        m2b = m2b.decode().strip()
        Sabertooth.m2_volt = int(m2b[4:])

        #print("m1c: {} m2c: {} m1t: {} m2t: {} m1b: {} m2b: {}".format(Sabertooth.m1_current, Sabertooth.m2_current, Sabertooth.m1_temp, Sabertooth.m2_temp, Sabertooth().m1_volt, Sabertooth().m2_volt))
        await asyncio.sleep(1)

async def send_sabertooth_status_to_robot_log(robot_log_func: Callable[[str, Optional[str]], None]) -> None:
    """
    Send Sabertooth status out to robot
    """
    await asyncio.sleep(1) #give read_sabertooth_data a bit to read in the first dataset
    while True:
        sabertooth_status = (
            f'ST m1 c: {Sabertooth.m1_current/10}a '
            f'ST m2 c: {Sabertooth.m2_current/10}a<br>'
            f'ST m1 t: {round(Sabertooth.m1_temp*1.8)+32}f '
            f'ST m2 t: {round(Sabertooth.m2_temp*1.8)+32}f '
            f'ST batt: {Sabertooth.m1_volt/10}v<br>')

        robot_log_func(sabertooth_status)
        await asyncio.sleep(5)