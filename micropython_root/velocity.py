"""
This controller is a simple controller intended to be used
with the bno055.py library.

Authors: Kevin Eckert

Using quaternion rotation, it attempts to calculate motion
due to movement and uses that to calculate the current velocity.

"""

import bno055 as bno
from time import sleep
import pump

ctrl = 1
delta = 0.6


def velocity(i2c, address):
    velocity = [0, 0, 0]
    bno.set_mode(i2c, address)
    sleep(1)
    while(ctrl == 1):
        matrix = bno.get_quaternion_data(i2c, address)
        accel = bno.get_linear_accel_data(i2c, address)
        accel = bno.quaternion_rotation(matrix, accel)
        sleep(delta)
        velocity = bno.calculate_velocity(velocity, accel, delta)
        if velocity[2] > 0:
            pump.pump_out()
        elif velocity[2] < 0:
            pump.pump_in()
        elif velocity[2] == 0:
            pump.stop()
    return 0


def stop():
    ctrl = 0
    pump.stop()
    return 0


def start():
    ctrl = 1
    return 0


def set_sample_rate(x):
    delta = x
    return 0
