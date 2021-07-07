import sys
import json
import unittest
from unittest.mock import call
import pytest
import asyncio

try:
    # Python 3.8+
    from unittest.mock import AsyncMock
except ImportError:
    # Python 3.6+
    from mock import AsyncMock

from majortom_gateway.command import Command
from majortom_gateway import gateway_api
from satellite import Satellite
from transform import stubs
from gateway import Gateway

class TypeMatcher:
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def __eq__(self, other):
        return isinstance(other, self.expected_type)

@pytest.fixture
def callback_mock():
    future = asyncio.Future()
    future.set_result(None)
    fn = AsyncMock(return_value=future) 
    return fn


#@pytest.mark.asyncio examplej test
#async def test_calls_transit_callback(callback_mock):
#    gw = GatewayAPI("host", "gateway_token", transit_callback=callback_mock)
#    # ToDo: Update this example message
#    message =  {
#        "type": "transit",
#    }
#
#    res = await gw.handle_message(json.dumps(message))
#    
#    # The transit callback is given the raw message
#    callback_mock.assert_called_once_with(message)


class TestCommandDefinitions(unittest.TestCase):
    def setUp(self):
        self.gw_api = gateway_api.GatewayAPI("host", "gateway_token", 
        command_callback=callback_mock, transit_callback=callback_mock)
        self.gateway = Gateway(api=self.gw_api)

    def test_process_command(self):
        system = "Example Flatsat" # Match 'system' identifier with Gateway CommandDef
        json_bytes = """{
            "type": "command",
            "id": "update_file_list",
            "system": "Example FlatSat", 
            "display_name": "Update File List",
            "tags": ["files", "operations"],
            "fields": [
                {"name": "show_hidden", "type": "boolean", "value": true }
            ]
        }"""
        jl = json.loads(json_bytes)
        cmd = Command(jl)

        cmd_bytes = stubs.translate_command_to_binary(cmd)
        print("CMD: #{cmd_bytes}", cmd_bytes)


        with open('satellite/example_commands.json','r') as f:
            command_defs = json.loads(f.read())
        asyncio.ensure_future(self.gw_api.update_command_definitions(
            system="Example FlatSat",
            definitions=command_defs["definitions"]))

        resp = "" 
        self.gateway.satellite_response(cmd_bytes, resp)
        print("command resp: {}", resp)