import logging
import asyncio
import time
import argparse
from mt_gateway_api.gateway_api import GatewayAPI
from demo.demo_sat import DemoSat

logger = logging.getLogger(__name__)

# Set up command line arguments
parser = argparse.ArgumentParser()
parser._action_groups.pop()
required = parser.add_argument_group('required arguments')
optional = parser.add_argument_group('optional arguments')
required.add_argument(
    '-m',
    '--majortomhost',
    help='Major Tom host name. Can also be an IP address for local development/on prem deployments.',
    required=True)
required.add_argument(
    '-g',
    '--gatewaytoken',
    help='Gateway Token used to authenticate the connection. Look this up in Major Tom under the gateway page for the gateway you are trying to connect.',
    required=True)
optional.add_argument(
    '-b',
    '--basicauth',
    help='Basic Authentication credentials. Not required unless BasicAuth is active on the Major Tom instance. Must be in the format "username:password".',
    required=False)
optional.add_argument(
    '-l',
    '--loglevel',
    help='Log level for the logger. Defaults to "debug", can be set to "info", or "error".',
    required=False)
optional.add_argument(
    '-t',
    '--telemetry',
    help='If included, starts the telemetry beacon for the demo spacecraft automatically in the mode indicated. Can be "nominal" or "error".',
    required=False)

args = parser.parse_args()

if args.loglevel == 'error':
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
elif args.loglevel == 'info':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger.info("Starting up!")
loop = asyncio.get_event_loop()

logger.debug("Setting up Demo Satellite")
demo_sat = DemoSat(name="Space Oddity")

logger.debug("Setting up MajorTom")
gateway = GatewayAPI(
    host=args.majortomhost,
    gateway_token=args.gatewaytoken,
    basic_auth=args.basicauth,
    command_callback=demo_sat.command_callback,
    cancel_callback=demo_sat.cancel_callback
)

logger.debug("Connecting to MajorTom")
asyncio.ensure_future(gateway.connect_with_retries())

logger.debug("Sending Command Definitions")
asyncio.ensure_future(gateway.update_command_definitions(
    system=demo_sat.name,
    definitions=demo_sat.definitions))

if args.telemetry == "nominal":
    logger.debug("Starting Nominal Telemetry")
    asyncio.ensure_future(demo_sat.telemetry.nominal(duration=30000000, gateway=gateway))
elif args.telemetry == "error":
    logger.debug("Starting Error Telemetry")
    asyncio.ensure_future(demo_sat.telemetry.error(duration=30000000, gateway=gateway))
elif args.telemetry == None:
    pass
else:
    raise ValueError(f"Invalid telemetry type: {args.telemetry}")

logger.debug("Starting Event Loop")
loop.run_forever()
