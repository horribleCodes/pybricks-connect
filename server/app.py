"""
Module that contains the main application logic for the Mindstorms Connector.
This module contains the main entry point for the application and sets up the
controller module managing the BLE connection interface.
"""

import asyncio
from controller import Controller, controller_runner
from server import Server, server_runner
from tools import print_kwargs, print_spacer, print_tasks, print_title
import argparse

# App infos
_NAME = "PYBRICKS CONNECT"
_VERSION = "0.1.0"
_TITLE_PATH = "title.txt"

# Environment variables
_HUB_NAME = "Pybricks Hub"  # Name of the hub to connect to. Used to discover the device with BT.
_HOST = "0.0.0.0"  # Host to run the server on.
_PORT = 5000  # Port to run the server on.
_INSTRUCTS_CONFIG = "server_data/instructs.yml"

# App components
_CONTROLLER: Controller = None
_SERVER: Server = None

# Collection of ongoing functions to be run
_TASKS: dict = {}


# Parse command line arguments
def _parse_args():
    """
    Parse command line arguments.
    """
    global _QUIET, _VERBOSE, _HOST, _PORT, _HUB_NAME, _INSTRUCTS_CONFIG

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quiet", action="store_true", help="Enable quiet mode", default=False
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose mode", default=False
    )
    parser.add_argument("--host", type=str, help="Specify the host", default=_HOST)
    parser.add_argument("--port", type=int, help="Specify the port", default=_PORT)
    parser.add_argument(
        "--hub-name", type=str, help="Specify the hub name", default=_HUB_NAME
    )
    parser.add_argument(
        "--instructs-config",
        type=str,
        help="Path to the instructs config file",
        default=_INSTRUCTS_CONFIG,
    )
    args = parser.parse_args()

    # Assign arguments to variables
    _QUIET = args.quiet
    _VERBOSE = args.verbose
    _HOST = args.host
    _PORT = args.port
    _HUB_NAME = args.hub_name
    _INSTRUCTS_CONFIG = args.instructs_config


def _setup():
    """
    Set up the environment variables and print the title.
    """
    global _CONTROLLER, _SERVER, _TASKS, _HUB_NAME, _HOST, _PORT, _QUIET, _VERBOSE
    global _INSTRUCTS_CONFIG

    print_title(_NAME, _VERSION, _TITLE_PATH)
    print_spacer()
    _parse_args()

    # App components
    _CONTROLLER = Controller(
        _HUB_NAME,
        quiet=_QUIET,
        verbose=_VERBOSE,
        instructs_config_path=_INSTRUCTS_CONFIG,
    )
    _SERVER = Server(_CONTROLLER, host=_HOST, port=_PORT)

    _TASKS = {
        controller_runner: [_CONTROLLER],
        server_runner: [_SERVER],
    }

    print("Environment variables:")
    print_kwargs(
        HUB_NAME=_HUB_NAME,
        HOST=_HOST,
        PORT=_PORT,
        QUIET=_QUIET,
        VERBOSE=_VERBOSE,
        INSTRUCTS_CONFIG=_INSTRUCTS_CONFIG,
    )
    print_spacer()


async def _gather_tasks():
    """
    Use asyncio to gather all tasks listed in the _TASKS dictionary and run them.
    """
    print("Tasks:")
    print_tasks(_TASKS)
    print_spacer()
    await asyncio.gather(*[runner(*args) for runner, args in _TASKS.items()])


def main():
    _setup()
    asyncio.run(_gather_tasks())
    print("Goodbye.")


if __name__ == "__main__":
    main()
