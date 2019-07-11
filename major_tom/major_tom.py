import asyncio
import json
import os
import re
import ssl
import logging
import time
import traceback
from base64 import b64encode

import websockets

from major_tom.command import Command

logger = logging.getLogger(__name__)

class MajorTom:
    def __init__(self, host, gateway_token, ssl_verify = False, basic_auth = None, https = True, ssl_ca_bundle = None, command_callback = None, error_callback = None):
        self.host = host
        self.gateway_token = gateway_token
        self.ssl_verify = ssl_verify
        self.basic_auth = basic_auth
        self.https = https
        if ssl_verify is True and ssl_ca_bundle is None:
            raise(ValueError('"ssl_ca_bundle" must be a valid path to a certificate bundle if "ssl_verify" is True. Could fetch from https://curl.haxx.se/docs/caextract.html'))
        else: self.ssl_ca_bundle = ssl_ca_bundle
        self.build_endpoints()
        self.command_callback = command_callback
        self.error_callback = error_callback
        self.websocket = None
        self.queued_payloads = []
        self.satellite = None

    def build_endpoints(self):
        if self.https:
            self.gateway_endpoint = "wss://" + self.host + "/gateway_api/v1.0"
        else:
            self.gateway_endpoint = "ws://" + self.host + "/gateway_api/v1.0"

    async def connect(self):
        if self.https:
            ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

            if self.ssl_verify:
                ssl_context.verify_mode = ssl.CERT_REQUIRED
                ssl_context.check_hostname = True
                # Should probably fetch from https://curl.haxx.se/docs/caextract.html
                ssl_context.load_verify_locations(self.ssl_ca_bundle)
            else:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE

        else:
            ssl_context = None

        extra_headers = {
            "X-Gateway-Token": self.gateway_token
        }
        if self.basic_auth != None:
            userAndPass = b64encode(str.encode(f"{self.basic_auth}")).decode("ascii")
            extra_headers['Authorization'] = 'Basic %s' %  userAndPass

        logger.info("Connecting to Major Tom")
        websocket = await websockets.connect(self.gateway_endpoint,
                                             extra_headers=extra_headers,
                                             ssl=ssl_context)
        logger.info("Connected to Major Tom")
        self.websocket = websocket
        await asyncio.sleep(1)
        await self.empty_queue()
        async for message in websocket:
            await self.handle_message(message)

    async def connect_with_retries(self):
        while True:
            try:
                return await self.connect()
            except (OSError, asyncio.streams.IncompleteReadError, websockets.ConnectionClosed) as e:
                self.websocket = None
                logger.warning("Connection error encountered, retrying in 5 seconds ({})".format(e))
                await asyncio.sleep(5)
            except Exception as e:
                logger.error("Unhandled {} in `connect_with_retries`".format(e.__class__.__name__))
                raise e

    async def handle_message(self, json_data):
        message = json.loads(json_data)
        message_type = message["type"]
        logger.debug("From Major Tom: {}".format(message))
        if message_type == "command":
            command = Command(message["command"])
            if self.command_callback != None:
                """
                TODO: Track the task and ensure it completes without errors
                reference: https://medium.com/@yeraydiazdiaz/asyncio-coroutine-patterns-errors-and-cancellation-3bb422e961ff
                """
                asyncio.ensure_future(self.command_callback(command, self))
            else:
                await self.fail_command(command.id, errors=["No command callback implemented"])
        elif message_type == "error":
            logger.error("Error from Major Tom: {}".format(message["error"]))
            if self.error_callback != None:
                asyncio.ensure_future(self.error_callback(message))
        elif message_type == "hello":
            logger.info("Major Tom says hello: {}".format(message))
        else:
            logger.warning("Unknown message type {} received from Major Tom: {}".format(message_type, message))

    async def empty_queue(self):
        while len(self.queued_payloads) > 0 and self.websocket:
            payload = self.queued_payloads.pop(0)
            await self.transmit(payload)

    async def transmit(self, payload):
        if self.websocket:
            logger.debug("To Major Tom: {}".format(payload))
            try:
                await self.websocket.send(json.dumps(payload))
            except Exception as e:
                self.websocket = None
                self.queued_payloads.append(payload)
        else:
            # Switch to https://docs.python.org/3/library/asyncio-queue.html
            self.queued_payloads.append(payload)

    async def transmit_metrics(self, metrics):
        """
        "metrics" must be of the format:
        [
            {
                "system": "foo",
                "subsystem": "foo2",
                "metric": "foo3",
                "value": 42,
                "timestamp": milliseconds utc
            },
            ...
        ]
        """
        await self.transmit({
            "type": "measurements",
            "measurements": [
                {
                    "system": metric["system"],
                    "subsystem": metric["subsystem"],
                    "metric": metric["metric"],
                    "value": metric["value"],
                    # Timestamp is expected to be millisecond unix epoch
                    "timestamp": metric.get("timestamp", int(time.time() * 1000))
                } for metric in metrics
            ]
        })

    async def transmit_events(self, events):
        await self.transmit({
            "type": "events",
            "events": [
                {
                    "system": event["system"],

                    "type": event.get("type","Gateway Event"),

                    "command_id": event.get("command_id", None),

                    "debug": event.get("debug", None),

                    # Can be "debug", "nominal", "warning", or "error".
                    "level": event.get("level", "nominal"),

                    "message": event["message"],

                    # Timestamp is expected to be millisecond unix epoch
                    "timestamp": event.get("timestamp", int(time.time() * 1000))
                } for event in events
            ]
        })

    async def transmit_command_update(self, command_id: int, state: str, dict = {}):
        update = {
            "type": "command_update",
            "command": {
                "id": command_id,
                "state": state
            }
        }
        for field in dict:
            update['command'][field] = dict[field]
        await self.transmit(update)

    async def fail_command(self, command_id: int, errors: list):
        await self.transmit_command_update(command_id = command_id, state = "failed", dict = {"errors":errors})

    async def complete_command(self, command_id: int, output: str):
        await self.transmit_command_update(command_id = command_id, state = "completed", dict = {"output":output})

    async def transmitted_command(self, command_id: int, payload = "None Provided"):
        await self.transmit_command_update(command_id = command_id, state = "transmitted_to_system", dict = {"payload":payload})

    async def update_command_definitions(self, system: str, definitions: dict):
        """
        "definitions" must be of the format:
        {
          "command": {
            "display_name": "Command Name To Display",
            "description": "Description to give context to the operator.",
            "fields": [
              {"name": "Field Name 1", "type": "number"},
              ...
            ]
          },
          ...
        }
        """
        await self.transmit({
            "type": "command_definitions_update",
            "command_definitions": {
                "system": system,
                "definitions": definitions
            }
        })

    async def update_file_list(self, system: str, files: list, timestamp = int(time.time() * 1000)):
        """
        "files" must be of the format:
        [
          {
            "name": "earth.tiff",
            "size": 1231040,
            "timestamp": 1528391000000,
            "metadata": { "type": "image", "lat": 40.730610, "lng": -73.935242 }
          },
          ...
        ]
        """
        await self.transmit({
            "type": "file_list",
            "file_list": {
                "system": system,
                "timestamp": timestamp,
                "files": files
            }
        })
