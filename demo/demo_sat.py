import asyncio
import time
import traceback
from random import randint
import requests
import logging
import re
import json
import datetime
import os

from demo.demo_telemetry import DemoTelemetry

logger = logging.getLogger(__name__)


class DemoSat:
    def __init__(self, name="Space Oddity"):
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
                    {"name": "mode", "type": "string", "range": ["NOMINAL", "ERROR"]},
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
            },
            "uplink_file": {
                "display_name": "Uplink File",
                "description": "Uplink a staged file to the spacecraft.",
                "fields": [
                    {"name": "gateway_download_path", "type": "string"}
                ]
            },
            "downlink_file": {
                "display_name": "Downlink File",
                "description": "Downlink an image from the Spacecraft.",
                "fields": [
                    {"name": "filename", "type": "string"}
                ]
            }
        }

    async def command_filter(self, command, major_tom):
        try:
            if command.type == "ping":
                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id, output="pong"))

            elif command.type == "connect":
                """
                Simulates achieving an RF Lock with the spacecraft.
                """
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="preparing_on_gateway",
                    dict={"status": "Pointing Antennas"}
                ))
                await asyncio.sleep(5)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={"status": "Broadcasting Acquisition Signal"}
                ))
                await asyncio.sleep(5)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="acked_by_system",
                    dict={"status": "Received acknowledgement from Spacecraft"}
                ))
                await asyncio.sleep(3)
                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id,
                    output="Link Established"
                ))

            elif command.type == "telemetry":
                """
                Begins telemetry beaconing. 2 modes: error and nominal
                Error sends data with low battery voltage and low uptime counter
                Nominal sends normal data that just varies slightly
                """
                if command.fields['mode'] == "ERROR":
                    asyncio.ensure_future(self.telemetry.error(
                        duration=command.fields['duration'], major_tom=major_tom))
                else:
                    asyncio.ensure_future(self.telemetry.nominal(
                        duration=command.fields['duration'], major_tom=major_tom))

                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id,
                    output=f"Started Telemetry Beacon in mode: {command.fields['mode']} for {command.fields['duration']} seconds."))

            elif command.type == "update_file_list":
                """
                Sends a dummy file list to Major Tom.
                """
                file_list = [
                    {
                        "name": "PayloadImage004",
                        "size": randint(10000000, 100000000),
                        "timestamp": int(time.time() * 1000),
                        "metadata": {"type": "image", "lat": (randint(-179, 179) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                    },
                    {
                        "name": "PayloadImage003",
                        "size": randint(10000000, 100000000),
                        "timestamp": int(time.time() * 1000) - 30*1000,
                        "metadata": {"type": "image", "lat": (randint(-179, 179) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                    },
                    {
                        "name": "PayloadImage002",
                        "size": randint(10000000, 100000000),
                        "timestamp": int(time.time() * 1000) - 90*1000,
                        "metadata": {"type": "image", "lat": (randint(-179, 179) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                    },
                    {
                        "name": "PayloadImage001",
                        "size": randint(10000000, 100000000),
                        "timestamp": int(time.time() * 1000) - 240*1000,
                        "metadata": {"type": "image", "lat": (randint(-179, 179) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                    }
                ]
                asyncio.ensure_future(major_tom.update_file_list(system=self.name, files=file_list))
                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id,
                    output="Updated Remote File List"
                ))

            elif command.type == "execute_maneuver":
                """

                """
                pass

            elif command.type == "error":
                """
                Always errors.
                """
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Uplinking Command"
                    }
                ))
                await asyncio.sleep(3)
                asyncio.ensure_future(major_tom.fail_command(
                    command_id=command.id, errors=["Command failed to execute."]))

            elif command.type == "safemode":
                """
                Simulates uplinking a safemode command, and the satellite confirming.
                """
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="transmitted_to_system",
                    dict={
                        "status": "Transmitted Safemode Command",
                        "payload": "0xFFFF"
                    }
                ))
                await asyncio.sleep(10)
                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id,
                    output="Spacecraft Confirmed Safemode"
                ))

            elif command.type == "uplink_file":
                """
                Simulates uplinking a file by going through the whole progress bar scenario
                """
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="processing_on_gateway",
                    dict={
                        "status": "Downloading Staged File from Major Tom for Transmission"
                    }
                ))
                try:
                    filename, content = major_tom.download_staged_file(
                        gateway_download_path=command.fields["gateway_download_path"])
                except Exception as e:
                    asyncio.ensure_future(major_tom.fail_command(command_id=command.id, errors=[
                                          "File failed to download", f"Error: {traceback.format_exc()}"]))

                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 10,
                        "progress_1_max": 100,
                        "progress_1_label": "Percent Transmitted",
                        "progress_2_current": 0,
                        "progress_2_max": 100,
                        "progress_2_label": "Percent Acked"
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 30,
                        "progress_2_current": 10
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 50,
                        "progress_2_current": 30
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 70,
                        "progress_2_current": 50
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 90,
                        "progress_2_current": 70
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "status": "Transmitting File to Spacecraft",
                        "progress_1_current": 100,
                        "progress_2_current": 90
                    }
                ))
                await asyncio.sleep(1)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="uplinking_to_system",
                    dict={
                        "progress_1_current": 100,
                        "progress_2_current": 100
                    }
                ))
                await asyncio.sleep(2)
                asyncio.ensure_future(major_tom.complete_command(
                    command_id=command.id,
                    output=f"File {filename} Successfully Uplinked to Spacecraft"
                ))

            elif command.type == "downlink_file":
                """
                "Downlinks" an image file and uploads it to Major Tom.
                Ignores the filename argument, and always pulls the latest
                image from NASA's Epic cam.
                """
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="downlinking_from_system",
                    dict={
                        "status": "Downlinking File from Spacecraft"
                    }
                ))

                # Get the latest image of the earth from epic cam
                try:
                    # Get the image info and download url
                    url = "https://epic.gsfc.nasa.gov/api/natural"
                    r = requests.get(url)
                    if r.status_code != 200:
                        raise(RuntimeError(f"File Download Failed. Status code: {r.status_code}"))

                    # Retrieve necessary data from the response
                    images = json.loads(r.content)
                    latest_image = images[-1]
                    for field in latest_image:
                        logger.debug(f'{field}  :  {latest_image[field]}')
                    image_date = datetime.datetime.strptime(
                        latest_image["date"], "%Y-%m-%d %H:%M:%S")
                    image_filename = latest_image["image"] + ".png"
                    image_url = "https://epic.gsfc.nasa.gov/archive/natural" + \
                        image_date.strftime("/%Y/%m/%d") + "/png/" + image_filename

                    # Get the image itself
                    image_r = requests.get(image_url)
                    if image_r.status_code != 200:
                        raise(RuntimeError(
                            f"File Download Failed. Status code: {image_r.status_code}"))

                    # Write file to disk
                    with open(image_filename, "wb") as f:
                        f.write(image_r.content)
                    logger.info(f"Downloaded Image: {image_filename}")
                except RuntimeError as e:
                    asyncio.ensure_future(major_tom.fail_command(command_id=command.id, errors=[
                                          "File failed to download", f"Error: {traceback.format_exc()}"]))

                # Update command in Major Tom
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="processing_on_gateway",
                    dict={
                        "status": f'File: "{image_filename}" Downlinked, Validating'
                    }
                ))
                await asyncio.sleep(3)
                asyncio.ensure_future(major_tom.transmit_command_update(
                    command_id=command.id,
                    state="processing_on_gateway",
                    dict={
                        "status": f'"{image_filename}" is Valid, Uploading to Major Tom'
                    }
                ))

                # Upload file to Major Tom with Metadata
                try:
                    major_tom.upload_downlinked_file(
                        filename=image_filename,
                        filepath=image_filename,
                        system=self.name,
                        command_id=command.id,
                        content_type=image_r.headers["Content-Type"],
                        metadata=latest_image
                    )
                    asyncio.ensure_future(major_tom.complete_command(
                        command_id=command.id,
                        output=f'"{image_filename}" successfully downlinked from Spacecraft and uploaded to Major Tom'
                    ))
                except RuntimeError as e:
                    asyncio.ensure_future(major_tom.fail_command(command_id=command.id, errors=[
                                          "Downlinked File failed to upload to Major Tom", f"Error: {traceback.format_exc()}"]))

                # Remove file now that it's uploaded so we don't fill the disk.
                os.remove(image_filename)

        except Exception as e:
            asyncio.ensure_future(major_tom.fail_command(command_id=command.id, errors=[
                                  "Command Failed to Execute. Unknown Error Occurred.", f"Error: {traceback.format_exc()}"]))
