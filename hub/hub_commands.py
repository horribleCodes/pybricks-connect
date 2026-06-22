from hub_tools import (
    ETX,
    ESC,
    FS,
    STX,
    convert_to_bytes,
    convert_to_float,
    convert_to_int,
    get_name_of_object,
    read_parameters,
    print_binary,
    NUM_NATURAL,
    NUM_DECIMAL,
    NUM_DECSIG,
    SUB,
    NAK,
)
from hub_actions import (
    get_angle,
    run_angle,
    run_target,
    run_time,
    change_light,
    get_distance,
    get_hsv,
)
from hub_devices import (
    get_device,
    read_port,
    get_allowed_devices,
    filter_devices_by_type,
)
from pybricks.hubs import InventorHub
from pybricks.pupdevices import Motor, UltrasonicSensor, ColorSensor
from pybricks.tools import wait


_RPS = 360
_MAX_SPEED = 2 * _RPS
_read_mode = False


def _toggle_read_mode():
    global _read_mode
    _read_mode = not _read_mode
    print_binary(FS)


def _print_angle(motor: Motor):
    if motor is None:
        return
    angle = get_angle(motor)
    _toggle_read_mode()
    print("Angle:%i" % angle)
    _toggle_read_mode()


def _check_valid_number(value, name):
    if value is None:
        raise ValueError("Please enter a valid number for %s." % name)


# Commands
def _motor_get_angle(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)
    _print_angle(motor)


def _motor_run_reset(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)
    run_target(motor, _MAX_SPEED, 0)
    _print_angle(motor)


def _motor_run_time(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)
    speed, time = read_parameters(
        "Speed (deg/s)", "Time (ms)", allowed_chars=NUM_DECSIG
    )

    speed, time = [convert_to_float(value) for value in [speed, time]]
    _check_valid_number(speed, "speed")
    _check_valid_number(time, "time")

    run_time(motor, speed, time)
    _print_angle(motor)


def _motor_run_target(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)
    speed, target = read_parameters(
        "Speed (deg/s)", "Target Angle(deg)", allowed_chars=NUM_DECSIG
    )

    speed, target = [convert_to_float(value) for value in [speed, target]]
    _check_valid_number(speed, "speed")
    _check_valid_number(target, "the target angle")

    run_target(motor, speed, target)
    _print_angle(motor)


def _motor_run_angle(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)
    speed, angle = read_parameters(
        "Speed (deg/s)", "Angle(deg)", allowed_chars=NUM_DECSIG
    )

    speed, angle = [convert_to_float(value) for value in [speed, angle]]
    _check_valid_number(speed, "speed")
    _check_valid_number(angle, "the angle")

    run_angle(motor, speed, angle)
    _print_angle(motor)


def _motor_run_back_forth(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    motor = get_device(port, devices, Motor)

    speed, target, rest = read_parameters(
        "Speed (deg/s)",
        "Target Angle(deg)",
        "Rest Time (ms)",
        allowed_chars=NUM_DECSIG,
    )

    speed, target, rest = [convert_to_float(value) for value in [speed, target, rest]]
    _check_valid_number(speed, "speed")
    _check_valid_number(target, "the target angle")
    _check_valid_number(rest, "the rest time")

    current_position = motor.angle()
    run_target(motor, speed, target)
    wait(rest)
    run_target(motor, speed, current_position)
    _print_angle(motor)


def _hub_set_light(**kwargs):
    hub: InventorHub = kwargs.get("hub")
    h, s, v = read_parameters(
        "Hue (0-360)",
        "Saturation (0-100)",
        "Value (0-100)",
        allowed_chars=NUM_DECIMAL,
    )

    h, s, v = [convert_to_float(value) for value in [h, s, v]]
    _check_valid_number(h, "hue")
    _check_valid_number(s, "saturation")
    _check_valid_number(v, "value")

    change_light(hub, h, s, v)


def _ussensor_get_distance(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    us_sensor = get_device(port, devices, UltrasonicSensor)
    distance = get_distance(us_sensor)
    if distance is not None:
        _toggle_read_mode()
        print("Distance:%i" % distance)
        _toggle_read_mode()


def _colsensor_get_hsv(**kwargs):
    devices: dict = kwargs.get("devices")
    port = read_port()
    color_sensor = get_device(port, devices, ColorSensor)
    surface = read_parameters("Surface Mode (Y/n)", allowed_chars="yYnN")
    if surface in ["y", "Y"]:
        surface = True
    hsv = get_hsv(color_sensor, surface)
    if hsv is not None:
        _toggle_read_mode()
        print("H:%s" % hsv.h)
        print("S:%s" % hsv.s)
        print("V:%s" % hsv.v)
        _toggle_read_mode()


def _get_devices(**kwargs):
    devices: dict = kwargs.get("devices")
    allowed_devices = get_allowed_devices()
    print("Select a device type:")
    print(" 0) All")
    for index in range(len(allowed_devices)):
        device = get_name_of_object(allowed_devices[index])
        print(" %i) %s" % (index + 1, device))
    index = read_parameters("Device Type", allowed_chars=NUM_NATURAL)[0]
    index = convert_to_int(index)
    if index > 0 and index <= len(allowed_devices):
        requested_devices = filter_devices_by_type(devices, allowed_devices[index - 1])
    else:
        requested_devices = devices
    _toggle_read_mode()
    for port, device in requested_devices.items():
        print("%s: %s" % (port, device))


def _cmd_exit(**kwargs):
    print("Shutting down...")
    print_binary(ESC)
    return True


def _cmd_help(**kwargs):
    print("Commands:")
    commands = list(_VALID_COMMANDS.keys())
    commands.sort()
    for command in commands:
        print("- %s" % str(command, "utf-8"))


_VALID_COMMANDS: dict[bytes, callable] = {
    b"mot get angle": _motor_get_angle,
    b"mot run reset": _motor_run_reset,
    b"mot run time": _motor_run_time,
    b"mot run target": _motor_run_target,
    b"mot run angle": _motor_run_angle,
    b"mot run backforth": _motor_run_back_forth,
    b"hub set light": _hub_set_light,
    b"uss get distance": _ussensor_get_distance,
    b"cls get hsv": _colsensor_get_hsv,
    b"get devices": _get_devices,
    b"bye": _cmd_exit,
    b"help": _cmd_help,
}


def register_command(command, function: callable):
    convert_to_bytes(command)
    _VALID_COMMANDS[command] = function


def execute_command(command: bytes, devices: dict, hub: InventorHub):
    global _read_mode
    success = False
    exit_flag = False
    _read_mode = False

    print_binary(STX)

    try:
        command_func: callable = _VALID_COMMANDS.get(convert_to_bytes(command))
        if command_func is None:
            raise KeyError('Unknown Command "%s".' % str(command, "utf-8"))

        exit_flag = command_func(devices=devices, hub=hub)
    except Exception as e:
        print(e)
    else:
        success = True
    finally:
        # Add a read mode toggle character if read mode is enabled
        if _read_mode:
            _toggle_read_mode()
        if success:
            print_binary(SUB)
        else:
            print_binary(NAK)
        print_binary(ETX)
        return exit_flag
