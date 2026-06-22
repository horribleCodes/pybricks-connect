import asyncio
from enum import Enum
from bleak_interface import BleakInterface
from colorsys import rgb_to_hsv
from instruct_config import load_instructs
from models import InstructDefinition

from server_data.hub_commands import _VALID_COMMANDS


class State(Enum):
    ERROR = 0
    READY = 1
    RETRIEVE = 2
    EXIT = 3


class Color:
    def __init__(self, red: int, green: int, blue: int):
        self.red = red
        self.green = green
        self.blue = blue

    def __str__(self):
        return "(%d, %d, %d)" % (self.red, self.green, self.blue)

    def to_dict(self):
        return {"red": self.red, "green": self.green, "blue": self.blue}

    def from_hsv(self, hue: int, saturation: int, value: int):
        (self.red, self.green, self.blue) = self.hsv_100_to_rgb_255(
            hue, saturation, value
        )

    def as_hsv(self):
        return self.rgb_255_to_hsv_100(self.red, self.green, self.blue)

    def rgb_255_to_hsv_100(self, r, g, b):
        (h, s, v) = rgb_to_hsv(r / 255, g / 255, b / 255)
        return tuple(round(c * 100, 0) for c in (h, s, v))

    def hsv_100_to_rgb_255(self, h, s, v):
        (r, g, b) = rgb_to_hsv(h / 100, s / 100, v / 100)
        return tuple(round(c * 255, 0) for c in (r, g, b))


class DeviceType(Enum):
    Motor = 0
    UltrasonicSensor = 1
    ColorSensor = 2


class Device:
    def __init__(self, port: int, type: DeviceType):
        self.port: int = port
        self.type: DeviceType = type
        self._value = None

    @property
    def value(self):
        value = self._value
        if self.type == DeviceType.ColorSensor:
            value = self._get_color()
        return value

    def to_dict(self):
        return {"port": self.port, "type": self.type.name, "value": self.value}

    def _get_color(self):
        color: Color = self._value
        return color.to_dict()


Motor_Reset = "mot run reset"
Motor_Run_Time = "mot run time"
Motor_Run_Angle = "mot run angle"
Motor_Get_Angle = "mot get angle"
USS_Get_Distance = "uss get distance"
Color_Get_HSV = "cls get hsv"
Hub_Set_Light = "hub set light"
Devices_Get = "get devices"

_UPDATE_KEY = "UPDATE"
_GROUP_SEPARATOR = "\x1d"


async def _default_instruct(controller, instruct: InstructDefinition):
    await controller._bleak_interface.send(instruct.function, *instruct.parameters)


# Instruction handlers
async def _motor_run_angle(controller, instruct: InstructDefinition):
    await controller._bleak_interface.send(
        Motor_Run_Angle, instruct.port, *instruct.parameters
    )


async def _motor_reset(controller, instruct: InstructDefinition):
    await controller._bleak_interface.send(Motor_Reset, instruct.port)


_INSTRUCT_HANDLERS = {"motor_run_angle": _motor_run_angle, "motor_reset": _motor_reset}


class Controller:
    def __init__(
        self,
        hub_name="Pybricks Hub",
        quiet=False,
        verbose=False,
        instructs_config_path="server_data/instructs.yml",
    ):
        self._instructs = load_instructs(
            instructs_config_path, valid_handlers=set(_INSTRUCT_HANDLERS.keys())
        )
        self._current_instruct = next(iter(self._instructs))
        self._state = State.READY
        self.queue = asyncio.Queue()
        self._bleak_interface = BleakInterface(hub_name)
        self._devices: dict[int, Device] = {}
        self.update_interval = 0.5
        self.quiet = quiet
        self.verbose = verbose
        self._bleak_interface.quiet(self.quiet)
        self._ready_color = Color(0, 60, 255)
        self._retrieve_color = Color(220, 40, 0)
        self._exit_color = Color(10, 10, 50)

    # Public
    async def connect(self, tries: int = 1, hub_name: str = None):
        return await self._bleak_interface.connect(tries, hub_name)

    async def cancel(self):
        if self._state not in [State.RETRIEVE]:
            return False, self._state.name, "System is not ordering at the moment."

        await self._change_state(State.READY)
        return True, self._state.name, "Successfully cancelled the current action."

    async def run_instruct(self, instruct_id: str):
        if self._state != State.READY:
            return False, self._state.name, "System is not ready to ship orders."

        self._current_instruct = instruct_id
        await self._change_state(State.RETRIEVE)
        return True, self._state.name, ("Running instruct %s." % self._current_instruct)

    async def reset_motor(self, instruct_id: str):
        port = self._instructs[instruct_id].port
        asyncio.create_task(self._bleak_interface.send(Motor_Reset, port))

    def exit(self):
        if not self.is_running():
            return 0, ("System is not running.")

        self.queue.put_nowait(State.EXIT)
        return self.get_queue_size(), ("Exiting the system...")

    def enqueue(self, instruct_id: str):
        self.queue.put_nowait(instruct_id)
        return self.get_queue_size(), ("Enqueued instruct %s." % instruct_id)

    def is_running(self):
        return self._bleak_interface.is_running()

    def get_state(self):
        return self._state

    def get_hub_name(self):
        return self._bleak_interface.hub_name()

    def get_current_instruct(self):
        return self._current_instruct

    def get_queue(self):
        return [instruct for instruct in self.queue]

    def get_queue_size(self):
        return self.queue.qsize()

    def get_distance(self, port: int | None = None):
        ussensor: Device = self._get_device(port, DeviceType.UltrasonicSensor)
        return {port: ussensor.value}

    def get_color(self, port: int | None = None):
        color_sensor: Device = self._get_device(port, DeviceType.ColorSensor)
        try:
            color_raw = color_sensor.value
            color: Color = color_raw
        except TypeError:
            raise TypeError(
                "Invalid Color Sensor data at port %s: %s" % (port, color_raw)
            )
        else:
            return {port: color.to_dict()}

    def get_angle(self, port: int | None = None):
        motor: Device = self._get_device(port, DeviceType.Motor)
        return {port: motor.value}

    def get_device(self, port: int | None = None, type: DeviceType = None):
        if port is None:
            devices = self._get_devices(type)
        else:
            devices = {port: self._get_device(port, type)}
        return {port: device.to_dict() for port, device in devices.items()}

    # Private
    def _get_device(self, port: int | None = None, type: DeviceType = None):
        filtered_devices: dict[int, Device] = self._get_devices(type)
        type_name = type.name if type else "device"
        if not filtered_devices:
            raise RuntimeError("No %ss available." % type_name)
        port = self._validate_port(port)

        if port is None:
            return filtered_devices[0]

        try:
            return self._devices[port]
        except KeyError:
            raise KeyError("No %s registered at port %s" % (type_name, port))

    def _get_devices(self, type: DeviceType = None):
        if type is None:
            return self._devices
        return {
            port: device
            for port, device in self._devices.items()
            if device.type == type
        }

    async def _init_devices(self):
        response = await self._bleak_interface.send(Devices_Get, 0)
        response = response[0]
        if not response:
            return
        for device_str in response:
            port_raw, device_type_raw = device_str.split(": ", 1)
            port = port_raw.split(".")[1]
            port = ord(port) - ord("A")
            device_type_raw = device_type_raw.split("(", 1)[0].strip(" <>")
            device_type = DeviceType[device_type_raw]
            self._devices[port] = Device(port, device_type)
            self._enqueue_update(port)

    async def _update_device(self, port: int):
        switcher = {
            DeviceType.Motor: self._get_angle,
            DeviceType.UltrasonicSensor: self._get_distance,
            DeviceType.ColorSensor: self._get_color,
        }
        self._devices[port]._value = await switcher.get(self._devices[port].type)(
            port, quiet=not self.verbose
        )

    async def _change_state(self, new_state: State):
        self._state = new_state

        switcher = {
            State.READY: self._enter_READY,
            State.RETRIEVE: self._enter_RETRIEVE,
            State.EXIT: self._enter_EXIT,
        }

        func = switcher.get(new_state, lambda: None)
        if func:
            await func()

    async def _enter_READY(self):
        await self._bleak_interface.send(Hub_Set_Light, *self._ready_color.as_hsv())

    async def _enter_RETRIEVE(self):
        await self._bleak_interface.send(Hub_Set_Light, *self._retrieve_color.as_hsv())
        await self._execute_instruct(self._current_instruct)

    async def _enter_EXIT(self):
        await self._bleak_interface.send(Hub_Set_Light, *self._exit_color.as_hsv())

    async def _execute_instruct(self, instruct_id: str):
        print("Running instruct %s..." % instruct_id)

        try:
            instruct = self._instructs[instruct_id]
            handler = _INSTRUCT_HANDLERS[instruct.function]
        except KeyError:
            if instruct_id in _VALID_COMMANDS:
                handler = _default_instruct
            else:
                raise KeyError("Unknown instruct %s." % instruct_id)
        else:
            await handler(self, instruct)
        finally:
            await self._change_state(State.READY)

    async def _get_angle(self, port=None, quiet=False):
        response = await self._bleak_interface.send(Motor_Get_Angle, port, quiet=quiet)
        if not response:
            raise ValueError("No angle data received.")
        return float(response[0][0].split(":")[1])

    async def _get_distance(self, port=None, quiet=False):
        response = await self._bleak_interface.send(USS_Get_Distance, port, quiet=quiet)
        if not response:
            raise ValueError("No distance data received.")
        return float(response[0][0].split(":")[1])

    async def _get_color(self, port=None, surface_mode="Y", quiet=False):
        response = await self._bleak_interface.send(
            Color_Get_HSV, port, surface_mode, quiet=quiet
        )
        if not response:
            raise ValueError("No color data received.")
        values_raw: list[str] = response[0]
        values = {
            name: value
            for name, value in [value_raw.split(":", 1) for value_raw in values_raw]
        }
        return Color(values["H"], values["S"], values["V"])

    def _validate_port(self, port):
        try:
            port = int(port)
            if port not in range(0, 6):
                raise ValueError
        except ValueError:
            raise ValueError("Invalid port number: %s" % port)
        return port

    def _should_update(self):
        should_update = True
        try:
            queue_item = self.queue._queue[-1]
        except IndexError:
            should_update = True
        else:
            if queue_item.startswith(_UPDATE_KEY):
                should_update = False
            elif queue_item == State.EXIT:
                should_update = False
        finally:
            return should_update

    def _enqueue_update(self, port: int):
        queue_item = _UPDATE_KEY + _GROUP_SEPARATOR + str(port)
        self.queue.put_nowait(queue_item)

    def _enqueue_updates(self):
        for port in self._devices.keys():
            self._enqueue_update(port)

    async def _handle_queue_item(self, queue_item: str):
        if queue_item == State.EXIT:
            await self._bleak_interface.disconnect()
        elif queue_item.startswith(_UPDATE_KEY):
            device_port = int(queue_item.split(_GROUP_SEPARATOR)[1])
            await self._update_device(device_port)
        else:
            print("Popped instruct %s from queue." % queue_item)
            self._current_instruct = queue_item
            await self._change_state(State.RETRIEVE)

    # Async Loops
    async def handle_queue(self):
        print("Queue handler is now running...")
        while self.is_running():
            if self.queue.empty():
                await asyncio.sleep(0.5)
                continue

            if self._state == State.EXIT:
                await self._bleak_interface.disconnect()
            elif self._state == State.READY:
                queue_item: str = await self.queue.get()
                await self._handle_queue_item(queue_item)
            else:
                await asyncio.sleep(0.1)
        print("Queue handler stopped.")

    async def schedule_update(self):
        print("Update scheduler is now running...")
        while self.is_running():
            await asyncio.sleep(self.update_interval)
            if self._should_update():
                self._enqueue_updates()


async def controller_runner(
    controller: Controller, max_repeats: int = 2, hub_name: str = None
):
    await asyncio.sleep(0.1)

    await controller._bleak_interface.connect(
        max_repeats=max_repeats, hub_name=hub_name
    )

    if controller.is_running():
        await controller._init_devices()

        tasks = [
            asyncio.create_task(controller.schedule_update()),
            asyncio.create_task(controller.handle_queue()),
        ]
        await asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
