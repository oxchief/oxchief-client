"""
Author: Wayne Baswell

Functionality directly related to the raspberry pi
"""

import os

def relay_pin_high() -> None:
    """Set `Constants.SHUTOFF_RELAY_GPIO_PIN` to `GPIO.HIGH`"""
    try:
        #GPIO.output(Constants.SHUTOFF_RELAY_GPIO_PIN, GPIO.HIGH)
        pass
    except KeyboardInterrupt:
        #GPIO.cleanup()
        pass

def relay_pin_low() -> None:
    """Set `Constants.SHUTOFF_RELAY_GPIO_PIN` to `GPIO.LOW`"""
    try:
        #GPIO.output(Constants.SHUTOFF_RELAY_GPIO_PIN, GPIO.LOW)
        pass
    except KeyboardInterrupt:
        #GPIO.cleanup()
        pass

def blades_and_wheels_power_off() -> None:
    """Shut off power to blades/wheels -- used for 585 hybrid electric mower"""
    relay_pin_high()

def blades_and_wheels_power_on() -> None:
    """Shut off power to blades/wheels -- used for 585 hybrid electric mower"""
    relay_pin_low()

def reboot_pi() -> None:
    """ CAUTION!!! Reboot Raspberry Pi."""
    os.system('echo "sudo reboot" > /oxpipe')
