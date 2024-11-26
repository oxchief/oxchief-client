"""
Author: Wayne Baswell

Networking related utilities
"""
import asyncio
import logging
import json
import os
import time

import websockets

#we need `from websockets import client` for the websockets.client.WebSocketClientProtocol
#type to work down below -- don't let the linter convince you to
#delete it
from websockets import client

from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription
from aiortc import RTCIceServer, RTCConfiguration, RTCDataChannel
from aiortc.contrib.signaling import object_from_string

from config import Config
import flight_controller
import util

class Network:
    """
    Handles networking tasks such as:
        - Setting up webrtc connection between robot and web UI
        - Provide simple method to send message to client
        - Start / Stop Tailscale service on host Raspberry Pi
    """
    def __init__(self, config=Config()):
        self.config = config
        self.ice_servers = []
        self.rtc_data_channels = {}
        self.pcs:set[RTCPeerConnection()] = set()
        self.setup_ice_servers()

    def setup_ice_servers(self) -> None:
        """stun/turn config for the RTC connection"""
        self.ice_servers.append(
            RTCIceServer(f"stun:{self.config.stun_url}:{self.config.stun_port}"))
        self.ice_servers.append(RTCIceServer(
            f"turn:{self.config.turn_url}:{self.config.turn_port}?transport=tcp",
            username=self.config.turn_uid,
            credential=self.config.turn_pwd))
        self.ice_servers.append(RTCIceServer(
            f"turn:{self.config.turn_url}:{self.config.turn_port}?transport=udp",
            username=self.config.turn_uid,
            credential=self.config.turn_pwd))

    def channel_log(self, channel:RTCDataChannel, message:str) -> None:
        """Log data we send across channel

        Args:
            channel (RTCDataChannel): rtc data channel
            message (str): message to log
        """
        logging.debug("channel(%s) %s", channel.label, message)

    def channel_send(self, channel:RTCDataChannel, message:str) -> None:
        """
        Log message and then send data across the data channel to the remote peer.

        Args:
            channel (RTCDataChannel): data channel i.e. rtc connection
            message (str): data to send over data channel
        """
        self.channel_log(channel, message)
        channel.send(message)

    async def start_vpn(self) -> None:
        """Start Tailscale VPN service"""
        os.system('echo "sudo service tailscaled start;sudo tailscale up" > /oxpipe')

    async def stop_vpn(self) -> None:
        """Stop Tailscale VPN service"""
        os.system('echo "sudo tailscale down;sudo service tailscaled stop" > /oxpipe')

    async def send_message_to_all_attached_rtc_data_channels(self, message:str) -> None:
        """
        Send message to all rtc clients

        Args:
            message (str): Message to send
        """
        for value in self.rtc_data_channels.values():
            if value.readyState == "open":
                self.channel_send(value, message)
                #asyncio.create_task(channel_send(value, message))

    async def simple_message_send(self,
                                m_type:str,
                                message:str,
                                quote_message=True,
                                websocket_uri=None,
                                send_over_web_rtc=True) -> None:
        """
        Convenience function to send a message out to the client (i.e. OxChief web ui).

        Parameters:
            m_type (str): JSON message `mType` property
            message (str): JSON `message` property
            quote_message (bool, optional): Quote the JSON message? Defaults to True.
            websocket_uri (_type_, optional): URI to send websocket message over. 
            Defaults to `Config.uri_info_silent`.
            send_over_web_rtc (bool, optional): Send the mssage over WebRTC (in 
            addition to WebSocket). Defaults to True.

        Returns: None
        """
        if websocket_uri is None:
            websocket_uri = self.config.uri_info_silent

        time_millis = time.time_ns() // 1_000_000
        # build json
        if quote_message:
            message_json_str = '{ "messageType":"command-reply", "time": ' + \
                str(time_millis) + ', "mType": "' + m_type + \
                    '", "message": "' + message + '"}'
        else:
            message_json_str = '{ "messageType":"command-reply", "time": ' + \
                str(time_millis) + ', "mType": "' + m_type + \
                    '", "message": ' + message + '}'

        # send via webrtc
        if send_over_web_rtc:
            webrtc_task = asyncio.create_task(
                self.send_message_to_all_attached_rtc_data_channels(message_json_str))

        # send via websocket
        async with websockets.connect(websocket_uri,
                                    extra_headers={"jwt":
                                        self.config.auth_token}) as ws:
            await ws.send(message_json_str)

        await webrtc_task

    def robot_log(self, log:str, level:str="INFO") -> None:
        """Send log message out to client (i.e. OxChief web ui)."""
        logging.info(log)
        util.asyncio_create_task_disappear_workaround(
            self.simple_message_send("robot_log",
                            '{"log": "' + log + '", "level": "' + level + '"}', 
                            False))

    async def send_robot_status_out_through_webrtc(self) -> None:
        """
        TODO -- Baswell Jan 26, 2024 -- I'm not sure this method is doing anything
        other than sending out the robot status once on startup and then
        disappearing forever..?? Should it just be deleted (and also)
        delete where it's called down in `asycio.gather(...)` ?
        """
        robot_status_json = await flight_controller.robot_json_status_string()
        util.asyncio_create_task_disappear_workaround(
            self.send_message_to_all_attached_rtc_data_channels(
                robot_status_json))
        #limit webrtc message rate by sleeping every cycle
        await asyncio.sleep(.5)

    async def quiet_close(self, pc:RTCPeerConnection) -> None:
        """ Suppress errors closing out RTCPeerConnection """
        try:
            await pc.close()
        except Exception as e:
            logging.error("error closing out RTCPeerConnections: ")
            logging.error(e)

    async def clean_up(self, _pcs:set[RTCPeerConnection]) -> None:
        """
        Close rtc peer connections
        Args:
            _pcs (set[RTCPeerConnection]): connections to close
        """
        # close peer connections
        coros = [await self.quiet_close(pc) for pc in _pcs]
        asyncio.gather(*coros)
        _pcs.clear()

    async def build_rtc_connection(self,
                                   message_json:any,
                                   the_message_processor:any,
                                   websock:websockets.client.WebSocketClientProtocol) -> None:
        """
        Build rtc connection. Connection is established by negotiating over
        the given `websock` websocket connection.

        Args:
            message_json (any): message json to process
            the_message_processor (any): message_processor.MessageProcessor
                instance to process messages
            websock (websockets.client.WebSocketClientProtocol): websocket 
                connection to use for communication
        """
        received_message = message_json["message"]
        descr = object_from_string(json.dumps(received_message))

        if isinstance(descr, RTCSessionDescription):
            logging.debug("in ininstance(descr, RTCSessionDescription)")
            pc = RTCPeerConnection(RTCConfiguration(self.ice_servers))
            self.pcs.add(pc)
            await pc.setRemoteDescription(descr)
            logging.debug("await success!")
            if received_message["type"] == "offer":
                logging.debug("offer detected!")
                # send answer
                await pc.setLocalDescription(await pc.createAnswer())
                #await signaling.send(pc.localDescription)
                origin = message_json["origin"]
                the_message = ('{"sdp":"' + pc.localDescription.sdp +
                                '", "type":"' + pc.localDescription.type +
                                '", "sender": "pi"}')
                rtc_answer = '{ "messageType":"rtc-signal", "origin":"' + \
                    str(origin) + '", "message": ' + the_message + "}"
                logging.debug(f"sending rtc_answer: \n{rtc_answer}")
                util.asyncio_create_task_disappear_workaround(websock.send(rtc_answer))

                @pc.on("datachannel")
                def on_datachannel(channel):
                    self.channel_log(channel, "created by remote party")
                    self.rtc_data_channels[origin] = channel

                    @channel.on("message")
                    def on_message(message):
                        self.channel_log(channel, message)

                        if (isinstance(message, str)
                            and message.startswith("ping")):
                            # this is the ping/pong message
                            latency = time.time()*1000-int(message[4:])
                            logging.debug("LATENCY RTC from client to server:")
                            logging.debug(f"{latency}")
                            self.channel_send(channel, "pong" + message[4:])
                                #asyncio.create_task(create_data_channel(pc))
                        elif isinstance(message, str):

                            #assume this is a command json
                            #blob coming in from the
                            #client -- process
                            #baswell pick up here
                            #baswell saturday morning begin
                            ###############################################
                            ###############################################

                            message_json = json.loads(message)
                            message_type = message_json["messageType"]
                            message_json_first_50 = f"{message_json}"
                            if len(message_json_first_50) > 50:
                                message_json_first_50 = message_json_first_50[:50]
                            logging.debug("rtc received message: %s",
                                            message_json_first_50)
                            if message_type == "command":
                                message = message_json["message"].lower()
                                asyncio.ensure_future(
                                    the_message_processor.process_command_message(
                                        message,
                                        self.send_message_to_all_attached_rtc_data_channels))
                            elif message_type == "meta":
                                message_str = message_json["message"]
                                message_json = json.loads(message_str)
                                util.asyncio_create_task_disappear_workaround(the_message_processor.process_meta_message(message_json))

                        elif isinstance(descr, RTCIceCandidate):
                            logging.debug("in isinstance(descr, RTCIceCandidate")
                            pc.addIceCandidate(descr)
                        else:
                            logging.debug("COULD NOT DETERMINE rtc-signal message type!")

                @pc.on("connectionstatechange")
                async def on_connectionstatechange():
                    logging.debug("Connection state is %s", pc.connectionState)
                    if pc.connectionState == "failed":
                        await pc.close()
                        self.pcs.discard(pc)
