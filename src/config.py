"""
Author: Wayne Baswell

Configuration file access
"""
import configparser
import logging
import os

class Config:
    """
    Reads config.ini file and makes data available as properties
    """

    def __init__(self, config_file_path='config.ini'):
        """
        Initialize the Config object.

        Args:
            config_file_path (str): The path to the config.ini file. Default is 'config.ini'.
        """
        self.config_file_path = config_file_path
        self._load_config()

    def _load_config(self):
        """
        Load the config.ini file and parse its contents.
        """
        self._config = configparser.ConfigParser()
        try:
            with open(self.config_file_path, 'r') as file:
                self._config.read_file(file)
        except FileNotFoundError:
            print(f"Config file '{self.config_file_path}' not found.")
            self._config = {}

    def get_property(self, section, key, default=None):
        """
        Get the value of a config property.

        Args:
            section (str): The section name in the config file.
            key (str): The key name of the property.
            default: The default value to return if the property is not found.

        Returns:
            The value of the config property, or the default value if not found.
        """
        return self._config.get(section, key, fallback=default)

    def get_string(self, section, key, default=None):
        """
        Get the string value of a config property.

        Args:
            section (str): The section name in the config file.
            key (str): The key name of the property.
            default: The default value to return if the property is not found.

        Returns:
            The string value of the config property, or the default value if not found.
        """
        return str(self._config.get(section, key, fallback=default))

    def get_int(self, section, key, default=None):
        """
        Get the integer value of a config property.

        Args:
            section (str): The section name in the config file.
            key (str): The key name of the property.
            default: The default value to return if the property is not found.

        Returns:
            The integer value of the config property, or the default value if not found.
        """
        return int(self._config.get(section, key, fallback=default))

    def get_boolean(self, section, key, default=False):
        """
        Get the boolean value of a config property.

        Args:
            section (str): The section name in the config file.
            key (str): The key name of the property.
            default: The default value to return if the property is not found.

        Returns:
            The boolean value of the config property, or the default value if not found.
        """
        return self._config.getboolean(section, key, fallback=default)

    def get_logging_level(self, section, key, default=logging.INFO):
        """
        Get the logging level from a config property.

        Args:
            section (str): The section name in the config file.
            key (str): The key name of the property.
            default: The default logging level to return if the property is not found.

        Returns:
            The logging level from the config property, or the default logging level if not found.
        """
        level_str = self._config.get(section, key, fallback=str(default))
        return getattr(logging, level_str.upper(), default)

    @property
    def enable_python_debug(self):
        """
        Whether or not to enable python debugging.

        Returns:
            bool: True if python debugging is enabled, False otherwise.
        """
        return self.get_boolean('Debug', 'enable_python_debug', False)

    @property
    def python_debug_ip(self):
        """
        IP to expose python debugging on.

        Returns:
            str: The IP address for python debugging.
        """
        return self.get_string('Debug', 'python_debug_ip', "0.0.0.0")

    @property
    def python_debug_port(self):
        """
        Port to expose python debugging on.

        Returns:
            int: The port number for python debugging.
        """
        return self.get_int('Debug', 'python_debug_port', 3339)

    @property
    def log_level(self):
        """
        Current log level.

        Returns:
            int: The current log level.
        """
        return self.get_logging_level('Settings', 'log_level')

    @property
    def stun_url(self):
        """
        URL to stun server used to facilitate WebRTC.

        Returns:
            str: The URL of the stun server.
        """
        return self.get_string('Network', 'stun_url', "oxchief.com")

    @property
    def stun_port(self):
        """
        Port to stun server used to facilitate WebRTC.

        Returns:
            int: The port number of the stun server.
        """
        return self.get_int('Network', 'stun_port', 3339)

    @property
    def turn_url(self):
        """
        URL to turn server used to facilitate WebRTC.

        Returns:
            str: The URL of the turn server.
        """
        return self.get_string('Network', 'turn_url', "oxchief.com")

    @property
    def turn_port(self):
        """
        Port to turn server used to facilitate WebRTC.

        Returns:
            int: The port number of the turn server.
        """
        return self.get_int('Network', 'turn_port', 3339)

    @property
    def wss_uri_prefix(self):
        """
        URI prefix for WebSocket communication channel.

        Returns:
            str: The URI prefix for WebSocket communication.
        """
        return self.get_string('Network', 'wss_uri_prefix', 'wss://oxchief.com/ws')

    @property
    def turn_uid(self):
        """
        Uid to coturn server used to facilitate WebRTC.

        Returns:
            str: The UID of the coturn server.
        """
        return os.environ.get("turn_uid")

    @property
    def turn_pwd(self):
        """
        Password to coturn server used to facilitate WebRTC.

        Returns:
            str: The password of the coturn server.
        """
        return os.environ.get("turn_pwd")

    @property
    def auth_token(self):
        """
        JWT token for robot auth.

        Returns:
            str: The JWT token for robot authentication.
        """
        return os.environ.get("auth_token")

    @property
    def robot_id(self):
        """
        Robot ID.

        Returns:
            str: The ID of the robot.
        """
        return os.environ.get("robot_id")
    
    @property
    def base_id(self):
        """
        Base Station ID.

        Returns:
            str: The ID of the base station.
        """
        return os.environ.get("base_id")

    @property
    def ardupilot_serial_1_name_substring(self):
        """
        Unique part of name of the serial 1 Flight Controller port. Specifically,
        this is the serial number assigned to a USB-to-Serial adapter.
        You can set this serial number on the card using
        https://github.com/DiUS/cp210x-cfg.git, i.e.:
        `sudo ./cp210x-cfg -m 10c4:ea60 -S 7702`

        Returns:
            str: The unique part of the name of serial 1 Flight Controller port.
        """
        return self.get_string('Serial', 'ardupilot_serial_1_name_substring', "_7702")

    @property
    def ardupilot_serial_2_name_substring(self):
        """
        Unique part of name of the serial 2 Flight Controller port. Specifically,
        this is the serial number assigned to a USB-to-Serial adapter.
        You can set this serial number on the card using
        https://github.com/DiUS/cp210x-cfg.git, i.e.:
        `sudo ./cp210x-cfg -m 10c4:ea60 -S 7704`

        Returns:
            str: The unique part of the name of serial 2 Flight Controller port.
        """
        return self.get_string('Serial', 'ardupilot_serial_2_name_substring', "_7704")

    @property
    def ardupilot_realsense_serial_name_substring(self):
        """
        Unique part of name of RealSense serial Flight Controller port. Specifically,
        this is the serial number assigned to a USB-to-Serial adapter.
        You can set this serial number on the card using
        https://github.com/DiUS/cp210x-cfg.git, i.e.:
        `sudo ./cp210x-cfg -m 10c4:ea60 -S 7706`

        Returns:
            str: The unique part of the name of RealSense serial Flight Controller port.
        """
        return self.get_string('Serial', 'ardupilot_realsense_serial_name_substring', "_7706")

    @property
    def gnss_rtcm_serial_name_substring(self):
        """
        Unique part of name of serial gnss corrections port.

        Returns:
            str: The unique part of the name of the serial gnss corrections port.
        """
        return self.get_string('Serial', 'gnss_rtcm_serial_name_substring', "_GNSS_receiver")

    @property
    def ardupilot_baud(self):
        """
        Baud rate of Flight Controller (i.e. Cube Orange) port.

        Returns:
            int: The baud rate of the Flight Controller port.
        """
        return self.get_int('Serial', 'ardupilot_baud', 921600)

    @property
    def gnss_rtcm_baud(self):
        """
        Baud rate of serial gnss corrections port.

        Returns:
            int: The baud rate of the serial gnss corrections port.
        """
        return self.get_int('Serial', 'gnss_rtcm_baud', 115200)

    @property
    def uri_info_silent(self):
        """
        URI Info Silent -- i.e. only send info; don't receive on this channel.

        Returns:
            str: The URI for the info silent channel.
        """
        return f"{self.wss_uri_prefix}/info/{self.robot_id}/none/"

    @property
    def uri_info_verbose(self):
        """
        URI Info Verbose -- send/receive info on this channel.

        Returns:
            str: The URI for the info verbose channel.
        """
        return f"{self.wss_uri_prefix}/info/{self.robot_id}/all/"

    @property
    def uri_control_verbose(self):
        """
        URI Control Verbose -- send/receive control data on this channel.

        Returns:
            str: The URI for the control verbose channel.
        """
        return f"{self.wss_uri_prefix}/control/{self.robot_id}/all/"

    @property
    def uri_startupdata_verbose(self):
        """
        URI Startup Data Verbose -- send/receive startup data on this channel.

        Returns:
            str: The URI for the startup data verbose channel.
        """
        return f"{self.wss_uri_prefix}/startupdata/{self.robot_id}/all/"

# Example usage:
if __name__ == "__main__":

    config = Config()

    logging.basicConfig(level=config.log_level)

    #test that the log level is where you want it
    logging.debug("Logging level test -- This is a debug message.")
    logging.info("Logging level test -- This is an info message.")
    logging.warning("Logging level test -- This is a warning message.")
    logging.error("Logging level test -- This is an error message.")
    logging.critical("Logging level test -- This is a critical message.")

    print(f"Enable debug: {config.enable_python_debug}")
    print(f"Python debug IP: {config.python_debug_ip}")
    print(f"Python debug port: {config.python_debug_port}")
    print(f"Log level: {config.log_level}")
