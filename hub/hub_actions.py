from pybricks.hubs import InventorHub
from pybricks.parameters import Stop, Color
from pybricks.pupdevices import Motor, UltrasonicSensor, ColorSensor
from hub_tools import abs_deg, clamp


def run_time(motor: Motor, speed: float, time: float):
    if motor is None:
        return
    motor.run_time(speed, time, Stop.COAST, True)


def run_target(motor: Motor, speed: float, target: float):
    if motor is None:
        return
    motor.run_target(speed, target, Stop.COAST, True)


def run_angle(motor: Motor, speed: float, angle: float):
    if motor is None:
        return
    motor.run_angle(speed, angle, Stop.COAST, True)


def stop(motor: Motor):
    if motor is None:
        return
    motor.stop()


def get_angle(motor: Motor):
    if motor is None:
        return
    return motor.angle()


def get_distance(us_sensor: UltrasonicSensor):
    if us_sensor is None:
        return
    return us_sensor.distance()


def get_hsv(color_sensor: ColorSensor, surface: bool = False):
    if color_sensor is None:
        return
    return color_sensor.hsv(surface)


def change_light(hub: InventorHub, h: float, s: float, v: float):
    # Clamp the values to the valid range.
    h = abs_deg(h)
    s = clamp(s, 0, 100)
    v = clamp(v, 0, 100)

    if h == 0 and s == 0 and v == 0:
        hub.light.off()
    else:
        hub.light.on(Color(h, s, v))
