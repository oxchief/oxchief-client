#pylint: disable = trailing-whitespace, missing-function-docstring, invalid-name
#pylint: disable = consider-using-enumerate, too-many-lines, logging-not-lazy
#pylint: disable = logging-fstring-interpolation, global-statement
"""
Author: Wayne Baswell
Example of how to create a Peripheral device/GATT Server
"""
# Standard modules
import logging
import random
import struct
import threading

from typing import Callable

from bluezero import async_tools
from bluezero import adapter
from bluezero import peripheral

import robot_state

from robot_state import autopilot_data
from robot_state import last_time

from constants import LastTime

class BluetoothPeripheralDataExposer:
    """
    Handles ble communication
    """

    def __init__(self, set_rc_channels_from_joystick_func:Callable[int, int]):
        self.set_rc_channels_from_joystick_func = set_rc_channels_from_joystick_func

    # PYTHON_DEBUG = True
    # if PYTHON_DEBUG:
    #     #os.environ['PYTHONASYNCIODEBUG'] = '1'
    #     import debugpy
    #     debugpy.listen(("0.0.0.0", 3338))
    #     print("debugging started -- now you should connect your debug client while we sleep for 10 seconds")
    #     time.sleep(10)

    # constants
    # Custom service uuid
    # CPU_TMP_SRVC = '12341000-1234-1234-1234-123456789abc'
    OX_DATA_SRVC = '22341123-4321-4321-4321-123456789def'

    OX_SRV_ID = 1
    #OX_CHRC_READ_ID = 1
    #OX_CHRC_WRITE_ID = 2

    ox_monitor = None

    # # https://www.bluetooth.com/specifications/assigned-numbers/
    # # Bluetooth SIG adopted UUID for Temperature characteristic
    # CPU_TMP_CHRC = '2A6E'

    OX_CHRC = '28590F7E-DB05-467E-8757-72F6FAEB0000'
    OX_CHRC_LAT = '28590F7E-DB05-467E-8757-72F6FAEB0001'
    OX_CHRC_LNG = '28590F7E-DB05-467E-8757-72F6FAEB0002'
    OX_CHRC_HDG = '28590F7E-DB05-467E-8757-72F6FAEB0003'
    OX_CHRC_NUM = '28590F7E-DB05-467E-8757-72F6FAEB0004'
    OX_CHRC_WRITE_X = '28590F7E-DB05-467E-8757-72F6FAEB0005'
    OX_CHRC_WRITE_Y = '28590F7E-DB05-467E-8757-72F6FAEB0006'

    # Characteristic id for JSON data service -- from Swift example
    #OX_WRITE_JSON_CHRC = '08590F7E-DB05-467E-8757-72F6FAEB0001'

    #OX_READ_CHRC = 'ABC90F7E-DB05-467E-8757-72F6FAEB0101'
    #OX_WRITE_CHRC = 'ABC90F7E-DB05-467E-8757-72F6FAEB1302'

    # # Bluetooth SIG adopted UUID for Characteristic Presentation Format
    CPU_FMT_DSCP = '2904'


    def ox_read_value(self):
        """
        Example read callback. Value returned needs to be a list of bytes/integers
        in little endian format.

        This one does a mock reading CPU temperature callback.
        Return list of integer values.
        Bluetooth expects the values to be in little endian format and the
        temperature characteristic to be an sint16 (signed & 2 octets) and that
        is what dictates the values to be used in the int.to_bytes method call.

        :return: list of uint8 values
        """
        print("ox_read_value called")
        cpu_value = random.randrange(3200, 5310, 10) / 100

        print("Service called. cpu_value: " + str(cpu_value))
        return self.string_to_unicode_nums(str(int(cpu_value * 100)) + ' degrees')

    def ox_read_num(self) -> list:
        """callback"""
        #print("ox_read_num called")
        #num = random.randrange(3200000000, 5310000000, 10) / 100000000
        global_position_int = autopilot_data['GLOBAL_POSITION_INT']
        the_hdg = global_position_int.hdg if global_position_int else -1 # divide by 10**7
        print("heading: " + str(the_hdg))
        ba = bytearray(struct.pack("f", the_hdg))
        return list(ba)

    def pack_int(self, the_int:int) -> list:
        """convert int to list(bytearray) for sending via ble"""
        ba = bytearray(struct.pack("i", the_int))
        return list(ba)

    def ox_read_val(self, key:str):
        """
        Read data out of the autopilot live data dict and return back as ble-ready lists of bytes
        """
        global_position_int = autopilot_data['GLOBAL_POSITION_INT']

        the_hdg = global_position_int.hdg if global_position_int else -1 #divide by 10**2
        the_lat = global_position_int.lat if global_position_int else -1 # divide by 10**7
        the_lng = global_position_int.lon if global_position_int else -1 # divide by 10**7

        if key == 'lat':
            print(f"Service called. {key}: " + str(the_lat))
            #return self.string_to_unicode_nums(str(the_lat) + ' ' + key)
            return self.pack_int(the_lat)
        elif key == 'lng':
            print(f"Service called. {key}: " + str(the_lng))
            #return self.string_to_unicode_nums(str(the_lng) + ' ' + key)
            return self.pack_int(the_lng)
        elif key == 'hdg':
            print(f"Service called. {key}: " + str(the_hdg))
            return self.pack_int(the_hdg)
        else:
            random_num = random.randrange(3200, 5310, 10) / 100
            print(f"Service called. {key}: " + str(random_num))
            #return list(int(cpu_value * 100).to_bytes(2, byteorder='little', signed=True))
            #ret_val = "whoaa " + str(int(cpu_value * 100))
            #print("Returned value: " + ret_val)
            #return list(ret_val.to_bytes(2, byteorder='little', signed=True))
            #return list(int(cpu_value * 100).to_bytes(2, byteorder='little', signed=True)) + string_to_unicode_nums(' degrees')
            return self.string_to_unicode_nums(str(int(random_num * 100)) + ' ' + key)

    def string_to_unicode_nums(self, the_str:str):
        """
        Convert string to unicode byte array
        """
        nums = []
        # Calling the for loop to iterate each
        # characters of the given byte string
        for the_chr in the_str:
            # Calling the ord() function
            # to convert the specified byte
            # characters to numbers of the unicode
            nums.append(ord(the_chr))

        return nums

    def x_data_received(self, data_and_time:list[int], options):
        """
        receive x-axis joystick data
        """
        int_val = int.from_bytes(data_and_time[0:2], "big", signed=True)
        original_val = int_val/10_000
        time = int.from_bytes(data_and_time[2:], "big")
        logging.info(f'time: {time}')
        logging.info(f'last_time x:{last_time[LastTime.META_X]}')
        if time > last_time[LastTime.META_X]:
            last_time[LastTime.META_X] = time
            robot_state.client_joystick_x = original_val
            self.set_rc_channels_from_joystick_func(robot_state.client_joystick_x,robot_state.client_joystick_y)
        print('x val: ' + str(original_val) + ' time: ' + str(time))

    def y_data_received(self, data_and_time:list[int], options):
        """
        receive y-axis joystick data
        """
        int_val = int.from_bytes(data_and_time[0:2], "big", signed=True)
        original_val = int_val/10_000
        time = int.from_bytes(data_and_time[2:], "big")
        logging.info(f'time: {time}')
        logging.info(f'last_time y:{last_time[LastTime.META_Y]}')
        if time > last_time[LastTime.META_Y]:
            last_time[LastTime.META_Y] = time
            robot_state.client_joystick_y = original_val
            self.set_rc_channels_from_joystick_func(robot_state.client_joystick_x,robot_state.client_joystick_y)
        print('y val: ' + str(original_val) + ' time: ' + str(time))

    def ox_update_value(self, characteristic):
        """
        Example of callback to send notifications

        :param characteristic:
        :return: boolean to indicate if timer should continue
        """
        print("ox_update_value called")
        # read/calculate new value.
        new_value = self.ox_read_value()
        # Causes characteristic to be updated and send notification
        characteristic.set_value(new_value)
        # Return True to continue notifying. Return a False will stop notifications
        # Getting the value from the characteristic of if it is notifying
        return characteristic.is_notifying

    def ox_update_val(self, characteristic, key:str):
        """
        Example of callback to send notifications

        :param characteristic:
        :return: boolean to indicate if timer should continue
        """
        print("ox_update_value called")
        # read/calculate new value.
        new_value = self.ox_read_val(key)
        # Causes characteristic to be updated and send notification
        characteristic.set_value(new_value)
        # Return True to continue notifying. Return a False will stop notifications
        # Getting the value from the characteristic of if it is notifying
        return characteristic.is_notifying

    def ox_update_num(self, characteristic):
        """
        Example of callback to send notifications

        :param characteristic:
        :return: boolean to indicate if timer should continue
        """
        print("ox_update_num called")
        # read/calculate new value.
        new_value = self.ox_read_num()
        # Causes characteristic to be updated and send notification
        characteristic.set_value(new_value)
        # Return True to continue notifying. Return a False will stop notifications
        # Getting the value from the characteristic of if it is notifying
        return characteristic.is_notifying

    def ox_update_lat(self, characteristic):
        """ Callback """
        return self.ox_update_val(characteristic, 'lat')

    def ox_update_lng(self, characteristic):
        """ Callback """
        return self.ox_update_val(characteristic, 'lng')

    def ox_update_hdg(self, characteristic):
        """ Callback """
        return self.ox_update_val(characteristic, 'hdg')

    def ox_notify_callback(self, notifying, characteristic):
        """
        Notificaton callback example. In this case used to start a timer event
        which calls the update callback every 2 seconds.

        :param notifying: boolean for start or stop of notifications
        :param characteristic: The python object for this characteristic
        """
        print("ox_notify_callback called")
        if notifying:
            print("notifying flag is enabled...")
            async_tools.add_timer_ms(500, self.ox_update_value, characteristic)

    def ox_notify_callback_lat(self, notifying, characteristic):
        """lat"""
        print("ox_notify_callback_lat called")
        if notifying:
            print("notifying flag is enabled...")
            async_tools.add_timer_ms(500, self.ox_update_lat, characteristic)

    def ox_notify_callback_lng(self, notifying, characteristic):
        """lng"""
        print("ox_notify_callback_lng called")
        if notifying:
            print("notifying flag is enabled...")
            async_tools.add_timer_ms(500, self.ox_update_lng, characteristic)

    def ox_notify_callback_hdg(self, notifying, characteristic):
        """hdg"""
        print("ox_notify_callback_hdg called")
        if notifying:
            print("notifying flag is enabled...")
            async_tools.add_timer_ms(500, self.ox_update_hdg, characteristic)


    def ox_notify_callback_num(self, notifying, characteristic):
        """num"""
        print("ox_notify_callback_num called")
        if notifying:
            print("notifying flag is enabled...")
            async_tools.add_timer_seconds(1, self.ox_update_num, characteristic)


    def start(self):
        """Creation of peripheral"""
        logger = logging.getLogger('localGATT')
        logger.setLevel(logging.DEBUG)
        adapter_address = list(adapter.Adapter.available())[0].address
        # Example of the output from read_value
        print('CPU temperature is {}\u00B0C'.format(
            int.from_bytes(self.ox_read_value(), byteorder='little', signed=True)/100))

        # Create peripheral
        ox_monitor = peripheral.Peripheral(adapter_address,
                                            local_name='oxchief2',
                                            appearance=1344) #1344 decimal is 540 hex == "Sensor" / "Generic Sensor" -- https://btprodspecificationrefs.blob.core.windows.net/assigned-numbers/Assigned%20Number%20Types/Assigned%20Numbers.pdf

        # Add service
        ox_monitor.add_service(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID, uuid=BluetoothPeripheralDataExposer.OX_DATA_SRVC, primary=True)

        # # Add read characteristic
        # ox_monitor.add_characteristic(srv_id=OX_SRV_ID, chr_id=OX_CHRC_READ_ID, uuid=OX_READ_CHRC,
        #                                value=[], notifying=True,
        #                                flags=['read', 'notify'],
        #                                read_callback=ox_read_value,
        #                                write_callback=None,
        #                                notify_callback=ox_notify_callback)

        # # Add write characteristic
        # ox_monitor.add_characteristic(srv_id=OX_SRV_ID, chr_id=OX_CHRC_WRITE_ID, uuid=OX_WRITE_JSON_CHRC,
        #                             value=[], notifying=False,
        #                             flags=['write', 'write-without-response'],
        #                             read_callback=None,
        #                             write_callback=json_data_received,
        #                             notify_callback=None)

        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=1, #I think this just needs to be unique across the characteristics of this service
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC,
                                    value=[], notifying=True,
                                    # flags=['read', 'notify', 'indicate', 'write', 'write-without-response'],
                                    flags=['read', 'notify'],
                                    read_callback=self.ox_read_value,
                                    notify_callback=self.ox_notify_callback)

        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=2,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_LAT,
                                    value=[], notifying=True,
                                    flags=['read', 'notify'],
                                    read_callback=lambda: self.ox_read_val('lat'),
                                    notify_callback=self.ox_notify_callback_lat)

        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=3,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_LNG,
                                    value=[], notifying=True,
                                    flags=['read', 'notify'],
                                    read_callback=lambda: self.ox_read_val('lng'),
                                    notify_callback=self.ox_notify_callback_lng)

        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=31,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_HDG,
                                    value=[], notifying=True,
                                    flags=['read', 'notify'],
                                    read_callback=lambda: self.ox_read_val('hdg'),
                                    notify_callback=self.ox_notify_callback_hdg)

        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=4,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_NUM,
                                    value=[], notifying=True,
                                    flags=['read', 'notify'],
                                    read_callback=self.ox_read_num,
                                    notify_callback=self.ox_notify_callback_num)
        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=5,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_WRITE_X,
                                    value=[], notifying=False,
                                    flags=['write', 'write-without-response'],
                                    read_callback=None,
                                    write_callback=self.x_data_received,
                                    notify_callback=None)
        ox_monitor.add_characteristic(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
                                    chr_id=6,
                                    uuid=BluetoothPeripheralDataExposer.OX_CHRC_WRITE_Y,
                                    value=[], notifying=False,
                                    flags=['write', 'write-without-response'],
                                    read_callback=None,
                                    write_callback=self.y_data_received,
                                    notify_callback=None)

        # # # Add descriptor
        # ox_monitor.add_descriptor(srv_id=BluetoothPeripheralDataExposer.OX_SRV_ID,
        #                             chr_id=4,
        #                             dsc_id=1,
        #                             uuid=BluetoothPeripheralDataExposer.CPU_FMT_DSCP,
        #                             value=[0x0E, 0xFE, 0x2F, 0x27, 0x01, 0x00, 0x00],
        #                             flags=['read, notify'])

        # Publish peripheral and start event loop
        ox_monitor.publish()

        # the_var = 1
        # print(the_var)

        # ox_charac = ox_monitor.characteristics[0]
        # ox_notify_callback(True, ox_charac)

def fire_off_ble_thread(set_rc_channels_from_joystick_func) -> None:
    """
    we're running the ble code on it's own thread because the ble
    library we use (bluezero) has it's own event loop that
    appears to take over the thread that it's running
    on -- there may be some way to run it in an
    asycnio-friendly way -- or we may end
    up wanting to replace bluezero with
    some other ble lib that's more
    asyncio-friendly if having
    this thread running ends
    up being a headache
    """
    print('Firing off ble thread')

    bleData = BluetoothPeripheralDataExposer(set_rc_channels_from_joystick_func)
    bleThread = threading.Thread(target=bleData.start, daemon=True)
    bleThread.start()
    print('BLE thread should be started now')

if __name__ == '__main__':
    #bleData = BluetoothPeripheralDataExposer()
    # Get the default adapter address and pass it to main
    #bleData.start()
    pass
