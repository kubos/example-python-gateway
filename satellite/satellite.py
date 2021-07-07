'''
This is a fake satellite. 

It takes the place of a simulator, flatsat, engineering model, or real satellite.
'''
import time
import logging

from random import randint
from threading import Timer

from transform import stubs
from commands import CommandStatus
from .telemetry import FakeTelemetry

logger = logging.getLogger(__name__)

class CommandCancelledError(RuntimeError):
    """Raised when a command is cancelled to halt the progress of that command"""

def safeget(dct, *keys):
    for key in keys:
        try:
            dct = dct[key]
        except KeyError:
            return None
    return dct

class Satellite:
    def __init__(self):
        self.name = "Example FlatSat"
        self.file_list = []
        self.running_commands = {}
        self.force_cancel = True  # Forces all commands to be cancelled, regardless of run state.
        self.telemetry = FakeTelemetry(name=self.name)

    def add_running_command(self, command_id, cancel=False):
        self.running_commands[str(command_id)] = {"cancel": False}

    def send_to_gateway(self, command, gateway, response):
        binary = stubs.translate_command_to_binary(command)
        packetized = stubs.packetize(binary)
        encrypted = stubs.encrypt(packetized)   
        gateway.satellite_response(encrypted, response)

    def check_cancelled(self, id):
        ''' Checks to see if a command-in-progress has been cancelled. '''
        if safeget(self.running_commands, str(id), "cancel"):
            # Raise an exception to immediately stop the command operations
            raise(CommandCancelledError(f"Command {id} Cancelled"))

    def process_command(self, bytes, gateway):
        logger.info(f"Satellite received: {bytes}")

        # The satellite would have it's own command transformation -- we'll just re-use the stubs
        decrypted = stubs.decrypt(bytes)  
        depacketized = stubs.depacketize(decrypted)
        command = stubs.translate_binary_to_command(depacketized)

        if command.type == "ping":
            binary = stubs.translate_command_to_binary(command)
            packetized = stubs.packetize(binary)
            encrypted = stubs.encrypt(packetized)    
            r = Timer(1.0, gateway.satellite_response, (encrypted, "pong"))
            r.start()

        elif command.type == "telemetry":
            # Begins telemetry beaconing. 2 modes: error and nominal
            # Error sends data with low battery voltage and low uptime counter
            # Nominal sends normal data that just varies slightly

            self.telemetry.safemode = False

            errors = self.validate(command)
            duration =  command.fields['duration']
            mode = command.fields['mode']
            if errors:
                gateway.fail_command(command.id, errors)
            else:
                msg = f"Started Telemetry Beacon in mode: {command.fields['mode']} for {command.fields['duration']} seconds."
                gateway.set_command_status(command.id, CommandStatus.COMPLETED, payload=msg)
                timeout = time.time() + duration
                while time.time() < timeout:
                    self.check_cancelled(id=command.id)
                    metrics, errors = self.telemetry.generate_telemetry(mode=mode)
                    if not errors:
                        gateway.update_metrics(metrics)
                    else:
                        logger.warn(errors)
                    time.sleep(1)
        
        elif command.type == "update_file_list":
            """
            Sends a dummy file list of images to Major Tom.

            Note that this command is special. In addition to the normal location in the commands list, 
            it appears as a button on the "Downlink" tab for a satellite. 
            
            Certain commands are 'known' to Major Tom, and can appear in more convenient places in the UI because of that. 
            See the documentation for a full list of such commands.
            """
            for i in range(1, randint(2, 4)):
                self.file_list.append({
                    "name": f'Payload-Image-{(len(self.file_list)+1):04d}.png',
                    "size": randint(2000000, 3000000),
                    "timestamp": int(time.time() * 1000) + i*10,
                    "metadata": {"type": "image", "lat": (randint(-89, 89) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                })

                if self.command.fields['show_hidden']:
                    for i in range(1, randint(1, 3)):
                        self.file_list.append({
                            "name": f'.thumb-{(len(self.file_list)+1):04d}.png',
                            "size": randint(200, 300),
                            "timestamp": int(time.time() * 1000) + i*10,
                            "metadata": {"type": "image", "lat": (randint(-89, 89) + .0001*randint(0, 9999)), "lng": (randint(-179, 179) + .0001*randint(0, 9999))}
                        })

            self.check_cancelled(id=command.id)
            logger.info("Files: {}".format(self.file_list))

            r = Timer(0.1, gateway.update_file_list, kwargs={"system":self.name, "files":self.file_list})
            r.start()
            time.sleep(10)
            self.check_cancelled(id=command.id)
            gateway.set_command_status(
                command_id=command.id, 
                status=CommandStatus.COMPLETED, 
                payload="Updated Remote File List")

        elif command.type == "error":
            """ Simulates a command erroring out. """
            logger.warn(f"We can print a warning to the log here.")
            errors = [f"Command purposely failed."]
            gateway.fail_command(command.id, errors=errors)

        else:
            # We'd want to generate an error if the command wasn't found.
            logger.warn(f"Satellite does not recognize command {command.type}")
            errors = [f"Command {command.type} not found on Satellite."]
            gateway.fail_command(command.id, errors=errors)


    ''' Command validator. 
    Returns a list of errors if any are found. 
    Otherwise returns None '''
    def validate(self, command):
        if command.type == "telemetry":
            if type(command.fields['duration']) != type(int()):
                return [f"Duration type is invalid. Must be an int. Type: {type(command.fields['duration'])}"]
        
        return None