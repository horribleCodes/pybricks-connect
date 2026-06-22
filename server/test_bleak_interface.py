from bleak_interface import BleakInterface
import asyncio


async def _get_devices(interface: BleakInterface):
    devices = await interface.send("get devices", 0)
    assert devices == [
        [
            "Port.A: Motor(Port.A, Direction.CLOCKWISE)",
            "Port.B: <ColorSensor>",
            "Port.C: <UltrasonicSensor>",
        ]
    ]
    motors = await interface.send("get devices", 1)
    assert motors == [["Port.A: Motor(Port.A, Direction.CLOCKWISE)"]]


def _assert_angle(response: list[list[str]], target_angle):
    angle = response[0][0].rsplit(":")[-1].strip()
    assert abs(int(angle) - target_angle) < 4


async def _test_motor(interface: BleakInterface, port: int):
    await interface.send("mot run time", port, 720, 500)
    await interface.send("mot run time", port, -430, 500)
    response = await interface.send("mot run reset", port)
    _assert_angle(response, 0)
    await interface.send("mot run target", port, 1080, 270)
    await interface.send("mot run angle", port, 60, -30)
    await interface.send("mot run backforth", port, -500, 300, 1000)
    response = await interface.send("mot run reset", port)
    _assert_angle(response, 0)


async def get_ultrasonic_distance(interface: BleakInterface):
    distance = await interface.send("uss get distance", 2)
    assert distance[0][0].isnumeric()


async def _get_color_hsv(interface: BleakInterface):
    hsv = await interface.send("cls get hsv", 1, "y")
    assert len(hsv[0]) == 3


async def test_connect():
    interface = BleakInterface("Pybricks Hub")
    await interface.connect(2)

    # Send a few messages to the hub.
    await interface.send("hub set light", 50, 75, 100)
    quiet = interface.quiet(True)
    assert quiet
    await _get_devices(interface)
    await _test_motor(interface, 0)
    await get_ultrasonic_distance(interface)
    quiet = interface.quiet(False)
    assert quiet
    await _get_color_hsv(interface)
    await interface.send("hub set light", 0, 0, 0)

    await interface.disconnect()


if __name__ == "__main__":
    asyncio.run(test_connect())
