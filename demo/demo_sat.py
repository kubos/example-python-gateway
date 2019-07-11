import asyncio
import time
from random import randint

from demo.demo_telemetry import DemoTelemetry

class DemoSat:
    def __init__(self, name = "Space Oddity"):
        self.name = name
        self.telemetry = DemoTelemetry(name=name)
        self.definitions = {
            "ping": {
                "display_name": "Ping",
                "description": "Ping",
                "fields": []
            },
            "error": {
                "display_name": "Error Command",
                "description": "Always errors to show the error process.",
                "fields": []
            },
            "update_file_list": {
                "display_name": "Update File List",
                "description": "Downlinks the latest file list from the spacecraft.",
                "fields": []
            },
            "telemetry": {
                "display_name": "Start Telemetry Beacon",
                "description": "Commands the spacecraft to beacon Health and Status Telemetry",
                "fields": [
                    {"name": "mode", "type": "string", "range": ["NOMINAL","ERROR"]},
                    {"name": "duration", "type": "integer", "default": 300}
                ]
            },
            "connect": {
                "display_name": "Establish RF Lock",
                "description": "Points antennas and starts broadcasting carrier signal to establish RF lock with the spacecraft.",
                "fields": []
            },
            "safemode": {
                "display_name": "Safemode Command",
                "description": "Commands the spacecraft into safemode, shutting down all non-essential systems.",
                "fields": []
            }
        }

    async def command_filter(self, command, major_tom):
        if command.type == "ping":
            asyncio.ensure_future(major_tom.complete_command(command_id=command.id,output="pong"))

        elif command.type == "connect":
            """
            Simulates achieving an RF Lock with the spacecraft.
            """
            asyncio.ensure_future(major_tom.transmit_command_update(
                command_id = command.id,
                state = "preparing_on_gateway",
                dict = {"status": "Pointing Antennas"}
            ))
            await asyncio.sleep(5)
            asyncio.ensure_future(major_tom.transmit_command_update(
                command_id = command.id,
                state = "uplinking_to_system",
                dict = {"status": "Establishing RF Lock"}
            ))
            await asyncio.sleep(5)
            asyncio.ensure_future(major_tom.transmit_command_update(
                command_id = command.id,
                state = "preparing_on_gateway",
                dict = {"status": "Pointing Antennas"}
            ))
            await asyncio.sleep(5)
            asyncio.ensure_future(major_tom.complete_command(
                command_id = command.id,
                output = "Link Established"
            ))

        elif command.type == "telemetry":
            """
            Begins telemetry beaconing. 2 modes: error and nominal
            Error sends data with low battery voltage and low uptime counter
            Nominal sends normal data that just varies slightly
            """
            if command.fields['mode'] == "ERROR":
                asyncio.ensure_future(self.telemetry.error(
                    duration=command.fields['duration'],major_tom=major_tom))
            else:
                asyncio.ensure_future(self.telemetry.nominal(
                    duration=command.fields['duration'],major_tom=major_tom))

            asyncio.ensure_future(major_tom.complete_command(
                command_id=command.id,
                output=f"Started Telemetry Beacon in mode: {command.fields['mode']} for {command.fields['duration']} seconds."))

        elif command.type == "uplink_file":
            """
            Simulates uplinking a file by going through the whole progress bar scenario
            """
            pass

        elif command.type == "downlink_file":
            """
            "Downlinks" an image file and uploads it to Major Tom.
            Ignores the filename argument, and always does the same file.
            Maybe from NASA's APOD? https://api.nasa.gov/api.html#apod
            """
            pass

        elif command.type == "update_file_list":
            """
            Sends a dummy file list to Major Tom.
            """
            file_list = [
                {
                    "name": "PayloadImage004",
                    "size": randint(10000000,100000000),
                    "timestamp": int(time.time() * 1000),
                    "metadata": { "type": "image", "lat": (randint(-179,179) + .0001*randint(0,9999)), "lng": (randint(-179,179) + .0001*randint(0,9999)) }
                },
                {
                    "name": "PayloadImage003",
                    "size": randint(10000000,100000000),
                    "timestamp": int(time.time() * 1000) - 30*1000,
                    "metadata": { "type": "image", "lat": (randint(-179,179) + .0001*randint(0,9999)), "lng": (randint(-179,179) + .0001*randint(0,9999)) }
                },
                {
                    "name": "PayloadImage002",
                    "size": randint(10000000,100000000),
                    "timestamp": int(time.time() * 1000) - 90*1000,
                    "metadata": { "type": "image", "lat": (randint(-179,179) + .0001*randint(0,9999)), "lng": (randint(-179,179) + .0001*randint(0,9999)) }
                },
                {
                    "name": "PayloadImage001",
                    "size": randint(10000000,100000000),
                    "timestamp": int(time.time() * 1000) - 240*1000,
                    "metadata": { "type": "image", "lat": (randint(-179,179) + .0001*randint(0,9999)), "lng": (randint(-179,179) + .0001*randint(0,9999)) }
                }
            ]
            asyncio.ensure_future(major_tom.update_file_list(system=self.name,files=file_list))

        elif command.type == "execute_maneuver":
            """

            """
            pass

        elif command.type == "error":
            """
            Always errors.
            """
            asyncio.ensure_future(major_tom.transmit_command_update(
                command_id = command.id,
                state = "uplinking_to_system",
                dict = {
                    "status": "Uplinking Command"
                }
            ))
            await asyncio.sleep(3)
            asyncio.ensure_future(major_tom.fail_command(command_id=command.id,errors=["Command failed to execute."]))

        elif command.type == "safemode":
            """
            Simulates uplinking a safemode command, and the satellite confirming.
            """
            asyncio.ensure_future(major_tom.transmit_command_update(
                command_id = command.id,
                state = "transmitted_to_system",
                dict = {
                    "status": "Transmitted Safemode Command",
                    "payload": "0xFFFF"
                }
            ))
            await asyncio.sleep(10)
            asyncio.ensure_future(major_tom.complete_command(
                command_id = command.id,
                output = "Spacecraft Confirmed Safemode"
            ))
