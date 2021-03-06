# TODO: implement temperature smoothing for thermal runaway protection
from micropython import const
import _thread
from time import sleep
import time

from statistics_tools import abs_fwd_timegraph, linreg_past

from bmp388 import BMP388
from VL53L0X import VL53L0X
from maxsonar import XLMaxSonarUART
from adxl345 import ADXL345
from accelerometer import ACCELEROMETER
from distance import HeightTiltCompensator
from altitude import ALTITUDE
import pump

_ALTITUDE_SAMPLING_TIME_BUDGET = 200  # sampling period of barometer in ms

# I2C Object
if 'i2c' not in globals():
    from machine import I2C, Pin
    i2c = I2C(0, scl=Pin(22), sda=Pin(21))

adxl = ADXL345(i2c, 83)
accelerometer = ACCELEROMETER(adxl, 'adxl345_calibration_2point')
tof = VL53L0X(i2c, 41)
tof_fusion = HeightTiltCompensator(accelerometer, tof)
ultrasonic = XLMaxSonarUART()
ultrasonic_fusion = HeightTiltCompensator(accelerometer, ultrasonic)
barometer = BMP388(i2c)

altitude = ALTITUDE(barometer, tof_fusion, ultrasonic_fusion)
altitude.sr.offset = -40.0

_MAX_LIST_SIZE = const(120)

CFGFILE = "ballonet_controller_cfg"

cfg = {
    'setpoint': 0,  # maintain this velocity
    'bangbang_tolerance': 50,  # mm/s, activate pump above this speed

    # when above ceiling height, decrease velocity setpoint
    # it may be good to set this well under max range of LR rangefinder
    # set to float('inf') to disable
    'ceiling_height': 120,

    # when below floor height, increase velocity setpoint
    # set to float('-inf') to disable
    'floor_height': 0,

    # noise scaling will widen the bangbang tolerance if noise is detected
    'noise_scaling': False,

    # see altitude.py file for info on these
    'barometer_drift': 1,
    'calibration_drift': 0.25
}


def loadcfg():
    with open(CFGFILE, 'r') as f:
        text = f.read().rstrip().split("\n")
        for i in text:
            key, value = i.split("\t")
            cfg[key] = eval(value)
    altitude.barometer_drift = cfg['barometer_drift']
    altitude.calibration_drift = cfg['calibration_drift']


def savecfg():  # only dicts with string keys and stringable values are supported
    # sadly pickle module not available in micropython yet :(
    with open(CFGFILE, 'w') as f:
        for key in cfg:
            f.write("{key}\t{value}\n".format(key=key, value=str(cfg[key])))


def __loop(n_s, T):
    global enable
    global history
    # Length of history to use for calculating velocity
    history = {'altitude': [], 'velocity': [], 'time': []}
    previous_time = time.ticks_ms()
    for i in range(n_s + 1):
        history['altitude'].append(altitude.meters)
        now = time.ticks_ms()
        history['time'].append(time.ticks_diff(now, previous_time))
        previous_time = time.ticks_ms()
        history['velocity'].append(0)
        sleep(0.3)
    i = 0
    while True:
        if not enable:
            pump.emergency_stop()
            print("Stopping!")
            _thread.exit()
            return
        setpoint = cfg['setpoint']
        h = history['altitude']
        t = history['time']
        fix_push(h, 0.5 * altitude.meters + 0.5 * h[-1])
        now = time.ticks_ms()
        fix_push(t, time.ticks_diff(now, previous_time))
        previous_time = time.ticks_ms()
        velocity = linreg_past(abs_fwd_timegraph(t, len(t) - n_s),
                               h,
                               n_s)[0]
        # convert velocity from weird units to mm/s
        velocity = int(velocity * 1000 * 1000 / (sum(t[-n_s:]) / 1000))
        fix_push(history['velocity'], velocity)

        if h[-1] < cfg['floor_height']:
            setpoint += 50
        elif h[-1] > cfg['ceiling_height']:
            setpoint -= 50
        e = velocity - setpoint  # +e is the velocity above the setpoint
        pwm_duty = 1
        if abs(e) > cfg['bangbang_tolerance']:
            if e > 0:  # velocity too upwards
                pump.pump_in(pwm_duty)  # reduce buoyancy
            elif e < 0:  # velocity too downwards
                pump.pump_out(pwm_duty)  # increase buoyancy
        else:
            pump.stop()
        print("{:3}| T: {:3d}, H: {:7.3f}, V: {:4d}".format(i, t[-1], h[-1], history['velocity'][-1]))
        i += 1
        sleep(T)


def calibrate(barometer_drift=1, calibration_drift=0.25):
    altitude.find_floor_from_range(10, True)


def start(n_s=5, T=1000):
    global enable
    global loop
    enable = True
    T_adjusted = T - _ALTITUDE_SAMPLING_TIME_BUDGET  # this is in ms
    loop = _thread.start_new_thread(__loop, (n_s, T_adjusted / 1000))


def stop():
    global enable
    global loop
    enable = False


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
