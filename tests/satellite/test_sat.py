import sys
import json

from majortom_gateway import command
from satellite import Satellite

def test_stub():
    assert True

def test_command_processing():
    # To make it easier to interact with this Gateway, we are going to configure a bunch of commands for a satellite
    # called "Example FlatSat". Please see the associated json file to see the list of commands.
    # logger.debug("Setting up Example Flatsat satellite and associated commands")
    with open('../../satellite/example_commands.json','r') as f:
        command_bytes = f.read()
        s = Satellite()
        s.process_command(command_bytes)

