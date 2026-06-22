from hub_tools import get_name_of_object, read_indefinite
from pybricks.pupdevices import Motor, UltrasonicSensor, ColorSensor
from pybricks.parameters import Port, Stop
from pybricks.tools import multitask, run_task


_ALLOWED_DEVICES: list = [Motor, UltrasonicSensor, ColorSensor]
_PORT_CHARS: bytearray = b"012345ABCDEFabcdef"
_PORT_MAP: bytearray = b"abcdef"
_PORT_ITER: list[Port] = [Port.A, Port.B, Port.C, Port.D, Port.E, Port.F]


def read_port():
    """
    Prompts the user to enter a port number from 0 to 5 and reads the input.

    Returns:
        input(int): The port number entered by the user.
    """
    input = read_indefinite(prompt="Port", allowed_chars=_PORT_CHARS)
    try:
        if len(input) != 1:
            raise IndexError()

        if input.isdigit():
            index = int(input)
        else:
            index = _PORT_MAP.index(input)
        return _PORT_ITER[index]
    except IndexError:
        raise IndexError(f'Invalid port number "{input}".')


def add_device(port: Port, devices: dict, required_device, verbose=False, quiet=True):
    quiet = quiet or verbose  # If verbose, disable quiet mode.
    success = False
    if port is None:
        print("PortError: Port is None.")
        return devices, success

    if required_device is not None:
        required_name = get_name_of_object(required_device)
    else:
        required_name = "None"

    if required_device not in _ALLOWED_DEVICES:
        print(f"InvalidDeviceError: {required_name} is not allowed.")
        return devices, success

    try:
        devices.update({port: required_device(port)})
    except Exception as e:
        message = f"Failed to add {required_name} at port {port}"
        if verbose:
            message += f": {str(e)}"
        else:
            message += "."

        if not quiet:
            print(message)
    else:
        success = True
        print(f"{required_name} {port} added.")
    finally:
        return devices, success


def get_device(port: Port, devices: dict, required_device=None):
    if port is None:
        return None

    if required_device is not None:
        required_type = get_name_of_object(required_device)
    else:
        required_type = "Device"

    device = None
    try:
        device = devices[port]
    except KeyError:
        raise KeyError(f"PortError: {required_type} at port {port} is missing.")

    actual_type = get_name_of_object(type(device))
    if actual_type != required_type:
        device = None
        raise TypeError(
            f"TypeError: Device at port {port} is not a {required_type}. "
            + f"Actual type: {actual_type}."
        )
    return device


def filter_devices_by_type(devices: dict, required_device):
    devices_copy = devices.copy()
    for port, device in devices.items():
        if not isinstance(device, required_device):
            devices_copy.pop(port, None)
    return devices_copy


async def reset_motors(devices: dict):
    motors: dict[Port, Motor] = filter_devices_by_type(devices, Motor)
    tasks = []
    for motor in motors.values():
        motor.run_target(100, 0, Stop.COAST, False)
    if tasks:
        print("Resetting motors...")
        await multitask(*tasks)
        print("Motors reset.")


def setup_devices(verbose=False, quiet=True):
    quiet = quiet or verbose  # If verbose, disable quiet mode.
    devices: dict[Port, Motor | UltrasonicSensor | ColorSensor] = {}

    print("Discovering devices...")
    for port in _PORT_ITER:
        for device in _ALLOWED_DEVICES:
            devices, success = add_device(port, devices, device, verbose, quiet)
            if success:
                break
    print("Scan for devices complete.")

    # If a type of device wasn't found, write a message.
    for device in _ALLOWED_DEVICES:
        if not any(isinstance(d, device) for d in devices.values()):
            print(f"No {get_name_of_object(device)} found.")

    run_task(reset_motors(devices))
    return devices


def get_allowed_devices():
    return _ALLOWED_DEVICES
