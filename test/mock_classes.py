from random import randint
from pybricks.parameters import Port


class MockMotor:
    def __init__(self, port: Port):
        self.port = port
        if port in [Port.A, Port.C, Port.E]:
            self.angle = 0
        else:
            raise Exception("Invalid port for motor")

    async def run_time(self, speed: int, time: int):
        print(f"Running motor on port {self.port} at speed {speed} for {time} ms")

    async def run_angle(self, speed: int, angle: int):
        print(f"Running motor on port {self.port} at speed {speed} for {angle} degrees")
        self.angle += (self.angle + angle) % 360

    async def run_target(self, speed: int, target_angle: int):
        print(
            f"Running motor on port {self.port} at speed {speed} to reach {target_angle} degrees"
        )
        self.angle = target_angle % 360
        if self.angle < 0:
            self.angle += 360

    async def run_until_stalled(self, speed: int):
        print(f"Running motor on port {self.port} at speed {speed} until stalled")
        self.angle = randint(0, 360)

    async def stop(self):
        print(f"Stopping motor on port {self.port}")

    async def reset_angle(self, angle: int):
        print(f"Resetting motor on port {self.port} to angle {angle}")
        self.angle = 0

    async def run(self, speed: int):
        print(f"Running motor on port {self.port} at speed {speed}")
        self.angle = (self.angle + speed * 10) % 360

    def angle(self):
        print(f"Getting angle of motor on port {self.port}")
        return self.angle


class MockUltrasonicSensor:
    def __init__(self, port: Port):
        self.port = port
        if port != Port.B:
            raise Exception("Invalid port for ultrasonic sensor")

    def distance(self):
        print(f"Getting distance from ultrasonic sensor on port {self.port}")
        return randint(400, 2000)


class MockColorSensor:
    def __init__(self, port: Port):
        self.port = port
        if port != Port.D:
            raise Exception("Invalid port for color sensor")

    def hsv(self, surface: bool = False):
        print(f"Getting HSV from color sensor on port {self.port}, surface={surface}")
        return (randint(0, 360), randint(0, 100), randint(0, 100))


class MockHub:
    def __init__(self, name: str):
        self.name = name

    def set_light(self, h: int, s: int, v: int):
        print(f"Setting light on hub {self.name} to HSV({h}, {s}, {v})")
