# TODO: implement temperature smoothing for thermal runaway protection
from micropython import const
import _thread
from time import sleep
import time

from statistics_tools import abs_fwd_timegraph, linreg_past
from bmp388 import BMP388
from VL53L0X import VL53L0X
from adxl345 import ADXL345
from accelerometer import ACCELEROMETER
from distance import HEIGHT_LIDAR
from altitude import ALTITUDE
import pump


# I2C Object
if 'i2c' not in globals():
    from machine import I2C, Pin
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))

adxl = ADXL345(i2c, 83)
accelerometer = ACCELEROMETER(adxl, 'adxl345_calibration_2point')
lidar = VL53L0X(i2c, 41)
distance_fusion = HEIGHT_LIDAR(accelerometer, lidar)
barometer = BMP388(i2c)

altitude = ALTITUDE(barometer, distance_fusion)
altitude.distance.offset = -40.0

_MAX_LIST_SIZE = const(120)


# returns list as cumulative, starting at element s onwards
def absolute_fwd_timegraph(list_, s):
    y = list_.copy()
    for i in range(s, len(y)):
        y[i] += y[i - 1]
    return y


# calculates the slope of a linear regression of past n pairs
# based on https://stackoverflow.com/a/19040841/2712730
def linreg_past_slope(x, y, n):
    sumx = sum(x[-n:])
    sumx2 = sum([i**2 for i in x[-n:]])
    sumy = sum(y[-n:])
    sumxy = sum([i * j for i, j in zip(x[-n:], y[-n:])])
    denom = n * sumx2 - sumx**2
    m = (n * sumxy - sumx * sumy) / denom
    return m


def __loop():
    global setpoint
    global enable
    global bangbang_tolerance
    n_s = 5
    history = {'altitude': [], 'velocity': [], 'time': []}
    previous_time = time.ticks_ms()
    for i in range(n_s + 1):
        history['altitude'].append(altitude.meters)
        now = time.ticks_ms()
        history['time'].append(time.ticks_diff(now, previous_time))
        previous_time = time.ticks_ms()
        history['velocity'].append(0)
        sleep(0.9)
    i = 0
    while True:
        if not enable:
            pump.emergency_stop()
            print("Stopping!")
            _thread.exit()
            return
        h = history['altitude']
        t = history['time']
        fix_push(h, 0.6 * altitude.meters + 0.4 * h[-1])
        now = time.ticks_ms()
        fix_push(t, time.ticks_diff(now, previous_time))
        previous_time = time.ticks_ms()
        velocity = linreg_past_slope(absolute_fwd_timegraph(t, len(t) - n_s),
                                     h,
                                     n_s)
        velocity = int(velocity * 1000 * 1000)
        fix_push(history['velocity'], velocity)
        e = setpoint - velocity
        pwm_duty = 1
        if abs(e) > bangbang_tolerance:
            if e > 0:
                pump.pump_out(pwm_duty)
            elif e < 0:
                pump.pump_in(pwm_duty)
        else:
            pump.stop()
        print("{:3}| T: {:3d}, H: {:05.2f}, V: {:4d}".format(i, t[-1], h[-1], history['velocity'][-1]))
        i += 1
        sleep(0.8)


def start(velocity_setpoint, tolerance):
    global setpoint
    global enable
    global bangbang_tolerance
    global loop
    bangbang_tolerance = tolerance
    setpoint = velocity_setpoint
    enable = True
    loop = _thread.start_new_thread(__loop, ())


def stop():
    global enable
    global loop
    enable = False
    loop.exit()


def setpoint(velocity):
    global setpoint
    setpoint = velocity


def fix_push(o, value, max_size=_MAX_LIST_SIZE):
    if len(o) + 1 > max_size:
        o.pop(0)
    try:
        o.append(value)
    except MemoryError:
        pump.emergency_stop()
        raise
