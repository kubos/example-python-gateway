import logging
import asyncio
import argparse
import json
from gateway.gateway import Gateway
from demo.demo_sat import DemoSat
from majortom_gateway import GatewayAPI

logger = logging.getLogger(__name__)

def parse_args():
    # Set up command line arguments
    parser = argparse.ArgumentParser()
    # Required Args
    parser.add_argument(
        "majortomhost",
        help='Major Tom host name. Can also be an IP address for local development/on prem deployments.')
    parser.add_argument(
        "gatewaytoken",
        help='Gateway Token used to authenticate the connection. Look this up in Major Tom under the gateway page for the gateway you are trying to connect.')

    # Optional Args and Flags
    parser.add_argument(
        '-b',
        '--basicauth',
        help='Basic Authentication credentials. Not required unless BasicAuth is active on the Major Tom instance. Must be in the format "username:password".')
    parser.add_argument(
        '-l',
        '--loglevel',
        choices=["debug", "info", "error"],
        default="debug",
        help='Log level for the logger.')
    parser.add_argument(
        '--http',
        help="If included, you can instruct the gateway to connect without encryption. This is to support on prem deployments and local development without https.",
        action="store_true")
    parser.add_argument(
        '-a', 
        '--async',

        help="If included, we use the original demo_sat.py gateway file instead of gateway.py. ",
        action="store_true")
    
    return parser.parse_args()

def configure_logging(args):
    if args.loglevel == 'error':
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    elif args.loglevel == 'info':
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    elif args.loglevel == 'debug':
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    else:
        raise Exception(f"Invalid log level: {args.loglevel}")

def run_async(args):
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
        cancel_callback=demo_sat.cancel_callback,
        http=args.http)

    logger.debug("Connecting to MajorTom")
    asyncio.ensure_future(gateway.connect_with_retries())

    logger.debug("Sending Command Definitions")
    asyncio.ensure_future(gateway.update_command_definitions(
        system=demo_sat.name,
        definitions=demo_sat.definitions))

    logger.debug("Starting Event Loop")
    loop.run_forever()

def run_sync(args):
    logger.debug("Starting Event Loop")
    loop = asyncio.get_event_loop()

    # Gateways are the link between the generic interfaces of Major Tom and the specifics of your
    # satellite(s) and groundstation(s). They can be designed to handle one or more satellites and 
    # one or more groundstations.    

    logger.debug("Setting up Gateway")
    gateway = Gateway()

    # Gateways use a websocket API, and we have a library to make the interface easier.
    # We instantiate the API, making sure to specify both sides of the connection:
    #  - The Major Tom side, which requires a host and authentication
    #  - The Gateway side, which specifies all the callbacks to be used when Major Tom communicates with this Gateway
    logger.debug("Setting up websocket connection")
    websocket_connection = GatewayAPI(
                            host=args.majortomhost,
                            gateway_token=args.gatewaytoken,
                            basic_auth=args.basicauth,
                            http=args.http,

                            command_callback=gateway.command_callback,
                            error_callback=gateway.error_callback,
                            rate_limit_callback=gateway.rate_limit_callback,
                            cancel_callback=gateway.cancel_callback,
                            transit_callback=gateway.transit_callback,
                            received_blob_callback=gateway.received_blob_callback,
                        )
    
    # It is useful to have a reference to the websocket api within your Gateway
    gateway.api = websocket_connection
    
    # Connect to MT
    asyncio.ensure_future(websocket_connection.connect_with_retries())

    # To make it easier to interact with this Gateway, we are going to configure a bunch of commands for a satellite
    # called "Example FlatSat". Please see the associated json file to see the list of commands.
    # logger.debug("Setting up Example Flatsat satellite and associated commands")
    with open('satellite/example_commands.json','r') as f:
        command_defs = json.loads(f.read())
    asyncio.ensure_future(websocket_connection.update_command_definitions(
        system="Example FlatSat",
        definitions=command_defs["definitions"]))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

    # Now, head to the Major Tom UI. You should see the Gateway whose token you used as "Connected". 
    # 
    # There should be an "Example FlatSat" satellite with commands that you can execute.
    # Executing those commands will cause this Gateway (and the associated fake Satellite) to respond. 
    # Trace the path of commands from Major Tom through the Gateway to the Satellite and back.
    # Then modify the gateway and fake satellite to suite your mission.


def main():
    args = parse_args()
    configure_logging(args)

    if vars(args)['async']:
        run_async(args)
    else:
        run_sync(args)
    

if __name__ == '__main__':
    main()