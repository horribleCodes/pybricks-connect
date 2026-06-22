from hub_commands import execute_command
from hub_tools import ENQ, print_binary, read_indefinite, STX, EM
from hub_devices import setup_devices
from pybricks.hubs import InventorHub
from pybricks.pupdevices import Motor, UltrasonicSensor, ColorSensor
from pybricks.parameters import Port
from pybricks.tools import wait
from usys import stdin
from uselect import poll

DEVICES: dict[Port, Motor | UltrasonicSensor | ColorSensor] = {}
HUB: InventorHub = None
_RUNNING = False
_KEYBOARD = None


def setup(verbose=False, quiet=True):
    """
    Set up the hub and devices.
    """
    global DEVICES, HUB, _RUNNING, _KEYBOARD
    # Define the hub.
    HUB = InventorHub()

    print_binary(STX)
    print(f"Starting {HUB.system.name()}...")

    # Define the devices.
    DEVICES = setup_devices(verbose=verbose, quiet=quiet)

    print("Ready for user input. Type commands and press Enter.")
    print('For help, type "help".')
    print('Type "bye" to exit.')
    print_binary(EM)

    _RUNNING = True

    # Register stdin for polling. This allows
    # you to wait for incoming data without blocking.
    _KEYBOARD = poll()
    _KEYBOARD.register(stdin)


def run():
    """
    Run the main loop.
    """
    global DEVICES, HUB, _RUNNING, _KEYBOARD

    print_binary(ENQ)

    # Wait for user input.
    while not _KEYBOARD.poll(0):
        wait(10)

    # Read a command.
    command = read_indefinite(prefix_enq=False)

    # Decide what to do based on the command.
    _RUNNING = not execute_command(command, DEVICES, HUB)

    if not _RUNNING:
        return


def _main():
    setup()
    while _RUNNING:
        run()


if __name__ == "__main__":
    _main()
