import logging
import time
from asgiref.sync import async_to_sync
from random import randint
from . import stubs
from .statuses import CommandStatus
from satellite.satellite import Satellite

logger = logging.getLogger(__name__)


class Gateway:
    def __init__(self, *args, **kwargs):
        # For simplicity, our gateway is going to talk with a fake satellite. 
        # We'll instantiate that now.
        # For a flatsat, engineering model, or company-owned groundstation, this is where you might set up 
        # your communication to the respective device(s).
        # For a Ground Station Network, support is included in the transmit_blob() and receive_blob() methods.

        self.satellite = Satellite()
        self.api = kwargs.get("api", None)

    def command_callback(self, command, api):
        ''' The command callback is where messages are received when an operator or script executes a command. 
            The goal of this method is to translate the command between Major Tom's definition and the
            actual bytes to be sent to the spacecraft or groundstation.           
        '''
        if command.type == "ping":
            # The function argument `command` is Major Tom's populated command definition. 
            # It will need to be converted into something your satellite understands. 
            # We stub out those processing steps here.

            # If these steps take time, you'll want to let the operator know by updating the status in the UI:
            logger.info("Preparing for satellite")
            self.set_command_status(command.id, CommandStatus.PREPARING)
            binary = stubs.translate_command_to_binary(command)
            packetized = stubs.packetize(binary)
            encrypted = stubs.encrypt(packetized)    

            # Send it to the satellite. We include a reference to ourself allow an asynchronous response.
            # See satellite_response()
            # Again, you may choose to update the UI status:
            logger.info("Sending to satellite")
            self.set_command_status(command.id, CommandStatus.TRANSMITTED)
            self.satellite.process_command(bytes=encrypted, gateway=self)

        elif command.type == "all_transitions":
            # We'll go through each of the command states. After sending this command from Major Tom, you'll
            # want to monitor the status of it on the Communications Card. The status will change 
            # according to the code below.
            # Note that 2 separate progress bars can be shown on any state ending in -ing.
            self.set_command_status(command.id, CommandStatus.PREPARING)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.EXECUTING)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.TRANSMITTED)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.ACKED)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.PROCESSING)
            self.fake_progress_bar(command.id, CommandStatus.PROCESSING, "Processing slowly to show progress bars...")
            time.sleep(2)
            self.set_command_status(command.id, CommandStatus.CANCELLED)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.FAILED)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.UPLINKING)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.DOWNLINKING)
            time.sleep(4)
            self.set_command_status(command.id, CommandStatus.COMPLETED)
            time.sleep(4)

        elif command.type == "ping_through_leaf_network":
            # This demonstrates how to send a command through a groundstation network
            logger.info("Preparing GSN Ping")

            # We start with translating, packetizing, and/or encrypting the command
            self.set_command_status(command.id, CommandStatus.PREPARING)
            binary = stubs.translate_command_to_binary(command)
            packetized = stubs.packetize(binary)
            encrypted = stubs.encrypt(packetized)   

            logger.info("Sending command to Leaf")
            context = {
                # We use all zeroes for the Leaf sandbox. Eventually, this will
                # be replaced with a field for Pass ID 
                "norad_id": "00000",
            }
            self.set_command_status(command.id, CommandStatus.UPLINKING)
            async_to_sync(self.api.transmit_blob)(blob=encrypted, context=context)
            # If all goes well, the response will come back on `received_blob_callback()`

        elif command.type == "connect":
            """
            Simulates achieving an RF Lock with the spacecraft.
            """
            time.sleep(2)
            self.satellite.check_cancelled(id=command.id)
            self.set_command_status(command.id, CommandStatus.PREPARING)

            time.sleep(4)
            self.satellite.check_cancelled(id=command.id)
            self.set_command_status(command.id, CommandStatus.UPLINKING)

            time.sleep(4)
            self.satellite.check_cancelled(id=command.id)
            self.set_command_status(command.id, CommandStatus.ACKED)

            time.sleep(3)
            self.satellite.check_cancelled(id=command.id)
            self.set_command_status(command.id, CommandStatus.COMPLETED)

        else:
            # You may not have special processing that is individualized to each command.
            # In that case, you can use something generic like the code below:
            logger.info("Preparing for satellite")
            self.set_command_status(command.id, CommandStatus.PREPARING)
            binary = stubs.translate_command_to_binary(command)
            packetized = stubs.packetize(binary)
            encrypted = stubs.encrypt(packetized)    

            # Send it to the satellite. We include a reference to ourself in order to mimic an asynchronous response.
            # See satellite_response()
            # Again, you may choose to update the UI status:
            logger.info("Sending to satellite")
            self.set_command_status(command.id, CommandStatus.TRANSMITTED)
            self.satellite.process_command(bytes=encrypted, gateway=self)
   

    def fake_progress_bar(self, command_id, state, status):
        for i in range(0,101,20):
            progress={
                "progress_1_current": i,
                "progress_1_max": 100,
                "progress_1_label": "Percent Processed",
                "progress_2_current": i,
                "progress_2_max": 100,
                "progress_2_label": "Second Progress Bar"
            }
            self.set_progress_bar(command_id=command_id, state=state, status=status, progress_dict=progress)
            time.sleep(1)

    def cancel_callback(self, command_id, api, *args, **kwargs):
        # When an operator or script attempts to cancel a command, this function receives the message.

        # Take steps to cancel the command. 
        success = self.cancel_command(command_id)

        # Let the operator know the command was cancelled
        if success:
            self.set_command_status(command_id, CommandStatus.CANCELLED)

    def cancel_command(self, command_id):
        # Stub
        return True

    def update_file_list(self, system, files):
        async_to_sync(self.api.update_file_list)(system=system, files=files)

    def received_blob_callback(self, blob, context, *args, **kwargs):
        # When we receive data from a Groundstation Network, this callback is called.
        # The data comes in the "blob" argument.
        # The "context" argument contains information around the conditions under which the data were obtained -- things like a Pass ID, Norad ID, or similar.
        # An optional "metadata" argument may contain traceability-related data, such as timestamps or internal processing steps.
        if context.get('uuid', None) is not None:
            logger.info(f"Got {context['uuid']}: Size: " + str(len(blob)))    
        else:
            logger.info("Got blob of size: " + str(len(blob)))
        # logger.info("Context was:" + str(context))
        # stubs.debug_hexprint(blob)
        # logger.info("Metadata was:" + str(metadata))

        # Try processsing
        try:
            decrypted = stubs.decrypt(blob)    
            depacketized = stubs.depacketize(decrypted)
            command = stubs.translate_binary_to_command(depacketized)
            # Once the data is understandable, you can route it to the proper
            # processing pipeline and inform the operator.
            self.set_command_status(command.id, CommandStatus.COMPLETED)
        except:
            pass

    def update_metrics(self, metrics):
        # Metrics are of the form:
        # {
        #     "system": "Satellite Name",
        #     "subsystem": "bus",
        #     "metric": "batt1_volts",
        #     "value": 7.23,
        #     "timestamp": int(time.time() * 1000)
        # }
        async_to_sync(self.api.transmit_metrics)(metrics=metrics)

    def set_command_status(self, command_id, status, **kwargs):
        ''' A helper method for updating Major Tom's display with a particular status for a specific command. '''
        if self.api is None:
            raise Exception("Websocket API must be set.")
        logger.info(f"Setting command #{command_id} status to {status}")
        args = {"status": status}
        args.update(kwargs)
        async_to_sync(self.api.transmit_command_update)(
            command_id=command_id,
            state=status,
            dict=args,
        )

    def set_progress_bar(self, command_id, state, status, progress_dict):
        ''' A helper method for updating Major Tom's display with a progress bar for a particular command. '''
        if self.api is None:
            raise Exception("Websocket API must be set.")
        info = {"status": status}
        info.update(progress_dict)
        async_to_sync(self.api.transmit_command_update)(
            command_id=command_id,
            state=state,
            dict=info,
        )

    def fail_command(self, command_id, errors):
        ''' A helper method to fail a command. The 'errors' argument must be a list '''
        self.set_command_status(command_id, CommandStatus.FAILED, errors=errors)

    def error_callback(self, message, *args, **kwargs):
        # It is important to implement this callback, as this is the main communication channel when Major Tom detects errors.
        logger.warn(message)

    def rate_limit_callback(self, message, *args, **kwargs):
        logger.warn(message)

    def transit_callback(self, message, *args, **kwargs):
        # This callback can be used to trigger code at the beginning of a pass.
        transit = message["transit"]
        logger.info(f"Ahoy {transit['satellite_name']} from {transit['ground_station_name']}!")

    ### CONNECTION TO SATELLITE ###

    def satellite_response(self, encrypted, response, *args, **kwargs):
        '''
        This method can be called asynchronously by the satellite to mimic raw packets being received from a 
        flatsat or customer-owned groundstation.
        '''
        decrypted = stubs.decrypt(encrypted)  
        depacketized = stubs.depacketize(decrypted)
        command = stubs.translate_binary_to_command(depacketized)

        payload = response
        self.set_command_status(command_id=command.id, status=CommandStatus.COMPLETED, payload=payload)
